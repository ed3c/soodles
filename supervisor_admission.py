#!/usr/bin/env python3
"""Materialize one externally selected local Soodles admission capability.

The supervisor selects the fresh Issue readback, carrier, control root and new
external output directory. This module derives no task identity and performs no
Noodle/provider write. Runtime bytes are copied from committed Git objects, not
from the working tree.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from issue_admission import AdmissionRefusal, body_digest, parse_contract, require, validate_issue
from issue_execution import validate_carrier
from repository_binding import git_origins, issue_urls

REPOSITORY = "ed3c/soodles"
BUNDLE_PATHS = (
    "soodles.py",
    "issue_admission.py",
    "issue_execution.py",
    "github_reader.py",
    "repository_binding.py",
)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _read_json(path, field):
    path = Path(path).resolve()
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise AdmissionRefusal(field, str(error), "supervisor", "valid_supervisor_input") from error
    require(isinstance(value, dict), field, type(value).__name__,
            owner="supervisor", required="valid_supervisor_input")
    return value


def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "supervisor.git", result.stderr.strip(),
            owner="Git", required="exact_control_root_readback")
    return result.stdout.strip()


def _git_bytes(root, revision, path):
    result = subprocess.run(
        ["git", "--no-pager", "show", f"{revision}:{path}"],
        cwd=root, capture_output=True, timeout=30)
    require(result.returncode == 0, "supervisor.bundle_path", path,
            owner="Git", required="committed_supervisor_runtime")
    return result.stdout


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _launcher_text(control_root, envelope_sha256, manifest_sha256, interpreter):
    template = """#!{interpreter}
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CONTROL_ROOT = Path({control_root!r})
ENVELOPE_SHA256 = {envelope_sha256!r}
MANIFEST_SHA256 = {manifest_sha256!r}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def refuse(field, value):
    print(json.dumps({{
        "owner": "supervisor.launcher",
        "status": "refused",
        "invalid": {{"field": field, "value": value}},
        "next": {{"kind": "input", "owner": "supervisor",
                  "required": ["fresh_supervisor_admission"]}},
        "authorizes_landing": False
    }}, indent=2))
    return 64


def main():
    if sys.argv[1:] != ["automatic"]:
        return refuse("launcher.argv", sys.argv[1:])
    manifest_path = ROOT / "manifest.json"
    try:
        manifest_bytes = manifest_path.read_bytes()
        if digest(manifest_bytes) != MANIFEST_SHA256:
            return refuse("launcher.manifest_sha256", digest(manifest_bytes))
        manifest = json.loads(manifest_bytes)
        envelope = ROOT / "envelope.json"
        if digest(envelope.read_bytes()) != ENVELOPE_SHA256:
            return refuse("launcher.envelope_sha256", digest(envelope.read_bytes()))
        for entry in manifest["runtime"]:
            path = ROOT / entry["path"]
            observed = digest(path.read_bytes())
            if observed != entry["sha256"]:
                return refuse("launcher.runtime_sha256", entry["path"] + ":" + observed)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return refuse("launcher.bundle", type(error).__name__)

    sys.path.insert(0, str(ROOT / "runtime"))
    import issue_execution
    from issue_admission import AdmissionRefusal
    try:
        result = issue_execution.automatic(
            str(ROOT / "envelope.json"), ENVELOPE_SHA256, CONTROL_ROOT)
    except AdmissionRefusal as error:
        result = issue_execution.refusal_output(error, "automatic")
        print(json.dumps(result, indent=2))
        print(issue_execution.refusal_text(result), file=sys.stderr)
        return getattr(error, "exit_code", 1)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
    return template.format(
        interpreter=interpreter,
        control_root=str(control_root),
        envelope_sha256=envelope_sha256,
        manifest_sha256=manifest_sha256,
    )


