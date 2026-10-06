"""Save linked disassembly and independently demonstrate compiler workaround support."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    if not build.is_relative_to(ROOT / "build"):
        raise ValueError("Output must remain in project build/")
    cache = {}
    for line in (build / "CMakeCache.txt").read_text().splitlines():
        if "=" in line and ":" in line and not line.startswith(("//", "#")):
            key, value = line.split("=", 1)
            cache[key.split(":", 1)[0]] = value
    manifest = json.loads((build / "poc-manifest.json").read_text())
    bindir = Path(cache["RISCV_TOOLCHAIN_ROOT"]) / "bin"
    prefix = cache["RISCV_PREFIX"]
    objdump = bindir / (prefix + "-objdump.exe")
    compiler = bindir / (prefix + "-gcc.exe")
    dis = subprocess.check_output([str(objdump), "-dC", str(build / "k1921-errata.elf")], text=True)
    (build / "linked.dis").write_text(dis)
    source = build / "compiler-fix-probe.c"
    source.write_text("float divide_probe(const float *p, float x) { return x / *p; }\n")
    evidence = dict(library_sha256=manifest["library_sha256"], table_address=manifest["table_address"], probes={})
    for mode in ("off", "on"):
        output = build / ("compiler-fix-" + mode + ".s")
        command = [str(compiler), "-march=" + manifest["arch"], "-mabi=ilp32f",
                   "-O2", "-S", str(source), "-o", str(output)]
        if mode == "on":
            command.append("-mfix-cloudbear-0001")
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        evidence["probes"][mode] = dict(returncode=result.returncode, stderr=result.stderr,
                                         assembly=output.read_text() if result.returncode == 0 else None)
    (build / "inspection.json").write_text(json.dumps(evidence, indent=2))
    print(build / "inspection.json")


if __name__ == "__main__":
    main()
