"""Replay fixed correction evidence; no models, provider writes or landing authority."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from test_local_routing_evidence import safe_unpack, relative

BASE = Path(__file__).resolve().parents[1] / 'docs/experiments/authorization-reentry/correction'
PINS = {'tools/archive_case.py': 'da3287c77f10c92c3800f30aede69e9148636050a8f83a2c4ce3cfe41ff863ac', 'tools/replay_archive.py': '8cb481b301ccb903de82a87a7dc0085be871021a96fd544905ac4351c2c70268', 'evaluator/check.py': 'a8f7866c61c8364388f27c5c1f3beb4c15173d25d8256cf58bfdcc2af3afc978', 'evaluator/capture_decoder.py': '701ada7eb3f22b4a7639df423573f1fb298c12620e8ff8ec1f8f56b04d38f8fd', 'evaluator/analysis.py': 'f4b824366c608c88354bee018d0c95d3dfb71ffa097ad7dfdfbcb9517e37fb73'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class CorrectionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.index = json.loads((BASE / 'evidence-index.json').read_text())
        self.assertEqual(self.index['tools'], PINS)
        for name, expected in PINS.items():
            self.assertEqual(sha(BASE / name), expected)

    def test_captures_replay_including_failures_and_tampering_refuses(self):
        self.assertEqual(len(self.index['runs']), 30)
        self.assertEqual(len({r['id'] for r in self.index['runs']}), 30)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for n, row in enumerate(self.index['runs']):
                with self.subTest(run=row['id']):
                    archive = BASE / relative(row['archive'])
                    self.assertEqual(sha(archive), row['archive_sha256'])
                    target = root / str(n); target.mkdir(); safe_unpack(archive, target)
                    argv = [sys.executable, '-B', str(BASE / 'tools/replay_archive.py'), str(target),
                            row['inventory_sha256'], str(BASE / 'evaluator/check.py'), str(root / f'{n}-result')]
                    result = subprocess.run(argv, capture_output=True, text=True, timeout=70)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    if n == 0:
                        (target / 'run/raw/stdout.bin').write_bytes(b'tampered')
                        argv[-1] = str(root / 'tampered')
                        result = subprocess.run(argv, capture_output=True, text=True, timeout=20)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertFalse(Path(argv[-1]).exists())

    def test_decisions_replay_and_efficiency_remains_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); results = {}
            for row in self.index['runs']:
                archive = BASE / relative(row['archive'])
                self.assertEqual(sha(archive), row['archive_sha256'])
                with tarfile.open(archive, 'r:gz') as tar:
                    raw = tar.extractfile('result.json').read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['result_sha256'])
                path = root / (row['id'] + '.json'); path.write_bytes(raw)
                results[row['id']] = {'path': str(path), 'sha256': sha(path)}
            for name, row in self.index['comparisons'].items():
                manifest = {arm: [results[i] for i in ids] for arm, ids in row['membership'].items()}
                path = root / (name + '-manifest.json'); path.write_text(json.dumps(manifest))
                result = subprocess.run([sys.executable, '-B', str(BASE / 'evaluator/analysis.py'), str(path), sha(path)], capture_output=True, text=True, timeout=20)
                expected = json.loads((BASE / relative(row['decision'])).read_text())
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertFalse(expected['authorizes_landing'])
            rejected = json.loads((BASE / 'r02-decision.json').read_text())
            self.assertFalse(rejected['adopt'])
            self.assertEqual(rejected['cost_improvement']['relative_reduction'], 0)

    def test_actual_parent_handoff_capture_is_sealed(self):
        row = self.index['downstream']; archive = BASE / relative(row['archive'])
        self.assertEqual(sha(archive), row['archive_sha256'])
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve(); safe_unpack(archive, target)
            self.assertEqual(sha(target / 'inventory.json'), row['inventory_sha256'])
            expected = json.loads((target / 'inventory.json').read_text())
            actual = {str(p.relative_to(target)): {'sha256': sha(p), 'bytes': p.stat().st_size}
                      for p in target.rglob('*') if p.is_file() and p.name != 'inventory.json'}
            self.assertEqual(actual, expected['files'])
            result = json.loads((target / 'result.json').read_text())
            self.assertTrue(result['pass']); self.assertTrue(all(result['checks'].values()))
            self.assertEqual(sha(target / 'result.json'), row['result_sha256'])
            context = json.loads((target / 'parent-context.json').read_text())
            self.assertEqual(sha(target / 'run/output/workspace/handoff/prepared.json'), context['receipt_sha256'])
            self.assertEqual(sha(target / 'parent/work-output/raw-cli-receipt.json'), context['receipt_sha256'])
