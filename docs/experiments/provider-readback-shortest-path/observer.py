#!/usr/bin/env python3
"""Bounded #126 local provider-readback discriminator."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import provider_readback
from test_provider_readback import Fixture


def main():
    fixture = Fixture()
    try:
        env = {"GH_TOKEN": "fixture-token"}

        landing_out = fixture.external / "observer-landing"
        landing = provider_readback.consume(
            fixture.landing_result(merged=True),
            fixture.context,
            landing_out,
            environ=env,
            api=fixture.landing_api(True),
        )

        skill = (ROOT / ".agents/skills/provider-readback/SKILL.md").read_text()
        verify = (ROOT / ".agents/skills/verify-noodle/SKILL.md").read_text()

        checks = {
            "landing_materialized": (
                landing["consumer"] == "landing"
                and landing["next"]["kind"] == "executable"
                and landing["next"]["operation"] == "advance"
                and Path(landing["readback"]).is_file()
            ),
            "merge_commit_exactly_once": (
                len([
                    call for call in fixture.calls
                    if "/git/commits/" + "d" * 40 in call[1]
                ]) == 1
            ),
            "no_provider_write": all(call[0] == "GET" for call in fixture.calls),
            "pclass_one_entry": (
                "./provider-readback consume" in skill
                and "provider-readback Skill" in verify
            ),
            "no_manual_assembly": (
                "do not translate GETs, pagination" in verify
                and "Do not use curl, gh, browser" in skill
            ),
        }
        receipt = {
            "schema": 1,
            "issue": {"repository": "ed3c/soodles", "number": 126},
            "classification": "VERIFIED" if all(checks.values()) else "FAILED",
            "checks": checks,
            "decision_surface": {
                "provider_url_assembly_by_agent": False,
                "pagination_by_agent": False,
                "snapshot_key_assembly_by_agent": False,
                "owner_reentry_assembly_by_agent": False,
            },
            "pclass_disposition": "SCOPED_ALIGNMENT",
            "authorizes_landing": False,
        }
        print(json.dumps(receipt, indent=2))
        return 0 if receipt["classification"] == "VERIFIED" else 1
    finally:
        fixture.close()


if __name__ == "__main__":
    raise SystemExit(main())
