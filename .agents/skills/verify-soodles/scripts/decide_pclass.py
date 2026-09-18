#!/usr/bin/env python3
"""Decide one frozen P-class comparison without granting landing authority."""
import hashlib
import json
from pathlib import Path
import sys


TARGETS = {"improvement", "nonregression"}
PASS = "PASS"


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def required(mapping, key, expected_type, errors, prefix):
    if not isinstance(mapping, dict) or key not in mapping:
        errors.append(f"missing_{prefix}{key}")
        return None
    value = mapping[key]
    if not isinstance(value, expected_type):
        errors.append(f"invalid_{prefix}{key}")
        return None
    return value


def arm_total(packet, arm, barrier, errors):
    receipts = required(packet, arm, list, errors, "")
    if not receipts:
        errors.append(f"missing_{arm}_receipts")
        return None
    total = 0
    for index, receipt in enumerate(receipts):
        prefix = f"{arm}_{index}_"
        if not isinstance(receipt, dict):
            errors.append(f"invalid_{prefix}receipt")
            continue
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
    return total


def controls_pass(packet, errors):
    controls = required(packet, "controls", list, errors, "")
    if not controls:
        errors.append("missing_sensitivity_controls")
        return
    names = set()
    for index, control in enumerate(controls):
        prefix = f"control_{index}_"
        if not isinstance(control, dict):
            errors.append(f"invalid_{prefix}receipt")
            continue
        name = required(control, "name", str, errors, prefix)
        expected = required(control, "expected", str, errors, prefix)
        observed = required(control, "observed", str, errors, prefix)
        if name in names:
            errors.append(f"duplicate_control_{name}")
        elif name:
            names.add(name)
        if expected not in {"PASS", "FAIL", "UNKNOWN"}:
            errors.append(f"invalid_{prefix}expected")
        if observed not in {"PASS", "FAIL", "UNKNOWN"}:
            errors.append(f"invalid_{prefix}observed")
        if expected != observed:
            errors.append(f"{prefix}mismatch")


def external_gate(packet, key, errors):
    gate = required(packet, key, dict, errors, "")
    if not isinstance(gate, dict) or gate.get("classification") != PASS:
        errors.append(f"{key}_not_pass")


def evaluate(packet):
    errors = []
    if not isinstance(packet, dict):
        packet = {}
        errors.append("invalid_packet")
    if packet.get("schema") != 1:
        errors.append("invalid_schema")
    target = packet.get("admission_target")
    if target not in TARGETS:
        errors.append("invalid_admission_target")
    barrier = required(packet, "primary_barrier", str, errors, "")
    if barrier == "":
        errors.append("invalid_primary_barrier")
    baseline = arm_total(packet, "baseline", barrier, errors)
    treatment = arm_total(packet, "treatment", barrier, errors)
    controls_pass(packet, errors)
    external_gate(packet, "causal_delta", errors)
    external_gate(packet, "independent_audit", errors)
    telemetry = packet.get("telemetry")
    if not isinstance(telemetry, dict):
        errors.append("invalid_telemetry")
        telemetry = None

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
        "schema": 1,
        "decision": decision,
        "admission_target": target,
        "primary_barrier": barrier,
        "baseline_total": baseline,
        "treatment_total": treatment,
        "hard_gate_errors": sorted(set(errors)),
        "telemetry": telemetry,
        "telemetry_authority": "report_only",
        "input_sha256": fingerprint(packet),
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: decide_pclass.py COMPARISON.json")
    try:
        packet = json.loads(Path(argv[1]).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read comparison packet: {type(error).__name__}") from error
    receipt = evaluate(packet)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["decision"].startswith("ADMIT_") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
