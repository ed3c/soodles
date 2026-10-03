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
        timings = [json.loads(line) for line in result['output'].splitlines()
                   if line.startswith('{"event": "soodles.timing"')]
        self.assertEqual({item['test'] for item in timings if item['operation'] == 'test.case'},
                         {'test_one.Control.test_ok', 'test_two.Control.test_ok'})

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

    def test_new_candidate_manifest_uses_existing_control_without_full_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'tests').mkdir()
            (root / 'tests/test_candidate_verification.py').write_text('')
            (root / 'docs').mkdir()
            path = root / 'docs/new-candidate.json'
            manifest = {'schema': 1, 'issue': {'repository': 'ed3c/soodles', 'number': 225},
                        'instructions': [], 'artifacts': [],
                        'owner': {'tool': 'issue_admission.validate_delivery_paths'},
                        'authorizes_landing': False}
            path.write_text(json.dumps(manifest))
            decision = test_manager.select(root, ['docs/new-candidate.json'])
            self.assertEqual(decision['status'], 'ready')
            self.assertEqual(decision['mode'], 'focused')
            self.assertEqual(decision['modules'], ['test_candidate_verification'])
            self.assertEqual(decision['physical'], [])
            self.assertFalse(decision['authorizes_landing'])
            for body in ('{}', '{invalid', json.dumps({**manifest, 'authorizes_landing': True})):
                path.write_text(body)
                self.assertEqual(test_manager.select(root, ['docs/new-candidate.json'])['status'],
                                 'needs_scope')

    def test_admission_names_missing_scope_consumer_before_freezing_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'tests').mkdir()
            (root / 'tests/test_candidate_verification.py').write_text('')
            contract = {'write_paths': ['new_boundary.py', 'docs/new-evidence.json'],
                        'required_paths': ['new_boundary.py', 'docs/new-evidence.json'],
                        'evidence_manifest': 'docs/new-evidence.json'}
            decision = test_manager.admission_scope(root, contract)
            self.assertEqual(decision['required_write_paths'], ['test_manager.py'])
            self.assertEqual(decision['unresolved'], [
                {'path': 'new_boundary.py', 'reason': 'trace the changed behavior and name its controls'}])
            self.assertEqual(decision['modules'], ['test_candidate_verification'])
            self.assertEqual(decision['physical'], [])
            contract['write_paths'].append('test_manager.py')
            self.assertEqual(test_manager.admission_scope(root, contract)['required_write_paths'], [])
            contract['required_paths'] = ['docs/new-evidence.json']
            self.assertEqual(test_manager.admission_scope(root, contract)['status'], 'ready')
            contract['write_paths'] = ['docs/new-evidence.json', 'tests/test_new_behavior.py']
            contract['required_paths'].append('tests/test_new_behavior.py')
            planned = test_manager.admission_scope(root, contract)
            self.assertEqual(planned['status'], 'ready')
            self.assertEqual(planned['required_write_paths'], [])
            self.assertEqual(planned['modules'], ['test_candidate_verification', 'test_new_behavior'])
            self.assertFalse((root / 'tests/test_new_behavior.py').exists())

    def test_repair_inputs_use_existing_boundary_scope(self):
        decision = test_manager.select(ROOT, ["atom_repair.py", "policy/repair-policy.json",
            "system_context.py", "contracts/system-v1/routes.json",
            "docs/experiments/bounded-repair/product-results.json"])
        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "focused")
        self.assertEqual(decision["physical"], [])
        self.assertIn("test_atom_repair", decision["modules"])
        self.assertIn("test_lifecycle_activation", decision["modules"])

    def test_host_field_evidence_uses_existing_owner_controls(self):
        decision = test_manager.select(ROOT, ["docs/experiments/schema-plan-fields/protocol.json",
            "docs/experiments/schema-plan-fields/results.json", "docs/experiments/schema-plan-fields/timing.json"])
        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["modules"], ["test_issue_atom", "test_lifecycle_activation",
                                             "test_schema_manager", "test_system_context"])
        self.assertEqual(decision["physical"], [])

    def test_stage_outcome_selects_external_runtime_consumer(self):
        decision = test_manager.select(ROOT, ["stage_outcome.py"])
        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "focused")
        self.assertEqual(decision["modules"], ["test_admission_revision", "test_feedback_owner",
            "test_generic_repository_binding", "test_pclass_feedback", "test_stage_outcome"])
        self.assertEqual(decision["physical"], [])
        self.assertFalse(decision["authorizes_landing"])

    def test_cost_evidence_uses_affected_controls_without_full_demand(self):
        decision = test_manager.select(ROOT, ["cost_telemetry.py", "docs/loop-cost/evidence.json"])
        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "focused")
        self.assertEqual(decision["physical"], [])
        self.assertIn("test_cost_telemetry", decision["modules"])
        self.assertIn("test_schema_manager", decision["modules"])
        for path in ("schema_manager.py", "issue_atom.py"):
            self.assertIn("test_cost_telemetry", test_manager.select(ROOT, [path])["modules"])

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

    def test_ci_requires_demand_beyond_pr_acceptance(self):
        base = 'a' * 40
        self.assertEqual(test_manager.ci_request('runtime', 'pull_request', base)['base'], base)
        for kind in ('runtime', 'quality'):
            requested = test_manager.ci_request(kind, 'workflow_dispatch', base, 'Inspect changed behavior')
            self.assertEqual(requested['reason'], 'Inspect changed behavior')
            self.assertFalse(requested['authorizes_landing'])
            for event, reason in (('push', 'merged'), ('workflow_dispatch', '  '),
                                  ('workflow_run', 'completed')):
                with self.subTest(kind=kind, event=event), self.assertRaises(ValueError):
                    test_manager.ci_request(kind, event, base, reason)
        with self.assertRaises(ValueError):
            test_manager.ci_request('quality', 'pull_request', base, 'automatic report')
        for base in ('main', '', '0' * 40, None):
            with self.subTest(base=base), self.assertRaises(ValueError):
                test_manager.ci_request('runtime', 'pull_request', base)

    def test_fixture_imports_expand_transitively_without_prose_mentions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / 'tests'
            tests.mkdir()
            files = {
                'test_source.py': 'import test_transitive\n',
                'test_consumer.py': 'def helper():\n from test_source import fixture\n',
                'test_transitive.py': 'import test_consumer as fixture\n',
                'test_dynamic.py': 'fixture = __import__("test_source")\n',
                'test_prose.py': '# test_source\ntext = "test_consumer"\n',
            }
            for name, source in files.items():
                (tests / name).write_text(source)
            decision = test_manager.select(root, ['tests/test_source.py'])
            self.assertEqual(decision['modules'], ['test_consumer', 'test_dynamic',
                                                   'test_source', 'test_transitive'])
            self.assertEqual(decision['status'], 'ready')
            (tests / 'test_dynamic.py').write_text('fixture = __import__(selected_name)\n')
            with self.assertRaisesRegex(ValueError, 'resolve dynamic fixture import'):
                test_manager.select(root, ['tests/test_source.py'])
