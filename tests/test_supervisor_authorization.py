"""Physical admission and publication-fault controls for authorization preparation."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import issue_atom
import supervisor_admission as admission
import test_issue_atom as atom_tests


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        fixture = atom_tests.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        entry = fixture.root / 'issue-atom'
        entry.write_text('#!/bin/sh\nexit 97\n')
        entry.chmod(0o755)
        workflow = fixture.root / admission.CANONICAL_WORKFLOW['path']
        workflow.parent.mkdir(parents=True)
        workflow.write_bytes((Path(admission.__file__).parent / admission.CANONICAL_WORKFLOW['path']).read_bytes())
        subprocess.run(['git', 'add', '.'], cwd=fixture.root, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Bind canonical workflow'], cwd=fixture.root,
                       check=True, capture_output=True)
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fixture.root, text=True).strip()
        value = fixture.authorization
        self.selection = {
            'schema': 1, 'repository': value['repository'], 'control_root': str(fixture.root),
            'issue': {**value['issue'], 'body': value['issue']['body'].replace(fixture.base, head)},
            'task': value['task'], 'carrier': {**value['carrier'], 'noodle': value['noodle']},
            'landing_owner': value['landing_owner'], 'instruction_paths': [],
        }
        self.path = fixture.outer / 'selection.json'
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        self.output = fixture.outer / 'prepared'

    def run_authorize(self):
        return admission.authorize(str(self.path), self.digest, str(self.output))

    def test_completion_is_bound_to_final_paths_and_existing_validator(self):
        result = self.run_authorize()
        authorization, digest = issue_atom.validate_authorization(
            result['authorization']['path'], result['authorization']['sha256'])
        self.assertEqual(result, json.loads((self.output / 'prepared.json').read_text()))
        self.assertEqual(result['next']['environment'], {'SOODLES_AUTHORIZATION_SHA256': digest})
        self.assertEqual(result['next']['argv'],
                         [str(self.fixture.root / 'issue-atom'), 'run', str(self.output / 'authorization.json')])
        self.assertEqual(authorization['landing_owner'], self.selection['landing_owner'])
        self.assertFalse(result['authorizes_landing'])

    def test_receipt_publication_failure_removes_only_owned_output(self):
        before = set(self.fixture.outer.iterdir())
        with patch.object(admission.os, 'replace', side_effect=OSError('injected publication fault')):
            with self.assertRaisesRegex(OSError, 'injected publication fault'):
                self.run_authorize()
        self.assertEqual(set(self.fixture.outer.iterdir()), before)

    def test_competing_output_is_never_replaced_or_removed(self):
        original = Path.mkdir
        def raced_mkdir(path, *args, **kwargs):
            if path == self.output:
                original(path)
                (path / 'foreign-owner').write_text('preserve')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'mkdir', raced_mkdir):
            with self.assertRaises(FileExistsError):
                self.run_authorize()
        self.assertEqual((self.output / 'foreign-owner').read_text(), 'preserve')
        self.assertEqual({p.name for p in self.output.iterdir()}, {'foreign-owner'})

    def test_git_subdirectory_cannot_become_a_control_root(self):
        self.selection['control_root'] = str(self.fixture.root / '.github')
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'selection.control_root'):
            self.run_authorize()
        self.assertFalse(self.output.exists())

    def test_missing_or_nonexecutable_continuation_refuses(self):
        entry = self.fixture.root / 'issue-atom'
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    entry.unlink()
                else:
                    entry.chmod(0o644)
                with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.next.entry'):
                    self.run_authorize()
                self.assertFalse(self.output.exists())

    def test_nonexecutable_selected_carrier_is_not_repaired(self):
        self.fixture.binary.chmod(0o644)
        with self.assertRaises(admission.AdmissionRefusal):
            self.run_authorize()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.fixture.binary.stat().st_mode & 0o777, 0o644)


if __name__ == '__main__':
    unittest.main()
