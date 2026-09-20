"""Frozen subprocess observer for one bounded cross-repository route."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


OPS = "ed3c/ops-reconciliation-copilot"
HEAD = "e3c530340aa8d8070206b0a893b9a9aef5e462d0"
TREE = "f0a2032ef3f4f1195a8deaf35175b94e211607c3"
BASE = "24a56d18661630b0dba97dcb0b057dce07b0ab32"
RUN = 35217009263


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_fixture(source, identity, draft=False):
    repo = {"full_name": OPS}
    claim = {"repository": OPS, "issue": 21, "pr": 22, "head": HEAD,
             "tree": TREE, "base_head": BASE, "run_id": RUN, "run_attempt": 1,
             "worktree": "research-jev-foundation-21", "verifier_sha256": identity}
    def passed(name):
        return {"name": name, "status": "completed", "conclusion": "success"}
    common = ["Run python scripts/verify_runtime.py", "Run python scripts/verify_owner.py",
              "Run python scripts/verify_browser.py", "Run python scripts/verify_mapping.py"]
    jobs = [
        {"id": 1, "name": "runtime", "run_id": RUN, "head_sha": HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in common]},
        {"id": 2, "name": "postgres", "run_id": RUN, "head_sha": HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [passed(name) for name in [*common[:2], "Run python scripts/verify_postgres.py", *common[2:]]]},
    ]
    snapshot = {
        "pr": {"number": 22, "html_url": f"https://github.com/{OPS}/pull/22",
               "body": f"Refs {OPS}#21", "head": {"repo": repo, "sha": HEAD, "ref": claim["worktree"]},
               "base": {"repo": repo, "sha": BASE, "ref": "main"},
               "merged": False, "state": "open", "draft": draft, "mergeable": True},
        "issue": {"number": 21, "html_url": f"https://github.com/{OPS}/issues/21", "state": "open"},
        "run": {"id": RUN, "run_attempt": 1, "repository": repo, "head_repository": repo,
                "head_sha": HEAD, "event": "pull_request", "path": ".github/workflows/runtime.yml",
                "status": "completed", "conclusion": "success"},
        "commit": {"sha": HEAD, "tree": {"sha": TREE}},
        "jobs": {"total_count": 2, "jobs": jobs},
        "branch": {"name": "main", "commit": {"sha": BASE}},
    }
    return claim, snapshot


def invoke(source, *args):
    result = subprocess.run(
        [sys.executable, "-B", str(Path(source) / "soodles.py"), *map(str, args)],
        capture_output=True, text=True, timeout=30)
    try:
        output = json.loads(result.stdout)
    except ValueError:
        output = None
    return {"argv": [sys.executable, "-B", str(Path(source) / "soodles.py"), *map(str, args)],
            "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "output": output}


def evaluate(report):
    failures = []
    rows = report["records"]
    def check(condition, reason):
        if not condition:
            failures.append(reason)
    baseline = report["arm"] == "baseline"
    if baseline:
        check(rows["legal"]["exit"] != 0, "baseline:legal_must_expose_barrier")
        check((rows["legal"]["output"] or {}).get("invalid", {}).get("field") == "claim.repository",
              "baseline:barrier_field")
    else:
        legal = rows["legal"]
        check(legal["exit"] == 0, "legal:exit")
        nxt = (legal["output"] or {}).get("next") or {}
        check(nxt.get("owner") == "GitHub" and nxt.get("operation") == "advance",
              "legal:owner_route")
        check(all(f"/repos/{OPS}/" in req.get("url", "")
                  for req in nxt.get("requests", {}).values()), "legal:repository_requests")
        check((nxt.get("argv") or [None])[-2:] == [legal["checkpoint"], legal["readback"]],
              "legal:bound_argv")
        check(rows["draft"]["exit"] != 0 and
              rows["draft"]["output"]["invalid"]["field"] == "pr.state", "draft:refusal")
        check(rows["missing_step"]["exit"] != 0 and
              rows["missing_step"]["output"]["invalid"]["field"] == "job.acceptance",
              "missing_step:refusal")
        check(rows["unsupported"]["exit"] != 0 and
              rows["unsupported"]["output"]["invalid"]["field"] == "claim.repository",
              "unsupported:refusal")
        check(all(not Path(rows[name]["checkpoint"]).exists()
                  for name in ("draft", "missing_step", "unsupported")), "refusal:no_checkpoint")
    return {"classification": "RED" if baseline and not failures else
            "VERIFIED" if not failures else "FAIL", "failures": failures}


def sensitivity(report):
    if report["arm"] == "baseline":
        return []
    plants = []
    mutations = [
        ("wrong_repo_request", lambda r: r["records"]["legal"]["output"]["next"]["requests"]["pr"].update(
            url="https://api.github.com/repos/ed3c/soodles/pulls/22")),
        ("missing_argv", lambda r: r["records"]["legal"]["output"]["next"].pop("argv")),
        ("draft_accepted", lambda r: r["records"]["draft"].update(exit=0)),
        ("missing_step_accepted", lambda r: r["records"]["missing_step"].update(exit=0)),
        ("unsupported_accepted", lambda r: r["records"]["unsupported"].update(exit=0)),
    ]
    for name, mutate in mutations:
        candidate = copy.deepcopy(report)
        mutate(candidate)
        plants.append({"plant": name, "rejected": evaluate(candidate)["classification"] != "VERIFIED"})
    return plants


def observe(source, arm):
    source = Path(source).resolve()
    records = {}
    with tempfile.TemporaryDirectory(prefix="cross-repository-route-") as folder:
        root = Path(folder)
        identity = (invoke(source, "landing", "identity")["output"] or {}).get("verifier_sha256", "0"*64)
        if arm == "baseline":
            # Baseline has no target fixture module; use the candidate's frozen
            # input producer supplied next to this observer.
            fixture_source = Path(__file__).resolve().parents[3]
        else:
            fixture_source = source
        claim, snapshot = load_fixture(fixture_source, identity)
        variants = {
            "legal": (claim, snapshot),
            "draft": (claim, load_fixture(fixture_source, identity, True)[1]),
            "missing_step": (claim, copy.deepcopy(snapshot)),
            "unsupported": ({**claim, "repository": "ed3c/unregistered"}, snapshot),
        }
        variants["missing_step"][1]["jobs"]["jobs"][1]["steps"] = [
            step for step in variants["missing_step"][1]["jobs"]["jobs"][1]["steps"]
            if step["name"] != "Run python scripts/verify_postgres.py"]
        for name, (case_claim, readback) in variants.items():
            cf, rf, cp = root/f"{name}-claim.json", root/f"{name}-readback.json", root/f"{name}-checkpoint.json"
            cf.write_text(json.dumps(case_claim)); rf.write_text(json.dumps(readback))
            row = invoke(source, "landing", "start", cf, rf, cp)
            row.update(checkpoint=str(cp), readback=str(rf))
            records[name] = row
    report = {"schema": 1, "arm": arm, "source": str(source),
              "observer_sha256": digest(__file__), "task_sha256": digest(Path(__file__).with_name("task.md")),
              "records": records, "authorizes_landing": False}
    report["evaluation"] = evaluate(report)
    report["sensitivity"] = sensitivity(report)
    return report


def main():
    report = observe(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"evaluation": report["evaluation"], "sensitivity": report["sensitivity"]}))
    sensitive = all(item["rejected"] for item in report["sensitivity"])
    return 0 if report["evaluation"]["classification"] in {"RED", "VERIFIED"} and sensitive else 1


if __name__ == "__main__":
    raise SystemExit(main())
