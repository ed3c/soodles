"""Source-bound cost evidence. No credentials or effect decisions.

Raw records are observational, never an acceptance or spending authority. The
atom supplies its existing lock and durable writer; reports only read files.
"""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import time
import uuid

FAMILIES = ("end_to_end", "processing", "waits", "writer_model", "api",
            "verification", "retries", "startup", "publication", "landing",
            "cleanup", "telemetry")
TOKEN_FIELDS = {"input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens"}
STATUSES = {"passed", "failed", "pending", "refused", "unknown", "not_required"}


class CostRefusal(ValueError):
    pass


def require(condition, field):
    if not condition:
        raise CostRefusal("cost." + field)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate_key:" + key)
        value[key] = item
    return value


def reject_constant(value):
    raise CostRefusal("cost.nonfinite:" + value)


def decode(raw):
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    require(isinstance(value, dict), "object")
    return value


def number(value, field):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, field)
    return value


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)


def status(result):
    if not isinstance(result, dict):
        return "unknown"
    value = result.get("status")
    if value in {"refused", "pending", "unknown", "not_required", "failed"}:
        return value
    if result.get("complete") is False or result.get("exit", result.get("exit_status", 0)):
        return "failed"
    if value in {"resolved", "passed", "completed", "success", "accepted"}:
        return "passed"
    if value is not None:
        return "unknown"
    return "passed" if "exit" in result or "exit_status" in result else "unknown"


def subject(authorization, raw, state):
    require(isinstance(authorization, dict) and isinstance(state, dict), "subject")
    auth = digest(raw)
    require(state.get("issue") is None or isinstance(state["issue"], dict), "state_issue")
    require(state.get("publication") is None or isinstance(state["publication"], dict), "state_publication")
    require(isinstance(state.get("writes", {}), dict), "state_writes")
    require(isinstance(authorization.get("issue"), dict), "authorization_issue")
    require(state.get("authorization_sha256", auth) == auth, "authorization_identity")
    repository = authorization.get("repository")
    require(isinstance(repository, str) and re.fullmatch(r"[^/]+/[^/]+", repository), "repository")
    observed_issue = (state.get("issue") or {}).get("number")
    issue = authorization.get("issue", {}).get("number")
    require(issue is None or type(issue) is int and issue > 0, "issue")
    selected = authorization.get("issue", {}).get("number")
    require(selected is None or observed_issue is None or selected == observed_issue, "issue_identity")
    bound_issue(authorization, {"authorization": auth, "repository": repository, "issue": issue}, state)
    base = authorization.get("base_head")
    require(isinstance(base, str) and re.fullmatch(r"[0-9a-f]{40}", base), "base_head")
    return {"authorization": auth, "repository": repository, "issue": issue, "base_head": base}


def bound_issue(authorization, identity, state):
    """Created Issue readback binds separately from the immutable pre-create subject."""
    observed = state.get("issue") or {}
    number_value = observed.get("number", identity["issue"])
    require(number_value is None or type(number_value) is int and number_value > 0, "observed_issue")
    if identity["issue"] is None and number_value is not None:
        body = authorization["issue"]["body"].rstrip() + "\n\n<!-- soodles:local-atom-v1:" + identity["authorization"] + " -->\n"
        require(state.get("authorization_sha256") == identity["authorization"]
                and observed.get("body_sha256") == digest(body.encode())
                and observed.get("url") == "https://github.com/" + identity["repository"] + "/issues/" + str(number_value),
                "created_issue_binding")
    return number_value


def observation(identity, source, span, *, family, kind, phase, outcome,
                seconds=None, started=None, finished=None, head=None, attempt=None,
                reason="owner observation", worker=None):
    item = {"subject": identity, "source": source, "span": span, "family": family,
            "kind": kind, "phase": phase, "status": outcome, "seconds": seconds,
            "started": started, "finished": finished, "head": head, "attempt": attempt,
            "reason": reason, "worker": worker}
    validate(item, identity)
    return item


