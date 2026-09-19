#!/usr/bin/env python3
"""Replay raw Noodle admission-recovery evidence without continuation authority."""
import base64
import binascii
import hashlib
import json


PASS = "PASS"
FEATURE = "noodle_admission_recovery"
BARRIERS = (
    "repeated_unchanged_inspect",
    "help_after_complete_projection",
    "repeated_unchanged_instruction_read",
    "avoidable_confirmation",
)


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def valid_hex(value, length):
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def decode_bytes(value, label, errors):
    if not isinstance(value, str):
        errors.append(f"missing_{label}_bytes")
        return None
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        errors.append(f"invalid_{label}_base64")
        return None


def decode_json(value, label, errors):
    raw = decode_bytes(value, label, errors)
    if raw is None:
        return None, None
    try:
        return raw, json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append(f"invalid_{label}_json")
        return raw, None


def bound_document(document, label, errors):
    if not isinstance(document, dict):
        errors.append(f"missing_{label}")
        return None
    raw = decode_bytes(document.get("bytes_b64"), label, errors)
    expected = document.get("sha256")
    if raw is not None and sha256(raw) != expected:
        errors.append(f"{label}_digest_mismatch")
    return expected


def projected_argv(projection):
    if not isinstance(projection, dict):
        return None
    next_value = projection.get("next")
    if not isinstance(next_value, dict):
        return None
    argv = next_value.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        return None
    return argv


def process_event(event, index, run_id, arm, errors):
    prefix = f"operation_{index}"
    _, receipt = decode_json(
        event.get("process_receipt_b64"), f"{prefix}_process_receipt", errors)
    if not isinstance(receipt, dict):
        errors.append(f"{prefix}_invalid_process_receipt")
        receipt = {}
    if receipt.get("run_id") != run_id:
        errors.append(f"{prefix}_process_run_id_mismatch")
    if receipt.get("arm") != arm:
        errors.append(f"{prefix}_process_arm_mismatch")
    if receipt.get("sequence") != index:
        errors.append(f"{prefix}_process_sequence_mismatch")
    if receipt.get("kind") not in {"owner_read", "owner_action"}:
        errors.append(f"{prefix}_invalid_kind")
    if event.get("kind") != receipt.get("kind"):
        errors.append(f"{prefix}_kind_receipt_mismatch")
    if not isinstance(receipt.get("operation"), str) or not receipt.get("operation"):
        errors.append(f"{prefix}_invalid_operation")
    argv = receipt.get("argv")
    if not isinstance(argv, list) or not argv or not all(
            isinstance(item, str) for item in argv):
        errors.append(f"{prefix}_invalid_argv")
    elif (receipt.get("operation") == "admission.inspect"
          and argv[-2:] != ["admission", "inspect"]):
        errors.append(f"{prefix}_inspect_argv_mismatch")
    exit_code = receipt.get("exit_code")
    if type(exit_code) is not int:
        errors.append(f"{prefix}_invalid_exit_code")
    elapsed = receipt.get("elapsed_ms")
    if type(elapsed) not in (int, float) or elapsed < 0:
        errors.append(f"{prefix}_invalid_elapsed_ms")
    stdout = decode_bytes(event.get("stdout_b64"), f"{prefix}_stdout", errors)
    stderr = decode_bytes(event.get("stderr_b64"), f"{prefix}_stderr", errors)
    if stdout is not None and sha256(stdout) != receipt.get("stdout_sha256"):
        errors.append(f"{prefix}_stdout_digest_mismatch")
    if stderr is not None and sha256(stderr) != receipt.get("stderr_sha256"):
        errors.append(f"{prefix}_stderr_digest_mismatch")
    parsed = None
    if stdout is not None:
        try:
            parsed = json.loads(stdout)
        except (UnicodeDecodeError, json.JSONDecodeError):
            errors.append(f"{prefix}_stdout_not_json")
    return parsed, receipt


