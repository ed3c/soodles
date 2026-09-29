"""Replay fixed historical evidence. This does not run models or authorize delivery."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from test_local_routing_evidence import safe_unpack, relative

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'docs/experiments/authorization-reentry/evidence-index.json'
PINS = {
    'tools/archive_case.py': 'da3287c77f10c92c3800f30aede69e9148636050a8f83a2c4ce3cfe41ff863ac',
    'tools/replay_archive.py': 'd6fd7f87781f92be00821beef48968fec7b6234976be65f0dd927d84a13cc25f',
    'evaluator/check.py': 'c371b70d81f2cfe3593c1de076a9d15fa65c6c7bb70762c39706580d9794e1d7',
    'evaluator/capture_decoder.py': '701ada7eb3f22b4a7639df423573f1fb298c12620e8ff8ec1f8f56b04d38f8fd',
    'evaluator/analysis.py': 'f4b824366c608c88354bee018d0c95d3dfb71ffa097ad7dfdfbcb9517e37fb73',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PreparationReentryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.index = json.loads(INDEX.read_text())
        self.base = INDEX.parent
        self.assertEqual(self.index['schema'], 1)
        self.assertEqual(self.index['tools'], PINS)
        for path, expected in PINS.items():
            self.assertEqual(sha(self.base / path), expected)

    def test_all_recorded_decisions_replay_and_tampering_refuses(self):
        rows = self.index['runs']
        self.assertEqual(len(rows), 31)
        self.assertEqual(len({r['id'] for r in rows}), len(rows))
        with tempfile.TemporaryDirectory(prefix='preparation-evidence-') as folder:
            temp = Path(folder).resolve()
            for number, row in enumerate(rows):
                with self.subTest(run=row['id']):
                    archive = self.base / relative(row['archive'])
                    self.assertEqual(sha(archive), row['archive_sha256'])
                    extracted = temp / str(number)
                    extracted.mkdir()
                    safe_unpack(archive, extracted)
                    argv = [sys.executable, '-B', str(self.base / 'tools/replay_archive.py'),
                            str(extracted), row['inventory_sha256'], str(self.base / 'evaluator/check.py'),
                            str(temp / (str(number) + '-receipt'))]
                    process = subprocess.run(argv, capture_output=True, text=True, timeout=70)
                    self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                    receipt = json.loads((Path(argv[-1]) / 'receipt.json').read_text())
                    self.assertTrue(receipt['result_json_equal'])
                    self.assertTrue(receipt['archive_integrity_after'])
                    if number == 0:
                        (extracted / 'run/raw/stdout.bin').write_bytes(b'altered capture\n')
                        argv[-1] = str(temp / 'tampered-receipt')
                        bad = subprocess.run(argv, capture_output=True, text=True, timeout=20)
                        self.assertNotEqual(bad.returncode, 0)
                        self.assertFalse(Path(argv[-1]).exists())

    def test_fixed_selection_and_confirmation_decisions(self):
        rows = {r['id']: r for r in self.index['runs']}
        with tempfile.TemporaryDirectory(prefix='preparation-decisions-') as folder:
            temp = Path(folder).resolve()
            results = {}
            for label, row in rows.items():
                archive = self.base / relative(row['archive'])
                self.assertEqual(sha(archive), row['archive_sha256'])
                with tarfile.open(archive, 'r:gz') as tar:
                    data = tar.extractfile('result.json').read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row['result_sha256'])
                path = temp / (label + '.json')
                path.write_bytes(data)
                results[label] = {'path': str(path), 'sha256': sha(path)}
            for name, comparison in self.index['comparisons'].items():
                with self.subTest(comparison=name):
                    manifest = {arm: [results[label] for label in labels]
                                for arm, labels in comparison['membership'].items()}
                    path = temp / (name + '-manifest.json')
                    path.write_text(json.dumps(manifest))
                    process = subprocess.run([sys.executable, '-B', str(self.base / 'evaluator/analysis.py'),
                                              str(path), sha(path)], capture_output=True, text=True, timeout=20)
                    expected = json.loads((self.base / relative(comparison['decision'])).read_text())
                    self.assertEqual(json.loads(process.stdout), expected)
                    self.assertEqual(process.returncode, 0 if expected['adopt'] else 1)
                    self.assertFalse(expected['authorizes_landing'])

    def test_winner_is_exact_second_round_and_no_efficiency_claim(self):
        winner = json.loads((self.base / 'confirmation/winner.json').read_text())
        self.assertEqual(winner['winner'], 'r02')
        self.assertFalse(winner['efficiency_claim'])
        descriptor = json.loads((self.base / 'rounds/r02/product-candidate.json').read_text())
        for path, pin in descriptor['files'].items():
            self.assertEqual(sha(ROOT / relative(path)), pin['sha256'])
        self.assertEqual(json.loads((self.base / 'rounds/r03/decision.json').read_text())['verdict'], 'revert')

if __name__ == '__main__':
    unittest.main()
