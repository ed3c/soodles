#!/usr/bin/env python3
"""Observe Noodle admission recovery without granting continuation authority."""
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


def valid_digest(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def valid_commit(value):
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def projected_next(projection):
    if not isinstance(projection, dict):
        return None, None
    value = projection.get("next")
    if not isinstance(value, dict):
        return None, None
    operation = value.get("operation")
    argv = value.get("argv")
    if operation is not None and (not isinstance(operation, str) or not operation):
        operation = None
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        argv = None
    return operation, argv


def process_errors(event, index):
    errors = []
    for key in ("exit_code", "elapsed_ms"):
        value = event.get(key)
        if type(value) not in (int, float) or value < 0:
            errors.append(f"operation_{index}_invalid_{key}")
    for key in ("stdout_sha256", "stderr_sha256"):
        if not valid_digest(event.get(key)):
            errors.append(f"operation_{index}_invalid_{key}")
    return errors


def evaluate(run, manifest):
    errors = []
    packet = run.get("packet") if isinstance(run.get("packet"), dict) else {}
    precondition = (run.get("precondition")
                    if isinstance(run.get("precondition"), dict) else {})
    postcondition = (run.get("postcondition")
                     if isinstance(run.get("postcondition"), dict) else {})
    operations = run.get("operations") if isinstance(run.get("operations"), list) else []

    if manifest.get("feature") != FEATURE:
        errors.append("feature_manifest_mismatch")
    subject = manifest.get("subject")
    if (not isinstance(subject, dict)
            or subject.get("repository") != "ed3c/noodle"
            or not valid_commit(subject.get("source_revision"))):
        errors.append("invalid_manifest_subject")
    carrier = manifest.get("carrier")
    if (not isinstance(carrier, dict)
            or not all(isinstance(carrier.get(key), str) and carrier.get(key)
                       for key in ("id", "os", "arch"))):
        errors.append("invalid_manifest_carrier")
    if not valid_digest(manifest.get("fixed_observer_sha256")):
        errors.append("invalid_manifest_fixed_observer")
    if not isinstance(manifest.get("fixed_observer_classification"), str):
        errors.append("invalid_manifest_observer_classification")
    cleanup_scope = manifest.get("cleanup_scope")
    if cleanup_scope in (None, "", [], {}):
        errors.append("invalid_manifest_cleanup_scope")
    if packet.get("subject") != subject:
        errors.append("packet_subject_manifest_mismatch")
    if precondition.get("subject") != subject:
        errors.append("precondition_subject_manifest_mismatch")
    if packet.get("carrier") != manifest.get("carrier"):
        errors.append("packet_carrier_manifest_mismatch")
    if precondition.get("carrier") != manifest.get("carrier"):
        errors.append("precondition_carrier_manifest_mismatch")

    initial = packet.get("initial_owner_projection")
    initial_sha = packet.get("expected_owner_projection_sha256")
    if not isinstance(initial, dict):
        errors.append("missing_initial_owner_projection")
    elif fingerprint(initial) != initial_sha:
        errors.append("initial_owner_projection_digest_mismatch")
    if precondition.get("initial_owner_projection") != initial:
        errors.append("initial_owner_projection_internal_mismatch")
    if precondition.get("initial_owner_projection_sha256") != initial_sha:
        errors.append("initial_owner_projection_binding_mismatch")
    expected_operation, expected_argv = projected_next(initial)
    if expected_argv is None:
        errors.append("initial_owner_continuation_incomplete")

    instruction = packet.get("instruction")
    observations = run.get("instruction_observations")
    if not isinstance(instruction, dict) or not isinstance(observations, list):
        errors.append("missing_instruction_binding")
    elif not any(isinstance(item, dict)
                 and item.get("path") == instruction.get("path")
                 and item.get("sha256") == instruction.get("sha256")
                 for item in observations):
        errors.append("instruction_binding_not_observed")

    if packet.get("transport_events") != []:
        errors.append("provider_transport_observed")
    if precondition.get("provider_transport_observed") is not False:
        errors.append("provider_transport_unknown")

    initial_reads = []
    actions = []
    completion_reads = []
    barriers = {name: 0 for name in BARRIERS}
    last_inspect_sha = None
    state_changed = False
    instruction_reads = set()
    complete_projection_seen = False

    for index, event in enumerate(operations):
        if not isinstance(event, dict):
            errors.append(f"operation_{index}_invalid")
            continue
        kind = event.get("kind")
        if kind in {"owner_read", "owner_action"}:
            errors.extend(process_errors(event, index))
        if kind == "owner_read" and event.get("operation") == "admission.inspect":
            projection = event.get("projection")
            projection_sha = event.get("projection_sha256")
            if fingerprint(projection) != projection_sha:
                errors.append(f"operation_{index}_projection_digest_mismatch")
            if projection_sha == initial_sha:
                initial_reads.append(index)
                complete_projection_seen = expected_argv is not None
            if last_inspect_sha == projection_sha and not state_changed:
                barriers["repeated_unchanged_inspect"] += 1
            last_inspect_sha = projection_sha
            state_changed = False
            if postcondition.get("completion_owner_projection_sha256") == projection_sha:
                completion_reads.append(index)
        elif kind == "owner_action":
            actions.append(index)
            if not initial_reads or index < initial_reads[0]:
                errors.append("continuation_before_fresh_projection")
            if event.get("bound_projection_sha256") != initial_sha:
                errors.append("continuation_projection_binding_mismatch")
            if (expected_operation is not None
                    and event.get("operation") != expected_operation):
                errors.append("wrong_current_owner_operation")
            if event.get("argv") != expected_argv:
                errors.append("continuation_argv_mismatch")
            if event.get("exit_code") != 0:
                errors.append("continuation_failed")
            state_changed = event.get("exit_code") == 0
            complete_projection_seen = False
        elif kind == "help_read":
            if complete_projection_seen:
                barriers["help_after_complete_projection"] += 1
        elif kind == "instruction_read":
            binding = (event.get("path"), event.get("sha256"))
            if binding in instruction_reads:
                barriers["repeated_unchanged_instruction_read"] += 1
            instruction_reads.add(binding)
        elif kind == "confirmation" and event.get("required") is False:
            barriers["avoidable_confirmation"] += 1

    if not initial_reads:
        errors.append("fresh_initial_projection_not_observed")
    if len(actions) != 1:
        errors.append("mutating_continuation_observation_not_unique")

    completion = postcondition.get("completion_owner_projection")
    completion_sha = postcondition.get("completion_owner_projection_sha256")
    if not isinstance(completion, dict):
        errors.append("missing_completion_owner_projection")
    else:
        if fingerprint(completion) != completion_sha:
            errors.append("completion_owner_projection_digest_mismatch")
        if len(completion_reads) != 1:
            errors.append("completion_projection_observation_not_unique")
        elif actions and completion_reads[0] < actions[0]:
            errors.append("completion_observed_before_continuation")
        _, completion_argv = projected_next(completion)
        if (isinstance(completion_argv, list)
                and "admission" in completion_argv
                and "retire" in completion_argv):
            errors.append("completion_still_offers_recovery_continuation")

    fixed = run.get("external_observer")
    if not isinstance(fixed, dict):
        errors.append("missing_external_observer_receipt")
    else:
        if fixed.get("sha256") != manifest.get("fixed_observer_sha256"):
            errors.append("external_observer_digest_mismatch")
        if fixed.get("classification") != manifest.get("fixed_observer_classification"):
            errors.append("external_observer_not_pass")
        if not valid_digest(fixed.get("receipt_sha256")):
            errors.append("external_observer_receipt_digest_missing")

    before_input = precondition.get("preserved_input_sha256")
    if not valid_digest(before_input):
        errors.append("invalid_preserved_input_digest")
    elif postcondition.get("retired_archive_sha256") != before_input:
        errors.append("retired_archive_digest_mismatch")
    if precondition.get("canonical_files") != postcondition.get("canonical_files"):
        errors.append("canonical_files_changed")
    if postcondition.get("mailbox_absent") is not True:
        errors.append("retired_mailbox_present")
    if postcondition.get("remaining_processes") != []:
        errors.append("remaining_process")
    if postcondition.get("residue_paths") != []:
        errors.append("cleanup_residue")
    if postcondition.get("cleanup_scope") != manifest.get("cleanup_scope"):
        errors.append("cleanup_scope_mismatch")
    consumer = run.get("consumer")
    if not isinstance(consumer, dict) or consumer.get("run_id") != run.get("run_id"):
        errors.append("invalid_consumer_receipt")
    elif consumer.get("authorizes_landing") is not False:
        errors.append("consumer_claims_landing_authority")

    return {
        "schema": 1,
        "feature": FEATURE,
        "classification": PASS if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "barriers": barriers,
        "initial_projection_sha256": initial_sha,
        "completion_projection_sha256": completion_sha,
        "operations_observed": len(operations),
        "authorizes_landing": False,
    }
