"""Run the five prepared diagnostic builds, restoring known-good blink in finally."""
import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stand", type=Path, required=True)
    args = parser.parse_args()
    stand = args.stand.resolve()
    rc = 0
    try:
        for variant in ("gcc13", "gcc14", "cloudbear14", "gcc14-ram", "cloudbear14-ram"):
            rc = subprocess.call([sys.executable, "-B", str(HERE / "run.py"), "flash",
                                  "--stand", str(stand), "--build",
                                  str(ROOT / "build" / ("k1921-errata-" + variant))], cwd=ROOT)
            if rc:
                break
    finally:
        restore = subprocess.call([sys.executable, "-B", str(HERE.parent / "k1921vg015-poc/run.py"),
                                   "flash", "--stand", str(stand)], cwd=ROOT)
        if restore:
            print("ERROR: blink restoration failed; inspect the PoC run logs")
            rc = restore
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
