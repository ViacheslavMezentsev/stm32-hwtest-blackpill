"""Bounded diagnostic runner. Restore the blink application after a hardware series."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import tomllib
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODULE = ROOT / "modules/stm32-gdbtest"
sys.path.insert(0, str(MODULE))
from stm32_gdbtest.processes import FLAGS, probe_lock, stop_tree


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("offline", "flash"))
    p.add_argument("--stand", type=Path)
    p.add_argument("--build", type=Path, default=ROOT / "build/k1921-errata-gcc13")
    p.add_argument("--gdb", type=Path, default=Path(os.environ["USERPROFILE"]) /
                   "xpack-riscv-none-elf-gcc-13.3.0-2/bin/riscv-none-elf-gdb-py3.exe")
    a = p.parse_args()
    build = a.build.resolve()
    if not build.is_relative_to(ROOT / "build"):
        raise ValueError("PoC build/output must remain in project build/")
    elf, image = build / "k1921-errata.elf", build / "k1921-errata.bin"
    manifest = json.loads((build / "poc-manifest.json").read_text())
    if sha(elf) != manifest["elf_sha256"] or sha(image) != manifest["bin_sha256"]:
        raise ValueError("Artifact differs from post-link snapshot")
    out = build / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + a.stage + "-" + uuid.uuid4().hex[:6])
    out.mkdir(parents=True)
    # Execute immutable run snapshots, not mutable build files.
    for source in (elf, image, build / "poc-manifest.json"):
        (out / source.name).write_bytes(source.read_bytes())
    if sha(out / elf.name) != manifest["elf_sha256"] or sha(out / image.name) != manifest["bin_sha256"]:
        raise ValueError("Build artifacts changed during snapshot")
    (out / "gdb_agent.py").write_bytes((HERE / "gdb_agent.py").read_bytes())
    config = dict(stage=a.stage, elf=(out / elf.name).as_posix(), image=(out / image.name).as_posix(),
                  module=MODULE.as_posix(), out=out.as_posix(), regions=manifest["load_regions"], table_address=manifest["table_address"], table_in_ram=manifest["table_in_ram"])
    env = dict(os.environ, TEMP=str(out), TMP=str(out), PYTHONDONTWRITEBYTECODE="1",
               K1921_POC_SESSION=str(out / "session.json"))
    env.pop("PYTHONPATH", None)
    command = [str(a.gdb), "-nx", "-nh", "-batch", "-iex", "set auto-load off",
               "-ex", "source " + (out / "gdb_agent.py").as_posix()]

    def client(timeout):
        with (out / "gdb.log").open("wb") as log:
            proc = subprocess.Popen(command, cwd=out, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, creationflags=FLAGS)
            try:
                return proc.wait(timeout=timeout)
            finally:
                stop_tree(proc)

    if a.stage == "offline":
        (out / "session.json").write_text(json.dumps(config), encoding="utf-8")
        rc = client(20)
    else:
        if a.stand is None:
            raise ValueError("Explicit --stand is required for hardware access")
        stand = tomllib.loads(a.stand.read_text(encoding="utf-8"))["probe"]
        if not re.fullmatch(r"[1-9][0-9]{3,}", stand["serial"]):
            raise ValueError("Explicit decimal J-Link USB serial required")
        speed = stand.get("speed_khz", 1000)
        if type(speed) is not int or not 1 <= speed <= 4000:
            raise ValueError("Invalid JTAG speed")
        with probe_lock(ROOT, stand["serial"], "jlink"):
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            config["endpoint"] = f"127.0.0.1:{port}"
            (out / "session.json").write_text(json.dumps(config), encoding="utf-8")
            server_cmd = [stand["executable"], "-device", "K1921VG015", "-if", "JTAG",
                          "-speed", str(speed), "-USB", stand["serial"], "-port", str(port),
                          "-swoport", "0", "-telnetport", "0", "-RTTTelnetPort", "0",
                          "-localhostonly", "1", "-nogui", "-strict", "-timeout", "5000",
                          "-noir", "-noreset", "-nohalt", "-nosinglerun", "-vd"]
            with (out / "server.log").open("wb") as log:
                server = subprocess.Popen(server_cmd, cwd=out, env=env, stdout=log,
                                          stderr=subprocess.STDOUT, creationflags=FLAGS)
                try:
                    deadline = time.monotonic() + 20
                    while "Waiting for GDB connection" not in (out / "server.log").read_text(errors="replace"):
                        if server.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError("Server unavailable; see " + str(out / "server.log"))
                        time.sleep(0.1)
                    try:
                        rc = client(300)
                    except subprocess.TimeoutExpired:
                        # The timeout remains ERROR even if recovery succeeds.
                        result = dict(status="ERROR", reason="external_timeout", stage=a.stage)
                        recovery = [str(a.gdb), "-nx", "-nh", "-batch", "-iex", "set auto-load off"]
                        for cmd in ("set confirm off", "set remotetimeout 5",
                                    "target extended-remote " + config["endpoint"],
                                    "monitor reset", "monitor go", "disconnect"):
                            recovery += ["-ex", cmd]
                        try:
                            with (out / "recovery.log").open("wb") as rlog:
                                rp = subprocess.Popen(recovery, cwd=out, env=env, stdout=rlog,
                                                      stderr=subprocess.STDOUT, creationflags=FLAGS)
                                try:
                                    result["recovery_returncode"] = rp.wait(timeout=15)
                                finally:
                                    stop_tree(rp)
                        except Exception as error:
                            result["recovery_error"] = str(error)
                        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                        rc = 2
                finally:
                    stop_tree(server)
    print("Report: " + str(out))
    if (out / "result.json").exists():
        result = json.loads((out / "result.json").read_text(encoding="utf-8"))
        print(json.dumps({k: v for k, v in result.items() if k not in ("macros", "stops", "checks", "load_regions", "unloaded_gaps")}, indent=2))

    else:
        print("No agent report")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
