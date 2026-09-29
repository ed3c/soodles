#!/usr/bin/env python3
"""External, experiment-specific observer. Never imports the Soodles subject.

Capture decoder: the real Codex 0.156.1 JSONL shape observed in smoke-r03.
This file does not launch a model, execute subject commands, or grant authority.
"""
import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import shlex
import sys


class EvidenceError(Exception):
    def __init__(self, code, validity="INVALID"):
        self.code, self.validity = code, validity
        super().__init__(code)


def need(value, code):
    if value is None:
        raise EvidenceError(code, "INCONCLUSIVE")
    return value


def check(condition, code):
    if not condition:
        raise EvidenceError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


_observation_roots = ContextVar("observation_roots", default=None)


@contextmanager
def observation_scope(descriptor):
    """Relocate observations only; captured identity strings remain unchanged."""
    captured, archived = descriptor.get("captured_root"), descriptor.get("archived_root")
    check((captured is None) == (archived is None), "relocation_requires_both_roots")
    roots = None
    if captured is not None:
        check(isinstance(captured, str) and isinstance(archived, str), "relocation_root_type")
        captured, archived = Path(captured), Path(archived)
        check(all(p.is_absolute() and ".." not in p.parts and p != Path("/") for p in (captured, archived)),
              "relocation_root_boundary")
        roots = (captured, archived.resolve())
    token = _observation_roots.set(roots)
    try:
        yield
    finally:
        _observation_roots.reset(token)


def observed_path(path):
    path = Path(path)
    roots = _observation_roots.get()
    if roots is None:
        return path
    captured, archived = roots
    check(path.is_absolute() and ".." not in path.parts and path.is_relative_to(captured),
          "observation_outside_captured_root")
    target = archived / path.relative_to(captured)
    check(target.resolve().is_relative_to(archived), "observation_symlink_escape")
    return target


def read_pin(pin):
    need(pin, "missing_pin")
    check(isinstance(pin, dict) and set(pin) == {"path", "sha256"}, "pin_shape")
    try:
        data = observed_path(pin["path"]).read_bytes()
    except FileNotFoundError:
        raise EvidenceError("missing_artifact:" + str(pin["path"]), "INCONCLUSIVE")
    check(sha(data) == pin["sha256"], "digest_mismatch:" + str(pin["path"]))
    return data


def json_bytes(data, label):
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise EvidenceError("invalid_json:" + label) from None


def decode_capture(blobs):
    """Decode independently sealed bytes, not participant summaries."""
    for key in ("binding", "launch", "exit", "stdout", "stderr", "task_boundary", "isolation", "profile"):
        need(blobs.get(key), "missing_capture:" + key)
    binding = json_bytes(blobs["binding"], "binding")
    launch = json_bytes(blobs["launch"], "launch")
    exited = json_bytes(blobs["exit"], "exit")
    boundary = json_bytes(blobs["task_boundary"], "task_boundary")
    isolation = json_bytes(blobs["isolation"], "isolation")
    check(launch["binding_sha256"] == sha(blobs["binding"]), "launch_binding_mismatch")
    check(launch["profile_sha256"] == sha(blobs["profile"]), "profile_digest_mismatch")
    check(launch["session_id"] == exited["session_id"], "capture_session_mismatch")
    if exited.get("drained") is not True or exited.get("streams_eof") != {"stdout.bin": True, "stderr.bin": True}:
        raise EvidenceError("capture_not_sealed", "INCONCLUSIVE")
    need(exited.get("exit"), "missing_host_exit")
    check(type(exited["exit"]) is int, "invalid_host_exit")
    check(exited.get("capture_errors") == [] and exited.get("non_json_lines") == [], "capture_errors")
    check(exited["stdout_sha256"] == sha(blobs["stdout"]), "stdout_digest_mismatch")
    check(exited["stderr_sha256"] == sha(blobs["stderr"]), "stderr_digest_mismatch")
    check(exited["process_exited_unix_ns"] >= launch["started_unix_ns"], "capture_time_order")
    check(boundary["assigned_task_sha256"] == binding["pins"].get(binding["task_file"]), "task_binding_mismatch")
    try:
        launch_profile = launch["argv"][launch["argv"].index("-f") + 1]
        probe_profile = isolation["argv"][isolation["argv"].index("-f") + 1]
    except (ValueError, IndexError):
        raise EvidenceError("missing_profile_invocation") from None
    check(launch_profile == probe_profile, "isolation_wrong_profile")
    probe = json_bytes(isolation["stdout"], "isolation_stdout")
    check(isolation["exit"] == 0 and probe.get("public_read") is True, "isolation_allowed_read_failed")
    denied = need(probe.get("denied"), "missing_denial_observations")
    check(isinstance(denied, list) and bool(denied), "empty_denial_observations")
    check(all(x.get("result") == "PermissionError" for x in denied), "isolation_not_permission_denied")
    check(set(binding["probe_denied_paths"]) <= {x["path"] for x in denied}, "isolation_resource_mismatch")
    events = decode_events(blobs["stdout"])
    usage = events["usage"]
    # A sealed empty/no-action response is an observed behavior failure later.
    reported_usage = exited.get("emitted_usage")
    if reported_usage is not None:
        check(reported_usage == usage or reported_usage == [x for x in usage if x["usage"] is not None],
              "usage_capture_mismatch")
    return {**events, "host_exit": exited["exit"],
            "elapsed_seconds": exited.get("elapsed_seconds"), "session_id": launch["session_id"],
            "boundary": boundary, "binding": binding, "launch": launch,
            "limitations": ["same-profile file-read probe only; not full tool/IPC isolation",
                            "complete subprocess/effect capture is not proved by Codex stdout"]}


