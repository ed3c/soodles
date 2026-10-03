import contextlib
import copy
import hashlib
import json
import os
import subprocess
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
        self.checkpoint = Path(self.temp.name).resolve() / "checkpoint.json"
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
        return landing.dispatch(self.checkpoint, self.snapshot)["request"]

    def merged(self):
        self.snapshot["pr"].update(merged=True, state="closed", merged_at="2026-09-15T12:00:00Z", merge_commit_sha="d" * 40)
        self.snapshot["merge_commit"] = {"sha": "d" * 40, "tree": {"sha": "b" * 40},
                                         "parents": [{"sha": "c" * 40}, {"sha": "a" * 40}]}

    def cloud_control(self, name):
        root = Path(self.temp.name) / name
        root.mkdir()
        soodles.checked(["git", "init", "-b", "main"], root)
        (root / "file").write_text("clean")
        soodles.checked(["git", "add", "."], root)
        soodles.checked(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                         "commit", "-m", "fixture"], root)
        soodles.checked(["git", "remote", "add", "origin", "https://github.com/ed3c/soodles.git"], root)
        head = soodles.checked(["git", "rev-parse", "HEAD"], root)
        tree = soodles.checked(["git", "rev-parse", "HEAD^{tree}"], root)
        claim = {**self.claim, "head": head, "tree": tree, "base_head": head,
                 "worktree": "cloud-only", "control_root": str(root)}
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["pr"]["head"].update(sha=head, ref="cloud-only")
        snapshot["pr"]["base"]["sha"] = head
        snapshot["commit"] = {"sha": head, "tree": {"sha": tree}}
        snapshot["run"]["head_sha"] = head
        snapshot["jobs"]["jobs"][0]["head_sha"] = head
        snapshot["branch"]["commit"]["sha"] = head
        return root, claim, snapshot, head

    def test_registered_detached_control_root_requires_exact_admitted_head(self):
        primary, claim, _, head = self.cloud_control("detached-primary")
        detached = Path(self.temp.name).resolve() / "detached-control"
        soodles.checked(["git", "worktree", "add", "--detach", str(detached), head], primary)
        claim.update(control_root=str(detached), base_head=head)
        before = soodles.source_identity(detached)
        state = {"phase": "awaiting_reconcile"}
        landing.require_control_checkout(detached, claim, state, before,
                                         {"execution": {"control_root": str(detached)}}, "main")
        with self.assertRaisesRegex(landing.LandingRefusal, "local.branch"):
            landing.require_control_checkout(detached, claim, state, before, None, "main")
        with self.assertRaisesRegex(landing.LandingRefusal, "local.detached_head"):
            landing.require_control_checkout(detached, {**claim, "base_head": "f" * 40},
                                             state, before,
                                             {"execution": {"control_root": str(detached)}}, "main")

    def test_postwrite_detached_control_fast_forwards_without_branch_switch(self):
        primary, claim, _, base = self.cloud_control("detached-reconcile-primary")
        detached = Path(self.temp.name).resolve() / "detached-reconcile-control"
        soodles.checked(["git", "worktree", "add", "--detach", str(detached), base], primary)
        (primary / "merged").write_text("provider merge\n")
        soodles.checked(["git", "add", "merged"], primary)
        soodles.checked(["git", "-c", "user.name=Fixture", "-c",
                         "user.email=fixture@example.invalid", "commit", "-m", "merged"], primary)
        merged = soodles.checked(["git", "rev-parse", "HEAD"], primary)
        soodles.checked(["git", "update-ref", "refs/remotes/origin/main", merged], primary)
        claim.update(control_root=str(detached), base_head=base,
                     execution_envelope={"path": str(Path(self.temp.name) / "envelope.json"),
                                         "sha256": "f" * 64})
        landing.save(self.checkpoint, {"schema": 2, "claim": claim,
                     "phase": "awaiting_reconcile", "classification": None,
                     "writes_offered": ["merge", "close"], "merge_sha": merged,
                     "issue_closed_at": "now"})
        binary = str(Path("/bin/true").resolve())
        (primary / ".git/info/exclude").write_text(".noodle/\n")
        (detached / ".noodle").mkdir()
        (detached / ".noodle/noodle.lock").touch()
        envelope = {"execution": {"carrier": {"noodle": {"sha256": "f" * 64}},
                                  "order_id": "fixture-order"}}
        with patch("landing.execution_binding", return_value=envelope), \
                patch("landing.fetch_main", side_effect=lambda root: None) as fetch, \
                patch("issue_execution.validate_carrier", return_value={"noodle": binary}), \
                patch("issue_execution.read_owner", return_value={"state": {"orders": {}}}), \
                patch("issue_execution.completed_original_order",
                      return_value={"order_id": "fixture-order"}):
            result = landing.reconcile(self.checkpoint, binary)
        fetch.assert_called_once_with(detached)
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(soodles.checked(["git", "rev-parse", "HEAD"], detached), merged)
        self.assertEqual(soodles.checked(["git", "branch", "--show-current"], detached), "")
        self.assertEqual(result["writes_offered"], ["merge", "close"])

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
        with self.assertRaisesRegex(soodles.Refusal, "base_comparison"):
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
        for case in range(8):
            data = copy.deepcopy(self.snapshot)
            data["pr"]["base"]["sha"] = "9" * 40
            if case == 0:
                data["pr"]["head"]["repo"] = {"full_name": "other/repo"}
            elif case == 1:
                data["commit"]["tree"]["sha"] = "e" * 40
            elif case == 2:
                data["branch"]["commit"]["sha"] = "e" * 40
            elif case == 3:
                data["jobs"]["jobs"][0]["steps"][0]["conclusion"] = "skipped"
            elif case == 4:
                data["jobs"]["jobs"][0]["head_sha"] = "e" * 40
            elif case == 5:
                data["pr"]["base"]["repo"] = {"full_name": "other/repo"}
            elif case == 6:
                data["pr"]["base"]["ref"] = "other"
            else:
                data["branch"]["name"] = "other"
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

    def test_merged_readback_start_keeps_confirmed_claim_without_creating_checkpoint(self):
        self.merged()
        self.snapshot.pop("merge_commit")
        with self.assertRaises(landing.LandingRefusal) as raised:
            self.start()
        out = landing.refusal_output(raised.exception, "start")
        self.assertEqual(out["invalid"], {"field": "merge_commit", "value": None})
        self.assertEqual(out["next"]["operation"], "start")
        self.assertEqual(out["next"]["known"], {"checkpoint": str(self.checkpoint), "claim": self.claim})
        self.assertEqual(out["next"]["requests"]["merge_commit"], {
            "method": "GET", "url": "https://api.github.com/repos/ed3c/soodles/git/commits/" + "d" * 40})
        self.assertFalse(self.checkpoint.exists())
        self.assertFalse(Path(str(self.checkpoint) + ".lock").exists())
        self.merged()
        with self.assertRaisesRegex(soodles.Refusal, "pr.merged"):
            self.start()
        self.assertFalse(self.checkpoint.exists())

    def test_merged_readback_readmit_retains_fresh_claim_without_adopting_provider_effect(self):
        self.start()
        landing.invalidate(self.checkpoint)
        fresh = {**self.claim, "head": "e" * 40, "run_id": 20}
        self.snapshot["pr"]["head"]["sha"] = fresh["head"]
        self.snapshot["commit"]["sha"] = fresh["head"]
        self.snapshot["run"].update(id=20, head_sha=fresh["head"])
        self.snapshot["jobs"]["jobs"][0].update(run_id=20, head_sha=fresh["head"])
        self.merged()
        self.snapshot.pop("merge_commit")
        before = self.checkpoint.read_bytes()
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.readmit(self.checkpoint, fresh, self.snapshot)
        out = landing.refusal_output(raised.exception, "readmit")
        self.assertEqual(out["next"]["operation"], "readmit")
        self.assertEqual(out["next"]["known"], {"checkpoint": str(self.checkpoint), "claim": fresh})
        self.assertEqual(self.checkpoint.read_bytes(), before)
        self.merged()
        self.snapshot["merge_commit"]["parents"][1]["sha"] = fresh["head"]
        with self.assertRaisesRegex(soodles.Refusal, "readmit.pr.merged"):
            landing.readmit(self.checkpoint, fresh, self.snapshot)
        self.assertEqual(self.checkpoint.read_bytes(), before)

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

    def test_corrected_verifier_can_resume_completed_awaiting_reconcile(self):
        self.start()
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"])
        state["claim"]["verifier_sha256"] = "old-source"
        landing.save(self.checkpoint, state)
        result = landing.resume(self.checkpoint, self.claim)
        self.assertEqual(result["phase"], "awaiting_reconcile")
        self.assertEqual(result["provider_requests"], [])
        resumed = landing.read(self.checkpoint)
        self.assertEqual(resumed["writes_offered"], ["merge", "close"])
        self.assertEqual(resumed["prior_verifiers"], ["old-source"])
        self.assertEqual(resumed["claim"], self.claim)
        for field in ("merge_sha", "issue_closed_at"):
            incomplete = copy.deepcopy(state)
            incomplete.pop(field)
            landing.save(self.checkpoint, incomplete)
            with self.subTest(field=field), self.assertRaisesRegex(soodles.Refusal, "resume.phase"):
                landing.resume(self.checkpoint, self.claim)
        incomplete = copy.deepcopy(state)
        incomplete["writes_offered"] = ["merge"]
        landing.save(self.checkpoint, incomplete)
        with self.assertRaisesRegex(soodles.Refusal, "resume.phase"):
            landing.resume(self.checkpoint, self.claim)

    def test_cloud_claim_resolves_from_provider_readback_without_local_tools(self):
        claim = {key: value for key, value in self.claim.items() if key != "control_root"}
        landing.start(claim, self.snapshot, self.checkpoint)
        landing.advance(self.checkpoint, self.snapshot)
        landing.dispatch(self.checkpoint, self.snapshot)
        self.merged()
        landing.advance(self.checkpoint, self.snapshot)
        landing.dispatch(self.checkpoint, self.snapshot)
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="now")
        self.snapshot["branch"]["commit"]["sha"] = "d" * 40
        with patch.object(landing, "fetch_main") as fetch, patch.object(landing, "runtime_check") as runtime:
            result = landing.advance(self.checkpoint, self.snapshot)
        fetch.assert_not_called()
        runtime.assert_not_called()
        self.assertEqual((result["phase"], result["classification"], result["action"], result["next"]),
                         ("resolved", "RESOLVED", "stop", None))
        self.assertEqual(result["provider_reconciliation"], {
            "mode": "cloud", "main_head": "d" * 40, "merge_sha": "d" * 40,
            "provider": "GitHub", "local_reconciliation_required": False})
        self.assertEqual(result["writes_offered"], ["merge", "close"])

    def test_cloud_provider_main_advance_requires_complete_comparison(self):
        claim = {key: value for key, value in self.claim.items() if key != "control_root"}
        landing.start(claim, self.snapshot, self.checkpoint)
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"],
                     delivery={"action": "close", "status": "offered"})
        landing.save(self.checkpoint, state)
        self.merged()
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="now")
        self.snapshot["branch"]["commit"]["sha"] = "e" * 40
        before = self.checkpoint.read_bytes()
        with self.assertRaises(landing.LandingRefusal) as caught:
            landing.advance(self.checkpoint, self.snapshot)
        self.assertEqual(caught.exception.invalid["field"], "main_comparison")
        self.assertEqual(caught.exception.next_action["operation"], "advance")
        self.assertIn("main_comparison", caught.exception.next_action["requests"])
        self.assertEqual(self.checkpoint.read_bytes(), before)
        self.snapshot["main_comparison"] = {
            "base_commit": {"sha": "d" * 40}, "merge_base_commit": {"sha": "d" * 40},
            "status": "ahead", "total_commits": 1, "commits": [{"sha": "e" * 40}]}
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["classification"], "RESOLVED")

    def test_completed_legacy_checkpoint_can_migrate_local_to_cloud_route(self):
        self.start()
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"], delivery={"action": "close", "status": "offered"})
        state["claim"]["verifier_sha256"] = "old-source"
        state["cleanup_intent"] = {"mode": "no_op", "path_present": False, "branch_head": None,
                                   "registrations": [], "main_head": "c" * 40}
        landing.save(self.checkpoint, state)
        cloud = {key: value for key, value in self.claim.items() if key != "control_root"}
        result = landing.resume(self.checkpoint, cloud)
        self.assertEqual((result["action"], result["next"]["kind"], result["next"]["operation"]),
                         ("readback", "provider_readback", "advance"))
        self.assertEqual(result["provider_requests"], [])
        migrated = landing.read(self.checkpoint)
        self.assertNotIn("control_root", migrated["claim"])
        self.assertEqual(migrated["prior_routes"], [{"route": "local", "control_root": "/fixture"}])
        self.merged()
        self.snapshot["issue"].update(state="closed", state_reason="completed", closed_at="now")
        self.snapshot["branch"]["commit"]["sha"] = "d" * 40
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["classification"], "RESOLVED")

    def test_cloud_route_migration_refuses_local_obligations_and_identity_changes(self):
        self.start()
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"], delivery={"action": "close", "status": "offered"})
        state["claim"]["verifier_sha256"] = "old-source"
        cloud = {key: value for key, value in self.claim.items() if key != "control_root"}
        for mutation, value, field in (
                ("identity", {**cloud, "issue": 99}, "resume.claim"),
                ("cleanup", cloud, "resume.cleanup_intent"),
                ("envelope", cloud, "resume.route")):
            candidate = copy.deepcopy(state)
            if mutation == "cleanup":
                candidate["cleanup_intent"] = {"path_present": True}
            elif mutation == "envelope":
                candidate["claim"]["execution_envelope"] = {"path": "/fixture/envelope", "sha256": "f" * 64}
            landing.save(self.checkpoint, candidate)
            before = self.checkpoint.read_bytes()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(soodles.Refusal, field):
                landing.resume(self.checkpoint, value)
            self.assertEqual(self.checkpoint.read_bytes(), before)
        landing.save(self.checkpoint, state)
        changed_dependencies = {**cloud, "dependencies": [{
            "repository": "ed3c/soodles", "issue": 113, "pr": 114,
            "base_ref": "main", "base_head": "a" * 40,
            "candidate_head": "b" * 40, "tree": "c" * 40,
            "revision": "d" * 40, "run_id": 1, "run_attempt": 1,
            "workflow_path": ".github/workflows/runtime.yml",
            "jobs": {"runtime-evidence": ["Canonical acceptance on the exact candidate head"]},
        }]}
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, "resume.claim"):
            landing.resume(self.checkpoint, changed_dependencies)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        legacy_cloud = copy.deepcopy(state)
        legacy_cloud["claim"].pop("control_root")
        landing.save(self.checkpoint, legacy_cloud)
        with self.assertRaisesRegex(soodles.Refusal, "resume.route"):
            landing.resume(self.checkpoint, self.claim)

    def test_cloud_claim_refuses_local_reconcile_and_local_claim_keeps_binary_boundary(self):
        cloud = {key: value for key, value in self.claim.items() if key != "control_root"}
        landing.start(cloud, self.snapshot, self.checkpoint)
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"], delivery={"action": "close", "status": "offered"})
        landing.save(self.checkpoint, state)
        with patch.object(landing, "checked") as command, self.assertRaisesRegex(soodles.Refusal, "reconcile.route"):
            landing.reconcile(self.checkpoint, "/unused")
        command.assert_not_called()
        self.checkpoint.unlink()
        self.start()
        local = landing.read(self.checkpoint)
        local.update(phase="awaiting_reconcile", merge_sha="d" * 40, issue_closed_at="now",
                     writes_offered=["merge", "close"], delivery={"action": "close", "status": "offered"})
        landing.save(self.checkpoint, local)
        result = landing.advance(self.checkpoint, {**self.snapshot,
            "pr": {**self.snapshot["pr"], "merged": True, "state": "closed", "merged_at": "now",
                   "merge_commit_sha": "d" * 40},
            "issue": {**self.snapshot["issue"], "state": "closed", "state_reason": "completed", "closed_at": "now"},
            "merge_commit": {"sha": "d" * 40, "tree": {"sha": "b" * 40},
                             "parents": [{"sha": "c" * 40}, {"sha": "a" * 40}]}})
        self.assertEqual((result["action"], result["next"]["required"]), ("reconcile", ["binary"]))

    def test_cloud_only_absence_is_persisted_as_noop_cleanup(self):
        root, claim, snapshot, head = self.cloud_control("cloud-control")
        soodles.checked(["git", "update-ref", "refs/remotes/origin/main", head], root)
        landing.start(claim, snapshot, self.checkpoint)
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha=head, issue_closed_at="now",
                     writes_offered=["merge", "close"])
        landing.save(self.checkpoint, state)
        runtime = {"observed_binary_sha256": "f" * 64}
        with patch.object(landing, "runtime_check", return_value=runtime), \
                patch.object(landing, "fetch_main", side_effect=landing.LandingRefusal("git.fetch.exit", 128)):
            with self.assertRaisesRegex(soodles.Refusal, "git.fetch.exit"):
                landing.reconcile(self.checkpoint, "/unused")
        interrupted = landing.read(self.checkpoint)
        self.assertEqual(interrupted["phase"], "reconciling")
        self.assertEqual(interrupted["cleanup_intent"]["mode"], "no_op")
        with patch.object(landing, "runtime_check", return_value=runtime), patch.object(landing, "fetch_main") as fetch:
            result = landing.reconcile(self.checkpoint, "/unused")
            fetch.assert_called_once_with(root.resolve())
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertIsNone(result["next"])
        self.assertEqual(result["writes_offered"], ["merge", "close"])
        self.assertEqual(result["local"]["cleanup_mode"], "no_op")
        intent = landing.read(self.checkpoint)["cleanup_intent"]
        self.assertEqual((intent["mode"], intent["path_present"], intent["branch_head"], intent["registrations"]),
                         ("no_op", False, None, []))

    def test_cloud_only_noop_refuses_branch_or_registration_before_checkpoint_change(self):
        root, claim, snapshot, head = self.cloud_control("cloud-negative")
        landing.start(claim, snapshot, self.checkpoint)
        state = landing.read(self.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha=head, issue_closed_at="now",
                     writes_offered=["merge", "close"])
        landing.save(self.checkpoint, state)
        runtime = {"observed_binary_sha256": "f" * 64}
        soodles.checked(["git", "branch", "cloud-only", head], root)
        before = self.checkpoint.read_bytes()
        with patch.object(landing, "runtime_check", return_value=runtime), patch.object(landing, "fetch_main") as fetch:
            with self.assertRaisesRegex(soodles.Refusal, "cleanup.branch"):
                landing.reconcile(self.checkpoint, "/unused")
        fetch.assert_not_called()
        self.assertEqual(self.checkpoint.read_bytes(), before)
        soodles.checked(["git", "branch", "-D", "cloud-only"], root)
        foreign = Path(self.temp.name) / "foreign-cloud-only"
        soodles.checked(["git", "worktree", "add", "-b", "cloud-only", str(foreign), head], root)
        with patch.object(landing, "runtime_check", return_value=runtime), patch.object(landing, "fetch_main") as fetch:
            with self.assertRaisesRegex(soodles.Refusal, "cleanup.registration"):
                landing.reconcile(self.checkpoint, "/unused")
        fetch.assert_not_called()
        self.assertEqual(self.checkpoint.read_bytes(), before)
        soodles.checked(["git", "worktree", "remove", str(foreign)], root)
        soodles.checked(["git", "branch", "-D", "cloud-only"], root)

    def test_cli_help_and_malformed_input_refuse_before_checkpoint(self):
        for route in (["landing"], ["landing", "start"], ["landing", "advance"],
                      ["landing", "dispatch"],
                      ["landing", "readmit"], ["landing", "reconcile"]):
            result = soodles.run(["./soodles", *route, "--help"], soodles.ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
        bad = Path(self.temp.name) / "bad.json"
        bad.write_text(json.dumps({"repository": "other/repo"}))
        result = soodles.run(["./soodles", "landing", "start", bad, bad, self.checkpoint], soodles.ROOT)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claim.fields", result.stderr)
        self.assertEqual(json.loads(result.stdout)["next"]["operation"], "start")
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.checkpoint.exists())

    def recovery_inputs(self):
        def comparison(base, head):
            return {"base_commit": {"sha": base}, "merge_base_commit": {"sha": base},
                    "status": "ahead", "total_commits": 1, "commits": [{"sha": head}]}
        moved = copy.deepcopy(self.snapshot)
        moved["branch"]["commit"]["sha"] = "f" * 40
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
        self.assertEqual(result["next"]["operation"], "readmit")
        invalidated = self.checkpoint.read_bytes()
        self.assertEqual(landing.advance(self.checkpoint, moved)["action"], "readmit")
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)["action"], "readmit")
        with self.assertRaisesRegex(soodles.Refusal, "dispatch.phase") as refused:
            landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(refused.exception.next_action["operation"], "readmit")
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
        self.assertEqual(landing.dispatch(self.checkpoint, fresh)["request"]["expected_head_sha"], claim["head"])

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

    def test_malformed_comparison_refuses_exact_field_without_traceback_or_checkpoint_change(self):
        self.start()
        moved, _, _ = self.recovery_inputs()
        sf = Path(self.temp.name) / "readback.json"
        before = self.checkpoint.read_bytes()
        for key, value, field in (("base_commit", [], "base_commit"), ("merge_base_commit", None, "merge_base_commit"),
                                  ("commits", None, "commits"), ("commits", [None], "commits[-1]"),
                                  ("total_commits", True, "total_commits")):
            data = copy.deepcopy(moved)
            data["base_comparison"][key] = value
            sf.write_text(json.dumps(data))
            result = soodles.run(["./soodles", "landing", "advance", self.checkpoint, sf], soodles.ROOT)
            with self.subTest(field=field):
                self.assertEqual(result.returncode, 1)
                self.assertIn("invalid base_comparison." + field + "=", result.stderr)
                next_action = json.loads(result.stdout)["next"]
                self.assertEqual(next_action["operation"], "advance")
                self.assertEqual(next_action["owner"], "GitHub")
                request = next_action["requests"]["base_comparison"]
                self.assertEqual(request, {"method": "GET", "url":
                    "https://api.github.com/repos/ed3c/soodles/compare/" + "c" * 40 + "..." + "f" * 40})
                self.assertEqual(next_action["known"]["checkpoint"], str(self.checkpoint))
                self.assertIn(request["url"], result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_comparison_guidance_preserves_fresh_claim_and_rejects_unconfirmed_endpoint(self):
        self.start()
        moved, fresh_claim, fresh = self.recovery_inputs()
        before = self.checkpoint.read_bytes()
        for invalid in ("refs/heads/main", "../another", None):
            bad = copy.deepcopy(moved)
            bad["branch"]["commit"]["sha"] = bad["pr"]["base"]["sha"] = invalid
            with self.assertRaises(landing.LandingRefusal) as error:
                landing.advance(self.checkpoint, bad)
            self.assertIsNone(error.exception.next_action)
            self.assertEqual(self.checkpoint.read_bytes(), before)
        landing.advance(self.checkpoint, moved)
        pending = self.checkpoint.read_bytes()
        missing = copy.deepcopy(fresh); missing.pop("candidate_comparison")
        with self.assertRaises(landing.LandingRefusal) as error:
            landing.readmit(self.checkpoint, fresh_claim, missing)
        nxt = error.exception.next_action
        self.assertEqual(nxt["operation"], "readmit")
        self.assertEqual(nxt["known"]["claim"], fresh_claim)
        self.assertEqual(nxt["requests"]["candidate_comparison"]["url"],
                         "https://api.github.com/repos/ed3c/soodles/compare/" + "f"*40 + "..." + "e"*40)
        self.assertEqual(nxt["requests"]["commit"]["url"].rsplit("/", 1)[-1], fresh_claim["head"])
        self.assertEqual(self.checkpoint.read_bytes(), pending)
        landing.readmit(self.checkpoint, fresh_claim, fresh)
        state = landing.read(self.checkpoint)
        self.assertEqual(state["phase"], "admitted")
        self.assertEqual(state["writes_offered"], [])
        self.assertNotIn("next", state)

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

    def test_supervisor_withdraws_green_without_new_ci_or_provider_write(self):
        self.start()
        landing.advance(self.checkpoint, self.snapshot)
        old = landing.read(self.checkpoint)
        result = landing.invalidate(self.checkpoint)
        self.assertEqual(result['next']['operation'], 'readmit')
        self.assertEqual(result['provider_requests'], [])
        state = landing.read(self.checkpoint)
        self.assertEqual(state['claim'], old['claim'])
        self.assertEqual(state['delivery'], old['delivery'])
        self.assertIsNone(state['classification'])
        before = self.checkpoint.read_bytes()
        landing.invalidate(self.checkpoint)
        failed = copy.deepcopy(self.snapshot)
        failed['run']['conclusion'] = 'failure'
        self.assertEqual(landing.advance(self.checkpoint, failed)['action'], 'readmit')
        self.assertEqual(self.checkpoint.read_bytes(), before)
        with self.assertRaisesRegex(soodles.Refusal, 'dispatch.phase'):
            landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_amendment_allows_forward_base_but_preserves_ancestry_controls(self):
        self.start()
        landing.invalidate(self.checkpoint)
        _, claim, fresh = self.recovery_inputs()
        invalid = copy.deepcopy(fresh)
        invalid.pop('base_comparison')
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, 'base_comparison'):
            landing.readmit(self.checkpoint, claim, invalid)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        landing.readmit(self.checkpoint, claim, fresh)
        state = landing.read(self.checkpoint)
        self.assertEqual(state['prior_admissions'][0]['claim'], self.claim)
        self.assertIsNone(state['classification'])
        with self.assertRaisesRegex(soodles.Refusal, 'checkpoint.phase'):
            landing.reconcile(self.checkpoint, '/not-executed')

    def test_invalidation_retains_legacy_empty_admission_and_base_recovery(self):
        self.start()
        original = landing.read(self.checkpoint)
        original['schema'] = 1
        landing.save(self.checkpoint, original)
        landing.invalidate(self.checkpoint)
        self.assertEqual(landing.read(self.checkpoint)['schema'], 2)
        landing.save(self.checkpoint, original)
        moved, _, _ = self.recovery_inputs()
        landing.advance(self.checkpoint, moved)
        before = self.checkpoint.read_bytes()
        self.assertEqual(landing.invalidate(self.checkpoint)['invalid']['field'], 'base.head')
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_amendment_record_cannot_launder_corrupt_identity_or_unknown_writes(self):
        self.start()
        landing.invalidate(self.checkpoint)
        good = landing.read(self.checkpoint)
        for field, value in [('previous_head', 'f'*40), ('base_head', 'f'*40), ('kind', 'unknown')]:
            state = copy.deepcopy(good)
            state['recovery'][field] = value
            landing.save(self.checkpoint, state)
            before = self.checkpoint.read_bytes()
            with self.subTest(field=field), self.assertRaisesRegex(soodles.Refusal, 'checkpoint.recovery'):
                landing.invalidate(self.checkpoint)
            self.assertEqual(self.checkpoint.read_bytes(), before)
        state = copy.deepcopy(good)
        state['writes_offered'] = ['merge']
        landing.save(self.checkpoint, state)
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(soodles.Refusal, 'checkpoint.writes_offered'):
            landing.invalidate(self.checkpoint)
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_owner_projection_names_missing_input_without_executable_placeholder(self):
        result = self.start()
        next_action = result['next']
        self.assertEqual(next_action['owner'], 'GitHub')
        self.assertEqual(next_action['requests']['pr']['url'], 'https://api.github.com/repos/ed3c/soodles/pulls/2')
        self.assertEqual(next_action['known']['checkpoint'], str(self.checkpoint))
        self.assertEqual(next_action['required'], ['readback'])
        self.assertNotIn('argv', next_action)
        prepared = landing.advance(self.checkpoint, self.snapshot)
        self.assertEqual(prepared['next']['operation'], 'dispatch')
        request = landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(request['request']['expected_head_sha'], self.claim['head'])
        self.assertEqual(request['next']['kind'], 'executable')
        self.assertEqual(request['next']['operation'], 'execute')
        self.assertEqual(request['next']['argv'], landing.provider_cli_argv(self.checkpoint))
        self.assertNotIn('next', landing.read(self.checkpoint))
        with self.assertRaises(landing.LandingRefusal) as refused:
            landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(refused.exception.next_action['kind'], 'provider_readback')
        self.assertEqual(refused.exception.next_action['operation'], 'advance')

    def test_terminal_has_no_next_or_checkpoint_rewrite_and_reconciling_names_binary(self):
        self.start()
        self.offer()
        self.merged()
        self.offer()
        self.snapshot['issue'].update(state='closed', state_reason='completed', closed_at='now')
        result = landing.advance(self.checkpoint, self.snapshot)
        self.assertEqual(result['next']['required'], ['binary'])
        self.assertEqual(result['next']['operation'], 'reconcile')
        state = landing.read(self.checkpoint)
        state.update(phase='reconciling')
        landing.save(self.checkpoint, state)
        self.assertEqual(landing.advance(self.checkpoint, self.snapshot)['next']['operation'], 'reconcile')
        state.update(phase='resolved', classification='RESOLVED', local={'fixture': True})
        landing.save(self.checkpoint, state)
        before = self.checkpoint.read_bytes()
        result = landing.advance(self.checkpoint, self.snapshot)
        self.assertIsNone(result['next'])
        self.assertEqual(result['action'], 'stop')
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_parser_and_refusal_help_are_bound_to_invoked_action(self):
        result = soodles.run(['./soodles', 'landing', 'dispatch', '--guessed'], soodles.ROOT)
        self.assertEqual(result.returncode, 2)
        refusal = json.loads(result.stdout)
        self.assertEqual(refusal['owner'], 'landing.dispatch')
        self.assertEqual(refusal['invalid']['field'], 'arguments')
        argv = refusal['next']['help_argv']
        self.assertEqual(argv[-3:], ['landing', 'dispatch', '--help'])
        help_result = soodles.run(argv, soodles.ROOT)
        self.assertEqual(help_result.returncode, 0)
        self.assertFalse(self.checkpoint.exists())

    def test_cloud_marked_contract_requires_exact_candidate_gate_not_local_envelope(self):
        self.claim.pop("control_root")
        from test_issue_admission import issue_fixture
        from issue_admission import parse_contract
        ordinary, _ = issue_fixture()
        contract = parse_contract(ordinary["body"])
        contract.update(schema=3, base_head=self.claim["base_head"],
                        required_paths=["evidence.json"], evidence_manifest="evidence.json",
                        write_paths=["evidence.json"],
                        frozen_paths=[{"path": "evidence.json", "revision": "head", "sha256": "f" * 64}])
        self.snapshot["issue"]["body"] = ("<!-- soodles:execution-v1 -->\n```json\n"
                                           + json.dumps(contract)
                                           + "\n```\n<!-- /soodles:execution-v1 -->\n")
        with self.assertRaises(landing.LandingRefusal) as caught:
            self.start()
        self.assertEqual(caught.exception.invalid["field"], "job.candidate_evidence")
        self.assertFalse(self.checkpoint.exists())
        self.snapshot["jobs"]["jobs"][0]["steps"].insert(0, {
            "name": "Verify exact candidate evidence from fresh Issue readback",
            "status": "completed", "conclusion": "success",
        })
        result = self.start()
        self.assertEqual(result["owner"], "landing.start")
        self.assertEqual(landing.read(self.checkpoint)["scope"],
                         "supervised single-Issue cloud landing")
        self.assertNotIn("execution_envelope", landing.read(self.checkpoint)["claim"])


