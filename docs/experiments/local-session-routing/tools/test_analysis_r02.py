"""Synthetic r02 aggregate controls only; never experiment run evidence."""

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "analysis_r02", Path(__file__).with_name("analysis-r02.py"))
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)
SCOPE = "synthetic_control_not_run_evidence"


def pin(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class AggregateControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        pins = {}
        for name in ("protocol", "oracle", "harness"):
            path = self.root / name
            path.write_text(SCOPE + ":" + name)
            pins[name] = pin(path)
        self.manifest = {"schema": 1, "pins": pins, "runs": []}
        values = {
            "selection": {"baseline": [10, 10, 11], "candidate": [8, 8, 9]},
            "confirmation": {"baseline": [5, 5, 6], "candidate": [4, 4, 5]},
        }
        serial = 0
        for split in ("selection", "confirmation"):
            for stratum, count in (("A", 3), ("B", 1), ("C", 1)):
                for arm in ("baseline", "candidate"):
                    commands = values[split][arm] if stratum == "A" else [20]
                    for repeat in range(count):
                        serial += 1
                        result = self.write_result(str(serial), commands[repeat], "PASS")
                        self.manifest["runs"].append({
                            "split": split, "group": split + "-" + stratum,
                            "arm": arm, "stratum": stratum, "result": result,
                        })

    def tearDown(self):
        self.temporary.cleanup()

    def write_result(self, name, commands, classification):
        path = self.root / (name + ".json")
        path.write_text(json.dumps({
            "evidence_validity": "VALID",
            "behavior": {"classification": classification},
            "cost": {"completed_commands": commands},
            "cost_comparison_eligible": classification == "PASS",
            "authorizes_landing": False,
        }, sort_keys=True))
        return pin(path)

    def find(self, split, arm, stratum):
        return next(run for run in self.manifest["runs"]
                    if (run["split"], run["arm"], run["stratum"])
                    == (split, arm, stratum))

    def test_pins_and_legal_medians_adopt(self):
        result = analysis.aggregate(self.manifest)
        self.assertEqual(result["behavior"]["comparison_gate"], "PASS")
        self.assertEqual(result["behavior"]["baseline_B_C"], "PASS")
        self.assertTrue(result["adopt"])
        self.assertEqual(result["cost"]["selection"]["candidate_median"], 8)
        self.assertEqual(result["cost"]["confirmation"]["candidate_median"], 4)
        self.assertFalse(result["authorizes_landing"])

    def test_selection_without_confirmation_can_keep_but_not_adopt(self):
        self.manifest["runs"] = [run for run in self.manifest["runs"]
                                 if run["split"] == "selection"]
        manifest = self.root / "selection-manifest.json"
        manifest.write_text(json.dumps(self.manifest, sort_keys=True))
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = analysis.main(["analysis-r02.py", "--selection", str(manifest),
                                  pin(manifest)["sha256"]])
        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(result["keep_candidate"])
        self.assertTrue(result["confirmation_pending"])
        self.assertFalse(result["adopt"])

    def test_baseline_B_failure_is_historical_and_selection_can_keep(self):
        self.manifest["runs"] = [run for run in self.manifest["runs"]
                                 if run["split"] == "selection"]
        self.find("selection", "baseline", "B")["result"] = \
            self.write_result("historical-B-failure", 0, "FAIL")
        result = analysis.aggregate(self.manifest, "selection")
        self.assertEqual(result["behavior"]["comparison_gate"], "PASS")
        self.assertEqual(result["behavior"]["baseline_B_C"], "FAIL")
        self.assertEqual(result["behavior"]["historical_failures"],
                         ["selection:selection-B:baseline:B"])
        self.assertTrue(result["keep_candidate"])
        self.assertIsNotNone(result["cost"])
        self.assertFalse(result["adopt"])

    def test_baseline_A_failure_blocks_cost(self):
        self.find("selection", "baseline", "A")["result"] = \
            self.write_result("baseline-A-failure", 0, "FAIL")
        result = analysis.aggregate(self.manifest)
        self.assertEqual(result["behavior"]["comparison_gate"], "FAIL")
        self.assertIsNone(result["cost"])
        self.assertFalse(result["adopt"])

    def test_candidate_failure_cannot_win_with_zero_cost(self):
        self.find("selection", "candidate", "B")["result"] = \
            self.write_result("candidate-B-failure", 0, "FAIL")
        result = analysis.aggregate(self.manifest)
        self.assertEqual(result["behavior"]["comparison_gate"], "FAIL")
        self.assertIsNone(result["cost"])
        self.assertFalse(result["adopt"])

    def test_invalid_result_blocks_comparison(self):
        path = self.root / "invalid-result.json"
        path.write_text(json.dumps({"evidence_validity": "INVALID", "behavior": None,
                                    "cost": None, "authorizes_landing": False}))
        self.find("selection", "baseline", "B")["result"] = pin(path)
        result = analysis.aggregate(self.manifest)
        self.assertEqual(result["evidence_validity"], "INVALID")
        self.assertIsNone(result["behavior"])
        self.assertIsNone(result["cost"])
        self.assertFalse(result["adopt"])

    def test_changed_pin_is_invalid(self):
        Path(self.manifest["pins"]["harness"]["path"]).write_text("changed")
        with self.assertRaisesRegex(analysis.EvidenceError, "harness:digest_mismatch"):
            analysis.aggregate(self.manifest)

    def test_cross_split_group_collision_is_invalid(self):
        for run in self.manifest["runs"]:
            if run["split"] == "confirmation" and run["stratum"] == "A":
                run["group"] = "selection-A"
        with self.assertRaisesRegex(analysis.EvidenceError, "cross_split_group_collision"):
            analysis.aggregate(self.manifest)


if __name__ == "__main__":
    unittest.main()