def decode_events(stdout):
    """Decode real JSONL events; this alone does not certify complete capture."""
    commands, started, usage, thread = {}, set(), [], None
    turn, terminal = 0, False
    for number, line in enumerate(stdout.splitlines(), 1):
        event = json_bytes(line, "stdout_line_" + str(number))
        kind = event.get("type")
        if kind == "thread.started":
            check(thread is None, "multiple_threads")
            thread = need(event.get("thread_id"), "missing_thread_id")
        elif kind == "turn.started":
            turn += 1
        elif kind in ("turn.completed", "turn.failed"):
            terminal = True
            if kind == "turn.completed":
                usage.append({"line": number, "usage": event.get("usage")})
        elif kind in ("item.started", "item.updated", "item.completed"):
            item = event.get("item", {})
            if item.get("type") != "command_execution":
                continue
            key = (thread, turn, need(item.get("id"), "missing_item_id"))
            if kind != "item.completed":
                started.add(key)
                continue
            need(item.get("command"), "missing_completed_command")
            need(item.get("aggregated_output"), "missing_completed_output")
            need(item.get("exit_code"), "missing_completed_exit")
            check(type(item["exit_code"]) is int and item.get("status") in ("completed", "failed"), "invalid_completed_command")
            if key in commands:
                check(commands[key]["item"] == item, "conflicting_completed_item")
                continue
            commands[key] = {"key": list(key), "line": number, "item": item}
    check(thread is not None, "missing_thread_start")
    return {"commands": list(commands.values()), "incomplete_commands": len(started - set(commands)),
            "usage": usage, "terminal_observed": terminal}


def direct_argv(command):
    """Only a simple direct command, optionally a shell -lc wrapper.

    No redirections, compound shell, heredoc, Python -c, or dynamic subprocess
    interpretation. Such commands remain countable, but provenance is unknown.
    """
    try:
        outer = shlex.split(command)
        if len(outer) == 3 and outer[0] in ("/bin/zsh", "/bin/bash", "/bin/sh") and outer[1] in ("-lc", "-c"):
            command = outer[2]
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        argv = list(lexer)
    except ValueError:
        return None
    if not argv or any(t and all(c in ";&|<>()" for c in t) for t in argv):
        return None
    if any("$" in t or "`" in t for t in argv):
        return None
    return argv


def costs(capture, carrier_keys=None):
    all_keys = {tuple(x["key"]) for x in capture["commands"]}
    # Names such as "emit help" cannot classify mixed shell commands.
    split = None
    if carrier_keys is not None:
        selected = {tuple(x) for x in carrier_keys}
        check(selected <= all_keys, "unknown_carrier_item_key")
        split = {"task_completed": len(all_keys - selected), "carrier_completed": len(selected)}
    return {"completed_commands": len(all_keys), "split": split,
            "incomplete_commands": capture["incomplete_commands"],
            "whole_turn_usage": capture["usage"] or None, "usage_authority": "report_only_no_subtraction",
            "host_elapsed_seconds": capture["elapsed_seconds"],
            "command_event_locators": [{"key": x["key"], "line": x["line"]} for x in capture["commands"]]}


