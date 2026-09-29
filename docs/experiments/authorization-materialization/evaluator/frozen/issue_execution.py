"""Consumers for one externally admitted Issue; Noodle owns scheduling/state.

Provider reads are live by default. Test callers may supply a reader explicitly.
Only the existing orders-next mailbox is written; no independent order ledger,
lock or retry loop is introduced. An installed supervisor launcher fixes the
external envelope path/digest and this implementation before executing it.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import shutil
import sys
import tempfile
import time

from issue_admission import (AdmissionRefusal, load_external_envelope,
                             require, validate_issue)
from repository_binding import git_origins


def fetch_issue(repository, number):
    # Landing consumes supplied readbacks and must not load a credential reader.
    # Automatic/supervised/worker retain the same default callable boundary.
    from github_reader import fetch_issue as read
    return read(repository, number)


def inspect_schedule(root, environ=None):
    """Project current Noodle role and supervisor capability without effects."""
    environ = os.environ if environ is None else environ
    session = environ.get("NOODLE_SESSION_ID")
    result = {"owner": "issue.inspect", "authorizes_landing": False}
    if not session:
        return {**result, "action": "not_applicable", "next": None}
    source = {"owner": "Noodle", "required": "current_dispatch_identity"}
    require(isinstance(session, str) and re.fullmatch(r"[a-zA-Z0-9-]+", session),
            "scheduler.session_id", session, **source)
    root = Path(root).resolve()
    # Scheduler dispatch supplies NOODLE_WORKTREE; PROJECT_DIR is worker-only.
    control = environ.get("NOODLE_WORKTREE")
    require(isinstance(control, str) and Path(control).is_absolute()
            and Path(control).resolve() == root,
            "scheduler.control_root", control, **source)
    path = root / ".noodle/sessions" / session / "spawn.json"
    try:
        spawn = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise AdmissionRefusal("scheduler.spawn", str(path), **source) from error
    require(isinstance(spawn, dict), "scheduler.spawn", str(path), **source)
    for key, expected in (("session_id", session), ("skill", "schedule")):
        require(spawn.get(key) == expected, "scheduler.spawn." + key,
                spawn.get(key), **source)
    worktree = spawn.get("worktree_path")
    require(isinstance(worktree, str) and Path(worktree).is_absolute()
            and Path(worktree).resolve() == root,
            "scheduler.spawn.worktree_path", worktree, **source)
    launcher = environ.get("SOODLES_ADMISSION_LAUNCHER")
    require(isinstance(launcher, str) and Path(launcher).is_absolute()
            and Path(launcher).is_file() and os.access(launcher, os.X_OK),
            "scheduler.launcher", launcher, owner="supervisor",
            required="SOODLES_ADMISSION_LAUNCHER")
    return {**result, "action": "ready", "session_id": session,
            "next": {"kind": "executable", "owner": "supervisor",
                     "operation": "automatic", "argv": [launcher, "automatic"]}}


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


READINESS_HANDOFF_FIELDS = {
    "schema", "kind", "repository", "origin_issue", "origin_pr", "selection",
    "task", "arms", "cases", "primary_outcome", "permitted_effects",
}
READINESS_LOCAL_FIELDS = {
    "schema", "owner", "origin_issue", "carrier", "input_root",
    "evidence_root", "output_root", "workdirs", "python",
}
READINESS_ARTIFACT_FIELDS = {"path", "sha256"}
READINESS_ARM_FIELDS = {"ref", "instruction", "replay"}
READINESS_REPLAY_FIELDS = {"script", "observer", "decider"}
READINESS_CASE_FIELDS = {"id", "inputs"}
READINESS_CASE_INPUTS = {"raw", "gates", "manifest"}


def _readiness_exact(value, fields, field, required="portable_experiment_handoff"):
    require(isinstance(value, dict) and set(value) == fields, field,
            sorted(value) if isinstance(value, dict) else value,
            owner="supervisor", required=required)


def _readiness_sha(value, length, field, required):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value),
            field, value, owner="supervisor", required=required)
    return value


def _readiness_portable_path(value, field):
    valid = (isinstance(value, str) and bool(value) and not value.startswith("/")
             and "\\" not in value and not any(ord(c) < 32 or ord(c) == 127 for c in value))
    if valid:
        parts = value.split("/")
        valid = (all(p and p not in (".", "..") and p.lower() != ".git" for p in parts)
                 and str(PurePosixPath(value)) == value)
    require(valid, field, value, owner="supervisor", required="corrected_experiment_handoff")
    return value


def _readiness_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _readiness_bound_json(path, expected_sha256, field, required):
    path = Path(path)
    require(path.is_absolute(), field + ".path", str(path), owner="supervisor", required=required)
    _readiness_sha(expected_sha256, 64, field + ".sha256", required)
    require(path.is_file() and not path.is_symlink(), field + ".path", str(path),
            owner="supervisor", required=required)
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    require(actual == expected_sha256, field + ".sha256", actual,
            owner="supervisor", required=required)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_readiness_unique,
                           parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise AdmissionRefusal(field, type(error).__name__, "supervisor", required) from None
    require(isinstance(value, dict), field, type(value).__name__,
            owner="supervisor", required=required)
    return value, actual, path.resolve()


def _readiness_artifact(root, spec, field):
    _readiness_exact(spec, READINESS_ARTIFACT_FIELDS, field, "selected_experiment_inputs")
    rel = _readiness_portable_path(spec["path"], field + ".path")
    _readiness_sha(spec["sha256"], 64, field + ".sha256", "selected_experiment_inputs")
    path = (root / rel).resolve()
    require(path.is_relative_to(root) and path.is_file() and not path.is_symlink(),
            field + ".path", str(path), owner="supervisor", required="selected_experiment_inputs")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == spec["sha256"], field + ".sha256", actual,
            owner="supervisor", required="selected_experiment_inputs")
    return {"path": str(path), "sha256": actual}


def _readiness_git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "readiness.git." + ".".join(args[:2]),
            result.stderr.strip(), owner="supervisor", required="exact_local_workdirs")
    return result.stdout.strip()


def _readiness_workdir(path, expected_ref, repository, arm):
    path = Path(path)
    require(path.is_absolute() and path.is_dir() and not path.is_symlink(),
            "local.workdirs." + arm, str(path),
            owner="supervisor", required="exact_local_workdirs")
    path = path.resolve()
    head = _readiness_git(path, "rev-parse", "HEAD")
    require(head == expected_ref, "local.workdirs." + arm + ".head", head,
            owner="supervisor", required="exact_local_workdirs")
    status = _readiness_git(path, "status", "--porcelain", "--untracked-files=all")
    require(status == "", "local.workdirs." + arm + ".status", status,
            owner="supervisor", required="clean_exact_local_workdirs")
    origin = _readiness_git(path, "remote", "get-url", "origin")
    require(origin in git_origins(repository), "local.workdirs." + arm + ".origin", origin,
            owner="supervisor", required="exact_local_workdirs")
    return path


def _readiness_executable(spec, field):
    _readiness_exact(spec, READINESS_ARTIFACT_FIELDS, field, "exact_local_executable")
    path = Path(spec["path"])
    require(path.is_absolute() and path.is_file() and os.access(path, os.X_OK)
            and not path.is_symlink(), field + ".path", str(path),
            owner="supervisor", required="exact_local_executable")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == spec["sha256"], field + ".sha256", actual,
            owner="supervisor", required="exact_local_executable")
    return str(path.resolve())


def readiness(handoff_path, handoff_digest, local_path, local_digest):
    """Materialize six selected experiment runs without launching a consumer."""
    handoff, handoff_sha, handoff_source = _readiness_bound_json(
        handoff_path, handoff_digest, "handoff", "portable_experiment_handoff")
    local, local_sha, local_source = _readiness_bound_json(
        local_path, local_digest, "local", "host_local_execution_binding")
    _readiness_exact(handoff, READINESS_HANDOFF_FIELDS, "handoff")
    _readiness_exact(local, READINESS_LOCAL_FIELDS, "local",
                     "host_local_execution_binding")
    require(handoff["schema"] == 1 and handoff["kind"] == "pclass-local-experiment",
            "handoff.identity", [handoff.get("schema"), handoff.get("kind")],
            owner="supervisor", required="portable_experiment_handoff")
    repository = handoff["repository"]
    require(repository == "ed3c/soodles", "handoff.repository", repository,
            owner="supervisor", required="supported_repository_handoff")
    origin_issue, origin_pr = handoff["origin_issue"], handoff["origin_pr"]
    require(type(origin_issue) is int and origin_issue > 0 and type(origin_pr) is int and origin_pr > 0,
            "handoff.origin", [origin_issue, origin_pr], owner="supervisor",
            required="portable_experiment_handoff")
    require(local["schema"] == 1 and local["owner"] == "external-supervisor"
            and local["origin_issue"] == origin_issue,
            "local.identity", [local.get("schema"), local.get("owner"), local.get("origin_issue")],
            owner="supervisor", required="host_local_execution_binding")
    require(handoff["permitted_effects"] == [], "handoff.permitted_effects",
            handoff["permitted_effects"], owner="supervisor",
            required="read_only_experiment_handoff")
    require(isinstance(handoff["primary_outcome"], str) and handoff["primary_outcome"].strip(),
            "handoff.primary_outcome", handoff["primary_outcome"], owner="supervisor",
            required="portable_experiment_handoff")

    selection = handoff["selection"]
    _readiness_exact(selection, {"observer_capture", "capture_plan"},
                     "handoff.selection")
    task_spec = handoff["task"]
    _readiness_exact(task_spec, READINESS_ARTIFACT_FIELDS, "handoff.task")
    arms = handoff["arms"]
    require(isinstance(arms, dict) and set(arms) == {"baseline", "treatment"},
            "handoff.arms", sorted(arms) if isinstance(arms, dict) else arms,
            owner="supervisor", required="baseline_treatment_handoff")
    for arm, spec in arms.items():
        _readiness_exact(spec, READINESS_ARM_FIELDS, "handoff.arms." + arm)
        _readiness_sha(spec["ref"], 40, "handoff.arms." + arm + ".ref",
                       "baseline_treatment_handoff")
        _readiness_exact(spec["instruction"], READINESS_ARTIFACT_FIELDS,
                         "handoff.arms." + arm + ".instruction")
        _readiness_exact(spec["replay"], READINESS_REPLAY_FIELDS,
                         "handoff.arms." + arm + ".replay")
        for name in READINESS_REPLAY_FIELDS:
            _readiness_exact(spec["replay"][name], READINESS_ARTIFACT_FIELDS,
                             "handoff.arms." + arm + ".replay." + name)

    cases = handoff["cases"]
    require(isinstance(cases, list) and len(cases) == 3,
            "handoff.cases", cases, owner="supervisor", required="three_case_experiment_handoff")
    case_ids = []
    for index, case in enumerate(cases):
        field = "handoff.cases." + str(index)
        _readiness_exact(case, READINESS_CASE_FIELDS, field)
        case_id = case["id"]
        require(isinstance(case_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]*", case_id),
                field + ".id", case_id, owner="supervisor",
                required="three_case_experiment_handoff")
        case_ids.append(case_id)
        _readiness_exact(case["inputs"], READINESS_CASE_INPUTS, field + ".inputs")
        for name in READINESS_CASE_INPUTS:
            _readiness_exact(case["inputs"][name], READINESS_ARTIFACT_FIELDS,
                             field + ".inputs." + name)
    require(len(set(case_ids)) == 3, "handoff.cases.ids", case_ids,
            owner="supervisor", required="three_unique_cases")

    input_root = Path(local["input_root"])
    evidence_root = Path(local["evidence_root"])
    output_root = Path(local["output_root"])
    for field, path, required in (
        ("local.input_root", input_root, "selected_experiment_inputs"),
        ("local.evidence_root", evidence_root, "external_evidence_root"),
    ):
        require(path.is_absolute() and path.is_dir() and not path.is_symlink(),
                field, str(path), owner="supervisor", required=required)
    input_root, evidence_root = input_root.resolve(), evidence_root.resolve()
    require(output_root.is_absolute(), "local.output_root", str(output_root),
            owner="supervisor", required="fresh_materialization_root")
    output_root = output_root.resolve()
    require(not output_root.exists() and output_root.parent.is_dir()
            and output_root.is_relative_to(evidence_root),
            "local.output_root", str(output_root), owner="supervisor",
            required="fresh_materialization_root")

    workdirs = local["workdirs"]
    require(isinstance(workdirs, dict) and set(workdirs) == {"baseline", "treatment"},
            "local.workdirs", workdirs, owner="supervisor", required="exact_local_workdirs")
    resolved = {
        arm: _readiness_workdir(workdirs[arm], arms[arm]["ref"], repository, arm)
        for arm in ("baseline", "treatment")
    }
    require(resolved["baseline"] != resolved["treatment"], "local.workdirs",
            [str(resolved["baseline"]), str(resolved["treatment"])],
            owner="supervisor", required="distinct_exact_local_workdirs")
    for root in resolved.values():
        for field, path in (("handoff.path", handoff_source), ("local.path", local_source),
                            ("input_root", input_root), ("evidence_root", evidence_root),
                            ("output_root", output_root)):
            require(not path.is_relative_to(root), "local." + field, str(path),
                    owner="supervisor", required="external_experiment_state")

    carrier = local["carrier"]
    _readiness_exact(carrier, {"platform", "codex"}, "local.carrier",
                     "selected_experiment_carrier")
    host = platform.system().lower() + "_" + platform.machine().lower()
    require(carrier["platform"] == host, "local.carrier.platform",
            carrier["platform"], owner="supervisor",
                     required="selected_experiment_carrier")
    codex = carrier["codex"]
    _readiness_exact(codex, {"path", "sha256", "model", "argv"},
                     "local.carrier.codex", "selected_experiment_carrier")
    _readiness_executable({"path": codex["path"], "sha256": codex["sha256"]},
                          "local.carrier.codex")
    require(isinstance(codex["model"], str) and codex["model"].strip()
            and isinstance(codex["argv"], list) and codex["argv"]
            and all(isinstance(arg, str) and arg and "\0" not in arg
                    for arg in codex["argv"]),
            "local.carrier.codex", codex, owner="supervisor",
            required="selected_experiment_carrier")
    python = _readiness_executable(local["python"], "local.python")
    selected = {name: _readiness_artifact(input_root, selection[name],
                                           "handoff.selection." + name)
                for name in ("observer_capture", "capture_plan")}
    task = _readiness_artifact(input_root, task_spec, "handoff.task")

    arm_artifacts = {}
    for arm in ("baseline", "treatment"):
        root, spec = resolved[arm], arms[arm]
        arm_artifacts[arm] = {
            "instruction": _readiness_artifact(root, spec["instruction"],
                                                "handoff.arms." + arm + ".instruction"),
            "replay": {name: _readiness_artifact(
                root, spec["replay"][name],
                "handoff.arms." + arm + ".replay." + name)
                for name in ("script", "observer", "decider")},
        }

    case_artifacts = {}
    for case in cases:
        case_artifacts[case["id"]] = {
            name: _readiness_artifact(input_root, case["inputs"][name],
                                      "handoff.cases." + case["id"] + ".inputs." + name)
            for name in ("raw", "gates", "manifest")
        }

    packets = []
    for arm in ("baseline", "treatment"):
        for case in cases:
            case_id = case["id"]
            run_id = case_id + "--" + arm
            inp, replay = case_artifacts[case_id], arm_artifacts[arm]["replay"]
            argv = [python, "-B", replay["script"]["path"], inp["raw"]["path"],
                    inp["gates"]["path"], inp["manifest"]["path"], inp["manifest"]["sha256"],
                    replay["observer"]["path"], replay["decider"]["path"]]
            evidence_dir = (evidence_root / run_id).resolve()
            require(evidence_dir.parent == evidence_root and not evidence_dir.exists(),
                    "readiness.evidence_dir." + run_id, str(evidence_dir),
                    owner="supervisor", required="fresh_run_evidence_destinations")
            packets.append({
                "schema": 1,
                "origin": {"repository": repository, "issue": origin_issue, "pr": origin_pr},
                "run_id": run_id, "arm": arm, "case": case_id,
                "workspace": {"path": str(resolved[arm]), "ref": arms[arm]["ref"]},
                "task": task,
                "instruction": arm_artifacts[arm]["instruction"],
                "external_selection": selected,
                "carrier": carrier,
                "inputs": inp,
                "replay_argv": argv,
                "evidence_dir": str(evidence_dir),
                "primary_outcome": handoff["primary_outcome"],
                "permitted_effects": [],
                "authorizes_landing": False,
            })
    require(len(packets) == 6 and len({p["run_id"] for p in packets}) == 6,
            "readiness.runs", [p["run_id"] for p in packets],
            owner="supervisor", required="six_unique_run_packets")

    temporary = Path(tempfile.mkdtemp(prefix=".issue-readiness-", dir=output_root.parent))
    try:
        records = []
        for packet in packets:
            path = temporary / (packet["run_id"] + ".json")
            data = (json.dumps(packet, indent=2, sort_keys=True) + "\n").encode()
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
            records.append({"run_id": packet["run_id"],
                            "packet": str(output_root / path.name),
                            "packet_sha256": hashlib.sha256(data).hexdigest(),
                            "argv": packet["replay_argv"]})
        os.replace(temporary, output_root)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    first = records[0]
    return {
        "schema": 1, "owner": "issue.readiness", "status": "READY",
        "origin": {"repository": repository, "issue": origin_issue, "pr": origin_pr},
        "handoff_sha256": handoff_sha, "local_binding_sha256": local_sha,
        "carrier": carrier, "materialized_root": str(output_root),
        "runs": records, "authorizes_landing": False,
        "next": {"kind": "input", "owner": "supervisor",
                 "required": ["fresh_consumer_launch"],
                 "known": {"run_id": first["run_id"], "packet": first["packet"]}},
    }


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
    return state


def context(envelope_path, envelope_digest, root, reader):
    envelope = load_external_envelope(envelope_path, envelope_digest, root)
    try:
        readback = reader(envelope["repository"], envelope["issue"])
        return validate_issue(readback, envelope)
    except AdmissionRefusal as error:
        # Retain only externally pinned identity, never identity from the rejected
        # provider payload. These values locate prior input; they do not renew it.
        error.next["known"] = {"repository": envelope["repository"], "issue": envelope["issue"],
                               "envelope": str(Path(envelope_path).resolve()),
                               "envelope_digest": envelope_digest}
        raise


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


def _matching_effects(state, order_id, kind):
    matches = []
    for record in state["effect_ledger"]:
        effect = record["effect"]
        if effect.get("type") == kind and effect.get("payload", {}).get("order_id") == order_id:
            matches.append(record)
    return matches


def _absent_process(directory, session):
    try:
        process = json.loads((directory / "process.json").read_text())
    except (OSError, ValueError) as error:
        raise AdmissionRefusal("completion.process", str(error), "Noodle", "process_group_readback") from error
    require(isinstance(process, dict) and process.get("session_id") == session
            and type(process.get("pid")) is int and process["pid"] > 1,
            "completion.process", process, owner="Noodle", required="process_group_readback")
    for target in (process["pid"], -process["pid"]):
        try:
            os.kill(target, 0)
        except ProcessLookupError:
            continue
        except PermissionError as error:
            raise AdmissionRefusal("completion.process", str(error), "Noodle", "process_group_readback") from error
        raise AdmissionRefusal("completion.process_alive", target, "Noodle", "quiescent_writer_and_session_readback")
    return {"session_id": session, "pid": process["pid"], "process_and_group_absent": True}


def completed_original_order(binding, state):
    """Prove completion from the current row or Noodle's retained projection history."""
    order_id = binding["execution"]["order_id"]
    order = state["state"]["orders"].get(order_id)
    if isinstance(order, dict):
        require(order.get("status") == "completed", "completion.order.status", order.get("status"),
                owner="Noodle", required="completed_original_order_and_quiescent_sessions")
        return {"order_id": order_id, "source": "current_order", "order": order,
                "quiescent_sessions": quiescent_order(binding, state)}
    require(order is None, "completion.order", order,
            owner="Noodle", required="canonical_order_readback")

    admission = _matching_effects(state, order_id, "initial_admission")
    require(len(admission) <= 1, "completion.initial_admission", len(admission),
            owner="Noodle", required="canonical_effect_history")
    admitted = admission[0] if admission else None
    if admitted is not None:
        require(admitted.get("status") == "done"
                and admitted.get("result", {}).get("status") == "completed",
                "completion.initial_admission.status", admitted.get("status"),
                owner="Noodle", required="canonical_effect_history")

    dispatches = [record for record in _matching_effects(state, order_id, "dispatch")
                  if record["effect"].get("payload", {}).get("stage_index") == binding["execution"]["stage_index"]]
    require(len(dispatches) == 1, "completion.dispatch", len(dispatches),
            owner="Noodle", required="canonical_attempt_readback")
    projections = _matching_effects(state, order_id, "write_projection")
    acknowledgements = _matching_effects(state, order_id, "ack")
    require(len(projections) == len(acknowledgements) == 1,
            "completion.projection", {"write_projection": len(projections), "ack": len(acknowledgements)},
            owner="Noodle", required="completed_order_projection_readback")
    projected, acknowledged = projections[0]["effect"], acknowledgements[0]["effect"]
    require(projected.get("created_at") == acknowledged.get("created_at")
            and projected.get("effect_id", "").rsplit("-", 1)[0] == acknowledged.get("effect_id", "").rsplit("-", 1)[0],
            "completion.projection.pair", [projected.get("effect_id"), acknowledged.get("effect_id")],
            owner="Noodle", required="completed_order_projection_readback")

    root = Path(binding["execution"]["control_root"])
    expected_worktree = str((root / ".worktrees" / binding["execution"]["worktree"]).resolve())
    sessions = []
    session_root = root / ".noodle/sessions"
    try:
        directories = list(session_root.iterdir())
    except OSError as error:
        raise AdmissionRefusal("completion.sessions", str(error), "Noodle",
                               "original_session_readback") from error
    carrier = binding["execution"]["carrier"]
    expected_model = carrier.get("codex", {}).get("model")
    for directory in directories:
        if not directory.is_dir():
            continue
        try:
            spawn = json.loads((directory / "spawn.json").read_text())
        except (OSError, ValueError):
            continue
        if (spawn.get("skill") == "execute" and spawn.get("worktree_path") == expected_worktree
                and spawn.get("provider") == "codex" and spawn.get("model") == expected_model):
            sessions.append((directory, spawn))
    require(len(sessions) == 1, "completion.sessions", len(sessions),
            owner="Noodle", required="original_session_readback")
    directory, spawn = sessions[0]
    session = spawn.get("session_id")
    require(isinstance(session, str) and directory.name == session,
            "completion.session_id", session, owner="Noodle", required="original_session_readback")
    try:
        meta = json.loads((directory / "meta.json").read_text())
        events = [json.loads(line) for line in (directory / "events.ndjson").read_text().splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise AdmissionRefusal("completion.session", str(error), "Noodle", "original_session_readback") from error
    require(meta.get("session_id") == session and meta.get("status") == "exited" and meta.get("alive") is False,
            "completion.meta", meta, owner="Noodle", required="original_session_exit_readback")
    terminal = [event for event in events if event.get("type") == "stage_message"
                and event.get("payload", {}).get("order_id") == order_id
                and event.get("payload", {}).get("stage_index") == binding["execution"]["stage_index"]]
    require(len(terminal) == 1, "completion.typed_outcome", len(terminal),
            owner="Noodle", required="completed_typed_outcome")
    payload = terminal[0]["payload"]
    require(payload.get("outcome") == "completed" and payload.get("blocking") is False,
            "completion.typed_outcome", payload, owner="Noodle", required="completed_typed_outcome")
    quiescent = _absent_process(directory, session)
    fresh = read_owner(binding)
    require(fresh.get("order_revision") == state.get("order_revision")
            and fresh["state"]["orders"].get(order_id) is None
            and fresh["effect_ledger"] == state["effect_ledger"],
            "completion.owner_changed", order_id, owner="Noodle", required="fresh_canonical_checkpoint")
    return {"order_id": order_id, "source": "archived_projection",
            "initial_admission_effect": admitted["effect_id"] if admitted else None,
            "dispatch_effect": dispatches[0]["effect_id"],
            "projection_effects": [projections[0]["effect_id"], acknowledgements[0]["effect_id"]],
            "typed_outcome": payload, "quiescent_sessions": [quiescent]}


def projection(binding, envelope_digest, route):
    subject = {"repository": binding["repository"], "issue": binding["issue"],
            "body_sha256": binding["body_sha256"], "body_updated_at": binding["body_updated_at"],
            "envelope_sha256": envelope_digest, "route": route, "task": binding["execution"]["task"],
            "contract": binding["contract"]}
    if "instruction_context" in binding["execution"]:
        subject["instruction_context"] = binding["execution"]["instruction_context"]
    return subject


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


def _admit(envelope_path, envelope_digest, root, reader, route, *, observe_live=False):
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
        if route == "supervised" and observe_live and live:
            # The Issue-atom foreground continuation observes the existing owner;
            # it is not the stopped-writer takeover entry. Never start or reset
            # anything because canonical state still reports a live attempt.
            require(len(order["stages"]) == 1 and len(live) == 1,
                    "observe.order", order_id, owner="Noodle", required="current_dispatch_identity")
            stage = order["stages"][0]
            try:
                subject = json.loads(stage.get("prompt", ""))
            except (ValueError, TypeError) as error:
                raise AdmissionRefusal("observe.binding", order_id, "Noodle", "admitted_order_readback") from error
            require(isinstance(subject, dict) and subject.get("route") in ("automatic", "supervised")
                    and subject == projection(binding, envelope_digest, subject["route"]),
                    "observe.binding", order_id, owner="Noodle", required="admitted_order_readback")
            require(stage.get("status") in ("dispatching", "running")
                    and stage.get("skill") == "execute" and stage.get("provider") == "codex"
                    and stage.get("model") == execution["carrier"]["codex"]["model"],
                    "observe.stage", order_id, owner="Noodle", required="current_dispatch_identity")
            return {"owner": "Noodle", "action": "running", "binding": binding, "published": False,
                    "attempt": live[0], "next": continuation({"kind": "input", "owner": "Noodle",
                    "required": ["current_order_and_session_readback"], "known": {"order_id": order_id}}, route)}
        if route == "supervised":
            require(not live, "takeover.prior_writer", live,
                    owner="Noodle", required="quiescent_writer_and_session_readback")
            quiescent_order(binding, state)
        return {"owner": "Noodle", "action": "owned", "binding": binding,
                "next": continuation({"kind": "input", "owner": "Noodle", "required": ["current_order_and_session_readback"],
                         "known": {"order_id": order_id}}, route), "published": False}
    for record in state["effect_ledger"]:
        effect = record.get("effect", {})
        if (effect.get("type") in {"initial_admission", "dispatch", "write_projection", "ack"}
                and effect.get("payload", {}).get("order_id") == order_id):
            return {"owner": "Noodle", "action": "previously_admitted", "binding": binding, "published": False,
                    "next": continuation({"kind": "input", "owner": "Noodle", "required": ["original_order_recovery"],
                             "known": {"order_id": order_id, "effect_id": record.get("effect_id")}}, route)}
    # Proposal identity does not select the provider policy; the installed carrier does.
    codex = execution["carrier"].get("codex")
    require(isinstance(codex, dict) and isinstance(codex.get("model"), str),
            "carrier.codex", codex)
    validate_carrier(binding, worker=True)
    proposal = {"orders": [{
        "id": order_id, "title": f"Execute {binding['repository']}#{binding['issue']}",
        "rationale": "Externally admitted current Issue",
        "stages": [{"do": "execute", "with": "codex", "model": codex["model"], "runtime": "process",
                    "prompt": json.dumps(projection(binding, envelope_digest, route), sort_keys=True)}],
    }]}
    published = publish_once(root / ".noodle/orders-next.json", proposal)
    return {"owner": "Noodle", "action": "proposal_pending", "binding": binding,
            "published": published, "next": continuation({"kind": "input", "owner": "Noodle",
            "required": ["canonical_promotion_readback"], "known": {"order_id": order_id}}, route)}


def automatic(envelope_path, envelope_digest, root, reader=fetch_issue):
    return _admit(envelope_path, envelope_digest, root, reader, "automatic")


def supervised(envelope_path, envelope_digest, root, reader=fetch_issue, *, observe_live=False):
    return _admit(envelope_path, envelope_digest, root, reader, "supervised", observe_live=observe_live)


def resume(checkpoint, envelope_path, envelope_digest, root, reader=fetch_issue):
    """Read a completed predecessor, then use the existing admission owner.

    The supervisor supplies the predecessor checkpoint and successor envelope.
    This adds no durable state or cleanup writer. It is a sequential recovery
    boundary, not a transaction with a concurrently consuming scheduler.
    """
    import landing

    root = Path(root).resolve()
    path = Path(checkpoint).resolve()
    require(Path(checkpoint).is_absolute() and not path.is_relative_to(root),
            "resume.checkpoint", "supervisor checkpoint must be outside the control root")
    try:
        state = landing.read(path)
        require(isinstance(state, dict) and state.get("schema") == 2,
                "resume.checkpoint.schema", "expected landing checkpoint schema 2")
        claim = state.get("claim")
        require(isinstance(claim, dict), "resume.claim", "missing")
        # Historical cleanup is not a request to promote its verifier today.
        landing.validate_claim(claim, verify_verifier=False)
    except (OSError, ValueError, TypeError, KeyError, landing.LandingRefusal) as error:
        raise AdmissionRefusal("resume.checkpoint", str(error)) from error
    require(state.get("phase") == "resolved" and state.get("classification") == "RESOLVED",
            "resume.predecessor", "cleanup has not reached RESOLVED")
    require(claim.get("control_root") == str(root), "resume.control_root", claim.get("control_root"))
    local = state.get("local", {})
    require(isinstance(local, dict), "resume.cleanup", "missing local receipt")
    require(local.get("removed_worktree") == claim["worktree"]
            and local.get("worktree_owner") == "Noodle" and local.get("cleanup_mode") == "noodle",
            "resume.cleanup", "original Noodle cleanup receipt required")
    ref = claim.get("execution_envelope", {})
    require(set(ref) == {"path", "sha256"}, "resume.predecessor_envelope", ref)
    predecessor = load_external_envelope(ref["path"], ref["sha256"], root)
    execution = predecessor["execution"]
    require(predecessor["repository"] == claim["repository"],
            "resume.predecessor.repository", predecessor["repository"])
    require(predecessor["issue"] == claim["issue"]
            and execution["control_root"] == str(root) and execution["worktree"] == claim["worktree"],
            "resume.predecessor_identity", "checkpoint and envelope differ")
    successor = load_external_envelope(envelope_path, envelope_digest, root)
    require(successor["repository"] == predecessor["repository"],
            "resume.successor.repository", successor["repository"])
    require(successor["execution"]["control_root"] == str(root)
            and successor["issue"] != predecessor["issue"]
            and successor["execution"]["order_id"] != execution["order_id"]
            and successor["execution"]["worktree"] != execution["worktree"],
            "resume.successor_identity", "distinct successor in the same control root required")
    worktree = root / ".worktrees" / claim["worktree"]
    require(not os.path.lexists(worktree), "resume.cleanup.path", str(worktree))

    def git(*argv):
        result = subprocess.run(["git", *argv], cwd=root, capture_output=True, text=True)
        require(result.returncode == 0, "resume.git", result.stderr)
        return result.stdout.strip()

    require(not git("branch", "--list", claim["worktree"]), "resume.cleanup.branch", claim["worktree"])
    registrations = git("worktree", "list", "--porcelain").splitlines()
    require("worktree " + str(worktree) not in registrations
            and "branch refs/heads/" + claim["worktree"] not in registrations,
            "resume.cleanup.registration", claim["worktree"])
    completion = completed_original_order(predecessor, read_owner(predecessor))
    # Keep the automatic proposal bytes unchanged so an unknown publication is
    # recognized by publish_once; current and retained ownership stay with Noodle.
    result = _admit(envelope_path, envelope_digest, root, reader, "automatic")
    result["next"] = continuation(result["next"], "resume")
    result["predecessor"] = {"checkpoint": str(path), "order_id": execution["order_id"],
                             "completion": completion, "cleanup": "absent"}
    return result


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
    require(origin in git_origins(binding["repository"]),
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


def continuation(next_action, operation):
    # The invoked boundary owns this route; invalid-field text never selects it.
    return {**next_action, "operation": operation,
            "help_argv": [sys.executable, "-B", str(Path(__file__).resolve().parent / "soodles.py"),
                          "issue", *([operation] if operation else []), "--help"],
            "reason": ("Obtain changed input/readback from the named owner before re-entering this boundary. "
                       "Preserve existing identity and history; do not retry unchanged input. "
                       "Worker entry remains Noodle-dispatched; help does not authorize another writer.")}


def refusal_output(error, operation):
    return {"owner": "issue." + operation, "status": "wait" if getattr(error, "exit_code", 1) == 75 else "refused", "invalid": error.invalid,
            "next": continuation(error.next, operation)}


def refusal_text(result):
    next_action, invalid = result["next"], result["invalid"]
    return (f"REFUSED: {result['owner']}: invalid {invalid['field']}={invalid['value']!r}; "
            f"owner: {next_action['owner']}; required: {next_action['required']}; "
            f"continuation: issue {next_action['operation']}; {next_action['reason']}")
