"""Compare offline CTest parallelism on an already built HIL profile; no hardware."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", choices=("F401CC", "F411CE"), default="F401CC")
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=3)
    args = parser.parse_args()
    build = ROOT / "build" / ("HIL_" + args.board)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("STM32_GDBTEST_", "HWTEST_"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    listing = json.loads(subprocess.check_output(
        ["ctest", "--test-dir", str(build), "-L", "^host$", "--show-only=json-v1"],
        env=env, text=True, timeout=30))["tests"]
    names = {test["name"] for test in listing}
    if len(listing) != 15 or len(names) != 15:
        raise ValueError("Expected fourteen prepare tests and traceability")
    for test in listing:
        command = test["command"]
        if test["name"].startswith("prepare.") and "--prepare-only" in command:
            continue
        if test["name"] == "host.traceability" and "trace" in command:
            continue
        raise ValueError("Unexpected command in offline benchmark")
    out = ROOT / "build/test-timing" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    out.mkdir(parents=True)
    rows = []
    summary = {"board": args.board, "runs": rows, "status": "ERROR"}
    try:
        for repeat in range(args.repeats):
            # Rotate order to reduce systematic first-run/cache bias.
            order = (1, 2, 4)
            for jobs in order[repeat % 3:] + order[:repeat % 3]:
                label = f"r{repeat}-j{jobs}"
                junit = out / (label + ".xml")
                started = time.perf_counter()
                with (out / (label + ".log")).open("wb") as log:
                    subprocess.run(["ctest", "--test-dir", str(build), "-L", "^host$",
                        "-j", str(jobs), "--no-tests=error", "--output-on-failure",
                        "--output-junit", str(junit)], env=env, stdout=log,
                        stderr=subprocess.STDOUT, check=True, timeout=180)
                elapsed = time.perf_counter() - started
                cases = ET.parse(junit).getroot().findall(".//testcase")
                if len(cases) != 15 or {c.attrib["name"] for c in cases} != names or any(
                        c.find(tag) is not None for c in cases for tag in ("failure", "error", "skipped")):
                    raise ValueError("Incomplete or unsuccessful benchmark result")
                row = {"repeat": repeat, "jobs": jobs, "wall_s": round(elapsed, 3)}
                rows.append(row)
                print(row, flush=True)
        summary["medians_s"] = {str(j): statistics.median(r["wall_s"] for r in rows if r["jobs"] == j)
                                for j in (1, 2, 4)}
        summary["status"] = "PASS"
    finally:
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(out / "summary.json", flush=True)


if __name__ == "__main__":
    main()
