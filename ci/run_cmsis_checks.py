"""Build both BlackPill CMSIS boards and prepare their scenarios without hardware."""
import argparse
import time
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-jobs", type=int, choices=(1, 2, 4), default=2,
                        help="parallel offline CTest processes; hardware is never run")
    args = parser.parse_args()
    out = ROOT / "build/ci-reports/cmsis"
    out.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("STM32_GDBTEST_", "HWTEST_"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    summary = []
    timings = []
    total_started = time.perf_counter()

    def run(command, name):
        started = time.perf_counter()
        record = {"step": name, "status": "ERROR"}
        try:
            with (out / (name + ".log")).open("wb") as log:
                subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                               stderr=subprocess.STDOUT, check=True, timeout=300)
            record["status"] = "PASS"
        finally:
            record["wall_s"] = round(time.perf_counter() - started, 3)
            timings.append(record)
            (out / "timings.json").write_text(json.dumps({
                "prepare_jobs": args.prepare_jobs, "steps": timings,
                "elapsed_s": round(time.perf_counter() - total_started, 3)
            }, indent=2) + "\n")

    for board in ("F411CE", "F401CC"):
        record = {"board": board, "status": "ERROR"}
        try:
            for config in ("Debug", "Release", "HIL"):
                preset = config + "_" + board
                run(["cmake", "--preset", preset, "-DSTM32_GDBTEST_STAND="], preset + "-configure")
                run(["cmake", "--build", "--preset", preset], preset + "-build")
            build = ROOT / "build" / ("HIL_" + board)
            session = json.loads((build / "hwtest/session.json").read_text())
            if session["stand"]:
                raise ValueError("Offline session must not select a hardware stand")
            listing = json.loads(subprocess.check_output(
                ["ctest", "--test-dir", str(build), "-L", "host", "--show-only=json-v1"],
                cwd=ROOT, env=env, text=True, timeout=30))["tests"]
            names = {test["name"] for test in listing}
            if len(listing) != 15 or sum(name.startswith("prepare.") for name in names) != 14:
                raise ValueError("Expected fourteen prepare tests and traceability")
            for test in listing:
                if test["name"].startswith("prepare."):
                    if "--prepare-only" not in test["command"]:
                        raise ValueError("Prepare command may access hardware")
                elif test["name"] != "host.traceability":
                    raise ValueError("Unexpected host test")
            junit = out / (board + "-junit.xml")
            junit.unlink(missing_ok=True)
            run(["ctest", "--test-dir", str(build), "-L", "host", "-j", str(args.prepare_jobs), "--no-tests=error",
                 "--output-on-failure", "--output-junit", str(junit)], board + "-tests")
            cases = ET.parse(junit).getroot().findall(".//testcase")
            if len(cases) != 15 or {c.attrib["name"] for c in cases} != names or any(
                    c.find(tag) is not None for c in cases for tag in ("skipped", "error", "failure")):
                raise ValueError("Incomplete or unsuccessful JUnit")
            manifest = json.loads(Path(session["build_manifest"]).read_text())
            record.update(status="PASS", tests=len(cases), elf_sha256=manifest["elf_sha256"])
        except (OSError, ValueError, KeyError, subprocess.SubprocessError, ET.ParseError) as error:
            record["error"] = str(error)
        summary.append(record)
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(record["status"], board, flush=True)
    record = {"board": "native-adc", "status": "ERROR"}
    try:
        build = ROOT / "build/native-adc"
        run(["cmake", "-S", str(ROOT / "hil/tests/native"), "-B", str(build),
             "-G", "Ninja"], "native-configure")
        run(["cmake", "--build", str(build)], "native-build")
        junit = out / "native-junit.xml"
        junit.unlink(missing_ok=True)
        run(["ctest", "--test-dir", str(build), "--no-tests=error",
             "--output-on-failure", "--output-junit", str(junit)], "native-tests")
        cases = ET.parse(junit).getroot().findall(".//testcase")
        if len(cases) != 1 or cases[0].attrib["name"] != "adc.units" or any(
                cases[0].find(tag) is not None for tag in ("failure", "error", "skipped")):
            raise ValueError("Incomplete native ADC result")
        record.update(status="PASS", tests=1)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, ET.ParseError) as error:
        record["error"] = str(error)
    summary.append(record)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(record["status"], "native-adc", flush=True)
    return int(any(record["status"] != "PASS" for record in summary))


if __name__ == "__main__":
    raise SystemExit(main())
