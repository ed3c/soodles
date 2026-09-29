#!/usr/bin/env python3
"""Execute one current owner's local GitHub provider-readback projection.

Read-only transport only. The current owner selects every primary GET. This
adapter materializes the required readback shape and returns one exact owner
re-entry argv. It performs no provider writes and owns no transition choice.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from repository_binding import profile


class ReadbackRefusal(RuntimeError):
    def __init__(self, field, value, required="corrected_provider_readback_input"):
        self.invalid = {"field": field, "value": value}
        self.next = {
            "kind": "input",
            "owner": "supervisor",
            "required": [required],
        }
        super().__init__(f"provider readback: invalid {field}={value!r}")


def require(condition, field, value, required="corrected_provider_readback_input"):
    if not condition:
        raise ReadbackRefusal(field, value, required)


def _read_json(path, field):
    path = Path(path).resolve()
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ReadbackRefusal(field, type(error).__name__, "valid_json_input") from error
    require(isinstance(value, dict), field, type(value).__name__, "json_object")
    return value


def _token(environ):
    gh = (environ.get("GH_TOKEN") or "").strip()
    github = (environ.get("GITHUB_TOKEN") or "").strip()
    require(not (gh and github and gh != github),
            "credential.identity", "conflicting", "single_provider_credential")
    token = gh or github
    require(bool(token) and not any(ch.isspace() for ch in token),
            "credential", "missing_or_malformed", "supervisor_injected_GH_TOKEN")
    return token


def _repository_from_url(url):
    require(isinstance(url, str), "request.url", url, "supported_github_get")
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == "https" and parsed.netloc == "api.github.com",
            "request.host", f"{parsed.scheme}://{parsed.netloc}",
            "api_github_com_only")
    match = re.match(r"^/repos/([^/]+/[^/]+)(?:/|$)", parsed.path)
    require(match is not None, "request.path", parsed.path,
            "repository_scoped_github_get")
    repository = match.group(1)
    require(profile(repository) is not None, "request.repository", repository,
            "supported_repository")
    return repository


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ReadbackRefusal(
            "provider.redirect",
            {"status": code, "url": newurl},
            "non_redirecting_provider_readback",
        )


def _http(method, url, token):
    require(method == "GET", "request.method", method, "GET_only")
    _repository_from_url(url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=30) as response:
            raw = response.read()
            headers = {key: value for key, value in response.headers.items()}
    except ReadbackRefusal:
        raise
    except urllib.error.HTTPError as error:
        if error.code in {301, 302, 303, 307, 308}:
            raise ReadbackRefusal(
                "provider.redirect",
                {"status": error.code, "url": error.headers.get("Location")},
                "non_redirecting_provider_readback",
            ) from error
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise ReadbackRefusal(
            "provider.http", f"{error.code}:{detail}", "successful_provider_readback"
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ReadbackRefusal(
            "provider.network", type(error).__name__, "provider_readback_capability"
        ) from error
    try:
        payload = json.loads(raw) if raw else {}
    except ValueError as error:
        raise ReadbackRefusal(
            "provider.json", url, "valid_provider_response"
        ) from error
    return payload, headers


def _api(api, method, url, token):
    if api is None:
        return _http(method, url, token)
    result = api(method, url, token)
    if isinstance(result, tuple) and len(result) == 2:
        return result
    return result, {}


def _next_projection(result):
    require(isinstance(result, dict), "owner_result", type(result).__name__)
    next_action = result.get("next")
    require(isinstance(next_action, dict), "next", next_action,
            "provider_readback_projection")
    require(next_action.get("kind") == "provider_readback",
            "next.kind", next_action.get("kind"), "provider_readback_projection")
    require(next_action.get("owner") == "GitHub",
            "next.owner", next_action.get("owner"), "GitHub_provider_readback")
    requests = next_action.get("requests")
    require(isinstance(requests, dict) and bool(requests),
            "next.requests", requests, "exact_owner_GETs")
    for key, request in requests.items():
        require(isinstance(key, str) and bool(key),
                "next.requests.key", key, "named_readback_key")
        require(isinstance(request, dict)
                and set(request) == {"method", "url"},
                f"next.requests.{key}", request, "exact_GET_request")
        require(request["method"] == "GET",
                f"next.requests.{key}.method", request["method"], "GET_only")
        _repository_from_url(request["url"])
    return next_action, requests


def _new_output(output):
    output = Path(output)
    require(output.is_absolute(), "output", str(output), "absolute_external_output")
    output = output.resolve()
    source_root = Path(__file__).resolve().parent
    require(not output.is_relative_to(source_root), "output", str(output),
            "external_output_outside_candidate")
    require(not output.exists(), "output.exists", str(output), "new_external_output")
    require(output.parent.is_dir(), "output.parent", str(output.parent),
            "existing_external_parent")
    return output


def _write_dir(output, files):
    temporary = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        for name, value in files.items():
            path = temporary / name
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        os.rename(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _verify_publisher(context):
    require(set(context) == {"schema", "kind", "publisher"},
            "context.fields", sorted(context))
    require(context["schema"] == 1 and context["kind"] == "landing",
            "context.kind", context.get("kind"), "landing_readback_context")
    publisher = context["publisher"]
    require(isinstance(publisher, dict)
            and set(publisher) == {"root", "verifier_sha256"},
            "context.publisher", publisher, "selected_publisher_identity")
    root = Path(publisher["root"])
    require(root.is_absolute(), "context.publisher.root", str(root),
            "absolute_publisher_root")
    root = root.resolve()
    cli = root / "soodles.py"
    require(cli.is_file(), "context.publisher.soodles", str(cli),
            "selected_publisher_cli")
    expected = publisher["verifier_sha256"]
    require(isinstance(expected, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected),
            "context.publisher.verifier_sha256", expected,
            "pinned_publisher_digest")
    identity = subprocess.run(
        [sys.executable, "-B", str(cli), "landing", "identity"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    require(identity.returncode == 0,
            "publisher.identity.exit", identity.returncode,
            "valid_selected_publisher")
    try:
        payload = json.loads(identity.stdout)
    except ValueError as error:
        raise ReadbackRefusal(
            "publisher.identity.json", identity.stdout[:200],
            "valid_selected_publisher"
        ) from error
    require(payload == {
        "owner": "landing.identity",
        "verifier_sha256": expected,
        "next": None,
    }, "publisher.identity", payload, "matching_selected_publisher")
    return root, cli


def _landing_consume(result, next_action, requests, context, output, token, api):
    root, cli = _verify_publisher(context)
    known = next_action.get("known") or {}
    checkpoint = known.get("checkpoint")
    operation = next_action.get("operation")
    require(operation in {"advance", "dispatch"},
            "next.operation", operation, "landing_advance_or_dispatch")
    require(isinstance(checkpoint, str) and Path(checkpoint).is_absolute(),
            "next.known.checkpoint", checkpoint, "absolute_landing_checkpoint")

    readback = {}
    reads = []
    for key, request in requests.items():
        payload, _ = _api(api, "GET", request["url"], token)
        readback[key] = payload
        reads.append(request["url"])

    if "merge_commit" not in readback:
        pr = readback.get("pr")
        if isinstance(pr, dict) and pr.get("merged") is True:
            sha = pr.get("merge_commit_sha")
            require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha),
                    "readback.pr.merge_commit_sha", sha,
                    "complete_merge_commit_sha")
            pr_request = requests.get("pr")
            require(isinstance(pr_request, dict), "next.requests.pr", pr_request,
                    "pr_readback_for_merge_commit")
            parsed = urllib.parse.urlsplit(pr_request["url"])
            match = re.match(r"^(/repos/[^/]+/[^/]+)/pulls/[1-9][0-9]*$", parsed.path)
            require(match is not None, "next.requests.pr.url", pr_request["url"],
                    "canonical_pr_readback_url")
            merge_url = urllib.parse.urlunsplit((
                "https", "api.github.com",
                match.group(1) + "/git/commits/" + sha, "", ""
            ))
            payload, _ = _api(api, "GET", merge_url, token)
            readback["merge_commit"] = payload
            reads.append(merge_url)

    readback_path = output / "readback.json"
    result_path = output / "result.json"
    argv = [
        sys.executable, "-B", str(cli), "landing", operation,
        str(Path(checkpoint).resolve()), str(readback_path),
    ]
    receipt = {
        "owner": "provider-readback.consume",
        "action": "materialized",
        "consumer": "landing",
        "readback": str(readback_path),
        "provider_reads": len(reads),
        "next": {
            "kind": "executable",
            "owner": "landing." + operation,
            "operation": operation,
            "known": {
                "checkpoint": str(Path(checkpoint).resolve()),
                "readback": str(readback_path),
            },
            "argv": argv,
        },
        "authorizes_landing": False,
    }
    _write_dir(output, {
        "readback.json": readback,
        "result.json": receipt,
    })
    return receipt


def _link_next(headers):
    link = None
    for key, value in headers.items():
        if key.lower() == "link":
            link = value
            break
    if not link:
        return None
    for part in link.split(","):
        match = re.match(r'\s*<([^>]+)>;\s*rel="([^"]+)"\s*$', part)
        if match and match.group(2) == "next":
            return match.group(1)
    return None


def _issue_frontier_item(repository, issue):
    require(isinstance(issue, dict), "provider.issue", type(issue).__name__,
            "provider_issue_object")
    require("pull_request" not in issue, "provider.issue.pull_request", issue.get("number"),
            "issue_only_frontier")
    number = issue.get("number")
    require(type(number) is int and number > 0,
            "provider.issue.number", number, "provider_issue_identity")
    html_url = issue.get("html_url")
    require(html_url == f"https://github.com/{repository}/issues/{number}",
            "provider.issue.html_url", html_url, "provider_issue_identity")
    state = issue.get("state")
    require(state in {"open", "closed"}, "provider.issue.state", state,
            "provider_issue_state")
    return {
        "repository": repository,
        "number": number,
        "state": state,
        "state_reason": issue.get("state_reason"),
        "closed_at": issue.get("closed_at"),
        "html_url": html_url,
        "body": issue.get("body") or "",
    }


def _next_issue_consume(result, next_action, requests, context, output, token, api):
    require(set(context) == {"schema", "kind", "consumer_root"},
            "context.fields", sorted(context))
    require(context["schema"] == 1 and context["kind"] == "next_issue",
            "context.kind", context.get("kind"), "next_issue_readback_context")
    root = Path(context["consumer_root"])
    require(root.is_absolute(), "context.consumer_root", str(root),
            "absolute_consumer_root")
    root = root.resolve()
    cli = root / "next-issue"
    require(cli.is_file(), "context.next_issue_cli", str(cli),
            "selected_next_issue_cli")

    require(set(requests) == {"issues"},
            "next.requests", sorted(requests), "issues_frontier_request_only")
    first = requests["issues"]["url"]
    repository = _repository_from_url(first)
    parsed = urllib.parse.urlsplit(first)
    require(parsed.path == f"/repos/{repository}/issues",
            "next.requests.issues.path", parsed.path,
            "canonical_issues_frontier")
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    require(query.get("state") == ["all"],
            "next.requests.issues.state", query.get("state"),
            "all_issue_states")
    require(query.get("per_page") == ["100"],
            "next.requests.issues.per_page", query.get("per_page"),
            "per_page_100")
    require(query.get("page") == ["1"],
            "next.requests.issues.page", query.get("page"),
            "frontier_starts_page_1")

    items = []
    reads = []
    seen = set()
    url = first
    for _ in range(100):
        require(url not in seen, "provider.pagination", url,
                "acyclic_provider_pagination")
        seen.add(url)
        require(_repository_from_url(url) == repository,
                "provider.pagination.repository", url,
                "same_repository_pagination")
        payload, headers = _api(api, "GET", url, token)
        require(isinstance(payload, list), "provider.issues", type(payload).__name__,
                "issue_list_response")
        reads.append(url)
        for issue in payload:
            if isinstance(issue, dict) and "pull_request" in issue:
                continue
            items.append(_issue_frontier_item(repository, issue))
        next_url = _link_next(headers)
        if not next_url:
            break
        require(_repository_from_url(next_url) == repository,
                "provider.pagination.repository", next_url,
                "same_repository_pagination")
        next_parsed = urllib.parse.urlsplit(next_url)
        require(next_parsed.path == f"/repos/{repository}/issues",
                "provider.pagination.path", next_parsed.path,
                "same_issues_endpoint")
        next_query = urllib.parse.parse_qs(
            next_parsed.query, keep_blank_values=True)
        require(next_query.get("state") == ["all"]
                and next_query.get("per_page") == ["100"]
                and len(next_query.get("page", [])) == 1
                and next_query["page"][0].isdigit()
                and int(next_query["page"][0]) >= 2,
                "provider.pagination.query", next_query,
                "same_issues_frontier_pagination")
        url = next_url
    else:
        raise ReadbackRefusal(
            "provider.pagination", "over_100_pages", "bounded_complete_frontier"
        )

    known = next_action.get("known") or {}
    intent = known.get("intent")
    operation = next_action.get("operation")
    require(operation == "reconcile",
            "next.operation", operation, "next_issue_reconcile")
    require(isinstance(intent, str) and Path(intent).is_absolute(),
            "next.known.intent", intent, "absolute_next_issue_intent")

    frontier = {"schema": 1, "complete": True, "issues": items}
    frontier_path = output / "frontier.json"
    argv = [
        sys.executable, "-B", str(cli), "reconcile",
        str(Path(intent).resolve()), str(frontier_path),
    ]
    receipt = {
        "owner": "provider-readback.consume",
        "action": "materialized",
        "consumer": "next_issue",
        "readback": str(frontier_path),
        "provider_reads": len(reads),
        "next": {
            "kind": "executable",
            "owner": "next-issue.reconcile",
            "operation": "reconcile",
            "known": {
                "intent": str(Path(intent).resolve()),
                "frontier": str(frontier_path),
            },
            "argv": argv,
        },
        "authorizes_landing": False,
    }
    _write_dir(output, {
        "frontier.json": frontier,
        "result.json": receipt,
    })
    return receipt


def consume(result, context, output, *, environ=None, api=None):
    output = _new_output(output)
    environ = os.environ if environ is None else environ
    token = _token(environ)
    next_action, requests = _next_projection(result)
    kind = context.get("kind") if isinstance(context, dict) else None
    if kind == "landing":
        return _landing_consume(
            result, next_action, requests, context, output, token, api)
    if kind == "next_issue":
        return _next_issue_consume(
            result, next_action, requests, context, output, token, api)
    raise ReadbackRefusal(
        "context.kind", kind, "landing_or_next_issue_context"
    )


def parser():
    p = argparse.ArgumentParser(
        prog="./provider-readback",
        description="Materialize one current owner's exact local GitHub readback.")
    verbs = p.add_subparsers(dest="verb", required=True)
    consume_p = verbs.add_parser("consume")
    consume_p.add_argument("owner_result")
    consume_p.add_argument("context")
    consume_p.add_argument("output")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = consume(
            _read_json(args.owner_result, "owner_result"),
            _read_json(args.context, "context"),
            args.output,
        )
    except (ReadbackRefusal, OSError, subprocess.TimeoutExpired) as error:
        invalid = getattr(
            error, "invalid",
            {"field": "input", "value": type(error).__name__})
        next_action = getattr(error, "next", {
            "kind": "input",
            "owner": "supervisor",
            "required": ["valid_provider_readback_input"],
        })
        print(json.dumps({
            "owner": "provider-readback",
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
