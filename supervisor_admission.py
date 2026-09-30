#!/usr/bin/env python3
"""Materialize one externally selected local Soodles admission capability.

The supervisor selects the fresh Issue readback, carrier, control root and new
external output directory. This module derives no task identity and performs no
Noodle/provider write. Runtime bytes are copied from committed Git objects, not
from the working tree. Provider credentials remain supervisor-owned: a configured
NOODLES_TOKEN_COMMAND is consumed only by the generated start wrapper, which
injects its result into the Noodle child environment and never persists it.
"""
import argparse
import ctypes
import errno
import stat
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

from issue_admission import (AdmissionRefusal, body_digest, parse_contract, require,
                             scoped_order_id, validate_issue, resolve_instruction_context)
from issue_execution import validate_carrier
from repository_binding import git_origins, issue_urls

REPOSITORY = "ed3c/soodles"
TOKEN_COMMAND_ENV = "NOODLES_TOKEN_COMMAND"
BUNDLE_PATHS = (
    "soodles.py",
    "issue_admission.py",
    "issue_execution.py",
    "github_reader.py",
    "repository_binding.py",
    "provider_credential.py",
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


def _start_text(control_root, launcher_sha256, manifest_sha256,
                noodle_path, noodle_sha256, interpreter, config_sha256=None,
                bootstrap_config_sha256=None, correction=False):
    template = """#!{interpreter}
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CONTROL_ROOT = {control_root!r}
LAUNCHER_SHA256 = {launcher_sha256!r}
MANIFEST_SHA256 = {manifest_sha256!r}
NOODLE_PATH = {noodle_path!r}
NOODLE_SHA256 = {noodle_sha256!r}
CONFIG_SHA256 = {config_sha256!r}
BOOTSTRAP_CONFIG_SHA256 = {bootstrap_config_sha256!r}
CORRECTION_HOLD = {correction!r}
TOKEN_COMMAND_ENV = {token_command_env!r}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def refuse(field, value, required):
    print(json.dumps({{
        "owner": "supervisor.start",
        "status": "refused",
        "invalid": {{"field": field, "value": value}},
        "next": {{"kind": "input", "owner": "supervisor",
                  "required": [required]}},
        "authorizes_landing": False
    }}, indent=2))
    return 64


def main():
    if sys.argv[1:] not in ([], ["--once"]):
        return refuse("start.argv", sys.argv[1:], "exact_start_or_once")
    if CORRECTION_HOLD and sys.argv[1:]:
        return refuse("start.argv", sys.argv[1:], "exact_correction_start")
    try:
        manifest = ROOT / "manifest.json"
        observed_manifest = digest(manifest.read_bytes())
        if observed_manifest != MANIFEST_SHA256:
            return refuse("start.manifest_sha256", observed_manifest,
                          "fresh_supervisor_admission")
        launcher = ROOT / "launcher"
        observed_launcher = digest(launcher.read_bytes())
        if observed_launcher != LAUNCHER_SHA256:
            return refuse("start.launcher_sha256", observed_launcher,
                          "fresh_supervisor_admission")
        noodle = Path(NOODLE_PATH)
        observed_noodle = digest(noodle.read_bytes())
        if observed_noodle != NOODLE_SHA256:
            return refuse("start.noodle_sha256", observed_noodle,
                          "measured_local_carrier")
        expected_config = BOOTSTRAP_CONFIG_SHA256 if sys.argv[1:] == ["--once"] else CONFIG_SHA256
        if expected_config is not None and digest((Path(CONTROL_ROOT) / ".noodle.toml").read_bytes()) != expected_config:
            return refuse("start.host_config", "changed", "unchanged_installed_configuration")
    except OSError as error:
        return refuse("start.bundle", type(error).__name__,
                      "fresh_supervisor_admission")

    try:
        for item in json.loads(manifest.read_bytes())["runtime"]:
            if digest((ROOT / item["path"]).read_bytes()) != item["sha256"]:
                return refuse("start.runtime", item["path"], "fresh_supervisor_admission")
    except (OSError, ValueError, KeyError) as error:
        return refuse("start.runtime", type(error).__name__, "fresh_supervisor_admission")
    sys.path.insert(0, str(ROOT / "runtime"))
    from provider_credential import CredentialRefusal, clean_child_env, supply_token
    try:
        token = supply_token("ed3c/soodles", {{"issues": "read"}})
    except CredentialRefusal as error:
        return refuse("start." + error.field, error.value, error.required)

    env = clean_child_env()
    env["GH_TOKEN"] = token
    env["GITHUB_TOKEN"] = token
    env["SOODLES_ADMISSION_LAUNCHER"] = str(ROOT / "launcher")
    env.setdefault("NOODLE_NO_BROWSER", "1")
    env.pop(TOKEN_COMMAND_ENV, None)
    os.execve(
        NOODLE_PATH,
        [NOODLE_PATH, "--project-dir", CONTROL_ROOT, "start",
         *(["--mode", "manual"] if CORRECTION_HOLD else sys.argv[1:])],
        env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
"""
    return template.format(
        interpreter=interpreter,
        control_root=str(control_root),
        launcher_sha256=launcher_sha256,
        manifest_sha256=manifest_sha256,
        noodle_path=noodle_path,
        noodle_sha256=noodle_sha256,
        config_sha256=config_sha256,
        bootstrap_config_sha256=bootstrap_config_sha256,
        correction=correction,
        token_command_env=TOKEN_COMMAND_ENV,
    )


def _entry_text(root, envelope_digest, runtime, interpreter, operation):
    """Bind the existing worker/backlog consumers; never create another order."""
    return f'''#!{interpreter}
import hashlib, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[{1 if operation == "worker" else 0}]
CONTROL = Path({str(root)!r})
HASHES = {runtime!r}
for name, expected in HASHES.items():
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
        raise SystemExit("changed admission bytes: " + name)
sys.path.insert(0, str(ROOT / "runtime"))
from issue_admission import load_external_envelope, validate_issue, AdmissionRefusal
import issue_execution
try:
    envelope = load_external_envelope(ROOT / "envelope.json", {envelope_digest!r}, CONTROL)
    if {operation!r} == "worker":
        issue_execution.worker(ROOT / "envelope.json", {envelope_digest!r},
                               Path.cwd(), sys.argv[1:])
    else:
        argv = sys.argv[1:]
        order = envelope["execution"]["order_id"]
        if argv == ["done", "schedule"]:
            print("{{}}")
        elif argv == ["sync"] or argv == ["done", order]:
            issue = issue_execution.fetch_issue(envelope["repository"], envelope["issue"])
            completed = issue.get("state") == "closed"
            validate_issue(issue, envelope, completed=completed)
            if argv == ["sync"]:
                if not completed:
                    print(json.dumps({{"id": order, "title": issue.get("title", order),
                        "status": "open", "plan": envelope["execution"]["task"]}}))
            elif not completed:
                raise SystemExit("provider Issue is not completed")
            else:
                print(json.dumps({{"readback": "closed/completed", "issue": envelope["issue"]}}))
        else:
            raise SystemExit("unsupported exact-Issue adapter operation")
except AdmissionRefusal as error:
    print(json.dumps(issue_execution.refusal_output(error, {operation!r})))
    raise SystemExit(getattr(error, "exit_code", 1))
'''


def _config_bytes(output, carrier, *, bootstrap=False):
    codex = carrier["codex"]
    prefix = ["exec", "--skip-git-repo-check", "--json", "--model", codex["model"]]
    require(codex["argv"][:len(prefix)] == prefix, "supervisor.worker.argv", codex["argv"],
            owner="supervisor", required="measured_noodle_worker_argv")
    # JSON strings/arrays are valid TOML basic strings/arrays. Shell commands
    # belong only to the existing adapter contract, with exact quoted paths.
    quote = json.dumps
    backlog = shlex.quote(str(output / "backlog"))
    base = (f'mode = "supervised"\n[server]\nenabled = false\n'
            f'[concurrency]\nmax_concurrency = 1\n[routing.defaults]\n'
            f'provider = "codex"\nmodel = {quote(codex["model"])}\n'
            f'[skills]\npaths = [{quote(str(output / "runtime/.agents/skills"))}]\n'
            f'[agents.codex]\npath = {quote(str(output / "provider"))}\n'
            f'args = {quote(codex["argv"][len(prefix):])}\nrequire_typed_outcome = true\n')
    return (base + ('' if bootstrap else f'[adapters.backlog.scripts]\n'
            + ''.join(f'{verb} = {quote(backlog + " " + verb)}\n'
                      for verb in ("sync", "add", "edit", "done")))).encode()


def prepare(issue_readback, carrier, control_root, output, *,
            interpreter=None, environ=None, task=None, wire_host=False, instruction_pins=None,
            correction=False):
    """Create one immutable external bundle and return the only start continuation."""
    environ = os.environ if environ is None else environ
    require(type(correction) is bool and (not correction or wire_host),
            "supervisor.correction", correction,
            owner="supervisor", required="host_wired_correction_bundle")
    root = Path(control_root)
    require(root.is_absolute(), "supervisor.control_root", str(control_root),
            owner="supervisor", required="absolute_control_root")
    root = root.resolve()
    require(root.is_dir(), "supervisor.control_root", str(root),
            owner="supervisor", required="existing_control_root")

    token_command = environ.get(TOKEN_COMMAND_ENV)
    require(isinstance(token_command, str) and bool(token_command.strip()),
            "supervisor.provider_credential_supplier",
            "absent" if not token_command else "empty",
            owner="supervisor", required=TOKEN_COMMAND_ENV)

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
    if contract.get("schema", 0) >= 3:
        require(head == contract["base_head"], "supervisor.control_root.head", head,
                owner="supervisor", required="fresh_issue_base_checkout")
    base_head = contract["base_head"] if contract.get("schema", 0) >= 3 else head
    origin = _git(root, "remote", "get-url", "origin")
    require(origin in git_origins(REPOSITORY), "supervisor.control_root.origin", origin,
            owner="Git", required="admitted_repository_identity")

    require(isinstance(carrier, dict), "supervisor.carrier", type(carrier).__name__,
            owner="supervisor", required="measured_local_carrier")
    validate_carrier({"execution": {"carrier": carrier}}, worker=True)

    order_id = scoped_order_id(number, root)
    worktree = root / ".worktrees" / (order_id + "-0-execute")
    # A correction retains the published worktree, whose HEAD is newer than
    # the control root. Bind the real worker input without advancing the base.
    worker_head = _git(worktree, "rev-parse", "HEAD") if correction else head
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
            "worktree": order_id + "-0-execute",
            "order_id": order_id,
            "stage_index": 0,
            "carrier": carrier,
            "task": task if task is not None else f"Execute externally admitted {REPOSITORY}#{number}.",
            "source_head": worker_head,
        },
    }
    if instruction_pins is not None:
        envelope["schema"] = 2
        envelope["execution"]["instruction_context"] = resolve_instruction_context(root, worker_head, instruction_pins)
    validate_issue(issue_readback, envelope)
    if correction:
        import issue_execution
        issue_execution.validate_worktree(worktree, envelope)
    require(isinstance(envelope["execution"]["task"], str)
            and bool(envelope["execution"]["task"].strip()),
            "supervisor.task", task, owner="supervisor", required="bounded_task")

    envelope_bytes = _canonical(envelope)
    envelope_digest = _sha256(envelope_bytes)
    runtime = []
    runtime_bytes = {}
    bundle_paths = BUNDLE_PATHS + ((".agents/skills/execute/SKILL.md",
                                  ".agents/skills/schedule/SKILL.md") if wire_host else ())
    for path in bundle_paths:
        data = _git_bytes(root, head, path)
        runtime_bytes[path] = data
        runtime.append({"path": "runtime/" + path, "sha256": _sha256(data)})

    interpreter = str(Path(interpreter or sys.executable).resolve())
    require(Path(interpreter).is_absolute() and Path(interpreter).is_file()
            and os.access(interpreter, os.X_OK),
            "supervisor.interpreter", interpreter,
            owner="supervisor", required="executable_python_interpreter")
    host_files = {}
    if wire_host:
        pins = {item["path"]: item["sha256"] for item in runtime}
        pins["envelope.json"] = envelope_digest
        host_files = {
            "provider/codex": _entry_text(root, envelope_digest, pins, interpreter, "worker").encode(),
            "backlog": _entry_text(root, envelope_digest, pins, interpreter, "backlog").encode(),
            "noodle.toml": _config_bytes(output, carrier),
            "bootstrap-noodle.toml": _config_bytes(output, carrier, bootstrap=True),
        }
        runtime.extend({"path": path, "sha256": _sha256(data)} for path, data in host_files.items())

    manifest = {
        "schema": 1,
        "repository": REPOSITORY,
        "issue": number,
        "source_head": head,
        "envelope_sha256": envelope_digest,
        "runtime": runtime,
        "credential_supplier": TOKEN_COMMAND_ENV,
        "authorizes_landing": False,
    }
    manifest_bytes = _canonical(manifest)
    manifest_digest = _sha256(manifest_bytes)
    launcher_bytes = _launcher_text(
        root, envelope_digest, manifest_digest, interpreter).encode()
    launcher_digest = _sha256(launcher_bytes)
    start_bytes = _start_text(
        root, launcher_digest, manifest_digest,
        carrier["noodle"]["path"], carrier["noodle"]["sha256"],
        interpreter, _sha256(host_files["noodle.toml"]) if wire_host else None,
        _sha256(host_files["bootstrap-noodle.toml"]) if wire_host else None,
        correction=correction).encode()

    temporary = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        runtime_dir = temporary / "runtime"
        runtime_dir.mkdir()
        (temporary / "envelope.json").write_bytes(envelope_bytes)
        for path, data in host_files.items():
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o600 if path.endswith("noodle.toml") else 0o755)
        for path, data in runtime_bytes.items():
            target = runtime_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        launcher = temporary / "launcher"
        launcher.write_bytes(launcher_bytes)
        launcher.chmod(0o755)
        start = temporary / "start-noodle"
        start.write_bytes(start_bytes)
        start.chmod(0o755)
        os.rename(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    launcher = output / "launcher"
    start = output / "start-noodle"
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
        "start": str(start),
        "start_sha256": _sha256(start.read_bytes()),
        **({"process_argv": [carrier["noodle"]["path"], "--project-dir", str(root),
                             "start", "--mode", "manual"]} if correction else {}),
        **({"bootstrap": {"argv": [str(start), "--once"], "owner": "supervisor",
                           "config": str(output / "bootstrap-noodle.toml") if wire_host else None,
                           "config_sha256": _sha256(host_files["bootstrap-noodle.toml"]) if wire_host else None}}
           if not correction else {}),
        "provider_identity": {
            "owner": "supervisor",
            "supplier": TOKEN_COMMAND_ENV,
            "in_argv": False,
            "persisted_token": False,
        },
        "authorizes_landing": False,
        "next": {
            "kind": "executable",
            "owner": "supervisor",
            "operation": "start_noodle",
            "argv": [str(start)],
        },
    }