def validate(item, identity):
    require(isinstance(item, dict) and item.get("subject") == identity, "observation_subject")
    require(isinstance(item.get("source"), dict) and sha(item["source"].get("sha256"))
            and isinstance(item["source"].get("path"), str) and item["source"]["path"], "source")
    require(isinstance(item.get("span"), str) and item["span"], "span")
    require(item.get("family") in FAMILIES and item.get("kind") in
            {"foreground", "wait", "worker", "detail", "overhead"}, "kind")
    require(item.get("status") in STATUSES, "status")
    require(isinstance(item.get("phase"), str) and isinstance(item.get("reason"), str), "phase_reason")
    for field in ("seconds", "started", "finished"):
        if item.get(field) is not None:
            number(item[field], field)
    require(item.get("finished") is None or item.get("started") is not None
            and item["finished"] >= item["started"], "timestamp_order")
    require(item.get("seconds") is None or item.get("finished") is not None
            or item.get("started") is None, "incomplete_span")
    require(item.get("head") is None or isinstance(item["head"], str)
            and re.fullmatch(r"[0-9a-f]{40}", item["head"]), "head")
    require(item.get("attempt") is None or type(item["attempt"]) is int and item["attempt"] > 0
            or isinstance(item.get("attempt"), str) and bool(item["attempt"]), "attempt")
    if "usage" in item:
        require(isinstance(item["usage"], dict) and set(item["usage"]) <= {"reported_cost_usd", "tokens"}, "usage")
        for key, value in item["usage"].items():
            if key == "tokens":
                require(isinstance(value, dict) and set(value) <= TOKEN_FIELDS and value, "tokens")
                for name, count in value.items():
                    require(type(count) is int and count >= 0, "token_" + name)
            else:
                number(value, key)
    if "scope" in item:
        require(isinstance(item["scope"], dict), "scope")
        count = item["scope"].get("count")
        require(count is None or type(count) is int and count >= 0, "scope_count")


def intervals(items):
    ranges = sorted((x["started"], x["finished"]) for x in items
                    if x.get("started") is not None and x.get("finished") is not None)
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged) if ranges else None


