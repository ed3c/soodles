"""Fixed observer of candidate CLI processes; all provider data is a local fixture."""
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def base_recovery_probe(subject, isolated=False):
    subject = Path(subject).resolve()
    cases = []

    def require(ok, reason):
        if not ok:
            raise RuntimeError("base recovery: " + reason)

    with tempfile.TemporaryDirectory(prefix="soodles-base-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        lane = root / "lane"
        lane.mkdir(mode=0o777 if isolated else 0o700)
        lane.chmod(0o777 if isolated else 0o700)
        env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL", "TMPDIR") if k in os.environ}
        identity_files = [subject / p for p in ("landing.py", "soodles.py", "policy/runtime.lock.json")]
        import hashlib
        initial_bytes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in identity_files]

        def command(args, kill_phase=None):
            argv = [sys.executable, "-B", str(subject / "soodles.py"), "landing", *map(str, args)]
            if kill_phase:
                code = '''import json,os,signal,sys
sys.path.insert(0,sys.argv[1])
import landing
save=landing.save
def crash(path,state):
 save(path,state)
 if state['phase']==sys.argv[2]: os.kill(os.getpid(),signal.SIGKILL)
landing.save=crash
if sys.argv[3]=='invalidate':
 landing.invalidate(sys.argv[4])
elif sys.argv[3]=='readmit':
 landing.readmit(sys.argv[4],json.load(open(sys.argv[5])),json.load(open(sys.argv[6])))
else:
 getattr(landing,sys.argv[3])(sys.argv[4],json.load(open(sys.argv[5])))
'''
                argv = [sys.executable, "-B", "-c", code, str(subject), kill_phase, *map(str, args)]
            return subprocess.run(argv, cwd=lane, env=env, text=True, capture_output=True, timeout=20,
                                  user=65534 if isolated else None, group=65534 if isolated else None)

        def invoke(args):
            r = command(args)
            require(r.returncode == 0, f"{args[0]} failed: {r.stderr.strip()}")
            return json.loads(r.stdout)

        def write(name, value):
            path = lane / name
            if path.exists():
                path.unlink()
            path.write_text(json.dumps(value))
            path.chmod(0o644)
            return path

        repo = {"full_name": "ed3c/soodles"}
        claim = {"repository": "ed3c/soodles", "issue": 1, "pr": 2, "head": "a"*40,
                 "tree": "b"*40, "base_head": "c"*40, "run_id": 10, "run_attempt": 1,
                 "worktree": "fixture", "control_root": str(root),
                 "verifier_sha256": invoke(["identity"])["verifier_sha256"]}
        snapshot = {
            "pr": {"number": 2, "html_url": "https://github.com/ed3c/soodles/pull/2",
                   "body": "Refs ed3c/soodles#1", "head": {"repo": repo, "sha": "a"*40, "ref": "fixture"},
                   "base": {"repo": repo, "sha": "c"*40, "ref": "main"}, "merged": False,
                   "state": "open", "draft": False, "mergeable": True},
            "issue": {"number": 1, "html_url": "https://github.com/ed3c/soodles/issues/1", "state": "open"},
            "run": {"id": 10, "run_attempt": 1, "repository": repo, "head_repository": repo,
                    "head_sha": "a"*40, "event": "pull_request", "path": ".github/workflows/runtime.yml",
                    "status": "completed", "conclusion": "success"},
            "commit": {"sha": "a"*40, "tree": {"sha": "b"*40}},
            "jobs": {"total_count": 1, "jobs": [{"id": 11, "name": "runtime-evidence", "run_id": 10,
                "head_sha": "a"*40, "status": "completed", "conclusion": "success", "steps": [
                    {"name": "Canonical acceptance on the exact candidate head", "status": "completed", "conclusion": "success"}]}]},
            "branch": {"name": "main", "commit": {"sha": "c"*40}}}

        def comparison(base, head):
            return {"base_commit": {"sha": base}, "merge_base_commit": {"sha": base},
                    "status": "ahead", "commits": [{"sha": head}], "total_commits": 1}

        moved = copy.deepcopy(snapshot)
        moved["branch"]["commit"]["sha"] = moved["pr"]["base"]["sha"] = "f"*40
        moved["base_comparison"] = comparison("c"*40, "f"*40)
        fresh_claim = {**claim, "head": "e"*40, "tree": "d"*40, "base_head": "f"*40, "run_id": 20}
        fresh = copy.deepcopy(moved)
        fresh["pr"]["head"]["sha"] = "e"*40
        fresh["commit"] = {"sha": "e"*40, "tree": {"sha": "d"*40}}
        fresh["run"].update(id=20, head_sha="e"*40)
        fresh["jobs"]["jobs"][0].update(run_id=20, head_sha="e"*40)
        fresh["candidate_comparison"] = comparison("f"*40, "e"*40)
        cf, sf = write("claim.json", claim), write("snapshot.json", snapshot)
        mf = write("moved.json", moved)
        nf, ns = write("fresh-claim.json", fresh_claim), write("fresh.json", fresh)

        def admit(name):
            cp = lane / (name + ".json")
            invoke(["start", cf, sf, cp])
            invoke(["advance", cp, sf])
            return cp

        def guided_refusal(args, field, base, head):
            cp = Path(args[1]); before = cp.read_bytes()
            r = command(args)
            require(r.returncode != 0, "missing comparison was accepted")
            value = json.loads(r.stdout); nxt = value.get("next", {})
            require(nxt.get("kind") == "provider_readback" and nxt.get("owner") == "GitHub",
                    "comparison lacks owning provider readback")
            require(nxt.get("operation") == args[0], "comparison routes to wrong operation")
            url = "https://api.github.com/repos/ed3c/soodles/compare/" + base + "..." + head
            require(nxt.get("requests", {}).get(field) == {"method": "GET", "url": url},
                    "comparison request has wrong subject")
            require(nxt.get("known", {}).get("checkpoint") == str(cp), "comparison lost checkpoint")
            if args[0] == "readmit":
                require(nxt["known"].get("claim") == json.loads(Path(args[2]).read_text()),
                        "comparison lost confirmed fresh claim")
            require(value.get("invalid", {}).get("field", "").startswith(field), "comparison lost invalid field")
            require(url in r.stderr, "human comparison guidance differs from machine request")
            require("request" not in value and cp.read_bytes() == before, "comparison refusal changed checkpoint or offered write")
            return value

        cp = admit("comparison-guidance")
        absent = copy.deepcopy(moved); absent.pop("base_comparison")
        af = write("absent-comparison.json", absent)
        for operation in ("advance", "dispatch"):
            guided_refusal([operation, cp, af], "base_comparison", "c"*40, "f"*40)
        wrong = copy.deepcopy(moved); wrong["base_comparison"] = comparison("f"*40, "c"*40)
        wf = write("wrong-comparison.json", wrong)
        guided_refusal(["advance", cp, wf], "base_comparison", "c"*40, "f"*40)
        # Changing only the owner-specified readback makes this attempt eligible.
        require(invoke(["advance", cp, mf])["action"] == "readmit", "correct readback cannot reach readmission")
        for field, base, head in (("base_comparison", "c"*40, "f"*40),
                                  ("candidate_comparison", "f"*40, "e"*40)):
            missing = copy.deepcopy(fresh); missing.pop(field)
            ff = write("missing-"+field+".json", missing)
            guided_refusal(["readmit", cp, nf, ff], field, base, head)
        # A second forward movement needs its own exact comparison, at either consumer.
        again = copy.deepcopy(moved)
        again["branch"]["commit"]["sha"] = again["pr"]["base"]["sha"] = "9"*40
        again["base_comparison"] = comparison("c"*40, "9"*40)
        gf = write("again.json", again)
        guided_refusal(["advance", cp, gf], "recovery_comparison", "f"*40, "9"*40)
        newer_claim = {**fresh_claim, "base_head": "9"*40}
        newer = copy.deepcopy(fresh)
        newer["branch"]["commit"]["sha"] = newer["pr"]["base"]["sha"] = "9"*40
        newer["base_comparison"] = comparison("c"*40, "9"*40)
        newer["candidate_comparison"] = comparison("9"*40, "e"*40)
        ncf, nrf = write("newer-claim.json", newer_claim), write("newer.json", newer)
        guided_refusal(["readmit", cp, ncf, nrf], "recovery_comparison", "f"*40, "9"*40)
        invoke(["readmit", cp, nf, ns])
        require(invoke(["advance", cp, ns])["action"] == "dispatch", "guided readback lost existing positive route")
        cases.append({"case": "comparison_owner_guidance", "comparison_fields": 3,
                      "invoked_operations": ["advance", "dispatch", "readmit"], "refusals": 7,
                      "checkpoint_preserved_on_refusal": True, "provider_writes": 0})

        cp = admit("comparison-invalid-identity")
        malformed = copy.deepcopy(moved)
        malformed["branch"]["commit"]["sha"] = malformed["pr"]["base"]["sha"] = "refs/heads/main"
        bad = write("bad-endpoint.json", malformed); before = cp.read_bytes()
        r = command(["advance", cp, bad]); value = json.loads(r.stdout)
        require(r.returncode != 0 and not value.get("next", {}).get("requests"), "unconfirmed endpoint became provider request")
        require(cp.read_bytes() == before, "invalid endpoint changed checkpoint")
        foreign = copy.deepcopy(moved); foreign["pr"]["base"]["repo"] = {"full_name": "foreign/repo"}
        foreign_file = write("foreign-repository.json", foreign)
        r = command(["advance", cp, foreign_file]); value = json.loads(r.stdout)
        require(r.returncode != 0 and not value.get("next", {}).get("requests"), "foreign identity became provider request")
        require(cp.read_bytes() == before, "foreign subject changed checkpoint")
        cases.append({"case": "comparison_identity_before_guidance", "guessed_provider_requests": 0})

        cp = admit("recovery")
        # Observe the baseline through the ordinary CLI before injecting faults.
        outcome = invoke(["advance", cp, mf])
        require(outcome.get("action") == "readmit", "base drift has no owning readmission action")
        require(outcome.get("next", {}).get("operation") == "readmit", "missing supported next command")
        require(outcome.get("invalid", {}).get("field") == "base.head", "missing exact invalid field")
        before = cp.read_bytes()
        require(invoke(["advance", cp, mf])["action"] == "readmit", "pending recovery cannot resume")
        require(cp.read_bytes() == before, "unchanged readback rewrote recovery")
        r = command(["dispatch", cp, sf])
        require(r.returncode != 0, "old acceptance dispatches after invalidation")
        require(cp.read_bytes() == before, "stale dispatch changes checkpoint")
        cases.append({"case": "old_acceptance_invalidated", "provider_requests": 0})

        cp = admit("invalidation-crash")
        r = command(["advance", cp, mf], "readmission_pending")
        require(r.returncode == -signal.SIGKILL, "invalidation SIGKILL was not reached")
        require(invoke(["advance", cp, mf])["action"] == "readmit", "invalidation crash cannot recover")
        r = command(["readmit", cp, nf, ns], "admitted")
        require(r.returncode == -signal.SIGKILL, "readmission SIGKILL was not reached")
        state = json.loads(cp.read_text())
        require(state["claim"] == fresh_claim and state["writes_offered"] == [], "fresh claim not atomically saved")
        require(state["prior_admissions"][-1]["claim"] == claim, "prior identity lost")
        before = cp.read_bytes()
        require(command(["readmit", cp, nf, ns]).returncode != 0, "duplicate readmission admitted")
        require(cp.read_bytes() == before, "duplicate readmission changed accepted state")
        require(invoke(["advance", cp, ns])["action"] == "dispatch", "fresh admission cannot advance")
        request = invoke(["dispatch", cp, ns])["request"]
        require(request == {"action": "merge", "repository_full_name": "ed3c/soodles", "pr_number": 2,
                            "expected_head_sha": "e"*40, "merge_method": "merge"}, "wrong fresh request")
        require(command(["dispatch", cp, ns]).returncode != 0, "fresh merge repeated")
        cases.append({"case": "sigkill_invalidation_and_readmission", "signals": 2, "fresh_requests": 1})

        for legacy in (False, True):
            cp = admit("unknown-" + str(legacy))
            invoke(["dispatch", cp, sf])
            if legacy:
                state = json.loads(cp.read_text())
                state["schema"] = 1
                state.pop("delivery")
                cp = write("legacy.json", state)
                if isolated:
                    os.chown(cp, 65534, 65534)
            require(invoke(["advance", cp, mf])["action"] == "readback", "unknown offer converted to readmission")
            before = cp.read_bytes()
            require(command(["readmit", cp, nf, ns]).returncode != 0, "unknown write re-admitted")
            require(cp.read_bytes() == before, "unknown identity overwritten")
        cases.append({"case": "offered_and_legacy_unknown", "reoffers": 0})

        cp = admit("concurrent")
        invoke(["advance", cp, mf])
        argv = [sys.executable, "-B", str(subject / "soodles.py"), "landing", "readmit", str(cp), str(nf), str(ns)]
        processes = [subprocess.Popen(argv, cwd=lane, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      user=65534 if isolated else None, group=65534 if isolated else None) for _ in range(2)]
        for process in processes:
            process.communicate(timeout=20)
        require(sum(p.returncode == 0 for p in processes) == 1, "concurrent readmission accepted more than once")
        require(len(json.loads(cp.read_text())["prior_admissions"]) == 1, "concurrent recovery lost history")
        cases.append({"case": "concurrent_readmission", "processes": 2, "admissions": 1})
        # A supervisor can withdraw green evidence before correcting the same atom.
        same_claim = {**fresh_claim, "base_head": claim["base_head"]}
        same = copy.deepcopy(fresh)
        same["pr"]["base"]["sha"] = same["branch"]["commit"]["sha"] = claim["base_head"]
        same.pop("base_comparison")
        same["candidate_comparison"] = comparison(claim["base_head"], same_claim["head"])
        ac, ar = write("amended-claim.json", same_claim), write("amended-readback.json", same)
        cp = admit("amendment")
        require(json.loads(cp.read_text())["classification"] is None, "green admission resolved the Issue")
        r = command(["invalidate", cp], "readmission_pending")
        require(r.returncode == -signal.SIGKILL, "explicit invalidation SIGKILL was not reached")
        before = cp.read_bytes()
        action = invoke(["invalidate", cp])
        require(action.get("next", {}).get("operation") == "readmit", "amendment has no next action")
        require(cp.read_bytes() == before, "repeated invalidation rewrote checkpoint")
        require(command(["dispatch", cp, sf]).returncode != 0, "old green dispatches after explicit invalidation")
        require(cp.read_bytes() == before, "old dispatch mutated amendment")
        failed = copy.deepcopy(same)
        failed["run"]["conclusion"] = "failure"
        fr = write("amended-failed.json", failed)
        require(command(["readmit", cp, ac, fr]).returncode != 0, "failed fresh CI was accepted")
        vc = write("amended-verifier.json", {**same_claim, "verifier_sha256": "0"*64})
        require(command(["readmit", cp, vc, ar]).returncode != 0, "candidate promoted another verifier")
        require(command(["readmit", cp, cf, sf]).returncode != 0, "unchanged acceptance was re-admitted")
        require(cp.read_bytes() == before, "refused readmission changed prior admission")
        r = command(["readmit", cp, ac, ar], "admitted")
        require(r.returncode == -signal.SIGKILL, "amendment readmission SIGKILL was not reached")
        state = json.loads(cp.read_text())
        require(state["claim"] == same_claim and state["classification"] is None, "fresh green is not scoped admission")
        require(state["prior_admissions"][-1]["claim"] == claim, "amendment lost old claim")
        require(state["prior_admissions"][-1]["delivery"] == {"action": "merge", "status": "prepared"}, "prepared intent history lost")
        require(invoke(["advance", cp, ar])["action"] == "dispatch", "same-base amendment cannot resume")
        require(invoke(["dispatch", cp, ar])["request"]["expected_head_sha"] == same_claim["head"], "amendment offers old head")
        require(json.loads(cp.read_text())["classification"] is None, "offered merge resolved the Issue")
        cases.append({"case": "same_base_supervised_amendment", "signals": 2,
                      "old_acceptance_dispatches": 0, "fresh_requests": 1, "terminal_classification": None})

        for legacy in (False, True):
            cp = admit("amendment-unknown-" + str(legacy))
            invoke(["dispatch", cp, sf])
            if legacy:
                state = json.loads(cp.read_text())
                state["schema"] = 1
                state.pop("delivery")
                cp = write("amendment-legacy.json", state)
                if isolated:
                    os.chown(cp, 65534, 65534)
            before = cp.read_bytes()
            r = command(["invalidate", cp])
            require(r.returncode != 0 and "landing advance --help" in r.stderr,
                    "unknown write lacks readback refusal")
            require(cp.read_bytes() == before, "amendment erased unknown offer")
        cases.append({"case": "amendment_preserves_offered_and_legacy_unknown", "reoffers": 0})

        require(initial_bytes == [hashlib.sha256(p.read_bytes()).hexdigest() for p in identity_files], "subject rewrote identity")
    return {"scope": "real child process faults; local provider fixtures, no GitHub writes",
            "cases": cases, "isolated_child_uid": 65534 if isolated else None, "authorizes_landing": False}


if __name__ == "__main__":
    try:
        print(json.dumps(base_recovery_probe(sys.argv[1], "--isolated" in sys.argv[2:]), indent=2))
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"verdict": "NOT VERIFIED", "reason": str(exc), "authorizes_landing": False}))
        sys.exit(1)
