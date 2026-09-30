"""Preserve archived oracle integrity and verify current preparation controls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / 'docs/experiments/authorization-materialization'
ORACLE_MANIFEST = '78867edb4b02eb786996a6f5242c836e15eeae1e122e59b9e59d8e708c8c0c6c'


class AuthorizationEvidenceTests(unittest.TestCase):
    def test_archived_oracle_integrity_and_current_preparation_contract(self):
        oracle = EXPERIMENT / 'evaluator'
        manifest_bytes = (oracle / 'manifest.json').read_bytes()
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), ORACLE_MANIFEST)
        manifest = json.loads(manifest_bytes)
        for name, digest in manifest['files'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((oracle / name).read_bytes()).hexdigest(), digest)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary).resolve() / 'replay'
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/authorization_prepare_controls.py'), str(ROOT), str(output)],
                                 capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads((output / 'result.json').read_text())
            self.assertEqual(result['status'], 'GREEN')
            self.assertEqual(len(result['results']), 28)
            self.assertFalse(result['authorizes_landing'])


if __name__ == '__main__':
    unittest.main()
