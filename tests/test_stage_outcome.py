"""Disposable admitted owners; sentinel event writes are not provider effects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import stage_outcome
import test_issue_execution


class StageOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = f = test_issue_execution.IssueExecutionTests("runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.mode = f.directory / "mode"
        self.calls = f.directory / "calls"
        self.mode.write_text("ok")
        f.binary.write_text("#!" + sys.executable + "\n" + '''
import json, pathlib, sys
base = pathlib.Path(__file__).parent
with (base / 'calls').open('a') as out: out.write(json.dumps(sys.argv[1:]) + '\\n')
mode = (base / 'mode').read_text()
args = sys.argv
control = pathlib.Path(args[args.index('--project-dir') + 1])
session = args[args.index('--session') + 1]
payload = json.loads(args[args.index('--payload') + 1])
if mode == 'failure': sys.exit(7)
if mode == 'no-write': sys.exit(0)
if mode == 'mismatch': payload['stage_index'] = 9
if mode == 'wrong-type': payload['stage_index'] = False
event = {'type': 'stage_message', 'session_id': session, 'payload': payload}
path = control / '.noodle/sessions' / session / 'events.ndjson'
with path.open('a') as out:
    out.write(json.dumps(event) + '\\n')
    if mode == 'duplicate': out.write(json.dumps(event) + '\\n')
if mode == 'write-failure': sys.exit(7)
''')
        pin = hashlib.sha256(f.binary.read_bytes()).hexdigest()
        for name in ("noodle", "codex"):
            f.envelope["execution"]["carrier"][name]["sha256"] = pin
        f.bind_envelope()
        f.admit("supervised")
        f.promote_fixture()
        self.stage = f.snapshot["state"]["orders"][f.env["NOODLE_ORDER_ID"]]["stages"][0]
        self.stage["status"] = "running"
        self.stage["attempts"][-1].update(status="running", session_id=f.session)
        f.save_owner()
        self.launcher = f.directory / "launcher"
        self.launcher.write_text("#!/bin/sh\nexit 1\n")
        self.launcher.chmod(0o755)
        f.env["SOODLES_ADMISSION_LAUNCHER"] = str(self.launcher)
        self.session_dir = f.runtime / "sessions" / f.session
        self.events = self.session_dir / "events.ndjson"
        self.events.write_text("")

    def invoke(self, outcome="completed", message="fixture task checked"):
        return subprocess.run([str(Path(stage_outcome.__file__).with_name("stage-outcome")),
                               outcome, message], cwd=self.fixture.worktree,
                              env={**os.environ, **self.fixture.env},
                              capture_output=True, text=True)

    def refused(self, result, effects=0):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["status"], "refused")
        self.assertFalse(receipt["authorizes_landing"])
        self.assertTrue(receipt["invalid"])
        self.assertTrue(receipt["next"]["owner"])
        self.assertTrue(receipt["next"]["required"])
        count = len(self.calls.read_text().splitlines()) if self.calls.exists() else 0
        self.assertEqual(count, effects)
        return receipt

    def test_all_outcomes_and_duplicate_refusal(self):
        for outcome in stage_outcome.OUTCOMES:
            with self.subTest(outcome=outcome):
                self.events.write_text("")
                self.calls.unlink(missing_ok=True)
                result = self.invoke(outcome)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt["status"], "recorded")
                payload = receipt["event"]["payload"]
                self.assertEqual(payload, {"outcome": outcome, "message": "fixture task checked",
                                          "blocking": outcome != "completed", "order_id": "soodles-18",
                                          "stage_index": 0})
                self.assertEqual(len(self.events.read_text().splitlines()), 1)
                self.refused(self.invoke(outcome), effects=1)

    def test_empty_message_and_unknown_choice(self):
        for outcome, message in (("completed", "  "), ("unknown", "message")):
            self.refused(self.invoke(outcome, message))

    def test_foreign_or_missing_environment(self):
        f = self.fixture
        for key in list(f.env):
            original = f.env[key]
            for value in ("", "foreign"):
                with self.subTest(key=key, value=value):
                    f.env[key] = value
                    self.refused(self.invoke())
            f.env[key] = original

    def test_missing_or_foreign_worker_role(self):
        path = self.session_dir / "spawn.json"
        spawn = json.loads(path.read_text())
        for role in (None, "schedule", "foreign"):
            with self.subTest(role=role):
                altered = dict(spawn)
                if role is None:
                    altered.pop("skill")
                else:
                    altered["skill"] = role
                path.write_text(json.dumps(altered))
                self.refused(self.invoke())

    def test_changed_envelope_and_binary(self):
        f = self.fixture
        original = f.path.read_bytes()
        f.path.write_bytes(original + b" ")
        self.refused(self.invoke())
        f.path.write_bytes(original)
        f.binary.write_text(f.binary.read_text() + "\n# changed\n")
        self.refused(self.invoke())

    def test_missing_pin_and_changed_prompt_contract(self):
        prompt = json.loads(self.stage["prompt"])
        for key in ("envelope_sha256", "contract", "task"):
            with self.subTest(key=key):
                altered = dict(prompt)
                altered.pop(key)
                self.stage["prompt"] = json.dumps(altered)
                self.fixture.save_owner()
                self.refused(self.invoke())

    def test_foreign_running_attempt(self):
        self.stage["attempts"][-1]["session_id"] = "foreign"
        self.fixture.save_owner()
        self.refused(self.invoke())

    def test_process_failure_and_contradictory_readback_do_not_retry(self):
        for mode in ("failure", "no-write", "mismatch", "wrong-type", "duplicate", "write-failure"):
            with self.subTest(mode=mode):
                self.events.write_text("")
                self.calls.unlink(missing_ok=True)
                self.mode.write_text(mode)
                receipt = self.refused(self.invoke(), effects=1)
                self.assertEqual(receipt["next"]["owner"], "Noodle")
                self.assertIn("current_session_event_readback", receipt["next"]["required"])

    def test_existing_unknown_typed_event_refuses(self):
        self.events.write_text(json.dumps({"type": "stage_message", "session_id": "foreign",
                                          "payload": {"outcome": "unknown"}}) + "\n")
        self.refused(self.invoke())

    def test_first_event_creates_log_but_malformed_events_refuse(self):
        self.events.unlink()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(self.events.is_file())
        self.calls.unlink()
        self.events.write_text("broken json\n")
        self.refused(self.invoke())

    def test_completion_accepts_committed_permitted_changes(self):
        f = self.fixture
        (f.worktree / "allowed.py").write_text("print('complete')\n")
        subprocess.run(["git", "add", "allowed.py"], cwd=f.worktree, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-m", "Complete fixture to prove completion accepts commits"],
                       cwd=f.worktree, check=True, capture_output=True)
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_help_has_closed_choices(self):
        result = subprocess.run([str(Path(stage_outcome.__file__).with_name("stage-outcome")), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("{completed,blocked,failed}", result.stdout)
        self.assertIn("SOODLES_ADMISSION_LAUNCHER", result.stdout)


if __name__ == "__main__":
    unittest.main()
