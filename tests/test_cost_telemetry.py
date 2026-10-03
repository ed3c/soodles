"""CI product controls, not live measurements or budget-exhaustion claims."""
import copy
import io
import json
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch

import cost_telemetry as cost
import issue_atom as atom
import schema_manager
import soodles
from test_admission_revision import RevisionFixture


class CostTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.auth = self.root / 'authorization.json'
        self.auth.write_text(json.dumps({'repository': 'ed3c/soodles', 'base_head': 'a'*40,
                                        'issue': {'number': 215}}))
        self.state = {'authorization_sha256': cost.digest(self.auth.read_bytes()),
                      'issue': {'number': 215}, 'phase': 'resolved', 'writes': {},
                      'publication': {'head': 'b'*40}}
        self.state_ref = self.write('state.json', self.state)
        self.identity = cost.subject(cost.decode(self.auth.read_bytes()), self.auth.read_bytes(), self.state)
        self.source = cost.file_ref(self.auth)
        self.manifest = {'schema': 1, 'authorization_sha256': self.identity['authorization'],
                         'subject': self.identity, 'state': self.state_ref, 'head': 'b'*40}

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return cost.file_ref(path)

    def span(self, name='one', **changes):
        options = dict(family='processing', kind='foreground', phase='execution',
                       outcome='pending', seconds=10, started=10, finished=20)
        options.update(changes)
        return cost.observation(self.identity, self.source, name, **options)

    def test_statuses_never_convert_pending_refusal_or_unknown_to_success(self):
        for status in ('pending', 'refused', 'unknown', 'failed', 'not_required'):
            with self.subTest(status=status):
                self.assertEqual(cost.status({'status': status, 'exit': 0}), status)
                stderr = io.StringIO()
                with patch('sys.stderr', stderr):
                    soodles.measured('example', lambda: {'status': status})
                record = json.loads(stderr.getvalue())
                self.assertEqual(record['outcome'], status)
                self.assertLessEqual(record['wall_started'], record['wall_finished'])
                self.assertTrue(record['span_id'])
        self.assertEqual(cost.status({'status': 'resolved'}), 'passed')
        self.assertEqual(cost.status({}), 'unknown')

    def test_replay_is_idempotent_and_conflicting_identity_refuses(self):
        item = self.span()
        one = cost.project(self.identity, [item])
        self.assertEqual(one, cost.project(self.identity, [item, copy.deepcopy(item)]))
        conflict = {**item, 'seconds': 9}
        with self.assertRaisesRegex(cost.CostRefusal, 'conflicting_replay'):
            cost.project(self.identity, [item, conflict])
        with self.assertRaisesRegex(cost.CostRefusal, 'subject'):
            cost.project({**self.identity, 'authorization': 'c'*64}, [item])

    def test_bad_numbers_and_incomplete_start(self):
        for value in (float('nan'), float('inf'), -1, True):
            with self.subTest(value=value), self.assertRaises(cost.CostRefusal):
                self.span(seconds=value)
        with self.assertRaises(cost.CostRefusal):
            self.span(started=21, finished=20)
        incomplete = self.span(seconds=None, finished=None, outcome='unknown')
        result = cost.project(self.identity, [incomplete])
        self.assertIsNone(result['summary']['foreground_seconds'])
        self.assertEqual(result['coverage']['processing']['status'], 'partial')
        self.assertEqual(result['summary']['statuses']['unknown'], 1)
        for field in ('tokens', 'price', 'api_calls', 'human_wait_seconds', 'cpu_seconds'):
            self.assertIsNone(result['summary'][field])
        with self.assertRaises(cost.CostRefusal):
            cost.decode('{"seconds": NaN}')
        with self.assertRaises(cost.CostRefusal):
            cost.decode('{"seconds": 1, "seconds": 2}')

    def test_cost_review_preserves_sources_and_unknowns_without_demand(self):
        values = [self.span('slow', outcome='passed', seconds=90000, started=None, finished=None),
                  self.span('incomplete', seconds=None, finished=None, outcome='unknown')]
        with patch('schema_manager.project_cost', wraps=schema_manager.project_cost) as project:
            result = cost.project(self.identity, values)
        review = project.call_args.kwargs['review']
        self.assertEqual(review['owner'], 'test-manager')
        self.assertEqual(review['subject'], self.identity)
        self.assertEqual(review['sources'], result['sources'])
        self.assertEqual(review['status'], 'reviewed')
        self.assertIsNone(review['next'])
        self.assertIsNone(review['test_demand'])
        self.assertEqual(review['effects'], [])
        self.assertFalse(review['authorizes_landing'])
        observed = next(item for item in review['findings'] if item['kind'] == 'observed_cost')
        self.assertEqual(observed['phase'], 'execution')
        self.assertEqual(observed['sources'], [self.source['sha256']])
        self.assertEqual(observed['observation']['inclusive_seconds'], 90000)
        self.assertEqual(observed['observation']['statuses'], {'passed': 1, 'unknown': 1})
        self.assertTrue(any(item['kind'] == 'unmeasured_spans' and item['phase'] == 'execution'
                            for item in review['unknowns']))
        self.assertTrue(any(item.get('family') == 'writer_model' and item['status'] == 'unknown'
                            for item in review['unknowns']))

    def test_cost_review_routes_failures_and_repeated_modules_to_owner_readback(self):
        values = [self.span('failure', outcome='failed'), self.span('refusal', outcome='refused'),
                  self.span('module-one', family='verification', kind='worker', phase='test.module',
                            worker='test_example', outcome='passed'),
                  self.span('module-two', family='verification', kind='worker', phase='test.module',
                            worker='test_example', outcome='passed')]
        with patch('schema_manager.project_cost', wraps=schema_manager.project_cost) as project:
            cost.project(self.identity, values)
        review = project.call_args.kwargs['review']
        self.assertEqual(review['status'], 'needs_owner_readback')
        self.assertEqual(review['next'], {'owner': 'original-owner', 'required': 'original_owner_readback',
                                          'continuation': 'existing_owner_next'})
        failure = next(item for item in review['findings'] if item['kind'] == 'owner_readback_required')
        self.assertEqual(failure['observation'], {'failed': 1, 'refused': 1})
        repeated = next(item for item in review['findings'] if item['kind'] == 'repeated_module_observations')
        self.assertEqual(repeated['worker'], 'test_example')
        self.assertEqual(repeated['observation'], {'runs': 2})
        self.assertEqual(repeated['sources'], [self.source['sha256']])
        self.assertTrue(any(item['kind'] == 'repeat_necessity' for item in review['unknowns']))
        self.assertEqual(review['effects'], [])
        self.assertIsNone(review['test_demand'])

    def test_nested_parallel_intervals_do_not_become_wall_sum(self):
        values = [self.span(), self.span('nested', started=12, finished=16, seconds=4),
                  self.span('other', started=18, finished=25, seconds=7),
                  self.span('wait', started=20, finished=30, seconds=10, kind='wait', family='waits'),
                  self.span('worker-a', kind='worker', family='verification', worker='a'),
                  self.span('worker-a-child', kind='worker', family='verification', worker='a',
                            started=11, finished=15, seconds=4),
                  self.span('worker-b', kind='worker', family='verification', worker='b')]
        summary = cost.project(self.identity, values)['summary']
        self.assertEqual(summary['foreground_seconds'], 15)
        self.assertEqual(summary['observed_wall_seconds'], 20)
        self.assertEqual(summary['external_wait_seconds'], 10)
        self.assertEqual(summary['parallel_worker_seconds'], 20)

    def test_old_log_nested_cases_and_wrong_passed_label(self):
        raw = '\n'.join(json.dumps(value) for value in [
            {'event': 'soodles.timing', 'operation': 'test.module', 'module': 'test_a', 'seconds': 6, 'exit': 0},
            {'event': 'soodles.timing', 'operation': 'test.case', 'seconds': 4},
            {'event': 'soodles.timing', 'operation': 'issue_atom.observe', 'seconds': 2,
             'status': 'refused', 'outcome': 'passed'}]).encode()
        values = cost.timing_log(raw, self.source, self.identity)
        report = cost.project(self.identity, values)
        self.assertEqual(report['summary']['parallel_worker_seconds'], 6)
        self.assertIsNone(report['summary']['observed_wall_seconds'])
        self.assertEqual(values[-1]['status'], 'refused')

    def process_manifest(self):
        argv = ['/pinned/issue-atom', 'run', str(self.auth)]
        input_ref = self.write('input.json', {'next': {'argv': argv}})
        output_ref = self.write('stdout.json', {'status': 'pending', 'phase': 'ci', 'issue': {'number': 215}})
        stderr = self.root / 'stderr.log'
        stderr.write_text(json.dumps({'event': 'soodles.timing', 'operation': 'issue_atom.observe',
                                     'status': 'pending', 'outcome': 'passed', 'seconds': 2})+'\n')
        observer = self.root / 'observer.py'
        observer.write_text('raise AssertionError("never execute input code")\n')
        process = {'argv': argv, 'input_receipt': input_ref['path'], 'input_sha256': input_ref['sha256'],
                   'stdout_sha256': output_ref['sha256'], 'stderr_sha256': cost.file_ref(stderr)['sha256'],
                   'observer_sha256': cost.file_ref(observer)['sha256'], 'wall_started': 10,
                   'wall_finished': 15, 'seconds': 5, 'exit_status': 0}
        self.manifest['processes'] = [{'process': self.write('process.json', process),
            'input': input_ref, 'stdout': output_ref, 'stderr': cost.file_ref(stderr),
            'observer': cost.file_ref(observer)}]
        return process

    def test_readonly_external_observer_and_provider_share_schema_projection(self):
        self.process_manifest()
        run = {'id': 100, 'run_attempt': 2, 'head_sha': 'b'*40,
               'repository': {'full_name': 'ed3c/soodles'}}
        jobs = {'jobs': [{'id': 101, 'run_id': 100, 'run_attempt': 2, 'head_sha': 'b'*40,
                         'name': 'runtime', 'status': 'in_progress', 'conclusion': None,
                         'started_at': '2026-10-01T12:00:00Z', 'completed_at': None}]}
        self.manifest['provider'] = [{'run': self.write('run.json', run), 'jobs': self.write('jobs.json', jobs)}]
        manifest = self.write('manifest.json', self.manifest)
        before = {p: p.read_bytes() for p in self.root.iterdir()}
        with patch('subprocess.run', side_effect=AssertionError('effect')), \
                patch('urllib.request.urlopen', side_effect=AssertionError('network')):
            result = cost.report(self.auth, manifest['path'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.iterdir()})
        self.assertEqual(result['summary']['foreground_seconds'], 5)
        self.assertEqual(result['schema_projection']['cost'], result['summary'])
        self.assertEqual(result['schema_projection']['effects'], [])
        self.assertFalse(result['authorizes_landing'])
        self.assertEqual(result['summary']['statuses']['pending'], 4)
        self.assertIsNone(result['summary']['parallel_worker_seconds'])

    def test_report_feedback_uses_only_bound_owner_result_and_preserves_next(self):
        for owner in (None,
                      {'owner': 'soodles.issue-atom', 'status': 'resolved', 'next': None},
                      {'owner': 'soodles.issue-atom', 'status': 'pending', 'phase': 'ci',
                       'next': {'argv': ['original-owner', 'readback'], 'environment': {'PIN': 'fixed'}}}):
            with self.subTest(owner=owner):
                if owner is not None:
                    self.manifest['owner_result'] = self.write('owner.json', owner)
                result = cost.report(self.auth, self.write('manifest.json', self.manifest)['path'])
                feedback = result['feedback']
                self.assertEqual(feedback['cost_review'], result['schema_projection']['review'])
                self.assertEqual(feedback['dag']['cost_review']['status'], 'observed')
                self.assertEqual(feedback['next'], (owner or {}).get('next'))
                self.assertEqual(feedback['state'], (owner or {}).get('status'))
                self.assertEqual(feedback['effects'], [])
                self.assertIsNone(feedback['test_demand'])
                self.assertFalse(feedback['authorizes_landing'])
                if owner is None:
                    self.assertEqual(feedback['dag']['owner_transition']['status'], 'unknown')
                else:
                    self.assertIn(self.manifest['owner_result'], result['evidence'])
        for owner in ({'owner': 'foreign'}, {'owner': 'soodles.issue-atom', 'issue': {'number': 216}},
                      {'owner': 'soodles.issue-atom', 'publication': {'head': 'c' * 40}}):
            self.manifest['owner_result'] = self.write('owner.json', owner)
            with self.subTest(owner=owner), self.assertRaisesRegex(cost.CostRefusal, 'owner_result'):
                cost.report(self.auth, self.write('manifest.json', self.manifest)['path'])

    def test_native_reported_usage_requires_original_claim_and_finite_numbers(self):
        claim = {'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#215',
                 'head': 'b'*40, 'base_head': 'a'*40, 'session_id': 'session', 'order_id': 'order'}
        self.manifest['claim'] = self.write('claim.json', claim)
        self.manifest['native'] = [{'kind': 'meta', 'session_id': 'session', 'order_id': 'order',
                                  'file': self.write('meta.json', {'session_id': 'session', 'total_cost_usd': 0.125})}]
        manifest = self.write('manifest.json', self.manifest)
        report = cost.report(self.auth, manifest['path'])
        self.assertEqual(report['summary']['native_usage'][0]['reported_cost_usd'], 0.125)
        self.assertIsNone(report['summary']['price'])
        self.manifest['native'][0]['file'] = self.write('meta.json', {'session_id': 'session', 'total_cost_usd': -1})
        manifest = self.write('manifest.json', self.manifest)
        with self.assertRaises(cost.CostRefusal):
            cost.report(self.auth, manifest['path'])

    def test_external_incomplete_intent_stays_unknown(self):
        process = self.process_manifest()
        entry = self.manifest.pop('processes')[0]
        intent = {key: value for key, value in process.items()
                  if key not in ('seconds', 'wall_finished', 'exit_status', 'stdout_sha256', 'stderr_sha256')}
        self.manifest['intents'] = [{'intent': self.write('intent.json', intent),
                                    'input': entry['input'], 'observer': entry['observer']}]
        manifest = self.write('manifest.json', self.manifest)
        result = cost.report(self.auth, manifest['path'])
        self.assertEqual(result['summary']['statuses']['unknown'], 1)
        self.assertIsNone(result['summary']['foreground_seconds'])

    def test_normal_provider_snapshot_is_read_only_and_idempotent(self):
        run = {'id': 100, 'run_attempt': 2, 'head_sha': 'b'*40,
               'repository': {'full_name': 'ed3c/soodles'}, 'status': 'completed'}
        jobs = {'jobs': [{'id': 101, 'run_id': 100, 'run_attempt': 2, 'head_sha': 'b'*40,
                         'name': 'runtime', 'status': 'completed', 'conclusion': 'success',
                         'started_at': '2026-10-01T12:00:00Z', 'completed_at': '2026-10-01T12:00:10Z'}]}
        atom.save_json(self.auth.with_name(self.auth.name + '.state.json'), self.state)
        with patch('urllib.request.urlopen', side_effect=AssertionError('network')):
            cost.record_provider(self.auth, self.state, run, jobs, atom.save_json)
            first = cost.report(self.auth)
            cost.record_provider(self.auth, self.state, run, jobs, atom.save_json)
            second = cost.report(self.auth)
        for result in (first, second):
            self.assertGreaterEqual(result['feedback'].pop('elapsed_ms'), 0)
        self.assertEqual(first, second)
        self.assertEqual(first['summary']['provider_job_seconds'], 10)
        self.assertIsNone(first['summary']['parallel_worker_seconds'])
        bad = copy.deepcopy(jobs)
        bad['jobs'][0]['run_attempt'] = 3
        with self.assertRaisesRegex(cost.CostRefusal, 'provider_job'):
            cost.record_provider(self.auth, self.state, run, bad, atom.save_json)

    def test_corrupt_external_sources_identity_and_replay_refuse(self):
        process = self.process_manifest()
        manifest = self.write('manifest.json', self.manifest)
        Path(self.manifest['processes'][0]['stderr']['path']).write_text('changed')
        with self.assertRaisesRegex(cost.CostRefusal, 'digest'):
            cost.report(self.auth, manifest['path'])
        self.process_manifest()
        process['input_sha256'] = '0'*64
        self.manifest['processes'][0]['process'] = self.write('process.json', process)
        manifest = self.write('manifest.json', self.manifest)
        with self.assertRaisesRegex(cost.CostRefusal, 'process_input'):
            cost.report(self.auth, manifest['path'])
        self.manifest['authorization_sha256'] = '0'*64
        manifest = self.write('manifest.json', self.manifest)
        with self.assertRaisesRegex(cost.CostRefusal, 'manifest_authorization'):
            cost.report(self.auth, manifest['path'])

    def test_normal_owner_record_resume_refusal_and_telemetry_failure(self):
        state_path = self.auth.with_name(self.auth.name + '.state.json')
        atom.save_json(state_path, self.state)
        env = {'SOODLES_AUTHORIZATION_SHA256': self.identity['authorization']}
        result = {'status': 'pending', 'phase': 'ci', 'next': {'argv': ['unchanged']}}
        with patch.object(atom, '_run', return_value=result):
            first = atom.run(self.auth, environ=env)
        self.assertEqual(first['cost']['summary']['statuses']['pending'], 2)
        self.assertIs(first['feedback'], first['cost']['feedback'])
        self.assertIs(first['feedback']['next'], result['next'])
        refusal = atom.AtomRefusal('github.issue.outcome', 'unknown', 'fresh_readback')
        with patch.object(atom, '_run', side_effect=refusal), self.assertRaises(atom.AtomRefusal) as caught:
            atom.run(self.auth, environ=env)
        refused = atom.refusal_output(caught.exception, self.auth)
        self.assertEqual(refused['invalid']['field'], 'github.issue.outcome')
        self.assertEqual(refused['next']['required'], ['fresh_readback'])
        self.assertIs(refused['feedback'], refused['cost']['feedback'])
        self.assertIs(refused['feedback']['next'], refused['next'])
        self.assertGreater(refused['cost']['summary']['observations'], first['cost']['summary']['observations'])
        with patch.object(atom, '_run', return_value={'status': 'resolved', 'next': None}), \
                patch.object(cost, 'begin', side_effect=OSError('disk unavailable')):
            final = atom.run(self.auth, environ=env)
        self.assertEqual(final['status'], 'resolved')
        self.assertIsNone(final['next'])
        self.assertEqual(final['cost']['status'], 'refused')
        self.assertEqual(final['feedback']['state'], 'resolved')
        self.assertIsNone(final['feedback']['next'])
        self.assertEqual(final['feedback']['dag']['cost_review']['status'], 'unknown')

    def test_untyped_owner_response_preserves_payload_and_exposes_cost_on_stderr(self):
        env = {'SOODLES_AUTHORIZATION_SHA256': self.identity['authorization']}
        payload = {'payload': {'next': ['opaque']}}
        stderr = io.StringIO()
        with patch.object(atom, '_run', return_value=payload), patch('sys.stderr', stderr):
            result = atom.run(self.auth, environ=env)
        self.assertIs(result, payload)
        self.assertEqual(result, {'payload': {'next': ['opaque']}})
        event = json.loads(stderr.getvalue())
        self.assertEqual(event['event'], 'soodles.cost')
        self.assertEqual(event['subject'], self.identity)
        self.assertEqual(event['summary']['statuses']['unknown'], 1)
        self.assertEqual(event['schema_projection']['cost'], event['summary'])
        self.assertTrue(event['observation_id'])
        stderr = io.StringIO()
        with patch.object(atom, '_run', return_value=payload), patch('sys.stderr', stderr), \
                patch.object(cost, 'report', side_effect=cost.CostRefusal('cost.native_fields')):
            result = atom.run(self.auth, environ=env)
        self.assertEqual(result, {'payload': {'next': ['opaque']}})
        event = json.loads(stderr.getvalue())
        self.assertEqual(event['event'], 'soodles.cost')
        self.assertEqual(event['status'], 'refused')
        self.assertEqual(event['invalid'], {'field': 'cost.evidence', 'value': 'cost.native_fields'})
        self.assertFalse(event['authorizes_landing'])
        self.assertEqual(cost.report(self.auth)['summary']['statuses']['unknown'], 2)

    def test_wait_preserves_observation_correlation_and_is_pending(self):
        atom.save_json(self.auth.with_name(self.auth.name + '.state.json'), self.state)
        result = {'status': 'pending', 'phase': 'ci', 'waiting_on': 'GitHub Actions',
                  'cost': {'observation_id': 'original-observation', 'subject': self.identity}}
        sleep, stderr = Mock(), io.StringIO()
        with patch('sys.stderr', stderr):
            atom.wait_cost(self.auth, result, 5, sleep)
        sleep.assert_called_once_with(5)
        event = json.loads(stderr.getvalue())
        self.assertEqual(event['observation_id'], 'original-observation')
        self.assertEqual(event['authorization_sha256'], self.identity['authorization'])
        self.assertEqual(event['outcome'], 'pending')
        self.assertEqual(cost.report(self.auth)['coverage']['waits']['status'], 'partial')

    def test_created_issue_keeps_subject_and_binds_actual_readback(self):
        auth = {'repository': 'ed3c/soodles', 'base_head': 'a'*40,
                'issue': {'title': 'cost', 'body': 'selected body'}}
        self.auth.write_text(json.dumps(auth))
        raw = self.auth.read_bytes()
        identity = cost.subject(auth, raw, {})
        body = 'selected body\n\n<!-- soodles:local-atom-v1:' + identity['authorization'] + ' -->\n'
        self.state.update(authorization_sha256=identity['authorization'], issue={
            'number': 215, 'url': 'https://github.com/ed3c/soodles/issues/215',
            'body_sha256': cost.digest(body.encode())})
        self.assertEqual(identity, cost.subject(auth, raw, self.state))
        self.manifest.update(subject=identity, authorization_sha256=identity['authorization'],
                             state=self.write('state.json', self.state))
        process = self.process_manifest()
        entry = self.manifest['processes'][0]
        entry['stdout'] = self.write('stdout.json', {'status': 'refused', 'issue': {'number': 215}})
        process.update(exit_status=1, stdout_sha256=entry['stdout']['sha256'])
        entry['process'] = self.write('process.json', process)
        self.manifest['claim'] = self.write('claim.json', {'repository': 'ed3c/soodles',
            'subject': 'ed3c/soodles#215', 'base_head': 'a'*40, 'head': 'b'*40})
        result = cost.report(self.auth, self.write('manifest.json', self.manifest)['path'])
        self.assertEqual(result['summary']['statuses']['refused'], 1)
        self.assertIsNone(result['subject']['issue'])
        self.state['issue']['body_sha256'] = '0'*64
        with self.assertRaisesRegex(cost.CostRefusal, 'created_issue_binding'):
            cost.subject(auth, raw, self.state)

    def test_codex_terminal_usage_and_nested_schema_numbers(self):
        self.manifest['claim'] = self.write('claim.json', {'repository': 'ed3c/soodles',
            'subject': 'ed3c/soodles#215', 'base_head': 'a'*40, 'head': 'b'*40,
            'session_id': 'session', 'order_id': 'order'})
        ref = self.write('raw.ndjson', {'type': 'turn.completed', 'usage': {
            'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 12,
            'reasoning_output_tokens': 3}})
        entry = {'file': ref, 'kind': 'codex_raw', 'session_id': 'session', 'order_id': 'order'}
        self.manifest['native'] = [entry, copy.deepcopy(entry)]
        result = cost.report(self.auth, self.write('manifest.json', self.manifest)['path'])
        self.assertEqual(result['summary']['tokens']['input_tokens'], 100)
        self.assertEqual(result['summary']['tokens']['output_tokens'], 12)
        self.assertIsNone(result['summary']['price'])
        facts = {key: result[key] for key in ('subject', 'coverage', 'summary', 'sources')}
        facts['summary']['tokens']['input_tokens'] = -1
        with self.assertRaises(schema_manager.SchemaRefusal):
            schema_manager.project_cost(facts)

    def test_phase_and_legacy_wait_costs_reach_schema_without_wall_invention(self):
        raw = json.dumps({'event': 'soodles.timing', 'operation': 'issue_atom.wait',
                          'seconds': 5, 'status': 'pending'}).encode()
        result = cost.project(self.identity, cost.timing_log(raw, self.source, self.identity))
        self.assertIsNone(result['summary']['external_wait_seconds'])
        self.assertEqual(result['summary']['logged_wait_seconds'], 5)
        self.assertEqual(result['schema_projection']['cost']['phase_costs'][0]['inclusive_seconds'], 5)

    def test_incomplete_normal_intent_and_direct_schema_numeric_refusal(self):
        handle = cost.begin(self.auth, atom.save_json)
        result = cost.report(self.auth)
        self.assertEqual(result['summary']['statuses']['unknown'], 1)
        self.assertIsNone(result['summary']['foreground_seconds'])
        facts = {key: result[key] for key in ('subject', 'coverage', 'summary', 'sources')}
        facts['summary']['foreground_seconds'] = float('inf')
        with self.assertRaises(schema_manager.SchemaRefusal):
            schema_manager.project_cost(facts)
        self.assertTrue(handle[0].exists())


