"""Independent, stdlib-only CLI continuation observer; synthetic provider only.

Usage: python continuation_observer.py SOURCE_ROOT OUTPUT_JSON
The observer never imports candidate modules. Projection absence is a contract
failure, not an Agent error. Fallback argv are explicit observer reconstruction.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture(identity):
    """Pure synthetic input factory, with no expected-outcome checks."""
    repo = {"full_name": "ed3c/soodles"}
    claim = dict(repository="ed3c/soodles", issue=1, pr=2, head="a"*40,
                 tree="b"*40, base_head="c"*40, run_id=10, run_attempt=1,
                 worktree="fixture", verifier_sha256=identity)
    snapshot = {
        "pr": dict(number=2, html_url="https://github.com/ed3c/soodles/pull/2",
                   body="Refs ed3c/soodles#1", head=dict(repo=copy.deepcopy(repo), sha="a"*40, ref="fixture"),
                   base=dict(repo=copy.deepcopy(repo), sha="c"*40, ref="main"),
                   merged=False, state="open", draft=False, mergeable=True),
        "issue": dict(number=1, html_url="https://github.com/ed3c/soodles/issues/1", state="open"),
        "run": dict(id=10, run_attempt=1, repository=copy.deepcopy(repo), head_repository=copy.deepcopy(repo),
                    head_sha="a"*40, event="pull_request", path=".github/workflows/runtime.yml",
                    status="completed", conclusion="success"),
        "commit": {"sha": "a"*40, "tree": {"sha": "b"*40}},
        "jobs": {"total_count": 1, "jobs": [dict(id=11, name="runtime-evidence", run_id=10,
                 head_sha="a"*40, status="completed", conclusion="success", steps=[dict(
                 name="Canonical acceptance on the exact candidate head", status="completed", conclusion="success")])]},
        "branch": {"name": "main", "commit": {"sha": "c"*40}},
    }
    return claim, snapshot


def output(record):
    try:
        value = json.loads(record["stdout"])
        return value if isinstance(value, dict) else {}
    except (ValueError, KeyError):
        return {}


def expected_argv(report, record, operation):
    return [report["python"], "-B", str(Path(report["source_root"])/"soodles.py"),
            "landing", operation, record["checkpoint"], record["readback"]]


def evaluate(report):
    """Evaluate raw observations; do not trust the report's cached verdicts."""
    safety, projection = [], []
    rows = {row["case"]: row for row in report["commands"]}
    def check(ok, key, bucket=safety):
        if not ok:
            bucket.append(key)
    operations = {"start": "advance", "prepare": "dispatch", "merge_offer": "advance",
                  "unknown_merge": "advance", "stale_dispatch": "advance",
                  "missing_merge_commit": "advance", "repair_merge_commit": "dispatch",
                  "close_offer": "advance", "unknown_close": "advance"}
    base = "https://api.github.com/repos/ed3c/soodles/"
    requests = {"pr": "pulls/2", "issue": "issues/1", "commit": "git/commits/"+"a"*40,
                "branch": "branches/main", "run": "actions/runs/10", "jobs": "actions/runs/10/jobs"}
    for name, operation in operations.items():
        row = rows.get(name, {})
        out = output(row)
        nxt = out.get("next") or {}
        check(nxt.get("kind") == "provider_readback" and nxt.get("operation") == operation,
              name+":route")
        check(nxt.get("owner") == "GitHub" and nxt.get("required") == ["readback"], name+":owner_required")
        for key, path in requests.items():
            check(nxt.get("requests", {}).get(key) == {"method": "GET", "url": base+path},
                  name+":required_get:"+key)
        check(nxt.get("known", {}).get("checkpoint") == row.get("checkpoint"), name+":checkpoint_binding")
        check(nxt.get("known", {}).get("readback") == row.get("readback"), name+":readback_binding", projection)
        check(nxt.get("argv") == expected_argv(report, row, operation), name+":argv", projection)
        check(out.get("classification") != "RESOLVED", name+":false_resolution")
    for name, prior in (("prepare", "start"), ("merge_offer", "prepare"),
                        ("repair_merge_commit", "missing_merge_commit"), ("close_offer", "repair_merge_commit")):
        row = rows.get(name, {})
        offered = (output(rows.get(prior, {})).get("next") or {}).get("argv")
        check(offered is not None and row.get("argv") == offered and row.get("provenance") == "emitted_argv",
              name+":verbatim_consumption", projection)
    merge = dict(action="merge", repository_full_name="ed3c/soodles", pr_number=2,
                 expected_head_sha="a"*40, merge_method="merge")
    close = dict(action="close", repository_full_name="ed3c/soodles", issue_number=1,
                 state="closed", state_reason="completed")
    for name, request, history in (("merge_offer", merge, ["merge"]), ("close_offer", close, ["merge", "close"])):
        row = rows.get(name, {})
        check(row.get("exit") == 0 and output(row).get("request") == request, name+":exact_request")
        check((row.get("state_after") or {}).get("writes_offered") == history, name+":durable_history")
    for name, row in rows.items():
        out = output(row)
        if name not in {"merge_offer", "close_offer"}:
            check("request" not in out, name+":unexpected_request")
        if name not in {"resolve", "resolved_again"}:
            check(out.get("classification") != "RESOLVED", name+":false_resolution")
    refusal_fields = {"stale_dispatch": "dispatch.status", "foreign_repository": "pr.head.repository",
                      "foreign_head": "pr.head.sha", "missing_merge_commit": "merge_commit"}
    for name in [*refusal_fields, "malformed_json", "missing_file"]:
        row = rows.get(name, {})
        check(row.get("exit", 0) != 0, name+":must_refuse")
        check(row.get("checkpoint_before") == row.get("checkpoint_after"), name+":refusal_changed_checkpoint")
        if name in refusal_fields:
            check(output(row).get("invalid", {}).get("field") == refusal_fields[name], name+":refusal_field")
    for name in ("foreign_repository", "foreign_head", "malformed_json", "missing_file", "invalidate", "direct_domain"):
        nxt = output(rows.get(name, {})).get("next") or {}
        check("argv" not in nxt and "readback" not in nxt.get("known", {}), name+":unexpected_binding")
    for name in ("start", "prepare", "unknown_merge", "repair_merge_commit", "unknown_close", "invalidate", "direct_domain"):
        check(rows.get(name, {}).get("exit") == 0, name+":exit")
    for name in ("prepare", "repair_merge_commit"):
        check(output(rows.get(name, {})).get("action") == "dispatch", name+":prepared")
    for name in ("unknown_merge", "unknown_close"):
        check(output(rows.get(name, {})).get("action") == "readback", name+":unknown_readback_only")
    check(output(rows.get("invalidate", {})).get("next", {}).get("operation") == "readmit", "invalidate:route")
    check(output(rows.get("invalidate", {})).get("next", {}).get("required") == ["claim", "readback"], "invalidate:required")
    check(output(rows.get("missing_merge_commit", {})).get("next", {}).get("requests", {}).get("merge_commit") ==
          {"method": "GET", "url": base+"git/commits/"+"d"*40}, "missing_merge_commit:dependent_get")
    for name, history in (("unknown_merge", ["merge"]), ("stale_dispatch", ["merge"]),
                          ("unknown_close", ["merge", "close"])):
        check((rows.get(name, {}).get("state_after") or {}).get("writes_offered") == history, name+":history")
    for name in ("resolve", "resolved_again"):
        row = rows.get(name, {})
        out = output(row)
        check(row.get("exit") == 0 and out.get("classification") == "RESOLVED" and
              out.get("phase") == "resolved" and out.get("next", "missing") is None, name+":terminal")
        check(out.get("provider_reconciliation", {}).get("local_reconciliation_required") is False or
              (row.get("state_after") or {}).get("provider_reconciliation", {}).get("local_reconciliation_required") is False,
              name+":cloud_scope")
    row = rows.get("resolved_again", {})
    check(row.get("checkpoint_before") == row.get("checkpoint_after"), "resolved_again:changed_checkpoint")
    check(report.get("cleanup", {}).get("removed") is True, "cleanup:residue")
    return {"safety": "PASS" if not safety else "FAIL", "safety_failures": safety,
            "projection": "PASS" if not projection else "RED", "projection_failures": projection,
            "bound_continuation_available": not projection}


