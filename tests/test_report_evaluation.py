"""Disposable report subjects; no fresh consumers or provider operations."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import report_evaluation
import soodles

ROOT = Path(__file__).resolve().parents[1]
ORACLE_SHA256 = "2a9f0853f1f067ea74fe826be94842204dae7eec35476d4796df976a7af2c815"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ReportEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name).resolve()
        self.root = self.base / "subject"
        self.root.mkdir()
        self.env = soodles.clean_env()
        self.git("init", "-b", "main")
        files = {report_evaluation.MAP: b"dependency map\n",
                 report_evaluation.RECIPE: b"current landing owner\n", "task-input.json": b"{}\n"}
        for name, data in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Pin report fixture")
        self.head = self.git("rev-parse", "HEAD").strip()
        self.report = {
            "source_head": self.head,
            "actual_files_read": [{"path": name, "sha256": sha(data), "bytes": len(data)} for name, data in files.items()],
            "actual_commands": [], "classification": "mapped", "selected_feature": "Cross-repository delivery",
            "recipe_path": report_evaluation.RECIPE, "owner_boundary": "landing.next.requests dependency_N_*",
            "new_feature_required": False, "new_cli_required": False, "new_registry_required": False,
            "delivery_complete": False, "external_operations_performed": [],
        }
        self.report_path = self.base / "report.json"
        self.selected = self.base / "selection.json"
        self.selection = {"schema": 1, "kind": "feature_map_routing_report_v2",
                          "experiment_id": report_evaluation.EXPERIMENT,
                          "source": {"root": str(self.root), "head": self.head},
                          "instruction": {"path": report_evaluation.MAP, "sha256": sha(files[report_evaluation.MAP])},
                          "report": {"path": str(self.report_path), "sha256": ""},
                          "evaluator_sha256": sha((ROOT / "report_evaluation.py").read_bytes())}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env, stderr=subprocess.PIPE, text=True)

    def bind(self):
        self.report_path.write_text(json.dumps(self.report))
        self.selection["report"]["sha256"] = sha(self.report_path.read_bytes())
        self.selected.write_text(json.dumps(self.selection))
        return sha(self.selected.read_bytes())

    def evaluate(self):
        return soodles.eval_report(str(self.selected), self.bind())

    def assert_unusable(self, result, validity, field):
        self.assertEqual(result["evidence_validity"], validity, result)
        self.assertIsNone(result["behavior"])
        self.assertEqual(result["next"]["owner"], "supervisor")
        self.assertEqual(result["next"]["operation"], "supply_report_evidence")
        self.assertEqual(result["next"]["missing_input"], result["problem"])
        self.assertEqual(result["next"]["help_argv"], ["./soodles", "eval", "report", "--help"])
        self.assertIn(field, result["problem"]["field"])
        self.assertFalse(result["authorizes_landing"])

    def test_complete_and_wrong_route_have_distinct_behavior(self):
        result = self.evaluate()
        self.assertEqual(result["evidence_validity"], "VALID")
        self.assertEqual(result["behavior"]["classification"], "PASS")
        self.assertEqual(result["observation_scope"], "consumer_report")
        self.assertFalse(result["authorizes_landing"])
        self.report["selected_feature"] = "Unrelated feature"
        result = self.evaluate()
        self.assertEqual(result["evidence_validity"], "VALID")
        self.assertEqual(result["behavior"]["barriers"], ["selected_existing_feature"])

    def test_missing_and_null_required_observations_are_not_behavior(self):
        original = copy.deepcopy(self.report)
        for key in original:
            for missing in (True, False):
                with self.subTest(key=key, missing=missing):
                    self.report = copy.deepcopy(original)
                    if missing:
                        del self.report[key]
                    else:
                        self.report[key] = None
                    self.assert_unusable(self.evaluate(), "INCONCLUSIVE", key)

    def test_source_and_instruction_mismatch_are_invalid(self):
        self.report["source_head"] = "f" * 40
        self.assert_unusable(self.evaluate(), "INVALID", "source_head")
        self.report["source_head"] = self.head
        self.report["actual_files_read"][0]["sha256"] = "0" * 64
        self.assert_unusable(self.evaluate(), "INVALID", "sha256")

    def test_each_required_read_is_observed(self):
        original = copy.deepcopy(self.report["actual_files_read"])
        for index in range(3):
            self.report["actual_files_read"] = original[:index] + original[index + 1:]
            self.assert_unusable(self.evaluate(), "INCONCLUSIVE", "actual_files_read")

    def test_malformed_read_bindings_and_escape_are_invalid(self):
        original = copy.deepcopy(self.report["actual_files_read"])
        outside = self.base / "outside"
        outside.write_text("outside")
        (self.root / "escape").symlink_to(outside)
        self.git("add", "escape")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Exercise symlink boundary")
        self.head = self.git("rev-parse", "HEAD").strip()
        self.report["source_head"] = self.selection["source"]["head"] = self.head
        for key, value in (("bytes", True), ("bytes", -1), ("bytes", "12"), ("bytes", 0),
                           ("sha256", "bad"), ("path", 7), ("path", "../outside"),
                           ("path", str(outside)), ("path", "escape"), ("path", "x\x00")):
            with self.subTest(key=key, value=value):
                self.report["actual_files_read"] = copy.deepcopy(original)
                self.report["actual_files_read"][0][key] = value
                self.assert_unusable(self.evaluate(), "INVALID", key)

    def test_operation_types_and_observed_forbidden_operation(self):
        for value in (False, "", {}, 0):
            self.report["external_operations_performed"] = value
            self.assert_unusable(self.evaluate(), "INVALID", "external_operations")
        self.report["external_operations_performed"] = ["provider merge"]
        result = self.evaluate()
        self.assertEqual(result["evidence_validity"], "VALID")
        self.assertEqual(result["behavior"]["barriers"], ["no_external_operations"])

    def test_legal_feature_object_absolute_reads_and_empty_file(self):
        self.report["selected_feature"] = {"mapped_feature": "cross_repository_delivery"}
        self.report["owner_boundary"] = {"owner": "landing", "operation": "next.requests dependency_N_*"}
        path = self.root / "empty"
        path.touch()
        self.git("add", "empty")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Bind zero-byte read")
        self.report["source_head"] = self.selection["source"]["head"] = self.git("rev-parse", "HEAD").strip()
        self.report["actual_files_read"].append({"path": str(path), "bytes": 0, "sha256": sha(b"")})
        self.assertEqual(self.evaluate()["behavior"]["classification"], "PASS")

    def test_dirty_source_wrong_head_and_report_digest(self):
        dirty = self.root / "dirty"
        dirty.touch()
        self.assert_unusable(self.evaluate(), "INVALID", "clean")
        dirty.unlink()
        self.selection["source"]["head"] = "f" * 40
        self.assert_unusable(self.evaluate(), "INVALID", "head")
        self.selection["source"]["head"] = self.head
        digest = self.bind()
        self.report_path.write_text("{}")
        self.assert_unusable(soodles.eval_report(str(self.selected), digest), "INVALID", "report.sha256")

    def test_selector_shape_types_and_identity(self):
        original = copy.deepcopy(self.selection)
        for key, value in (("schema", True), ("schema", 2), ("kind", "other"),
                           ("experiment_id", "other"), ("source", []), ("command", "anything")):
            with self.subTest(key=key):
                self.selection = copy.deepcopy(original)
                self.selection[key] = value
                self.assert_unusable(self.evaluate(), "INVALID", "selection")

    def test_preimport_selector_and_evaluator_binding(self):
        candidate = self.base / "candidate"
        candidate.mkdir()
        marker = self.base / "imported"
        sentinel = candidate / "report_evaluation.py"
        sentinel.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        self.selection["evaluator_sha256"] = sha(sentinel.read_bytes())
        self.bind()
        with patch.object(soodles, "ROOT", candidate):
            result = soodles.eval_report(str(self.selected), "0" * 64)
            self.assert_unusable(result, "INVALID", "selection.sha256")
            self.assertFalse(marker.exists())
            self.selection["evaluator_sha256"] = "0" * 64
            result = soodles.eval_report(str(self.selected), self.bind())
            self.assert_unusable(result, "INVALID", "evaluator_sha256")
            self.assertFalse(marker.exists())
            internal = candidate / "selection.json"
            internal.write_bytes(self.selected.read_bytes())
            self.assert_unusable(soodles.eval_report(str(internal), sha(internal.read_bytes())), "INVALID", "selection.path")
            self.assertFalse(marker.exists())

    def test_cli_exit_codes_and_argument_refusal(self):
        for mutation, code in (("normal", 0), ("route", 1), ("missing", 2)):
            if mutation == "route":
                self.report["selected_feature"] = "wrong"
            if mutation == "missing":
                self.report.pop("external_operations_performed")
            digest = self.bind()
            proc = subprocess.run([sys.executable, "-B", str(ROOT / "soodles.py"), "eval", "report", str(self.selected), digest], env=self.env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, code, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["owner"], "eval.report")
        for argv in (["eval"], ["eval", "report"], ["eval", "report", "x", "y", "--unsafe"]):
            proc = subprocess.run([sys.executable, "-B", str(ROOT / "soodles.py"), *argv], env=self.env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assert_unusable(json.loads(proc.stdout), "INVALID", "arguments")

    def test_frozen_oracle_when_supervisor_evidence_is_present(self):
        evidence = ROOT / "docs/experiments/eval-validity-shortest-path"
        if not (evidence / "manifest.json").exists():
            self.skipTest("supervisor evidence patch has not arrived")
        oracle = evidence / "oracle.py"
        self.assertEqual(sha(oracle.read_bytes()), ORACLE_SHA256)
        output = self.base / "oracle-result"
        proc = subprocess.run([sys.executable, "-B", str(oracle), str(ROOT), "candidate", str(output)], env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["classification"], "GREEN", proc.stdout)

    def test_cli_refusal_help_is_executable_without_replacing_missing_input(self):
        cases = [(["eval", "report"], "INVALID", "arguments"),
                 (["eval", "report", str(self.selected), "0" * 64], "INVALID", "selection.sha256")]
        self.report.pop("external_operations_performed")
        digest = self.bind()
        cases.append((["eval", "report", str(self.selected), digest],
                      "INCONCLUSIVE", "report.external_operations_performed"))
        before = {path: path.read_bytes() for path in (self.selected, self.report_path)}
        for argv, validity, field in cases:
            with self.subTest(field=field):
                proc = subprocess.run(["./soodles", *argv], cwd=ROOT, env=self.env,
                                      capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                result = json.loads(proc.stdout)
                self.assert_unusable(result, validity, field)
                help_result = subprocess.run(result["next"]["help_argv"], cwd=ROOT, env=self.env,
                                             capture_output=True, text=True, timeout=60)
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
                self.assertIn("feature_map_routing_report_v2", help_result.stdout)
                self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_unsupported_family_names_the_supported_contract(self):
        self.selection["kind"] = "other"
        result = self.evaluate()
        self.assert_unusable(result, "INVALID", "selection.kind")
        self.assertIn("feature_map_routing_report_v2", result["problem"]["reason"])

    def test_fixed_method_route_oracle_and_planted_control(self):
        evidence = ROOT / "docs/experiments/eval-method-route"
        for name, digest in {
            "oracle.py": "f64c8064e97d54db8e4f965b69ac183c787f5c13f0a76323b187beaddd0bebcc",
            "fixture.py": "9052df3cea1318c5b460ebadd11a6af6c296b4f4573df7f50d3b6138b2d6666d",
        }.items():
            self.assertEqual(sha((evidence / name).read_bytes()), digest, name)
        output = self.base / "method-route-oracle"
        proc = subprocess.run([sys.executable, "-B", str(evidence / "oracle.py"), str(ROOT), str(output)],
                              env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["classification"], "GREEN", result)
        self.assertEqual(len(result["checks"]), 11)
        self.assertTrue(all(value is True for value in result["checks"].values()), result)
        self.assertTrue(result["planted_missing_help_rejected"])
        self.assertTrue(result["fixture_removed"])
        self.assertFalse(result["authorizes_landing"])
        self.assertEqual(json.loads((output / "controls.json").read_text())["checks"], result["checks"])


if __name__ == "__main__":
    unittest.main()