class IntegrationReconciliationTests(unittest.TestCase):
    """Real Git effects with fixture provider and original-order readbacks."""

    def setUp(self):
        self.fixture = LandingTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.primary, self.claim, _, self.base = self.fixture.cloud_control("integration-primary")
        self.primary = self.primary.resolve()
        self.directory = Path(self.fixture.temp.name).resolve()
        self.checkpoint = self.fixture.checkpoint
        (self.primary / ".git/info/exclude").write_text(".worktrees/\n.noodle/\n")
        self.root = self.directory / "detached-control"
        self.git(self.primary, "worktree", "add", "--detach", str(self.root), self.base)
        self.worktree = self.root / ".worktrees" / self.claim["worktree"]
        self.git(self.root, "worktree", "add", "-b", self.claim["worktree"], str(self.worktree), self.base)
        (self.worktree / "candidate").write_text("candidate change\n")
        self.git(self.worktree, "add", "candidate")
        self.commit(self.worktree, "candidate")
        self.candidate = self.git(self.worktree, "rev-parse", "HEAD")
        self.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "merge", "--no-ff", "-m", "confirmed provider merge", self.candidate)
        self.target = self.git(self.root, "rev-parse", "HEAD")
        self.git(self.root, "update-ref", "refs/remotes/origin/main", self.target)
        self.claim.update(control_root=str(self.root), head=self.candidate,
                          tree=self.git(self.worktree, "rev-parse", "HEAD^{tree}"),
                          execution_envelope={"path": str(self.directory / "envelope.json"), "sha256": "f" * 64})
        self.state = {"schema": 2, "claim": self.claim, "phase": "reconciling", "classification": None,
                      "writes_offered": ["merge", "close"], "merge_sha": self.target, "issue_closed_at": "now",
                      "observations": [{"provider": "retained"}], "prior_verifiers": ["e" * 64]}
        landing.save(self.checkpoint, self.state)
        self.binary = str(Path("/bin/true").resolve())
        self.envelope = {"execution": {"control_root": str(self.root), "order_id": "original-order",
                         "carrier": {"noodle": {"sha256": "f" * 64}}}}
        self.events = []
        self.base_ref = "main"
        self.runtime = self.root / ".noodle"
        self.runtime.mkdir()
        (self.runtime / "noodle.lock").touch()
        self.owner = {"state": {"orders": {}}, "effect_ledger": []}

    def git(self, root, *args):
        return soodles.checked(["git", *args], root)

    def commit(self, root, message):
        return self.git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--allow-empty", "-m", message)

    def complete(self, envelope, owner):
        self.events.append("completed-and-quiescent")
        return {"order_id": "original-order"}

    def checked(self, argv, cwd):
        if argv[0] == self.binary:
            self.events.append("cleanup")
            self.assertEqual(argv[1:], ["worktree", "cleanup", self.claim["worktree"]])
            self.assertEqual(self.git(self.primary, "branch", "--show-current"), self.base_ref)
            self.assertEqual(self.git(self.primary, "rev-parse", "HEAD"), self.target)
            self.git(self.root, "merge-base", "--is-ancestor", self.candidate, "refs/heads/" + self.base_ref)
            self.git(self.root, "worktree", "remove", str(self.worktree))
            self.git(self.root, "branch", "-d", self.claim["worktree"])
            return ""
        if argv[:3] == ["git", "merge", "--ff-only"]:
            self.events.append(("ff", str(cwd), argv[-1]))
            if Path(cwd) != self.root or self.root == self.primary:
                self.assertIn("completed-and-quiescent", self.events)
        return soodles.checked(argv, cwd)

    @contextlib.contextmanager
    def owners(self, *, checked=None, completion=None):
        with patch("landing.execution_binding", return_value=self.envelope), \
                patch("landing.fetch_main") as fetch, \
                patch("issue_execution.validate_carrier", return_value={"noodle": self.binary}), \
                patch("issue_execution.read_owner", side_effect=lambda binding: copy.deepcopy(self.owner)), \
                patch("issue_execution.completed_original_order", side_effect=completion or self.complete), \
                patch("landing.checked", side_effect=checked or self.checked):
            yield fetch

    def observe(self):
        return {"heads": {str(root): self.git(root, "rev-parse", "HEAD", "HEAD^{tree}")
                          for root in (self.primary, self.root, self.worktree)},
                "primary_branch": self.git(self.primary, "branch", "--show-current"),
                "refs": self.git(self.root, "show-ref"),
                "files": {str(path): path.read_bytes() for root in (self.primary, self.root, self.worktree)
                          for path in root.iterdir() if path.is_file() and path.name != ".git"}}

    def reconcile(self):
        return landing.reconcile(self.checkpoint, self.binary)

    def test_detached_target_advances_primary_before_real_cleanup_guard(self):
        self.assertEqual(self.git(self.primary, "rev-parse", "HEAD"), self.base)
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD"), self.target)
        self.assertEqual(len(self.git(self.root, "rev-list", "--parents", "-n", "1", self.target).split()), 3)
        before_branch = self.git(self.primary, "symbolic-ref", "HEAD")
        before_common = self.git(self.primary, "rev-parse", "--path-format=absolute", "--git-common-dir")
        with self.owners() as fetch:
            result = self.reconcile()
        fetch.assert_called_once_with(self.root)
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(self.git(self.primary, "symbolic-ref", "HEAD"), before_branch)
        self.assertEqual(self.git(self.primary, "rev-parse", "--path-format=absolute", "--git-common-dir"), before_common)
        self.assertEqual(self.git(self.root, "branch", "--show-current"), "")
        self.assertEqual([event for event in self.events if isinstance(event, tuple)],
                         [("ff", str(self.primary), self.target)])
        self.assertLess(self.events.index("completed-and-quiescent"), self.events.index("cleanup"))
        self.assertEqual(result["integration_sync"]["status"], "confirmed")
        self.assertEqual(result["observations"], self.state["observations"])
        self.assertEqual(result["prior_verifiers"], self.state["prior_verifiers"])
        self.assertEqual(result["writes_offered"], ["merge", "close"])
        self.assertFalse(self.worktree.exists())

    def test_already_target_is_noop_before_cleanup(self):
        self.git(self.primary, "merge", "--ff-only", self.target)
        with self.owners():
            self.assertEqual(self.reconcile()["classification"], "RESOLVED")
        self.assertFalse(any(isinstance(event, tuple) for event in self.events))
        self.assertEqual(self.events.count("cleanup"), 1)

    def test_control_itself_on_integration_branch_uses_one_fast_forward(self):
        old_worktree = self.worktree
        self.root = self.primary
        self.worktree = self.primary / ".worktrees" / self.claim["worktree"]
        self.worktree.parent.mkdir()
        self.git(self.primary, "worktree", "move", str(old_worktree), str(self.worktree))
        self.claim["control_root"] = str(self.primary)
        self.envelope["execution"]["control_root"] = str(self.primary)
        (self.primary / ".noodle").mkdir()
        (self.primary / ".noodle/noodle.lock").touch()
        landing.save(self.checkpoint, self.state)
        with self.owners():
            self.assertEqual(self.reconcile()["classification"], "RESOLVED")
        self.assertEqual([event for event in self.events if isinstance(event, tuple)],
                         [("ff", str(self.primary), self.target)])

    def test_generic_base_ref_uses_bound_fetch_and_cleanup_branch(self):
        self.base_ref = "trunk"
        self.git(self.primary, "branch", "-m", "main", "trunk")
        self.git(self.primary, "update-ref", "refs/remotes/origin/trunk", self.target)
        self.git(self.primary, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        binding = self.directory / "binding.json"
        landing.save(binding, {"schema": 1, "repository": self.claim["repository"], "base_ref": "trunk",
                     "workflow_path": ".github/workflows/runtime.yml", "jobs": {"runtime": ["accept"]},
                     "verification": {}})
        self.claim["target_binding"] = {"path": str(binding), "sha256": hashlib.sha256(binding.read_bytes()).hexdigest()}
        landing.save(self.checkpoint, self.state)
        with self.owners() as fetch:
            result = self.reconcile()
        fetch.assert_called_once_with(self.root, "trunk")
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(result["integration_sync"]["integration_ref"], "refs/heads/trunk")

    def parked_fixture(self):
        from test_issue_admission import issue_fixture
        from issue_admission import parse_contract
        from issue_execution import projection
        issue, envelope = issue_fixture()
        envelope["execution"].update(self.envelope["execution"])
        envelope["execution"].update(worktree=self.claim["worktree"], stage_index=0)
        envelope["execution"]["carrier"]["codex"] = {"model": "fixture-model"}
        self.envelope = envelope
        body = issue["body"]
        binding = {**envelope, "issue_body": body, "contract": parse_contract(body)}
        prompt = json.dumps(projection(binding, self.claim["execution_envelope"]["sha256"], "supervised"))
        self.session = "original-terminal-session"
        self.stage = {"status": "review", "stage_index": 0, "skill": "execute", "provider": "codex",
                      "model": "fixture-model", "runtime": "process", "prompt": prompt,
                      "attempts": [{"status": "completed", "session_id": self.session,
                                    "attempt_id": "original-attempt", "worktree_name": self.claim["worktree"]}]}
        review = {"order_id": "original-order", "stage_index": 0, "session_id": self.session,
                  "worktree_name": self.claim["worktree"], "worktree_path": str(self.worktree),
                  **{key: self.stage[key] for key in ("skill", "provider", "model", "runtime", "prompt")}}
        self.owner = {"state": {"orders": {"original-order": {"status": "active", "stages": [self.stage]}},
                                "pending_reviews": {"original-order": review}},
                      "effect_ledger": [{"effect": {"type": "dispatch", "payload": {
                          "order_id": "original-order", "stage_index": 0, "attempt_id": "original-attempt"}}}]}
        self.session_root = self.runtime / "sessions" / self.session
        self.session_root.mkdir(parents=True)
        stopped = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
        stopped.wait()
        landing.save(self.session_root / "process.json", {"session_id": self.session, "pid": stopped.pid})
        landing.save(self.session_root / "spawn.json", {"session_id": self.session,
                     "worktree_path": str(self.worktree), "skill": "execute", "provider": "codex",
                     "runtime": "process", "model": "fixture-model"})
        event = {"type": "stage_message", "session_id": self.session,
                 "payload": {"order_id": "original-order", "stage_index": 0,
                             "outcome": "completed", "blocking": False}}
        (self.session_root / "events.ndjson").write_text(json.dumps(event) + "\n")
        self.git(self.root, "checkout", "--detach", self.base)
        self.state["phase"] = "awaiting_reconcile"
        landing.save(self.checkpoint, self.state)

    def test_parked_review_advances_control_before_native_completion_and_integration(self):
        self.parked_fixture()
        with self.owners():
            result = self.reconcile()
            self.assertEqual(result["action"], "noodle_reconcile")
            self.assertEqual(result["next"]["known"]["session_id"], self.session)
            self.assertEqual(self.git(self.root, "rev-parse", "HEAD"), self.target)
            self.assertEqual(self.git(self.primary, "rev-parse", "HEAD"), self.base)
            self.assertNotIn("cleanup", self.events)
            self.assertNotIn("integration_sync", landing.read(self.checkpoint))
            self.owner["state"]["orders"]["original-order"]["status"] = "completed"
            result = self.reconcile()
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual([event for event in self.events if isinstance(event, tuple)],
                         [("ff", str(self.root), self.target), ("ff", str(self.primary), self.target)])
        self.assertEqual(result["control_sync"]["status"], "confirmed")

    def test_native_wait_preserves_fixed_control_target_and_newer_integration(self):
        self.parked_fixture()
        merge = self.target
        with self.owners():
            self.assertEqual(self.reconcile()["action"], "noodle_reconcile")
            self.git(self.primary, "merge", "--ff-only", merge)
            self.commit(self.primary, "later main change")
            self.target = self.git(self.primary, "rev-parse", "HEAD")
            self.git(self.primary, "update-ref", "refs/remotes/origin/main", self.target)
            self.owner["state"]["orders"]["original-order"]["status"] = "completed"
            result = self.reconcile()
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD"), merge)
        self.assertEqual(self.git(self.primary, "rev-parse", "HEAD"), self.target)
        self.assertEqual(result["control_sync"]["target_head"], merge)
        self.assertEqual(result["integration_sync"]["target_head"], self.target)
        self.assertEqual([event for event in self.events if isinstance(event, tuple)],
                         [("ff", str(self.root), merge)])

    def test_active_foreign_and_missing_parked_custody_refuse_before_git_effect(self):
        self.parked_fixture()
        original = copy.deepcopy(self.owner)
        for condition in ("active", "foreign_review", "foreign_prompt", "missing_order", "missing_attempt", "foreign_dispatch", "foreign_order", "stage_index", "runtime"):
            with self.subTest(condition=condition):
                self.owner = copy.deepcopy(original)
                order = self.owner["state"]["orders"]["original-order"]
                if condition == "active":
                    order["stages"][0]["attempts"][0]["status"] = "running"
                elif condition == "foreign_review":
                    self.owner["state"]["pending_reviews"]["original-order"]["session_id"] = "foreign"
                elif condition == "foreign_prompt":
                    order["stages"][0]["prompt"] = "{}"
                elif condition == "missing_order":
                    del self.owner["state"]["orders"]["original-order"]
                elif condition == "foreign_dispatch":
                    self.owner["effect_ledger"][0]["effect"]["payload"]["attempt_id"] = "foreign-attempt"
                elif condition == "foreign_order":
                    self.owner["state"]["orders"]["foreign"] = {"status": "active", "stages": []}
                elif condition == "stage_index":
                    order["stages"][0]["stage_index"] = 1
                elif condition == "runtime":
                    order["stages"][0]["runtime"] = "foreign"
                else:
                    order["stages"][0]["attempts"] = []
                before = self.observe()
                with self.owners(completion=landing.LandingRefusal("completion.dispatch", "missing")) as fetch:
                    with self.assertRaises(landing.LandingRefusal):
                        self.reconcile()
                fetch.assert_not_called()
                self.assertEqual(self.observe(), before)
                self.assertEqual(self.events, [])
                self.assertNotIn("control_sync", landing.read(self.checkpoint))

    def test_control_unknown_intent_is_readback_only_and_lost_success_is_adopted(self):
        self.parked_fixture()
        def unknown(argv, cwd):
            if argv[:3] == ["git", "merge", "--ff-only"]:
                self.assertEqual(landing.read(self.checkpoint)["control_sync"]["status"], "intent")
                raise RuntimeError("unknown control dispatch")
            return self.checked(argv, cwd)
        with self.owners(checked=unknown), self.assertRaisesRegex(RuntimeError, "unknown control"):
            self.reconcile()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "control_sync.outcome"):
            self.reconcile()
        self.assertEqual(self.events, [])
        self.git(self.root, "merge", "--ff-only", self.target)
        with self.owners():
            result = self.reconcile()
        self.assertEqual(result["action"], "noodle_reconcile")
        self.assertEqual(landing.read(self.checkpoint)["control_sync"]["status"], "confirmed")
        self.assertEqual(self.events, [])

    def test_parked_process_and_native_lock_refuse_without_effect(self):
        import fcntl
        self.parked_fixture()
        process = subprocess.Popen(["/bin/sh", "-c", "sleep 30"], start_new_session=True)
        try:
            landing.save(self.session_root / "process.json", {"session_id": self.session, "pid": process.pid})
            before = self.observe()
            with self.owners() as fetch, self.assertRaisesRegex(landing.LandingRefusal, "takeover.process_alive"):
                self.reconcile()
            fetch.assert_not_called()
            self.assertEqual(self.observe(), before)
        finally:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            process.wait()
        with (self.runtime / "noodle.lock").open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.owners() as fetch, self.assertRaisesRegex(landing.LandingRefusal, "reconcile.live_owner"):
                self.reconcile()
            fetch.assert_not_called()
        (self.runtime / "noodle.lock").unlink()
        with self.owners() as fetch, self.assertRaisesRegex(landing.LandingRefusal, "reconcile.noodle_lock"):
            self.reconcile()
        fetch.assert_not_called()
        self.assertEqual(self.events, [])

    def test_parked_control_busy_does_not_offer_an_intent(self):
        self.parked_fixture()
        lock = Path(self.git(self.root, "rev-parse", "--path-format=absolute", "--git-path", "index.lock"))
        lock.touch()
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "control_sync.busy"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertNotIn("control_sync", landing.read(self.checkpoint))
        self.assertEqual(self.events, [])
        lock.unlink()
        with self.owners():
            self.assertEqual(self.reconcile()["action"], "noodle_reconcile")
        lock.touch()
        prior = landing.read(self.checkpoint)["control_sync"]
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "control_sync.busy"):
            self.reconcile()
        self.assertEqual(landing.read(self.checkpoint)["control_sync"], prior)

    def test_control_lost_success_acknowledgement_is_adopted_without_replay(self):
        self.parked_fixture()
        def lost(argv, cwd):
            result = self.checked(argv, cwd)
            if argv[:3] == ["git", "merge", "--ff-only"]:
                raise RuntimeError("lost control acknowledgement")
            return result
        with self.owners(checked=lost), self.assertRaisesRegex(RuntimeError, "lost control"):
            self.reconcile()
        with self.owners():
            self.assertEqual(self.reconcile()["action"], "noodle_reconcile")
        self.assertEqual(self.events, [("ff", str(self.root), self.target)])
        self.assertEqual(landing.read(self.checkpoint)["control_sync"]["status"], "confirmed")

    def test_dirty_primary_preserves_tracked_and_untracked_bytes(self):
        for name in ("file", "untracked"):
            with self.subTest(name=name):
                target = self.primary / name
                original = target.read_bytes() if target.exists() else None
                target.write_bytes(b"user bytes must survive\n")
                before = self.observe()
                with self.owners(), self.assertRaises(soodles.Refusal):
                    self.reconcile()
                self.assertEqual(self.observe(), before)
                self.assertNotIn("cleanup", self.events)
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)

    def test_foreign_origin_refuses_without_effect(self):
        self.git(self.primary, "remote", "set-url", "origin", "https://github.com/foreign/repository.git")
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "origin"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(self.events, [])

    def test_diverged_primary_and_missing_confirmed_merge_refuse_without_effect(self):
        self.commit(self.primary, "independent primary change")
        before = self.observe()
        with self.owners(), self.assertRaises(landing.LandingRefusal) as diverged:
            self.reconcile()
        self.assertEqual(diverged.exception.invalid["field"], "integration_sync.ancestry")
        self.assertEqual(self.observe(), before)
        self.assertNotIn("cleanup", self.events)
        self.state["merge_sha"] = self.git(self.primary, "rev-parse", "HEAD")
        landing.save(self.checkpoint, self.state)
        with self.owners(), self.assertRaises(landing.LandingRefusal) as missing_merge:
            self.reconcile()
        self.assertEqual(missing_merge.exception.invalid["field"], "reconcile.merge_ancestry")
        self.assertEqual(self.observe(), before)
        self.assertNotIn("cleanup", self.events)
        self.assertFalse(any(isinstance(event, tuple) for event in self.events))

    def test_unknown_intent_at_before_head_never_reissues_fast_forward(self):
        def interrupted(argv, cwd):
            if argv[:3] == ["git", "merge", "--ff-only"] and Path(cwd) == self.primary:
                intent = landing.read(self.checkpoint)["integration_sync"]
                self.assertEqual(intent["status"], "intent")
                self.assertEqual(intent["before_head"], self.base)
                self.assertEqual(intent["target_head"], self.target)
                self.assertNotIn("process_result", intent)
                raise RuntimeError("lost dispatch acknowledgement")
            return self.checked(argv, cwd)
        with self.owners(checked=interrupted), self.assertRaisesRegex(RuntimeError, "lost dispatch"):
            self.reconcile()
        before = self.observe()
        saved = landing.read(self.checkpoint)["integration_sync"]
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "integration_sync.outcome") as caught:
            self.reconcile()
        self.assertEqual(caught.exception.next_action["required"], ["material_integration_sync_readback_without_retry"])
        self.assertEqual(self.observe(), before)
        self.assertEqual(landing.read(self.checkpoint)["integration_sync"], saved)
        self.assertNotIn("cleanup", self.events)
        self.assertFalse(any(isinstance(event, tuple) for event in self.events))

    def test_lost_success_acknowledgement_confirms_readback_without_repeating_effect(self):
        def lost_ack(argv, cwd):
            output = self.checked(argv, cwd)
            if argv[:3] == ["git", "merge", "--ff-only"] and Path(cwd) == self.primary:
                raise RuntimeError("success acknowledgement lost")
            return output
        with self.owners(checked=lost_ack), self.assertRaisesRegex(RuntimeError, "acknowledgement lost"):
            self.reconcile()
        self.assertEqual(landing.read(self.checkpoint)["integration_sync"]["status"], "intent")
        with self.owners():
            result = self.reconcile()
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertEqual(result["integration_sync"]["status"], "confirmed")
        self.assertEqual(result["integration_sync"]["confirmation"], "observed")
        self.assertEqual(len([event for event in self.events if isinstance(event, tuple)]), 1)
        self.assertEqual(result["observations"], self.state["observations"])

    def test_missing_ambiguous_locked_or_wrong_branch_registry_refuses_without_effect(self):
        actual = self.git(self.root, "worktree", "list", "--porcelain", "-z")
        blocks = actual.split("\0\0")
        selected = next(block for block in blocks if "branch refs/heads/main" in block)
        cases = {
            "missing": actual.replace(selected + "\0\0", ""),
            "ambiguous": actual + "\0\0" + selected,
            "locked": actual.replace(selected, selected + "\0locked fixture"),
            "wrong_branch": actual.replace("worktree " + str(self.primary), "worktree " + str(self.worktree))
                .replace("worktree " + str(self.worktree) + "\0HEAD " + self.candidate,
                         "worktree " + str(self.directory / "unused") + "\0HEAD " + self.candidate),
        }
        expected = {"missing": "integration_sync.registration", "ambiguous": "integration_sync.registration",
                    "locked": "integration_sync.registration_locked", "wrong_branch": "integration_sync.branch"}
        for name, registry in cases.items():
            with self.subTest(name=name):
                def planted(argv, cwd):
                    if argv == ["git", "worktree", "list", "--porcelain", "-z"]:
                        return registry
                    return self.checked(argv, cwd)
                before = self.observe()
                with self.owners(checked=planted), self.assertRaisesRegex(landing.LandingRefusal, expected[name]):
                    self.reconcile()
                self.assertEqual(self.observe(), before)
                self.assertNotIn("cleanup", self.events)
                self.assertFalse(any(isinstance(event, tuple) for event in self.events))

    def test_foreign_common_directory_registry_refuses_without_effect(self):
        foreign, _, _, foreign_head = self.fixture.cloud_control("foreign-common-dir")
        foreign = foreign.resolve()
        def planted(argv, cwd):
            if argv == ["git", "worktree", "list", "--porcelain", "-z"]:
                return "worktree " + str(foreign) + "\0HEAD " + foreign_head + "\0branch refs/heads/main\0\0"
            return self.checked(argv, cwd)
        before = self.observe()
        foreign_before = soodles.source_identity(foreign)
        with self.owners(checked=planted), self.assertRaisesRegex(landing.LandingRefusal, "integration_sync.common_dir"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(soodles.source_identity(foreign), foreign_before)
        self.assertNotIn("cleanup", self.events)

    def test_saved_intent_rejects_changed_checkout_and_preserves_history(self):
        def stop(argv, cwd):
            if argv[:3] == ["git", "merge", "--ff-only"]:
                raise RuntimeError("intent saved")
            return self.checked(argv, cwd)
        with self.owners(checked=stop), self.assertRaisesRegex(RuntimeError, "intent saved"):
            self.reconcile()
        saved = landing.read(self.checkpoint)
        (self.primary / "untracked").write_text("new owner bytes\n")
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "integration_sync.residue"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(landing.read(self.checkpoint)["integration_sync"], saved["integration_sync"])
        (self.primary / "untracked").unlink()
        changed = copy.deepcopy(saved)
        changed["integration_sync"]["checkout"] = str(self.directory / "different-checkout")
        landing.save(self.checkpoint, changed)
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "integration_sync.intent"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(landing.read(self.checkpoint)["integration_sync"], changed["integration_sync"])
        self.assertNotIn("cleanup", self.events)

    def test_missing_provider_confirmation_refuses_before_local_effect(self):
        for field in ("issue_closed_at", "writes_offered"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.state)
                changed.pop(field)
                landing.save(self.checkpoint, changed)
                before = self.observe()
                with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "reconcile.provider_confirmation"):
                    self.reconcile()
                self.assertEqual(self.observe(), before)
                self.assertNotIn("cleanup", self.events)
                self.assertFalse(any(isinstance(event, tuple) for event in self.events))

    def test_immutable_binding_bytes_drift_refuses_saved_intent_without_effect(self):
        binding = self.directory / "binding.json"
        landing.save(binding, {"schema": 1, "repository": self.claim["repository"], "base_ref": "main",
                     "workflow_path": ".github/workflows/runtime.yml", "jobs": {"runtime": ["accept"]},
                     "verification": {}})
        self.claim["target_binding"] = {"path": str(binding), "sha256": hashlib.sha256(binding.read_bytes()).hexdigest()}
        landing.save(self.checkpoint, self.state)
        def stop(argv, cwd):
            if argv[:3] == ["git", "merge", "--ff-only"]:
                raise RuntimeError("intent saved")
            return self.checked(argv, cwd)
        with self.owners(checked=stop), self.assertRaisesRegex(RuntimeError, "intent saved"):
            self.reconcile()
        checkpoint_bytes = self.checkpoint.read_bytes()
        binding.write_text("{}\n")
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "binding.sha256"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(self.checkpoint.read_bytes(), checkpoint_bytes)
        self.assertEqual(binding.read_text(), "{}\n")
        self.assertNotIn("cleanup", self.events)

    def test_saved_intent_rejects_fetched_target_or_identity_drift(self):
        def stop(argv, cwd):
            if argv[:3] == ["git", "merge", "--ff-only"]:
                raise RuntimeError("intent saved")
            return self.checked(argv, cwd)
        with self.owners(checked=stop), self.assertRaisesRegex(RuntimeError, "intent saved"):
            self.reconcile()
        saved = landing.read(self.checkpoint)
        self.commit(self.root, "later remote target")
        later = self.git(self.root, "rev-parse", "HEAD")
        self.git(self.root, "update-ref", "refs/remotes/origin/main", later)
        before = self.observe()
        with self.owners(), self.assertRaisesRegex(landing.LandingRefusal, "control_sync.outcome"):
            self.reconcile()
        self.assertEqual(self.observe(), before)
        self.assertEqual(landing.read(self.checkpoint)["integration_sync"], saved["integration_sync"])
        self.assertNotIn("cleanup", self.events)


