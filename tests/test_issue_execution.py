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
        e["source_head"] = self.envelope["base_head"]
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
        self.assertEqual(set(proposal), {"orders"})
        self.assertEqual(proposal["orders"][0]["id"], "soodles-18")
        self.assertFalse(self.effect.exists())
        (self.runtime / "orders-next.json").unlink()
        supervised = self.admit("supervised")
        self.assertEqual(automatic["binding"], supervised["binding"])
        self.assertTrue(supervised["published"])

    def test_stale_body_continuation_preserves_entry_and_requires_supervisor_rebinding(self):
        original = self.issue["body"]
        for route in ("automatic", "supervised"):
            self.issue["body"] = original + "\ncurrent provider amendment"
            with self.assertRaises(admission.AdmissionRefusal) as caught:
                self.admit(route)
            output = execution.refusal_output(caught.exception, route)
            next_action = output["next"]
            self.assertEqual(next_action["operation"], route)
            self.assertEqual(next_action["owner"], "supervisor")
            self.assertEqual(next_action["required"], ["fresh_execution_envelope"])
            self.assertEqual(next_action["known"]["issue"], 18)
            self.assertEqual(next_action["known"]["envelope"], str(self.path))
            help_result = subprocess.run(next_action["help_argv"], capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("issue " + route, help_result.stdout)
            self.assertNotIn("request", output)
            self.assertNotIn("argv", next_action)
            self.assertFalse((self.runtime / "orders-next.json").exists())
            self.assertFalse(self.effect.exists())
            # Only the external supervisor supplies changed authority; the guard
            # does not rewrite the old envelope or retry on its own.
            self.envelope["body_sha256"] = admission.body_digest(self.issue["body"])
            self.bind_envelope()
            current = self.admit(route)
            self.assertTrue(current["published"])
            self.assertEqual(current["next"]["operation"], route)
            (self.runtime / "orders-next.json").unlink()
            self.issue["body"] = original
            self.envelope["body_sha256"] = admission.body_digest(original)
            self.bind_envelope()

    def test_worker_refusal_keeps_owner_dispatch_instead_of_offering_another_writer(self):
        self.admit("automatic")
        self.promote_fixture()
        self.issue["body"] += "\nstale at worker boundary"
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.launch()
        output = execution.refusal_output(caught.exception, "worker")
        self.assertEqual(output["next"]["operation"], "worker")
        self.assertIn("Noodle", output["next"]["reason"])
        self.assertNotIn("argv", output["next"])
        self.assertNotIn("request", output)
        self.assertFalse(self.effect.exists())

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
        stage["attempts"][0].update(status="completed", session_id=self.session)
        stage["status"] = "review"
        ended = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
        ended.wait()
        (self.runtime / "sessions" / self.session / "process.json").write_text(
            json.dumps({"pid": ended.pid, "session_id": self.session}))
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

    def test_clean_descendant_is_not_the_selected_starting_head(self):
        self.admit("automatic")
        self.promote_fixture()
        (self.worktree / "allowed.py").write_text("different committed subject\n")
        subprocess.run(["git", "add", "allowed.py"], cwd=self.worktree, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-m", "different subject"],
                       cwd=self.worktree, check=True, capture_output=True)
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.launch()
        self.assertEqual(caught.exception.invalid["field"], "worker.git.head")
        self.assertFalse(self.effect.exists())

    def test_lock_selected_noodle_proposal_does_not_invent_revision_protocol(self):
        del self.snapshot["order_revision"]
        self.save_owner()
        result = self.admit("automatic")
        self.assertTrue(result["published"])
        self.assertEqual(set(json.loads((self.runtime / "orders-next.json").read_text())), {"orders"})

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

    def test_network_failure_names_provider_readback_without_mailbox_effects(self):
        from unittest.mock import patch
        import urllib.error
        with patch.dict(os.environ, {"GH_TOKEN": "fixture_installation", "XDG_CACHE_HOME": str(self.directory)}), patch("github_reader._request", side_effect=urllib.error.URLError("DNS unavailable")):
            with self.assertRaises(admission.AdmissionRefusal) as caught:
                execution.automatic(self.path, self.pin, self.root)
        self.assertEqual(caught.exception.invalid["field"], "issue.provider_readback")
        self.assertEqual(caught.exception.next["owner"], "GitHub")
        self.assertEqual(caught.exception.next["required"], ["fresh_issue_readback"])
        self.assertFalse((self.runtime / "orders-next.json").exists())

    def test_shared_default_reader_admits_then_reuses_without_duplicate_mailbox(self):
        from unittest.mock import patch
        from test_github_reader import response
        url = self.issue["url"]
        def fresh(_):
            value = response(headers={"ETag": '"same"'}, value=self.issue)
            value.url = url
            return value
        with patch.dict(os.environ, {"GH_TOKEN": "fixture_installation", "XDG_CACHE_HOME": str(self.directory)}), patch("github_reader._request", side_effect=fresh) as transport:
            first = execution.automatic(self.path, self.pin, self.root)
            before = (self.runtime / "orders-next.json").read_bytes()
            second = execution.automatic(self.path, self.pin, self.root)
            self.assertEqual(first["binding"], second["binding"])
            self.assertEqual((self.runtime / "orders-next.json").read_bytes(), before)
            self.assertEqual(transport.call_count, 2)
            self.assertEqual(transport.call_args.args[0].get_header("Authorization"), "Bearer fixture_installation")

    def test_shared_default_reader_quota_preserves_mailbox_and_worker(self):
        from unittest.mock import patch
        from test_github_reader import response
        import github_reader
        self.admit("automatic")
        before = (self.runtime / "orders-next.json").read_bytes()
        import time
        def exhausted(_):
            value = response(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(time.time()) + 600)})
            value.url = self.issue["url"]
            return value
        with patch.dict(os.environ, {"GH_TOKEN": "fixture_installation", "XDG_CACHE_HOME": str(self.directory)}), patch("github_reader._request", side_effect=exhausted) as transport:
            for route in ("automatic", "supervised"):
                with self.assertRaises(github_reader.ProviderWait):
                    getattr(execution, route)(self.path, self.pin, self.root)
            with self.assertRaises(github_reader.ProviderWait):
                execution.worker(self.path, self.pin, self.worktree, self.argv, environ=self.env)
            self.assertEqual(transport.call_count, 1)
        self.assertEqual((self.runtime / "orders-next.json").read_bytes(), before)
        self.assertFalse(self.effect.exists())

    def test_completed_label_cannot_hide_a_live_process_group(self):
        self.admit("automatic")
        self.promote_fixture()
        stage = self.snapshot["state"]["orders"]["soodles-18"]["stages"][0]
        stage["status"] = "review"
        stage["attempts"][0].update(status="completed", session_id=self.session)
        self.save_owner()
        process = subprocess.Popen(["/bin/sh", "-c", "sleep 30"], start_new_session=True)
        try:
            (self.runtime / "sessions" / self.session / "process.json").write_text(
                json.dumps({"pid": process.pid, "session_id": self.session}))
            with self.assertRaises(admission.AdmissionRefusal) as caught:
                self.admit("supervised")
            self.assertEqual(caught.exception.invalid["field"], "takeover.process_alive")
            self.assertFalse((self.runtime / "orders-next.json").exists())
        finally:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            process.wait()

    def archived_completion(self, *, outcome="completed", blocking=False):
        self.admit("automatic")
        self.promote_fixture()
        ended = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
        ended.wait()
        session_dir = self.runtime / "sessions" / self.session
        (session_dir / "process.json").write_text(json.dumps(
            {"pid": ended.pid, "session_id": self.session}))
        (session_dir / "meta.json").write_text(json.dumps(
            {"session_id": self.session, "status": "exited", "alive": False}))
        (session_dir / "events.ndjson").write_text(json.dumps({
            "type": "stage_message", "payload": {
                "message": "fixture result", "blocking": blocking, "outcome": outcome,
                "order_id": "soodles-18", "stage_index": 0}}) + "\n")
        created = "2026-09-20T00:00:00Z"
        admission_record = self.snapshot["effect_ledger"][0]
        admission_record.update(status="done", result={"status": "completed"})
        admission_record["effect"]["effect_id"] = admission_record["effect_id"]
        self.snapshot["effect_ledger"].extend([
            {"effect_id": "event-2-effect-0", "effect": {
                "effect_id": "event-2-effect-0", "type": "dispatch", "payload": {
                    "attempt_id": "soodles-18-0-attempt-0", "order_id": "soodles-18",
                    "stage_index": 0}, "created_at": "2026-09-20T00:00:00Z"}},
            {"effect_id": "event-3-effect-0", "effect": {
                "effect_id": "event-3-effect-0", "type": "write_projection",
                "payload": {"order_id": "soodles-18"}, "created_at": created}},
            {"effect_id": "event-3-effect-1", "effect": {
                "effect_id": "event-3-effect-1", "type": "ack",
                "payload": {"order_id": "soodles-18"}, "created_at": created}},
        ])
        self.snapshot["state"]["orders"] = {}
        self.save_owner()
        return session_dir

    def test_projected_away_original_order_requires_exact_completed_session(self):
        self.archived_completion()
        self.snapshot["effect_ledger"] = [record for record in self.snapshot["effect_ledger"]
                                          if record["effect"]["type"] != "initial_admission"]
        self.save_owner()
        result = execution.completed_original_order(self.envelope, self.snapshot)
        self.assertEqual(result["source"], "archived_projection")
        self.assertIsNone(result["initial_admission_effect"])
        self.assertEqual(result["typed_outcome"]["outcome"], "completed")
        self.assertTrue(result["quiescent_sessions"][0]["process_and_group_absent"])
        self.assertEqual(self.admit("automatic")["action"], "previously_admitted")
        self.assertFalse((self.runtime / "orders-next.json").exists())

    def test_projected_away_blocked_outcome_cannot_authorize_cleanup(self):
        self.archived_completion(outcome="blocked", blocking=True)
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            execution.completed_original_order(self.envelope, self.snapshot)
        self.assertEqual(caught.exception.invalid["field"], "completion.typed_outcome")


if __name__ == "__main__":
    unittest.main()
