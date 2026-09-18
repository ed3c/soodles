import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/verify-soodles/scripts/decide_pclass.py"
spec = importlib.util.spec_from_file_location("pclass_decision", SCRIPT)
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)


def packet(target="nonregression", baseline=(0, 0, 0), treatment=(0, 0, 0)):
    def receipts(values):
        return [{"hard_gate": "PASS", "barriers": {"wrong_route": value}}
                for value in values]
    return {
        "schema": 1,
        "admission_target": target,
        "primary_barrier": "wrong_route",
        "baseline": receipts(baseline),
        "treatment": receipts(treatment),
        "controls": [
            {"name": "wrong_route", "expected": "FAIL", "observed": "FAIL"},
            {"name": "legal_route", "expected": "PASS", "observed": "PASS"},
        ],
        "causal_delta": {"classification": "PASS"},
        "independent_audit": {"classification": "PASS"},
        "telemetry": {"elapsed_seconds": {"baseline": 3.0, "treatment": 2.0}},
    }


class PclassDecisionTests(unittest.TestCase):
    def test_equal_green_arms_admit_only_nonregression(self):
        receipt = decision.evaluate(packet())
        self.assertEqual(receipt["decision"], "ADMIT_NONREGRESSION")
        self.assertEqual(receipt["baseline_total"], 0)
        self.assertEqual(receipt["treatment_total"], 0)
        self.assertFalse(receipt["authorizes_landing"])

        improvement = decision.evaluate(packet(target="improvement"))
        self.assertEqual(improvement["decision"], "REJECT")
        self.assertIn("primary_barrier_not_improved", improvement["hard_gate_errors"])

    def test_strictly_lower_barrier_admits_improvement(self):
        receipt = decision.evaluate(packet(
            target="improvement", baseline=(1, 0, 0), treatment=(0, 0, 0)))
        self.assertEqual(receipt["decision"], "ADMIT_IMPROVEMENT")
        self.assertEqual(receipt["baseline_total"], 1)
        self.assertEqual(receipt["treatment_total"], 0)

    def test_behavior_failure_rejects_despite_better_telemetry(self):
        value = packet()
        value["treatment"][0]["hard_gate"] = "FAIL"
        value["telemetry"] = {
            "elapsed_seconds": {"baseline": 100, "treatment": 1},
            "bytes": {"baseline": 10000, "treatment": 1},
        }
        receipt = decision.evaluate(value)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("treatment_0_hard_gate_not_pass", receipt["hard_gate_errors"])
        self.assertEqual(receipt["telemetry"], value["telemetry"])
        self.assertEqual(receipt["telemetry_authority"], "report_only")

    def test_missing_or_mismatched_control_rejects(self):
        missing = packet()
        missing["controls"] = []
        receipt = decision.evaluate(missing)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("missing_sensitivity_controls", receipt["hard_gate_errors"])

        mismatch = packet()
        mismatch["controls"][0]["observed"] = "PASS"
        receipt = decision.evaluate(mismatch)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("control_0_mismatch", receipt["hard_gate_errors"])

    def test_worse_telemetry_cannot_turn_nonregression_red(self):
        value = packet()
        value["telemetry"] = {
            "elapsed_seconds": {"baseline": 1, "treatment": 100},
            "bytes": {"baseline": 1, "treatment": 10000},
        }
        receipt = decision.evaluate(value)
        self.assertEqual(receipt["decision"], "ADMIT_NONREGRESSION")
        self.assertEqual(receipt["telemetry"], value["telemetry"])

    def test_missing_audit_causal_delta_or_barrier_rejects(self):
        for key, expected in (
                ("independent_audit", "missing_independent_audit"),
                ("causal_delta", "missing_causal_delta")):
            with self.subTest(key=key):
                value = packet()
                del value[key]
                receipt = decision.evaluate(value)
                self.assertEqual(receipt["decision"], "REJECT")
                self.assertIn(expected, receipt["hard_gate_errors"])
        value = packet()
        del value["treatment"][1]["barriers"]["wrong_route"]
        receipt = decision.evaluate(value)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("missing_treatment_1_primary_barrier", receipt["hard_gate_errors"])

    def test_regression_rejects_nonregression_target(self):
        receipt = decision.evaluate(packet(treatment=(0, 1, 0)))
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("primary_barrier_regressed", receipt["hard_gate_errors"])

    def test_unknown_or_negative_counts_reject(self):
        for invalid in (None, -1, True, "0"):
            with self.subTest(invalid=invalid):
                value = packet()
                value["treatment"][0]["barriers"]["wrong_route"] = invalid
                receipt = decision.evaluate(value)
                self.assertEqual(receipt["decision"], "REJECT")
                self.assertIn("invalid_treatment_0_primary_barrier",
                              receipt["hard_gate_errors"])


if __name__ == "__main__":
    unittest.main()
