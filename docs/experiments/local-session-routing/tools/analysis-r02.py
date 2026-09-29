#!/usr/bin/env python3
"""Aggregate pinned receipts while retaining baseline B/C failures as history."""

import hashlib
import json
from pathlib import Path
from statistics import median
import sys


class EvidenceError(Exception):
    def __init__(self, code, validity="INVALID"):
        self.code, self.validity = code, validity
        super().__init__(code)


def check(condition, code):
    if not condition:
        raise EvidenceError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pinned_bytes(pin, label):
    check(isinstance(pin, dict) and set(pin) == {"path", "sha256"}, label + ":pin_shape")
    check(isinstance(pin["path"], str) and isinstance(pin["sha256"], str), label + ":pin_types")
    try:
        data = Path(pin["path"]).read_bytes()
    except FileNotFoundError:
        raise EvidenceError(label + ":missing", "INCONCLUSIVE") from None
    check(sha(data) == pin["sha256"], label + ":digest_mismatch")
    return data


def pinned_json(pin, label):
    try:
        value = json.loads(pinned_bytes(pin, label))
    except (ValueError, UnicodeError):
        raise EvidenceError(label + ":invalid_json") from None
    check(isinstance(value, dict), label + ":not_object")
    return value


def output(validity, behavior=None, cost=None, adopt=False, problems=(),
           keep_candidate=False, confirmation_pending=False):
    return {"evidence_validity": validity, "behavior": behavior, "cost": cost,
            "keep_candidate": keep_candidate, "confirmation_pending": confirmation_pending,
            "adopt": adopt, "problems": list(problems), "authorizes_landing": False}


