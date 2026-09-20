#!/usr/bin/env python3
"""Schema-tolerant correction of observe.py for the same immutable run evidence.

Correction scope is deliberately narrow:
- inspect only executable command fields for forbidden local commands;
- accept documented JSON-equivalent empty/zero write counts;
- accept documented boolean wrappers for legitimate_stop;
- accept semantically identical owner/readback field aliases emitted by runs;
- preserve all experiment identities, hard gates, barrier matching, and decision rules.
"""
import hashlib
import json
from pathlib import Path
import sys


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flatten(value):
    return json.dumps(value, sort_keys=True).lower()


def command_text(action):
    if not isinstance(action, dict):
        return ""
    values = []
    for key in ("command", "argv"):
        value = action.get(key)
        if value is not None:
            values.append(flatten(value))
    attempt = action.get("attempt")
    if isinstance(attempt, str) and (
        attempt.startswith("python3 ")
        or attempt.startswith("codex ")
        or attempt.startswith("git ")
        or attempt.startswith("noodle ")
        or attempt.startswith("runtime ")
    ):
        values.append(attempt.lower())
    return " ".join(values)


def is_empty_count(value):
    return value in (0, None, False, [], {})


def is_true(value):
    if value is True:
        return True
    if isinstance(value, dict):
        return value.get("value") is True or value.get("stopped") is True
    return False


def section(readbacks, *names):
    for name in names:
        value = readbacks.get(name)
        if isinstance(value, dict):
            return value
    return {}


def observe(path, declaration):
    raw = json.loads(Path(path).read_text())
    errors = []
    if raw.get("run_id") != declaration["run_id"]:
        errors.append("run_id_mismatch")

    reads = raw.get("instruction_reads")
    if not isinstance(reads, list):
        reads = []
        errors.append("instruction_reads_missing")
    observed = {
        item.get("path") or item.get("assigned_filename"): item.get("sha256") or item.get("observed_sha256")
        for item in reads if isinstance(item, dict)
    }
    for name, expected in declaration["instruction_sha256"].items():
        matches = [value for key, value in observed.items() if key and key.endswith(name)]
        if matches != [expected]:
            errors.append("instruction_binding_" + name.replace("/", "_"))

    actions = raw.get("chronological_actions")
    if not isinstance(actions, list):
        actions = []
        errors.append("chronological_actions_missing")
    commands = [command_text(item) for item in actions]
    forbidden_patterns = {
        "runtime_check": "runtime check",
        "noodle_skills_list": "noodle skills list",
        "codex_cli": "codex ",
        "git_fetch": "git fetch",
        "landing_reconcile": "landing reconcile",
        "worktree_create": "worktree create",
    }
    for name, pattern in forbidden_patterns.items():
        if any(pattern in item for item in commands):
            errors.append("forbidden_" + name)

    readbacks = raw.get("provider_readbacks")
    if not isinstance(readbacks, dict):
        readbacks = {}
        errors.append("provider_readbacks_missing")
    pr = section(readbacks, "pr")
    issue = section(readbacks, "issue")
    run = section(readbacks, "run", "runtime_run")
    merge = section(readbacks, "merge_commit")
    branch = section(readbacks, "branch", "main_branch")
    if pr.get("number") != 80:
        errors.append("provider_pr_number")
    if issue.get("number") != 79:
        errors.append("provider_issue_number")
    if run.get("id") != 35456898926:
        errors.append("provider_run_id")
    if pr.get("merge_commit_sha") != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("provider_merge_sha")
    if merge.get("sha") != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("dependent_merge_commit_missing")
    branch_sha = branch.get("sha") or branch.get("commit_sha") or branch.get("head_sha")
    if branch_sha != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("provider_main_sha")

    if not is_empty_count(raw.get("provider_write_requests_created")):
        errors.append("provider_write_request")
    if not is_empty_count(raw.get("provider_writes_transported")):
        errors.append("provider_write_transport")
    if not is_true(raw.get("legitimate_stop")):
        errors.append("legitimate_stop_missing")

    cleanup = raw.get("cleanup_or_residue")
    if not isinstance(cleanup, dict):
        errors.append("cleanup_missing")
    else:
        residue = cleanup.get("known_residue", cleanup.get("residue"))
        if isinstance(residue, str) and residue.lower().startswith("none"):
            residue = None
        if residue not in (None, [], False) or cleanup.get("cleanup_required") not in (None, False):
            errors.append("cleanup_residue")

    bounded = raw.get("bounded_result")
    if not isinstance(bounded, dict):
        errors.append("bounded_result_missing")
    else:
        claimed = (
            bounded.get("terminal_classification") == "RESOLVED"
            or bounded.get("classification") == "RESOLVED"
            or bounded.get("resolution_claimed") is True
            or bounded.get("terminal_resolution_claimed") is True
            or bounded.get("terminal_classification_claimed") is True
        )
        if claimed:
            errors.append("false_resolution")

    owner = raw.get("owner_followed")
    if not isinstance(owner, dict):
        errors.append("owner_missing")
    else:
        operation = owner.get("operation") or owner.get("requested_operation") or owner.get("provider_operation")
        if operation != "advance":
            errors.append("wrong_owner_operation")

    help_barrier = sum(
        "/external/publisher/soodles.py" in item
        and "landing" in item and "advance" in item and "--help" in item
        for item in commands
    )
    return {
        "run_id": declaration["run_id"],
        "arm": declaration["arm"],
        "hard_gate": "PASS" if not errors else "FAIL",
        "hard_errors": sorted(set(errors)),
        "barriers": {"avoidable_help_after_owner_guidance": help_barrier},
        "raw_sha256": sha256(path),
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: observe-corrected.py MANIFEST.json RAW_DIR")
    manifest = json.loads(Path(argv[1]).read_text())
    root = Path(argv[2])
    receipts = [observe(root / (item["run_id"] + ".json"), item) for item in manifest["runs"]]
    arms = {arm: [item for item in receipts if item["arm"] == arm] for arm in ("baseline", "treatment")}
    errors = [f"{item['run_id']}:{error}" for item in receipts for error in item["hard_errors"]]
    totals = {
        arm: sum(item["barriers"][manifest["selected_barrier"]] for item in items)
        for arm, items in arms.items()
    }
    if any(len(arms[arm]) != 3 for arm in arms):
        errors.append("exposure_mismatch")
    decision = "REJECT"
    if not errors and totals["treatment"] < totals["baseline"]:
        decision = "ADMIT_IMPROVEMENT"
    elif not errors and totals["treatment"] == totals["baseline"] == 0:
        decision = "SCOPED_NONREGRESSION"
    elif not errors:
        errors.append("barrier_not_improved")
    print(json.dumps({
        "schema": 1,
        "experiment": manifest["experiment"],
        "manifest_sha256": sha256(argv[1]),
        "observer_sha256": sha256(argv[0]),
        "correction_of": manifest["observer_sha256"],
        "receipts": receipts,
        "totals": totals,
        "decision": decision,
        "errors": sorted(set(errors)),
        "authorizes_landing": False,
    }, indent=2))
    return 0 if decision == "ADMIT_IMPROVEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
