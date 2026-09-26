#!/usr/bin/env python3
"""External discriminator for landing-supervisor's returned continuation paths."""
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
        output, result = fixture.prepare("continuation")
        action = result["landing_owner"]["next"]
        expected_checkpoint = str(output / "checkpoint.json")
        expected_readback = str(output / "readback.json")
        checks = {
            "checkpoint": Path(expected_checkpoint).is_file()
                          and action["known"]["checkpoint"] == expected_checkpoint,
            "readback": Path(expected_readback).is_file()
                        and action["known"]["readback"] == expected_readback,
            "argv": action["argv"][-2:] == [expected_checkpoint, expected_readback],
            "single_activation": result["action"] == "activated"
                                 and result["authorizes_landing"] is False,
        }
        print(json.dumps({"classification": "VERIFIED" if all(checks.values()) else "FAILED",
                          "checks": checks, "authorizes_landing": False}, indent=2))
        return 0 if all(checks.values()) else 1
    finally:
        fixture.close()


if __name__ == "__main__":
    raise SystemExit(main())
