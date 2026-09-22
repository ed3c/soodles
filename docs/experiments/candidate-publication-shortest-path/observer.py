#!/usr/bin/env python3
"""Non-authorizing observer for the candidate-publication shortest path."""
import json
from pathlib import Path
import subprocess
import sys


def observe(source):
    source = Path(source).resolve()
    skill = source / ".agents/skills/candidate-publication/SKILL.md"
    entry = source / "candidate-publish"
    errors = []
    if not skill.is_file():
        errors.append("missing_pclass_route")
    else:
        text = skill.read_text()
        if "./candidate-publish /absolute/acceptance.json /absolute/noodle-claim.json" not in text:
            errors.append("missing_single_owner_command")
        forbidden = ("git push", "gh pr create", "connector PR mutation")
        if not all(value in text for value in forbidden):
            errors.append("missing_manual_path_prohibition")
    if not entry.is_file() or not entry.stat().st_mode & 0o111:
        errors.append("missing_executable_entry")
    else:
        result = subprocess.run([str(entry), "--help"], cwd=source,
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30)
        if result.returncode or "acceptance_receipt" not in result.stdout or "noodle_claim" not in result.stdout:
            errors.append("entry_help_not_executable")
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest",
                            "tests.test_candidate_publication"], cwd=source,
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=60)
    if tests.returncode:
        errors.append("focused_behavior_red")
    barrier = int(any(error in errors for error in (
        "missing_pclass_route", "missing_single_owner_command",
        "missing_executable_entry", "entry_help_not_executable")))
    return {"classification": "PASS" if not errors else "FAIL",
            "primary_barrier": barrier, "errors": errors,
            "focused_tests_exit": tests.returncode,
            "authorizes_landing": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: observer.py SOURCE")
    result = observe(sys.argv[1])
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(result["classification"] != "PASS")
