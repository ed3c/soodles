import copy
import hashlib
import importlib.util
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
FIXED_OBSERVER = "a" * 64
INSTRUCTION = {"path": ".agents/skills/verify-noodle/features/admission-recovery.md",
               "sha256": "b" * 64}
INPUT = "c" * 64
CANONICAL = {"orders-next.json": "d" * 64, "state.snapshot.json": "e" * 64,
             "orders.json": "f" * 64}


def projection(status, revision=7):
    if status == "recoverable":
        next_value = {
            "argv": ["/tmp/noodle", "--project-dir", "/tmp/project", "admission",
                     "retire", "--proposal-sha256", "1" * 64,
                     "--revision", str(revision)],
        }
    else:
        next_value = None
    return {"owner": "Noodle", "status": status,
            "subject": {"proposal_sha256": "1" * 64},
            "current_order_revision": revision, "next": next_value}


def process_event(**values):
    return {"exit_code": 0, "elapsed_ms": 1,
            "stdout_sha256": "2" * 64, "stderr_sha256": "3" * 64, **values}


def raw_run(run_id, arm, repeated=False, manual=False):
    initial = projection("recoverable")
    completed = projection("no_proposal")
    initial_sha = replayer.fingerprint(initial)
    completed_sha = replayer.fingerprint(completed)
    inspect = process_event(kind="owner_read", operation="admission.inspect",
                            projection=initial, projection_sha256=initial_sha)
    operations = [inspect]
    if repeated:
        operations.append(copy.deepcopy(inspect))
    operations.extend([
        process_event(kind="owner_action", operation="admission.retire",
                      argv=initial["next"]["argv"],
                      argv_source="manual" if manual else "projection",
                      bound_projection_sha256=initial_sha),
        process_event(kind="owner_read", operation="admission.inspect",
                      projection=completed, projection_sha256=completed_sha),
    ])
    return {
        "run_id": run_id,
        "arm": arm,
        "packet": {
            "run_id": run_id, "arm": arm, "case": "admission_recovery",
            "subject": copy.deepcopy(SUBJECT), "carrier": {"id": "linux_amd64", "os": "linux", "arch": "amd64"},
            "instruction": copy.deepcopy(INSTRUCTION),
            "initial_owner_projection": initial,
            "expected_owner_projection_sha256": initial_sha,
            "transport_events": [],
        },
        "precondition": {
            "subject": copy.deepcopy(SUBJECT), "carrier": {"id": "linux_amd64", "os": "linux", "arch": "amd64"},
            "initial_owner_projection": initial,
            "initial_owner_projection_sha256": initial_sha,
            "provider_transport_observed": False,
            "preserved_input_sha256": INPUT,
            "canonical_files": copy.deepcopy(CANONICAL),
        },
        "operations": operations,
        "postcondition": {
            "completion_owner_projection": completed,
            "completion_owner_projection_sha256": completed_sha,
            "retired_archive_sha256": INPUT,
            "canonical_files": copy.deepcopy(CANONICAL),
            "mailbox_absent": True,
            "remaining_processes": [],
            "residue_paths": [],
            "cleanup_scope": ["fixture", "process_group"],
        },
        "instruction_observations": [copy.deepcopy(INSTRUCTION)],
        "external_observer": {"sha256": FIXED_OBSERVER, "classification": "GREEN",
                              "receipt_sha256": "4" * 64},
        "consumer": {"run_id": run_id, "authorizes_landing": False},
    }


def raw_bundle():
    runs = []
    for arm in ("baseline", "treatment"):
        for index in range(3):
            runs.append(raw_run(f"{arm}-{index}", arm,
                                repeated=arm == "baseline",
                                manual=arm == "treatment" and index == 0))
    return {"runs": runs}


