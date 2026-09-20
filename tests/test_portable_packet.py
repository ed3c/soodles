"""Physical packet defects, exact fixture selection and legal carrier/nonzero cases."""
import copy
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import portable_packet as packet


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'evidence'
        self.root.mkdir()
        for name, role in packet.layout().items():
            if role in ('observer', 'input_selection', 'input'):
                packet.write(self.root, name, packet.read_file(packet.FIXTURES, name))
        packet.write(self.root, 'subject.json', {'repository': 'ed3c/noodle',
                     'source_revision': packet.SOURCE, 'binary_sha256': 'a' * 64})
        packet.write(self.root, 'build.txt', ('vcs.revision=' + packet.SOURCE +
                     '\nvcs.modified=false\nGOOS=darwin\nGOARCH=arm64\n').encode())
        for label, sha in packet.OBSERVERS.items():
            packet.write(self.root, label + '/receipt.json', {'observer_sha256': sha,
                         'binary_sha256': 'a' * 64, 'scratch_removed': True,
                         'input_selection_sha256': packet.INPUT_SELECTION_SHA256,
                         'authorizes_landing': False})
            packet.write(self.root, label + '/stdout.bin', b'actual output\n')
            packet.write(self.root, label + '/stderr.bin', b'')
            packet.write(self.root, label + '/process.json', {'exit_code': 0,
                         'waited': True, 'timed_out': False,
                         'stdout_sha256': packet.digest(b'actual output\n'),
                         'stderr_sha256': packet.digest(b'')})
            packet.write(self.root, label + '/cleanup.json', {'owned_residue_absent': True})
        self.archive = Path(self.temp.name) / 'packet.tar'

    def test_recovery_scratch_isolates_captured_process_identity(self):
        observer_path = packet.FIXTURES / 'recovery-observer.py'
        spec = importlib.util.spec_from_file_location('recovery_observer', observer_path)
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
        source = Path(self.temp.name) / 'source'
        scratch = Path(self.temp.name) / 'scratch'
        process = source / '.noodle/sessions/captured/process.json'
        process.parent.mkdir(parents=True)
        process.write_text(json.dumps({'pid': os.getpid(), 'session_id': 'captured'}) + '\n')
        original = process.read_bytes()
        shutil.copytree(source, scratch)
        adjustments = observer.isolate_captured_process_identities(scratch)
        self.assertEqual(process.read_bytes(), original)
        changed = json.loads((scratch / '.noodle/sessions/captured/process.json').read_text())
        self.assertEqual(changed['pid'], observer.HISTORICAL_ABSENT_PID)
        self.assertEqual(adjustments, [{
            'path': '.noodle/sessions/captured/process.json',
            'captured_pid': os.getpid(),
            'scratch_pid': observer.HISTORICAL_ABSENT_PID,
        }])

    def create(self):
        packet.create(self.root, 'darwin_arm64', self.archive)
        return json.loads((self.root / 'packet.json').read_bytes())

    def rewrite(self, manifest):
        packet.write(self.root, 'packet.json', manifest)

    def test_exact_observers_and_input_digests(self):
        for label, sha in packet.OBSERVERS.items():
            self.assertEqual(packet.digest((packet.FIXTURES / (label + '-observer.py')).read_bytes()), sha)
        for name, sha in packet.selected_files().items():
            self.assertEqual(packet.digest(packet.read_file(packet.FIXTURES, 'preserved-soodles-input/' + name)), sha)

    def test_deterministic_tar_relocates_and_excludes_ambient_secrets(self):
        (self.root / '.env').write_text('GH_TOKEN=must-not-be-packaged')
        manifest = self.create()
        self.assertNotIn(str(self.root), json.dumps(manifest))
        (self.root / 'packet.json').unlink()
        other = self.archive.with_name('second.tar')
        packet.create(self.root, 'darwin_arm64', other)
        self.assertEqual(self.archive.read_bytes(), other.read_bytes())
        with tarfile.open(other) as tar:
            self.assertNotIn('.env', tar.getnames())
            self.assertTrue(all(x.mtime == 0 and x.uid == 0 and not x.uname for x in tar))
        self.assertEqual(packet.verify(other, 'darwin_arm64')['classification'], 'GREEN')
        with self.assertRaisesRegex(ValueError, 'carrier.id.*admission inspect'):
            packet.verify(other, 'linux_amd64')

    def test_linux_schema_noncase_uses_its_own_build_carrier(self):
        packet.write(self.root, 'build.txt', ('vcs.revision=' + packet.SOURCE +
                     '\nvcs.modified=false\nGOOS=linux\nGOARCH=amd64\n').encode())
        packet.create(self.root, 'linux_amd64', self.archive)
        self.assertEqual(packet.verify(self.archive, 'linux_amd64')['classification'], 'GREEN')
        with self.assertRaisesRegex(ValueError, 'carrier.id'):
            packet.verify(self.archive, 'darwin_arm64')

    def test_recorder_drops_credentials_and_live_owner_identity(self):
        output = Path(self.temp.name) / 'environment'
        keys = ('GH_TOKEN', 'GITHUB_TOKEN', 'NOODLE_PROJECT_DIR', 'NOODLE_SESSION_ID')
        with patch.dict('os.environ', {key: 'private-sentinel' for key in keys}):
            result = packet.record([sys.executable, '-c',
                'import os; print([k for k in ' + repr(keys) + ' if k in os.environ])'],
                self.root, output, Path(self.temp.name) / 'scratch')
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual((output / 'stdout.bin').read_bytes(), b'[]\n')

    def test_source_measurement_keeps_only_the_explicit_toolchain_selector(self):
        with patch.dict(os.environ, {'GOTOOLCHAIN': 'go1.26.1',
                                     'GITHUB_TOKEN': 'private-sentinel'}):
            environment = packet.credential_free_environment('GOTOOLCHAIN')
        self.assertEqual(environment['GOTOOLCHAIN'], 'go1.26.1')
        self.assertNotIn('GITHUB_TOKEN', environment)

    def test_manifest_planted_defects(self):
        valid = self.create()
        defects = [
            ('missing process role', lambda m: m['files'].__setitem__(slice(None), [f for f in m['files'] if f['role'] != 'process_exit'])),
            ('traversal', lambda m: m['files'][0].update(path='../secret')),
            ('absolute', lambda m: m['files'][0].update(path='/tmp/secret')),
            ('duplicate', lambda m: m['files'].append(m['files'][0])),
            ('role', lambda m: m['files'][0].update(role='receipt')),
            ('cleanup', lambda m: m['cleanup'].update(owned_residue_absent=False)),
            ('portable', lambda m: m['continuation'].update(portable=True)),
            ('historical argv', lambda m: m['continuation'].update(argv=['noodle', 'admission', 'retire'])),
            ('landing', lambda m: m.update(authorizes_landing=True)),
            ('carrier', lambda m: m['carrier'].update(os='linux')),
            ('source', lambda m: m['subject'].update(source_revision='b' * 40)),
        ]
        for name, defect in defects:
            with self.subTest(name=name):
                bad = copy.deepcopy(valid)
                defect(bad)
                self.rewrite(bad)
                with self.assertRaises(ValueError):
                    packet.verify(self.root, 'darwin_arm64')

    def test_changed_missing_symlink_evidence(self):
        self.create()
        file = self.root / 'recovery/stdout.bin'
        file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'bytes|sha256'):
            packet.verify(self.root)
        file.unlink()
        with self.assertRaisesRegex(ValueError, 'files.path'):
            packet.verify(self.root)
        file.symlink_to(self.root / 'refusal/stdout.bin')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            packet.verify(self.root)

    def test_rehashed_false_process_and_cleanup_are_rejected(self):
        for filename, field, value in [('process.json', 'exit_code', None),
                                       ('process.json', 'waited', False),
                                       ('cleanup.json', 'owned_residue_absent', False),
                                       ('receipt.json', 'scratch_removed', False)]:
            with self.subTest(filename=filename, field=field):
                path = self.root / 'recovery' / filename
                original = path.read_bytes()
                changed = json.loads(original)
                changed[field] = value
                path.write_bytes(packet.rendered(changed))
                with self.assertRaises(ValueError):
                    packet.create(self.root, 'darwin_arm64', self.archive)
                path.write_bytes(original)

    def test_real_nonzero_wait_and_streams_survive_packet(self):
        output = Path(self.temp.name) / 'actual'
        result = packet.record([sys.executable, '-c', 'import sys;print("refused");print("reason",file=sys.stderr);sys.exit(7)'],
                               self.root, output, Path(self.temp.name) / 'scratch')
        self.assertEqual(result['exit_code'], 7)
        self.assertTrue(result['waited'])
        for name in ('process.json', 'stdout.bin', 'stderr.bin', 'cleanup.json'):
            packet.write(self.root, 'refusal/' + name, (output / name).read_bytes())
        self.create()
        self.assertEqual(packet.verify(self.archive)['classification'], 'GREEN')
        self.assertEqual((self.root / 'refusal/stderr.bin').read_bytes(), b'reason\n')

    def test_timeout_is_waited_and_not_zero(self):
        output = Path(self.temp.name) / 'timeout'
        result = packet.record([sys.executable, '-u', '-c', 'import time;print("started");time.sleep(30)'],
                               self.root, output, Path(self.temp.name) / 'scratch', timeout=0.1)
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['waited'])
        self.assertLess(result['exit_code'], 0)
        self.assertEqual((output / 'stdout.bin').read_bytes(), b'started\n')

    def test_tar_refuses_traversal_symlink_and_duplicate_without_extraction(self):
        for kind in ('traversal', 'symlink', 'duplicate'):
            with self.subTest(kind=kind):
                with tarfile.open(self.archive, 'w') as tar:
                    info = tarfile.TarInfo('../escape' if kind == 'traversal' else 'packet.json')
                    if kind == 'symlink':
                        info.type, info.linkname = tarfile.SYMTYPE, '/tmp/secret'
                    tar.addfile(info, io.BytesIO(b''))
                    if kind == 'duplicate':
                        tar.addfile(info, io.BytesIO(b''))
                with self.assertRaises(ValueError):
                    packet.verify(self.archive)
                self.assertFalse((Path(self.temp.name) / 'escape').exists())

    def test_cli_create_and_verify(self):
        cli = Path(packet.__file__).parent / 'soodles'
        for args in [('create', str(self.root), str(self.archive), '--carrier', 'darwin_arm64'),
                     ('verify', str(self.archive), '--expected-carrier', 'darwin_arm64')]:
            result = subprocess.run([str(cli), 'packet', *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['authorizes_landing'])

    def test_actions_builds_the_tracked_ui_before_the_embedded_binary(self):
        workflow = (Path(packet.__file__).parent / '.github/workflows/runtime.yml').read_text()
        self.assertIn('GITHUB_API_TOKEN: ${{ github.token }}', workflow)
        self.assertIn("authenticated=True", workflow)
        install = workflow.index('corepack pnpm install --frozen-lockfile')
        ui = workflow.index('corepack pnpm --filter noodle-ui build')
        binary = workflow.index('go build -o "$RUNNER_TEMP/noodle-admission"')
        measurement = workflow.index('go version -m "$RUNNER_TEMP/noodle-admission"')
        observation = workflow.index('--build-info "$RUNNER_TEMP/noodle-build.txt"')
        self.assertLess(install, ui)
        self.assertLess(ui, binary)
        self.assertLess(binary, measurement)
        self.assertLess(measurement, observation)


if __name__ == '__main__':
    unittest.main()
