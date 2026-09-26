"""Reject unresolved #157 consumer evidence; NOT a native execution verifier.

This stage has no positive native-capture adapter. Unsupported completion records
remain blocked until a supervisor selects and validates the real capture mapping.
It never spawns agents, imports supplied code, repairs evidence or grants landing.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_BYTES = 1_048_576


def refusal(field, reason, validity="INCONCLUSIVE", required="native_consumer_evidence"):
    return {
        "schema": 1, "owner": "pclass.consumer_evidence",
        "issue": {"repository": "ed3c/soodles", "number": 157},
        "scope": "required-consumer-evidence readiness veto only",
        "evidence_validity": validity, "behavior": None,
        "terminal_ready": False, "authorizes_landing": False,
        "problem": {"field": field, "reason": reason},
        "next": {"kind": "input", "owner": "supervisor", "required": [required]},
    }


def inspect_comparison(value):
    if not isinstance(value, dict) or type(value.get("schema")) is not int:
        return refusal("schema", "expected a versioned comparison object", "INVALID")
    if value["schema"] != 1:
        return refusal("schema", "no validated capture adapter for this schema",
                       required="supervisor_selected_native_capture_validator")
    issue = value.get("issue")
    if (not isinstance(issue, dict) or type(issue.get("number")) is not int
            or issue != {"repository": "ed3c/soodles", "number": 157}):
        return refusal("issue", "comparison does not belong to this atom", "INVALID")
    if value.get("authorizes_landing") is not False:
        return refusal("authorizes_landing", "comparison cannot grant authority", "INVALID")
    runs = value.get("fresh_runs")
    if not isinstance(runs, list):
        return refusal("fresh_runs", "required run observations are absent or malformed")
    if not runs:
        return refusal("fresh_runs", "six planned fresh consumer runs have not been supplied")
    if len(runs) != 6 or any(not isinstance(run, dict) for run in runs):
        return refusal("fresh_runs", "the declared six-run comparison is incomplete or malformed")
    if value.get("status") != "COMPLETED":
        return refusal("status", "consumer execution is not complete")
    if value.get("independent_agent_telemetry") is None:
        return refusal("independent_agent_telemetry", "independent operation records are missing")
    # Six dictionaries, PASS text and a caller digest cannot establish execution.
    # Do not invent native tool fields from the historical #39 normalized format.
    return refusal("native_capture", "completion requires a validated native capture mapping",
                   required="supervisor_selected_native_capture_validator")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def inspect_file(path, expected_sha256):
    if not isinstance(expected_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        return refusal("expected_sha256", "expected a supplied SHA-256", "INVALID",
                       "selected_consumer_evidence")
    try:
        # Nonblocking/no-follow open also rejects FIFO and symlink substitutions.
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return refusal("file", "evidence must be a regular file", "INVALID")
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return refusal("file", "evidence exceeds bounded input size", "INVALID")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_sha256:
            return refusal("sha256", "selected raw-byte digest mismatch", "INVALID",
                           "selected_consumer_evidence")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                           parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except FileNotFoundError:
        return refusal("file", "required consumer artifact is missing")
    except (OSError, UnicodeError, ValueError, RecursionError):
        return refusal("file", "evidence is not a readable bounded UTF-8 JSON object", "INVALID")
    return {**inspect_comparison(value), "evidence_sha256": digest}


def main(argv):
    if len(argv) != 3:
        result = refusal("arguments", "usage: consumer_gate.py COMPARISON.json EXPECTED_SHA256",
                         "INVALID", "selected_consumer_evidence")
        code = 2
    else:
        result = inspect_file(Path(argv[1]), argv[2])
        code = 2 if result["evidence_validity"] == "INVALID" else 1
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
