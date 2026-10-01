"""Current candidate byte binding on disposable Git commits, without historical heads."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import issue_admission as admission
from test_issue_admission import issue_fixture


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CandidateVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.git('init', '-b', 'main')
        (self.root / 'policy.md').write_bytes(b'baseline\n')
        self.base = self.commit()
        (self.root / 'policy.md').write_bytes(b'treatment\n')
        (self.root / 'observer.py').write_bytes(b'externally selected observer\n')
        self.manifest = {
            'schema': 1, 'issue': {'repository': 'ed3c/soodles', 'number': 18},
            'instructions': [{'path': 'policy.md', 'baseline_sha256': digest(b'baseline\n'),
                              'treatment_sha256': digest(b'treatment\n')}],
            'artifacts': [{'path': 'observer.py', 'role': 'observer',
                           'sha256': digest((self.root / 'observer.py').read_bytes())}],
            'owner': {'name': 'Soodles Issue admission',
                      'tool': 'issue_admission.validate_delivery_paths',
                      'authorization': 'ed3c/soodles#18'},
            'authorizes_landing': False,
        }
        self.issue, _ = issue_fixture()
        self.contract = admission.parse_contract(self.issue['body'])
        paths = ['policy.md', 'observer.py', 'manifest.json']
        self.contract.update(schema=3, base_head=self.base, write_paths=paths, required_paths=paths,
                             evidence_manifest='manifest.json', frozen_paths=[{
                                 'path': 'observer.py', 'revision': 'head',
                                 'sha256': self.manifest['artifacts'][0]['sha256']}])

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True,
                                       stderr=subprocess.PIPE).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-m', 'Bind candidate control')
        return self.git('rev-parse', 'HEAD')

    def candidate(self):
        (self.root / 'manifest.json').write_text(json.dumps(self.manifest))
        self.issue['body'] = ('<!-- soodles:execution-v1 -->\n```json\n'
                              + json.dumps(self.contract) + '\n```\n<!-- /soodles:execution-v1 -->')
        return self.commit()

    def test_complete_candidate_reads_selected_git_bytes_not_dirty_files(self):
        head = self.candidate()
        (self.root / 'policy.md').write_text('unselected working copy')
        result = admission.verify_candidate(self.root, self.base, head, self.issue)
        self.assertEqual(result['classification'], 'VERIFIED')
        self.assertEqual(result['head'], head)
        self.assertEqual(result['tree'], self.git('rev-parse', 'HEAD^{tree}'))
        self.assertFalse(result['authorizes_landing'])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'candidate.checkout_head'):
            admission.verify_candidate(self.root, self.base, self.base, self.issue)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'candidate.base'):
            admission.verify_candidate(self.root, 'f' * 40, head, self.issue)

    def test_instruction_artifact_and_external_pin_mismatches_refuse(self):
        original = copy.deepcopy(self.manifest)
        for field in ('baseline', 'treatment', 'artifact', 'external_pin'):
            with self.subTest(field=field):
                self.manifest = copy.deepcopy(original)
                if field in ('baseline', 'treatment'):
                    self.manifest['instructions'][0][field + '_sha256'] = '0' * 64
                    expected = 'candidate.instruction.' + field + '_sha256'
                elif field == 'artifact':
                    self.manifest['artifacts'][0]['sha256'] = '0' * 64
                    expected = 'candidate.artifact.sha256'
                else:
                    # Manifest and candidate agree; the external pin still rejects them.
                    changed = b'candidate-selected observer\n'
                    (self.root / 'observer.py').write_bytes(changed)
                    self.manifest['artifacts'][0]['sha256'] = digest(changed)
                    expected = 'candidate.frozen_path.sha256'
                head = self.candidate()
                with self.assertRaises(admission.AdmissionRefusal) as caught:
                    admission.verify_candidate(self.root, self.base, head, self.issue)
                self.assertEqual(caught.exception.invalid['field'], expected)
                if field in ('baseline', 'treatment'):
                    self.assertEqual(caught.exception.next['required'],
                                     ['candidate_instruction_matches_frozen_evidence'])

    def test_missing_evidence_and_legacy_schema_two_binding(self):
        head = self.commit()
        binding = {'issue': 18, 'base_head': self.base,
                   'write_paths': self.contract['write_paths'], 'contract': {
                       'schema': 2, 'candidate_evidence': {
                           'manifest_path': 'manifest.json',
                           'required_paths': self.contract['required_paths']}}}
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'candidate.missing_required_paths'):
            admission.validate_delivery_paths(self.root, self.base, head, binding)
        head = self.candidate()
        self.assertEqual(admission.validate_delivery_paths(self.root, self.base, head, binding)['changed_paths'],
                         sorted(self.contract['required_paths']))
        self.assertEqual(admission.AdmissionRefusal('envelope', None).next['required'], ['execution_envelope'])
