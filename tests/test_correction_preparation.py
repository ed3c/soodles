"""Correction selection keeps the original authority and one fixed continuation."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom
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
        self.run = {'id': 1, 'head_sha': self.publication['head'], 'event': 'pull_request',
                    'path': self.auth['workflow']['path'], 'status': 'completed', 'conclusion': 'failure'}
        self.job = {'name': self.auth['workflow']['job'], 'status': 'completed', 'conclusion': 'failure',
                    'steps': [{'name': self.auth['workflow']['step'], 'status': 'completed',
                               'conclusion': 'failure'}]}
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}
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
        self.owner.assert_called_once_with(corrected)
        self.assertEqual(self.source.read_bytes(), original_auth)
        self.assertEqual(self.paths['state'].read_bytes(), original_state)
        self.assertFalse(result['authorizes_landing'])
        for operation in ('create_issue', 'update_issue_body', 'merge', 'close_issue'):
            getattr(self.provider, operation).assert_not_called()

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

    def test_successor_authorization_cannot_derive_another_correction(self):
        first = self.prepare()
        path, digest = first['authorization']['path'], first['authorization']['sha256']
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage') as caught:
            admission.correction(path, digest, str(atom.artifact_paths(path)['directory'] / 'correction'),
                                 provider=self.provider)
        self.assertEqual(caught.exception.next['required'],
                         ['original_owner_after_one_automatic_correction'])

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


if __name__ == '__main__':
    unittest.main()
