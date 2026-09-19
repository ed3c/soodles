import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/verify-soodles/scripts/replay_pclass.py"
OBSERVER = ROOT / ".agents/skills/verify-soodles/scripts/observe_pclass.py"
RAW = ROOT / "docs/experiments/pclass-recovery-stop-73/raw/raw-runs.json"
spec = importlib.util.spec_from_file_location("pclass_replay", SCRIPT)
replayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replayer)


def manifest(raw):
    return {
        "schema": 1,
        "experiment_id": "ed3c/soodles#73-replay",
        "admission_target": "improvement",
        "primary_barrier": "post_completion_owner_request",
        "observer_sha256": hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
        "normalizer_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "required_controls": ["completion_boundary", "legal_continuation"],
        "runs": [{
            "run_id": run["run_id"],
            "arm": run["arm"],
            "case": run["packet"]["case"],
            "evidence_sha256": replayer.fingerprint(run),
        } for run in raw["runs"]],
    }


class PclassReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text())

    def test_issue_73_replays_three_to_zero(self):
        specification = manifest(self.raw)
        receipt = replayer.replay(
            self.raw, specification, replayer.fingerprint(specification), OBSERVER, SCRIPT)
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

    def test_raw_evidence_tampering_is_red(self):
        specification = manifest(self.raw)
        changed = copy.deepcopy(self.raw)
        changed["runs"][0]["owner_events"].append({"owner": "landing.dispatch"})
        receipt = replayer.replay(
            changed, specification, replayer.fingerprint(specification), OBSERVER, SCRIPT)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertTrue(any("evidence_sha256_manifest_mismatch" in error
                            for error in receipt["errors"]))

    def test_analyzer_digest_mismatch_is_red(self):
        specification = manifest(self.raw)
        specification["observer_sha256"] = "f" * 64
        receipt = replayer.replay(
            self.raw, specification, replayer.fingerprint(specification), OBSERVER, SCRIPT)
        self.assertEqual(receipt["classification"], "FAIL")
        self.assertIn("observer_digest_mismatch", receipt["errors"])


if __name__ == "__main__":
    unittest.main()
