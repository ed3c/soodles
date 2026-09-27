"""Replay the externally frozen receiver case without contacting any provider."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs/experiments/issue-181-handoff/replay.py"


class Issue181EvidenceTests(unittest.TestCase):
    def test_frozen_receiver_evidence_and_discriminating_controls(self):
        spec = importlib.util.spec_from_file_location("issue181_replay", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.replay(ROOT)
        self.assertEqual(result["classification"], "PASS")
        self.assertFalse(result["authorizes_landing"])
        self.assertTrue(result["controls"]["legal_owner_prose_alias"])
        self.assertTrue(result["controls"]["planted_wrong_continuation"])
