"""Physical current-next and A -> cleanup -> B discriminator.

The provider data is a local fixture.  Noodle sessions, typed outcomes,
process exits, linked worktrees, cleanup, and the order projection are real.
The returned receipt is local evidence and never authorizes landing.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import time


REPOSITORY = "ed3c/soodles"


def _run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f"command failed {argv!r}: {result.stderr}")
    return result.stdout.strip()


def _wait(predicate, label, seconds=12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise RuntimeError("timed out waiting for " + label)


def _start(noodle, root):
    return subprocess.Popen(
        [noodle, "--project-dir", str(root), "start"], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True)


def _stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
    stdout, stderr = process.communicate(timeout=15)
    if process.returncode != 0:
        raise RuntimeError(f"Noodle exited {process.returncode}: {stderr}")
    return {"pid": process.pid, "returncode": process.returncode,
            "waited": True, "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()}


def _effect(state, order_id, kind):
    return [record for record in state.get("effect_ledger", [])
            if record.get("effect", {}).get("type") == kind
            and record["effect"].get("payload", {}).get("order_id") == order_id]


def _projected(root, order_id):
    try:
        state = json.loads((root / ".noodle/state.snapshot.json").read_text())
    except (OSError, ValueError):
        return None
    return state if (order_id not in state.get("state", {}).get("orders", {})
                     and len(_effect(state, order_id, "write_projection")) == 1
                     and len(_effect(state, order_id, "ack")) == 1) else None


def _session(root, order_id):
    matches = []
    for path in (root / ".noodle/sessions").glob(order_id + "-0-execute-*/spawn.json"):
        spawn = json.loads(path.read_text())
        if spawn.get("skill") == "execute":
            matches.append((path.parent, spawn))
    if len(matches) != 1:
        raise RuntimeError(f"expected one original session for {order_id}, got {len(matches)}")
    directory, spawn = matches[0]
    meta = json.loads((directory / "meta.json").read_text())
    events = [json.loads(line) for line in (directory / "events.ndjson").read_text().splitlines()]
    terminal = [event for event in events if event.get("type") == "stage_message"]
    if (len(terminal) != 1 or terminal[0].get("payload", {}).get("outcome") != "completed"
            or terminal[0]["payload"].get("blocking") is not False
            or meta.get("status") != "exited" or meta.get("alive") is not False):
        raise RuntimeError("original session lacks one completed typed outcome and exit")
    return directory, spawn, meta, terminal[0]


def _envelope(root, external, noodle, codex, issue):
    import issue_admission

    head = _run(["git", "rev-parse", "HEAD"], root)
    contract = {
        "schema": 1, "trigger": "A completed order was projected from the current map.",
        "source": f"physical fixture {issue}", "owner": "Soodles Issue admission",
        "changes": ["Consume retained Noodle completion evidence before cleanup."],
        "write_paths": ["fixture.txt"],
        "behavior": ["Require the original session, outcome, exit, and projection."],
        "defect_controls": ["A missing or blocked typed outcome refuses cleanup."],
        "non_cases": ["Provider delivery remains a fixture."], "dependencies": [],
        "acceptance": "Run the frozen physical observer.",
        "delivery": "Use the existing landing owner.",
        "reconciliation": "Noodle removes the exact worktree before the next order.",
        "feature_scope": "One A to cleanup to B lifecycle.",
    }
    body = ("<!-- soodles:execution-v1 -->\n```json\n"
            + json.dumps(contract, indent=2) + "\n```\n<!-- /soodles:execution-v1 -->\n")
    updated = "2026-09-20T00:00:00Z"
    order_id = f"soodles-{issue}"
    data = {
        "schema": 1, "repository": REPOSITORY, "issue": issue,
        "body_sha256": issue_admission.body_digest(body), "body_updated_at": updated,
        "owner": contract["owner"], "write_paths": contract["write_paths"],
        "base_head": head, "execution": {
            "control_root": str(root), "worktree": order_id + "-0-execute",
            "order_id": order_id, "stage_index": 0,
            "task": f"Complete physical order {order_id}.", "source_head": head,
            "carrier": {
                "platform": platform.system().lower() + "_" + platform.machine().lower(),
                "noodle": {"path": noodle,
                           "sha256": hashlib.sha256(Path(noodle).read_bytes()).hexdigest()},
                "codex": {"path": str(codex),
                          "sha256": hashlib.sha256(codex.read_bytes()).hexdigest(),
                          "argv": ["exec"], "model": "fixture"}}}}
    path = external / f"envelope-{issue}.json"
    raw = json.dumps(data, sort_keys=True).encode()
    path.write_bytes(raw)
    readback = {"url": f"https://api.github.com/repos/{REPOSITORY}/issues/{issue}",
                "html_url": f"https://github.com/{REPOSITORY}/issues/{issue}",
                "number": issue, "body": body, "updated_at": updated, "state": "open"}
    return data, path, hashlib.sha256(raw).hexdigest(), readback


def _consume_probe(directory, source):
    import landing

    checkpoint = directory / "consume-checkpoint.json"
    claim = {"repository": REPOSITORY, "issue": 1, "pr": 2, "head": "a" * 40,
             "tree": "b" * 40, "base_head": "c" * 40, "run_id": 10,
             "run_attempt": 1, "worktree": "fixture",
             "verifier_sha256": landing.verifier_digest()}
    repo = {"full_name": REPOSITORY}
    snapshot = {
        "pr": {"number": 2, "html_url": f"https://github.com/{REPOSITORY}/pull/2",
               "body": f"Refs {REPOSITORY}#1\n", "head": {"repo": repo, "sha": "a" * 40,
               "ref": "fixture"}, "base": {"repo": repo, "sha": "c" * 40, "ref": "main"},
               "merged": False, "state": "open", "draft": False, "mergeable": True},
        "issue": {"number": 1, "html_url": f"https://github.com/{REPOSITORY}/issues/1",
                  "state": "open"},
        "run": {"id": 10, "run_attempt": 1, "repository": repo, "head_repository": repo,
                "head_sha": "a" * 40, "event": "pull_request",
                "path": ".github/workflows/runtime.yml", "status": "completed",
                "conclusion": "success"},
        "commit": {"sha": "a" * 40, "tree": {"sha": "b" * 40}},
        "jobs": {"total_count": 1, "jobs": [{"id": 11, "name": "runtime-evidence",
                 "run_id": 10, "head_sha": "a" * 40, "status": "completed",
                 "conclusion": "success", "steps": [{
                     "name": "Canonical acceptance on the exact candidate head",
                     "status": "completed", "conclusion": "success"}]}]},
        "branch": {"name": "main", "commit": {"sha": "c" * 40}}}
    readback_path = directory / "consume-readback.json"
    readback_path.write_text(json.dumps(snapshot))
    landing.start(claim, snapshot, checkpoint)
    source = Path(source).resolve()

    def consume(argv):
        result = subprocess.run(argv, cwd=source, text=True, capture_output=True, timeout=30)
        if result.returncode:
            raise RuntimeError(f"current-next argv failed {argv!r}: {result.stderr}")
        return json.loads(result.stdout)

    prepared = consume(["./soodles", "landing", "advance",
                        str(checkpoint), str(readback_path)])
    offered = consume(prepared["next"]["argv"])
    readback = consume(offered["next"]["argv"])
    if ([prepared["action"], offered["action"], readback["action"]]
            != ["dispatch", "merge", "readback"]
            or landing.read(checkpoint)["writes_offered"] != ["merge"]):
        raise RuntimeError("current-next consumer did not preserve exactly-once offer state")
    return {"actions": [prepared["action"], offered["action"], readback["action"]],
            "argv": [prepared["next"]["argv"], offered["next"]["argv"]],
            "provider_requests": 1, "writes_offered": ["merge"]}


def handoff_probe(binary, source=None):
    """Run the frozen observer against source with the supplied real Noodle binary."""
    if source is not None:
        import sys
        sys.path.insert(0, str(Path(source).resolve()))
    import issue_execution
    import landing

    noodle = str(Path(binary).resolve())
    with tempfile.TemporaryDirectory(prefix="soodles-handoff-") as temporary:
        outside = Path(temporary).resolve()
        root = outside / "control"
        root.mkdir()
        _run(["git", "init", "-b", "main"], root)
        (root / ".gitignore").write_text(".noodle/\n.worktrees/\n")
        (root / "fixture.txt").write_text("fixture\n")
        for skill in ("schedule", "execute"):
            path = root / ".agents/skills" / skill
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                f"---\nname: {skill}\ndescription: physical fixture\n"
                "schedule: test\n---\n")
        agent = root / "agent"
        agent.mkdir()
        codex = agent / "codex"
        codex.write_text("""#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path
