import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/schedule/SKILL.md"
FIXTURE = (
    ROOT
    / "tests/fixtures/admission-recovery-portable/preserved-soodles-input"
)
SESSION = "schedule-20260916-170423-d53732"


def is_schedule_session(session_id, control_root, checkout):
    """Read only Noodle-owned identity needed before launcher admission."""
    if not session_id:
        return False
    spawn_path = control_root / ".noodle/sessions" / session_id / "spawn.json"
    try:
        spawn = json.loads(spawn_path.read_text())
    except (OSError, ValueError, TypeError):
        return False
    return (
        spawn.get("session_id") == session_id
        and spawn.get("skill") == "schedule"
        and Path(spawn.get("worktree_path", "")).resolve()
        == Path(checkout).resolve()
    )


class ScheduleRoleBoundaryTests(unittest.TestCase):
    def test_preserved_missing_launcher_session_is_a_real_scheduler(self):
        spawn_path = FIXTURE / ".noodle/sessions" / SESSION / "spawn.json"
        meta_path = FIXTURE / ".noodle/sessions" / SESSION / "meta.json"
        spawn = json.loads(spawn_path.read_text())
        meta = json.loads(meta_path.read_text())

        self.assertTrue(
            is_schedule_session(SESSION, FIXTURE, spawn["worktree_path"])
        )
        self.assertEqual(spawn["skill"], "schedule")
        self.assertIn("SOODLES_ADMISSION_LAUNCHER is unset", meta["current_action"])
        self.assertIn("exit 64", meta["current_action"])

    def test_missing_noodle_identity_does_not_create_launcher_prerequisite(self):
        self.assertFalse(is_schedule_session("", FIXTURE, "/tmp/analysis"))

    def test_missing_or_mismatched_spawn_cannot_establish_schedule_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / ".noodle/sessions/session-a"
            sessions.mkdir(parents=True)
            checkout = root / "worktree"
            checkout.mkdir()

            cases = [
                {
                    "session_id": "session-b",
                    "skill": "schedule",
                    "worktree_path": str(checkout),
                },
                {
                    "session_id": "session-a",
                    "skill": "execute",
                    "worktree_path": str(checkout),
                },
                {
                    "session_id": "session-a",
                    "skill": "schedule",
                    "worktree_path": str(root / "foreign"),
                },
            ]
            for index, spawn in enumerate(cases):
                with self.subTest(index=index):
                    (sessions / "spawn.json").write_text(json.dumps(spawn))
                    self.assertFalse(
                        is_schedule_session("session-a", root, checkout)
                    )

            (sessions / "spawn.json").unlink()
            self.assertFalse(is_schedule_session("session-a", root, checkout))

    def test_skill_puts_role_readback_before_launcher_requirement(self):
        text = SKILL.read_text()
        role = text.index("## Establish scheduler identity first")
        launcher = text.index("## Consume the admitted launcher")
        self.assertLess(role, launcher)
        self.assertIn(
            "If it is\nabsent, this Skill does not establish a Noodle schedule Session",
            text,
        )
        self.assertIn(
            "A missing or\nmismatched spawn is a Noodle/supervisor role-identity refusal",
            text,
        )
        self.assertIn("Do not dump the environment.", text)
        self.assertIn("never search for, synthesize, export, or reuse", text)


if __name__ == "__main__":
    unittest.main()