def prepare(issue_readback, carrier, control_root, output, *, interpreter=None):
    """Create one immutable external bundle and return the only start continuation."""
    root = Path(control_root)
    require(root.is_absolute(), "supervisor.control_root", str(control_root),
            owner="supervisor", required="absolute_control_root")
    root = root.resolve()
    require(root.is_dir(), "supervisor.control_root", str(root),
            owner="supervisor", required="existing_control_root")

    output = Path(output)
    require(output.is_absolute(), "supervisor.output", str(output),
            owner="supervisor", required="absolute_external_output")
    output = output.resolve()
    require(not output.is_relative_to(root), "supervisor.output", str(output),
            owner="supervisor", required="external_output_outside_control_root")
    require(not output.exists(), "supervisor.output.exists", str(output),
            owner="supervisor", required="new_external_output")
    require(output.parent.is_dir(), "supervisor.output.parent", str(output.parent),
            owner="supervisor", required="existing_external_output_parent")

    require(isinstance(issue_readback, dict), "supervisor.issue_readback",
            type(issue_readback).__name__, owner="supervisor", required="fresh_issue_readback")
    number = issue_readback.get("number")
    require(type(number) is int and number > 0, "supervisor.issue.number", number,
            owner="GitHub", required="fresh_issue_readback")
    api_url, html_url = issue_urls(REPOSITORY, number)
    require(issue_readback.get("url") == api_url
            and issue_readback.get("html_url") == html_url,
            "supervisor.issue.identity",
            [issue_readback.get("url"), issue_readback.get("html_url")],
            owner="GitHub", required="fresh_issue_readback")

    body = issue_readback.get("body")
    contract = parse_contract(body)
    head = _git(root, "rev-parse", "HEAD")
    if contract.get("schema") == 3:
        require(head == contract["base_head"], "supervisor.control_root.head", head,
                owner="supervisor", required="fresh_issue_base_checkout")
    base_head = contract["base_head"] if contract.get("schema") == 3 else head
    origin = _git(root, "remote", "get-url", "origin")
    require(origin in git_origins(REPOSITORY), "supervisor.control_root.origin", origin,
            owner="Git", required="admitted_repository_identity")

    require(isinstance(carrier, dict), "supervisor.carrier", type(carrier).__name__,
            owner="supervisor", required="measured_local_carrier")
    validate_carrier({"execution": {"carrier": carrier}}, worker=True)

    envelope = {
        "schema": 1,
        "repository": REPOSITORY,
        "issue": number,
        "body_sha256": body_digest(body),
        "body_updated_at": issue_readback.get("updated_at"),
        "owner": contract["owner"],
        "write_paths": contract["write_paths"],
        "base_head": base_head,
        "execution": {
            "control_root": str(root),
            "worktree": f"soodles-{number}-0-execute",
            "order_id": f"soodles-{number}",
            "stage_index": 0,
            "carrier": carrier,
            "task": f"Execute externally admitted {REPOSITORY}#{number}.",
            "source_head": head,
        },
    }
    validate_issue(issue_readback, envelope)

    envelope_bytes = _canonical(envelope)
    envelope_digest = _sha256(envelope_bytes)
    runtime = []
    runtime_bytes = {}
    for path in BUNDLE_PATHS:
        data = _git_bytes(root, head, path)
        runtime_bytes[path] = data
        runtime.append({"path": "runtime/" + path, "sha256": _sha256(data)})

    manifest = {
        "schema": 1,
        "repository": REPOSITORY,
        "issue": number,
        "source_head": head,
        "envelope_sha256": envelope_digest,
        "runtime": runtime,
        "authorizes_landing": False,
    }
    manifest_bytes = _canonical(manifest)
    manifest_digest = _sha256(manifest_bytes)
    interpreter = str(Path(interpreter or sys.executable).resolve())
    require(Path(interpreter).is_absolute() and Path(interpreter).is_file()
            and os.access(interpreter, os.X_OK),
            "supervisor.interpreter", interpreter,
            owner="supervisor", required="executable_python_interpreter")
    launcher_bytes = _launcher_text(
        root, envelope_digest, manifest_digest, interpreter).encode()

    temporary = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        runtime_dir = temporary / "runtime"
        runtime_dir.mkdir()
        (temporary / "envelope.json").write_bytes(envelope_bytes)
        for path, data in runtime_bytes.items():
            target = runtime_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        launcher = temporary / "launcher"
        launcher.write_bytes(launcher_bytes)
        launcher.chmod(0o755)
        os.rename(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    launcher = output / "launcher"
    env_path = shutil.which("env") or "/usr/bin/env"
    require(Path(env_path).is_absolute() and Path(env_path).is_file()
            and os.access(env_path, os.X_OK),
            "supervisor.env", env_path, owner="supervisor",
            required="executable_environment_launcher")
    next_argv = [
        str(Path(env_path).resolve()),
        "SOODLES_ADMISSION_LAUNCHER=" + str(launcher),
        carrier["noodle"]["path"],
        "--project-dir",
        str(root),
        "start",
    ]
    return {
        "owner": "supervisor.admission",
        "action": "ready",
        "repository": REPOSITORY,
        "issue": number,
        "source_head": head,
        "bundle": str(output),
        "envelope_sha256": envelope_digest,
        "launcher": str(launcher),
        "launcher_sha256": _sha256(launcher.read_bytes()),
        "authorizes_landing": False,
        "next": {
            "kind": "executable",
            "owner": "supervisor",
            "operation": "start_noodle",
            "argv": next_argv,
        },
    }


def parser():
    value = argparse.ArgumentParser(
        description="Materialize one externally selected local Soodles admission bundle.")
    sub = value.add_subparsers(dest="verb", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("issue_readback")
    prepare_parser.add_argument("carrier")
    prepare_parser.add_argument("control_root")
    prepare_parser.add_argument("output")
    return value


def main():
    args = parser().parse_args()
    try:
        result = prepare(
            _read_json(args.issue_readback, "supervisor.issue_readback"),
            _read_json(args.carrier, "supervisor.carrier"),
            args.control_root,
            args.output,
        )
    except (AdmissionRefusal, OSError, ValueError, subprocess.TimeoutExpired) as error:
        invalid = getattr(error, "invalid", {"field": "input", "value": str(error)})
        next_action = getattr(error, "next", {
            "kind": "input", "owner": "supervisor",
            "required": ["valid_supervisor_input"]})
        print(json.dumps({
            "owner": "supervisor.admission",
            "status": "refused",
            "invalid": invalid,
            "next": next_action,
            "authorizes_landing": False,
        }, indent=2))
        return getattr(error, "exit_code", 1)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
