import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/experiments/fresh-delivery-decisions"
spec = importlib.util.spec_from_file_location("guidance_drive", HERE / "guidance-drive.py")
drive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive)


class CandidateGuidanceTests(unittest.TestCase):
    def test_only_digest_recovery_guidance_changes(self):
        observed = drive.drive()["arms"]
        for arm in ("baseline", "treatment"):
            cases = observed[arm]["observations"]
            self.assertEqual(cases["A"]["output"]["invalid"]["field"], "candidate.missing_required_paths")
            self.assertEqual(cases["B"]["output"]["invalid"]["field"], "candidate.instruction.treatment_sha256")
            self.assertEqual(cases["C"]["output"]["classification"], "VERIFIED")
        self.assertEqual(observed["baseline"]["observations"]["B"]["output"]["next"]["required"], ["execution_envelope"])
        self.assertEqual(observed["treatment"]["observations"]["B"]["output"]["next"], {
            "kind": "input", "owner": "Soodles Issue admission",
            "required": ["candidate_instruction_matches_frozen_evidence"]})
        archived = json.loads((HERE / "inputs/guidance.json").read_text())["arms"]
        for arm in ("baseline", "treatment"):
            self.assertEqual(observed[arm]["input"], archived[arm]["input"])
            self.assertEqual(observed[arm]["module_sha256"], archived[arm]["module_sha256"])

    def test_actual_admission_still_requires_its_envelope(self):
        import issue_admission
        refusal = issue_admission.AdmissionRefusal("envelope", None)
        self.assertEqual(refusal.next["required"], ["execution_envelope"])

    def test_followup_raw_binding_and_frozen_replay(self):
        spec = importlib.util.spec_from_file_location("original_observer", HERE / "observer.py")
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
        responses = json.loads((HERE / "raw/guidance-responses.json").read_text())
        reads = json.loads((HERE / "raw/guidance-reads.json").read_text())
        launches = json.loads((HERE / "raw/guidance-launches.json").read_text())
        self.assertEqual(set(responses), {"X1", "X2", "Y1", "Y2", "Z1"})
        self.assertEqual(set(responses), set(reads))
        self.assertEqual(set(responses), set(launches))
        for run, response in responses.items():
            label = "D" if run == "Z1" else run[0]
            case = json.loads((HERE / ("inputs/" + label + ".json")).read_text())
            self.assertEqual(observer.evaluate(case, response["raw_final"]), response["observer_result"])
            record = reads[run]
            stdout = (HERE / record["stdout_path"]).read_bytes()
            self.assertEqual(stdout, b"".join((HERE / path).read_bytes() for path in (
                "task.md", "inputs/context.json", "inputs/" + label + ".json")))
            self.assertEqual(hashlib.sha256(stdout).hexdigest(), record["result"]["stdout_sha256"])
            self.assertEqual(record["result"]["exit_code"], 0)
            self.assertFalse(record["result"]["timed_out"])
            self.assertEqual(launches[run]["fork_turns"], "none")


if __name__ == "__main__":
    unittest.main()
