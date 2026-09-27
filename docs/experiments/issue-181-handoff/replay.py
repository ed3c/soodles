"""Replay frozen #181 receiver evidence; never launch an owner or authorize landing."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(root):
    root = Path(root).resolve()
    evidence = root / "docs/experiments/issue-181-handoff"
    manifest = json.loads((evidence / "manifest.json").read_bytes())
    for item in manifest["artifacts"]:
        path = (root / item["path"]).resolve()
        assert path.is_relative_to(root), "artifact escapes candidate"
        assert sha(path) == item["sha256"], item["path"]
    for item in manifest["instructions"]:
        assert sha(root / item["path"]) == item["treatment_sha256"], item["path"]
    selection = json.loads((evidence / "observer-v2-selection.json").read_bytes())
    assert sha(evidence / "protocol.json") == selection["protocol_sha256"]
    assert sha(evidence / "observe-v2.py") == selection["new_observer_sha256"]
    spec = importlib.util.spec_from_file_location("issue181_observer", evidence / "observe-v2.py")
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    controls = observer.controls()
    assert all(controls.values()), controls
    protocol = json.loads((evidence / "protocol.json").read_bytes())
    relocated = copy.deepcopy(protocol)
    results = {}
    for label in ("A", "B"):
        # Relocate storage only. Original source/argv/instruction identities remain bound.
        arm = evidence / "raw" / label
        assert sha(arm / "report.json") == selection["raw_report_sha256"][label]
        relocated["arms"][label]["evidence"] = str(arm)
        results[label] = observer.observe(relocated, label)
        frozen = json.loads((evidence / ("observer-v2-" + label + ".stdout.json")).read_bytes())
        assert results[label] == frozen, label + " replay changed"
    assert results["A"]["errors"] == ["wrong_continuation"], results["A"]["errors"]
    assert results["B"]["classification"] == "PASS", results["B"]["errors"]
    packet = json.loads((evidence / "cloud-handoff-01.json").read_bytes())
    for files in packet["cases"].values():
        for item in files.values():
            data = item["text"].encode("utf-8")
            assert len(data) == item["bytes"]
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
    return {"classification": "PASS", "case": "selected authorization unavailable",
            "baseline_continuation_missing": True, "treatment_continuation_preserved": True,
            "controls": controls, "consumer_launches": 2,
            "scope": "frozen consumer-recorded local pair and evidence integrity",
            "p_only_causal_effect": "NOT_ISOLATED", "runtime_handoff": "NOT_PROVEN_BY_REPLAY",
            "authorizes_landing": False}


if __name__ == "__main__":
    print(json.dumps(replay(sys.argv[1]), indent=2))
