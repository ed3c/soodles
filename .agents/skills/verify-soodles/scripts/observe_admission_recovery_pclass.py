#!/usr/bin/env python3
"""Normalize the fixed recorder packet; never execute an archived command.

The packet is consumer-recorded subprocess evidence, not a complete platform
transcript. Confirmation observations retain that narrower consumer provenance.
"""
import base64
import copy
import hashlib
import json
from pathlib import PurePosixPath

BARRIERS = ["repeated_unchanged_projection", "help_after_complete_projection",
            "repeated_unchanged_instruction", "avoidable_confirmation"]
CONTROLS = ["stale_continuation", "wrong_projection_digest", "wrong_subject",
            "missing_completion", "false_cleanup", "incomplete_membership",
            "duplicate_membership", "observer_identity", "run_identity",
            "archive_changed", "provider_transport", "unwaited_process",
            "fresh_reinspection", "equivalent_argv"]
SUPPLEMENT_CONTROLS = ["cleanup_supplement_omitted", "cleanup_supplement_rebound",
                       "cleanup_supplement_corrected", "complete_cleanup_non_case"]
CLEANUP_SCOPE = [".noodle/noodle.lock", ".noodle/orders-next.json",
                 ".noodle/admission-retirements/*.json",
                 ".noodle/sessions/*/process.json", ".noodle/**/*.tmp"]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(blob):
    data = base64.b64decode(blob["base64"], validate=True)
    if sha(data) != blob["sha256"]:
        raise ValueError("raw_blob_digest_mismatch")
    return data


def pack(data):
    return {"base64": base64.b64encode(data).decode(), "sha256": sha(data)}


def parsed(record, name):
    return json.loads(unpack(record[name]))


def cleanup_supplement(raw, manifest):
    """Read fixed external bytes as data, never execute the cleanup observer."""
    declared = manifest.get("cleanup_supplement")
    supplied = raw.get("cleanup_supplement")
    if declared is None and supplied is None:
        return {}
    if declared is None or supplied is None:
        raise ValueError("cleanup_supplement_missing_or_unbound")
    for name in ("observer", "selection"):
        if sha(unpack(supplied[name])) != declared[name + "_sha256"]:
            raise ValueError("cleanup_supplement_" + name + "_digest_mismatch")
    selection = json.loads(unpack(supplied["selection"]))
    if (selection["schema"] != 1 or selection["authorizes_landing"] is not False
            or selection["observer_sha256"] != declared["observer_sha256"]
            or selection["scope"] != CLEANUP_SCOPE
            or set(selection["runs"]) != set(declared["runs"])
            or set(supplied["receipts"]) != set(declared["runs"])):
        raise ValueError("cleanup_supplement_selection_mismatch")
    receipts = {}
    for rid, binding in declared["runs"].items():
        data = unpack(supplied["receipts"][rid])
        if sha(data) != binding["receipt_sha256"]:
            raise ValueError("cleanup_supplement_receipt_digest_mismatch")
        receipt = json.loads(data)
        if (receipt["run_id"] != rid or receipt["project"] != selection["runs"][rid]
                or receipt["project"] != binding["project"]):
            raise ValueError("cleanup_supplement_run_binding_mismatch")
        receipts[rid] = receipt
    return receipts


