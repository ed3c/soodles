from pathlib import Path
import json
import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom
import landing


class LocalContinuationTests(unittest.TestCase):
    def setUp(self):
        self.auth = {"workflow": {"path": ".github/workflows/runtime.yml", "job": "runtime",
                                  "step": "acceptance"}}
        self.run = {"id": 9, "head_sha": "a" * 40, "event": "pull_request",
                    "path": self.auth["workflow"]["path"], "status": "completed",
                    "conclusion": "success"}
        self.job = {"name": "runtime", "status": "completed", "conclusion": "success",
                    "steps": [{"name": "acceptance", "status": "completed", "conclusion": "success"}]}
        self.provider = Mock()

    def observe(self, run, jobs):
        self.provider.workflow_runs.return_value = {"workflow_runs": [run]}
        self.provider.jobs.return_value = {"jobs": jobs}
        return atom.select_run(self.provider, self.auth, "a" * 40)

    def test_queued_without_jobs_is_wait(self):
        run = {**self.run, "status": "queued", "conclusion": None}
        self.assertEqual(self.observe(run, [])[0], run)

    def test_in_progress_without_steps_is_wait(self):
        run = {**self.run, "status": "in_progress", "conclusion": None}
        self.assertEqual(self.observe(run, [{"name": "runtime"}])[0], run)

    def test_missing_jobs_at_completed_run_refuses(self):
        with self.assertRaisesRegex(atom.AtomRefusal, "workflow_job.count"):
            self.observe(self.run, [])

    def test_failed_ci_refuses(self):
        with self.assertRaisesRegex(atom.AtomRefusal, "workflow.conclusion"):
            self.observe({**self.run, "conclusion": "failure"}, [self.job])

    def test_failed_ci_does_not_offer_the_old_authorization_as_a_correction(self):
        with self.assertRaises(atom.AtomRefusal) as caught:
            self.observe({**self.run, "conclusion": "failure"}, [self.job])
        result = atom.refusal_output(caught.exception, "/external/original-authorization.json")
        self.assertEqual(result["next"]["required"], ["new_candidate_head_after_failed_ci"])
        self.assertNotIn("argv", result["next"])
        self.assertIn("current authorized Local Session is the external supervisor",
                      result["next"]["reason"])
        self.assertIn("do not ask the user to recreate authorization",
                      result["next"]["reason"])
        self.assertFalse(result["authorizes_landing"])

    def test_prior_loop_readback_uses_process_and_lock_not_saved_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".noodle"
            runtime.mkdir()
            lock = runtime / "noodle.lock"
            lock.touch()
            ended = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
            ended.wait()
            auth = {"control_root": str(root), "noodle": {"path": "/bin/false"},
                    "host_config_sha256": None}
            state = {"noodle_start": {"status": "started", "pid": ended.pid}}
            self.assertEqual(atom.observe_prior_loop(auth, state), "stopped")
            state["noodle_start"]["restored"] = True
            self.assertEqual(atom.observe_prior_loop(auth, state), "restored")
            (root / ".noodle.toml").write_text('mode = "supervised"\n')
            with self.assertRaisesRegex(atom.AtomRefusal,
                                        "amendment.prior_loop.restored"):
                atom.observe_prior_loop(auth, state)
            (root / ".noodle.toml").unlink()
            state["noodle_start"].pop("restored")
            with patch.object(atom.subprocess, "run",
                              return_value=Mock(returncode=0, stdout="foreign owner")):
                with self.assertRaisesRegex(atom.AtomRefusal,
                                            "amendment.prior_loop.identity"):
                    atom.observe_prior_loop(auth, state)
            lock.unlink()
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.prior_loop.lock"):
                atom.observe_prior_loop(auth, state)

    def test_process_identity_preserves_hold_and_rejects_alternative_flags(self):
        auth = {"noodle": {"path": "/external/noodle"}, "control_root": "/control"}
        normal = ["/external/noodle", "--project-dir", "/control", "start"]
        held = normal + ["--mode", "manual"]
        self.assertEqual(atom.noodle_process_argv(auth, {}), normal)
        self.assertEqual(atom.noodle_process_argv(auth, {"process_argv": held}), held)
        for bad in (normal + ["--mode", "auto"], normal + ["--once"],
                    ["/foreign/noodle", *held[1:]]):
            with self.subTest(argv=bad), self.assertRaisesRegex(atom.AtomRefusal, "noodle.process.argv"):
                atom.noodle_process_argv(auth, {"process_argv": bad})

    def test_stopped_prior_loop_does_not_advance_new_authorization(self):
        auth = {"prior_atom": {"path": "/fixture/prior"},
                "control_root": "/fixture/control"}
        with patch.object(atom, "verify_prior_atom", return_value={
                "order_id": "same-order", "prior_loop_status": "stopped"}):
            observed = atom.require_available_owner(auth, {}, {"phase": "issue"})
        self.assertEqual(observed["action"], "prior_loop_stopped")
        self.assertEqual(observed["next"]["required"],
                         ["original_host_recovery_before_new_bundle"])

    def test_prior_host_recovery_persists_intent_before_original_owner_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "control"
            (root / ".noodle/sessions").mkdir(parents=True)
            old_path = Path(directory) / "previous.json"
            old_path.write_text(json.dumps({"control_root": str(root)}) + "\n")
            digest = hashlib.sha256(old_path.read_bytes()).hexdigest()
            old_paths = atom.artifact_paths(old_path)
            old_paths["state"].write_text('{}\n')
            old_paths["envelope"].parent.mkdir(parents=True)
            old_paths["envelope"].write_text('{}\n')
            auth = {"control_root": str(root), "host_config_sha256": None,
                    "prior_atom": {"path": str(old_path), "sha256": digest}}
            paths = {"state": Path(directory) / "new-state.json"}
            state = {"phase": "issue"}
            prior = {"order_id": "same-order", "prior_loop_status": "stopped"}
            def original_owner(*_args):
                persisted = json.loads(paths["state"].read_text())
                self.assertEqual(persisted["prior_host_recovery"], {
                    "prior_authorization_sha256": digest, "order_id": "same-order",
                    "status": "offered"})
                return True
            with patch.object(atom, "verify_prior_atom", return_value=prior), \
                 patch.object(atom.issue_execution, "read_owner",
                              return_value={"state": {"orders": {}}}), \
                 patch.object(atom, "finish_host", side_effect=original_owner) as finish:
                self.assertTrue(atom.recover_prior_host(auth, paths, state))
            finish.assert_called_once()
            self.assertEqual(state["prior_host_recovery"]["status"], "restored")
            self.assertEqual(json.loads(paths["state"].read_text()), state)

    def test_amendment_preflight_binds_failed_run_and_current_pr(self):
        prior = {"branch": "soodles/issue-1-" + "b" * 12,
                 "head": "b" * 40, "pr": {"number": 41}}
        authorization = {"repository": "ed3c/soodles", "base_head": "c" * 40,
                         "issue": {"number": 1}, "prior_publication": prior,
                         "workflow": self.auth["workflow"]}
        self.provider.repository_info.return_value = {
            "full_name": "ed3c/soodles", "default_branch": "main"}
        self.provider.base_head.return_value = "c" * 40
        pr = {"number": 41, "state": "open", "merged": False,
              "head": {"ref": prior["branch"], "sha": prior["head"]},
              "base": {"ref": "main"}, "body": "Refs ed3c/soodles#1"}
        self.provider.pull.return_value = pr
        self.provider.branch.return_value = {"object": {"sha": prior["head"]}}
        self.provider.workflow_runs.return_value = {
            "workflow_runs": [{**self.run, "head_sha": prior["head"], "conclusion": "failure"}]}
        failed_job = {**self.job, "conclusion": "failure",
                      "steps": [{**self.job["steps"][0], "conclusion": "failure"}]}
        self.provider.jobs.return_value = {"jobs": [failed_job]}
        atom.verify_failed_prior(self.provider, authorization)
        self.provider.pull.return_value = {**pr, "head": {**pr["head"], "sha": "f" * 40}}
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.prior_pr"):
            atom.verify_failed_prior(self.provider, authorization)
        self.provider.pull.return_value = pr
        self.provider.workflow_runs.return_value = {
            "workflow_runs": [{**self.run, "head_sha": prior["head"]}]}
        self.provider.jobs.return_value = {"jobs": [self.job]}
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.prior_runtime"):
            atom.verify_failed_prior(self.provider, authorization)

    def test_candidate_amendment_persists_offer_before_effect_and_never_repeats_it(self):
        with tempfile.TemporaryDirectory(prefix="issue-amendment-") as directory:
            path = Path(directory) / "state.json"
            prior = {"head": "b" * 40, "pr": {"number": 41}}
            authorization = {"prior_publication": prior}
            state = {"schema_version": 1, "writes": {}}
            claim = {"head": "a" * 40, "worktree_path": directory}
            calls = []
            def observed(*args, **kwargs):
                calls.append(kwargs)
                self.assertEqual(json.loads(path.read_text())["writes"]["candidate_amendment"],
                                 {"old_head": "b" * 40, "new_head": "a" * 40,
                                  "pr": 41, "status": "offered"})
                return {"status": "amended"}
            with patch.object(atom, "authenticated_push", return_value=lambda *_a, **_k: None), \
                 patch.object(atom.candidate_publication, "publish_amendment", side_effect=observed):
                self.assertEqual(atom.publish_candidate(authorization, state, {"state": path},
                                                        claim, {}, self.provider)["status"], "amended")
                self.assertIsNotNone(calls[0]["push"])
                atom.publish_candidate(authorization, state, {"state": path}, claim, {}, self.provider)
                self.assertIsNone(calls[1]["push"])
                with self.assertRaisesRegex(atom.AtomRefusal, "amendment.intent"):
                    atom.publish_candidate(authorization, state, {"state": path},
                                           {**claim, "head": "f" * 40}, {}, self.provider)
                self.assertEqual(len(calls), 2)

    def test_incomplete_job_cannot_authorize_completed_run(self):
        with self.assertRaisesRegex(atom.AtomRefusal, "workflow_job.status"):
            self.observe(self.run, [{**self.job, "status": "in_progress"}])

    def test_exact_green_result(self):
        self.assertEqual(self.observe(self.run, [self.job])[0], self.run)

    def test_other_head_is_not_adopted(self):
        self.assertEqual(self.observe({**self.run, "head_sha": "b" * 40}, [self.job]), (None, None))
        self.provider.jobs.assert_not_called()

    def test_wait_continues_same_entry(self):
        pending = {"status": "pending", "next": {"argv": ["same"]}}
        with patch.object(atom, "run", side_effect=[pending, {"status": "resolved", "next": None}]) as run:
            result = atom.drive("/fixture/auth.json", interval=0, sleep=lambda _: None)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(call.args == ("/fixture/auth.json",) for call in run.call_args_list))

    def test_wait_exhaustion_retains_pending_identity(self):
        pending = {"status": "pending", "next": {"argv": ["same"]}, "issue": {"number": 1}}
        with patch.object(atom, "run", return_value=pending) as run:
            result = atom.drive("/fixture/auth.json", timeout=0)
        self.assertTrue(result["wait_exhausted"])
        self.assertEqual(result["issue"], pending["issue"])
        run.assert_called_once()

    def test_refusal_is_never_retried(self):
        error = atom.AtomRefusal("github.issue.outcome", "unknown", "fresh_provider_readback")
        with patch.object(atom, "run", side_effect=error) as run:
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.drive("/fixture/auth.json", interval=0)
        self.assertIs(caught.exception, error)
        run.assert_called_once()

    def test_own_wait_refreshes_identity_before_legal_continuation(self):
        from test_issue_atom import IssueAtomTests
        fixture = IssueAtomTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        paths, state, snapshot = fixture.own_wait_fixture(running=True)
        def become_idle(_):
            snapshot["state"]["orders"]["schedule"]["stages"][0].update(status="pending", attempts=None)
            atom.save_json(fixture.root / ".noodle/state.snapshot.json", snapshot)
        # Reaching the existing credential gate proves normal continuation resumed.
        with fixture.own_wait_processes(), patch.object(atom.provider_credential,
                "resolve_host_environment", side_effect=RuntimeError("normal credential gate")) as gate:
            with self.assertRaisesRegex(RuntimeError, "normal credential gate"):
                atom.drive(fixture.path, interval=0, sleep=become_idle, environ=fixture.env)
        gate.assert_called_once()

    def test_own_wait_identity_drift_refuses_without_retry(self):
        from test_issue_atom import IssueAtomTests
        fixture = IssueAtomTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        paths, state, snapshot = fixture.own_wait_fixture()
        def drift(_):
            snapshot["state"]["orders"]["foreign"] = {
                "stages": [{"status": "running", "attempts": []}]}
            atom.save_json(fixture.root / ".noodle/state.snapshot.json", snapshot)
        sleeper = Mock(side_effect=drift)
        with fixture.own_wait_processes(), patch.object(atom.provider_credential, "supply_token") as supplier:
            with self.assertRaisesRegex(atom.AtomRefusal, "foreign_nonterminal"):
                atom.drive(fixture.path, interval=0, sleep=sleeper, environ=fixture.env)
        sleeper.assert_called_once()
        supplier.assert_not_called()
        self.assertEqual(atom.read_json(paths["state"], "state"), state)

    def test_native_receipt_is_the_prepublication_boundary(self):
        receipt = {"scope": "native publication readiness", "authorizes_landing": False}
        with patch.object(atom.candidate_publication, "native_readiness", return_value=receipt) as native, \
                patch.object(atom, "save_json") as save, \
                patch("soodles.acceptance_verify", side_effect=AssertionError("Linux-only")):
            self.assertEqual(atom._accept({"noodle": {"path": "/native"}},
                                          {"worktree_path": "/candidate"}, "/receipt"), receipt)
        native.assert_called_once_with(Path("/candidate"), {"worktree_path": "/candidate"}, {"path": "/native"})
        save.assert_called_once_with("/receipt", receipt, fresh=True)

    def test_publication_branch_does_not_replace_local_cleanup_identity(self):
        from test_landing import LandingTests
        fixture = LandingTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        branch = "soodles/issue-1-" + "a" * 12
        fixture.claim["publication_branch"] = branch
        fixture.snapshot["pr"]["head"]["ref"] = branch
        fixture.start()
        self.assertEqual(landing.read(fixture.checkpoint)["claim"]["worktree"], "example")
        self.assertEqual(fixture.offer()["expected_head_sha"], "a" * 40)

    def test_corrected_head_keeps_original_provider_pr_branch(self):
        from test_landing import LandingTests
        fixture = LandingTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        branch = "soodles/issue-1-" + "b" * 12
        fixture.claim["publication_branch"] = branch
        fixture.snapshot["pr"]["head"]["ref"] = branch
        fixture.start()
        self.assertEqual(landing.read(fixture.checkpoint)["claim"]["publication_branch"], branch)
        self.assertEqual(fixture.offer()["expected_head_sha"], "a" * 40)

    def test_unrelated_publication_branch_cannot_be_selected(self):
        from test_landing import LandingTests
        fixture = LandingTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.claim["publication_branch"] = "arbitrary-branch"
        with self.assertRaisesRegex(landing.LandingRefusal, "claim.publication_branch"):
            fixture.start()
        self.assertFalse(fixture.checkpoint.exists())


if __name__ == "__main__":
    unittest.main()
