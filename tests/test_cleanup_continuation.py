"""Original post-write cleanup continuation; no live provider effects."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import issue_atom as atom
import landing
import soodles
import test_issue_atom as atom_tests
import test_landing as landing_tests
import test_lifecycle_activation as activation_tests


class CleanupIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = landing_tests.LandingTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.primary, self.claim, _, self.base = self.fixture.cloud_control("primary")
        (self.primary / ".git/info/exclude").write_text(".worktrees/\n")
        self.root = Path(self.fixture.temp.name).resolve() / "detached"
        self.git("worktree", "add", "--detach", str(self.root), self.base)

    def git(self, *args):
        return soodles.checked(["git", *args], self.primary)

    def advance_main(self):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--allow-empty", "-m", "integration advanced")
        return self.git("rev-parse", "HEAD")

    def test_actual_local_ref_changes_without_detached_head_or_remote_tracking(self):
        first = landing.cleanup_integration(self.root, "main")
        merged = self.advance_main()
        second = landing.cleanup_integration(self.root, "main")
        self.assertEqual(first["integration_ref"], "refs/heads/main")
        self.assertEqual(second["main_head"], merged)
        self.assertEqual(first["control_head"], second["control_head"])
        self.assertFalse(landing.same_cleanup_input(first, second))
        self.assertTrue(landing.same_cleanup_input(second, landing.cleanup_integration(self.root, "main")))
        self.assertTrue(landing.same_cleanup_input(second, {**second, "control_head": "f" * 40}))
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.assertEqual(landing.cleanup_integration(self.root, "main"), second)

    def test_unsupported_branch_and_missing_local_ref_refuse(self):
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.integration_branch"):
            landing.cleanup_integration(self.root, "main")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("update-ref", "-d", "refs/heads/main")
        with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.integration_ref"):
            landing.cleanup_integration(self.root, "main")

    def reconciliation_fixture(self):
        fixture = landing_tests.IntegrationReconciliationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_cleanup_refusal_is_not_reoffered_without_material_readback(self):
        fixture = self.reconciliation_fixture()
        calls = []
        def refuse(argv, cwd):
            if argv[0] == fixture.binary:
                calls.append(argv)
                raise soodles.Refusal("fixture cleanup response unavailable")
            return fixture.checked(argv, cwd)
        with fixture.owners(checked=refuse):
            with self.assertRaisesRegex(soodles.Refusal, "cleanup response unavailable"):
                fixture.reconcile()
            intent = landing.read(fixture.checkpoint)["cleanup_intent"]
            self.assertEqual(intent["main_head"], fixture.target)
            with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.observation"):
                fixture.reconcile()
        self.assertEqual(len(calls), 1)
        self.assertTrue(fixture.worktree.exists())
        self.assertEqual(landing.read(fixture.checkpoint)["cleanup_intent"], intent)

    def test_cleanup_ref_lock_release_preserves_integration_intent_and_then_cleans(self):
        fixture = self.reconciliation_fixture()
        lock = Path(fixture.git(fixture.root, "rev-parse", "--path-format=absolute", "--git-path",
                               "refs/heads/" + fixture.claim["worktree"] + ".lock"))
        lock.write_text("another owner holds the ref\n")
        with fixture.owners():
            with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.ref_lock"):
                fixture.reconcile()
            self.assertEqual(lock.read_text(), "another owner holds the ref\n")
            self.assertNotIn("cleanup", fixture.events)
            previous = landing.read(fixture.checkpoint)
            lock.unlink()
            result = fixture.reconcile()
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(result["integration_sync"], previous["integration_sync"])
        self.assertEqual(fixture.events.count("cleanup"), 1)

    def test_actual_unmerged_candidate_guard_still_refuses_after_integration_sync(self):
        fixture = self.reconciliation_fixture()
        fixture.commit(fixture.worktree, "candidate not included in provider merge")
        fixture.candidate = fixture.git(fixture.worktree, "rev-parse", "HEAD")
        fixture.claim.update(head=fixture.candidate,
                             tree=fixture.git(fixture.worktree, "rev-parse", "HEAD^{tree}"))
        landing.save(fixture.checkpoint, fixture.state)
        with fixture.owners():
            with self.assertRaises(soodles.Refusal):
                fixture.reconcile()
            self.assertEqual(fixture.git(fixture.primary, "rev-parse", "HEAD"), fixture.target)
            self.assertTrue(fixture.worktree.exists())
            self.assertEqual(fixture.git(fixture.worktree, "rev-parse", "HEAD"), fixture.candidate)
            with self.assertRaisesRegex(landing.LandingRefusal, "cleanup.observation"):
                fixture.reconcile()
        self.assertEqual(fixture.events.count("cleanup"), 1)


class PostwritePublisherTests(unittest.TestCase):
    def fixture(self, activated):
        fixture = atom_tests.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        state, paths, original, spec, selected = fixture.postwrite_resume_fixture()
        if not activated:
            state.pop("landing_activation")
            atom.save_json(paths["directory"] / "landing-claim.json", original)
        checkpoint = atom.read_json(paths["landing"], "checkpoint")
        checkpoint.update(phase="reconciling", cleanup_intent={"main_head": "e" * 40},
                          cleanup_blocked={"ref_lock": "retained"}, observations=[{"provider": "history"}],
                          delivery={"action": "close", "status": "observed"})
        atom.save_json(paths["landing"], checkpoint)
        return fixture, state, paths, original, spec, selected, checkpoint

    def test_normal_and_activated_resume_preserve_all_provider_and_cleanup_history(self):
        for activated in (False, True):
            with self.subTest(activated=activated):
                f, state, paths, original, spec, selected, before = self.fixture(activated)
                def invoke(_owner, checkpoint, claim_path):
                    # Exercise the actual landing owner mutation; only immutable verifier validation is substituted.
                    with patch("landing.validate_claim"):
                        return landing.resume(checkpoint, atom.read_json(claim_path, "claim"))
                auth_before = f.path.read_bytes()
                with patch("issue_atom.LandingOwner.resume", autospec=True, side_effect=invoke) as call:
                    atom.external_landing_resume(f.authorization, state, paths, selected)
                    atom.external_landing_resume(f.authorization, state, paths, {})
                self.assertEqual(call.call_count, 1)
                after = atom.read_json(paths["landing"], "checkpoint")
                for key, value in before.items():
                    if key != "claim":
                        self.assertEqual(after[key], value)
                self.assertEqual(after["claim"], {**original, "verifier_sha256": spec["verifier_sha256"]})
                self.assertEqual(f.path.read_bytes(), auth_before)

    def test_normal_unknown_resume_is_readback_only_and_rejects_drift_or_missing_confirmation(self):
        f, state, paths, original, spec, selected, before = self.fixture(False)
        for change in ({"merge_sha": None}, {"issue_closed_at": None}, {"writes_offered": ["merge"]},
                       {"claim": {**original, "head": "f" * 40}}):
            atom.save_json(paths["landing"], {**before, **change})
            with patch("issue_atom.LandingOwner.resume", side_effect=AssertionError("effect")):
                with self.assertRaisesRegex(atom.AtomRefusal, "landing_resume.checkpoint"):
                    atom.external_landing_resume(f.authorization, state, paths, selected)
        atom.save_json(paths["landing"], before)
        with patch("issue_atom.LandingOwner.resume", side_effect=subprocess.TimeoutExpired("resume", 1)):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing_resume.outcome"):
                atom.external_landing_resume(f.authorization, state, paths, selected)
        with patch("issue_atom.LandingOwner.resume", side_effect=AssertionError("replay")):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing_resume.outcome"):
                atom.external_landing_resume(f.authorization, state, paths, {})
            atom.save_json(paths["landing"], {**before, "claim": {**original, "verifier_sha256": spec["verifier_sha256"]},
                           "prior_verifiers": [original["verifier_sha256"]]})
            atom.external_landing_resume(f.authorization, state, paths, {})
        self.assertEqual(state["landing_resume"]["status"], "adopted")


class PostwriteLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = atom_tests.IssueAtomTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.paths, self.state, self.snapshot = f.own_wait_fixture(running=True)
        self.binding = atom.read_json(self.paths["envelope"], "envelope")
        execution = self.binding["execution"]
        order = self.snapshot["state"]["orders"][execution["order_id"]]
        order["status"] = "completed"
        stage = order["stages"][0]
        stage["status"] = stage["attempts"][0]["status"] = "completed"
        schedule = self.snapshot["state"]["orders"]["schedule"]["stages"][0]
        schedule.update(status="pending", attempts=None)
        self.snapshot_path = f.root / ".noodle/state.snapshot.json"
        atom.save_json(self.snapshot_path, self.snapshot)
        claim = {"schema_version": 1, "owner": "Noodle", "authorizes_landing": False,
                 "authorizes_provider_write": False, "repository": "ed3c/soodles", "subject": "ed3c/soodles#131",
                 "head": "b" * 40, "tree": "c" * 40, "base_head": f.base,
                 "order_id": execution["order_id"], "stage_index": 0,
                 "worktree_name": execution["worktree"],
                 "worktree_path": str(f.root / ".worktrees" / execution["worktree"]),
                 "attempt_id": stage["attempts"][0]["attempt_id"], "session_id": "fixture-execute"}
        atom.save_json(self.paths["claim"], claim)
        publication = {"pr": {"number": 132}, "branch": "published"}
        self.state.update(phase="landing", publication=publication,
                          writes={"candidate_amendment": {"status": "observed"}})
        atom.save_json(self.paths["state"], self.state)
        landed = {k: claim[k] for k in ("repository", "head", "tree", "base_head")}
        landed.update(issue=131, pr=132, worktree=execution["worktree"], publication_branch="published",
                      control_root=str(f.root), execution_envelope={"path": str(self.paths["envelope"]),
                                                                  "sha256": self.state["envelope_sha256"]})
        self.checkpoint = {"schema": 2, "claim": landed, "phase": "reconciling",
                           "merge_sha": "d" * 40, "issue_closed_at": "now", "writes_offered": ["merge", "close"],
                           "cleanup_intent": {"main_head": "e" * 40}}
        atom.save_json(self.paths["landing"], self.checkpoint)
        # Reuse the fixed external bundle fixture, not a repository copy or live owner.
        activation = activation_tests.LifecycleActivationTests()
        activation.setUp()
        self.addCleanup(activation.doCleanups)
        self.runtime, self.spec = activation.runtime, activation.spec
        self.descriptor = f.outer / "selected-runtime.json"
        atom.save_json(self.descriptor, self.spec)
        self.descriptor_digest = atom.digest_file(self.descriptor)

    def resume(self):
        with patch.object(atom, "__file__", str(self.runtime / "issue_atom.py")), \
                patch.object(atom.os, "kill", side_effect=ProcessLookupError):
            return atom.resume(self.fixture.path, self.descriptor, self.descriptor_digest, environ=self.fixture.env)

    def test_cli_dispatches_selected_resume_without_starting_run(self):
        argv = ["soodles", "atom", "resume", str(self.fixture.path), str(self.descriptor), self.descriptor_digest]
        with patch.object(sys, "argv", argv), patch.object(atom, "resume", return_value={"status": "resumed"}) as resume, \
                patch.object(atom, "drive", side_effect=AssertionError("new run")), patch("builtins.print"):
            self.assertEqual(soodles.main(), 0)
        resume.assert_called_once_with(str(self.fixture.path), str(self.descriptor), self.descriptor_digest)

    def test_original_resume_preserves_auth_canonical_history_and_selects_its_own_next(self):
        f = self.fixture
        immutable = [f.path, self.snapshot_path, self.paths["claim"], self.paths["envelope"], self.paths["landing"]]
        before = {path: path.read_bytes() for path in immutable}
        # The original control root may have already fast-forwarded after provider closure.
        subprocess.run(["git", "commit", "--allow-empty", "-m", "provider fast-forward fixture"],
                       cwd=f.root, check=True, capture_output=True)
        result = self.resume()
        after = atom.read_json(self.paths["state"], "state")
        self.assertEqual({k: v for k, v in after.items() if k != "lifecycle_resume"}, self.state)
        self.assertEqual(after["lifecycle_resume"], {"from": None, "to": self.spec, "authorization_sha256": f.digest})
        self.assertEqual(result["next"]["argv"], [self.spec["path"], "run", str(f.path)])
        self.assertEqual(result, self.resume())
        for path in immutable:
            self.assertEqual(path.read_bytes(), before[path])
        with patch.object(atom, "__file__", str(self.runtime / "issue_atom.py")), \
                patch.object(atom, "_run_owned", return_value={"continued": True}) as run:
            self.assertEqual(atom.run(f.path, environ=f.env), {"continued": True})
            self.assertEqual(run.call_args.args[1], f.authorization)
            atom.host_manager(f.authorization, after)
        changed = {**self.spec, "source_sha256": "f" * 64}
        atom.save_json(self.descriptor, changed)
        with self.assertRaisesRegex(atom.AtomRefusal, "lifecycle.resume.selection"):
            self.resume()

    def test_postwrite_reads_current_claim_and_preserves_retained_pair(self):
        f = self.fixture
        claim = atom.read_json(self.paths["claim"], "fixture.claim")
        with atom_tests.typed_revision_receipts(f.path, self.state, f.outer / "revision") as current:
            atom.save_json(current["claim"], claim)
            atom.save_json(self.paths["claim"], {**claim, "head": "retained", "session_id": "old"})
            retained = self.paths["claim"].read_bytes()
            with patch.object(atom.os, "kill", side_effect=ProcessLookupError):
                binding, owner = atom.postwrite_lifecycle(f.authorization, self.state, self.paths)
            self.assertEqual(binding["execution"], self.binding["execution"])
            self.assertEqual(owner["state"]["orders"], self.snapshot["state"]["orders"])
            self.assertEqual(self.paths["claim"].read_bytes(), retained)
            current["claim"].unlink()
            with self.assertRaisesRegex(atom.AtomRefusal, "publication.claim"):
                atom.postwrite_lifecycle(f.authorization, self.state, self.paths)

    def test_missing_confirmation_identity_drift_sessions_and_locks_block_selection(self):
        f = self.fixture
        for field in ("merge_sha", "issue_closed_at"):
            atom.save_json(self.paths["landing"], {**self.checkpoint, field: None})
            with self.assertRaisesRegex(atom.AtomRefusal, "lifecycle.resume.landing"):
                self.resume()
        atom.save_json(self.paths["landing"], self.checkpoint)
        oid = self.binding["execution"]["order_id"]
        original = self.snapshot["state"]["orders"][oid]["stages"][0]["prompt"]
        self.snapshot["state"]["orders"][oid]["stages"][0]["prompt"] = "foreign"
        atom.save_json(self.snapshot_path, self.snapshot)
        with self.assertRaisesRegex(atom.AtomRefusal, "noodle.order.binding"):
            self.resume()
        self.snapshot["state"]["orders"][oid]["stages"][0]["prompt"] = original
        atom.save_json(self.snapshot_path, self.snapshot)
        with patch.object(atom, "__file__", str(self.runtime / "issue_atom.py")), \
                patch.object(atom.os, "kill", return_value=None):
            with self.assertRaisesRegex(atom.AtomRefusal, "process_alive"):
                atom.resume(f.path, self.descriptor, self.descriptor_digest, environ=f.env)
        for lock_name, field in (("issue-atom.lock", "noodle.atom_entry"), ("noodle.lock", "lifecycle.resume.noodle")):
            with (f.root / ".noodle" / lock_name).open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaisesRegex(atom.AtomRefusal, field):
                    self.resume()
        self.assertNotIn("lifecycle_resume", atom.read_json(self.paths["state"], "state"))

    def test_activated_checkpoint_and_different_second_selection(self):
        directory = self.fixture.outer / "activation"
        directory.mkdir()
        manifest = directory / "manifest.json"
        atom.save_json(manifest, {"fixture": "immutable activation"})
        atom.save_json(directory / "checkpoint.json", self.checkpoint)
        self.paths["landing"].unlink()
        self.state["landing_activation"] = {"manifest": str(manifest), "sha256": atom.digest_file(manifest)}
        atom.save_json(self.paths["state"], self.state)
        self.resume()
        state = atom.read_json(self.paths["state"], "state")
        state["lifecycle_resume"]["to"] = {**self.spec, "path": "/different/issue-atom"}
        atom.save_json(self.paths["state"], state)
        with self.assertRaisesRegex(atom.AtomRefusal, "lifecycle.resume.intent"):
            self.resume()
        state["lifecycle_resume"]["authorization_sha256"] = "f" * 64
        with self.assertRaisesRegex(atom.AtomRefusal, "lifecycle.resume.binding"):
            atom.resumed_lifecycle(self.fixture.authorization, state)
