#!/usr/bin/env python3
"""RESOLVED -> one exact next-Issue provider identity.

The supervisor supplies semantic candidate atoms. This module owns only
mechanical qualification, deterministic Issue materialization, one persisted
create intent, narrow local create transport, and exact provider readback
adoption. It never invents product priority or a new task.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

import issue_admission
from repository_binding import profile


FINGERPRINT_PREFIX = "<!-- soodles:causal-atom-sha256:"
PACKET_FIELDS = {"schema", "selected_candidate", "candidates"}
CANDIDATE_FIELDS = {"candidate_id", "repository", "title", "contract"}
FRONTIER_FIELDS = {"schema", "complete", "issues"}
FRONTIER_ISSUE_FIELDS = {
    "repository", "number", "state", "state_reason", "closed_at", "html_url", "body"
}


class NextIssueRefusal(RuntimeError):
    def __init__(self, field, value, owner="supervisor", required="corrected_next_issue_input"):
        self.invalid = {"field": field, "value": value}
        self.next = {"kind": "input", "owner": owner, "required": [required]}
        super().__init__(f"next issue: invalid {field}={value!r}")


class ProviderUnknown(RuntimeError):
    pass


def require(condition, field, value, *, owner="supervisor", required="corrected_next_issue_input"):
    if not condition:
        raise NextIssueRefusal(field, value, owner, required)


def _read_json(path, field):
    path = Path(path).resolve()
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise NextIssueRefusal(field, type(error).__name__, required="valid_json_input") from error
    require(isinstance(value, dict), field, type(value).__name__, required="json_object")
    return value


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _fingerprint(candidate):
    contract = candidate["contract"]
    material = {
        "repository": candidate["repository"],
        "trigger": contract["trigger"].strip(),
        "owner": contract["owner"].strip(),
        "write_paths": sorted(contract["write_paths"]),
        "dependencies": contract["dependencies"],
    }
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _marker(digest):
    return FINGERPRINT_PREFIX + digest + " -->"


def _body(candidate, digest):
    return (
        _marker(digest)
        + "\n\n<!-- soodles:execution-v1 -->\n```json\n"
        + json.dumps(candidate["contract"], indent=2)
        + "\n```\n<!-- /soodles:execution-v1 -->\n"
    )


def _validate_resolved(receipt):
    require(isinstance(receipt, dict), "resolved", type(receipt).__name__)
    require(receipt.get("classification") == "RESOLVED",
            "resolved.classification", receipt.get("classification"),
            required="resolved_landing_receipt")
    require(receipt.get("phase") == "resolved",
            "resolved.phase", receipt.get("phase"),
            required="resolved_landing_receipt")
    require(receipt.get("next") is None,
            "resolved.next", receipt.get("next"),
            required="terminal_landing_receipt")
    claim = receipt.get("claim")
    require(isinstance(claim, dict), "resolved.claim", claim,
            required="resolved_landing_claim")
    repository = claim.get("repository")
    issue = claim.get("issue")
    require(isinstance(repository, str) and profile(repository) is not None,
            "resolved.claim.repository", repository,
            required="supported_resolved_repository")
    require(type(issue) is int and issue > 0, "resolved.claim.issue", issue,
            required="resolved_issue_identity")
    return {"repository": repository, "issue": issue}


def _validate_packet(packet):
    require(set(packet) == PACKET_FIELDS, "candidates.fields", sorted(packet))
    require(packet["schema"] == 1, "candidates.schema", packet["schema"])
    selected = packet["selected_candidate"]
    require(selected is None or (isinstance(selected, str) and bool(selected.strip())),
            "candidates.selected_candidate", selected)
    values = packet["candidates"]
    require(isinstance(values, list) and bool(values),
            "candidates", values, required="bounded_candidate_set")
    ids = []
    normalized = []
    for index, candidate in enumerate(values):
        field = f"candidates[{index}]"
        require(isinstance(candidate, dict) and set(candidate) == CANDIDATE_FIELDS,
                field + ".fields", sorted(candidate) if isinstance(candidate, dict) else candidate)
        candidate_id = candidate["candidate_id"]
        repository = candidate["repository"]
        title = candidate["title"]
        require(isinstance(candidate_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,99}", candidate_id),
                field + ".candidate_id", candidate_id)
        require(candidate_id not in ids, "candidates.candidate_id", candidate_id)
        ids.append(candidate_id)
        require(isinstance(repository, str) and profile(repository) is not None,
                field + ".repository", repository,
                required="supported_candidate_repository")
        require(isinstance(title, str) and bool(title.strip()) and "\n" not in title,
                field + ".title", title)
        contract = candidate["contract"]
        require(isinstance(contract, dict), field + ".contract", type(contract).__name__)
        require(contract.get("schema") == 1,
                field + ".contract.schema", contract.get("schema"),
                required="schema1_semantic_candidate")
        # Reuse the production parser to validate all semantic fields and paths.
        digest = _fingerprint(candidate)
        body = _body(candidate, digest)
        parsed = issue_admission.parse_contract(body)
        require(parsed["write_paths"] == sorted(contract["write_paths"]),
                field + ".contract.write_paths", contract["write_paths"])
        normalized.append({**candidate, "fingerprint": digest, "body": body})
    if selected is not None:
        require(selected in ids, "candidates.selected_candidate", selected,
                required="candidate_id_from_packet")
    return selected, normalized


def _validate_frontier(frontier):
    require(set(frontier) == FRONTIER_FIELDS,
            "frontier.fields", sorted(frontier))
    require(frontier["schema"] == 1, "frontier.schema", frontier["schema"])
    require(frontier["complete"] is True, "frontier.complete", frontier["complete"],
            owner="GitHub", required="complete_provider_frontier")
    issues = frontier["issues"]
    require(isinstance(issues, list), "frontier.issues", issues,
            owner="GitHub", required="complete_provider_frontier")
    identities = []
    normalized = []
    for index, issue in enumerate(issues):
        field = f"frontier.issues[{index}]"
        require(isinstance(issue, dict) and set(issue) == FRONTIER_ISSUE_FIELDS,
                field + ".fields", sorted(issue) if isinstance(issue, dict) else issue,
                owner="GitHub", required="exact_provider_issue_readback")
        repository, number = issue["repository"], issue["number"]
        require(isinstance(repository, str) and profile(repository) is not None,
                field + ".repository", repository,
                owner="GitHub", required="supported_provider_issue")
        require(type(number) is int and number > 0, field + ".number", number,
                owner="GitHub", required="provider_issue_identity")
        identity = (repository, number)
        require(identity not in identities, "frontier.issue.identity", list(identity),
                owner="GitHub", required="unique_provider_issue_identity")
        identities.append(identity)
        require(issue["html_url"] == f"https://github.com/{repository}/issues/{number}",
                field + ".html_url", issue["html_url"],
                owner="GitHub", required="provider_issue_identity")
        require(issue["state"] in {"open", "closed"}, field + ".state", issue["state"],
                owner="GitHub", required="provider_issue_state")
        normalized.append(issue)
    return normalized


def _dependency_satisfied(dependency, issues):
    matches = [
        issue for issue in issues
        if issue["repository"] == dependency["repository"]
        and issue["number"] == dependency["issue"]
    ]
    return (
        len(matches) == 1
        and matches[0]["state"] == "closed"
        and matches[0]["state_reason"] == "completed"
        and bool(matches[0]["closed_at"])
    )


def _open_contract(issue):
    if issue["state"] != "open" or not isinstance(issue.get("body"), str):
        return None
    if "soodles:execution-v1" not in issue["body"]:
        return None
    try:
        return issue_admission.parse_contract(issue["body"])
    except Exception:
        # An open malformed execution Issue is not safe to ignore as a write owner.
        raise NextIssueRefusal(
            "frontier.open_issue_contract", issue["html_url"],
            owner="GitHub", required="valid_open_issue_contract"
        )


def _eligibility(candidate, issues):
    reasons = []
    fingerprint = candidate["fingerprint"]
    marker = _marker(fingerprint)
    if any(marker in (issue.get("body") or "") for issue in issues):
        reasons.append("duplicate_fingerprint")

    contract = candidate["contract"]
    for dependency in contract["dependencies"]:
        if not _dependency_satisfied(dependency, issues):
            reasons.append(
                f"dependency_unsatisfied:{dependency['repository']}#{dependency['issue']}"
            )

    candidate_paths = set(contract["write_paths"])
    for issue in issues:
        existing = _open_contract(issue)
        if existing is None or issue["repository"] != candidate["repository"]:
            continue
        overlap = sorted(candidate_paths & set(existing["write_paths"]))
        if overlap:
            reasons.append(
                "write_boundary_collision:"
                + str(issue["number"])
                + ":"
                + ",".join(overlap)
            )
    return sorted(set(reasons))


def _route(route):
    require(isinstance(route, dict) and set(route) == {"kind"},
            "route.fields", sorted(route) if isinstance(route, dict) else route)
    require(route["kind"] in {"cloud", "local"}, "route.kind", route["kind"],
            required="cloud_or_local_create_route")
    return route["kind"]


def _persist(output, intent, report):
    output = Path(output)
    require(output.is_absolute(), "output", str(output),
            required="absolute_external_output")
    output = output.resolve()
    require(not output.exists(), "output.exists", str(output),
            required="new_external_output")
    require(output.parent.is_dir(), "output.parent", str(output.parent),
            required="existing_external_parent")
    temporary = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        (temporary / "intent.json").write_bytes(_canonical(intent))
        (temporary / "qualification.json").write_bytes(_canonical(report))
        os.rename(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return output


def prepare(resolved, packet, frontier, route, output):
    predecessor = _validate_resolved(resolved)
    selected, candidates = _validate_packet(packet)
    issues = _validate_frontier(frontier)
    kind = _route(route)

    reports = []
    eligible = []
    for candidate in candidates:
        reasons = _eligibility(candidate, issues)
        report = {
            "candidate_id": candidate["candidate_id"],
            "fingerprint": candidate["fingerprint"],
            "eligible": not reasons,
            "reasons": reasons,
        }
        reports.append(report)
        if not reasons:
            eligible.append(candidate)

    if selected is not None:
        chosen = next((candidate for candidate in eligible
                       if candidate["candidate_id"] == selected), None)
        require(chosen is not None, "selected_candidate", selected,
                required="eligible_selected_candidate")
    elif len(eligible) == 0:
        return {
            "owner": "next-issue.prepare",
            "action": "stop",
            "predecessor": predecessor,
            "qualification": reports,
            "next": None,
            "authorizes_landing": False,
        }
    elif len(eligible) > 1:
        return {
            "owner": "next-issue.prepare",
            "action": "select",
            "predecessor": predecessor,
            "qualification": reports,
            "next": {
                "kind": "input",
                "owner": "supervisor",
                "required": ["selected_candidate"],
                "known": {
                    "eligible": [candidate["candidate_id"] for candidate in eligible]
                },
            },
            "authorizes_landing": False,
        }
    else:
        chosen = eligible[0]

    request = {
        "action": "create_issue",
        "repository_full_name": chosen["repository"],
        "title": chosen["title"],
        "body": chosen["body"],
        "causal_fingerprint": chosen["fingerprint"],
    }
    intent = {
        "schema": 1,
        "route": kind,
        "predecessor": predecessor,
        "candidate_id": chosen["candidate_id"],
        "fingerprint": chosen["fingerprint"],
        "request": request,
        "status": "prepared",
        "authorizes_landing": False,
    }
    output = _persist(output, intent, {
        "schema": 1,
        "qualification": reports,
        "selected": chosen["candidate_id"],
        "authorizes_landing": False,
    })
    intent_path = output / "intent.json"
    if kind == "local":
        next_action = {
            "kind": "executable",
            "owner": "next-issue.execute",
            "operation": "execute",
            "known": {"intent": str(intent_path)},
            "argv": [
                os.path.realpath(sys.executable),
                "-B",
                str(Path(__file__).resolve().parent / "next-issue"),
                "execute",
                str(intent_path),
            ],
        }
    else:
        next_action = {
            "kind": "provider_write",
            "owner": "GitHub",
            "operation": "create_issue",
            "request": request,
            "known": {"intent": str(intent_path)},
        }
    return {
        "owner": "next-issue.prepare",
        "action": "create",
        "predecessor": predecessor,
        "qualification": reports,
        "request": request,
        "next": next_action,
        "authorizes_landing": False,
    }


def _token(environ):
    gh = (environ.get("GH_TOKEN") or "").strip()
    github = (environ.get("GITHUB_TOKEN") or "").strip()
    require(not (gh and github and gh != github),
            "credential.identity", "conflicting",
            required="single_provider_credential")
    token = gh or github
    require(bool(token) and not any(ch.isspace() for ch in token),
            "credential", "missing_or_malformed",
            required="supervisor_injected_GH_TOKEN")
    return token


def _http(method, url, payload, token):
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Content-Type": "application/json"} if body is not None else {}),
        })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise NextIssueRefusal(
            "provider.http", f"{error.code}:{detail}",
            owner="GitHub", required="provider_issue_create_readback"
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderUnknown(type(error).__name__) from error
    try:
        return json.loads(raw) if raw else {}
    except ValueError as error:
        raise NextIssueRefusal(
            "provider.json", url,
            owner="GitHub", required="valid_provider_response"
        ) from error


def _api(api, method, url, payload, token):
    return (api or _http)(method, url, payload, token)


def _issue_matches(issue, request):
    return (
        isinstance(issue, dict)
        and issue.get("html_url")
        == f"https://github.com/{request['repository_full_name']}/issues/{issue.get('number')}"
        and issue.get("title") == request["title"]
        and issue.get("body") == request["body"]
        and _marker(request["causal_fingerprint"]) in (issue.get("body") or "")
        and "pull_request" not in issue
    )


def _terminal(issue, intent):
    return {
        "owner": "next-issue",
        "action": "created",
        "candidate_id": intent["candidate_id"],
        "fingerprint": intent["fingerprint"],
        "issue": {
            "repository": intent["request"]["repository_full_name"],
            "number": issue["number"],
            "html_url": issue["html_url"],
        },
        "next": None,
        "authorizes_landing": False,
    }


def _readback_next(intent_path, intent):
    repository = intent["request"]["repository_full_name"]
    return {
        "kind": "provider_readback",
        "owner": "GitHub",
        "operation": "reconcile",
        "required": ["frontier"],
        "known": {
            "intent": str(Path(intent_path).resolve()),
            "causal_fingerprint": intent["fingerprint"],
        },
        "requests": {
            "issues": {
                "method": "GET",
                "url": f"https://api.github.com/repos/{repository}/issues?state=all&per_page=100&page=1",
            }
        },
        "reason": "Unknown create outcome requires fresh complete provider frontier; never repeat POST.",
    }


def execute(intent_path, *, environ=None, api=None):
    environ = os.environ if environ is None else environ
    intent_path = Path(intent_path).resolve()
    intent = _read_json(intent_path, "intent")
    require(intent.get("schema") == 1 and intent.get("route") == "local",
            "intent.route", intent.get("route"),
            required="local_create_intent")
    require(intent.get("status") == "prepared",
            "intent.status", intent.get("status"),
            required="prepared_create_intent")
    token = _token(environ)
    request = intent["request"]
    url = f"https://api.github.com/repos/{request['repository_full_name']}/issues"
    try:
        issue = _api(
            api, "POST", url,
            {"title": request["title"], "body": request["body"]},
            token,
        )
    except ProviderUnknown:
        return {
            "owner": "next-issue.execute",
            "action": "unknown",
            "provider_mutations": None,
            "next": _readback_next(intent_path, intent),
            "authorizes_landing": False,
        }
    require(_issue_matches(issue, request),
            "provider.issue", issue,
            owner="GitHub", required="exact_created_issue_readback")
    return _terminal(issue, intent)


def reconcile(intent_path, frontier):
    intent_path = Path(intent_path).resolve()
    intent = _read_json(intent_path, "intent")
    issues = _validate_frontier(frontier)
    marker = _marker(intent["fingerprint"])
    matches = [
        issue for issue in issues
        if issue["repository"] == intent["request"]["repository_full_name"]
        and marker in (issue.get("body") or "")
    ]
    if len(matches) == 0:
        return {
            "owner": "next-issue.reconcile",
            "action": "readback",
            "next": _readback_next(intent_path, intent),
            "authorizes_landing": False,
        }
    require(len(matches) == 1, "provider.fingerprint_matches",
            [issue["number"] for issue in matches],
            owner="GitHub", required="unique_created_issue")
    issue = matches[0]
    require(issue.get("state") == "open", "provider.issue.state", issue.get("state"),
            owner="GitHub", required="open_created_issue")
    # frontier omits title by design; body+fingerprint+repository uniquely bind adoption.
    require(issue.get("body") == intent["request"]["body"],
            "provider.issue.body", issue.get("number"),
            owner="GitHub", required="exact_created_issue_body")
    return _terminal(issue, intent)


def parser():
    p = argparse.ArgumentParser(
        prog="./next-issue",
        description="Materialize or reconcile one next Issue from a RESOLVED predecessor.")
    verbs = p.add_subparsers(dest="verb", required=True)
    prepare_p = verbs.add_parser("prepare")
    prepare_p.add_argument("resolved")
    prepare_p.add_argument("candidates")
    prepare_p.add_argument("frontier")
    prepare_p.add_argument("route")
    prepare_p.add_argument("output")
    execute_p = verbs.add_parser("execute")
    execute_p.add_argument("intent")
    reconcile_p = verbs.add_parser("reconcile")
    reconcile_p.add_argument("intent")
    reconcile_p.add_argument("frontier")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.verb == "prepare":
            result = prepare(
                _read_json(args.resolved, "resolved"),
                _read_json(args.candidates, "candidates"),
                _read_json(args.frontier, "frontier"),
                _read_json(args.route, "route"),
                args.output,
            )
        elif args.verb == "execute":
            result = execute(args.intent)
        else:
            result = reconcile(args.intent, _read_json(args.frontier, "frontier"))
    except (NextIssueRefusal, OSError, ValueError) as error:
        invalid = getattr(error, "invalid", {"field": "input", "value": type(error).__name__})
        next_action = getattr(error, "next", {
            "kind": "input", "owner": "supervisor",
            "required": ["valid_next_issue_input"],
        })
        print(json.dumps({
            "owner": "next-issue",
            "status": "refused",
            "invalid": invalid,
            "next": next_action,
            "authorizes_landing": False,
        }, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