def apply_cleanup_supplement(run, bindings, manifest, receipt, initial_errors, by_label):
    """Discharge only the observed lock residue, retaining all initial errors."""
    selected = manifest["cleanup_supplement"]["runs"][run["run_id"]]
    if (fingerprint(run) != selected["original_run_sha256"]
            or bindings["project"] != selected["project"]):
        return ["cleanup_supplement_original_run_mismatch"]
    before, after = receipt["before"], receipt["after"]
    lock = selected["lock"]
    if ({k: before[k] for k in ("lock_bytes", "lock_sha256", "lock_pid")} != lock
            or type(lock["lock_pid"]) is not int or lock["lock_pid"] <= 1):
        return ["cleanup_supplement_lock_binding_mismatch"]
    # e_b4 recorded lock bytes; e_b6 recorded lock presence only. Its before
    # digest is supplied by the fixed external observer, not invented here.
    if bindings["cleanup_format"] == "find":
        original_lock = unpack(by_label[bindings["roles"]["lock"]]["stdout.bin"])
        if sha(original_lock) != lock["lock_sha256"] or len(original_lock) != lock["lock_bytes"]:
            return ["cleanup_supplement_original_lock_mismatch"]
        expected_errors = ["retained_runtime_lock"]
    elif bindings["cleanup_format"] == "kernel_signals":
        original = parsed(by_label[bindings["roles"]["cleanup"]], "stdout.bin")
        if original["recovery_named_residue"] != [".noodle/noodle.lock"]:
            return ["cleanup_supplement_residue_scope_mismatch"]
        expected_errors = ["recovery_residue"]
    else:
        return ["cleanup_supplement_unselected_cleanup_format"]
    archive = f'.noodle/admission-retirements/{bindings["proposal_sha256"]}-{bindings["revision"]}.json'
    sessions = receipt["session_readback"]
    original_sessions = []
    decoder = json.JSONDecoder()
    for label in selected["session_record_labels"]:
        record = by_label[label]
        if parsed(record, "result.json")["exit_code"] != 0:
            return ["cleanup_supplement_original_sessions_failed"]
        text = unpack(record["stdout.bin"]).decode()
        # The e_b4 recorder concatenated path lines and JSON objects; e_b6
        # recorded one JSON object per command. Decode both without execution.
        while "{" in text:
            text = text[text.index("{"):]
            item, end = decoder.raw_decode(text)
            original_sessions.append((item["session_id"], item["pid"]))
            text = text[end:]
    if (receipt["schema"] != 1 or receipt["authorizes_landing"] is not False
            or receipt["classification"] != "GREEN" or receipt["errors"] != []
            or receipt["removed"] is not True
            or receipt["scope"] != {"owned_path": CLEANUP_SCOPE[0], "mailbox": CLEANUP_SCOPE[1],
                                     "session_process_records": len(bindings["session_pids"])}
            or before["mailbox_absent"] is not True or before["temporary_paths"] != []
            or before["archives"] != [archive]
            or after != {"lock_absent": True, "mailbox_absent": True, "archives": [archive]}
            or receipt["process_readback"] != [{"target": lock["lock_pid"], "absent": True},
                                               {"target": -lock["lock_pid"], "absent": True}]
            or sorted(s["pid"] for s in sessions) != bindings["session_pids"]
            or sorted((s["session_id"], s["pid"]) for s in sessions) != sorted(original_sessions)
            or len({s["session_id"] for s in sessions}) != len(sessions)
            or any(s["process_absent"] is not True or s["group_absent"] is not True for s in sessions)
            or type(receipt["observed_at_ns"]) is not int
            or receipt["observed_at_ns"] <= max(parsed(r, "request.json")["time_ns"] for r in run["records"])):
        return ["cleanup_supplement_incomplete_readback"]
    if sorted(set(initial_errors)) != expected_errors:
        return ["cleanup_supplement_initial_scope_mismatch"]
    return []