def aggregate(manifest, phase="final"):
    check(phase in ("selection", "final"), "analysis_phase")
    splits = ("selection",) if phase == "selection" else ("selection", "confirmation")
    check(isinstance(manifest, dict) and set(manifest) == {"schema", "pins", "runs"}, "manifest_shape")
    check(type(manifest["schema"]) is int and manifest["schema"] == 1, "manifest_schema")
    pins = manifest["pins"]
    check(isinstance(pins, dict) and set(pins) == {"protocol", "oracle", "harness"}, "pins_shape")
    for name in ("protocol", "oracle", "harness"):
        pinned_bytes(pins[name], name)
    runs = manifest["runs"]
    check(isinstance(runs, list), "runs_shape")
    seen_results, group_owner, buckets = set(), {}, {}
    for index, run in enumerate(runs):
        label = "run_" + str(index)
        check(isinstance(run, dict) and set(run) == {"split", "group", "arm", "stratum", "result"}, label + ":shape")
        split, group, arm, stratum = (run[k] for k in ("split", "group", "arm", "stratum"))
        check(split in splits, label + ":split")
        check(arm in ("baseline", "candidate"), label + ":arm")
        check(stratum in ("A", "B", "C"), label + ":stratum")
        check(isinstance(group, str) and group, label + ":group")
        owner = group_owner.setdefault(group, (split, stratum))
        check(owner[0] == split, "cross_split_group_collision:" + group)
        check(owner[1] == stratum, "cross_stratum_group_collision:" + group)
        result_path = run["result"].get("path") if isinstance(run["result"], dict) else None
        check(result_path not in seen_results, label + ":duplicate_result")
        seen_results.add(result_path)
        buckets.setdefault((split, stratum, arm), []).append(run)
    expected = {"A": 3, "B": 1, "C": 1}
    for split in splits:
        for stratum, count in expected.items():
            baseline = buckets.get((split, stratum, "baseline"), [])
            candidate = buckets.get((split, stratum, "candidate"), [])
            check(len(baseline) == count and len(candidate) == count,
                  f"run_count:{split}:{stratum}")
            groups = {r["group"] for r in baseline + candidate}
            check(len(groups) == 1, f"unmatched_exposure:{split}:{stratum}")

    unusable, blocking_failures, historical_failures, costs = [], [], [], {}
    for run in runs:
        key = ":".join(run[k] for k in ("split", "group", "arm", "stratum"))
        result = pinned_json(run["result"], "result:" + key)
        check(result.get("authorizes_landing") is False, "authorizing_result:" + key)
        validity = result.get("evidence_validity")
        check(validity in ("VALID", "INVALID", "INCONCLUSIVE"), "result_validity:" + key)
        if validity != "VALID":
            check(result.get("behavior") is None and result.get("cost") is None,
                  "unusable_result_has_measurement:" + key)
            unusable.append((validity, key))
            continue
        behavior = result.get("behavior")
        check(isinstance(behavior, dict) and behavior.get("classification") in ("PASS", "FAIL"),
              "behavior_shape:" + key)
        if behavior["classification"] != "PASS":
            if run["arm"] == "baseline" and run["stratum"] in ("B", "C"):
                historical_failures.append(key)
            else:
                blocking_failures.append(key)
            continue
        if run["stratum"] == "A":
            check(result.get("cost_comparison_eligible") is True, "ineligible_pass:" + key)
            commands = result.get("cost", {}).get("completed_commands")
            check(type(commands) is int and commands >= 0, "completed_commands:" + key)
            cost_key = (run["split"], run["arm"], run["stratum"], run["group"])
            costs[cost_key] = costs.get(cost_key, []) + [commands]
    if unusable:
        validity = "INVALID" if any(v == "INVALID" for v, _ in unusable) else "INCONCLUSIVE"
        return output(validity, problems=[v + ":" + key for v, key in unusable],
                      confirmation_pending=phase == "selection")
    if blocking_failures:
        behavior = {"comparison_gate": "FAIL",
                    "blocking_failures": sorted(blocking_failures),
                    "historical_failures": sorted(historical_failures)}
        return output("VALID", behavior, problems=["behavior_gate_failed"],
                      confirmation_pending=phase == "selection")

    comparisons = {}
    for split in splits:
        base = sorted(v for (s, arm, st, _), values in costs.items()
                      if (s, arm, st) == (split, "baseline", "A") for v in values)
        candidate = sorted(v for (s, arm, st, _), values in costs.items()
                           if (s, arm, st) == (split, "candidate", "A") for v in values)
        base_median, candidate_median = median(base), median(candidate)
        lower = sum(value < base_median for value in candidate)
        reduction = base_median > 0 and candidate_median * 5 <= base_median * 4
        comparisons[split] = {
            "baseline_A_completed_commands": base,
            "candidate_A_completed_commands": candidate,
            "baseline_median": base_median, "candidate_median": candidate_median,
            "median_reduction_percent": None if base_median == 0 else
                round((base_median - candidate_median) * 100 / base_median, 6),
            "candidate_runs_below_baseline_median": lower,
            "meets_adoption_cost": reduction and lower >= 2,
            "candidate_B_C_behavior_gates": "PASS",
        }
    keep = comparisons["selection"]["meets_adoption_cost"]
    adopt = phase == "final" and keep and comparisons["confirmation"]["meets_adoption_cost"]
    behavior = {"comparison_gate": "PASS", "candidate_all_strata": "PASS",
                "baseline_A": "PASS",
                "baseline_B_C": "FAIL" if historical_failures else "PASS",
                "historical_failures": sorted(historical_failures)}
    return output("VALID", behavior, comparisons, adopt,
                  keep_candidate=keep, confirmation_pending=phase == "selection")


def main(argv):
    args = argv[1:]
    phase = "selection" if args[:1] == ["--selection"] else "final"
    if phase == "selection":
        args = args[1:]
    try:
        check(len(args) == 2, "usage:analysis-r02.py [--selection] MANIFEST EXPECTED_SHA256")
        manifest = pinned_json({"path": args[0], "sha256": args[1]}, "manifest")
        result = aggregate(manifest, phase)
    except (EvidenceError, OSError, KeyError, TypeError) as error:
        if isinstance(error, EvidenceError):
            result = output(error.validity, problems=[error.code],
                            confirmation_pending=phase == "selection")
        else:
            result = output("INVALID", problems=[type(error).__name__],
                            confirmation_pending=phase == "selection")
    print(json.dumps(result, indent=2, sort_keys=True))
    accepted = result["keep_candidate"] if phase == "selection" else result["adopt"]
    return 2 if result["evidence_validity"] != "VALID" else (0 if accepted else 1)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
