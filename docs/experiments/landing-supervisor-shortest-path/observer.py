#!/usr/bin/env python3
"""Bounded #122 discriminator: terminal candidate -> landing owner activation."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_landing_supervisor import SupervisorFixture


def main():
    fixture = SupervisorFixture()
    try:
        cloud_out, cloud = fixture.prepare("observer-cloud")
        local_snapshot, local_route = fixture.local_case()
        local_out, local = fixture.prepare(
            "observer-local", snapshot=local_snapshot, route=local_route)

        agents = (ROOT / "AGENTS.md").read_text()
        section = agents.split("Terminal candidate delivery entry", 1)[1].split("\n## ", 1)[0]
        checks = {
            "cloud_activated": (
                cloud["route"] == "cloud"
                and cloud["landing_owner"]["owner"] == "landing.start"
                and cloud["landing_owner"]["action"] == "readback"
                and cloud["landing_owner"]["next"]["kind"] == "provider_readback"
                and Path(cloud["checkpoint"]).is_file()
            ),
            "local_activated": (
                local["route"] == "local"
                and local["landing_owner"]["owner"] == "landing.start"
                and local["landing_owner"]["action"] == "readback"
                and local["claim"]["control_root"] == local_route["control_root"]
                and local["claim"]["execution_envelope"]["sha256"]
                == local_route["execution_envelope"]["sha256"]
                and Path(local["checkpoint"]).is_file()
            ),
            "external_outputs": (
                not cloud_out.is_relative_to(ROOT)
                and not local_out.is_relative_to(ROOT)
            ),
            "pclass_single_entry": (
                "landing-supervisor" in section
                and "current landing-owner `next` exactly" in section
            ),
            "pclass_no_discovery": all(value not in section for value in (
                "git log", "landing start --help", "choose `start`",
            )),
        }
        receipt = {
            "schema": 1,
            "issue": {"repository": "ed3c/soodles", "number": 122},
            "classification": "VERIFIED" if all(checks.values()) else "FAILED",
            "checks": checks,
            "decision_surface": {
                "publisher_selected_by_agent": False,
                "claim_constructed_by_agent": False,
                "checkpoint_selected_by_agent": False,
                "landing_verb_selected_by_agent": False,
                "current_owner_next_exposed": True,
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
