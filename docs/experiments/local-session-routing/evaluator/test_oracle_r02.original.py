"""R02 controls; retained C1 is evaluator repair data, never a fresh baseline."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

import test_oracle as previous_controls

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("oracle_r02", ROOT / "evaluator/oracle-r02.py")
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
DESCRIPTOR = ROOT / "host/runs/selection-baseline-c1/descriptor.json"


def actual_c1():
    descriptor = json.loads(DESCRIPTOR.read_bytes())
    facts = json.loads(oracle.read_pin(descriptor["workspace"]))
    capture = oracle.decode_capture({name: oracle.read_pin(pin) for name, pin in descriptor["capture"].items()})
    driver = str(Path(capture["launch"]["cwd"]) / "drive.py")
    drives, _ = oracle.extract_drives(capture, facts, descriptor["workspace"]["path"], driver)
    return descriptor, facts, drives


class SameOwnerControls(unittest.TestCase):
    def test_real_c1_python_dispatch_is_valid_pass(self):
        descriptor, facts, drives = actual_c1()
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0]["record"]["argv"], [facts["host"]["python"], "-B", str(Path(facts["control_root"]) / "soodles.py"), "atom", "run", facts["authorization"]["path"]])
        result = oracle.evaluate(descriptor)
        self.assertEqual(result["evidence_validity"], "VALID")
        self.assertEqual(result["behavior"]["classification"], "PASS", result)
        self.assertEqual(result["cost"]["completed_commands"], 10)

    def test_proved_wrapper_syntax_equivalents(self):
        # In-memory syntax controls grounded in pinned source dispatch, not new runs.
        _, facts, drives = actual_c1()
        root = Path(facts["control_root"])
        auth = facts["authorization"]["path"]
        forms = [
            [facts["entries"]["issue_atom"], "run", auth],
            ["/bin/sh", facts["entries"]["issue_atom"], "run", auth],
            [str(root / "soodles"), "atom", "run", auth],
            [facts["host"]["python"], str(root / "soodles.py"), "atom", "run", auth],
        ]
        for argv in forms:
            with self.subTest(argv=argv):
                changed = copy.deepcopy(drives)
                changed[0]["record"]["argv"] = argv
                self.assertEqual(oracle.judge_behavior(facts, changed)["classification"], "PASS")

    def test_wrong_identity_is_not_same_owner(self):
        _, facts, drives = actual_c1()
        original = drives[0]["record"]["argv"]
        for index, value in ((0, "/wrong/python"), (2, "/wrong/control/soodles.py"), (3, "issue"), (4, "inspect"), (5, "/wrong/authorization.json")):
            with self.subTest(index=index):
                changed = copy.deepcopy(drives)
                changed[0]["record"]["argv"] = list(original)
                changed[0]["record"]["argv"][index] = value
                result = oracle.judge_behavior(facts, changed)
                self.assertEqual(result["classification"], "FAIL")
                self.assertIn("one_exact_owner_invocation", result["barriers"])

    def test_python_shell_script_is_still_invalid_invocation(self):
        _, facts, drives = actual_c1()
        changed = copy.deepcopy(drives)
        changed[0]["record"]["argv"] = [facts["host"]["python"], "-B", facts["entries"]["issue_atom"], "run", facts["authorization"]["path"]]
        self.assertEqual(oracle.judge_behavior(facts, changed)["classification"], "FAIL")


def load_tests(loader, tests, pattern):
    # Reuse existing discriminating controls against the new module in memory.
    # No frozen source file is changed or used as the implementation authority.
    previous_controls.oracle = oracle
    tests.addTests(loader.loadTestsFromModule(previous_controls))
    return tests


if __name__ == "__main__":
    unittest.main()
