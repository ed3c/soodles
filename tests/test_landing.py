import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import landing
import soodles


class LandingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "checkpoint.json"
        self.claim = {"repository": "ed3c/soodles", "issue": 1, "pr": 2, "head": "a" * 40,
                      "tree": "b" * 40, "base_head": "c" * 40, "run_id": 10, "run_attempt": 1,
                      "worktree": "example", "control_root": "/fixture", "verifier_sha256": landing.verifier_digest()}
        repo = {"full_name": "ed3c/soodles"}
        self.snapshot = {
            "pr": {"number": 2, "html_url": "https://github.com/ed3c/soodles/pull/2", "body": "Refs ed3c/soodles#1\n",
                   "head": {"repo": repo, "sha": "a" * 40, "ref": "example"},
                   "base": {"repo": repo, "sha": "c" * 40, "ref": "main"}, "merged": False,
                   "state": "open", "draft": False, "mergeable": True},
            "issue": {"number": 1, "html_url": "https://github.com/ed3c/soodles/issues/1", "state": "open"},
            "run": {"id": 10, "run_attempt": 1, "repository": repo, "head_repository": repo,
                    "head_sha": "a" * 40, "event": "pull_request", "path": ".github/workflows/runtime.yml",
                    "status": "completed", "conclusion": "success"},
            "commit": {"sha": "a" * 40, "tree": {"sha": "b" * 40}},
            "jobs": {"total_count": 1, "jobs": [{"id": 11, "name": "runtime-evidence", "run_id": 10, "head_sha": "a" * 40,
                "status": "completed", "conclusion": "success", "steps": [{"name": "Canonical acceptance on the exact candidate head",
                "status": "completed", "conclusion": "success"}]}]},
            "branch": {"name": "main", "commit": {"sha": "c" * 40}}}

    def start(self):
        return landing.start(self.claim, self.snapshot, self.checkpoint)

    def offer(self):
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "dispatch")
        return landing.dispatch(self.checkpoint, self.snapshot)

    def merged(self):
        self.snapshot["pr"].update(merged=True, state="closed", merged_at="2026-09-15T12:00:00Z", merge_commit_sha="d" * 40)
        self.snapshot["merge_commit"] = {"sha": "d" * 40, "tree": {"sha": "b" * 40},
                                         "parents": [{"sha": "c" * 40}, {"sha": "a" * 40}]}

    def test_intent_is_persisted_before_exact_head_request_and_no_unchanged_retry(self):
        self.start()
        request = self.offer()
        self.assertEqual(request["expected_head_sha"], self.claim["head"])
        self.assertEqual(request["merge_method"], "merge")
        self.assertEqual(landing.read(self.checkpoint)["phase"], "merge_pending")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "readback")
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], ["merge"])

    def test_prepared_intent_is_not_an_offer_and_requires_fresh_identity(self):
        self.start()
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "dispatch")
        before = self.checkpoint.read_bytes()
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], [])
        changed = copy.deepcopy(self.snapshot)
        changed["branch"]["commit"]["sha"] = "f" * 40
        with self.assertRaisesRegex(soodles.Refusal, "base.head"):
            landing.dispatch(self.checkpoint, changed)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        landing.dispatch(self.checkpoint, self.snapshot)
        with self.assertRaisesRegex(soodles.Refusal, "dispatch.status"):
            landing.dispatch(self.checkpoint, self.snapshot)

    def test_missing_or_inconsistent_delivery_evidence_cannot_dispatch(self):
        self.start()
        landing.advance(self.checkpoint, self.snapshot)
        prepared = landing.read(self.checkpoint)
        for mutation in ("missing", "wrong_action", "already_offered", "legacy_missing_offer"):
            state = copy.deepcopy(prepared)
            if mutation == "missing":
                state.pop("delivery")
            elif mutation == "wrong_action":
                state["delivery"]["action"] = "close"
            elif mutation == "already_offered":
                state["writes_offered"] = ["merge"]
            else:
                state["schema"] = 1
                state.pop("delivery")
            landing.save(self.checkpoint, state)
            before = self.checkpoint.read_bytes()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(soodles.Refusal, "checkpoint"):
                landing.dispatch(self.checkpoint, self.snapshot)
            self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_legacy_unknown_preserves_identity_and_cleanup_evidence(self):
        self.start()
        self.offer()
        state = landing.read(self.checkpoint)
        state["schema"] = 1
        state.pop("delivery")
        state["cleanup_intent"] = {"retained": "evidence"}
        landing.save(self.checkpoint, state)
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "readback")
        migrated = landing.read(self.checkpoint)
        self.assertEqual(migrated["schema"], 2)
        self.assertEqual(migrated["claim"], state["claim"])
        self.assertEqual(migrated["cleanup_intent"], state["cleanup_intent"])
        self.assertEqual(migrated["writes_offered"], ["merge"])
        with self.assertRaisesRegex(soodles.Refusal, "dispatch.status"):
            landing.dispatch(self.checkpoint, self.snapshot)

    def test_prepared_but_unoffered_provider_effect_cannot_be_adopted(self):
        self.start()
        landing.advance(self.checkpoint, self.snapshot)
        self.merged()
        with self.assertRaisesRegex(soodles.Refusal, "merge.owner"):
            landing.advance(self.checkpoint, self.snapshot)
        self.snapshot["pr"].update(merged=False, state="open")
        self.offer()
        self.merged()
        landing.advance(self.checkpoint, self.snapshot)
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="now")
        with self.assertRaisesRegex(soodles.Refusal, "closure.owner"):
            landing.advance(self.checkpoint, self.snapshot)

    def test_crash_after_merge_and_close_resumes_by_readback_without_duplicate_write(self):
        self.start()
        self.offer()
        self.merged()
        request = self.offer()
        self.assertEqual((request["action"], request["issue_number"]), ("close", 1))
        self.assertEqual(landing.read(self.checkpoint)["phase"], "close_pending")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "readback")
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="2026-09-15T12:01:00Z")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "reconcile")
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], ["merge", "close"])
        self.assertIsNone(landing.read(self.checkpoint)["classification"])

    def test_wrong_provider_identities_fail_before_checkpoint(self):
        cases = [("pr", "number", 4), ("pr", "body", "Refs other/repo#1"),
                 ("pr", "body", "Refs ed3c/soodles#1\nRefs ed3c/soodles#2"),
                 ("pr", "body", "Refs ed3c/soodles#1\nCloses #1"), ("issue", "number", 2),
                 ("run", "head_sha", "e" * 40), ("run", "id", 20), ("run", "run_attempt", 2),
                 ("run", "event", "push"), ("run", "conclusion", "failure"),
                 ("run", "path", ".github/workflows/other.yml"), ("pr", "draft", True)]
        for obj, key, value in cases:
            with self.subTest(obj=obj, key=key, value=value):
                data = copy.deepcopy(self.snapshot)
                data[obj][key] = value
                with self.assertRaises(soodles.Refusal):
                    landing.start(self.claim, data, self.checkpoint)
                self.assertFalse(self.checkpoint.exists())

    def test_foreign_repository_tree_base_and_skipped_step_refuse(self):
        for case in range(5):
            data = copy.deepcopy(self.snapshot)
            if case == 0:
                data["pr"]["head"]["repo"] = {"full_name": "other/repo"}
            elif case == 1:
                data["commit"]["tree"]["sha"] = "e" * 40
            elif case == 2:
                data["branch"]["commit"]["sha"] = "e" * 40
            elif case == 3:
                data["jobs"]["jobs"][0]["steps"][0]["conclusion"] = "skipped"
            else:
                data["jobs"]["jobs"][0]["head_sha"] = "e" * 40
            with self.subTest(case=case), self.assertRaises(soodles.Refusal):
                landing.start(self.claim, data, self.checkpoint)
            self.assertFalse(self.checkpoint.exists())

    def test_wrong_claim_fields_identity_and_verifier_cannot_admit(self):
        for key, value in (("repository", "other/repo"), ("issue", True), ("head", "HEAD"),
                           ("verifier_sha256", "x"), ("worktree", "../main"), ("permission", "bypass")):
            claim = {**self.claim, key: value}
            with self.subTest(key=key), self.assertRaises(soodles.Refusal):
                landing.start(claim, self.snapshot, self.checkpoint)
            self.assertFalse(self.checkpoint.exists())

    def test_checkpoint_cannot_be_overwritten_or_head_retargeted(self):
        self.start()
        before = self.checkpoint.read_bytes()
        with self.assertRaises(soodles.Refusal):
            self.start()
        self.snapshot["pr"]["head"]["sha"] = "f" * 40
        with self.assertRaises(soodles.Refusal):
            self.offer()
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_foreign_merge_parent_or_tree_cannot_close_issue(self):
        self.start()
        self.offer()
        self.merged()
        for field in ("parents", "tree"):
            data = copy.deepcopy(self.snapshot)
            data["merge_commit"][field] = [{"sha": "e" * 40}] if field == "parents" else {"sha": "e" * 40}
            with self.assertRaises(soodles.Refusal):
                landing.advance(self.checkpoint, data)
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], ["merge"])

    def test_wrong_closure_reason_and_closed_unmerged_do_not_resolve(self):
        self.start()
        self.offer()
        self.snapshot["pr"]["state"] = "closed"
        with self.assertRaises(soodles.Refusal):
            self.offer()
        self.merged()
        self.offer()
        self.snapshot["issue"].update(state="closed", state_reason="not_planned", closed_at="now")
        with self.assertRaises(soodles.Refusal):
            self.offer()

    def test_reconciliation_cannot_start_before_provider_closure(self):
        self.start()
        with patch.object(landing, "checked") as command:
            with self.assertRaises(soodles.Refusal):
                landing.reconcile(self.checkpoint, "/unused")
            command.assert_not_called()

    def test_dirty_root_and_wrong_origin_refuse_before_runtime_or_cleanup(self):
        root = Path(self.temp.name) / "control"
        root.mkdir()
        soodles.checked(["git", "init", "-b", "main"], root)
        (root / "file").write_text("clean")
        soodles.checked(["git", "add", "."], root)
        soodles.checked(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture"], root)
        soodles.checked(["git", "remote", "add", "origin", "https://github.com/other/repo.git"], root)
        self.claim["control_root"] = str(root)
        self.start()
        state = landing.read(self.checkpoint)
        state["phase"] = "awaiting_reconcile"
        landing.save(self.checkpoint, state)
        with patch.object(landing, "runtime_check") as runtime:
            with self.assertRaisesRegex(soodles.Refusal, "origin"):
                landing.reconcile(self.checkpoint, "/unused")
            soodles.checked(["git", "remote", "set-url", "origin", "https://github.com/ed3c/soodles.git"], root)
            (root / "file").write_text("dirty")
            with self.assertRaisesRegex(soodles.Refusal, "source.residue"):
                landing.reconcile(self.checkpoint, "/unused")
            runtime.assert_not_called()

    def test_unoffered_external_merge_or_closure_cannot_resolve_this_checkpoint(self):
        self.start()
        self.merged()
        with self.assertRaisesRegex(soodles.Refusal, "merge.owner"):
            self.offer()
        state = landing.read(self.checkpoint)
        state["schema"] = 1
        state["phase"] = "merge_pending"
        state["writes_offered"] = ["merge"]
        landing.save(self.checkpoint, state)
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="now")
        with self.assertRaisesRegex(soodles.Refusal, "closure.owner"):
            self.offer()

    def test_network_child_keeps_proxy_route_without_provider_or_git_injection(self):
        executable = Path(self.temp.name) / "git"
        executable.write_text('#!/bin/sh\n[ "$1 $2 $3" = "fetch origin main" ] && '
                              '[ "$HTTPS_PROXY" = "https://transport.invalid" ] && '
                              '[ -z "$GH_TOKEN$GITHUB_TOKEN$GIT_DIR$GIT_CONFIG_PARAMETERS" ]\n')
        executable.chmod(0o755)
        with patch.dict(os.environ, {"PATH": self.temp.name + os.pathsep + os.environ["PATH"],
                                     "HTTPS_PROXY": "https://transport.invalid", "GH_TOKEN": "secret", "GITHUB_TOKEN": "secret",
                                     "GIT_DIR": "/foreign", "GIT_CONFIG_PARAMETERS": "foreign"}):
            landing.fetch_main(Path(self.temp.name))

    def test_corrected_verifier_resume_preserves_identity_and_cannot_repeat_provider_writes(self):
        self.start()
        with self.assertRaisesRegex(soodles.Refusal, "resume.phase"):
            landing.resume(self.checkpoint, self.claim)
        state = landing.read(self.checkpoint)
        state.update(phase="reconciling", merge_sha="d" * 40, issue_closed_at="now", writes_offered=["merge", "close"])
        state["claim"]["verifier_sha256"] = "old-source"
        landing.save(self.checkpoint, state)
        with self.assertRaisesRegex(soodles.Refusal, "resume.claim"):
            landing.resume(self.checkpoint, {**self.claim, "issue": 99})
        result = landing.resume(self.checkpoint, self.claim)
        self.assertEqual(result["provider_requests"], [])
        resumed = landing.read(self.checkpoint)
        self.assertEqual(resumed["writes_offered"], ["merge", "close"])
        self.assertEqual(resumed["prior_verifiers"], ["old-source"])
        self.assertEqual(resumed["claim"], self.claim)

    def test_cli_help_and_malformed_input_refuse_before_checkpoint(self):
        for route in (["landing"], ["landing", "start"], ["landing", "advance"], ["landing", "dispatch"], ["landing", "readmit"], ["landing", "reconcile"]):
            result = soodles.run(["./soodles", *route, "--help"], soodles.ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
        bad = Path(self.temp.name) / "bad.json"
        bad.write_text(json.dumps({"repository": "other/repo"}))
        result = soodles.run(["./soodles", "landing", "start", bad, bad, self.checkpoint], soodles.ROOT)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claim.fields", result.stderr)
        self.assertIn("./soodles landing --help", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.checkpoint.exists())

    def recovery_inputs(self):
        def comparison(base, head):
            return {"base_commit": {"sha": base}, "merge_base_commit": {"sha": base},
                    "status": "ahead", "total_commits": 1, "commits": [{"sha": head}]}
        moved = copy.deepcopy(self.snapshot)
        moved["branch"]["commit"]["sha"] = moved["pr"]["base"]["sha"] = "f" * 40
        moved["base_comparison"] = comparison("c" * 40, "f" * 40)
        claim = {**self.claim, "base_head": "f" * 40, "head": "e" * 40, "tree": "d" * 40, "run_id": 20}
        fresh = copy.deepcopy(moved)
        fresh["pr"]["head"]["sha"] = "e" * 40
        fresh["commit"] = {"sha": "e" * 40, "tree": {"sha": "d" * 40}}
        fresh["run"].update(id=20, head_sha="e" * 40)
        fresh["jobs"]["jobs"][0].update(run_id=20, head_sha="e" * 40)
        fresh["candidate_comparison"] = comparison("f" * 40, "e" * 40)
        return moved, claim, fresh

    def test_dispatch_base_drift_invalidates_without_emitting_or_reusing_old_acceptance(self):
        self.start()
        landing.advance(self.checkpoint, self.snapshot)
        moved, claim, fresh = self.recovery_inputs()
        result = landing.dispatch(self.checkpoint, moved)
        self.assertEqual(result["action"], "readmit")
        self.assertEqual(result["invalid"], {"field": "base.head", "value": "f" * 40, "expected": "c" * 40})
        self.assertEqual(result["next_command"], "./soodles landing readmit --help")
        invalidated = self.checkpoint.read_bytes()
        self.assertEqual(landing.advance(self.checkpoint, moved)["action"], "readmit")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "readmit")
        with self.assertRaisesRegex(soodles.Refusal, "landing readmit --help"):
            landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(self.checkpoint.read_bytes(), invalidated)
        landing.readmit(self.checkpoint, claim, fresh)
        state = landing.read(self.checkpoint)
        self.assertEqual(state["prior_admissions"][0]["claim"], self.claim)
        self.assertEqual(state["prior_admissions"][0]["classification"], "SUPERSEDED")
        self.assertEqual(state["prior_admissions"][0]["delivery"]["status"], "prepared")
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, "readmit.phase"):
            landing.readmit(self.checkpoint, claim, fresh)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        landing.advance(self.checkpoint, fresh)
        self.assertEqual(landing.dispatch(self.checkpoint, fresh)["expected_head_sha"], claim["head"])

    def test_recovery_requires_forward_complete_comparison_and_original_subject(self):
        self.start()
        moved, _, _ = self.recovery_inputs()
        cases = [lambda s: s.pop("base_comparison"),
                 lambda s: s["base_comparison"].update(status="diverged"),
                 lambda s: s["base_comparison"].update(total_commits=2),
                 lambda s: s["base_comparison"]["base_commit"].update(sha="d" * 40),
                 lambda s: s["base_comparison"]["merge_base_commit"].update(sha="d" * 40),
                 lambda s: s["base_comparison"]["commits"][-1].update(sha="d" * 40),
                 lambda s: s["pr"]["head"].update(sha="d" * 40),
                 lambda s: s["run"].update(conclusion="failure")]
        before = self.checkpoint.read_bytes()
        for index, mutate in enumerate(cases):
            data = copy.deepcopy(moved)
            mutate(data)
            with self.subTest(case=index), self.assertRaises(soodles.Refusal):
                landing.advance(self.checkpoint, data)
            self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_fresh_admission_rejects_identity_changes_stale_acceptance_and_bad_ancestry(self):
        self.start()
        moved, claim, fresh = self.recovery_inputs()
        landing.advance(self.checkpoint, moved)
        before = self.checkpoint.read_bytes()
        for field, value in (("issue", 99), ("pr", 99), ("repository", "other/repo"),
                             ("worktree", "other"), ("control_root", "/other"), ("verifier_sha256", "other"),
                             ("head", self.claim["head"]), ("base_head", self.claim["base_head"]), ("run_id", 10)):
            with self.subTest(field=field), self.assertRaises(soodles.Refusal):
                landing.readmit(self.checkpoint, {**claim, field: value}, fresh)
            self.assertEqual(self.checkpoint.read_bytes(), before)
        for field in ("base_comparison", "candidate_comparison"):
            data = copy.deepcopy(fresh)
            data[field]["merge_base_commit"]["sha"] = "b" * 40
            with self.subTest(field=field), self.assertRaisesRegex(soodles.Refusal, field):
                landing.readmit(self.checkpoint, claim, data)
            self.assertEqual(self.checkpoint.read_bytes(), before)
        for target, key, value in (("run", "head_sha", self.claim["head"]), ("run", "conclusion", "failure"),
                                   ("run", "run_attempt", 2), ("issue", "state", "closed")):
            data = copy.deepcopy(fresh)
            data[target][key] = value
            with self.subTest(key=key), self.assertRaises(soodles.Refusal):
                landing.readmit(self.checkpoint, claim, data)
            self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_base_advances_again_requires_ancestry_from_observed_recovery_base(self):
        self.start()
        moved, claim, fresh = self.recovery_inputs()
        landing.advance(self.checkpoint, moved)
        new_base = "1" * 40
        claim["base_head"] = new_base
        fresh["branch"]["commit"]["sha"] = fresh["pr"]["base"]["sha"] = new_base
        fresh["base_comparison"]["commits"][-1]["sha"] = new_base
        fresh["candidate_comparison"]["base_commit"]["sha"] = new_base
        fresh["candidate_comparison"]["merge_base_commit"]["sha"] = new_base
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, "recovery_comparison"):
            landing.readmit(self.checkpoint, claim, fresh)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        fresh["recovery_comparison"] = {"base_commit": {"sha": "f" * 40}, "merge_base_commit": {"sha": "f" * 40},
                                        "status": "ahead", "total_commits": 1, "commits": [{"sha": new_base}]}
        landing.readmit(self.checkpoint, claim, fresh)
        self.assertEqual(landing.read(self.checkpoint)["claim"], claim)

    def test_legacy_admitted_can_recover_but_legacy_pending_remains_unknown(self):
        self.start()
        moved, claim, fresh = self.recovery_inputs()
        admitted = landing.read(self.checkpoint)
        admitted.update(schema=1, cleanup_intent={"preserved": True})
        landing.save(self.checkpoint, admitted)
        landing.advance(self.checkpoint, moved)
        landing.readmit(self.checkpoint, claim, fresh)
        self.assertEqual(landing.read(self.checkpoint)["cleanup_intent"], {"preserved": True})
        unknown = {**admitted, "phase": "merge_pending", "writes_offered": ["merge"]}
        landing.save(self.checkpoint, unknown)
        self.assertEqual(landing.advance(self.checkpoint, moved)["action"], "readback")
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, "readmit.phase"):
            landing.readmit(self.checkpoint, claim, fresh)
        self.assertEqual(self.checkpoint.read_bytes(), before)
