"""Offline historical capture integrity/replay, not a fresh model or adoption test."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

INDEX = Path(__file__).resolve().parents[1] / "docs/experiments/local-session-routing/evidence-index.json"
PINS = {
    "archive_case.py": "73d03c242c7a0b907e8dec022cf471f25a77f145396d9e2f49f43d3de589690d",
    "replay_archive.py": "eacf0ed4ba769165598a7d0ce09d511769c605d62ae295afb57f1884590e7051",
    "oracle-r02.py": "701ada7eb3f22b4a7639df423573f1fb298c12620e8ff8ec1f8f56b04d38f8fd",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or any(p in ("", ".", "..", ".git", "auth.json") for p in name.split("/")):
        raise ValueError("unsafe archive/index path: " + name)
    return Path(*path.parts)


def safe_unpack(path, destination):
    seen, total = set(), 0
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            name = member.name.rstrip("/") if member.isdir() else member.name
            target = destination / relative(name)
            total += member.size
            if name in seen or len(seen) >= 5000 or member.size > 16 * 1024 * 1024 or total > 64 * 1024 * 1024:
                raise ValueError("duplicate or oversized archive member")
            seen.add(name)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile() and not member.sparse:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
            else:
                raise ValueError("link/special/sparse archive member refused")


class LocalRoutingEvidenceTests(unittest.TestCase):
    def test_required_archives_replay_identically(self):
        index = json.loads(INDEX.read_text())
        self.assertEqual(index["schema"], 1)
        self.assertEqual(set(index["tools"]), set(PINS))
        tools = {}
        for name, expected in PINS.items():
            pin = index["tools"][name]
            tools[name] = INDEX.parent / relative(pin["path"])
            self.assertEqual(pin["sha256"], expected)
            self.assertEqual(sha(tools[name]), expected)
        runs = index["required_runs"]
        self.assertTrue(runs)
        self.assertEqual(len({r["id"] for r in runs}), len(runs))
        with tempfile.TemporaryDirectory(prefix="routing-evidence-") as folder:
            base = Path(folder).resolve()
            for number, run in enumerate(runs):
                with self.subTest(run=run["id"]):
                    archive = INDEX.parent / relative(run["archive"])
                    self.assertEqual(sha(archive), run["archive_sha256"])
                    extracted, receipts = base / str(number), base / (str(number) + "-receipts")
                    extracted.mkdir()
                    safe_unpack(archive, extracted)
                    argv = [sys.executable, "-B", str(tools["replay_archive.py"]), str(extracted),
                            run["inventory_sha256"], str(tools["oracle-r02.py"]), str(receipts)]
                    result = subprocess.run(argv, capture_output=True, text=True, timeout=70)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    receipt = json.loads((receipts / "receipt.json").read_text())
                    for field in ("archive_integrity_before", "archive_integrity_after", "result_json_equal", "captured_identity_unchanged"):
                        self.assertIs(receipt[field], True)
                    self.assertEqual(json.loads((receipts / "stdout.json").read_text()), json.loads((extracted / "result.json").read_text()))
                    self.assertIs(receipt["authorizes_landing"], False)

    def test_fixed_comparison_replays_adoption(self):
        root = INDEX.parent
        analysis = root / "tools/analysis-r02.py"
        self.assertEqual(sha(analysis), "a60e38f920d6b5d9181219826f8f63fb4a05db689cd8311de1c447ffa4e1c664")
        index = json.loads(INDEX.read_text())
        archives = {run["id"]: run for run in index["required_runs"]}
        comparison = json.loads((root / "comparison.json").read_text())
        winner = json.loads((root / "confirmation/winner.json").read_text())
        self.assertIs(winner["search_stopped"], True)
        self.assertEqual(winner["round"], "r02")
        self.assertEqual(sha(root / "rounds/r02/AGENTS.md"), winner["instruction"]["sha256"])
        def pin(path):
            return {"path": str(path), "sha256": sha(path)}
        with tempfile.TemporaryDirectory(prefix="routing-comparison-") as folder:
            temporary = Path(folder).resolve()
            manifest = {"schema": 1, "pins": {"protocol": pin(root / "protocol.md"),
                        "oracle": pin(root / "tools/oracle-r02.py"),
                        "harness": pin(root / "freeze.json")}, "runs": []}
            self.assertEqual(len(comparison["runs"]), 20)
            for row in comparison["runs"]:
                selected = archives[row["id"]]
                archive = root / relative(selected["archive"])
                self.assertEqual(sha(archive), selected["archive_sha256"])
                with tarfile.open(archive, "r:gz") as tar:
                    data = tar.extractfile("result.json").read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["result_sha256"])
                result = json.loads(data)
                self.assertEqual(result["stratum"], row["stratum"])
                path = temporary / (row["id"] + ".json")
                path.write_bytes(data)
                manifest["runs"].append({k: row[k] for k in ("split", "group", "arm", "stratum")} | {"result": pin(path)})
            path = temporary / "manifest.json"
            path.write_text(json.dumps(manifest))
            process = subprocess.run([sys.executable, "-B", str(analysis), str(path), sha(path)],
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result, json.loads((root / "decision.json").read_text()))
            self.assertIs(result["adopt"], True)
            self.assertIs(result["authorizes_landing"], False)

    def test_unsafe_tar_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            for number, (name, kind) in enumerate((("/absolute", tarfile.REGTYPE), ("../escape", tarfile.REGTYPE),
                    ("link", tarfile.SYMTYPE), ("hard", tarfile.LNKTYPE), ("fifo", tarfile.FIFOTYPE))):
                with self.subTest(name=name):
                    archive, output = base / (str(number) + ".tar.gz"), base / str(number)
                    output.mkdir()
                    with tarfile.open(archive, "w:gz") as tar:
                        info = tarfile.TarInfo(name)
                        info.type, info.linkname = kind, "outside"
                        tar.addfile(info, io.BytesIO())
                    with self.assertRaises(ValueError):
                        safe_unpack(archive, output)


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        INDEX = Path(sys.argv.pop(1)).absolute()
    unittest.main()
