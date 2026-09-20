#!/usr/bin/env python3
"""Externally frozen observer for exact-head candidate evidence verification."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


SUBJECT = "policy.md"
MANIFEST = "evidence/manifest.json"
TASK = "evidence/task.md"
OBSERVER = "evidence/observer.py"
BASELINE_RAW = "evidence/raw/baseline.json"
TREATMENT_RAW = "evidence/raw/treatment.json"
NONCASE_RAW = "evidence/raw/noncase.json"
RESULTS = "evidence/results.md"
REQUIRED = [SUBJECT, MANIFEST, TASK, OBSERVER, BASELINE_RAW,
            TREATMENT_RAW, NONCASE_RAW, RESULTS]


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
    git(root, "-c", "user.name=Exact Head Observer",
        "-c", "user.email=observer@example.invalid", "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def contract(base, task_sha, observer_sha):
    return {
        "schema": 3,
        "trigger": "Exact candidate bytes can avoid the workflow gate.",
        "source": "Externally frozen exact-head observer.",
        "owner": "Soodles candidate verification",
        "changes": ["Verify the exact candidate tree before runtime acceptance."],
        "write_paths": REQUIRED,
        "required_paths": REQUIRED,
        "evidence_manifest": MANIFEST,
        "base_head": base,
        "frozen_paths": [
            {"path": TASK, "revision": "head", "sha256": task_sha},
            {"path": OBSERVER, "revision": "head", "sha256": observer_sha},
        ],
        "behavior": ["Invalid exact candidate bytes refuse."],
        "defect_controls": ["Change one bound byte."],
        "non_cases": ["The complete candidate remains legal."],
        "dependencies": [],
        "acceptance": "The frozen observer records treatment GREEN.",
        "delivery": "One non-authorizing candidate receipt.",
        "reconciliation": "Read back the exact provider head.",
        "feature_scope": "Exact candidate byte binding only.",
    }


def issue_body(contract_value):
    return ("<!-- soodles:execution-v1 -->\n```json\n"
            + json.dumps(contract_value, sort_keys=True, indent=2)
            + "\n```\n<!-- /soodles:execution-v1 -->\n")


def evidence_manifest(issue, baseline, treatment, artifacts):
    return {
        "schema": 1,
        "issue": {"repository": "ed3c/soodles", "number": issue},
        "instructions": [{
            "path": SUBJECT,
            "baseline_sha256": digest(baseline),
            "treatment_sha256": digest(treatment),
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
    baseline = b"baseline policy\n"
    treatment = b"baseline policy\nverify exact candidate bytes\n"
    task = b"fixed exact-head task\n"
    observer = b"fixed external observer\n"
    baseline_raw = b'{"classification":"RED"}\n'
    treatment_raw = b'{"classification":"GREEN"}\n'
    noncase_raw = b'{"classification":"GREEN","case":"complete"}\n'
    results = b"# Exact-head result\n\nInvalid bytes refuse.\n"
    base_artifacts = [
        (TASK, "experiment_task", task),
        (OBSERVER, "observer", observer),
        (BASELINE_RAW, "baseline_raw_receipt", baseline_raw),
        (TREATMENT_RAW, "treatment_raw_receipt", treatment_raw),
        (NONCASE_RAW, "legal_noncase_receipt", noncase_raw),
        (RESULTS, "results", results),
    ]
    records = []
    for case in ("prompt_mismatch", "frozen_observer_mismatch", "complete"):
        with tempfile.TemporaryDirectory(prefix="exact-head-binding-") as folder:
            root = Path(folder)
            git(root, "init", "-b", "main")
            write(root, SUBJECT, baseline)
            base = commit(root, "baseline")
            actual_treatment = treatment + (b"tamper\n" if case == "prompt_mismatch" else b"")
            write(root, SUBJECT, actual_treatment)
            artifacts = list(base_artifacts)
            if case == "frozen_observer_mismatch":
                artifacts[1] = (OBSERVER, "observer", b"candidate-selected observer\n")
            for path, _, data in artifacts:
                write(root, path, data)
            manifest = evidence_manifest(issue, baseline, treatment, artifacts)
            write(root, MANIFEST,
                  (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
            head = commit(root, case)
            selected = contract(base, digest(task), digest(observer))
            body = issue_body(selected)
            readback = {
                "url": f"https://api.github.com/repos/ed3c/soodles/issues/{issue}",
                "html_url": f"https://github.com/ed3c/soodles/issues/{issue}",
                "number": issue,
                "body": body,
                "updated_at": "2026-09-20T00:00:00Z",
                "state": "open",
            }
            record = {"case": case}
            if mode == "baseline" or not hasattr(module, "verify_candidate"):
                record["outcome"] = "accepted"
            else:
                try:
                    module.verify_candidate(root, base, head, readback)
                    record["outcome"] = "accepted"
                except module.AdmissionRefusal as refusal:
                    record.update(outcome="refused",
                                  field=refusal.invalid["field"])
            records.append(record)
    expected = {
        "baseline": {
            "prompt_mismatch": ("accepted", None),
            "frozen_observer_mismatch": ("accepted", None),
            "complete": ("accepted", None),
        },
        "treatment": {
            "prompt_mismatch": ("refused", "candidate.instruction.treatment_sha256"),
            "frozen_observer_mismatch": ("refused", "candidate.frozen_path.sha256"),
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
    result = observe(load_module(Path(args.module).resolve()), args.issue, args.mode)
    print(json.dumps(result, sort_keys=True, indent=2))
    return int(result["classification"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
