"""PoC evidence only; not the module's production build-manifest schema."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_regions(sections, image_size):
    regions = []
    for match in re.finditer(r"(?m)^\s*\d+\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)[^\n]*\n([^\n]+)", sections):
        name, size, vma, lma, flags = match.groups()
        if not {"CONTENTS", "ALLOC", "LOAD"} <= {f.strip() for f in flags.split(",")}:
            continue
        size, address = int(size, 16), int(lma, 16)
        offset = address - 0x80000000
        if size <= 0 or offset < 0 or offset + size > image_size or offset + size > 1024 * 1024:
            raise ValueError("Load section outside documented Flash: " + name)
        regions.append(dict(name=name, address=address, size=size, offset=offset))
    regions.sort(key=lambda r: r["address"])
    if not regions or regions[0]["address"] != 0x80000000:
        raise ValueError("Expected Flash entry region")
    if any(a["address"] + a["size"] > b["address"] for a, b in zip(regions, regions[1:])):
        raise ValueError("Overlapping Flash load regions")
    return regions


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--elf", type=Path, required=True)
    p.add_argument("--sdk", type=Path, required=True)
    p.add_argument("--compiler", type=Path, required=True)
    p.add_argument("--objdump", type=Path, required=True)
    a = p.parse_args()
    sources = {"sdk/" + f.relative_to(a.sdk).as_posix(): digest(f)
               for f in a.sdk.rglob("*") if f.is_file()}
    own = Path(__file__).resolve().parent
    sources.update({"poc/" + f.relative_to(own).as_posix(): digest(f)
                    for f in own.rglob("*") if f.is_file() and f.suffix in (".cpp", ".cmake", ".txt")})
    sections = subprocess.check_output([str(a.objdump), "-h", str(a.elf)], text=True)
    regions = load_regions(sections, a.elf.with_suffix(".bin").stat().st_size)
    report = dict(schema="k1921-poc-1", elf_sha256=digest(a.elf), load_regions=regions,
                  bin_sha256=digest(a.elf.with_suffix(".bin")), inputs=sources,
                  compiler_sha256=digest(a.compiler),
                  compiler_version=subprocess.check_output([str(a.compiler), "-dumpfullversion"], text=True).strip(),
                  limitations="Post-link source snapshot, not compilation provenance; no concurrent edits; full SDK inventory")
    (a.elf.parent / "poc-manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
