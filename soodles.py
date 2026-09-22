"""Runtime evidence and supervised single-Issue landing requests."""
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
        if self.prog.startswith("./soodles github"):
            from issue_admission import AdmissionRefusal
            from github_reader import refusal_output
            print(json.dumps(refusal_output(AdmissionRefusal("arguments", message)), indent=2))
            self.exit(2)
        if self.prog.startswith("./soodles issue"):
            from issue_admission import AdmissionRefusal
            from issue_execution import refusal_output, refusal_text
            operation = self.prog.removeprefix("./soodles issue").strip()
            result = refusal_output(AdmissionRefusal("arguments", message), operation)
            print(json.dumps(result, indent=2))
            self.exit(2, refusal_text(result) + "\n")
        if self.prog.startswith("./soodles landing"):
            import landing
            operation = self.prog.removeprefix("./soodles landing").strip()
            result = landing.refusal_output(landing.LandingRefusal("arguments", message), operation)
            print(json.dumps(result, indent=2))
            self.exit(2, landing.refusal_text(result) + "\n")
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: {message}; supported help: {self.prog} --help\n")


def refuse(action, field, value):
    error = Refusal(f"{action}: invalid {field}={value!r}; supported help: ./soodles {action} --help")
    error.invalid = {"field": field, "value": value}
    raise error


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_env():
    # Fixture commands need local tools only, never inherited provider credentials or Noodle identity.
    return {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TMPDIR") if key in os.environ}


def run(argv, cwd, timeout=30):
    return subprocess.run([str(v) for v in argv], cwd=cwd, env=clean_env(),
                          stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=timeout)


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
    result = run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], root,
                 timeout=120)
    print(result.stderr, file=sys.stderr, end="")
    if result.returncode or not re.search(r"Ran [1-9][0-9]* tests?", result.stderr) or "skipped=" in result.stderr:
        raise Refusal("acceptance verify: test discovery failed, empty, or skipped; supported help: ./soodles acceptance verify --help")
    physical = worktree_probe(runtime["binary"])
    from cleanup_oracle import cleanup_recovery_probe
    physical["cleanup_recovery"] = cleanup_recovery_probe(runtime["binary"])
    from cleanup_lock_oracle import lock_recovery_probe
    physical["cleanup_lock_recovery"] = lock_recovery_probe(runtime["binary"], ROOT)
    from delivery_oracle import delivery_probe
    physical["delivery_recovery"] = delivery_probe(ROOT)
    from base_recovery_oracle import base_recovery_probe
    physical["base_recovery"] = base_recovery_probe(ROOT)
    from handoff_oracle import handoff_probe
    physical["order_handoff"] = handoff_probe(runtime["binary"], ROOT)
    from resume_oracle import resume_probe
    physical["interruption_resume"] = resume_probe(runtime["binary"], ROOT)
    print(json.dumps({"delivery_recovery": physical["delivery_recovery"]["cases"]}), file=sys.stderr)
    print(json.dumps({"cleanup_lock_recovery": physical["cleanup_lock_recovery"]["cases"]}), file=sys.stderr)
    print(json.dumps({"cleanup_recovery": physical["cleanup_recovery"]["cases"]}), file=sys.stderr)
    if source_identity(root) != before:
        refuse("acceptance verify", "source.identity", "changed during acceptance")
    return {"repository": "ed3c/soodles", "scope": "candidate runtime acceptance",
            "candidate": before, "runtime": runtime, "physical": physical,
            "unit_tests": {"exit": result.returncode, "output": result.stderr},
            "authorizes_landing": False,
            "non_claims": ["Codex generation", "provider admission", "merge", "Issue closure", "production checkpoint recovery"]}


