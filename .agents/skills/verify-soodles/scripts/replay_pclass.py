#!/usr/bin/env python3
"""Replay and decide fixed P-class evidence under an externally pinned manifest."""
import base64
import copy
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


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
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


def normalize_recovery_run(run, declared, manifest, observer):
    errors = []
    run_id = run.get("run_id")
    arm = run.get("arm")
    packet = run.get("packet") if isinstance(run.get("packet"), dict) else {}
    evidence_sha256 = fingerprint(run)
    for key, actual in (("run_id", run_id), ("arm", arm),
                        ("case", packet.get("case")),
                        ("evidence_sha256", evidence_sha256)):
        if actual != declared.get(key):
            errors.append(f"{key}_manifest_mismatch")
    if packet.get("run_id") != run_id or packet.get("arm") != arm:
        errors.append("run_identity_internal_mismatch")
    consumer = run.get("consumer") if isinstance(run.get("consumer"), dict) else {}
    if consumer.get("session_id") != declared.get("consumer_session_id"):
        errors.append("consumer_session_manifest_mismatch")
    if declared.get("phase") == "confirmation":
        if packet.get("selection_sha256") != manifest.get("selection_sha256"):
            errors.append("selection_binding_mismatch")
    try:
        observed = observer.evaluate(run, manifest, declared)
    except (KeyError, TypeError, ValueError) as error:
        observed = {
            "classification": "FAIL",
            "errors": [f"exception_{type(error).__name__}"],
            "barriers": {},
        }
    if observed.get("classification") != PASS:
        errors.extend(f"observer_{item}" for item in observed.get("errors", []))
    barrier_name = manifest.get("primary_barrier")
    barriers = observed.get("barriers") if isinstance(observed.get("barriers"), dict) else {}
    if barrier_name not in barriers:
        errors.append("primary_barrier_not_observed")
    return {
        "schema": 1,
        "feature": manifest.get("feature"),
        "run_id": run_id,
        "arm": arm,
        "case": packet.get("case"),
        "phase": declared.get("phase"),
        "hard_gate": PASS if not errors else "FAIL",
        "hard_errors": sorted(set(errors)),
        "barriers": barriers,
        "operations_observed": observed.get("operations_observed"),
        "evidence_sha256": evidence_sha256,
        "observer_sha256": manifest.get("observer_sha256"),
        "normalizer_sha256": manifest.get("normalizer_sha256"),
        "authorizes_landing": False,
    }


def normalize_run(run, declared, manifest, observer):
    if manifest.get("feature") == "noodle_admission_recovery":
        return normalize_recovery_run(run, declared, manifest, observer)
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
        if completion_index is not None and events[completion_index + 1:]:
            errors.append("owner_operation_after_completion")
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


def failed_receipt(errors, manifest, expected_manifest_sha256, raw_bundle=None):
    return {
        "schema": 2,
        "classification": "FAIL",
        "errors": sorted(set(errors)),
        "experiment_id": manifest.get("experiment_id") if isinstance(manifest, dict) else None,
        "manifest_sha256": expected_manifest_sha256,
        "raw_bundle_sha256": fingerprint(raw_bundle) if raw_bundle is not None else None,
        "authorizes_landing": False,
    }


def incomplete_receipt(errors, manifest, expected_manifest_sha256, raw_bundle=None):
    return {
        "schema": 2,
        "classification": "INCONCLUSIVE",
        "disposition": "INCONCLUSIVE",
        "errors": sorted(set(errors)),
        "experiment_id": manifest.get("experiment_id") if isinstance(manifest, dict) else None,
        "manifest_sha256": expected_manifest_sha256,
        "raw_bundle_sha256": fingerprint(raw_bundle) if raw_bundle is not None else None,
        "authorizes_landing": False,
    }