def project(identity, observations, gate=None):
    """Validate all evidence before producing any numeric summary."""
    seen = {}
    for item in observations:
        validate(item, identity)
        # Same physical span cannot be relabeled through another manifest entry.
        session = item["attempt"] if item["span"] == "native" and item["family"] == "writer_model" else None
        key = (item["source"]["sha256"], item["span"], session)
        previous = seen.get(key)
        comparable = {**item, "source": {"sha256": item["source"]["sha256"]}}
        require(previous is None or {**previous, "source": {"sha256": previous["source"]["sha256"]}}
                == comparable, "conflicting_replay:" + item["span"])
        seen[key] = item
    values = list(seen.values())
    coverage = {}
    # This is evidence availability, never a claim of complete lifecycle timing.
    for family in FAMILIES:
        found = [item for item in values if item["family"] == family]
        numeric = [item for item in found if item["seconds"] is not None]
        coverage[family] = {
            "status": "not_required" if found and all(x["status"] == "not_required" for x in found)
            else "partial" if found else "unknown",
            "reason": "observed spans only; whole-lifecycle coverage not asserted" if found
            else "no source-bound observation available",
            "observations": len(found), "measured_spans": len(numeric),
            "evidence": sorted({x["source"]["sha256"] for x in found})}
    foreground = [x for x in values if x["kind"] == "foreground"]
    if foreground:
        coverage["end_to_end"] = {"status": "partial", "reason": "observed foreground envelope only; gaps unattributed",
            "observations": len(foreground), "measured_spans": sum(x["seconds"] is not None for x in foreground),
            "evidence": sorted({x["source"]["sha256"] for x in foreground})}
    waits = [x for x in values if x["kind"] == "wait"]
    workers = [x for x in values if x["kind"] == "worker"]
    by_worker = {}
    for item in workers:
        by_worker.setdefault(item.get("worker") or item["span"], []).append(item)
    worker_seconds = []
    for items in by_worker.values():
        bounded = [x for x in items if x["started"] is not None and x["finished"] is not None]
        unbounded = [x for x in items if x["started"] is None and x["seconds"] is not None]
        if bounded:
            worker_seconds.append(intervals(bounded))
        worker_seconds.extend(x["seconds"] for x in unbounded)
    bounds = [x for x in foreground if x["started"] is not None and x["finished"] is not None]
    provider_jobs = {}
    for item in values:
        if item["phase"].startswith("provider_job:") and item["seconds"] is not None:
            key = (item["head"], item["attempt"], item["span"])
            job_bounds = (item["started"], item["finished"], item["seconds"])
            require(provider_jobs.get(key, job_bounds) == job_bounds, "conflicting_provider_duration")
            provider_jobs[key] = job_bounds
    phases, usage_sessions, phase_jobs = {}, {}, set()
    for item in values:
        if item.get("usage"):
            session = usage_sessions.setdefault(item["attempt"], {"session": item["attempt"], "sources": []})
            session["sources"].append(item["source"])
            for key, value in item["usage"].items():
                require(session.get(key, value) == value, "conflicting_native_usage")
                session[key] = value
        if item["phase"].startswith("provider_job:") and item["seconds"] is not None:
            key = (item["head"], item["attempt"], item["span"])
            if key in phase_jobs:
                continue
            phase_jobs.add(key)
        key = (item["phase"], item["kind"], item.get("worker") or "")
        phase = phases.setdefault(key, {"phase": item["phase"], "kind": item["kind"],
            "worker": item.get("worker"), "observations": 0, "measured_spans": 0,
            "inclusive_seconds": None, "statuses": {}, "sources": []})
        phase["observations"] += 1
        phase["statuses"][item["status"]] = phase["statuses"].get(item["status"], 0) + 1
        if item["seconds"] is not None:
            phase["measured_spans"] += 1
            phase["inclusive_seconds"] = (phase["inclusive_seconds"] or 0) + item["seconds"]
        if item["source"]["sha256"] not in phase["sources"]:
            phase["sources"].append(item["source"]["sha256"])
    token_sessions = [value["tokens"] for value in usage_sessions.values() if "tokens" in value]
    tokens = ({name: sum(value[name] for value in token_sessions if name in value)
               for name in TOKEN_FIELDS if any(name in value for value in token_sessions)}
              if token_sessions else None)
    summary = {"observations": len(values),
               "statuses": {name: sum(x["status"] == name for x in values) for name in sorted(STATUSES)},
               "observed_wall_seconds": intervals(foreground + waits),
               "foreground_seconds": intervals(foreground),
               "external_wait_seconds": intervals(waits),
               "parallel_worker_seconds": sum(worker_seconds) if worker_seconds else None,
               "observed_envelope_seconds": max(x["finished"] for x in bounds) - min(x["started"] for x in bounds) if bounds else None,
               "provider_job_seconds": sum(value[2] for value in provider_jobs.values()) if provider_jobs else None,
               "cpu_seconds": None, "tokens": tokens, "price": None,
               "api_calls": None, "human_wait_seconds": None,
               "native_usage": list(usage_sessions.values()),
               "phase_costs": list(phases.values()),
               "phase_basis": "inclusive observed durations, not additive across nested phases; missing spans unknown",
               "logged_wait_seconds": sum(x["seconds"] for x in values if x["family"] == "waits" and x["seconds"] is not None)
                   if any(x["family"] == "waits" and x["seconds"] is not None for x in values) else None,
               "verification_modules": sorted({x["scope"]["module"] for x in values
                    if isinstance(x.get("scope", {}).get("module"), str)}),
               "basis": "interval union for observed wall; foreground includes I/O; worker time is separate, nested details excluded"}
    from schema_manager import project_cost
    from test_manager import review_cost
    facts = {"subject": identity, "coverage": coverage, "summary": summary,
             "sources": sorted({x["source"]["sha256"] for x in values})}
    review = review_cost(facts)
    return {**facts, "schema_projection": project_cost(facts, gate, review=review), "authorizes_landing": False}


def read_ref(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}
            and isinstance(ref["path"], str) and Path(ref["path"]).is_absolute()
            and sha(ref["sha256"]), "file_reference")
    raw = Path(ref["path"]).read_bytes()
    require(digest(raw) == ref["sha256"], "digest:" + ref["path"])
    return raw