def parser():
    p = Parser(prog="./soodles", description="Noodle runtime evidence and supervised landing checkpoints.",
                                epilog="Examples: ./soodles runtime --help; ./soodles acceptance --help; ./soodles landing --help")
    groups = p.add_subparsers(dest="group", required=True)
    packet = groups.add_parser("packet", description="Portable admission-recovery evidence; no executable continuation.")
    packet_verbs = packet.add_subparsers(dest="verb", required=True)
    create = packet_verbs.add_parser("create", description="Package only the fixed evidence allowlist, validate, and write deterministic tar.")
    create.add_argument("root")
    create.add_argument("archive")
    create.add_argument("--carrier", required=True, choices=("linux_amd64", "darwin_arm64"))
    verify = packet_verbs.add_parser("verify", description="Verify a directory or tar without executing or extracting it.")
    verify.add_argument("root")
    verify.add_argument("--expected-carrier", required=True, choices=("linux_amd64", "darwin_arm64"))
    drive = packet_verbs.add_parser("observe", description="Run only the pinned disposable recovery/refusal observers against the selected exact source build.")
    drive.add_argument("binary")
    drive.add_argument("source")
    drive.add_argument("output")
    drive.add_argument("--build-info", help="Actual successful `go version -m BINARY` output from the same carrier.")
    github = groups.add_parser("github", description="Authenticated Issue readback; credentials come from the supervisor.")
    github_verbs = github.add_subparsers(dest="verb", required=True)
    read_issue = github_verbs.add_parser("issue", description="Read one Issue from a supported supervisor-selected repository using GH_TOKEN. Missing credentials refuse; quota waits exit 75. No token discovery, minting, anonymous fallback or retry.", epilog="Example: ./soodles github issue ed3c/ops-reconciliation-copilot 21. The supervisor supplies a repository-scoped installation token with Issues:read in the child environment. Never put credentials in argv. Cache uses XDG_CACHE_HOME or ~/.cache; 304 requires server confirmation.")
    read_issue.add_argument("repository")
    read_issue.add_argument("number", type=int)
    candidate = groups.add_parser(
        "candidate",
        description="Read-only exact Git-object verification against a fresh Issue readback.",
        epilog="Example: ./soodles candidate verify /tmp/issue.json BASE_SHA HEAD_SHA")
    candidate_verbs = candidate.add_subparsers(dest="verb", required=True)
    candidate_verify = candidate_verbs.add_parser(
        "verify", description="Verify the checked-out candidate and its required evidence; no provider write or landing authority.")
    candidate_verify.add_argument("issue_readback")
    candidate_verify.add_argument("base_head")
    candidate_verify.add_argument("candidate_head")
    candidate_publish = candidate_verbs.add_parser(
        "publish", description="Publish one accepted Noodle-owned local candidate to one exact provider PR.")
    candidate_publish.add_argument("acceptance_receipt")
    candidate_publish.add_argument("noodle_claim")
    issue = groups.add_parser("issue", description="Consume one externally pinned Issue envelope before Noodle effects.",
                              epilog="Examples: ./soodles issue automatic --help; ./soodles issue supervised --help")
    issue_verbs = issue.add_subparsers(dest="verb", required=True)
    issue_verbs.add_parser("inspect", description="Read current Noodle schedule identity and launcher capability without effects.")
    for name in ("automatic", "supervised", "worker", "resume"):
        example = ("/external/A-checkpoint.json " if name == "resume" else "") + "/external/envelope.json SHA256"
        command = issue_verbs.add_parser(name, epilog=f"Examples: ./soodles issue {name} {example}")
        if name == "resume":
            command.add_argument("checkpoint", help="Supervisor-selected resolved predecessor landing checkpoint.")
        command.add_argument("envelope", help="Supervisor-selected envelope outside the candidate.")
        command.add_argument("envelope_digest", help="Digest fixed by the external supervisor launcher, not Issue prose.")
        if name == "worker":
            command.add_argument("worker_argv", nargs=argparse.REMAINDER,
                                 help="Exact provider argv supplied by Noodle and bound by the carrier.")
    for group, verb, description in (("runtime", "check", "Check the pinned host and binary before executing it."),
                                     ("acceptance", "verify", "Run all controls on a clean candidate; emit a non-authorizing receipt.")):
        g = groups.add_parser(group, epilog=f"Examples: ./soodles {group} {verb} --help")
        verbs = g.add_subparsers(dest="verb", required=True)
        v = verbs.add_parser(verb, description=description,
                            epilog=f"Examples: ./soodles {group} {verb} /absolute/path/to/noodle")
        v.add_argument("binary", help="Explicit path to the pinned Noodle executable; no PATH fallback or installation.")
    landing = groups.add_parser("landing", description="The supervisor supplies exact claims and raw provider readbacks. No credentials or provider writes in this process.",
                                epilog="Examples: ./soodles landing start --help; ./soodles landing advance --help; ./soodles landing reconcile --help")
    verbs = landing.add_subparsers(dest="verb", required=True)
    verbs.add_parser("identity", epilog="Examples: ./soodles landing identity")
    start = verbs.add_parser("start", epilog="Examples: ./soodles landing start /tmp/claim.json /tmp/readback.json /tmp/checkpoint.json")
    start.add_argument("claim")
    start.add_argument("readback")
    start.add_argument("checkpoint")
    advance = verbs.add_parser("advance", epilog="Examples: ./soodles landing advance /tmp/checkpoint.json /tmp/readback.json")
    advance.add_argument("checkpoint")
    advance.add_argument("readback")
    dispatch = verbs.add_parser("dispatch", description="Consume one prepared intent with fresh owner readback; emit its exact connector request once.",
                                epilog="Examples: ./soodles landing dispatch /tmp/checkpoint.json /tmp/readback.json")
    dispatch.add_argument("checkpoint")
    dispatch.add_argument("readback")
    resume = verbs.add_parser("resume", description="Supervisor re-admits a corrected verifier after provider closure; an identity-preserving local-to-cloud migration returns fresh connector readback instead of a binary.",
                             epilog="Examples: ./soodles landing resume /tmp/checkpoint.json /tmp/fresh-claim.json")
    resume.add_argument("checkpoint")
    resume.add_argument("claim")
    invalidate = verbs.add_parser("invalidate", description="Supervisor withdraws a known-unoffered acceptance before correcting this Issue. No provider write or successful CI is needed; unknown writes require owner readback.",
                                  epilog="Example: ./soodles landing invalidate /tmp/checkpoint.json")
    invalidate.add_argument("checkpoint")
    readmit = verbs.add_parser("readmit", description="Recover an invalidated, unoffered admission. The supervisor supplies a changed candidate head, fresh successful runtime evidence and raw GitHub comparisons: base_comparison when base changed (old base...new base), candidate_comparison (new base...new head), and recovery_comparison if the observed recovery base advanced again. Preserve repository, Issue, PR, worktree and verifier. No automatic rebase or provider write.",
                              epilog="Example: ./soodles landing readmit /tmp/checkpoint.json /tmp/fresh-claim.json /tmp/readback.json")
    readmit.add_argument("checkpoint")
    readmit.add_argument("claim")
    readmit.add_argument("readback")
    reconcile = verbs.add_parser("reconcile", description="Local route only: synchronize main and delegate real worktree cleanup to Noodle.", epilog="Examples: ./soodles landing reconcile /tmp/checkpoint.json /absolute/path/to/noodle")
    reconcile.add_argument("checkpoint")
    reconcile.add_argument("binary")
    return p


