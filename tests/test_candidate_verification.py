import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import issue_admission as admission


ROOT = Path(admission.__file__).resolve().parent
EVIDENCE = ROOT / "docs/experiments/exact-head-candidate-binding"


class CandidateVerificationTests(unittest.TestCase):
    def test_frozen_exact_head_observer_replays_treatment(self):
        observer = EVIDENCE / "observer.py"
        self.assertEqual(
            hashlib.sha256(observer.read_bytes()).hexdigest(),
            "0e22cb83764980a41a10a638e06139c82070df5e2e49b6007a9a57410e831511")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT)
        result = subprocess.run(
            [sys.executable, str(observer), str(ROOT / "issue_admission.py"),
             "91", "treatment"],
            cwd=ROOT, env=environment, capture_output=True, text=True,
            timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            json.loads((EVIDENCE / "raw/treatment.json").read_text()))

    def test_pr_90_committed_evidence_preserves_historical_baseline_mismatch(self):
        base = "de7b07b99e7879d54fda99e8166cc2aa782e04cc"
        head = "448ff50b8e399c55c51b8b1afe7d481aa463d3a4"
        prompt = ".agents/skills/verify-soodles/features/pclass-context.md"
        prefix = "docs/experiments/pclass-atom-binding/"
        required = [
            prompt,
            prefix + "task.md",
            prefix + "observer.py",
            prefix + "raw/baseline.json",
            prefix + "raw/treatment.json",
            prefix + "raw/noncase.json",
            prefix + "manifest.json",
            prefix + "results.md",
        ]
        write_paths = required + [
            ".github/ISSUE_TEMPLATE/execution.yml",
            "issue_admission.py",
            "tests/test_issue_admission.py",
        ]
        binding = {
            "issue": 89,
            "base_head": base,
            "write_paths": sorted(write_paths),
            "contract": {
                "schema": 2,
                "required_paths": sorted(required),
                "evidence_manifest": prefix + "manifest.json",
            },
        }
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            admission.validate_delivery_paths(ROOT, base, head, binding)
        self.assertEqual(caught.exception.invalid["field"],
                         "candidate.instruction.baseline_sha256")
        manifest_bytes = admission.git_bytes(
            ROOT, head, prefix + "manifest.json")
        self.assertEqual(
            hashlib.sha256(manifest_bytes).hexdigest(),
            "1dfa4370d483017fc51cd636010f863846d286c62d8209dbc002e5ac9ccae5c5")
        manifest = json.loads(manifest_bytes)
        instruction = manifest["instructions"][0]
        self.assertEqual(
            hashlib.sha256(admission.git_bytes(ROOT, head, prompt)).hexdigest(),
            instruction["treatment_sha256"])
        self.assertNotEqual(
            hashlib.sha256(admission.git_bytes(ROOT, base, prompt)).hexdigest(),
            instruction["baseline_sha256"])
        for artifact in manifest["artifacts"]:
            self.assertEqual(
                hashlib.sha256(admission.git_bytes(
                    ROOT, head, artifact["path"])).hexdigest(),
                artifact["sha256"])

    def test_baseline_preserves_the_two_preexisting_admissions(self):
        baseline = json.loads((EVIDENCE / "raw/baseline.json").read_text())
        self.assertEqual(baseline["classification"], "RED")
        self.assertEqual(
            [(item["case"], item["outcome"]) for item in baseline["records"]],
            [("prompt_mismatch", "accepted"),
             ("frozen_observer_mismatch", "accepted"),
             ("complete", "accepted")])


if __name__ == "__main__":
    unittest.main()
