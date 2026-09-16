"""Consumers for one externally admitted Issue; Noodle owns scheduling/state.

Provider reads are live by default. Test callers may supply a reader explicitly.
Only the existing orders-next mailbox is written; no independent order ledger,
lock or retry loop is introduced. An installed supervisor launcher fixes the
external envelope path/digest and this implementation before executing it.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

from issue_admission import (AdmissionRefusal, REPOSITORY, load_external_envelope,
                             require, validate_issue)


def fetch_issue(number):
    url = f"https://api.github.com/repos/{REPOSITORY}/issues/{number}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                  "User-Agent": "soodles-issue-admission"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            require(response.url == url, "issue.provider_url", response.url,
                    owner="GitHub", required="exact_issue_readback")
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise AdmissionRefusal("issue.provider_readback", str(error), "GitHub", "fresh_issue_readback") from error


def executable_identity(spec, field):
    require(isinstance(spec, dict), field, spec)
    path = spec.get("path")
    require(isinstance(path, str) and Path(path).is_absolute(), field + ".path", path)
    path = Path(path).resolve()
    require(path.is_file() and os.access(path, os.X_OK), field + ".path", str(path))
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    require(observed == spec.get("sha256"), field + ".sha256", observed)
    return str(path)


def validate_carrier(binding, worker=False):
    carrier = binding["execution"]["carrier"]
    host = platform.system().lower() + "_" + platform.machine().lower()
    require(host == carrier.get("platform"), "carrier.platform", host)
    noodle = executable_identity(carrier.get("noodle"), "carrier.noodle")
    result = {"noodle": noodle}
    if worker:
        codex = carrier.get("codex")
        result["codex"] = executable_identity(codex, "carrier.codex")
        require(isinstance(codex.get("argv"), list) and bool(codex["argv"])
                and all(isinstance(a, str) and "\0" not in a for a in codex["argv"]),
                "carrier.codex.argv", codex.get("argv"))
        require(isinstance(codex.get("model"), str) and bool(codex["model"]),
                "carrier.codex.model", codex.get("model"))
    return result


def read_owner(binding):
    root = Path(binding["execution"]["control_root"]).resolve()
    path = root / ".noodle/state.snapshot.json"
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise AdmissionRefusal("noodle.snapshot", str(error), "Noodle", "canonical_checkpoint_readback") from error
    require(isinstance(state, dict) and isinstance(state.get("state"), dict),
            "noodle.snapshot", state, owner="Noodle", required="canonical_checkpoint_readback")
    require(isinstance(state["state"].get("orders"), dict),
            "noodle.orders", state["state"].get("orders"), owner="Noodle", required="canonical_checkpoint_readback")
    require(isinstance(state.get("effect_ledger"), list),
            "noodle.effect_ledger", state.get("effect_ledger"), owner="Noodle", required="canonical_checkpoint_readback")
    for record in state["effect_ledger"]:
        require(isinstance(record, dict) and isinstance(record.get("effect"), dict),
                "noodle.effect_ledger.record", record, owner="Noodle", required="canonical_checkpoint_readback")
        effect = record["effect"]
        if effect.get("type") == "initial_admission":
            require(isinstance(effect.get("payload"), dict) and isinstance(effect["payload"].get("order_id"), str),
                    "noodle.initial_admission", effect, owner="Noodle", required="canonical_checkpoint_readback")
    revision = state.get("order_revision")
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{32}", revision),
            "noodle.order_revision", revision, owner="Noodle", required="current_order_revision")
    return state


def context(envelope_path, envelope_digest, root, reader):
    envelope = load_external_envelope(envelope_path, envelope_digest, root)
    readback = reader(envelope["issue"])
    return validate_issue(readback, envelope)


def quiescent_order(binding, state):
    """Read the canonical attempts and their Noodle-owned process groups.

    This is a bounded local readback, not a new lease or permission to retry.
    A recycled PID or an unreadable process remains a refusal.
    """
    order_id = binding["execution"]["order_id"]
    order = state["state"]["orders"].get(order_id)
    require(isinstance(order, dict) and isinstance(order.get("stages"), list) and bool(order["stages"]),
            "takeover.order", order, owner="Noodle", required="canonical_order_readback")
    observations = []
    for stage in order["stages"]:
        require(isinstance(stage, dict) and stage.get("status") in ("review", "completed", "failed", "cancelled"),
                "takeover.stage", stage, owner="Noodle", required="quiescent_writer_and_session_readback")
        attempts = stage.get("attempts")
        require(isinstance(attempts, list) and bool(attempts), "takeover.attempts", attempts,
                owner="Noodle", required="canonical_attempt_readback")
        for attempt in attempts:
            require(isinstance(attempt, dict) and attempt.get("status") in ("completed", "failed", "cancelled"),
                    "takeover.prior_writer", attempt, owner="Noodle", required="quiescent_writer_and_session_readback")
            session = attempt.get("session_id")
            require(isinstance(session, str) and re.fullmatch(r"[a-zA-Z0-9-]+", session), "takeover.session", session,
                    owner="Noodle", required="canonical_attempt_readback")
            directory = Path(binding["execution"]["control_root"]) / ".noodle/sessions" / session
            try:
                process = json.loads((directory / "process.json").read_text())
            except (OSError, ValueError) as error:
                raise AdmissionRefusal("takeover.process", str(error), "Noodle", "process_group_readback") from error
            require(isinstance(process, dict) and process.get("session_id") == session
                    and type(process.get("pid")) is int and process["pid"] > 1,
                    "takeover.process", process, owner="Noodle", required="process_group_readback")
            for target in (process["pid"], -process["pid"]):
                try:
                    os.kill(target, 0)
                except ProcessLookupError:
                    continue
                except PermissionError as error:
                    raise AdmissionRefusal("takeover.process", str(error), "Noodle", "process_group_readback") from error
                raise AdmissionRefusal("takeover.process_alive", target, "Noodle", "quiescent_writer_and_session_readback")
            observations.append({"session_id": session, "pid": process["pid"], "process_and_group_absent": True})
    require(read_owner(binding)["state"]["orders"].get(order_id) == order,
            "takeover.owner_changed", order_id, owner="Noodle", required="fresh_canonical_checkpoint")
    return observations


def projection(binding, envelope_digest, route):
    return {"repository": binding["repository"], "issue": binding["issue"],
            "body_sha256": binding["body_sha256"], "body_updated_at": binding["body_updated_at"],
            "envelope_sha256": envelope_digest, "route": route, "task": binding["execution"]["task"]}


def publish_once(path, proposal):
    """Use Noodle's one mailbox without replacing an outstanding proposal."""
    data = (json.dumps(proposal, sort_keys=True) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".soodles-proposal-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(name, path)
        except FileExistsError:
            # This is owner readback, not permission to overwrite/retry a write.
            try:
                current = path.read_bytes()
            except FileNotFoundError as error:
                raise AdmissionRefusal("noodle.proposal", "changed during owner readback",
                                       "Noodle", "fresh_canonical_checkpoint") from error
            require(current == data, "noodle.proposal", "different outstanding proposal",
                    owner="Noodle", required="pending_proposal_readback")
            return False
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return True
    finally:
        os.unlink(name)


def _admit(envelope_path, envelope_digest, root, reader, route):
    root = Path(root).resolve()
    binding = context(envelope_path, envelope_digest, root, reader)
    execution = binding["execution"]
    require(root == Path(execution["control_root"]).resolve(), "execution.control_root", str(root))
    validate_carrier(binding)
    state = read_owner(binding)
    order_id = execution["order_id"]
    orders = state["state"]["orders"]
    if order_id in orders:
        order = orders[order_id]
        require(isinstance(order, dict) and isinstance(order.get("stages"), list),
                "noodle.order", order, owner="Noodle", required="canonical_order_readback")
        for stage in order["stages"]:
            require(isinstance(stage, dict) and isinstance(stage.get("attempts"), list)
                    and all(isinstance(a, dict) for a in stage["attempts"]),
                    "noodle.stage", stage, owner="Noodle", required="canonical_order_readback")
        live = [a for stage in order["stages"] for a in stage.get("attempts", [])
                if a.get("status") in ("launching", "running")]
        if route == "supervised":
            require(not live, "takeover.prior_writer", live,
                    owner="Noodle", required="quiescent_writer_and_session_readback")
            quiescent_order(binding, state)
        return {"owner": "Noodle", "action": "owned", "binding": binding,
                "next": {"kind": "input", "owner": "Noodle", "required": ["current_order_and_session_readback"],
                         "known": {"order_id": order_id}}, "published": False}
    for record in state["effect_ledger"]:
        effect = record.get("effect", {})
        if effect.get("type") == "initial_admission" and effect.get("payload", {}).get("order_id") == order_id:
            return {"owner": "Noodle", "action": "previously_admitted", "binding": binding, "published": False,
                    "next": {"kind": "input", "owner": "Noodle", "required": ["original_order_recovery"],
                             "known": {"order_id": order_id, "effect_id": record.get("effect_id")}}}
    # Proposal identity does not select the provider policy; the installed carrier does.
    codex = execution["carrier"].get("codex")
    require(isinstance(codex, dict) and isinstance(codex.get("model"), str),
            "carrier.codex", codex)
    validate_carrier(binding, worker=True)
    proposal = {"initial_revision": state["order_revision"], "orders": [{
        "id": order_id, "title": f"Execute {REPOSITORY}#{binding['issue']}",
        "rationale": "Externally admitted current Issue",
        "stages": [{"do": "execute", "with": "codex", "model": codex["model"], "runtime": "process",
                    "prompt": json.dumps(projection(binding, envelope_digest, route), sort_keys=True)}],
    }]}
    published = publish_once(root / ".noodle/orders-next.json", proposal)
    return {"owner": "Noodle", "action": "proposal_pending", "binding": binding,
            "published": published, "next": {"kind": "input", "owner": "Noodle",
            "required": ["canonical_promotion_readback"], "known": {"order_id": order_id}}}


def automatic(envelope_path, envelope_digest, root, reader=fetch_issue):
    return _admit(envelope_path, envelope_digest, root, reader, "automatic")


def supervised(envelope_path, envelope_digest, root, reader=fetch_issue):
    return _admit(envelope_path, envelope_digest, root, reader, "supervised")


def validate_worktree(root, binding):
    execution = binding["execution"]
    control = Path(execution["control_root"]).resolve()
    def git(cwd, *args):
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
        require(result.returncode == 0, "worker.git", result.stderr,
                owner="Git", required="registered_worktree_readback")
        return result.stdout.strip()
    require(git(root, "rev-parse", "--show-toplevel") == str(root),
            "worker.git.root", str(root), owner="Git", required="registered_worktree_readback")
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    expected = Path(git(control, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    require(common == expected, "worker.git.common_dir", str(common),
            owner="Git", required="registered_worktree_readback")
    branch = git(root, "branch", "--show-current")
    require(branch == execution["worktree"], "worker.git.branch", branch,
            owner="Git", required="registered_worktree_readback")
    head = git(root, "rev-parse", "HEAD")
    require(head == execution["source_head"], "worker.git.head", head,
            owner="supervisor", required="fresh_execution_envelope")
    origin = git(root, "remote", "get-url", "origin")
    require(origin in (f"https://github.com/{REPOSITORY}.git", f"git@github.com:{REPOSITORY}.git"),
            "worker.git.origin", origin, owner="Git", required="admitted_repository_identity")
    residue = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    require(not residue, "worker.git.residue", residue, owner="Git", required="clean_worker_subject")
    result = subprocess.run(["git", "merge-base", "--is-ancestor", binding["base_head"], "HEAD"],
                            cwd=root, capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "worker.git.base", binding["base_head"],
            owner="Git", required="admitted_base_ancestry")


def spawn_readback(binding, session):
    path = Path(binding["execution"]["control_root"]) / ".noodle/sessions" / session / "spawn.json"
    # Noodle writes spawn metadata immediately after starting this same process.
    # Bound this initialization observation; never start another writer on expiry.
    deadline = time.monotonic() + 2
    while True:
        try:
            spawn = json.loads(path.read_text())
            break
        except FileNotFoundError as error:
            if time.monotonic() >= deadline:
                raise AdmissionRefusal("worker.spawn", str(path), "Noodle", "current_dispatch_metadata") from error
            time.sleep(0.01)
    require(isinstance(spawn, dict), "worker.spawn", spawn, owner="Noodle", required="current_dispatch_identity")
    return spawn


def launch_checked(binding, session, root, spawn, argv, execute):
    carrier = binding["execution"]["carrier"]
    for key, expected in (("session_id", session), ("provider", "codex"), ("runtime", "process"),
                          ("worktree_path", str(root)), ("model", carrier.get("codex", {}).get("model"))):
        require(spawn.get(key) == expected, "worker.spawn." + key, spawn.get(key),
                owner="Noodle", required="current_dispatch_identity")
    identities = validate_carrier(binding, worker=True)
    require(list(argv) == carrier["codex"]["argv"], "worker.argv", list(argv))
    execute(identities["codex"], [identities["codex"], *argv])
    return {"owner": "Noodle", "action": "worker_started", "binding": binding, "session_id": session}


def worker(envelope_path, envelope_digest, root, argv, *, reader=fetch_issue, environ=None, execute=os.execv):
    environ = os.environ if environ is None else environ
    root = Path(root).resolve()
    binding = context(envelope_path, envelope_digest, root, reader)
    execution = binding["execution"]
    session = environ.get("NOODLE_SESSION_ID")
    require(isinstance(session, str) and re.fullmatch(r"[a-zA-Z0-9-]+", session),
            "worker.session_id", session, owner="Noodle", required="current_dispatch_identity")
    spawn = spawn_readback(binding, session)
    state = read_owner(binding)
    if spawn.get("skill") == "schedule":
        require(root == Path(execution["control_root"]).resolve(), "scheduler.control_root", str(root))
        require(environ.get("NOODLE_WORKTREE") == str(root), "scheduler.worktree", environ.get("NOODLE_WORKTREE"),
                owner="Noodle", required="current_dispatch_identity")
        schedule = state["state"]["orders"].get("schedule")
        require(isinstance(schedule, dict) and isinstance(schedule.get("stages"), list)
                and len(schedule["stages"]) == 1, "scheduler.order", schedule,
                owner="Noodle", required="current_schedule_readback")
        stage = schedule["stages"][0]
        require(isinstance(stage, dict) and stage.get("status") in ("dispatching", "running"),
                "scheduler.stage", stage, owner="Noodle", required="current_schedule_readback")
        attempts = stage.get("attempts", [])
        require(isinstance(attempts, list) and bool(attempts) and isinstance(attempts[-1], dict)
                and attempts[-1].get("status") in ("launching", "running")
                and attempts[-1].get("session_id") in ("", session)
                and all(isinstance(a, dict) and a.get("status") not in ("launching", "running") for a in attempts[:-1]),
                "scheduler.attempts", attempts, owner="Noodle", required="current_schedule_readback")
        return launch_checked(binding, session, root, spawn, argv, execute)
    expected_root = (Path(execution["control_root"]) / ".worktrees" / execution["worktree"]).resolve()
    require(root == expected_root, "worker.worktree", str(root))
    validate_worktree(root, binding)
    for key, expected in (("NOODLE_PROJECT_DIR", execution["control_root"]),
                          ("NOODLE_WORKTREE", str(expected_root)),
                          ("NOODLE_ORDER_ID", execution["order_id"]),
                          ("NOODLE_STAGE_INDEX", str(execution["stage_index"]))):
        require(environ.get(key) == expected, "worker." + key, environ.get(key),
                owner="Noodle", required="current_dispatch_identity")
    order = state["state"]["orders"].get(execution["order_id"])
    require(isinstance(order, dict) and isinstance(order.get("stages"), list) and len(order["stages"]) == 1,
            "worker.order", order, owner="Noodle", required="current_dispatch_identity")
    stage = order["stages"][0]
    require(isinstance(stage, dict), "worker.stage", stage, owner="Noodle", required="current_dispatch_identity")
    require(stage.get("status") in ("dispatching", "running"), "worker.stage.status", stage.get("status"),
            owner="Noodle", required="current_dispatch_identity")
    try:
        subject = json.loads(stage.get("prompt", ""))
    except (ValueError, TypeError) as error:
        raise AdmissionRefusal("worker.stage.prompt", str(error), "Noodle", "admitted_order_readback") from error
    require(isinstance(subject, dict) and subject.get("route") in ("automatic", "supervised"),
            "worker.stage.binding", subject)
    require(subject == projection(binding, envelope_digest, subject["route"]), "worker.stage.binding", subject)
    attempts = stage.get("attempts", [])
    require(isinstance(attempts, list) and bool(attempts) and all(isinstance(a, dict) for a in attempts), "worker.attempts", attempts,
            owner="Noodle", required="current_dispatch_identity")
    current = attempts[-1]
    require(current.get("status") in ("launching", "running")
            and current.get("session_id") in ("", session)
            and not any(a.get("status") in ("launching", "running") for a in attempts[:-1]),
            "worker.attempt", attempts, owner="Noodle", required="quiescent_prior_attempt")
    # This replaces the Noodle-owned process; it cannot create a parallel writer.
    require(spawn.get("skill") == "execute", "worker.spawn.skill", spawn.get("skill"),
            owner="Noodle", required="current_dispatch_identity")
    return launch_checked(binding, session, root, spawn, argv, execute)


def refusal_output(error, operation):
    return {"owner": "issue." + operation, "status": "refused", "invalid": error.invalid, "next": error.next}
