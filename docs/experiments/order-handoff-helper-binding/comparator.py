"""Matched black-box discriminator for external resume/helper binding."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def execute(label, out, resume_path, source, marker):
    stdout_path = out / f"{label}.stdout.bin"
    stderr_path = out / f"{label}.stderr.bin"
    argv = [sys.executable, "-B", str(resume_path), str(out / "absent-noodle"), str(source)]
    env = dict(os.environ, SOODLES_PLANTED_HELPER_MARKER=str(marker))
    started = time.monotonic()
    result = subprocess.run(argv, cwd=out, env=env, capture_output=True)
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    return {
        "argv": argv,
        "cwd": str(out),
        "exit_status": result.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "stdout": str(stdout_path),
        "stdout_sha256": sha(result.stdout),
        "stderr": str(stderr_path),
        "stderr_sha256": sha(result.stderr),
        "stderr_text": result.stderr.decode(errors="replace"),
        "marker_present": marker.exists(),
        "marker_bytes": marker.read_text() if marker.exists() else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root")
    parser.add_argument("expected_head")
    parser.add_argument("output")
    args = parser.parse_args()
    root = Path(args.source_root).resolve()
    out = Path(args.output).resolve()
    out.mkdir(exist_ok=False)
    before = git(root, "status", "--porcelain")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    tree = git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    assert head == args.expected_head and not before
    resume = (root / "resume_oracle.py").read_bytes()
    helper = (root / "handoff_oracle.py").read_bytes()

    external = out / "external"
    matching = out / "matching-source"
    mismatched = out / "mismatched-source"
    for path in (external, matching, mismatched):
        path.mkdir()
    resume_path = external / "resume_oracle.py"
    resume_path.write_bytes(resume)
    (external / "handoff_oracle.py").write_bytes(helper)
    (matching / "handoff_oracle.py").write_bytes(helper)
    planted = b'''import os\nfrom pathlib import Path\nmarker = Path(os.environ["SOODLES_PLANTED_HELPER_MARKER"])\nmarker.write_text("candidate helper executed\\n")\nraise RuntimeError("candidate helper executed")\n'''
    assert sha(planted) != sha(helper)
    (mismatched / "handoff_oracle.py").write_bytes(planted)

    matching_marker = out / "matching.marker"
    mismatched_marker = out / "mismatched.marker"
    matching_result = execute("matching", out, resume_path, matching, matching_marker)
    mismatch_result = execute("mismatched", out, resume_path, mismatched, mismatched_marker)
    matching_ok = (
        matching_result["exit_status"] != 0
        and not matching_result["marker_present"]
        and "No module named 'issue_execution'" in matching_result["stderr_text"]
    )
    mismatch_executed = (
        mismatch_result["exit_status"] != 0
        and mismatch_result["marker_bytes"] == "candidate helper executed\n"
        and "candidate helper executed" in mismatch_result["stderr_text"]
    )
    mismatch_safe = (
        mismatch_result["exit_status"] != 0
        and not mismatch_result["marker_present"]
        and "No module named 'issue_execution'" in mismatch_result["stderr_text"]
    )
    after = git(root, "status", "--porcelain")
    stable = before == after == b"" and git(root, "rev-parse", "HEAD").decode().strip() == head
    classification = (
        "OBSERVED_BARRIER" if stable and matching_ok and mismatch_executed
        else "NO_OBSERVED_BARRIER" if stable and matching_ok and mismatch_safe
        else "INCONCLUSIVE"
    )
    result = {
        "schema": 1,
        "classification": classification,
        "barrier": "candidate transitive helper executed before external identity binding" if mismatch_executed else None,
        "source": {"root": str(root), "head": head, "tree": tree,
                   "status_before": before.decode(), "status_after": after.decode()},
        "inputs": {"resume_oracle_sha256": sha(resume), "handoff_oracle_sha256": sha(helper),
                   "planted_helper_sha256": sha(planted)},
        "sample_count": {"matching": 1, "planted_negative": 1},
        "matching": matching_result,
        "planted_negative": mismatch_result,
        "checks": {"source_stable": stable, "matching_ok": matching_ok,
                   "mismatch_executed": mismatch_executed, "mismatch_safe": mismatch_safe},
        "external_operations": [],
        "cleanup": {"source_unchanged": stable, "disposable_run_retained": True},
        "authorizes_landing": False,
        "unknowns": ["canonical Linux behavior", "fresh model behavior", "provider behavior"],
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classification": classification, **result["checks"]}))
    if classification == "INCONCLUSIVE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