def bind_landing_continuation(result, args):
    """Bind known CLI paths; required provider readback still precedes execution."""
    if args.group != "landing" or not getattr(args, "readback", None):
        return result
    next_action = result.get("next")
    checkpoint = getattr(args, "checkpoint", None)
    if (not isinstance(next_action, dict) or not checkpoint
            or next_action.get("kind") != "provider_readback"
            or next_action.get("required") != ["readback"]
            or next_action.get("operation") not in {"advance", "dispatch"}
            or next_action.get("known", {}).get("checkpoint") != str(Path(checkpoint).resolve())):
        return result
    import landing
    readback = str(Path(args.readback).resolve())
    return {**result, "next": {**next_action,
            "known": {**next_action["known"], "readback": readback},
            "argv": landing.cli_argv(next_action["operation"],
                                     next_action["known"]["checkpoint"], readback)}}


def main():
    args = parser().parse_args()
    import landing
    try:
        if args.group == "packet":
            import portable_packet
            if args.verb == "create":
                result = portable_packet.create(args.root, args.carrier, args.archive)
            elif args.verb == "verify":
                result = portable_packet.verify(args.root, args.expected_carrier)
            else:
                result = portable_packet.run_observers(args.binary, args.source, args.output, args.build_info)
        elif args.group == "github":
            import github_reader
            result = github_reader.issue(args.repository, args.number)
        elif args.group == "candidate":
            if args.verb == "verify":
                import issue_admission
                readback = json.loads(Path(args.issue_readback).read_text())
                result = issue_admission.verify_candidate(
                    ROOT, args.base_head, args.candidate_head, readback)
            else:
                import candidate_publication
                result = candidate_publication.run(
                    ROOT, args.acceptance_receipt, args.noodle_claim)
        elif args.group == "issue":
            import issue_execution
            if args.verb == "inspect":
                result = issue_execution.inspect_schedule(Path.cwd())
            else:
                operation = getattr(issue_execution, args.verb)
                if args.verb == "worker":
                    result = operation(args.envelope, args.envelope_digest, Path.cwd(), args.worker_argv)
                elif args.verb == "resume":
                    result = operation(args.checkpoint, args.envelope, args.envelope_digest, Path.cwd())
                else:
                    result = operation(args.envelope, args.envelope_digest, Path.cwd())
        elif args.group == "landing":
            import landing
            if args.verb == "identity":
                result = {"owner": "landing.identity", "verifier_sha256": landing.verifier_digest(), "next": None}
            elif args.verb == "start":
                result = landing.start(landing.read(args.claim), landing.read(args.readback), args.checkpoint)
            elif args.verb == "advance":
                result = landing.advance(args.checkpoint, landing.read(args.readback))
            elif args.verb == "dispatch":
                result = landing.dispatch(args.checkpoint, landing.read(args.readback))
            elif args.verb == "resume":
                result = landing.resume(args.checkpoint, landing.read(args.claim))
            elif args.verb == "invalidate":
                result = landing.invalidate(args.checkpoint)
            elif args.verb == "readmit":
                result = landing.readmit(args.checkpoint, landing.read(args.claim), landing.read(args.readback))
            else:
                result = landing.reconcile(args.checkpoint, args.binary)
        else:
            result = runtime_check(ROOT, args.binary) if args.group == "runtime" else acceptance_verify(ROOT, args.binary)
        print(json.dumps(bind_landing_continuation(result, args), indent=2))
    except landing.LandingRefusal as exc:
        result = landing.refusal_output(exc, args.verb)
        print(json.dumps(bind_landing_continuation(result, args), indent=2))
        print(landing.refusal_text(result), file=sys.stderr)
        return 1
    except (KeyError, TypeError) as exc:
        if args.group == "github":
            from issue_admission import AdmissionRefusal
            from github_reader import refusal_output
            print(json.dumps(refusal_output(AdmissionRefusal("input.field", type(exc).__name__)), indent=2))
        elif args.group == "issue":
            from issue_admission import AdmissionRefusal
            from issue_execution import refusal_output, refusal_text
            result = refusal_output(AdmissionRefusal("input.field", str(exc)), args.verb)
            print(json.dumps(bind_landing_continuation(result, args), indent=2))
            print(refusal_text(result), file=sys.stderr)
        elif args.group == "landing":
            result = landing.refusal_output(landing.LandingRefusal("input.field", str(exc)), args.verb)
            print(json.dumps(bind_landing_continuation(result, args), indent=2))
            print(landing.refusal_text(result), file=sys.stderr)
        else:
            print(f"REFUSED: {args.group}: invalid input field={exc}; supported help: ./soodles {args.group} --help", file=sys.stderr)
        return 1
    except (Refusal, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        if args.group == "github":
            from issue_admission import AdmissionRefusal
            import github_reader
            error = exc if isinstance(exc, AdmissionRefusal) else AdmissionRefusal("input", type(exc).__name__)
            print(json.dumps(github_reader.refusal_output(error), indent=2))
            return getattr(error, "exit_code", 1)
        if args.group == "issue":
            from issue_admission import AdmissionRefusal
            import issue_execution
            error = exc if isinstance(exc, AdmissionRefusal) else AdmissionRefusal("input", str(exc))
            result = issue_execution.refusal_output(error, args.verb)
            print(json.dumps(bind_landing_continuation(result, args), indent=2))
            print(issue_execution.refusal_text(result), file=sys.stderr)
            return getattr(error, "exit_code", 1)
        if args.group == "candidate":
            import candidate_publication
            if isinstance(exc, candidate_publication.PublicationRefusal):
                result = candidate_publication.refusal_output(exc)
                print(json.dumps(result, indent=2))
                print(
                    f"REFUSED: candidate publish: invalid {exc.invalid['field']}={exc.invalid['value']!r}; "
                    "supported help: ./soodles candidate publish --help",
                    file=sys.stderr)
                return 1
            invalid = getattr(exc, "invalid", {"field": "input", "value": str(exc)})
            result = {
                "owner": "candidate.verify",
                "status": "refused",
                "invalid": invalid,
                "next": getattr(exc, "next", {
                    "kind": "input", "owner": "supervisor",
                    "required": ["valid_candidate_evidence"]}),
                "authorizes_landing": False,
            }
            print(json.dumps(bind_landing_continuation(result, args), indent=2))
            print(
                f"REFUSED: candidate verify: invalid {invalid['field']}={invalid['value']!r}; "
                "supported help: ./soodles candidate verify --help",
                file=sys.stderr)
            return getattr(exc, "exit_code", 1)
        elif args.group == "landing":
            invalid = getattr(exc, "invalid", {"field": "input", "value": str(exc)})
            result = landing.refusal_output(landing.LandingRefusal(invalid["field"], invalid["value"]), args.verb)
            print(json.dumps(bind_landing_continuation(result, args), indent=2))
            print(landing.refusal_text(result), file=sys.stderr)
        else:
            print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.modules.setdefault("soodles", sys.modules[__name__])
    sys.exit(main())
