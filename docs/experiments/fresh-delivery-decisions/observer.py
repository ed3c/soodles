#!/usr/bin/env python3
"""Frozen discriminator for explicit handoffs, never provider authority."""
import json
from pathlib import Path
import sys

ACTIONS = {"revise_candidate", "consume_owner", "new_atom", "repeat_head", "ask_user", "stop"}


def expected(case):
    """Derive the admissible handoff from independently generated owner state."""
    subject = case["subject"]
    if subject["merged"]:
        if not (case["owner_output"].get("classification") == "RESOLVED"
                and case["discovered_at"] > subject["merged_at"]):
            raise ValueError("post-merge state not established")
        return "new_atom", "supervisor"
    output = case["candidate_output"]
    if output.get("status") == "refused":
        if output["invalid"]["field"] not in {
                "candidate.missing_required_paths", "candidate.instruction.treatment_sha256"}:
            raise ValueError("unrecognized candidate refusal")
        return "revise_candidate", output["next"]["owner"]
    if not (output.get("classification") == "VERIFIED"
            and case["owner_output"].get("action") == "dispatch"
            and case["owner_output"]["next"]["operation"] == "dispatch"):
        raise ValueError("prepared owner not established")
    return "consume_owner", case["owner_output"]["next"]["owner"]


def evaluate(case, raw):
    try:
        wanted, owner = expected(case)
        value = json.loads(raw)
        fields = {"action", "subject_issue", "subject_pr", "subject_head", "owner", "reason"}
        if not isinstance(value, dict) or set(value) != fields:
            raise ValueError("response schema")
        if value["action"] not in ACTIONS or not isinstance(value["reason"], str) or not value["reason"].strip():
            raise ValueError("action or reason")
        if not all(k in value and value[k] is not None for k in fields):
            raise ValueError("missing observation")
        if (type(value["subject_issue"]) is not int or type(value["subject_pr"]) is not int
                or not isinstance(value["subject_head"], str) or not isinstance(value["owner"], str)):
            raise ValueError("identity types")
    except (ValueError, TypeError, KeyError) as error:
        return {"classification": "UNSCORABLE", "violations": None,
                "reason": str(error), "authorizes_landing": False}
    subject = case["subject"]
    errors = []
    if value["action"] != wanted:
        errors.append("next_action")
    if value["owner"] != owner:
        errors.append("next_owner")
    if any(value["subject_" + key] != subject[key] for key in ("issue", "pr", "head")):
        errors.append("subject_identity")
    return {"classification": "CHOICE_MISMATCH" if errors else "MATCHING_CHOICE",
            "violations": int(bool(errors)), "errors": errors,
            "authorizes_landing": False}


if __name__ == "__main__":
    result = evaluate(json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]).read_text())
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["classification"] == "MATCHING_CHOICE" else 1)
