"""Finite repair decisions inside the atom's existing checkpoint and locks.

Only owning call sites select signals. Data cannot name executable code, shell
commands or predicates. Legacy/unlinked checkpoints never acquire zero budgets.
"""
import copy
import hashlib
import json
import math
import re
import time


POLICY_PATH = "policy/repair-policy.json"
LIMITS = {"readback": 1, "rebuild": 1, "model": 1, "verification": 1,
          "actions": 4, "seconds": 60}
PROTECTED = ["subject", "evidence", "verifier", "policy", "limits", "unknown_writes"]
# Each decision has one registered producer, consumer and necessary P root.
DECISIONS = {
    "missing_input": ("external_owner", "issue_atom._run_owned", "stop", "issue-atom"),
    "identity_conflict": ("identity_validator", "issue_atom._run_owned", "stop", "issue-atom"),
    "stale_pr": ("candidate_publication.publish", "issue_atom.refresh_publication", "readback", "candidate"),
    "invalid_entry": ("system_context.select", "system_context.select", "stop", "readback"),
    "unknown_effect": ("effect_owner", "issue_atom._run_owned", "stop", "readback"),
    "failed_process": ("process_owner", "issue_atom._run_owned", "model", "issue-atom"),
    "cleanup_residue": ("cleanup_owner", "issue_atom.finish_host", "stop", "issue-atom"),
    "no_legal_next": ("landing_owner", "issue_atom._run_owned", "stop", "readback"),
    "missing_projection": ("atom_checkpoint", "issue_atom.restore_publication", "rebuild", "candidate"),
    "unknown_signal": ("unregistered_owner", "issue_atom._run_owned", "stop", "issue-atom"),
}
FACTS = {
    "missing_input": "named owner prerequisite",
    "identity_conflict": "unchanged admitted identity",
    "stale_pr": "exact PR head after confirmed branch readback",
    "invalid_entry": "registered entry and supported options",
    "unknown_effect": "current effect-owner outcome; never reoffer",
    "failed_process": "bounded_patch_capability_required",
    "cleanup_residue": "owner-confirmed cleanup",
    "no_legal_next": "owner transition for satisfied prerequisites",
    "missing_projection": "publication projection from unchanged validated source",
    "unknown_signal": "registered trusted observation adapter",
}


class RepairRefusal(ValueError):
    def __init__(self, field, value):
        self.invalid = {"field": "repair." + field, "value": value}
        super().__init__(f"invalid repair.{field}={value!r}")


def require(condition, field, value):
    if not condition:
        raise RepairRefusal(field, value)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_key", key)
        result[key] = value
    return result


def load(raw):
    try:
        policy = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, RecursionError) as error:
        raise RepairRefusal("policy_json", str(error)) from error
    require(isinstance(policy, dict) and set(policy) == {
        "schema", "limits", "protected", "actions", "signals"}, "policy_fields", policy)
    require(type(policy["schema"]) is int and policy["schema"] == 1, "schema", policy["schema"])
    require(policy["limits"] == LIMITS and all(type(v) is int for v in policy["limits"].values()),
            "limits", policy["limits"])
    require(policy["protected"] == PROTECTED, "protected", policy["protected"])
    require(policy["actions"] == ["stop", "readback", "rebuild", "model"], "actions", policy["actions"])
    require(isinstance(policy["signals"], dict) and set(policy["signals"]) == set(DECISIONS),
            "signals", policy["signals"])
    for signal, (producer, consumer, action, context) in DECISIONS.items():
        expected = {"producer": producer, "consumer": consumer, "action": action,
                    "requires": ["contracts/system-v1/" + context + ".md"],
                    "missing_fact": FACTS[signal], "wake": "material_owner_readback"}
        require(policy["signals"][signal] == expected, "signal." + signal, policy["signals"][signal])
    return policy


def new_history(lineage, binding, policy, now=None, context=None):
    now = time.time() if now is None else now
    return {"schema": 1, "lineage": lineage, "binding": binding,
            "policy": digest(policy), "limits": dict(LIMITS),
            "started": None, "last_time": now, "used": {key: 0 for key in LIMITS if key != "seconds"},
            "history": [], "context": context or {}}


