from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom


@contextmanager
def typed_revision_receipts(authorization_path, state, output, *, body=None):
    """Fix the admitted packet while exercising the real receipt projection."""
    authorization = atom.read_json(authorization_path, "fixture.authorization")
    packet = {"authorization": {"path": str(authorization_path)}, "output": str(output),
              "selection": {"schema": 2, "target_base": authorization["base_head"],
                            "native_acceptance": {}}}
    state["scope_amendment"] = {"status": "released"}
    body = body or atom.authorized_issue_body(authorization, state["authorization_sha256"])
    with patch.object(atom, "scope_packet", return_value=packet), \
            patch.object(atom, "scope_history_authority", side_effect=lambda original, _: original), \
            patch.object(atom, "revision_body", return_value=body), \
            patch.object(atom.issue_admission, "load_revision_native", return_value=authorization["noodle"]):
        yield atom.scope_projection(authorization, state, atom.artifact_paths(authorization_path))[1]


class Result:
    def __init__(self, returncode, stderr=""):
        self.returncode = returncode
        self.stderr = stderr


class Provider:
    def __init__(self):
        self.token = "fixture-token"
        self.value = None
        self.create_calls = 0
        self.create_effect = True
        self.create_unknown = False
        self.merge_calls = 0

    def issues(self):
        return [] if self.value is None else [self.value]

    def issue(self, number):
        if self.value is None or self.value["number"] != number:
            return None
        return dict(self.value)

    def create_issue(self, title, body):
        self.create_calls += 1
        if self.create_effect:
            self.value = {"number": 131, "title": title, "body": body,
                          "state": "open", "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131",
                          "url": "https://api.github.com/repos/ed3c/soodles/issues/131"}
        if self.create_unknown:
            raise atom.MutationUnknown("lost response")
        return self.value

    def merge(self, number, head, method):
        self.merge_calls += 1
        return {"merged": True}

    def close_issue(self, number, state_reason):
        self.value["state"] = "closed"
        return self.value


class IssueAtomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.root = self.outer / "project"
        subprocess.run(["git", "init", "-b", "main", self.root], check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Atom Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "atom@example.invalid"],
                       cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(".noodle/\n.worktrees/\n.noodle.toml\n")
        for name in atom.supervisor_admission.BUNDLE_PATHS + (
                "schema_manager.py", "policy/host-finalization.json",
                ".agents/skills/execute/SKILL.md", ".agents/skills/schedule/SKILL.md"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(atom.__file__).parent / name).read_bytes())
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin",
                        "https://github.com/ed3c/soodles.git"], cwd=self.root, check=True)
        self.base = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                            cwd=self.root, text=True).strip()
        self.binary = self.outer / "carrier"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary),
                    "sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        self.owner_root = self.outer / "external-owner"
        hashes = {}
        for name in atom.OWNER_FILES:
            target = self.owner_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(atom.__file__).parent / name).read_bytes())
            hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.owner_spec = {"path": str(self.owner_root / "soodles.py"),
                           "sha256": hashes["soodles.py"],
                           "verifier_sha256": atom.digest_bytes(json.dumps(
                               hashes, sort_keys=True, separators=(",", ":")).encode())}
        contract = {
            "schema": 3, "trigger": "fixture", "source": "fixture",
            "owner": "fixture owner", "changes": ["fixture"],
            "write_paths": ["allowed.py"], "behavior": ["fixture"],
            "defect_controls": ["fixture"], "non_cases": ["fixture"],
            "dependencies": [], "acceptance": "fixture", "delivery": "fixture",
            "reconciliation": "fixture", "feature_scope": "fixture",
            "required_paths": ["allowed.py"], "evidence_manifest": "allowed.py",
            "base_head": self.base,
            "frozen_paths": [{"path": "allowed.py", "revision": "head",
                              "sha256": "a" * 64}],
        }
        body = ("<!-- soodles:execution-v1 -->\n```json\n"
                + json.dumps(contract) + "\n```\n"
                "<!-- /soodles:execution-v1 -->")
        self.authorization = {
            "schema_version": 2, "owner": "external-supervisor",
            "repository": "ed3c/soodles", "control_root": str(self.root),
            "base_head": self.base, "task": "Execute exact Issue.",
            "host_config_sha256": None,
            "issue": {"title": "Fixture atom", "body": body},
            "noodle": dict(identity),
            "landing_owner": self.owner_spec,
            "carrier": {"platform": __import__("platform").system().lower() + "_"
                                    + __import__("platform").machine().lower(),
                        "codex": {**identity, "model": "fixture-model",
                                  "argv": ["exec", "--skip-git-repo-check", "--json", "--model", "fixture-model"]}},
            "workflow": {"path": ".github/workflows/runtime.yml",
                         "job": "runtime-evidence",
                         "step": "Canonical acceptance on the exact candidate head"},
        }
        self.path = self.outer / "authorization.json"
        self.path.write_text(json.dumps(self.authorization))
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.env = {"SOODLES_AUTHORIZATION_SHA256": self.digest, "GH_TOKEN": "fixture",
                    "NOODLES_TOKEN_COMMAND": "printf fixture-installation-token"}

    def fixture_issue_body(self):
        body = self.authorization["issue"]["body"]
        if "number" in self.authorization["issue"]:
            return body
        return body.rstrip() + "\n\n" + atom.marker(self.digest) + "\n"

    def ready_issue(self, provider):
        body = self.fixture_issue_body()
        provider.value = {"number": 131, "title": self.authorization["issue"]["title"],
                          "body": body, "state": "open",
                          "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131",
                          "url": "https://api.github.com/repos/ed3c/soodles/issues/131"}

    def pending_patches(self):
        return (
            patch("issue_atom.issue_execution.supervised", return_value={"action": "running"}),
            patch("issue_atom._run_claim", side_effect=AssertionError("running owner must not request a claim")),
        )

    def startup_fixture(self):
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        envelope, digest = atom.create_envelope(self.authorization, provider.value,
                                               provider.value["body"], paths["envelope"], environ=self.env)
        runtime = self.root / ".noodle"
        runtime.mkdir()
        atom.save_json(runtime / "state.snapshot.json", {"state": {"orders": {}}, "effect_ledger": []})
        state = {"phase": "execution", "authorization_sha256": self.digest, "envelope_sha256": digest,
                 "admission_sha256": atom.digest_file(paths["envelope"].parent / "prepared.json")}
        return paths, state

    def own_wait_fixture(self, running=False):
        """Disposable canonical/process fixture, never live process attestation."""
        paths, state = self.startup_fixture()
        binding = atom.read_json(paths["envelope"], "envelope")
        binding["issue_body"] = self.fixture_issue_body()
        binding["contract"] = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        oid = binding["execution"]["order_id"]
        config = paths["envelope"].parent / "noodle.toml"
        (self.root / ".noodle.toml").write_bytes(config.read_bytes())
        state.update(schema_version=1, issue={"number": 131}, writes={}, publication=None,
                     noodle_start={"status": "started", "pid": 424242,
                                   "argv": [str(config.parent / "start-noodle")],
                                   "config_sha256": atom.digest_file(config), "original_config": None})
        stages = {}
        for skill, current_id in (("schedule", "schedule"), ("execute", oid)):
            sid = "fixture-" + skill
            worktree = "" if skill == "schedule" else oid + "-0-execute"
            stages[skill] = {"stage_index": 0, "task_key": skill, "skill": skill,
                "provider": "codex", "model": "fixture-model", "runtime": "process",
                "prompt": "" if skill == "schedule" else json.dumps(atom.issue_execution.projection(
                    binding, state["envelope_sha256"], "supervised")),
                "status": "running", "attempts": [{"attempt_id": current_id + "-0-attempt-0",
                    "session_id": sid, "status": "running", "worktree_name": worktree}]}
            if skill == "execute" and not running:
                stages[skill].update(status="pending", attempts=None)
                continue
            directory = self.root / ".noodle/sessions" / sid
            atom.save_json(directory / "spawn.json", {"session_id": sid, "provider": "codex",
                "model": "fixture-model", "runtime": "process", "skill": skill,
                "worktree_path": str(self.root if skill == "schedule" else self.root / ".worktrees" / worktree)})
            atom.save_json(directory / "process.json", {"session_id": sid,
                "pid": 424243 if skill == "schedule" else 424244})
            atom.save_json(directory / "meta.json", {"session_id": sid, "provider": "codex",
                "model": "fixture-model", "runtime": "process", "status": "running", "alive": True})
        snapshot = {"state": {"orders": {
            "schedule": {"order_id": "schedule", "status": "active", "stages": [stages["schedule"]]},
            oid: {"order_id": oid, "status": "active", "stages": [stages["execute"]]}}}, "effect_ledger": []}
        atom.save_json(self.root / ".noodle/state.snapshot.json", snapshot)
        atom.save_json(paths["state"], state)
        return paths, state, snapshot

    def own_wait_processes(self):
        from contextlib import ExitStack
        import fcntl
        stack = ExitStack()
        self.addCleanup(stack.close)
        lock = stack.enter_context((self.root / ".noodle/noodle.lock").open("a+b"))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        expected = " ".join([self.authorization["noodle"]["path"], "--project-dir", str(self.root), "start"])
        actual_run = atom.subprocess.run
        def process_read(argv, *args, **kwargs):
            if argv[0] == "ps":
                return subprocess.CompletedProcess(argv, 0, expected + "\n", "")
            return actual_run(argv, *args, **kwargs)
        stack.enter_context(patch.object(atom.subprocess, "run", side_effect=process_read))
        stack.enter_context(patch.object(atom.os, "kill", return_value=None))
        return stack

    def allow_cost_artifacts_only(self, stack, paths):
        save = atom.save_json
        def guarded(path, value, **kwargs):
            self.assertTrue(Path(path).resolve().is_relative_to((paths["directory"] / "cost").resolve()),
                            "wait must not write lifecycle state or offer effects")
            return save(path, value, **kwargs)
        stack.enter_context(patch.object(atom, "save_json", side_effect=guarded))

    def test_own_start_wait_has_no_effects_and_preserves_all_fixture_bytes(self):
        paths, state, snapshot = self.own_wait_fixture()
        with self.own_wait_processes() as stack:
            self.allow_cost_artifacts_only(stack, paths)
            spies = [stack.enter_context(patch.object(owner, name, side_effect=AssertionError(name)))
                     for owner, name in ((atom.provider_credential, "resolve_host_environment"),
                         (atom.provider_credential, "supply_token"), (atom, "GitHubProvider"),
                         (atom, "LandingOwner"), (atom, "ensure_noodle"), (atom, "exact_issue"),
                         (atom, "_run_claim"))]
            before = {p: p.read_bytes() for root in (self.root / ".noodle", paths["directory"])
                      for p in root.rglob("*") if p.is_file()}
            before[self.root / ".noodle.toml"] = (self.root / ".noodle.toml").read_bytes()
            result = atom.drive(self.path, timeout=0, environ=self.env)
            self.assertEqual(result["execution"]["action"], "own_start_wait")
            self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
            self.assertTrue(result["wait_exhausted"])
            self.assertFalse(result["authorizes_landing"])
            self.assertTrue(all(path.read_bytes() == raw for path, raw in before.items()))
            for spy in spies:
                spy.assert_not_called()

    def test_own_running_metadata_and_pins_remain_required(self):
        paths, state, snapshot = self.own_wait_fixture(running=True)
        session = self.root / ".noodle/sessions/fixture-execute"
        with self.own_wait_processes(), patch.object(atom.provider_credential, "supply_token") as supplier:
            self.assertEqual(atom.run(self.path, environ=self.env)["status"], "pending")
            mutations = [
                (paths["state"], lambda v: v["noodle_start"].update(restored=True)),
                (paths["state"], lambda v: v.update(admission_sha256="0" * 64)),
                (paths["state"], lambda v: v["noodle_start"].update(config_sha256="0" * 64)),
                (paths["state"], lambda v: v["noodle_start"].update(argv=["/foreign"])),
                (session / "process.json", lambda v: v.update(session_id="foreign")),
                (session / "process.json", lambda v: v.update(pid=True)),
                (session / "meta.json", lambda v: v.update(alive=False)),
                (session / "spawn.json", lambda v: v.update(worktree_path="/foreign")),
            ]
            for path, mutate in mutations:
                with self.subTest(path=path, mutation=mutate):
                    original = path.read_bytes()
                    value = json.loads(original); mutate(value); atom.save_json(path, value)
                    try:
                        with self.assertRaises(atom.AtomRefusal):
                            atom.run(self.path, environ=self.env)
                    finally:
                        path.write_bytes(original)
            supplier.assert_not_called()

    def test_owner_binding_preserves_adopted_body_and_rejects_digest_mismatch(self):
        self.authorization["issue"]["number"] = 131
        self.authorization["issue"]["body"] += "\n\nAdopted Issue text.\n\n"
        paths, state, _ = self.own_wait_fixture()
        with self.own_wait_processes(), patch.object(atom.provider_credential, "supply_token") as supplier:
            observed = atom.require_available_owner(self.authorization, paths, state)
            self.assertEqual(observed["action"], "own_start_wait")
            self.authorization["issue"]["body"] += "Changed text.\n"
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.binding"):
                atom.require_available_owner(self.authorization, paths, state)
            supplier.assert_not_called()

    def test_own_wait_requires_consistent_dispatch_and_pending_attempts(self):
        paths, state, snapshot = self.own_wait_fixture(running=True)
        snapshot_path = self.root / ".noodle/state.snapshot.json"
        execute = next(order["stages"][0] for oid, order in snapshot["state"]["orders"].items()
                       if oid != "schedule")
        meta_path = self.root / ".noodle/sessions/fixture-execute/meta.json"
        with self.own_wait_processes():
            execute["status"] = "dispatching"
            execute["attempts"][0]["status"] = "launching"
            meta = atom.read_json(meta_path, "meta"); meta["status"] = "launching"
            atom.save_json(meta_path, meta); atom.save_json(snapshot_path, snapshot)
            self.assertEqual(atom.run(self.path, environ=self.env)["status"], "pending")
            for change in ({"status": "pending"}, {"status": "running"},
                           {"status": "dispatching", "attempts": []}):
                original = dict(execute)
                execute.update(change); atom.save_json(snapshot_path, snapshot)
                with self.assertRaises(atom.AtomRefusal):
                    atom.run(self.path, environ=self.env)
                execute.clear(); execute.update(original)

    def test_own_start_wait_refuses_readback_race(self):
        paths, state, snapshot = self.own_wait_fixture()
        actual_read = atom.issue_execution.read_owner
        def changing_read(binding):
            value = actual_read(binding)
            if changing_read.seen:
                value["state"]["orders"]["schedule"]["stages"][0]["model"] = "foreign"
            changing_read.seen = True
            return value
        changing_read.seen = False
        with self.own_wait_processes(), patch.object(atom.issue_execution, "read_owner", side_effect=changing_read):
            with self.assertRaisesRegex(atom.AtomRefusal, "snapshot_changed"):
                atom.run(self.path, environ=self.env)

    def test_own_wait_ignores_telemetry_churn_but_refuses_session_drift(self):
        paths, state, snapshot = self.own_wait_fixture(running=True)
        actual_read = Path.read_bytes
        session = self.root / ".noodle/sessions/fixture-execute"
        meta_path = session / "meta.json"
        original = actual_read(meta_path)
        for change, allowed in (({"total_cost_usd": 0.001, "updated_at": "later"}, True),
                                ({"session_id": "foreign"}, False),
                                ({"provider": "foreign"}, False),
                                ({"model": "foreign"}, False),
                                ({"runtime": "foreign"}, False),
                                ({"status": "exited"}, False),
                                ({"alive": False}, False),
                                ({"alive": 1}, False)):
            with self.subTest(change=change):
                reads = []
                def churn(path):
                    raw = actual_read(path)
                    if path == meta_path:
                        reads.append(path)
                        if len(reads) == 2:
                            value = json.loads(raw)
                            value.update(change)
                            path.write_text(json.dumps(value))
                            raw = actual_read(path)
                    return raw
                with self.own_wait_processes() as stack:
                    self.allow_cost_artifacts_only(stack, paths)
                    spies = [stack.enter_context(patch.object(owner, name,
                                side_effect=AssertionError(name))) for owner, name in
                             ((atom.provider_credential, "resolve_host_environment"),
                              (atom.provider_credential, "supply_token"),
                              (atom, "GitHubProvider"), (atom, "ensure_noodle"),
                              (atom, "_run_claim"))]
                    with patch.object(Path, "read_bytes", churn):
                        if allowed:
                            result = atom.drive(self.path, timeout=0, environ=self.env)
                            self.assertEqual(result["status"], "pending")
                            self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
                        else:
                            with self.assertRaisesRegex(atom.AtomRefusal, "metadata_changed"):
                                atom.drive(self.path, timeout=0, environ=self.env)
                    for spy in spies:
                        spy.assert_not_called()
                self.assertEqual(len(reads), 2)
                meta_path.write_bytes(original)
                self.assertEqual(atom.read_json(paths["state"], "state"), state)
                self.assertEqual(atom.read_json(self.root / ".noodle/state.snapshot.json", "snapshot"), snapshot)

    def test_own_wait_order_timestamp_churn_preserves_state_discriminator(self):
        paths, state, snapshot = self.own_wait_fixture()
        actual_read = atom.issue_execution.read_owner
        for change, allowed in (({"updated_at": "later"}, True),
                                ({"status": "failed"}, False)):
            with self.subTest(change=change):
                reads = []
                def changing_read(binding):
                    value = actual_read(binding)
                    reads.append(value)
                    if len(reads) == 2:
                        value["state"]["orders"]["schedule"].update(change)
                    return value
                with self.own_wait_processes(), patch.object(atom.issue_execution, "read_owner",
                        side_effect=changing_read), patch.object(atom.provider_credential,
                        "supply_token") as supplier:
                    if allowed:
                        self.assertEqual(atom.run(self.path, environ=self.env)["status"], "pending")
                    else:
                        with self.assertRaisesRegex(atom.AtomRefusal, "snapshot_changed"):
                            atom.run(self.path, environ=self.env)
                    supplier.assert_not_called()
                self.assertEqual(len(reads), 2)


    def test_invalid_authorization_precedes_shared_owner_entry(self):
        import fcntl
        runtime = self.root / ".noodle"
        runtime.mkdir()
        with (runtime / "issue-atom.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(atom.AtomRefusal, "authorization.digest"):
                atom.run(self.path, environ={**self.env, "SOODLES_AUTHORIZATION_SHA256": "0" * 64})
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())

    def test_matching_config_does_not_adopt_foreign_order(self):
        import fcntl
        paths, state = self.startup_fixture()
        state.update(schema_version=1, issue={"number": 131}, writes={})
        atom.save_json(paths["state"], state)
        (self.root / ".noodle.toml").write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        snapshot = self.root / ".noodle/state.snapshot.json"
        atom.save_json(snapshot, {"state": {"orders": {"soodles-130": {
            "stages": [{"status": "running", "attempts": []}]}}}, "effect_ledger": []})
        before = snapshot.read_bytes(), paths["state"].read_bytes()
        with (self.root / ".noodle/noodle.lock").open("a+b") as lock, \
                patch.object(atom.provider_credential, "supply_token") as supplier:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.run(self.path, environ=self.env)
        result = atom.refusal_output(caught.exception, self.path)
        self.assertEqual(result["next"]["owner"], "Noodle")
        self.assertEqual(result["next"]["known"]["blocking_order_ids"], ["soodles-130"])
        self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(before, (snapshot.read_bytes(), paths["state"].read_bytes()))
        supplier.assert_not_called()

    def test_retired_resolved_checkpoint_is_historical_readback(self):
        paths = atom.artifact_paths(self.path)
        runtime = self.root / ".noodle"
        runtime.mkdir()
        (runtime / "state.snapshot.json").write_text("retired owner no longer available")
        state = {"phase": "resolved", "noodle_start": {"restored": True}}
        atom.require_available_owner(self.authorization, paths, state)
        state["noodle_start"]["restored"] = False
        with self.assertRaises(atom.AtomRefusal) as caught:
            atom.require_available_owner(self.authorization, paths, state)
        self.assertEqual(caught.exception.owner, "Noodle")

    def test_exact_projection_with_malformed_stage_refuses_before_supplier(self):
        import fcntl
        paths, state = self.startup_fixture()
        state.update(schema_version=1, issue={"number": 131}, writes={})
        atom.save_json(paths["state"], state)
        (self.root / ".noodle.toml").write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        binding = atom.read_json(paths["envelope"], "envelope")
        binding["issue_body"] = self.fixture_issue_body()
        binding["contract"] = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        stage = {"status": "running", "skill": "execute", "provider": "codex", "model": "fixture-model",
                 "prompt": json.dumps(atom.issue_execution.projection(binding, state["envelope_sha256"], "supervised")),
                 "attempts": [{"status": "running", "session_id": "fixture-existing"}]}
        with (self.root / ".noodle/noodle.lock").open("a+b") as lock, \
                patch.object(atom.provider_credential, "supply_token") as supplier:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for change in ({"attempts": None}, {"attempts": []}, {"status": "unknown"}, {"model": "foreign"}):
                with self.subTest(change=change):
                    atom.save_json(self.root / ".noodle/state.snapshot.json", {
                        "state": {"orders": {binding["execution"]["order_id"]: {"stages": [{**stage, **change}]}}},
                        "effect_ledger": []})
                    with self.assertRaises(atom.AtomRefusal) as caught:
                        atom.run(self.path, environ=self.env)
                    self.assertEqual(caught.exception.owner, "Noodle")
        supplier.assert_not_called()

    def test_idle_native_schedule_is_observed_but_foreign_scheduler_refuses(self):
        import fcntl
        paths, state = self.startup_fixture()
        state.update(issue={"number": 131}, noodle_start={"status": "started"})
        (self.root / ".noodle.toml").write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        binding = atom.read_json(paths["envelope"], "envelope")
        binding["issue_body"] = self.fixture_issue_body()
        binding["contract"] = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        order_id = binding["execution"]["order_id"]
        stage = {"status": "running", "skill": "execute", "provider": "codex",
                 "model": "fixture-model", "prompt": json.dumps(atom.issue_execution.projection(
                     binding, state["envelope_sha256"], "supervised")),
                 "attempts": [{"status": "running", "session_id": "fixture-existing"}]}
        schedule = {"order_id": "schedule", "status": "active", "stages": [{
            "stage_index": 0, "task_key": "schedule", "skill": "schedule",
            "provider": "codex", "model": "fixture-model", "runtime": "process",
            "prompt": "", "status": "pending", "attempts": None}]}
        snapshot = self.root / ".noodle/state.snapshot.json"
        with (self.root / ".noodle/noodle.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atom.save_json(snapshot, {"state": {"orders": {
                order_id: {"stages": [stage]}, "schedule": schedule}}, "effect_ledger": []})
            atom.require_available_owner(self.authorization, paths, state)
            for changed in ({"provider": "foreign"}, {"status": "running"}):
                schedule["stages"][0].update(changed)
                atom.save_json(snapshot, {"state": {"orders": {
                    order_id: {"stages": [stage]}, "schedule": schedule}}, "effect_ledger": []})
                with self.assertRaisesRegex(atom.AtomRefusal, "noodle.orders"):
                    atom.require_available_owner(self.authorization, paths, state)
                schedule["stages"][0] = {**schedule["stages"][0], **{"provider": "codex", "status": "pending"}}

    def test_stopped_owner_idle_schedule_keeps_exact_order_and_all_process_checks(self):
        paths, state = self.startup_fixture()
        state.update(issue={"number": 131}, noodle_start={"stop_offered": True})
        binding = atom.read_json(paths["envelope"], "envelope")
        binding["issue_body"] = self.fixture_issue_body()
        binding["contract"] = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        oid = binding["execution"]["order_id"]
        stage = {"status": "completed", "skill": "execute", "provider": "codex",
                 "model": "fixture-model", "prompt": json.dumps(atom.issue_execution.projection(
                     binding, state["envelope_sha256"], "supervised")),
                 "attempts": [{"status": "completed", "session_id": "original"}]}
        schedule = {"order_id": "schedule", "status": "active", "stages": [{
            "stage_index": 0, "task_key": "schedule", "skill": "schedule",
            "provider": "codex", "model": "fixture-model", "runtime": "process",
            "prompt": "", "status": "pending", "attempts": None}]}
        snapshot = {"state": {"orders": {oid: {"stages": [stage]}, "schedule": schedule}}, "effect_ledger": []}
        for sid, pid in (("original", 987650), ("other-session", 987651)):
            directory = self.root / ".noodle/sessions" / sid
            directory.mkdir(parents=True)
            atom.save_json(directory / "process.json", {"session_id": sid, "pid": pid})
        path = self.root / ".noodle/state.snapshot.json"
        atom.save_json(path, snapshot)
        with patch.object(atom.os, "kill", side_effect=ProcessLookupError):
            atom.require_available_owner(self.authorization, paths, state)
            stage["prompt"] = "foreign"
            atom.save_json(path, snapshot)
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.order.binding"):
                atom.require_available_owner(self.authorization, paths, state)
            stage["prompt"] = json.dumps(atom.issue_execution.projection(binding, state["envelope_sha256"], "supervised"))
            schedule["stages"][0]["model"] = "foreign"
            atom.save_json(path, snapshot)
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.orders"):
                atom.require_available_owner(self.authorization, paths, state)
        schedule["stages"][0]["model"] = "fixture-model"
        atom.save_json(path, snapshot)
        def live_extra(pid, sig):
            if abs(pid) != 987651:
                raise ProcessLookupError
        with patch.object(atom.os, "kill", side_effect=live_extra):
            with self.assertRaisesRegex(atom.AtomRefusal, "completion.process_alive"):
                atom.require_available_owner(self.authorization, paths, state)

    def test_projected_completed_order_can_continue_original_cleanup(self):
        import fcntl
        from test_issue_execution import IssueExecutionTests
        fixture = IssueExecutionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        session = fixture.archived_completion()
        events = session / "events.ndjson"
        event = json.loads(events.read_text())
        event["session_id"] = fixture.session
        events.write_text(json.dumps(event) + "\n")
        retained_path = fixture.path.parent / "publication-claim.json"
        atom.save_json(retained_path, {"session_id": "retained", "attempt_id": "old"})
        retained = retained_path.read_bytes()
        claim_path = fixture.path.parent / "revision/publication/publication-claim.json"
        atom.save_json(claim_path, {
            "order_id": "soodles-18", "stage_index": 0,
            "worktree_name": fixture.envelope["execution"]["worktree"],
            "attempt_id": "soodles-18-0-attempt-0", "session_id": fixture.session})
        paths = {"envelope": fixture.path, "claim": claim_path}
        config = b"fixture installed config\n"
        (fixture.root / ".noodle.toml").write_bytes(config)
        (fixture.path.parent / "noodle.toml").write_bytes(config)
        authorization = {"control_root": str(fixture.root), "repository": "ed3c/soodles",
                         "base_head": fixture.envelope["base_head"],
                         "issue": {"number": 18, "body": fixture.issue["body"]}}
        state = {"phase": "landing", "issue": {"number": 18},
                 "authorization_sha256": atom.digest_bytes(json.dumps(authorization).encode()),
                 "envelope_sha256": fixture.pin, "noodle_completion": {"order_id": "soodles-18"}}
        with (fixture.runtime / "noodle.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atom.require_available_owner(authorization, paths, state)
            del state["noodle_completion"]
            state["noodle_reconciliation"] = {"status": "observed"}
            atom.require_available_owner(authorization, paths, state)
            events = session / "events.ndjson"
            bad = json.loads(events.read_text())
            bad["payload"].update(outcome="blocked", blocking=True)
            events.write_text(json.dumps(bad) + "\n")
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.require_available_owner(authorization, paths, state)
        self.assertEqual(caught.exception.invalid["field"], "completion.typed_outcome")
        self.assertEqual(caught.exception.owner, "Noodle")
        self.assertEqual(retained_path.read_bytes(), retained)

    def test_exact_existing_issue_adoption_never_creates_or_rewrites(self):
        provider = Provider()
        self.ready_issue(provider)
        selected = {**self.authorization, "issue": {"number": 131,
                    "title": provider.value["title"], "body": provider.value["body"]}}
        issue, body = atom.exact_issue(provider, selected, self.digest)
        self.assertEqual(issue, provider.value)
        self.assertEqual(body, provider.value["body"])
        provider.value["body"] += "drift"
        with self.assertRaisesRegex(atom.AtomRefusal, "github.issue.adoption"):
            atom.exact_issue(provider, selected, self.digest)
        provider.value = None
        with self.assertRaises(atom.AtomRefusal):
            atom.exact_issue(provider, selected, self.digest)
        self.assertEqual(provider.create_calls, 0)

    def test_start_persists_intent_and_does_not_repeat_unknown_start(self):
        paths, state = self.startup_fixture()
        from unittest.mock import Mock
        def spawn(*args, **kwargs):
            persisted = atom.read_json(paths["state"], "state")
            self.assertEqual(persisted["noodle_start"]["status"], "offered")
            self.assertEqual(args[0], [str(paths["envelope"].parent / "start-noodle")])
            self.assertEqual((self.root / ".noodle.toml").read_bytes(),
                             (paths["envelope"].parent / "noodle.toml").read_bytes())
            return Mock(pid=987654)
        with patch.object(atom.subprocess, "Popen", side_effect=spawn) as start, \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=0)):
            observed = atom.ensure_noodle(self.authorization, paths, state,
                                         {"action": "proposal_pending"}, self.env)
            self.assertEqual(observed["action"], "started")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.start.outcome"):
                atom.ensure_noodle(self.authorization, paths, state, {"action": "proposal_pending"}, self.env)
        self.assertEqual(start.call_count, 1)

    def test_same_pr_can_use_fresh_admission_without_restoring_an_old_order(self):
        import test_supervisor_authorization
        fixture = test_supervisor_authorization.AuthorizationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.selection["issue"]["number"] = 128
        prior = {
            "owner": "soodles.candidate-publication", "status": "created",
            "repository": "ed3c/soodles", "subject": "ed3c/soodles#128",
            "branch": "soodles/issue-128-" + "b" * 12,
            "head": "b" * 40, "tree": "c" * 40,
            "pr": {"number": 41, "url": "https://github.com/ed3c/soodles/pull/41"},
            "next": None, "authorizes_landing": False,
        }
        fixture.selection["prior_publication"] = prior
        fixture.path.write_text(json.dumps(fixture.selection))
        fixture.digest = atom.digest_file(fixture.path)
        with patch.object(atom, "prior_host_config", side_effect=AssertionError("old host")), \
                patch.object(atom, "verify_prior_atom", side_effect=AssertionError("old order")):
            prepared = fixture.run_authorize()
            authorization, _ = atom.validate_authorization(
                prepared["authorization"]["path"], prepared["authorization"]["sha256"])
            self.assertEqual(authorization["prior_publication"], prior)
            self.assertNotIn("prior_atom", authorization)
            self.assertEqual(fixture.run_authorize(), prepared)
            issue = {**authorization["issue"], "state": "open",
                     "updated_at": "2026-09-30T00:00:00Z",
                     "url": "https://api.github.com/repos/ed3c/soodles/issues/128",
                     "html_url": "https://github.com/ed3c/soodles/issues/128"}
            paths = atom.artifact_paths(prepared["authorization"]["path"])
            envelope, _ = atom.create_envelope(authorization, issue, issue["body"],
                paths["envelope"], environ={"NOODLES_TOKEN_COMMAND": "printf fixture"})
            native = atom.read_json(paths["envelope"].parent / "prepared.json", "prepared")
            self.assertIn("bootstrap", native)
            self.assertNotIn("process_argv", native)
            self.assertEqual(envelope["execution"]["order_id"],
                             atom.issue_admission.scoped_order_id(128, fixture.fixture.root))
        # Publication identity remains mandatory; removing order coupling
        # must not permit another Issue, PR or a half-specified prior order.
        fixture.output = fixture.fixture.outer / "wrong-issue"
        fixture.selection["prior_publication"]["subject"] = "ed3c/soodles#999"
        fixture.path.write_text(json.dumps(fixture.selection))
        fixture.digest = atom.digest_file(fixture.path)
        with self.assertRaisesRegex(atom.issue_admission.AdmissionRefusal, "amendment.prior.identity"):
            fixture.run_authorize()
        self.assertFalse(fixture.output.exists())
        del fixture.selection["prior_publication"]
        fixture.selection["prior_atom"] = {"path": "/missing", "sha256": "a" * 64}
        fixture.path.write_text(json.dumps(fixture.selection))
        fixture.digest = atom.digest_file(fixture.path)
        with self.assertRaisesRegex(atom.issue_admission.AdmissionRefusal, "selection.fields"):
            fixture.run_authorize()

    def selected_lifecycle_fixture(self):
        runtime = self.outer / "selected-lifecycle"
        for name in atom.LIFECYCLE_FILES:
            target = runtime / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(atom.__file__).parent / name).read_bytes())
        for name in ("issue-atom", "soodles"):
            (runtime / name).chmod(0o755)
        with (runtime / "issue_execution.py").open("a") as stream:
            stream.write("\n# Selected lifecycle fixture bytes.\n")
        hashes = {name: atom.digest_file(runtime / name) for name in atom.LIFECYCLE_FILES}
        self.authorization["lifecycle_owner"] = {
            "path": str(runtime / "issue-atom"), "sha256": hashes["issue-atom"],
            "source_sha256": atom.digest_bytes(json.dumps(
                hashes, sort_keys=True, separators=(",", ":")).encode()),
        }
        return runtime

    def test_initial_envelope_uses_selected_lifecycle_bundle_and_prompt(self):
        runtime = self.selected_lifecycle_fixture()
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        landing_owner = dict(self.authorization["landing_owner"])
        skill = ".agents/skills/execute/SKILL.md"
        committed_skill = (self.root / skill).read_bytes()
        (self.root / skill).write_text("Uncommitted instructions must not enter the bundle.\n")
        with patch.object(atom, "__file__", str(runtime / "issue_atom.py")), \
                patch.object(atom, "verify_prior_atom", side_effect=AssertionError("initial admission")), \
                patch.object(atom, "save_json", side_effect=AssertionError("duplicate prepared receipt")):
            envelope, digest = atom.create_envelope(self.authorization, provider.value,
                provider.value["body"], paths["envelope"], environ=self.env)
        bundle = paths["envelope"].parent
        for name in atom.supervisor_admission.BUNDLE_PATHS:
            self.assertEqual((bundle / "runtime" / name).read_bytes(), (runtime / name).read_bytes())
        self.assertNotEqual((bundle / "runtime/issue_execution.py").read_bytes(),
                            (self.root / "issue_execution.py").read_bytes())
        self.assertEqual((bundle / "runtime" / skill).read_bytes(), committed_skill)
        self.assertEqual(self.authorization["landing_owner"], landing_owner)
        prepared = atom.read_json(bundle / "prepared.json", "prepared")
        self.assertEqual(prepared["envelope_sha256"], digest)
        self.assertIn("bootstrap", prepared)
        self.assertNotIn("process_argv", prepared)
        binding = {**envelope, "contract": atom.issue_admission.parse_contract(provider.value["body"]),
                   "issue_body": provider.value["body"]}
        prompt = subprocess.check_output([
            sys.executable, "-B", "-c",
            "import json, sys, issue_execution; "
            "print(json.dumps(issue_execution.projection(json.load(sys.stdin), sys.argv[1], 'supervised')))",
            digest], input=json.dumps(binding), text=True, cwd=bundle / "runtime")
        self.assertEqual(json.loads(prompt)["issue_body"], provider.value["body"])

    def test_initial_envelope_without_lifecycle_uses_committed_runtime(self):
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        source = self.root / "issue_execution.py"
        committed = source.read_bytes()
        source.write_text("Uncommitted runtime must not enter the bundle.\n")
        with patch.object(atom, "validate_lifecycle_owner", side_effect=AssertionError("no selection")):
            _, digest = atom.create_envelope(self.authorization, provider.value,
                provider.value["body"], paths["envelope"], environ=self.env)
        bundle = paths["envelope"].parent
        self.assertEqual((bundle / "runtime/issue_execution.py").read_bytes(), committed)
        self.assertEqual(atom.read_json(bundle / "prepared.json", "prepared")["envelope_sha256"], digest)

    def test_initial_envelope_rejects_changed_lifecycle_before_preparation(self):
        runtime = self.selected_lifecycle_fixture()
        with (runtime / "issue_execution.py").open("a") as stream:
            stream.write("\n# Changed after selection.\n")
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        with patch.object(atom, "__file__", str(runtime / "issue_atom.py")), \
                patch.object(atom.supervisor_admission, "prepare") as prepare:
            with self.assertRaisesRegex(atom.AtomRefusal, "authorization.lifecycle_owner.source_sha256"):
                atom.create_envelope(self.authorization, provider.value,
                    provider.value["body"], paths["envelope"], environ=self.env)
        prepare.assert_not_called()
        self.assertFalse(paths["envelope"].parent.exists())

    def test_correction_envelope_derives_hold_only_after_original_host_recovery(self):
        provider = Provider()
        self.ready_issue(provider)
        self.authorization["prior_atom"] = {"path": "/external/prior", "sha256": "a" * 64}
        paths = atom.artifact_paths(self.path)
        with patch.object(atom, "verify_prior_atom", return_value={"prior_loop_status": "stopped"}):
            with self.assertRaisesRegex(atom.AtomRefusal, "envelope.prior_host"):
                atom.create_envelope(self.authorization, provider.value,
                                     provider.value["body"], paths["envelope"], environ=self.env)
        self.assertFalse(paths["envelope"].parent.exists())
        name = atom.issue_admission.scoped_order_id(provider.value["number"], self.root) + "-0-execute"
        subprocess.run(["git", "worktree", "add", "-b", name,
                        str(self.root / ".worktrees" / name), self.authorization["base_head"]],
                       cwd=self.root, check=True, capture_output=True)
        with patch.object(atom, "verify_prior_atom", return_value={"prior_loop_status": "restored"}):
            atom.create_envelope(self.authorization, provider.value,
                                 provider.value["body"], paths["envelope"], environ=self.env)
        prepared = atom.read_json(paths["envelope"].parent / "prepared.json", "prepared")
        self.assertEqual(prepared["process_argv"], [self.authorization["noodle"]["path"],
                         "--project-dir", str(self.root), "start", "--mode", "manual"])
        self.assertNotIn("bootstrap", prepared)

    def test_prior_review_preserves_failed_history_but_binds_latest_completed_session(self):
        paths, state = self.startup_fixture()
        binding = atom.read_json(paths["envelope"], "envelope")
        oid = binding["execution"]["order_id"]
        name = binding["execution"]["worktree"]
        worker = self.root / ".worktrees" / name
        subprocess.run(["git", "worktree", "add", "-b", name, str(worker), self.base],
                       cwd=self.root, check=True, capture_output=True)
        tree = atom._git(worker, "rev-parse", "HEAD^{tree}")
        publication = {"head": self.base, "tree": tree}
        state.update(phase="ci", issue={"number": 131}, publication=publication)
        atom.save_json(paths["state"], state)
        atom.save_json(paths["claim"], {"repository": "ed3c/soodles", "subject": "ed3c/soodles#131",
            "head": self.base, "tree": tree, "base_head": self.base, "order_id": oid,
            "worktree_name": name, "worktree_path": str(worker), "session_id": "latest"})
        current = self.enterContext(typed_revision_receipts(self.path, state, self.outer / "revision"))
        atom.save_json(current["claim"], atom.read_json(paths["claim"], "fixture.claim"))
        atom.save_json(paths["claim"], {"head": "retained", "session_id": "old"})
        retained = paths["claim"].read_bytes()
        atom.save_json(paths["state"], state)
        authorization = {**self.authorization, "issue": {**self.authorization["issue"], "number": 131},
            "prior_atom": {"path": str(self.path), "sha256": self.digest}, "prior_publication": publication}
        old_binding = {**binding, "issue_body": self.fixture_issue_body(),
                       "contract": atom.issue_admission.parse_contract(self.fixture_issue_body())}
        stage = {"status": "review", "skill": "execute", "provider": "codex", "model": "fixture-model",
                 "prompt": json.dumps(atom.issue_execution.projection(old_binding, state["envelope_sha256"], "supervised"))}
        snapshot = {"state": {"orders": {oid: {"status": "active", "stages": [stage]}},
                              "pending_reviews": {oid: {}}}, "effect_ledger": []}
        cases = (([], True), ([{"status": "failed", "session_id": "old"}], True),
                 ([{"status": "failed", "session_id": "old"}, {"status": "failed", "session_id": "older"}], True),
                 ([{"status": "completed", "session_id": "old"}], False),
                 ([{"status": "failed", "session_id": "latest"}], False),
                 ([{"status": "cancelled", "session_id": "old"}], False))
        with patch.object(atom.issue_execution, "quiescent_order"), \
                patch.object(atom, "observe_prior_loop", return_value="running"):
            for history, valid in cases:
                stage["attempts"] = history + [{"status": "completed", "session_id": "latest"}]
                atom.save_json(self.root / ".noodle/state.snapshot.json", snapshot)
                with self.subTest(history=history):
                    if valid:
                        self.assertEqual(atom.verify_prior_atom(authorization)["order_id"], oid)
                    else:
                        with self.assertRaisesRegex(atom.AtomRefusal, "prior_review"):
                            atom.verify_prior_atom(authorization)
            self.assertEqual(paths["claim"].read_bytes(), retained)
            current["claim"].unlink()
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.prior_claim"):
                atom.verify_prior_atom(authorization)
            atom.save_json(current["claim"], {"repository": "ed3c/soodles", "subject": "ed3c/soodles#131",
                "head": self.base, "tree": tree, "base_head": self.base, "order_id": oid,
                "worktree_name": name, "worktree_path": str(worker), "session_id": "latest"})
            stage["attempts"] = [{"status": "completed", "session_id": "foreign"}]
            atom.save_json(self.root / ".noodle/state.snapshot.json", snapshot)
            with self.assertRaisesRegex(atom.AtomRefusal, "prior_review"):
                atom.verify_prior_atom(authorization)
            binding["body_sha256"] = "0" * 64
            atom.save_json(paths["envelope"], binding)
            state["envelope_sha256"] = atom.digest_file(paths["envelope"])
            atom.save_json(paths["state"], state)
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.prior_envelope.body_sha256"):
                atom.verify_prior_atom(authorization)

    def test_corrected_start_reuses_only_the_unchanged_parked_review(self):
        from unittest.mock import Mock
        paths, state = self.startup_fixture()
        envelope = atom.read_json(paths["envelope"], "envelope")
        order_id = envelope["execution"]["order_id"]
        snapshot = self.root / ".noodle/state.snapshot.json"
        atom.save_json(snapshot, {"state": {"orders": {order_id: {
            "status": "active", "stages": [{"status": "review"}]}},
            "pending_reviews": {order_id: {}}}, "effect_ledger": []})
        self.authorization["prior_atom"] = {"path": "/external/prior", "sha256": "a" * 64}
        # A new supervisor checkpoint may consume the original owner's
        # verified restored readback without copying a second success marker.
        self.assertNotIn("prior_host_recovery", state)
        prepared_path = paths["envelope"].parent / "prepared.json"
        prepared = atom.read_json(prepared_path, "prepared")
        prepared["process_argv"] = [self.authorization["noodle"]["path"], "--project-dir",
                                     str(self.root), "start", "--mode", "manual"]
        atom.save_json(prepared_path, prepared)
        state["admission_sha256"] = atom.digest_file(prepared_path)
        prior = {"order_id": order_id, "prior_loop_status": "restored",
                 "owner_snapshot_sha256": atom.digest_file(snapshot)}
        with patch.object(atom, "verify_prior_atom", return_value=prior), \
             patch.object(atom.subprocess, "Popen", return_value=Mock(pid=987655)) as spawn, \
             patch.object(atom.subprocess, "run", return_value=Mock(returncode=0)):
            result = atom.ensure_noodle(self.authorization, paths, state,
                                        {"action": "correction_review"}, self.env,
                                        correction=True)
        self.assertEqual(result["action"], "started")
        spawn.assert_called_once()
        self.assertEqual((self.root / ".noodle.toml").read_bytes(),
                         (paths["envelope"].parent / "noodle.toml").read_bytes())
        self.assertEqual(state["noodle_start"]["process_argv"], prepared["process_argv"])

    def test_corrected_start_refuses_missing_process_hold_before_any_effect(self):
        paths, state = self.startup_fixture()
        order_id = atom.read_json(paths["envelope"], "envelope")["execution"]["order_id"]
        snapshot = self.root / ".noodle/state.snapshot.json"
        atom.save_json(snapshot, {"state": {"orders": {order_id: {
            "status": "active", "stages": [{"status": "review"}]}},
            "pending_reviews": {order_id: {}}}, "effect_ledger": []})
        self.authorization["prior_atom"] = {"path": "/external/prior", "sha256": "a" * 64}
        state["prior_host_recovery"] = {"status": "restored"}
        prior = {"order_id": order_id, "prior_loop_status": "restored",
                 "owner_snapshot_sha256": atom.digest_file(snapshot)}
        with patch.object(atom, "verify_prior_atom", return_value=prior), \
             patch.object(atom.subprocess, "Popen") as spawn, \
             patch.object(atom.subprocess, "run",
                          return_value=subprocess.CompletedProcess(["git"], 0)):
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.start.correction_mode"):
                atom.ensure_noodle(self.authorization, paths, state,
                                   {"action": "correction_review"}, self.env,
                                   correction=True)
        spawn.assert_not_called()
        self.assertFalse((self.root / ".noodle.toml").exists())
        self.assertNotIn("noodle_start", state)

    def test_corrected_start_rejects_changed_original_review(self):
        paths, state = self.startup_fixture()
        envelope = atom.read_json(paths["envelope"], "envelope")
        order_id = envelope["execution"]["order_id"]
        snapshot = self.root / ".noodle/state.snapshot.json"
        atom.save_json(snapshot, {"state": {"orders": {order_id: {
            "status": "active", "stages": [{"status": "review"}]}},
            "pending_reviews": {order_id: {}}}, "effect_ledger": []})
        self.authorization["prior_atom"] = {"path": "/external/prior", "sha256": "a" * 64}
        state["prior_host_recovery"] = {"status": "restored"}
        prior = {"order_id": order_id, "prior_loop_status": "restored",
                 "owner_snapshot_sha256": "f" * 64}
        with patch.object(atom, "verify_prior_atom", return_value=prior), \
             patch.object(atom.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.start.prior_snapshot"):
                atom.ensure_noodle(self.authorization, paths, state,
                                   {"action": "correction_review"}, self.env,
                                   correction=True)
        spawn.assert_not_called()
        self.assertFalse((self.root / ".noodle.toml").exists())

    def test_correction_owner_checks_real_lock_pinned_bytes_and_foreign_control(self):
        import fcntl
        paths, state = self.startup_fixture()
        runtime = self.root / ".noodle"
        prepared_path = paths["envelope"].parent / "prepared.json"
        prepared = atom.read_json(prepared_path, "prepared")
        process_argv = [self.authorization["noodle"]["path"], "--project-dir", str(self.root),
                        "start", "--mode", "manual"]
        prepared["process_argv"] = process_argv
        atom.save_json(prepared_path, prepared)
        config = paths["envelope"].parent / "noodle.toml"
        (self.root / ".noodle.toml").write_bytes(config.read_bytes())
        state.update(admission_sha256=atom.digest_file(prepared_path), correction_ack_prefix="",
                     noodle_start={"status": "started", "pid": 424242,
                                   "argv": prepared["next"]["argv"], "process_argv": process_argv,
                                   "config_sha256": atom.digest_file(config)})
        with (runtime / "noodle.lock").open("a+b") as lock, patch.object(atom.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 0, " ".join(process_argv), "")):
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            binding, _ = atom.correction_owner(self.authorization, paths, state)
            self.assertIn("contract", binding)
            self.assertEqual(binding["issue_body"], self.fixture_issue_body())
            original_body = self.authorization["issue"]["body"]
            self.authorization["issue"]["body"] += "\nChanged body."
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.envelope.body_sha256"):
                atom.correction_owner(self.authorization, paths, state)
            self.authorization["issue"]["body"] = original_body
            ack = runtime / "control-ack.ndjson"
            ack.write_text('{"id":"foreign","action":"mode","status":"ok"}\n')
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.control.foreign"):
                atom.correction_owner(self.authorization, paths, state)
            ack.unlink()
            (self.root / ".noodle.toml").write_text("mode='auto'\n")
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.process.identity"):
                atom.correction_owner(self.authorization, paths, state)
        self.assertFalse((runtime / "control.ndjson").exists())

    def test_correction_lost_proposal_response_does_not_publish_again(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        atom.advance_correction(self.authorization, paths, state, Provider())
        self.correction_ack(state, "correction_review")
        stage["status"] = "failed"
        stage["attempts"][0]["status"] = "failed"
        owner["state"]["orders"][binding["execution"]["order_id"]]["status"] = "failed"
        owner["state"]["pending_reviews"] = {}
        def lost_after_offer(*args, before_publish, **kwargs):
            before_publish()
            raise OSError("lost response")
        with patch.object(atom.issue_execution, "supervised_correction",
                          side_effect=lost_after_offer) as propose:
            with self.assertRaisesRegex(OSError, "lost response"):
                atom.advance_correction(self.authorization, paths, state, Provider())
            resumed = atom.read_json(paths["state"], "state")
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.proposal.outcome"):
                atom.advance_correction(self.authorization, paths, resumed, Provider())
            propose.assert_called_once()
        self.assertNotIn("correction_release", resumed)

    def test_preflight_refusal_does_not_leave_an_offered_proposal(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        atom.advance_correction(self.authorization, paths, state, Provider())
        self.correction_ack(state, "correction_review")
        stage["status"] = "failed"
        stage["attempts"][0]["status"] = "failed"
        owner["state"]["orders"][binding["execution"]["order_id"]]["status"] = "failed"
        owner["state"]["pending_reviews"] = {}
        with patch.object(atom.issue_execution, "supervised_correction",
                          side_effect=atom.issue_admission.AdmissionRefusal(
                              "correction.foreign_orders", ["foreign"], "Noodle", "quiescent_noodle_owner")):
            with self.assertRaisesRegex(atom.AtomRefusal, "correction.foreign_orders"):
                atom.advance_correction(self.authorization, paths, state, Provider())
        self.assertNotIn("correction_proposal", state)
        self.assertNotIn("correction_proposal", atom.read_json(paths["state"], "state"))
        self.assertNotIn("correction_release", state)
        self.assertFalse((self.root / ".noodle/orders-next.json").exists())

    def correction_fixture(self):
        paths, state = self.startup_fixture()
        binding = atom.read_json(paths["envelope"], "envelope")
        binding["issue_body"] = self.fixture_issue_body()
        binding["contract"] = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        oid = binding["execution"]["order_id"]
        stage = {"status": "review", "prompt": json.dumps({"original": True}),
                 "skill": "execute", "provider": "codex", "model": "fixture-model",
                 "attempts": [{"session_id": "old-session", "status": "completed"}]}
        owner = {"state": {"orders": {oid: {"status": "active", "stages": [stage]}},
                           "mode": "supervised", "mode_epoch": 4, "pending_reviews": {oid: {}}},
                 "effect_ledger": []}
        state["correction_prior"] = {"order_id": oid, "worktree": binding["execution"]["worktree"],
            "worktree_path": str(self.root), "stage": json.loads(json.dumps(stage))}
        self.authorization["prior_publication"] = {"head": self.base}
        self.addCleanup(patch.stopall)
        patch.object(atom, "correction_owner", return_value=(binding, owner)).start()
        patch.object(atom.issue_execution, "quiescent_order").start()
        patch.object(atom, "verify_failed_prior").start()
        return paths, state, binding, owner, stage

    def correction_ack(self, state, name):
        runtime = self.root / ".noodle"
        command = state[name]
        with (runtime / "control-ack.ndjson").open("a") as stream:
            stream.write(json.dumps({"id": command["id"], "action": command["action"],
                                     "status": "ok"}) + "\n")
        (runtime / "control.ndjson").write_text("")

    def test_correction_chain_requires_transition_then_exact_promotion_before_release(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        provider = Provider()
        def publish(*args, before_publish, **kwargs):
            before_publish()
            return {"published": True}
        with patch.object(atom.issue_execution, "supervised_correction",
                          side_effect=publish) as propose:
            self.assertEqual(atom.advance_correction(self.authorization, paths, state, provider)
                             ["action"], "correction_review_pending")
            self.correction_ack(state, "correction_review")
            stage["status"] = "failed"
            stage["attempts"][0]["status"] = "failed"
            owner["state"]["orders"][binding["execution"]["order_id"]]["status"] = "failed"
            owner["state"]["pending_reviews"] = {}
            self.assertEqual(atom.advance_correction(self.authorization, paths, state, provider)
                             ["action"], "correction_proposal_pending")
            # Unobserved promotion must never append another proposal.
            atom.save_json(self.root / ".noodle/orders-next.json",
                           atom.issue_execution.correction_proposal(binding, state["envelope_sha256"]))
            atom.advance_correction(self.authorization, paths, state, provider)
            propose.assert_called_once()
            self.assertNotIn("correction_release", state)
            stage.update(status="pending", prompt=json.dumps(
                atom.issue_execution.projection(binding, state["envelope_sha256"], "supervised")))
            owner["state"]["orders"][binding["execution"]["order_id"]]["status"] = "active"
            self.assertEqual(atom.advance_correction(self.authorization, paths, state, provider)
                             ["action"], "correction_release_pending")
            self.assertNotIn("noodle_amendment", state)
            self.correction_ack(state, "correction_release")
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.release.transition"):
                atom.advance_correction(self.authorization, paths, state, provider)
            self.assertNotIn("noodle_amendment", state)
            owner["state"]["mode_epoch"] += 1
            self.assertEqual(atom.advance_correction(self.authorization, paths, state, provider)
                             ["action"], "correction_released")
            self.assertEqual(state["noodle_amendment"]["order_id"], binding["execution"]["order_id"])

    def test_correction_ack_without_state_change_refuses_without_proposal_or_resend(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        atom.advance_correction(self.authorization, paths, state, Provider())
        self.correction_ack(state, "correction_review")
        with patch.object(atom.issue_execution, "supervised_correction") as propose:
            with self.assertRaisesRegex(atom.AtomRefusal, "amendment.review.transition"):
                atom.advance_correction(self.authorization, paths, state, Provider())
            propose.assert_not_called()
        self.assertEqual((self.root / ".noodle/control.ndjson").read_text(), "")
        self.assertNotIn("correction_proposal", state)

    def test_correction_unknown_control_never_reappends_even_after_mailbox_disappears(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        atom.advance_correction(self.authorization, paths, state, Provider())
        (self.root / ".noodle/control.ndjson").unlink()
        # Reconstruct state from disk, as a fresh Session would.
        resumed = atom.read_json(paths["state"], "state")
        atom.advance_correction(self.authorization, paths, resumed, Provider())
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_correction_changed_review_refuses_before_control(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        stage["prompt"] = json.dumps({"foreign": True})
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.review.identity"):
            atom.advance_correction(self.authorization, paths, state, Provider())
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_correction_foreign_or_already_dispatched_promotion_cannot_release(self):
        paths, state, binding, owner, stage = self.correction_fixture()
        state["correction_failed_attempts"] = [{"session_id": "old-session", "status": "failed"}]
        state["correction_proposal"] = {"status": "offered", "envelope_sha256": state["envelope_sha256"]}
        stage.update(status="pending", prompt=json.dumps({"foreign": True}), attempts=[])
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.promotion"):
            atom.advance_correction(self.authorization, paths, state, Provider())
        stage.update(status="running", prompt=json.dumps(
            atom.issue_execution.projection(binding, state["envelope_sha256"], "supervised")))
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.promotion.hold"):
            atom.advance_correction(self.authorization, paths, state, Provider())
        self.assertNotIn("correction_release", state)
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_correction_control_rejects_unowned_ack_and_foreign_pending(self):
        paths, state = self.startup_fixture()
        command = {"id": "exact", "action": "request-changes", "order_id": "one"}
        runtime = self.root / ".noodle"
        (runtime / "control-ack.ndjson").write_text(json.dumps(
            {"id": "exact", "action": "request-changes", "status": "ok"}) + "\n")
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.control.ack"):
            atom.amendment_control(self.authorization, paths, state, "correction_review", command)
        (runtime / "control-ack.ndjson").unlink()
        (runtime / "control.ndjson").write_text('{"id":"foreign","action":"mode","value":"auto"}\n')
        with self.assertRaisesRegex(atom.AtomRefusal, "amendment.control.pending"):
            atom.amendment_control(self.authorization, paths, state, "correction_review", command)
        self.assertNotIn("correction_review", state)

    def test_fresh_root_bootstraps_with_pinned_noodle_before_admission(self):
        from unittest.mock import Mock
        provider = Provider()
        self.ready_issue(provider)
        real_run = subprocess.run
        real_popen = subprocess.Popen
        bootstrap_calls = []

        def run(argv, **kwargs):
            if isinstance(argv, list) and argv[-1:] == ["--once"]:
                bootstrap_calls.append(argv)
                state = atom.read_json(atom.artifact_paths(self.path)["state"], "state")
                self.assertEqual(state["noodle_bootstrap"]["status"], "offered")
                self.assertEqual(kwargs["cwd"], self.root)
                self.assertEqual((self.root / ".noodle.toml").read_bytes(),
                                 (atom.artifact_paths(self.path)["envelope"].parent
                                  / "bootstrap-noodle.toml").read_bytes())
                atom.save_json(self.root / ".noodle/state.snapshot.json",
                               {"state": {"orders": {}}, "effect_ledger": []})
                return Result(0)
            return real_run(argv, **kwargs)

        def popen(argv, *args, **kwargs):
            if isinstance(argv, list) and len(argv) == 1 and Path(argv[0]).name == "start-noodle":
                return Mock(pid=987654)
            return real_popen(argv, *args, **kwargs)

        with patch.object(atom.subprocess, "run", side_effect=run), \
                patch.object(atom.subprocess, "Popen", side_effect=popen):
            result = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(result["waiting_on"], "Noodle")
        self.assertEqual(len(bootstrap_calls), 1)
        self.assertEqual(bootstrap_calls[0][-1], "--once")
        self.assertEqual(provider.create_calls, 0)
        state = atom.read_json(atom.artifact_paths(self.path)["state"], "state")
        self.assertEqual(state["noodle_bootstrap"]["status"], "complete")
        self.assertEqual(state["noodle_start"]["status"], "started")

    def test_unknown_bootstrap_never_replays_and_preserves_owner_input(self):
        provider = Provider()
        self.ready_issue(provider)
        paths, state = self.startup_fixture()
        (self.root / ".noodle/state.snapshot.json").unlink()
        (self.root / ".noodle/issue-atom.lock").touch()
        calls = []
        real_run = subprocess.run

        def run(argv, **kwargs):
            if isinstance(argv, list) and argv[-1:] == ["--once"]:
                calls.append(argv)
                atom.save_json(self.root / ".noodle/state.snapshot.json",
                               {"state": {"orders": {}}, "effect_ledger": []})
                raise subprocess.TimeoutExpired(argv, 120)
            return real_run(argv, **kwargs)

        with patch.object(atom.subprocess, "run", side_effect=run):
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.bootstrap.outcome"):
                atom.bootstrap_noodle(self.authorization, paths, state, self.env)
            saved = atom.read_json(paths["state"], "state")
            self.assertEqual(saved["noodle_bootstrap"]["status"], "offered")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.bootstrap.outcome"):
                atom.bootstrap_noodle(self.authorization, paths, saved, self.env)
        self.assertEqual(len(calls), 1)
        self.assertTrue((self.root / ".noodle/state.snapshot.json").exists())

    def test_partial_runtime_refuses_bootstrap_before_noodle_start(self):
        paths, state = self.startup_fixture()
        (self.root / ".noodle/state.snapshot.json").unlink()
        (self.root / ".noodle/issue-atom.lock").touch()
        (self.root / ".noodle/foreign-owner").touch()
        with patch.object(atom.subprocess, "run") as run:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.bootstrap.runtime"):
                atom.bootstrap_noodle(self.authorization, paths, state, self.env)
        run.assert_not_called()

    def test_completed_bootstrap_config_restore_is_idempotent(self):
        paths, state = self.startup_fixture()
        prepared = atom.read_json(paths["envelope"].parent / "prepared.json", "prepared")
        (self.root / ".noodle/noodle.lock").touch()
        state["noodle_bootstrap"] = {
            "status": "exited_zero", "argv": prepared["bootstrap"]["argv"],
            "config_sha256": atom.digest_file(paths["envelope"].parent / "bootstrap-noodle.toml"),
            "original_config": None, "returncode": 0,
        }
        atom.save_json(paths["state"], state)
        with patch.object(atom.subprocess, "run") as run:
            atom.bootstrap_noodle(self.authorization, paths, state, self.env)
        self.assertEqual(state["noodle_bootstrap"]["status"], "complete")
        self.assertFalse((self.root / ".noodle.toml").exists())
        run.assert_not_called()

    def test_lost_start_response_cannot_spawn_again(self):
        paths, state = self.startup_fixture()
        from unittest.mock import Mock
        with patch.object(atom.subprocess, "Popen", side_effect=OSError("fixture lost start")) as start, \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=0)):
            with self.assertRaises(OSError):
                atom.ensure_noodle(self.authorization, paths, state, {"action": "proposal_pending"}, self.env)
            state = atom.read_json(paths["state"], "state")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.start.outcome"):
                atom.ensure_noodle(self.authorization, paths, state, {"action": "proposal_pending"}, self.env)
        self.assertEqual(start.call_count, 1)

    def test_existing_noodle_lock_adopts_only_exact_config_without_spawn(self):
        import fcntl
        paths, state = self.startup_fixture()
        config = self.root / ".noodle.toml"
        config.write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        with (self.root / ".noodle/noodle.lock").open("a+b") as lock, patch.object(atom.subprocess, "Popen") as start:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(atom.ensure_noodle(self.authorization, paths, state,
                                               {"action": "proposal_pending"}, self.env)["action"], "running")
            config.write_text("foreign = true\n")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.running.config"):
                atom.ensure_noodle(self.authorization, paths, state, {"action": "proposal_pending"}, self.env)
        start.assert_not_called()

    def test_configuration_and_owner_drift_refuse_before_start(self):
        paths, state = self.startup_fixture()
        with patch.object(atom.subprocess, "Popen") as start:
            (self.root / ".noodle.toml").write_text("retain = true\n")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.digest"):
                atom.ensure_noodle(self.authorization, paths, state, {"action": "proposal_pending"}, self.env)
            self.assertNotIn("noodle_start", state)
            self.assertEqual((self.root / ".noodle.toml").read_text(), "retain = true\n")
        start.assert_not_called()

    def test_changed_host_configuration_refuses_before_provider_write(self):
        (self.root / ".noodle.toml").write_text("unselected = true\n")
        provider = Provider()
        with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.digest"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 0)
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())

    def test_foreign_origin_suffix_refuses_before_provider_write(self):
        subprocess.run(["git", "remote", "set-url", "origin", "https://example.invalid/ed3c/soodles.git"],
                       cwd=self.root, check=True)
        provider = Provider()
        with self.assertRaisesRegex(atom.AtomRefusal, "git.origin"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 0)

    def test_completion_ack_required_before_shutdown(self):
        paths, state = self.startup_fixture()
        order_id = atom.read_json(paths["envelope"], "envelope")["execution"]["order_id"]
        state["noodle_completion"] = {"id": "exact", "action": "merge", "order_id": order_id}
        (self.root / ".noodle/control-ack.ndjson").write_text(json.dumps(
            {"id": "exact", "action": "merge", "status": "error"}) + "\n")
        with patch.object(atom.os, "kill") as kill:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.ack"):
                atom.finish_host(self.authorization, paths, state)
        kill.assert_not_called()

    def completion_fixture(self):
        paths, state = self.startup_fixture()
        order_id = atom.read_json(paths["envelope"], "envelope")["execution"]["order_id"]
        claim = {"order_id": order_id, "head": self.base, "tree": "exact-tree"}
        atom.save_json(paths["claim"], claim)
        atom.save_json(paths["landing"], {"phase": "reconciling", "writes_offered": ["merge", "close"],
                                         "claim": claim, "merge_sha": self.base})
        transition = {"next": {"owner": "Noodle", "known": {"order_id": order_id}}}
        owner = {"state": {"orders": {order_id: {"stages": [{"status": "failed"}]}}}}
        return paths, state, claim, transition, owner

    def test_completion_reconciles_original_order_without_merge_or_writer(self):
        paths, state, claim, transition, owner = self.completion_fixture()
        ack = {"id": "old-merge", "action": "merge", "status": "error", "message": "merge_failed"}
        state["noodle_completion"] = {"id": "old-merge", "action": "merge", "order_id": claim["order_id"]}
        ack_path = self.root / ".noodle/control-ack.ndjson"
        ack_path.write_text(json.dumps(ack) + "\n")
        with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                patch.object(atom.issue_execution, "quiescent_order"), \
                patch.object(atom.issue_execution, "completed_original_order", return_value={"order_id": claim["order_id"]}) as readback, \
                patch.object(atom, "finish_host", return_value=True) as stop, \
                patch.object(atom, "_git") as ancestry, \
                patch.object(atom.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{}', '')) as native:
            atom.complete_noodle(self.authorization, paths, state, transition)
            atom.complete_noodle(self.authorization, paths, state, transition)
        self.assertEqual(native.call_count, 1)
        self.assertEqual(native.call_args.args[0], [self.authorization["noodle"]["path"],
            "--project-dir", str(self.root), "publication", "reconcile", str(paths["claim"]),
            atom.digest_file(paths["claim"]), self.base])
        self.assertEqual(readback.call_count, 2)
        stop.assert_called_once_with(self.authorization, paths, state, stop_only=True)
        self.assertEqual(ancestry.call_count, 4)
        self.assertEqual(state["noodle_reconciliation"]["status"], "observed")
        self.assertEqual(json.loads(ack_path.read_text()), ack)
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_revision_reconciliation_uses_current_claim_path_hash_and_readback(self):
        paths, state, claim, transition, owner = self.completion_fixture()
        state["issue"] = {"number": 131}
        with typed_revision_receipts(self.path, state, self.outer / "revision") as current:
            atom.save_json(current["claim"], claim)
            atom.save_json(paths["claim"], {**claim, "head": "retained", "session_id": "old"})
            retained = paths["claim"].read_bytes()
            with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                    patch.object(atom.issue_execution, "quiescent_order"), \
                    patch.object(atom.issue_execution, "completed_original_order", return_value={}) as readback, \
                    patch.object(atom, "finish_host", return_value=True), \
                    patch.object(atom, "_git"), \
                    patch.object(atom.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{}', '')) as native:
                atom.complete_noodle(self.authorization, current, state, transition)
            self.assertEqual(native.call_args.args[0][-3:],
                             [str(current["claim"]), atom.digest_file(current["claim"]), self.base])
            self.assertEqual(readback.call_args.args[2], claim)
            self.assertEqual(current["landing"], paths["landing"])
            self.assertEqual(paths["claim"].read_bytes(), retained)
            current["claim"].unlink()
            with patch.object(atom, "_git"), patch.object(atom.subprocess, "run") as native:
                with self.assertRaisesRegex(atom.AtomRefusal, "publication.claim"):
                    atom.complete_noodle(self.authorization, current, state, transition)
            native.assert_not_called()

    def test_repair_hashes_and_validates_the_same_current_receipt_pair(self):
        paths, state = self.startup_fixture()
        state["issue"] = {"number": 131}
        with typed_revision_receipts(self.path, state, self.outer / "revision") as current:
            claim = {"head": "current", "worktree_path": str(self.root)}
            acceptance = {"candidate": {"head": "current"}}
            for key, value in (("claim", claim), ("acceptance", acceptance)):
                atom.save_json(current[key], value)
                atom.save_json(paths[key], {"head": "retained"})
            with patch("system_context.compile_repair", return_value={}), \
                    patch.object(atom.candidate_publication, "validate_inputs") as validate:
                controller = atom.repair_controller(self.authorization, state, paths, authorization_path=self.path)
                observed = controller.invariants()
            validate.assert_called_once_with(self.root, acceptance, claim)
            for key in ("claim", "acceptance"):
                self.assertEqual(observed["files"][key], atom.digest_file(current[key]))
                self.assertNotEqual(observed["files"][key], atom.digest_file(paths[key]))

    def test_reconciliation_waits_for_original_loop_shutdown(self):
        paths, state, _, transition, owner = self.completion_fixture()
        with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                patch.object(atom.issue_execution, "quiescent_order"), \
                patch.object(atom, "finish_host", return_value=False), \
                patch.object(atom, "_git"), patch.object(atom.subprocess, "run") as native:
            atom.complete_noodle(self.authorization, paths, state, transition)
        native.assert_not_called()
        self.assertNotIn("noodle_reconciliation", state)

    def test_reconciliation_rejects_changed_claim_or_unmerged_head_before_effect(self):
        paths, state, claim, transition, _ = self.completion_fixture()
        atom.save_json(paths["claim"], {**claim, "head": "f" * 40})
        with patch.object(atom, "finish_host") as stop:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.claim"):
                atom.complete_noodle(self.authorization, paths, state, transition)
            stop.assert_not_called()
        atom.save_json(paths["claim"], claim)
        with patch.object(atom, "_git", side_effect=atom.AtomRefusal("git", "not an ancestor")), \
                patch.object(atom, "finish_host") as stop:
            with self.assertRaisesRegex(atom.AtomRefusal, "not an ancestor"):
                atom.complete_noodle(self.authorization, paths, state, transition)
            stop.assert_not_called()
        self.assertNotIn("noodle_reconciliation", state)

    def test_lost_reconciliation_result_resumes_native_projection_after_canonical_completion(self):
        paths, state, claim, transition, owner = self.completion_fixture()
        with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                patch.object(atom.issue_execution, "quiescent_order"), \
                patch.object(atom, "finish_host", return_value=True), patch.object(atom, "_git"), \
                patch.object(atom.subprocess, "run", side_effect=subprocess.TimeoutExpired('reconcile', 30)) as native:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.process"):
                atom.complete_noodle(self.authorization, paths, state, transition)
            self.assertEqual(state["noodle_reconciliation"]["process"]["status"], "unknown")
            owner["state"]["orders"][claim["order_id"]]["status"] = "completed"
            native.side_effect = None
            native.return_value = subprocess.CompletedProcess([], 0, '{}', '')
            with patch.object(atom.issue_execution, "completed_original_order", return_value={"order_id": claim["order_id"]}):
                atom.complete_noodle(self.authorization, paths, state, transition)
        self.assertEqual(native.call_count, 2)
        self.assertEqual(native.call_args_list[0].args[0], native.call_args_list[1].args[0])
        self.assertEqual(state["noodle_reconciliation"]["status"], "observed")
        self.assertEqual(state["noodle_reconciliation"]["process"]["status"], "completed")

    def test_repair_diagnostic_gap_preserves_original_unknown_process_refusal(self):
        paths, state = self.startup_fixture()
        original = atom.AtomRefusal("noodle.completion.process", "TimeoutExpired",
                                   "selected_noodle_reconciler_readback")
        with patch.object(atom, "_run_owned", side_effect=original), \
                patch.object(atom, "repair_controller", side_effect=atom.AtomRefusal(
                    "repair.original_effect", "unresolved", "original_repair_owner_readback_without_retry")) as repair:
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom._run(self.path, environ=self.env, provider=Provider())
        self.assertIs(caught.exception, original)
        self.assertEqual(caught.exception.required, "selected_noodle_reconciler_readback")
        self.assertEqual(repair.call_args.kwargs['authorization_path'], self.path)

    def test_reconciliation_process_success_requires_canonical_completion(self):
        paths, state, _, transition, owner = self.completion_fixture()
        with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                patch.object(atom.issue_execution, "quiescent_order"), \
                patch.object(atom.issue_execution, "completed_original_order",
                             side_effect=atom.issue_admission.AdmissionRefusal("completion.order.status", "failed")), \
                patch.object(atom, "finish_host", return_value=True), patch.object(atom, "_git"), \
                patch.object(atom.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{}', '')):
            with self.assertRaisesRegex(atom.issue_admission.AdmissionRefusal, "completion.order.status"):
                atom.complete_noodle(self.authorization, paths, state, transition)
        self.assertEqual(state["noodle_reconciliation"]["status"], "offered")

    def test_completion_cannot_precede_provider_closure_or_select_another_order(self):
        paths, state = self.startup_fixture()
        order_id = atom.read_json(paths["envelope"], "envelope")["execution"]["order_id"]
        with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.owner"):
            atom.complete_noodle(self.authorization, paths, state,
                                 {"next": {"owner": "Noodle", "known": {"order_id": "foreign"}}})
        atom.save_json(paths["landing"], {"phase": "merged", "writes_offered": ["merge"]})
        with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.phase"):
            atom.complete_noodle(self.authorization, paths, state,
                                 {"next": {"owner": "Noodle", "known": {"order_id": order_id}}})
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_finish_host_restores_only_own_unchanged_configuration(self):
        from unittest.mock import Mock
        paths, state = self.startup_fixture()
        config = self.root / ".noodle.toml"
        config.write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        state["noodle_start"] = {"pid": 987654, "config_sha256": atom.digest_file(config), "original_config": None}
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom, "host_manager", return_value=manager), \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=1, stdout="")), \
                patch.object(atom.os, "killpg", side_effect=ProcessLookupError):
            self.assertTrue(atom.finish_host(self.authorization, paths, state))
            self.assertFalse(config.exists())
            self.assertTrue(state["noodle_start"]["restored"])
            self.assertTrue(atom.finish_host(self.authorization, paths, state))

    def test_stop_only_preserves_installed_config_and_failed_merge_ack(self):
        paths, state = self.startup_fixture()
        config = self.root / ".noodle.toml"
        config.write_bytes((paths["envelope"].parent / "noodle.toml").read_bytes())
        original = config.read_bytes()
        state["noodle_start"] = {"pid": 987654, "config_sha256": atom.digest_file(config),
                                 "original_config": None}
        state["noodle_completion"] = {"id": "old-merge", "action": "merge"}
        ack = {"id": "old-merge", "action": "merge", "status": "error"}
        ack_path = self.root / ".noodle/control-ack.ndjson"
        ack_path.write_text(json.dumps(ack) + "\n")
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom, "host_manager", return_value=manager), \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=1, stdout="")), \
                patch.object(atom.os, "killpg", side_effect=ProcessLookupError):
            self.assertTrue(atom.finish_host(self.authorization, paths, state, stop_only=True))
            self.assertEqual(config.read_bytes(), original)
            self.assertNotIn("restore_offered", state["noodle_start"])
            self.assertNotIn("owner_confirmed", state["host_finalization"]["facts"])
            state["noodle_reconciliation"] = {"status": "observed"}
            self.assertTrue(atom.finish_host(self.authorization, paths, state,
                                             landing={"classification": "RESOLVED"}))
        self.assertEqual(json.loads(ack_path.read_text()), ack)
        self.assertFalse(config.exists())
        self.assertTrue(state["noodle_start"]["restored"])

    def test_finish_host_refuses_recycled_pid_without_signalling(self):
        from unittest.mock import Mock
        paths, state = self.startup_fixture()
        state["noodle_start"] = {"pid": 987654}
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom, "host_manager", return_value=manager), \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=0, stdout="foreign-process")), \
                patch.object(atom.os, "kill") as kill:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.stop.identity"):
                atom.finish_host(self.authorization, paths, state)
        kill.assert_not_called()

    def test_host_manager_unknown_stop_is_not_reoffered_after_restart(self):
        paths, state = self.startup_fixture()
        state["noodle_start"] = {"pid": 987654}
        expected = " ".join(atom.noodle_process_argv(self.authorization, state["noodle_start"]))
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom.subprocess, "run", return_value=Mock(returncode=0, stdout=expected)), \
                patch.object(atom.os, "kill", side_effect=OSError("lost signal response")) as kill:
            with patch.object(atom, "host_manager", return_value=manager):
                with self.assertRaisesRegex(atom.AtomRefusal, "noodle.stop.outcome") as caught:
                    atom.finish_host(self.authorization, paths, state)
                self.assertEqual(atom.refusal_output(caught.exception, self.path)["next"]["argv"],
                                 atom.same_command(self.path))
                self.assertTrue(atom.read_json(paths["state"], "state")["noodle_start"]["stop_offered"])
                resumed = atom.schema_manager.Manager(manager.plan, manager.identity, state["host_finalization"])
            with patch.object(atom, "host_manager", return_value=resumed):
                self.assertFalse(atom.finish_host(self.authorization, paths, state))
        self.assertEqual(kill.call_count, 1)
        result = atom.response(state, self.path, waiting_on="Noodle shutdown readback")
        projection = result["host_finalization_projection"]
        self.assertEqual(result["next"], atom.response(
            {k: v for k, v in state.items() if k != "host_finalization"}, self.path)["next"])
        self.assertEqual(projection["required"], "original_owner_readback")
        self.assertEqual(projection["dag"]["stop"]["status"], "blocked")
        self.assertEqual(projection["facts"]["stop_offered"]["observation"]["value"], True)
        self.assertEqual(projection["facts"]["config_restored"]["status"], "unknown")
        self.assertNotIn("host_finalization_projection", atom.read_json(paths["state"], "state"))

    def test_host_manager_unknown_restore_refuses_without_second_write(self):
        paths, state = self.startup_fixture()
        config = self.root / ".noodle.toml"
        config.write_text("installed")
        state["noodle_start"] = {"pid": 987654, "config_sha256": atom.digest_file(config),
                                 "original_config": None}
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom, "host_manager", return_value=manager), \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=1, stdout="")), \
                patch.object(atom.os, "killpg", side_effect=ProcessLookupError):
            with patch.object(Path, "unlink", side_effect=OSError("lost write")) as write:
                with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.restore_outcome") as caught:
                    atom.finish_host(self.authorization, paths, state)
                self.assertEqual(atom.refusal_output(caught.exception, self.path)["next"]["argv"],
                                 atom.same_command(self.path))
                self.assertEqual(write.call_count, 1)
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.restore_outcome"):
                atom.finish_host(self.authorization, paths, state)
        self.assertEqual(config.read_text(), "installed")
        self.assertNotIn("repair", state)

    def test_host_manager_terminal_requires_physical_facts_and_landing(self):
        paths, state = self.startup_fixture()
        state["repair"] = {"fixture": "existing finite history stays unchanged", "used": {"actions": 3}}
        landing = {"classification": "RESOLVED", "next": None}
        self.assertTrue(atom.finish_host(self.authorization, paths, state))
        manager = atom.host_manager(self.authorization, state)
        self.assertNotEqual(manager.project()["status"], "complete")
        self.assertEqual(manager.project()["facts"]["landing_resolved"]["status"], "unknown")
        self.assertTrue(atom.finish_host(self.authorization, paths, state, landing=landing))
        self.assertEqual(atom.host_manager(self.authorization, state).project()["status"], "complete")
        (self.root / ".noodle.toml").write_text("foreign")
        with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.restored"):
            atom.finish_host(self.authorization, paths, state, landing=landing)
        self.assertNotEqual(atom.host_manager(self.authorization, state).project()["status"], "complete")
        self.assertNotIn("owner_confirmed", state["host_finalization"]["facts"])
        self.assertEqual(state["repair"]["used"], {"actions": 3})

    def test_pending_completion_without_consumer_keeps_named_owner_gap(self):
        paths, state = self.startup_fixture()
        state["noodle_completion"] = {"id": "original-completion", "action": "merge"}
        (self.root / ".noodle/control-ack.ndjson").write_text("")
        with patch.object(atom.os, "kill") as kill:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.ack") as caught:
                atom.finish_host(self.authorization, paths, state, landing={"classification": "RESOLVED"})
        result = atom.refusal_output(caught.exception, self.path)
        self.assertEqual(result["next"]["required"], ["current_noodle_owner_readback"])
        self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
        self.assertNotIn("host_finalization", state)
        kill.assert_not_called()

    def test_host_manager_preserves_group_lock_and_changed_config_refusals(self):
        import fcntl
        paths, state = self.startup_fixture()
        config = self.root / ".noodle.toml"
        config.write_text("installed")
        state["noodle_start"] = {"pid": 987654, "config_sha256": atom.digest_file(config),
                                 "original_config": None}
        manager = atom.host_manager(self.authorization, state)
        with patch.object(atom, "host_manager", return_value=manager), \
                patch.object(atom.subprocess, "run", return_value=Mock(returncode=1, stdout="")):
            with patch.object(atom.os, "killpg"):
                with self.assertRaisesRegex(atom.AtomRefusal, "noodle.stop.process_group"):
                    atom.finish_host(self.authorization, paths, state)
            with patch.object(atom.os, "killpg", side_effect=ProcessLookupError):
                with (self.root / ".noodle/noodle.lock").open("a+b") as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    with self.assertRaisesRegex(atom.AtomRefusal, "noodle.stop.owner"):
                        atom.finish_host(self.authorization, paths, state)
                config.write_text("foreign")
                with self.assertRaisesRegex(atom.AtomRefusal, "noodle.config.restore"):
                    atom.finish_host(self.authorization, paths, state)
        self.assertEqual(config.read_text(), "foreign")
        self.assertNotIn("restore_offered", state["noodle_start"])

    def test_live_owner_wait_does_not_ask_for_claim_or_take_over(self):
        provider = Provider()
        self.ready_issue(provider)
        with patch.object(atom.issue_execution, "supervised", return_value={"action": "running"}) as observe, \
                patch.object(atom, "_run_claim") as claim:
            result = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(result["waiting_on"], "Noodle")
        self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
        self.assertTrue(observe.call_args.kwargs["observe_live"])
        claim.assert_not_called()
        self.assertEqual(provider.create_calls, 0)

    def test_blocked_admission_stops_before_claim_or_cached_candidate_publication(self):
        provider = Provider()
        self.ready_issue(provider)
        blocked = {"message": {"outcome": "blocked", "message": "Missing admitted adapter"},
                   "session_id": "original-session", "attempt_id": "original-attempt",
                   "source": {"path": "/original/events.ndjson", "sha256": "a" * 64}}
        order_id = atom.issue_admission.scoped_order_id(131, self.root)
        observed = {"action": "blocked", "blocked": blocked,
                    "binding": {"execution": {"order_id": order_id}}}
        paths = atom.artifact_paths(self.path)
        with patch.object(atom.issue_execution, "supervised", return_value=observed), \
                patch.object(atom.issue_execution, "read_owner") as owner, \
                patch.object(atom, "_run_claim") as claim, \
                patch.object(atom, "_accept") as accept, \
                patch.object(atom.candidate_publication, "publish") as publish:
            for cached in (False, True):
                with self.subTest(cached=cached):
                    if cached:
                        atom.save_json(paths["claim"], {"head": "b" * 40})
                    with self.assertRaises(atom.AtomRefusal) as caught:
                        atom.run(self.path, environ=self.env, provider=provider)
                    receipt = atom.refusal_output(caught.exception, self.path)
                    self.assertEqual(receipt["invalid"]["field"], "noodle.stage.blocked")
                    self.assertEqual(receipt["next"]["owner"], "original-admission-owner")
                    self.assertEqual(receipt["next"]["known"]["blocked"], blocked)
                    self.assertEqual(receipt["next"]["known"]["order_id"], order_id)
            owner.assert_not_called()
            claim.assert_not_called()
            accept.assert_not_called()
            publish.assert_not_called()
        self.assertEqual(provider.merge_calls, 0)

    def test_failed_claim_stops_drive_before_wait_or_publication(self):
        provider = Provider()
        self.ready_issue(provider)
        sleep = Mock()
        with patch.object(atom.issue_execution, "supervised", return_value={"published": True}), \
                patch.object(atom, "_run_claim", return_value=Result(2, "terminal subject refusal")) as claim, \
                patch.object(atom, "_accept") as accept, \
                patch.object(atom.candidate_publication, "publish") as publish:
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.drive(self.path, timeout=2, sleep=sleep,
                           clock=iter((0, 0, 1, 2)).__next__,
                           environ=self.env, provider=provider)
        receipt = atom.refusal_output(caught.exception, self.path)
        self.assertEqual(receipt["status"], "refused")
        self.assertEqual(receipt["invalid"]["field"], "noodle.claim.exit")
        self.assertEqual(receipt["invalid"]["value"]["exit_status"], 2)
        self.assertEqual(receipt["next"]["kind"], "input")
        self.assertEqual(receipt["next"]["owner"], "Noodle")
        self.assertEqual(receipt["next"]["required"], ["fresh_noodle_claim"])
        self.assertEqual(receipt["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(receipt["next"]["known"]["order_id"],
                         atom.issue_admission.scoped_order_id(131, self.root))
        claim.assert_called_once()
        sleep.assert_not_called()
        accept.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(provider.create_calls, 0)
        self.assertEqual(provider.merge_calls, 0)

    def test_help_exposes_only_same_lifecycle_command(self):
        result = subprocess.run([str(Path(atom.__file__).parent / "issue-atom"), "--help"],
                                cwd=Path(atom.__file__).parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("authorization", result.stdout)
        self.assertIn("same command", result.stdout)

    def test_host_supplier_replaces_stale_parent_token(self):
        provider = Provider()
        self.ready_issue(provider)
        self.env["NOODLES_TOKEN_COMMAND"] = "printf fixture-installation-token"
        first, second = self.pending_patches()
        with first, second, patch.object(atom, "GitHubProvider", return_value=provider) as factory:
            result = atom.run(self.path, environ=self.env)
        factory.assert_called_once_with("ed3c/soodles", token="fixture-installation-token")
        self.assertEqual(result["waiting_on"], "Noodle")
        self.assertEqual(provider.create_calls, 0)

    def test_missing_supplier_leaves_no_new_checkpoint(self):
        self.env.pop("NOODLES_TOKEN_COMMAND")
        with self.assertRaises(atom.AtomRefusal) as caught:
            atom.run(self.path, environ=self.env)
        self.assertEqual(caught.exception.required, "provider_credential_profile.path")
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())

    def test_registered_missing_input_then_same_entry_reaches_admission(self):
        from test_provider_credential import HostRegistrationTests
        fixture = HostRegistrationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.env.pop("NOODLES_TOKEN_COMMAND")
        self.env.update(fixture.env)
        fixture.spec["app"].pop("installation_id")
        fixture.write_profile()
        with patch.object(atom, "GitHubProvider") as factory, \
                patch.object(atom.provider_credential, "supply_token") as supplier:
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.run(self.path, environ=self.env)
            receipt = atom.refusal_output(caught.exception, self.path)
            self.assertEqual(receipt["invalid"]["field"], "provider_credential_profile.app.installation_id")
            self.assertEqual(receipt["next"]["argv"], atom.same_command(self.path))
            factory.assert_not_called()
            supplier.assert_not_called()
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())
        fixture.spec["app"]["installation_id"] = "123"
        fixture.write_profile()
        provider = Provider()
        self.ready_issue(provider)
        first, second = self.pending_patches()
        fixture.supplier.write_text(fixture.supplier.read_text()
            .replace('["other"]', '["soodles"]')
            .replace('{"issues": "read"}', '{"actions": "read", "contents": "write", "issues": "write", "pull_requests": "write"}'))
        fixture.spec["supplier"]["sha256"] = atom.digest_file(fixture.supplier)
        fixture.write_profile()
        with first, second, patch.object(atom, "GitHubProvider", return_value=provider) as factory:
            result = atom.run(self.path, environ=self.env)
        factory.assert_called_once_with("ed3c/soodles", token="fixture-token")
        self.assertEqual(result["next"]["argv"], receipt["next"]["argv"])
        self.assertEqual(provider.create_calls, 0)
        public = json.dumps(result) + atom.artifact_paths(self.path)["state"].read_text()
        for secret in (str(fixture.supplier), str(fixture.key), "fixture-client", "fixture-token"):
            self.assertNotIn(secret, public)

    def test_dirty_control_root_still_refuses_before_supplier_or_provider(self):
        (self.root / "dirty").write_text("uncommitted")
        with patch.object(atom.provider_credential, "supply_token") as supplier, \
                patch.object(atom, "GitHubProvider") as provider:
            with self.assertRaisesRegex(atom.AtomRefusal, "git.status"):
                atom.run(self.path, environ=self.env)
            supplier.assert_not_called()
            provider.assert_not_called()
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())

    def test_invalid_authorization_precedes_profile_resolution(self):
        self.env["SOODLES_AUTHORIZATION_SHA256"] = "0" * 64
        with patch.object(atom.provider_credential, "resolve_host_environment") as resolver:
            with self.assertRaises(atom.AtomRefusal):
                atom.run(self.path, environ=self.env)
            resolver.assert_not_called()

    def test_lost_issue_create_adopts_exact_readback_and_never_recreates(self):
        provider = Provider()
        provider.create_unknown = True
        first, second = self.pending_patches()
        with first, second:
            result = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(result["waiting_on"], "Noodle")
        self.assertEqual(provider.create_calls, 1)
        first, second = self.pending_patches()
        with first, second:
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)

    def test_unknown_issue_create_without_effect_refuses_without_retry(self):
        provider = Provider()
        provider.create_unknown = True
        provider.create_effect = False
        with self.assertRaisesRegex(atom.AtomRefusal, "github.issue.outcome"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)
        with self.assertRaisesRegex(atom.AtomRefusal, "github.issue.outcome"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)

    def test_authorization_must_be_external_exact_and_clean(self):
        inside = self.root / "authorization.json"
        inside.write_bytes(self.path.read_bytes())
        digest = hashlib.sha256(inside.read_bytes()).hexdigest()
        with self.assertRaisesRegex(atom.AtomRefusal, "authorization.path"):
            atom.validate_authorization(inside, digest)
        (self.root / "dirty").write_text("dirty")
        with self.assertRaisesRegex(atom.AtomRefusal, "git.status"):
            atom.validate_authorization(self.path, self.digest)

    def test_unavailable_authorization_keeps_structured_same_entry_refusal(self):
        for source in (self.outer / "missing-authorization.json", self.outer):
            with self.subTest(source=source):
                with patch.object(atom, "_run") as lifecycle:
                    with self.assertRaises(atom.AtomRefusal) as caught:
                        atom.run(source, environ=self.env)
                    lifecycle.assert_not_called()
                self.assertEqual(caught.exception.invalid["field"], "authorization.path")
                command = [str(Path(atom.__file__).with_name("issue-atom")), "run", str(source)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt["status"], "refused")
                self.assertEqual(receipt["invalid"]["field"], "authorization.path")
                self.assertEqual(receipt["continuation_state"], "input_required")
                self.assertEqual(receipt["next"]["owner"], "external-supervisor")
                self.assertEqual(receipt["next"]["required"], ["readable_external_authorization"])
                self.assertEqual(receipt["next"]["argv"], command)
                self.assertIn("current authorized Local Session is the external supervisor",
                              receipt["next"]["reason"])
                self.assertFalse(receipt["authorizes_landing"])
                paths = atom.artifact_paths(source)
                self.assertFalse(paths["state"].exists())
                self.assertFalse(paths["directory"].exists())

    def test_unreadable_authorization_does_not_enter_lifecycle(self):
        with patch.object(Path, "open", side_effect=PermissionError), \
                patch.object(atom, "_run") as lifecycle:
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.run(self.path, environ=self.env)
        lifecycle.assert_not_called()
        self.assertEqual(caught.exception.invalid,
                         {"field": "authorization.path", "value": "PermissionError"})
        self.assertEqual(caught.exception.required, "readable_external_authorization")

    def test_provider_credentials_are_removed_from_child_environment(self):
        with patch.dict(os.environ, {"GH_TOKEN": "secret", "GITHUB_TOKEN": "other",
                                     "SAFE_VALUE": "kept"}, clear=True):
            child = atom.clean_child_env()
        self.assertNotIn("GH_TOKEN", child)
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertEqual(child["SAFE_VALUE"], "kept")

    def test_one_entry_routes_publication_landing_and_resolution(self):
        provider = Provider()
        self.ready_issue(provider)
        with patch.object(atom.issue_execution, "supervised", return_value={"action": "running"}):
            atom.run(self.path, environ=self.env, provider=provider)
        paths = atom.artifact_paths(self.path)
        state = atom.read_json(paths["state"], "fixture.state")
        current = self.enterContext(typed_revision_receipts(self.path, state, self.outer / "revision"))
        atom.save_json(paths["state"], state)
        for key in ("claim", "acceptance"):
            atom.save_json(paths[key], {"head": "retained"})
        retained = {key: paths[key].read_bytes() for key in ("claim", "acceptance")}
        claim = {
            "repository": "ed3c/soodles", "subject": "ed3c/soodles#131",
            "session_id": "fixture-session",
            "worktree_path": str(self.root),
            "worktree_name": atom.issue_admission.scoped_order_id(131, self.root) + "-0-execute",
            "head": "b" * 40, "tree": "c" * 40, "base_head": self.base,
        }

        def claim_ready(_authorization, _subject, output, order_id):
            self.assertEqual(output, current["claim"])
            self.assertEqual(order_id, atom.issue_admission.scoped_order_id(131, self.root))
            atom.save_json(output, claim, fresh=True)
            return Result(0)

        def accepted(_authorization, _claim, output):
            self.assertEqual(_claim, claim)
            self.assertEqual(output, current["acceptance"])
            value = {"repository": "ed3c/soodles",
                     "scope": "candidate runtime acceptance",
                     "candidate": {"head": "b" * 40, "tree": "c" * 40},
                     "authorizes_landing": False}
            atom.save_json(output, value, fresh=True)
            return value

        publication = {
            "pr": {"number": 132, "url": "https://github.com/ed3c/soodles/pull/132"},
            "branch": "soodles/issue-131-" + "b" * 12,
            "head": "b" * 40, "tree": "c" * 40, "authorizes_landing": False,
        }
        run = {"id": 7, "run_attempt": 1, "status": "completed",
               "head_sha": "b" * 40, "repository": {"full_name": "ed3c/soodles"}}
        jobs = {"jobs": []}

        def start(landing_claim, _snapshot, checkpoint):
            self.assertEqual(checkpoint, paths["landing"])
            self.assertEqual(landing_claim["head"], claim["head"])
            self.assertEqual(landing_claim["tree"], claim["tree"])
            atom.save_json(checkpoint, {"claim": landing_claim}, fresh=True)
            return {"action": "readback"}

        first_transition = {"action": "dispatch"}
        second_transition = {"action": "reconcile"}
        waiting = {"owner": "landing.advance", "action": "readback", "phase": "admitted",
                   "next": {"kind": "provider_readback", "owner": "GitHub",
                            "requests": {"pr": {"method": "GET", "url": "fixture://exact-pr"}}}}
        deadlock = {"owner": "landing.advance", "action": "readback", "phase": "admitted", "next": None}
        transitions = [first_transition, waiting, deadlock, second_transition]

        def advance(_checkpoint, _snapshot):
            return transitions.pop(0)

        dispatch = {"request": {"action": "merge", "pr_number": 132,
                                "expected_head_sha": "b" * 40, "merge_method": "merge"}}
        resolved = {"classification": "RESOLVED", "phase": "resolved", "next": None}
        # The packet fixture fixes admission history; cost still consumes its current paths.
        receipt_view = {"current": {"paths": current, "lineage": {
            "authorization_sha256": self.digest, "base_head": self.base,
            "sources": [{"path": str(self.path), "sha256": self.digest}]}}, "retained": []}
        patches = [
            patch("issue_atom.publication_receipt_view", return_value=receipt_view),
            patch("issue_atom.issue_execution.supervised", return_value={"published": True}),
            patch("issue_atom._run_claim", side_effect=claim_ready),
            patch("issue_atom._accept", side_effect=accepted),
            patch("issue_atom.validate_revision_publication"),
            patch("issue_atom.candidate_publication.publish", return_value=publication),
            patch("issue_atom.select_run", return_value=(run, jobs)),
            patch("issue_atom.provider_snapshot", return_value={"fixture": True}),
            patch("issue_atom.LandingOwner.start", side_effect=start),
            patch("issue_atom.LandingOwner.advance", side_effect=advance),
            patch("issue_atom.LandingOwner.dispatch", return_value=dispatch),
            patch("issue_atom.LandingOwner.reconcile", return_value=resolved),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        first = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(first["waiting_on"], "fresh provider readback")
        self.assertEqual(first["continuation_state"], "waiting")
        self.assertEqual(first["feedback"]["review_disposition"], "wait_for_owner_change")
        self.assertEqual(first["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(provider.merge_calls, 1)
        observed = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(observed["status"], "pending")
        self.assertEqual(observed["landing"], waiting)
        stopped = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(stopped["status"], "refused")
        self.assertEqual(stopped["repair"]["classification"], "no_legal_next")
        self.assertEqual(stopped["landing"], deadlock)
        self.assertEqual(stopped["continuation_state"], "unknown")
        self.assertEqual(stopped["feedback"]["review_disposition"], "owner_readback_required")
        self.assertEqual(provider.merge_calls, 1)
        second = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(second["status"], "resolved")
        self.assertEqual(second["continuation_state"], "complete")
        self.assertEqual(second["feedback"]["review_disposition"], "history_retained")
        self.assertIsNone(second["next"])
        self.assertFalse(second["authorizes_landing"])
        projection = second["host_finalization_projection"]
        self.assertEqual(projection["status"], "complete")
        self.assertEqual(projection["identity"], second["host_finalization"]["identity"])
        self.assertEqual(projection["facts"]["config_restored"]["observation"]["value"], True)
        self.assertEqual(projection["facts"]["owner_confirmed"]["observation"]["producer"],
                         "issue_atom.py:finish_host.confirm")
        self.assertEqual(projection["context"]["consumer"], "issue_atom.finish_host")
        self.assertEqual(second["cost"]["status"], "reported")
        cost_projection = second["cost"]["schema_projection"]
        self.assertEqual(cost_projection["hard_gate"]["status"], "resolved")
        self.assertEqual(cost_projection["hard_gate"]["host_finalization"], second["host_finalization"])
        self.assertEqual(cost_projection["hard_gate"]["repair_budget"], second["repair_budget"])
        self.assertFalse(cost_projection["authorizes_landing"])
        self.assertEqual(cost_projection["effects"], [])
        print(json.dumps({"event": "schema_plan_fields.owner_response", "response": second}, sort_keys=True))
        self.assertTrue(paths["landing"].exists())
        for key in ("claim", "acceptance"):
            self.assertEqual(paths[key].read_bytes(), retained[key])
        published = atom.candidate_publication.publish.call_args.args
        self.assertEqual(published[0], self.root)
        self.assertEqual(published[1], atom.read_json(current["acceptance"], "fixture.acceptance"))
        self.assertEqual(published[2], atom.read_json(current["claim"], "fixture.claim"))

    def test_owner_drift_refuses_before_provider_write_or_checkpoint(self):
        (self.owner_root / "landing.py").write_text("# drift\n")
        provider = Provider()
        with self.assertRaisesRegex(atom.AtomRefusal, "landing_owner.verifier_sha256"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 0)
        self.assertFalse(atom.artifact_paths(self.path)["state"].exists())

    def test_candidate_cannot_select_itself_as_landing_owner(self):
        self.authorization["landing_owner"] = {**self.owner_spec,
                                               "path": str(Path(atom.__file__).parent / "soodles.py")}
        with self.assertRaisesRegex(atom.AtomRefusal, "landing_owner.path"):
            atom.validate_landing_owner(self.authorization)

    def test_external_landing_process_identity(self):
        # Execute the selected, copied owner, not a patched candidate import.
        result = atom.LandingOwner(self.authorization, self.outer / "evidence").call("identity")
        self.assertEqual(result["verifier_sha256"], self.owner_spec["verifier_sha256"])
        self.assertEqual(len(list((self.outer / "evidence").glob("landing-identity-*.json"))), 1)

    def test_prewrite_external_activation_preserves_old_authorization(self):
        paths = atom.artifact_paths(self.path)
        paths["directory"].mkdir()
        atom.save_json(paths["directory"] / "landing-start-refused.json", {
            "argv": [sys.executable, "-B", self.owner_spec["path"], "landing", "start",
                     str(paths["directory"] / "landing-claim.json"),
                     str(paths["directory"] / "readback.json"), str(paths["landing"])],
            "exit_status": 1,
            "stdout": json.dumps({"owner": "landing.start", "status": "refused",
                                  "invalid": {"field": "envelope.execution.order_id"}}),
            "stderr": ""}, fresh=True)
        paths["envelope"].parent.mkdir()
        paths["envelope"].write_text("{}\n")
        original = self.path.read_bytes()
        native = {"head": "b" * 40, "tree": "c" * 40,
                  "base_head": self.base, "worktree_name": "soodles-131-local"}
        publication = {"pr": {"number": 132},
                       "branch": "soodles/issue-131-" + native["head"][:12]}
        run = {"id": 7, "run_attempt": 1}
        state = {"schema_version": 1, "authorization_sha256": self.digest,
                 "phase": "ci", "issue": {"number": 131},
                 "envelope_sha256": atom.digest_file(paths["envelope"])}
        atom.save_json(paths["state"], state, fresh=True)
        external = self.outer / "activation"
        external.mkdir()
        claim = {"repository": "ed3c/soodles", "issue": 131, "pr": 132,
                 "head": native["head"], "tree": native["tree"],
                 "base_head": self.base, "run_id": 7, "run_attempt": 1,
                 "worktree": native["worktree_name"],
                 "publication_branch": publication["branch"],
                 "control_root": str(self.root),
                 "verifier_sha256": self.owner_spec["verifier_sha256"],
                 "execution_envelope": {"path": str(paths["envelope"]),
                                        "sha256": state["envelope_sha256"]}}
        atom.save_json(external / "claim.json", claim, fresh=True)
        atom.save_json(external / "readback.json", {"fixture": True}, fresh=True)
        atom.save_json(external / "checkpoint.json", {
            "schema": 2, "claim": claim, "phase": "admitted",
            "writes_offered": [], "classification": None}, fresh=True)
        manifest = {"schema": 1, "publisher_root": str(self.owner_root),
                    "publisher_verifier_sha256": self.owner_spec["verifier_sha256"],
                    "route": "local", "claim_sha256": atom.digest_file(external / "claim.json"),
                    "readback_sha256": atom.digest_file(external / "readback.json"),
                    "authorizes_landing": False}
        atom.save_json(external / "manifest.json", manifest, fresh=True)
        selected = {"SOODLES_LANDING_ACTIVATION": str(external / "manifest.json"),
                    "SOODLES_LANDING_ACTIVATION_SHA256": atom.digest_file(external / "manifest.json")}
        owner = atom.external_landing_activation(
            self.authorization, state, paths, selected, native, publication, run)
        self.assertEqual(owner["landing_owner"], self.owner_spec)
        self.assertEqual(state["phase"], "landing")
        self.assertEqual(paths["landing"], external / "checkpoint.json")
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(atom.read_json(paths["state"], "state")["landing_activation"],
                         state["landing_activation"])
        atom.external_landing_activation(
            self.authorization, state, paths, {}, native, publication, run)

    def test_external_activation_rejects_offered_write(self):
        paths = atom.artifact_paths(self.path)
        paths["directory"].mkdir()
        atom.save_json(paths["directory"] / "landing-start-refused.json", {
            "argv": [sys.executable, "-B", self.owner_spec["path"], "landing", "start",
                     str(paths["directory"] / "landing-claim.json"),
                     str(paths["directory"] / "readback.json"), str(paths["landing"])],
            "exit_status": 1,
            "stdout": json.dumps({"owner": "landing.start", "status": "refused",
                                  "invalid": {"field": "envelope.execution.order_id"}}),
            "stderr": ""}, fresh=True)
        paths["envelope"].parent.mkdir()
        paths["envelope"].write_text("{}\n")
        state = {"phase": "ci", "issue": {"number": 131},
                 "envelope_sha256": atom.digest_file(paths["envelope"])}
        publication = {"pr": {"number": 132}, "branch": "soodles/issue-131-" + "b" * 12}
        native = {"head": "b" * 40, "tree": "c" * 40,
                  "base_head": self.base, "worktree_name": "soodles-131-local"}
        run = {"id": 7, "run_attempt": 1}
        external = self.outer / "activation"
        external.mkdir()
        claim = {"repository": "ed3c/soodles", "issue": 131, "pr": 132,
                 "head": native["head"], "tree": native["tree"],
                 "base_head": self.base, "run_id": 7, "run_attempt": 1,
                 "worktree": native["worktree_name"], "publication_branch": publication["branch"],
                 "control_root": str(self.root),
                 "verifier_sha256": self.owner_spec["verifier_sha256"],
                 "execution_envelope": {"path": str(paths["envelope"]),
                                        "sha256": state["envelope_sha256"]}}
        atom.save_json(external / "claim.json", claim, fresh=True)
        atom.save_json(external / "readback.json", {}, fresh=True)
        atom.save_json(external / "checkpoint.json", {"schema": 2, "claim": claim,
            "phase": "merge_pending", "writes_offered": ["merge"]}, fresh=True)
        atom.save_json(external / "manifest.json", {
            "schema": 1, "publisher_root": str(self.owner_root),
            "publisher_verifier_sha256": self.owner_spec["verifier_sha256"],
            "route": "local", "claim_sha256": atom.digest_file(external / "claim.json"),
            "readback_sha256": atom.digest_file(external / "readback.json"),
            "authorizes_landing": False}, fresh=True)
        selected = {"SOODLES_LANDING_ACTIVATION": str(external / "manifest.json"),
                    "SOODLES_LANDING_ACTIVATION_SHA256": atom.digest_file(external / "manifest.json")}
        with self.assertRaisesRegex(atom.AtomRefusal, "landing_activation.prewrite"):
            atom.external_landing_activation(
                self.authorization, state, paths, selected, native, publication, run)
        self.assertEqual(state["phase"], "ci")

    def postwrite_resume_fixture(self):
        paths = atom.artifact_paths(self.path)
        paths["directory"].mkdir()
        external = self.outer / "postwrite"
        external.mkdir()
        original = {"repository": "ed3c/soodles", "issue": 131, "pr": 132,
                    "head": "b" * 40, "tree": "c" * 40,
                    "base_head": self.base, "run_id": 7, "run_attempt": 1,
                    "worktree": "soodles-131-local",
                    "control_root": str(self.root),
                    "verifier_sha256": self.owner_spec["verifier_sha256"]}
        atom.save_json(external / "claim.json", original, fresh=True)
        checkpoint = external / "checkpoint.json"
        atom.save_json(checkpoint, {"schema": 2, "claim": original,
                       "phase": "awaiting_reconcile", "classification": None,
                       "writes_offered": ["merge", "close"],
                       "merge_sha": "d" * 40, "issue_closed_at": "now"}, fresh=True)
        paths["landing"] = checkpoint
        state = {"phase": "landing", "landing_activation": {"manifest": "pinned"}}
        atom.save_json(paths["state"], state, fresh=True)
        corrected_root = self.outer / "corrected-owner"
        hashes = {}
        for name in atom.OWNER_FILES:
            target = corrected_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.owner_root / name).read_bytes())
            if name == "landing.py":
                target.write_text(target.read_text() + "\n# corrected detached owner\n")
            hashes[name] = atom.digest_file(target)
        spec = {"path": str(corrected_root / "soodles.py"),
                "sha256": hashes["soodles.py"],
                "verifier_sha256": atom.digest_bytes(json.dumps(
                    hashes, sort_keys=True, separators=(",", ":")).encode())}
        descriptor = self.outer / "resume-owner.json"
        atom.save_json(descriptor, spec, fresh=True)
        selected = {"SOODLES_LANDING_RESUME_OWNER": str(descriptor),
                    "SOODLES_LANDING_RESUME_OWNER_SHA256": atom.digest_file(descriptor)}
        return state, paths, original, spec, selected

    def test_postwrite_resume_adopts_only_corrected_verifier(self):
        state, paths, original, spec, selected = self.postwrite_resume_fixture()
        authorization_before = self.path.read_bytes()
        calls = []
        def resume(_owner, checkpoint, claim_path):
            calls.append(str(checkpoint))
            claim = atom.read_json(claim_path, "claim")
            self.assertEqual(claim, {**original,
                                    "verifier_sha256": spec["verifier_sha256"]})
            saved = atom.read_json(checkpoint, "checkpoint")
            saved["claim"] = claim
            saved["prior_verifiers"] = [original["verifier_sha256"]]
            atom.save_json(checkpoint, saved)
            return {"owner": "landing.resume", "action": "reconcile"}
        with patch("issue_atom.LandingOwner.resume", autospec=True, side_effect=resume):
            corrected = atom.external_landing_resume(
                self.authorization, state, paths, selected)
        self.assertEqual(corrected["landing_owner"], spec)
        self.assertEqual(state["landing_resume"]["status"], "adopted")
        self.assertEqual(calls, [str(paths["landing"])])
        self.assertEqual(self.path.read_bytes(), authorization_before)
        with patch("issue_atom.LandingOwner.resume", side_effect=AssertionError("replayed")):
            atom.external_landing_resume(self.authorization, state, paths, {})

    def test_unknown_postwrite_resume_requires_readback_without_retry(self):
        state, paths, _, _, selected = self.postwrite_resume_fixture()
        with patch("issue_atom.LandingOwner.resume",
                   side_effect=atom.AtomRefusal("landing.owner", "lost response")):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing.owner"):
                atom.external_landing_resume(self.authorization, state, paths, selected)
        self.assertEqual(state["landing_resume"]["status"], "offered")
        with patch("issue_atom.LandingOwner.resume", side_effect=AssertionError("replayed")):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing_resume.outcome"):
                atom.external_landing_resume(self.authorization, state, paths, {})
        self.assertEqual(atom.read_json(paths["landing"], "checkpoint")["claim"]["verifier_sha256"],
                         self.owner_spec["verifier_sha256"])

    def test_changed_corrected_publisher_refuses_before_resume(self):
        state, paths, _, spec, selected = self.postwrite_resume_fixture()
        (Path(spec["path"]).parent / "landing.py").write_text("# drift\n")
        before = paths["landing"].read_bytes()
        with patch("issue_atom.LandingOwner.resume", side_effect=AssertionError("called")):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing_owner.verifier_sha256"):
                atom.external_landing_resume(self.authorization, state, paths, selected)
        self.assertEqual(paths["landing"].read_bytes(), before)
        self.assertNotIn("landing_resume", state)

    def test_timed_out_postwrite_resume_is_unknown(self):
        state, paths, _, _, selected = self.postwrite_resume_fixture()
        with patch("issue_atom.LandingOwner.resume",
                   side_effect=subprocess.TimeoutExpired(["landing", "resume"], 180)):
            with self.assertRaisesRegex(atom.AtomRefusal, "landing_resume.outcome"):
                atom.external_landing_resume(self.authorization, state, paths, selected)
        self.assertEqual(state["landing_resume"]["status"], "offered")
        self.assertEqual(atom.read_json(paths["landing"], "checkpoint")["phase"],
                         "awaiting_reconcile")


    def base_recovery_fixture(self):
        contract = atom.issue_admission.parse_contract(self.authorization["issue"]["body"])
        contract["frozen_paths"] = [{"path": "allowed.py", "revision": "head",
                                    "sha256": atom.digest_bytes(b"candidate\n")}]
        self.authorization["issue"]["body"] = ("<!-- soodles:execution-v1 -->\n```json\n" +
            json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->")
        self.path.write_text(json.dumps(self.authorization))
        self.digest = atom.digest_file(self.path)
        self.env["SOODLES_AUTHORIZATION_SHA256"] = self.digest
        paths, state = self.startup_fixture()
        binding = atom.read_json(paths["envelope"], "envelope")
        binding.update(contract=contract, issue_body=self.fixture_issue_body())
        oid, name = binding["execution"]["order_id"], binding["execution"]["worktree"]
        worktree = self.root / ".worktrees" / name
        atom._git(self.root, "worktree", "add", "-b", name, str(worktree), self.base)
        (worktree / "allowed.py").write_text("candidate\n")
        atom._git(worktree, "add", "allowed.py")
        atom._git(worktree, "commit", "-m", "candidate")
        head = atom._git(worktree, "rev-parse", "HEAD")
        target = atom._git(self.root, "commit-tree", self.base + "^{tree}", "-p", self.base, "-m", "provider advances")
        integration = atom._git(self.root, "commit-tree", head + "^{tree}", "-p", head, "-p", target, "-m", "integrate")
        session = "original-session"
        stage = {"stage_index": 0, "task_key": "execute", "skill": "execute", "provider": "codex",
            "model": "fixture-model", "runtime": "process", "status": "review",
            "prompt": json.dumps(atom.issue_execution.projection(binding, state["envelope_sha256"], "supervised")),
            "attempts": [{"attempt_id": "original-attempt", "session_id": session,
                          "status": "completed", "worktree_name": name}]}
        owner = {"state": {"orders": {oid: {"status": "active", "stages": [stage]}},
            "mode": "supervised", "mode_epoch": 4,
            "pending_reviews": {oid: {"order_id": oid, "stage_index": 0, "session_id": session,
                "worktree_name": name, "worktree_path": str(worktree)}}}, "effect_ledger": []}
        events = self.root / ".noodle/sessions" / session / "events.ndjson"
        events.parent.mkdir(parents=True)
        events.write_text(json.dumps({"type": "stage_message", "session_id": session,
            "payload": {"order_id": oid, "stage_index": 0, "outcome": "completed", "blocking": False}}) + "\n")
        config = paths["envelope"].parent / "noodle.toml"
        (self.root / ".noodle.toml").write_bytes(config.read_bytes())
        state.update(schema_version=1, issue={"number": 131, "url": "https://github.com/ed3c/soodles/issues/131"},
            publication=None, writes={"issue_create": {"status": "offered"}},
            noodle_start={"status": "started", "pid": 424242, "original_config": None,
                "argv": [str(config.parent / "start-noodle")], "config_sha256": atom.digest_file(config)})
        atom.save_json(self.root / ".noodle/state.snapshot.json", owner)
        atom.save_json(paths["state"], state)
        source = Path(atom.__file__).parent
        hashes = {name: atom.digest_file(source / name) for name in atom.LIFECYCLE_FILES}
        selected = {"path": str(source / "issue-atom"), "sha256": hashes["issue-atom"],
            "source_sha256": atom.digest_bytes(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode())}
        packet = {"schema": 1, "kind": "prepublication_base_recovery",
            "authorization": {"path": str(self.path), "sha256": self.digest},
            "original_envelope": {"path": str(paths["envelope"]), "sha256": state["envelope_sha256"]},
            "candidate_head": head, "target_base": target, "integration_head": integration,
            "lifecycle_owner": selected, "output": str(self.outer / "base-recovery")}
        descriptor = self.outer / "base-selection.json"
        atom.save_json(descriptor, packet)
        provider = Provider()
        self.ready_issue(provider)
        provider.repository_info = lambda: {"full_name": "ed3c/soodles", "default_branch": "main"}
        provider.base_head = lambda _: target
        self.addCleanup(patch.stopall)
        patch.object(atom.issue_execution, "quiescent_order", return_value=[]).start()
        patch.object(atom, "observe_prior_loop", return_value="running").start()
        return paths, state, binding, owner, packet, descriptor, provider

    def test_base_resume_preserves_identity_and_same_entry_dispatches_new_owner(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        raw = self.path.read_bytes()
        result = atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        self.assertEqual(result["continuation_state"], "ready")
        self.assertEqual(result["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(result["next"]["environment"], {"SOODLES_AUTHORIZATION_SHA256": self.digest})
        selected = atom.read_json(paths["state"], "state")
        self.assertEqual(selected["authorization_sha256"], self.digest)
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertIsNone(selected["publication"])
        self.assertEqual(atom._git(Path(packet["output"]).parent / "project", "rev-parse", "HEAD"), self.base)
        controller = Mock()
        with patch.object(atom, "repair_controller", return_value=controller), \
             patch.object(atom, "advance_base_recovery", return_value={"action": "base_hold_ack_pending"}) as advance, \
             patch.object(atom, "response", return_value={"status": "pending"}), \
             patch.object(atom, "_run_claim") as claim:
            atom.run(self.path, environ=result["next"]["environment"], provider=provider)
        advance.assert_called_once()
        claim.assert_not_called()
        atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        self.assertEqual(atom.read_json(paths["state"], "state"), selected)

    def test_base_selection_refuses_foreign_parent_scope_and_effect_before_adoption(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        for field, value in (("integration_head", packet["candidate_head"]), ("target_base", self.base)):
            changed = {**packet, field: value}
            atom.save_json(descriptor, changed)
            with self.subTest(field=field), self.assertRaises(atom.AtomRefusal):
                atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
            self.assertNotIn("base_recovery", atom.read_json(paths["state"], "state"))
        for invalid in ({key: value for key, value in packet.items() if key != "lifecycle_owner"},
                        {**packet, "replacement_judge": {}}):
            atom.save_json(descriptor, invalid)
            with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.selection"):
                atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
            self.assertNotIn("base_recovery", atom.read_json(paths["state"], "state"))
        atom.save_json(descriptor, packet)
        atom.save_json(paths["claim"], {"head": packet["candidate_head"]})
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.phase"):
            atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())

    def test_base_recovery_holds_review_then_stops_before_git_or_provider_effect(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        state = atom.read_json(paths["state"], "state")
        snapshot = self.root / ".noodle/state.snapshot.json"
        with patch.object(atom, "base_recovery_sync") as sync, patch.object(atom.os, "kill") as stop:
            self.assertEqual(atom.advance_base_recovery(self.authorization, paths, state, provider, self.env)["action"], "base_hold_ack_pending")
            self.correction_ack(state, "base_hold")
            owner["state"].update(mode="manual", mode_epoch=5)
            atom.save_json(snapshot, owner)
            self.assertEqual(atom.advance_base_recovery(self.authorization, paths, state, provider, self.env)["action"], "base_stop_readback_pending")
            self.assertNotIn("base_review", state)
            self.assertEqual(owner["state"]["orders"][binding["execution"]["order_id"]]["stages"][0]["status"], "review")
            stop.assert_called_once_with(424242, atom.signal.SIGTERM)
            sync.assert_not_called()
            with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.stop"):
                atom.advance_base_recovery(self.authorization, paths, state, provider, self.env)
            self.assertEqual(stop.call_count, 1)
        self.assertEqual(provider.value["body"], self.fixture_issue_body())

    def test_base_sync_adopts_exact_readback_and_never_repeats_unknown_effect(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        state["base_recovery"] = {"control_branch": "main"}
        with patch.object(atom.subprocess, "run", wraps=atom.subprocess.run) as run:
            atom.base_recovery_sync(self.authorization, paths, state, "control_sync", self.root, self.base, packet["target_base"])
            atom.base_recovery_sync(self.authorization, paths, state, "control_sync", self.root, self.base, packet["target_base"])
        effects = [call for call in run.call_args_list if call.args[0][:3] == ["git", "merge", "--ff-only"]]
        self.assertEqual(len(effects), 1)
        self.assertEqual(state["base_recovery"]["control_sync"]["status"], "observed")
        state["base_recovery"]["unknown"] = {"before": packet["target_base"], "after": packet["integration_head"],
            "root": str(self.root), "status": "offered"}
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.sync.outcome"):
            atom.base_recovery_sync(self.authorization, paths, state, "unknown", self.root, packet["target_base"], packet["integration_head"])
        self.assertEqual(atom._git(self.root, "rev-parse", "HEAD"), packet["target_base"])

    def test_base_publication_gate_rejects_original_completed_session(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        state = atom.read_json(paths["state"], "state")
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.publication"):
            atom.base_recovery_final(self.authorization, paths, state)
        state["base_recovery"]["released"] = True
        state["base_recovery"]["failed_stage"] = json.loads(json.dumps(owner["state"]["orders"][binding["execution"]["order_id"]]["stages"][0]))
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.successor"):
            atom.base_recovery_final(self.authorization, paths, state)
        self.assertNotIn("terminal", state["base_recovery"])


    def test_base_recovery_refuses_same_head_branch_drift_after_adoption(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        state = atom.read_json(paths["state"], "state")
        self.assertEqual(state["base_recovery"]["control_branch"], "main")
        atom._git(self.root, "checkout", "--detach", self.base)
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.control_branch"):
            atom.advance_base_recovery(self.authorization, paths, state, provider, self.env)
        self.assertFalse((self.root / ".noodle/control.ndjson").exists())
        self.assertEqual(atom._git(self.root, "rev-parse", "HEAD"), self.base)

    def test_base_sync_preserves_detached_control_root(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        atom._git(self.root, "checkout", "--detach", self.base)
        state["base_recovery"] = {"control_branch": None}
        self.assertIsNone(atom.base_recovery_branch(self.root))
        atom.base_recovery_sync(self.authorization, paths, state, "control_sync", self.root, self.base, packet["target_base"])
        self.assertIsNone(atom.base_recovery_branch(self.root))
        self.assertEqual(state["base_recovery"]["control_sync"]["process"]["exit_status"], 0)

    def test_base_completed_requires_exact_review_and_frozen_input(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        missing = json.loads(json.dumps(owner))
        missing["state"]["pending_reviews"] = {}
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.review.identity"):
            atom.base_recovery_completed(binding, missing)
        foreign = json.loads(json.dumps(owner))
        foreign["state"]["pending_reviews"][binding["execution"]["order_id"]]["session_id"] = "foreign-session"
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.review.identity"):
            atom.base_recovery_completed(binding, foreign)
        changed = json.loads(json.dumps(self.authorization))
        contract = atom.issue_admission.parse_contract(changed["issue"]["body"])
        contract["frozen_paths"][0]["sha256"] = "0" * 64
        changed["issue"]["body"] = changed["issue"]["body"].replace(atom.digest_bytes(b"candidate\n"), "0" * 64)
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.frozen"):
            atom.base_recovery_integration(changed, packet)

    def test_base_recovery_rebinds_then_releases_one_verified_new_successor(self):
        paths, state, binding, owner, packet, descriptor, provider = self.base_recovery_fixture()
        atom.resume(self.path, descriptor, atom.digest_file(descriptor), environ=self.env)
        state = atom.read_json(paths["state"], "state")
        snapshot = self.root / ".noodle/state.snapshot.json"
        oid = binding["execution"]["order_id"]
        order = owner["state"]["orders"][oid]
        stage = order["stages"][0]
        def advance():
            return atom.advance_base_recovery(self.authorization, paths, state, provider, self.env)
        self.assertEqual(advance()["action"], "base_hold_ack_pending")
        self.correction_ack(state, "base_hold")
        owner["state"].update(mode="manual", mode_epoch=5)
        atom.save_json(snapshot, owner)
        with patch.object(atom.os, "kill") as stop:
            self.assertEqual(advance()["action"], "base_stop_readback_pending")
        stop.assert_called_once()
        self.assertEqual(stage["status"], "review")
        updates = []
        def update(number, body):
            updates.append((number, body))
            raise atom.MutationUnknown("effect has no current readback")
        provider.update_issue_body = update
        actual_run = atom.subprocess.run
        def process_run(argv, *args, **kwargs):
            if argv[:3] == [self.authorization["noodle"]["path"], "worktree", "exec"]:
                self.assertEqual(kwargs["cwd"], self.authorization["control_root"])
                kwargs["cwd"] = self.root / ".worktrees" / argv[3]
                return actual_run(argv[4:], *args, **kwargs)
            return actual_run(argv, *args, **kwargs)
        (self.root / ".noodle/noodle.lock").touch()
        with patch.object(atom, "observe_prior_loop", return_value="stopped"), \
             patch.object(atom.subprocess, "run", side_effect=process_run):
            self.assertEqual(advance()["action"], "base_issue_readback_pending")
            with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.issue.outcome"):
                advance()
            self.assertEqual(len(updates), 1)
            provider.value["body"] = updates[0][1]
            self.assertEqual(advance()["action"], "base_bundle_prepared")
            self.assertEqual(len(updates), 1)
            prepared = state["base_recovery"]["prepared"]
            self.assertEqual(atom.digest_file(prepared["path"]), prepared["sha256"])
            actual_popen = atom.subprocess.Popen
            starts = []
            def start_process(argv, *args, **kwargs):
                if str(argv[0]).endswith("start-noodle"):
                    starts.append(argv)
                    return Mock(pid=424243)
                return actual_popen(argv, *args, **kwargs)
            with patch.object(atom.subprocess, "Popen", side_effect=start_process), \
                 patch.object(atom.issue_execution, "_absent_process"):
                self.assertEqual(advance()["action"], "started")
            self.assertEqual(len(starts), 1)
        effective, selected_paths = atom.base_recovery_projection(self.authorization, state, paths)
        new_binding = atom.issue_execution.context(selected_paths["envelope"], state["envelope_sha256"], self.root, lambda *_: provider.value)
        self.assertEqual(new_binding["base_head"], packet["target_base"])
        self.assertEqual(new_binding["execution"]["source_head"], packet["integration_head"])
        self.assertTrue(new_binding["execution"]["task"].startswith(self.authorization["task"]))
        self.assertIn("Do not apply the original patch again", new_binding["execution"]["task"])
        self.assertEqual(advance()["action"], "correction_review_pending")
        self.correction_ack(state, "correction_review")
        order["status"] = stage["status"] = "failed"
        stage["attempts"][0]["status"] = "failed"
        owner["state"]["pending_reviews"] = {}
        atom.save_json(snapshot, owner)
        self.assertEqual(advance()["action"], "correction_proposal_pending")
        self.assertTrue((self.root / ".noodle/orders-next.json").is_file())
        self.assertEqual(advance()["action"], "correction_proposal_pending")
        (self.root / ".noodle/orders-next.json").unlink()
        order["status"] = "active"
        stage["status"] = "pending"
        stage["prompt"] = json.dumps(atom.issue_execution.projection(new_binding, state["envelope_sha256"], "supervised"))
        atom.save_json(snapshot, owner)
        self.assertEqual(advance()["action"], "correction_release_pending")
        self.correction_ack(state, "correction_release")
        owner["state"].update(mode="supervised", mode_epoch=6)
        atom.save_json(snapshot, owner)
        self.assertEqual(advance()["action"], "correction_released")
        self.assertTrue(state["base_recovery"]["released"])
        with self.assertRaisesRegex(atom.AtomRefusal, "base_recovery.review"):
            atom.base_recovery_final(effective, selected_paths, state)
        session = "new-session"
        events = self.root / ".noodle/sessions" / session / "events.ndjson"
        events.parent.mkdir()
        events.write_text(json.dumps({"type": "stage_message", "session_id": session,
            "payload": {"order_id": oid, "stage_index": 0, "outcome": "completed", "blocking": False}}) + "\n")
        stage["status"] = "review"
        stage["attempts"].append({"attempt_id": "new-attempt", "session_id": session,
            "status": "completed", "worktree_name": binding["execution"]["worktree"]})
        owner["state"]["pending_reviews"] = {oid: {"order_id": oid, "stage_index": 0, "session_id": session,
            "worktree_name": binding["execution"]["worktree"],
            "worktree_path": str(self.root / ".worktrees" / binding["execution"]["worktree"])}}
        atom.save_json(snapshot, owner)
        atom.base_recovery_final(effective, selected_paths, state)
        self.assertEqual(state["base_recovery"]["terminal"]["stage"]["attempts"][-1]["session_id"], session)
        self.assertEqual(self.path.read_bytes(), json.dumps(self.authorization).encode())
        self.assertIsNone(state["publication"])


class PrewriteScopeRefusalTests(unittest.TestCase):
    def test_exact_prewrite_refusal_allows_correction_but_not_other_subject_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            prior_path = root / 'authorization.json'
            paths = atom.artifact_paths(prior_path)
            publisher = root / 'publisher/soodles.py'
            old = {'landing_owner': {'verifier_sha256': 'v' * 64}}
            atom.save_json(prior_path, old)
            authorization = {'prior_atom': {'path': str(prior_path),
                'sha256': atom.digest_file(prior_path)}, 'control_root': str(root / 'control'),
                'repository': 'ed3c/soodles', 'issue': {'number': 201}, 'base_head': 'b' * 40,
                'prior_publication': {'pr': {'number': 203}, 'head': 'h' * 40, 'tree': 't' * 40}}
            run = {'id': 1, 'run_attempt': 1}
            steps = [{'name': 'runtime preparation', 'status': 'completed', 'conclusion': 'skipped'}]
            jobs = {'jobs': [{'steps': steps}]}
            claim = {'repository': 'ed3c/soodles', 'issue': 201, 'pr': 203,
                'head': 'h' * 40, 'tree': 't' * 40, 'base_head': 'b' * 40,
                'run_id': 1, 'run_attempt': 1, 'verifier_sha256': 'v' * 64}
            claim_path = paths['directory'] / 'landing-claim.json'
            atom.save_json(claim_path, claim)
            result = {'owner': 'landing.start', 'status': 'refused',
                      'invalid': {'field': 'job.steps', 'value': steps}}
            record = {'exit_status': 1, 'stdout': json.dumps(result),
                'argv': [sys.executable, '-B', str(publisher), 'landing', 'start',
                         str(claim_path), str(paths['directory'] / 'readback.json'), str(paths['landing'])]}
            receipt = paths['directory'] / 'landing-start-fixture.json'
            atom.save_json(receipt, record)
            with patch.object(atom, 'validate_landing_owner', return_value=publisher):
                self.assertTrue(atom.prewrite_scope_refusal(authorization, run, jobs))
                self.assertFalse(atom.prewrite_scope_refusal(authorization, {**run, 'id': 2}, jobs))
                self.assertFalse(atom.prewrite_scope_refusal(authorization, run, {'jobs': []}))
                atom.save_json(claim_path, {**claim, 'head': 'x' * 40})
                self.assertFalse(atom.prewrite_scope_refusal(authorization, run, jobs))
                atom.save_json(claim_path, claim)
                atom.save_json(receipt, {**record, 'stdout': json.dumps({**result, 'request': {}})})
                self.assertFalse(atom.prewrite_scope_refusal(authorization, run, jobs))
                atom.save_json(receipt, record)
                atom.save_json(paths['landing'], {'phase': 'offered'})
                self.assertFalse(atom.prewrite_scope_refusal(authorization, run, jobs))
            self.assertFalse(atom.prewrite_scope_refusal({}, run, jobs))


if __name__ == "__main__":
    unittest.main()
