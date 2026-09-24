"""Bounded, read-only live Sleep observation after check-hw. No reset/halt/flash."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "modules/stm32-gdbtest"
sys.path.insert(0, str(MODULE_ROOT))
from stm32_gdbtest.openocd import load_stand, server_command
from stm32_gdbtest.processes import FLAGS, probe_lock
from stm32_gdbtest.profile import load_profile
from stm32_gdbtest.runner import local_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--identity-policy", choices=("warn", "strict"),
                        default=os.environ.get("STM32_GDBTEST_IDENTITY_POLICY", "warn"))
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--interval-ms", type=int, default=37)
    parser.add_argument("--out", type=Path, default=ROOT / "build/sleep-observation")
    args = parser.parse_args()
    if args.identity_policy not in ("warn", "strict"):
        parser.error("Identity policy must be warn or strict")
    if not 5 <= args.samples <= 100 or not 10 <= args.interval_ms <= 500:
        parser.error("samples must be 5..100; interval-ms must be 10..500")
    out = local_directory(args.out, ROOT)
    env = os.environ.copy()
    env.update(TEMP=str(local_directory(ROOT / "build/hwtest-tmp", ROOT)), TMP=str(ROOT / "build/hwtest-tmp"))
    session = json.loads(args.session.read_text(encoding="utf-8"))
    profile = load_profile(session["profile"])
    stand = load_stand(session["stand"])
    nm = Path(session["gdb"]).with_name("arm-none-eabi-nm.exe")
    symbols = subprocess.run([str(nm), "-n", session["elf"]], capture_output=True,
                             text=True, check=True, timeout=10, env=env, creationflags=FLAGS).stdout
    match = re.search(r"^([0-9a-fA-F]+) [A-Za-z] uwTick$", symbols, re.M)
    if not match:
        raise ValueError("uwTick missing from the selected ELF")
    tick_address = int(match[1], 16)
    identity = profile["identity"]
    commands = ["init", f"echo HWIDENT:[read_memory {identity['address']} 32 1]"]
    for _ in range(args.samples):
        commands += [f"echo HWSAMPLE:[read_memory 0xE000EDF0 32 1],[read_memory 0xE000ED10 32 1],[read_memory {tick_address} 32 1],[read_memory 0xE0042004 32 1]",
                     f"sleep {args.interval_ms}"]
    commands += ["shutdown"]
    cmd = server_command(stand, 0, profile) + ["-c", "gdb_port disabled", "-c", "; ".join(commands)]
    report = {"profile": profile["name"], "status": "ERROR", "samples": [],
              "limitations": "No Flash verification; run check-hw first. Debug connection affects power."}
    try:
        with probe_lock(ROOT, stand["serial"], stand["backend"]):
            run = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=ROOT,
                                 timeout=10 + args.samples * args.interval_ms / 1000, creationflags=FLAGS)
        output = run.stdout + run.stderr
        (out / "openocd.log").write_text(output.replace(stand["serial"], "<probe>"), encoding="utf-8")
        if run.returncode:
            raise RuntimeError("OpenOCD failed; see openocd.log")
        identity_match = re.search(r"HWIDENT:(0x[0-9a-fA-F]+)", output)
        if not identity_match:
            raise RuntimeError("MCU identity could not be read")
        actual = int(identity_match[1], 16) & identity["mask"]
        report["identity"] = dict(policy=args.identity_policy, expected=identity["value"],
                                  observed=actual, matches=actual == identity["value"])
        if actual != identity["value"]:
            report["warnings"] = [f"DEV_ID mismatch: expected 0x{identity['value']:03X}, observed 0x{actual:03X}"]
            if args.identity_policy == "strict":
                raise RuntimeError("MCU identity differs from selected profile (strict)")
        pattern = r"HWSAMPLE:(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+)"
        samples = [dict(zip(("dhcsr", "scr", "tick", "dbgmcu_cr"), (int(x, 16) for x in values)))
                   for values in re.findall(pattern, output)]
        report["samples"] = samples
        if len(samples) != args.samples:
            raise RuntimeError("Incomplete live observation")
        report["sleep_samples"] = sum(bool(x["dhcsr"] & (1 << 18)) for x in samples)
        report["tick_delta"] = (samples[-1]["tick"] - samples[0]["tick"]) & 0xFFFFFFFF
        report["checks"] = {
            "never_halted": all(not x["dhcsr"] & (1 << 17) for x in samples),
            "sleep_observed": report["sleep_samples"] > 0,
            "not_deep_sleep": all(not x["scr"] & 4 for x in samples),
            "tick_advanced": 0 < report["tick_delta"] < 0x80000000,
        }
        report["status"] = "PASS" if all(report["checks"].values()) else "FAIL"
    except Exception as exc:
        report["error"] = str(exc)
    (out / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
