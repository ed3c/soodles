"""The fixed process observer checks the CLI projection and existing guards."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT / 'docs/experiments/landing-continuation/observer.py'


class LandingContinuationTests(unittest.TestCase):
    def test_current_argv_is_executable_without_weakening_readback_guards(self):
        spec = importlib.util.spec_from_file_location('continuation_observer', OBSERVER)
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
        report = observer.observe(ROOT)
        self.assertEqual(report['evaluation']['safety'], 'PASS', report['evaluation'])
        self.assertEqual(report['evaluation']['projection'], 'PASS', report['evaluation'])
        self.assertTrue(report['cleanup']['removed'])
        self.assertTrue(all(plant['rejected'] and plant['synthetic_positive_reference_accepted']
                            for plant in report['sensitivity']))


if __name__ == '__main__':
    unittest.main()
