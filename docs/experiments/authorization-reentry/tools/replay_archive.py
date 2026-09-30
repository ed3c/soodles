#!/usr/bin/env python3
"""Replay one sealed archive with the fixed external oracle; no subject execution."""
import hashlib
import json
import copy
from pathlib import Path
import subprocess
import sys

ORACLE_SHA256 = "c371b70d81f2cfe3593c1de076a9d15fa65c6c7bb70762c39706580d9794e1d7"
ARCHIVER_SHA256 = "da3287c77f10c92c3800f30aede69e9148636050a8f83a2c4ce3cfe41ff863ac"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    if len(sys.argv) != 5:
        raise ValueError("usage: replay_archive.py ARCHIVE INVENTORY_SHA256 ORACLE FRESH_RECEIPTS")
    archive, expected, oracle, output = Path(sys.argv[1]).absolute(), sys.argv[2], Path(sys.argv[3]).absolute(), Path(sys.argv[4]).absolute()
    helper = Path(__file__).with_name("archive_case.py")
    if sha(helper) != ARCHIVER_SHA256 or sha(oracle) != ORACLE_SHA256:
        raise ValueError("fixed archiver/oracle source pin mismatch")
    if sha(oracle.parent / "capture_decoder.py") != "701ada7eb3f22b4a7639df423573f1fb298c12620e8ff8ec1f8f56b04d38f8fd":
        raise ValueError("fixed capture decoder changed")
    from archive_case import plain, inventory
    for path in (archive, oracle, output.parent):
        plain(path)
    if output == archive or archive in output.parents:
        raise ValueError("receipts must be outside the immutable archive")
    if sha(archive / "inventory.json") != expected:
        raise ValueError("inventory pin mismatch")
    manifest = json.loads((archive / "inventory.json").read_text())
    if inventory(archive) != manifest:
        raise ValueError("archive membership/bytes mismatch before replay")
    descriptor = json.loads((archive / "descriptor.json").read_text())
    original = json.loads((archive / "descriptor.original.json").read_text())
    identity = {k: v for k, v in descriptor.items() if k not in ("captured_root", "archived_root")}
    expected_identity = copy.deepcopy(original)
    expected_identity["drive"]["path"] = str(Path(descriptor["captured_root"]) / "control/drive.py")
    if identity != expected_identity or descriptor["captured_root"] != json.loads((archive / "case.json").read_text())["run_root"]:
        raise ValueError("archive descriptor differs beyond relocation roots")
    previous_root = descriptor["archived_root"]
    descriptor["archived_root"] = str(archive / "run")
    output.mkdir()  # Fresh only; neither archive nor prior receipts are updated.
    relocated = output / "descriptor.json"
    write(relocated, descriptor)
    bootstrap = "import runpy,sys; sys.path.insert(0,sys.argv[1]); sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name='__main__')"
    argv = [sys.executable, "-I", "-B", "-c", bootstrap, str(oracle.parent), str(oracle), str(relocated), sha(relocated)]
    result = subprocess.run(argv, capture_output=True, timeout=60)
    (output / "stdout.json").write_bytes(result.stdout)
    (output / "stderr.bin").write_bytes(result.stderr)
    try:
        observed = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        observed = None
    recorded = json.loads((archive / "result.json").read_text())
    unchanged = inventory(archive) == manifest and sha(archive / "inventory.json") == expected
    equal = observed == recorded
    expected_exit = 2 if recorded["evidence_validity"] != "VALID" else (0 if recorded["behavior"]["classification"] == "PASS" else 1)
    receipt = {"scope": "sealed evidence replay only; no fresh model/subject execution", "authorizes_landing": False,
               "archive": str(archive), "inventory_sha256": expected, "oracle_sha256": ORACLE_SHA256,
               "archiver_sha256": ARCHIVER_SHA256, "replayer_sha256": sha(Path(__file__)),
               "original_descriptor_sha256": sha(archive / "descriptor.json"),
               "replay_descriptor_sha256": sha(relocated), "previous_archived_root": previous_root,
               "actual_archived_root": descriptor["archived_root"], "captured_identity_unchanged": True,
               "argv": argv, "exit": result.returncode, "expected_exit": expected_exit,
               "stdout_sha256": sha(output / "stdout.json"), "stderr_sha256": sha(output / "stderr.bin"),
               "archive_integrity_before": True, "archive_integrity_after": unchanged,
               "recorded_result_sha256": sha(archive / "result.json"), "result_json_equal": equal}
    write(output / "receipt.json", receipt)
    print(json.dumps({"receipt": str(output / "receipt.json"), "result_json_equal": equal, "archive_unchanged": unchanged}))
    return 0 if equal and unchanged and result.returncode == expected_exit else 1


if __name__ == "__main__":
    raise SystemExit(main())
