#!/usr/bin/env python3
"""Archive one sealed experiment case; integrity only, never scoring/promotion."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys


def plain(path):
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError("symlink refused: " + str(item))
    if path.name == "auth.json":
        raise ValueError("credential filename refused: " + str(path))


def digest(path):
    plain(path)
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def walk(path, exclude_git=False):
    plain(path)
    mode = path.stat().st_mode
    if stat.S_ISREG(mode):
        return [path], []
    if not stat.S_ISDIR(mode):
        raise ValueError("non-regular file refused: " + str(path))
    files, directories = [], [path]
    for child in sorted(path.iterdir()):
        plain(child)
        if exclude_git and child.name == ".git":
            continue
        found, dirs = walk(child, exclude_git)
        files.extend(found)
        directories.extend(dirs)
    return files, directories


def inventory(root):
    files, dirs = walk(root)
    return {"files": {str(p.relative_to(root)): {"sha256": digest(p), "bytes": p.stat().st_size}
                      for p in files if p != root / "inventory.json"},
            "directories": sorted(str(p.relative_to(root)) for p in dirs)}


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--verify":
        root = Path(sys.argv[2]).absolute()
        if digest(root / "inventory.json") != sys.argv[3]:
            raise ValueError("inventory pin mismatch")
        if inventory(root) != json.loads((root / "inventory.json").read_text()):
            raise ValueError("archive membership/bytes mismatch")
        print(json.dumps({"verified": str(root), "scope": "archive integrity only"}))
        return
    if len(sys.argv) != 3:
        raise ValueError("usage: archive_case.py CASE_DIR FRESH_DEST | --verify DEST INVENTORY_SHA256")
    case, dest = (Path(x).absolute() for x in sys.argv[1:])
    for path in (case, dest.parent):
        plain(path)
    plain(case / "case.json"); plain(case / "descriptor.json")
    spec = json.loads((case / "case.json").read_text())
    descriptor = json.loads((case / "descriptor.json").read_text())
    captured = Path(spec["run_root"])
    if not captured.is_absolute() or "captured_root" in descriptor or "archived_root" in descriptor:
        raise ValueError("expected original absolute case descriptor")
    workspace = Path(descriptor["workspace"]["path"]).parent
    if workspace != captured / "output/workspace" or Path(descriptor["drive"]["path"]) != case / "public/drive.py":
        raise ValueError("unexpected experiment layout")
    if digest(captured / "control/drive.py") != descriptor["drive"]["sha256"]:
        raise ValueError("captured driver differs from selected public driver")
    pairs = [(case / n, dest / n) for n in ("case.json", "result.json")]
    pairs.append((case / "descriptor.json", dest / "descriptor.original.json"))
    dirs = []
    for relative in ("raw", "binding.json", "control/drive.py", "output/workspace"):
        files, found = walk(captured / relative, exclude_git=True)
        pairs.extend((p, dest / "run" / p.relative_to(captured)) for p in files)
        dirs.extend(dest / "run" / p.relative_to(captured) for p in found)
    if digest(Path(descriptor["drive"]["path"])) != descriptor["drive"]["sha256"]:
        raise ValueError("original driver pin changed")
    for pin in [*descriptor["capture"].values(), descriptor["workspace"], descriptor["before"]]:
        path = Path(pin["path"])
        if path not in {p for p, _ in pairs} or digest(path) != pin["sha256"]:
            raise ValueError("descriptor pin missing/changed: " + str(path))
    if dest == captured or captured in dest.parents or dest == case or case in dest.parents:
        raise ValueError("archive must be outside captured inputs")
    dest.mkdir()  # Fresh only; a partial failed copy is retained for diagnosis.
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    for source, target in pairs:
        plain(source); target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target, follow_symlinks=False)
        if digest(source) != digest(target):
            raise ValueError("copy mismatch: " + str(source))
    descriptor["drive"]["path"] = str(captured / "control/drive.py")
    descriptor.update(captured_root=str(captured), archived_root=str(dest / "run"))
    write(dest / "descriptor.json", descriptor)
    write(dest / "inventory.json", inventory(dest))
    print(json.dumps({"archive": str(dest), "inventory_sha256": digest(dest / "inventory.json"),
                      "scope": "archive integrity only; driver path relocated to captured byte-identical copy; all other original pin paths unchanged; .git excluded"}))


if __name__ == "__main__":
    main()
