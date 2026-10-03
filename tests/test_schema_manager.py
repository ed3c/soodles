"""Fixed protocol controls; no model/provider effects or recurring timing gate."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import issue_atom as atom
import schema_manager as manager

ROOT = Path(manager.__file__).parent


def fact(value, evidence="readback", producer="issue_atom.py:finish_host"):
    return {"value": value, "evidence": manager.digest(evidence), "producer": producer}


class SchemaManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = manager.compile_plan(ROOT)

    def setUp(self):
        self.identity = {"authorization": "a" * 64, "subject": "b" * 64,
                         "plan": self.plan.identity}
        self.owner = manager.Manager(self.plan, self.identity)

    def test_and_prerequisites_and_original_confirmation(self):
        for missing in ("landing_resolved", "loop_absent", "config_restored", "owner_confirmed"):
            owner = manager.Manager(self.plan, self.identity)
            owner.observe({k: fact(True) for k in
                           ("landing_resolved", "loop_absent", "config_restored") if k != missing})
            if missing != "owner_confirmed":
                owner.observe({"owner_confirmed": fact(True, producer="issue_atom.py:finish_host.confirm")})
            self.assertNotEqual(owner.project()["status"], "complete")
        self.owner.observe({k: fact(True) for k in
                            ("cleanup_allowed", "landing_resolved", "loop_absent", "config_restored")})
        self.assertIn("confirm", self.owner.project()["ready"])
        self.assertNotEqual(self.owner.project()["status"], "complete")
        self.owner.observe({"owner_confirmed": fact(True, producer="issue_atom.py:finish_host.confirm")})
        self.assertEqual(self.owner.project()["status"], "complete")
        self.assertFalse(self.owner.project()["authorizes_landing"])

    def test_replay_conflict_sequence_and_identity(self):
        self.owner.observe({"cleanup_allowed": fact(True)})
        event = self.owner.record()
        before = copy.deepcopy(event)
        for _ in range(10):
            self.owner.apply(event)
        self.assertEqual(self.owner.record(), before)
        for field in ("authorization", "subject", "plan"):
            altered = copy.deepcopy(event)
            altered["identity"][field] = "c" * 64
            with self.assertRaisesRegex(manager.SchemaRefusal, "identity"):
                self.owner.apply(altered)
        altered = copy.deepcopy(event)
        altered["facts"]["cleanup_allowed"] = fact(False)
        with self.assertRaisesRegex(manager.SchemaRefusal, "conflicting_replay"):
            self.owner.apply(altered)
        for sequence in (0, 3, True):
            with self.assertRaisesRegex(manager.SchemaRefusal, "sequence"):
                self.owner.apply({**event, "sequence": sequence})
        self.assertEqual(self.owner.record(), before)

    def test_changed_physical_evidence_invalidates_confirmation_and_restart_is_bounded(self):
        self.owner.observe({k: fact(True) for k in
                           ("cleanup_allowed", "landing_resolved", "loop_absent", "config_restored")})
        self.owner.observe({"owner_confirmed": fact(True, producer="issue_atom.py:finish_host.confirm")})
        record = json.loads(json.dumps(self.owner.record()))
        resumed = manager.Manager(self.plan, self.identity, record)
        self.assertEqual(resumed.project(), self.owner.project())
        resumed.observe({"config_restored": fact(True, "changed readback")})
        self.assertNotEqual(resumed.project()["status"], "complete")
        self.assertNotIn("owner_confirmed", resumed.facts)
        self.assertLessEqual(len(resumed.facts), len(manager.FACTS))
        self.assertNotIn("repair", resumed.record())
        changed = copy.deepcopy(record)
        changed["sequence"] += 1
        changed["facts"]["loop_absent"] = fact(False)
        with self.assertRaisesRegex(manager.SchemaRefusal, "confirmation_invalidated"):
            self.owner.apply(changed)

    def test_unknown_effect_does_not_offer_stop_or_restore_again(self):
        self.owner.observe({"cleanup_allowed": fact(True), "loop_live": fact(True),
                            "stop_offered": fact(False)})
        self.assertIn("stop", self.owner.project()["ready"])
        self.owner.observe({"stop_offered": fact(True)})
        self.assertEqual(self.owner.project()["status"], "stop")
        self.assertNotIn("stop", self.owner.project()["ready"])
        self.owner.observe({"loop_live": fact(False), "loop_absent": fact(True),
                            "config_installed": fact(True), "restore_offered": fact(False)})
        self.assertIn("restore", self.owner.project()["ready"])
        self.owner.observe({"restore_offered": fact(True)})
        self.assertEqual(self.owner.project()["required"], "original_owner_readback")
        self.assertNotIn("restore", self.owner.project()["ready"])

    def test_hot_path_has_no_source_or_context_loading(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("hot filesystem")), \
                patch.object(manager, "compile_repair", side_effect=AssertionError("hot context")), \
                patch.object(Path, "read_text", side_effect=AssertionError("hot filesystem")), \
                patch("builtins.open", side_effect=AssertionError("hot filesystem")), \
                patch("subprocess.run", side_effect=AssertionError("hot process")), \
                patch("socket.socket", side_effect=AssertionError("hot network")):
            self.owner.observe({"cleanup_allowed": fact(True)})
            self.owner.apply(self.owner.record())
            self.owner.project()
        self.assertEqual(self.plan.context["consumer"], "issue_atom.finish_host")
        self.assertEqual(self.plan.context["requires"], [
            "contracts/system-v1/common.md", "contracts/system-v1/issue-atom.md"])

    def test_byte_reader_compiles_exact_source_without_filesystem_or_execution(self):
        names = set(self.plan.sources) | {
            "candidate_publication.py", "provider_readback.py", "issue-atom",
            "soodles", "soodles.py", "provider-readback",
            "contracts/system-v1/candidate.md", "contracts/system-v1/readback.md"}
        sources = {name: (ROOT / name).read_bytes() for name in names}
        with patch.object(Path, "read_bytes", side_effect=AssertionError("filesystem")), \
                patch.object(Path, "read_text", side_effect=AssertionError("filesystem")):
            plan = manager.compile_plan(ROOT, read_bytes=sources.__getitem__)
        self.assertEqual(plan, self.plan)
        sources["issue_atom.py"] += b'\nraise RuntimeError("historical Python executed")\n'
        changed = manager.compile_plan(ROOT, read_bytes=sources.__getitem__)
        self.assertNotEqual(changed.identity, plan.identity)
        self.assertEqual(changed.rules, plan.rules)
        self.assertEqual(changed.sources["issue_atom.py"],
                         hashlib.sha256(sources["issue_atom.py"]).hexdigest())

    def test_catalog_names_missing_and_wrong_producers_and_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in self.plan.sources:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            original = json.loads((root / manager.PLAN_PATH).read_text())
            cases = [
                (lambda v: v["facts"].pop("loop_absent"), "catalog.fact:loop_absent"),
                (lambda v: v["facts"].update(foreign={}), "catalog.fact:foreign"),
                (lambda v: v["facts"]["loop_absent"].pop("producer"), "catalog.fields:loop_absent"),
                (lambda v: v["facts"]["loop_absent"]["producer"].update(function="invented"), "loop_absent.producer"),
                (lambda v: v["facts"]["config_restored"].update(readbacks=["invented"]), "config_restored.readbacks"),
                (lambda v: v["facts"]["config_restored"].update(consumers=[]), "config_restored.consumers"),
                (lambda v: v.update(entry="issue-atom recover"), "catalog.entry"),
                (lambda v: v["nodes"]["complete"].pop("owner_confirmed"), "plan.nodes"),
            ]
            for mutate, gap in cases:
                value = copy.deepcopy(original)
                mutate(value)
                (root / manager.PLAN_PATH).write_text(json.dumps(value))
                with self.subTest(gap=gap), self.assertRaisesRegex(manager.SchemaRefusal, gap):
                    manager.compile_plan(root)

    def test_missing_data_is_unknown_and_false_is_a_blocked_prerequisite(self):
        projection = self.owner.project()
        self.assertEqual(projection["dag"]["complete"]["requires"], [
            {"fact": "landing_resolved", "value": True, "status": "unknown"},
            {"fact": "loop_absent", "value": True, "status": "unknown"},
            {"fact": "config_restored", "value": True, "status": "unknown"},
            {"fact": "owner_confirmed", "value": True, "status": "unknown"},
        ])
        self.assertIsNone(projection["facts"]["loop_absent"]["observation"])
        self.assertEqual(projection["facts"]["loop_absent"]["field"]["producer"],
                         {"file": "issue_atom.py", "function": "finish_host"})
        projection = self.owner.observe({"loop_absent": fact(False)})
        self.assertEqual(projection["dag"]["complete"]["status"], "blocked")
        self.assertEqual(projection["dag"]["complete"]["requires"][1]["status"], "blocked")
        self.assertEqual(projection["dag"]["complete"]["requires"][0]["status"], "unknown")
        projection = self.owner.observe({"loop_absent": None})
        self.assertEqual(projection["dag"]["complete"]["status"], "unknown")
        self.assertNotIn("loop_absent", self.owner.record()["facts"])

    def test_event_producer_required_and_legacy_metadata_not_invented(self):
        for observation, gap in (({"value": True, "evidence": "a" * 64}, "producer_missing"),
                                 (fact(True, producer="agent:success"), "producer:")):
            with self.assertRaisesRegex(manager.SchemaRefusal, gap):
                self.owner.observe({"cleanup_allowed": observation})
        legacy = {"identity": self.identity, "sequence": 1,
                  "facts": {"cleanup_allowed": {"value": True, "evidence": "a" * 64}}}
        resumed = manager.Manager(self.plan, self.identity, legacy)
        self.assertEqual(resumed.record(), legacy)
        self.assertEqual(resumed.project()["facts"]["cleanup_allowed"]["provenance"],
                         "legacy_without_producer")
        resumed.apply(legacy)
        resumed.observe({"loop_absent": fact(True)})
        self.assertEqual(resumed.facts["cleanup_allowed"], legacy["facts"]["cleanup_allowed"])
        resumed.observe({"cleanup_allowed": fact(True)})
        self.assertEqual(resumed.project()["facts"]["cleanup_allowed"]["provenance"], "recorded")

    def test_invalid_plan_facts_and_source_mutation_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in self.plan.sources:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.plan.validate_sources(root)
            (root / manager.PLAN_PATH).write_text("{}")
            with self.assertRaisesRegex(manager.SchemaRefusal, "source_changed"):
                self.plan.validate_sources(root)
            with self.assertRaisesRegex(manager.SchemaRefusal, "plan"):
                manager.compile_plan(root)
        for facts in ({"unknown": fact(True)}, {"loop_live": fact(True), "loop_absent": fact(True)},
                      {"cleanup_allowed": {"value": 1, "evidence": "a" * 64}}):
            with self.assertRaises(manager.SchemaRefusal):
                self.owner.apply({"identity": self.identity, "sequence": 1, "facts": facts})


class OwnerFeedbackTests(unittest.TestCase):
    authorization = "/external/original-authorization.json"

    def correction(self, *, known=True):
        return atom.refusal_output(atom.AtomRefusal(
            "workflow.conclusion", "failure", "new_candidate_head_after_failed_ci",
            known={"authorization_sha256": "a" * 64} if known else None), self.authorization)

    def project(self, result, state, disposition):
        before = copy.deepcopy(result)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("filesystem")), \
                patch("subprocess.run", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            feedback = manager.project_owner_feedback(result)
        self.assertEqual(result, before)
        self.assertIs(feedback["next"], result.get("next"))
        self.assertEqual(feedback["state"], result["status"])
        self.assertEqual(feedback["transition_owner"], result["owner"])
        self.assertEqual(feedback["dag"]["owner_transition"]["status"], state)
        self.assertEqual(feedback["review_disposition"], disposition)
        self.assertEqual(feedback["effects"], [])
        self.assertIsNone(feedback["test_demand"])
        self.assertFalse(feedback["authorizes_landing"])
        return feedback["dag"]["owner_transition"]

    def test_pending_preserves_material_change_condition_and_owner(self):
        result = atom.response({"phase": "ci"}, self.authorization, waiting_on="GitHub Actions")
        transition = self.project(result, "waiting", "wait_for_owner_change")
        self.assertEqual(result["continuation_state"], "waiting")
        self.assertEqual(transition["requires"], ["material_owner_or_provider_state_change"])
        self.assertEqual(transition["continuation_owner"], result["next"]["owner"])
        self.assertEqual(transition["waiting_on"], "GitHub Actions")
        self.assertEqual(transition["gaps"], [])

    def test_failed_ci_correction_is_ready_only_with_selected_digest(self):
        result = self.correction()
        transition = self.project(result, "ready", "consume_current_owner_next")
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["continuation_state"], "ready")
        self.assertEqual(result["next"]["argv"][3:6], ["correction", self.authorization, "a" * 64])
        self.assertEqual(transition["continuation_owner"], "supervisor.authorization")
        self.assertEqual(transition["gaps"], [])
        missing = self.correction(known=False)
        self.project(missing, "input_required", "supply_owner_input")
        self.assertNotIn("argv", missing["next"])

    def test_refusal_preserves_named_input_even_with_argv(self):
        result = atom.refusal_output(atom.AtomRefusal(
            "authorization.path", "FileNotFoundError", "readable_external_authorization"), self.authorization)
        transition = self.project(result, "input_required", "supply_owner_input")
        self.assertEqual(result["next"]["argv"], atom.same_command(self.authorization))
        self.assertEqual(transition["requires"], ["readable_external_authorization"])
        self.assertEqual(transition["continuation_owner"], "external-supervisor")

    def test_structural_deadlock_and_resolved_are_distinct(self):
        stopped = atom.response({"phase": "landing"}, self.authorization, status="refused",
                                details={"landing": {"next": None}})
        transition = self.project(stopped, "unknown", "owner_readback_required")
        self.assertTrue(transition["gaps"])
        self.assertEqual(stopped["next"]["argv"], atom.same_command(self.authorization))
        resolved = atom.response({"phase": "resolved"}, self.authorization, status="resolved")
        transition = self.project(resolved, "complete", "history_retained")
        self.assertIsNone(resolved["next"])
        self.assertEqual(transition["requires"], [])
        self.assertEqual(transition["gaps"], [])

    def test_legacy_does_not_infer_readiness_or_completion(self):
        results = [self.correction(), atom.response({"phase": "resolved"}, self.authorization, status="resolved")]
        for result in results:
            result.pop("continuation_state")
            disposition = "history_retained" if result["status"] == "resolved" else "owner_readback_required"
            transition = self.project(result, "unknown", disposition)
            self.assertIn("continuation_state: missing or invalid owner declaration", transition["gaps"])

    def test_ready_command_accepts_empty_arguments_and_environment_values(self):
        result = self.correction()
        result["next"]["argv"].append("")
        result["next"]["environment"] = {"OPTIONAL_VALUE": ""}
        self.project(result, "ready", "consume_current_owner_next")

    def test_malformed_readiness_keeps_original_owner_response(self):
        ready = self.correction()
        waiting = atom.response({"phase": "ci"}, self.authorization, waiting_on="GitHub Actions")
        complete = atom.response({"phase": "resolved"}, self.authorization, status="resolved")
        cases = [
            ({**ready, "continuation_state": []}, "continuation_state"),
            ({**ready, "owner": None}, "owner:"),
            ({**ready, "next": None}, "next:"),
            ({**ready, "next": {**ready["next"], "argv": []}}, "next.argv"),
            ({**ready, "next": {**ready["next"], "argv": [""]}}, "next.argv"),
            ({**ready, "next": {**ready["next"], "argv": ["command", 1]}}, "next.argv"),
            ({**ready, "next": {**ready["next"], "argv": ["bad\0command"]}}, "next.argv"),
            ({**ready, "next": {**ready["next"], "environment": []}}, "next.environment"),
            ({**ready, "next": {**ready["next"], "environment": {"TOKEN": None}}}, "next.environment"),
            ({**ready, "next": {**ready["next"], "environment": {"BAD=NAME": "value"}}}, "next.environment"),
            ({**ready, "next": {**ready["next"], "required": ["missing_input"]}}, "next.required"),
            ({**ready, "next": {**ready["next"], "kind": "input"}}, "next.kind"),
            ({**ready, "waiting_on": "provider"}, "waiting_on"),
            ({**waiting, "next": {**waiting["next"], "required": []}}, "next.required"),
            ({**waiting, "next": {**waiting["next"], "required": "changed"}}, "next.required"),
            ({**waiting, "continuation_state": "ready"}, "status:"),
            ({**waiting, "continuation_state": "input_required"}, "status:"),
            ({**complete, "next": ready["next"]}, "complete:"),
            ({**complete, "status": "pending"}, "complete:"),
            ({**complete, "waiting_on": "provider"}, "waiting_on"),
        ]
        for result, gap in cases:
            with self.subTest(result=result, gap=gap):
                transition = self.project(result, "unknown", "owner_readback_required")
                self.assertTrue(any(item.startswith(gap) for item in transition["gaps"]))


if __name__ == "__main__":
    unittest.main()
