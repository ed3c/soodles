import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import candidate_publication
import issue_admission
import issue_atom
import issue_execution
import landing
import next_issue
import provider_readback
import repository_binding
import schema_manager
import supervisor_admission
import test_manager


class GenericBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.outer = Path(self.temporary.name).resolve()
        self.source = Path(issue_atom.__file__).parent
        self.runtime = self.outer / "runtime"
        self.publisher = self.outer / "publisher"
        for directory, names in ((self.runtime, issue_atom.GENERIC_LIFECYCLE_FILES),
                                 (self.publisher, issue_atom.OWNER_FILES)):
            for name in names:
                target = directory / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((self.source / name).read_bytes())
                target.chmod((self.source / name).stat().st_mode & 0o777)
        self.binary = self.outer / "carrier"
        self.binary.write_text("#!" + sys.executable + "\n" +
            "import json,pathlib,sys\n"
            "args=sys.argv\n"
            "if 'event' in args:\n"
            " root=pathlib.Path(args[args.index('--project-dir')+1])\n"
            " session=args[args.index('--session')+1]\n"
            " payload=json.loads(args[args.index('--payload')+1])\n"
            " path=root/'.noodle/sessions'/session/'events.ndjson'\n"
            " with path.open('a') as out: out.write(json.dumps({'type':'stage_message','session_id':session,'payload':payload})+'\\n')\n")
        self.binary.chmod(0o755)
        self.carrier = {"platform": platform.system().lower() + "_" + platform.machine().lower(),
            "noodle": self.ref(self.binary), "codex": {**self.ref(self.binary), "model": "fixture",
                "argv": ["exec", "--skip-git-repo-check", "--json", "--model", "fixture"]}}

    def ref(self, path):
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def git(self, root, *args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
            env={**os.environ, "GIT_AUTHOR_DATE": "2026-10-03T00:00:00Z",
                 "GIT_COMMITTER_DATE": "2026-10-03T00:00:00Z"})
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def target(self, repository="example/first-target", branch="trunk"):
        root = self.outer / repository.split("/")[1]
        root.mkdir()
        self.git(root, "init", "-b", branch)
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "remote", "add", "origin", "https://github.com/" + repository + ".git")
        (root / ".gitignore").write_text(".noodle/\n.worktrees/\n.noodle.toml\n")
        (root / "AGENTS.md").write_text("Change only the admitted target file.\n")
        (root / "target.py").write_text("print('target')\n")
        workflow = root / ".github/workflows/target.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: target\non: pull_request\njobs:\n  unit:\n    steps:\n      - name: Target tests\n        run: python3 target.py\n  lint:\n    steps:\n      - name: Target lint\n        run: python3 target.py\n")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "Provide target fixture inputs")
        head = self.git(root, "rev-parse", "HEAD")
        self.git(root, "update-ref", "refs/remotes/origin/" + branch, head)
        self.git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/" + branch)
        contract = {"schema": 3, "trigger": "fixture", "source": "fixture", "owner": "target owner",
            "changes": ["target correction"], "write_paths": ["target.py", "evidence.json"],
            "behavior": ["target command"], "defect_controls": ["target command"],
            "non_cases": ["provider effects"], "dependencies": [], "acceptance": "selected target checks",
            "delivery": "existing owner", "reconciliation": "existing owner", "feature_scope": "fixture",
            "required_paths": ["target.py", "evidence.json"], "evidence_manifest": "evidence.json",
            "base_head": head, "frozen_paths": [{"path": "target.py", "revision": "base",
                                                   "sha256": self.ref(root / "target.py")["sha256"]}]}
        body = "<!-- soodles:execution-v1 -->\n```json\n" + json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->"
        binding = {"schema": 1, "repository": repository, "base_ref": branch,
            "workflow_path": ".github/workflows/target.yml",
            "jobs": {"unit": ["Target tests"], "lint": ["Target lint"]},
            "verification": {"owner": "target test owner", "paths": contract["write_paths"],
                             "commands": [[sys.executable, "-B", "target.py"]]}}
        path = self.outer / (root.name + "-binding.json")
        path.write_text(json.dumps(binding))
        def hashes(directory, names):
            return {name: self.ref(directory / name)["sha256"] for name in names}
        def closure(directory, names):
            return hashlib.sha256(json.dumps(hashes(directory, names), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        selection = {"schema": 1, "repository": repository, "control_root": str(root),
            "issue": {"title": "Target fixture", "body": body, "number": 7}, "task": "Correct the target",
            "carrier": self.carrier, "instruction_paths": ["AGENTS.md"], "target_binding": self.ref(path),
            "lifecycle_owner": {**self.ref(self.runtime / "issue-atom"),
                                "source_sha256": closure(self.runtime, issue_atom.GENERIC_LIFECYCLE_FILES)},
            "landing_owner": {**self.ref(self.publisher / "soodles.py"),
                              "verifier_sha256": closure(self.publisher, issue_atom.OWNER_FILES)}}
        return root, selection, binding

    def authorize(self, selection, name="prepared"):
        path = self.outer / (name + "-selection.json")
        path.write_text(json.dumps(selection))
        return supervisor_admission.authorize(str(path), self.ref(path)["sha256"], str(self.outer / name))

    def prepared_target(self):
        root, selection, _ = self.target()
        receipt = self.authorize(selection)
        authorization = json.loads(Path(receipt["authorization"]["path"]).read_text())
        repo = selection["repository"]
        issue = {**selection["issue"], "state": "open", "updated_at": "2026-10-03T00:00:00Z",
                 "url": f"https://api.github.com/repos/{repo}/issues/7",
                 "html_url": f"https://github.com/{repo}/issues/7"}
        output = self.outer / "admission"
        supervisor_admission.prepare(issue, self.carrier, root, output,
            environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"],
            instruction_pins=authorization["instruction_pins"])
        envelope = json.loads((output / "envelope.json").read_text())
        worktree = root / ".worktrees" / envelope["execution"]["worktree"]
        self.git(root, "worktree", "add", "-b", worktree.name, str(worktree))
        return root, selection, authorization, issue, output, envelope, worktree

    def test_generic_interruption_rebinds_entries_to_current_bundle(self):
        root, selection, _, issue, original, envelope, worktree = self.prepared_target()
        execution = envelope["execution"]
        reference = self.ref(original / "envelope.json")
        subject = selection["repository"] + "#7"
        recovery = {"kind": "prepublication_interruption", "original_envelope": reference,
            "custody_sha256": "a" * 64,
            "custody": {"order_id": execution["order_id"], "stage_index": 0, "subject": subject,
                "envelope_sha256": reference["sha256"], "worktree_name": worktree.name,
                "worktree_path": str(worktree), "branch": worktree.name, "head": execution["source_head"]},
            "evidence_path": str(root / ".noodle/interruptions" / hashlib.sha256(
                (execution["order_id"] + "\n" + subject).encode()).hexdigest())}
        (worktree / "target.py").write_text("retained dirty progress\n")
        output = self.outer / "recovery"
        result = supervisor_admission.prepare(issue, self.carrier, root, output,
            environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True, correction=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"], recovery_context=recovery)
        actual = issue_admission.load_external_envelope(output / "envelope.json", result["envelope_sha256"], root)
        self.assertEqual(issue_admission.validate_recovery_context(actual), envelope)
        self.assertEqual(actual["execution"]["runtime"], {
            "stage_outcome_argv": [str(output / "stage-outcome")], "test_argv": [str(output / "test")]})
        self.assertEqual((worktree / "target.py").read_text(), "retained dirty progress\n")
        actual["execution"]["runtime"] = execution["runtime"]
        (output / "envelope.json").write_text(json.dumps(actual))
        with self.assertRaisesRegex(issue_admission.AdmissionRefusal, "envelope.runtime.bundle"):
            issue_admission.load_external_envelope(output / "envelope.json", self.ref(output / "envelope.json")["sha256"], root)

    def test_generic_revision_preserves_instructions_and_rebinds_entries(self):
        root, selection, _, issue, original, envelope, worktree = self.prepared_target()
        execution = envelope["execution"]
        (root / "base.txt").write_text("selected provider base\n")
        self.git(root, "add", "base.txt")
        self.git(root, "commit", "-m", "Advance the fixture provider base")
        target = self.git(root, "rev-parse", "HEAD")
        contract = issue_admission.parse_contract(issue["body"])
        contract["base_head"] = target
        issue["body"] = "<!-- soodles:execution-v1 -->\n```json\n" + json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->"
        history = self.outer / "terminal.ndjson"
        history.write_text(json.dumps({"outcome": "completed"}))
        accepted = self.outer / "native.json"
        accepted.write_text(json.dumps({"schema": 1, "issue": 106, "accepted_at": "fixture",
            "binary": self.ref(self.binary), "acceptance": self.ref(history), "interface": self.ref(history)}))
        entry = {"schema": 1, "kind": "base_advance", "original_envelope": self.ref(original / "envelope.json"),
            "selection_sha256": "b" * 64, "candidate_head": execution["source_head"],
            "candidate_tree": self.git(worktree, "rev-parse", "HEAD^{tree}"), "old_base": envelope["base_head"],
            "target_base": target, "terminal": {"source": self.ref(history), "message": {"outcome": "completed"}},
            "prior_attempts": [], "native_acceptance": self.ref(accepted),
            **{key: execution[key] for key in ("order_id", "stage_index", "worktree")}}
        output = self.outer / "revision"
        options = dict(environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True, correction=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"], revision_entry=entry)
        result = supervisor_admission.prepare(issue, self.carrier, root, output, **options)
        self.assertEqual(supervisor_admission.prepare(issue, self.carrier, root, output, readback=True, **options), result)
        actual = issue_admission.load_external_envelope(output / "envelope.json", result["envelope_sha256"], root)
        bound = issue_execution.revision_context(actual, self.ref(output / "revision-entry.json"), result["envelope_sha256"])
        self.assertEqual(bound["execution"]["instruction_context"], execution["instruction_context"])
        self.assertEqual(bound["target_binding"], selection["target_binding"])
        self.assertEqual(bound["execution"]["runtime"]["test_argv"], [str(output / "test")])
        changed = copy.deepcopy(actual)
        changed["target_binding"] = {**selection["target_binding"], "sha256": "f" * 64}
        with self.assertRaisesRegex(issue_admission.AdmissionRefusal, "revision.entry.target_binding"):
            issue_execution.revision_context(changed, self.ref(output / "revision-entry.json"), result["envelope_sha256"])

    def test_original_generic_repair_closure_uses_pinned_source(self):
        _, selection, _ = self.target()
        receipt = self.authorize(selection)
        authorization = json.loads(Path(receipt["authorization"]["path"]).read_text())
        policy, _, identity = issue_atom.original_repair_source(authorization)
        self.assertEqual(identity, issue_atom.repair_binding(authorization, policy, source_root=self.runtime))
        with patch.object(issue_atom, "LIFECYCLE_FILES", ("new-only.py",)), \
                patch.object(issue_atom, "GENERIC_LIFECYCLE_FILES", ("other-only.py",)):
            self.assertEqual(issue_atom.original_repair_source(authorization)[2], identity)
        (self.runtime / ".agents/skills/execute/SKILL.md").write_text("changed generic-only bytes")
        with self.assertRaises(issue_atom.AtomRefusal):
            issue_atom.original_repair_source(authorization)
        with self.assertRaises(issue_atom.AtomRefusal):
            issue_atom.literal_lifecycle_files(b"LIFECYCLE_FILES = ('a',)\nGENERIC_LIFECYCLE_FILES = dangerous()", generic=True)

    def test_two_targets_authorize_and_prepare_without_factory_files(self):
        for index, (repo, branch) in enumerate((("example/first-target", "trunk"), ("other/second-target", "stable"))):
            root, selection, binding = self.target(repo, branch)
            receipt = self.authorize(selection, "prepared-" + str(index))
            self.assertEqual(self.authorize(selection, "prepared-" + str(index)), receipt)
            authorization = json.loads(Path(receipt["authorization"]["path"]).read_text())
            self.assertEqual(authorization["workflow"], {"path": binding["workflow_path"], "jobs": binding["jobs"]})
            self.assertEqual(receipt["next"]["argv"][0], str(self.runtime / "issue-atom"))
            issue = {**selection["issue"], "state": "open", "updated_at": "2026-10-03T00:00:00Z",
                     "url": f"https://api.github.com/repos/{repo}/issues/7",
                     "html_url": f"https://github.com/{repo}/issues/7"}
            result = supervisor_admission.prepare(issue, self.carrier, root, self.outer / ("admission-" + str(index)),
                environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True,
                runtime_root=self.runtime, target_binding=selection["target_binding"],
                instruction_pins=authorization["instruction_pins"])
            envelope = json.loads((Path(result["bundle"]) / "envelope.json").read_text())
            self.assertEqual(issue_admission.validate_issue(issue, envelope)["target_binding"], selection["target_binding"])
            self.assertTrue(Path(envelope["execution"]["runtime"]["stage_outcome_argv"][0]).is_file())
            self.assertFalse(any((root / name).exists() for name in ("issue-atom", "soodles.py", "stage-outcome", "tests")))

    def test_binding_tampering_refuses_before_authorization(self):
        root, selection, _ = self.target()
        Path(selection["target_binding"]["path"]).write_text("{}")
        with self.assertRaises(issue_admission.AdmissionRefusal):
            self.authorize(selection)
        self.assertFalse((self.outer / "prepared").exists())

    def test_runtime_tampering_refuses_before_authorization(self):
        _, selection, _ = self.target()
        (self.runtime / "stage_outcome.py").write_text("raise RuntimeError('wrong runtime')\n")
        with self.assertRaises(issue_atom.AtomRefusal):
            self.authorize(selection)
        self.assertFalse((self.outer / "prepared").exists())

    def test_external_worker_test_and_outcome_entries_bind_the_original_owner(self):
        root, selection, _ = self.target()
        receipt = self.authorize(selection)
        authorization = json.loads(Path(receipt["authorization"]["path"]).read_text())
        repo = selection["repository"]
        issue = {**selection["issue"], "state": "open", "updated_at": "2026-10-03T00:00:00Z",
                 "url": f"https://api.github.com/repos/{repo}/issues/7",
                 "html_url": f"https://github.com/{repo}/issues/7"}
        output = self.outer / "admission"
        prepared = supervisor_admission.prepare(issue, self.carrier, root, output,
            environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"],
            instruction_pins=authorization["instruction_pins"])
        envelope = json.loads((output / "envelope.json").read_text())
        execution = envelope["execution"]
        worktree = root / ".worktrees" / execution["worktree"]
        self.git(root, "worktree", "add", "-b", execution["worktree"], str(worktree))
        binding = issue_admission.validate_issue(issue, envelope)
        session = "generic-fixture-session"
        session_dir = root / ".noodle/sessions" / session
        session_dir.mkdir(parents=True)
        (session_dir / "spawn.json").write_text(json.dumps({"session_id": session,
            "skill": "execute", "provider": "codex", "runtime": "process", "model": "fixture",
            "worktree_path": str(worktree)}))
        (session_dir / "events.ndjson").write_text("")
        stage = {"stage_index": 0, "skill": "execute", "provider": "codex", "runtime": "process",
                 "model": "fixture", "status": "running", "attempts": [{"status": "running", "session_id": session}],
                 "prompt": json.dumps(issue_execution.projection(binding, prepared["envelope_sha256"], "supervised"))}
        snapshot = {"state": {"orders": {execution["order_id"]: {"stages": [stage]}}}, "effect_ledger": []}
        (root / ".noodle/state.snapshot.json").write_text(json.dumps(snapshot))
        environment = {**os.environ, "NOODLE_PROJECT_DIR": str(root), "NOODLE_WORKTREE": str(worktree),
            "NOODLE_ORDER_ID": execution["order_id"], "NOODLE_STAGE_INDEX": "0", "NOODLE_SESSION_ID": session,
            "SOODLES_ADMISSION_LAUNCHER": str(output / "launcher")}
        for arguments in (["--plan"], []):
            run = subprocess.run([*execution["runtime"]["test_argv"], *arguments], cwd=worktree,
                                 env=environment, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            observed = json.loads(run.stdout)
            if not arguments:
                self.assertEqual(observed["results"][0]["stdout"], "target\n")
                self.assertEqual(observed["scope"]["modules"], [])
        feedback_root = self.outer / "feedback"
        feedback_root.mkdir()
        def save(name, value):
            path = feedback_root / name
            path.write_text(json.dumps(value))
            return self.ref(path)
        instruction = self.ref(worktree / "AGENTS.md")
        task = save("task.json", {"task": "target correction"})
        requirements = save("requirements.json", {"task": execution["task"], "contract": binding["contract"]})
        protocol = save("protocol.json", {"schema": 2, "subject": "generic feedback fixture",
            "requirements": requirements, "instructions": [instruction], "methods": [instruction],
            "cases": [{"id": "target", "input": task, "expected": {"complete": False}}]})
        review = save("review.json", {"schema": 1, "protocol_sha256": protocol["sha256"], "reviewer": "fixture",
            "checks": {"target": {"complete": {"status": "supported", "requirement_quote": "target correction",
                                             "reason": "Synthetic product control, not Agent evidence"}}}})
        report = save("report.json", {"schema": 1, "case_id": "target", "instructions": {
            instruction["path"]: instruction["sha256"]}, "input_sha256": task["sha256"], "output": {"complete": False}})
        trace = save("trace.json", {"fixture": "complete=false"})
        packet = save("selection.json", {"schema": 2, "protocol": protocol, "criteria_review": review,
            "observations": [{"case_id": "target", "report": report, "trace": trace}]})
        feedback_argv = [*execution["runtime"]["stage_outcome_argv"], "feedback", packet["path"], packet["sha256"]]
        feedback = subprocess.run(feedback_argv, cwd=worktree, env=environment, capture_output=True, text=True)
        self.assertEqual(feedback.returncode, 0, feedback.stdout + feedback.stderr)
        projected = json.loads(feedback.stdout)
        self.assertEqual(projected["feedback"]["result"]["target_scope"]["target_binding"], selection["target_binding"])
        self.assertEqual(projected["next"]["operation"], "consume_verified_behavior")
        argv = [*execution["runtime"]["stage_outcome_argv"], "completed", "Fixture target command passed"]
        foreign = subprocess.run(argv, cwd=worktree, env={**environment, "NOODLE_SESSION_ID": "foreign"},
                                 capture_output=True, text=True)
        self.assertNotEqual(foreign.returncode, 0)
        self.assertEqual(len((session_dir / "events.ndjson").read_text().splitlines()), 1)
        outcome = subprocess.run(argv, cwd=worktree, env=environment, capture_output=True, text=True)
        self.assertEqual(outcome.returncode, 0, outcome.stdout + outcome.stderr)
        self.assertEqual(json.loads(outcome.stdout)["status"], "recorded")
        duplicate = subprocess.run(argv, cwd=worktree, env=environment, capture_output=True, text=True)
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertEqual(len((session_dir / "events.ndjson").read_text().splitlines()), 2)
        (output / "runtime/stage_outcome.py").write_text("raise SystemExit(0)\n")
        tampered = subprocess.run(argv, cwd=worktree, env=environment, capture_output=True, text=True)
        self.assertNotEqual(tampered.returncode, 0)
        self.assertIn("changed admission bytes", tampered.stderr)

    def test_next_issue_keeps_binding_and_reads_back_unknown_create(self):
        _, selection, _ = self.target()
        repo = selection["repository"]
        reference = selection["target_binding"]
        contract = issue_admission.parse_contract(selection["issue"]["body"])
        for key in ("base_head", "frozen_paths", "required_paths", "evidence_manifest"):
            del contract[key]
        contract["schema"] = 1
        candidate = {"candidate_id": "followup", "repository": repo, "title": "Followup fixture",
                     "contract": contract, "target_binding": reference}
        resolved = {"claim": {"repository": repo, "issue": 7, "target_binding": reference},
                    "classification": "RESOLVED", "phase": "resolved", "next": None}
        plan = next_issue.prepare(resolved, {"schema": 1, "selected_candidate": "followup", "candidates": [candidate]},
            {"schema": 1, "complete": True, "issues": []}, {"kind": "local"}, self.outer / "next")
        intent = self.outer / "next/intent.json"
        self.assertEqual(json.loads(intent.read_text())["target_binding"], reference)
        calls = []
        def lost(method, url, payload, token):
            calls.append((method, url, payload))
            raise next_issue.ProviderUnknown("response lost")
        first = next_issue.execute(intent, environ={"GH_TOKEN": "fixture"}, api=lost)
        second = next_issue.execute(intent, environ={"GH_TOKEN": "fixture"}, api=lost)
        self.assertEqual(len(calls), 1)
        self.assertEqual(first["next"], second["next"])
        self.assertEqual(first["next"]["bindings"], [{"repository": repo, "target_binding": reference}])
        body = json.loads(intent.read_text())["request"]["body"]
        observed = {"repository": repo, "number": 8, "state": "open", "state_reason": None,
                    "closed_at": None, "html_url": f"https://github.com/{repo}/issues/8", "body": body}
        materialized = provider_readback.consume(first,
            {"schema": 1, "kind": "next_issue", "consumer_root": str(self.runtime)},
            self.outer / "readback", environ={"GH_TOKEN": "fixture"},
            api=lambda method, url, token: ([observed], {}))
        process = subprocess.run(materialized["next"]["argv"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        terminal = json.loads(process.stdout)
        self.assertEqual(terminal["issue"]["number"], 8)
        self.assertEqual(terminal["target_binding"], reference)

    def test_selected_scope_never_uses_soodles_boundaries(self):
        root, selection, _ = self.target()
        contract = issue_admission.parse_contract(selection["issue"]["body"])
        decision = test_manager.admission_scope(root, contract, target=selection)
        self.assertEqual(decision["commands"], [[sys.executable, "-B", "target.py"]])
        self.assertEqual(decision["modules"], [])
        current_next = {"owner": "original-atom", "argv": ["/selected/issue-atom", "run", "/selected/auth.json"]}
        projected = schema_manager.project_target_scope(decision, current_next)
        self.assertEqual(projected["target_binding"], selection["target_binding"])
        self.assertEqual(projected["unknowns"], ["target_command_execution", "target_normal_use"])
        self.assertEqual(projected["next"], current_next)
        contract["write_paths"].append("unselected.py")
        gap = test_manager.admission_scope(root, contract, target=selection)
        self.assertEqual(gap["next"], {"owner": "target test owner", "required": ["selected_target_scope"]})

    def test_atom_cost_feedback_preserves_selected_target_scope(self):
        _, selection, binding = self.target()
        receipt = self.authorize(selection)
        authorization_path = receipt["authorization"]["path"]
        current_next = {"owner": "soodles.issue-atom", **receipt["next"]}
        for state in ("ready", "unknown"):
            with self.subTest(state=state):
                if state == "unknown":
                    Path(selection["target_binding"]["path"]).write_text("changed binding bytes\n")
                owner_result = {"status": "pending", "phase": "execution",
                                "owner": "soodles.issue-atom", "next": current_next}
                with patch.object(issue_atom, "_run", return_value=owner_result), \
                        patch.object(issue_atom, "cost_response", wraps=issue_atom.cost_response) as cost, \
                        patch.object(schema_manager, "project_owner_feedback",
                                     wraps=schema_manager.project_owner_feedback) as project:
                    result = issue_atom.run(authorization_path, environ={})
                cost.assert_called_once()
                project.assert_called_once()
                self.assertEqual(result["cost"]["status"], "reported")
                scope = result["target_scope"]
                self.assertEqual(scope["state"], state)
                self.assertEqual(result["cost"]["feedback"]["target_scope"], scope)
                self.assertIs(result["feedback"], result["cost"]["feedback"])
                self.assertEqual(result["next"], current_next)
                self.assertEqual(result["feedback"]["next"], current_next)
                self.assertFalse(scope["authorizes_landing"])
                if state == "ready":
                    self.assertEqual(scope["target_binding"], selection["target_binding"])
                    self.assertEqual(scope["repository"], selection["repository"])
                    self.assertEqual(scope["scope_owner"], binding["verification"]["owner"])
                    self.assertEqual(scope["facts"]["commands"], binding["verification"]["commands"])
                    self.assertEqual(scope["next"], current_next)
                else:
                    self.assertIn("invalid", scope)
                    self.assertIn("next", scope)

    def test_legacy_consumer_reads_generic_dependency_through_original_owner(self):
        _, selection, _ = self.target()
        dependency = {"repository": selection["repository"], "target_binding": selection["target_binding"],
            "issue": 7, "pr": 12, "base_head": "a" * 40, "candidate_head": "b" * 40,
            "tree": "c" * 40, "revision": "d" * 40, "run_id": 11, "run_attempt": 2}
        claim = {"repository": "ed3c/soodles", "issue": 229, "pr": 230, "head": "e" * 40,
                 "run_id": 21, "dependencies": [dependency]}
        checkpoint = self.outer / "landing.json"
        next_action = landing.provider_next(claim, "advance", checkpoint)
        requests = next_action["requests"]
        reads = []
        def read(method, url, token):
            self.assertEqual(method, "GET")
            reads.append(url)
            return {"source_url": url}, {}
        receipt = provider_readback.consume({"next": next_action},
            {"schema": 1, "kind": "landing", "publisher": {
                "root": str(self.publisher), "verifier_sha256": landing.verifier_digest()}},
            self.outer / "dependency-readback", environ={"GH_TOKEN": "fixture"}, api=read)
        self.assertEqual(reads, [request["url"] for request in requests.values()])
        materialized = json.loads(Path(receipt["readback"]).read_text())
        self.assertEqual(materialized["dependency_0_issue"], {
            "source_url": "https://api.github.com/repos/example/first-target/issues/7"})
        self.assertEqual(receipt["next"]["known"]["checkpoint"], str(checkpoint))
        self.assertEqual(receipt["next"]["owner"], "landing.advance")

    def test_generic_publication_validates_target_candidate_before_effect(self):
        self.generic_delivery("example/first-target", "trunk")

    def test_second_target_uses_same_delivery_owners(self):
        self.generic_delivery("other/second-target", "stable")

    def generic_delivery(self, repository, base_ref):
        root, selection, binding = self.target(repository, base_ref)
        contract = issue_admission.parse_contract(selection["issue"]["body"])
        repo = selection["repository"]
        issue = {**selection["issue"], "state": "open", "updated_at": "2026-10-03T00:00:00Z",
                 "url": f"https://api.github.com/repos/{repo}/issues/7",
                 "html_url": f"https://github.com/{repo}/issues/7"}
        prepared = supervisor_admission.prepare(issue, self.carrier, root, self.outer / "admission",
            environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"])
        envelope_path = Path(prepared["bundle"]) / "envelope.json"
        envelope = json.loads(envelope_path.read_text())
        name = envelope["execution"]["worktree"]
        worktree = root / ".worktrees" / name
        self.git(root, "worktree", "add", "-b", name, str(worktree))
        (worktree / "target.py").write_text("print('corrected target')\n")
        manifest = {"schema": 1, "issue": {"repository": selection["repository"], "number": 7},
            "instructions": [{"path": "target.py", "baseline_sha256": self.ref(root / "target.py")["sha256"],
                              "treatment_sha256": self.ref(worktree / "target.py")["sha256"]}],
            "artifacts": [], "owner": {"name": "fixture", "tool": "issue_admission.validate_delivery_paths",
                                       "authorization": selection["repository"] + "#7"},
            "authorizes_landing": False}
        (worktree / "evidence.json").write_text(json.dumps(manifest))
        self.git(worktree, "add", ".")
        self.git(worktree, "commit", "-m", "Correct target behavior")
        events = root / ".noodle/sessions/fixture/events.ndjson"
        events.parent.mkdir(parents=True)
        events.write_text('{"fixture":"completed"}\n')
        snapshot = root / ".noodle/state.snapshot.json"
        snapshot.write_text('{"fixture":"canonical"}\n')
        head, tree = self.git(worktree, "rev-parse", "HEAD"), self.git(worktree, "rev-parse", "HEAD^{tree}")
        corrected_output = self.outer / "corrected-admission"
        corrected = supervisor_admission.prepare(issue, self.carrier, root, corrected_output,
            environ={"NOODLES_TOKEN_COMMAND": "fixture supplier"}, wire_host=True, correction=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"])
        self.assertEqual(supervisor_admission.prepare(issue, self.carrier, root, corrected_output,
            environ={}, wire_host=True, correction=True, readback=True,
            runtime_root=self.runtime, target_binding=selection["target_binding"]), corrected)
        correction_envelope = json.loads((corrected_output / "envelope.json").read_text())
        self.assertEqual(correction_envelope["execution"]["source_head"], head)
        self.assertEqual(correction_envelope["target_binding"], selection["target_binding"])
        claim = {"schema_version": 1, "owner": "Noodle", "repository": repo, "subject": repo + "#7",
            "order_id": "target-7", "stage_index": 0, "attempt_id": "target-7:0:0", "session_id": "fixture",
            "worktree_name": name, "worktree_path": str(worktree), "branch": name,
            "head": head, "tree": tree, "base_branch": binding["base_ref"], "base_head": contract["base_head"],
            "push_remote": "origin", "remote_url": "https://github.com/" + repo + ".git",
            "evidence": {"canonical_snapshot_sha256": self.ref(snapshot)["sha256"],
                         "session_events_sha256": self.ref(events)["sha256"]},
            "authorizes_provider_write": False, "authorizes_landing": False}
        readiness = candidate_publication.native_readiness(worktree, claim, self.ref(self.binary), selection["target_binding"])
        effects, state = [], {}
        def create(title, branch, base, body):
            effects.append("create")
            state["pull"] = {"number": 12, "state": "open", "html_url": f"https://github.com/{repo}/pull/12",
                "body": body, "head": {"ref": branch, "sha": head}, "base": {"ref": base}}
            return state["pull"]
        provider = SimpleNamespace(repository_info=lambda: {"full_name": repo, "default_branch": "unselected"},
            issue=lambda number: issue, base_head=lambda branch: contract["base_head"] if branch == base_ref else None,
            branch=lambda branch: {"object": {"sha": state["head"]}} if "head" in state else None,
            pulls=lambda branch, base: [state["pull"]] if "pull" in state else [],
            create_pull=create, pull=lambda number: state["pull"])
        def push(path, *args, **kwargs):
            self.assertEqual(path, worktree)
            effects.append("push")
            state["head"] = head
            return SimpleNamespace(returncode=0)
        wrong = {**claim, "base_branch": "main"}
        with self.assertRaises(candidate_publication.PublicationRefusal):
            candidate_publication.publish(worktree, readiness, wrong, provider, push=push)
        self.assertEqual(effects, [])
        result = candidate_publication.publish(worktree, readiness, claim, provider, push=push)
        self.assertEqual(result["pr"]["number"], 12)
        self.assertEqual(effects, ["push", "create"])
        reused = candidate_publication.publish(worktree, readiness, claim, provider, push=push)
        self.assertEqual(reused["status"], "reused")
        self.assertEqual(effects, ["push", "create"])
        run, jobs = self.ci(selection, binding, head)
        provider.workflow_runs = lambda current: {"workflow_runs": [run]}
        provider.jobs = lambda run_id: jobs
        authorization = {**selection, "base_head": contract["base_head"],
            "workflow": {"path": binding["workflow_path"], "jobs": binding["jobs"]}}
        self.assertEqual(issue_atom.select_run(provider, authorization, head), (run, jobs))
        delivery = {"repository": repo, "issue": 7, "pr": 12, "head": head, "tree": tree,
            "base_head": contract["base_head"], "run_id": run["id"], "run_attempt": run["run_attempt"],
            "control_root": str(root), "worktree": name, "publication_branch": result["branch"],
            "target_binding": selection["target_binding"], "execution_envelope": self.ref(envelope_path),
            "verifier_sha256": landing.verifier_digest()}
        pull = copy.deepcopy(state["pull"])
        pull["head"]["repo"] = {"full_name": repo}
        pull["base"].update(repo={"full_name": repo}, sha=contract["base_head"])
        pull.update(merged=False, draft=False, mergeable=True)
        readback = {"pr": pull, "issue": issue, "run": run, "jobs": jobs,
            "commit": {"sha": head, "tree": {"sha": tree}},
            "branch": {"name": base_ref, "commit": {"sha": contract["base_head"]}}}
        checkpoint = self.outer / "landing.json"
        landing.start(delivery, readback, checkpoint)
        landing.advance(checkpoint, readback)
        offered = landing.dispatch(checkpoint, readback)
        self.assertEqual(offered["request"]["expected_head_sha"], head)
        unchanged = checkpoint.read_bytes()
        waiting = landing.advance(checkpoint, readback)
        self.assertEqual(waiting["action"], "readback")
        self.assertEqual(checkpoint.read_bytes(), unchanged)
        self.git(root, "merge", "--no-ff", name, "-m", "Fixture provider merge")
        merge = self.git(root, "rev-parse", "HEAD")
        readback["pr"].update(merged=True, state="closed", merged_at="now", merge_commit_sha=merge)
        readback["merge_commit"] = {"sha": merge, "tree": {"sha": tree},
            "parents": [{"sha": contract["base_head"]}, {"sha": head}]}
        landing.advance(checkpoint, readback)
        closed = landing.dispatch(checkpoint, readback)
        self.assertEqual(closed["request"]["state"], "closed")
        readback["issue"].update(state="closed", closed_at="now", state_reason="completed")
        readback["branch"]["commit"]["sha"] = merge
        landed = landing.advance(checkpoint, readback)
        self.assertEqual(landed["phase"], "awaiting_reconcile")
        self.git(root, "update-ref", "refs/remotes/origin/" + base_ref, merge)
        self.git(root, "worktree", "remove", str(worktree))
        self.git(root, "branch", "-d", name)
        order = envelope["execution"]["order_id"]
        snapshot.write_text(json.dumps({"state": {"orders": {order: {"status": "completed", "stages": [
            {"status": "completed", "attempts": [{"status": "completed", "session_id": "fixture"}]}]}}},
            "effect_ledger": []}))
        (events.parent / "process.json").write_text(json.dumps({"session_id": "fixture", "pid": 2147483647}))
        with patch("landing.fetch_main", side_effect=lambda root, base_ref: None) as fetch:
            resolved = landing.reconcile(checkpoint, str(self.binary))
        fetch.assert_called_once_with(root, base_ref)
        self.assertEqual(resolved["classification"], "RESOLVED")
        self.assertEqual(resolved["local"]["cleanup_mode"], "no_op")
        self.assertEqual(resolved["noodle_reconciliation"]["order_id"], order)
        self.assertEqual(resolved["writes_offered"], ["merge", "close"])

    def test_reconciliation_fetches_selected_base(self):
        with patch("landing.subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
            landing.fetch_main(self.outer, "stable")
        self.assertEqual(run.call_args.args[0], ["git", "fetch", "origin", "stable"])

    def test_correction_uses_binding_base_and_complete_failed_jobs(self):
        _, selection, binding = self.target()
        head = "a" * 40
        run, jobs = self.ci(selection, binding, head)
        run["conclusion"] = "failure"
        jobs["jobs"][1]["conclusion"] = "failure"
        jobs["jobs"][1]["steps"][0]["conclusion"] = "failure"
        base = issue_admission.parse_contract(selection["issue"]["body"])["base_head"]
        branch = "soodles/issue-7-" + head[:12]
        prior = {"branch": branch, "head": head, "pr": {"number": 12}}
        authorization = {**selection, "base_head": base, "prior_publication": prior,
            "workflow": {"path": binding["workflow_path"], "jobs": binding["jobs"]}}
        observed = []
        def base_head(name):
            observed.append(name)
            return base if name == "trunk" else "f" * 40
        provider = SimpleNamespace(repository_info=lambda: {"full_name": selection["repository"], "default_branch": "main"},
            base_head=base_head, pull=lambda number: {"number": 12, "state": "open", "merged": False,
                "head": {"ref": branch, "sha": head}, "base": {"ref": "trunk"},
                "body": "Refs example/first-target#7"}, branch=lambda name: {"object": {"sha": head}},
            workflow_runs=lambda head: {"workflow_runs": [run]}, jobs=lambda number: jobs,
            job_log=lambda number: {"job_id": number, "raw": b"fixture failed lint", "gap": None})
        self.assertEqual(issue_atom.verify_failed_prior(provider, authorization), (run, jobs))
        self.assertEqual(observed, ["trunk"])
        context, raw = issue_atom.failed_ci_context(provider, authorization, run, jobs, self.outer / "failure.log")
        self.assertEqual(context["data"]["target_binding"], selection["target_binding"])
        self.assertEqual(raw, b"fixture failed lint")
        jobs["jobs"].pop(0)
        with self.assertRaises(issue_atom.AtomRefusal):
            issue_atom.verify_failed_prior(provider, authorization)

    def test_missing_target_scope_refuses_authorization(self):
        _, selection, binding = self.target()
        binding["verification"]["paths"] = ["target.py"]
        path = Path(selection["target_binding"]["path"])
        path.write_text(json.dumps(binding))
        selection["target_binding"] = self.ref(path)
        with self.assertRaises(issue_admission.AdmissionRefusal) as caught:
            self.authorize(selection)
        self.assertEqual(caught.exception.next["owner"], "target test owner")
        self.assertFalse((self.outer / "prepared").exists())

    def test_missing_external_runtime_names_supervisor_input(self):
        _, selection, _ = self.target()
        del selection["lifecycle_owner"]
        with self.assertRaises(issue_admission.AdmissionRefusal) as caught:
            self.authorize(selection)
        self.assertEqual(caught.exception.next["required"], ["immutable_external_lifecycle_owner"])
        self.assertFalse((self.outer / "prepared").exists())

    def test_origin_and_base_ref_refuse_before_preparation(self):
        root, selection, _ = self.target()
        self.git(root, "remote", "set-url", "origin", "https://github.com/foreign/repository.git")
        with self.assertRaises((issue_admission.AdmissionRefusal, issue_atom.AtomRefusal)):
            self.authorize(selection)
        self.assertFalse((self.outer / "prepared").exists())
        self.git(root, "remote", "set-url", "origin", "https://github.com/example/first-target.git")
        self.git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        with self.assertRaises((issue_admission.AdmissionRefusal, issue_atom.AtomRefusal)):
            self.authorize(selection)
        self.assertFalse((self.outer / "prepared").exists())

    def test_ci_requires_every_selected_job_and_exact_attempt(self):
        _, selection, binding = self.target()
        run, jobs = self.ci(selection, binding, "a" * 40)
        self.assertTrue(repository_binding.validate_run(selection, run, jobs, "a" * 40, issue_atom.require))
        for change in (lambda value: value["jobs"].pop(),
                       lambda value: value["jobs"][1].update(run_attempt=1),
                       lambda value: value["jobs"][1].update(steps=[])):
            invalid = copy.deepcopy(jobs)
            change(invalid)
            with self.assertRaises(issue_atom.AtomRefusal):
                repository_binding.validate_run(selection, run, invalid, "a" * 40, issue_atom.require)

    def ci(self, selection, binding, head):
        repo = {"full_name": selection["repository"]}
        run = {"id": 11, "run_attempt": 2, "repository": repo, "head_repository": repo,
               "head_sha": head, "event": "pull_request", "path": binding["workflow_path"],
               "status": "completed", "conclusion": "success"}
        jobs = {"total_count": 2, "jobs": [{"id": index, "name": name, "run_id": 11, "run_attempt": 2,
                "head_sha": head, "status": "completed", "conclusion": "success",
                "steps": [{"name": step, "status": "completed", "conclusion": "success"} for step in steps]}
                for index, (name, steps) in enumerate(binding["jobs"].items(), 1)]}
        return run, jobs
