"""Frozen deterministic decider probe; synthetic receipts, NOT Agent telemetry."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

CASES = [
    ("matched_improvement", ["pending", "recovery", "recovery"], ["recovery", "pending", "recovery"], "improvement", "ADMIT_IMPROVEMENT"),
    ("matched_nonregression", ["pending", "recovery", "recovery"], ["pending", "recovery", "recovery"], "nonregression", "ADMIT_NONREGRESSION"),
    ("different_case_sets", ["recovery"] * 3, ["pending"] * 3, "improvement", "REJECT"),
    ("different_case_counts", ["pending", "recovery", "recovery"], ["pending", "pending", "recovery"], "improvement", "REJECT"),
    ("unmatched_nonregression", ["recovery"] * 3, ["pending"] * 3, "nonregression", "REJECT"),
    ("missing_case", ["pending", "recovery", "recovery"], [None, "recovery", "recovery"], "improvement", "REJECT"),
    ("failed_required_gate", ["recovery"] * 3, ["recovery"] * 3, "improvement", "REJECT"),
    ("missing_observation", ["recovery"] * 3, ["recovery"] * 3, "improvement", "REJECT"),
    ("zero_to_zero_not_improvement", ["recovery"] * 3, ["recovery"] * 3, "improvement", "REJECT"),
]

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inputs(label, baseline_cases, treatment_cases, target):
    declarations = []
    arms = {"baseline": [], "treatment": []}
    for arm, cases in (("baseline", baseline_cases), ("treatment", treatment_cases)):
        for index, case in enumerate(cases):
            run_id = f"{arm}-{index}"
            declared = {"run_id": run_id, "arm": arm, "case": case,
                        "evidence_sha256": hashlib.sha256(run_id.encode()).hexdigest()}
            declarations.append(declared)
            count = int(arm == "baseline" and target == "improvement" and label != "zero_to_zero_not_improvement")
            arms[arm].append({**declared, "hard_gate": "PASS", "barriers": {"fixture_barrier": count},
                              "observer_sha256": "1" * 64, "normalizer_sha256": "2" * 64,
                              "authorizes_landing": False})
    if label == "failed_required_gate":
        arms["treatment"][0]["hard_gate"] = "FAIL"
    if label == "missing_observation":
        arms["treatment"][0]["barriers"] = {}
    manifest = {"schema": 2, "experiment_id": "case-exposure-regression-control",
                "admission_target": target, "primary_barrier": "fixture_barrier", "runs_per_arm": 3,
                "observer_sha256": "1" * 64, "normalizer_sha256": "2" * 64,
                "decider_sha256": "3" * 64, "gates_sha256": "4" * 64,
                "required_controls": ["fixture_control"], "runs": declarations}
    packet = {"schema": 2, "experiment_id": manifest["experiment_id"],
              "manifest_sha256": fingerprint(manifest), "admission_target": target,
              "primary_barrier": "fixture_barrier", **arms,
              "controls": [{"name": "fixture_control", "expected": "PASS", "observed": "PASS"}],
              "causal_delta": {"classification": "PASS"}, "independent_audit": {"classification": "PASS"},
              "telemetry": {"scope": "synthetic_regression_fixture_not_agent_evidence"}}
    return manifest, packet


def run(path):
    spec = importlib.util.spec_from_file_location("subject_decider", path)
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    results = []
    for label, baseline_cases, treatment_cases, target, expected in CASES:
        manifest, packet = inputs(label, baseline_cases, treatment_cases, target)
        observed = subject.evaluate(copy.deepcopy(packet), copy.deepcopy(manifest), fingerprint(manifest))
        results.append({"case": label, "expected": expected, "observed": observed["decision"],
                        "pass": observed["decision"] == expected, "manifest": manifest,
                        "input": packet, "receipt": observed})
    data = Path(path).read_bytes()
    return {"schema": 1, "scope": "actual_decider_with_synthetic_regression_fixtures",
            "subject_sha256": hashlib.sha256(data).hexdigest(),
            "subject_git_blob": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "passed": sum(item["pass"] for item in results), "total": len(results), "cases": results,
            "fresh_agent_comparison": "NOT_RUN", "authorizes_landing": False}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe.py DECIDER.py")
    print(json.dumps(run(Path(sys.argv[1])), indent=2))