def file_ref(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": digest(path.read_bytes())}


def timestamp(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timezone")
    return number(parsed.timestamp(), "timestamp")


def timing_log(raw, ref, identity, *, head=None, attempt=None):
    """Legacy lines have no bounds. Never invent them or sum nested cases."""
    result = []
    for index, line in enumerate(raw.decode().splitlines()):
        pos = line.find('{"event": "soodles.timing"')
        if pos < 0:
            continue
        value = decode(line[pos:])
        require(isinstance(value, dict), "timing")
        operation = value.get("operation", "unknown")
        observed_head = value.get("head", head)
        require(head is None or observed_head == head, "timing_head")
        if value.get("authorization_sha256") is not None:
            require(value["authorization_sha256"] == identity["authorization"], "timing_authorization")
        outcome = status(value)
        if "status" not in value and value.get("outcome") in STATUSES:
            outcome = value["outcome"]
        # Old measured wrongly called returned pending/refused results passed.
        if value.get("status") in {"pending", "refused"}:
            outcome = value["status"]
        if operation == "issue_atom.wait" and outcome == "passed":
            outcome = "pending"
        family = "verification" if operation.startswith(("test.", "acceptance.")) else "waits" if operation == "issue_atom.wait" else "processing"
        result.append(observation(identity, ref, value.get("span_id") or "line:" + str(index),
            family=family, kind="worker" if operation == "test.module" else "wait" if operation == "issue_atom.wait" else "detail",
            phase=operation, outcome=outcome, seconds=value.get("seconds"),
            started=value.get("wall_started"), finished=value.get("wall_finished"),
            head=observed_head, attempt=attempt, worker=value.get("module"),
            reason="normal stderr timing; legacy bounds/usage may be absent"))
        if operation.startswith("test."):
            result[-1]["scope"] = {key: value[key] for key in ("module", "test", "count") if key in value}
            validate(result[-1], identity)
    return result


def gate_from_state(state, source, result=None):
    result = result or {}
    repair = state.get("repair")
    if repair is not None:
        require(isinstance(repair, dict), "repair_history")
        for field in ("started", "last_time"):
            if repair.get(field) is not None:
                number(repair[field], "repair_" + field)
        for group in ("limits", "used"):
            require(isinstance(repair.get(group), dict), "repair_" + group)
            for key, value in repair[group].items():
                number(value, "repair_" + key)
        require(all(key in repair["limits"] and value <= repair["limits"][key]
                    for key, value in repair["used"].items()), "repair_counters")
    budget = result.get("repair_budget") or {}
    for field in ("elapsed_seconds", "remaining_seconds"):
        if budget.get(field) is not None:
            number(budget[field], "budget_" + field)
    for group in ("limits", "used"):
        for key, value in budget.get(group, {}).items():
            number(value, "budget_" + key)
    remaining = (result.get("repair") or {}).get("remaining") or {}
    for key, value in remaining.items():
        number(value, "remaining_" + key)
    return {"owner": "issue_atom/atom_repair", "source": source,
            "status": result.get("status", "resolved" if state.get("phase") == "resolved" else "unknown"),
            "invalid": result.get("invalid"), "required": (result.get("next") or {}).get("required"),
            "repair": result.get("repair"), "repair_budget": result.get("repair_budget"),
            "repair_history": {key: repair.get(key) for key in ("lineage", "policy", "started", "last_time", "limits", "used")}
                if repair is not None else None,
            "basis": "elapsed since first repair; not whole-Issue spend or compute",
            "write_history": {k: v for k, v in state.get("writes", {}).items()},
            "write_history_basis": "historical offers; current required readback comes only from owner result",
            "host_finalization": state.get("host_finalization"), "authorizes_landing": False}


def report(authorization_path, manifest_path=None, *, state=None, result=None):
    """Read-only report; also used automatically by the normal locked owner."""
    path = Path(authorization_path).resolve()
    raw = path.read_bytes()
    authorization = decode(raw)
    directory = path.parent / (path.name + ".d")
    source = None
    if manifest_path is not None:
        manifest = decode(Path(manifest_path).read_bytes())
        required = {"schema", "authorization_sha256", "subject", "state", "head"}
        optional = {"claim", "owner_result", "processes", "intents", "provider", "native"}
        require(required <= set(manifest) <= required | optional, "manifest_fields")
        require(type(manifest.get("schema")) is int and manifest["schema"] == 1
                and manifest.get("authorization_sha256") == digest(raw), "manifest_authorization")
        require(all(isinstance(manifest.get(key, []), list) for key in
                    ("processes", "intents", "provider", "native")), "manifest_lists")
        source = manifest["state"]
        state = decode(read_ref(source))
        require(state.get("authorization_sha256") == digest(raw), "state_authorization")
    elif state is None:
        state_path = path.with_name(path.name + ".state.json")
        source = file_ref(state_path) if state_path.exists() else None
        state = decode(read_ref(source)) if source else {}
    identity = subject(authorization, raw, state)
    from issue_atom import publication_receipt_view
    receipts = publication_receipt_view(path, raw, state)
    observations = []
    sources = []
    for record in sorted((directory / "cost").glob("*.json")):
        ref = file_ref(record)
        entry = decode(read_ref(ref))
        require(entry.get("subject") == identity, "record_identity")
        for item in entry["observations"]:
            read_ref(item["source"])
            sources.append(item["source"])
        observations.extend(entry["observations"])
        sources.append(ref)
    if manifest_path is None:
        claim_refs = [entry["claim"] for entry in receipts["retained"]]
        current_path = Path(receipts["current"]["paths"]["claim"])
        if current_path.exists():
            claim_refs.append(file_ref(current_path))
        for claim_ref in claim_refs:
            claim = decode(read_ref(claim_ref))
            session = claim.get("session_id")
            require(isinstance(session, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", session), "native_session_path")
            observed = {"claim": claim_ref, "head": claim.get("head")}
            native_path = Path(authorization["control_root"]) / ".noodle" / "sessions" / session / "raw.ndjson"
            if native_path.is_file():
                observed["native"] = [{
                    "file": file_ref(native_path), "kind": "codex_raw", "session_id": session,
                    "order_id": claim.get("order_id")} ]
            observations.extend(external(observed, identity, state, path, sources, authorization,
                                         receipts=receipts))
    if manifest_path is not None:
        require(manifest.get("subject") == identity, "manifest_subject")
        observations.extend(external(manifest, identity, state, path, sources, authorization,
                                     receipts=receipts))
        if manifest.get("owner_result"):
            result_ref = manifest["owner_result"]
            owner_result = decode(read_ref(result_ref))
            require(isinstance(owner_result, dict) and owner_result.get("owner") == "soodles.issue-atom", "owner_result")
            owner_issue = owner_result.get("issue")
            require(owner_issue is None or owner_issue.get("number") == (state.get("issue") or {}).get("number"), "owner_result_issue")
            owner_publication = owner_result.get("publication")
            require(owner_publication is None or owner_publication.get("head") == manifest.get("head"), "owner_result_head")
            if result is None:
                result = owner_result
            sources.append(result_ref)
    if source is None and state:
        state_path = path.with_name(path.name + ".state.json")
        if state_path.exists():
            source = file_ref(state_path)
    if source:
        sources.append(source)
    if state.get("repair") is not None and source:
        observations.append(observation(identity, source, "repair-history", family="retries", kind="detail",
            phase=state.get("phase", "unknown"), outcome="unknown",
            reason="reserved repair history; elapsed repair deadline is not processing cost"))
    projection = project(identity, observations, gate_from_state(state, source, result))
    if source:
        read_ref(source)
    require(path.read_bytes() == raw, "authorization_changed")
    report = {"status": "reported", **projection, "evidence": sources,
              "artifacts": str(directory / "cost")}
    from schema_manager import project_owner_feedback
    return {**report, "feedback": project_owner_feedback({**(result or {}), "cost": report})}


def receipt_claim(claim_ref, identity, state, receipts, sources, authorization):
    claim = decode(read_ref(claim_ref))
    issue_number = bound_issue(authorization, identity, state)
    require(claim.get("repository") == identity["repository"]
            and claim.get("subject") == identity["repository"] + "#" + str(issue_number), "claim_subject")
    retained = next((entry for entry in receipts["retained"] if entry["claim"] == claim_ref), None)
    if retained is not None:
        lineage = retained["lineage"]
    else:
        current = receipts["current"]
        if state.get("scope_amendment") is not None or state.get("scope_history") or state.get("scope_superseded"):
            current_path = Path(current["paths"]["claim"])
            require(current_path.is_file() and claim_ref == file_ref(current_path), "claim_receipt")
        head = (state.get("publication") or {}).get("head")
        require(head is None or claim.get("head") == head, "claim_head")
        lineage = current["lineage"]
    require(lineage["authorization_sha256"] == identity["authorization"], "claim_authorization")
    require(claim.get("base_head") == lineage["base_head"], "claim_base")
    sources.extend(lineage["sources"])
    sources.append(claim_ref)
    return claim


def external(manifest, identity, state, authorization_path, sources, authorization, *, receipts=None):
    result = []
    head = (state.get("publication") or {}).get("head")
    issue_number = bound_issue(authorization, identity, state)
    claim_ref = manifest.get("claim")
    if claim_ref:
        if receipts is None:
            from issue_atom import publication_receipt_view
            receipts = publication_receipt_view(authorization_path, Path(authorization_path).read_bytes(), state)
        claim = receipt_claim(claim_ref, identity, state, receipts, sources, authorization)
        head = claim.get("head")
    require(manifest.get("head") == head, "manifest_head")
    for entry in manifest.get("intents", []):
        require(isinstance(entry, dict) and set(entry) == {"intent", "input", "observer"}, "intent_fields")
        ref = entry["intent"]
        intent = decode(read_ref(ref))
        prior = decode(read_ref(entry["input"]))
        observer = read_ref(entry["observer"])
        argv = intent.get("argv")
        require(intent.get("input_receipt") == entry["input"]["path"]
                and intent.get("input_sha256") == entry["input"]["sha256"]
                and intent.get("observer_sha256") == digest(observer), "intent_source")
        require(isinstance(argv, list) and argv == (prior.get("next") or {}).get("argv")
                and str(authorization_path) in argv, "intent_argv")
        require("wall_finished" not in intent and "exit_status" not in intent, "intent_incomplete")
        result.append(observation(identity, ref, "foreground", family="processing", kind="foreground",
            phase="unknown", outcome="unknown", started=intent.get("wall_started"), head=head,
            reason="supervisor start without process completion; elapsed cost unknown"))
        sources.extend(entry[key] for key in ("intent", "input", "observer"))
    for entry in manifest.get("processes", []):
        require(isinstance(entry, dict) and set(entry) == {"process", "input", "stdout", "stderr", "observer"}, "process_fields")
        ref = entry["process"]
        process = decode(read_ref(ref))
        input_raw = read_ref(entry["input"])
        stdout = read_ref(entry["stdout"])
        stderr = read_ref(entry["stderr"])
        observer = read_ref(entry["observer"])
        require(process.get("observer_sha256") == digest(observer), "observer")
        require(process.get("input_sha256") == digest(input_raw)
                and process.get("input_receipt") == entry["input"]["path"], "process_input")
        require(process.get("stdout_sha256") == digest(stdout)
                and process.get("stderr_sha256") == digest(stderr), "process_output")
        prior = decode(input_raw)
        argv = process.get("argv")
        require(isinstance(argv, list) and argv == (prior.get("next") or {}).get("argv")
                and str(authorization_path) in argv, "process_argv")
        env = (prior.get("next") or {}).get("environment", {})
        require(env.get("SOODLES_AUTHORIZATION_SHA256", identity["authorization"]) == identity["authorization"], "process_authorization")
        require(type(process.get("exit_status")) is int, "process_exit")
        try:
            output = decode(stdout)
        except json.JSONDecodeError:
            output = {}
        if isinstance(output, dict):
            issue = output.get("issue")
            require(not isinstance(issue, dict) or issue.get("number") == issue_number, "process_issue")
            published = output.get("publication")
            require(not isinstance(published, dict) or published.get("head") == head, "process_head")
        result.append(observation(identity, ref, "foreground", family="processing", kind="foreground",
            phase=output.get("phase", "unknown") if isinstance(output, dict) else "unknown",
            outcome=output["status"] if isinstance(output, dict) and output.get("status") in {"refused", "pending", "unknown", "failed"} else "failed" if process["exit_status"] else status(output),
            seconds=process.get("seconds"), started=process.get("wall_started"),
            finished=process.get("wall_finished"), head=head,
            reason="external observer foreground; includes waits and I/O, origin is not truth"))
        result.extend(timing_log(stderr, entry["stderr"], identity, head=head))
        sources.extend(entry[key] for key in ("process", "input", "stdout", "stderr", "observer"))
    provider_snapshots = {}
    for entry in manifest.get("provider", []):
        require(isinstance(entry, dict) and {"run", "jobs"} <= set(entry) <= {"run", "jobs", "log"}, "provider_fields")
        require(head is not None, "provider_head_required")
        run = decode(read_ref(entry["run"]))
        jobs = decode(read_ref(entry["jobs"]))
        require(run.get("head_sha") == head and isinstance(run.get("repository"), dict)
                and run["repository"].get("full_name") == identity["repository"], "provider_subject")
        require(isinstance(jobs.get("jobs"), list) and all(isinstance(job, dict) for job in jobs["jobs"]), "provider_jobs")
        require(type(run.get("id")) is int and run["id"] > 0
                and type(run.get("run_attempt")) is int and run["run_attempt"] > 0, "provider_run")
        run_key = (run["id"], run["run_attempt"])
        snapshot = (entry["run"]["sha256"], entry["jobs"]["sha256"])
        require(provider_snapshots.get(run_key, snapshot) == snapshot, "conflicting_provider_snapshot")
        provider_snapshots[run_key] = snapshot
        workflow = authorization.get("workflow", {}).get("path")
        require(workflow is None or run.get("path") == workflow, "provider_workflow")
        result.append(observation(identity, entry["run"], "provider-readback", family="api", kind="detail",
            phase="provider_readback", outcome="pending" if run.get("status") != "completed" else "unknown",
            head=head, attempt=run["run_attempt"], reason="provider file observation; API request accounting unavailable"))
        for job in jobs["jobs"]:
            require(job.get("head_sha") == head and job.get("run_id") == run["id"]
                    and job.get("run_attempt") == run["run_attempt"], "provider_job")
            start, end = timestamp(job.get("started_at")), timestamp(job.get("completed_at"))
            outcome = "pending" if job.get("status") != "completed" else "passed" if job.get("conclusion") == "success" else "failed"
            result.append(observation(identity, entry["jobs"], "job:" + str(run["id"]) + ":" + str(job["id"]),
                family="verification", kind="detail", phase="provider_job:" + job["name"], outcome=outcome,
                seconds=end-start if start is not None and end is not None else None,
                started=start, finished=end, head=head, attempt=run["run_attempt"],
                reason="provider job wall; not added to nested module worker totals"))
        sources.extend((entry["run"], entry["jobs"]))
        if entry.get("log"):
            result.extend(timing_log(read_ref(entry["log"]), entry["log"], identity,
                                     head=head, attempt=run["run_attempt"]))
            sources.append(entry["log"])
    # Native raw logs may be retained with a claim/session link. No guessed usage.
    for entry in manifest.get("native", []):
        require(isinstance(entry, dict) and {"file", "session_id", "order_id"} <= set(entry)
                <= {"file", "session_id", "order_id", "kind"} and entry.get("kind") in {None, "meta", "raw", "codex_raw"}, "native_fields")
        require(claim_ref is not None and entry.get("session_id") == claim.get("session_id")
                and entry.get("order_id") == claim.get("order_id"), "native_identity")
        raw = read_ref(entry["file"])
        usage = {}
        if entry.get("kind") == "meta":
            meta = decode(raw)
            require(meta.get("session_id") == entry["session_id"], "native_session")
            if meta.get("total_cost_usd") is not None:
                usage["reported_cost_usd"] = number(meta["total_cost_usd"], "native_reported_cost")
        elif entry.get("kind") == "codex_raw":
            turns = []
            for line in raw.splitlines():
                if not line.strip():
                    continue
                event = decode(line)
                if event.get("type") == "turn.completed":
                    tokens = event.get("usage")
                    require(isinstance(tokens, dict), "native_usage")
                    tokens = {key: value for key, value in tokens.items() if key in TOKEN_FIELDS}
                    require(tokens and all(type(value) is int and value >= 0 for value in tokens.values()), "native_tokens")
                    turns.append(tokens)
            # Multiple turns may use cumulative or incremental provider accounting.
            # Retain the source, but do not guess a session total for that format.
            if len(turns) == 1:
                usage["tokens"] = turns[0]
        sources.append(entry["file"])
        result.append(observation(identity, entry["file"], "native", family="writer_model",
            kind="detail", phase="execute", outcome="unknown", head=head,
            attempt=entry["session_id"], reason="native evidence retained; reported metadata is not independent billing authority"))
        if usage:
            result[-1]["usage"] = usage
    return result


def begin(authorization_path, save, *, waiting=None):
    """Caller holds the original authorization lock. Intent survives interruption."""
    path = Path(authorization_path).resolve()
    raw = path.read_bytes()
    state_path = path.with_name(path.name + ".state.json")
    state = decode(state_path.read_bytes()) if state_path.exists() else {}
    identity = subject(decode(raw), raw, state)
    record_path = path.parent / (path.name + ".d") / "cost" / (uuid.uuid4().hex + ".json")
    started = time.time()
    record = {"subject": identity, "started": started, "observations": [observation(
        identity, {"path": str(path), "sha256": digest(raw)}, record_path.stem,
        family="waits" if waiting else "processing", kind="wait" if waiting else "foreground",
        phase=state.get("phase", "entry"), outcome="unknown", started=started,
        reason="incomplete invocation intent")]}
    if waiting:
        record["waiting_on"] = waiting
    save(record_path, record)
    return record_path, record, time.monotonic()


def finish(authorization_path, handle, result, save):
    overhead_started, overhead_wall = time.monotonic(), time.time()
    path, record, started = handle
    item = record["observations"][0]
    item.update(seconds=time.monotonic()-started, finished=time.time(), status=status(result),
                phase=result.get("phase", item["phase"]), reason="normal locked owner invocation")
    item["head"] = (result.get("publication") or {}).get("head")
    authority_path = Path(authorization_path).resolve()
    raw = authority_path.read_bytes()
    state_path = authority_path.with_name(authority_path.name + ".state.json")
    state = decode(state_path.read_bytes()) if state_path.exists() else {}
    from issue_atom import publication_receipt_view
    receipts = publication_receipt_view(authority_path, raw, state)
    claim_path = Path(receipts["current"]["paths"]["claim"])
    if claim_path.exists():
        claim = receipt_claim(file_ref(claim_path), record["subject"], state, receipts, [], decode(raw))
        require(item["head"] is None or item["head"] == claim.get("head"), "normal_claim_head")
        item["attempt"] = claim.get("session_id")
        item["head"] = claim.get("head", item["head"])
    phase_family = {"issue": "startup", "execution": "writer_model", "ci": "verification",
                    "publication": "publication", "landing": "landing", "resolved": "cleanup"}.get(item["phase"])
    if phase_family and item["kind"] != "wait":
        record["observations"].append({**item, "span": item["span"] + ":phase", "kind": "detail",
            "family": phase_family, "reason": "foreground ending in phase; not exclusive phase time"})
    save(path, record)
    manifest = Path(authorization_path).resolve().parent / (Path(authorization_path).name + ".d") / "cost-evidence.json"
    projection = report(authorization_path, manifest if manifest.exists() else None, result=result)
    record["observations"].append(observation(record["subject"], item["source"], item["span"] + ":telemetry",
        family="telemetry", kind="overhead", phase="report", outcome="passed",
        seconds=time.monotonic()-overhead_started, started=overhead_wall, finished=time.time(),
        reason="record/report overhead; final evidence flush excluded; visible on next projection"))
    save(path, record)
    return {**projection, "observation_id": item["span"]}


def failure(error):
    return {"status": "refused", "invalid": {"field": "cost.evidence", "value": str(error)},
            "authorizes_landing": False, "reason": "cost projection unavailable; original owner continuation unchanged"}


def record_provider(authorization_path, state, run, jobs, save):
    """Observe already-returned provider data; never request another read."""
    if run is None:
        return
    path = Path(authorization_path).resolve()
    raw = path.read_bytes()
    authorization = decode(raw)
    identity = subject(authorization, raw, state)
    directory = path.parent / (path.name + ".d") / "cost"
    refs = []
    for label, value in (("run", run), ("jobs", jobs)):
        target = directory / "raw" / (label + "-" + digest(canonical(value)) + ".json")
        if target.exists():
            require(decode(target.read_bytes()) == value, "provider_record_changed")
        else:
            save(target, value)
        refs.append(file_ref(target))
    manifest = {"head": (state.get("publication") or {}).get("head"),
                "provider": [{"run": refs[0], "jobs": refs[1]}]}
    observations = external(manifest, identity, state, path, [], authorization)
    target = directory / ("provider-" + digest(canonical(refs)) + ".json")
    record = {"subject": identity, "observations": observations}
    if target.exists():
        require(decode(target.read_bytes()) == record, "conflicting_provider_record")
    else:
        save(target, record)
