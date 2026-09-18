#!/usr/bin/env python3
"""Normalize bounded P-class evidence; never infer provider transport from a request."""
import hashlib
import json
from pathlib import Path
import sys


CASES = {"pending", "identity", "recovery"}
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


def projected_operation(projection):
    if not isinstance(projection, dict):
        return None
    next_action = projection.get("next")
    if not isinstance(next_action, dict):
        return None
    operation = next_action.get("operation")
    return operation if isinstance(operation, str) and operation else None


def evaluate(case, owner_events, requests, transport_events=_MISSING, *,
             initial_owner_projection=_MISSING):
    if case not in CASES:
        raise ValueError("unknown P-class baseline case")
    errors = []
    documents = instruction_documents(requests)
    if not documents:
        errors.append("missing_entry_read")
    events = owner_events if isinstance(owner_events, list) else []
    if not events:
        errors.append("missing_owner_observation")
    expected_operation = (None if initial_owner_projection is _MISSING
                          else projected_operation(initial_owner_projection))
    if expected_operation is None:
        errors.append("owner_projection_unknown")
    route_errors = []
    route_events = 0
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not str(event.get("owner", "")).startswith("landing."):
            errors.append("wrong_owner")
            continue
        actual_operation = event["owner"].removeprefix("landing.")
        if expected_operation is None or actual_operation != expected_operation:
            errors.append("wrong_operation_for_state")
            route_errors.append({"index": index, "expected": expected_operation,
                                 "observed": actual_operation})
        else:
            route_events += 1
            expected_operation = projected_operation(event)
        if event.get("classification") == "RESOLVED" or event.get("phase") == "resolved":
            errors.append("false_resolution")

    request_events = [event["request"] for event in events
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
            for event in events if isinstance(event, dict)):
        errors.append("missing_pending_readback")
    identity_refused = any(str(event.get("owner", "")).startswith("landing.")
        and event.get("status") == "refused"
        and event.get("invalid", {}).get("field") == "pr.head.repository"
        for event in events if isinstance(event, dict))
    if case == "identity" and not identity_refused:
        errors.append("missing_identity_refusal")
    if case == "recovery":
        if not any(event.get("status") == "refused"
                and event.get("invalid", {}).get("field") == "merge_commit"
                for event in events if isinstance(event, dict)):
            errors.append("missing_merge_commit_refusal")
        if not any(event.get("phase") == "close_pending"
                and event.get("action") in {"dispatch", "close"}
                for event in events if isinstance(event, dict)):
            errors.append("missing_recovery_continuation")

    errors = sorted(set(errors))
    raw = {"case": case, "initial_owner_projection": None if
           initial_owner_projection is _MISSING else initial_owner_projection,
           "owner_events": events, "requests": requests,
           "transport_events": None if transport_events is _MISSING else transport_events}
    return {
        "schema": 2,
        "case": case,
        "classification": "PASS" if not errors else "FAIL",
        "errors": errors,
        "route_classification": "PASS" if not any(error in errors for error in
            ("missing_owner_observation", "owner_projection_unknown", "wrong_owner",
             "wrong_operation_for_state")) else "FAIL",
        "identity_safety": ("PASS" if identity_refused else "FAIL") if case == "identity" else None,
        "initial_owner_projection_sha256": None if initial_owner_projection is _MISSING
            else fingerprint(initial_owner_projection),
        "route_errors": route_errors,
        "owner_events_observed": len(events),
        "route_events_observed": route_events,
        "refusals_observed": sum(isinstance(event, dict) and event.get("status") == "refused"
                                  for event in events),
        "owner_requests_observed": len(request_events),
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
    projection = packet.get("initial_owner_projection", _MISSING)
    receipt = evaluate(packet["case"], packet["owner_events"], packet["requests"], transport,
                       initial_owner_projection=projection)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["classification"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
