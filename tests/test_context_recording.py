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


def bound_evaluate(case, events, requests, projection, transport=observer._MISSING):
    kwargs = {
        'initial_owner_projection': projection,
        'expected_owner_projection_sha256': observer.fingerprint(projection),
    }
    if transport is observer._MISSING:
        return observer.evaluate(case, events, requests, **kwargs)
    return observer.evaluate(case, events, requests, transport, **kwargs)


def capture_refusal(operation, function, *args):
    try:
        function(*args)
    except landing.LandingRefusal as error:
        return landing.refusal_output(error, operation)
    raise AssertionError(f'{operation} did not refuse')


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
        for shell in (False, True):
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'state'
                path.write_text('before')
                original = Path.read_bytes
                def read_bytes(p):
                    if p == path and p.read_text() == 'after':
                        raise PermissionError('injected snapshot failure')
                    return original(p)
                argv = [sys.executable, '-c',
                    'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("after")', str(path)]
                if shell:
                    argv = ['/bin/sh', '-c', shlex.join(argv)]
                with patch.object(Path, 'read_bytes', read_bytes):
                    result, _, _ = module.record(tmp, 'changed', argv)
                request = json.loads((Path(tmp)/'changed/request.json').read_text())
                self.assertEqual(request['files_before'][str(path)]['bytes'], len(b'before'))
                self.assertEqual(result['exit_code'], 0)
                self.assertEqual(result['files_after'][str(path)], {
                    'snapshot_error': 'PermissionError',
                    'observed_from': ['shell' if shell else 'argv']})
                self.assertTrue((Path(tmp)/'changed/result.json').is_file())

    def test_snapshot_errors_before_and_after_remain_in_raw_requests(self):
        from unittest.mock import patch
        for shell in (False, True):
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'AGENTS.md'
                path.write_text('route\n')
                original = Path.read_bytes
                def read_bytes(p):
                    if p == path:
                        raise PermissionError('injected snapshot failure')
                    return original(p)
                argv = ['cat', str(path)]
                if shell:
                    argv = ['/bin/sh', '-c', shlex.join(argv)]
                with patch.object(Path, 'read_bytes', read_bytes):
                    result, stdout, _ = module.record(tmp, 'denied', argv)
                request = json.loads((Path(tmp)/'denied/request.json').read_text())
                expected = {'snapshot_error': 'PermissionError',
                            'observed_from': ['shell' if shell else 'argv']}
                self.assertEqual(request['files_before'][str(path)], expected)
                self.assertEqual(result['files_after'][str(path)], expected)
                # The injected snapshot failure does not affect the subprocess.
                self.assertEqual(result['exit_code'], 0)
                self.assertEqual(stdout, b'route\n')
                self.assertEqual(observer.instruction_documents([request]), {})

    def test_instruction_bindings_require_valid_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            claim, snapshot = self.landing_inputs()
            checkpoint = Path(tmp)/'pending.json'
            landing.start(claim, snapshot, checkpoint)
            landing.advance(checkpoint, snapshot)
            projection = landing.dispatch(checkpoint, snapshot)
            pending = landing.advance(checkpoint, snapshot)
            instruction = Path(tmp)/'AGENTS.md'
            instruction.write_bytes(b'')
            result, stdout, _ = module.record(tmp, 'empty', ['cat', str(instruction)])
            request = json.loads((Path(tmp)/'empty/request.json').read_text())
            valid = request['files_before'][str(instruction)]
            receipt = bound_evaluate('pending', [pending], [request], projection, [])
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(stdout, b'')
            self.assertEqual(valid['bytes'], 0)
            self.assertEqual(receipt['classification'], 'PASS')

            invalid = [None, [], 'metadata', 0, {},
                       {'snapshot_error': 'PermissionError'},
                       {'bytes': 0}, {'sha256': valid['sha256']},
                       {**valid, 'snapshot_error': None}]
            invalid.extend({**valid, 'bytes': value}
                           for value in (None, True, False, -1, 0.0, '0'))
            invalid.extend({**valid, 'sha256': value}
                           for value in (None, 64, '', 'a' * 63, 'a' * 65,
                                         'g' * 64, 'a' * 63 + '\n'))
            for path in (str(instruction), str(Path(tmp)/'.agents/skills/example/SKILL.md')):
                for observation in invalid:
                    with self.subTest(path=path, observation=observation):
                        bad_request = {'files_before': {path: observation}}
                        original_request = copy.deepcopy(bad_request)
                        receipt = bound_evaluate(
                            'pending', [pending], [bad_request], projection, [])
                        self.assertEqual(receipt['classification'], 'FAIL')
                        self.assertEqual(receipt['errors'], ['missing_entry_read'])
                        self.assertEqual(receipt['instruction_documents'], {})
                        self.assertEqual(receipt['route_classification'], 'PASS')
                        self.assertFalse(receipt['provider_transport_observed'])
                        self.assertEqual(bad_request, original_request)

            failed = {'snapshot_error': 'PermissionError'}
            mixed_request = {'files_before': {
                str(instruction): valid,
                str(Path(tmp)/'.agents/skills/denied/SKILL.md'): failed}}
            repeated_failure = {'files_before': {str(instruction): failed}}
            for requests in ([mixed_request, repeated_failure],
                             [repeated_failure, mixed_request]):
                receipt = bound_evaluate('pending', [pending], requests, projection, [])
                self.assertEqual(receipt['classification'], 'PASS')
                self.assertEqual(receipt['instruction_documents'], {str(instruction): valid})
            uppercase = {**valid, 'sha256': valid['sha256'].upper()}
            self.assertEqual(observer.instruction_documents([
                {'files_before': {str(instruction): uppercase}}]), {str(instruction): uppercase})

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
            pending_projection = landing.dispatch(pending_checkpoint, snapshot)
            pending = landing.advance(pending_checkpoint, snapshot)
            pending_receipt = bound_evaluate(
                'pending', [pending], requests, pending_projection, [])
            self.assertEqual(pending_receipt['classification'], 'PASS')
            self.assertEqual(pending_receipt['route_classification'], 'PASS')
            self.assertFalse(pending_receipt['provider_transport_observed'])

            identity_checkpoint = root / 'identity.json'
            identity_projection = landing.start(claim, snapshot, identity_checkpoint)
            foreign = copy.deepcopy(snapshot)
            foreign['pr']['head']['repo'] = {'full_name': 'other/repo'}
            identity = capture_refusal(
                'advance', landing.advance, identity_checkpoint, foreign)
            identity_receipt = bound_evaluate(
                'identity', [identity], requests, identity_projection, [])
            self.assertEqual(identity_receipt['classification'], 'PASS')
            self.assertEqual(identity_receipt['route_classification'], 'PASS')
            self.assertEqual(identity_receipt['identity_safety'], 'PASS')

            recovery_checkpoint = root / 'recovery.json'
            landing.start(claim, snapshot, recovery_checkpoint)
            landing.advance(recovery_checkpoint, snapshot)
            recovery_projection = landing.dispatch(recovery_checkpoint, snapshot)
            merged = copy.deepcopy(snapshot)
            merged['pr'].update(merged=True, state='closed', merged_at='fixture',
                                merge_commit_sha='d' * 40)
            refusal = capture_refusal(
                'advance', landing.advance, recovery_checkpoint, merged)
            merged['merge_commit'] = {'sha': 'd' * 40, 'tree': {'sha': 'b' * 40},
                                      'parents': [{'sha': 'c' * 40}, {'sha': 'a' * 40}]}
            continuation = landing.advance(recovery_checkpoint, merged)
            request_created = landing.dispatch(recovery_checkpoint, merged)
            recovery_receipt = bound_evaluate(
                'recovery', [refusal, continuation, request_created],
                requests, recovery_projection, [])
            self.assertEqual(recovery_receipt['classification'], 'PASS')
            self.assertTrue(recovery_receipt['owner_request_created'])
            self.assertTrue(recovery_receipt['request_created_without_transport'])

            false_resolution = copy.deepcopy(pending)
            false_resolution['classification'] = 'RESOLVED'
            false_receipt = bound_evaluate(
                'pending', [false_resolution], requests, pending_projection, [])
            self.assertIn('false_resolution', false_receipt['errors'])
            wrong_owner = copy.deepcopy(pending)
            wrong_owner['owner'] = 'other.advance'
            wrong_receipt = bound_evaluate(
                'pending', [wrong_owner], requests, pending_projection, [])
            self.assertIn('wrong_owner', wrong_receipt['errors'])
            unknown_transport = bound_evaluate(
                'pending', [pending], requests, pending_projection)
            self.assertIsNone(unknown_transport['provider_transport_observed'])
            self.assertIn('transport_evidence_unknown', unknown_transport['errors'])
            transported = bound_evaluate(
                'recovery', [refusal, continuation, request_created],
                requests, recovery_projection, [{'kind': 'provider_transport'}])
            self.assertIn('provider_transport_observed', transported['errors'])

            wrong_operation = copy.deepcopy(identity)
            wrong_operation['owner'] = 'landing.dispatch'
            historical = bound_evaluate(
                'identity', [wrong_operation], requests, identity_projection, [])
            self.assertEqual(historical['route_classification'], 'FAIL')
            self.assertEqual(historical['identity_safety'], 'PASS')
            self.assertIn('wrong_operation_for_state', historical['errors'])
            self.assertEqual(historical['owner_events_observed'], 1)
            self.assertEqual(historical['route_events_observed'], 0)
            self.assertEqual(historical['refusals_observed'], 1)

            mixed = bound_evaluate(
                'identity', [identity, wrong_operation], requests, identity_projection, [])
            self.assertEqual(mixed['classification'], 'FAIL')
            self.assertIn('wrong_operation_for_state', mixed['errors'])
            self.assertEqual(mixed['owner_events_observed'], 2)
            self.assertEqual(mixed['route_events_observed'], 1)
            self.assertEqual(mixed['refusals_observed'], 2)

            dispatch_checkpoint = root / 'dispatch.json'
            landing.start(claim, snapshot, dispatch_checkpoint)
            dispatch_projection = landing.advance(dispatch_checkpoint, snapshot)
            dispatch_refusal = capture_refusal(
                'dispatch', landing.dispatch, dispatch_checkpoint, foreign)
            dispatch_is_current = bound_evaluate(
                'identity', [dispatch_refusal], requests, dispatch_projection, [])
            self.assertEqual(dispatch_is_current['classification'], 'PASS')

            stale_binding = observer.evaluate(
                'identity', [dispatch_refusal], requests, [],
                initial_owner_projection=dispatch_projection,
                expected_owner_projection_sha256=observer.fingerprint(identity_projection))
            self.assertEqual(stale_binding['route_classification'], 'FAIL')
            self.assertIn('owner_projection_digest_mismatch', stale_binding['errors'])

            request_after_refusal = copy.deepcopy(identity)
            request_after_refusal['request'] = {'operation': 'merge'}
            unsafe_identity = bound_evaluate(
                'identity', [request_after_refusal], requests, identity_projection, [])
            self.assertEqual(unsafe_identity['identity_safety'], 'FAIL')
            self.assertIn('identity_request_created', unsafe_identity['errors'])

            identity_unknown = bound_evaluate(
                'identity', [identity], requests, identity_projection)
            self.assertEqual(identity_unknown['identity_safety'], 'UNKNOWN')

            receipt_path = evidence / 'normalized.json'
            receipt_path.write_text(json.dumps(recovery_receipt, indent=2) + '\n')
            for checkpoint in (
                    pending_checkpoint, identity_checkpoint, recovery_checkpoint,
                    dispatch_checkpoint):
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