def evaluate_run(run, declaration, manifest, supplement=None):
    errors = []
    counts = dict.fromkeys(BARRIERS, 0)
    bindings = declaration["bindings"]
    records = run["records"]
    if bindings["observer_sha256"] != manifest["observer_sha256"]:
        errors.append("run_observer_identity_mismatch")
    if bindings["carrier"] != manifest["carrier"]:
        errors.append("run_carrier_mismatch")
    if declaration["arm"] != run["arm"]:
        errors.append("arm_binding_mismatch")
    by_label = {r["label"]: r for r in records}
    if len(by_label) != len(records):
        errors.append("duplicate_record_label")
    if [r["label"] for r in records] != bindings["record_labels"]:
        errors.append("record_membership_mismatch")
    if run["run_id"] != declaration["run_id"] or run["arm"] != "baseline":
        errors.append("run_identity_mismatch")
    if fingerprint(run) != declaration["evidence_sha256"]:
        errors.append("run_evidence_digest_mismatch")
    consumer = json.loads(unpack(run["consumer"]))
    if consumer["run_id"] != bindings["consumer_run_id"] or consumer["arm"] != "baseline":
        errors.append("consumer_identity_mismatch")
    if consumer.get("authorizes_landing") is not False:
        errors.append("consumer_landing_authority")

    decoded = []
    previous_time = -1
    for r in records:
        q, s = parsed(r, "request.json"), parsed(r, "result.json")
        out, err = unpack(r["stdout.bin"]), unpack(r["stderr.bin"])
        if q["time_ns"] <= previous_time:
            errors.append("record_order_mismatch")
        previous_time = q["time_ns"]
        if q["cwd"] != bindings["cwd"]:
            errors.append("record_project_mismatch")
        if fingerprint(q["argv"]) != bindings["commands"].get(r["label"]):
            errors.append("unbound_command_or_transport")
        if s["stdout_sha256"] != sha(out) or s["stderr_sha256"] != sha(err):
            errors.append("process_stream_digest_mismatch")
        elapsed = s["elapsed_seconds"]
        if (type(elapsed) not in (int, float) or not 0 <= elapsed < 60
                or s["timed_out"] is not False or s.get("authorizes_landing") is not False):
            errors.append("invalid_process_result")
        # Popen failure is not a waited process. Retain its exact observation;
        # all actual subprocesses were communicate()d by the pinned recorder.
        if type(s["exit_code"]) is not int:
            if not (s["exit_code"] is None and isinstance(s["error"], str)
                    and s["error"].startswith("[Errno 2]")
                    and out == err == b""
                    and r["label"] in bindings["spawn_failures"]):
                errors.append("process_not_waited")
        elif s["error"] is not None:
            errors.append("process_error")
        decoded.append((r, q, s, out, err))

    def get(role):
        r = by_label[bindings["roles"][role]]
        return r, parsed(r, "request.json"), parsed(r, "result.json"), unpack(r["stdout.bin"])

    for role in ("build", "proposal", "archive", "before_snapshot", "before_orders", "before_state",
                 "after_snapshot", "after_orders", "after_state"):
        label = bindings["roles"][role]
        label = label[0] if isinstance(label, list) else label
        if parsed(by_label[label], "result.json")["exit_code"] != 0:
            errors.append("required_observation_failed")
    for role in ("archive", "cleanup", "process", "after_snapshot", "after_orders", "after_state"):
        label = bindings["roles"][role]
        label = label[0] if isinstance(label, list) else label
        if (bindings["roles"]["completion"] in by_label
                and parsed(by_label[label], "request.json")["time_ns"] <=
                parsed(by_label[bindings["roles"]["completion"]], "request.json")["time_ns"]):
            errors.append("observation_precedes_completion")

    # The recorder snapshots the measured binary for each invocation.
    binary = manifest["selection"]["binary"]
    binary_digest = manifest["selection"]["binary_sha256"]
    instruction_seen = {}
    task_seen = False
    current = None
    current_digest = None
    retired = False
    completion = False
    initial = None
    mutations = 0
    for r, q, s, out, err in decoded:
        argv = q["argv"]
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            errors.append("invalid_argv")
            continue
        if PurePosixPath(argv[0]).name == "cat" and len(argv) == 2:
            name = PurePosixPath(argv[1]).name
            if name in manifest["selection"]["instruction_files"]:
                digest = sha(out)
                if s["exit_code"] != 0 or digest != manifest["selection"]["instruction_files"][name]:
                    errors.append("instruction_digest_mismatch")
                if instruction_seen.get(name) == digest:
                    counts[BARRIERS[2]] += 1
                instruction_seen[name] = digest
            if name == "task.txt":
                task_seen = s["exit_code"] == 0 and sha(out) == manifest["selection"]["task_sha256"]
        if argv[0] != binary:
            continue
        for observed in (q["files_before"], s["files_after"]):
            if observed.get(binary, {}).get("sha256") != binary_digest:
                errors.append("noodle_binary_mismatch")
        if "--help" in argv:
            if current is not None and current.get("next", {}).get("argv"):
                counts[BARRIERS[1]] += 1
            continue
        if argv == [binary, "version"]:
            continue
        if argv[:4] != [binary, "--project-dir", bindings["project"], "admission"]:
            errors.append("wrong_owner_operation")
            continue
        if s["exit_code"] != 0:
            errors.append("owner_operation_failed")
            continue
        projection = json.loads(out)
        if projection.get("owner") != "Noodle initial admission":
            errors.append("owner_identity_mismatch")
        if projection.get("current_order_revision") != bindings["revision"]:
            errors.append("owner_revision_mismatch")
        operation = argv[4:]
        if operation == ["inspect"]:
            if current_digest == sha(out):
                # Only repeated identical, successful reads of unchanged state
                # count; retirement changes the state and clears the projection.
                counts[BARRIERS[0]] += 1
            if initial is None:
                initial = projection
                if r["label"] != bindings["roles"]["initial"] or sha(out) != bindings["projection_sha256"]:
                    errors.append("initial_projection_digest_mismatch")
                if projection.get("status") != "recoverable":
                    errors.append("initial_not_recoverable")
            elif retired:
                if (projection.get("status") != "no_proposal"
                        or projection.get("next", {}).get("argv") != []
                        or projection.get("subject", {}).get("proposal_sha256") != ""):
                    errors.append("failed_completion")
                elif not completion:
                    completion = True
                    if (r["label"] != bindings["roles"]["completion"]
                            or sha(out) != bindings["completion_sha256"]):
                        errors.append("completion_projection_digest_mismatch")
            current, current_digest = projection, sha(out)
        elif operation[:1] == ["retire"]:
            mutations += 1
            if (current is None or current.get("status") != "recoverable"
                    or argv != current.get("next", {}).get("argv")):
                errors.append("stale_or_unbound_continuation")
            if (operation != ["retire", bindings["proposal_sha256"], bindings["revision"]]
                    or projection.get("status") != "retired"
                    or projection.get("subject", {}).get("proposal_sha256") != bindings["proposal_sha256"]):
                errors.append("wrong_retirement_subject")
            if projection.get("next", {}).get("argv") != [binary, "--project-dir", bindings["project"], "admission", "inspect"]:
                errors.append("completion_continuation_mismatch")
            retired = True
            current, current_digest = None, None
        else:
            errors.append("wrong_owner_operation")
    if mutations != 1:
        errors.append("mutating_continuation_count")
    if not completion:
        errors.append("missing_completion")
    if initial is None:
        errors.append("missing_fresh_projection")
    elif initial.get("subject", {}).get("proposal_sha256") != bindings["proposal_sha256"]:
        errors.append("projection_subject_mismatch")
    if not task_seen or set(instruction_seen) != set(manifest["selection"]["instruction_files"]):
        errors.append("missing_instruction_exposure")
    build = get("build")[3].decode()
    for key, value in (("vcs.revision", manifest["selection"]["subject"]["noodle"]),
                       ("vcs.modified", "false"), ("GOOS", "darwin"), ("GOARCH", "arm64")):
        if f"{key}={value}\n" not in build:
            errors.append("noodle_subject_or_carrier_mismatch")

    # Archive and canonical equality are recomputed from raw bytes, not from
    # the consumer's bytes_equal assertion or comparison script's verdict.
    before = get("proposal")[3]
    archive = json.loads(get("archive")[3])
    if (base64.b64decode(archive["proposal_bytes"], validate=True) != before
            or sha(before) != bindings["proposal_sha256"]
            or archive.get("retired") is not True
            or archive.get("owner") != "Noodle initial admission"
            or archive.get("current_order_revision") != bindings["revision"]
            or archive.get("subject", {}).get("proposal_sha256") != bindings["proposal_sha256"]):
        errors.append("archive_preservation_failed")
    for name in ("snapshot", "orders", "state"):
        b = get("before_" + name)[3]
        after_role = bindings["roles"]["after_" + name]
        if isinstance(after_role, list):
            a = json.loads(unpack(by_label[after_role[0]]["stdout.bin"]))
            a = next(row["text"].encode() for row in a if row["path"] == after_role[1])
        else:
            a = get("after_" + name)[3]
        if b != a:
            errors.append("canonical_bytes_changed")

    # Three recorded cleanup interfaces. Exact commands and scopes are pinned
    # by the manifest; none of these archived programs is imported or executed.
    cleanup_error_start = len(errors)
    cleanup = get("cleanup")[3]
    process = get("process")[3]
    if bindings["cleanup_format"] == "find":
        if cleanup.strip():
            errors.append("recovery_residue")
        if process.strip():
            errors.append("live_scoped_process")
        if get("mailbox_absence")[2]["exit_code"] != 0:
            errors.append("mailbox_remains")
        # A retained lock is observable residue, even with an absent PID.
        if get("lock")[3].strip():
            errors.append("retained_runtime_lock")
    elif bindings["cleanup_format"] == "json_inventory":
        c, p = json.loads(cleanup), json.loads(process)
        if c["mailbox_exists"] is not False:
            errors.append("mailbox_remains")
        if c["lock_exists"] is not False or c["other_scoped_candidates"] != []:
            errors.append("recovery_residue")
        lock = json.loads(get("lock_process")[3])
        if (get("lock_process")[2]["exit_code"] != 0
                or lock["pid_or_group_matches"] != []):
            errors.append("live_lock_process")
        if p["pid_or_group_matches"] != []:
            errors.append("live_scoped_process")
        if sorted(row["pid"] for row in p["recorded_processes"]) != bindings["session_pids"]:
            errors.append("process_scope_mismatch")
    elif bindings["cleanup_format"] == "kernel_signals":
        c = json.loads(cleanup)
        if c["mailbox_exists"] is not False:
            errors.append("mailbox_remains")
        if c["recovery_named_residue"] != []:
            errors.append("recovery_residue")
        if sorted(row["pid"] for row in c["process_group"]) != bindings["session_pids"]:
            errors.append("process_scope_mismatch")
        if any(row["process"] != "absent" or row["group_id_equal_pid"] != "absent"
               for row in c["process_group"]):
            errors.append("live_scoped_process")
    else:
        errors.append("unknown_cleanup_format")
    for role in ("cleanup", "process"):
        if get(role)[2]["exit_code"] != 0:
            errors.append("cleanup_observation_failed")
    initial_cleanup_errors = errors[cleanup_error_start:]
    if supplement is not None:
        remaining = apply_cleanup_supplement(
            run, bindings, manifest, supplement, initial_cleanup_errors, by_label)
        if remaining:
            errors.extend(remaining)
        else:
            del errors[cleanup_error_start:]
    if bindings["transport_scope"] != "recorded_subprocesses_only":
        errors.append("unbound_transport_scope")
    # Consumer-recorded non-subprocess events remain explicit evidence. Missing
    # fields are unknown; a prose stopping reason cannot substitute for them.
    if "confirmation" in consumer:
        c = consumer["confirmation"]
        if type(c["count"]) is not int or c["count"] < 0 or c["requested"] != (c["count"] > 0):
            errors.append("invalid_confirmation_observation")
        if consumer["questions"] != []:
            errors.append("unclassified_confirmation")
        counts[BARRIERS[3]] = c["count"]
    else:
        c = consumer["confirmation_questions"]
        if c != {"confirmations_requested": 0, "questions_asked": 0}:
            errors.append("unclassified_confirmation")
    return {"run_id": run["run_id"], "arm": run["arm"],
            "hard_gate": "FAIL" if errors else "PASS", "hard_errors": sorted(set(errors)),
            "barriers": counts if not errors else None,
            "observed_legal_barriers": counts, "records": len(records),
            "initial_cleanup_errors": initial_cleanup_errors,
            "cleanup_supplement_verified": supplement is not None and not errors,
            "evidence_sha256": fingerprint(run), "authorizes_landing": False}


