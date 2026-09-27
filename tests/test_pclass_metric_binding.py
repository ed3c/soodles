"""Fixed external controls for the bounded recovery measurement, not model evals."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/experiments/pclass-metric-binding"
SCRIPT = ROOT / ".agents/skills/verify-soodles/scripts/replay_pclass.py"
FROZEN = {
    "frozen/oracle.py": "ad13c139690ea2f9d8cca66410fd7068fe1b0a6658a09c0ef5209e7f717429b0",
    "frozen/fixture.json": "1eb228481c65ecd612480601e73f4579f0ca6c232673afa7d31acf128652495d",
    "frozen/protocol.md": "1da73282b974cd793a232f5c77ae89801ce659ae8c948575ad24a9981c6186f1",
    "raw/baseline-oracle.json": "67305fc3c437ada938f60ae448dad4c37d8279b6b88367ab7e4dec3a6b7abdb4",
    "frozen/migration.md": "abbe18c9ebfdcc3d757103d8ac2119c66a4b84cb08eadad3ed79e5eebcdd2695",
    "raw/first-attempt.json": "541f0062a9db1fc0091429f7ddc22a30b8a10f978cf50ced49f0e3d48cea88c2",
}


class PclassMetricBindingTests(unittest.TestCase):
    def test_frozen_inputs_and_observed_red_are_preserved(self):
        for path, expected in FROZEN.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((EVIDENCE / path).read_bytes()).hexdigest(), expected)
        baseline = json.loads((EVIDENCE / "raw/baseline-oracle.json").read_text())
        self.assertEqual(baseline["classification"], "FAIL")
        self.assertEqual([case["case"] for case in baseline["cases"] if case["passed"]],
                         ["supported"])
        self.assertEqual(baseline["oracle_sha256"], FROZEN["frozen/oracle.py"])
        self.assertEqual(baseline["fixture_sha256"], FROZEN["frozen/fixture.json"])
        self.assertFalse(baseline["authorizes_landing"])

    def test_fixed_oracle_against_current_source(self):
        with tempfile.TemporaryDirectory(prefix="metric-binding-") as directory:
            output = Path(directory) / "oracle.json"
            run = subprocess.run(
                [sys.executable, "-B", str(EVIDENCE / "frozen/oracle.py"), str(ROOT), str(output)],
                capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(output.read_text())
        self.assertEqual(result["classification"], "PASS")
        self.assertEqual(len(result["cases"]), 8)
        self.assertTrue(all(case["passed"] for case in result["cases"]), result)
        self.assertEqual(result["replayer_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertFalse(result["authorizes_landing"])

    def test_other_json_types_are_rejected_before_either_analyzer_import(self):
        spec = importlib.util.spec_from_file_location("metric_replay", SCRIPT)
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        fixture = json.loads((EVIDENCE / "frozen/fixture.json").read_text())
        with tempfile.TemporaryDirectory(prefix="metric-types-") as directory:
            observer, decider = (Path(directory) / name for name in ("observer.py", "decider.py"))
            observer.write_text(fixture["observer"])
            decider.write_text(fixture["decider"])
            for metric in ({}, {"name": "post_completion_owner_request"}, 0, 1, True, False):
                with self.subTest(metric=metric):
                    manifest = copy.deepcopy(fixture["manifest"])
                    manifest["primary_barrier"] = metric
                    for label, path in (("observer", observer), ("decider", decider), ("normalizer", SCRIPT)):
                        manifest[label + "_sha256"] = replay.file_sha256(path)
                    with patch.object(replay, "load_module") as loader:
                        result = replay.replay(fixture["raw"], fixture["gates"], manifest,
                                               replay.fingerprint(manifest), observer, decider)
                    loader.assert_not_called()
                    self.assertEqual(result["classification"], "FAIL")
                    self.assertEqual(result["errors"], ["unsupported_primary_barrier"])
                    self.assertNotIn("decision", result)
                    self.assertFalse(result["authorizes_landing"])


if __name__ == "__main__":
    unittest.main()
