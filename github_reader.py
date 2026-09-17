"""Authenticated Issue readback shared by Session and admission consumers.

The supervisor supplies GH_TOKEN. This reader never acquires credentials or
retries requests. Cached bytes become fresh only through an authenticated 304.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime

from issue_admission import AdmissionRefusal, REPOSITORY

RATE_HEADERS = ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-used",
                "x-ratelimit-reset", "x-ratelimit-resource", "retry-after")


class ProviderWait(AdmissionRefusal):
    exit_code = 75

    def __init__(self, until, observation):
        super().__init__("issue.provider_budget", observation, "GitHub", "fresh_issue_readback")
        self.next.update(kind="wait", not_before=until)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(request):
    # Default urllib redirects may forward Authorization before response.url is checked.
    return urllib.request.build_opener(NoRedirect()).open(request, timeout=30)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _read(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        raise AdmissionRefusal("github.cache", "unreadable cache", "supervisor", "readable_private_cache")


def _save(path, value):
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _deadline(headers, now):
    dates = []
    if headers.get("x-ratelimit-remaining") == "0":
        try:
            dates.append(int(headers["x-ratelimit-reset"]))
        except (KeyError, ValueError):
            pass
    retry = headers.get("retry-after")
    if retry:
        try:
            dates.append(now + max(0, int(retry)))
        except ValueError:
            try:
                dates.append(parsedate_to_datetime(retry).timestamp())
            except (ValueError, TypeError, OverflowError):
                pass
    return max([now] + dates)


def issue(number):
    if type(number) is not int or number <= 0:
        raise AdmissionRefusal("issue.number", number)
    token = os.environ.get("GH_TOKEN", "")
    if not token or any(not 33 <= ord(character) <= 126 for character in token):
        raise AdmissionRefusal("github.credential", "missing or invalid GH_TOKEN", "supervisor",
                               "repository_scoped_installation_token_in_GH_TOKEN")
    url = f"https://api.github.com/repos/{REPOSITORY}/issues/{number}"
    identity = _hash(token.encode())
    directory = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "soodles/github" / identity
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    cache_path = directory / (_hash(url.encode()) + ".json")
    budget_path = directory / "budget.json"
    with open(directory / "request.lock", "a") as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        now = time.time()
        budget = _read(budget_path)
        if not isinstance(budget, dict):
            raise AdmissionRefusal("github.cache", "invalid budget", "supervisor", "readable_private_cache")
        until = budget.get("not_before", 0)
        if not isinstance(until, (int, float)):
            raise AdmissionRefusal("github.cache", "invalid deadline", "supervisor", "readable_private_cache")
        if until > now:
            raise ProviderWait(until, {"request_sent": False, **budget.get("observation", {})})
        cached = _read(cache_path)
        valid_cache = (isinstance(cached, dict) and cached.get("url") == url
                       and cached.get("identity") == identity and isinstance(cached.get("body"), str)
                       and cached.get("sha256") == _hash(cached["body"].encode())
                       and isinstance(cached.get("etag"), str)
                       and re.fullmatch(r'[\x20-\x7e]+', cached["etag"]) is not None)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "soodles-issue-admission",
                   "Authorization": "Bearer " + token, "X-GitHub-Api-Version": "2022-11-28"}
        if valid_cache:
            headers["If-None-Match"] = cached["etag"]
        request = urllib.request.Request(url, headers=headers)
        try:
            try:
                response = _request(request)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                status = response.code
                # No redirected request was sent, and the received URL is also checked.
                if response.url != url:
                    raise AdmissionRefusal("issue.provider_url", "unexpected response URL", "GitHub", "exact_issue_readback")
                now = time.time()
                received = {key.lower(): value for key, value in response.headers.items()}
                observation = {"url": url, "status": status, "authenticated": True,
                               "observed_at": now, "rate": {key: received[key] for key in RATE_HEADERS if key in received}}
                deadline = _deadline(received, now)
                _save(budget_path, {"not_before": deadline, "observation": observation})
                if status in (403, 429) and deadline > now:
                    raise ProviderWait(deadline, {"request_sent": True, **observation})
                if status == 401:
                    raise AdmissionRefusal("github.credential", observation, "supervisor",
                                           "repository_scoped_installation_token_in_GH_TOKEN")
                if status == 304:
                    if not valid_cache:
                        raise AdmissionRefusal("github.cache", "304 without matching cached bytes", "GitHub", "fresh_issue_readback")
                    body = cached["body"]
                elif status == 200:
                    body = response.read().decode("utf-8")
                else:
                    raise AdmissionRefusal("issue.provider_readback", observation, "GitHub", "fresh_issue_readback")
                value = json.loads(body)
                if not isinstance(value, dict) or value.get("url") != url or type(value.get("number")) is not int or value["number"] != number or "pull_request" in value:
                    raise AdmissionRefusal("issue.provider_readback", "mismatched Issue identity", "GitHub", "exact_issue_readback")
                if status == 200:
                    _save(cache_path, {"url": url, "identity": identity, "etag": received.get("etag"),
                                       "body": body, "sha256": _hash(body.encode())})
                return {"owner": "github.issue", "status": "read", "issue": value,
                        "observation": observation, "next": None, "authorizes_landing": False}
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError) as error:
            # Do not reflect server bodies, transport exceptions or credentials to logs.
            raise AdmissionRefusal("issue.provider_readback", type(error).__name__, "GitHub", "fresh_issue_readback") from None


def fetch_issue(number):
    return issue(number)["issue"]


def refusal_output(error):
    return {"owner": "github.issue", "status": "wait" if isinstance(error, ProviderWait) else "refused",
            "invalid": error.invalid, "next": {**error.next, "operation": "issue",
            "help_argv": [str(Path(__file__).resolve().parent / "soodles"), "github", "issue", "--help"],
            "reason": "The named owner supplies missing input. After the provider deadline, re-enter this same reader. Never change identity or use stale bytes to bypass refusal."}}
