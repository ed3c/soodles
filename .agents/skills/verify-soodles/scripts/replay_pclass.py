#!/usr/bin/env python3
"""Replay fixed P-class raw evidence under an externally pinned manifest."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


PASS = "PASS"


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_observer(path):
    spec = importlib.util.spec_from_file_location("pclass_observer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completion_projection(run, errors):
    precondition = run.get("precondition", {})
    projection = precondition.get("completion_owner_projection")
    expected = precondition.get("completion_owner_projection_sha256")
    if not isinstance(projection, dict):
        errors.append("missing_completion_owner_projection")
        return None, None
    if fingerprint(projection) != expected:
        errors.append("completion_owner_projection_digest_mismatch")
    events = run.get("owner_events")
    if not isinstance(events, list):
        errors.append("invalid_owner_events")
        return projection, None
    matches = [index for index, event in enumerate(events) if event == projection]
    if len(matches) != 1:
        errors.append("completion_projection_observation_not_unique")
        return projection, None
    return projection, matches[0]


def normalize_run(run, declared, manifest, observer):
    errors = []
    evidence_sha256 = fingerprint(run)
    run_id = run.get("run_id")
    arm = run.get("arm")
    packet = run.get("packet") if isinstance(run.get("packet"), dict) else {}
    precondition = (run.get("precondition")
                    if isinstance(run.get("precondition"), dict) else {})
    events = run.get("owner_events") if isinstance(run.get("owner_events"), list) else []

    for key, actual in (("run_id", run_id), ("arm", arm),
                        ("case", packet.get("case")),
                        ("evidence_sha256", evidence_sha256)):
        if actual != declared.get(key):
            errors.append(f"{key}_manifest_mismatch")
    if packet.get("run_id") != run_id or precondition.get("run_id") != run_id:
        errors.append("run_id_internal_mismatch")
    if packet.get("case") != precondition.get("case"):
        errors.append("case_internal_mismatch")

    initial = packet.get("initial_owner_projection")
    expected_initial = packet.get("expected_owner_projection_sha256")
    if initial != precondition.get("initial_owner_projection"):
        errors.append("initial_owner_projection_internal_mismatch")
    if fingerprint(initial) != expected_initial:
        errors.append("initial_owner_projection_digest_mismatch")
    if expected_initial != precondition.get("initial_owner_projection_sha256"):
        errors.append("initial_owner_projection_binding_mismatch")

    instruction = packet.get("instruction", {})
    observations = run.get("instruction_observations", [])
    if not any(isinstance(item, dict)
               and item.get("path") == instruction.get("path")
               and item.get("sha256") == instruction.get("sha256")
               for item in observations):
        errors.append("instruction_binding_not_observed")

    if packet.get("connector_transport_authorized") is not False:
        errors.append("connector_transport_not_forbidden")
    if packet.get("transport_events") != []:
        errors.append("packet_transport_not_empty")
    if precondition.get("provider_transport_observed") is not False:
        errors.append("provider_transport_observed")
    if precondition.get("transport_events") != []:
        errors.append("precondition_transport_not_empty")

    requests = [{"files_before": {
        item.get("path", ""): item for item in observations if isinstance(item, dict)}}]
    try:
        observed = observer.evaluate(
            packet.get("case"), events, requests, packet.get("transport_events"),
            initial_owner_projection=initial,
            expected_owner_projection_sha256=expected_initial)
    except (KeyError, TypeError, ValueError) as error:
        observed = {"classification": "FAIL", "errors": [
            f"exception_{type(error).__name__}"]}
    if observed.get("classification") != PASS:
        errors.extend(f"observer_{item}" for item in observed.get("errors", []))

    projection, completion_index = completion_projection(run, errors)
    if arm == "treatment":
        if packet.get("completion_owner_projection") != projection:
            errors.append("treatment_completion_projection_mismatch")
        if packet.get("expected_completion_owner_projection_sha256") != fingerprint(projection):
            errors.append("treatment_completion_digest_mismatch")
        if packet.get("stop_when_completion_projection_observed") is not True:
            errors.append("treatment_completion_stop_not_required")
    elif arm == "baseline":
        if "completion_owner_projection" in packet:
            errors.append("baseline_contains_treatment_projection")
    else:
        errors.append("invalid_arm")

    consumer = run.get("consumer")
    if not isinstance(consumer, dict) or consumer.get("run_id") != run_id:
        errors.append("invalid_consumer_receipt")
    elif consumer.get("authorizes_landing") is not False:
        errors.append("consumer_claims_landing_authority")
    if run.get("remaining_disposable_paths") != []:
        errors.append("teardown_residue")

    barrier = 0
    if completion_index is not None:
        barrier = sum(isinstance(event, dict) and isinstance(event.get("request"), dict)
                      for event in events[completion_index + 1:])
    return {
        "schema": 1,
        "run_id": run_id,
        "arm": arm,
        "case": packet.get("case"),
        "hard_gate": PASS if not errors else "FAIL",
        "hard_errors": sorted(set(errors)),
        "barriers": {manifest.get("primary_barrier"): barrier},
        "completion_event_index": completion_index,
        "owner_events_observed": len(events),
        "owner_requests_observed": sum(
            isinstance(event, dict) and isinstance(event.get("request"), dict)
            for event in events),
        "refusals_observed": sum(
            isinstance(event, dict) and event.get("status") == "refused"
            for event in events),
        "evidence_sha256": evidence_sha256,
        "observer_sha256": manifest.get("observer_sha256"),
        "normalizer_sha256": manifest.get("normalizer_sha256"),
        "authorizes_landing": False,
    }


def replay(raw_bundle, manifest, expected_manifest_sha256, observer_path,
           normalizer_path=None):
    errors = []
    normalizer_path = Path(normalizer_path or __file__).resolve()
    observer_path = Path(observer_path).resolve()
    manifest_sha256 = fingerprint(manifest) if isinstance(manifest, dict) else None
    if manifest_sha256 != expected_manifest_sha256:
        errors.append("manifest_digest_mismatch")
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        errors.append("invalid_manifest")
        manifest = {}
    if file_sha256(observer_path) != manifest.get("observer_sha256"):
        errors.append("observer_digest_mismatch")
    if file_sha256(normalizer_path) != manifest.get("normalizer_sha256"):
        errors.append("normalizer_digest_mismatch")

    declarations = manifest.get("runs")
    runs = raw_bundle.get("runs") if isinstance(raw_bundle, dict) else None
    if not isinstance(declarations, list) or not isinstance(runs, list):
        errors.append("invalid_run_collections")
        declarations, runs = [], []
    declared = {}
    for item in declarations:
        if not isinstance(item, dict) or not isinstance(item.get("run_id"), str):
            errors.append("invalid_manifest_run")
            continue
        run_id = item["run_id"]
        if run_id in declared:
            errors.append(f"duplicate_manifest_run_id_{run_id}")
        declared[run_id] = item
    raw_ids = [run.get("run_id") for run in runs if isinstance(run, dict)]
    if len(raw_ids) != len(set(raw_ids)):
        errors.append("duplicate_raw_run_id")
    if set(raw_ids) != set(declared) or len(raw_ids) != len(declared):
        errors.append("run_set_mismatch")

    observer = load_observer(observer_path)
    receipts = []
    for run in runs:
        if not isinstance(run, dict) or run.get("run_id") not in declared:
            continue
        receipts.append(normalize_run(
            run, declared[run["run_id"]], manifest, observer))
    errors.extend(
        f"{receipt['run_id']}_{error}"
        for receipt in receipts for error in receipt["hard_errors"])
    arms = {arm: [receipt for receipt in receipts if receipt["arm"] == arm]
            for arm in ("baseline", "treatment")}
    return {
        "schema": 1,
        "classification": PASS if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "experiment_id": manifest.get("experiment_id"),
        "manifest_sha256": expected_manifest_sha256,
        **arms,
        "raw_bundle_sha256": fingerprint(raw_bundle),
        "observer_sha256": manifest.get("observer_sha256"),
        "normalizer_sha256": manifest.get("normalizer_sha256"),
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 5:
        raise SystemExit(
            "usage: replay_pclass.py RAW.json MANIFEST.json EXPECTED_MANIFEST_SHA256 OBSERVER.py")
    try:
        raw_bundle = json.loads(Path(argv[1]).read_text())
        manifest = json.loads(Path(argv[2]).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read replay evidence: {type(error).__name__}") from error
    receipt = replay(raw_bundle, manifest, argv[3], argv[4])
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["classification"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
