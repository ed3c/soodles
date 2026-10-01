"""Real publication, durable atom checkpoint and interrupted process controls."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from contextlib import ExitStack
import unittest
from unittest.mock import patch

import atom_repair as repair
import candidate_publication as publication
import issue_atom as atom
import provider_readback
import test_candidate_publication as publication_tests
import test_issue_atom as atom_tests


ROOT = Path(atom.__file__).parent


def record(name, value):
    print("REPAIR_EVIDENCE " + json.dumps({"name": name, "value": value}, sort_keys=True))
    target = os.environ.get("SOODLES_REPAIR_EVIDENCE")
    if target:
        path = Path(target)
        path.mkdir(parents=True, exist_ok=True)
        (path / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")


class RepairTests(unittest.TestCase):
    def setUp(self):
        fixture = publication_tests.CandidatePublicationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.policy = repair.load((ROOT / repair.POLICY_PATH).read_bytes())
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.checkpoint = Path(self.directory.name).resolve() / "atom.state.json"
        self.state = {"repair": repair.new_history("a" * 64, "fixed", self.policy)}
        self.save()

    def save(self):
        atom.save_json(self.checkpoint, self.state)

    def controller(self, **kwargs):
        return repair.Controller(self.state, self.policy, "fixed", self.save, **kwargs)

    def test_stale_pr_refresh_is_read_only_and_rebuild_uses_unchanged_source(self):
        f = self.fixture
        prior, acceptance, claim = f.amended_candidate()
        pushes, reads = [], []
        fresh = publication_tests.exact_pull(prior["pr"]["number"], prior["branch"],
                                             claim["head"], "main", "Refs " + claim["subject"])
        def push(*args, **kwargs):
            pushes.append(args)
            f.provider.ref = claim["head"]  # PR readback intentionally still old
            return publication_tests.Result()
        def read(number, timeout):
            reads.append({"number": number, "timeout": timeout})
            # A raw subprocess result, not a boolean proving refresh success.
            result = subprocess.run([sys.executable, "-c", "import sys; print(sys.stdin.read())"],
                                    input=json.dumps(fresh), capture_output=True, text=True, timeout=timeout)
            self.assertEqual(result.returncode, 0, result.stderr)
            record("refresh-process", {"argv": result.args, "exit_status": result.returncode,
                                        "stdout": result.stdout, "stderr": result.stderr})
            return json.loads(result.stdout)
        f.provider.repair_pull = read
        self.state["writes"] = {}
        with patch.object(atom, "authenticated_push", return_value=push):
            result = atom.publish_candidate(
                {"prior_publication": prior}, self.state, {"state": self.checkpoint},
                claim, acceptance, f.provider, self.controller())
        self.assertEqual(len(pushes), 1)
        self.assertEqual(len(reads), 1)
        self.assertLessEqual(reads[0]["timeout"], 60)
        self.assertEqual(result["head"], claim["head"])
        self.assertFalse(result["authorizes_landing"])
        self.state["publication_source"] = {"value": result, "sha256": repair.digest(result),
                                             "claim_sha256": repair.digest(claim)}
        self.assertEqual(atom.restore_publication(self.state, claim, self.controller()), result)
        self.assertEqual(self.state["repair"]["used"]["actions"], 2)
        before = self.checkpoint.read_bytes()
        self.assertEqual(atom.restore_publication(self.state, claim, self.controller()), result)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        self.assertEqual(f.provider.create_calls, 1)  # initial fixture PR only
        record("refresh-and-rebuild", {"checkpoint": json.loads(self.checkpoint.read_text()),
                                        "publication": result, "pushes": len(pushes), "reads": reads})

    def test_unknown_write_and_legal_noncase_never_spend_refresh(self):
        f = self.fixture
        prior, acceptance, claim = f.amended_candidate()
        refresh = lambda *_: self.fail("unknown branch must not refresh or duplicate effects")
        for _ in range(2):
            with self.assertRaisesRegex(publication.PublicationRefusal, "github.branch.outcome"):
                publication.publish_amendment(f.root, acceptance, claim, f.provider, prior,
                                               offered=True, refresh=refresh)
        f.provider.ref = claim["head"]
        f.provider.pull_value = publication_tests.exact_pull(prior["pr"]["number"], prior["branch"],
                                                             claim["head"], "main", "Refs " + claim["subject"])
        value = publication.publish_amendment(f.root, acceptance, claim, f.provider, prior,
                                              offered=True, refresh=refresh)
        self.assertEqual(value["status"], "amended")
        self.assertEqual(self.state["repair"]["used"]["actions"], 0)
        self.assertEqual(f.provider.create_calls, 1)

    def test_atom_initial_publication_intent_blocks_unknown_create_on_restart(self):
        f = self.fixture
        f.provider.token = "fixture-token"
        self.state["writes"] = {}
        f.provider.unknown_create = True
        f.provider.drop_create = True
        with patch.object(atom, "authenticated_push", return_value=f.push()):
            with self.assertRaisesRegex(publication.PublicationRefusal, "github.pull.outcome"):
                atom.publish_candidate({}, self.state, {"state": self.checkpoint},
                                       f.claim, f.acceptance, f.provider)
        self.state = atom.read_json(self.checkpoint, "state")
        with self.assertRaisesRegex(atom.AtomRefusal, "publication.effect"):
            atom.publish_candidate({}, self.state, {"state": self.checkpoint},
                                   f.claim, f.acceptance, f.provider)
        self.assertEqual(f.provider.create_calls, 1)
        self.assertEqual(self.state["repair"]["used"]["actions"], 0)
        # A material exact readback resumes normally, without repeating create.
        f.provider.pull_value = publication_tests.exact_pull(
            41, "soodles/issue-128-" + f.head[:12], f.head, "main", "Refs " + f.claim["subject"])
        result = atom.publish_candidate({}, self.state, {"state": self.checkpoint},
                                        f.claim, f.acceptance, f.provider)
        self.assertEqual(result["status"], "reused")
        self.assertEqual(f.provider.create_calls, 1)
        record("unknown-create", {"checkpoint": json.loads(self.checkpoint.read_text()),
                                   "create_calls": f.provider.create_calls,
                                   "material_readback_result": result})

    def test_interrupted_intent_survives_real_process_and_changed_head(self):
        script = """import json,os,sys