def evaluate(raw, manifest):
    errors, receipts = [], []
    runs, declarations = raw["runs"], manifest["runs"]
    ids = [r["run_id"] for r in runs]
    expected = [d["run_id"] for d in declarations]
    if (len(ids) != 3 or len(set(ids)) != 3 or ids != expected
            or expected != manifest["selection"]["run_ids"]):
        errors.append("incomplete_or_duplicate_membership")
    if (raw["experiment_id"] != manifest["experiment_id"] or raw["phase"] != "exploration"
            or raw["feature"] != "admission_recovery" or raw["authorizes_landing"] is not False):
        errors.append("experiment_identity_mismatch")
    selection = manifest["selection"]
    if (manifest["experiment_id"] != selection["experiment_id"] or selection["arm"] != "baseline"
            or manifest["carrier"] != {"platform": "darwin_arm64", "model_observed": "UNKNOWN",
                               "config_observed": "UNKNOWN"}
            or selection["carrier"] != {"id": "darwin_arm64", "os": "darwin", "arch": "arm64"}
            or selection["subject"]["soodles"] != "255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78"):
        errors.append("selection_identity_mismatch")
    for name, digest in selection["instruction_files"].items():
        if sha(unpack(raw["inputs"][name])) != digest:
            errors.append("instruction_input_mismatch")
    if (sha(unpack(raw["inputs"]["record_context.py"])) != selection["recorder_sha256"]
            or sha(unpack(raw["inputs"]["preserved-input-selection.json"])) != selection["input_selection_sha256"]
            or sha(unpack(raw["task"])) != selection["task_sha256"]):
        errors.append("input_selection_mismatch")
    required = CONTROLS + (SUPPLEMENT_CONTROLS if "cleanup_supplement" in manifest else [])
    if selection["barrier_order"] != BARRIERS or manifest["required_controls"] != required:
        errors.append("experiment_contract_mismatch")
    try:
        supplements = cleanup_supplement(raw, manifest)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"invalid_cleanup_supplement:{error}")
    if errors:
        return receipts, errors
    for run, declaration in zip(runs, declarations):
        try:
            receipt = evaluate_run(run, declaration, manifest, supplements.get(run["run_id"]))
        except (KeyError, TypeError, ValueError, IndexError, StopIteration) as error:
            receipt = {"run_id": run.get("run_id"), "arm": run.get("arm"),
                       "hard_gate": "FAIL", "hard_errors": [f"missing_or_invalid_evidence:{error}"],
                       "barriers": None, "authorizes_landing": False}
        receipts.append(receipt)
        errors.extend(f"{run['run_id']}:{error}" for error in receipt["hard_errors"])
    return receipts, errors


