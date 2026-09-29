#!/usr/bin/env python3
"""Materialize one exact landing-owner activation from a terminal candidate.

The external supervisor selects immutable publisher bytes and route identity.
This producer derives the landing claim from a fresh provider snapshot, creates
one new external claim/checkpoint package, and invokes the selected publisher's
existing landing.start once. It performs no provider mutation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


class SupervisorRefusal(RuntimeError):
    def __init__(self, field, value, required="corrected_supervisor_input"):
        self.invalid = {"field": field, "value": value}
        self.next = {"kind": "input", "owner": "supervisor", "required": [required]}
        super().__init__(f"landing supervisor: invalid {field}={value!r}")


def require(condition, field, value, required="corrected_supervisor_input"):
    if not condition:
        raise SupervisorRefusal(field, value, required)


def _read_json(path, field):
    path = Path(path).resolve()
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise SupervisorRefusal(field, type(error).__name__, "valid_json_input") from error
    require(isinstance(value, dict), field, type(value).__name__, "json_object")
    return value


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _publisher_identity(descriptor):
    require(set(descriptor) == {"root", "verifier_sha256"},
            "publisher.fields", sorted(descriptor))
    root = Path(descriptor["root"])
    require(root.is_absolute(), "publisher.root", str(root), "absolute_publisher_root")
    root = root.resolve()
    require(root.is_dir(), "publisher.root", str(root), "existing_publisher_root")
    expected = descriptor["verifier_sha256"]
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected),
            "publisher.verifier_sha256", expected, "pinned_publisher_digest")
    cli = root / "soodles.py"
    require(cli.is_file(), "publisher.soodles", str(cli), "immutable_publisher_cli")
    result = subprocess.run(
        [sys.executable, "-B", str(cli), "landing", "identity"],
        cwd=root, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "publisher.identity.exit", result.returncode,
            "valid_publisher_identity")
    try:
        payload = json.loads(result.stdout)
    except ValueError as error:
        raise SupervisorRefusal(
            "publisher.identity.json", result.stdout[:200], "valid_publisher_identity") from error
    require(payload == {
        "owner": "landing.identity",
        "verifier_sha256": expected,
        "next": None,
    }, "publisher.identity", payload, "matching_publisher_identity")
    return root, cli, expected


def _repository(snapshot):
    try:
        pr = snapshot["pr"]
        repository = pr["head"]["repo"]["full_name"]
    except (KeyError, TypeError) as error:
        raise SupervisorRefusal("snapshot.repository", type(error).__name__,
                                "complete_provider_snapshot") from error
    require(isinstance(repository, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository),
            "snapshot.repository", repository, "supported_repository_identity")
    require(pr.get("base", {}).get("repo", {}).get("full_name") == repository,
            "snapshot.pr.base.repository",
            pr.get("base", {}).get("repo", {}).get("full_name"),
            "same_repository_pr")
    return repository


def _derive_claim(snapshot, route, verifier_sha256):
    repository = _repository(snapshot)
    require(set(route) in (
        {"kind"},
        {"kind", "control_root", "execution_envelope", "publication_claim"},
    ), "route.fields", sorted(route))
    kind = route.get("kind")
    require(kind in {"cloud", "local"}, "route.kind", kind, "cloud_or_local_route")
    require((kind == "cloud") == (set(route) == {"kind"}),
            "route.shape", sorted(route), "route_specific_identity")
    require((kind == "local") == ("control_root" in route),
            "route.shape", sorted(route), "route_specific_identity")

    try:
        pr = snapshot["pr"]
        issue = snapshot["issue"]
        run = snapshot["run"]
        jobs = snapshot["jobs"]
        commit = snapshot["commit"]
        branch = snapshot["branch"]
        claim = {
            "repository": repository,
            "issue": issue["number"],
            "pr": pr["number"],
            "head": pr["head"]["sha"],
            "tree": commit["tree"]["sha"],
            "base_head": pr["base"]["sha"],
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "worktree": pr["head"]["ref"],
            "verifier_sha256": verifier_sha256,
        }
    except (KeyError, TypeError) as error:
        raise SupervisorRefusal("snapshot.fields", type(error).__name__,
                                "complete_provider_snapshot") from error

    require(issue.get("html_url") == f"https://github.com/{repository}/issues/{claim['issue']}",
            "snapshot.issue.identity", issue.get("html_url"), "matching_issue_readback")
    require(pr.get("html_url") == f"https://github.com/{repository}/pull/{claim['pr']}",
            "snapshot.pr.identity", pr.get("html_url"), "matching_pr_readback")
    require(commit.get("sha") == claim["head"], "snapshot.commit.head",
            commit.get("sha"), "exact_candidate_commit")
    require(branch.get("commit", {}).get("sha") == claim["base_head"],
            "snapshot.base.head", branch.get("commit", {}).get("sha"),
            "exact_base_readback")
    require(run.get("head_sha") == claim["head"],
            "snapshot.run.head_sha", run.get("head_sha"), "exact_head_runtime")
    require(run.get("status") == "completed" and run.get("conclusion") == "success",
            "snapshot.run.conclusion", run.get("conclusion"), "successful_exact_head_runtime")
    require(jobs.get("total_count") == len(jobs.get("jobs", [])) and jobs.get("total_count", 0) > 0,
            "snapshot.jobs", jobs.get("total_count"), "complete_runtime_jobs")

    if kind == "cloud":
        publication_branch = pr["head"]["ref"]
        require(isinstance(publication_branch, str) and publication_branch
                and len(publication_branch) <= 255,
                "snapshot.pr.head.ref", publication_branch, "provider_publication_branch")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", publication_branch):
            claim["worktree"] = f"cloud-{claim['issue']}"
            claim["publication_branch"] = publication_branch

    if kind == "local":
        control_root = route["control_root"]
        ref = route["execution_envelope"]
        native_ref = route["publication_claim"]
        require(isinstance(control_root, str) and Path(control_root).is_absolute(),
                "route.control_root", control_root, "absolute_control_root")
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
                "route.execution_envelope", ref, "exact_execution_envelope")
        require(isinstance(ref["path"], str) and Path(ref["path"]).is_absolute(),
                "route.execution_envelope.path", ref["path"], "absolute_execution_envelope")
        require(isinstance(ref["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]),
                "route.execution_envelope.sha256", ref["sha256"],
                "pinned_execution_envelope")
        require(isinstance(native_ref, dict) and set(native_ref) == {"path", "sha256"},
                "route.publication_claim", native_ref, "exact_native_publication_claim")
        require(isinstance(native_ref["path"], str)
                and Path(native_ref["path"]).is_absolute()
                and isinstance(native_ref["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", native_ref["sha256"]),
                "route.publication_claim", native_ref, "pinned_native_publication_claim")
        native_path = Path(native_ref["path"]).resolve()
        try:
            native_bytes = native_path.read_bytes()
        except OSError as error:
            raise SupervisorRefusal("route.publication_claim.path", str(native_path),
                                    "existing_native_publication_claim") from error
        require(hashlib.sha256(native_bytes).hexdigest() == native_ref["sha256"],
                "route.publication_claim.sha256", native_ref["sha256"],
                "unchanged_native_publication_claim")
        try:
            native = json.loads(native_bytes)
        except ValueError as error:
            raise SupervisorRefusal("route.publication_claim.json", str(native_path),
                                    "valid_native_publication_claim") from error
        require(isinstance(native, dict) and native.get("owner") == "Noodle"
                and native.get("repository") == repository
                and native.get("subject") == f"{repository}#{claim['issue']}"
                and native.get("head") == claim["head"]
                and native.get("tree") == claim["tree"]
                and native.get("base_head") == claim["base_head"]
                and native.get("authorizes_landing") is False,
                "route.publication_claim.identity", native, "matching_native_candidate")
        worktree = native.get("worktree_name")
        require(isinstance(worktree, str)
                and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", worktree),
                "route.publication_claim.worktree", worktree, "native_noodle_worktree")
        require(native.get("worktree_path") == str(Path(control_root).resolve() / ".worktrees" / worktree),
                "route.publication_claim.worktree_path", native.get("worktree_path"),
                "native_noodle_worktree_path")
        require(native.get("branch") == worktree,
                "route.publication_claim.branch", native.get("branch"), "native_noodle_branch")
        claim["worktree"] = worktree
        claim["publication_branch"] = pr["head"]["ref"]
        claim["control_root"] = str(Path(control_root).resolve())
        claim["execution_envelope"] = {
            "path": str(Path(ref["path"]).resolve()),
            "sha256": ref["sha256"],
        }
    return claim


def _write(path, data):
    path.write_bytes(data)
    handle = os.open(path, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def _rebase_next(next_action, temporary, output):
    """Preserve the owner continuation while moving its two local inputs."""
    require(isinstance(next_action, dict)
            and next_action.get("kind") == "provider_readback",
            "landing.start.next", next_action, "current_provider_readback")
    known = next_action.get("known")
    argv = next_action.get("argv")
    old = [str(temporary / name) for name in ("checkpoint.json", "readback.json")]
    require(isinstance(known, dict)
            and [known.get("checkpoint"), known.get("readback")] == old,
            "landing.start.next.known", known, "temporary_owner_inputs")
    require(isinstance(argv, list) and len(argv) >= 2 and argv[-2:] == old,
            "landing.start.next.argv", argv, "temporary_owner_argv")
    new = [str(output / name) for name in ("checkpoint.json", "readback.json")]
    return {**next_action,
            "known": {**known, "checkpoint": new[0], "readback": new[1]},
            "argv": [*argv[:-2], *new]}


def prepare(snapshot, publisher, route, output):
    """Create one external landing activation and return the selected owner's current result."""
    publisher_root, publisher_cli, verifier = _publisher_identity(publisher)
    source_root = Path(__file__).resolve().parent
    require(not publisher_root.is_relative_to(source_root)
            and not source_root.is_relative_to(publisher_root),
            "publisher.root", str(publisher_root),
            "external_immutable_publisher")
    claim = _derive_claim(snapshot, route, verifier)

    output = Path(output)
    require(output.is_absolute(), "output", str(output), "absolute_external_output")
    output = output.resolve()
    require(not output.is_relative_to(source_root), "output", str(output),
            "external_output_outside_candidate")
    require(not output.is_relative_to(publisher_root), "output", str(output),
            "external_output_outside_publisher")
    require(not output.exists(), "output.exists", str(output), "new_external_output")
    require(output.parent.is_dir(), "output.parent", str(output.parent),
            "existing_external_parent")

    temporary = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        claim_path = temporary / "claim.json"
        readback_path = temporary / "readback.json"
        checkpoint = temporary / "checkpoint.json"
        _write(claim_path, _canonical(claim))
        _write(readback_path, _canonical(snapshot))
        manifest = {
            "schema": 1,
            "publisher_root": str(publisher_root),
            "publisher_verifier_sha256": verifier,
            "route": route["kind"],
            "claim_sha256": hashlib.sha256(claim_path.read_bytes()).hexdigest(),
            "readback_sha256": hashlib.sha256(readback_path.read_bytes()).hexdigest(),
            "authorizes_landing": False,
        }
        _write(temporary / "manifest.json", _canonical(manifest))

        start = subprocess.run(
            [sys.executable, "-B", str(publisher_cli), "landing", "start",
             str(claim_path), str(readback_path), str(checkpoint)],
            cwd=publisher_root, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=30)
        require(start.returncode == 0, "landing.start.exit",
                {"exit": start.returncode, "stderr": start.stderr[-500:]},
                "valid_terminal_candidate_or_route")
        try:
            owner = json.loads(start.stdout)
        except ValueError as error:
            raise SupervisorRefusal(
                "landing.start.json", start.stdout[:200], "valid_landing_owner_output") from error
        require(owner.get("owner") == "landing.start",
                "landing.start.owner", owner.get("owner"), "landing_start_owner")
        require(checkpoint.is_file(), "checkpoint", "missing",
                "landing_start_checkpoint")
        os.rename(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    rebased = json.loads((output / "claim.json").read_text())
    require(owner.get("checkpoint") == str(temporary / "checkpoint.json"),
            "landing.start.checkpoint", owner.get("checkpoint"),
            "temporary_owner_checkpoint")
    next_action = _rebase_next(owner.get("next"), temporary, output)
    return {
        "owner": "landing-supervisor",
        "action": "activated",
        "route": route["kind"],
        "publisher": {
            "root": str(publisher_root),
            "verifier_sha256": verifier,
        },
        "claim": rebased,
        "checkpoint": str(output / "checkpoint.json"),
        "landing_owner": {**owner, "checkpoint": str(output / "checkpoint.json"),
                          "next": next_action},
        "authorizes_landing": False,
    }


def parser():
    p = argparse.ArgumentParser(
        prog="./landing-supervisor",
        description="Activate the externally selected landing owner for one terminal candidate.")
    p.add_argument("snapshot", help="Fresh raw provider snapshot JSON.")
    p.add_argument("publisher", help="Supervisor-selected publisher descriptor JSON.")
    p.add_argument("route", help="Supervisor-selected cloud/local route descriptor JSON.")
    p.add_argument("output", help="New absolute external output directory.")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = prepare(
            _read_json(args.snapshot, "snapshot"),
            _read_json(args.publisher, "publisher"),
            _read_json(args.route, "route"),
            args.output,
        )
    except (SupervisorRefusal, OSError, subprocess.TimeoutExpired) as error:
        invalid = getattr(error, "invalid", {"field": "input", "value": type(error).__name__})
        next_action = getattr(error, "next", {
            "kind": "input", "owner": "supervisor",
            "required": ["valid_terminal_candidate_activation"],
        })
        print(json.dumps({
            "owner": "landing-supervisor",
            "status": "refused",
            "invalid": invalid,
            "next": next_action,
            "authorizes_landing": False,
        }, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