def validate_manifest(manifest, errors):
    subject = manifest.get("subject")
    if (not isinstance(subject, dict)
            or subject.get("repository") != "ed3c/noodle"
            or not valid_hex(subject.get("source_revision"), 40)):
        errors.append("invalid_manifest_subject")
    carrier = manifest.get("carrier")
    if (not isinstance(carrier, dict)
            or not all(isinstance(carrier.get(key), str) and carrier.get(key)
                       for key in ("id", "os", "arch"))):
        errors.append("invalid_manifest_carrier")
    if not valid_hex(manifest.get("fixed_observer_sha256"), 64):
        errors.append("invalid_manifest_fixed_observer")
    if manifest.get("fixed_observer_classification") != "GREEN":
        errors.append("invalid_manifest_observer_classification")
    if not isinstance(manifest.get("cleanup_scope"), str) or not manifest.get("cleanup_scope"):
        errors.append("invalid_manifest_cleanup_scope")
    completion = manifest.get("completion_statuses")
    if (not isinstance(completion, list) or not completion
            or not all(isinstance(item, str) and item for item in completion)):
        errors.append("invalid_manifest_completion_statuses")
        completion = []
    paths = manifest.get("canonical_paths")
    if (not isinstance(paths, list) or not paths
            or len(paths) != len(set(paths))
            or not all(isinstance(item, str) and item for item in paths)):
        errors.append("invalid_manifest_canonical_paths")
        paths = []
    instructions = manifest.get("instructions")
    if (not isinstance(instructions, dict)
            or set(instructions) != {"baseline", "treatment"}
            or not all(valid_hex(instructions.get(arm), 64)
                       for arm in ("baseline", "treatment"))
            or instructions.get("baseline") == instructions.get("treatment")):
        errors.append("invalid_manifest_instruction_delta")
        instructions = {}
    for key in ("task_sha256", "exposure_sha256"):
        if not valid_hex(manifest.get(key), 64):
            errors.append(f"invalid_manifest_{key}")
    if manifest.get("barrier_order") != list(BARRIERS):
        errors.append("invalid_manifest_barrier_order")
    uncertainties = manifest.get("allowed_uncertainties")
    if (not isinstance(uncertainties, list)
            or len(uncertainties) != len(set(uncertainties))
            or not all(isinstance(item, str) and item for item in uncertainties)):
        errors.append("invalid_manifest_allowed_uncertainties")
    return completion, paths, instructions


