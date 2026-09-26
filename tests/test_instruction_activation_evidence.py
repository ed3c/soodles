"""Replay the independently frozen activation controls and bounded consumer record."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(os.environ.get("SOODLES_TEST_SUBJECT_ROOT", Path(__file__).resolve().parents[1])).resolve()
EVIDENCE = ROOT / "docs/experiments/instruction-activation"


# Source-byte comparison retained separately from the closed delivery manifest schema.
EXECUTABLE_READMISSION = {'historical_head': 'fa3667645e38326a68f551a33a3b98c53d794840',
 'base_head': '3d8f6490994cefa7d092d427c5f73be12824b3fe',
 'files': [{'path': 'issue_admission.py',
            'historical_sha256': '1b7d6891d2d7a7958a09a77e072c6b523ee029c4ad4d44aa5ba3f991927fa728',
            'candidate_sha256': '6bb652a9c1b41f9ad68b83fbf589bcf2a668b80eca6944752497c152798889fa',
            'unchanged': False},
           {'path': 'issue_atom.py',
            'historical_sha256': '362be3efb0fd16e80383c56046a8c63bdbccdeea0db968a862abce9e2ce36d37',
            'candidate_sha256': 'fc709be6efbb3b252c91000bdfd4f4f495646ca2b05b969474cc7a798748b214',
            'unchanged': False},
           {'path': 'issue_execution.py',
            'historical_sha256': 'd4c66cd582c454e9b997b8ff95cf87278d5a841ba49c88899cf6b3b4ff77d12c',
            'candidate_sha256': 'd4c66cd582c454e9b997b8ff95cf87278d5a841ba49c88899cf6b3b4ff77d12c',
            'unchanged': True},
           {'path': 'supervisor_admission.py',
            'historical_sha256': '11aeda62d621074c22b2876b55be053ee52551f19f861a50dad841356e0d1937',
            'candidate_sha256': '4b28dae7e49af10eced199441c274dff2825a9bb1819dd9dd347d763b03b559a',
            'unchanged': False}],
 'scope': 'Historical oracle receipt is unchanged; replay uses current source with preserved bootstrap, '
          'backlog-isolation and root-scoped order changes.',
 'authorizes_landing': False}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class InstructionActivationEvidenceTests(unittest.TestCase):
    def test_complete_exact_manifest_and_selected_instructions(self):
        manifest = json.loads((EVIDENCE / "manifest.json").read_text())
        self.assertEqual(set(manifest), {"schema", "issue", "instructions", "artifacts",
                                         "owner", "authorizes_landing"})
        selection = json.loads((EVIDENCE / "frozen-selection.json").read_text())
        self.assertEqual(manifest["issue"], {"repository": "ed3c/soodles", "number": 156})
        overlay = json.loads((EVIDENCE / "readmission-selection.json").read_text())
        self.assertEqual(digest(EVIDENCE / "frozen-selection.json"),
                         "e827c0cc4a429c2c1749364461a82bf1d30fece1c21ed7698bd07fbb0c64d88c")
        self.assertEqual(digest(EVIDENCE / "readmission-selection.json"),
                         "f6b8fc2bc1327a71b754c8ac71e11af5de0242df7d1ac22ac64ba4558ee5448b")
        self.assertEqual(overlay["historical_selection_sha256"], digest(EVIDENCE / "frozen-selection.json"))
        self.assertEqual(overlay["base_head"], "3d8f6490994cefa7d092d427c5f73be12824b3fe")
        self.assertEqual(manifest["instructions"], overlay["instructions"])
        for entry in overlay["instructions"]:
            self.assertEqual(digest(ROOT / entry["path"]), entry["treatment_sha256"])
            baseline = subprocess.check_output(
                ["git", "show", overlay["base_head"] + ":" + entry["path"]], cwd=ROOT)
            self.assertEqual(hashlib.sha256(baseline).hexdigest(), entry["baseline_sha256"])
        self.assertFalse(manifest["authorizes_landing"])
        self.assertEqual(manifest["owner"]["tool"], "issue_admission.validate_delivery_paths")
        for entry in selection["files"]:
            self.assertEqual(digest(EVIDENCE / "frozen" / entry["path"]), entry["sha256"])
        for entry in selection["instructions"]:
            self.assertEqual(digest(EVIDENCE / "frozen/baseline" / entry["path"]), entry["baseline_sha256"])
            self.assertEqual(digest(EVIDENCE / "frozen/treatment" / entry["path"]), entry["treatment_sha256"])
        expected = set()
        for entry in manifest["artifacts"]:
            path = entry["path"]
            self.assertNotIn(path, expected)
            self.assertTrue(path.startswith("docs/experiments/instruction-activation/"))
            self.assertEqual(digest(ROOT / path), entry["sha256"])
            expected.add(path)
        present = {str(path.relative_to(ROOT)) for path in EVIDENCE.rglob("*") if path.is_file()}
        self.assertEqual(expected | {"docs/experiments/instruction-activation/manifest.json"}, present)

    def test_frozen_oracle_replays_against_current_executable(self):
        captured = json.loads((EVIDENCE / "raw/treatment-controls.json").read_text())
        readmission = EXECUTABLE_READMISSION
        self.assertEqual(readmission["historical_head"], captured["subject_head"])
        self.assertFalse(readmission["authorizes_landing"])
        self.assertEqual({entry["path"] for entry in readmission["files"]},
                         {"issue_admission.py", "issue_atom.py", "issue_execution.py",
                          "supervisor_admission.py"})
        for entry in readmission["files"]:
            self.assertEqual(digest(ROOT / entry["path"]), entry["candidate_sha256"])
            self.assertEqual(entry["unchanged"],
                             entry["historical_sha256"] == entry["candidate_sha256"])
        oracle = EVIDENCE / "frozen/oracle.py"
        self.assertEqual(captured["oracle_sha256"], digest(oracle))
        with tempfile.TemporaryDirectory(prefix="instruction-activation-oracle-") as directory:
            run = subprocess.run([sys.executable, "-B", str(oracle), str(ROOT), directory],
                                 cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            current = json.loads((Path(directory) / "controls.json").read_text())
        self.assertEqual([x["case"] for x in current["cases"]],
                         [x["case"] for x in captured["cases"]])
        self.assertEqual(len(current["cases"]), 16)
        self.assertTrue(all(x["verdict"] == "PASS" for x in current["cases"]), current["cases"])
        self.assertFalse(current["authorizes_landing"])
        self.assertEqual(current["network"], "fixture-only; no provider transport")

    def test_frozen_observer_and_planted_bad_result(self):
        captured = json.loads((EVIDENCE / "raw/consumer-comparison.json").read_text())
        self.assertEqual(captured["behavior"], "PASS")
        self.assertEqual(captured["context_acquisition_delta"], -1)
        self.assertEqual(captured["planted_bad_result"], "rejected")
        observer = EVIDENCE / "frozen/consumer-observer.py"
        def invoke(root):
            run = subprocess.run([sys.executable, "-B", str(observer), str(root)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            return json.loads(run.stdout)
        actual = invoke(EVIDENCE / "raw")
        for key in ("behavior", "context_acquisition_delta", "supported_claim", "planted_bad_result"):
            self.assertEqual(actual[key], captured[key])
        self.assertEqual({arm: actual["results"][arm]["recipe_reads"] for arm in ("sample-a", "sample-b")},
                         {"sample-a": 1, "sample-b": 0})
        with tempfile.TemporaryDirectory(prefix="instruction-activation-control-") as directory:
            fixture = Path(directory)
            shutil.copytree(EVIDENCE / "raw/sample-a", fixture / "sample-a")
            shutil.copytree(EVIDENCE / "raw/sample-b", fixture / "sample-b")
            shutil.copytree(EVIDENCE / "raw/observations", fixture / "observations")
            bad = fixture / "sample-b/result.json"
            value = json.loads(bad.read_text())
            value["behavior"] = "PASS"
            bad.write_text(json.dumps(value))
            rejected = invoke(fixture)
        self.assertEqual(rejected["behavior"], "FAIL")
        self.assertFalse(rejected["results"]["sample-b"]["behavior_pass"])


if __name__ == "__main__":
    unittest.main()
