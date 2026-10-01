"""External lifecycle activation: selection is not candidate self-authorization."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import issue_atom as atom
import supervisor_admission as admission
import test_supervisor_authorization as authorization_tests


class LifecycleActivationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = authorization_tests.AuthorizationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.runtime = self.fixture.fixture.outer / 'selected-lifecycle'
        self.runtime.mkdir()
        expected_files = {"issue-atom", "soodles", "soodles.py", "issue_atom.py",
            "supervisor_admission.py", "issue_admission.py", "issue_execution.py",
            "candidate_publication.py", "provider_credential.py", "provider_transport.py",
            "repository_binding.py", "dependency_binding.py", "github_reader.py",
            "landing.py", "policy/runtime.lock.json", "atom_repair.py",
            "policy/repair-policy.json", "provider_readback.py", "system_context.py",
            "contracts/system-v1/routes.json", "contracts/system-v1/common.md",
            "contracts/system-v1/issue-atom.md", "contracts/system-v1/candidate.md",
            "contracts/system-v1/readback.md", "provider-readback"}
        self.assertEqual(set(atom.LIFECYCLE_FILES), expected_files)
        for name in expected_files:
            destination = self.runtime / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(atom.__file__).parent / name, destination)
        hashes = {name: atom.digest_file(self.runtime / name) for name in atom.LIFECYCLE_FILES}
        self.spec = {'path': str(self.runtime / 'issue-atom'),
                     'sha256': hashes['issue-atom'],
                     'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True,
                                                    separators=(',', ':')).encode())}
        self.fixture.selection['lifecycle_owner'] = self.spec
        self.fixture.path.write_text(json.dumps(self.fixture.selection))
        self.fixture.digest = atom.digest_file(self.fixture.path)

    def test_prepared_continuation_and_resume_keep_exact_external_owner(self):
        receipt = self.fixture.run_authorize()
        self.assertEqual(receipt['next']['argv'][0], self.spec['path'])
        auth = atom.read_json(receipt['authorization']['path'], 'authorization')
        self.assertEqual(auth['lifecycle_owner'], self.spec)
        self.assertEqual(auth['landing_owner'], self.fixture.selection['landing_owner'])
        # Provenance readback remains possible without present runtime bytes.
        (self.runtime / 'issue_atom.py').unlink()
        self.assertEqual(receipt, self.fixture.run_authorize())
        with self.assertRaises(atom.AtomRefusal):
            atom.validate_authorization(receipt['authorization']['path'], receipt['authorization']['sha256'])

    def test_unselected_process_refuses_before_any_effect(self):
        receipt = self.fixture.run_authorize()
        with patch.object(atom, '_run_owned', side_effect=AssertionError('effect')):
            with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.execution'):
                atom.run(receipt['authorization']['path'], environ=receipt['next']['environment'])
        self.assertFalse((self.fixture.fixture.root / '.noodle').exists())

    def test_transitive_byte_drift_refuses_before_publication(self):
        (self.runtime / 'issue_execution.py').write_text('# different source\n')
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.source_sha256'):
            self.fixture.run_authorize()
        self.assertFalse(self.fixture.output.exists())

    def test_selected_runtime_can_validate_its_own_execution_identity(self):
        receipt = self.fixture.run_authorize()
        script = ('import issue_atom,sys; a,d=issue_atom.validate_authorization(sys.argv[1],sys.argv[2]); '
                  'issue_atom.validate_lifecycle_owner(a, executing=True); '
                  'print(issue_atom.same_command(sys.argv[1])[0])')
        process = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys;sys.path.insert(0,sys.argv.pop(1));' + script,
            str(self.runtime), receipt['authorization']['path'], receipt['authorization']['sha256']],
            capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), self.spec['path'])

    def test_candidate_or_symlink_owner_is_not_an_external_snapshot(self):
        spec = dict(self.spec)
        spec['path'] = str(self.fixture.fixture.root / 'issue-atom')
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.path'):
            atom.validate_lifecycle_owner({**self.fixture.fixture.authorization, 'lifecycle_owner': spec})
        target = self.runtime / 'provider_credential.py'
        raw = target.read_bytes()
        other = self.runtime.parent / 'credential-copy.py'
        other.write_bytes(raw)
        target.unlink()
        target.symlink_to(other)
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.file'):
            self.fixture.run_authorize()


if __name__ == '__main__':
    unittest.main()
