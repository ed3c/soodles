import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / ".agents/skills/verify-soodles/scripts/replay_pclass.py"
OBSERVER = ROOT / ".agents/skills/verify-soodles/scripts/observe_recovery_pclass.py"
DECIDER = ROOT / ".agents/skills/verify-soodles/scripts/decide_pclass.py"
spec = importlib.util.spec_from_file_location("pclass_recovery_replay", REPLAY)
replayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replayer)

SUBJECT = {"repository": "ed3c/noodle",
           "source_revision": "ca81f942f478e8e4afcbbce6ca69640867efe753"}
CARRIER = {"id": "linux_amd64", "os": "linux", "arch": "amd64"}
FIXED_OBSERVER = "a" * 64
TASK = b"Retire the current disposable admission proposal and prove completion."
BASELINE_INSTRUCTION = b"Inspect the owner state, recover it, and verify completion."
TREATMENT_INSTRUCTION = (
    b"Inspect once, execute the exact projected continuation, then inspect once for completion."
)
EXPOSURE = {"tools": ["shell"], "budget": 8, "network": False}
CANONICAL_PATHS = ["orders-next.json", "orders.json", "state.snapshot.json"]
CLEANUP_SCOPE = "disposable fixture and its process group"
BARRIERS = [
    "repeated_unchanged_inspect",
    "help_after_complete_projection",
    "repeated_unchanged_instruction_read",
    "avoidable_confirmation",
]


def encoded(raw):
    return base64.b64encode(raw).decode()


