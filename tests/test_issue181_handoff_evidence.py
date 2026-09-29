"""Replay the externally frozen receiver case without contacting any provider."""
import importlib.util
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs/experiments/issue-181-handoff/replay.py"
HISTORICAL_HEAD = "12fb0a6ab8660fc1d7f0e0822e3b0fd28089d5dd"


class Issue181EvidenceTests(unittest.TestCase):
    def test_frozen_receiver_evidence_and_discriminating_controls(self):
        spec = importlib.util.spec_from_file_location("issue181_replay", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # #185 changes the live owner and Skill. Replay #181's fixed evidence
        # against its exact matching source, as the shared-owner test does.
        # Current owner behavior has its own current-source frozen oracle.
        archive = subprocess.run(["git", "archive", HISTORICAL_HEAD], cwd=ROOT,
                                 capture_output=True)
        self.assertEqual(archive.returncode, 0,
                         "Required #181 historical source " + HISTORICAL_HEAD +
                         " unavailable: " + archive.stderr.decode(errors="replace"))
        with tempfile.TemporaryDirectory(prefix="issue181-historical-") as directory:
            historical = Path(directory)
            with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as files:
                files.extractall(historical, filter="data")
            # No repinning or silent replacement of retained evidence is legal.
            relative = Path("docs/experiments/issue-181-handoff")
            current_files = {p.relative_to(ROOT / relative): p.read_bytes()
                             for p in (ROOT / relative).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
            historical_files = {p.relative_to(historical / relative): p.read_bytes()
                                for p in (historical / relative).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
            self.assertEqual(current_files, historical_files,
                             "Frozen #181 evidence must remain byte-for-byte unchanged")
            result = module.replay(historical)
        self.assertEqual(result["classification"], "PASS")
        self.assertFalse(result["authorizes_landing"])
        self.assertTrue(result["controls"]["legal_owner_prose_alias"])
        self.assertTrue(result["controls"]["planted_wrong_continuation"])