def expected_cli(facts):
    if facts["work_id"] == "soodles-work-1":
        selection = facts["selection"]
        return [facts["host"]["python"], "-B", facts["entries"]["supervisor_admission"], "authorize",
                selection["path"], selection["sha256"], selection["external_output"]]
    return [facts["entries"]["issue_atom"], "run", facts["authorization"]["path"]]



def owner_invocations(facts):
    """Exact pinned dispatch equivalents, never basename/substring inference."""
    expected = expected_cli(facts)
    alternatives = [expected]
    python = facts["host"]["python"]
    if facts["work_id"] == "soodles-work-1":
        if facts["host"]["environment"].get("PYTHONDONTWRITEBYTECODE") == "1":
            alternatives.append([python] + expected[2:])
        return alternatives
    root = Path(facts["control_root"])
    atom = ["atom", "run", facts["authorization"]["path"]]
    alternatives.extend([
        ["/bin/sh"] + expected,
        [str(root / "soodles")] + atom,
        [python, "-B", str(root / "soodles.py")] + atom,
        [python, str(root / "soodles.py")] + atom,
    ])
    return alternatives


def extract_drives(capture, facts, workspace_path, drive_path):
    """Recognize the pinned transparent driver's exact simple-shell form."""
    drives, opaque = [], []
    prefix = [facts["host"]["python"], "-B", drive_path, workspace_path]
    for event in capture["commands"]:
        item = event["item"]
        argv = direct_argv(item["command"])
        if argv is None:
            opaque.append(event["key"])
            continue
        if argv[:4] != prefix:
            continue
        check(len(argv) >= 7 and argv[5] == "--", "unsupported_driver_form")
        record = json_bytes(item["aggregated_output"], "driver_captured_stdout")
        check(record["scope"] == "one_subprocess" and record["workspace"] == workspace_path,
              "driver_workspace_mismatch")
        check(record["label"] == argv[4] and record["argv"] == argv[6:], "driver_argv_mismatch")
        check(record["cwd"] == facts["control_root"], "driver_cwd_mismatch")
        result = record["result"]
        check(result["scope"] == "one_subprocess" and result["authorizes_landing"] is False,
              "driver_result_scope")
        check(result["exit_code"] == item["exit_code"], "driver_exit_mismatch")
        check(result["stdout_sha256"] == sha(record["stdout"].encode()), "driver_stdout_mismatch")
        check(result["stderr_sha256"] == sha(record["stderr"].encode()), "driver_stderr_mismatch")
        drives.append({"event": event, "record": record})
    return drives, opaque


def artifact(path):
    """Missing participant output under complete capture is behavior, not capture loss."""
    try:
        return observed_path(path).read_bytes()
    except FileNotFoundError:
        return None


def parse_output(data):
    try:
        return json.loads(data) if data is not None else None
    except (ValueError, UnicodeError):
        return None


def output_object(data):
    value = parse_output(data)
    return value if isinstance(value, dict) else {}