def manifest(raw, target="improvement"):
    gates = {
        "schema": 1, "experiment_id": "ed3c/soodles#81-fixture",
        "causal_delta": {"classification": "PASS"},
        "independent_audit": {"classification": "PASS"},
        "telemetry": {"authority": "report_only"},
    }
    controls = [
        {"name": "stale_projection_binding", "source_run_id": "treatment-0",
         "mutation": "stale_recovery_binding", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_continuation_projection_binding_mismatch"],
         "expected_barrier": 0},
        {"name": "wrong_subject", "source_run_id": "treatment-0",
         "mutation": "wrong_recovery_subject", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_packet_subject_manifest_mismatch"],
         "expected_barrier": 0},
        {"name": "missing_completion", "source_run_id": "treatment-0",
         "mutation": "missing_recovery_completion", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_missing_completion_owner_projection"],
         "expected_barrier": 0},
        {"name": "false_cleanup", "source_run_id": "treatment-0",
         "mutation": "false_recovery_cleanup", "expected_hard_gate": "FAIL",
         "expected_errors": ["observer_cleanup_residue"],
         "expected_barrier": 0},
        {"name": "legal_equivalent_argv", "source_run_id": "treatment-0",
         "mutation": "none", "expected_hard_gate": "PASS",
         "expected_errors": [], "expected_barrier": 0},
        {"name": "legal_fresh_completion_inspect", "source_run_id": "treatment-1",
         "mutation": "none", "expected_hard_gate": "PASS",
         "expected_errors": [], "expected_barrier": 0},
    ]
    value = {
        "schema": 2,
        "feature": "noodle_admission_recovery",
        "experiment_id": "ed3c/soodles#81-fixture",
        "admission_target": target,
        "primary_barrier": "repeated_unchanged_inspect",
        "runs_per_arm": 3,
        "subject": copy.deepcopy(SUBJECT),
        "carrier": {"id": "linux_amd64", "os": "linux", "arch": "amd64"},
        "fixed_observer_sha256": FIXED_OBSERVER,
        "fixed_observer_classification": "GREEN",
        "cleanup_scope": ["fixture", "process_group"],
        "completion_statuses": ["no_proposal"],
        "canonical_paths": sorted(CANONICAL),
        "observer_sha256": hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
        "normalizer_sha256": hashlib.sha256(REPLAY.read_bytes()).hexdigest(),
        "decider_sha256": hashlib.sha256(DECIDER.read_bytes()).hexdigest(),
        "gates_sha256": replayer.fingerprint(gates),
        "required_controls": [item["name"] for item in controls],
        "control_specs": controls,
        "runs": [{
            "run_id": run["run_id"], "arm": run["arm"],
            "case": run["packet"]["case"],
            "evidence_sha256": replayer.fingerprint(run),
            "initial_owner_projection_sha256":
                run["packet"]["expected_owner_projection_sha256"],
            "external_observer_receipt_sha256":
                run["external_observer"]["receipt_sha256"],
        } for run in raw["runs"]],
    }
    return value, gates


class RecoveryPclassReplayTests(unittest.TestCase):
    def test_complete_recovery_evidence_replays_three_to_zero(self):
        raw = raw_bundle()
        specification, gates = manifest(raw)
        receipt = replayer.replay(
            raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "PASS", receipt["errors"])
        self.assertEqual(receipt["decision"]["decision"], "ADMIT_IMPROVEMENT")
        self.assertEqual(receipt["decision"]["baseline_total"], 3)
        self.assertEqual(receipt["decision"]["treatment_total"], 0)
        self.assertTrue(all(item["predicate"] == "PASS"
                            for item in receipt["controls"]))
        self.assertFalse(receipt["authorizes_landing"])

    def test_raw_subject_tampering_is_bound_by_manifest(self):
        raw = raw_bundle()
        specification, gates = manifest(raw)
        raw["runs"][0]["packet"]["subject"]["source_revision"] = "9" * 40
        receipt = replayer.replay(
            raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertTrue(any("evidence_sha256_manifest_mismatch" in item
                            for item in receipt["errors"]))

    def test_manifest_cannot_omit_recovery_owner_bindings(self):
        raw = raw_bundle()
        expected = {
            "subject": "observer_invalid_manifest_subject",
            "carrier": "observer_invalid_manifest_carrier",
            "fixed_observer_classification":
                "observer_invalid_manifest_observer_classification",
            "cleanup_scope": "observer_invalid_manifest_cleanup_scope",
            "completion_statuses":
                "observer_invalid_manifest_completion_statuses",
            "canonical_paths": "observer_invalid_manifest_canonical_paths",
        }
        for key, error in expected.items():
            with self.subTest(key=key):
                specification, gates = manifest(raw)
                del specification[key]
                receipt = replayer.replay(
                    raw, gates, specification, replayer.fingerprint(specification),
                    OBSERVER, DECIDER, REPLAY)
                self.assertEqual(receipt["classification"], "FAIL")
                self.assertTrue(any(error in item for item in receipt["errors"]),
                                receipt["errors"])

    def test_external_observer_receipt_is_bound_per_run(self):
        raw = raw_bundle()
        specification, _ = manifest(raw)
        run = copy.deepcopy(raw["runs"][3])
        run["external_observer"]["receipt_sha256"] = "9" * 64
        declared = copy.deepcopy(specification["runs"][3])
        declared["evidence_sha256"] = replayer.fingerprint(run)
        observer_spec = importlib.util.spec_from_file_location(
            "recovery_observer_test", OBSERVER)
        observer = importlib.util.module_from_spec(observer_spec)
        observer_spec.loader.exec_module(observer)
        receipt = replayer.normalize_run(
            run, declared, specification, observer)
        self.assertEqual(receipt["hard_gate"], "FAIL")
        self.assertIn("external_observer_receipt_manifest_mismatch",
                      receipt["hard_errors"])

    def test_zero_to_zero_cannot_admit_improvement(self):
        raw = raw_bundle()
        for run in raw["runs"]:
            if run["arm"] == "baseline":
                run["operations"].pop(1)
        specification, gates = manifest(raw)
        receipt = replayer.replay(
            raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertEqual(receipt["decision"]["decision"], "REJECT")
        self.assertIn("primary_barrier_not_improved",
                      receipt["decision"]["hard_gate_errors"])

    def test_incomplete_arm_is_rejected_before_comparison(self):
        raw = raw_bundle()
        specification, gates = manifest(raw)
        raw["runs"].pop()
        receipt = replayer.replay(
            raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, REPLAY)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertIn("run_set_mismatch", receipt["errors"])


if __name__ == "__main__":
    unittest.main()
