"""Report one admitted worker outcome through Noodle's existing event writer.

This is a stateless identity/readback adapter, not a concurrency lease or a
replacement for Noodle's typed-outcome consumer. No provider access occurs.
"""
import json
import hashlib
import fcntl
import time
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
    require(isinstance(carrier.get("codex"), dict),
            "carrier.codex", carrier.get("codex"))
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


FEEDBACK_PREFIX = "soodles.pclass-feedback.v1 "


def feedback_records(events, session, execution):
    records = []
    for event in events:
        payload = event.get("payload", {})
        message = payload.get("message", "") if isinstance(payload, dict) else ""
        if event.get("type") != "stage_message" or not isinstance(message, str) or not message.startswith(FEEDBACK_PREFIX):
            continue
        try:
            record = json.loads(message[len(FEEDBACK_PREFIX):])
        except ValueError as error:
            raise AdmissionRefusal("worker.feedback.record", str(error), **READBACK) from error
        require(isinstance(record, dict) and event.get("session_id") == session
                and payload.get("outcome") in (None, "") and payload.get("blocking") is False
                and payload.get("order_id") == execution["order_id"]
                and type(payload.get("stage_index")) is int
                and payload["stage_index"] == execution["stage_index"]
                and record.get("round") == len(records) + 1
                and record.get("previous") == (records[-1]["identity"] if records else None),
                "worker.feedback.lineage", record, **READBACK)
        require(isinstance(record.get("result"), dict) and isinstance(record.get("selection"), dict)
                and record.get("identity") == feedback_identity(record["result"]),
                "worker.feedback.identity", record, **READBACK)
        records.append(record)
    return records


def feedback_identity(result):
    material = {"case_fingerprints": result.get("case_fingerprints"),
                "criteria": result.get("criteria", {}).get("status"),
                "observed": {c["id"]: c["observed"] for c in result.get("cases", [])}}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def failed_feedback(result):
    return (result.get("criteria", {}).get("status") == "REVISION_REQUIRED"
            or (result.get("behavior") or {}).get("classification") == "FAIL")


def pclass_paths(root, binding):
    base = binding.get("base_head") or binding.get("contract", {}).get("base_head")
    if not base:
        return []  # Legacy contracts retain their existing completion boundary.
    run = subprocess.run(["git", "diff", "--name-only", base], cwd=root,
                         capture_output=True, text=True, timeout=30)
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root,
                              capture_output=True, text=True, timeout=30)
    require(run.returncode == untracked.returncode == 0, "worker.feedback.changed_paths",
            run.stderr + untracked.stderr, owner="Git", required="admitted_base_diff")
    return [str((Path(root) / name).resolve()) for name in set((run.stdout + untracked.stdout).splitlines())
            if name.endswith(".md") and (name == "AGENTS.md" or name.startswith((".agents/skills/", "contracts/")))
            and (Path(root) / name).is_file()]


def require_feedback_completion(root, binding, session, events):
    records = feedback_records(events, session, binding["execution"])
    changed = pclass_paths(root, binding)
    if not records and not changed:
        return
    require(bool(records), "worker.feedback.missing", changed,
            owner="review-writing", required="current_pclass_feedback")
    from schema_manager import pclass_feedback
    record = records[-1]
    selected = record["selection"]
    current = pclass_feedback(selected["path"], selected["sha256"])
    require(current.get("criteria", {}).get("status") == "SUPPORTED"
            and current.get("evidence_validity") == "VALID"
            and current.get("behavior", {}).get("classification") == "PASS"
            and feedback_identity(current) == record["identity"],
            "worker.feedback.incomplete", current, owner="review-writing", required="current_pclass_feedback")
    covered = {str(Path(ref["path"]).resolve()) for ref in current["instructions"]}
    require(set(changed) <= covered, "worker.feedback.coverage", sorted(set(changed) - covered),
            owner="review-writing", required="changed_pclass_behavior_coverage")


