#!/usr/bin/env python3
"""Summarize fixed raw drives; model decisions remain a separate claim."""
import hashlib
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parent
oracle = root / "evaluator"
manifest = oracle / "manifest.json"
assert hashlib.sha256(manifest.read_bytes()).hexdigest() == "22f3b5cd7fb458a29f21c0281f52211974cda769f0e9f2ca8e1d4f5c39bf0ba7"
for name, expected in json.loads(manifest.read_text())["files"].items():
    assert hashlib.sha256((oracle / name).read_bytes()).hexdigest() == expected, name
spec = importlib.util.spec_from_file_location("fixed_claim_evaluator", oracle / "evaluate.py")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)
rows = []
for case in ("refusal", "refusal75", "running", "success", "resume_initial", "resume_running", "resume_success"):
    runs = {}
    for arm, folder in (("baseline", "baseline-r03"), ("treatment", "treatment-r01")):
        raw = json.loads((root / "verification" / folder / (case + ".stdout")).read_text())
        runs[arm] = {"status": raw["result"]["status"],
                     "claim_processes": len(raw["claim_processes"]),
                     "fake_sleeps": len(raw["sleeps"]),
                     "checks": evaluator.assess(raw, raw["mode"])}
    rows.append({"case": case, **runs})
print(json.dumps({"runtime": rows,
                  "all_treatment_cases_pass": all(row["treatment"]["checks"]["pass"] for row in rows),
                  "agent_decisions": "See independently frozen behavior decision; runtime metrics do not measure Agent effort.",
                  "authorizes_landing": False}, indent=2))
