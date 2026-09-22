"""Discriminating controls over the real reader; fixtures never authorize landing."""
import io
import json
import os
import re
import shlex
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import github_reader as reader
import issue_execution
import soodles
from issue_admission import AdmissionRefusal

URL = 'https://api.github.com/repos/ed3c/soodles/issues/44'
TOKEN = 'installation_fixture_not_a_real_token'


def response(status=200, headers=None, value=None):
    stream = io.BytesIO(json.dumps(value or {'url': URL, 'number': 44, 'body': 'unchanged'}).encode())
    stream.url, stream.code = URL, status
    stream.headers = headers or {}
    return stream


class GithubReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.environment = patch.dict(os.environ, {'GH_TOKEN': TOKEN, 'XDG_CACHE_HOME': self.temp.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def cli(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', argv), redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = soodles.main()
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_recipe_command_reads_externally_selected_issue(self):
        root = Path(reader.__file__).resolve().parent
        recipe = (root / '.agents/skills/verify-soodles/features/github-read.md').read_text()
        template = re.search(r'`(\./soodles github issue [^`]+)`', recipe).group(1)
        for repository, number in [('ed3c/soodles', 44), ('ed3c/ops-reconciliation-copilot', 21)]:
            with self.subTest(repository=repository):
                argv = shlex.split(template.replace('OWNER/REPOSITORY', repository).replace('NUMBER', str(number)))
                url = f'https://api.github.com/repos/{repository}/issues/{number}'
                value = {'url': url, 'number': number, 'body': 'unchanged'}
                received = response(value=value)
                received.url = url
                with patch.object(reader, '_request', return_value=received) as transport:
                    code, stdout, stderr = self.cli(argv)
                self.assertEqual(code, 0, stdout + stderr)
                receipt = json.loads(stdout)
                self.assertEqual(receipt['status'], 'read')
                self.assertEqual(receipt['issue'], value)
                transport.assert_called_once()
                self.assertEqual(transport.call_args.args[0].full_url, url)
                self.assertEqual(transport.call_args.args[0].get_header('Authorization'), 'Bearer ' + TOKEN)

    def test_malformed_read_arguments_stay_caller_owned_before_transport(self):
        cases = [[], ['44'], ['ed3c/soodles'], ['ed3c/soodles', 'invalid'],
                 ['ed3c/soodles', '44', '--unknown']]
        root = Path(reader.__file__).resolve().parent
        for arguments in cases:
            with self.subTest(arguments=arguments), patch.object(reader, '_request') as transport:
                code, stdout, stderr = self.cli(['./soodles', 'github', 'issue', *arguments])
                self.assertEqual(code, 2, stdout + stderr)
                transport.assert_not_called()
                receipt = json.loads(stdout)
                self.assertEqual(receipt['status'], 'refused')
                self.assertEqual(receipt['invalid']['field'], 'arguments')
                self.assertEqual(receipt['next']['owner'], 'caller')
                self.assertEqual(receipt['next']['required'], ['valid_read_arguments'])
                self.assertNotIn('execution_envelope', stdout + stderr)
                self.assertEqual(receipt['next']['help_argv'],
                                 [str(root / 'soodles'), 'github', 'issue', '--help'])
        code, stdout, stderr = self.cli(receipt['next']['help_argv'])
        self.assertEqual(code, 0, stdout + stderr)
        self.assertIn('repository', stdout)
        self.assertIn('number', stdout)

    def test_read_input_non_cases_keep_supervisor_owner(self):
        cases = [('ed3c/soodles', '', 'github.credential',
                  'repository_scoped_installation_token_in_GH_TOKEN'),
                 ('ed3c/unregistered', TOKEN, 'issue.repository',
                  'supported_repository_identity')]
        for repository, token, field, required in cases:
            with self.subTest(field=field), patch.dict(os.environ, {'GH_TOKEN': token}), patch.object(reader, '_request') as transport:
                code, stdout, stderr = self.cli(['./soodles', 'github', 'issue', repository, '44'])
                self.assertEqual(code, 1, stdout + stderr)
                transport.assert_not_called()
                receipt = json.loads(stdout)
                self.assertEqual(receipt['invalid']['field'], field)
                self.assertEqual(receipt['next']['owner'], 'supervisor')
                self.assertEqual(receipt['next']['required'], [required])

    def test_no_anonymous_request_without_credentials(self):
        # This exact assertion also runs against the old production fetch_issue.
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.OpenerDirector.open', side_effect=urllib.error.URLError('sentinel')) as transport:
            with self.assertRaises(AdmissionRefusal):
                issue_execution.fetch_issue('ed3c/soodles', 44)
        self.assertEqual(transport.call_count, 0)

    def test_authenticated_non_case(self):
        with patch.object(reader, '_request', return_value=response()) as transport:
            result = issue_execution.fetch_issue('ed3c/soodles', 44)
        self.assertEqual(result['number'], 44)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(transport.call_args.args[0].get_header('Authorization'), 'Bearer ' + TOKEN)

    def test_opaque_provider_credential_is_a_legal_non_case(self):
        token = "fixture.opaque-token~+/="
        with patch.dict(os.environ, {"GH_TOKEN": token}), patch.object(reader, '_request', return_value=response()) as transport:
            self.assertEqual(reader.issue('ed3c/soodles', 44)['issue']['number'], 44)
        self.assertEqual(transport.call_args.args[0].get_header('Authorization'), 'Bearer ' + token)

    def test_304_revalidates_same_identity_and_bytes(self):
        with patch.object(reader, '_request', side_effect=[response(headers={'ETag': '"one"'}), response(304)]) as transport:
            first = reader.issue('ed3c/soodles', 44)
            second = reader.issue('ed3c/soodles', 44)
        self.assertEqual(first['issue'], second['issue'])
        self.assertEqual(second['observation']['status'], 304)
        self.assertEqual(transport.call_args.args[0].get_header('If-none-match'), '"one"')
        self.assertEqual(transport.call_args.args[0].get_header('Authorization'), 'Bearer ' + TOKEN)

    def test_changed_identity_never_reuses_cache(self):
        with patch.object(reader, '_request', return_value=response(headers={'ETag': '"one"'})):
            reader.issue('ed3c/soodles', 44)
        with patch.dict(os.environ, {'GH_TOKEN': 'another_fixture_identity'}), patch.object(reader, '_request', return_value=response(304)) as transport:
            with self.assertRaises(AdmissionRefusal):
                reader.issue('ed3c/soodles', 44)
        self.assertIsNone(transport.call_args.args[0].get_header('If-none-match'))

    def test_corrupt_cache_requires_fresh_bytes(self):
        with patch.object(reader, '_request', return_value=response(headers={'ETag': '"one"'})):
            reader.issue('ed3c/soodles', 44)
        path = next(p for p in Path(self.temp.name).rglob('*.json') if p.name != 'budget.json')
        value = json.loads(path.read_text()); value['body'] = '{}'; path.write_text(json.dumps(value))
        with patch.object(reader, '_request', return_value=response(304)) as transport:
            with self.assertRaises(AdmissionRefusal):
                reader.issue('ed3c/soodles', 44)
        self.assertIsNone(transport.call_args.args[0].get_header('If-none-match'))

    def test_provider_failure_never_returns_stale_cache(self):
        with patch.object(reader, '_request', side_effect=[response(headers={'ETag': '"one"'}), response(500)]) as transport:
            reader.issue('ed3c/soodles', 44)
            with self.assertRaises(AdmissionRefusal) as caught:
                reader.issue('ed3c/soodles', 44)
        self.assertEqual(transport.call_count, 2)
        self.assertEqual(caught.exception.next['owner'], 'GitHub')
        self.assertEqual(caught.exception.next['required'], ['fresh_issue_readback'])

    def test_quota_wait_has_no_retry_and_blocks_next_call(self):
        until = int(time.time()) + 600
        with patch.object(reader, '_request', return_value=response(403, {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(until)})) as transport:
            for sent in (True, False):
                with self.assertRaises(reader.ProviderWait) as caught:
                    reader.issue('ed3c/soodles', 44)
                self.assertEqual(caught.exception.next['not_before'], until)
                self.assertEqual(caught.exception.invalid['value']['request_sent'], sent)
        self.assertEqual(transport.call_count, 1)

    def test_retry_after_wait_and_no_missing_deadline_inference(self):
        with patch.object(reader, '_request', return_value=response(429, {'Retry-After': '10'})) as transport:
            with self.assertRaises(reader.ProviderWait) as caught:
                reader.issue('ed3c/soodles', 44)
        self.assertGreater(caught.exception.next['not_before'], time.time())
        self.assertEqual(transport.call_count, 1)

    def test_expired_wait_allows_authenticated_non_case(self):
        with patch.object(reader, '_request', return_value=response(403, {'Retry-After': '10'})), patch.object(reader.time, 'time', return_value=100):
            with self.assertRaises(reader.ProviderWait):
                reader.issue('ed3c/soodles', 44)
        with patch.object(reader, '_request', return_value=response()) as transport:
            self.assertEqual(reader.issue('ed3c/soodles', 44)['issue']['number'], 44)
        self.assertEqual(transport.call_count, 1)

    def test_invalid_credential_no_fallback_or_secret_output(self):
        with patch.object(reader, '_request', return_value=response(401)) as transport:
            with self.assertRaises(AdmissionRefusal) as caught:
                reader.issue('ed3c/soodles', 44)
        self.assertEqual(transport.call_count, 1)
        self.assertNotIn(TOKEN, json.dumps(reader.refusal_output(caught.exception)))
        self.assertEqual(caught.exception.next['owner'], 'supervisor')
        self.assertEqual(caught.exception.next['required'], ['repository_scoped_installation_token_in_GH_TOKEN'])

    def test_wrong_issue_identity_refused(self):
        with patch.object(reader, '_request', return_value=response(value={'url': URL, 'number': 45})):
            with self.assertRaises(AdmissionRefusal):
                reader.issue('ed3c/soodles', 44)

    def test_credential_not_forwarded_on_redirect(self):
        hits = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                if self.path == '/first':
                    self.send_response(302)
                    self.send_header('Location', '/target')
                    self.end_headers()
                else:
                    self.send_response(200); self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            request = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/first', headers={'Authorization': 'Bearer ' + TOKEN})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                reader._request(request)
            caught.exception.close()
            self.assertEqual(hits, ['/first'])
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_cli_quota_wait_reports_exit_75_without_network(self):
        with patch.object(reader, '_request', return_value=response(403, {'Retry-After': '600'})):
            with self.assertRaises(reader.ProviderWait):
                reader.issue('ed3c/soodles', 44)
        root = Path(reader.__file__).resolve().parent
        result = subprocess.run([str(root / 'soodles'), 'github', 'issue', 'ed3c/soodles', '44'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 75)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['status'], 'wait')
        self.assertFalse(receipt['invalid']['value']['request_sent'])
        self.assertEqual(receipt['next']['kind'], 'wait')
        self.assertEqual(receipt['next']['owner'], 'GitHub')
        self.assertEqual(receipt['next']['required'], ['fresh_issue_readback'])
        self.assertGreater(receipt['next']['not_before'], time.time())

    def test_header_control_characters_refused_before_transport(self):
        with patch.dict(os.environ, {'GH_TOKEN': 'fixture\r\nInjected: value'}), patch.object(reader, '_request') as transport:
            with self.assertRaises(AdmissionRefusal):
                reader.issue('ed3c/soodles', 44)
        transport.assert_not_called()

    def test_cli_missing_credential_names_owner_and_help(self):
        root = Path(reader.__file__).resolve().parent
        env = {key: value for key, value in os.environ.items() if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
        result = subprocess.run([str(root / 'soodles'), 'github', 'issue', 'ed3c/soodles', '44'], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['next']['owner'], 'supervisor')
        self.assertEqual(receipt['next']['help_argv'][-3:], ['github', 'issue', '--help'])
        self.assertEqual(receipt['status'], 'refused')


if __name__ == '__main__':
    unittest.main()
