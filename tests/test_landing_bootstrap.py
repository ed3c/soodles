import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import unittest
from unittest.mock import patch

import issue_admission
import landing
import test_candidate_publication as publication_fixture
import test_landing as landing_fixture
from soodles import Refusal


class BootstrapCustodyTests(unittest.TestCase):
    def setUp(self):
        self.git = publication_fixture.CandidatePublicationTests()
        self.git.setUp()
        self.addCleanup(self.git.doCleanups)
        self.provider = landing_fixture.LandingTests()
        self.provider.setUp()
        self.addCleanup(self.provider.doCleanups)
        root = self.git.project.resolve()
        self.claim = {**self.provider.claim, "issue": 128, "pr": 41,
                      "head": self.git.head, "tree": self.git.tree, "base_head": self.git.base,
                      "control_root": str(root), "worktree": "candidate"}
        self.snapshot = copy.deepcopy(self.provider.snapshot)
        self.snapshot["pr"].update(number=41, html_url="https://github.com/ed3c/soodles/pull/41",
                                   body="Refs ed3c/soodles#128")
        self.snapshot["pr"]["head"].update(sha=self.git.head, ref="candidate")
        self.snapshot["pr"]["base"]["sha"] = self.git.base
        self.snapshot["commit"] = {"sha": self.git.head, "tree": {"sha": self.git.tree}}
        self.snapshot["run"]["head_sha"] = self.git.head
        self.snapshot["jobs"]["jobs"][0]["head_sha"] = self.git.head
        self.snapshot["branch"]["commit"]["sha"] = self.git.base
        contract = issue_admission.parse_contract(publication_fixture.issue_body(self.git.base))
        contract = {key: value for key, value in contract.items() if key in issue_admission.CONTRACT_V1_FIELDS}
        contract.update(schema=1, write_paths=["candidate.txt"])
        self.body = "<!-- soodles:execution-v1 -->\n```json\n" + json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->"
        self.snapshot["issue"].update(number=128, html_url="https://github.com/ed3c/soodles/issues/128", body=self.body)
        self.binary = Path(self.git.temp.name).resolve() / "native-noodle-sentinel"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o755)
        self.runtime = root / ".noodle"
        self.state = {"state": {"orders": {}}, "effect_ledger": []}
        self.save_owner()
        (self.runtime / "noodle.lock").touch()
        self.custody_path = Path(self.git.temp.name).resolve() / "custody.json"
        self.custody = {"schema": 1, "owner": "external-supervisor", "kind": "worktree-only-bootstrap",
                        "claim": {key: value for key, value in self.claim.items() if key != "verifier_sha256"},
                        "platform": platform.system().lower() + "_" + platform.machine().lower(),
                        "noodle": {"path": str(self.binary), "sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()},
                        "issue_body": self.body}
        self.save_custody()
        self.checkpoint = Path(self.git.temp.name).resolve() / "landing.json"

    def save_owner(self):
        (self.runtime / "state.snapshot.json").write_text(json.dumps(self.state))

    def save_custody(self):
        self.custody_path.write_text(json.dumps(self.custody))
        self.claim["bootstrap_custody"] = {"path": str(self.custody_path),
                                           "sha256": hashlib.sha256(self.custody_path.read_bytes()).hexdigest()}

    def start(self):
        return landing.start(self.claim, self.snapshot, self.checkpoint)

    def test_exact_explicit_custody_admits_without_fabricated_execution(self):
        result = self.start()
        self.assertEqual(result["phase"], "admitted")
        value = landing.read(self.checkpoint)
        self.assertIn("bootstrap_custody", value["claim"])
        self.assertNotIn("execution_envelope", value["claim"])
        self.assertNotIn("noodle_reconciliation", value)

    def test_missing_history_alone_is_not_admission(self):
        self.claim.pop("bootstrap_custody")
        with self.assertRaisesRegex(landing.LandingRefusal, "claim.execution_envelope"):
            self.start()
        self.assertFalse(self.checkpoint.exists())

    def test_execution_cannot_be_downgraded_to_bootstrap(self):
        self.claim["execution_envelope"] = {"path": "/unused", "sha256": "a" * 64}
        with self.assertRaisesRegex(landing.LandingRefusal, "claim.fields"):
            self.start()

    def test_original_order_history_requires_execution_route(self):
        self.state["effect_ledger"] = [{"effect": {"type": "initial_admission", "payload": {"order_id": "soodles-128"}}}]
        self.save_owner()
        with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.original_history"):
            self.start()

    def test_running_noodle_owner_refuses(self):
        with (self.runtime / "noodle.lock").open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.live_owner"):
                self.start()
        self.assertFalse(self.checkpoint.exists())

    def test_orphan_live_process_is_not_ignored(self):
        session = self.runtime / "sessions/orphan"
        session.mkdir()
        (session / "process.json").write_text(json.dumps({"session_id": "orphan", "pid": os.getpid()}))
        with self.assertRaisesRegex(landing.LandingRefusal, "completion.process_alive"):
            self.start()

    def test_changed_subject_and_foreign_platform_refuse(self):
        for key, value in (("platform", "foreign"), ("issue_body", self.body + "changed")):
            original = self.custody[key]
            self.custody[key] = value
            self.save_custody()
            with self.subTest(key=key), self.assertRaises(landing.LandingRefusal):
                self.start()
            self.custody[key] = original

    def test_dirty_worktree_refuses(self):
        (self.git.root / "untracked").write_text("retain")
        with self.assertRaises(Refusal):
            self.start()
        self.assertFalse(self.checkpoint.exists())
        self.assertTrue((self.git.root / "untracked").exists())

    def test_malformed_custody_and_issue_body_refuse_before_checkpoint(self):
        for value in (None, [], {**self.custody, "issue_body": None}):
            self.custody_path.write_text(json.dumps(value))
            self.claim["bootstrap_custody"]["sha256"] = hashlib.sha256(self.custody_path.read_bytes()).hexdigest()
            with self.subTest(value=value), self.assertRaises(landing.LandingRefusal):
                self.start()
            self.assertFalse(self.checkpoint.exists())
        self.save_custody()
        self.snapshot["issue"]["body"] = None
        with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.issue_body"):
            self.start()
        self.assertFalse(self.checkpoint.exists())

    def test_changed_pin_and_identity_refuse(self):
        self.custody_path.write_text("{}")
        with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.sha256"):
            self.start()
        self.custody["claim"]["issue"] = 999
        self.save_custody()
        with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.claim"):
            self.start()

    def test_pending_proposal_is_preserved(self):
        proposal = self.runtime / "orders-next.json"
        proposal.write_text("{}")
        with self.assertRaisesRegex(landing.LandingRefusal, "bootstrap.proposal"):
            self.start()
        self.assertEqual(proposal.read_text(), "{}")

    def ready_to_reconcile(self):
        self.start()
        landing.advance(self.checkpoint, self.snapshot)
        landing.dispatch(self.checkpoint, self.snapshot)
        self.git.command(self.git.project, "git", "merge", "--no-ff", "--no-edit", "candidate")
        merged = self.git.value(self.git.project, "git", "rev-parse", "HEAD")
        self.git.command(self.git.project, "git", "update-ref", "refs/remotes/origin/main", merged)
        self.snapshot["pr"].update(merged=True, state="closed", merged_at="fixture", merge_commit_sha=merged)
        self.snapshot["merge_commit"] = {"sha": merged, "tree": {"sha": self.git.tree},
                                         "parents": [{"sha": self.git.base}, {"sha": self.git.head}]}
        self.snapshot["branch"]["commit"]["sha"] = merged
        landing.advance(self.checkpoint, self.snapshot)
        landing.dispatch(self.checkpoint, self.snapshot)
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="fixture")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "reconcile")

    def test_unknown_cleanup_is_not_reoffered(self):
        self.ready_to_reconcile()
        with patch.object(landing, "fetch_main"):
            # The sentinel exits zero but performs no cleanup. Readback, not exit
            # status, decides success, and the durable intent prevents repetition.
            with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.path"):
                landing.reconcile(self.checkpoint, self.binary)
            with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.observation"):
                landing.reconcile(self.checkpoint, self.binary)
        self.assertTrue(self.git.root.exists())
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], ["merge", "close"])

    def test_bootstrap_reconciliation_retains_native_custody_and_lock(self):
        self.ready_to_reconcile()
        checked = landing.checked
        cleanups = []

        def command(argv, cwd):
            if argv[:3] == [str(self.binary), "worktree", "cleanup"]:
                with (self.runtime / "noodle.lock").open("rb") as lock:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                cleanups.append(argv)
                # Local provider/Noodle-shaped fixture, not real Noodle evidence.
                self.git.command(self.git.project, "git", "worktree", "remove", self.git.root)
                self.git.command(self.git.project, "git", "branch", "-D", "candidate")
                return ""
            return checked(argv, cwd)

        with patch.object(landing, "fetch_main"), patch.object(landing, "checked", side_effect=command), \
                patch.object(landing, "runtime_check", side_effect=AssertionError("Linux-only")):
            result = landing.reconcile(self.checkpoint, self.binary)
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(len(cleanups), 1)
        self.assertNotIn("noodle_reconciliation", result)
        self.assertFalse(self.git.root.exists())


if __name__ == "__main__":
    unittest.main()
