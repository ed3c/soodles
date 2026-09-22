#!/usr/bin/env python3
"""Bounded #124 discriminator."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import next_issue
from test_next_issue import candidate, frontier, packet, resolved, provider_issue


def main():
    with __import__("tempfile").TemporaryDirectory() as directory:
        root = Path(directory).resolve()

        one = next_issue.prepare(
            resolved(), packet(candidate("one")), frontier(),
            {"kind": "cloud"}, root / "one")

        many = next_issue.prepare(
            resolved(), packet(candidate("a"), candidate("b")), frontier(),
            {"kind": "cloud"}, root / "many")

        duplicate_candidate = candidate("dup")
        duplicate_body = next_issue._body(
            duplicate_candidate, next_issue._fingerprint(duplicate_candidate))
        duplicate = next_issue.prepare(
            resolved(), packet(duplicate_candidate),
            frontier(provider_issue("ed3c/soodles", 9, body=duplicate_body)),
            {"kind": "cloud"}, root / "duplicate")

        skill = (ROOT / ".agents/skills/next-issue/SKILL.md").read_text()
        checks = {
            "unique_create_intent": (
                one["action"] == "create"
                and one["next"]["kind"] == "provider_write"
                and (root / "one/intent.json").is_file()
            ),
            "multiple_requires_supervisor": (
                many["action"] == "select"
                and many["next"]["owner"] == "supervisor"
                and many["next"]["required"] == ["selected_candidate"]
                and not (root / "many").exists()
            ),
            "duplicate_stops": (
                duplicate["action"] == "stop"
                and duplicate["next"] is None
                and not (root / "duplicate").exists()
            ),
            "pclass_one_entry": (
                "./next-issue prepare" in skill
                and "consume the current next exactly" in skill
            ),
        }
        receipt = {
            "schema": 1,
            "issue": {"repository": "ed3c/soodles", "number": 124},
            "classification": "VERIFIED" if all(checks.values()) else "FAILED",
            "checks": checks,
            "decision_surface": {
                "backlog_discovery_by_agent": False,
                "candidate_priority_by_agent": False,
                "issue_body_assembly_by_agent": False,
                "transport_selection_by_agent": False,
            },
            "pclass_disposition": "SCOPED_ALIGNMENT",
            "authorizes_landing": False,
        }
        print(json.dumps(receipt, indent=2))
        return 0 if receipt["classification"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