class Controller:
    def __init__(self, state, policy, binding, save, *, clock=time.time, invariants=lambda: None, context=None, disabled=None):
        self.state, self.policy, self.binding, self.save, self.clock = state, policy, binding, save, clock
        self.invariants = invariants
        self.context = context or {}
        self.disabled = disabled

    def check(self):
        require(self.disabled is None, "lineage", self.disabled)
        record = self.state.get("repair")
        require(isinstance(record, dict), "lineage", "trusted repair history unavailable")
        require(set(record) == {"schema", "lineage", "binding", "policy", "limits", "started",
                                "last_time", "used", "history", "context"}, "history_fields", record)
        require(type(record["schema"]) is int and record["schema"] == 1
                and isinstance(record["lineage"], str)
                and re.fullmatch(r"[0-9a-f]{64}", record["lineage"]), "lineage", record["lineage"])
        require(record["binding"] == self.binding and record["policy"] == digest(self.policy)
                and record["limits"] == LIMITS, "invariants", "changed")
        require(record["context"] == self.context, "context", "changed compiled closure")
        used, history = record["used"], record["history"]
        require(isinstance(used, dict) and set(used) == set(LIMITS) - {"seconds"}
                and all(type(n) is int and 0 <= n <= LIMITS[k] for k, n in used.items()),
                "counters", used)
        require(isinstance(history, list) and len(history) == used["actions"], "history", history)
        counts = {key: 0 for key in used}
        for entry in history:
            require(isinstance(entry, dict) and set(entry) == {"signal", "action", "status", "evidence"}
                    and entry["signal"] in DECISIONS
                    and entry["action"] == DECISIONS[entry["signal"]][2]
                    and entry["action"] in {"readback", "rebuild"}
                    and entry["status"] in {"intent", "confirmed", "failed"}, "history_entry", entry)
            counts[entry["action"]] += 1
            counts["actions"] += 1
        require(counts == used, "counters", "history mismatch")
        now = self.clock()
        require(all(type(n) in (int, float) and math.isfinite(n)
                    for n in (now, record["last_time"])) and now >= record["last_time"],
                "clock", "missing or reversed time")
        started = record["started"]
        require((not history and started is None) or
                (bool(history) and type(started) in (int, float) and math.isfinite(started)
                 and started <= record["last_time"]), "clock", "invalid start")
        return record, now

    def report(self, signal, *, stop=None):
        signal = signal if signal in DECISIONS else "unknown_signal"
        rule = self.policy["signals"][signal]
        try:
            record, now = self.check()
            remaining = {k: LIMITS[k] - record["used"][k] for k in record["used"]}
            remaining["seconds"] = max(0, LIMITS["seconds"] - (now - record["started"])) if record["started"] is not None else LIMITS["seconds"]
        except RepairRefusal as error:
            remaining, stop = None, error.invalid
        if signal == "failed_process":
            stop = "bounded_patch_capability_required"
        mode = ("defined_risk" if signal in {"stale_pr", "missing_projection", "no_legal_next"}
                else "offline_measurement" if signal == "unknown_signal" else "owner_continuation")
        return {"classification": signal, "mode": mode,
                "offline_request": "scoped_unknown_behavior_evidence" if mode == "offline_measurement" else None,
                "context": copy.deepcopy(self.context.get(signal)),
                **copy.deepcopy(rule), "remaining": remaining,
                "stop": stop or ("owner_input_required" if rule["action"] == "stop" else None),
                "model_invocations": 0, "authorizes_landing": False}

    def perform(self, signal, operation, confirm):
        record, now = self.check()
        action = self.policy["signals"][signal]["action"]
        require(action in {"readback", "rebuild"}, "capability", FACTS[signal])
        require(not any(item["signal"] == signal for item in record["history"]), "repeated_failure", signal)
        require(record["used"][action] < LIMITS[action]
                and record["used"]["actions"] < LIMITS["actions"], "budget", action)
        protected = self.invariants()
        if record["started"] is None:
            record["started"] = now
        require(now < record["started"] + LIMITS["seconds"], "deadline", "exhausted")
        record["last_time"] = now
        record["used"][action] += 1
        record["used"]["actions"] += 1
        intent = {"signal": signal, "action": action, "status": "intent", "evidence": None}
        record["history"].append(intent)
        self.save()  # unknown outcomes remain charged, including process death
        def remaining():
            current, observed = self.check()
            left = current["started"] + LIMITS["seconds"] - observed
            require(left > 0, "deadline", "exhausted")
            return left
        try:
            result = operation(remaining)
            remaining()
            require(self.invariants() == protected, "invariants", "independent evidence changed")
            require(confirm(result), "original_predicate", signal)
        except Exception as error:
            intent["status"] = "failed"
            intent["evidence"] = {"error": type(error).__name__, "invalid": getattr(error, "invalid", None)}
            self.save()
            raise
        intent["status"], intent["evidence"] = "confirmed", digest(result)
        record["last_time"] = self.clock()
        self.save()
        return result


# Exact typed fields from existing owners; arbitrary exception prose is unused.
ERROR_SIGNALS = {
    "github.issue.outcome": "unknown_effect", "github.branch.outcome": "unknown_effect",
    "github.pull.outcome": "unknown_effect", "amendment.intent": "unknown_effect",
    "publication.effect": "unknown_effect", "github.branch.readback": "unknown_effect",
    "github.pull.identity": "identity_conflict", "github.branch.head": "identity_conflict",
    "state.authorization": "identity_conflict", "envelope.digest": "identity_conflict",
    "noodle.claim.exit": "failed_process", "acceptance": "failed_process",
    "github.workflow.conclusion": "failed_process", "authorization.path": "missing_input",
    "provider_credential_profile.path": "missing_input", "noodle.claim": "missing_input",
    "noodle.snapshot": "missing_input", "noodle.config.digest": "identity_conflict",
    "noodle.stop.readback": "cleanup_residue", "noodle.stop.pid": "cleanup_residue",
    "noodle.stop.process_group": "cleanup_residue", "noodle.stop.owner": "cleanup_residue",
    "noodle.config.restore": "identity_conflict", "noodle.config.restored": "identity_conflict",
}


def observation(error):
    return ERROR_SIGNALS.get(getattr(error, "invalid", {}).get("field"), "unknown_signal")