def sensitivity(report):
    """Planted transcript mutations must be rejected for the exact reason."""
    # This positive evaluator control is explicitly synthetic: on a RED baseline
    # complete only the missing projection and its consumption transcript. It is
    # never evidence of a candidate effect or an Agent's behavior.
    reference = copy.deepcopy(report)
    reference_rows = {r["case"]: r for r in reference["commands"]}
    for case in ("start", "prepare", "merge_offer", "unknown_merge", "stale_dispatch",
                 "missing_merge_commit", "repair_merge_commit", "close_offer", "unknown_close"):
        row = reference_rows[case]
        out = output(row)
        out["next"]["argv"] = expected_argv(reference, row, out["next"]["operation"])
        out["next"]["known"]["readback"] = row["readback"]
        row["stdout"] = json.dumps(out)
    for case, prior in (("prepare", "start"), ("merge_offer", "prepare"),
                        ("repair_merge_commit", "missing_merge_commit"), ("close_offer", "repair_merge_commit")):
        reference_rows[case]["argv"] = output(reference_rows[prior])["next"]["argv"]
        reference_rows[case]["provenance"] = "emitted_argv"
    positive = evaluate(reference)
    accepted = positive["safety"] == "PASS" and positive["projection"] == "PASS"
    results = []
    plants = [
        ("wrong_argv", "prepare", "argv", "prepare:argv"),
        ("wrong_operation", "prepare", "operation", "prepare:route"),
        ("false_resolution", "unknown_merge", "classification", "unknown_merge:false_resolution"),
        ("duplicate_offer", "unknown_merge", "request", "unknown_merge:unexpected_request"),
        ("refusal_state_change", "stale_dispatch", "state", "stale_dispatch:refusal_changed_checkpoint"),
        ("missing_get", "prepare", "requests", "prepare:required_get:pr"),
        ("missing_dependent_get", "missing_merge_commit", "dependent", "missing_merge_commit:dependent_get"),
    ]
    for name, case, field, reason in plants:
        mutant = copy.deepcopy(reference)
        row = next(r for r in mutant["commands"] if r["case"] == case)
        out = output(row)
        if field == "argv":
            out["next"]["argv"] = expected_argv(mutant, row, "advance")
        elif field == "operation":
            out["next"]["operation"] = "advance"
        elif field == "classification":
            out["classification"] = "RESOLVED"
        elif field == "request":
            out["request"] = {"action": "merge"}
        elif field == "state":
            row["checkpoint_after"] = "planted changed bytes"
        elif field == "requests":
            out["next"]["requests"].pop("pr", None)
        else:
            out["next"]["requests"].pop("merge_commit", None)
        row["stdout"] = json.dumps(out)
        verdict = evaluate(mutant)
        rejected = reason in verdict["safety_failures"]+verdict["projection_failures"]
        results.append(dict(plant=name, expected_reason=reason, rejected=rejected,
                            synthetic_positive_reference_accepted=accepted))
    return results


