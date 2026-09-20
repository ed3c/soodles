#!/usr/bin/env python3
"""Deterministic observer for the bounded P0/P1 receipts."""
import json
from pathlib import Path
import sys


def evaluate(receipt):
    errors = []
    fixture = receipt.get("fixture", {})
    delivery = receipt.get("delivery", {})
    if fixture.get("historical_identities_isolated") is not True:
        errors.append("historical_identities_not_isolated")
    if fixture.get("original_fixture_unchanged") is not True:
        errors.append("original_fixture_changed")
    if fixture.get("target_cases_passed") != 4:
        errors.append("target_cases_incomplete")
    if fixture.get("live_controls_passed") != 2:
        errors.append("live_controls_incomplete")
    if fixture.get("observer_exit") != 0:
        errors.append("observer_failed")
    prs = delivery.get("pull_requests")
    if not isinstance(prs, list) or len(prs) != 1:
        errors.append("delivery_pr_count")
    attempts = delivery.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        errors.append("delivery_attempts_missing")
    elif any(item.get("failed") and item.get("rerun_same_head") for item in attempts):
        errors.append("failed_head_rerun")
    if delivery.get("all_required_evidence_present") is not True:
        errors.append("required_evidence_missing")
    if delivery.get("exact_bytes_verified") is not True:
        errors.append("exact_bytes_unverified")
    if delivery.get("terminal_runtime_green") is not True:
        errors.append("terminal_runtime_red")
    return {
        "classification": "PASS" if not errors else "FAIL",
        "errors": errors,
        "fixture_barrier": 0 if not any(e.startswith(("historical_", "original_", "target_", "live_", "observer_")) for e in errors) else 1,
        "delivery_split_barrier": max(0, len(prs) - 1) if isinstance(prs, list) else 1,
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: observer.py RECEIPT.json")
    result = evaluate(json.loads(Path(argv[1]).read_text()))
    print(json.dumps(result, indent=2))
    return 0 if result["classification"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
