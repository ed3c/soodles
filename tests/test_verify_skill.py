import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent.parent / '.agents/skills/verify-soodles/scripts/verify_runtime.py'
spec = importlib.util.spec_from_file_location('verify_runtime', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class VerificationSkillTests(unittest.TestCase):
    def test_resolution_requires_exact_local_skill(self):
        local = verify.SKILL
        row = f'verify-soodles\t.agents/skills\ttrue\t{local}\n'
        self.assertEqual(verify.resolved_skill(row, local)['path'], str(local))
        for invalid in ('', row + row, row.replace(str(local), '/foreign/verify-soodles'), row.replace('\ttrue\t', '\tfalse\t')):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                verify.resolved_skill(invalid, local)

    def test_output_refusal_precedes_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / 'evidence'
            with self.assertRaisesRegex(ValueError, 'absolute path'):
                verify.preflight('noodle', fresh)
            self.assertFalse(fresh.exists())
            with self.assertRaisesRegex(ValueError, 'fresh directory'):
                verify.preflight('/runtime/noodle', tmp)
        with self.assertRaisesRegex(ValueError, 'outside the checkout'):
            verify.preflight('/runtime/noodle', verify.ROOT/'evidence')

    def test_counts_separate_control_refusal_from_failure_and_keep_guard_repeats(self):
        events = [
            {'argv':['git','status'], 'kind':'readback', 'exit':0, 'expected_exit':0},
            {'argv':['git','status'], 'kind':'readback', 'exit':0, 'expected_exit':0},
            {'argv':['./soodles','runtime','check','bad'], 'kind':'verification', 'exit':1, 'expected_exit':1},
            {'argv':['./soodles','wrong'], 'kind':'verification', 'exit':2, 'expected_exit':0}]
        result = verify.counts(events)
        self.assertEqual(result['unexpected_command_failures'], 1)
        self.assertEqual(result['expected_refusals'], 1)
        self.assertEqual(result['repeated_readbacks'], 1)
        self.assertEqual(result['verification_invocations'], 2)
        self.assertEqual(result['canonical_acceptance_invocations'], 0)
