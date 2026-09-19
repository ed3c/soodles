import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/verify-soodles/scripts/replay_pclass.py"
OBSERVER = ROOT / ".agents/skills/verify-soodles/scripts/observe_pclass.py"
DECIDER = ROOT / ".agents/skills/verify-soodles/scripts/decide_pclass.py"
RAW = ROOT / "docs/experiments/pclass-recovery-stop-73/raw/raw-runs.json"
spec = importlib.util.spec_from_file_location("pclass_replay", SCRIPT)
replayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replayer)


def manifest(raw):
    gates = {
        "schema": 1,
        "experiment_id": "ed3c/soodles#73-replay",
        "causal_delta": {"classification": "PASS"},
        "independent_audit": {"classification": "PASS"},
        "telemetry": {"authority": "report_only"},
    }
    specification = {
        "schema": 2,
        "experiment_id": "ed3c/soodles#73-replay",
        "admission_target": "improvement",
        "primary_barrier": "post_completion_owner_request",
        "runs_per_arm": 3,
        "observer_sha256": hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
        "normalizer_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "decider_sha256": hashlib.sha256(DECIDER.read_bytes()).hexdigest(),
        "gates_sha256": replayer.fingerprint(gates),
        "required_controls": [
            "premature_stop", "wrong_operation", "stale_completion_digest",
            "missing_transport_evidence", "request_after_completion",
            "legal_exact_completion_no_request"],
        "control_specs": [
            {"name": "premature_stop", "source_run_id": "19cfa2",
             "mutation": "premature_stop", "expected_hard_gate": "FAIL",
             "expected_errors": ["completion_projection_observation_not_unique",
                                 "observer_missing_recovery_continuation"],
             "expected_barrier": 0},
            {"name": "wrong_operation", "source_run_id": "19cfa2",
             "mutation": "wrong_operation", "expected_hard_gate": "FAIL",
             "expected_errors": ["completion_projection_observation_not_unique",
                                 "observer_wrong_operation_for_state"],
             "expected_barrier": 0},
            {"name": "stale_completion_digest", "source_run_id": "19cfa2",
             "mutation": "stale_completion_digest", "expected_hard_gate": "FAIL",
             "expected_errors": ["treatment_completion_digest_mismatch"],
             "expected_barrier": 0},
            {"name": "missing_transport_evidence", "source_run_id": "19cfa2",
             "mutation": "missing_transport_evidence", "expected_hard_gate": "FAIL",
             "expected_errors": ["observer_invalid_transport_evidence",
                                 "packet_transport_not_empty"],
             "expected_barrier": 0},
            {"name": "request_after_completion", "source_run_id": "19cfa2",
             "donor_run_id": "3b7e81", "mutation": "request_after_completion",
             "expected_hard_gate": "FAIL",
             "expected_errors": ["owner_operation_after_completion"],
             "expected_barrier": 1},
            {"name": "legal_exact_completion_no_request", "source_run_id": "19cfa2",
             "mutation": "none", "expected_hard_gate": "PASS",
             "expected_errors": [], "expected_barrier": 0},
        ],
        "runs": [{
            "run_id": run["run_id"],
            "arm": run["arm"],
            "case": run["packet"]["case"],
            "evidence_sha256": replayer.fingerprint(run),
        } for run in raw["runs"]],
    }
    return specification, gates


class PclassReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text())

    def test_issue_73_replays_three_to_zero(self):
        specification, gates = manifest(self.raw)
        receipt = replayer.replay(
            self.raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, SCRIPT)
        self.assertEqual(receipt["classification"], "PASS", receipt["errors"])
        self.assertEqual(
            [item["barriers"]["post_completion_owner_request"]
             for item in receipt["baseline"]], [1, 1, 1])
        self.assertEqual(
            [item["barriers"]["post_completion_owner_request"]
             for item in receipt["treatment"]], [0, 0, 0])
        self.assertTrue(all(item["hard_gate"] == "PASS"
                            for arm in ("baseline", "treatment")
                            for item in receipt[arm]))
        self.assertFalse(receipt["authorizes_landing"])
        self.assertEqual(receipt["decision"]["decision"], "ADMIT_IMPROVEMENT")
        self.assertTrue(all(item["predicate"] == "PASS"
                            for item in receipt["controls"]))

    def test_raw_evidence_tampering_is_red(self):
        specification, gates = manifest(self.raw)
        changed = copy.deepcopy(self.raw)
        changed["runs"][0]["owner_events"].append({"owner": "landing.dispatch"})
        receipt = replayer.replay(
            changed, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, SCRIPT)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertTrue(any("evidence_sha256_manifest_mismatch" in error
                            for error in receipt["errors"]))

    def test_analyzer_digest_mismatch_is_red(self):
        specification, gates = manifest(self.raw)
        specification["observer_sha256"] = "f" * 64
        receipt = replayer.replay(
            self.raw, gates, specification, replayer.fingerprint(specification),
            OBSERVER, DECIDER, SCRIPT)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertIn("observer_digest_mismatch", receipt["errors"])

    def test_digest_failure_happens_before_analyzer_import(self):
        specification, gates = manifest(self.raw)
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "imported"
            analyzer = Path(directory) / "observer.py"
            analyzer.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
            receipt = replayer.replay(
                self.raw, gates, specification, replayer.fingerprint(specification),
                analyzer, DECIDER, SCRIPT)
            self.assertEqual(receipt["classification"], "FAIL")
            self.assertIn("observer_digest_mismatch", receipt["errors"])
            self.assertFalse(marker.exists())

    def test_treatment_operation_after_completion_is_red(self):
        specification, _ = manifest(self.raw)
        source = copy.deepcopy(next(
            item for item in self.raw["runs"] if item["arm"] == "treatment"))
        donor = next(item for item in self.raw["runs"] if item["arm"] == "baseline")
        source["owner_events"].append(copy.deepcopy(donor["owner_events"][-1]))
        declared = copy.deepcopy(next(
            item for item in specification["runs"] if item["run_id"] == source["run_id"]))
        declared["evidence_sha256"] = replayer.fingerprint(source)
        observer = replayer.load_module("test_observer", OBSERVER)
        receipt = replayer.normalize_run(source, declared, specification, observer)
        self.assertEqual(receipt["hard_gate"], "FAIL")
        self.assertIn("owner_operation_after_completion", receipt["hard_errors"])


if __name__ == "__main__":
    unittest.main()