def observe(source_root):
    source_root = Path(source_root).resolve()
    report = dict(schema=1, source_root=str(source_root), python=sys.executable,
                  synthetic_provider=True, authorizes_landing=False,
                  observer_sha256=digest(Path(__file__).read_bytes()), commands=[],
                  source_sha256={name: digest((source_root/name).read_bytes()) for name in
                      ("landing.py", "soodles.py", "issue_admission.py", "issue_execution.py", "policy/runtime.lock.json")})
    with tempfile.TemporaryDirectory(prefix="continuation observer ") as directory:
        lane = Path(directory)
        cp, sf, cf = lane/"checkpoint with spaces.json", lane/"readback with spaces.json", lane/"claim with spaces.json"
        def write(path, value):
            path.write_text(json.dumps(value, indent=2)+"\n")
        def state(path):
            return path.read_bytes() if path and path.exists() else None
        def invoke(name, argv, checkpoint=cp, readback=sf, provenance="observer_control"):
            before = state(checkpoint)
            result = subprocess.run(argv, cwd=lane, env={k: os.environ[k] for k in
                ("PATH", "LANG", "LC_ALL", "TMPDIR") if k in os.environ}, capture_output=True, text=True, timeout=20)
            after = state(checkpoint)
            row = dict(case=name, argv=list(argv), provenance=provenance, cwd=str(lane),
                       checkpoint=str(checkpoint), readback=str(readback),
                       exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
                       readback_bytes=readback.read_text() if readback.exists() else None,
                       checkpoint_before=before.decode() if before else None,
                       checkpoint_after=after.decode() if after else None,
                       state_after=json.loads(after) if after else None)
            report["commands"].append(row)
            return output(row)
        def argv(operation, *args):
            return [sys.executable, "-B", str(source_root/"soodles.py"), "landing", operation, *map(str,args)]
        identity = invoke("identity", argv("identity"))["verifier_sha256"]
        claim, original = fixture(identity)
        write(cf, claim); write(sf, original)
        report["fixture_claim"] = claim
        start = invoke("start", argv("start", cf, sf, cp))
        write(sf, copy.deepcopy(original))
        prepared = invoke("prepare", start.get("next", {}).get("argv") or argv("advance", cp, sf),
                          provenance="emitted_argv" if start.get("next", {}).get("argv") else "observer_reconstructed_baseline")
        dispatch_argv = prepared.get("next", {}).get("argv") or argv("dispatch", cp, sf)
        write(sf, copy.deepcopy(original))
        invoke("merge_offer", dispatch_argv, provenance="emitted_argv" if prepared.get("next", {}).get("argv") else "observer_reconstructed_baseline")
        write(sf, copy.deepcopy(original))
        invoke("unknown_merge", argv("advance", cp, sf))
        invoke("stale_dispatch", dispatch_argv, provenance="historical_dispatch_replay_control")
        for name in ("foreign_repository", "foreign_head"):
            bad = copy.deepcopy(original)
            if name == "foreign_repository": bad["pr"]["head"]["repo"] = {"full_name": "other/repository"}
            else: bad["pr"]["head"]["sha"] = "f"*40
            write(sf, bad); invoke(name, argv("advance", cp, sf))
        sf.write_text("{malformed JSON")
        invoke("malformed_json", argv("advance", cp, sf))
        missing = lane/"missing readback.json"
        invoke("missing_file", argv("advance", cp, missing), readback=missing)
        merged = copy.deepcopy(original)
        merged["pr"].update(merged=True, state="closed", merged_at="2026-09-20T00:00:00Z", merge_commit_sha="d"*40)
        write(sf, merged)
        missing_result = invoke("missing_merge_commit", argv("advance", cp, sf))
        merged["merge_commit"] = {"sha": "d"*40, "tree": {"sha": "b"*40}, "parents": [{"sha": "c"*40}, {"sha": "a"*40}]}
        write(sf, merged)
        repaired = invoke("repair_merge_commit", missing_result.get("next", {}).get("argv") or argv("advance", cp, sf),
                          provenance="emitted_argv" if missing_result.get("next", {}).get("argv") else "observer_reconstructed_baseline")
        write(sf, copy.deepcopy(merged))
        invoke("close_offer", repaired.get("next", {}).get("argv") or argv("dispatch", cp, sf),
               provenance="emitted_argv" if repaired.get("next", {}).get("argv") else "observer_reconstructed_baseline")
        invoke("unknown_close", argv("advance", cp, sf))
        closed = copy.deepcopy(merged)
        closed["issue"].update(state="closed", state_reason="completed", closed_at="2026-09-20T00:01:00Z")
        closed["branch"]["commit"]["sha"] = "d"*40
        write(sf, closed)
        invoke("resolve", argv("advance", cp, sf))
        invoke("resolved_again", argv("advance", cp, sf))
        cp2 = lane/"unoffered checkpoint.json"
        write(sf, original)
        invoke("start_for_invalidate", argv("start", cf, sf, cp2), checkpoint=cp2)
        invoke("invalidate", argv("invalidate", cp2), checkpoint=cp2)
        cp3 = lane/"direct domain checkpoint.json"
        code = "import json,sys;sys.path.insert(0,sys.argv[1]);import landing;print(json.dumps(landing.start(landing.read(sys.argv[2]),landing.read(sys.argv[3]),sys.argv[4])))"
        invoke("direct_domain", [sys.executable,"-B","-c",code,str(source_root),str(cf),str(sf),str(cp3)], checkpoint=cp3)
        report["cleanup"] = {"directory": str(lane), "entries_before_removal": sorted(p.name for p in lane.iterdir())}
    report["cleanup"]["removed"] = not Path(report["cleanup"]["directory"]).exists()
    report["evaluation"] = evaluate(report)
    report["sensitivity"] = sensitivity(report)
    return report


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: continuation_observer.py SOURCE_ROOT OUTPUT_JSON")
    report = observe(sys.argv[1])
    target = Path(sys.argv[2]).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+"\n")
    sensitive = all(x["rejected"] and x["synthetic_positive_reference_accepted"] for x in report["sensitivity"])
    print(json.dumps({"report": str(target), **report["evaluation"], "sensitivity_pass": sensitive}))
    return 0 if report["evaluation"]["safety"] == "PASS" and sensitive else 1


if __name__ == "__main__":
    raise SystemExit(main())
