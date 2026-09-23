import json
import subprocess
import unittest
from unittest.mock import patch

import provider_credential as credential


class ProviderCredentialTests(unittest.TestCase):
    def test_real_supplier_gets_exact_scope_and_no_inherited_token(self):
        command = ('test -z "$GH_TOKEN$GITHUB_TOKEN" && '
                   'test "$NOODLES_APP_REPOSITORIES_JSON" = \'["soodles"]\' && '
                   'test "$NOODLES_APP_PERMISSIONS_JSON" = \'{"issues": "read"}\' && '
                   'printf fixture-token')
        self.assertEqual(credential.supply_token("ed3c/soodles", {"issues": "read"}, environ={
            "NOODLES_TOKEN_COMMAND": command, "GH_TOKEN": "stale", "GITHUB_TOKEN": "stale",
            "NOODLES_APP_REPOSITORIES_JSON": '["other"]',
            "NOODLES_APP_PERMISSIONS_JSON": '{"administration":"write"}',
        }), "fixture-token")

    def test_missing_supplier_does_not_fall_back_to_parent_token(self):
        with self.assertRaises(credential.CredentialRefusal) as caught:
            credential.supply_token("ed3c/soodles", {}, environ={"GH_TOKEN": "stale"})
        self.assertEqual(caught.exception.required, "NOODLES_TOKEN_COMMAND")

    def test_bad_output_and_failure_are_redacted(self):
        for command in ("printf 'fixture-secret\\nsecond'", "printf '\\001'",
                        "printf fixture-secret >&2; exit 7", "true"):
            with self.subTest(command=command), self.assertRaises(credential.CredentialRefusal) as caught:
                credential.supply_token("ed3c/soodles", {}, environ={"NOODLES_TOKEN_COMMAND": command})
            self.assertNotIn("fixture-secret", str(caught.exception))

    def test_timeout_exception_does_not_expose_output_or_command(self):
        error = subprocess.TimeoutExpired("fixture-secret-command", 30,
                                          output="fixture-secret", stderr="fixture-secret")
        with patch.object(credential.subprocess, "run", side_effect=error), \
             self.assertRaises(credential.CredentialRefusal) as caught:
            credential.supply_token("ed3c/soodles", {}, environ={"NOODLES_TOKEN_COMMAND": "configured"})
        self.assertEqual(caught.exception.value, "TimeoutExpired")
        self.assertNotIn("fixture-secret", str(caught.exception))

    def test_clean_child_keeps_normal_environment_not_host_capability(self):
        env = {key: "sensitive" for key in (
            "GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
            "NOODLES_TOKEN_COMMAND", "NOODLES_APP_CLIENT_ID", "NOODLES_APP_PRIVATE_KEY_PATH",
            "NOODLES_APP_INSTALLATION_ID", "NOODLES_GITHUB_TOKEN", "GITHUB_APP_ID",
            "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND")}
        env["PATH"] = "/fixture/bin"
        self.assertEqual(credential.clean_child_env(env), {"PATH": "/fixture/bin"})


class HostRegistrationTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        import hashlib
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.root = self.outer / 'candidate'
        self.root.mkdir()
        self.profile = self.outer / 'config/soodles/provider.json'
        self.profile.parent.mkdir(parents=True)
        self.key = self.outer / 'synthetic-key'
        self.key.write_text('fixture-secret-key')
        self.supplier = self.outer / "supplier ' $(touch injected)"
        self.supplier.write_text('''#!/bin/sh
test "$NOODLES_APP_CLIENT_ID" = fixture-client || exit 11
test "$NOODLES_APP_INSTALLATION_ID" = 123 || exit 12
test -f "$NOODLES_APP_PRIVATE_KEY_PATH" || exit 13
test "$NOODLES_APP_REPOSITORIES_JSON" = '["other"]' || exit 14
test "$NOODLES_APP_PERMISSIONS_JSON" = '{"issues": "read"}' || exit 15
printf fixture-token
''')
        self.supplier.chmod(0o700)
        self.spec = {'schema': 1, 'kind': 'github_app_supplier',
                     'supplier': {'path': str(self.supplier), 'sha256': hashlib.sha256(self.supplier.read_bytes()).hexdigest()},
                     'app': {'client_id': 'fixture-client', 'installation_id': '123', 'private_key_path': str(self.key)}}
        self.env = {'XDG_CONFIG_HOME': str(self.outer / 'config'), 'HOME': str(self.outer / 'home')}
        self.write_profile()

    def write_profile(self):
        self.profile.write_text(json.dumps(self.spec))

    def resolve(self):
        return credential.resolve_host_environment(self.root, environ=self.env)

    def assert_refusal(self, field):
        with patch.object(credential.subprocess, 'run') as launch, \
             self.assertRaises(credential.CredentialRefusal) as caught:
            self.resolve()
        self.assertEqual(caught.exception.field, 'provider_credential_profile.' + field)
        self.assertEqual(caught.exception.required, caught.exception.field)
        self.assertNotIn(str(self.outer), str(caught.exception))
        self.assertNotIn('fixture-secret', str(caught.exception))
        launch.assert_not_called()

    def test_registered_scope_quoting_stripping_and_no_private_key_read(self):
        from pathlib import Path
        original = Path.read_bytes
        def read(path):
            self.assertNotEqual(path, self.key)
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            resolved = self.resolve()
        self.assertNotIn(credential.TOKEN_COMMAND_ENV, self.env)
        self.assertEqual(credential.supply_token('ed3c/other', {'issues': 'read'}, environ=resolved), 'fixture-token')
        self.assertEqual(credential.clean_child_env(resolved), self.env)
        self.assertFalse((self.outer / 'injected').exists())

    def test_home_fallback_blank_command_and_no_ambient_fallback(self):
        self.env['HOME'] = str(self.outer)
        self.env.pop('XDG_CONFIG_HOME')
        destination = self.outer / '.config/soodles/provider.json'
        destination.parent.mkdir(parents=True)
        destination.write_bytes(self.profile.read_bytes())
        self.env[credential.TOKEN_COMMAND_ENV] = '  '
        self.assertIn(credential.TOKEN_COMMAND_ENV, self.resolve())
        self.env.pop('HOME')
        with patch.dict(credential.os.environ, {'HOME': str(self.outer)}, clear=True):
            self.assert_refusal('path')

    def test_explicit_legacy_is_opaque_and_bypasses_profile_and_context(self):
        self.profile.write_text('invalid')
        self.env.update({credential.TOKEN_COMMAND_ENV: 'printf fixture-token; true', 'NOODLE_ORDER_ID': 'child'})
        self.assertEqual(self.resolve(), self.env)

    def test_generic_supplier_never_autoloads(self):
        with self.assertRaises(credential.CredentialRefusal) as caught:
            credential.supply_token('ed3c/soodles', {}, environ=self.env)
        self.assertEqual(caught.exception.field, 'provider_credential_supplier')

    def test_child_context_refuses_each_identity_even_empty(self):
        for name in ('NOODLE_SESSION_ID', 'NOODLE_ORDER_ID'):
            for value in ('child', ''):
                with self.subTest(name=name, value=value):
                    self.env[name] = value
                    self.assert_refusal('context')
                    del self.env[name]

    def test_bad_profile_shapes_and_fields_are_redacted(self):
        import copy
        original = copy.deepcopy(self.spec)
        cases = [(None, 'path'), ([], 'path'), ('fixture-secret', 'path')]
        for field, values in [('schema', [True, 2, '1']), ('kind', ['other', None]),
                              ('supplier', [[], None]), ('app', [[], None])]:
            for value in values:
                spec = copy.deepcopy(original); spec[field] = value
                cases.append((spec, field))
        for group, name, values in [
            ('app', 'client_id', ['', ' ', 1, None, 'bad\0value']),
            ('app', 'installation_id', ['', 123, '１２３', '-1', ' 123', None]),
            ('supplier', 'sha256', ['', '0' * 64, None]),
            ('supplier', 'path', ['relative', '/', 'bad\0path', None]),
            ('app', 'private_key_path', ['relative', '/', None])]:
            for value in values:
                spec = copy.deepcopy(original); spec[group][name] = value
                cases.append((spec, group + '.' + name))
            spec = copy.deepcopy(original); del spec[group][name]
            cases.append((spec, group + '.' + name))
        extra = copy.deepcopy(original); extra['supplier']['args'] = ['fixture-secret']
        cases.append((extra, 'supplier'))
        for spec, field in cases:
            with self.subTest(field=field, spec=spec):
                self.spec = spec; self.write_profile(); self.assert_refusal(field)
        self.profile.write_text('{fixture-secret')
        self.assert_refusal('path')

    def test_invalid_locator_boundaries(self):
        self.env['XDG_CONFIG_HOME'] = 'relative'
        self.assert_refusal('path')
        self.env['XDG_CONFIG_HOME'] = str(self.outer / 'config')
        self.supplier.chmod(0o600)
        self.assert_refusal('supplier.path')
        self.supplier.chmod(0o700)
        with patch.object(credential.os, 'access', side_effect=lambda path, mode: path != self.key):
            self.assert_refusal('app.private_key_path')
        self.key.unlink()
        self.assert_refusal('app.private_key_path')

    def test_profile_and_supplier_cannot_cross_candidate_boundary_via_symlink(self):
        for name in ('profile', 'supplier'):
            with self.subTest(name=name):
                path = self.profile if name == 'profile' else self.supplier
                data = path.read_bytes(); path.unlink()
                target = self.root / name; target.write_bytes(data); target.chmod(0o700)
                path.symlink_to(target)
                self.assert_refusal('path' if name == 'profile' else 'supplier.path')
                path.unlink(); path.write_bytes(data); path.chmod(0o700)
        inside = self.root / 'supplier-link'
        inside.symlink_to(self.supplier)
        self.spec['supplier']['path'] = str(inside); self.write_profile()
        self.assert_refusal('supplier.path')


