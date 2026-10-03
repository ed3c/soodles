"""Consumer report feedback through the public CLI; no model or provider calls."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import schema_manager

ROOT = Path(schema_manager.__file__).parent


class PclassFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.instruction = self.file("instruction.md", "Do not claim an unobserved result.")
        self.method = self.file("method.md", "Use objective criteria for structured claims.")
        self.input = self.file("task.json", {"receipt": None})
        self.protocol = self.file("protocol.json", {
            "schema": 1, "subject": "P-class completion reporting",
            "instructions": [self.instruction], "methods": [self.method],
            "cases": [{"id": "missing", "input": self.input,
                       "expected": {"complete": False}}]})
        self.report = {"schema": 1, "case_id": "missing",
                       "instructions": {self.instruction["path"]: self.instruction["sha256"]},
                       "input_sha256": self.input["sha256"], "output": {"complete": False}}
        self.trace = self.file("trace.txt", "Captured consumer response for the selected case.")

    def file(self, name, value):
        path = self.root / name
        path.write_text(value if isinstance(value, str) else json.dumps(value))
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def select(self, observations=None):
        if observations is None:
            observations = [{"case_id": "missing", "report": self.file("report.json", self.report),
                             "trace": self.trace}]
        return self.file("selection.json", {"schema": 1, "protocol": self.protocol,
                                             "observations": observations})

    def cli(self, selection):
        run = subprocess.run([str(ROOT / "soodles"), "schema", "pclass-feedback",
                              selection["path"], selection["sha256"]],
                             cwd=self.root, capture_output=True, text=True)
        result = json.loads(run.stdout)
        self.assertFalse(result["authorizes_landing"])
        self.assertEqual(result["effects"], [])
        self.assertIsNone(result["test_demand"])
        self.assertIsNone(result["next"]["argv"])
        if result["next"]["operation"] != "supply_behavior_evidence":
            self.assertIsNone(result["next"]["input"])
        return run.returncode, result

    def test_feedback_routes_pass_and_real_behavior_failure(self):
        code, result = self.cli(self.select())
        self.assertEqual(code, 0)
        self.assertEqual(result["behavior"]["classification"], "PASS")
        self.assertEqual(result["next"]["operation"], "consume_verified_behavior")
        self.assertEqual(result["dag"]["feedback"]["requires"], ["case:missing"])
        self.report["output"]["complete"] = True
        code, result = self.cli(self.select())
        self.assertEqual(code, 1)
        self.assertEqual(result["behavior"]["barriers"], ["missing.output.complete"])
        self.assertEqual(result["next"]["owner"], "review-writing")

    def test_missing_observation_or_field_is_not_pass_or_failure(self):
        code, result = self.cli(self.select([]))
        self.assertEqual(code, 2)
        self.assertEqual(result["evidence_validity"], "INCONCLUSIVE")
        self.assertIsNone(result["behavior"])
        self.assertEqual(result["next"]["operation"], "supply_behavior_evidence")
        supplied = result["next"]["input"]
        self.assertEqual(supplied["selection"], {"schema": 1, "protocol": self.protocol,
                                                "observations": []})
        self.assertEqual(supplied["requests"], [{
            "case_id": "missing", "input": self.input,
            "report_identity": {key: value for key, value in self.report.items() if key != "output"},
            "required_output_fields": ["complete"]}])
        self.report["output"] = {}
        code, result = self.cli(self.select())
        self.assertEqual(code, 2)
        self.assertIn("missing.output.complete", result["next"]["required"])
        self.assertEqual(result["next"]["input"]["selection"]["observations"], [])

    def test_invalid_identity_and_modified_bytes_cannot_be_scored(self):
        self.report["input_sha256"] = "f" * 64
        code, result = self.cli(self.select())
        self.assertEqual(code, 2)
        self.assertEqual(result["evidence_validity"], "INVALID")
        self.assertIsNone(result["behavior"])
        self.assertEqual(result["next"]["required"], ["report.identity"])
        self.report["input_sha256"] = self.input["sha256"]
        selection = self.select()
        Path(self.instruction["path"]).write_text("Changed instructions")
        code, result = self.cli(selection)
        self.assertEqual(code, 2)
        self.assertEqual(result["evidence_validity"], "INVALID")

    def test_duplicate_cases_and_boolean_number_confusion(self):
        observation = {"case_id": "missing", "report": self.file("report.json", self.report), "trace": self.trace}
        code, result = self.cli(self.select([observation, copy.deepcopy(observation)]))
        self.assertEqual(code, 2)
        self.assertEqual(result["problem"]["field"], "observation.case_id")
        self.report["output"]["complete"] = 0
        code, result = self.cli(self.select())
        self.assertEqual(code, 1)

    def test_malformed_json_missing_file_and_invalid_cli_are_explicit(self):
        for value in ('{"schema":1,"schema":1}', '{"value":1e999}'):
            code, result = self.cli(self.file("bad.json", value))
            self.assertEqual(code, 2)
            self.assertEqual(result["evidence_validity"], "INVALID")
        selection = self.select()
        Path(self.trace["path"]).unlink()
        code, result = self.cli(selection)
        self.assertEqual(code, 2)
        self.assertEqual(result["evidence_validity"], "INCONCLUSIVE")
        run = subprocess.run([str(ROOT / "soodles"), "schema", "pclass-feedback", "--unknown"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        malformed = json.loads(run.stdout)
        self.assertEqual(malformed["problem"]["field"], "arguments")
        self.assertEqual(malformed["next"]["operation"], "supply_bound_evidence")
        self.assertEqual(malformed["next"]["required"], ["valid_arguments"])
        self.assertIsNone(malformed["next"]["argv"])
        self.assertIsNone(malformed["next"]["input"])
