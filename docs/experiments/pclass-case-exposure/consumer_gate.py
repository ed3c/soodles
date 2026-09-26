"""Validate one bounded #157 Local Codex comparison from captured bytes.

The selected external observer remains the independent experiment judge. This
candidate gate only checks a narrow, portable capture contract for exact-head
acceptance. It never launches an agent, imports supplied code, repairs evidence,
or grants landing authority.
"""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys

MAX_BYTES = 1_048_576
RAW_MAX_BYTES = 8_000_000
CASES = ("matched_legal_improvement", "mismatched_case_exposure",
         "missing_required_observation")
ARMS = ("baseline", "treatment")


def refusal(field, reason, validity="INCONCLUSIVE", required="selected_consumer_evidence"):
    return {
        "schema": 1, "owner": "pclass.consumer_evidence",
        "issue": {"repository": "ed3c/soodles", "number": 157},
        "scope": "required-consumer-evidence readiness veto only",
        "evidence_validity": validity, "behavior": None,
        "terminal_ready": False, "authorizes_landing": False,
        "problem": {"field": field, "reason": reason},
        "next": {"kind": "input", "owner": "supervisor", "required": [required]},
    }


def inspect_comparison(value, evidence_root=None):
    if not isinstance(value, dict) or type(value.get("schema")) is not int:
        return refusal("schema", "expected a versioned comparison object", "INVALID")
    if value["schema"] == 2:
        return inspect_selected_comparison(value, evidence_root)
    if value["schema"] != 1:
        return refusal("schema", "no validated capture adapter for this schema",
                       required="supervisor_selected_capture_validator")
    issue = value.get("issue")
    if (not isinstance(issue, dict) or type(issue.get("number")) is not int
            or issue != {"repository": "ed3c/soodles", "number": 157}):
        return refusal("issue", "comparison does not belong to this atom", "INVALID")
    if value.get("authorizes_landing") is not False:
        return refusal("authorizes_landing", "comparison cannot grant authority", "INVALID")
    runs = value.get("fresh_runs")
    if not isinstance(runs, list):
        return refusal("fresh_runs", "required run observations are absent or malformed")
    # Schema 1 is only a public status projection. Its self-labelled run and
    # telemetry fields never acquire the raw-capture meaning of schema 2.
    if runs:
        return refusal("schema", "status projection cannot carry raw captures", "INVALID",
                       required="supervisor_selected_capture_validator")
    return refusal("fresh_runs", "six raw consumer captures are not present in this artifact")