class BoundLandingTests(unittest.TestCase):
    """Real Git paths and owner functions; provider responses are fixtures."""
    def setUp(self):
        from test_issue_execution import IssueExecutionTests
        self.consumer = IssueExecutionTests()
        self.consumer.setUp()
        self.addCleanup(self.consumer.doCleanups)
        c = self.consumer
        (c.runtime / "noodle.lock").touch()
        self.delivery = LandingTests()
        self.delivery.setUp()
        self.addCleanup(self.delivery.doCleanups)
        d = self.delivery
        d.claim.update(issue=18, head=c.git("rev-parse", "HEAD"), tree=c.git("rev-parse", "HEAD^{tree}"),
                       base_head=c.envelope["base_head"], control_root=str(c.root),
                       worktree=c.envelope["execution"]["worktree"],
                       execution_envelope={"path": str(c.path), "sha256": c.pin})
        d.snapshot["issue"] = copy.deepcopy(c.issue)
        d.snapshot["pr"]["body"] = "Refs ed3c/soodles#18"
        d.snapshot["pr"]["head"].update(sha=d.claim["head"], ref=d.claim["worktree"])
        d.snapshot["pr"]["base"]["sha"] = d.claim["base_head"]
        d.snapshot["commit"] = {"sha": d.claim["head"], "tree": {"sha": d.claim["tree"]}}
        d.snapshot["branch"]["commit"]["sha"] = d.claim["base_head"]
        d.snapshot["run"]["head_sha"] = d.claim["head"]
        d.snapshot["jobs"]["jobs"][0]["head_sha"] = d.claim["head"]

    def test_missing_binding_refuses_marked_contract_before_checkpoint(self):
        d = self.delivery
        del d.claim["execution_envelope"]
        with self.assertRaises(landing.LandingRefusal) as caught:
            d.start()
        self.assertEqual(caught.exception.invalid["field"], "claim.execution_envelope")
        self.assertFalse(d.checkpoint.exists())

    def test_body_amendment_refuses_prepared_dispatch_without_offer(self):
        d = self.delivery
        d.start()
        landing.advance(d.checkpoint, d.snapshot)
        before = d.checkpoint.read_bytes()
        d.snapshot["issue"]["body"] += "\nAmended requirement."
        with self.assertRaises(landing.LandingRefusal) as caught:
            landing.dispatch(d.checkpoint, d.snapshot)
        self.assertEqual(caught.exception.invalid["field"], "issue.body_sha256")
        self.assertEqual(caught.exception.next_action["owner"], "supervisor")
        self.assertEqual(caught.exception.next_action["required"], ["fresh_execution_envelope"])
        self.assertEqual(caught.exception.next_action["operation"], "dispatch")
        self.assertEqual(caught.exception.next_action["known"]["checkpoint"], str(d.checkpoint.resolve()))
        self.assertEqual(caught.exception.next_action["help_argv"][-2:], ["dispatch", "--help"])
        self.assertEqual(d.checkpoint.read_bytes(), before)

    def test_outside_delivery_paths_refuse_and_current_paths_pass(self):
        import subprocess
        c, d = self.consumer, self.delivery
        for name in ("unauthorized.py", "allowed.py"):
            path = c.worktree / name
            path.write_text("new candidate\n")
            subprocess.run(["git", "add", name], cwd=c.worktree, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@example.invalid",
                            "commit", "-m", "bounded fixture"], cwd=c.worktree, check=True, capture_output=True)
            claim = {**d.claim, "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=c.worktree, text=True).strip()}
            if name == "unauthorized.py":
                with self.assertRaises(landing.LandingRefusal) as caught:
                    landing.execution_binding(claim, d.snapshot["issue"])
                self.assertEqual(caught.exception.invalid, {"field": "candidate.outside_write_paths", "value": [name]})
                subprocess.run(["git", "reset", "--hard", d.claim["base_head"]], cwd=c.worktree, check=True, capture_output=True)
            else:
                self.assertEqual(landing.execution_binding(claim, d.snapshot["issue"])["issue"], 18)

    def test_closure_metadata_is_legal_but_body_change_still_refuses(self):
        c, d = self.consumer, self.delivery
        closed = {**c.issue, "state": "closed", "state_reason": "completed", "closed_at": "now", "updated_at": "later"}
        self.assertEqual(landing.execution_binding(d.claim, closed)["body_sha256"], c.envelope["body_sha256"])
        with self.assertRaisesRegex(landing.LandingRefusal, "issue.body_sha256"):
            landing.execution_binding(d.claim, {**closed, "body": closed["body"] + " changed"})
        # The same provider closure is not new worker authorization.
        import issue_admission
        with self.assertRaisesRegex(issue_admission.AdmissionRefusal, "issue.state"):
            issue_admission.validate_issue(closed, c.envelope)

    def test_provider_closure_cannot_resolve_before_original_noodle_order(self):
        c, d = self.consumer, self.delivery
        d.start()
        state = landing.read(d.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha=d.claim["head"], issue_closed_at="now",
                     writes_offered=["merge", "close"])
        landing.save(d.checkpoint, state)
        c.git("update-ref", "refs/remotes/origin/main", d.claim["head"])
        with patch("landing.fetch_main") as fetch:
            with self.assertRaises(landing.LandingRefusal) as incomplete:
                landing.reconcile(d.checkpoint, str(c.binary))
        fetch.assert_not_called()
        self.assertEqual(incomplete.exception.next_action["owner"], "Noodle")
        self.assertEqual(incomplete.exception.next_action["known"]["order_id"], "soodles-18")
        self.assertIsNone(landing.read(d.checkpoint)["classification"])
        self.assertTrue(c.worktree.exists())
        self.assertFalse(c.effect.exists())
        # Unavailable canonical readback is a different branch from an observed
        # incomplete order. It must retain the same continuation identity too.
        from issue_admission import AdmissionRefusal
        missing = AdmissionRefusal("noodle.snapshot", "unavailable", "Noodle", "canonical_checkpoint_readback")
        with patch("landing.fetch_main"), patch("issue_execution.read_owner", side_effect=missing):
            with self.assertRaises(landing.LandingRefusal) as caught:
                landing.reconcile(d.checkpoint, str(c.binary))
        next_action = caught.exception.next_action
        self.assertEqual(next_action["operation"], "reconcile")
        self.assertEqual(caught.exception.invalid, missing.invalid)
        self.assertEqual(next_action["required"], ["canonical_checkpoint_readback"])
        self.assertEqual(next_action["known"]["checkpoint"], str(d.checkpoint.resolve()))
        self.assertEqual(next_action["known"]["order_id"], "soodles-18")
        self.assertEqual(next_action["owner"], "Noodle")
        self.assertIsNone(landing.read(d.checkpoint)["classification"])
        self.assertTrue(c.worktree.exists())

    def test_completed_bound_order_can_reconcile_and_clean_fixture_worktree(self):
        import subprocess
        c, d = self.consumer, self.delivery
        c.admit("automatic")
        c.promote_fixture()
        order = c.snapshot["state"]["orders"]["soodles-18"]
        order["status"] = "completed"
        order["stages"][0]["status"] = "completed"
        ended = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
        ended.wait()
        order["stages"][0]["attempts"][0].update(status="completed", session_id=c.session)
        (c.runtime / "sessions" / c.session / "process.json").write_text(json.dumps({"pid": ended.pid, "session_id": c.session}))
        c.save_owner()
        d.start()
        state = landing.read(d.checkpoint)
        state.update(phase="awaiting_reconcile", merge_sha=d.claim["head"], issue_closed_at="now", writes_offered=["merge", "close"])
        landing.save(d.checkpoint, state)
        c.git("update-ref", "refs/remotes/origin/main", d.claim["head"])
        original = landing.checked
        requests = []
        def cleanup_fixture(argv, cwd):
            if argv[0] == str(c.binary):
                self.assertEqual(argv[1:], ["worktree", "cleanup", d.claim["worktree"]])
                requests.append(argv)
                c.git("worktree", "remove", str(c.worktree))
                c.git("branch", "-d", d.claim["worktree"])
                return ""
            return original(argv, cwd)
        with patch("landing.fetch_main"), patch("landing.checked", side_effect=cleanup_fixture):
            result = landing.reconcile(d.checkpoint, str(c.binary))
        self.assertEqual(result["classification"], "RESOLVED")
        self.assertIsNone(result["next"])
        self.assertEqual(len(requests), 1)
        self.assertFalse(c.worktree.exists())
        self.assertEqual(result["noodle_reconciliation"]["order_id"], "soodles-18")
