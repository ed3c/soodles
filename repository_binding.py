"""Trusted repository identities and repository-owned acceptance surfaces.

The installed supervisor selects a repository through an external envelope or
claim.  Agents cannot add targets or redefine acceptance through CLI flags.
"""
import hashlib
import json
from pathlib import Path
import re


PROFILES = {
    "ed3c/soodles": {
        "base_ref": "main",
        "workflow_path": ".github/workflows/runtime.yml",
        "jobs": {
            "runtime-evidence": ["Canonical acceptance on the exact candidate head"],
        },
    },
    "ed3c/ops-reconciliation-copilot": {
        "base_ref": "main",
        "workflow_path": ".github/workflows/runtime.yml",
        "jobs": {
            "runtime": [
                "Run python scripts/verify_runtime.py",
                "Run python scripts/verify_owner.py",
                "Run python scripts/verify_browser.py",
                "Run python scripts/verify_mapping.py",
            ],
            "postgres": [
                "Run python scripts/verify_runtime.py",
                "Run python scripts/verify_owner.py",
                "Run python scripts/verify_postgres.py",
                "Run python scripts/verify_browser.py",
                "Run python scripts/verify_mapping.py",
            ],
        },
    },
}


def valid_name(value):
    return (isinstance(value, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value) is not None)


def profile(value):
    return PROFILES.get(value)


def selected(subject, require):
    """Resolve the supervisor's one immutable target reference at the boundary."""
    repository = subject.get("repository")
    ref = subject.get("target_binding")
    if ref is None:
        result = profile(repository)
        require(result is not None, "binding.repository", repository)
        return result
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "binding.reference", ref)
    name = ref["path"]
    require(isinstance(name, str) and Path(name).is_absolute(), "binding.path", name)
    path = Path(name)
    require(path.is_file() and not path.is_symlink() and path.resolve() == path,
            "binding.path", name)
    root = subject.get("control_root") or subject.get("execution", {}).get("control_root")
    if root:
        require(not path.is_relative_to(Path(root).resolve()), "binding.external", name)
    try:
        raw = path.read_bytes()
        require(isinstance(ref["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])
                and hashlib.sha256(raw).hexdigest() == ref["sha256"], "binding.sha256", name)
        def unique(pairs):
            value = {}
            for key, item in pairs:
                require(key not in value, "binding.duplicate_key", key)
                value[key] = item
            return value
        result = json.loads(raw, object_pairs_hook=unique)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        require(False, "binding.read", type(error).__name__)
    require(isinstance(result, dict) and set(result) == {
        "schema", "repository", "base_ref", "workflow_path", "jobs", "verification"},
        "binding.fields", name)
    require(type(result["schema"]) is int and result["schema"] == 1, "binding.schema", result["schema"])
    require(valid_name(repository) and result["repository"] == repository,
            "binding.repository", result["repository"])
    base = result["base_ref"]
    require(isinstance(base, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", base)
            and not any(part in base for part in ("..", "//", "@{"))
            and not base.endswith(("/", ".", ".lock")), "binding.base_ref", base)
    workflow = result["workflow_path"]
    require(isinstance(workflow, str) and re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml", workflow),
            "binding.workflow_path", workflow)
    jobs = result["jobs"]
    require(isinstance(jobs, dict) and bool(jobs), "binding.jobs", jobs)
    for job, steps in jobs.items():
        require(isinstance(job, str) and bool(job.strip()) and isinstance(steps, list)
                and bool(steps) and all(isinstance(step, str) and step.strip() for step in steps)
                and len(steps) == len(set(steps)), "binding.jobs.steps", job)
    require(isinstance(result["verification"], dict), "binding.verification", result["verification"])
    return result


def validate_run(subject, run, jobs, head, require, *, allow_failure=False):
    acceptance = selected(subject, require)
    require(isinstance(run, dict) and type(run.get("id")) is int and run["id"] > 0
            and type(run.get("run_attempt")) is int and run["run_attempt"] > 0,
            "run.identity", run)
    require(all((run.get(key) or {}).get("full_name") == subject["repository"]
                for key in ("repository", "head_repository")), "run.repository", run)
    require(run.get("head_sha") == head and run.get("event") == "pull_request"
            and run.get("path") == acceptance["workflow_path"]
            and run.get("status") == "completed", "run.subject", run)
    expected = acceptance["jobs"]
    values = jobs.get("jobs") if isinstance(jobs, dict) else None
    require(isinstance(values, list) and all(isinstance(job, dict) for job in values)
            and jobs.get("total_count") == len(values) == len(expected), "jobs.count", jobs)
    observed = {job.get("name"): job for job in values}
    require(set(observed) == set(expected), "jobs.names", list(observed))
    conclusions = [run.get("conclusion")]
    for name, required_steps in expected.items():
        job = observed[name]
        require(job.get("run_id") == run["id"] and job.get("run_attempt") == run["run_attempt"]
                and job.get("head_sha") == head and job.get("status") == "completed",
                "job.identity", name)
        steps = job.get("steps")
        require(isinstance(steps, list) and all(isinstance(step, dict) for step in steps),
                "job.steps", name)
        conclusions.append(job.get("conclusion"))
        for wanted in required_steps:
            matches = [step for step in steps if step.get("name") == wanted]
            require(len(matches) == 1 and matches[0].get("status") == "completed",
                    "job.required_step", {"job": name, "step": wanted})
            conclusions.append(matches[0].get("conclusion"))
    if allow_failure and conclusions[0] == "failure":
        require("failure" in conclusions[1:] and all(value in {"success", "failure", "skipped"}
                                                    for value in conclusions),
                "run.failure", conclusions)
        return False
    require(all(value == "success" for value in conclusions), "run.conclusion", conclusions)
    return True


def issue_urls(repository, number):
    return (f"https://api.github.com/repos/{repository}/issues/{number}",
            f"https://github.com/{repository}/issues/{number}")


def git_origins(repository):
    return {f"https://github.com/{repository}.git", f"git@github.com:{repository}.git"}
