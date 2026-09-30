"""Report one admitted worker outcome through Noodle's existing event writer.

This is a stateless identity/readback adapter, not a concurrency lease or a
replacement for Noodle's typed-outcome consumer. No provider access occurs.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from issue_admission import (AdmissionRefusal, load_external_envelope, nonempty,
                             parse_contract, require)
from issue_execution import (projection, read_owner, spawn_readback,
                             validate_carrier)
from repository_binding import git_origins


OUTCOMES = ("completed", "blocked", "failed")
DISPATCH = {"owner": "Noodle", "required": "current_dispatch_identity"}
READBACK = {"owner": "Noodle", "required": "current_session_event_readback"}


def registered_worktree(root, binding):
    """Completion may have commits and residue; Git identity must still match."""
    control = Path(binding["execution"]["control_root"]).resolve()
    source = {"owner": "Git", "required": "registered_worktree_readback"}

    def git(cwd, *args):
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                                text=True, timeout=30)
        require(result.returncode == 0, "worker.git", result.stderr, **source)
        return result.stdout.strip()

    require(git(root, "rev-parse", "--show-toplevel") == str(root),
            "worker.git.root", str(root), **source)
    common_args = ("rev-parse", "--path-format=absolute", "--git-common-dir")
    require(Path(git(root, *common_args)).resolve()
            == Path(git(control, *common_args)).resolve(),
            "worker.git.common_dir", str(root), **source)
    branch = binding["execution"]["worktree"]
    require(git(root, "branch", "--show-current") == branch,
            "worker.git.branch", branch, **source)
    records = git(control, "worktree", "list", "--porcelain").split("\n\n")
    require(any("worktree " + str(root) in r.splitlines()
                and "branch refs/heads/" + branch in r.splitlines() for r in records),
            "worker.git.registration", str(root), **source)
    origin = git(root, "remote", "get-url", "origin")
    require(origin in git_origins(binding["repository"]),
            "worker.git.origin", origin, **source)


def worker_context(root, environ):
    root = Path(root).resolve()
    for key in ("NOODLE_PROJECT_DIR", "NOODLE_WORKTREE"):
        value = environ.get(key)
        require(isinstance(value, str) and Path(value).is_absolute(),
                "worker." + key, value, **DISPATCH)
    control = Path(environ["NOODLE_PROJECT_DIR"]).resolve()
    session = environ.get("NOODLE_SESSION_ID")
    require(isinstance(session, str) and re.fullmatch(r"[a-zA-Z0-9-]+", session),
            "worker.session_id", session, **DISPATCH)
    order_id = environ.get("NOODLE_ORDER_ID")
    require(nonempty(order_id), "worker.order_id", order_id, **DISPATCH)
    # Bootstrap only the canonical owner location. Its current stage prompt
    # supplies the independent envelope pin; envelope bytes never pin themselves.
    state = read_owner({"execution": {"control_root": str(control)}})
    order = state["state"]["orders"].get(order_id)
    require(isinstance(order, dict) and isinstance(order.get("stages"), list)
            and len(order["stages"]) == 1, "worker.order", order, **DISPATCH)
    stage = order["stages"][0]
    require(isinstance(stage, dict), "worker.stage", stage, **DISPATCH)
    for key, expected in (("stage_index", 0), ("skill", "execute"),
                          ("provider", "codex"), ("runtime", "process"),
                          ("status", "running")):
        require(type(stage.get(key)) is type(expected) and stage.get(key) == expected,
                "worker.stage." + key, stage.get(key), **DISPATCH)
    try:
        subject = json.loads(stage.get("prompt", ""))
    except (ValueError, TypeError) as error:
        raise AdmissionRefusal("worker.stage.prompt", str(error), **DISPATCH) from error
    require(isinstance(subject, dict), "worker.stage.prompt", subject, **DISPATCH)
    digest = subject.get("envelope_sha256")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
            "worker.stage.envelope_sha256", digest, **DISPATCH)
    launcher = environ.get("SOODLES_ADMISSION_LAUNCHER")
    require(isinstance(launcher, str) and Path(launcher).is_absolute()
            and Path(launcher).is_file() and os.access(launcher, os.X_OK),
            "worker.launcher", launcher, owner="supervisor",
            required="SOODLES_ADMISSION_LAUNCHER")
    envelope = load_external_envelope(Path(launcher).parent / "envelope.json", digest, root)
    contract = parse_contract("<!-- soodles:execution-v1 -->\n```json\n"
                              + json.dumps(subject.get("contract"))
                              + "\n```\n<!-- /soodles:execution-v1 -->")
    for key in ("owner", "write_paths"):
        require(contract[key] == envelope[key], "worker.contract." + key,
                contract[key], **DISPATCH)
    if contract["schema"] >= 3:
        require(contract["base_head"] == envelope["base_head"],
                "worker.contract.base_head", contract["base_head"], **DISPATCH)
    binding = {**envelope, "contract": contract}
    execution = binding["execution"]
    expected_root = (Path(execution["control_root"]) / ".worktrees" / execution["worktree"]).resolve()
    require(root == expected_root, "worker.worktree", str(root), **DISPATCH)
    for key, expected in (("NOODLE_PROJECT_DIR", execution["control_root"]),
                          ("NOODLE_WORKTREE", str(expected_root)),
                          ("NOODLE_ORDER_ID", execution["order_id"]),
                          ("NOODLE_STAGE_INDEX", str(execution["stage_index"]))):
        require(environ.get(key) == expected, "worker." + key, environ.get(key), **DISPATCH)
    require(subject.get("route") in ("automatic", "supervised")
            and subject == projection(binding, digest, subject["route"]),
            "worker.stage.binding", subject, **DISPATCH)
    attempts = stage.get("attempts")
    require(isinstance(attempts, list) and bool(attempts)
            and all(isinstance(a, dict) for a in attempts),
            "worker.attempts", attempts, **DISPATCH)
    require(attempts[-1].get("status") == "running"
            and attempts[-1].get("session_id") == session
            and not any(a.get("status") in ("launching", "running") for a in attempts[:-1]),
            "worker.attempt", attempts, **DISPATCH)
    spawn = spawn_readback(binding, session)
    carrier = execution["carrier"]
    for key, expected in (("session_id", session), ("skill", "execute"),
                          ("provider", "codex"), ("runtime", "process"),
                          ("worktree_path", str(root)),
                          ("model", carrier.get("codex", {}).get("model"))):
        require(spawn.get(key) == expected, "worker.spawn." + key, spawn.get(key), **DISPATCH)
    require(stage.get("model") == spawn.get("model"),
            "worker.stage.model", stage.get("model"), **DISPATCH)
    binary = validate_carrier(binding, worker=True)["noodle"]
    registered_worktree(root, binding)
    return binding, session, binary


def session_events(path, *, initial=False):
    try:
        raw = path.read_bytes()
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except FileNotFoundError as error:
        # The selected Noodle writer creates the log on its first append.
        # Only an admitted, validated session may reach this initial read.
        if initial:
            return b"", []
        raise AdmissionRefusal("worker.events", str(error), **READBACK) from error
    except (OSError, ValueError) as error:
        raise AdmissionRefusal("worker.events", str(error), **READBACK) from error
    require(all(isinstance(e, dict) for e in events), "worker.events", str(path), **READBACK)
    for event in events:
        if event.get("type") == "stage_message":
            require(isinstance(event.get("payload"), dict),
                    "worker.events.payload", event, **READBACK)
    return raw, events


def typed_events(events):
    return [e for e in events if e.get("type") == "stage_message"
            and e["payload"].get("outcome") not in (None, "")]


def report(outcome, message, root=None, environ=None):
    require(outcome in OUTCOMES, "outcome", outcome,
            owner="worker", required="completed_blocked_or_failed")
    require(nonempty(message), "message", message, owner="worker", required="nonblank_message")
    binding, session, binary = worker_context(root or Path.cwd(), os.environ if environ is None else environ)
    execution = binding["execution"]
    control = execution["control_root"]
    path = Path(control) / ".noodle/sessions" / session / "events.ndjson"
    before, events = session_events(path, initial=True)
    require(not typed_events(events), "worker.events.existing_outcome", typed_events(events), **READBACK)
    payload = {"message": message, "outcome": outcome, "blocking": outcome != "completed",
               "order_id": execution["order_id"], "stage_index": execution["stage_index"]}
    argv = [binary, "--project-dir", control, "event", "emit", "stage_message",
            "--session", session, "--payload", json.dumps(payload)]
    # After this call, every error means owner readback, never an automatic retry.
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        raise AdmissionRefusal("worker.event.process_unknown", str(error), **READBACK) from error
    after, observed = session_events(path)
    require(result.returncode == 0, "worker.event.process",
            {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, **READBACK)
    typed = typed_events(observed)
    require(after.startswith(before) and len(typed) == 1,
            "worker.event.readback", typed, **READBACK)
    event = typed[0]
    require(event.get("session_id") == session and event["payload"] == payload
            and type(event["payload"].get("blocking")) is bool
            and type(event["payload"].get("stage_index")) is int
            and [e for e in observed if e.get("type") == "stage_message"][-1] == event,
            "worker.event.readback", event, **READBACK)
    return {"status": "recorded", "event": event, "authorizes_landing": False}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv in (["--help"], ["-h"]):
        print("Usage: ./stage-outcome {completed,blocked,failed} MESSAGE\n"
              "Requires admitted worker cwd, NOODLE_PROJECT_DIR, NOODLE_WORKTREE,\n"
              "NOODLE_SESSION_ID, NOODLE_ORDER_ID, NOODLE_STAGE_INDEX and\n"
              "SOODLES_ADMISSION_LAUNCHER with its pinned sibling envelope.json.\n"
              "MESSAGE must be nonblank; identity and blocking are derived.\n"
              "Refusal requires the named owner's input/readback; never auto-retry.")
        return 0
    try:
        require(len(argv) == 2, "arguments", argv, owner="worker", required="outcome_and_message")
        receipt = report(*argv)
    except AdmissionRefusal as error:
        receipt = {"status": "refused", "invalid": error.invalid,
                   "next": error.next, "authorizes_landing": False}
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        receipt = {"status": "refused", "invalid": {"field": "worker.input", "value": str(error)},
                   "next": {"owner": "Noodle", "required": ["current_dispatch_and_admission_readback"]},
                   "authorizes_landing": False}
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] == "recorded" else 1


if __name__ == "__main__":
    sys.exit(main())
