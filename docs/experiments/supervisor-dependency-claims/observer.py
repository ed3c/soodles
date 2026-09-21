"""Frozen subprocess observer for supervisor-bound dependency selection."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


OPS = "ed3c/ops-reconciliation-copilot"
OPS_HEAD = "e3c530340aa8d8070206b0a893b9a9aef5e462d0"
OPS_TREE = "f0a2032ef3f4f1195a8deaf35175b94e211607c3"
OPS_BASE = "24a56d18661630b0dba97dcb0b057dce07b0ab32"
OPS_RUN = 35217009263
SOODLES = "ed3c/soodles"
UP_ISSUE = 113
UP_PR = 114
UP_HEAD = "35e4da6df2dfbb9f00d578b2d0a3f868c1c26d0f"
UP_TREE = "09c8f86a818a47c18880468e265bcb92b2e7b73e"
UP_BASE = "b7dd55ab1074d28afe83dae3a469fc5e6f5ad36d"
UP_MERGE = "bea629a5be6017326e35d60e0a3fd7d6b19301de"
UP_RUN = 35543883941


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passed(name):
    return {"name": name, "status": "completed", "conclusion": "success"}


def selected_dependency():
    return {
        "repository": SOODLES, "issue": UP_ISSUE, "pr": UP_PR,
        "base_ref": "main", "base_head": UP_BASE,
        "candidate_head": UP_HEAD, "tree": UP_TREE, "revision": UP_MERGE,
        "run_id": UP_RUN, "run_attempt": 1,
        "workflow_path": ".github/workflows/runtime.yml",
        "jobs": {"runtime-evidence": ["Canonical acceptance on the exact candidate head"]},
    }


def fixture(identity):
    consumer = {"full_name": OPS}
    claim = {
        "repository": OPS, "issue": 23, "pr": 22, "head": OPS_HEAD,
        "tree": OPS_TREE, "base_head": OPS_BASE, "run_id": OPS_RUN,
        "run_attempt": 1, "worktree": "research-jev-foundation-23",
        "verifier_sha256": identity, "dependencies": [selected_dependency()],
    }
    common = ["Run python scripts/verify_runtime.py", "Run python scripts/verify_owner.py",
              "Run python scripts/verify_browser.py", "Run python scripts/verify_mapping.py"]
    consumer_jobs = [
        {"id": 1, "name": "runtime", "run_id": OPS_RUN, "head_sha": OPS_HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in common]},
        {"id": 2, "name": "postgres", "run_id": OPS_RUN, "head_sha": OPS_HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in [*common[:2],
                   "Run python scripts/verify_postgres.py", *common[2:]]]},
    ]
    producer = {"full_name": SOODLES}
    snapshot = {
        "pr": {"number": 22, "html_url": f"https://github.com/{OPS}/pull/22",
               "body": f"Refs {OPS}#23",
               "head": {"repo": consumer, "sha": OPS_HEAD,
                        "ref": claim["worktree"]},
               "base": {"repo": consumer, "sha": OPS_BASE, "ref": "main"},
               "merged": False, "state": "open", "draft": False,
               "mergeable": True},
        "issue": {"number": 23, "html_url": f"https://github.com/{OPS}/issues/23",
                  "state": "open"},
        "run": {"id": OPS_RUN, "run_attempt": 1, "repository": consumer,
                "head_repository": consumer, "head_sha": OPS_HEAD,
                "event": "pull_request", "path": ".github/workflows/runtime.yml",
                "status": "completed", "conclusion": "success"},
        "commit": {"sha": OPS_HEAD, "tree": {"sha": OPS_TREE}},
        "jobs": {"total_count": 2, "jobs": consumer_jobs},
        "branch": {"name": "main", "commit": {"sha": OPS_BASE}},
        "dependency_0_issue": {
            "url": f"https://api.github.com/repos/{SOODLES}/issues/{UP_ISSUE}",
            "html_url": f"https://github.com/{SOODLES}/issues/{UP_ISSUE}",
            "number": UP_ISSUE, "state": "closed", "state_reason": "completed",
            "closed_at": "2026-09-20T23:14:44Z"},
        "dependency_0_pr": {
            "number": UP_PR, "html_url": f"https://github.com/{SOODLES}/pull/{UP_PR}",
            "state": "closed", "merged": True,
            "merged_at": "2026-09-20T23:13:00Z", "merge_commit_sha": UP_MERGE,
            "head": {"repo": producer, "sha": UP_HEAD},
            "base": {"repo": producer, "sha": UP_BASE, "ref": "main"}},
        "dependency_0_commit": {
            "sha": UP_MERGE, "tree": {"sha": UP_TREE},
            "parents": [{"sha": UP_BASE}, {"sha": UP_HEAD}]},
        "dependency_0_branch": {"name": "main", "commit": {"sha": UP_MERGE}},
        "dependency_0_ancestry": {
            "status": "identical", "base_commit": {"sha": UP_MERGE},
            "merge_base_commit": {"sha": UP_MERGE},
            "head_commit": {"sha": UP_MERGE}, "total_commits": 0,
            "commits": []},
        "dependency_0_run": {
            "id": UP_RUN, "run_attempt": 1, "repository": producer,
            "head_repository": producer, "head_sha": UP_HEAD,
            "event": "pull_request", "path": ".github/workflows/runtime.yml",
            "status": "completed", "conclusion": "success"},
        "dependency_0_jobs": {"total_count": 1, "jobs": [{
            "id": 106166274151, "name": "runtime-evidence", "run_id": UP_RUN,
            "head_sha": UP_HEAD, "status": "completed", "conclusion": "success",
            "steps": [passed("Canonical acceptance on the exact candidate head")]}]},
    }
    return claim, snapshot


def invoke(source, *args):
    argv = [sys.executable, "-B", str(Path(source) / "soodles.py"), *map(str, args)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    try:
        output = json.loads(result.stdout)
    except ValueError:
        output = None
    return {"argv": argv, "exit": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "output": output}


def evaluate(report):
    failures = []
    rows = report["records"]

    def check(condition, reason):
        if not condition:
            failures.append(reason)

    dynamic = rows["dynamic"]
    independent = rows["independent"]
    if report["arm"] == "baseline":
        check(dynamic["exit"] != 0
              and (dynamic["output"] or {}).get("invalid", {}).get("field") == "claim.fields",
              "baseline:dynamic_claim_not_supported")
        check(independent["exit"] == 0, "baseline:independent_claim")
        classification = "RED" if not failures else "FAIL"
    else:
        check(dynamic["exit"] == 0, "dynamic:exit")
        nxt = (dynamic["output"] or {}).get("next") or {}
        requests = nxt.get("requests", {})
        expected = {f"dependency_0_{kind}" for kind in
                    ("issue", "pr", "commit", "branch", "ancestry", "run", "jobs")}
        check(nxt.get("owner") == "GitHub" and nxt.get("operation") == "advance",
              "dynamic:owner")
        check({key for key in requests if key.startswith("dependency_")} == expected,
              "dynamic:requests")
        check(all(key in requests and f"/repos/{SOODLES}/" in requests[key]["url"]
                  for key in expected),
              "dynamic:producer")
        check(independent["exit"] == 0
              and not any(key.startswith("dependency_") for key in
                          ((independent["output"] or {}).get("next") or {}).get("requests", {})),
              "independent:no_invented_edge")
        expected_refusals = {
            "malformed": "claim.dependencies[0].repository",
            "wrong_revision": "dependency[0].commit.sha",
            "missing_result": "dependency[0].pr",
        }
        for name, field in expected_refusals.items():
            row = rows[name]
            check(row["exit"] != 0
                  and (row["output"] or {}).get("invalid", {}).get("field") == field,
                  name + ":refusal")
            check(not Path(row["checkpoint"]).exists(), name + ":no_checkpoint")
        classification = "VERIFIED" if not failures else "FAIL"
    return {"classification": classification, "failures": failures}


def sensitivity(report):
    if report["arm"] == "baseline":
        return []
    plants = []
    mutations = [
        ("dynamic_refused", lambda r: r["records"]["dynamic"].update(exit=1)),
        ("wrong_revision_accepted", lambda r: r["records"]["wrong_revision"].update(exit=0)),
        ("missing_request", lambda r: r["records"]["dynamic"]["output"]["next"]["requests"].pop(
            "dependency_0_commit")),
    ]
    for name, mutate in mutations:
        planted = copy.deepcopy(report)
        mutate(planted)
        plants.append({"plant": name,
                       "rejected": evaluate(planted)["classification"] != "VERIFIED"})
    return plants


def observe(source, arm):
    source = Path(source).resolve()
    records = {}
    with tempfile.TemporaryDirectory(prefix="supervisor-dependency-claims-") as folder:
        root = Path(folder)
        identity = (invoke(source, "landing", "identity")["output"] or {}).get(
            "verifier_sha256", "0" * 64)
        claim, legal = fixture(identity)
        variants = {"dynamic": (claim, legal)}
        independent = {key: value for key, value in claim.items() if key != "dependencies"}
        variants["independent"] = (independent, legal)
        malformed = copy.deepcopy(claim)
        malformed["dependencies"][0]["repository"] = "not-a-repository"
        variants["malformed"] = (malformed, legal)
        wrong = copy.deepcopy(legal)
        wrong["dependency_0_commit"]["sha"] = UP_HEAD
        variants["wrong_revision"] = (claim, wrong)
        missing = {key: value for key, value in legal.items()
                   if key != "dependency_0_pr"}
        variants["missing_result"] = (claim, missing)
        for name, (selected_claim, readback) in variants.items():
            cf = root / f"{name}-claim.json"
            rf = root / f"{name}-readback.json"
            cp = root / f"{name}-checkpoint.json"
            cf.write_text(json.dumps(selected_claim))
            rf.write_text(json.dumps(readback))
            row = invoke(source, "landing", "start", cf, rf, cp)
            row.update(checkpoint=str(cp), readback=str(rf))
            records[name] = row
    report = {"schema": 1, "arm": arm, "source": str(source),
              "observer_sha256": digest(__file__),
              "task_sha256": digest(Path(__file__).with_name("task.md")),
              "records": records, "authorizes_landing": False}
    report["evaluation"] = evaluate(report)
    report["sensitivity"] = sensitivity(report)
    return report


def main():
    report = observe(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"evaluation": report["evaluation"],
                      "sensitivity": report["sensitivity"]}))
    sensitive = all(item["rejected"] for item in report["sensitivity"])
    return 0 if report["evaluation"]["classification"] in {"RED", "VERIFIED"} and sensitive else 1


if __name__ == "__main__":
    raise SystemExit(main())
