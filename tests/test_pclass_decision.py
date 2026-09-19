import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/verify-soodles/scripts/decide_pclass.py"
spec = importlib.util.spec_from_file_location("pclass_decision", SCRIPT)
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)

OBSERVER = "1" * 64
NORMALIZER = "2" * 64


def manifest(target="nonregression"):
    runs = []
    for arm in ("baseline", "treatment"):
        for index in range(3):
            run_id = f"{arm}-{index}"
            runs.append({
                "run_id": run_id,
                "arm": arm,
                "case": "recovery",
                "evidence_sha256": hashlib.sha256(run_id.encode()).hexdigest(),
            })
    return {
        "schema": 1,
        "experiment_id": "test-comparison",
        "admission_target": target,
        "primary_barrier": "wrong_route",
        "observer_sha256": OBSERVER,
        "normalizer_sha256": NORMALIZER,
        "required_controls": ["wrong_route", "legal_route"],
        "runs": runs,
    }


def packet(specification, baseline=(0, 0, 0), treatment=(0, 0, 0)):
    values = {"baseline": iter(baseline), "treatment": iter(treatment)}
    receipts = {"baseline": [], "treatment": []}
    for declared in specification["runs"]:
        arm = declared["arm"]
        receipts[arm].append({
            **declared,
            "hard_gate": "PASS",
            "barriers": {"wrong_route": next(values[arm])},
            "observer_sha256": OBSERVER,
            "normalizer_sha256": NORMALIZER,
        })
    return {
        "schema": 2,
        "experiment_id": specification["experiment_id"],
        "manifest_sha256": decision.fingerprint(specification),
        "admission_target": specification["admission_target"],
        "primary_barrier": specification["primary_barrier"],
        **receipts,
        "controls": [
            {"name": "wrong_route", "expected": "FAIL", "observed": "FAIL"},
            {"name": "legal_route", "expected": "PASS", "observed": "PASS"},
        ],
        "causal_delta": {"classification": "PASS"},
        "independent_audit": {"classification": "PASS"},
        "telemetry": {"elapsed_seconds": {"baseline": 3.0, "treatment": 2.0}},
    }


def evaluate(specification, value):
    return decision.evaluate(value, specification, decision.fingerprint(specification))


