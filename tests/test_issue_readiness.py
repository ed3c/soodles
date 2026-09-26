"""Focused controls for portable experiment handoff -> local readiness."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import issue_execution
import issue_atom


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReadinessFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.input = self.root / "selected"
        self.evidence = self.root / "evidence"
        self.input.mkdir()
        self.evidence.mkdir()
        self.baseline = self.repo("baseline")
        self.treatment = self.repo("treatment")
        self.python = Path(sys.executable).resolve()
        self.issue = 157
        self.pr = 158
        self.write(self.input / "observer-capture-selection-v2.json", "{}\n")
        self.write(self.input / "observer.py", "# external observer\n")
        self.write(self.input / "capture-plan.md", "capture plan\n")
        self.write(self.input / "task.md", "Assess the supplied comparison and report the supported result.\n")
        self.cases = []
        for name in ("matched_legal", "mismatched_exposure", "missing_observation"):
            folder = self.input / "cases" / name
            folder.mkdir(parents=True)
            specs = {}
            for filename, content in (("raw.json", '{"runs":[]}\n'),
                                      ("gates.json", '{"schema":1}\n'),
                                      ("manifest.json", '{"schema":2}\n')):
                path = folder / filename
                self.write(path, content)
                specs[filename.split(".")[0]] = {
                    "path": str(path.relative_to(self.input)), "sha256": sha(path)}
            self.cases.append({"id": name, "inputs": specs})
        self.authorization = self.root / "authorization.json"
        self.save(self.authorization, {
            "owner": "external-supervisor", "repository": "ed3c/soodles",
            "issue": {"number": self.issue},
            "control_root": str(self.root / "control"),
            "carrier": {"platform": "fixture", "codex": {"model": "fixture"}}})
        self.handoff = self.root / "handoff.json"
        self.local = self.root / "local.json"
        self.output = self.evidence / "readiness"
        self.write_repo_files(self.baseline)
        self.write_repo_files(self.treatment)
        self.save_handoff()
        self.save_local()

    def close(self):
        self.temp.cleanup()

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def save(self, path, value):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    def git(self, root, *args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def repo(self, name):
        root = self.root / name
        root.mkdir()
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/ed3c/soodles.git"],
                       cwd=root, check=True)
        (root / "seed").write_text(name + "\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-m", name], cwd=root, check=True, capture_output=True)
        return root

    def write_repo_files(self, root):
        paths = [
            ".agents/skills/verify-soodles/features/pclass-context.md",
            ".agents/skills/verify-soodles/scripts/replay_pclass.py",
            ".agents/skills/verify-soodles/scripts/observe_pclass.py",
            ".agents/skills/verify-soodles/scripts/decide_pclass.py",
        ]
        for rel in paths:
            self.write(root / rel, rel + "\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-m", "experiment files"], cwd=root, check=True, capture_output=True)

    def arm(self, root):
        def spec(rel):
            path = root / rel
            return {"path": rel, "sha256": sha(path)}
        return {
            "ref": self.git(root, "rev-parse", "HEAD"),
            "instruction": spec(".agents/skills/verify-soodles/features/pclass-context.md"),
            "replay": {
                "script": spec(".agents/skills/verify-soodles/scripts/replay_pclass.py"),
                "observer": spec(".agents/skills/verify-soodles/scripts/observe_pclass.py"),
                "decider": spec(".agents/skills/verify-soodles/scripts/decide_pclass.py"),
            },
        }

    def save_handoff(self):
        def external(name):
            path = self.input / name
            return {"path": name, "sha256": sha(path)}
        self.save(self.handoff, {
            "schema": 1, "kind": "pclass-local-experiment",
            "repository": "ed3c/soodles", "origin_issue": self.issue, "origin_pr": self.pr,
            "selection": {
                "observer_capture": external("observer-capture-selection-v2.json"),
                "observer": external("observer.py"), "capture_plan": external("capture-plan.md")},
            "task": external("task.md"),
            "arms": {"baseline": self.arm(self.baseline), "treatment": self.arm(self.treatment)},
            "cases": self.cases, "primary_outcome": "unsupported_admission",
            "permitted_effects": [],
        })

    def save_local(self):
        self.save(self.local, {
            "schema": 1, "owner": "external-supervisor", "origin_issue": self.issue,
            "authorization": {"path": str(self.authorization), "sha256": sha(self.authorization)},
            "input_root": str(self.input), "evidence_root": str(self.evidence),
            "output_root": str(self.output),
            "workdirs": {"baseline": str(self.baseline), "treatment": str(self.treatment)},
            "python": {"path": str(self.python), "sha256": sha(self.python)},
        })

    def run(self):
        def validate(path, expected_digest):
            path = Path(path)
            if not path.is_file():
                raise issue_atom.AtomRefusal(
                    "authorization.path", "FileNotFoundError",
                    "local_execution_authorization")
            actual = sha(path)
            if actual != expected_digest:
                raise issue_atom.AtomRefusal(
                    "authorization.digest", actual, "matching_external_digest")
            return json.loads(path.read_text()), actual

        with patch("issue_atom.validate_authorization", side_effect=validate) as owner:
            result = issue_execution.readiness(
                str(self.handoff), sha(self.handoff), str(self.local), sha(self.local))
        self.authorization_owner_call = owner.call_args
        return result


class IssueReadinessTests(unittest.TestCase):
    def setUp(self):
        self.f = ReadinessFixture()

    def tearDown(self):
        self.f.close()

    def test_complete_binding_materializes_exactly_six_runs(self):
        result = self.f.run()
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["owner"], "issue.readiness")
        self.assertFalse(result["authorizes_landing"])
        self.assertEqual(len(result["runs"]), 6)
        self.assertEqual(len({row["run_id"] for row in result["runs"]}), 6)
        self.assertEqual(result["next"]["owner"], "supervisor")
        self.assertEqual(result["next"]["required"], ["fresh_consumer_launch"])
        self.assertEqual(
            self.f.authorization_owner_call.args,
            (self.f.authorization, sha(self.f.authorization)))
        for row in result["runs"]:
            packet_path = Path(row["packet"])
            packet = json.loads(packet_path.read_text())
            self.assertEqual(sha(packet_path), row["packet_sha256"])
            self.assertEqual(packet["replay_argv"], row["argv"])
            self.assertEqual(packet["carrier"], json.loads(self.f.authorization.read_text())["carrier"])
            self.assertEqual(packet["permitted_effects"], [])
            self.assertFalse(packet["authorizes_landing"])
            self.assertTrue(Path(packet["evidence_dir"]).is_relative_to(self.f.evidence))

    def test_foreign_authorization_refuses_before_materialization(self):
        auth = json.loads(self.f.authorization.read_text())
        auth["issue"]["number"] = 156
        self.f.save(self.f.authorization, auth)
        self.f.save_local()
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.invalid["field"], "local.authorization.identity")
        self.assertEqual(caught.exception.next["required"], ["issue_scoped_local_execution_authorization"])
        self.assertFalse(self.f.output.exists())

    def test_missing_authorization_is_typed_and_has_no_output(self):
        self.f.authorization.unlink()
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.next["owner"], "external-supervisor")
        self.assertEqual(caught.exception.next["required"], ["local_execution_authorization"])
        self.assertEqual(caught.exception.invalid["field"], "local.authorization.path")
        self.assertFalse(self.f.output.exists())

    def test_wrong_head_and_dirty_workdir_refuse(self):
        handoff = json.loads(self.f.handoff.read_text())
        handoff["arms"]["baseline"]["ref"] = "0" * 40
        self.f.save(self.f.handoff, handoff)
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.invalid["field"], "local.workdirs.baseline.head")
        self.assertFalse(self.f.output.exists())

        f = ReadinessFixture()
        try:
            (f.baseline / "dirty").write_text("dirty\n")
            with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
                f.run()
            self.assertEqual(caught.exception.invalid["field"], "local.workdirs.baseline.status")
            self.assertFalse(f.output.exists())
        finally:
            f.close()

    def test_selected_input_digest_and_case_membership_are_hard_gates(self):
        handoff = json.loads(self.f.handoff.read_text())
        handoff["selection"]["observer_capture"]["sha256"] = "0" * 64
        self.f.save(self.f.handoff, handoff)
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.invalid["field"],
                         "handoff.selection.observer_capture.sha256")
        self.assertFalse(self.f.output.exists())

        f = ReadinessFixture()
        try:
            handoff = json.loads(f.handoff.read_text())
            handoff["cases"] = handoff["cases"][:2]
            f.save(f.handoff, handoff)
            with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
                f.run()
            self.assertEqual(caught.exception.invalid["field"], "handoff.cases")
            self.assertFalse(f.output.exists())
        finally:
            f.close()

    def test_stale_run_evidence_destination_refuses_before_materialization(self):
        stale = self.f.evidence / "matched_legal--baseline"
        stale.mkdir()
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.invalid["field"],
                         "readiness.evidence_dir.matched_legal--baseline")
        self.assertEqual(caught.exception.next["required"],
                         ["fresh_run_evidence_destinations"])
        self.assertFalse(self.f.output.exists())

    def test_output_and_evidence_must_stay_outside_workdirs(self):
        local = json.loads(self.f.local.read_text())
        local["evidence_root"] = str(self.f.baseline)
        local["output_root"] = str(self.f.baseline / "readiness")
        self.f.save(self.f.local, local)
        with self.assertRaises(issue_execution.AdmissionRefusal) as caught:
            self.f.run()
        self.assertEqual(caught.exception.invalid["field"], "local.evidence_root")
        self.assertFalse(self.f.output.exists())

    def test_cli_missing_inputs_returns_structured_supervisor_refusal(self):
        process = subprocess.run([str(ROOT / "soodles"), "issue", "readiness"],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        receipt = json.loads(process.stdout)
        self.assertEqual(receipt["owner"], "issue.readiness")
        self.assertEqual(receipt["next"]["owner"], "supervisor")
        self.assertNotIn("request", receipt)


if __name__ == "__main__":
    unittest.main()