def validate_gates(gates, manifest, errors):
    keys = {"schema", "experiment_id", "causal_delta", "independent_audit",
            "telemetry"}
    if not isinstance(gates, dict) or set(gates) != keys:
        errors.append("invalid_gates_schema")
        return
    if gates.get("schema") != 1:
        errors.append("invalid_gates_schema")
    if gates.get("experiment_id") != manifest.get("experiment_id"):
        errors.append("gates_experiment_id_mismatch")
    if fingerprint(gates) != manifest.get("gates_sha256"):
        errors.append("gates_digest_mismatch")
    for key in ("causal_delta", "independent_audit"):
        value = gates.get(key)
        if not isinstance(value, dict) or set(value) != {"classification"}:
            errors.append(f"invalid_{key}_gate")
        elif value.get("classification") != PASS:
            errors.append(f"{key}_not_pass")
    if not isinstance(gates.get("telemetry"), dict):
        errors.append("invalid_telemetry")


def validate_control_specs(manifest, errors):
    specs = manifest.get("control_specs")
    required = manifest.get("required_controls")
    if not isinstance(specs, list) or not isinstance(required, list):
        errors.append("invalid_control_specs")
        return
    names = []
    mutations = {"premature_stop", "wrong_operation", "stale_completion_digest",
                 "missing_transport_evidence", "request_after_completion", "none",
                 "stale_recovery_binding", "wrong_recovery_subject",
                 "missing_recovery_completion", "false_recovery_cleanup",
                 "changed_recovery_canonical", "recovery_provider_transport",
                 "duplicate_recovery_continuation", "wrong_recovery_argv",
                 "failed_recovery_observer", "recovery_instruction_mismatch",
                 "recovery_exposure_mismatch", "legal_declared_uncertainty"}
    for index, control in enumerate(specs):
        if not isinstance(control, dict):
            errors.append(f"invalid_control_spec_{index}")
            continue
        name = control.get("name")
        names.append(name)
        if not isinstance(name, str) or not name:
            errors.append(f"invalid_control_spec_{index}_name")
        if not isinstance(control.get("source_run_id"), str):
            errors.append(f"invalid_control_spec_{index}_source")
        if control.get("mutation") not in mutations:
            errors.append(f"invalid_control_spec_{index}_mutation")
        if control.get("expected_hard_gate") not in {PASS, "FAIL"}:
            errors.append(f"invalid_control_spec_{index}_hard_gate")
        expected_errors = control.get("expected_errors")
        if (not isinstance(expected_errors, list)
                or not all(isinstance(item, str) for item in expected_errors)):
            errors.append(f"invalid_control_spec_{index}_errors")
        barrier = control.get("expected_barrier")
        if type(barrier) is not int or barrier < 0:
            errors.append(f"invalid_control_spec_{index}_barrier")
        if (control.get("mutation") == "request_after_completion"
                and not isinstance(control.get("donor_run_id"), str)):
            errors.append(f"invalid_control_spec_{index}_donor")
    if names != required or len(names) != len(set(names)):
        errors.append("control_spec_set_mismatch")