class PclassDecisionTests(unittest.TestCase):
    def test_complete_equal_arms_admit_only_nonregression(self):
        specification = manifest()
        receipt = evaluate(specification, packet(specification))
        self.assertEqual(receipt["decision"], "ADMIT_NONREGRESSION")
        self.assertEqual(receipt["observed_run_count"], 6)
        self.assertFalse(receipt["authorizes_landing"])

        specification = manifest(target="improvement")
        receipt = evaluate(specification, packet(specification))
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("primary_barrier_not_improved", receipt["hard_gate_errors"])

    def test_complete_strictly_lower_barrier_admits_improvement(self):
        specification = manifest(target="improvement")
        receipt = evaluate(specification, packet(
            specification, baseline=(1, 1, 1), treatment=(0, 0, 0)))
        self.assertEqual(receipt["decision"], "ADMIT_IMPROVEMENT")
        self.assertEqual(receipt["baseline_total"], 3)
        self.assertEqual(receipt["treatment_total"], 0)

    def test_three_against_one_is_incomplete_not_improvement(self):
        specification = manifest(target="improvement")
        value = packet(specification, baseline=(1, 1, 1), treatment=(1, 1, 1))
        value["treatment"] = value["treatment"][:1]
        receipt = evaluate(specification, value)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("run_set_mismatch", receipt["hard_gate_errors"])

    def test_duplicate_or_extra_run_rejects(self):
        specification = manifest(target="improvement")
        value = packet(specification, baseline=(1, 1, 1))
        value["treatment"][2] = copy.deepcopy(value["treatment"][0])
        receipt = evaluate(specification, value)
        self.assertIn("duplicate_run_id_treatment-0", receipt["hard_gate_errors"])
        self.assertIn("run_set_mismatch", receipt["hard_gate_errors"])

        value = packet(specification, baseline=(1, 1, 1))
        value["treatment"].append({**value["treatment"][0], "run_id": "extra"})
        receipt = evaluate(specification, value)
        self.assertIn("unexpected_run_id_extra", receipt["hard_gate_errors"])

    def test_arm_case_and_evidence_bindings_reject(self):
        specification = manifest(target="improvement")
        fields = {
            "arm": "other",
            "case": "pending",
            "evidence_sha256": "f" * 64,
            "observer_sha256": "e" * 64,
            "normalizer_sha256": "d" * 64,
        }
        for key, replacement in fields.items():
            with self.subTest(key=key):
                value = packet(specification, baseline=(1, 1, 1))
                value["baseline"][0][key] = replacement
                receipt = evaluate(specification, value)
                self.assertEqual(receipt["decision"], "REJECT")
                self.assertIn(f"baseline-0_{key}_mismatch", receipt["hard_gate_errors"])

    def test_manifest_binding_rejects(self):
        specification = manifest(target="improvement")
        value = packet(specification, baseline=(1, 1, 1))
        receipt = decision.evaluate(value, specification, "f" * 64)
        self.assertIn("manifest_digest_mismatch", receipt["hard_gate_errors"])
        self.assertIn("packet_manifest_digest_mismatch", receipt["hard_gate_errors"])

        value = packet(specification, baseline=(1, 1, 1))
        value["primary_barrier"] = "other"
        receipt = evaluate(specification, value)
        self.assertIn("primary_barrier_manifest_mismatch", receipt["hard_gate_errors"])

    def test_controls_must_exactly_match_manifest(self):
        specification = manifest()
        for mutation in ("missing", "duplicate", "extra"):
            with self.subTest(mutation=mutation):
                value = packet(specification)
                if mutation == "missing":
                    value["controls"] = value["controls"][:1]
                elif mutation == "duplicate":
                    value["controls"][1] = copy.deepcopy(value["controls"][0])
                else:
                    value["controls"].append(
                        {"name": "unplanned", "expected": "PASS", "observed": "PASS"})
                receipt = evaluate(specification, value)
                self.assertEqual(receipt["decision"], "REJECT")
                self.assertIn("control_set_mismatch", receipt["hard_gate_errors"])

    def test_behavior_failure_rejects_despite_better_telemetry(self):
        specification = manifest()
        value = packet(specification)
        value["treatment"][0]["hard_gate"] = "FAIL"
        value["telemetry"] = {"elapsed_seconds": {"baseline": 100, "treatment": 1}}
        receipt = evaluate(specification, value)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("treatment_0_hard_gate_not_pass", receipt["hard_gate_errors"])
        self.assertEqual(receipt["telemetry_authority"], "report_only")

    def test_worse_telemetry_cannot_turn_nonregression_red(self):
        specification = manifest()
        value = packet(specification)
        value["telemetry"] = {"elapsed_seconds": {"baseline": 1, "treatment": 100}}
        receipt = evaluate(specification, value)
        self.assertEqual(receipt["decision"], "ADMIT_NONREGRESSION")

    def test_missing_audit_delta_or_barrier_rejects(self):
        specification = manifest()
        for key, expected in (("independent_audit", "missing_independent_audit"),
                              ("causal_delta", "missing_causal_delta")):
            with self.subTest(key=key):
                value = packet(specification)
                del value[key]
                receipt = evaluate(specification, value)
                self.assertIn(expected, receipt["hard_gate_errors"])
        value = packet(specification)
        del value["treatment"][1]["barriers"]["wrong_route"]
        receipt = evaluate(specification, value)
        self.assertIn("missing_treatment_1_primary_barrier", receipt["hard_gate_errors"])

    def test_invalid_counts_reject(self):
        specification = manifest()
        for invalid in (None, -1, True, "0"):
            with self.subTest(invalid=invalid):
                value = packet(specification)
                value["treatment"][0]["barriers"]["wrong_route"] = invalid
                receipt = evaluate(specification, value)
                self.assertIn("invalid_treatment_0_primary_barrier",
                              receipt["hard_gate_errors"])


if __name__ == "__main__":
    unittest.main()
