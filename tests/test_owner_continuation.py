"""Replay externally frozen process/provider fixtures against current source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class OwnerContinuationTests(unittest.TestCase):
    def test_frozen_hashes_and_current_source_oracle(self):
        source = Path(__file__).resolve().parents[1]
        evidence = source / "docs/experiments/pclass-owner-continuation"
        pins = {
            "frozen/driver.py": "1831f8af62beba5efaddec1a85418862d796cfb82251b0c284ee5e9b0aa593f2",
            "frozen/fixture.py": "0b2abed6703631ad9ce7d27cb5e687d2e94cfe77298d07c5869a8e5e86b86e23",
            "frozen/oracle.py": "60f4aa7f96d0e642a1a0b3d071480769fbd521d4fe351ec908b955f9c9d8f7c4",
            "frozen/protocol.md": "1f0ecff6fbc71993d08fd9de54e74c67fce8b153a7b053310e0bd6511015b9b1",
            "raw/baseline-oracle.json": "87ffc33ed971a406b9b58071e5d2bc70a11db2f6d8e04254c8083675e1796b5c",
            "raw/observed-history.json": "7e2c6b40fc49c2d4ac054408d405ede71053537ac96aa3f60f29bd39e07caa84",
            "frozen/migration.md": "b0534aec69db1c1ff718de4fd338736d2b3ad2e446b59d8c6ecb244bcf17f1f8",
            "raw/first-attempt.json": "993b93867d45be72e39942475f2e74a81763fb2472b346eed3f41c0b4b11a2a1",
        }
        for name, expected in pins.items():
            self.assertEqual(hashlib.sha256((evidence / name).read_bytes()).hexdigest(), expected, name)
        env = {key: value for key, value in os.environ.items() if not key.startswith("NOODLE_")}
        env["TMPDIR"] = "/private/tmp" if sys.platform == "darwin" else tempfile.gettempdir()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "oracle.json"
            result = subprocess.run([sys.executable, "-B", str(evidence / "frozen/oracle.py"),
                                     str(source), str(output)], env=env, capture_output=True,
                                    text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(output.read_text())
            self.assertEqual(receipt["classification"], "PASS")
            self.assertEqual(len(receipt["cases"]), 18)
            self.assertTrue(all(case["passed"] for case in receipt["cases"]))
            self.assertFalse(receipt["authorizes_landing"])


if __name__ == "__main__":
    unittest.main()
