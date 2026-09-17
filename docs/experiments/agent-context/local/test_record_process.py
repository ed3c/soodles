"""Real OS subprocess controls; no model sessions or provider writes."""
import json
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


RECORDER = Path(__file__).with_name('record_process.py')


class ProcessControls(unittest.TestCase):
    def run_child(self, root, code):
        return subprocess.run([sys.executable, '-B', str(RECORDER), str(root / 'record'),
                               '--', sys.executable, '-c', code], text=True,
                              capture_output=True, timeout=10,
                              env={**os.environ, 'NOODLE_SESSION_ID': 'control-session',
                                   'NOODLE_ORDER_ID': 'control-order', 'NOODLE_STAGE_INDEX': '0'})

    def test_success_and_nonzero_are_actual_child_exits(self):
        for code in (0, 7):
            with tempfile.TemporaryDirectory() as name:
                root = Path(name)
                result = self.run_child(root, f'import sys;print("child-output");sys.exit({code})')
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(result.stdout, 'child-output\n')
                receipt = json.loads((root / 'record/exit.json').read_text())
                self.assertEqual(receipt['returncode'], code)
                self.assertTrue(receipt['waited'])
                self.assertEqual(receipt['session_id'], 'control-session')
                self.assertEqual(receipt['order_id'], 'control-order')
                self.assertEqual(receipt['stage_index'], '0')
                self.assertNotEqual(receipt['recorder_pid'], receipt['child_pid'])
                self.assertIsNone(receipt['termination_signal'])

    def test_signal_exit_is_not_normalized_to_success(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result = self.run_child(root, 'import os,signal;os.kill(os.getpid(),signal.SIGTERM)')
            self.assertEqual(result.returncode, 128 + signal.SIGTERM, result.stderr)
            receipt = json.loads((root / 'record/exit.json').read_text())
            self.assertEqual(receipt['returncode'], -signal.SIGTERM)
            self.assertEqual(receipt['termination_signal'], signal.SIGTERM)

    def test_wait_boundary_and_parent_signal_forwarding(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); ready = root / 'ready'; record = root / 'record'
            code = f'from pathlib import Path;import time;Path({str(ready)!r}).touch();time.sleep(30)'
            child = subprocess.Popen([sys.executable, '-B', str(RECORDER), str(record),
                                      '--', sys.executable, '-c', code],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not (ready.exists() and (record / 'launch.json').exists()):
                    if child.poll() is not None or time.monotonic() > deadline:
                        self.fail('recorder/child did not reach the wait boundary')
                    time.sleep(.01)
                self.assertFalse((record / 'exit.json').exists())
                child.send_signal(signal.SIGTERM)
                stdout, stderr = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 128 + signal.SIGTERM, stderr)
                receipt = json.loads((record / 'exit.json').read_text())
                self.assertEqual(receipt['returncode'], -signal.SIGTERM)
                self.assertEqual(receipt['forwarded_signals'], [signal.SIGTERM])
                with self.assertRaises(ProcessLookupError):
                    os.kill(receipt['child_pid'], 0)
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.communicate()

    def test_existing_record_is_preserved_without_launch(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); record = root / 'record'; record.mkdir()
            sentinel = record / 'exit.json'; sentinel.write_text('original receipt')
            result = self.run_child(root, 'raise SystemExit(0)')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'original receipt')
            self.assertFalse((record / 'launch.json').exists())

    def test_terminal_delivery_survives_owner_group_kill(self):
        with tempfile.TemporaryDirectory() as name:
            record = Path(name) / 'record'
            first = b'{"type":"turn.started"}\n'
            terminal = b'{"type":"turn.completed"}\n'
            code = ('import sys,time;sys.stdout.buffer.write(' + repr(first + terminal)
                    + ');sys.stdout.flush();time.sleep(.2)')
            parent = subprocess.Popen([sys.executable, '-B', str(RECORDER), str(record),
                                       '--', sys.executable, '-c', code],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      start_new_session=True)
            try:
                self.assertEqual(parent.stdout.readline(), first)
                self.assertFalse((record / 'exit.json').exists())
                self.assertEqual(parent.stdout.readline(), terminal)
                # Reproduce Noodle's terminal-meta repair: kill the whole group
                # immediately when it can observe a completed turn.
                try:
                    os.killpg(parent.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # The group may already have exited naturally.
                parent.communicate(timeout=5)
                receipt = json.loads((record / 'exit.json').read_text())
                self.assertEqual(receipt['returncode'], 0)
                self.assertEqual(receipt['terminal_tail_lines_deferred'], 1)
                self.assertEqual((record / 'stdout.log').read_bytes(), first + terminal)
                self.assertEqual(receipt['stdout_sha256'], hashlib.sha256(first + terminal).hexdigest())
                with self.assertRaises(ProcessLookupError):
                    os.kill(receipt['child_pid'], 0)
            finally:
                if parent.poll() is None:
                    os.killpg(parent.pid, signal.SIGKILL)
                    parent.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
