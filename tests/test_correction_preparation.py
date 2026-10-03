"""Correction selection keeps the original authority and one fixed continuation."""
import copy
import json
import io
import subprocess
import sys
import urllib.error
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom
import test_issue_atom as atom_tests
import supervisor_admission as admission
import test_supervisor_authorization as authorization_tests


class CorrectionPreparationTests(unittest.TestCase):
    def setUp(self):
        fixture = authorization_tests.AuthorizationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        prepared = fixture.run_authorize()
        self.source = Path(prepared['authorization']['path'])
        self.digest = prepared['authorization']['sha256']
        self.auth = json.loads(self.source.read_text())
        self.paths = atom.artifact_paths(self.source)
        self.paths['directory'].mkdir()
        self.output = self.paths['directory'] / 'correction'
        self.publication = {
            'owner': 'soodles.candidate-publication', 'status': 'created',
            'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#131',
            'branch': 'soodles/issue-131-' + 'b' * 12,
            'head': 'b' * 40, 'tree': 'c' * 40,
            'pr': {'number': 41, 'url': 'https://github.com/ed3c/soodles/pull/41'},
            'next': None, 'authorizes_landing': False,
        }
        self.state = {
            'schema_version': 1, 'authorization_sha256': self.digest,
            'phase': 'ci', 'issue': {'number': 131}, 'publication': self.publication,
            'writes': {}, 'noodle_start': {
                'status': 'started', 'config_sha256': '1' * 64,
                'original_config': None, 'restored': True},
        }
        atom.save_json(self.paths['state'], self.state)
        self.issue = {
            'number': 131, 'title': self.auth['issue']['title'],
            'body': self.auth['issue']['body'].rstrip() + '\n\n' + atom.marker(self.digest) + '\n',
            'state': 'open', 'html_url': 'https://github.com/ed3c/soodles/issues/131',
        }
        self.provider = Mock()
        self.provider.issues.side_effect = lambda: [dict(self.issue)]
        self.provider.issue.side_effect = lambda _: dict(self.issue)
        self.provider.repository_info.return_value = {'full_name': 'ed3c/soodles', 'default_branch': 'main'}
        self.provider.base_head.return_value = self.auth['base_head']
        self.provider.pull.return_value = {
            'number': 41, 'state': 'open', 'merged': False,
            'head': {'ref': self.publication['branch'], 'sha': self.publication['head']},
            'base': {'ref': 'main'}, 'body': 'Refs ed3c/soodles#131',
        }
        self.provider.branch.return_value = {'object': {'sha': self.publication['head']}}
        self.run = {'id': 1, 'run_attempt': 1, 'head_sha': self.publication['head'], 'event': 'pull_request',
                    'path': self.auth['workflow']['path'], 'status': 'completed', 'conclusion': 'failure'}
        self.job = {'id': 10, 'run_id': 1, 'run_attempt': 1, 'head_sha': self.publication['head'], 'name': self.auth['workflow']['job'], 'status': 'completed', 'conclusion': 'failure',
                    'steps': [{'name': self.auth['workflow']['step'], 'status': 'completed',
                               'conclusion': 'failure'}]}
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}
        self.provider.job_log.side_effect = lambda job_id: {
            'job_id': job_id, 'raw': b'exact failure: assertion A\n', 'gap': None}
        owner_patch = patch.object(atom, 'verify_prior_atom', return_value={'order_id': 'original'})
        self.owner = owner_patch.start()
        self.addCleanup(owner_patch.stop)

    def prepare(self, *, provider=None, output=None):
        return admission.correction(str(self.source), self.digest, str(output or self.output),
                                    provider=self.provider if provider is None else provider)

    def test_prepares_same_issue_task_judge_carrier_and_fixed_continuation(self):
        original_auth = self.source.read_bytes()
        original_state = self.paths['state'].read_bytes()
        result = self.prepare()
        corrected = json.loads(Path(result['authorization']['path']).read_text())
        self.assertEqual(result['status'], 'prepared')
        self.assertEqual(result['next']['argv'],
                         [str(self.fixture.fixture.root / 'issue-atom'), 'run',
                          str(self.output / 'prepared/authorization.json')])
        self.assertEqual(result['next']['environment'],
                         {'SOODLES_AUTHORIZATION_SHA256': result['authorization']['sha256']})
        for key in ('task', 'base_head', 'control_root', 'carrier', 'noodle', 'landing_owner'):
            self.assertEqual(corrected[key], self.auth[key])
        self.assertEqual(corrected['issue'], {key: self.issue[key] for key in ('number', 'title', 'body')})
        self.assertEqual(atom.issue_admission.parse_contract(corrected['issue']['body']),
                         atom.issue_admission.parse_contract(self.auth['issue']['body']))
        self.assertEqual(corrected['prior_publication'], self.publication)
        self.assertEqual(corrected['prior_atom'], {'path': str(self.source), 'sha256': self.digest})
        self.owner.assert_called_once_with({k: v for k, v in corrected.items() if k != 'failure_context'})
        failure = corrected['failure_context']['data']
        self.assertEqual(failure['run'], self.run)
        self.assertEqual(failure['jobs'], {'jobs': [self.job]})
        log = failure['diagnostics'][0]['log']
        self.assertEqual(Path(log['path']).read_bytes(), b'exact failure: assertion A\n')
        self.assertEqual(log['bytes'], 27)
        self.assertNotIn('text', failure['diagnostics'][0])
        self.assertEqual(self.source.read_bytes(), original_auth)
        self.assertEqual(self.paths['state'].read_bytes(), original_state)
        self.assertFalse(result['authorizes_landing'])
        for operation in ('create_issue', 'update_issue_body', 'merge', 'close_issue'):
            getattr(self.provider, operation).assert_not_called()

    def test_revision_correction_preserves_effective_scope_and_original_lineage(self):
        body = self.issue['body'] + '\nRevision criteria apply to the successor.\n'
        original = self.source.read_bytes()
        with atom_tests.typed_revision_receipts(self.source, self.state,
                self.paths['directory'] / 'revision', body=body) as current:
            atom.save_json(self.paths['state'], self.state)
            atom.save_json(self.paths['claim'], {'head': 'retained'})
            atom.save_json(current['claim'], {'head': self.publication['head']})
            self.issue['body'] = body
            result = self.prepare()
            corrected = atom.read_json(result['authorization']['path'], 'fixture.authorization')
            self.assertEqual(corrected['issue']['body'], body)
            self.assertEqual(corrected['prior_atom'], {'path': str(self.source), 'sha256': self.digest})
            self.assertEqual(corrected['prior_publication'], self.publication)
            self.assertEqual(corrected['landing_owner'], self.auth['landing_owner'])
            self.assertEqual(self.owner.call_args.args[0]['issue']['body'], body)
            self.assertEqual(self.source.read_bytes(), original)
            self.assertEqual(atom.read_json(self.paths['claim'], 'fixture.retained'), {'head': 'retained'})

    def test_prepared_failure_reaches_envelope_and_writer_projection_as_data(self):
        head = self.auth['base_head']
        self.publication['head'] = head
        self.run['head_sha'] = self.job['head_sha'] = head
        self.provider.pull.return_value['head']['sha'] = head
        self.provider.branch.return_value['object']['sha'] = head
        atom.save_json(self.paths['state'], self.state)
        prepared = self.prepare()
        corrected = atom.read_json(prepared['authorization']['path'], 'fixture')
        root = Path(corrected['control_root'])
        name = atom.issue_admission.scoped_order_id(131, root) + '-0-execute'
        subprocess.run(['git', 'worktree', 'add', '-b', name, str(root / '.worktrees' / name), head],
                       cwd=root, check=True, capture_output=True)
        issue = {**self.issue, 'updated_at': '2026-10-02T00:00:00Z',
                 'url': 'https://api.github.com/repos/ed3c/soodles/issues/131'}
        paths = atom.artifact_paths(prepared['authorization']['path'])
        self.owner.return_value = {'prior_loop_status': 'restored'}
        envelope, digest = atom.create_envelope(corrected, issue, issue['body'], paths['envelope'],
                                                environ={'NOODLES_TOKEN_COMMAND': 'printf fixture'})
        binding = atom.issue_admission.validate_issue(issue, envelope)
        prompt = atom.issue_execution.projection(binding, digest, 'supervised')
        self.assertEqual(prompt['failure_context'], corrected['failure_context'])
        self.assertEqual(prompt['task'], self.auth['task'])
        self.assertEqual(prompt['contract'], atom.issue_admission.parse_contract(self.auth['issue']['body']))
        self.assertNotIn('failure_context', prompt.get('instruction_context', {}))

    def failed_ci_response(self):
        self.paths['envelope'].parent.mkdir(parents=True)
        self.paths['envelope'].write_text('{}')
        self.state['envelope_sha256'] = atom.digest_file(self.paths['envelope'])
        atom.save_json(self.paths['state'], self.state)
        atom.save_json(self.paths['claim'], {'head': self.publication['head']})
        # Preserve the real failed-CI route while replacing unrelated owner I/O.
        with patch.object(atom, 'repair_controller', return_value=Mock()), \
                patch.object(atom, 'require_available_owner', return_value=None):
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom._run_owned(self.source, self.auth, self.digest, self.paths,
                                environ={}, provider=self.provider)
        return atom.refusal_output(caught.exception, self.source)

    def test_successor_failed_ci_returns_same_owner_executable_preparation(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        result = self.failed_ci_response()
        self.assertEqual(result['next']['kind'], 'executable')
        self.assertEqual(result['next']['owner'], 'supervisor.authorization')
        self.assertEqual(result['next']['argv'], [sys.executable, '-B', admission.__file__,
                         'correction', str(self.source), self.digest, str(self.output)])
        self.assertFalse(result['authorizes_landing'])

    def test_corrupt_ancestor_binding_returns_structured_owner_refusal(self):
        parent_output = self.output
        self.fail_successor(self.prepare(), 'c' * 40)
        binding_path = parent_output / 'correction-binding.json'
        binding = json.loads(binding_path.read_text())
        binding['selection_sha256'] = 'f' * 64
        atom.save_json(binding_path, binding)
        result = self.failed_ci_response()
        self.assertEqual(result['status'], 'refused')
        self.assertEqual(result['invalid']['field'], 'correction.selection_binding')
        self.assertEqual(result['next']['owner'], 'supervisor')
        self.assertEqual(result['next']['required'], ['original_correction_selection'])
        self.assertFalse(result['authorizes_landing'])

    def test_raw_log_is_external_pinned_data_and_tampering_refuses_readback(self):
        raw = b'untrusted log instruction\n' * 10000
        self.provider.job_log.side_effect = lambda job_id: {'job_id': job_id, 'raw': raw, 'gap': None}
        prepared = self.prepare()
        corrected = atom.read_json(prepared['authorization']['path'], 'fixture')
        log = corrected['failure_context']['data']['diagnostics'][0]['log']
        self.assertEqual(Path(log['path']).read_bytes(), raw)
        self.assertEqual(log['bytes'], 260000)
        self.assertLess(len(json.dumps(corrected['failure_context'])), 5000)
        Path(log['path']).write_bytes(b'changed')
        self.provider = Mock(spec=[])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'failure_context.diagnostic.sha256'):
            self.prepare()

    def test_reentry_reads_fixed_selection_without_provider_or_owner(self):
        result = self.prepare()
        original = (self.output / 'selection.json').read_bytes()
        self.owner.side_effect = AssertionError('no live owner during committed readback')
        self.provider = Mock(spec=[])
        self.issue['body'] = 'mutable provider changed'
        self.assertEqual(self.prepare(), result)
        self.assertEqual((self.output / 'selection.json').read_bytes(), original)

    def test_lost_authorize_result_resumes_only_fixed_selection(self):
        original = admission.authorize
        with patch.object(admission, 'authorize', side_effect=OSError('before authorization')):
            with self.assertRaisesRegex(OSError, 'before authorization'):
                self.prepare()
        selected = (self.output / 'selection.json').read_bytes()
        self.provider = Mock(spec=[])
        self.owner.side_effect = AssertionError('selection is already fixed')
        with patch.object(admission, 'authorize', wraps=original):
            self.assertEqual(self.prepare()['status'], 'prepared')
        self.assertEqual((self.output / 'selection.json').read_bytes(), selected)

    def test_foreign_or_corrupt_output_is_preserved_without_reselection(self):
        self.output.mkdir()
        foreign = self.output / 'foreign'
        foreign.write_text('retain')
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.component'):
            self.prepare()
        self.assertEqual(foreign.read_text(), 'retain')
        self.owner.assert_not_called()
        self.provider.issue.assert_not_called()

    def test_changed_selection_refuses_even_when_provider_now_matches_it(self):
        self.prepare()
        selected = self.output / 'selection.json'
        value = json.loads(selected.read_text())
        value['task'] = 'A different task'
        selected.write_text(json.dumps(value))
        self.provider = Mock(spec=[])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.selection_binding'):
            self.prepare()
        self.assertEqual(json.loads(selected.read_text())['task'], 'A different task')

    def test_missing_carrier_does_not_select_a_replacement(self):
        Path(self.auth['noodle']['path']).unlink()
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.noodle') as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['required'], ['exact_noodle_binary'])
        self.assertFalse(self.output.exists())
        self.provider.issue.assert_not_called()

    def test_different_output_cannot_create_another_budget(self):
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.output'):
            self.prepare(output=self.output.with_name('another-correction'))
        self.assertFalse(self.output.exists())
        self.owner.assert_not_called()

    def fail_successor(self, prepared, head):
        self.source = Path(prepared['authorization']['path'])
        self.digest = prepared['authorization']['sha256']
        self.auth = json.loads(self.source.read_text())
        self.paths = atom.artifact_paths(self.source)
        self.paths['directory'].mkdir()
        self.output = self.paths['directory'] / 'correction'
        self.publication = {**self.publication, 'status': 'amended', 'head': head}
        self.state = {**copy.deepcopy(self.state), 'authorization_sha256': self.digest,
                      'publication': self.publication}
        atom.save_json(self.paths['state'], self.state)
        self.provider.pull.return_value['head']['sha'] = head
        self.provider.branch.return_value['object']['sha'] = head
        self.run.update(id=self.run['id'] + 1, head_sha=head)
        self.job.update(id=self.job['id'] + 1, run_id=self.run['id'], head_sha=head)
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}

    def test_three_distinct_corrections_keep_original_owner_then_require_reassessment(self):
        original = copy.deepcopy(self.auth)
        ledgers = []
        for head in ('c' * 40, 'd' * 40, 'e' * 40):
            self.state['repair'] = {'history': [{'status': 'confirmed', 'signal': 'stale_pr'}],
                                    'models': 1, 'started_at': 'original'}
            atom.save_json(self.paths['state'], self.state)
            ledgers.append((self.paths['state'], self.paths['state'].read_bytes()))
            prepared = self.prepare()
            self.assertEqual(self.prepare(), prepared)
            self.fail_successor(prepared, head)
            for key in ('task', 'base_head', 'control_root', 'carrier', 'noodle', 'landing_owner'):
                self.assertEqual(self.auth[key], original[key])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.limit') as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['required'], ['reassess_cause_after_three_failed_corrections'])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.provider.job_log.call_count, 3)
        for path, raw in ledgers:
            self.assertEqual(path.read_bytes(), raw)

    def test_pending_third_correction_is_not_a_third_confirmed_failure(self):
        for head in ('c' * 40, 'd' * 40, 'e' * 40):
            self.fail_successor(self.prepare(), head)
        self.run['status'] = 'in_progress'
        self.run['conclusion'] = None
        for _ in range(2):
            with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior_runtime') as caught:
                self.prepare()
            self.assertNotIn('reassess_cause_after_three_failed_corrections', caught.exception.next['required'])
            self.assertFalse(self.output.exists())
        self.assertEqual(self.provider.job_log.call_count, 3)

    def test_repeated_failed_head_cannot_prepare_successor(self):
        self.fail_successor(self.prepare(), 'b' * 40)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.head'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_unknown_ancestor_effect_blocks_successor_without_provider_reads(self):
        ancestor_paths = self.paths
        self.fail_successor(self.prepare(), 'c' * 40)
        ancestor = atom.read_json(ancestor_paths['state'], 'fixture')
        ancestor['writes']['merge'] = {'status': 'offered'}
        atom.save_json(ancestor_paths['state'], ancestor)
        self.provider.reset_mock()
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.effects'):
            self.prepare()
        self.provider.issue.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_changed_task_judge_scope_and_parent_publication_refuse(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        original = copy.deepcopy(self.auth)
        for field in ('task', 'landing_owner', 'contract', 'prior_publication', 'failure_context'):
            with self.subTest(field=field):
                value = copy.deepcopy(original)
                if field == 'task':
                    value['task'] += ' changed scope'
                elif field == 'landing_owner':
                    value[field]['verifier_sha256'] = 'f' * 64
                elif field == 'contract':
                    contract = atom.issue_admission.parse_contract(value['issue']['body'])
                    changed = copy.deepcopy(contract)
                    changed['behavior'].append('unadmitted behavior')
                    value['issue']['body'] = value['issue']['body'].replace(
                        json.dumps(contract), json.dumps(changed))
                    self.assertNotEqual(value['issue']['body'], original['issue']['body'])
                elif field == 'prior_publication':
                    value[field]['pr']['number'] = 99
                else:
                    value[field]['data']['run']['head_sha'] = 'f' * 40
                    value[field]['sha256'] = atom.issue_admission.failure_digest(value[field]['data'])
                atom.save_json(self.source, value)
                digest = atom.digest_file(self.source)
                state = {**self.state, 'authorization_sha256': digest}
                with self.assertRaises((atom.AtomRefusal, admission.AdmissionRefusal)):
                    atom.validate_correction_lineage(value, {'path': str(self.source), 'sha256': digest}, state)
        atom.save_json(self.source, original)

    def test_legacy_external_predecessor_does_not_reset_history(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        del self.auth['failure_context']
        atom.save_json(self.source, self.auth)
        self.digest = atom.digest_file(self.source)
        self.state['authorization_sha256'] = self.digest
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.external'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_cyclic_or_broken_parent_reference_refuses(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        self.auth['prior_atom'] = {'path': str(self.source), 'sha256': self.digest}
        atom.save_json(self.source, self.auth)
        self.digest = atom.digest_file(self.source)
        self.state['authorization_sha256'] = self.digest
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior_atom.sha256'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_missing_log_is_explicit_data_and_does_not_change_task(self):
        self.provider.job_log.return_value = None
        self.provider.job_log.side_effect = lambda job_id: {
            'job_id': job_id, 'raw': None, 'gap': 'log_http_status_404'}
        prepared = self.prepare()
        authorization = atom.read_json(prepared['authorization']['path'], 'fixture')
        self.assertEqual(authorization['task'], self.auth['task'])
        self.assertEqual(authorization['failure_context']['data']['diagnostics'][0]['gap'], 'log_http_status_404')
        self.assertEqual(self.prepare(), prepared)
        self.provider.job_log.assert_called_once_with(10)

    def test_wrong_run_job_or_diagnostic_identity_is_not_admitted(self):
        original_run, original_job = copy.deepcopy(self.run), copy.deepcopy(self.job)
        for field in ('run_attempt', 'job_run', 'job_attempt', 'job_head', 'log_job'):
            with self.subTest(field=field):
                if field == 'run_attempt':
                    self.run['run_attempt'] = 0
                elif field == 'job_run':
                    self.job['run_id'] = 999
                elif field == 'job_attempt':
                    self.job['run_attempt'] = 2
                elif field == 'job_head':
                    self.job['head_sha'] = 'f' * 40
                else:
                    self.provider.job_log.side_effect = lambda job_id: {
                        'job_id': 999, 'raw': b'changed', 'gap': None}
                with self.assertRaises(admission.AdmissionRefusal):
                    self.prepare()
                self.assertFalse(self.output.exists())
                self.run.clear()
                self.run.update(original_run)
                self.job.clear()
                self.job.update(original_job)

    def test_unresolved_original_effect_refuses_without_new_preparation(self):
        self.state['repair'] = {'history': [{'signal': 'stale_pr', 'status': 'intent'}]}
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.repair_history'):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.provider.issue.assert_not_called()

    def test_unknown_original_owner_is_not_replaced(self):
        self.owner.side_effect = atom.AtomRefusal('amendment.prior_loop.group', 'present',
                                                'quiescent_noodle_owner', owner='Noodle')
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['owner'], 'Noodle')
        self.assertEqual(caught.exception.next['required'], ['quiescent_noodle_owner'])
        self.provider.issue.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_provider_base_drift_and_nonfailed_ci_leave_no_selection(self):
        for kind in ('base', 'head', 'running', 'success', 'cancelled', 'missing'):
            with self.subTest(kind=kind):
                base, pull = self.provider.base_head.return_value, copy.deepcopy(self.provider.pull.return_value)
                run, job = copy.deepcopy(self.run), copy.deepcopy(self.job)
                if kind == 'base':
                    self.provider.base_head.return_value = 'f' * 40
                elif kind == 'head':
                    self.provider.pull.return_value['head']['sha'] = 'f' * 40
                elif kind == 'running':
                    self.run['status'] = 'in_progress'
                elif kind == 'missing':
                    self.provider.workflow_runs.return_value = {'workflow_runs': []}
                else:
                    self.run['conclusion'] = self.job['conclusion'] = self.job['steps'][0]['conclusion'] = kind
                with self.assertRaises(admission.AdmissionRefusal):
                    self.prepare()
                self.assertFalse(self.output.exists())
                self.provider.base_head.return_value = base
                self.provider.pull.return_value = pull
                self.run.clear()
                self.run.update(run)
                self.job.clear()
                self.job.update(job)
                self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}

    def test_skipped_acceptance_after_exact_runtime_failure_is_supported(self):
        self.job['steps'][0]['conclusion'] = 'skipped'
        self.job['steps'].insert(0, {'name': 'Prepare runtime', 'status': 'completed', 'conclusion': 'failure'})
        self.assertEqual(self.prepare()['status'], 'prepared')

    def test_host_credential_supplier_requests_only_read_capabilities(self):
        with patch.object(atom.provider_credential, 'resolve_host_environment', return_value={'selected': 'host'}) as host, \
                patch.object(atom.provider_credential, 'supply_token', return_value='fixture-token') as token, \
                patch.object(atom, 'GitHubProvider', return_value=self.provider):
            result = admission.correction(str(self.source), self.digest, str(self.output), environ={})
        self.assertEqual(result['status'], 'prepared')
        host.assert_called_once_with(Path(self.auth['control_root']), environ={})
        token.assert_called_once_with(self.auth['repository'],
            {'contents': 'read', 'issues': 'read', 'pull_requests': 'read', 'actions': 'read'},
            environ={'selected': 'host'})


