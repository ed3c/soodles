"""Trusted repository identities and repository-owned acceptance surfaces.

The installed supervisor selects a repository through an external envelope or
claim.  Agents cannot add targets or redefine acceptance through CLI flags.
"""
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


def issue_urls(repository, number):
    return (f"https://api.github.com/repos/{repository}/issues/{number}",
            f"https://github.com/{repository}/issues/{number}")


def git_origins(repository):
    return {f"https://github.com/{repository}.git", f"git@github.com:{repository}.git"}
