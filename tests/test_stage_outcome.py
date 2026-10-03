"""Disposable admitted owners; sentinel event writes are not provider effects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import stage_outcome
import supervisor_admission
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
if 'interruption' in sys.argv:
    print((base / 'interruption.json').read_text())
    sys.exit(0)
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

    def recovered_bundle(self):
        f = self.fixture
        original = f.directory / "original-envelope.json"
        original.write_bytes(f.path.read_bytes())
        e = f.envelope["execution"]
        subject = f.envelope["repository"] + "#" + str(f.envelope["issue"])
        custody = {"order_id": e["order_id"], "stage_index": e["stage_index"],
                   "subject": subject, "envelope_sha256": f.pin,
                   "worktree_name": e["worktree"], "worktree_path": str(f.worktree),
                   "branch": e["worktree"], "head": e["source_head"]}
        e["recovery_context"] = {
            "kind": "prepublication_interruption",
            "original_envelope": {"path": str(original), "sha256": f.pin},
            "custody": custody, "custody_sha256": "c" * 64,
            "evidence_path": str(f.runtime / "interruptions" / hashlib.sha256(
                (e["order_id"] + "\n" + subject).encode()).hexdigest())}
        f.bind_envelope()
        prompt = json.loads(self.stage["prompt"])
        self.stage["prompt"] = json.dumps(stage_outcome.projection(
            {**f.envelope, "contract": prompt["contract"], "issue_body": prompt["issue_body"]},
            f.pin, prompt["route"]))
        self.stage["attempts"][-1]["attempt_id"] = "successor-attempt"
        f.save_owner()
        self.interruption = f.directory / "interruption.json"
        self.native_receipt = {
            "owner": "Noodle interrupted execution", "status": "dispatched",
            **{key: e["recovery_context"][key] for key in ("custody", "custody_sha256", "evidence_path")},
            "successor": {"attempt_id": "successor-attempt", "session_id": f.session},
            "candidate_unchanged": False, "candidate_invalid": ["writer changed allowed.py"]}
        self.interruption.write_text(json.dumps(self.native_receipt))
        self.install_bundle()

    def install_bundle(self):
        f = self.fixture
        runtime = []
        for name in supervisor_admission.BUNDLE_PATHS:
            path = f.directory / "runtime" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(Path(supervisor_admission.__file__).with_name(name).read_bytes())
            runtime.append({"path": "runtime/" + name,
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        raw = json.dumps({"runtime": runtime}).encode()
        (f.directory / "manifest.json").write_bytes(raw)
        self.launcher.write_text(supervisor_admission._launcher_text(
            f.root, f.pin, hashlib.sha256(raw).hexdigest(), sys.executable))

    def invoke_bundle(self, *args):
        return subprocess.run([str(self.launcher), "stage-outcome", *args],
                              cwd=self.fixture.worktree,
                              env={**os.environ, **self.fixture.env},
                              capture_output=True, text=True)

    def test_recovery_bundle_reports_changed_candidate_for_unique_successor(self):
        self.recovered_bundle()
        (self.fixture.worktree / "allowed.py").write_text("print('recovered')\n")
        prompt = json.loads(self.stage["prompt"])
        entry = prompt["recovery_context"]["stage_outcome"]
        self.assertIn('"$SOODLES_ADMISSION_LAUNCHER" stage-outcome', entry["outcome_command"])
        self.assertIn("stage-outcome feedback", entry["feedback_command"])
        self.assertEqual(prompt["task"], self.fixture.envelope["execution"]["task"])
        result = self.invoke_bundle("completed", "original candidate continued")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["event"]["session_id"], self.fixture.session)
        self.assertEqual(len(self.events.read_text().splitlines()), 1)
        self.refused(self.invoke_bundle("completed", "duplicate"), effects=1)

    def test_recovery_bundle_rejects_foreign_successor_and_custody_without_event(self):
        self.recovered_bundle()
        for field in ("session_id", "attempt_id"):
            with self.subTest(field=field):
                receipt = {**self.native_receipt,
                           "successor": {**self.native_receipt["successor"], field: "foreign"}}
                self.interruption.write_text(json.dumps(receipt))
                rejected = self.refused(self.invoke_bundle("blocked", "gap"))
                self.assertEqual(rejected["invalid"]["field"], "worker.recovery.successor")
        self.interruption.write_text(json.dumps({**self.native_receipt, "custody_sha256": "d" * 64}))
        rejected = self.refused(self.invoke_bundle("blocked", "gap"))
        self.assertEqual(rejected["invalid"]["field"], "interruption.custody")
        self.assertEqual(self.events.read_text(), "")

    def test_recovery_bundle_tamper_refuses_before_event(self):
        self.recovered_bundle()
        for name in ("stage_outcome.py", "schema_manager.py", "system_context.py", "test_manager.py"):
            with self.subTest(name=name):
                path = self.fixture.directory / "runtime" / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n# changed\n")
                receipt = self.refused(self.invoke_bundle("blocked", "gap"))
                self.assertEqual(receipt["invalid"]["field"], "launcher.runtime_sha256")
                self.assertEqual(self.events.read_text(), "")
                path.write_bytes(original)

    def test_recovery_readback_allows_owner_metadata_refresh(self):
        self.recovered_bundle()
        def refreshed(binding):
            self.stage["updated_at"] = "owner refreshed metadata"
            self.stage["attempts"][-1]["observed_at"] = "later observation"
            self.fixture.save_owner()
            return self.native_receipt
        with patch.object(stage_outcome, "interruption_readback", side_effect=refreshed):
            result = stage_outcome.report("blocked", "gap", self.fixture.worktree, self.fixture.env)
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(len(self.events.read_text().splitlines()), 1)

    def test_recovery_readback_rejects_changed_current_attempt(self):
        self.recovered_bundle()
        def changed(binding):
            self.stage["attempts"][-1]["attempt_id"] = "replacement"
            self.fixture.save_owner()
            return self.native_receipt
        with patch.object(stage_outcome, "interruption_readback", side_effect=changed):
            with self.assertRaisesRegex(stage_outcome.AdmissionRefusal, "worker.recovery.current"):
                stage_outcome.report("blocked", "gap", self.fixture.worktree, self.fixture.env)
        self.assertEqual(self.events.read_text(), "")
        self.assertFalse(self.calls.exists())

    def test_bundle_feedback_loads_pinned_dependency_closure(self):
        self.recovered_bundle()
        f = self.fixture
        for name in ("stage_outcome.py", "schema_manager.py", "system_context.py", "test_manager.py"):
            (f.worktree / name).write_text("raise RuntimeError('candidate module must not load')\n")
        def ref(name, value):
            path = f.directory / name
            path.write_text(value if isinstance(value, str) else json.dumps(value))
            return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        prompt = json.loads(self.stage["prompt"])
        requirement = ref("requirements.json", {"task": prompt["task"], "contract": prompt["contract"]})
        instruction = ref("instruction.md", "Retain missing evidence.")
        method = ref("method.md", "Read the selected evidence.")
        case = ref("case.json", {"evidence": None})
        protocol = ref("protocol.json", {"schema": 2, "subject": "fixture feedback",
            "requirements": requirement, "instructions": [instruction], "methods": [method],
            "cases": [{"id": "missing", "input": case, "expected": {"complete": False}}]})
        selection = ref("selection.json", {"schema": 2, "protocol": protocol,
                                          "criteria_review": None, "observations": []})
        result = self.invoke_bundle("feedback", selection["path"], selection["sha256"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["next"]["operation"], "review_criteria")
        self.assertEqual(receipt["feedback"]["test_scope"]["owner"], "test-manager")
        self.assertEqual(len(self.events.read_text().splitlines()), 1)
        self.assertNotEqual(self.invoke_bundle("completed", "missing feedback").returncode, 0)

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
        for key in ("envelope_sha256", "contract", "task", "issue_body"):
            with self.subTest(key=key):
                altered = dict(prompt)
                altered.pop(key)
                self.stage["prompt"] = json.dumps(altered)
                self.fixture.save_owner()
                self.refused(self.invoke())

    def test_changed_body_refuses_before_event_write(self):
        prompt = json.loads(self.stage["prompt"])
        prompt['issue_body'] += '\nChanged scope'
        self.stage['prompt'] = json.dumps(prompt)
        self.fixture.save_owner()
        self.refused(self.invoke())

    def test_malformed_admitted_carrier_is_a_json_refusal(self):
        f = self.fixture
        for value in (None, [], "foreign"):
            with self.subTest(value=value):
                f.envelope["execution"]["carrier"]["codex"] = value
                f.bind_envelope()
                prompt = json.loads(self.stage["prompt"])
                prompt["envelope_sha256"] = f.pin
                self.stage["prompt"] = json.dumps(prompt)
                f.save_owner()
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