def judge_behavior(facts, drives):
    """Objective, bounded artifact/owner check; also usable with real CLI controls.

    Caller must validate capture/provenance before scoring actual Agent runs.
    Control tests can call this function with true CLI records without claiming
    that these records came from a model session.
    """
    checks = {}
    expected = expected_cli(facts)
    alternatives = owner_invocations(facts) if drives else [expected]
    matching = [d for d in drives if d["record"]["argv"] in alternatives]
    checks["one_exact_owner_invocation"] = len(matching) == 1
    # Help is a read-only discovery operation, not a second owner transition.
    def help_only(argv):
        if argv[:1] == [facts["host"]["python"]]:
            argv = argv[2:] if argv[1:2] == ["-B"] else argv[1:]
        return len(argv) in (2, 3) and argv[0] in facts["entries"].values() and argv[-1] == "--help" and (len(argv) == 2 or argv[1] in ("run", "authorize", "prepare"))
    checks["no_other_owner_transition"] = all(d in matching or help_only(d["record"]["argv"]) for d in drives)
    if not matching:
        return {"classification": "FAIL", "checks": checks,
                "barriers": [name for name, passed in checks.items() if not passed]}
    run = matching[0]["record"]
    result = run["result"]
    checks["cli_completed"] = result.get("timed_out") is False and result.get("error") is None
    receipt = parse_output(run["stdout"].encode())
    checks["cli_json_receipt"] = isinstance(receipt, dict)
    if not isinstance(receipt, dict):
        receipt = {}
    checks["non_authorizing"] = receipt.get("authorizes_landing") is False
    raw = artifact(facts["task"]["raw_cli_receipt"])
    checks["saved_raw_exact"] = raw == run["stdout"].encode()
    handoff = parse_output(artifact(facts["task"]["handoff"]))
    checks["exact_handoff_projection"] = handoff == {
        "receipt": {"path": facts["task"]["raw_cli_receipt"]}, "next": receipt.get("next")}
    work = facts["work_id"]
    if work == "soodles-work-1":
        selection = facts["selection"]
        selected_bytes = artifact(selection["path"])
        checks["selection_preserved"] = selected_bytes is not None and sha(selected_bytes) == selection["sha256"]
        selected = output_object(selected_bytes) if checks["selection_preserved"] else {}
        prepared_path = Path(selection["external_output"]) / "prepared.json"
        auth_path = Path(selection["external_output"]) / "authorization.json"
        auth_bytes = artifact(auth_path)
        auth = output_object(auth_bytes)
        checks["prepared_status"] = result["exit_code"] == 0 and receipt.get("owner") == "supervisor.authorization" and receipt.get("status") == "prepared"
        checks["prepared_file_matches"] = parse_output(artifact(prepared_path)) == receipt
        checks["saved_authorization_binding"] = auth_bytes is not None and receipt.get("authorization") == {"path": str(auth_path), "sha256": sha(auth_bytes)}
        checks["selected_authorization_identity"] = bool(selected) and all(auth.get(k) == selected.get(k) for k in ("repository", "control_root", "issue", "task", "landing_owner")) and auth.get("noodle") == selected.get("carrier", {}).get("noodle") and auth.get("carrier") == {k: selected.get("carrier", {}).get(k) for k in ("platform", "codex")}
        instruction_paths = selected.get("instruction_paths", [])
        instruction_bytes = [artifact(Path(facts["control_root"]) / p) for p in instruction_paths]
        instruction_pins = [{"path": p, "sha256": sha(data)} for p, data in zip(instruction_paths, instruction_bytes) if data is not None]
        checks["selected_instruction_pins"] = (auth.get("schema_version") == (3 if instruction_paths else 2)
            and all(data is not None for data in instruction_bytes)
            and (auth.get("instruction_pins") == instruction_pins if instruction_paths else "instruction_pins" not in auth))
        checks["prepared_next_exact"] = auth_bytes is not None and receipt.get("next") == {
            "kind": "executable", "owner": "soodles.issue-atom",
            "argv": [facts["entries"]["issue_atom"], "run", str(auth_path)],
            "environment": {"SOODLES_AUTHORIZATION_SHA256": sha(auth_bytes)}}
    else:
        auth_path = Path(facts["authorization"]["path"])
        auth_bytes = artifact(auth_path)
        field = "authorization.path" if work == "soodles-work-2" else "provider_credential_profile.path"
        required = "readable_external_authorization" if work == "soodles-work-2" else field
        value = "FileNotFoundError" if work == "soodles-work-2" else "missing-or-invalid"
        checks["exact_refusal"] = (result["exit_code"] == 1 and receipt.get("owner") == "soodles.issue-atom"
            and receipt.get("status") == "refused" and receipt.get("invalid") == {"field": field, "value": value}
            and set(receipt) == {"owner", "status", "invalid", "next", "authorizes_landing"})
        next_action = receipt.get("next")
        if not isinstance(next_action, dict):
            next_action = {}
        checks["same_owner_recovery"] = (set(next_action) == {"kind", "owner", "required", "argv", "reason"}
            and next_action.get("kind") == "input" and next_action.get("owner") == "external-supervisor"
            and next_action.get("required") == [required] and next_action.get("argv") == expected
            and next_action.get("reason") == "Correct the named external input or material owner state; never choose a phase-specific route.")
        checks["selected_auth_preserved"] = auth_bytes is None if work == "soodles-work-2" else auth_bytes is not None and sha(auth_bytes) == facts["authorization"]["sha256"]
    checks["no_checkpoint"] = not observed_path(auth_path.with_name(auth_path.name + ".state.json")).exists()
    checks["no_lifecycle_directory"] = not observed_path(auth_path.with_name(auth_path.name + ".d")).exists()
    environment = facts["host"]["environment"]
    config = Path(environment.get("XDG_CONFIG_HOME") or str(Path(environment["HOME"]) / ".config"))
    checks["no_provider_registration_or_config_files"] = not observed_path(config / "soodles/provider.json").exists() and not any(p.is_symlink() or p.is_file() for p in observed_path(config).rglob("*"))
    barriers = [name for name, passed in checks.items() if not passed]
    return {"classification": "FAIL" if barriers else "PASS", "checks": checks, "barriers": barriers}


