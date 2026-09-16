import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parent.parent / '.agents/skills/verify-soodles/scripts/verify_recovery.py'
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location('verify_recovery', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
sys.path.pop(0)


class RecoveryVerificationTests(unittest.TestCase):
    def cleanup_result(self):
        return {'scope': 'local fixture', 'authorizes_landing': False, 'provider_requests': 0,
                'zero_residue': True, 'cases': [{'case': name, 'control': 'passed',
                                               'zero_residue': True, 'lock_refusal_before_deletion': True}
                                              for name in sorted(verify.REQUIRED_CASES['cleanup-lock'])],
                'controls': [{'argv': ['noodle', 'worktree', 'cleanup', 'fixture'], 'exit': 0, 'stdout': '', 'stderr': ''}]}

    def test_cleanup_evidence_rejects_old_refusal_and_false_green(self):
        valid = self.cleanup_result()
        verify.validate_result('cleanup-lock', valid)
        invalid = [None, {}, {**valid, 'cases': []}, {**valid, 'scope': ''},
                   {**valid, 'authorizes_landing': True}, {**valid, 'provider_requests': 1},
                   {**valid, 'zero_residue': False}, {**valid, 'controls': []},
                   {**valid, 'cases': valid['cases'][:-1]}]
        for field in ('control', 'zero_residue', 'lock_refusal_before_deletion'):
            changed = copy.deepcopy(valid)
            changed['cases'][0].pop(field)
            invalid.append(changed)
        invalid.append({**valid, 'cases': valid['cases'] * 2})
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify.validate_result('cleanup-lock', value)

    def test_legacy_cleanup_keeps_original_receipt_and_no_count_ratchet(self):
        value = self.cleanup_result()
        value['cases'] = [{**value['cases'][0], 'case': name} for name in sorted(verify.REQUIRED_CASES['cleanup'])]
        del value['authorizes_landing']
        before = copy.deepcopy(value)
        verify.validate_result('cleanup', value)
        self.assertEqual(value, before)
        with self.assertRaises(ValueError):
            verify.validate_result('cleanup-lock', value)
        value['cases'].append({**value['cases'][0], 'case': 'new_cleanup_behavior'})
        verify.validate_result('cleanup', value)

    def test_delivery_and_base_reject_names_without_behavior_evidence(self):
        for name in ('delivery', 'base'):
            for cases in ([{'case': 'placeholder'}], [{'case': c} for c in sorted(verify.REQUIRED_CASES[name])]):
                value = {'scope': 'fixture', 'authorizes_landing': False, 'cases': cases}
                with self.subTest(name=name, cases=cases), self.assertRaises(ValueError):
                    verify.validate_result(name, value)

    def test_every_required_journey_must_be_verified_once(self):
        required = [name for name, _ in verify.journeys('/runtime/noodle')]
        good = {'journeys': [{'name': name, 'status': 'VERIFIED'} for name in required]}
        verify.complete(good, required)
        for bad in (good['journeys'][:-1], good['journeys'] + good['journeys'][:1],
                    [{**j, 'status': 'NOT_RUN'} if i == 1 else j for i, j in enumerate(good['journeys'])]):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                verify.complete({'journeys': bad}, required)

    def test_failed_or_hollow_oracle_preserves_evidence_and_stops(self):
        context = {'classification': 'VERIFIED', 'trace': [], 'candidate': {'head': 'a'*40, 'tree': 'b'*40},
                   'runtime': {}}
        for returned in (subprocess.CompletedProcess([], 7, '', 'planted failure'),
                         subprocess.CompletedProcess([], 0, '{}', '')):
            with self.subTest(exit=returned.returncode), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'evidence'
                with patch.object(verify.runtime, 'drive', return_value=context), patch.object(verify.subprocess, 'run', return_value=returned) as called:
                    receipt = verify.drive('/runtime/noodle', output)
                self.assertEqual(called.call_count, 1)
                self.assertEqual(receipt['classification'], 'FAILED')
                self.assertIs(receipt['authorizes_landing'], False)
                self.assertEqual(receipt['journeys'][0]['status'], 'FAILED')
                self.assertTrue(all(j['status'] == 'NOT_RUN' for j in receipt['journeys'][1:]))
                self.assertEqual(receipt['trace'][0]['stderr'], returned.stderr)
                self.assertFalse(receipt['cleanup']['verified'])
                self.assertEqual(json.loads((output/'receipt.json').read_text()), receipt)

    def test_timeout_retains_partial_output_without_claiming_cleanup(self):
        context = {'classification': 'VERIFIED', 'trace': [], 'candidate': {'head': 'a'*40, 'tree': 'b'*40}, 'runtime': {}}
        with tempfile.TemporaryDirectory() as directory:
            error = subprocess.TimeoutExpired(['oracle'], 30, output=b'partial progress', stderr=b'pending')
            with patch.object(verify.runtime, 'drive', return_value=context), patch.object(verify.subprocess, 'run', side_effect=error):
                receipt = verify.drive('/runtime/noodle', Path(directory)/'evidence')
            self.assertEqual(receipt['trace'][0]['stdout'], 'partial progress')
            self.assertEqual(receipt['trace'][0]['stderr'], 'pending')
            self.assertFalse(receipt['cleanup']['verified'])
            self.assertEqual(receipt['classification'], 'FAILED')

    def test_real_cli_invalid_input_has_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'untouched'
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'guessed-noodle', str(output)],
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertIn("binary='guessed-noodle'", result.stderr)
            self.assertIn('verify-soodles delivery-recovery', result.stderr)
            self.assertIn('--help', result.stderr)
