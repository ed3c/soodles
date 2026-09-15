"""Real local Noodle crash controls; provider closure fields are explicitly fixture data."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from soodles import ROOT, Refusal, clean_env


def cleanup_recovery_probe(binary, cli_root=ROOT):
    binary = str(Path(binary).resolve())
    cli = str(Path(cli_root).resolve() / "soodles")
    git = shutil.which("git")
    transcript, cases = [], []

    def require(condition, detail):
        if not condition:
            raise Refusal("cleanup oracle: " + detail)

    with tempfile.TemporaryDirectory(prefix="soodles-cleanup-oracle-") as directory:
        area = Path(directory)
        for case in ("resume", "moved_branch", "foreign_checkout", "unchanged_attempt", "legacy_checkpoint"):
            home = area / case
            root, shim = home / "repo", home / "shim"
            root.mkdir(parents=True)
            shim.mkdir()
            marker, deletions = home / "kill-on-delete", home / "deletions"
            script = shim / "git"
            # Only this disposable repo is injected. Fetch is real Git against local fixture data.
            # No GitHub network request, credentials, or provider mutation occurs in this oracle.
            script.write_text(
                "#!" + sys.executable + "\nimport os,sys,signal\nfrom pathlib import Path\n"
                f"root={str(root)!r}\nmarker=Path({str(marker)!r})\n"
                f"git={git!r}\nargs=sys.argv[1:]\n"
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
            env = clean_env()
            env["PATH"] = str(shim) + os.pathsep + env["PATH"]

            def invoke(argv, success=True):
                result = subprocess.run([str(x) for x in argv], cwd=root, env=env, stdin=subprocess.DEVNULL,
                                        capture_output=True, text=True, timeout=30)
                transcript.append({"case": case, "argv": [str(x) for x in argv], "exit": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
                if success:
                    require(result.returncode == 0, f"{case}: {argv!r}: {result.stderr}")
                return result

            def output(argv):
                return invoke(argv).stdout.strip()

            def deletion_log():
                return deletions.read_text() if deletions.exists() else ""

            invoke(["git", "init", "-b", "main"])
            invoke(["git", "remote", "add", "origin", "https://github.com/ed3c/soodles.git"])
            (root / ".gitignore").write_text(".worktrees/\n.noodle/\n")
            invoke(["git", "add", "."])
            commit = ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit"]
            invoke([*commit, "-m", "Local recovery fixture"])
            head, tree = output(["git", "rev-parse", "HEAD"]), output(["git", "rev-parse", "HEAD^{tree}"])
            invoke([binary, "worktree", "create", "probe"])
            claim = {"repository": "ed3c/soodles", "issue": 1, "pr": 2, "head": head, "tree": tree,
                     "base_head": head, "run_id": 1, "run_attempt": 1, "worktree": "probe",
                     "control_root": str(root), "verifier_sha256": json.loads(output([cli, "landing", "identity"]))["verifier_sha256"]}
            checkpoint = home / "checkpoint.json"
            checkpoint.write_text(json.dumps({"schema": 1, "claim": claim, "phase": "awaiting_reconcile",
                "classification": None, "merge_sha": head, "issue_closed_at": "fixture-only",
                "writes_offered": ["merge", "close"]}))
            reconcile = [cli, "landing", "reconcile", checkpoint, binary]
            marker.touch()
            interrupted = invoke(reconcile, success=False)
            require(interrupted.returncode != 0 and "(-9)" in interrupted.stderr, case + ": missing real Noodle SIGKILL")
            require(not (root / ".worktrees/probe").exists() and output(["git", "rev-parse", "refs/heads/probe"]) == head,
                    case + ": interruption did not leave the expected path/branch gap")
            state = json.loads(checkpoint.read_text())
            require(state["phase"] == "reconciling" and state["classification"] is None, case + ": incorrect crash checkpoint")
            rejection = None
            if case == "legacy_checkpoint":
                state.pop("cleanup_intent", None)
                checkpoint.write_text(json.dumps(state))
            if case == "moved_branch":
                invoke([*commit, "--allow-empty", "-m", "Planted foreign head"])
                invoke(["git", "branch", "-f", "probe", "HEAD"])
                rejection = "cleanup.branch_head"
            if case == "foreign_checkout":
                # Deliberately plant the forbidden checkout; this is not a managed production worktree.
                invoke(["git", "worktree", "add", home / "foreign", "probe"])
                rejection = "cleanup.checkout"
            if case == "unchanged_attempt":
                marker.touch()
                second = invoke(reconcile, success=False)
                require(second.returncode != 0 and "(-9)" in second.stderr, "changed gap must reach Noodle once")
                rejection = "cleanup.observation"
            if rejection:
                before, before_deletions = checkpoint.read_bytes(), deletion_log()
                before_head = output(["git", "rev-parse", "refs/heads/probe"])
                refused = invoke(reconcile, success=False)
                require(refused.returncode != 0 and rejection in refused.stderr, f"{case}: expected {rejection}: {refused.stderr}")
                require(deletion_log() == before_deletions and checkpoint.read_bytes() == before,
                        case + ": refusal altered deletion or checkpoint state")
                require(output(["git", "rev-parse", "refs/heads/probe"]) == before_head, case + ": refusal deleted or moved branch")
                if case == "foreign_checkout":
                    invoke(["git", "worktree", "remove", home / "foreign"])
                if case == "unchanged_attempt":
                    # A changed executable capability, not an unchanged retry.
                    script.write_text(script.read_text() + "\n# repaired fixture capability\n")
            if case not in ("moved_branch", "foreign_checkout"):
                result = json.loads(invoke(reconcile).stdout)
                require(result["classification"] == "RESOLVED" and result["local"]["head"] == head, case + ": incorrect resolution")
                require(result["writes_offered"] == ["merge", "close"], case + ": repeated provider intent")
            else:
                # Remove the negative fixture through the actual owner after its preservation was checked.
                invoke([binary, "worktree", "cleanup", "probe"])
            require(not output(["git", "branch", "--list", "probe"]), case + ": leftover branch")
            require(output(["git", "worktree", "list", "--porcelain"]).count("worktree ") == 1, case + ": leftover registration")
            require(not output(["git", "status", "--porcelain", "--untracked-files=all"]), case + ": source residue")
            cases.append({"case": case, "injected_noodle_signal": "SIGKILL", "control": "passed", "zero_residue": True})
    return {"scope": "local runtime crash recovery; provider closure fields are fixture data", "provider_requests": 0,
            "worktree_owner": "Noodle", "zero_residue": True, "cases": cases, "controls": transcript}