def mutate_control(source, control, raw_by_id):
    mutated = copy.deepcopy(source)
    mutation = control.get("mutation")
    if mutation == "premature_stop":
        mutated["owner_events"] = mutated["owner_events"][:1]
    elif mutation == "wrong_operation":
        mutated["owner_events"][1]["owner"] = "landing.dispatch"
    elif mutation == "stale_completion_digest":
        mutated["packet"]["expected_completion_owner_projection_sha256"] = "f" * 64
    elif mutation == "missing_transport_evidence":
        mutated["packet"].pop("transport_events", None)
    elif mutation == "request_after_completion":
        donor = raw_by_id.get(control.get("donor_run_id"))
        if not isinstance(donor, dict) or not donor.get("owner_events"):
            raise ValueError("invalid_control_donor")
        mutated["owner_events"].append(copy.deepcopy(donor["owner_events"][-1]))
    elif mutation == "stale_recovery_binding":
        action = next(item for item in mutated["operations"]
                      if item.get("kind") == "owner_action")
        process = json.loads(base64.b64decode(action["process_receipt_b64"]))
        process["bound_projection_sha256"] = "f" * 64
        action["process_receipt_b64"] = base64.b64encode(json.dumps(
            process, sort_keys=True, separators=(",", ":")).encode()).decode()
    elif mutation == "wrong_recovery_subject":
        mutated["packet"]["subject"]["source_revision"] = "f" * 40
    elif mutation == "missing_recovery_completion":
        mutated["operations"] = mutated["operations"][:-1]
    elif mutation == "false_recovery_cleanup":
        mutated["evidence"]["remaining_processes"] = [123]
    elif mutation == "changed_recovery_canonical":
        path = next(iter(mutated["evidence"]["canonical_after"]))
        mutated["evidence"]["canonical_after"][path] = "Y2hhbmdlZA=="
    elif mutation == "recovery_provider_transport":
        mutated["evidence"]["provider_transport_events"] = [{"kind": "connector"}]
    elif mutation == "duplicate_recovery_continuation":
        action = next(item for item in mutated["operations"]
                      if item.get("kind") == "owner_action")
        mutated["operations"].insert(-1, copy.deepcopy(action))
    elif mutation == "wrong_recovery_argv":
        action = next(item for item in mutated["operations"]
                      if item.get("kind") == "owner_action")
        process = json.loads(base64.b64decode(action["process_receipt_b64"]))
        process["argv"] = ["/tmp/noodle", "admission", "inspect"]
        action["process_receipt_b64"] = base64.b64encode(json.dumps(
            process, sort_keys=True, separators=(",", ":")).encode()).decode()
    elif mutation == "failed_recovery_observer":
        mutated["evidence"]["external_observer_receipt_b64"] = "e30="
    elif mutation == "recovery_instruction_mismatch":
        mutated["packet"]["instruction"]["bytes_b64"] = "dGFtcGVyZWQ="
    elif mutation == "recovery_exposure_mismatch":
        mutated["packet"]["exposure"]["budget"] = 999
    elif mutation == "legal_declared_uncertainty":
        inspect = copy.deepcopy(mutated["operations"][0])
        mutated["operations"][0]["opens_uncertainty"] = "owner-state-race"
        inspect["resolves_uncertainty"] = "owner-state-race"
        mutated["operations"].insert(1, inspect)
    elif mutation == "none":
        pass
    else:
        raise ValueError("unknown_control_mutation")
    return mutated


def replay_controls(raw_by_id, declared, manifest, observer):
    receipts = []
    errors = []
    barrier_name = manifest.get("primary_barrier")
    for control in manifest.get("control_specs", []):
        name = control.get("name")
        source = raw_by_id.get(control.get("source_run_id"))
        if not isinstance(source, dict):
            errors.append(f"control_{name}_source_missing")
            continue
        try:
            mutated = mutate_control(source, control, raw_by_id)
        except (IndexError, KeyError, TypeError, ValueError) as error:
            errors.append(f"control_{name}_{error}")
            continue
        declaration = copy.deepcopy(declared[source["run_id"]])
        declaration["evidence_sha256"] = fingerprint(mutated)
        observed = normalize_run(mutated, declaration, manifest, observer)
        expected_errors = sorted(control.get("expected_errors", []))
        expected_gate = control.get("expected_hard_gate")
        expected_barrier = control.get("expected_barrier")
        actual_barrier = observed["barriers"].get(barrier_name)
        matched = (observed["hard_gate"] == expected_gate
                   and observed["hard_errors"] == expected_errors
                   and actual_barrier == expected_barrier)
        if not matched:
            errors.append(f"control_{name}_predicate_mismatch")
        receipts.append({
            "name": name,
            "expected": expected_gate,
            "observed": observed["hard_gate"],
            "expected_errors": expected_errors,
            "observed_errors": observed["hard_errors"],
            "expected_barrier": expected_barrier,
            "observed_barrier": actual_barrier,
            "predicate": PASS if matched else "FAIL",
        })
    if [item.get("name") for item in manifest.get("control_specs", [])] != manifest.get("required_controls"):
        errors.append("control_spec_set_mismatch")
    return receipts, errors


def bind_run_collection(declarations, runs, label, errors):
    prefix = f"{label}_" if label else ""
    if not isinstance(declarations, list) or not isinstance(runs, list):
        errors.append(f"invalid_{prefix}run_collections")
        return {}, []
    declared = {}
    for item in declarations:
        if not isinstance(item, dict) or not isinstance(item.get("run_id"), str):
            errors.append(f"invalid_{prefix}manifest_run")
            continue
        run_id = item["run_id"]
        if run_id in declared:
            errors.append(f"duplicate_{prefix}manifest_run_id_{run_id}")
        declared[run_id] = item
    raw_ids = [run.get("run_id") for run in runs if isinstance(run, dict)]
    if len(raw_ids) != len(set(raw_ids)):
        errors.append(f"duplicate_{prefix}raw_run_id")
    if set(raw_ids) != set(declared) or len(raw_ids) != len(declared):
        errors.append(f"{prefix}run_set_mismatch")
    return declared, runs


