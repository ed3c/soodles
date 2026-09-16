"""Real consumer functions and executable sentinels over explicit provider/owner fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest

import issue_admission as admission
import issue_execution as execution
from test_issue_admission import issue_fixture


class IssueExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.root = self.directory / "control"
        self.root.mkdir()
        self.git("init", "-b", "main")
        (self.root / ".gitignore").write_text(".noodle/\n.worktrees/\n")
        (self.root / "allowed.py").write_text("print('fixture')\n")
        self.git("add", ".")
        self.git("-c", "user.name=Consumer Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "consumer fixture")
        self.git("remote", "add", "origin", "https://github.com/ed3c/soodles.git")
        self.issue, self.envelope = issue_fixture()
        e = self.envelope["execution"]
        e["control_root"] = str(self.root)
        self.worktree = self.root / ".worktrees" / e["worktree"]
        self.git("worktree", "add", "-b", e["worktree"], str(self.worktree))
        self.envelope["base_head"] = self.git("rev-parse", "HEAD")
        self.effect = self.directory / "WORKER_EFFECT"
        self.binary = self.directory / "executable-sentinel"
        self.binary.write_text("#!/bin/sh\nprintf observed > '" + str(self.effect) + "'\n")
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary), "sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        self.argv = ["exec", "--json", "--model", "fixture-model"]
        e["carrier"] = {"platform": platform.system().lower() + "_" + platform.machine().lower(),
                        "noodle": dict(identity),
                        "codex": {**identity, "model": "fixture-model", "argv": self.argv}}
        self.path = self.directory / "envelope.json"
        self.bind_envelope()
        self.runtime = self.root / ".noodle"
        self.runtime.mkdir()
        self.snapshot = {"order_revision": "a" * 32, "state": {"orders": {}}, "effect_ledger": []}
        self.save_owner()
        self.session = "soodles-18-0-execute-session"
        self.env = {"NOODLE_PROJECT_DIR": str(self.root), "NOODLE_WORKTREE": str(self.worktree),
                    "NOODLE_ORDER_ID": "soodles-18", "NOODLE_STAGE_INDEX": "0",
                    "NOODLE_SESSION_ID": self.session}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.PIPE).strip()

    def bind_envelope(self):
        data = json.dumps(self.envelope).encode()
        self.path.write_bytes(data)
        self.pin = hashlib.sha256(data).hexdigest()

    def save_owner(self):
        (self.runtime / "state.snapshot.json").write_text(json.dumps(self.snapshot))

    def reader(self, number):
        self.assertEqual(number, 18)
        return copy.deepcopy(self.issue)

    def admit(self, route):
        return getattr(execution, route)(self.path, self.pin, self.root, reader=self.reader)

    def promote_fixture(self):
        # This fixture is not a claim about Noodle promotion; #82 has real-owner controls.
        proposal = json.loads((self.runtime / "orders-next.json").read_text())
        order = proposal["orders"][0]
        stage = order["stages"][0]
        self.snapshot["state"]["orders"][order["id"]] = {
            "stages": [{**stage, "status": "dispatching",
                        "attempts": [{"status": "launching", "session_id": ""}]}]}
        self.snapshot["order_revision"] = "b" * 32
        self.snapshot["effect_ledger"] = [{"effect_id": "owner-fixture-receipt", "status": "done",
            "effect": {"type": "initial_admission", "payload": {"order_id": order["id"]}}}]
        self.save_owner()
        (self.runtime / "orders-next.json").unlink()
        session_dir = self.runtime / "sessions" / self.session
        session_dir.mkdir(parents=True)
        (session_dir / "spawn.json").write_text(json.dumps({
            "session_id": self.session, "provider": "codex", "runtime": "process",
            "worktree_path": str(self.worktree), "model": "fixture-model", "skill": "execute"}))

    def launch(self, **kwargs):
        def sentinel(binary, argv):
            self.assertEqual(binary, str(self.binary))
            subprocess.run(argv, cwd=self.worktree, check=True)
        return execution.worker(self.path, self.pin, self.worktree, self.argv,
                                reader=self.reader, environ=self.env, execute=sentinel, **kwargs)

    def test_both_real_entry_functions_consume_same_normalized_binding(self):
        automatic = self.admit("automatic")
        proposal = json.loads((self.runtime / "orders-next.json").read_text())
        self.assertEqual(proposal["initial_revision"], self.snapshot["order_revision"])
        self.assertEqual(proposal["orders"][0]["id"], "soodles-18")
        self.assertFalse(self.effect.exists())
        (self.runtime / "orders-next.json").unlink()
        supervised = self.admit("supervised")
        self.assertEqual(automatic["binding"], supervised["binding"])
        self.assertTrue(supervised["published"])

    def test_illegal_binding_refuses_both_routes_before_mailbox_effects(self):
        for route in ("automatic", "supervised"):
            for change, field in (({"number": 19}, "issue.number"),
                                  ({"body": self.issue["body"] + "\nchanged"}, "issue.body_sha256")):
                with self.subTest(route=route, field=field):
                    original = self.issue
                    self.issue = {**original, **change}
                    with self.assertRaises(admission.AdmissionRefusal) as caught:
                        self.admit(route)
                    self.assertEqual(caught.exception.invalid["field"], field)
                    self.issue = original
                    self.assertFalse((self.runtime / "orders-next.json").exists())
                    self.assertFalse(list(self.runtime.glob(".soodles-proposal-*")))
                    self.assertFalse(self.effect.exists())

    def test_repeated_publication_preserves_one_mailbox_and_prior_admission(self):
        first = self.admit("automatic")
        before = (self.runtime / "orders-next.json").read_bytes()
        repeated = self.admit("automatic")
        self.assertTrue(first["published"])
        self.assertFalse(repeated["published"])
        self.assertEqual((self.runtime / "orders-next.json").read_bytes(), before)
        self.promote_fixture()
        self.assertEqual(self.admit("automatic")["action"], "owned")
        self.snapshot["state"]["orders"] = {}
        self.save_owner()
        self.assertEqual(self.admit("automatic")["action"], "previously_admitted")
        self.assertFalse((self.runtime / "orders-next.json").exists())

    def test_live_writer_refuses_supervised_takeover_without_resetting_history(self):
        self.admit("automatic")
        self.promote_fixture()
        before = (self.runtime / "state.snapshot.json").read_bytes()
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.admit("supervised")
        self.assertEqual(caught.exception.invalid["field"], "takeover.prior_writer")
        self.assertEqual((self.runtime / "state.snapshot.json").read_bytes(), before)
        self.assertFalse((self.runtime / "orders-next.json").exists())
        stage = self.snapshot["state"]["orders"]["soodles-18"]["stages"][0]
        stage["attempts"][0]["status"] = "completed"
        self.save_owner()
        # Existing supervised ownership inspection needs no local nested Agent.
        del self.envelope["execution"]["carrier"]["codex"]
        self.bind_envelope()
        result = self.admit("supervised")
        self.assertEqual(result["action"], "owned")
        self.assertFalse(result["published"])

    def test_worker_revalidates_live_body_before_executable_effect(self):
        self.admit("automatic")
        self.promote_fixture()
        original = self.issue["body"]
        self.issue["body"] += "\nAmended after publication."
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.launch()
        self.assertEqual(caught.exception.invalid["field"], "issue.body_sha256")
        self.assertFalse(self.effect.exists())
        self.issue["body"] = original
        result = self.launch()
        self.assertEqual(result["session_id"], self.session)
        self.assertEqual(self.effect.read_text(), "observed")

    def test_worker_rejects_foreign_dispatch_and_changed_executable(self):
        self.admit("automatic")
        self.promote_fixture()
        self.env["NOODLE_ORDER_ID"] = "soodles-19"
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.launch()
        self.assertEqual(caught.exception.invalid["field"], "worker.NOODLE_ORDER_ID")
        self.assertFalse(self.effect.exists())
        self.env["NOODLE_ORDER_ID"] = "soodles-18"
        self.binary.write_text("#!/bin/sh\nprintf replaced > '" + str(self.effect) + "'\n")
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.launch()
        self.assertEqual(caught.exception.invalid["field"], "carrier.noodle.sha256")
        self.assertFalse(self.effect.exists())

    def test_unknown_owner_revision_refuses_before_publication(self):
        del self.snapshot["order_revision"]
        self.save_owner()
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.admit("automatic")
        self.assertEqual(caught.exception.invalid["field"], "noodle.order_revision")
        self.assertEqual(caught.exception.next["owner"], "Noodle")
        self.assertFalse((self.runtime / "orders-next.json").exists())

    def test_real_scheduler_provider_entry_also_revalidates_before_launch(self):
        self.snapshot["state"]["orders"]["schedule"] = {
            "stages": [{"status": "dispatching", "attempts": [{"status": "launching", "session_id": ""}]}]}
        self.save_owner()
        session_dir = self.runtime / "sessions" / self.session
        session_dir.mkdir(parents=True)
        (session_dir / "spawn.json").write_text(json.dumps({
            "session_id": self.session, "provider": "codex", "runtime": "process",
            "worktree_path": str(self.root), "model": "fixture-model", "skill": "schedule"}))
        env = {**self.env, "NOODLE_WORKTREE": str(self.root)}
        called = []
        def run():
            return execution.worker(self.path, self.pin, self.root, self.argv,
                                    reader=self.reader, environ=env,
                                    execute=lambda *args: called.append(args))
        original = self.issue["body"]
        self.issue["body"] += "\nchanged before scheduling"
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            run()
        self.assertEqual(caught.exception.invalid["field"], "issue.body_sha256")
        self.assertFalse(called)
        self.issue["body"] = original
        run()
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], str(self.binary))

    def test_cli_missing_supervisor_input_is_structured_and_has_no_effect(self):
        source = Path(execution.__file__).resolve().parent
        result = subprocess.run([str(source / "soodles"), "issue", "automatic"],
                                cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["owner"], "issue.automatic")
        self.assertEqual(receipt["invalid"]["field"], "arguments")
        self.assertEqual(receipt["next"]["owner"], "supervisor")
        self.assertFalse((self.runtime / "orders-next.json").exists())


if __name__ == "__main__":
    unittest.main()
