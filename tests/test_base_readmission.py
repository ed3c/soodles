"""Current base continuation: provider effects, lost responses and instruction identity."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import issue_atom as atom


class BaseReadmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Readmission fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'policy.md').write_text('old instructions\n')
        self.git('add', '.')
        self.git('commit', '-m', 'old base')
        self.old = self.git('rev-parse', 'HEAD')
        old_hash = atom.digest_file(self.root / 'policy.md')
        (self.root / 'policy.md').write_text('current instructions\n')
        self.git('commit', '-am', 'provider advances')
        self.base = self.git('rev-parse', 'HEAD')
        new_hash = atom.digest_file(self.root / 'policy.md')
        self.contract = {
            'schema': 3, **{key: 'fixture' for key in (
                'trigger', 'source', 'owner', 'acceptance', 'delivery',
                'reconciliation', 'feature_scope')},
            **{key: ['fixture'] for key in ('changes', 'behavior', 'defect_controls', 'non_cases')},
            'write_paths': ['policy.md', 'evidence.json'],
            'required_paths': ['policy.md', 'evidence.json'], 'evidence_manifest': 'evidence.json',
            'dependencies': [], 'base_head': self.old,
            'frozen_paths': [{'path': 'policy.md', 'revision': 'base', 'sha256': old_hash}],
        }
        new = {**self.contract, 'base_head': self.base,
               'frozen_paths': [{'path': 'policy.md', 'revision': 'base', 'sha256': new_hash}]}
        self.auth = {
            'schema_version': 3, 'repository': 'ed3c/soodles',
            'control_root': str(self.root), 'base_head': self.base,
            'issue': {'number': 204, 'title': 'Same task', 'body': self.body(new)},
            'prior_publication': {'head': self.old, 'branch': 'soodles/issue-204', 'pr': {'number': 205}},
            'workflow': {'path': '.github/workflows/runtime.yml', 'job': 'runtime', 'step': 'acceptance'},
            'instruction_pins': [{'path': 'policy.md', 'sha256': new_hash}],
        }
        self.value = {'number': 204, 'title': 'Same task', 'body': self.body(self.contract),
                      'state': 'open', 'html_url': 'https://github.com/ed3c/soodles/issues/204'}
        self.paths = atom.artifact_paths(self.root / 'authorization.json')
        self.state = {'phase': 'issue', 'writes': {}, 'issue': None, 'publication': None}
        self.provider = Mock()
        self.provider.issue.side_effect = lambda _: dict(self.value)
        self.provider.repository_info.return_value = {'full_name': 'ed3c/soodles', 'default_branch': 'main'}
        self.provider.base_head.return_value = self.base
        self.provider.pull.return_value = {
            'number': 205, 'state': 'open', 'merged': False,
            'head': {'ref': 'soodles/issue-204', 'sha': self.old},
            'base': {'ref': 'main'}, 'body': 'Refs ed3c/soodles#204'}
        self.provider.branch.return_value = {'object': {'sha': self.old}}
        self.run = {'id': 1, 'head_sha': self.old, 'event': 'pull_request',
                    'path': self.auth['workflow']['path'], 'status': 'completed', 'conclusion': 'failure'}
        self.job = {'name': 'runtime', 'status': 'completed', 'conclusion': 'failure',
                    'steps': [{'name': 'acceptance', 'status': 'completed', 'conclusion': 'skipped'}]}
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}
        self.effect = True
        self.unknown = False
        self.provider.update_issue_body.side_effect = self.update

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE, text=True).strip()

    def body(self, contract):
        return ('Original scope.\n<!-- soodles:execution-v1 -->\n```json\n' + json.dumps(contract)
                + '\n```\n<!-- /soodles:execution-v1 -->\n<!-- original-marker -->\n')

    def update(self, number, body):
        self.assertEqual(number, 204)
        persisted = json.loads(self.paths['state'].read_text())
        self.assertEqual(persisted['writes']['issue_base']['status'], 'offered')
        if self.effect:
            self.value['body'] = body
        if self.unknown:
            raise atom.MutationUnknown('response lost')

    def advance(self):
        atom.readmit_issue_base(self.provider, self.auth, self.state, self.paths)

    def test_known_success_is_adopted_from_readback_without_another_patch(self):
        self.job['steps'][0]['conclusion'] = 'failure'
        self.advance()
        self.assertEqual(self.value['body'], self.auth['issue']['body'])
        self.assertEqual(self.state['writes']['issue_base']['status'], 'observed')
        self.advance()
        self.provider.update_issue_body.assert_called_once()

    def test_descendant_base_rebinds_same_issue_once_and_adopts_lost_response(self):
        self.unknown = True
        self.advance()
        self.assertEqual(self.value['body'], self.auth['issue']['body'])
        self.assertEqual(self.state['writes']['issue_base']['status'], 'observed')
        self.assertEqual(self.state['writes']['issue_base']['previous_base'], self.old)
        self.advance()
        self.provider.update_issue_body.assert_called_once()
        self.assertEqual(json.loads(self.paths['state'].read_text()), self.state)

    def test_unknown_without_effect_never_reoffers_even_after_restart(self):
        self.unknown, self.effect = True, False
        for _ in range(2):
            with self.assertRaisesRegex(atom.AtomRefusal, 'readmission.issue.outcome'):
                self.advance()
            self.state = json.loads(self.paths['state'].read_text())
        self.provider.update_issue_body.assert_called_once()
        self.value['body'] = self.auth['issue']['body']
        self.advance()
        self.assertEqual(self.state['writes']['issue_base']['status'], 'observed')
        self.provider.update_issue_body.assert_called_once()

    def test_scope_prose_and_original_pin_changes_refuse_before_write(self):
        original_auth, original_value = copy.deepcopy(self.auth), dict(self.value)
        for kind in ('scope', 'prose', 'pin', 'ancestry'):
            with self.subTest(kind=kind):
                self.auth, self.value = copy.deepcopy(original_auth), dict(original_value)
                if kind == 'prose':
                    self.auth['issue']['body'] += 'Another task\n'
                elif kind == 'scope':
                    contract = atom.issue_admission.parse_contract(self.auth['issue']['body'])
                    contract['changes'].append('Another task')
                    self.auth['issue']['body'] = self.body(contract)
                else:
                    contract = copy.deepcopy(self.contract)
                    if kind == 'pin':
                        contract['frozen_paths'][0]['sha256'] = '0' * 64
                    else:
                        contract['base_head'] = 'f' * 40
                    self.value['body'] = self.body(contract)
                with self.assertRaises(atom.AtomRefusal):
                    self.advance()
                self.provider.update_issue_body.assert_not_called()
                self.assertEqual(self.state['writes'], {})

    def test_provider_drift_and_nonterminal_checks_refuse_before_write(self):
        for kind in ('base', 'head', 'success', 'cancelled', 'running', 'step_running', 'missing_step'):
            with self.subTest(kind=kind):
                base = self.provider.base_head.return_value
                pull = copy.deepcopy(self.provider.pull.return_value)
                run, job = copy.deepcopy(self.run), copy.deepcopy(self.job)
                if kind == 'base':
                    self.provider.base_head.return_value = 'f' * 40
                elif kind == 'head':
                    self.provider.pull.return_value['head']['sha'] = 'f' * 40
                elif kind in ('success', 'cancelled'):
                    self.run['conclusion'] = self.job['conclusion'] = self.job['steps'][0]['conclusion'] = kind
                elif kind == 'running':
                    self.run['status'] = 'in_progress'
                elif kind == 'step_running':
                    self.job['steps'][0]['status'] = 'in_progress'
                else:
                    self.job['steps'] = []
                with self.assertRaises(atom.AtomRefusal):
                    self.advance()
                self.provider.update_issue_body.assert_not_called()
                self.provider.base_head.return_value = base
                self.provider.pull.return_value = pull
                self.run.clear(); self.run.update(run)
                self.job.clear(); self.job.update(job)

    def test_same_root_correction_does_not_patch_issue(self):
        self.auth['prior_atom'] = {'path': '/original/authorization.json'}
        self.advance()
        self.provider.issue.assert_not_called()
        self.provider.update_issue_body.assert_not_called()

    def test_wrong_issue_identity_refuses_before_write(self):
        original = dict(self.value)
        for field, value in (('number', 999), ('title', 'Different task'),
                             ('html_url', 'https://github.com/ed3c/soodles/issues/999'),
                             ('pull_request', {})):
            with self.subTest(field=field):
                self.value = {**original, field: value}
                with self.assertRaisesRegex(atom.AtomRefusal, 'readmission.issue.identity'):
                    self.advance()
                self.provider.update_issue_body.assert_not_called()
                self.assertEqual(self.state['writes'], {})

    def test_fresh_root_instructions_belong_to_base_and_same_root_to_prior_head(self):
        self.assertEqual(atom.selected_instruction_pins(self.auth), self.auth['instruction_pins'])
        self.auth['prior_atom'] = {'path': '/original/authorization.json'}
        with self.assertRaisesRegex(atom.AtomRefusal, 'instruction_context.files.sha256'):
            atom.selected_instruction_pins(self.auth)
        self.auth['instruction_pins'][0]['sha256'] = self.contract['frozen_paths'][0]['sha256']
        self.assertEqual(atom.selected_instruction_pins(self.auth), self.auth['instruction_pins'])

    def test_authorization_producer_pins_fresh_root_instead_of_prior_candidate(self):
        import test_supervisor_authorization
        fixture = test_supervisor_authorization.AuthorizationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.selection['issue']['number'] = 128
        instruction_path = '.agents/skills/execute/SKILL.md'
        fixture.selection['instruction_paths'] = [instruction_path]
        fixture.selection['prior_publication'] = {
            'owner': 'soodles.candidate-publication', 'status': 'created',
            'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#128',
            'branch': 'soodles/issue-128-' + 'b' * 12, 'head': 'b' * 40, 'tree': 'c' * 40,
            'pr': {'number': 41, 'url': 'https://github.com/ed3c/soodles/pull/41'},
            'next': None, 'authorizes_landing': False}
        fixture.path.write_text(json.dumps(fixture.selection))
        fixture.digest = atom.digest_file(fixture.path)
        prepared = fixture.run_authorize()
        auth, _ = atom.validate_authorization(prepared['authorization']['path'], prepared['authorization']['sha256'])
        self.assertEqual(auth['instruction_pins'][0]['sha256'],
                         atom.digest_file(fixture.fixture.root / instruction_path))
        self.assertNotIn('prior_atom', auth)
