"""Issue #1: local runtime evidence, with no provider or landing authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


class Refusal(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: {message}; supported help: {self.prog} --help\n")


def refuse(action, field, value):
    raise Refusal(f"{action}: invalid {field}={value!r}; supported help: ./soodles {action} --help")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_env():
    # Fixture commands need local tools only, never inherited provider credentials or Noodle identity.
    return {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TMPDIR") if key in os.environ}


def run(argv, cwd):
    return subprocess.run([str(v) for v in argv], cwd=cwd, env=clean_env(),
                          stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=30)


def checked(argv, cwd):
    result = run(argv, cwd)
    if result.returncode:
        raise Refusal(f"command failed ({result.returncode}): {argv!r}\n{result.stderr}")
    return result.stdout.strip()


def load_lock(root):
    action = "runtime check"
    lock = json.loads((root / "policy/runtime.lock.json").read_text())
    fixed = {"repository": "ed3c/noodle", "platform": "linux_amd64",
             "asset_name": "noodle_linux_amd64.tar.gz"}
    expected = set(fixed) | {"release", "commit", "asset_sha256", "binary_sha256"}
    if not isinstance(lock, dict) or set(lock) != expected:
        refuse(action, "lock.fields", sorted(lock) if isinstance(lock, dict) else lock)
    for field, value in fixed.items():
        if lock[field] != value:
            refuse(action, field, lock[field])
    for field, pattern in {"release": r"v[0-9]+\.[0-9]+\.[0-9]+", "commit": r"[0-9a-f]{40}",
                           "asset_sha256": r"[0-9a-f]{64}", "binary_sha256": r"[0-9a-f]{64}"}.items():
        if not isinstance(lock[field], str) or not re.fullmatch(pattern, lock[field]):
            refuse(action, field, lock[field])
    return lock


def runtime_check(root, binary):
    lock = load_lock(root)
    host = f"{platform.system().lower()}_{platform.machine().lower()}"
    if host not in ("linux_x86_64", "linux_amd64"):
        refuse("runtime check", "platform", host)
    binary = Path(binary).resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        refuse("runtime check", "binary.path", str(binary))
    actual = digest(binary)
    if actual != lock["binary_sha256"]:
        refuse("runtime check", "binary.sha256", actual)
    result = run([binary, "--version"], root)
    if result.returncode or result.stdout.strip() != lock["release"]:
        refuse("runtime check", "binary.version", {"exit": result.returncode, "stdout": result.stdout.strip()})
    if digest(binary) != actual:
        refuse("runtime check", "binary.sha256", "changed during version readback")
    return {"binary": str(binary), **lock, "observed_version": result.stdout.strip(),
            "observed_binary_sha256": actual, "authorizes_landing": False}


def source_identity(root):
    if checked(["git", "rev-parse", "--show-toplevel"], root) != str(root.resolve()):
        refuse("acceptance verify", "source.root", str(root))
    residue = checked(["git", "status", "--porcelain", "--untracked-files=all"], root)
    if residue:
        refuse("acceptance verify", "source.residue", residue)
    return {"head": checked(["git", "rev-parse", "HEAD"], root),
            "tree": checked(["git", "rev-parse", "HEAD^{tree}"], root)}


def worktree_probe(binary):
    transcript = []
    with tempfile.TemporaryDirectory(prefix="soodles-runtime-") as directory:
        root = Path(directory)

        def record(argv, success=True):
            result = run(argv, root)
            transcript.append({"argv": [str(x) for x in argv], "exit": result.returncode,
                               "stdout": result.stdout, "stderr": result.stderr})
            if success and result.returncode:
                raise Refusal(f"runtime probe: command {argv!r} exited {result.returncode}: {result.stderr}")
            return result

        record(["git", "init", "-b", "main"])
        (root / ".gitignore").write_text(".worktrees/\n.noodle/\n")
        (root / "sentinel.txt").write_text("unchanged\n")
        record(["git", "add", ".gitignore", "sentinel.txt"])
        record(["git", "-c", "user.name=Runtime Probe", "-c", "user.email=probe@example.invalid",
                "commit", "-m", "Runtime fixture"])
        head = record(["git", "rev-parse", "HEAD"]).stdout.strip()
        record([binary, "worktree", "create", "probe"])
        try:
            actual_root = record([binary, "worktree", "exec", "probe", "git", "rev-parse", "--show-toplevel"]).stdout.strip()
            actual_head = record([binary, "worktree", "exec", "probe", "git", "rev-parse", "HEAD"]).stdout.strip()
            if actual_root != str(root / ".worktrees/probe") or actual_head != head:
                raise Refusal("runtime probe: worktree path or HEAD readback differs")
            failure = record([binary, "worktree", "exec", "absent", sys.executable, "-c",
                              "open('SHOULD_NOT_EXIST', 'w').write('bad')"], success=False)
            if failure.returncode == 0 or "does not exist" not in failure.stderr:
                raise Refusal("runtime probe: absent worktree was not refused by its owner")
            if list(root.rglob("SHOULD_NOT_EXIST")):
                raise Refusal("runtime probe: refused execution produced a side effect")
        finally:
            record([binary, "worktree", "cleanup", "probe"])
        worktrees = record(["git", "worktree", "list", "--porcelain"]).stdout
        branch = record(["git", "branch", "--list", "probe"]).stdout.strip()
        residue = record(["git", "status", "--porcelain", "--untracked-files=all"]).stdout.strip()
        final_head = record(["git", "rev-parse", "HEAD"]).stdout.strip()
        if worktrees.count("worktree ") != 1 or branch or residue or final_head != head:
            raise Refusal("runtime probe: worktree/branch/source residue or root HEAD drift")
        return {"worktree_owner": "Noodle", "zero_residue": True, "controls": transcript}


def acceptance_verify(root, binary):
    before = source_identity(root)
    runtime = runtime_check(root, binary)
    result = run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], root)
    print(result.stderr, file=sys.stderr, end="")
    if result.returncode or not re.search(r"Ran [1-9][0-9]* tests?", result.stderr) or "skipped=" in result.stderr:
        raise Refusal("acceptance verify: test discovery failed, empty, or skipped; supported help: ./soodles acceptance verify --help")
    physical = worktree_probe(runtime["binary"])
    if source_identity(root) != before:
        refuse("acceptance verify", "source.identity", "changed during acceptance")
    return {"subject": "ed3c/soodles#1", "scope": "bootstrap runtime acceptance",
            "candidate": before, "runtime": runtime, "physical": physical,
            "unit_tests": {"exit": result.returncode, "output": result.stderr},
            "authorizes_landing": False,
            "non_claims": ["Codex generation", "provider admission", "merge", "Issue closure", "checkpoint recovery"]}


def parser():
    p = Parser(prog="./soodles", description="Local Noodle runtime evidence. No provider write or landing authority.",
                                epilog="Examples: ./soodles runtime --help; ./soodles acceptance --help")
    groups = p.add_subparsers(dest="group", required=True)
    for group, verb, description in (("runtime", "check", "Check the pinned host and binary before executing it."),
                                     ("acceptance", "verify", "Run all controls on a clean candidate; emit a non-authorizing receipt.")):
        g = groups.add_parser(group, epilog=f"Examples: ./soodles {group} {verb} --help")
        verbs = g.add_subparsers(dest="verb", required=True)
        v = verbs.add_parser(verb, description=description,
                            epilog=f"Examples: ./soodles {group} {verb} /absolute/path/to/noodle")
        v.add_argument("binary", help="Explicit path to the pinned Noodle executable; no PATH fallback or installation.")
    return p


def main():
    args = parser().parse_args()
    try:
        result = runtime_check(ROOT, args.binary) if args.group == "runtime" else acceptance_verify(ROOT, args.binary)
        print(json.dumps(result, indent=2))
    except (Refusal, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
