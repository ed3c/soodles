"""Standalone local runtime oracle. No candidate imports or provider authorization."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def lock_recovery_probe(binary, cli_root, isolated=False):
    binary, cli = str(Path(binary).resolve()), str(Path(cli_root).resolve() / "soodles")
    git = shutil.which("git")
    prefix = ["setpriv", "--reuid=65534", "--regid=65534", "--clear-groups", "--no-new-privs"] if isolated else []
    if isolated and os.geteuid() != 0:
        raise RuntimeError("isolated oracle requires supervisor uid 0")
    transcript, cases = [], []

    def require(condition, detail):
        if not condition:
            raise AssertionError(detail)

    with tempfile.TemporaryDirectory(prefix="soodles-lock-oracle-") as directory:
        area = Path(directory)
        area.chmod(0o755)
        for case in ("lock_release", "legacy_unknown", "consumed_release", "moved_after_block"):
            home = area / case
            home.mkdir(mode=0o755)
            root, shim = home / "repo", home / "shim"
            root.mkdir()
            shim.mkdir()
            data = home / "state"
            data.mkdir()
            if isolated:
                os.chown(root, 65534, 65534)
                os.chown(data, 65534, 65534)
            marker, deletions = data / "kill-on-delete", data / "deletions"
            script = shim / "git"
            script.write_text(
                "#!" + sys.executable + "\nimport os,sys,signal\nfrom pathlib import Path\n"
                f"root={str(root)!r}\nmarker=Path({str(marker)!r})\ngit={git!r}\nargs=sys.argv[1:]\n"
                "if os.getcwd()==root:\n"
                "    if args==['fetch','origin','main']:\n"
                "        os.execv(git,[git,'fetch',root,'main:refs/remotes/origin/main'])\n"
                "    if args[:2] in (['worktree','remove'],['branch','-d'],['branch','-D']):\n"
                f"        with open({str(deletions)!r},'a') as out: out.write(repr(args)+'\\n')\n"
                "    if args==['branch','-d','probe'] and marker.exists():\n"
                "        marker.unlink()\n        os.kill(os.getppid(),signal.SIGKILL)\n        sys.exit(137)\n"
                "os.execv(git,[git]+args)\n"
            )
            script.chmod(0o755)
            env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ}
            env["PATH"] = str(shim) + os.pathsep + env["PATH"]

            def invoke(argv, success=True):
                result = subprocess.run(prefix + [str(x) for x in argv], cwd=root, env=env,
                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
                transcript.append({"case": case, "argv": [str(x) for x in argv], "exit": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
                if success:
                    require(result.returncode == 0, f"{case}: {argv!r}: {result.stderr}")
                return result

            def output(argv):
                return invoke(argv).stdout.strip()

            def log():
                return deletions.read_bytes() if deletions.exists() else b""

            def write_json(path, value):
                path.write_text(json.dumps(value))
                if isolated:
                    os.chown(path, 65534, 65534)

            def kill_cleanup():
                marker.touch()
                result = invoke(reconcile, success=False)
                require(result.returncode != 0 and "(-9)" in result.stderr, case + ": missing actual Noodle SIGKILL")
                require(not (root / ".worktrees/probe").exists(), case + ": directory not removed")
                require(output([git, "rev-parse", "refs/heads/probe"]) == head, case + ": admitted branch lost")

            invoke([git, "init", "-b", "main"])
            invoke([git, "remote", "add", "origin", "https://github.com/ed3c/soodles.git"])
            (root / ".gitignore").write_text(".worktrees/\n.noodle/\n")
            invoke([git, "add", "."])
            commit = [git, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit"]
            invoke([*commit, "-m", "Local lock recovery fixture"])
            head, tree = output([git, "rev-parse", "HEAD"]), output([git, "rev-parse", "HEAD^{tree}"])
            invoke([binary, "worktree", "create", "probe"])
            claim = {"repository": "ed3c/soodles", "issue": 8, "pr": 1, "head": head, "tree": tree,
                "base_head": head, "run_id": 1, "run_attempt": 1, "worktree": "probe", "control_root": str(root),
                "verifier_sha256": json.loads(output([cli, "landing", "identity"]))["verifier_sha256"]}
            checkpoint = data / "checkpoint.json"
            write_json(checkpoint, {"schema": 1, "claim": claim, "phase": "awaiting_reconcile",
                "classification": None, "merge_sha": head, "issue_closed_at": "fixture-only",
                "writes_offered": ["merge", "close"]})
            reconcile = [cli, "landing", "reconcile", checkpoint, binary]
            kill_cleanup()
            if case in ("legacy_unknown", "consumed_release"):
                kill_cleanup()  # Changed path state permits this one attempt; old intent now has path=false.
                state = json.loads(checkpoint.read_text())
                require("cleanup_blocked" not in state, case + ": unexpected prior lock knowledge")
                before, before_log = checkpoint.read_bytes(), log()
                refused = invoke(reconcile, success=False)
                require(refused.returncode != 0 and "cleanup.observation" in refused.stderr,
                        case + ": unknown legacy state must not authorize unchanged retry")
                require(checkpoint.read_bytes() == before and log() == before_log, case + ": unchanged retry side effect")
            lock = Path(output([git, "rev-parse", "--path-format=absolute", "--git-path", "refs/heads/probe.lock"]))
            lock.touch()
            before_log = log()
            blocked = invoke(reconcile, success=False)
            # Accept the old post-deletion refusal for baseline comparison, then test actual resumption.
            require(blocked.returncode != 0 and ("cleanup.ref_lock" in blocked.stderr or "cleanup.branch" in blocked.stderr),
                    case + ": expected real lock refusal: " + blocked.stderr)
            new_contract = "cleanup.ref_lock" in blocked.stderr
            if new_contract:
                require(log() == before_log, case + ": blocked lock reached deletion owner")
                state = json.loads(checkpoint.read_text())
                require(state["cleanup_blocked"]["ref_lock"] == str(lock), case + ": wrong Git lock identity")
                before = checkpoint.read_bytes()
                refused = invoke(reconcile, success=False)
                require(refused.returncode != 0 and "cleanup.ref_lock" in refused.stderr, case + ": unchanged lock not refused")
                require(checkpoint.read_bytes() == before and log() == before_log and lock.exists(),
                        case + ": repeated lock readback changed checkpoint, deletion or lock")
            lock.unlink()  # Only the fixture creator removes its own planted lock.
            if case == "moved_after_block":
                invoke([*commit, "--allow-empty", "-m", "Planted moved branch"])
                invoke([git, "branch", "-f", "probe", "HEAD"])
                before, before_log = checkpoint.read_bytes(), log()
                refused = invoke(reconcile, success=False)
                require(refused.returncode != 0 and "cleanup.branch_head" in refused.stderr, case + ": wrong owner accepted")
                require(checkpoint.read_bytes() == before and log() == before_log, case + ": refusal had side effects")
                invoke([binary, "worktree", "cleanup", "probe"])
            elif case == "consumed_release":
                kill_cleanup()
                state = json.loads(checkpoint.read_text())
                require("cleanup_blocked" not in state, case + ": recovery capability not consumed before effect")
                before, before_log = checkpoint.read_bytes(), log()
                refused = invoke(reconcile, success=False)
                require(refused.returncode != 0 and "cleanup.observation" in refused.stderr, case + ": consumed recovery retried")
                require(checkpoint.read_bytes() == before and log() == before_log, case + ": unchanged retry changed state")
                invoke([binary, "worktree", "cleanup", "probe"])
            else:
                result = invoke(reconcile, success=False)
                require(result.returncode == 0, case + ": released lock still cannot resume: " + result.stderr)
                # Independent Git readback happens before trusting candidate JSON or checkpoint claims.
                require(not output([git, "branch", "--list", "probe"]), case + ": false success retained branch")
                require(not (root / ".worktrees/probe").exists(), case + ": false success retained directory")
                state = json.loads(checkpoint.read_text())
                require(json.loads(result.stdout)["classification"] == state["classification"] == "RESOLVED",
                        case + ": terminal classification absent")
                require(state["local"]["head"] == head and state["local"]["tree"] == tree, case + ": wrong local identity")
                require(state["writes_offered"] == ["merge", "close"] and "cleanup_blocked" not in state,
                        case + ": duplicated provider intent or unconsumed capability")
            require(not output([git, "branch", "--list", "probe"]), case + ": leftover branch")
            require(output([git, "worktree", "list", "--porcelain"]).count("worktree ") == 1, case + ": leftover registration")
            require(not output([git, "status", "--porcelain", "--untracked-files=all"]), case + ": source residue")
            cases.append({"case": case, "control": "passed", "zero_residue": True,
                          "injected_noodle_signal": "SIGKILL", "lock_refusal_before_deletion": new_contract})
    return {"scope": "local lock recovery; synthetic provider fields; no landing authority", "provider_requests": 0,
            "isolated_child_uid": 65534 if isolated else None, "worktree_owner": "Noodle",
            "binary_sha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
            "authorizes_landing": False, "zero_residue": True, "cases": cases, "controls": transcript}


if __name__ == "__main__":
    try:
        print(json.dumps(lock_recovery_probe(sys.argv[1], sys.argv[2], isolated="--isolated" in sys.argv[3:]), indent=2))
    except AssertionError as error:
        print(json.dumps({"verdict": "NOT VERIFIED", "reason": str(error), "authorizes_landing": False}))
        sys.exit(1)
