import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / '.agents/skills/verify-soodles/scripts/record_context.py'
spec = importlib.util.spec_from_file_location('context_recording', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContextRecordingTests(unittest.TestCase):
    def test_records_real_nonzero_and_file_change_without_inventing_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state'
            path.write_text('before')
            result, stdout, _ = module.record(tmp, 'drive', [sys.executable, '-c',
                'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("after");print("observed");sys.exit(3)', str(path)])
            self.assertEqual(result['exit_code'], 3)
            self.assertEqual(stdout, b'observed\n')
            import json
            before = json.loads((Path(tmp)/'drive/request.json').read_text())['files_before']
            self.assertNotEqual(before[str(path)]['sha256'], result['files_after'][str(path)]['sha256'])
            self.assertFalse(result['authorizes_landing'])

    def test_duplicate_label_refuses_before_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sentinel'
            module.record(tmp, 'once', [sys.executable, '-c', 'pass'])
            with self.assertRaises(FileExistsError):
                module.record(tmp, 'once', [sys.executable, '-c',
                    'import pathlib,sys;pathlib.Path(sys.argv[1]).touch()', str(path)])
            self.assertFalse(path.exists())

    def test_timeout_retains_output_and_waits_for_killed_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, stdout, _ = module.record(tmp, 'timeout', [sys.executable, '-u', '-c',
                'import time;print("started");time.sleep(30)'], timeout=0.2)
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['exit_code'], -9)
            self.assertEqual(stdout, b'started\n')

    def test_missing_executable_is_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, _, _ = module.record(tmp, 'missing', [str(Path(tmp)/'absent')])
            self.assertIsNone(result['exit_code'])
            self.assertIsNotNone(result['error'])

    def test_long_non_path_argument_does_not_lose_command_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, stdout, _ = module.record(tmp, 'long', [sys.executable, '-c',
                'print("' + 'x' * 300 + '")'])
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(stdout, b'x' * 300 + b'\n')
            self.assertTrue((Path(tmp)/'long/result.json').is_file())

    def test_snapshot_error_after_effect_preserves_result(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'state'
            path.write_text('before')
            original = Path.read_bytes
            def read_bytes(p):
                if p == path and p.read_text() == 'after':
                    raise PermissionError('injected snapshot failure')
                return original(p)
            with patch.object(Path, 'read_bytes', read_bytes):
                result, _, _ = module.record(tmp, 'changed', [sys.executable, '-c',
                    'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("after")', str(path)])
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['files_after'][str(path)]['snapshot_error'], 'PermissionError')
            self.assertTrue((Path(tmp)/'changed/result.json').is_file())
