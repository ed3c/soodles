#!/usr/bin/env python3
"""Matched real candidate-verifier drives with fixed fixture Git identities."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def drive():
    prepare = load(HERE / "prepare.py", "fixed_guidance_fixture")
    modules = {"baseline": load(HERE / "inputs/baseline-admission.py", "old_admission"),
               "treatment": load(ROOT / "issue_admission.py", "new_admission")}
    original = {key: os.environ.get(key) for key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE")}
    for key in original:
        os.environ[key] = "2026-09-20T00:00:00Z"
    result = {}
    try:
        for arm, module in modules.items():
            prepare.issue_admission = module
            observations = {case: prepare.candidate(case) for case in "ABC"}
            case = json.loads((HERE / "inputs/B.json").read_text())
            case["subject"]["head"] = observations["B"]["head"]
            case["candidate_output"] = observations["B"]["output"]
            result[arm] = {"input": case, "observations": observations,
                           "module_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()}
        for label in "ABC":
            for field in ("head", "tree", "base", "input", "manifest"):
                assert result["baseline"]["observations"][label][field] == result["treatment"]["observations"][label][field], (label, field)
        old, new = copy.deepcopy(result["baseline"]["input"]), copy.deepcopy(result["treatment"]["input"])
        old["candidate_output"].pop("next")
        new["candidate_output"].pop("next")
        assert old == new
        return {"arms": result, "scope": "real function calls on disposable identical Git fixtures; no transport",
                "authorizes_landing": False}
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    print(json.dumps(drive(), sort_keys=True, indent=2))