def controls(raw, manifest):
    """Planted mutations bypass only the outer raw digest, never semantic gates."""
    results = []
    for name in CONTROLS:
        changed, contract = copy.deepcopy(raw), copy.deepcopy(manifest)
        # The source is externally declared, not whichever failed run happens
        # to make a negative control pass.
        index = next(i for i, r in enumerate(changed["runs"])
                     if r["run_id"] == manifest["control_source_run_id"])
        run, declaration = changed["runs"][index], contract["runs"][index]
        b = declaration["bindings"]
        records = {r["label"]: r for r in run["records"]}
        def modify(role, file, fn):
            r = records[b["roles"][role]]
            value = parsed(r, file)
            fn(value)
            r[file] = pack((json.dumps(value, indent=2) + "\n").encode())
            if file == "stdout.bin":
                result = parsed(r, "result.json")
                result["stdout_sha256"] = r[file]["sha256"]
                r["result.json"] = pack((json.dumps(result) + "\n").encode())
        target = None
        if name == "stale_continuation":
            run["records"].remove(records[b["roles"]["initial"]]); target = "stale_or_unbound_continuation"
        elif name == "wrong_projection_digest":
            b["projection_sha256"] = "0" * 64; target = "initial_projection_digest_mismatch"
        elif name == "wrong_subject":
            contract["selection"]["subject"]["noodle"] = "0" * 40; target = "noodle_subject_or_carrier_mismatch"
        elif name == "missing_completion":
            run["records"].remove(records[b["roles"]["completion"]]); target = "missing_completion"
        elif name == "false_cleanup":
            modify("cleanup", "stdout.bin", lambda x: x.update(other_scoped_candidates=[{"path": "planted.tmp"}]))
            target = "recovery_residue"
        elif name == "incomplete_membership":
            changed["runs"].pop(); target = "incomplete_or_duplicate_membership"
        elif name == "duplicate_membership":
            changed["runs"].append(copy.deepcopy(run)); target = "incomplete_or_duplicate_membership"
        elif name == "observer_identity":
            # The public replay preflight separately tests executable digest
            # mismatches. This probes the raw recorder's identity binding.
            contract["selection"]["recorder_sha256"] = "0" * 64; target = "input_selection_mismatch"
        elif name == "run_identity":
            c = json.loads(unpack(run["consumer"])); c["run_id"] = "another-run"
            run["consumer"] = pack(json.dumps(c).encode()); target = "consumer_identity_mismatch"
        elif name == "archive_changed":
            modify("archive", "stdout.bin", lambda x: x.update(proposal_bytes=base64.b64encode(b"changed").decode()))
            target = "archive_preservation_failed"
        elif name == "provider_transport":
            modify("retire", "request.json", lambda x: x.update(argv=["gh", "issue", "close", "81"]))
            target = "unbound_command_or_transport"
        elif name == "unwaited_process":
            modify("retire", "result.json", lambda x: x.update(exit_code=None, error=None))
            target = "process_not_waited"
        elif name == "equivalent_argv":
            # Re-serialize a separately assembled identical argv array.
            argv = list(parsed(records[b["roles"]["initial"]], "stdout.bin")["next"]["argv"])
            modify("retire", "request.json", lambda x: x.update(argv=argv))
        elif name != "fresh_reinspection":
            raise ValueError("unknown_control")
        declaration["evidence_sha256"] = fingerprint(run)
        receipts, errors = evaluate(changed, contract)
        if target:
            scoped_errors = [e for e in errors if e.startswith(run["run_id"] + ":") or ":" not in e]
            matched = any(target in e for e in scoped_errors)
            observed = "FAIL" if scoped_errors else "PASS"
        else:
            receipt = next((r for r in receipts if r["run_id"] == run["run_id"]),
                           {"hard_gate": "FAIL", "barriers": None})
            observed = receipt["hard_gate"]
            matched = observed == "PASS" and receipt["barriers"] == dict.fromkeys(BARRIERS, 0)
        results.append({"name": name, "expected": "FAIL" if target else "PASS",
                        "observed": observed, "required_error": target,
                        "predicate": "PASS" if matched else "FAIL",
                        "errors": [e for e in errors if e.startswith(run["run_id"] + ":") or ":" not in e],
                        "source_run_id": run["run_id"], "authorizes_landing": False})
    if "cleanup_supplement" in manifest:
        for name in SUPPLEMENT_CONTROLS:
            changed = copy.deepcopy(raw)
            if name == "cleanup_supplement_omitted":
                changed.pop("cleanup_supplement", None)
            elif name == "cleanup_supplement_rebound" and "cleanup_supplement" in changed:
                receipts = changed["cleanup_supplement"]["receipts"]
                receipts["e_b4"] = receipts["e_b6"]
            receipts, errors = evaluate(changed, manifest)
            if name in SUPPLEMENT_CONTROLS[:2]:
                matched = any(e.startswith("invalid_cleanup_supplement:") for e in errors)
                expected, observed = "FAIL", "FAIL" if errors else "PASS"
            else:
                selected = receipts if name == "cleanup_supplement_corrected" else [
                    r for r in receipts if r["run_id"] == manifest["control_source_run_id"]]
                matched = bool(selected) and all(r["hard_gate"] == "PASS" for r in selected)
                expected, observed = "PASS", "PASS" if matched else "FAIL"
            results.append({"name": name, "expected": expected, "observed": observed,
                            "predicate": "PASS" if matched else "FAIL", "errors": errors,
                            "authorizes_landing": False})
    return results