def validate_receipt_binding(receipt, label, run, initial_sha, operations_sha,
                             errors):
    if not isinstance(receipt, dict):
        errors.append(f"invalid_{label}")
        return False
    expected = {
        "run_id": run.get("run_id"),
        "arm": run.get("arm"),
        "consumer_session_id": run.get("consumer", {}).get("session_id"),
        "subject": run.get("packet", {}).get("subject"),
        "initial_projection_sha256": initial_sha,
        "operations_sha256": operations_sha,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            errors.append(f"{label}_{key}_mismatch")
    return True


def validate_external_receipt(receipt, run, manifest, initial_sha,
                              operations_sha, errors):
    if not validate_receipt_binding(
            receipt, "external_observer_receipt", run, initial_sha,
            operations_sha, errors):
        return set()
    if receipt.get("observer_sha256") != manifest.get("fixed_observer_sha256"):
        errors.append("external_observer_digest_mismatch")
    if receipt.get("classification") != "GREEN":
        errors.append("external_observer_not_green")
    if receipt.get("errors") != []:
        errors.append("external_observer_has_errors")
    if receipt.get("production_mutations") != 0:
        errors.append("external_observer_mutated_production")
    if receipt.get("authorizes_landing") is not False:
        errors.append("external_observer_claims_authority")
    resolved = receipt.get("resolved_uncertainties")
    if not isinstance(resolved, list):
        errors.append("external_observer_invalid_resolved_uncertainties")
        return set()
    confirmed = set()
    for item in resolved:
        if (not isinstance(item, dict)
                or set(item) != {"id", "opened_at", "resolved_at"}
                or item.get("id") not in manifest.get("allowed_uncertainties", [])
                or type(item.get("opened_at")) is not int
                or type(item.get("resolved_at")) is not int):
            errors.append("external_observer_invalid_resolved_uncertainty")
            continue
        confirmed.add((item["id"], item["opened_at"], item["resolved_at"]))
    return confirmed


def validate_cleanup_receipt(receipt, run, manifest, initial_sha,
                             operations_sha, errors):
    if not validate_receipt_binding(
            receipt, "cleanup_receipt", run, initial_sha, operations_sha,
            errors):
        return
    if receipt.get("owned_residue_absent") is not True:
        errors.append("cleanup_residue")
    if receipt.get("scope") != manifest.get("cleanup_scope"):
        errors.append("cleanup_scope_mismatch")


def evaluate(run, manifest, declared=None):
    errors = []
    if manifest.get("feature") != FEATURE:
        errors.append("feature_manifest_mismatch")
    completion_statuses, canonical_paths, instructions = validate_manifest(
        manifest, errors)
    packet = run.get("packet") if isinstance(run.get("packet"), dict) else {}
    evidence = run.get("evidence") if isinstance(run.get("evidence"), dict) else {}
    operations = run.get("operations") if isinstance(run.get("operations"), list) else []
    arm = run.get("arm")
    run_id = run.get("run_id")
    subject = manifest.get("subject")
    if packet.get("subject") != subject:
        errors.append("packet_subject_manifest_mismatch")
    if packet.get("carrier") != manifest.get("carrier"):
        errors.append("packet_carrier_manifest_mismatch")

    task_sha = bound_document(packet.get("task"), "task", errors)
    if task_sha != manifest.get("task_sha256"):
        errors.append("task_manifest_mismatch")
    instruction_sha = bound_document(packet.get("instruction"), "instruction", errors)
    if instruction_sha != instructions.get(arm):
        errors.append("instruction_manifest_mismatch")
    exposure = packet.get("exposure")
    if not isinstance(exposure, dict) or fingerprint(exposure) != manifest.get("exposure_sha256"):
        errors.append("exposure_manifest_mismatch")
    if packet.get("transport_events") != []:
        errors.append("provider_transport_observed")

    barriers = {name: 0 for name in BARRIERS}
    initial_projection = None
    initial_sha = None
    initial_index = None
    action_index = None
    action_result = None
    completion_projection = None
    last_inspect_sha = None
    state_changed = False
    complete_projection_seen = False
    instruction_reads = set()
    open_uncertainties = {}
    pending_uncertainty_repeats = []

    for index, event in enumerate(operations):
        if not isinstance(event, dict):
            errors.append(f"operation_{index}_invalid")
            continue
        kind = event.get("kind")
        process = {}
        if kind in {"owner_read", "owner_action"}:
            output, process = process_event(
                event, index, run_id, arm, errors)
            kind = process.get("kind")
        else:
            output = None
        if kind == "owner_read" and process.get("operation") == "admission.inspect":
            projection = output
            projection_sha = fingerprint(projection)
            if initial_projection is None:
                initial_projection = projection
                initial_sha = projection_sha
                initial_index = index
                complete_projection_seen = projected_argv(projection) is not None
            resolution = event.get("resolves_uncertainty")
            legal_resolution = (isinstance(resolution, str)
                                and resolution in open_uncertainties)
            if legal_resolution:
                opened_at = open_uncertainties.pop(resolution)
            if last_inspect_sha == projection_sha and not state_changed and not legal_resolution:
                barriers["repeated_unchanged_inspect"] += 1
            elif last_inspect_sha == projection_sha and not state_changed:
                pending_uncertainty_repeats.append(
                    (resolution, opened_at, index))
            opened = event.get("opens_uncertainty")
            if isinstance(opened, str) and opened:
                if opened in manifest.get("allowed_uncertainties", []):
                    open_uncertainties[opened] = index
                else:
                    errors.append("undeclared_uncertainty")
            last_inspect_sha = projection_sha
            state_changed = False
            if action_index is not None:
                completion_projection = projection
        elif kind == "owner_action":
            if action_index is not None:
                errors.append("duplicate_mutating_continuation")
            action_index = index
            if initial_projection is None:
                errors.append("continuation_before_fresh_projection")
            if process.get("bound_projection_sha256") != initial_sha:
                errors.append("continuation_projection_binding_mismatch")
            if process.get("argv") != projected_argv(initial_projection):
                errors.append("continuation_argv_mismatch")
            if process.get("exit_code") != 0:
                errors.append("continuation_failed")
            action_result = output
            state_changed = process.get("exit_code") == 0
            complete_projection_seen = False
        elif kind == "help_read" and complete_projection_seen:
            barriers["help_after_complete_projection"] += 1
        elif kind == "instruction_read":
            binding = (event.get("path"), event.get("sha256"))
            if binding in instruction_reads:
                barriers["repeated_unchanged_instruction_read"] += 1
            instruction_reads.add(binding)
        elif kind == "confirmation" and event.get("required") is False:
            barriers["avoidable_confirmation"] += 1

    if not isinstance(initial_projection, dict):
        errors.append("fresh_initial_projection_not_observed")
    else:
        if initial_projection.get("status") != "recoverable":
            errors.append("initial_owner_projection_not_recoverable")
        if not str(initial_projection.get("owner", "")).startswith("Noodle"):
            errors.append("initial_owner_mismatch")
        if projected_argv(initial_projection) is None:
            errors.append("initial_owner_continuation_incomplete")
    if declared is not None and initial_sha != declared.get(
            "initial_owner_projection_sha256"):
        errors.append("initial_owner_projection_manifest_mismatch")
    if action_index is None:
        errors.append("mutating_continuation_not_observed")
    if isinstance(action_result, dict) and isinstance(initial_projection, dict):
        if action_result.get("status") != "retired":
            errors.append("retirement_result_not_retired")
        if not str(action_result.get("owner", "")).startswith("Noodle"):
            errors.append("retirement_owner_mismatch")
        for key in ("subject", "current_order_revision"):
            if action_result.get(key) != initial_projection.get(key):
                errors.append(f"retirement_{key}_mismatch")
    else:
        errors.append("missing_retirement_result")

    if not isinstance(completion_projection, dict):
        errors.append("missing_completion_owner_projection")
    else:
        if completion_projection.get("status") not in completion_statuses:
            errors.append("unexpected_completion_status")
        if not str(completion_projection.get("owner", "")).startswith("Noodle"):
            errors.append("completion_owner_mismatch")
        if projected_argv(completion_projection) is not None:
            errors.append("completion_offers_executable_continuation")

    operations_sha = fingerprint(operations)
    observer_raw, observer_receipt = decode_json(
        evidence.get("external_observer_receipt_b64"),
        "external_observer_receipt", errors)
    if observer_raw is not None and declared is not None:
        if sha256(observer_raw) != declared.get("external_observer_receipt_sha256"):
            errors.append("external_observer_receipt_manifest_mismatch")
    confirmed_uncertainties = validate_external_receipt(
        observer_receipt, run, manifest, initial_sha, operations_sha, errors)
    for item in pending_uncertainty_repeats:
        if item not in confirmed_uncertainties:
            barriers["repeated_unchanged_inspect"] += 1

    cleanup_raw, cleanup = decode_json(
        evidence.get("cleanup_receipt_b64"), "cleanup_receipt", errors)
    if cleanup_raw is not None and declared is not None:
        if sha256(cleanup_raw) != declared.get("cleanup_receipt_sha256"):
            errors.append("cleanup_receipt_manifest_mismatch")
    validate_cleanup_receipt(
        cleanup, run, manifest, initial_sha, operations_sha, errors)

    preserved = decode_bytes(evidence.get("preserved_input_b64"),
                             "preserved_input", errors)
    archived = decode_bytes(evidence.get("retired_archive_b64"),
                            "retired_archive", errors)
    if preserved is not None and archived is not None and preserved != archived:
        errors.append("retired_archive_bytes_changed")
    before = evidence.get("canonical_before")
    after = evidence.get("canonical_after")
    if not isinstance(before, dict) or set(before) != set(canonical_paths):
        errors.append("invalid_canonical_before")
    elif not isinstance(after, dict) or set(after) != set(canonical_paths):
        errors.append("invalid_canonical_after")
    else:
        for path in canonical_paths:
            old = decode_bytes(before[path], f"canonical_before_{path}", errors)
            new = decode_bytes(after[path], f"canonical_after_{path}", errors)
            if old is not None and new is not None and old != new:
                errors.append(f"canonical_file_changed_{path}")
    if evidence.get("mailbox_absent") is not True:
        errors.append("retired_mailbox_present")
    if evidence.get("remaining_processes") != []:
        errors.append("remaining_process")
    if evidence.get("provider_transport_events") != []:
        errors.append("provider_transport_observed")
    if open_uncertainties:
        errors.append("unresolved_declared_uncertainty")
    consumer = run.get("consumer")
    if not isinstance(consumer, dict) or consumer.get("run_id") != run.get("run_id"):
        errors.append("invalid_consumer_receipt")
    elif not isinstance(consumer.get("session_id"), str) or not consumer.get("session_id"):
        errors.append("invalid_consumer_session")
    elif consumer.get("authorizes_landing") is not False:
        errors.append("consumer_claims_landing_authority")

    return {
        "schema": 2,
        "feature": FEATURE,
        "classification": PASS if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "barriers": barriers,
        "initial_projection_sha256": initial_sha,
        "operations_observed": len(operations),
        "authorizes_landing": False,
    }
