#!/usr/bin/env python3
"""Internal exploration-only decision; baseline zero is not nonregression."""


def evaluate(receipts, controls, errors, manifest):
    errors = list(errors)
    if len(receipts) != 3 or any(r.get("arm") != "baseline" for r in receipts):
        errors.append("incomplete_exploration")
    if [c["name"] for c in controls] != manifest["required_controls"] or any(
            c["predicate"] != "PASS" for c in controls):
        errors.append("failed_planted_control")
    if any(r["hard_gate"] != "PASS" or r["barriers"] is None for r in receipts):
        errors.append("failed_hard_gate")
    totals = None
    selected = None
    if errors:
        disposition = "INCONCLUSIVE"
    else:
        order = manifest["selection"]["barrier_order"]
        totals = {name: sum(r["barriers"][name] for r in receipts) for name in order}
        selected = next((name for name in order if totals[name] > 0), None)
        # A positive pilot needs a separately frozen experiment. This bounded
        # entry neither creates a treatment nor admits confirmation evidence.
        disposition = "NO_QUALIFIED_BARRIER" if selected is None else "INCONCLUSIVE"
    return {"disposition": disposition, "barrier_totals": totals,
            "selected_barrier": selected, "errors": sorted(set(errors)),
            "confirmation_authorized": False, "treatment_retained": False,
            "authorizes_landing": False}


if __name__ == "__main__":
    raise SystemExit("use the manifest-bound replay_pclass.py entry")
