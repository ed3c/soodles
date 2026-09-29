"""Replay the externally fixed claim-transition oracle on the current source."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ClaimRefusalEvidenceTests(unittest.TestCase):
    def test_frozen_oracle_preserves_refusal_wait_and_resume(self):
        source = Path(__file__).resolve().parents[1]
        oracle = source / "docs/experiments/claim-refusal-closure/evaluator"
        manifest = oracle / "manifest.json"
        self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(),
                         "22f3b5cd7fb458a29f21c0281f52211974cda769f0e9f2ca8e1d4f5c39bf0ba7")
        for name, expected in json.loads(manifest.read_text())["files"].items():
            self.assertEqual(hashlib.sha256((oracle / name).read_bytes()).hexdigest(), expected, name)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence"
            result = subprocess.run([sys.executable, "-B", str(oracle / "evaluate.py"),
                                     str(source), str(output)], capture_output=True,
                                    text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads((output / "summary.json").read_text())
            self.assertEqual(receipt["decision"], "PASS")
            self.assertFalse(receipt["authorizes_landing"])