def raw_file(root, descriptor):
    if not isinstance(descriptor, dict) or set(descriptor) not in (
            {"path", "sha256"}, {"base64", "sha256"}):
        raise ValueError("capture descriptor is missing")
    expected = descriptor["sha256"]
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise ValueError("capture digest absent")
    if "base64" in descriptor:
        encoded = descriptor["base64"]
        if not isinstance(encoded, str) or len(encoded) > (RAW_MAX_BYTES * 4 // 3 + 4):
            raise ValueError("inline capture exceeds bound")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("inline capture is not base64") from error
    else:
        relative = Path(descriptor["path"])
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ValueError("raw file path escapes the evidence root")
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("raw file path resolves outside the evidence root")
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("raw evidence is not a regular file")
            data = stream.read(RAW_MAX_BYTES + 1)
    if len(data) > RAW_MAX_BYTES or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("raw file length or digest differs")
    return data


def strict_value(data):
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


def raw_jsonl(data):
    if not data or not data.endswith(b"\n"):
        raise ValueError("raw JSONL is empty or unterminated")
    events = [strict_value(line) for line in data.splitlines()]
    if any(not isinstance(event, dict) or not isinstance(event.get("type"), str)
           for event in events):
        raise ValueError("raw JSONL event is not a typed object")
    return events


def exactly_one(rows, what):
    if len(rows) != 1:
        raise ValueError(f"expected one {what}; found {len(rows)}")
    return rows[0]


def shell_argv(command):
    """Decode the selected CLI's /bin/zsh -lc command display, not arbitrary shell."""
    outer = shlex.split(command)
    if len(outer) != 3 or outer[:2] != ["/bin/zsh", "-lc"]:
        raise ValueError("unselected command wrapper")
    return shlex.split(outer[2])


def inspect_raw_run(run, packet, common, root, capture_scope):
    if not isinstance(run, dict) or run.get("id") != packet["id"]:
        raise ValueError("run identity differs from selection")
    capture = run.get("capture")
    required = {"request", "result", "stdout", "stderr", "final", "rollout"}
    if not isinstance(capture, dict) or set(capture) != required:
        raise ValueError("six raw capture files are required per run")
    field = "base64" if capture_scope == "public_projection" else "path"
    if any(not isinstance(capture[name], dict) or set(capture[name]) != {field, "sha256"}
           for name in required):
        raise ValueError("capture representation differs from selected scope")
    if capture_scope == "public_projection" and not re.fullmatch(
            r"[0-9a-f]{64}", run.get("private_rollout_sha256", "")):
        raise ValueError("private rollout digest absent from public projection")
    data = {name: raw_file(root, capture[name]) for name in required}
    request, result = strict_value(data["request"]), strict_value(data["result"])
    if not isinstance(request, dict) or not isinstance(result, dict):
        raise ValueError("outer recorder JSON must be objects")
    if (result.get("scope") != "one_subprocess" or result.get("authorizes_landing") is not False
            or result.get("exit_code") != 0 or result.get("timed_out") is not False
            or result.get("error") is not None):
        raise ValueError("Codex process did not complete normally")
    if (result.get("stdout_sha256") != capture["stdout"]["sha256"]
            or result.get("stderr_sha256") != capture["stderr"]["sha256"]):
        raise ValueError("recorder raw stream digest differs")
    argv = request.get("argv")
    if not isinstance(argv, list) or len(argv) < 12 or argv[0] != "codex":
        raise ValueError("Codex argv absent")
    final_original = packet["final_path"]
    expected = ["codex", "-C", packet["cwd"], "exec", *common["launch_options"],
                "--json", "--output-schema", common["output_schema_path"],
                "-o", final_original]
    if argv[:-1] != expected or not isinstance(argv[-1], str):
        raise ValueError("Codex launch differs from selected exact argv")
    if hashlib.sha256(argv[-1].encode()).hexdigest() != packet["prompt_sha256"]:
        raise ValueError("submitted prompt bytes differ")
    if request.get("cwd") != common["supervisor_cwd"]:
        raise ValueError("recorder cwd differs")
    before, after = request.get("files_before"), result.get("files_after")
    if (not isinstance(before, dict) or not isinstance(after, dict)
            or before.get(common["output_schema_path"], {}).get("sha256") != common["output_schema_sha256"]
            or any(after.get(path) != state for path, state in before.items())):
        raise ValueError("recorded argv input snapshot differs")
    if after.get(final_original, {}).get("sha256") != capture["final"]["sha256"]:
        raise ValueError("recorder final-message digest differs")
    events = raw_jsonl(data["stdout"])
    thread = exactly_one([event.get("thread_id") for event in events
                          if event.get("type") == "thread.started"], "thread identity")
    if not isinstance(thread, str) or not thread:
        raise ValueError("thread identity absent")
    exactly_one([e for e in events if e.get("type") == "turn.started"], "turn start")
    exactly_one([e for e in events if e.get("type") == "turn.completed"], "turn completion")
    if any(e.get("type") in {"turn.failed", "error"} for e in events):
        raise ValueError("CLI emitted terminal error")
    items = [e.get("item") for e in events if e.get("type", "").startswith("item.")]
    if any(not isinstance(item, dict) or item.get("type") not in
           {"agent_message", "command_execution", "reasoning"} for item in items):
        raise ValueError("unselected CLI item/tool type")
    messages = [e["item"].get("text") for e in events if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "agent_message"]
    if not messages or not isinstance(messages[-1], str) or messages[-1].strip() != data["final"].decode().strip():
        raise ValueError("last agent message differs from final raw bytes")
    final = strict_value(data["final"])
    if (not isinstance(final, dict) or set(final) != {"decision", "next_owner"}
            or final["decision"] not in {"ADMIT_IMPROVEMENT", "ADMIT_NONREGRESSION", "REJECT"}
            or final["next_owner"] is not None and not isinstance(final["next_owner"], str)):
        raise ValueError("final decision schema invalid")
    rollout = raw_jsonl(data["rollout"])
    if capture_scope == "public_projection" and (len(rollout) != 2
            or rollout[0].get("type") != "session_meta"
            or set(rollout[0]) != {"type", "payload"}
            or set(rollout[0].get("payload", {})) != {"id", "cwd", "cli_version", "git"}
            or set(rollout[0]["payload"].get("git", {})) != {"commit_hash"}
            or rollout[1].get("type") != "turn_context"
            or set(rollout[1]) != {"type", "payload"}
            or set(rollout[1].get("payload", {})) != {"model", "effort", "approval_policy", "sandbox_policy"}
            or set(rollout[1]["payload"].get("sandbox_policy", {})) != {"type"}):
        raise ValueError("public rollout projection has unselected fields")
    meta = exactly_one([e.get("payload") for e in rollout if e.get("type") == "session_meta"], "rollout meta")
    turn = exactly_one([e.get("payload") for e in rollout if e.get("type") == "turn_context"], "rollout context")
    if not isinstance(meta, dict) or not isinstance(turn, dict):
        raise ValueError("rollout meta/context absent")
    if (meta.get("id") != thread or meta.get("cwd") != packet["cwd"]
            or meta.get("git", {}).get("commit_hash") != packet["source_ref"]
            or meta.get("cli_version") != common["cli_version"]
            or turn.get("model") != common["model"] or turn.get("effort") != common["reasoning"]
            or turn.get("approval_policy") != common["approval"]
            or turn.get("sandbox_policy", {}).get("type") != common["sandbox"]):
        raise ValueError("persisted turn settings differ from selection")
    starts, ends = {}, {}
    for event in events:
        if event.get("type") not in {"item.started", "item.completed"}:
            continue
        item = event.get("item", {})
        if item.get("type") != "command_execution":
            continue
        ident = item.get("id")
        target = starts if event["type"] == "item.started" else ends
        if not isinstance(ident, str) or ident in target:
            raise ValueError("command identity absent or repeated")
        target[ident] = item
    if not starts or starts.keys() != ends.keys():
        raise ValueError("command request/result pair incomplete")
    replay = []
    extras = 0
    for ident, start in starts.items():
        end = ends[ident]
        if start.get("command") != end.get("command") or not isinstance(end.get("aggregated_output"), str):
            raise ValueError("command request/result differs")
        if shell_argv(start["command"]) == packet["replay_argv"]:
            replay.append(end)
        else:
            # The selected read-only sandbox bounds effects. Additional fully
            # captured commands are secondary observations, not an input schema.
            extras += 1
    replay_end = exactly_one(replay, "selected replay command")
    receipt = strict_value(replay_end["aggregated_output"].encode())
    decision = receipt.get("decision")
    if (receipt.get("authorizes_landing") is not False or not isinstance(decision, dict)
            or decision.get("decision") not in {"ADMIT_IMPROVEMENT", "ADMIT_NONREGRESSION", "REJECT"}
            or replay_end.get("exit_code") != (1 if decision["decision"] == "REJECT" else 0)):
        raise ValueError("replay command result incomplete")
    return {"id": packet["id"], "arm": packet["arm"], "case": packet["case"],
            "thread_id": thread, "decision": final["decision"],
            "next_owner": final["next_owner"], "replay_decision": decision["decision"],
            "replay_next": decision.get("next"),
            "extra_command_count": extras}


def inspect_selected_comparison(value, root):
    """Schema 2 succeeds only from selected bytes and six complete raw captures."""
    if value.get("issue") != {"repository": "ed3c/soodles", "number": 157}:
        return refusal("issue", "comparison does not belong to this atom", "INVALID")
    if value.get("authorizes_landing") is not False:
        return refusal("authorizes_landing", "comparison cannot grant authority", "INVALID")
    if value.get("status") != "COMPLETED" or root is None:
        return refusal("status", "selected raw comparison is not complete")
    capture_scope = value.get("capture_scope", "private_raw")
    if capture_scope not in {"private_raw", "public_projection"}:
        return refusal("capture_scope", "unsupported comparison capture scope", "INVALID")
    try:
        field = "base64" if capture_scope == "public_projection" else "path"
        if (not isinstance(value.get("selection"), dict)
                or set(value["selection"]) != {field, "sha256"}
                or not isinstance(value.get("observer_report"), dict)
                or set(value["observer_report"]) != {field, "sha256"}):
            raise ValueError("selection/report representation differs from capture scope")
        selected = strict_value(raw_file(root, value.get("selection")))
        if (not isinstance(selected, dict) or selected.get("issue") != "ed3c/soodles#157"
                or selected.get("carrier") != "Local Codex CLI"
                or selected.get("status") != "SELECTED" or not re.fullmatch(r"[0-9a-f]{64}", selected.get("observer_sha256", ""))):
            raise ValueError("external selection identity incomplete")
        common = selected["common"]
        packets = selected["packets"]
        if (not isinstance(packets, list) or len(packets) != 6
                or {(p.get("arm"), p.get("case")) for p in packets} != {(a, c) for a in ARMS for c in CASES}
                or len({p.get("id") for p in packets}) != 6):
            raise ValueError("six selected arm/case packets absent")
        if (not re.fullmatch(r"[0-9a-f]{40}", common.get("baseline_ref", ""))
                or not re.fullmatch(r"[0-9a-f]{40}", common.get("treatment_ref", ""))
                or any(p.get("source_ref") != common[p["arm"] + "_ref"] for p in packets)):
            raise ValueError("selected source ref differs across run assignment")
        runs = value.get("fresh_runs")
        if (not isinstance(runs, list) or len(runs) != 6
                or {r.get("id") for r in runs if isinstance(r, dict)} != {p["id"] for p in packets}):
            raise ValueError("six fresh run captures absent")
        by_id = {r["id"]: r for r in runs}
        observations = [inspect_raw_run(by_id[p["id"]], p, common, root, capture_scope) for p in packets]
        if len({r["thread_id"] for r in observations}) != 6:
            raise ValueError("six fresh thread identities are not distinct")
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError,
            UnicodeError, RecursionError) as error:
        return refusal("raw_capture", str(error))
    by_case = {(r["arm"], r["case"]): r for r in observations}
    mismatch = {arm: by_case[(arm, "mismatched_case_exposure")] for arm in ARMS}
    unsupported = {arm: int(mismatch[arm]["decision"].startswith("ADMIT_")) for arm in ARMS}
    decisions = {r["id"]: {"decision": r["decision"],
                            "replay_decision": r["replay_decision"]} for r in observations}
    try:
        observer_report = strict_value(raw_file(root, value.get("observer_report")))
        classification = observer_report.get("classification")
        controls_failed = observer_report.get("controls_failed")
        if (observer_report.get("issue") != "ed3c/soodles#157"
                or observer_report.get("selection_sha256") != value["selection"]["sha256"]
                or observer_report.get("observer_sha256") != selected["observer_sha256"]
                or observer_report.get("authorizes_landing") is not False
                or observer_report.get("evidence_validity") != "VALID"
                or classification not in {"FAIL", "BOUNDED_IMPROVEMENT", "SCOPED_NONREGRESSION"}
                or observer_report.get("primary_unsupported_admission") != unsupported
                or observer_report.get("decisions") != decisions
                or not isinstance(controls_failed, list)
                or any(not isinstance(item, str) or not item for item in controls_failed)):
            raise ValueError("selected external observer report differs from raw decisions")
        if capture_scope == "public_projection" and (
                not re.fullmatch(r"[0-9a-f]{64}", selected.get("external_selection_sha256", ""))
                or not re.fullmatch(r"[0-9a-f]{64}", observer_report.get("external_report_sha256", ""))
                or observer_report.get("private_rollout_sha256_by_run") != {
                    run["id"]: run["private_rollout_sha256"] for run in value["fresh_runs"]}):
            raise ValueError("private raw/readback binding absent from public projection")
        if classification == "BOUNDED_IMPROVEMENT" and unsupported != {"baseline": 1, "treatment": 0}:
            raise ValueError("observer improvement classification contradicts primary outcome")
        if classification == "SCOPED_NONREGRESSION" and unsupported != {"baseline": 0, "treatment": 0}:
            raise ValueError("observer nonregression classification contradicts primary outcome")
        if classification != "FAIL" and (controls_failed or any(
                by_case[(arm, "matched_legal_improvement")]["decision"] != "ADMIT_IMPROVEMENT"
                or by_case[(arm, "missing_required_observation")]["decision"] != "REJECT"
                for arm in ARMS)):
            raise ValueError("observer pass contradicts required decision controls")
        if classification != "FAIL" and by_case[("treatment", "mismatched_case_exposure")]["replay_next"] != {
                "kind": "input", "owner": "supervisor", "required": ["matched_case_exposure"]}:
            raise ValueError("observer pass contradicts typed case-exposure next")
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OSError,
            UnicodeError, RecursionError) as error:
        return refusal("observer_report", str(error))
    return {"schema": 2, "owner": "pclass.consumer_evidence",
            "issue": {"repository": "ed3c/soodles", "number": 157},
            "scope": "bounded Local Codex CLI+P combined six-run comparison; public rollout is a field projection and original provenance requires external supervisor readback",
            "evidence_validity": "VALID",
            "behavior": {"classification": classification,
                         "primary_unsupported_admission": unsupported,
                         "controls_failed": controls_failed,
                         "extra_command_count": {r["id"]: r["extra_command_count"] for r in observations},
                         "operation_review": "raw command texts remain available to the external supervisor; hidden effects are outside this gate"},
            "terminal_ready": classification != "FAIL", "authorizes_landing": False,
            "next": {"kind": "readback" if classification != "FAIL" else "input",
                     "owner": "supervisor", "required": ["exact_head_acceptance"] if classification != "FAIL" else ["behavior_regression"]}}


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
    return {**inspect_comparison(value, path.parent), "evidence_sha256": digest}


def main(argv):
    if len(argv) != 3:
        result = refusal("arguments", "usage: consumer_gate.py COMPARISON.json EXPECTED_SHA256",
                         "INVALID", "selected_consumer_evidence")
        code = 2
    else:
        result = inspect_file(Path(argv[1]), argv[2])
        code = 0 if result["terminal_ready"] else 2 if result["evidence_validity"] == "INVALID" else 1
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
