"""Frozen subprocess observer for one executable cross-repository dependency."""
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
UP_ISSUE = 111
UP_PR = 112
UP_HEAD = "498f384337609fc2a76c1cb293aa100e5d639b0d"
UP_TREE = "85fb13afdf603baccf1ee7644b209e40dfd25d88"
UP_BASE = "db5dd0c7e46ba5c8fe5270907b229688326fc8f4"
UP_MERGE = "b7dd55ab1074d28afe83dae3a469fc5e6f5ad36d"
UP_RUN = 35541786068


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def passed(name):
    return {"name": name, "status": "completed", "conclusion": "success"}


def fixture(identity):
    repo = {"full_name": OPS}
    claim = {"repository": OPS, "issue": 21, "pr": 22, "head": OPS_HEAD,
             "tree": OPS_TREE, "base_head": OPS_BASE, "run_id": OPS_RUN,
             "run_attempt": 1, "worktree": "research-jev-foundation-21",
             "verifier_sha256": identity}
    common = ["Run python scripts/verify_runtime.py", "Run python scripts/verify_owner.py",
              "Run python scripts/verify_browser.py", "Run python scripts/verify_mapping.py"]
    jobs = [
        {"id": 1, "name": "runtime", "run_id": OPS_RUN, "head_sha": OPS_HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in common]},
        {"id": 2, "name": "postgres", "run_id": OPS_RUN, "head_sha": OPS_HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in [*common[:2],
                   "Run python scripts/verify_postgres.py", *common[2:]]]},
    ]
    upstream_repo = {"full_name": SOODLES}
    snapshot = {
        "pr": {"number": 22, "html_url": f"https://github.com/{OPS}/pull/22",
               "body": f"Refs {OPS}#21",
               "head": {"repo": repo, "sha": OPS_HEAD, "ref": claim["worktree"]},
               "base": {"repo": repo, "sha": OPS_BASE, "ref": "main"},
               "merged": False, "state": "open", "draft": False, "mergeable": True},
        "issue": {"number": 21, "html_url": f"https://github.com/{OPS}/issues/21",
                  "state": "open"},
        "run": {"id": OPS_RUN, "run_attempt": 1, "repository": repo,
                "head_repository": repo, "head_sha": OPS_HEAD,
                "event": "pull_request", "path": ".github/workflows/runtime.yml",
                "status": "completed", "conclusion": "success"},
        "commit": {"sha": OPS_HEAD, "tree": {"sha": OPS_TREE}},
        "jobs": {"total_count": 2, "jobs": jobs},
        "branch": {"name": "main", "commit": {"sha": OPS_BASE}},
        "dependency_issue": {
            "url": f"https://api.github.com/repos/{SOODLES}/issues/{UP_ISSUE}",
            "html_url": f"https://github.com/{SOODLES}/issues/{UP_ISSUE}",
            "number": UP_ISSUE, "state": "closed", "state_reason": "completed",
            "closed_at": "2026-09-20T22:30:59Z"},
        "dependency_pr": {
            "number": UP_PR, "html_url": f"https://github.com/{SOODLES}/pull/{UP_PR}",
            "state": "closed", "merged": True, "merged_at": "2026-09-20T22:30:59Z",
            "merge_commit_sha": UP_MERGE,
            "head": {"repo": upstream_repo, "sha": UP_HEAD},
            "base": {"repo": upstream_repo, "sha": UP_BASE, "ref": "main"}},
        "dependency_commit": {
            "sha": UP_MERGE, "tree": {"sha": UP_TREE},
            "parents": [{"sha": UP_BASE}, {"sha": UP_HEAD}]},
        "dependency_branch": {"name": "main", "commit": {"sha": UP_MERGE}},
        "dependency_ancestry": {
            "status": "identical", "base_commit": {"sha": UP_MERGE},
            "merge_base_commit": {"sha": UP_MERGE},
            "head_commit": {"sha": UP_MERGE}, "total_commits": 0, "commits": []},
        "dependency_run": {
            "id": UP_RUN, "run_attempt": 1, "repository": upstream_repo,
            "head_repository": upstream_repo, "head_sha": UP_HEAD,
            "event": "pull_request", "path": ".github/workflows/runtime.yml",
            "status": "completed", "conclusion": "success"},
        "dependency_jobs": {"total_count": 1, "jobs": [{
            "id": 106160654219, "name": "runtime-evidence", "run_id": UP_RUN,
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
    if report["arm"] == "baseline":
        check(rows["legal"]["exit"] == 0, "baseline:legal")
        check(all(rows[name]["exit"] == 0 for name in
                  ("closure_only", "wrong_repo", "wrong_revision", "stale", "missing_step")),
              "baseline:dependency_barrier_absent")
        classification = "RED" if not failures else "FAIL"
    else:
        check(rows["legal"]["exit"] == 0, "legal:exit")
        nxt = (rows["legal"]["output"] or {}).get("next") or {}
        requests = nxt.get("requests", {})
        check(nxt.get("owner") == "GitHub" and nxt.get("operation") == "advance",
              "legal:owner")
        check(set(k for k in requests if k.startswith("dependency_")) == {
            "dependency_issue", "dependency_pr", "dependency_commit",
            "dependency_branch", "dependency_ancestry", "dependency_run",
            "dependency_jobs"}, "legal:dependency_requests")
        check(all((f"/repos/{SOODLES}/" in item["url"] if key.startswith("dependency_")
                   else f"/repos/{OPS}/" in item["url"])
                  for key, item in requests.items()), "legal:request_repository")
        expected = {
            "closure_only": "dependency.pr",
            "wrong_repo": "dependency.pr.repository",
            "wrong_revision": "dependency.commit.sha",
            "stale": "dependency.ancestry.status",
            "missing_step": "dependency.job.acceptance",
        }
        for name, field in expected.items():
            row = rows[name]
            check(row["exit"] != 0 and (row["output"] or {}).get("invalid", {}).get("field") == field,
                  name + ":refusal")
            check(not Path(row["checkpoint"]).exists(), name + ":no_checkpoint")
        classification = "VERIFIED" if not failures else "FAIL"
    return {"classification": classification, "failures": failures}


def sensitivity(report):
    if report["arm"] == "baseline":
        return []
    plants = []
    mutations = [
        ("closure_accepted", lambda r: r["records"]["closure_only"].update(exit=0)),
        ("wrong_repo_accepted", lambda r: r["records"]["wrong_repo"].update(exit=0)),
        ("wrong_revision_accepted", lambda r: r["records"]["wrong_revision"].update(exit=0)),
        ("stale_accepted", lambda r: r["records"]["stale"].update(exit=0)),
        ("missing_dependency_request", lambda r: r["records"]["legal"]["output"]["next"]["requests"].pop("dependency_commit")),
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
    with tempfile.TemporaryDirectory(prefix="cross-repository-dependency-") as folder:
        root = Path(folder)
        identity = (invoke(source, "landing", "identity")["output"] or {}).get(
            "verifier_sha256", "0" * 64)
        claim, legal = fixture(identity)
        variants = {"legal": legal}
        closure = {key: copy.deepcopy(value) for key, value in legal.items()
                   if not key.startswith("dependency_") or key == "dependency_issue"}
        variants["closure_only"] = closure
        variants["wrong_repo"] = copy.deepcopy(legal)
        variants["wrong_repo"]["dependency_pr"]["head"]["repo"]["full_name"] = OPS
        variants["wrong_revision"] = copy.deepcopy(legal)
        variants["wrong_revision"]["dependency_commit"]["sha"] = UP_HEAD
        variants["stale"] = copy.deepcopy(legal)
        variants["stale"]["dependency_ancestry"]["status"] = "behind"
        variants["missing_step"] = copy.deepcopy(legal)
        variants["missing_step"]["dependency_jobs"]["jobs"][0]["steps"] = []
        for name, readback in variants.items():
            cf, rf, cp = root/f"{name}-claim.json", root/f"{name}-readback.json", root/f"{name}-checkpoint.json"
            cf.write_text(json.dumps(claim)); rf.write_text(json.dumps(readback))
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
