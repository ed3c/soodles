import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import issue_atom as atom


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

    def ready_issue(self, provider):
        body = self.authorization["issue"]["body"].rstrip() + "\n\n" + atom.marker(self.digest) + "\n"
        provider.value = {"number": 131, "title": self.authorization["issue"]["title"],
                          "body": body, "state": "open",
                          "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131",
                          "url": "https://api.github.com/repos/ed3c/soodles/issues/131"}

    def pending_patches(self):
        return (
            patch("issue_atom.issue_execution.supervised", return_value={"published": True}),
            patch("issue_atom._run_claim", return_value=Result(1, "order is not ready")),
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

    def test_fixed_external_shared_owner_controls(self):
        source = Path(atom.__file__).resolve().parent
        oracle = source / "docs/experiments/shared-owner-handoff/oracle.py"
        self.assertEqual(atom.digest_file(oracle),
                         "4691bc4dd03245ed667925de604b0c9637c333170f96bfc2b408db6fbe67021b")
        home = self.outer / "isolated-home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("NOODLE_")}
        env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "config"), TMPDIR="/private/tmp")
        output = self.outer / "fixed-controls"
        # The frozen consumer encodes the historical static order ID. Replay it
        # against its exact prior source; current scoped-ID behavior has live controls.
        historical = self.outer / "historical-source"
        historical.mkdir()
        archive = subprocess.check_output(["git", "archive",
            "95e8a3abddda8328d32f0ccf8011b463603d15b2"], cwd=source)
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            files.extractall(historical, filter="data")
        result = subprocess.run([sys.executable, "-B", str(oracle), str(historical), str(output)],
                                env=env, capture_output=True, text=True,
                                start_new_session=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads((output / "result.json").read_text())
        self.assertEqual(receipt["classification"], "GREEN", result.stdout + result.stderr)

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

    def test_projected_completed_order_can_continue_original_cleanup(self):
        import fcntl
        from test_issue_execution import IssueExecutionTests
        fixture = IssueExecutionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        session = fixture.archived_completion()
        config = b"fixture installed config\n"
        (fixture.root / ".noodle.toml").write_bytes(config)
        (fixture.path.parent / "noodle.toml").write_bytes(config)
        authorization = {"control_root": str(fixture.root), "repository": "ed3c/soodles",
                         "base_head": fixture.envelope["base_head"], "issue": {"body": fixture.issue["body"]}}
        state = {"phase": "landing", "issue": {"number": 18},
                 "envelope_sha256": fixture.pin, "noodle_completion": {"order_id": "soodles-18"}}
        with (fixture.runtime / "noodle.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atom.require_available_owner(authorization, {"envelope": fixture.path}, state)
            events = session / "events.ndjson"
            bad = json.loads(events.read_text())
            bad["payload"].update(outcome="blocked", blocking=True)
            events.write_text(json.dumps(bad) + "\n")
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.require_available_owner(authorization, {"envelope": fixture.path}, state)
        self.assertEqual(caught.exception.invalid["field"], "completion.typed_outcome")
        self.assertEqual(caught.exception.owner, "Noodle")

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

    def test_completion_uses_noodle_mailbox_once_and_preserves_error_ack(self):
        paths, state = self.startup_fixture()
        order_id = atom.read_json(paths["envelope"], "envelope")["execution"]["order_id"]
        atom.save_json(paths["landing"], {"phase": "reconciling", "writes_offered": ["merge", "close"],
                                         "claim": {"head": self.base}, "merge_sha": self.base})
        transition = {"next": {"owner": "Noodle", "known": {"order_id": order_id}}}
        owner = {"state": {"orders": {order_id: {"stages": [{"status": "review"}]}}}}
        with patch.object(atom.issue_execution, "read_owner", return_value=owner), \
                patch.object(atom.issue_execution, "quiescent_order"):
            atom.complete_noodle(self.authorization, paths, state, transition)
            atom.complete_noodle(self.authorization, paths, state, transition)
            lines = (self.root / ".noodle/control.ndjson").read_text().splitlines()
            self.assertEqual(len(lines), 1)
            command = json.loads(lines[0])
            self.assertEqual(command["action"], "merge")
            self.assertEqual(command["order_id"], order_id)
            ack = {"id": command["id"], "action": "merge", "status": "error", "message": "fixture refusal"}
            (self.root / ".noodle/control-ack.ndjson").write_text(json.dumps(ack) + "\n")
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.completion.ack"):
                atom.complete_noodle(self.authorization, paths, state, transition)
            self.assertEqual((self.root / ".noodle/control.ndjson").read_text().splitlines(), lines)

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
        with patch.object(atom.subprocess, "run", return_value=Mock(returncode=1, stdout="")), \
                patch.object(atom.os, "killpg", side_effect=ProcessLookupError):
            self.assertTrue(atom.finish_host(self.authorization, paths, state))
            self.assertFalse(config.exists())
            self.assertTrue(state["noodle_start"]["restored"])
            self.assertTrue(atom.finish_host(self.authorization, paths, state))

    def test_finish_host_refuses_recycled_pid_without_signalling(self):
        from unittest.mock import Mock
        paths, state = self.startup_fixture()
        state["noodle_start"] = {"pid": 987654}
        with patch.object(atom.subprocess, "run", return_value=Mock(returncode=0, stdout="foreign-process")), \
                patch.object(atom.os, "kill") as kill:
            with self.assertRaisesRegex(atom.AtomRefusal, "noodle.stop.identity"):
                atom.finish_host(self.authorization, paths, state)
        kill.assert_not_called()

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
        # Scope of the real supplier is exercised independently by the fixed CLI oracle.
        with first, second, patch.object(atom, "GitHubProvider", return_value=provider), \
                patch.object(atom.provider_credential, "supply_token", return_value="fixture-token") as supplier:
            result = atom.run(self.path, environ=self.env)
        resolved = supplier.call_args.kwargs["environ"]
        self.assertEqual(resolved["NOODLES_APP_INSTALLATION_ID"], "123")
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
        paths = atom.artifact_paths(self.path)
        claim = {
            "worktree_path": str(self.root),
            "worktree_name": atom.issue_admission.scoped_order_id(131, self.root) + "-0-execute",
            "head": "b" * 40, "tree": "c" * 40, "base_head": self.base,
        }

        def claim_ready(_authorization, _subject, output, order_id):
            self.assertEqual(order_id, atom.issue_admission.scoped_order_id(131, self.root))
            atom.save_json(output, claim, fresh=True)
            return Result(0)

        def accepted(_authorization, _claim, output):
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
        run = {"id": 7, "run_attempt": 1, "status": "completed"}
        jobs = {"jobs": []}

        def start(landing_claim, _snapshot, checkpoint):
            atom.save_json(checkpoint, {"claim": landing_claim}, fresh=True)
            return {"action": "readback"}

        first_transition = {"action": "dispatch"}
        second_transition = {"action": "reconcile"}
        transitions = [first_transition, second_transition]

        def advance(_checkpoint, _snapshot):
            return transitions.pop(0)

        dispatch = {"request": {"action": "merge", "pr_number": 132,
                                "expected_head_sha": "b" * 40, "merge_method": "merge"}}
        resolved = {"classification": "RESOLVED", "phase": "resolved", "next": None}
        patches = [
            patch("issue_atom.issue_execution.supervised", return_value={"published": True}),
            patch("issue_atom._run_claim", side_effect=claim_ready),
            patch("issue_atom._accept", side_effect=accepted),
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
        self.assertEqual(first["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(provider.merge_calls, 1)
        second = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(second["status"], "resolved")
        self.assertIsNone(second["next"])
        self.assertFalse(second["authorizes_landing"])
        self.assertTrue(paths["landing"].exists())

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


if __name__ == "__main__":
    unittest.main()