def replay_recovery_pilot(raw_bundle, manifest, observer):
    errors = []
    count = manifest.get("pilot_run_count")
    if type(count) is not int or count < 1:
        errors.append("invalid_pilot_run_count")
    declared, runs = bind_run_collection(
        manifest.get("pilot_runs"),
        raw_bundle.get("pilot_runs") if isinstance(raw_bundle, dict) else None,
        "pilot", errors)
    if len(declared) != count:
        errors.append("pilot_run_count_mismatch")
    for item in declared.values():
        if item.get("arm") != "baseline" or item.get("phase") != "exploration":
            errors.append(f"pilot_{item.get('run_id')}_invalid_phase_or_arm")
    if errors:
        return None, errors
    receipts = [normalize_recovery_run(run, declared[run["run_id"]], manifest, observer)
                for run in runs]
    for receipt in receipts:
        if receipt["hard_gate"] != PASS:
            errors.extend(f"pilot_{receipt['run_id']}_{error}"
                          for error in receipt["hard_errors"])
    if errors:
        return None, errors
    order = manifest.get("barrier_order", [])
    totals = {name: sum(receipt["barriers"].get(name, 0)
                        for receipt in receipts) for name in order}
    selected = next((name for name in order if totals[name] > 0), None)
    selection = {
        "schema": 1,
        "pilot_runs": [{"run_id": receipt["run_id"],
                         "evidence_sha256": receipt["evidence_sha256"]}
                        for receipt in receipts],
        "barrier_order": order,
        "barrier_totals": totals,
        "selected_barrier": selected,
    }
    if fingerprint(selection) != manifest.get("selection_sha256"):
        errors.append("selection_digest_mismatch")
    if selected != manifest.get("selected_barrier"):
        errors.append("selected_barrier_mismatch")
    if selected is not None and selected != manifest.get("primary_barrier"):
        errors.append("primary_barrier_not_first_positive")
    return {"receipts": receipts, "selection": selection}, errors