def json_raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def document(raw):
    return {"bytes_b64": encoded(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def projection(status, revision=7):
    subject = {"proposal_sha256": "1" * 64}
    if status == "recoverable":
        next_value = {
            "argv": ["/tmp/noodle", "--project-dir", "/tmp/project", "admission",
                     "retire", "--proposal-sha256", "1" * 64,
                     "--revision", str(revision)],
        }
    else:
        next_value = None
    return {"owner": "Noodle initial admission", "status": status,
            "subject": subject, "current_order_revision": revision,
            "next": next_value}


def operation(run_id, arm, sequence, kind, operation_name, argv, output,
              **values):
    stdout = json_raw(output)
    stderr = b""
    process = {
        "run_id": run_id,
        "arm": arm,
        "sequence": sequence,
        "kind": kind,
        "operation": operation_name,
        "argv": argv,
        "exit_code": 0,
        "elapsed_ms": 1,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        **values,
    }
    return {
        "kind": kind,
        "process_receipt_b64": encoded(json_raw(process)),
        "stdout_b64": encoded(stdout),
        "stderr_b64": encoded(stderr),
    }


def raw_run(run_id, arm, repeated=False, phase="confirmation",
            legal_uncertainty=False):
    initial = projection("recoverable")
    retired = {**projection("retired"), "owner": "Noodle initial admission"}
    completed = {**projection("no_proposal"), "owner": "Noodle initial admission"}
    initial_sha = replayer.fingerprint(initial)
    inspect_argv = ["/tmp/noodle", "--project-dir", "/tmp/project",
                    "admission", "inspect"]
    operation_specs = [("owner_read", "admission.inspect", inspect_argv,
                        initial, {})]
    if repeated:
        operation_specs.append(("owner_read", "admission.inspect", inspect_argv,
                                initial, {}))
    if legal_uncertainty:
        operation_specs[0][4]["opens_uncertainty"] = "owner-state-race"
        operation_specs.append(("owner_read", "admission.inspect", inspect_argv,
                                initial,
                                {"resolves_uncertainty": "owner-state-race"}))
    operation_specs.extend([
        ("owner_action", "admission.retire", initial["next"]["argv"], retired,
         {"bound_projection_sha256": initial_sha}),
        ("owner_read", "admission.inspect", inspect_argv, completed, {}),
    ])
    operations = []
    for sequence, (kind, operation_name, argv, output, metadata) in enumerate(
            operation_specs):
        annotations = {key: value for key, value in metadata.items()
                       if key in {"opens_uncertainty", "resolves_uncertainty"}}
        process_values = {key: value for key, value in metadata.items()
                          if key not in annotations}
        event = operation(run_id, arm, sequence, kind, operation_name, argv,
                          output, **process_values)
        event.update(annotations)
        operations.append(event)
    operations_sha = replayer.fingerprint(operations)
    receipt_binding = {
        "run_id": run_id,
        "arm": arm,
        "consumer_session_id": f"session-{run_id}",
        "subject": copy.deepcopy(SUBJECT),
        "initial_projection_sha256": initial_sha,
        "operations_sha256": operations_sha,
    }
    resolved = ([{"id": "owner-state-race", "opened_at": 0,
                  "resolved_at": 1}] if legal_uncertainty else [])
    observer_receipt = json_raw({
        **receipt_binding,
        "classification": "GREEN",
        "observer_sha256": FIXED_OBSERVER,
        "errors": [],
        "production_mutations": 0,
        "resolved_uncertainties": resolved,
        "authorizes_landing": False,
    })
    cleanup_receipt = json_raw({
        **receipt_binding,
        "owned_residue_absent": True,
        "scope": CLEANUP_SCOPE,
    })
    canonical = {
        path: encoded(f"fixed:{path}".encode()) for path in CANONICAL_PATHS
    }
    packet = {
        "run_id": run_id,
        "arm": arm,
        "case": "admission_recovery",
        "subject": copy.deepcopy(SUBJECT),
        "carrier": copy.deepcopy(CARRIER),
        "task": document(TASK),
        "instruction": document(
            BASELINE_INSTRUCTION if arm == "baseline" else TREATMENT_INSTRUCTION),
        "exposure": copy.deepcopy(EXPOSURE),
        "transport_events": [],
    }
    return {
        "run_id": run_id,
        "arm": arm,
        "packet": packet,
        "operations": operations,
        "evidence": {
            "external_observer_receipt_b64": encoded(observer_receipt),
            "cleanup_receipt_b64": encoded(cleanup_receipt),
            "preserved_input_b64": encoded(b"original proposal bytes"),
            "retired_archive_b64": encoded(b"original proposal bytes"),
            "canonical_before": copy.deepcopy(canonical),
            "canonical_after": copy.deepcopy(canonical),
            "mailbox_absent": True,
            "remaining_processes": [],
            "provider_transport_events": [],
        },
        "consumer": {"run_id": run_id, "session_id": f"session-{run_id}",
                     "authorizes_landing": False},
        "_phase": phase,
    }


def declaration(run, phase):
    initial_raw = base64.b64decode(run["operations"][0]["stdout_b64"])
    initial = json.loads(initial_raw)
    observer_raw = base64.b64decode(
        run["evidence"]["external_observer_receipt_b64"])
    cleanup_raw = base64.b64decode(run["evidence"]["cleanup_receipt_b64"])
    clean = copy.deepcopy(run)
    clean.pop("_phase", None)
    return {
        "run_id": run["run_id"],
        "arm": run["arm"],
        "case": run["packet"]["case"],
        "phase": phase,
        "consumer_session_id": run["consumer"]["session_id"],
        "evidence_sha256": replayer.fingerprint(clean),
        "initial_owner_projection_sha256": replayer.fingerprint(initial),
        "external_observer_receipt_sha256":
            hashlib.sha256(observer_raw).hexdigest(),
        "cleanup_receipt_sha256": hashlib.sha256(cleanup_raw).hexdigest(),
    }


def raw_bundle(pilot_repeated=True, baseline_repeated=True):
    pilots = [raw_run(f"pilot-{index}", "baseline",
                      repeated=pilot_repeated, phase="exploration")
              for index in range(3)]
    runs = []
    for arm in ("baseline", "treatment"):
        for index in range(3):
            runs.append(raw_run(
                f"{arm}-{index}", arm,
                repeated=baseline_repeated and arm == "baseline",
                legal_uncertainty=arm == "treatment" and index == 1))
    return {"pilot_runs": pilots, "runs": runs}


def manifest(raw, target="improvement", selected=None):
    gates = {
        "schema": 1,
        "experiment_id": "ed3c/soodles#81-fixture",
        "causal_delta": {"classification": "PASS"},
        "independent_audit": {"classification": "PASS"},
        "telemetry": {"authority": "report_only"},
    }
    pilot_declarations = [
        declaration(run, "exploration") for run in raw["pilot_runs"]
    ]
    def inspect_count(run):
        return sum(
            1 for event in run["operations"]
            if json.loads(base64.b64decode(
                event["process_receipt_b64"]))["operation"]
            == "admission.inspect")
    pilot_total = sum(inspect_count(run) > 2 for run in raw["pilot_runs"])
    totals = {name: 0 for name in BARRIERS}
    totals["repeated_unchanged_inspect"] = pilot_total
    chosen = next((name for name in BARRIERS if totals[name] > 0), None)
    if selected is not None:
        chosen = selected
    selection = {
        "schema": 1,
        "pilot_runs": [
            {"run_id": item["run_id"],
             "evidence_sha256": item["evidence_sha256"]}
            for item in pilot_declarations
        ],
        "barrier_order": BARRIERS,
        "barrier_totals": totals,
        "selected_barrier": chosen,
    }
    selection_sha = replayer.fingerprint(selection)
    for run in raw["runs"]:
        run["packet"]["selection_sha256"] = selection_sha
    controls = [
        {"name": "stale_projection_binding", "source_run_id": "treatment-0",
         "mutation": "stale_recovery_binding", "expected_hard_gate": "FAIL",
         "expected_errors": [
             "observer_cleanup_receipt_operations_sha256_mismatch",
             "observer_continuation_projection_binding_mismatch",
             "observer_external_observer_receipt_operations_sha256_mismatch"],
         "expected_barrier": 0},
        {"name": "wrong_subject", "source_run_id": "treatment-0",
         "mutation": "wrong_recovery_subject", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_cleanup_receipt_subject_mismatch",
                             "observer_external_observer_receipt_subject_mismatch",
                             "observer_packet_subject_manifest_mismatch"],
         "expected_barrier": 0},
        {"name": "missing_completion", "source_run_id": "treatment-0",
         "mutation": "missing_recovery_completion", "expected_hard_gate": "FAIL",
         "expected_errors": [
             "observer_cleanup_receipt_operations_sha256_mismatch",
             "observer_external_observer_receipt_operations_sha256_mismatch",
             "observer_missing_completion_owner_projection"],
         "expected_barrier": 0},
        {"name": "false_cleanup", "source_run_id": "treatment-0",
         "mutation": "false_recovery_cleanup", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_remaining_process"],
         "expected_barrier": 0},
        {"name": "changed_canonical", "source_run_id": "treatment-0",
         "mutation": "changed_recovery_canonical", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_canonical_file_changed_orders-next.json"],
         "expected_barrier": 0},
        {"name": "provider_transport", "source_run_id": "treatment-0",
         "mutation": "recovery_provider_transport", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_provider_transport_observed"],
         "expected_barrier": 0},
        {"name": "duplicate_continuation", "source_run_id": "treatment-0",
         "mutation": "duplicate_recovery_continuation", "expected_hard_gate": "FAIL",
         "expected_errors": [
             "observer_cleanup_receipt_operations_sha256_mismatch",
             "observer_duplicate_mutating_continuation",
             "observer_external_observer_receipt_operations_sha256_mismatch",
             "observer_operation_2_process_sequence_mismatch",
             "observer_operation_3_process_sequence_mismatch"],
         "expected_barrier": 0},
        {"name": "wrong_argv", "source_run_id": "treatment-0",
         "mutation": "wrong_recovery_argv", "expected_hard_gate": "FAIL",
         "expected_errors": [
             "observer_cleanup_receipt_operations_sha256_mismatch",
             "observer_continuation_argv_mismatch",
             "observer_external_observer_receipt_operations_sha256_mismatch"],
         "expected_barrier": 0},
        {"name": "instruction_mismatch", "source_run_id": "treatment-0",
         "mutation": "recovery_instruction_mismatch", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_instruction_digest_mismatch"],
         "expected_barrier": 0},
        {"name": "exposure_mismatch", "source_run_id": "treatment-0",
         "mutation": "recovery_exposure_mismatch", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_exposure_manifest_mismatch"],
         "expected_barrier": 0},
        {"name": "legal_declared_uncertainty", "source_run_id": "treatment-1",
         "mutation": "none", "expected_hard_gate": "PASS",
         "expected_errors": [], "expected_barrier": 0},
        {"name": "legal_equivalent_argv", "source_run_id": "treatment-0",
         "mutation": "none", "expected_hard_gate": "PASS",
         "expected_errors": [], "expected_barrier": 0},
    ]
    value = {
        "schema": 2,
        "feature": "noodle_admission_recovery",
        "experiment_id": "ed3c/soodles#81-fixture",
        "admission_target": target,
        "primary_barrier": chosen or "repeated_unchanged_inspect",
        "selected_barrier": chosen,
        "barrier_order": BARRIERS,
        "allowed_uncertainties": ["owner-state-race"],
        "pilot_run_count": 3,
        "runs_per_arm": 3,
        "subject": copy.deepcopy(SUBJECT),
        "carrier": copy.deepcopy(CARRIER),
        "task_sha256": hashlib.sha256(TASK).hexdigest(),
        "instructions": {
            "baseline": hashlib.sha256(BASELINE_INSTRUCTION).hexdigest(),
            "treatment": hashlib.sha256(TREATMENT_INSTRUCTION).hexdigest(),
        },
        "exposure_sha256": replayer.fingerprint(EXPOSURE),
        "selection_sha256": selection_sha,
        "fixed_observer_sha256": FIXED_OBSERVER,
        "fixed_observer_classification": "GREEN",
        "cleanup_scope": CLEANUP_SCOPE,
        "completion_statuses": ["no_proposal"],
        "canonical_paths": CANONICAL_PATHS,
        "observer_sha256": hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
        "normalizer_sha256": hashlib.sha256(REPLAY.read_bytes()).hexdigest(),
        "decider_sha256": hashlib.sha256(DECIDER.read_bytes()).hexdigest(),
        "gates_sha256": replayer.fingerprint(gates),
        "required_controls": [item["name"] for item in controls],
        "control_specs": controls,
        "pilot_runs": pilot_declarations,
        "runs": [declaration(run, "confirmation") for run in raw["runs"]],
    }
    clean = copy.deepcopy(raw)
    for run in clean["pilot_runs"] + clean["runs"]:
        run.pop("_phase", None)
    return value, gates, clean


class RecoveryPclassReplayTests(unittest.TestCase):
    def replay(self, raw, target="improvement"):
        specification, gates, clean = manifest(raw, target)
        return replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)

    def test_fresh_pilot_selects_first_positive_and_confirmation_replays(self):
        receipt = self.replay(raw_bundle())
        self.assertEqual(receipt["classification"], "PASS", receipt["errors"])
        self.assertEqual(receipt["disposition"], "IMPROVEMENT")
        self.assertEqual(receipt["selection"]["selected_barrier"],
                         "repeated_unchanged_inspect")
        self.assertEqual(receipt["decision"]["decision"], "ADMIT_IMPROVEMENT")
        self.assertEqual(receipt["decision"]["baseline_total"], 3)
        self.assertEqual(receipt["decision"]["treatment_total"], 0)
        self.assertTrue(all(item["predicate"] == "PASS"
                            for item in receipt["controls"]))
        self.assertFalse(receipt["authorizes_landing"])

    def test_zero_pilot_has_no_qualified_barrier(self):
        raw = raw_bundle(pilot_repeated=False, baseline_repeated=False)
        receipt = self.replay(raw)
        self.assertEqual(receipt["classification"], "PASS", receipt["errors"])
        self.assertEqual(receipt["disposition"], "NO_QUALIFIED_BARRIER")
        self.assertNotIn("decision", receipt)

    def test_missing_pilot_is_inconclusive(self):
        raw = raw_bundle()
        specification, gates, clean = manifest(raw)
        clean["pilot_runs"].pop()
        receipt = replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "INCONCLUSIVE")
        self.assertEqual(receipt["disposition"], "INCONCLUSIVE")
        self.assertIn("pilot_run_set_mismatch", receipt["errors"])

    def test_wrong_preselected_barrier_is_inconclusive(self):
        raw = raw_bundle()
        specification, gates, clean = manifest(raw, selected="help_after_complete_projection")
        receipt = replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "INCONCLUSIVE")
        self.assertTrue(
            {"selection_digest_mismatch", "selected_barrier_mismatch"}
            & set(receipt["errors"]))

    def test_raw_operation_bytes_are_rehashed_and_parsed(self):
        raw = raw_bundle()
        specification, _, clean = manifest(raw)
        run = clean["runs"][3]
        run["operations"][0]["stdout_b64"] = encoded(b"{}")
        declared = copy.deepcopy(specification["runs"][3])
        declared["evidence_sha256"] = replayer.fingerprint(run)
        observer = replayer.load_module("recovery_observer_bytes", OBSERVER)
        receipt = replayer.normalize_run(run, declared, specification, observer)
        self.assertEqual(receipt["hard_gate"], "FAIL")
        self.assertIn("observer_operation_0_stdout_digest_mismatch",
                      receipt["hard_errors"])

    def test_external_and_cleanup_receipt_bytes_are_manifest_bound(self):
        raw = raw_bundle()
        specification, _, clean = manifest(raw)
        for field, expected in (
                ("external_observer_receipt_b64",
                 "observer_external_observer_receipt_manifest_mismatch"),
                ("cleanup_receipt_b64",
                 "observer_cleanup_receipt_manifest_mismatch")):
            with self.subTest(field=field):
                run = copy.deepcopy(clean["runs"][3])
                run["evidence"][field] = encoded(b"{}")
                declared = copy.deepcopy(specification["runs"][3])
                declared["evidence_sha256"] = replayer.fingerprint(run)
                observer = replayer.load_module(
                    f"recovery_observer_{field}", OBSERVER)
                receipt = replayer.normalize_run(
                    run, declared, specification, observer)
                self.assertEqual(receipt["hard_gate"], "FAIL")
                self.assertIn(expected, receipt["hard_errors"])

    def test_manifest_bound_non_object_receipts_are_rejected(self):
        raw = raw_bundle()
        specification, _, clean = manifest(raw)
        for field, digest_field, expected in (
                ("external_observer_receipt_b64",
                 "external_observer_receipt_sha256",
                 "observer_invalid_external_observer_receipt"),
                ("cleanup_receipt_b64", "cleanup_receipt_sha256",
                 "observer_invalid_cleanup_receipt")):
            with self.subTest(field=field):
                run = copy.deepcopy(clean["runs"][3])
                receipt_bytes = b"[]"
                run["evidence"][field] = encoded(receipt_bytes)
                declared = copy.deepcopy(specification["runs"][3])
                declared[digest_field] = hashlib.sha256(receipt_bytes).hexdigest()
                declared["evidence_sha256"] = replayer.fingerprint(run)
                observer = replayer.load_module(
                    f"recovery_observer_non_object_{field}", OBSERVER)
                normalized = replayer.normalize_run(
                    run, declared, specification, observer)
                self.assertIn(expected, normalized["hard_errors"])

    def test_instruction_delta_and_equal_exposure_are_enforced(self):
        raw = raw_bundle()
        specification, gates, clean = manifest(raw)
        specification["instructions"]["treatment"] = (
            specification["instructions"]["baseline"])
        receipt = replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "INCONCLUSIVE")
        self.assertTrue(any("invalid_manifest_instruction_delta" in item
                            for item in receipt["errors"]))

        specification, _, clean = manifest(raw_bundle())
        run = clean["runs"][3]
        run["packet"]["exposure"]["budget"] = 99
        declared = copy.deepcopy(specification["runs"][3])
        declared["evidence_sha256"] = replayer.fingerprint(run)
        observer = replayer.load_module("recovery_observer_exposure", OBSERVER)
        normalized = replayer.normalize_run(
            run, declared, specification, observer)
        self.assertIn("observer_exposure_manifest_mismatch",
                      normalized["hard_errors"])

    def test_legal_uncertainty_reinspection_is_not_a_barrier(self):
        raw = raw_bundle()
        specification, _, clean = manifest(raw)
        run = raw_run("treatment-u", "treatment", legal_uncertainty=True)
        run["packet"]["selection_sha256"] = specification["selection_sha256"]
        run.pop("_phase")
        declared = declaration({**copy.deepcopy(run), "_phase": "confirmation"},
                               "confirmation")
        observer = replayer.load_module("recovery_observer_uncertainty", OBSERVER)
        receipt = replayer.normalize_run(
            run, declared, specification, observer)
        self.assertEqual(receipt["hard_gate"], "PASS", receipt["hard_errors"])
        self.assertEqual(receipt["barriers"]["repeated_unchanged_inspect"], 0)

    def test_unverified_uncertainty_labels_do_not_suppress_barrier(self):
        raw = raw_bundle()
        specification, _, clean = manifest(raw)
        run = copy.deepcopy(clean["runs"][3])
        run["operations"][0]["opens_uncertainty"] = "owner-state-race"
        repeated = copy.deepcopy(run["operations"][0])
        repeated.pop("opens_uncertainty")
        repeated["resolves_uncertainty"] = "owner-state-race"
        process = json.loads(base64.b64decode(repeated["process_receipt_b64"]))
        process["sequence"] = 1
        repeated["process_receipt_b64"] = encoded(json_raw(process))
        for event in run["operations"][1:]:
            process = json.loads(base64.b64decode(event["process_receipt_b64"]))
            process["sequence"] += 1
            event["process_receipt_b64"] = encoded(json_raw(process))
        run["operations"].insert(1, repeated)
        declared = copy.deepcopy(specification["runs"][3])
        declared["evidence_sha256"] = replayer.fingerprint(run)
        observer = replayer.load_module("recovery_observer_unverified", OBSERVER)
        receipt = replayer.normalize_run(run, declared, specification, observer)
        self.assertEqual(receipt["barriers"]["repeated_unchanged_inspect"], 1)

    def test_pilot_and_confirmation_sessions_must_be_distinct(self):
        raw = raw_bundle()
        raw["runs"][0]["consumer"]["session_id"] = (
            raw["pilot_runs"][0]["consumer"]["session_id"])
        specification, gates, clean = manifest(raw)
        receipt = replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "INCONCLUSIVE")
        self.assertIn("pilot_confirmation_consumer_session_id_not_distinct",
                      receipt["errors"])

    def test_incomplete_confirmation_is_inconclusive(self):
        raw = raw_bundle()
        specification, gates, clean = manifest(raw)
        clean["runs"].pop()
        receipt = replayer.replay(
            clean, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "INCONCLUSIVE")
        self.assertEqual(receipt["disposition"], "INCONCLUSIVE")
        self.assertIn("confirmation_run_set_mismatch", receipt["errors"])


if __name__ == "__main__":
    unittest.main()
