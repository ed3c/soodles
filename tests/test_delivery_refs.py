import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/experiments/fresh-delivery-decisions"


def parser_source():
    workflow = (ROOT / ".github/workflows/runtime.yml").read_text()
    return textwrap.dedent(workflow.split("issue=\"$(python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]) + "\n"


def execute(source, body):
    return subprocess.run([sys.executable, "-B", "-c", source],
                          env={**os.environ, "PR_BODY": body}, capture_output=True,
                          text=True, timeout=10)


class DeliveryRefsTests(unittest.TestCase):
    def test_actual_runtime_parser_accepts_publisher_spelling_and_legacy_short(self):
        before = json.loads((EVIDENCE / "raw/delivery-entry-refusal.json").read_text())
        source = before["baseline_runtime_parser"]
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), before["baseline_runtime_parser_sha256"])
        self.assertNotEqual(execute(source, "Refs ed3c/soodles#99\n").returncode, 0)
        for body in ("Refs #99\n", "Refs ed3c/soodles#99\n"):
            result = execute(parser_source(), body)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "99\n")
        for body in ("Refs other/repo#99\n", "Refs #0\n", "Closes #99\n", "",
                     "Refs #99\nRefs ed3c/soodles#99\n"):
            self.assertNotEqual(execute(parser_source(), body).returncode, 0)

    def test_real_publisher_refusal_is_preserved_before_any_request(self):
        before = json.loads((EVIDENCE / "raw/delivery-entry-refusal.json").read_text())
        output = json.loads(before["stdout"])
        self.assertEqual(output["invalid"], {"field": "pr.Refs", "value": ["#99"]})
        self.assertEqual(before["result"]["exit_code"], 1)
        self.assertFalse(before["checkpoint_exists_after"])
        self.assertNotIn("request", output)
        self.assertEqual(before["provider_readback"]["run"]["head_sha"], before["head"])
        self.assertEqual(before["provider_readback"]["run"]["conclusion"], "success")
        self.assertEqual(hashlib.sha256(before["stdout"].encode()).hexdigest(), before["result"]["stdout_sha256"])


if __name__ == "__main__":
    unittest.main()