class FrozenHostRouteControlsTests(unittest.TestCase):
    def test_frozen_inputs_and_real_cli_oracle(self):
        import hashlib
        import os
        from pathlib import Path
        import sys
        import tempfile
        root = Path(credential.__file__).parent
        evidence = root / 'docs/experiments/host-credential-route'
        frozen = {
            'protocol.md': 'c5726114a6392d656462ba00a647b69442cd629b15c04c060b23471afd3cbe64',
            'oracle.py': '2af7c4402aa8a77b7a8ba4c0f316e1454fbe6eb1c6db907bb2b32b18178f5216',
            'consumer-drive.py': 'bb23cba4878c2248232e683cf26cc4c319cfe05a1d8237e39afd94f912c60eeb',
            'fixture.py': '813ef574ec739ddd99467c69bd57ed0f65fb52b739591edc05882a419860be80',
        }
        for name, digest in frozen.items():
            self.assertEqual(hashlib.sha256((evidence / name).read_bytes()).hexdigest(), digest, name)
        with tempfile.TemporaryDirectory() as directory:
            env = credential.clean_child_env({key: value for key, value in os.environ.items()
                                               if not key.startswith('NOODLE_')})
            env.update(HOME=directory, XDG_CONFIG_HOME=directory)
            result = subprocess.run([sys.executable, '-B', str(evidence / 'oracle.py'),
                                     str(root), str(Path(directory) / 'controls')],
                                    capture_output=True, text=True, env=env, timeout=180,
                                    start_new_session=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['classification'], 'GREEN', result.stdout)
