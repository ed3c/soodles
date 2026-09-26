#!/usr/bin/env python3
"""External disposable Noodle first-checkpoint observation; no model provider."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


EXPECTED_NOODLE_SHA256 = "965cfd6f985e207551d0664e728ae9fae10ae0cc8cd2885a816415823d9d103d"
EXPECTED_SOURCE_HEAD = "00a5909941a632537dc6992b5354cd37614ea4a8"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--noodle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    noodle = args.noodle.resolve()
    output = args.output.resolve()
    if output.exists() or digest(noodle) != EXPECTED_NOODLE_SHA256:
        raise SystemExit("non-fresh output or Noodle digest mismatch")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if head != EXPECTED_SOURCE_HEAD:
        raise SystemExit("source head mismatch")
    output.mkdir(parents=True)
    root = output / "fixture"
    root.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
    (root / "README.md").write_text("disposable Noodle bootstrap fixture\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid",
                    "commit", "-m", "Create disposable fixture"], cwd=root, check=True, capture_output=True)
    for name in ("execute", "schedule"):
        shutil.copytree(source / ".agents/skills" / name, root / ".agents/skills" / name)
    provider = root / "provider"
    provider.mkdir()
    child = provider / "codex"
    child.write_text("#!/bin/sh\necho invoked >> " + str(root / "provider.log") + "\nexit 1\n")
    child.chmod(0o755)
    backlog = root / "backlog"
    backlog.write_text("#!/bin/sh\nif [ \"$1\" = sync ]; then echo "
                       "'{\"id\":\"probe\",\"title\":\"probe\",\"status\":\"open\",\"plan\":\"probe\"}'; fi\n")
    backlog.chmod(0o755)
    (root / ".noodle.toml").write_text(
        'mode = "supervised"\n[server]\nenabled = false\n[concurrency]\nmax_concurrency = 1\n'
        '[routing.defaults]\nprovider = "codex"\nmodel = "probe"\n'
        f'[skills]\npaths = ["{root}/.agents/skills"]\n'
        f'[agents.codex]\npath = "{provider}"\nrequire_typed_outcome = true\n'
        f'[adapters.backlog.scripts]\nsync = "{backlog}"\nadd = "{backlog}"\n'
        f'edit = "{backlog}"\ndone = "{backlog}"\n')
    argv = [str(noodle), "--project-dir", str(root), "start", "--once"]
    (output / "request.json").write_text(json.dumps({"argv": argv, "cwd": str(root),
                                                      "source_head": head,
                                                      "noodle_sha256": digest(noodle)}, indent=2) + "\n")
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=30,
                                env={**os.environ, "NOODLE_NO_BROWSER": "1"})
        exit_code = result.returncode
        (output / "stdout.txt").write_text(result.stdout)
        (output / "stderr.txt").write_text(result.stderr)
    except subprocess.TimeoutExpired as error:
        exit_code = None
        (output / "stdout.txt").write_bytes(error.stdout or b"")
        (output / "stderr.txt").write_bytes(error.stderr or b"")
    snapshot = root / ".noodle/state.snapshot.json"
    observed = json.loads(snapshot.read_text()) if snapshot.is_file() else None
    receipt = {
        "exit_code": exit_code,
        "snapshot_sha256": digest(snapshot) if observed is not None else None,
        "orders": list(observed["state"]["orders"]) if observed is not None else None,
        "effect_ledger_count": len(observed["effect_ledger"]) if observed is not None else None,
        "mode": observed["state"].get("mode") if observed is not None else None,
        "model_child_invoked": (root / "provider.log").exists(),
        "authorizes_landing": False,
    }
    receipt["classification"] = "PASS" if (exit_code == 0 and receipt["orders"] == []
        and receipt["effect_ledger_count"] == 0 and receipt["mode"] == "supervised"
        and not receipt["model_child_invoked"]) else "FAIL"
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    return 0 if receipt["classification"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