from pathlib import Path
import atom_repair as r, issue_atom as a
p=Path(sys.argv[1]); state=json.loads(p.read_text())
policy=r.load(Path(r.POLICY_PATH).read_bytes())
c=r.Controller(state,policy,'fixed',lambda:a.save_json(p,state))
c.perform('stale_pr',lambda remaining:os._exit(17),lambda value:True)
"""
        process = subprocess.run([sys.executable, "-B", "-c", script, str(self.checkpoint)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 17)
        self.assertEqual(process.stdout + process.stderr, "")
        self.state = atom.read_json(self.checkpoint, "state")
        self.state["head"] = "b" * 40
        before = self.checkpoint.read_bytes()
        with self.assertRaisesRegex(repair.RepairRefusal, "repeated_failure"):
            self.controller().perform("stale_pr", lambda _: self.fail("reoffered"), lambda _: True)
        self.assertEqual(self.checkpoint.read_bytes(), before)
        self.assertEqual(self.state["repair"]["used"]["readback"], 1)
        self.assertEqual(self.state["repair"]["history"][0]["status"], "intent")
        record("interrupted-process", {"argv": process.args, "exit_status": process.returncode,
                                        "stdout": process.stdout, "stderr": process.stderr,
                                        "checkpoint": json.loads(self.checkpoint.read_text())})

    def test_failed_confirmation_tamper_and_missing_capability_stop(self):
        guard = {"verifier": "external", "evidence": "required"}
        controller = self.controller(invariants=lambda: dict(guard))
        def tamper(_):
            guard.pop("evidence")
            return {"schema": "valid"}
        with self.assertRaisesRegex(repair.RepairRefusal, "invariants"):
            controller.perform("stale_pr", tamper, lambda _: True)
        self.assertEqual(self.state["repair"]["history"][0]["status"], "failed")
        self.state = atom.read_json(self.checkpoint, "state")
        with self.assertRaisesRegex(repair.RepairRefusal, "repeated_failure"):
            self.controller().perform("stale_pr", lambda _: self.fail("reoffered"), lambda _: True)
        with patch.object(subprocess, "Popen", side_effect=AssertionError("model spawned")):
            result = self.controller().report("failed_process")
        self.assertEqual(result["stop"], "bounded_patch_capability_required")
        self.assertEqual(result["model_invocations"], 0)
        record("capability-and-tamper", {"capability": result,
                                        "checkpoint": json.loads(self.checkpoint.read_text())})
        self.state["repair"]["limits"]["model"] = 5
        with self.assertRaisesRegex(repair.RepairRefusal, "invariants"):
            self.controller().perform("missing_projection", lambda _: {}, lambda _: True)

    def test_original_predicate_and_clock_are_not_schema_success(self):
        with self.assertRaisesRegex(repair.RepairRefusal, "original_predicate"):
            self.controller().perform("stale_pr", lambda _: {"valid": "JSON"}, lambda _: False)
        self.assertEqual(self.state["repair"]["history"][0]["status"], "failed")
        with self.assertRaisesRegex(repair.RepairRefusal, "clock"):
            self.controller(clock=lambda: 0).perform("missing_projection", lambda _: {}, lambda _: True)
        with self.assertRaisesRegex(repair.RepairRefusal, "deadline"):
            self.controller(clock=lambda: self.state["repair"]["started"] + 61).perform(
                "missing_projection", lambda _: self.fail("expired"), lambda _: True)

    def test_policy_refuses_dsl_unknown_actions_and_changed_limits(self):
        for change in (lambda p: p["signals"]["stale_pr"].update(action="shell"),
                       lambda p: p["signals"]["stale_pr"].update(requires=["missing"]),
                       lambda p: p["limits"].update(readback=2)):
            policy = copy.deepcopy(self.policy)
            change(policy)
            with self.assertRaises(repair.RepairRefusal):
                repair.load(json.dumps(policy))
        self.assertEqual(self.controller().report("arbitrary refusal prose")["classification"], "unknown_signal")


class OwnerLineageTests(unittest.TestCase):
    def setUp(self):
        self.fixture = atom_tests.IssueAtomTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture
        for name in atom.LIFECYCLE_FILES:
            path = self.f.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        subprocess.run(["git", "add", "."], cwd=self.f.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Bind repair source before admission"], cwd=self.f.root,
                       check=True, capture_output=True)
        self.f.authorization["base_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.f.root, text=True).strip()
        self.f.authorization["issue"]["body"] = self.f.authorization["issue"]["body"].replace(
            self.f.base, self.f.authorization["base_head"])
        self.f.path.write_text(json.dumps(self.f.authorization))
        self.f.digest = atom.digest_file(self.f.path)
        self.paths = atom.artifact_paths(self.f.path)
        for name in ("claim", "acceptance", "envelope"):
            atom.save_json(self.paths[name], {"fixture": name})
        self.state = {"schema_version": 1, "authorization_sha256": self.f.digest,
                      "phase": "issue", "writes": {}, "issue": None, "publication": None}

    def test_two_successors_cannot_fork_an_unspent_budget(self):
        c = atom.repair_controller(self.f.authorization, self.state, self.paths, fresh=True)
        self.state["issue"] = {"number": 202}
        self.state["publication"] = {"head": "old", "pr": {"number": 203}}
        atom.save_json(self.paths["state"], self.state)
        original = self.paths["state"].read_bytes()
        new_auth = {**self.f.authorization, "issue": {**self.f.authorization["issue"], "number": 202},
                    "prior_atom": {"path": str(self.f.path), "sha256": self.f.digest},
                    "prior_publication": self.state["publication"]}
        successors = []
        for name in ("successor-a", "successor-b"):
            new_paths = atom.artifact_paths(self.f.outer / (name + ".json"))
            new_state = {"authorization_sha256": "b" * 64}
            successor = atom.repair_controller(new_auth, new_state, new_paths, fresh=True)
            self.assertNotIn("repair", new_state)
            for signal in ("stale_pr", "missing_projection"):
                with self.assertRaisesRegex(repair.RepairRefusal, "exclusive_lineage_continuity_required"):
                    successor.perform(signal, lambda _: self.fail("forked budget"), lambda _: True)
            successors.append(successor.report("stale_pr"))
        self.assertEqual(self.paths["state"].read_bytes(), original)
        self.assertEqual(c.check()[0]["used"]["actions"], 0)
        record("fork-refused", {"successors": successors, "original": json.loads(original)})

    def test_new_lineage_reaches_refresh_and_rebuild_through_owned_runtime(self):
        f = self.f
        provider = atom_tests.Provider()
        # No precreated state or fabricated repair history: the actual owner
        # initializes, persists and creates the fixture Issue before stopping at
        # the existing Noodle wait. External owner/provider seams are fixtures.
        self.paths["envelope"].unlink()
        self.paths["envelope"].parent.rmdir()
        with patch.object(atom, "require_available_owner", return_value=None), \
             patch.object(atom.issue_execution, "supervised", return_value={"action": "running"}):
            first = atom._run_owned(f.path, f.authorization, f.digest, self.paths,
                                    environ=f.env, provider=provider)
        self.state = atom.read_json(self.paths["state"], "state")
        self.assertEqual(provider.create_calls, 1)
        self.assertEqual(self.state["repair"]["used"]["actions"], 0)
        self.assertEqual(self.state["phase"], "execution")
        # Candidate and claim share the newly admitted control root/base/Issue.
        candidate = f.root / ".worktrees" / "candidate"
        subprocess.run(["git", "worktree", "add", "-b", "candidate", str(candidate)],
                       cwd=f.root, check=True, capture_output=True)
        (candidate / "allowed.py").write_text("# fixture candidate\n")
        subprocess.run(["git", "add", "allowed.py"], cwd=candidate, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Exercise admitted candidate publication"],
                       cwd=candidate, check=True, capture_output=True)
        def git_value(ref):
            return subprocess.check_output(["git", "rev-parse", ref], cwd=candidate, text=True).strip()
        snapshot = f.root / ".noodle/state.snapshot.json"
        events = f.root / ".noodle/sessions/fixture/events.ndjson"
        atom.save_json(snapshot, {"fixture": "owner snapshot"})
        atom.save_json(events, {"fixture": "completed"})
        head, tree = git_value("HEAD"), git_value("HEAD^{tree}")
        envelope = atom.read_json(self.paths["envelope"], "envelope")
        claim = {"schema_version": 1, "owner": "Noodle", "repository": "ed3c/soodles",
            "subject": "ed3c/soodles#131", "order_id": envelope["execution"]["order_id"],
            "stage_index": 0, "attempt_id": "fixture:0:0", "session_id": "fixture",
            "worktree_name": "candidate", "worktree_path": str(candidate), "branch": "candidate",
            "head": head, "tree": tree, "base_branch": "main", "base_head": f.authorization["base_head"],
            "push_remote": "origin", "remote_url": "https://github.com/ed3c/soodles.git",
            "evidence": {"canonical_snapshot_sha256": atom.digest_file(snapshot),
                         "session_events_sha256": atom.digest_file(events)},
            "authorizes_provider_write": False, "authorizes_landing": False}
        fixture = SimpleNamespace(claim=claim, head=head, base=claim["base_head"],
            acceptance={"repository": claim["repository"], "scope": "candidate runtime acceptance",
                        "candidate": {"head": head, "tree": tree}, "authorizes_landing": False},
            provider=publication_tests.Provider(claim["base_head"], provider.value["body"]))
        branch = "soodles/issue-131-" + fixture.head[:12]
        stale = publication_tests.exact_pull(41, branch, fixture.base, "main", "Refs " + fixture.claim["subject"])
        fixture.provider.pull = lambda number: copy.deepcopy(stale)
        processes = []
        def refresh(number, timeout):
            process = subprocess.run([sys.executable, "-c", "import sys; print(sys.stdin.read())"],
                input=json.dumps(fixture.provider.pull_value), capture_output=True, text=True, timeout=timeout)
            self.assertEqual(process.returncode, 0)
            processes.append({"argv": process.args, "exit_status": process.returncode,
                              "stdout": process.stdout, "stderr": process.stderr})
            return json.loads(process.stdout)
        fixture.provider.repair_pull = refresh
        atom.save_json(self.paths["claim"], fixture.claim)
        atom.save_json(self.paths["acceptance"], fixture.acceptance)
        # Current Noodle claim/readiness are independently validated by the real
        # publisher. Only their production and GitHub transport use fixtures.
        def publish(auth, state, paths, claim, acceptance, unused, controller):
            return original_publish(auth, state, paths, claim, acceptance, fixture.provider, controller)
        original_publish = atom.publish_candidate
        def push(*args, **kwargs):
            fixture.provider.ref = fixture.head
            return publication_tests.Result()
        with patch.object(atom, "require_available_owner", return_value=None), \
             patch.object(atom.issue_execution, "supervised", return_value={"action": "review"}), \
             patch.object(atom, "authenticated_push", return_value=push), \
             patch.object(atom, "publish_candidate", side_effect=publish), \
             patch.object(atom, "select_run", return_value=(None, None)):
            published = atom._run_owned(f.path, f.authorization, f.digest, self.paths,
                                        environ=f.env, provider=provider)
        self.state = atom.read_json(self.paths["state"], "state")
        self.assertEqual(self.state["repair"]["used"]["readback"], 1)
        self.assertEqual(fixture.provider.create_calls, 1)
        self.state["publication"] = None  # only the disposable projection is lost
        atom.save_json(self.paths["state"], self.state)
        with patch.object(atom, "require_available_owner", return_value=None), \
             patch.object(atom, "publish_candidate", side_effect=AssertionError("duplicate publish")), \
             patch.object(atom, "select_run", return_value=(None, None)):
            original_acceptance = self.paths["acceptance"].read_bytes()
            invalid = copy.deepcopy(fixture.acceptance)
            invalid["candidate"]["head"] = "a" * 40
            atom.save_json(self.paths["acceptance"], invalid)
            with self.assertRaisesRegex(publication.PublicationRefusal, "acceptance.candidate"):
                atom._run_owned(f.path, f.authorization, f.digest, self.paths,
                                environ=f.env, provider=provider)
            self.assertEqual(atom.read_json(self.paths["state"], "state")["repair"]["used"]["rebuild"], 0)
            self.paths["acceptance"].write_bytes(original_acceptance)
            rebuilt = atom._run_owned(f.path, f.authorization, f.digest, self.paths,
                                      environ=f.env, provider=provider)
        self.state = atom.read_json(self.paths["state"], "state")
        self.assertEqual(self.state["repair"]["used"]["rebuild"], 1)
        before = self.paths["state"].read_bytes()
        c = atom.repair_controller(f.authorization, self.state, self.paths)
        with self.assertRaisesRegex(repair.RepairRefusal, "repeated_failure"):
            atom.refresh_publication(c, fixture.provider, 41, lambda _: True)
        self.assertEqual(self.paths["state"].read_bytes(), before)
        record("reachable-owner", {"first": first, "published": published, "rebuilt": rebuilt,
            "processes": processes, "checkpoint": self.state,
            "issue_creates": provider.create_calls, "pr_creates": fixture.provider.create_calls})

    def test_compiled_decision_is_io_free_and_does_not_require_future_evidence(self):
        c = atom.repair_controller(self.f.authorization, self.state, self.paths, fresh=True)
        for name in ("claim", "acceptance", "envelope"):
            self.paths[name].unlink()
        with ExitStack() as stack:
            for target in ("builtins.open", "pathlib.Path.open", "subprocess.Popen", "os.stat",
                           "socket.socket", "atom_repair.Controller.perform", "issue_atom.repair_binding",
                           "system_context.compile_repair", "test_manager.execute_units"):
                stack.enter_context(patch(target, side_effect=AssertionError("decision attempted IO/effect")))
            started = time.perf_counter_ns()
            report = c.report("missing_input")
            elapsed = time.perf_counter_ns() - started
            unknown = c.report("unknown_signal")
            risk = c.report("missing_projection")
            effect = c.report("unknown_effect")
        self.assertEqual(report["mode"], "owner_continuation")
        self.assertEqual(effect["mode"], "owner_continuation")
        self.assertEqual(risk["mode"], "defined_risk")
        self.assertEqual(unknown["mode"], "offline_measurement")
        self.assertEqual(report["context"]["requires"], ["contracts/system-v1/common.md",
                                                        "contracts/system-v1/issue-atom.md"])
        record("pure-decision", {"elapsed_ns": elapsed, "observation_count": 1,
            "scope": "one local data-only report; excludes cold compile, CLI, provider and Agent latency",
            "io_forbidden": True, "report": report, "risk": risk, "unknown": unknown})

    def test_legacy_and_same_issue_without_prior_history_do_not_reset(self):
        legacy = atom.repair_controller(self.f.authorization, self.state, self.paths)
        self.assertNotIn("repair", self.state)
        self.assertIsNone(legacy.report("stale_pr")["remaining"])
        adopted = {**self.f.authorization, "issue": {**self.f.authorization["issue"], "number": 202}}
        atom.repair_controller(adopted, self.state, self.paths, fresh=True)
        self.assertNotIn("repair", self.state)

    def test_missing_evidence_and_source_drift_refuse_before_repair_intent(self):
        with patch.object(atom, "__file__", str(self.f.root / "issue_atom.py")):
            c = atom.repair_controller(self.f.authorization, self.state, self.paths, fresh=True)
            self.paths["acceptance"].unlink()
            with self.assertRaisesRegex(atom.AtomRefusal, "repair.evidence.acceptance"):
                c.perform("stale_pr", lambda _: self.fail("missing evidence"), lambda _: True)
            atom.save_json(self.paths["acceptance"], {"fixture": "acceptance"})
            source = self.f.root / "atom_repair.py"
            source.write_bytes(source.read_bytes() + b"\n# changed after controller creation\n")
            with self.assertRaisesRegex(atom.AtomRefusal, "repair.source"):
                c.perform("stale_pr", lambda _: self.fail("changed source"), lambda _: True)
        self.assertEqual(self.state["repair"]["used"]["actions"], 0)

    def test_failed_real_claim_process_reports_capability_without_model(self):
        # Existing _run_owned boundary: fixture replaces external admission and
        # provider, but the Noodle claim command is a real failing subprocess.
        f = self.f
        f.env["SOODLES_AUTHORIZATION_SHA256"] = f.digest
        provider = atom_tests.Provider()
        f.ready_issue(provider)
        f.binary.write_text("#!/bin/sh\nprintf 'fixture claim failure' >&2\nexit 7\n")
        identity = {"path": str(f.binary), "sha256": atom.digest_file(f.binary)}
        f.authorization["noodle"] = identity
        f.authorization["carrier"]["codex"].update(identity)
        # Use the owned function: authorization validity is exercised by existing
        # test_issue_atom; this control fixes process/classification/checkpoint.
        paths = self.paths
        paths["claim"].unlink()
        paths["envelope"].parent.mkdir(parents=True, exist_ok=True)
        atom.save_json(paths["envelope"], {"execution": {"order_id": "fixture-order"}})
        self.state.update(phase="execution", issue={"number": 131},
                          envelope_sha256=atom.digest_file(paths["envelope"]))
        atom.save_json(paths["state"], self.state)
        with patch.object(atom, "require_available_owner", return_value=None), \
             patch.object(atom, "require_clean_control_root"), \
             patch.object(atom.issue_execution, "supervised", return_value={"action": "review"}):
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom._run_owned(f.path, f.authorization, f.digest, paths, environ=f.env, provider=provider)
        self.assertEqual(caught.exception.invalid["field"], "noodle.claim.exit")
        self.assertEqual(caught.exception.invalid["value"]["exit_status"], 7)
        record("claim-process", {"processes": [json.loads(p.read_text()) for p in paths["directory"].glob("claim-process-*.json")],
                                 "refusal": atom.refusal_output(caught.exception, f.path),
                                 "checkpoint": json.loads(paths["state"].read_text())})
        c = atom.repair_controller(f.authorization, self.state, paths)
        self.assertEqual(c.report(repair.observation(caught.exception))["stop"], "bounded_patch_capability_required")


class BoundedTransportTests(unittest.TestCase):
    def test_real_child_timeout_and_no_write_worker(self):
        # Substitute only the read transport within the actual fixed child.
        # Production supplies the same subprocess deadline; no method selector.
        original = subprocess.run
        observed = []
        def run(argv, **kwargs):
            observed.append((argv, kwargs["timeout"]))
            self.assertIn("_http('GET'", argv[-1])
            return original([sys.executable, "-c", "import time; time.sleep(5)"], **kwargs)
        with patch.object(provider_readback.subprocess, "run", side_effect=run):
            with self.assertRaises(subprocess.TimeoutExpired):
                provider_readback.bounded_pull("ed3c/soodles", 203, "fixture-token", 0.05)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][1], 0.05)


if __name__ == "__main__":
    unittest.main()
