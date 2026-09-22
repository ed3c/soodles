"""Frozen #118 observer. Provider/Noodle effects are explicit local fixtures."""
import json
import os
from pathlib import Path
import shlex
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(sys.argv.pop(1)).resolve()))
import issue_atom as atom
from issue_atom_fixture import IssueAtomTests, Provider, Result


class SupplierBoundary(unittest.TestCase):
    def setUp(self):
        self.fixture = IssueAtomTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.trace = self.fixture.outer / 'supplier-readback.json'
        self.supplier = self.fixture.outer / 'supplier.py'
        self.supplier.write_text(
            'import json, os\nfrom pathlib import Path\n'
            'Path(os.environ["SUPPLIER_TRACE"]).write_text(json.dumps({k:os.environ.get(k) for k in '
            '["GH_TOKEN","GITHUB_TOKEN","NOODLES_APP_REPOSITORIES_JSON","NOODLES_APP_PERMISSIONS_JSON"]}))\n'
            'print("fixture-installation-token")\n')
        self.env = {'PATH': os.environ['PATH'],
                    'SOODLES_AUTHORIZATION_SHA256': self.fixture.digest,
                    'NOODLES_TOKEN_COMMAND': shlex.join([sys.executable, str(self.supplier)]),
                    'SUPPLIER_TRACE': str(self.trace)}
        self.provider = Provider()
        self.fixture.ready_issue(self.provider)

    def drive(self):
        def provider(repository, token):
            self.assertEqual(repository, 'ed3c/soodles')
            self.assertEqual(token, 'fixture-installation-token')
            self.provider.token = token
            return self.provider
        with patch.object(atom, 'GitHubProvider', side_effect=provider), \
             patch.object(atom.issue_execution, 'supervised', return_value={'published': False}), \
             patch.object(atom, '_run_claim', return_value=Result(1, 'fixture stop before dispatch')):
            return atom.run(self.fixture.path, environ=self.env)

    def test_configured_supplier_without_parent_token_reaches_existing_owner(self):
        value = self.drive()
        self.assertEqual(value['waiting_on'], 'Noodle')
        self.assertEqual(value['next']['argv'][-1], str(self.fixture.path))
        observed = json.loads(self.trace.read_text())
        self.assertIsNone(observed['GH_TOKEN'])
        self.assertEqual(json.loads(observed['NOODLES_APP_REPOSITORIES_JSON']), ['soodles'])
        self.assertEqual(json.loads(observed['NOODLES_APP_PERMISSIONS_JSON']),
                         {'contents':'write','issues':'write','pull_requests':'write','actions':'read'})
        self.assertEqual(self.provider.create_calls, 0)

    def test_stale_parent_token_does_not_select_another_identity(self):
        self.env.update(GH_TOKEN='stale-parent', GITHUB_TOKEN='stale-parent')
        self.drive()
        observed = json.loads(self.trace.read_text())
        self.assertIsNone(observed['GH_TOKEN'])
        self.assertIsNone(observed['GITHUB_TOKEN'])

    def test_missing_supplier_refuses_before_checkpoint_even_with_parent_token(self):
        self.env.pop('NOODLES_TOKEN_COMMAND')
        self.env['GH_TOKEN'] = 'stale-parent'
        with self.assertRaises(atom.AtomRefusal) as raised:
            self.drive()
        self.assertEqual(raised.exception.required, 'NOODLES_TOKEN_COMMAND')
        self.assertFalse(atom.artifact_paths(self.fixture.path)['state'].exists())
        self.assertEqual(self.provider.create_calls, 0)

    def test_supplier_failure_is_redacted_and_creates_no_checkpoint(self):
        self.env['NOODLES_TOKEN_COMMAND'] = 'printf fixture-secret >&2; exit 7'
        with self.assertRaises(atom.AtomRefusal) as raised:
            self.drive()
        self.assertNotIn('fixture-secret', str(raised.exception))
        self.assertFalse(atom.artifact_paths(self.fixture.path)['state'].exists())
        self.assertEqual(self.provider.create_calls, 0)

    def test_invalid_authorization_never_calls_supplier(self):
        self.env['SOODLES_AUTHORIZATION_SHA256'] = '0' * 64
        with self.assertRaises(atom.AtomRefusal):
            self.drive()
        self.assertFalse(self.trace.exists())

    def test_candidate_child_cannot_inherit_supplier_or_app_material(self):
        with patch.dict(os.environ, {'GH_TOKEN':'fixture-secret','GITHUB_TOKEN':'fixture-secret',
                        'NOODLES_TOKEN_COMMAND':'fixture-command',
                        'NOODLES_APP_PRIVATE_KEY_PATH':'/fixture/key',
                        'NOODLES_APP_CLIENT_ID':'fixture-client', 'KEEP':'yes'}, clear=True):
            self.assertEqual(atom.clean_child_env(), {'KEEP':'yes'})


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SupplierBoundary)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'scope':'local supplier and provider fixtures; not fresh Agent behavior',
                      'tests':result.testsRun,'failures':len(result.failures),
                      'errors':len(result.errors),'authorizes_landing':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