class CostLineageTests(unittest.TestCase):
    def setUp(self):
        self.f = RevisionFixture()
        self.addCleanup(self.f.temp.cleanup)
        self.owner = patch.object(atom, 'validate_lifecycle_owner')
        self.owner.start()
        self.addCleanup(self.owner.stop)
        self.auth = self.f.save('authorization.json', self.f.auth)
        self.raw = self.auth.read_bytes()
        self.state = {'authorization_sha256': cost.digest(self.raw), 'issue': {'number': 18},
                      'phase': 'resolved', 'writes': {}, 'publication': {'head': self.f.candidate}}
        self.identity = cost.subject(self.f.auth, self.raw, self.state)
        self.claim = {'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#18',
                      'head': self.f.candidate, 'base_head': self.f.base,
                      'session_id': 'cost-session', 'order_id': self.f.selection['order_id']}
        self.state_path = self.auth.with_name(self.auth.name + '.state.json')
        self.claim_path = self.auth.parent / (self.auth.name + '.d/publication-claim.json')
        self.claim_path.parent.mkdir()
        self.manifest_path = self.f.directory / 'manifest.json'
        self.ack_path = self.f.root / '.noodle/control-ack.ndjson'
        self.ack_path.parent.mkdir()

    def released(self, *, selection=None, authorization=None, index=0):
        entry = self.f.released_scope(self.auth, authorization, selection, index)
        self.state.update(scope_amendment=entry['amendment'], **entry['controls'],
                          admission_sha256=entry['amendment']['prepared']['sha256'])
        self.state['writes']['issue_scope'] = entry['issue_write']
        self.ack_path.write_text(''.join(json.dumps(ack) + '\n' for ack in entry['acks']))
        return entry

    def save(self):
        self.state_path.write_text(json.dumps(self.state))
        self.claim_path.write_text(json.dumps(self.claim))
        manifest = {'schema': 1, 'authorization_sha256': self.identity['authorization'],
                    'subject': self.identity, 'state': cost.file_ref(self.state_path),
                    'claim': cost.file_ref(self.claim_path), 'head': self.claim['head']}
        self.manifest_path.write_text(json.dumps(manifest))

    def report(self, automatic=False):
        self.save()
        return cost.report(self.auth, None if automatic else self.manifest_path)

    def test_original_and_released_claim_share_subject_and_readonly_report_paths(self):
        record = {'subject': self.identity, 'observations': [cost.observation(
            self.identity, cost.file_ref(self.auth), 'original-cost', family='processing',
            kind='foreground', phase='execution', outcome='passed', seconds=7)]}
        record_path = self.claim_path.parent / 'cost/original.json'
        record_path.parent.mkdir()
        record_path.write_text(json.dumps(record))
        record_raw = record_path.read_bytes()
        self.assertEqual(self.report()['subject'], self.identity)
        self.released()
        for automatic in (False, True):
            with self.subTest(automatic=automatic), self.assertRaisesRegex(cost.CostRefusal, 'claim_base'):
                self.report(automatic)
        self.claim['base_head'] = self.f.target
        shutil.rmtree(self.f.wt)
        with self.ack_path.open('a') as stream:
            stream.write(json.dumps({'id': 'later-operation', 'action': 'mode', 'status': 'ok'}) + '\n')
        self.save()
        before = {str(p): p.read_bytes() for p in self.f.directory.rglob('*') if p.is_file()}
        with patch.object(atom, 'save_json', side_effect=AssertionError('state write')), \
                patch.object(atom, 'amendment_control', side_effect=AssertionError('control effect')), \
                patch.object(atom, 'scope_control_readback', side_effect=AssertionError('lock')), \
                patch('fcntl.flock', side_effect=AssertionError('lock')), \
                patch('urllib.request.urlopen', side_effect=AssertionError('provider')):
            for manifest in (self.manifest_path, None):
                result = cost.report(self.auth, manifest)
                self.assertEqual(result['subject'], self.identity)
                self.assertEqual(result['status'], 'reported')
                self.assertEqual(result['summary']['observations'], 1)
                self.assertEqual(result['summary']['phase_costs'][0]['inclusive_seconds'], 7)
                self.assertEqual(record_path.read_bytes(), record_raw)
                self.assertEqual(result['schema_projection']['review']['owner'], 'test-manager')
                self.assertIn(cost.file_ref(self.ack_path), result['evidence'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.f.directory.rglob('*') if p.is_file()})

    def test_unreleased_target_uses_previous_accepted_base(self):
        entry = self.released()
        self.state['scope_amendment']['status'] = 'prepared'
        self.assertEqual(self.report()['subject'], self.identity)
        self.claim['base_head'] = self.f.target
        for automatic in (False, True):
            with self.subTest(automatic=automatic), self.assertRaisesRegex(cost.CostRefusal, 'claim_base'):
                self.report(automatic)
        entry['amendment']['status'] = 'released'
        self.state['scope_history'] = [entry]
        self.state['scope_amendment'] = {'status': 'prepared', 'selection': {'unaccepted': True}}
        for name in entry['controls']:
            self.state.pop(name)
        self.state['writes'] = {}
        self.ack_path.unlink()
        self.assertEqual(self.report()['subject'], self.identity)

    def test_history_and_current_release_validate_contract_chain(self):
        first = self.released(selection=self.f.criteria())
        self.state['scope_history'] = [first]
        effective = atom.scope_history_authority(self.f.auth, self.state)
        self.released(authorization=effective, index=1)
        self.claim['base_head'] = self.f.target
        self.assertEqual(self.report()['subject'], self.identity)
        self.state['scope_history'][0]['issue_write']['previous_body_sha256'] = '0' * 64
        with self.assertRaisesRegex(atom.AtomRefusal, 'revision.history.issue'):
            self.report()

    def test_missing_conflicting_and_mismatched_ack_refuse_current_and_history(self):
        entry = self.released()
        self.claim['base_head'] = self.f.target
        original = copy.deepcopy(entry['acks'])
        bad_sets = [original[:-1], [*original, original[0]],
                    [*original, {**original[0], 'status': 'error'}],
                    [{**original[0], 'action': 'foreign'}, *original[1:]],
                    [{**original[0], 'status': 'error'}, *original[1:]], [*original, 'malformed']]
        for history in (False, True):
            if history:
                self.state['scope_history'] = [entry]
                self.state.pop('scope_amendment')
            for acks in bad_sets:
                with self.subTest(history=history, acks=acks):
                    if history:
                        entry['acks'] = acks
                    else:
                        self.ack_path.write_text(''.join(json.dumps(ack) + '\n' for ack in acks))
                    with self.assertRaisesRegex(atom.AtomRefusal, 'revision.history.ack'):
                        self.report()

    def test_foreign_tampered_and_missing_lineage_never_fall_back_to_claim(self):
        entry = self.released()
        original_state = copy.deepcopy(self.state)
        for mutate in (
                lambda: self.state.update(authorization_sha256='0' * 64),
                lambda: self.state.update(scope_amendment='malformed'),
                lambda: self.state.update(base_recovery='malformed'),
                lambda: self.state['scope_amendment']['selection'].update(sha256='0' * 64),
                lambda: self.state['scope_amendment']['prepared'].update(sha256='0' * 64),
                lambda: self.state['scope_amendment'].pop('prepared'),
                lambda: self.state.update(admission_sha256='0' * 64),
                lambda: self.state['writes']['issue_scope'].update(status='offered'),
                lambda: self.state['scope_edit'].update(action='mode')):
            self.state = copy.deepcopy(original_state)
            mutate()
            with self.assertRaises((atom.AtomRefusal, cost.CostRefusal)):
                self.report()
        self.state = copy.deepcopy(original_state)
        packet_path = Path(entry['amendment']['selection']['path'])
        packet = json.loads(packet_path.read_text())
        foreign = self.f.save('foreign-auth.json', {**self.f.auth, 'repository': 'foreign/repository'})
        packet['authorization'] = cost.file_ref(foreign)
        packet_path.write_text(json.dumps(packet))
        self.state['scope_amendment']['selection'] = cost.file_ref(packet_path)
        with self.assertRaisesRegex(atom.AtomRefusal, 'scope.authorization'):
            self.report()
        packet_path.unlink()
        with self.assertRaisesRegex(atom.AtomRefusal, 'prior_atom.path'):
            self.report()

    def test_prepared_base_recovery_has_no_typed_release_proof(self):
        self.state['base_recovery'] = {'prepared': {'path': '/not-accepted'}}
        with self.assertRaisesRegex(atom.AtomRefusal, 'cost.lineage.base_recovery'):
            self.report()

    def test_state_change_during_report_refuses_snapshot(self):
        self.save()
        original = cost.project
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            self.state_path.write_text(json.dumps({**self.state, 'phase': 'changed'}))
            return result
        with patch.object(cost, 'project', side_effect=changed), self.assertRaisesRegex(cost.CostRefusal, 'digest'):
            cost.report(self.auth, self.manifest_path)


if __name__ == '__main__':
    unittest.main()
