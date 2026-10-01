import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


def parser_source():
    workflow = (ROOT / ".github/workflows/runtime.yml").read_text()
    return textwrap.dedent(workflow.split("issue=\"$(python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]) + "\n"


def execute(source, body):
    return subprocess.run([sys.executable, "-B", "-c", source],
                          env={**os.environ, "PR_BODY": body}, capture_output=True,
                          text=True, timeout=10)


class DeliveryRefsTests(unittest.TestCase):
    def test_actual_runtime_parser_accepts_publisher_spelling_and_legacy_short(self):
        for body in ("Refs #99\n", "Refs ed3c/soodles#99\n"):
            result = execute(parser_source(), body)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "99\n")
        for body in ("Refs other/repo#99\n", "Refs #0\n", "Closes #99\n", "",
                     "Refs #99\nRefs ed3c/soodles#99\n"):
            self.assertNotEqual(execute(parser_source(), body).returncode, 0)


if __name__ == "__main__":
    unittest.main()
