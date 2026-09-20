#!/usr/bin/env python3
"""Frozen black-box observer for candidate evidence admission.

The issue selects these bytes before implementation. The candidate module is
only the subject. This observer creates real Git commits and calls the existing
delivery-path entry.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


PROMPT = ".agents/skills/verify-soodles/features/pclass-context.md"
MANIFEST = "docs/experiments/pclass-atom-binding/manifest.json"
TASK = "docs/experiments/pclass-atom-binding/task.md"
RAW = "docs/experiments/pclass-atom-binding/raw.json"
RESULTS = "docs/experiments/pclass-atom-binding/results.md"
REQUIRED = [PROMPT, MANIFEST, TASK, RAW, RESULTS]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location("candidate_admission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def write(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def commit(root, message):
    git(root, "add", ".")
    git(root, "-c", "user.name=Atom Observer",
        "-c", "user.email=observer@example.invalid", "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def manifest(issue, baseline_prompt, treatment_prompt, artifacts):
    return {
        "schema": 1,
        "issue": {"repository": "ed3c/soodles", "number": issue},
        "instructions": [{
            "path": PROMPT,
            "baseline_sha256": digest(baseline_prompt),
            "treatment_sha256": digest(treatment_prompt),
        }],
        "artifacts": [
            {"path": path, "role": role, "sha256": digest(data)}
            for path, role, data in artifacts
        ],
        "owner": {
            "name": "Soodles Issue admission",
            "tool": "issue_admission.validate_delivery_paths",
            "authorization": f"ed3c/soodles#{issue}",
        },
        "authorizes_landing": False,
    }


def observe(module, issue, mode):
    records = []
    baseline_prompt = b"baseline prompt\n"
    treatment_prompt = b"baseline prompt\nrequired evidence binding\n"
    task = b"exercise missing, mismatched and complete candidate evidence\n"
    raw = b'{"baseline":"missing evidence accepted","treatment":"fail closed"}\n'
    results = b"# Candidate evidence binding\n\nMissing and mismatched evidence must refuse.\n"
    artifacts = [(TASK, "experiment_task", task),
                 (RAW, "raw_receipt", raw),
                 (RESULTS, "results", results)]

    for case in ("missing", "mismatch", "complete"):
        with tempfile.TemporaryDirectory(prefix="pclass-atom-binding-") as folder:
            root = Path(folder)
            git(root, "init", "-b", "main")
            write(root, PROMPT, baseline_prompt)
            base = commit(root, "baseline")
            write(root, PROMPT, treatment_prompt)
            if case != "missing":
                for path, _, data in artifacts:
                    write(root, path, data)
                selected = manifest(issue, baseline_prompt, treatment_prompt, artifacts)
                if case == "mismatch":
                    selected["instructions"][0]["treatment_sha256"] = "0" * 64
                write(root, MANIFEST, (json.dumps(selected, sort_keys=True, indent=2) + "\n").encode())
            head = commit(root, case)
            binding = {
                "issue": issue,
                "base_head": base,
                "write_paths": REQUIRED,
                "contract": {
                    "schema": 2,
                    "candidate_evidence": {
                        "manifest_path": MANIFEST,
                        "required_paths": REQUIRED,
                    },
                },
            }
            record = {"case": case}
            try:
                receipt = module.validate_delivery_paths(root, base, head, binding)
                record.update({"outcome": "accepted",
                               "changed_paths": receipt["changed_paths"]})
            except module.AdmissionRefusal as refusal:
                record.update({"outcome": "refused",
                               "field": refusal.invalid["field"]})
            records.append(record)

    expected = {
        "baseline": {
            "missing": ("accepted", None),
            "mismatch": ("accepted", None),
            "complete": ("accepted", None),
        },
        "treatment": {
            "missing": ("refused", "candidate.missing_required_paths"),
            "mismatch": ("refused", "candidate.instruction.treatment_sha256"),
            "complete": ("accepted", None),
        },
    }[mode]
    errors = []
    for record in records:
        outcome, field = expected[record["case"]]
        if record["outcome"] != outcome or record.get("field") != field:
            errors.append(record["case"])
    return {
        "schema": 1,
        "phase": mode,
        "classification": ("RED" if mode == "baseline" and not errors
                           else "GREEN" if not errors else "FAIL"),
        "records": records,
        "errors": errors,
        "observer_sha256": digest(Path(__file__).read_bytes()),
        "authorizes_landing": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("module")
    parser.add_argument("issue", type=int)
    parser.add_argument("mode", choices=("baseline", "treatment"))
    args = parser.parse_args()
    receipt = observe(load_module(Path(args.module).resolve()), args.issue, args.mode)
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return int(receipt["classification"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