class DiagnosticTransportTests(unittest.TestCase):
    def response(self, url, code, raw=b'', headers=None):
        value = io.BytesIO(raw)
        value.url, value.code, value.headers = url, code, headers or {}
        return value

    def test_signed_redirect_receives_no_token_and_preserves_exact_log(self):
        provider = atom.GitHubProvider('ed3c/soodles', token='fixture-secret')
        url = provider.api + '/actions/jobs/10/logs'
        redirect = 'https://logs.example.invalid/signed?signature=opaque'
        opener = Mock()
        opener.open.side_effect = [self.response(url, 302, headers={'Location': redirect}),
                                  self.response(redirect, 200, b'raw failure\n')]
        with patch.object(atom.urllib.request, 'build_opener', return_value=opener) as build:
            result = provider.job_log(10)
        self.assertIsInstance(build.call_args.args[0], atom.candidate_publication.NoRedirect)
        requests = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer fixture-secret')
        self.assertIsNone(requests[1].get_header('Authorization'))
        self.assertEqual(requests[1].full_url, redirect)
        self.assertEqual(result, {'job_id': 10, 'raw': b'raw failure\n', 'gap': None})

    def test_missing_or_unsafe_logs_are_explicit_gaps_without_redirect_effect(self):
        provider = atom.GitHubProvider('ed3c/soodles', token='fixture-secret')
        url = provider.api + '/actions/jobs/10/logs'
        for code, location, expected in ((404, None, 'log_http_status_404'),
                                        (302, 'http://unsafe.invalid', 'invalid_log_redirect')):
            with self.subTest(code=code):
                opener = Mock()
                opener.open.return_value = self.response(url, code, headers={'Location': location})
                with patch.object(atom.urllib.request, 'build_opener', return_value=opener):
                    result = provider.job_log(10)
                self.assertEqual(result['gap'], expected)
                self.assertIsNone(result['raw'])
                opener.open.assert_called_once()


if __name__ == '__main__':
    unittest.main()
