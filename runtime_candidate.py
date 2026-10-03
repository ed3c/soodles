"""Bind runtime PR inputs to the admitted base before strict verification."""
import re
import subprocess

from issue_admission import AdmissionRefusal, parse_contract, require, verify_candidate
from repository_binding import issue_urls, profile, valid_name


def _git(root, field, *args):
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AdmissionRefusal(field, str(error), "Git", "exact_commit_ancestry") from error


def _require_commit(root, revision, field):
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision),
            field, revision, owner="Git", required="exact_commit_identity")
    result = _git(root, field, "cat-file", "-t", revision)
    require(result.returncode == 0 and result.stdout.strip() == "commit",
            field, {"revision": revision, "type": result.stdout.strip(),
                    "returncode": result.returncode, "stderr": result.stderr.strip()},
            owner="Git", required="exact_commit_identity")


def _require_ancestor(root, ancestor, descendant, field):
    result = _git(root, field, "merge-base", "--is-ancestor", ancestor, descendant)
    require(result.returncode == 0,
            field, {"ancestor": ancestor, "descendant": descendant,
                    "returncode": result.returncode, "stderr": result.stderr.strip()},
            owner="Git", required="exact_commit_ancestry")


def verify_pull_request(root, event_base, head, readback, *, issue_number, repository):
    """Return strict evidence for the PR-selected Issue and its admitted base."""
    source = {"owner": "GitHub", "required": "fresh_issue_readback"}
    require(isinstance(readback, dict), "candidate.issue_readback", readback, **source)
    issue = readback
    if readback.get("owner") == "github.issue":
        require(readback.get("status") == "read" and readback.get("next") is None
                and readback.get("authorizes_landing") is False,
                "candidate.issue_readback", readback.get("status"), **source)
        issue = readback.get("issue")
    require(isinstance(issue, dict), "candidate.issue_readback", issue, **source)
    require(type(issue_number) is int and issue_number > 0
            and type(issue.get("number")) is int and issue["number"] == issue_number,
            "runtime.issue.number", {"expected": issue_number, "actual": issue.get("number")},
            owner="GitHub", required="pr_selected_issue_readback")
    require(valid_name(repository) and profile(repository) is not None,
            "runtime.issue.repository", repository,
            owner="supervisor", required="supported_repository_readback")
    api_url, html_url = issue_urls(repository, issue_number)
    require(issue.get("url") == api_url and issue.get("html_url") == html_url,
            "runtime.issue.repository", {"expected": repository,
                                         "url": issue.get("url"), "html_url": issue.get("html_url")},
            owner="GitHub", required="pr_selected_issue_readback")
    contract = parse_contract(issue.get("body"))
    base = event_base
    if contract["schema"] >= 3:
        base = contract["base_head"]
        for revision, field in ((event_base, "runtime.event_base"),
                                (base, "runtime.admitted_base"), (head, "runtime.head")):
            _require_commit(root, revision, field)
        _require_ancestor(root, event_base, base, "runtime.event_base_ancestry")
        _require_ancestor(root, base, head, "runtime.admitted_base_ancestry")
    receipt = verify_candidate(root, base, head, readback)
    return {**receipt, "event_base": event_base}
