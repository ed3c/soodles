#!/usr/bin/env python3
"""Decide one manifest-bound P-class comparison without landing authority."""
import hashlib
import json
import sys


TARGETS = {"improvement", "nonregression"}
ARMS = {"baseline", "treatment"}
PASS = "PASS"
CONTROL_STATES = {"PASS", "FAIL"}


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def valid_digest(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def required(mapping, key, expected_type, errors, prefix=""):
    if not isinstance(mapping, dict) or key not in mapping:
        errors.append(f"missing_{prefix}{key}")
        return None
    value = mapping[key]
    if not isinstance(value, expected_type):
        errors.append(f"invalid_{prefix}{key}")
        return None
    return value


def validate_manifest(manifest, expected_sha256, errors):
    if not isinstance(manifest, dict):
        errors.append("invalid_manifest")
        return {}, {}, set()
    actual_sha256 = fingerprint(manifest)
    if not valid_digest(expected_sha256) or actual_sha256 != expected_sha256:
        errors.append("manifest_digest_mismatch")
    if manifest.get("schema") != 2:
        errors.append("invalid_manifest_schema")
    for key in ("experiment_id", "primary_barrier", "observer_sha256",
                "normalizer_sha256", "decider_sha256", "gates_sha256"):
        value = required(manifest, key, str, errors, "manifest_")
        if value == "":
            errors.append(f"invalid_manifest_{key}")
    if manifest.get("admission_target") not in TARGETS:
        errors.append("invalid_manifest_admission_target")
    for key in ("observer_sha256", "normalizer_sha256", "decider_sha256",
                "gates_sha256"):
        if not valid_digest(manifest.get(key)):
            errors.append(f"invalid_manifest_{key}")

    runs_per_arm = manifest.get("runs_per_arm")
    if type(runs_per_arm) is not int or runs_per_arm < 1:
        errors.append("invalid_manifest_runs_per_arm")

    required_controls = required(
        manifest, "required_controls", list, errors, "manifest_") or []
    control_set = set()
    for name in required_controls:
        if not isinstance(name, str) or not name:
            errors.append("invalid_manifest_required_control")
        elif name in control_set:
            errors.append(f"duplicate_manifest_control_{name}")
        else:
            control_set.add(name)
    if not control_set:
        errors.append("missing_manifest_required_controls")

    declarations = required(manifest, "runs", list, errors, "manifest_") or []
    declared = {}
    arm_counts = {arm: 0 for arm in ARMS}
    case_counts = {arm: {} for arm in ARMS}
    for index, item in enumerate(declarations):
        prefix = f"manifest_run_{index}_"
        if not isinstance(item, dict):
            errors.append(f"invalid_{prefix}receipt")
            continue
        run_id = required(item, "run_id", str, errors, prefix)
        arm = required(item, "arm", str, errors, prefix)
        case = required(item, "case", str, errors, prefix)
        evidence = required(item, "evidence_sha256", str, errors, prefix)
        if run_id == "":
            errors.append(f"invalid_{prefix}run_id")
        elif run_id in declared:
            errors.append(f"duplicate_manifest_run_id_{run_id}")
        else:
            declared[run_id] = item
        if arm not in ARMS:
            errors.append(f"invalid_{prefix}arm")
        else:
            arm_counts[arm] += 1
            if isinstance(case, str) and case:
                case_counts[arm][case] = case_counts[arm].get(case, 0) + 1
        if case == "":
            errors.append(f"invalid_{prefix}case")
        if not valid_digest(evidence):
            errors.append(f"invalid_{prefix}evidence_sha256")
    for arm, count in arm_counts.items():
        if count != runs_per_arm:
            errors.append(f"manifest_{arm}_exposure_mismatch")
    if case_counts["baseline"] != case_counts["treatment"]:
        errors.append("manifest_case_exposure_mismatch")
    return manifest, declared, control_set


def validate_packet_binding(packet, manifest, expected_manifest_sha256, errors):
    if packet.get("schema") != 2:
        errors.append("invalid_schema")
    for key in ("experiment_id", "admission_target", "primary_barrier"):
        if packet.get(key) != manifest.get(key):
            errors.append(f"{key}_manifest_mismatch")
    if packet.get("manifest_sha256") != expected_manifest_sha256:
        errors.append("packet_manifest_digest_mismatch")


def arm_total(packet, arm, barrier, manifest, declared, errors):
    receipts = required(packet, arm, list, errors) or []
    total = 0
    observed_ids = []
    seen = set()
    for index, receipt in enumerate(receipts):
        prefix = f"{arm}_{index}_"
        if not isinstance(receipt, dict):
            errors.append(f"invalid_{prefix}receipt")
            continue
        run_id = required(receipt, "run_id", str, errors, prefix)
        if run_id in seen:
            errors.append(f"duplicate_run_id_{run_id}")
        elif run_id:
            seen.add(run_id)
            observed_ids.append(run_id)
        expected = declared.get(run_id)
        if expected is None:
            errors.append(f"unexpected_run_id_{run_id}")
        else:
            for key in ("arm", "case", "evidence_sha256"):
                if receipt.get(key) != expected.get(key):
                    errors.append(f"{run_id}_{key}_mismatch")
            if expected.get("arm") != arm:
                errors.append(f"{run_id}_arm_container_mismatch")
        for key in ("observer_sha256", "normalizer_sha256"):
            if receipt.get(key) != manifest.get(key):
                errors.append(f"{run_id}_{key}_mismatch")
        if receipt.get("authorizes_landing", False) is not False:
            errors.append(f"{run_id}_claims_landing_authority")
        if receipt.get("hard_gate") != PASS:
            errors.append(f"{prefix}hard_gate_not_pass")
        barriers = receipt.get("barriers")
        if not isinstance(barriers, dict) or barrier not in barriers:
            errors.append(f"missing_{prefix}primary_barrier")
            continue
        count = barriers[barrier]
        if type(count) is not int or count < 0:
            errors.append(f"invalid_{prefix}primary_barrier")
            continue
        total += count
    return total, observed_ids


def controls_pass(packet, required_controls, errors):
    controls = required(packet, "controls", list, errors) or []
    names = []
    seen = set()
    for index, control in enumerate(controls):
        prefix = f"control_{index}_"
        if not isinstance(control, dict):
            errors.append(f"invalid_{prefix}receipt")
            continue
        name = required(control, "name", str, errors, prefix)
        expected = required(control, "expected", str, errors, prefix)
        observed = required(control, "observed", str, errors, prefix)
        if name in seen:
            errors.append(f"duplicate_control_{name}")
        elif name:
            seen.add(name)
            names.append(name)
        if expected not in CONTROL_STATES:
            errors.append(f"invalid_{prefix}expected")
        if observed not in CONTROL_STATES:
            errors.append(f"invalid_{prefix}observed")
        if expected != observed:
            errors.append(f"{prefix}mismatch")
    if set(names) != required_controls or len(names) != len(required_controls):
        errors.append("control_set_mismatch")


def external_gate(packet, key, errors):
    gate = required(packet, key, dict, errors)
    if not isinstance(gate, dict) or gate.get("classification") != PASS:
        errors.append(f"{key}_not_pass")


def evaluate(packet, manifest, expected_manifest_sha256):
    errors = []
    if not isinstance(packet, dict):
        packet = {}
        errors.append("invalid_packet")
    manifest, declared, required_controls = validate_manifest(
        manifest, expected_manifest_sha256, errors)
    validate_packet_binding(packet, manifest, expected_manifest_sha256, errors)
    barrier = packet.get("primary_barrier")
    baseline, baseline_ids = arm_total(
        packet, "baseline", barrier, manifest, declared, errors)
    treatment, treatment_ids = arm_total(
        packet, "treatment", barrier, manifest, declared, errors)
    actual_ids = baseline_ids + treatment_ids
    for run_id in set(actual_ids):
        if actual_ids.count(run_id) > 1:
            errors.append(f"duplicate_run_id_{run_id}")
    if set(actual_ids) != set(declared) or len(actual_ids) != len(declared):
        errors.append("run_set_mismatch")
    controls_pass(packet, required_controls, errors)
    external_gate(packet, "causal_delta", errors)
    external_gate(packet, "independent_audit", errors)
    telemetry = packet.get("telemetry")
    if not isinstance(telemetry, dict):
        errors.append("invalid_telemetry")
        telemetry = None

    target = packet.get("admission_target")
    if not errors and target == "improvement":
        if treatment < baseline:
            decision = "ADMIT_IMPROVEMENT"
        else:
            errors.append("primary_barrier_not_improved")
            decision = "REJECT"
    elif not errors and target == "nonregression":
        if treatment <= baseline:
            decision = "ADMIT_NONREGRESSION"
        else:
            errors.append("primary_barrier_regressed")
            decision = "REJECT"
    else:
        decision = "REJECT"

    return {
        "schema": 2,
        "decision": decision,
        "experiment_id": packet.get("experiment_id"),
        "manifest_sha256": expected_manifest_sha256,
        "admission_target": target,
        "primary_barrier": barrier,
        "baseline_total": baseline,
        "treatment_total": treatment,
        "observed_run_count": len(actual_ids),
        "declared_run_count": len(declared),
        "hard_gate_errors": sorted(set(errors)),
        "telemetry": telemetry,
        "telemetry_authority": "report_only",
        "input_sha256": fingerprint(packet),
        "authorizes_landing": False,
    }


def main(argv):
    raise SystemExit(
        "direct comparison input is disabled; use replay_pclass.py so receipts "
        "and controls are derived from manifest-bound raw evidence")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
