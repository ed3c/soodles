import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from issue_admission import AdmissionRefusal
from issue_execution import inspect_schedule


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/admission-recovery-portable/preserved-soodles-input"
SESSION = "schedule-20260916-170423-d53732"


class ScheduleRoleBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.spawn_path = self.root / ".noodle/sessions" / SESSION / "spawn.json"
        self.spawn_path.parent.mkdir(parents=True)
        self.spawn = json.loads((FIXTURE / ".noodle/sessions" / SESSION / "spawn.json").read_text())
        # Adapt only the disposable host path; retained source evidence is unchanged.
        self.spawn["worktree_path"] = str(self.root)
        self.spawn_path.write_text(json.dumps(self.spawn))
        self.env = {"NOODLE_SESSION_ID": SESSION, "NOODLE_WORKTREE": str(self.root)}

    def test_preserved_scheduler_requires_supervisor_launcher(self):
        meta = json.loads((FIXTURE / ".noodle/sessions" / SESSION / "meta.json").read_text())
        self.assertIn("SOODLES_ADMISSION_LAUNCHER is unset", meta["current_action"])
        self.assertIn("exit 64", meta["current_action"])
        with self.assertRaises(AdmissionRefusal) as caught:
            inspect_schedule(self.root, self.env)
        self.assertEqual(caught.exception.invalid["field"], "scheduler.launcher")
        self.assertEqual(caught.exception.next["owner"], "supervisor")

    def test_generic_session_has_no_launcher_prerequisite(self):
        result = inspect_schedule(self.root, {})
        self.assertEqual(result["action"], "not_applicable")
        self.assertIsNone(result["next"])
        self.assertFalse(result["authorizes_landing"])

    def test_mismatched_role_refuses_before_missing_launcher(self):
        cases = [("session_id", "foreign"), ("skill", "execute"),
                 ("worktree_path", str(self.root / "foreign")),
                 ("worktree_path", None), ("worktree_path", "")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                spawn = {**self.spawn, field: value}
                self.spawn_path.write_text(json.dumps(spawn))
                with self.assertRaises(AdmissionRefusal) as caught:
                    inspect_schedule(self.root, self.env)
                self.assertEqual(caught.exception.invalid["field"], "scheduler.spawn." + field)
                self.assertEqual(caught.exception.next["owner"], "Noodle")

    def test_missing_malformed_or_foreign_dispatch_inputs(self):
        for raw in ("[]", "{invalid"):
            self.spawn_path.write_text(raw)
            with self.assertRaises(AdmissionRefusal) as caught:
                inspect_schedule(self.root, self.env)
            self.assertEqual(caught.exception.invalid["field"], "scheduler.spawn")
        self.spawn_path.unlink()
        with self.assertRaises(AdmissionRefusal) as caught:
            inspect_schedule(self.root, self.env)
        self.assertEqual(caught.exception.invalid["field"], "scheduler.spawn")
        for env, field in [
            ({**self.env, "NOODLE_SESSION_ID": "../foreign"}, "scheduler.session_id"),
            ({"NOODLE_SESSION_ID": SESSION}, "scheduler.control_root"),
            ({**self.env, "NOODLE_WORKTREE": str(self.root / "foreign")}, "scheduler.control_root"),
        ]:
            with self.assertRaises(AdmissionRefusal) as caught:
                inspect_schedule(self.root, env)
            self.assertEqual(caught.exception.invalid["field"], field)

    def test_actual_cli_projects_exact_argv_without_executing_launcher(self):
        launcher = self.root / "selected launcher"
        marker = self.root / "unexpected-effect"
        launcher.write_text("#!/bin/sh\ntouch '" + str(marker) + "'\n")
        launcher.chmod(0o755)
        before = self.spawn_path.read_bytes()
        env = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
        env.update(self.env)
        env["SOODLES_ADMISSION_LAUNCHER"] = str(launcher)
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "soodles.py"), "issue", "inspect"],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["action"], "ready")
        self.assertEqual(output["next"]["argv"], [str(launcher), "automatic"])
        self.assertFalse(output["authorizes_landing"])
        self.assertFalse(marker.exists())
        self.assertEqual(self.spawn_path.read_bytes(), before)
        launcher.chmod(0o644)
        with self.assertRaises(AdmissionRefusal) as caught:
            inspect_schedule(self.root, env)
        self.assertEqual(caught.exception.invalid["field"], "scheduler.launcher")


if __name__ == "__main__":
    unittest.main()
