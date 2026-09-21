#!/usr/bin/env python3
"""Execute one landing-owner-authorized local GitHub mutation.

This is transport, not transition authority. It accepts only the checkpoint path;
repository, subject, expected head and action come from the durable offered
request already persisted by landing.py. The caller's supervisor injects
GH_TOKEN/GITHUB_TOKEN. Mutations are never retried here.
"""
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.request

import landing


class ProviderRefusal(RuntimeError):
    def __init__(self, field, value, required="fresh_landing_owner"):
        self.invalid = {"field": field, "value": value}
        self.next = {"kind": "input", "owner": "supervisor", "required": [required]}
        super().__init__(f"local provider: invalid {field}={value!r}")


class ProviderUnknown(RuntimeError):
    pass


def require(condition, field, value, required="fresh_landing_owner"):
    if not condition:
        raise ProviderRefusal(field, value, required)


def _token(environ):
    gh = (environ.get("GH_TOKEN") or "").strip()
    github = (environ.get("GITHUB_TOKEN") or "").strip()
    require(not (gh and github and gh != github), "credential.identity", "conflicting", "single_provider_credential")
    token = gh or github
    require(bool(token) and not any(ch.isspace() for ch in token),
            "credential", "missing_or_malformed", "supervisor_injected_GH_TOKEN")
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
        raise ProviderRefusal("provider.http", f"{error.code}:{detail}", "provider_readback") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderUnknown(type(error).__name__) from error
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError as error:
        raise ProviderRefusal("provider.json", url, "valid_provider_response") from error


def _api(api, method, url, payload, token):
    return (api or _http)(method, url, payload, token)


def _snapshot(claim, checkpoint, api, token):
    projection = landing.provider_next(claim, "advance", checkpoint)
    snapshot = {}
    for key, spec in projection["requests"].items():
        require(spec.get("method") == "GET" and isinstance(spec.get("url"), str),
                "readback.request", key)
        snapshot[key] = _api(api, "GET", spec["url"], None, token)
    pr = snapshot.get("pr") or {}
    merge_sha = pr.get("merge_commit_sha")
    if pr.get("merged") and isinstance(merge_sha, str):
        base = "https://api.github.com/repos/" + claim["repository"]
        snapshot["merge_commit"] = _api(
            api, "GET", base + "/git/commits/" + merge_sha, None, token)
    return snapshot


def _save_readback(checkpoint, snapshot):
    checkpoint = Path(checkpoint).resolve()
    path = checkpoint.with_name(checkpoint.name + ".provider-readback.json")
    fd, temporary = tempfile.mkstemp(prefix=".provider-readback-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(snapshot, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def _unknown(claim, checkpoint, reason):
    next_action = landing.provider_next(claim, "advance", checkpoint)
    next_action["reason"] = (
        "Provider mutation outcome is unknown. Perform only the emitted fresh "
        "readbacks; never rerun the mutation from this receipt.")
    return {
        "owner": "local-provider.execute",
        "action": "unknown",
        "reason": reason,
        "provider_mutations": None,
        "next": next_action,
        "authorizes_landing": False,
    }


def execute(checkpoint, *, environ=None, api=None):
    """Execute at most one persisted local merge/close offer and return fresh owner input."""
    environ = os.environ if environ is None else environ
    token = _token(environ)
    with landing.locked(checkpoint) as path:
        state = landing.read(path)
        require(state.get("schema") in (1, 2), "checkpoint.schema", state.get("schema"))
        claim = state.get("claim")
        landing.validate_claim(claim)
        require(landing.claim_route(claim) == "local", "claim.route", landing.claim_route(claim))
        delivery = state.get("delivery")
        require(isinstance(delivery, dict), "delivery", delivery)
        require(delivery.get("status") == "offered", "delivery.status", delivery.get("status"))
        action = delivery.get("action")
        require(action in {"merge", "close"}, "delivery.action", action)
        expected = landing.delivery_request(claim, action)
        request = delivery.get("request")
        require(request == expected, "delivery.request", request)

        try:
            before = _snapshot(claim, path, api, token)
            landing.validate_snapshot(claim, before, operation="dispatch", checkpoint=path)
            mutated = 0
            base = "https://api.github.com/repos/" + claim["repository"]
            if action == "merge":
                pr = before["pr"]
                if not pr.get("merged"):
                    require(pr.get("state") == "open" and pr.get("mergeable") is True,
                            "provider.merge", {"state": pr.get("state"), "mergeable": pr.get("mergeable")})
                    _api(api, "PUT", base + f"/pulls/{claim['pr']}/merge",
                         {"sha": claim["head"], "merge_method": "merge"}, token)
                    mutated = 1
            else:
                issue = before["issue"]
                if issue.get("state") != "closed":
                    require(before["pr"].get("merged") is True,
                            "provider.close.pr", before["pr"].get("merged"))
                    require(issue.get("state") == "open", "provider.close.issue", issue.get("state"))
                    _api(api, "PATCH", base + f"/issues/{claim['issue']}",
                         {"state": "closed", "state_reason": "completed"}, token)
                    mutated = 1
            after = _snapshot(claim, path, api, token)
        except ProviderUnknown as error:
            try:
                after = _snapshot(claim, path, api, token)
            except Exception:
                return _unknown(claim, path, str(error))
            if action == "merge" and not after.get("pr", {}).get("merged"):
                return _unknown(claim, path, str(error))
            if action == "close" and after.get("issue", {}).get("state") != "closed":
                return _unknown(claim, path, str(error))
            mutated = None

        readback = _save_readback(path, after)
        return {
            "owner": "local-provider.execute",
            "action": action,
            "provider_mutations": mutated,
            "readback": str(readback),
            "next": {
                "kind": "executable",
                "owner": "landing.advance",
                "operation": "advance",
                "known": {"checkpoint": str(path), "readback": str(readback)},
                "argv": landing.cli_argv("advance", path, readback),
            },
            "authorizes_landing": False,
        }


def main(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 1:
        print(json.dumps({
            "owner": "local-provider.execute",
            "status": "refused",
            "invalid": {"field": "arguments", "value": argv},
            "next": {"kind": "input", "owner": "caller", "required": ["checkpoint_only"]},
            "authorizes_landing": False,
        }, indent=2))
        return 2
    try:
        result = execute(argv[0])
    except ProviderRefusal as error:
        result = {
            "owner": "local-provider.execute",
            "status": "refused",
            "invalid": error.invalid,
            "next": error.next,
            "authorizes_landing": False,
        }
        print(json.dumps(result, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