AUTHORIZATION_SELECTION_FIELDS = {
    "schema", "repository", "control_root", "issue", "task", "carrier",
    "landing_owner", "instruction_paths",
}
CANONICAL_WORKFLOW = {
    "path": ".github/workflows/runtime.yml",
    "job": "runtime-evidence",
    "step": "Canonical acceptance on the exact candidate head",
}


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "selection.duplicate_key", key)
        value[key] = item
    return value


def _publish_directory(staging, target):
    """The sole identity commit: an atomic, exclusive directory publication."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        name, arguments = "renamex_np", [os.fsencode(staging), os.fsencode(target), 4]
        types = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    elif sys.platform.startswith("linux"):
        name = "renameat2"
        # Absolute paths make the directory descriptors irrelevant.
        arguments = [-100, os.fsencode(staging), -100, os.fsencode(target), 1]
        types = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                 ctypes.c_char_p, ctypes.c_uint]
    else:
        raise AdmissionRefusal("authorization.publication", sys.platform,
                               "supervisor", "supported_exclusive_directory_publication")
    function = getattr(libc, name, None)
    require(function is not None, "authorization.publication", name,
            owner="supervisor", required="supported_exclusive_directory_publication")
    function.argtypes = types
    function.restype = ctypes.c_int
    if function(*arguments) != 0:
        error = ctypes.get_errno()
        if error in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(error, os.strerror(error), str(target))
        raise AdmissionRefusal("authorization.publication", os.strerror(error),
                               "supervisor", "supported_exclusive_directory_publication")


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_durable(path, data):
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _prepared_receipt(root, target, digest, lifecycle_owner=None):
    final = target / "authorization.json"
    return {
        "owner": "supervisor.authorization", "status": "prepared",
        "authorizes_landing": False,
        "authorization": {"path": str(final), "sha256": digest},
        "next": {
            "kind": "executable", "owner": "soodles.issue-atom",
            "argv": [lifecycle_owner["path"] if lifecycle_owner else str(root / "issue-atom"), "run", str(final)],
            "environment": {"SOODLES_AUTHORIZATION_SHA256": digest},
        },
    }


def _committed_preparation(target, selection, selection_digest, root):
    """Check stored provenance only; issue-atom owns all live readiness checks."""
    import issue_atom
    require(stat.S_ISDIR(target.lstat().st_mode), "authorization.output", str(target))
    objects, hashes = {}, {}
    for name in ("authorization", "prepared", "selection-binding"):
        path = target / (name + ".json")
        field = "authorization.bundle." + name
        try:
            require(stat.S_ISREG(path.lstat().st_mode), field, str(path),
                    required="exact_committed_bundle_component")
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), field, str(path),
                        required="exact_committed_bundle_component")
                raw = stream.read()
            objects[name] = json.loads(raw, object_pairs_hook=_unique_object)
        except (OSError, ValueError, AdmissionRefusal) as error:
            # Readback never repairs committed bytes or substitutes an identity.
            raise AdmissionRefusal(field, str(path), "supervisor",
                                   "exact_committed_bundle_component") from error
        hashes[name] = _sha256(raw)
    binding = objects["selection-binding"]
    expected = {"schema": 1, "selection_sha256": selection_digest,
                "authorization_sha256": hashes["authorization"],
                "prepared_sha256": hashes["prepared"], "output": str(target)}
    require(isinstance(binding, dict) and type(binding.get("schema")) is int
            and binding == expected, "authorization.selection_binding", binding)
    auth = objects["authorization"]
    pins = selection["instruction_paths"]
    require(isinstance(pins, list), "selection.instruction_paths", pins)
    schema = 3 if pins else 2
    fields = (issue_atom.AUTH_FIELDS | {"landing_owner"}
              | ({"instruction_pins"} if pins else set())
              | ({"prior_publication", "prior_atom"} & selection.keys())
              | ({"lifecycle_owner"} if "lifecycle_owner" in selection else set()))
    require(isinstance(auth, dict) and set(auth) == fields
            and type(auth.get("schema_version")) is int and auth["schema_version"] == schema,
            "authorization.bundle.schema", auth)
    selected = {"owner": "external-supervisor", "control_root": str(root),
                "repository": selection["repository"], "issue": selection["issue"],
                "task": selection["task"], "landing_owner": selection["landing_owner"],
                "noodle": selection["carrier"]["noodle"],
                "carrier": {k: selection["carrier"][k] for k in ("platform", "codex")},
                "workflow": CANONICAL_WORKFLOW}
    require(all(auth[k] == v for k, v in selected.items()),
            "authorization.bundle.selection", str(target))
    if "lifecycle_owner" in selection:
        require(auth["lifecycle_owner"] == selection["lifecycle_owner"],
                "authorization.bundle.lifecycle_owner", str(target))
    if "prior_publication" in selection:
        require(auth["prior_publication"] == selection["prior_publication"],
                "authorization.bundle.prior_publication", str(target))
    if "prior_atom" in selection:
        require(auth["prior_atom"] == selection["prior_atom"],
                "authorization.bundle.prior_atom", str(target))
    require(isinstance(auth["base_head"], str) and issue_atom.SHA40.fullmatch(auth["base_head"])
            and parse_contract(auth["issue"]["body"]).get("base_head") == auth["base_head"],
            "authorization.bundle.base", auth["base_head"])
    config = auth["host_config_sha256"]
    require(config is None or isinstance(config, str) and issue_atom.SHA64.fullmatch(config),
            "authorization.bundle.config", config)
    if "prior_atom" in selection:
        require(config == issue_atom.prior_host_config(selection["prior_atom"], root)["original_sha256"],
                "authorization.bundle.prior_host_config", config)
    if pins:
        from issue_admission import validate_instruction_files
        validate_instruction_files(auth["instruction_pins"])
        require([pin["path"] for pin in auth["instruction_pins"]] == pins,
                "authorization.bundle.instructions", pins)
    receipt = objects["prepared"]
    require(receipt == _prepared_receipt(root, target, hashes["authorization"], selection.get("lifecycle_owner"))
            and receipt.get("authorizes_landing") is False,
            "authorization.bundle.prepared", receipt)
    return receipt


def authorize(selection_path, expected_sha256, output):
    """Materialize selected authority; never select it or run its continuation."""
    # Local import preserves the existing issue_atom -> prepare dependency.
    import issue_atom
    from issue_admission import validate_instruction_files

    source = Path(selection_path)
    require(source.is_absolute() and source.is_file() and not source.is_symlink(),
            "selection.path", str(source), owner="supervisor",
            required="absolute_selected_regular_file")
    raw = source.read_bytes()
    require(isinstance(expected_sha256, str)
            and issue_atom.SHA64.fullmatch(expected_sha256)
            and _sha256(raw) == expected_sha256,
            "selection.sha256", _sha256(raw), owner="supervisor",
            required="unchanged_selected_bytes")
    selection = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    required_fields = AUTHORIZATION_SELECTION_FIELDS | (
        {"lifecycle_owner"} if isinstance(selection, dict) and "lifecycle_owner" in selection else set())
    require(isinstance(selection, dict) and set(selection) in
            (required_fields, required_fields | {"prior_publication"},
             required_fields | {"prior_publication", "prior_atom"}),
            "selection.fields", sorted(selection) if isinstance(selection, dict) else type(selection).__name__)
    require(type(selection["schema"]) is int and selection["schema"] == 1,
            "selection.schema", selection["schema"])
    root_value = selection["control_root"]
    require(isinstance(root_value, str) and Path(root_value).is_absolute(),
            "selection.control_root", root_value)
    root = Path(root_value).resolve()
    target = Path(output)
    require(target.is_absolute(), "authorization.output", str(target))
    target = target.parent.resolve() / target.name
    require(not target.is_relative_to(root) and target.parent.is_dir(),
            "authorization.output", str(target), owner="supervisor",
            required="external_output_with_existing_parent")
    if os.path.lexists(target):
        return _committed_preparation(target, selection, expected_sha256, root)
    require(root.is_dir(), "selection.control_root", str(root))
    require(Path(_git(root, "rev-parse", "--show-toplevel")).resolve() == root,
            "selection.control_root", str(root), owner="supervisor",
            required="exact_git_control_root")
    entry = root / "issue-atom"
    require(entry.is_file() and not entry.is_symlink() and os.access(entry, os.X_OK),
            "authorization.next.entry", str(entry), owner="supervisor",
            required="executable_issue_atom_entry")
    head = _git(root, "rev-parse", "HEAD")
    carrier = selection["carrier"]
    host_config = issue_atom.host_config_identity(root)
    if "prior_publication" in selection:
        import candidate_publication
        number = selection["issue"].get("number")
        require(type(number) is int and number > 0, "selection.issue.number", number,
                required="existing_issue_for_candidate_amendment")
        try:
            candidate_publication.validate_amendment_prior(
                selection["prior_publication"], selection["repository"],
                selection["repository"] + "#" + str(number), number)
        except candidate_publication.PublicationRefusal as error:
            raise AdmissionRefusal(error.invalid["field"], error.invalid["value"],
                                   "supervisor", "exact_prior_publication") from error
    if "prior_atom" in selection:
        try:
            issue_atom.validate_prior_atom_ref(selection["prior_atom"], root)
            prior_host = issue_atom.prior_host_config(selection["prior_atom"], root)
        except issue_atom.AtomRefusal as error:
            raise AdmissionRefusal(error.invalid["field"], error.invalid["value"],
                                   "supervisor", "selected_previous_atom") from error
        expected_host = (prior_host["original_sha256"] if prior_host["restored"]
                         else prior_host["installed_sha256"])
        require(host_config == expected_host, "amendment.current_host_config", host_config,
                owner="supervisor", required="unchanged_previous_host_configuration")
        host_config = prior_host["original_sha256"]
    require(isinstance(carrier, dict) and set(carrier) == {"platform", "noodle", "codex"},
            "selection.carrier", carrier)
    validate_carrier({"execution": {"carrier": carrier}}, worker=True)
    workflow = dict(CANONICAL_WORKFLOW)
    workflow_bytes = _git_bytes(root, head, workflow["path"]).decode("utf-8")
    require(all(workflow[key] in workflow_bytes for key in ("job", "step")),
            "authorization.workflow", workflow, owner="supervisor",
            required="committed_canonical_workflow")
    paths = selection["instruction_paths"]
    require(isinstance(paths, list), "selection.instruction_paths", paths)
    pins = []
    if paths:
        instruction_head = (selection["prior_publication"]["head"]
                            if "prior_publication" in selection else head)
        pins = [{"path": path, "sha256": "0" * 64} for path in paths]
        validate_instruction_files(pins)
        for pin in pins:
            pin["sha256"] = _sha256(_git_bytes(root, instruction_head, pin["path"]))
        resolve_instruction_context(root, instruction_head, pins)
    authorization = {
        "schema_version": 3 if pins else 2,
        "owner": "external-supervisor",
        "repository": selection["repository"],
        "control_root": str(root), "base_head": head,
        "issue": selection["issue"], "task": selection["task"],
        "noodle": carrier["noodle"],
        "carrier": {"platform": carrier["platform"], "codex": carrier["codex"]},
        "workflow": workflow,
        "host_config_sha256": host_config,
        "landing_owner": selection["landing_owner"],
    }
    if "lifecycle_owner" in selection:
        authorization["lifecycle_owner"] = selection["lifecycle_owner"]
    if pins:
        authorization["instruction_pins"] = pins
    if "prior_publication" in selection:
        authorization["prior_publication"] = selection["prior_publication"]
    if "prior_atom" in selection:
        authorization["prior_atom"] = selection["prior_atom"]
    data = _canonical(authorization)
    digest = _sha256(data)
    receipt = _prepared_receipt(root, target, digest, selection.get("lifecycle_owner"))
    receipt_data = _canonical(receipt)
    binding = {"schema": 1, "selection_sha256": expected_sha256,
               "authorization_sha256": digest, "prepared_sha256": _sha256(receipt_data),
               "output": str(target)}
    staging = Path(tempfile.mkdtemp(prefix=".authorization-", dir=target.parent))
    try:
        staged = staging / "authorization.json"
        _write_durable(staged, data)
        issue_atom.validate_authorization(staged, digest)
        _write_durable(staging / "prepared.json", receipt_data)
        _write_durable(staging / "selection-binding.json", _canonical(binding))
        _sync_directory(staging)
        try:
            _publish_directory(staging, target)
        except FileExistsError:
            return _committed_preparation(target, selection, expected_sha256, root)
        # Publication has committed. No subsequent error may remove target.
        _sync_directory(target.parent)
        return receipt
    finally:
        # Only this invocation's private, uncommitted staging is ours to remove.
        # SIGKILL can leave it behind, but it is never an offered continuation.
        if staging.exists():
            shutil.rmtree(staging)


def parser():
    value = argparse.ArgumentParser(
        description="Materialize one externally selected local Soodles admission bundle.")
    sub = value.add_subparsers(dest="verb", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("issue_readback")
    prepare_parser.add_argument("carrier")
    prepare_parser.add_argument("control_root")
    prepare_parser.add_argument("output")
    authorize_parser = sub.add_parser("authorize")
    authorize_parser.add_argument("selection")
    authorize_parser.add_argument("expected_sha256")
    authorize_parser.add_argument("output")
    return value


def main():
    args = parser().parse_args()
    try:
        if args.verb == "authorize":
            result = authorize(args.selection, args.expected_sha256, args.output)
        else:
            result = prepare(
                _read_json(args.issue_readback, "supervisor.issue_readback"),
                _read_json(args.carrier, "supervisor.carrier"),
                args.control_root,
                args.output,
            )
    except (AdmissionRefusal, OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as error:
        invalid = getattr(error, "invalid", {"field": "input", "value": str(error)})
        next_action = getattr(error, "next", {
            "kind": "input", "owner": getattr(error, "owner", "supervisor"),
            "required": [getattr(error, "required", "valid_supervisor_input")]})
        print(json.dumps({
            "owner": "supervisor.authorization" if args.verb == "authorize" else "supervisor.admission",
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
