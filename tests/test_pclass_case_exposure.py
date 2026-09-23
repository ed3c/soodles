"""Case-exposure controls. Fixture traces are not fresh Agent observations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/verify-soodles/scripts"
DECIDER = SCRIPTS / "decide_pclass.py"
REPLAYER = SCRIPTS / "replay_pclass.py"
OBSERVER = SCRIPTS / "observe_pclass.py"
PROBE = ROOT / "docs/experiments/pclass-case-exposure/probe.py"
spec = importlib.util.spec_from_file_location("case_exposure_probe", PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def fixture_run(arm, index, case):
    """Synthetic state projections for the real replayer and observer controls."""
    run_id = f"{arm}-{index}"
    initial = {"next": {"operation": "advance"}}
    if case == "recovery":
        events = [{"owner": "landing.advance", "status": "refused",
                   "invalid": {"field": "merge_commit"},
                   "next": {"operation": "advance"}}]
        completion = {"owner": "landing.advance", "phase": "close_pending",
                      "action": "dispatch", "next": {"operation": "dispatch"}}
    else:
        events = []
        completion = {"owner": "landing.advance", "action": "readback",
                      "next": {"operation": "dispatch"}}
    events.append(completion)
    instruction = {"path": "/fixture/AGENTS.md", "bytes": 0,
                   "sha256": hashlib.sha256(b"").hexdigest()}
    packet = {"run_id": run_id, "case": case, "instruction": instruction,
              "initial_owner_projection": initial,
              "expected_owner_projection_sha256": probe.fingerprint(initial),
              "connector_transport_authorized": False, "transport_events": []}
    if arm == "baseline":
        events.append({"owner": "landing.dispatch", "next": None,
                       "request": {"fixture": "not executed"}})
    else:
        packet.update(completion_owner_projection=completion,
                      expected_completion_owner_projection_sha256=probe.fingerprint(completion),
                      stop_when_completion_projection_observed=True)
    return {"run_id": run_id, "arm": arm, "packet": packet,
            "precondition": {"run_id": run_id, "case": case,
                "initial_owner_projection": initial,
                "initial_owner_projection_sha256": probe.fingerprint(initial),
                "completion_owner_projection": completion,
                "completion_owner_projection_sha256": probe.fingerprint(completion),
                "provider_transport_observed": False, "transport_events": []},
            "owner_events": events, "instruction_observations": [instruction],
            "consumer": {"run_id": run_id, "authorizes_landing": False},
            "remaining_disposable_paths": []}


def replay_fixture(baseline_cases, treatment_cases):
    runs = [fixture_run(arm, i, case)
            for arm, cases in (("baseline", baseline_cases), ("treatment", treatment_cases))
            for i, case in enumerate(cases)]
    gates = {"schema": 1, "experiment_id": "case-exposure-cli-fixture",
             "causal_delta": {"classification": "PASS"},
             "independent_audit": {"classification": "PASS"},
             "telemetry": {"scope": "synthetic_fixture_not_agent_evidence"}}
    manifest = {"schema": 2, "experiment_id": gates["experiment_id"],
        "admission_target": "improvement", "primary_barrier": "post_completion_owner_request",
        "runs_per_arm": len(baseline_cases), "gates_sha256": probe.fingerprint(gates),
        "required_controls": ["legal_completion"],
        "control_specs": [{"name": "legal_completion", "source_run_id": "treatment-0",
            "mutation": "none", "expected_hard_gate": "PASS", "expected_errors": [],
            "expected_barrier": 0}],
        "runs": [{"run_id": r["run_id"], "arm": r["arm"], "case": r["packet"]["case"],
                  "evidence_sha256": probe.fingerprint(r)} for r in runs]}
    for name, path in (("observer", OBSERVER), ("normalizer", REPLAYER), ("decider", DECIDER)):
        manifest[name + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"runs": runs}, gates, manifest


class CaseExposureTests(unittest.TestCase):
    def test_frozen_nine_case_probe(self):
        result = probe.run(DECIDER)
        self.assertEqual(result["probe_sha256"],
                         "ebae7abe11fa4ccf009de1e75537fa0148e8b0945febd2c77b6d26eacf069581")
        self.assertEqual(result["passed"], result["total"],
                         [(r["case"], r["observed"]) for r in result["cases"] if not r["pass"]])
        for row in result["cases"]:
            if row["case"] in {"different_case_sets", "different_case_counts", "unmatched_nonregression"}:
                self.assertIn("manifest_case_exposure_mismatch", row["receipt"]["hard_gate_errors"])

    def test_real_public_replay_entry(self):
        baseline = ["pending", "recovery", "recovery"]
        for treatment, expected in ((["recovery", "pending", "recovery"], "ADMIT_IMPROVEMENT"),
                                    (["pending", "pending", "recovery"], "REJECT")):
            with self.subTest(treatment=treatment), tempfile.TemporaryDirectory() as directory:
                raw, gates, manifest = replay_fixture(baseline, treatment)
                paths = [Path(directory) / name for name in ("raw.json", "gates.json", "manifest.json")]
                for path, value in zip(paths, (raw, gates, manifest)):
                    path.write_text(json.dumps(value))
                process = subprocess.run(
                    [sys.executable, "-B", str(REPLAYER), *map(str, paths),
                     probe.fingerprint(manifest), str(OBSERVER), str(DECIDER)],
                    capture_output=True, text=True, timeout=30, check=False)
                receipt = json.loads(process.stdout)
                self.assertEqual(receipt["decision"]["decision"], expected, receipt)
                self.assertEqual(process.returncode, 0 if expected.startswith("ADMIT_") else 1)
                self.assertFalse(receipt["authorizes_landing"])
                # Both cases must first pass the existing trace-level discriminator.
                self.assertTrue(all(r["hard_gate"] == "PASS"
                                    for arm in ("baseline", "treatment") for r in receipt[arm]))
                if expected == "REJECT":
                    self.assertIn("manifest_case_exposure_mismatch",
                                  receipt["decision"]["hard_gate_errors"])


if __name__ == "__main__":
    unittest.main()