def feedback(selection_path, expected_sha256, root=None, environ=None):
    """Consume one observation through Noodle's existing session event writer."""
    from schema_manager import pclass_feedback, feedback_bytes, feedback_json, project_feedback_history
    from test_manager import feedback_scope
    root = Path(root or Path.cwd()).resolve()
    binding, session, binary = worker_context(root, os.environ if environ is None else environ)
    execution = binding["execution"]
    directory = Path(execution["control_root"]) / ".noodle/sessions" / session
    # Serialize this adapter on an existing session file. Noodle still owns append.
    with (directory / "spawn.json").open("rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise AdmissionRefusal("worker.feedback.busy", session, **READBACK) from error
        before, events = session_events(directory / "events.ndjson", initial=True)
        require(not typed_events(events), "worker.events.existing_outcome", typed_events(events), **READBACK)
        records = feedback_records(events, session, execution)
        result = pclass_feedback(selection_path, expected_sha256)
        require(result.get("evidence_validity") != "INVALID" and "case_fingerprints" in result
                and result.get("criteria", {}).get("status") != "NOT_REVIEWED",
                "worker.feedback.input", result, owner="review-writing", required="bound_schema_2_feedback")
        requirements = feedback_json(feedback_bytes(result["requirements"], "requirements"), "requirements")
        require(requirements == {"task": execution["task"], "contract": binding["contract"]},
                "worker.feedback.requirements", "changed task or contract",
                owner="supervisor", required="original_admitted_requirements")
        identity = feedback_identity(result)
        if records and identity == records[-1]["identity"]:
            return {"status": "readback", "round": records[-1]["round"],
                    "feedback": records[-1], "next": records[-1]["result"]["next"],
                    "authorizes_landing": False}
        failures = sum(failed_feedback(record["result"]) for record in records)
        require(failures < 3 or not failed_feedback(result), "worker.feedback.budget", failures,
                owner="review-writing", required="reassess_cause_after_three_failures")
        require(identity not in {r["identity"] for r in records}, "worker.feedback.cycle", identity,
                owner="review-writing", required="material_evidence_without_replaying_failed_state")
        result = project_feedback_history(result, failures + int(failed_feedback(result)))
        record = {"round": len(records) + 1, "previous": records[-1]["identity"] if records else None,
                  "identity": identity, "selection": {"path": str(Path(selection_path).resolve()),
                                                       "sha256": expected_sha256},
                  "result": result, "failed_attempts": failures + int(failed_feedback(result)),
                  "test_scope": feedback_scope(result, records[-1]["result"] if records else None)}
        payload = {"message": FEEDBACK_PREFIX + json.dumps(record, sort_keys=True),
                   "blocking": False, "order_id": execution["order_id"], "stage_index": execution["stage_index"]}
        argv = [binary, "--project-dir", execution["control_root"], "event", "emit", "stage_message",
                "--session", session, "--payload", json.dumps(payload)]
        try:
            run = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as error:
            raise AdmissionRefusal("worker.event.process_unknown", str(error), **READBACK) from error
        after, observed = session_events(directory / "events.ndjson")
        accepted = feedback_records(observed, session, execution)
        require(run.returncode == 0 and after.startswith(before) and len(accepted) == len(records) + 1
                and accepted[-1] == record and not typed_events(observed),
                "worker.feedback.readback", {"exit_code": run.returncode, "stderr": run.stderr}, **READBACK)
        return {"status": "recorded", "round": record["round"], "feedback": record,
                "next": result["next"], "authorizes_landing": False}


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
    if outcome == "completed":
        require_feedback_completion(root or Path.cwd(), binding, session, events)
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
    started = time.perf_counter()
    argv = sys.argv[1:] if argv is None else argv
    if argv in (["--help"], ["-h"]):
        print("Usage: ./stage-outcome {completed,blocked,failed} MESSAGE\n"
              "       ./stage-outcome feedback /absolute/selection.json SHA256\n"
              "Requires admitted worker cwd, NOODLE_PROJECT_DIR, NOODLE_WORKTREE,\n"
              "NOODLE_SESSION_ID, NOODLE_ORDER_ID, NOODLE_STAGE_INDEX and\n"
              "SOODLES_ADMISSION_LAUNCHER with its pinned sibling envelope.json.\n"
              "MESSAGE must be nonblank; identity and blocking are derived.\n"
              "Refusal requires the named owner's input/readback; never auto-retry.")
        return 0
    try:
        if len(argv) == 3 and argv[0] == "feedback":
            receipt = feedback(*argv[1:])
        else:
            require(len(argv) == 2, "arguments", argv, owner="worker", required="outcome_and_message")
            receipt = report(*argv)
    except AdmissionRefusal as error:
        receipt = {"status": "refused", "invalid": error.invalid,
                   "next": error.next, "authorizes_landing": False}
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        receipt = {"status": "refused", "invalid": {"field": "worker.input", "value": str(error)},
                   "next": {"owner": "Noodle", "required": ["current_dispatch_and_admission_readback"]},
                   "authorizes_landing": False}
    print(json.dumps({"event": "soodles.timing", "operation": "stage.feedback" if argv and argv[0] == "feedback" else "stage.outcome",
                      "seconds": time.perf_counter() - started, "status": receipt["status"]}), file=sys.stderr)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] in ("recorded", "readback") else 1


if __name__ == "__main__":
    sys.exit(main())