root = Path(os.environ.get("NOODLE_PROJECT_DIR", os.getcwd())).resolve()
order = os.environ.get("NOODLE_ORDER_ID")
session = os.environ["NOODLE_SESSION_ID"]
if order:
    payload = {"message": "completed " + order, "blocking": False,
               "outcome": "completed", "order_id": order,
               "stage_index": int(os.environ["NOODLE_STAGE_INDEX"])}
    subprocess.run([os.environ["FIXTURE_NOODLE"], "--project-dir", str(root),
                    "event", "emit", "stage_message", "--session", session,
                    "--payload", json.dumps(payload)], check=True)
else:
    runtime = root / ".noodle"
    a = runtime / "a-scheduled"
    orders = []
    if not a.exists():
        orders = [{"id": "soodles-105", "title": "A", "rationale": "first",
                   "stages": [{"do": "execute", "with": "codex", "model": "fixture",
                               "runtime": "process", "prompt": "complete A"}]}]
        a.write_text("1")
    (runtime / "orders-next.json").write_text(json.dumps({"orders": orders}))
print(json.dumps({"type": "turn.completed"}))
""")
        codex.chmod(0o755)
        (root / ".noodle.toml").write_text(f"""mode = "auto"
[routing.defaults]
provider = "codex"
model = "fixture"
[skills]
paths = [".agents/skills"]
[agents.codex]
path = "{agent}"
require_typed_outcome = true
[concurrency]
max_concurrency = 1
[runtime]
default = "process"
[server]
enabled = false
""")
        _run(["git", "add", "."], root)
        _run(["git", "-c", "user.name=Handoff Probe", "-c",
              "user.email=probe@example.invalid", "commit", "-m", "fixture"], root)
        _run(["git", "remote", "add", "origin", f"https://github.com/{REPOSITORY}.git"], root)
        head = _run(["git", "rev-parse", "HEAD"], root)
        tree = _run(["git", "rev-parse", "HEAD^{tree}"], root)
        _run(["git", "update-ref", "refs/remotes/origin/main", head], root)
        env = os.environ.copy()
        env["FIXTURE_NOODLE"] = noodle
        subprocess.run([noodle, "--project-dir", str(root), "start", "--once"],
                       cwd=root, env=env, check=True, capture_output=True, text=True)

        original_env = os.environ.get("FIXTURE_NOODLE")
        os.environ["FIXTURE_NOODLE"] = noodle
        try:
            first = _start(noodle, root)
            a_state = _wait(lambda: _projected(root, "soodles-105"), "A projection")
            a_exit = _stop(first)
            a_directory, a_spawn, _, a_event = _session(root, "soodles-105")
            a_envelope, a_path, a_digest, _ = _envelope(root, outside, noodle, codex, 105)
            a_completion = issue_execution.completed_original_order(a_envelope, a_state)

            checkpoint = outside / "landing-checkpoint.json"
            claim = {"repository": REPOSITORY, "issue": 105, "pr": 1005,
                     "head": head, "tree": tree, "base_head": head, "run_id": 1,
                     "run_attempt": 1, "worktree": "soodles-105-0-execute",
                     "control_root": str(root), "verifier_sha256": landing.verifier_digest(),
                     "execution_envelope": {"path": str(a_path), "sha256": a_digest}}
            landing.save(checkpoint, {"schema": 2, "claim": claim,
                         "phase": "awaiting_reconcile", "observations": [],
                         "classification": None, "scope": "physical local fixture",
                         "writes_offered": ["merge", "close"], "merge_sha": head,
                         "issue_closed_at": "2026-09-20T00:01:00Z"})
            fetch = landing.fetch_main
            landing.fetch_main = lambda unused: None
            try:
                resolved = landing.reconcile(checkpoint, noodle)
            finally:
                landing.fetch_main = fetch
            if (resolved.get("classification") != "RESOLVED"
                    or (root / ".worktrees/soodles-105-0-execute").exists()):
                raise RuntimeError("A was not reconciled and cleaned by the landing owner")
            cleanup_at = time.time_ns()

            _, b_path, b_digest, b_issue = _envelope(
                root, outside, noodle, codex, 106)
            issue_reads = []
            def read_b(repository, number):
                if repository != REPOSITORY or number != 106:
                    raise RuntimeError(
                        f"unexpected Issue read {repository}#{number}")
                issue_reads.append({"form": "repository-bound",
                                    "repository": repository,
                                    "issue": number})
                return b_issue
            admitted = issue_execution.automatic(
                b_path, b_digest, root, reader=read_b)
            if not admitted.get("published"):
                raise RuntimeError("B was not admitted through the Soodles mailbox owner")
            second = _start(noodle, root)
            b_state = _wait(lambda: _projected(root, "soodles-106"), "B projection")
            b_exit = _stop(second)
            b_directory, b_spawn, _, b_event = _session(root, "soodles-106")
            b_started_at = (b_directory / "spawn.json").stat().st_mtime_ns
            if b_started_at <= cleanup_at:
                raise RuntimeError("B started before A cleanup completed")
            _run([noodle, "worktree", "cleanup", "soodles-106-0-execute"], root)
            worktrees = _run(["git", "worktree", "list", "--porcelain"], root)
            branches = _run(["git", "branch", "--list", "soodles-*-0-execute"], root)
            if worktrees.count("worktree ") != 1 or branches:
                raise RuntimeError("fixture worktree or branch residue remains")
            current_next = _consume_probe(outside, source or Path(__file__).resolve().parent)
        finally:
            if original_env is None:
                os.environ.pop("FIXTURE_NOODLE", None)
            else:
                os.environ["FIXTURE_NOODLE"] = original_env

        return {
            "classification": "VERIFIED", "sequence": ["A", "cleanup", "B"],
            "current_next": current_next,
            "A": {"order_id": "soodles-105", "session_id": a_spawn["session_id"],
                  "typed_outcome": a_event["payload"], "process": a_exit,
                  "completion_source": a_completion["source"], "cleanup": "Noodle"},
            "B": {"order_id": "soodles-106", "session_id": b_spawn["session_id"],
                  "typed_outcome": b_event["payload"], "process": b_exit,
                  "admission": "issue.automatic",
                  "issue_reads": issue_reads,
                  "projection_effect": _effect(b_state, "soodles-106", "write_projection")[0]["effect_id"]},
            "runtime": {"binary": noodle,
                        "sha256": hashlib.sha256(Path(noodle).read_bytes()).hexdigest()},
            "zero_residue": True, "provider_fixture": True,
            "authorizes_landing": False,
        }


if __name__ == "__main__":
    import sys
    print(json.dumps(handoff_probe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
