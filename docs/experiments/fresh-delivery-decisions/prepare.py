#!/usr/bin/env python3
"""Generate labeled disposable owner fixtures and byte-pinned consumer inputs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import issue_admission
import landing


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def candidate(label):
    helper = module(ROOT / "docs/experiments/exact-head-candidate-binding/observer.py", "frozen_fixture_helper")
    with tempfile.TemporaryDirectory(prefix="decision-candidate-") as folder:
        root = Path(folder)
        helper.git(root, "init", "-b", "main")
        baseline, treatment = b"baseline policy\n", b"exact-byte policy\n"
        helper.write(root, helper.SUBJECT, baseline)
        base = helper.commit(root, "baseline fixture")
        artifacts = [(p, "fixture", (p + "\n").encode()) for p in helper.REQUIRED
                     if p not in (helper.SUBJECT, helper.MANIFEST)]
        helper.write(root, helper.SUBJECT, treatment + (b"tamper\n" if label == "B" else b""))
        for path, _, data in artifacts:
            if not (label == "A" and path == helper.NONCASE_RAW):
                helper.write(root, path, data)
        manifest = helper.evidence_manifest(1, baseline, treatment, artifacts)
        helper.write(root, helper.MANIFEST, (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
        head = helper.commit(root, "candidate fixture")
        contract = helper.contract(base, sha((helper.TASK + "\n").encode()),
                                   sha((helper.OBSERVER + "\n").encode()))
        readback = {"number": 1, "state": "open",
                    "url": "https://api.github.com/repos/ed3c/soodles/issues/1",
                    "html_url": "https://github.com/ed3c/soodles/issues/1",
                    "body": helper.issue_body(contract)}
        try:
            output = issue_admission.verify_candidate(root, base, head, readback)
        except issue_admission.AdmissionRefusal as error:
            output = {"owner": "candidate.verify", "status": "refused",
                      "invalid": error.invalid, "next": error.next,
                      "authorizes_landing": False}
        return {"head": head, "base": base, "tree": helper.git(root, "rev-parse", "HEAD^{tree}"),
                "input": readback, "output": output, "manifest": manifest}


def owner(current, merged):
    test = module(ROOT / "tests/test_landing.py", "frozen_landing_fixture").LandingTests()
    test.setUp()
    try:
        claim = test.claim
        claim.pop("control_root")
        claim.update(head=current["head"], tree=current["tree"], base_head=current["base"])
        snapshot = test.snapshot
        snapshot["pr"]["head"]["sha"] = claim["head"]
        snapshot["pr"]["base"]["sha"] = claim["base_head"]
        snapshot["run"]["head_sha"] = claim["head"]
        snapshot["commit"] = {"sha": claim["head"], "tree": {"sha": claim["tree"]}}
        snapshot["jobs"]["jobs"][0]["head_sha"] = claim["head"]
        snapshot["branch"]["commit"]["sha"] = claim["base_head"]
        trace = []

        def call(operation):
            args = (claim, snapshot, test.checkpoint) if operation == "start" else (test.checkpoint, snapshot)
            output = getattr(landing, operation)(*args)
            trace.append({"operation": "landing." + operation,
                          "snapshot": copy.deepcopy(snapshot), "output": output,
                          "checkpoint_after": json.loads(test.checkpoint.read_text())})
            return output

        call("start")
        output = call("advance")
        if merged:
            call("dispatch")
            snapshot["pr"].update(merged=True, state="closed", merged_at="2026-09-20T01:00:00Z", merge_commit_sha="d" * 40)
            snapshot["merge_commit"] = {"sha": "d" * 40, "tree": {"sha": claim["tree"]},
                                        "parents": [{"sha": claim["base_head"]}, {"sha": claim["head"]}]}
            call("advance")
            call("dispatch")
            snapshot["issue"].update(state="closed", state_reason="completed", closed_at="2026-09-20T01:01:00Z")
            snapshot["branch"]["commit"]["sha"] = "d" * 40
            output = call("advance")
        return output, {"claim": claim, "trace": trace, "transport_events": [],
                        "scope": "real owner function calls on synthetic provider data; no provider transport"}
    finally:
        test.doCleanups()


def main():
    destination = Path(sys.argv[1]).resolve()
    if destination.exists():
        raise SystemExit("refuse to overwrite generated inputs")
    destination.mkdir(parents=True)
    context = []
    paths = ["AGENTS.md", ".agents/skills/verify-soodles/SKILL.md",
             ".agents/skills/verify-soodles/features/supervised-delivery.md", "contracts/system-v1.md"]
    for path in paths:
        data = (ROOT / path).read_bytes()
        text = data.decode()
        if path == "contracts/system-v1.md":
            text = "## LANDING.SUPERVISED.001" + text.split("## LANDING.SUPERVISED.001", 1)[1].split("\n## ", 1)[0]
        context.append({"path": path, "source_sha256": sha(data), "loaded_sha256": sha(text.encode()), "text": text})
    write(destination / "context.json", {"source_provider_sha": "a2e46631b59b1f304391bfcd49615cdd9f6124e7", "documents": context})
    traces = {}
    for label in "ABCD":
        current = candidate(label)
        case = {"fixture": True, "case": label, "authorization": "Read and return the next handoff only; no effects.",
                "subject": {"repository": "ed3c/soodles", "issue": 1, "pr": 2,
                            "head": current["head"], "merged": label == "D", "state": "closed" if label == "D" else "open"},
                "candidate_output": current["output"],
                "owner_output": None,
                "discovered_at": "2026-09-20T02:00:00Z" if label == "D" else "2026-09-20T00:30:00Z",
                "discovery": "A required evidence artifact is absent." if label in "AD" else "Current candidate verification readback attached.",
                "available_inputs": "Issue identity, current candidate and owning readbacks, prior delivery status, supervisor authorization for the handoff are supplied."}
        traces[label] = {"candidate": current}
        if label in "CD":
            case["owner_output"], traces[label]["owner"] = owner(current, label == "D")
        if label == "D":
            case["subject"]["merged_at"] = "2026-09-20T01:00:00Z"
        write(destination / (label + ".json"), case)
    write(destination / "owner-traces.json", traces)
    print(json.dumps({"output": str(destination), "cases": list(traces), "authorizes_landing": False}))


if __name__ == "__main__":
    main()
