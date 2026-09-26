"""Synthetic schema controls for the bounded #157 candidate gate, not model evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / 'docs/experiments/pclass-case-exposure/consumer_gate.py'
spec = importlib.util.spec_from_file_location('pclass_gate_positive', GATE_PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def write(root, relative, raw):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest()}


def json_file(root, relative, value):
    return write(root, relative, (json.dumps(value, sort_keys=True) + '\n').encode())


def fixture(root, *, regression=False):
    common = {'launch_options': ['--ignore-user-config', '-m', 'synthetic-model', '-s', 'read-only'],
              'output_schema_path': '/selected/output-schema.json',
              'output_schema_sha256': 'a' * 64,
              'supervisor_cwd': '/selected/supervisor', 'cli_version': '0.156.1',
              'model': 'synthetic-model', 'reasoning': 'high',
              'approval': 'never', 'sandbox': 'read-only',
              'baseline_ref': 'b'*40, 'treatment_ref': 'c'*40}
    packets, runs = [], []
    for arm in gate.ARMS:
        for case in gate.CASES:
            ident = f'{arm}-{case}'
            thread = f'synthetic-thread-{ident}'
            cwd = f'/selected/{arm}'
            final_path = f'/selected/evidence/{ident}/final.raw'
            prompt = f'synthetic neutral task for {ident}'
            prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
            replay_argv = ['python3', '-B', 'replay.py', f'/selected/{case}.json']
            command = shlex.join(['/bin/zsh', '-lc', shlex.join(replay_argv)])
            replay_decision = 'REJECT' if case == 'missing_required_observation' or (
                case == 'mismatched_case_exposure' and arm == 'treatment') else 'ADMIT_IMPROVEMENT'
            final_decision = ('ADMIT_IMPROVEMENT' if regression and arm == 'treatment'
                              and case == 'mismatched_case_exposure' else replay_decision)
            owner = 'supervisor' if final_decision == 'REJECT' else 'originating Issue owner'
            final = (json.dumps({'decision': final_decision, 'next_owner': owner}, sort_keys=True) + '\n').encode()
            final_desc = write(root, f'{ident}/final.raw', final)
            replay_output = json.dumps({'decision': {'decision': replay_decision},
                                        'authorizes_landing': False})
            events = [{'type': 'thread.started', 'thread_id': thread}, {'type': 'turn.started'},
                      {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'progress'}},
                      {'type': 'item.started', 'item': {'id': 'cmd', 'type': 'command_execution', 'command': command}},
                      {'type': 'item.completed', 'item': {'id': 'cmd', 'type': 'command_execution',
                                                         'command': command, 'aggregated_output': replay_output,
                                                         'exit_code': 1 if replay_decision == 'REJECT' else 0}},
                      {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': final.decode().strip()}},
                      {'type': 'turn.completed'}]
            stdout = write(root, f'{ident}/stdout.bin',
                           ''.join(json.dumps(event) + '\n' for event in events).encode())
            stderr = write(root, f'{ident}/stderr.bin', b'')
            rollout = write(root, f'{ident}/rollout.jsonl', (
                json.dumps({'type': 'session_meta', 'payload': {'id': thread, 'cwd': cwd,
                            'cli_version': common['cli_version'],
                            'git': {'commit_hash': common[arm + '_ref']}}}) + '\n' +
                json.dumps({'type': 'turn_context', 'payload': {'model': common['model'],
                            'effort': common['reasoning'], 'approval_policy': common['approval'],
                            'sandbox_policy': {'type': common['sandbox']}}}) + '\n').encode())
            before = {common['output_schema_path']: {'sha256': common['output_schema_sha256']}}
            request = json_file(root, f'{ident}/request.json', {'cwd': common['supervisor_cwd'],
                'argv': ['codex', '-C', cwd, 'exec', *common['launch_options'], '--json',
                         '--output-schema', common['output_schema_path'], '-o', final_path, prompt],
                'files_before': before})
            result = json_file(root, f'{ident}/result.json', {'scope': 'one_subprocess',
                'authorizes_landing': False, 'exit_code': 0, 'timed_out': False, 'error': None,
                'stdout_sha256': stdout['sha256'], 'stderr_sha256': stderr['sha256'],
                'files_after': {**before, final_path: {'sha256': final_desc['sha256']}}})
            packets.append({'id': ident, 'arm': arm, 'case': case, 'cwd': cwd,
                            'source_ref': common[arm + '_ref'],
                            'final_path': final_path, 'prompt_sha256': prompt_sha,
                            'replay_argv': replay_argv})
            runs.append({'id': ident, 'capture': {'request': request, 'result': result,
                          'stdout': stdout, 'stderr': stderr, 'final': final_desc, 'rollout': rollout}})
    selection = json_file(root, 'selection.json', {'issue': 'ed3c/soodles#157',
        'carrier': 'Local Codex CLI', 'status': 'SELECTED', 'observer_sha256': 'f'*64,
        'common': common, 'packets': packets})
    observed_primary = {'baseline': 1, 'treatment': int(regression)}
    observer_report = json_file(root, 'observer-report.json', {
        'issue': 'ed3c/soodles#157', 'selection_sha256': selection['sha256'],
        'observer_sha256': 'f'*64, 'authorizes_landing': False,
        'evidence_validity': 'VALID',
        'classification': 'FAIL' if regression else 'BOUNDED_IMPROVEMENT',
        'primary_unsupported_admission': observed_primary})
    comparison = {'schema': 2, 'issue': {'repository': 'ed3c/soodles', 'number': 157},
                  'status': 'COMPLETED', 'authorizes_landing': False,
                  'selection': selection, 'observer_report': observer_report,
                  'fresh_runs': runs}
    descriptor = json_file(root, 'comparison.json', comparison)
    return comparison, descriptor


class CandidatePositiveControls(unittest.TestCase):
    def test_six_raw_captures_support_bounded_positive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, descriptor = fixture(root)
            receipt = gate.inspect_file(root / descriptor['path'], descriptor['sha256'])
            self.assertTrue(receipt['terminal_ready'], receipt)
            self.assertEqual(receipt['evidence_validity'], 'VALID')
            self.assertEqual(receipt['behavior']['classification'], 'BOUNDED_IMPROVEMENT')
            self.assertFalse(receipt['authorizes_landing'])

    def test_valid_behavior_regression_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, descriptor = fixture(root, regression=True)
            receipt = gate.inspect_file(root / descriptor['path'], descriptor['sha256'])
            self.assertFalse(receipt['terminal_ready'])
            self.assertEqual(receipt['evidence_validity'], 'VALID')
            self.assertEqual(receipt['behavior']['classification'], 'FAIL')

    def test_missing_raw_capture_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            comparison, _ = fixture(root)
            comparison['fresh_runs'][0]['capture']['stdout']['sha256'] = '0'*64
            descriptor = json_file(root, 'comparison-mutated.json', comparison)
            receipt = gate.inspect_file(root / descriptor['path'], descriptor['sha256'])
            self.assertFalse(receipt['terminal_ready'])
            self.assertEqual(receipt['evidence_validity'], 'INCONCLUSIVE')

    def test_observer_report_must_match_raw_classification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            comparison, _ = fixture(root)
            report = root / comparison['observer_report']['path']
            value = json.loads(report.read_text())
            value['classification'] = 'SCOPED_NONREGRESSION'
            comparison['observer_report'] = json_file(root, 'observer-report-mutated.json', value)
            descriptor = json_file(root, 'comparison-mutated.json', comparison)
            receipt = gate.inspect_file(root / descriptor['path'], descriptor['sha256'])
            self.assertFalse(receipt['terminal_ready'])
            self.assertEqual(receipt['evidence_validity'], 'INCONCLUSIVE')
            self.assertEqual(receipt['problem']['field'], 'observer_report')


if __name__ == '__main__':
    unittest.main()
