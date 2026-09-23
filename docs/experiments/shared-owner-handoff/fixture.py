import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
import issue_atom as atom
class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.root = self.outer / "project"
        subprocess.run(["git", "init", "-b", "main", self.root], check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Atom Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "atom@example.invalid"],
                       cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(".noodle/\n.worktrees/\n.noodle.toml\n")
        for name in atom.supervisor_admission.BUNDLE_PATHS + (
                ".agents/skills/execute/SKILL.md", ".agents/skills/schedule/SKILL.md"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(atom.__file__).parent / name).read_bytes())
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin",
                        "https://github.com/ed3c/soodles.git"], cwd=self.root, check=True)
        self.base = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                            cwd=self.root, text=True).strip()
        self.binary = self.outer / "carrier"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary),
                    "sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        self.owner_root = self.outer / "external-owner"
        hashes = {}
        for name in atom.OWNER_FILES:
            target = self.owner_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(atom.__file__).parent / name).read_bytes())
            hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.owner_spec = {"path": str(self.owner_root / "soodles.py"),
                           "sha256": hashes["soodles.py"],
                           "verifier_sha256": atom.digest_bytes(json.dumps(
                               hashes, sort_keys=True, separators=(",", ":")).encode())}
        contract = {
            "schema": 3, "trigger": "fixture", "source": "fixture",
            "owner": "fixture owner", "changes": ["fixture"],
            "write_paths": ["allowed.py"], "behavior": ["fixture"],
            "defect_controls": ["fixture"], "non_cases": ["fixture"],
            "dependencies": [], "acceptance": "fixture", "delivery": "fixture",
            "reconciliation": "fixture", "feature_scope": "fixture",
            "required_paths": ["allowed.py"], "evidence_manifest": "allowed.py",
            "base_head": self.base,
            "frozen_paths": [{"path": "allowed.py", "revision": "head",
                              "sha256": "a" * 64}],
        }
        body = ("<!-- soodles:execution-v1 -->\n```json\n"
                + json.dumps(contract) + "\n```\n"
                "<!-- /soodles:execution-v1 -->")
        self.authorization = {
            "schema_version": 2, "owner": "external-supervisor",
            "repository": "ed3c/soodles", "control_root": str(self.root),
            "base_head": self.base, "task": "Execute exact Issue.",
            "host_config_sha256": None,
            "issue": {"title": "Fixture atom", "body": body},
            "noodle": dict(identity),
            "landing_owner": self.owner_spec,
            "carrier": {"platform": __import__("platform").system().lower() + "_"
                                    + __import__("platform").machine().lower(),
                        "codex": {**identity, "model": "fixture-model",
                                  "argv": ["exec", "--skip-git-repo-check", "--json", "--model", "fixture-model"]}},
            "workflow": {"path": ".github/workflows/runtime.yml",
                         "job": "runtime-evidence",
                         "step": "Canonical acceptance on the exact candidate head"},
        }
        self.path = self.outer / "authorization.json"
        self.path.write_text(json.dumps(self.authorization))
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.env = {"SOODLES_AUTHORIZATION_SHA256": self.digest, "GH_TOKEN": "fixture",
                    "NOODLES_TOKEN_COMMAND": "printf fixture-installation-token"}

    def ready_issue(self, provider):
        body = self.authorization["issue"]["body"].rstrip() + "\n\n" + atom.marker(self.digest) + "\n"
        provider.value = {"number": 131, "title": self.authorization["issue"]["title"],
                          "body": body, "state": "open",
                          "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131",
                          "url": "https://api.github.com/repos/ed3c/soodles/issues/131"}

    def startup_fixture(self):
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        envelope, digest = atom.create_envelope(self.authorization, provider.value,
                                               provider.value["body"], paths["envelope"], environ=self.env)
        runtime = self.root / ".noodle"
        runtime.mkdir()
        atom.save_json(runtime / "state.snapshot.json", {"state": {"orders": {}}, "effect_ledger": []})
        state = {"phase": "execution", "authorization_sha256": self.digest, "envelope_sha256": digest,
                 "admission_sha256": atom.digest_file(paths["envelope"].parent / "prepared.json")}
        return paths, state


class Provider:
    def __init__(self):
        self.token = "fixture-token"
        self.value = None
        self.create_calls = 0
        self.create_effect = True
        self.create_unknown = False
        self.merge_calls = 0

    def issues(self):
        return [] if self.value is None else [self.value]

    def issue(self, number):
        if self.value is None or self.value["number"] != number:
            return None
        return dict(self.value)

    def create_issue(self, title, body):
        self.create_calls += 1
        if self.create_effect:
            self.value = {"number": 131, "title": title, "body": body,
                          "state": "open", "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131",
                          "url": "https://api.github.com/repos/ed3c/soodles/issues/131"}
        if self.create_unknown:
            raise atom.MutationUnknown("lost response")
        return self.value

    def merge(self, number, head, method):
        self.merge_calls += 1
        return {"merged": True}

    def close_issue(self, number, state_reason):
        self.value["state"] = "closed"
        return self.value

