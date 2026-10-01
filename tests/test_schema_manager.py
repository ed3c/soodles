"""Fixed protocol controls; no model/provider effects or recurring timing gate."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import schema_manager as manager

ROOT = Path(manager.__file__).parent


def fact(value, evidence="readback"):
    return {"value": value, "evidence": manager.digest(evidence)}


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
                owner.observe({"owner_confirmed": fact(True)})
            self.assertNotEqual(owner.project()["status"], "complete")
        self.owner.observe({k: fact(True) for k in
                            ("cleanup_allowed", "landing_resolved", "loop_absent", "config_restored")})
        self.assertIn("confirm", self.owner.project()["ready"])
        self.assertNotEqual(self.owner.project()["status"], "complete")
        self.owner.observe({"owner_confirmed": fact(True)})
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
        self.owner.observe({"owner_confirmed": fact(True)})
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
                patch.object(manager, "compile_repair", side_effect=AssertionError("hot context")):
            self.owner.observe({"cleanup_allowed": fact(True)})
            self.owner.apply(self.owner.record())
            self.owner.project()
        self.assertEqual(self.plan.context["consumer"], "issue_atom.finish_host")
        self.assertEqual(self.plan.context["requires"], [
            "contracts/system-v1/common.md", "contracts/system-v1/issue-atom.md"])

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


if __name__ == "__main__":
    unittest.main()
