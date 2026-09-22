"""Windows bring-up runner. No flashing; the selected ELF must already be on the board."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import socket
import time


ROOT = Path(__file__).resolve().parents[1]


def stop(process):
    if process is not None and process.poll() is None:
        # Kill only the tree started by this runner (including Scoop shims).
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, timeout=10)
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="ST-Link serial; kept out of source control")
    parser.add_argument("--elf", type=Path, default=ROOT / "build/debug/stm32-hwtest-blackpill.elf")
    parser.add_argument("--gdb", type=Path, default=Path.home() /
                        "xpack-arm-none-eabi-gcc-13.3.1-1.1/bin/arm-none-eabi-gdb-py3.exe")
    parser.add_argument("--openocd", default=shutil.which("openocd"))
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This bring-up runner currently supports Windows only")
    if not args.serial.isalnum() or args.timeout <= 0:
        parser.error("Use an alphanumeric serial and a positive timeout")
    if not args.openocd or not args.gdb.is_file() or not args.elf.is_file():
        parser.error("OpenOCD, GDB-Python and a built ELF are required")
    import msvcrt

    lock_name = hashlib.sha256(args.serial.encode()).hexdigest()
    lock_dir = ROOT / "build" / "probe-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = open(lock_dir / f"{lock_name}.lock", "a+b")
    lock.seek(0)
    if os.fstat(lock.fileno()).st_size == 0:
        lock.write(b"0")
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        parser.error("Another smoke runner owns this probe")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    out = ROOT / "build/hardware-smoke" / stamp
    out.mkdir(parents=True)
    result = out / "result.json"
    image = out / "image.bin"
    env = os.environ.copy()
    env.update(HWTEST_RESULT=str(result), HWTEST_IMAGE=str(image))
    server = client = None
    ready = False
    report = {"status": "ERROR", "checks": []}
    code = 2
    flags = subprocess.CREATE_NO_WINDOW
    gdb_base = [str(args.gdb), "-nx", "-batch", "-q", "-iex", "set auto-load off"]
    try:
        subprocess.run([str(args.gdb.parent / "arm-none-eabi-objcopy.exe"), "-O", "binary",
                        str(args.elf.resolve()), str(image)], check=True, timeout=15,
                       creationflags=flags)
        with socket.socket() as port_socket:
            port_socket.bind(("127.0.0.1", 0))
            port = port_socket.getsockname()[1]
        env["HWTEST_ENDPOINT"] = f"127.0.0.1:{port}"
        server_cmd = [args.openocd, "-f", "interface/stlink.cfg", "-f", "target/stm32f4x.cfg",
                      "-c", f"adapter serial {args.serial}", "-c", "adapter speed 1000",
                      "-c", f"gdb_port {port}", "-c", "tcl_port disabled", "-c", "telnet_port disabled"]
        with (out / "server.log").open("wb") as server_log, (out / "gdb.log").open("wb") as gdb_log:
            server = subprocess.Popen(server_cmd, stdout=server_log, stderr=subprocess.STDOUT,
                                      creationflags=flags)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("OpenOCD exited before ready; see server.log")
                log = (out / "server.log").read_text(errors="replace")
                if f"Listening on port {port} for gdb connections" in log:
                    ready = True
                    break
                time.sleep(0.1)
            if not ready:
                raise TimeoutError("OpenOCD startup timed out")
            client = subprocess.Popen(gdb_base + [str(args.elf.resolve()), "-x",
                                      str(ROOT / "Tests/hardware_smoke.py")], env=env,
                                      stdout=gdb_log, stderr=subprocess.STDOUT, creationflags=flags)
            code = client.wait(timeout=args.timeout)
        if not result.exists():
            raise RuntimeError(f"GDB exited {code} without a result; see gdb.log")
        report = json.loads(result.read_text(encoding="utf-8"))
        if code != 0 and report["status"] == "PASS":
            raise RuntimeError(f"GDB reported PASS but exited {code}")
    except Exception as exc:
        report.update(status="ERROR", error=str(exc))
        code = 2
    finally:
        try:
            stop(client)
            if ready and report.get("teardown") != "reset_run":
                # Recover even if the agent timed out or failed before its finally block.
                with (out / "recovery.log").open("wb") as recovery_log:
                    subprocess.run(gdb_base + ["-ex", "set confirm off", "-ex",
                                   "target extended-remote " + env["HWTEST_ENDPOINT"],
                                   "-ex", "monitor reset run", "-ex", "disconnect"],
                                   stdout=recovery_log, stderr=subprocess.STDOUT, check=True,
                                   timeout=10, creationflags=flags)
                report["teardown"] = "reset_run (host recovery)"
        except Exception as exc:
            report.update(status="ERROR", teardown_error=str(exc))
            code = 2
        finally:
            try:
                stop(server)
            finally:
                lock.close()
                result.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {result}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