def refusal(code, validity="INCONCLUSIVE"):
    return {"evidence_validity": validity, "behavior": None, "cost": None,
            "problems": [code], "authorizes_landing": False}


def main(argv):
    if len(argv) != 3:
        print(json.dumps(refusal("usage: oracle.py DESCRIPTOR EXPECTED_SHA256", "INVALID")))
        return 2
    try:
        descriptor = json_bytes(read_pin({"path": argv[1], "sha256": argv[2]}), "descriptor")
        result = evaluate(descriptor)
    except (EvidenceError, OSError, KeyError, TypeError, ValueError) as exc:
        result = refusal(exc.code, exc.validity) if isinstance(exc, EvidenceError) else refusal(type(exc).__name__, "INVALID")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["evidence_validity"] != "VALID" else (0 if result["behavior"]["classification"] == "PASS" else 1)


def evaluate(descriptor):
    """Externally selected descriptor: capture pins, workspace/drive pins and preinventory."""
    with observation_scope(descriptor):
        return evaluate_observed(descriptor)


def evaluate_observed(descriptor):
    check(descriptor.get("stratum") in ("A", "B", "C"), "unsupported_stratum")
    drive_bytes = read_pin(descriptor["drive"])
    facts = json_bytes(read_pin(descriptor["workspace"]), "workspace")
    check(facts["work_id"] == {"A": "soodles-work-1", "B": "soodles-work-2", "C": "soodles-work-3"}[descriptor["stratum"]], "case_stratum_mismatch")
    retained = facts.get("authorization", {}).get("prepared_receipt")
    if retained is not None:
        check(retained in descriptor["source_before"], "missing_retained_prepared_pin")
    for path, digest in descriptor["source_before"].items():
        data = artifact(path)
        check(data is not None and sha(data) == digest, "source_changed:" + path)
    check(bool(descriptor["source_before"]), "missing_source_inventory")
    capture = decode_capture({name: read_pin(pin) for name, pin in descriptor["capture"].items()})
    check(sha(drive_bytes) == capture["binding"]["public_files"].get("drive.py"), "driver_activation_digest_mismatch")
    # Noodle removes the actual worktree after capture. Pin the surviving copy,
    # but match argv against the activated path, never read a deleted worktree.
    activated_driver = str(Path(capture["launch"]["cwd"]) / "drive.py")
    drives, opaque = extract_drives(capture, facts, descriptor["workspace"]["path"], activated_driver)
    behavior = judge_behavior(facts, drives)
    measured = costs(capture, descriptor.get("carrier_item_keys"))
    limitations = capture["limitations"] + ["natural-language policy suggestions not independently judged", "unrecognized commands are not independent subprocess/effect observations"]
    # Missing required output with a complete trace is a behavior failure.
    # An existing output without a recognized real drive cannot establish provenance.
    if not drives and artifact(facts["task"]["raw_cli_receipt"]) is not None:
        return refusal("unproven_cli_provenance")
    if capture["incomplete_commands"]:
        behavior["checks"]["all_commands_completed"] = False
        behavior["barriers"].append("all_commands_completed")
        behavior["classification"] = "FAIL"
    return {"evidence_validity": "VALID", "stratum": descriptor["stratum"],
            "behavior": behavior, "cost": measured,
            "cost_comparison_eligible": behavior["classification"] == "PASS" and not capture["incomplete_commands"],
            "opaque_command_keys": opaque, "limitations": limitations,
            "authorizes_landing": False}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
