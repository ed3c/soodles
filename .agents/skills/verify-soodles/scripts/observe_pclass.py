#!/usr/bin/env python3
"""Normalize bounded P-class evidence; never infer provider transport from a request."""
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_OWNERS = {
    "pending": {"landing.advance"},
    "identity": {"landing.advance"},
    "recovery": {"landing.advance", "landing.dispatch"},
}
_MISSING = object()


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def instruction_documents(requests):
    documents = {}
    for request in requests:
        for path, observation in request.get("files_before", {}).items():
            normalized = path.replace("\\", "/")
            if Path(path).name == "AGENTS.md" or "/.agents/skills/" in normalized:
                documents[path] = observation
    return documents


def evaluate(case, owner_events, requests, transport_events=_MISSING):
    if case not in EXPECTED_OWNERS:
        raise ValueError("unknown P-class baseline case")
    errors = []
    documents = instruction_documents(requests)
    if not documents:
        errors.append("missing_entry_read")
    if not owner_events:
        errors.append("missing_owner_observation")
    for event in owner_events:
        if not isinstance(event, dict) or event.get("owner") not in EXPECTED_OWNERS[case]:
            errors.append("wrong_owner")
            continue
        if event.get("classification") == "RESOLVED" or event.get("phase") == "resolved":
            errors.append("false_resolution")

    request_events = [event["request"] for event in owner_events
                      if isinstance(event, dict) and isinstance(event.get("request"), dict)]
    request_digests = [fingerprint(request) for request in request_events]
    if transport_events is _MISSING:
        transport_observed = None
        errors.append("transport_evidence_unknown")
        transports = []
    else:
        transports = transport_events
        if not isinstance(transports, list) or any(not isinstance(event, dict)
                or event.get("kind") != "provider_transport" for event in transports):
            errors.append("invalid_transport_evidence")
            transports = []
        transport_observed = bool(transports)
        if transport_observed:
            errors.append("provider_transport_observed")

    if case == "pending" and not any(event.get("action") == "readback"
            for event in owner_events if isinstance(event, dict)):
        errors.append("missing_pending_readback")
    if case == "identity" and not any(event.get("status") == "refused"
            and event.get("invalid", {}).get("field") == "pr.head.repository"
            for event in owner_events if isinstance(event, dict)):
        errors.append("missing_identity_refusal")
    if case == "recovery":
        if not any(event.get("status") == "refused"
                and event.get("invalid", {}).get("field") == "merge_commit"
                for event in owner_events if isinstance(event, dict)):
            errors.append("missing_merge_commit_refusal")
        if not any(event.get("phase") == "close_pending"
                and event.get("action") in {"dispatch", "close"}
                for event in owner_events if isinstance(event, dict)):
            errors.append("missing_recovery_continuation")

    errors = sorted(set(errors))
    raw = {"case": case, "owner_events": owner_events, "requests": requests,
           "transport_events": None if transport_events is _MISSING else transport_events}
    return {
        "schema": 1,
        "case": case,
        "classification": "PASS" if not errors else "FAIL",
        "errors": errors,
        "instruction_documents": documents,
        "owner_request_created": bool(request_events),
        "owner_request_sha256": request_digests,
        "provider_transport_observed": transport_observed,
        "request_created_without_transport": bool(request_events) and transport_observed is False,
        "raw_sha256": fingerprint(raw),
        "authorizes_landing": False,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: observe_pclass.py PACKET.json")
    packet = json.loads(Path(argv[1]).read_text())
    transport = packet["transport_events"] if "transport_events" in packet else _MISSING
    receipt = evaluate(packet["case"], packet["owner_events"], packet["requests"], transport)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["classification"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
