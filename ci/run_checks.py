"""Build and prepare consumer profiles without starting a GDB server or using USB."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {"f030r8": 17, "f103c8": 22, "f401cc": 22, "f411ce": 22, "f429zi": 22}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=COUNTS, action="append")
    args = parser.parse_args()
    out = ROOT / "build/ci-reports"
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for key in list(env):
        if key.startswith(("STM32_GDBTEST_", "HWTEST_")):
            del env[key]
    env["TMPDIR"] = env["TMP"] = env["TEMP"] = str(out / "tmp")
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    summary = []

    def run(command, log, timeout=300):
        with log.open("wb") as stream:
            subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=timeout)

    for profile in args.profile or COUNTS:
        preset = f"ci-{profile}"
        build = ROOT / "build" / preset
        record = {"profile": profile, "status": "ERROR"}
        try:
            run(["cmake", "--preset", preset], out / f"{profile}-configure.log")
            run(["cmake", "--build", "--preset", preset, "--parallel", "4"],
                out / f"{profile}-build.log")
            session = json.loads((build / "hwtest/session.json").read_text())
            if session["stand"]:
                raise ValueError("CI session must not select a hardware stand")
            listing = subprocess.check_output(
                ["ctest", "--test-dir", str(build), "-L", "host", "--show-only=json-v1"],
                cwd=ROOT, env=env, text=True, timeout=30)
            tests = json.loads(listing)["tests"]
            expected = COUNTS[profile] + 3
            if len(tests) != expected or sum(t["name"].startswith("prepare.") for t in tests) != COUNTS[profile]:
                raise ValueError(f"Unexpected test inventory: expected {expected}, got {len(tests)}")
            for test in tests:
                if test["name"].startswith("prepare."):
                    if "--prepare-only" not in test["command"]:
                        raise ValueError("Prepare test lacks --prepare-only")
                elif test["name"] not in {"host.hwtest", "host.traceability", "host.profile_offline"}:
                    raise ValueError("Unexpected host test: " + test["name"])
            junit = out / f"{profile}-junit.xml"
            junit.unlink(missing_ok=True)
            run(["ctest", "--test-dir", str(build), "-L", "host", "-j", "1",
                 "--output-on-failure", "--no-tests=error", "--output-junit", str(junit)],
                out / f"{profile}-tests.log", timeout=600)
            cases = ET.parse(junit).getroot().findall(".//testcase")
            if len(cases) != expected or any(c.find("skipped") is not None or
                    c.find("failure") is not None or c.find("error") is not None for c in cases):
                raise ValueError("Incomplete or unsuccessful JUnit report")
            manifest = json.loads(Path(session["build_manifest"]).read_text())
            record.update(status="PASS", tests=len(cases), elf_sha256=manifest["elf_sha256"])
        except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
            record["error"] = str(error)
        summary.append(record)
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"{record['status']} {profile}", flush=True)
    # Independent CMSIS consumer: same pinned module, no parent YAML/HAL sources.
    record = {"profile": "minimal-consumer", "status": "ERROR"}
    try:
        source = ROOT / "examples/minimal-consumer"
        build = source / "build/ci"
        run(["cmake", "-S", str(source), "-B", str(build), "-G", "Ninja",
             "--toolchain", str(source / "cmake/arm-gcc.cmake"),
             "-DSTM32_GDBTEST_STAND="], out / "consumer-configure.log")
        run(["cmake", "--build", str(build)], out / "consumer-build.log")
        junit = out / "consumer-junit.xml"
        junit.unlink(missing_ok=True)
        run(["ctest", "--test-dir", str(build), "-L", "host", "--output-on-failure",
             "--no-tests=error", "--output-junit", str(junit)], out / "consumer-tests.log")
        cases = ET.parse(junit).getroot().findall(".//testcase")
        names = {"prepare.HW_CONSUMER_GPIO", "prepare.HW_CONSUMER_BLINK",
                 "host.traceability", "host.consumer_offline"}
        if len(cases) != 4 or {c.attrib["name"] for c in cases} != names or any(
                c.find(tag) is not None for c in cases for tag in ("skipped", "failure", "error")):
            raise ValueError("Incomplete CMSIS consumer result")
        record.update(status="PASS", tests=4)
    except (OSError, ValueError, subprocess.SubprocessError, ET.ParseError) as error:
        record["error"] = str(error)
    summary.append(record)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"{record['status']} minimal-consumer", flush=True)
    cmsis = subprocess.run([os.sys.executable, "-B", str(ROOT / "ci/run_cmsis_checks.py")],
                           cwd=ROOT, env=env, timeout=1200)
    return int(cmsis.returncode != 0 or any(item["status"] != "PASS" for item in summary))


if __name__ == "__main__":
    raise SystemExit(main())
