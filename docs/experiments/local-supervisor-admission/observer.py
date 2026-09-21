#!/usr/bin/env python3
"""Run the frozen local-supervisor admission discriminator."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_supervisor_admission import observe_baseline_and_treatment, observe_sensitivity


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: observer.py OUTPUT_DIRECTORY")
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)

    paired = observe_baseline_and_treatment()
    sensitivity = observe_sensitivity()
    baseline = paired["baseline"]
    treatment = paired["treatment"]

    checks = {
        "baseline_missing_launcher": (
            baseline["field"] == "scheduler.launcher"
            and baseline["owner"] == "supervisor"
            and baseline["required"] == ["SOODLES_ADMISSION_LAUNCHER"]
            and baseline["proposal_exists"] is False
        ),
        "treatment_exact_route": (
            treatment["prepared_action"] == "ready"
            and treatment["start_operation"] == "start_noodle"
            and treatment["inspect_action"] == "ready"
            and treatment["inspect_argv"][1] == "automatic"
            and treatment["launcher_exit"] == 0
            and treatment["launcher_action"] == "proposal_pending"
            and treatment["proposal_exists"] is True
        ),
        "committed_bytes_only": (
            treatment["status_unchanged_by_prepare"] is True
            and treatment["bundle_uses_committed_soodles"] is True
            and treatment["dirty_sentinel_excluded"] is True
        ),
        "non_authorizing": treatment["authorizes_landing"] is False,
        "sensitivity": (
            sensitivity["historical_unselected_launcher"]["field"] == "scheduler.launcher"
            and sensitivity["historical_unselected_launcher"]["historical_executed"] is False
            and sensitivity["envelope_tamper"]["exit"] == 64
            and sensitivity["envelope_tamper"]["proposal_exists"] is False
            and sensitivity["runtime_tamper"]["exit"] == 64
            and sensitivity["runtime_tamper"]["proposal_exists"] is False
            and sensitivity["existing_output"]["field"] == "supervisor.output.exists"
        ),
    }
    receipt = {
        "schema": 1,
        "issue": {"repository": "ed3c/soodles", "number": 118},
        "classification": "VERIFIED" if all(checks.values()) else "FAILED",
        "checks": checks,
        "source_sha256": {
            "supervisor_admission.py": sha(ROOT / "supervisor_admission.py"),
            "tests/test_supervisor_admission.py": sha(ROOT / "tests/test_supervisor_admission.py"),
            ".agents/skills/schedule/SKILL.md": sha(ROOT / ".agents/skills/schedule/SKILL.md"),
        },
        "authorizes_landing": False,
    }
    (output / "baseline.json").write_text(json.dumps(baseline, indent=2) + "\n")
    (output / "treatment.json").write_text(json.dumps(treatment, indent=2) + "\n")
    (output / "sensitivity.json").write_text(json.dumps(sensitivity, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["classification"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
