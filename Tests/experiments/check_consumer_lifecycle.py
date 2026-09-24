"""Explicit F411/OpenOCD experiment; restores the main application in finally."""
import argparse
import hashlib
import os
import subprocess
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def inventory(directory):
    return {p.relative_to(directory).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in directory.rglob("*") if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stand", required=True, type=Path)
    parser.add_argument("--consumer-root", type=Path, default=ROOT / "examples/minimal-consumer")
    parser.add_argument("--module-root", type=Path, default=ROOT)
    parser.add_argument("--ctest", action="store_true", help="Also exercise generated CTest HW registration")
    args = parser.parse_args()
    consumer_root, module_root = args.consumer_root.resolve(), args.module_root.resolve()
    if not all(path.is_relative_to(ROOT) for path in (consumer_root, module_root)):
        raise ValueError("Experiment copies must remain inside this repository")
    sys.path.insert(0, str(module_root))
    from stm32_gdbtest.build_manifest import digest, load_verified
    from stm32_gdbtest.collect import collect
    from stm32_gdbtest.openocd import load_stand
    from stm32_gdbtest.runner import local_directory, run
    import stm32_gdbtest.runner
    assert Path(stm32_gdbtest.runner.__file__).resolve() == module_root / "stm32_gdbtest/runner.py"

    stand_path = args.stand.resolve()
    stand = load_stand(stand_path)
    if stand["flash"] != "if-different":
        raise ValueError("Experiment needs if-different to restore the main firmware")
    consumer = json.loads((consumer_root / "build/debug/hwtest/session.json").read_text())
    original = json.loads((ROOT / "build/f411ce-debug-hwtest/hwtest/session.json").read_text())
    # Validate BOTH restore artifacts before any hardware access.
    for session in (consumer, original):
        load_verified(session["build_manifest"], digest(session["elf"]), session["profile"])
    directory = local_directory(consumer_root / "build/lifecycle", consumer_root)
    summary = dict(status="ERROR", consumer_elf=digest(consumer["elf"]),
                   original_elf=digest(original["elf"]), stages={})
    cases = collect(consumer["tests"])
    baseline = inventory(module_root / "stm32_gdbtest")
    infrastructure = {name: inventory(ROOT / "build" / name)
                      for name in ("hwtest-tmp", "probe-locks")}

    def execute(label, session, test, selected_stand=stand_path, timeout=None):
        session = dict(session, out=str(directory / label))
        existing = set(Path(session["out"]).glob("*/result.json"))
        rc = run(session, test, selected_stand, timeout=timeout, identity_policy="strict")
        reports = set(Path(session["out"]).glob("*/result.json")) - existing
        if len(reports) != 1:
            raise AssertionError("Expected exactly one report for " + label)
        path = reports.pop()
        report = json.loads(path.read_text())
        summary["stages"][label] = dict(status=report["status"], code=rc,
            flashed=report.get("flashed"), image_verified=report.get("image_verified"),
            teardown=report.get("teardown"), report=str(path.relative_to(consumer_root)))
        return rc, report, path.parent

    try:
        if args.ctest:
            env = os.environ.copy()
            env.update(STM32_GDBTEST_STAND=str(stand_path), STM32_GDBTEST_IDENTITY_POLICY="strict",
                       PYTHONDONTWRITEBYTECODE="1", TEMP=str(directory), TMP=str(directory))
            with (directory / "ctest.log").open("wb") as log:
                ctest = subprocess.run(["ctest", "--test-dir", str(consumer_root / "build/debug"),
                    "--output-on-failure"], cwd=consumer_root, env=env, timeout=90,
                    stdout=log, stderr=subprocess.STDOUT)
            summary["ctest_returncode"] = ctest.returncode
            assert ctest.returncode == 0, "Consumer CTest failed; see ctest.log"
        rc, report, _ = execute("consumer", consumer, cases[0])
        assert rc == 0 and report["image_verified"] and report["teardown"] == "reset_run", report
        # Local private copy: never modify the user's stand or expose its serial in Git.
        verify_stand = directory / "verify-only.toml"
        verify_stand.write_text("[probe]\n" + "\n".join(
            key + " = " + json.dumps("verify-only" if key == "flash" else value)
            for key, value in stand.items()) + "\n", encoding="utf-8")
        rc, report, _ = execute("verify_only", consumer, cases[0], verify_stand)
        assert rc == 0 and report["flashed"] is False and report["image_verified"], report
        injected = directory / "timeout_case.py"
        injected.write_text('''import json, os, time
from pathlib import Path

def stall(target):
    target.reach("app_loop")
    request = json.loads(Path(os.environ["STM32_GDBTEST_RUN"]).read_text())
    Path(request["result"]).with_name("stall-entered.txt").write_text("at app_loop")
    time.sleep(60)
''', encoding="utf-8")
        timeout_test = dict(cases[0], id="HW_CONSUMER_TIMEOUT", path=str(injected), function="stall")
        rc, report, run_dir = execute("timeout", consumer, timeout_test, verify_stand, timeout=5)
        assert rc == 2 and "TimeoutExpired" in report.get("error", ""), report
        assert (run_dir / "stall-entered.txt").exists(), "Timeout happened before reaching the test"
        assert report.get("teardown") == "reset_run (host recovery)", report
        rc, report, _ = execute("after_recovery", consumer, cases[0], verify_stand)
        assert rc == 0 and report["flashed"] is False, report
        summary["module_unchanged"] = inventory(module_root / "stm32_gdbtest") == baseline
        summary["parent_runtime_dirs_unchanged"] = all(
            inventory(ROOT / "build" / name) == before for name, before in infrastructure.items())
        assert summary["module_unchanged"] and summary["parent_runtime_dirs_unchanged"]
        summary["status"] = "PASS"
    finally:
        try:
            original_cases = {case["id"]: case for case in collect(original["tests"])}
            for identifier in ("HW_BOOT", "HW_BLINK"):
                rc, report, _ = execute("restore_" + identifier, original, original_cases[identifier])
                if rc != 0 or report.get("teardown") != "reset_run":
                    summary["status"] = "ERROR"
                    raise RuntimeError("Original firmware restore/check failed: " + identifier)
        except BaseException:
            summary["status"] = "ERROR"
            raise
        finally:
            (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
