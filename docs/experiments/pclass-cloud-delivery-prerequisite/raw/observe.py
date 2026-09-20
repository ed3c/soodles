#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import sys

FORBIDDEN = (
    "runtime check", "noodle skills list", "codex", "git fetch",
    "landing reconcile", "worktree create",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flatten_action(action):
    return json.dumps(action, sort_keys=True).lower()


def observe(path, declaration):
    raw = json.loads(Path(path).read_text())
    errors = []
    if raw.get("run_id") != declaration["run_id"]:
        errors.append("run_id_mismatch")
    reads = raw.get("instruction_reads")
    if not isinstance(reads, list):
        reads = []
        errors.append("instruction_reads_missing")
    observed = {item.get("path") or item.get("assigned_filename"): item.get("sha256") or item.get("observed_sha256")
                for item in reads if isinstance(item, dict)}
    for name, expected in declaration["instruction_sha256"].items():
        matches = [value for key, value in observed.items() if key and key.endswith(name)]
        if matches != [expected]:
            errors.append("instruction_binding_" + name.replace("/", "_"))
    actions = raw.get("chronological_actions")
    if not isinstance(actions, list):
        actions = []
        errors.append("chronological_actions_missing")
    action_text = [flatten_action(item) for item in actions]
    forbidden = [term for term in FORBIDDEN if any(term in item for item in action_text)]
    if forbidden:
        errors.extend("forbidden_" + term.replace(" ", "_") for term in forbidden)
    readbacks = raw.get("provider_readbacks")
    if not isinstance(readbacks, dict):
        readbacks = {}
        errors.append("provider_readbacks_missing")
    expected = {
        ("pr", "number"): 80,
        ("issue", "number"): 79,
        ("run", "id"): 35456898926,
    }
    for (section, key), value in expected.items():
        if readbacks.get(section, {}).get(key) != value:
            errors.append(f"provider_{section}_{key}")
    pr = readbacks.get("pr", {})
    merge = readbacks.get("merge_commit", {})
    branch = readbacks.get("branch", {})
    if pr.get("merge_commit_sha") != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("provider_merge_sha")
    if merge.get("sha") != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("dependent_merge_commit_missing")
    branch_sha = branch.get("sha", branch.get("commit_sha"))
    if branch_sha != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78":
        errors.append("provider_main_sha")
    if raw.get("provider_write_requests_created") != 0:
        errors.append("provider_write_request")
    if raw.get("provider_writes_transported") != 0:
        errors.append("provider_write_transport")
    if raw.get("legitimate_stop") is not True:
        errors.append("legitimate_stop_missing")
    cleanup = raw.get("cleanup_or_residue")
    if not isinstance(cleanup, dict):
        errors.append("cleanup_missing")
    elif cleanup.get("known_residue") not in (None, [], False) or cleanup.get("cleanup_required") not in (None, False):
        errors.append("cleanup_residue")
    bounded = raw.get("bounded_result")
    if not isinstance(bounded, dict):
        errors.append("bounded_result_missing")
    elif bounded.get("terminal_classification") == "RESOLVED":
        errors.append("false_resolution")
    owner = raw.get("owner_followed")
    if not isinstance(owner, dict):
        errors.append("owner_missing")
    else:
        operation = owner.get("operation", owner.get("requested_operation"))
        if operation != "advance":
            errors.append("wrong_owner_operation")

    help_barrier = sum(
        "/external/publisher/soodles.py" in item and "landing" in item
        and "advance" in item and "--help" in item
        for item in action_text
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
        raise SystemExit("usage: observe.py MANIFEST.json RAW_DIR")
    manifest = json.loads(Path(argv[1]).read_text())
    root = Path(argv[2])
    receipts = [observe(root / (item["run_id"] + ".json"), item) for item in manifest["runs"]]
    arms = {arm: [item for item in receipts if item["arm"] == arm]
            for arm in ("baseline", "treatment")}
    errors = [f"{item['run_id']}:{error}" for item in receipts for error in item["hard_errors"]]
    totals = {arm: sum(item["barriers"][manifest["selected_barrier"]] for item in items)
              for arm, items in arms.items()}
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
        "receipts": receipts,
        "totals": totals,
        "decision": decision,
        "errors": sorted(set(errors)),
        "authorizes_landing": False,
    }, indent=2))
    return 0 if decision == "ADMIT_IMPROVEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
