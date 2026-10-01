"""The shared test entry must not turn partial execution into success."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import soodles
import test_manager

ROOT = Path(soodles.__file__).resolve().parent


class TestSuiteTests(unittest.TestCase):
    def run_fixture(self, files):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / 'tests').mkdir()
            for name, source in files.items():
                (root / 'tests' / name).write_text(source)
            code = ('import sys,json;sys.path.insert(0,sys.argv[1]);import test_manager;'
                    'p=test_manager.select(sys.argv[2],[],full=True);'
                    'print(json.dumps(test_manager.execute_units(sys.argv[2],p)))')
            return subprocess.run([sys.executable, '-B', '-c', code, str(ROOT), str(root)],
                                  cwd=root, env=soodles.clean_env(), capture_output=True,
                                  text=True, timeout=15)

    def test_all_discovered_modules_run_in_separate_processes(self):
        source = ('import os,unittest\nclass Control(unittest.TestCase):\n'
                  ' def test_ok(self): print("worker_pid="+str(os.getpid()))\n')
        process = self.run_fixture({'test_one.py': source, 'test_two.py': source})
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual((result['exit'], result['count']), (0, 2))
        pids = [line for line in result['output'].splitlines() if line.startswith('worker_pid=')]
        self.assertEqual(len(set(pids)), 2)

    def test_failed_skipped_and_early_exit_cannot_pass(self):
        for body in ('self.fail("planted failure")', 'self.skipTest("planted skip")',
                     'raise SystemExit(0)'):
            with self.subTest(body=body):
                process = self.run_fixture({'test_control.py':
                    'import unittest\nclass Control(unittest.TestCase):\n def test_control(self): ' + body + '\n'})
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(json.loads(process.stdout)['exit'], 1)
        # A process can terminate successfully without completing any test.
        process = self.run_fixture({'test_control.py':
            'import os,unittest\nclass Control(unittest.TestCase):\n def test_control(self): os._exit(0)\n'})
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result['exit'], 1)
        self.assertIn('did not match discovery', result['output'])

    def test_empty_suite_and_import_failure_refuse(self):
        for files in ({}, {'test_broken.py': 'raise RuntimeError("planted import failure")\n'}):
            with self.subTest(files=files):
                process = self.run_fixture(files)
                self.assertNotEqual(process.returncode, 0)
                self.assertTrue('test discovery' in process.stderr or 'discovery found no tests' in process.stderr)

    def test_repair_inputs_use_existing_boundary_scope(self):
        decision = test_manager.select(ROOT, ["atom_repair.py", "policy/repair-policy.json",
            "system_context.py", "contracts/system-v1/routes.json",
            "docs/experiments/bounded-repair/product-results.json"])
        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "focused")
        self.assertEqual(decision["physical"], [])
        self.assertIn("test_atom_repair", decision["modules"])
        self.assertIn("test_lifecycle_activation", decision["modules"])

    def test_unknown_scope_never_falls_back_to_full_or_executes(self):
        decision = test_manager.select(ROOT, ["new_owner.py", "tests/test_removed.py"])
        self.assertEqual(decision["status"], "needs_scope")
        self.assertNotEqual(decision["mode"], "full")
        with patch.object(test_manager, "_run_suite") as execute:
            with self.assertRaisesRegex(ValueError, "needs scope"):
                test_manager.execute_units(ROOT, decision)
            execute.assert_not_called()

    def test_explicit_coverage_is_distinct_from_missing_base(self):
        with self.assertRaisesRegex(ValueError, "no full fallback"):
            test_manager.plan(ROOT, require_base=True)
        full = test_manager.select(ROOT, [], full=True, reason="Requested complete regression")
        self.assertEqual((full["status"], full["mode"]), ("ready", "full"))
        focused = test_manager.select(ROOT, ["new_owner.py"], modules=["test_test_suite"],
                                      reason="The new owner routes this runner")
        self.assertEqual(focused["modules"], ["test_test_suite"])
        self.assertEqual(focused["mode"], "focused")
        self.assertEqual(focused["unresolved"], [])
