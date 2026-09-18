import copy
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest

import landing

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/skills/verify-soodles/scripts/record_context.py'
OBSERVER = ROOT / '.agents/skills/verify-soodles/scripts/observe_pclass.py'
spec = importlib.util.spec_from_file_location('context_recording', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
observer_spec = importlib.util.spec_from_file_location('pclass_observer', OBSERVER)
observer = importlib.util.module_from_spec(observer_spec)
observer_spec.loader.exec_module(observer)


class ContextRecordingTests(unittest.TestCase):
    def test_records_real_nonzero_and_file_change_without_inventing_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state'
            path.write_text('before')
            result, stdout, _ = module.record(tmp, 'drive', [sys.executable, '-c',
                'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("after");print("observed");sys.exit(3)', str(path)])
            self.assertEqual(result['exit_code'], 3)
            self.assertEqual(stdout, b'observed\n')
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

    def test_shell_wrapped_instruction_read_and_parse_failure_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            instruction = Path(tmp) / 'AGENTS.md'
            instruction.write_text('route\n')
            evidence = Path(tmp) / 'evidence'
            module.record(evidence, 'shell', ['/bin/sh', '-c',
                'sed -n "1p" ' + shlex.quote(str(instruction))])
            request = json.loads((evidence/'shell/request.json').read_text())
            observed = request['files_before'][str(instruction.resolve())]
            self.assertEqual(observed['observed_from'], ['shell'])
            self.assertEqual(observed['bytes'], len(b'route\n'))
            result, _, _ = module.record(evidence, 'malformed', ['/bin/sh', '-c', "'"])
            malformed = json.loads((evidence/'malformed/request.json').read_text())
            self.assertEqual(malformed['shell_parse_error'], 'ValueError')
            self.assertNotEqual(result['exit_code'], 0)

    def test_three_owner_baselines_and_planted_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instruction = root / 'AGENTS.md'
            instruction.write_text('route\n')
            evidence = root / 'evidence'
            module.record(evidence, 'entry', ['/bin/sh', '-c',
                'cat ' + shlex.quote(str(instruction))])
            requests = [json.loads((evidence/'entry/request.json').read_text())]
            claim, snapshot = self.landing_inputs()

            pending_checkpoint = root / 'pending.json'
            landing.start(claim, snapshot, pending_checkpoint)
            landing.advance(pending_checkpoint, snapshot)
            landing.dispatch(pending_checkpoint, snapshot)
            pending = landing.advance(pending_checkpoint, snapshot)
            pending_receipt = observer.evaluate('pending', [pending], requests, [])
            self.assertEqual(pending_receipt['classification'], 'PASS')
            self.assertFalse(pending_receipt['provider_transport_observed'])

            identity_checkpoint = root / 'identity.json'
            landing.start(claim, snapshot, identity_checkpoint)
            foreign = copy.deepcopy(snapshot)
            foreign['pr']['head']['repo'] = {'full_name': 'other/repo'}
            try:
                landing.advance(identity_checkpoint, foreign)
            except landing.LandingRefusal as error:
                identity = landing.refusal_output(error, 'advance')
            identity_receipt = observer.evaluate('identity', [identity], requests, [])
            self.assertEqual(identity_receipt['classification'], 'PASS')

            recovery_checkpoint = root / 'recovery.json'
            landing.start(claim, snapshot, recovery_checkpoint)
            landing.advance(recovery_checkpoint, snapshot)
            landing.dispatch(recovery_checkpoint, snapshot)
            merged = copy.deepcopy(snapshot)
            merged['pr'].update(merged=True, state='closed', merged_at='fixture',
                                merge_commit_sha='d' * 40)
            try:
                landing.advance(recovery_checkpoint, merged)
            except landing.LandingRefusal as error:
                refusal = landing.refusal_output(error, 'advance')
            merged['merge_commit'] = {'sha': 'd' * 40, 'tree': {'sha': 'b' * 40},
                                      'parents': [{'sha': 'c' * 40}, {'sha': 'a' * 40}]}
            continuation = landing.advance(recovery_checkpoint, merged)
            request_created = landing.dispatch(recovery_checkpoint, merged)
            recovery_receipt = observer.evaluate(
                'recovery', [refusal, continuation, request_created], requests, [])
            self.assertEqual(recovery_receipt['classification'], 'PASS')
            self.assertTrue(recovery_receipt['owner_request_created'])
            self.assertTrue(recovery_receipt['request_created_without_transport'])

            false_resolution = copy.deepcopy(pending)
            false_resolution['classification'] = 'RESOLVED'
            false_receipt = observer.evaluate('pending', [false_resolution], requests, [])
            self.assertIn('false_resolution', false_receipt['errors'])
            wrong_owner = copy.deepcopy(pending)
            wrong_owner['owner'] = 'other.advance'
            wrong_receipt = observer.evaluate('pending', [wrong_owner], requests, [])
            self.assertIn('wrong_owner', wrong_receipt['errors'])
            unknown_transport = observer.evaluate('pending', [pending], requests)
            self.assertIsNone(unknown_transport['provider_transport_observed'])
            self.assertIn('transport_evidence_unknown', unknown_transport['errors'])
            transported = observer.evaluate(
                'recovery', [refusal, continuation, request_created], requests,
                [{'kind': 'provider_transport'}])
            self.assertIn('provider_transport_observed', transported['errors'])

            receipt_path = evidence / 'normalized.json'
            receipt_path.write_text(json.dumps(recovery_receipt, indent=2) + '\n')
            for checkpoint in (pending_checkpoint, identity_checkpoint, recovery_checkpoint):
                checkpoint.unlink()
                Path(str(checkpoint) + '.lock').unlink()
            self.assertTrue(receipt_path.is_file())
            self.assertTrue((evidence/'entry/request.json').is_file())
            self.assertFalse(any(root.glob('*.json')))

    @staticmethod
    def landing_inputs():
        claim = {'repository': 'ed3c/soodles', 'issue': 1, 'pr': 2,
                 'head': 'a' * 40, 'tree': 'b' * 40, 'base_head': 'c' * 40,
                 'run_id': 10, 'run_attempt': 1, 'worktree': 'example',
                 'verifier_sha256': landing.verifier_digest()}
        repo = {'full_name': 'ed3c/soodles'}
        snapshot = {
            'pr': {'number': 2, 'html_url': 'https://github.com/ed3c/soodles/pull/2',
                   'body': 'Refs ed3c/soodles#1\n',
                   'head': {'repo': repo, 'sha': 'a' * 40, 'ref': 'example'},
                   'base': {'repo': repo, 'sha': 'c' * 40, 'ref': 'main'},
                   'merged': False, 'state': 'open', 'draft': False, 'mergeable': True},
            'issue': {'number': 1, 'html_url': 'https://github.com/ed3c/soodles/issues/1',
                      'state': 'open'},
            'run': {'id': 10, 'run_attempt': 1, 'repository': repo, 'head_repository': repo,
                    'head_sha': 'a' * 40, 'event': 'pull_request',
                    'path': '.github/workflows/runtime.yml', 'status': 'completed',
                    'conclusion': 'success'},
            'commit': {'sha': 'a' * 40, 'tree': {'sha': 'b' * 40}},
            'jobs': {'total_count': 1, 'jobs': [{
                'id': 11, 'name': 'runtime-evidence', 'run_id': 10, 'head_sha': 'a' * 40,
                'status': 'completed', 'conclusion': 'success', 'steps': [{
                    'name': 'Canonical acceptance on the exact candidate head',
                    'status': 'completed', 'conclusion': 'success'}]}]},
            'branch': {'name': 'main', 'commit': {'sha': 'c' * 40}}}
        return claim, snapshot
