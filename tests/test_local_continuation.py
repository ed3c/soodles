from pathlib import Path
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