def replay(raw_bundle, gates, manifest, expected_manifest_sha256, observer_path,
           decider_path, normalizer_path=None):
    errors = []
    normalizer_path = Path(normalizer_path or __file__).resolve()
    observer_path = Path(observer_path).resolve()
    decider_path = Path(decider_path).resolve()
    manifest_sha256 = fingerprint(manifest) if isinstance(manifest, dict) else None
    if manifest_sha256 != expected_manifest_sha256:
        errors.append("manifest_digest_mismatch")
    if not isinstance(manifest, dict) or manifest.get("schema") != 2:
        errors.append("invalid_manifest")
        manifest = {}
    for label, path in (("observer", observer_path), ("normalizer", normalizer_path),
                        ("decider", decider_path)):
        try:
            actual = file_sha256(path)
        except OSError:
            errors.append(f"{label}_unreadable")
            continue
        if actual != manifest.get(f"{label}_sha256"):
            errors.append(f"{label}_digest_mismatch")
    validate_gates(gates, manifest, errors)
    validate_control_specs(manifest, errors)

    # Analyzer bytes are never imported after a failed preflight.
    if errors:
        return failed_receipt(errors, manifest, expected_manifest_sha256, raw_bundle)

    observer = load_module("pclass_observer", observer_path)
    decider = load_module("pclass_decider", decider_path)
    pilot = None
    if manifest.get("feature") == "noodle_admission_recovery":
        pilot, pilot_errors = replay_recovery_pilot(raw_bundle, manifest, observer)
        if pilot_errors:
            return incomplete_receipt(
                pilot_errors, manifest, expected_manifest_sha256, raw_bundle)
        if pilot["selection"]["selected_barrier"] is None:
            return {
                "schema": 2,
                "classification": PASS,
                "disposition": "NO_QUALIFIED_BARRIER",
                "errors": [],
                "experiment_id": manifest.get("experiment_id"),
                "manifest_sha256": expected_manifest_sha256,
                "pilot": pilot["receipts"],
                "selection": pilot["selection"],
                "raw_bundle_sha256": fingerprint(raw_bundle),
                "authorizes_landing": False,
            }

    declarations = manifest.get("runs")
    runs = raw_bundle.get("runs") if isinstance(raw_bundle, dict) else None
    collection_label = ("confirmation"
                        if manifest.get("feature") == "noodle_admission_recovery"
                        else "")
    declared, runs = bind_run_collection(
        declarations, runs, collection_label, errors)
    if errors:
        if manifest.get("feature") == "noodle_admission_recovery":
            return incomplete_receipt(
                errors, manifest, expected_manifest_sha256, raw_bundle)
        return failed_receipt(errors, manifest, expected_manifest_sha256, raw_bundle)
    if manifest.get("feature") == "noodle_admission_recovery":
        pilot_declarations = manifest.get("pilot_runs", [])
        for key in ("run_id", "evidence_sha256", "consumer_session_id"):
            pilot_values = {item.get(key) for item in pilot_declarations
                            if isinstance(item, dict)}
            confirmation_values = {item.get(key) for item in declared.values()}
            if pilot_values & confirmation_values:
                errors.append(f"pilot_confirmation_{key}_not_distinct")
        if any(item.get("phase") != "confirmation"
               for item in declared.values()):
            errors.append("confirmation_invalid_phase")
        if errors:
            return incomplete_receipt(
                errors, manifest, expected_manifest_sha256, raw_bundle)

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
    raw_by_id = {run["run_id"]: run for run in runs if isinstance(run, dict)}
    controls, control_errors = replay_controls(raw_by_id, declared, manifest, observer)
    errors.extend(control_errors)
    comparison = {
        "schema": 2,
        "experiment_id": manifest.get("experiment_id"),
        "manifest_sha256": expected_manifest_sha256,
        "admission_target": manifest.get("admission_target"),
        "primary_barrier": manifest.get("primary_barrier"),
        **arms,
        "controls": controls,
        "causal_delta": gates.get("causal_delta"),
        "independent_audit": gates.get("independent_audit"),
        "telemetry": gates.get("telemetry"),
    }
    decision = decider.evaluate(comparison, manifest, expected_manifest_sha256)
    if not decision.get("decision", "").startswith("ADMIT_"):
        errors.append("comparison_not_admitted")
    dispositions = {
        "ADMIT_IMPROVEMENT": "IMPROVEMENT",
        "ADMIT_NONREGRESSION": "SCOPED_NONREGRESSION",
        "REJECT": "REJECTED",
    }
    return {
        "schema": 2,
        "classification": PASS if not errors else "FAIL",
        "disposition": dispositions.get(decision.get("decision"), "REJECTED"),
        "errors": sorted(set(errors)),
        "experiment_id": manifest.get("experiment_id"),
        "manifest_sha256": expected_manifest_sha256,
        **arms,
        "controls": controls,
        "comparison_sha256": fingerprint(comparison),
        "decision": decision,
        "pilot": pilot["receipts"] if pilot else None,
        "selection": pilot["selection"] if pilot else None,
        "raw_bundle_sha256": fingerprint(raw_bundle),
        "observer_sha256": manifest.get("observer_sha256"),
        "normalizer_sha256": manifest.get("normalizer_sha256"),
        "decider_sha256": manifest.get("decider_sha256"),
        "gates_sha256": manifest.get("gates_sha256"),
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 7:
        raise SystemExit(
            "usage: replay_pclass.py RAW.json GATES.json MANIFEST.json "
            "EXPECTED_MANIFEST_SHA256 OBSERVER.py DECIDER.py")
    try:
        raw_bundle = json.loads(Path(argv[1]).read_text())
        gates = json.loads(Path(argv[2]).read_text())
        manifest = json.loads(Path(argv[3]).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read replay evidence: {type(error).__name__}") from error
    receipt = replay(raw_bundle, gates, manifest, argv[4], argv[5], argv[6])
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["classification"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
