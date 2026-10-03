"""Runtime caller binding on small Git subjects and the saved workflow programs."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

import comparison_fixture
import issue_admission as admission
import runtime_candidate
import test_issue_admission
import test_manager


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ed3c/soodles'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def issue_body(contract):
    return ('<!-- soodles:execution-v1 -->\n```json\n' + json.dumps(contract)
            + '\n```\n<!-- /soodles:execution-v1 -->\n')


def workflow_program(step_name, command):
    workflow = (ROOT / '.github/workflows/runtime.yml').read_text()
    step = workflow.split('      - name: ' + step_name + '\n', 1)[1].split('      - name:', 1)[0]
    source = step.split(command + " <<'PY'\n", 1)[1].split('\n          PY', 1)[0]
    return textwrap.dedent(source) + '\n'


class CandidateFixture:
    def __init__(self, root):
        self.root = root
        root.mkdir()
        self.git('init', '-b', 'main')
        (root / 'tests').mkdir()
        (root / 'tests/test_candidate_verification.py').write_bytes(
            (ROOT / 'tests/test_candidate_verification.py').read_bytes())
        (root / 'policy.md').write_bytes(b'baseline\n')
        (root / 'upstream-only.py').write_bytes(b'original upstream\n')
        self.event = self.commit('Record PR event base')
        (root / 'upstream-only.py').write_bytes(b'new upstream\n')
        self.base = self.commit('Record admitted upstream base')
        (root / 'policy.md').write_bytes(b'treatment\n')
        (root / 'docs').mkdir()
        (root / 'docs/control.md').write_bytes(b'frozen control\n')
        self.manifest = {
            'schema': 1,
            'issue': {'repository': REPOSITORY, 'number': 18},
            'instructions': [{'path': 'policy.md', 'baseline_sha256': sha(b'baseline\n'),
                              'treatment_sha256': sha(b'treatment\n')}],
            'artifacts': [{'path': 'docs/control.md', 'role': 'observer',
                           'sha256': sha(b'frozen control\n')}],
            'owner': {'name': 'Soodles Issue admission',
                      'tool': 'issue_admission.validate_delivery_paths',
                      'authorization': REPOSITORY + '#18'},
            'authorizes_landing': False,
        }
        (root / 'docs/runtime-base.json').write_text(json.dumps(self.manifest))
        self.head = self.commit('Bind candidate evidence to admitted base')
        self.issue, _ = test_issue_admission.issue_fixture()
        self.contract = admission.parse_contract(self.issue['body'])
        paths = ['policy.md', 'docs/control.md', 'docs/runtime-base.json']
        self.contract.update(schema=3, base_head=self.base, write_paths=paths,
                             required_paths=paths, evidence_manifest='docs/runtime-base.json',
                             frozen_paths=[{'path': 'docs/control.md', 'revision': 'head',
                                            'sha256': sha(b'frozen control\n')}])
        self.issue['body'] = issue_body(self.contract)

    def git(self, *args):
        return subprocess.check_output(
            ['git', '-c', 'user.name=Runtime Fixture', '-c',
             'user.email=fixture@example.invalid', *args],
            cwd=self.root, text=True, stderr=subprocess.PIPE).strip()

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def detached_commit(self, revision, *, parent=None):
        args = ['commit-tree', self.git('rev-parse', revision + '^{tree}')]
        if parent is not None:
            args.extend(['-p', parent])
        return self.git(*args, '-m', 'Create isolated lineage control')

    def readback(self, contract=None):
        return {**self.issue, 'body': issue_body(self.contract if contract is None else contract)}

    def verify(self, event=None, head=None, readback=None):
        return runtime_candidate.verify_pull_request(
            self.root, self.event if event is None else event,
            self.head if head is None else head,
            self.readback() if readback is None else readback,
            issue_number=18, repository=REPOSITORY)


class RuntimeBaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = CandidateFixture(Path(self.temp.name) / 'candidate')

    def assert_refused(self, *, field=None, **kwargs):
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.fixture.verify(**kwargs)
        if field is not None:
            self.assertEqual(caught.exception.invalid['field'], field)
        self.assertTrue(caught.exception.next['owner'])
        self.assertTrue(caught.exception.next['required'])
        return caught.exception

    def test_older_and_equal_event_base_use_the_admitted_candidate_diff(self):
        fixture = self.fixture
        for event in (fixture.event, fixture.base):
            with self.subTest(event=event):
                result = fixture.verify(event=event)
                self.assertEqual(result['base_head'], fixture.base)
                self.assertEqual(result['head'], fixture.head)
                self.assertEqual(result['event_base'], event)
                self.assertEqual(result['classification'], 'VERIFIED')
                self.assertEqual(result['changed_paths'], sorted(fixture.contract['required_paths']))
                self.assertNotIn('upstream-only.py', result['changed_paths'])
                self.assertFalse(result['authorizes_landing'])
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            admission.verify_candidate(fixture.root, fixture.event, fixture.head, fixture.readback())
        self.assertEqual(caught.exception.invalid['field'], 'candidate.base')

    def test_future_and_unrelated_event_bases_refuse(self):
        fixture = self.fixture
        future = fixture.detached_commit(fixture.head, parent=fixture.head)
        unrelated = fixture.detached_commit(fixture.event)
        for event in (fixture.head, future, unrelated):
            with self.subTest(event=event):
                self.assert_refused(event=event, field='runtime.event_base_ancestry')

    def test_missing_malformed_and_noncommit_event_bases_refuse(self):
        fixture = self.fixture
        tree = fixture.git('rev-parse', fixture.base + '^{tree}')
        blob = fixture.git('rev-parse', fixture.base + ':policy.md')
        for event in ('', 'a' * 39, 'f' * 40, '0' * 40, tree, blob):
            with self.subTest(event=event):
                self.assert_refused(event=event, field='runtime.event_base')

    def test_invalid_admitted_base_and_missing_contract_base_refuse(self):
        fixture = self.fixture
        for base in ('', 'a' * 39, 'f' * 40, fixture.git('rev-parse', fixture.base + '^{tree}')):
            with self.subTest(base=base):
                contract = {**fixture.contract, 'base_head': base}
                self.assert_refused(readback=fixture.readback(contract))
        contract = dict(fixture.contract)
        del contract['base_head']
        self.assert_refused(readback=fixture.readback(contract))

    def test_head_must_include_admitted_base_and_match_checkout(self):
        fixture = self.fixture
        self.assert_refused(head=fixture.event, field='runtime.admitted_base_ancestry')
        unrelated = fixture.detached_commit(fixture.event)
        self.assert_refused(head=unrelated, field='runtime.admitted_base_ancestry')
        self.assert_refused(head=fixture.base, field='candidate.checkout_head')
        for head in ('a' * 39, 'f' * 40, fixture.git('rev-parse', fixture.head + '^{tree}')):
            with self.subTest(head=head):
                self.assert_refused(head=head, field='runtime.head')

    def test_fresh_issue_identity_and_reader_wrapper_remain_bound(self):
        fixture = self.fixture
        issue = fixture.readback()
        for update in ({'number': 19}, {'number': True},
                       {'url': 'https://api.github.com/repos/ed3c/noodle/issues/18'},
                       {'html_url': 'https://github.com/ed3c/noodle/issues/18'},
                       {'state': 'closed'}, {'pull_request': {}}):
            with self.subTest(update=update):
                self.assert_refused(readback={**issue, **update})
        wrapper = {'owner': 'github.issue', 'status': 'read', 'next': None,
                   'issue': issue, 'authorizes_landing': False}
        self.assertEqual(fixture.verify(readback=wrapper)['base_head'], fixture.base)
        for update in ({'status': 'pending'}, {'next': {'kind': 'input'}},
                       {'authorizes_landing': True}, {'issue': None}):
            with self.subTest(update=update):
                self.assert_refused(readback={**wrapper, **update})

    def test_valid_lineage_does_not_bypass_frozen_artifacts_or_write_scope(self):
        fixture = self.fixture
        contract = copy.deepcopy(fixture.contract)
        contract['frozen_paths'][0]['sha256'] = '0' * 64
        self.assert_refused(readback=fixture.readback(contract), field='candidate.frozen_path.sha256')
        (fixture.root / 'outside.md').write_text('not admitted\n')
        fixture.head = fixture.commit('Plant an out of scope candidate path')
        self.assert_refused(field='candidate.outside_write_paths')

    def test_valid_lineage_does_not_bypass_artifact_bytes(self):
        fixture = self.fixture
        (fixture.root / 'docs/control.md').write_bytes(b'changed control\n')
        fixture.head = fixture.commit('Plant changed artifact bytes')
        self.assert_refused(field='candidate.artifact.sha256')

    def test_schema_two_preserves_base_without_new_ancestry_requirements(self):
        fixture = self.fixture
        contract = {key: value for key, value in fixture.contract.items()
                    if key not in ('base_head', 'frozen_paths')}
        contract['schema'] = 2
        unrelated = fixture.detached_commit(fixture.base)
        result = fixture.verify(event=unrelated, readback=fixture.readback(contract))
        self.assertEqual(result['base_head'], unrelated)
        self.assertEqual(result['classification'], 'VERIFIED')
        self.assertFalse(result['authorizes_landing'])


class RuntimeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.fixture = CandidateFixture(self.directory / 'candidate')
        self.runtime = self.directory / 'runner' / 'soodles-runtime'
        self.runtime.mkdir(parents=True)
        self.output = self.directory / 'github-output'
        self.output.write_text('')

    def execute(self, program, *, root=None, issue_number=None, **environment):
        env = {**os.environ, 'PYTHONPATH': str(ROOT),
               'RUNNER_TEMP': str(self.runtime.parent), 'GITHUB_OUTPUT': str(self.output),
               'GITHUB_EVENT_NAME': 'pull_request', 'GITHUB_REPOSITORY': REPOSITORY,
               'BASE_SHA': self.fixture.event, 'HEAD_SHA': self.fixture.head,
               **environment}
        args = [sys.executable, '-B', '-c', program]
        if issue_number is not None:
            args.append(str(issue_number))
        return subprocess.run(args, cwd=self.fixture.root if root is None else root,
                              env=env, capture_output=True, text=True, timeout=40)

    def candidate_program(self):
        return workflow_program('Verify exact candidate evidence from fresh Issue readback',
                                'python3 -B - "$issue"')

    def scope_program(self):
        return workflow_program('Request verification scope from Test Manager', 'python3 -B -')

    def candidate(self, *, readback=None, **environment):
        issue = self.fixture.readback() if readback is None else readback
        (self.runtime / 'issue-readback.json').write_text(json.dumps(issue))
        return self.execute(self.candidate_program(), issue_number=18, **environment)

    def test_saved_candidate_and_scope_programs_share_verified_base(self):
        result = self.candidate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('base=' + self.fixture.base + '\n', self.output.read_text())
        candidate_outputs = dict(line.split('=', 1) for line in self.output.read_text().splitlines())
        receipt = json.loads((self.runtime / 'candidate-evidence.json').read_text())
        self.assertEqual(receipt['base_head'], self.fixture.base)
        self.output.write_text('')
        scope = self.execute(self.scope_program(), VERIFIED_PR_BASE=candidate_outputs['base'],
                             DISPATCH_BASE=self.fixture.event, REQUEST_REASON='')
        self.assertEqual(scope.returncode, 0, scope.stdout + scope.stderr)
        selection = json.loads((self.runtime / 'selection.json').read_text())
        self.assertEqual(selection['base'], self.fixture.base)
        self.assertEqual(selection['request']['base'], self.fixture.base)
        self.assertNotIn('upstream-only.py', selection['changed_paths'])
        self.assertIn('base=' + self.fixture.base + '\n', self.output.read_text())
        workflow = (ROOT / '.github/workflows/runtime.yml').read_text()
        candidate = workflow.split('      - name: Verify exact candidate evidence from fresh Issue readback\n', 1)[1].split('      - name:', 1)[0]
        self.assertIn('        id: candidate\n', candidate)
        scope_step = workflow.split('      - name: Request verification scope from Test Manager\n', 1)[1].split('      - name:', 1)[0]
        self.assertIn('VERIFIED_PR_BASE: ${{ steps.candidate.outputs.base }}', scope_step)
        self.assertIn('DISPATCH_BASE: ${{ inputs.base }}', scope_step)
        self.assertIn('REQUEST_REASON: ${{ inputs.reason }}', scope_step)
        acceptance = workflow.split('      - name: Canonical acceptance on the exact candidate head\n', 1)[1]
        self.assertIn('BASE_SHA: ${{ steps.scope.outputs.base }}', acceptance)

    def test_saved_candidate_refusal_preserves_structured_receipt_without_output(self):
        result = self.candidate(BASE_SHA=self.fixture.head)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), '')
        receipt = json.loads((self.runtime / 'candidate-evidence.json').read_text())
        self.assertEqual(receipt['invalid']['field'], 'runtime.event_base_ancestry')
        self.assertTrue(receipt['next']['owner'])
        self.assertFalse(receipt['authorizes_landing'])

    def test_scope_dispatch_preserves_its_explicit_base_and_reason(self):
        reason = 'Inspect the selected runtime behavior'
        result = self.execute(self.scope_program(), GITHUB_EVENT_NAME='workflow_dispatch',
                              DISPATCH_BASE=self.fixture.base, VERIFIED_PR_BASE=self.fixture.event,
                              REQUEST_REASON=reason)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        selection = json.loads((self.runtime / 'selection.json').read_text())
        self.assertEqual(selection['request']['base'], self.fixture.base)
        self.assertEqual(selection['request']['reason'], reason)
        self.assertEqual(selection['request']['event'], 'workflow_dispatch')

    def test_scope_refuses_missing_verified_pr_base_instead_of_falling_back(self):
        result = self.execute(self.scope_program(), VERIFIED_PR_BASE='',
                              DISPATCH_BASE=self.fixture.base, REQUEST_REASON='')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), '')

    def test_schema_four_runs_saved_caller_with_real_comparison_and_manifest(self):
        # Synthetic deterministic controls are not new Agent behavior evidence.
        value = comparison_fixture.build(ROOT, self.directory / 'comparison')
        issue = json.loads(Path(value['issue']).read_text())
        (self.runtime / 'issue-readback.json').write_text(json.dumps(issue))
        result = self.execute(self.candidate_program(), root=value['root'], issue_number=1,
                              BASE_SHA=value['base'], HEAD_SHA=value['head'])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads((self.runtime / 'candidate-evidence.json').read_text())
        self.assertEqual(receipt['classification'], 'VERIFIED')
        self.assertEqual(receipt['comparison']['decision'], 'ADMIT_IMPROVEMENT')
        self.assertEqual(receipt['base_head'], value['base'])
        self.assertEqual(receipt['head'], value['head'])
        self.assertFalse(receipt['authorizes_landing'])
        self.assertIn('base=' + value['base'] + '\n', self.output.read_text())


class RuntimeScopeRoutingTests(unittest.TestCase):
    def test_test_manager_routes_both_caller_files_to_runtime_controls(self):
        for path in ('runtime_candidate.py', '.github/workflows/runtime.yml'):
            with self.subTest(path=path):
                decision = test_manager.select(ROOT, [path])
                self.assertEqual(decision['status'], 'ready')
                self.assertIn('test_runtime_base', decision['modules'])
                self.assertEqual(decision['physical'], [])


if __name__ == '__main__':
    unittest.main()
