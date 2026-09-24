"""Prepare a standalone source snapshot inside build; no Git init, network or push."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "build/module-export/stm32-gdbtest")
    args = parser.parse_args()
    out = args.out.resolve()
    build = (ROOT / "build").resolve()
    if out == build or not out.is_relative_to(build):
        raise ValueError("Export must be a new directory strictly below repository build")
    if out.exists():
        raise FileExistsError("Refusing to overwrite export: " + str(out))
    tracked = set(subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                                         cwd=ROOT, text=True).splitlines())
    mapping = {}
    prefixes = ("stm32_gdbtest/", "Tests/host/", "Tests/fixtures/", "examples/minimal-consumer/")
    for name in sorted(tracked):
        if name.startswith(prefixes):
            if "__pycache__" in name or "/build/" in name or name.endswith((".pyc", ".local.toml", "CMakeUserPresets.json")):
                continue
            path = ROOT / name
            if not path.is_file():
                raise FileNotFoundError(name)
            mapping[name] = path
        elif name.startswith("distribution/stm32-gdbtest/"):
            mapping[name.removeprefix("distribution/stm32-gdbtest/")] = ROOT / name
    # Templates intentionally override the consumer README inherited from the demo repository.
    for path in (ROOT / "distribution/stm32-gdbtest").rglob("*"):
        if path.is_file():
            mapping[path.relative_to(ROOT / "distribution/stm32-gdbtest").as_posix()] = path
    mapping["LICENSE"] = ROOT / "LICENSE"
    mapping["examples/stands/stlink.example.toml"] = ROOT / "Tests/stands/blackpill.example.toml"
    expected = {"README.md", "CHANGELOG.md", "TODO.md", "AGENTS.md", "LICENSE",
                "stm32_gdbtest/__init__.py", "docs/TEST_AUTHORING.md"}
    if not expected <= mapping.keys():
        raise ValueError("Incomplete export file list")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    out.mkdir(parents=True)
    manifest = dict(source_commit=head, source_worktree_dirty=dirty, files=[])
    for name, source in sorted(mapping.items()):
        destination = out / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        manifest["files"].append(dict(path=name, sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    (out / "EXPORT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "SOURCE.md").write_text(
        "# Происхождение\n\nНачальный снимок из "
        "https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill\n\n"
        + "Базовый commit: `" + head + "`.\n"
        + "Незакоммиченные изменения при экспорте: " + str(dirty) + ".\n"
        + "Точный состав фиксирует EXPORT_MANIFEST.json; это снимок, не перенос Git-истории.\n"
        + "MIT License и исходное авторство сохранены. HAL/CMSIS/Cube и инструменты не включены.\n",
        encoding="utf-8")
    print(json.dumps(dict(out=str(out), files=len(mapping), source_commit=head, dirty=dirty)))


if __name__ == "__main__":
    main()
