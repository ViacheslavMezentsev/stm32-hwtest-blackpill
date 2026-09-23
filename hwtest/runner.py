"""Host orchestrator: snapshot, probe ownership, lifecycle and reports."""

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import time
import traceback

from hwtest.backends import load_stand, server_spec
from hwtest.profile import load_profile
from hwtest.processes import FLAGS, probe_lock, stop_tree
from hwtest.reports import CODES, write_reports
from hwtest.compatibility import runtime_manifest


ROOT = Path(__file__).resolve().parents[1]


def local_directory(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Output directories must remain inside this repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(session, test, stand_path=None, timeout=None):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    out = local_directory(Path(session["out"]) / f"{stamp}-{test['id']}-{os.getpid()}")
    started = time.monotonic()
    report = {"id": test["id"], "status": "ERROR", "checks": [], "started_utc": stamp}
    try:
        if os.name != "nt":
            raise RuntimeError("This MVP supports Windows only")
        limit = test["timeout_s"] if timeout is None else timeout
        if not math.isfinite(limit) or not 0 < limit <= 300:
            raise ValueError("Timeout must be positive and <= 300 seconds")
        path = stand_path or os.environ.get("HWTEST_STAND") or session.get("stand")
        if not path:
            raise RuntimeError("Select a local stand with HWTEST_STAND or --stand")
        stand = load_stand(path)
        report["backend"] = stand["backend"]
        profile = load_profile(session["profile"])
        report["profile"] = profile
        with probe_lock(ROOT, stand["serial"]):
            execute(session, test, stand, out, report, limit, profile)
    except BaseException:
        report.update(status="ERROR", error=traceback.format_exc())
    server_log = ""
    try:
        server_log = (out / "server.log").read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass  # Runs failing before server startup still receive an explicit partial manifest.
    report["compatibility"] = runtime_manifest(report, server_log)
    report["duration_s"] = round(time.monotonic() - started, 3)
    write_reports(out, report)
    print(f"{report['status']} {test['id']}: {out / 'result.json'}")
    if report["status"] != "PASS":
        print(report.get("error", "") + report.get("teardown_error", ""))
    return CODES[report["status"]]


def execute(session, test, stand, out, report, timeout, profile):
    server = client = None
    ready = False
    env = os.environ.copy()
    temp = local_directory(ROOT / "build/hwtest-tmp")
    env.update(TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
    # The embedded Python must not inherit another Python installation's runtime path.
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    elf = out / "firmware.elf"
    image = out / "image.bin"
    agent_result = out / "agent-result.json"
    gdb = Path(session["gdb"])
    gdb_base = [str(gdb), "-nx", "-batch", "-q", "-iex", "set auto-load off"]
    endpoint = None
    try:
        # All clients consume this immutable per-run snapshot, never a changing build ELF.
        elf.write_bytes(Path(session["elf"]).read_bytes())
        report["elf_sha256"] = hashlib.sha256(elf.read_bytes()).hexdigest()
        with (out / "prepare.log").open("wb") as log:
            subprocess.run([str(gdb.parent / "arm-none-eabi-objcopy.exe"), "-O", "binary",
                            str(elf), str(image)], check=True, timeout=15, env=env,
                           stdout=log, stderr=subprocess.STDOUT, creationflags=FLAGS)
            subprocess.run(gdb_base + ["-ex", "python import gdb, json; print(gdb.VERSION)"],
                           check=True, timeout=10, env=env, stdout=log,
                           stderr=subprocess.STDOUT, creationflags=FLAGS)
        if not 0 < image.stat().st_size <= profile["flash_size"]:
            raise ValueError("Firmware image is empty or exceeds profile Flash")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        endpoint = f"127.0.0.1:{port}"
        backend = server_spec(stand, port, profile, out)
        report["backend_commands"] = dict(reset_halt=backend["reset_halt"], finish=backend["finish"],
                                          setup=backend.get("setup", []))
        run_data = dict(test=test, elf=str(elf), image=str(image), result=str(agent_result),
                        endpoint=endpoint, flash=stand["flash"], profile=profile,
                        reset_halt=backend["reset_halt"], finish=backend["finish"],
                        setup=backend.get("setup", []))
        run_file = out / "run.json"
        run_file.write_text(json.dumps(run_data), encoding="utf-8")
        env["HWTEST_RUN"] = str(run_file)
        with (out / "server.log").open("wb") as server_log, (out / "gdb.log").open("wb") as gdb_log:
            server = subprocess.Popen(backend["command"], env=env, cwd=out,
                                      stdout=server_log, stderr=subprocess.STDOUT, creationflags=FLAGS)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("GDB server exited before ready; see server.log")
                if backend["ready"] in (out / "server.log").read_text(errors="replace"):
                    ready = True
                    break
                time.sleep(0.1)
            if not ready:
                raise TimeoutError("GDB server startup timed out")
            client = subprocess.Popen(gdb_base + [str(elf), "-x", str(ROOT / "hwtest/agent.py")],
                                      env=env, cwd=ROOT, stdout=gdb_log, stderr=subprocess.STDOUT,
                                      creationflags=FLAGS)
            returncode = client.wait(timeout=timeout)
        if not agent_result.exists():
            raise RuntimeError(f"GDB exited {returncode} without report; see gdb.log")
        result = json.loads(agent_result.read_text(encoding="utf-8"))
        if (result.get("id") != test["id"] or result.get("elf_sha256") != report["elf_sha256"]
                or result.get("status") not in CODES or returncode != CODES[result["status"]]):
            raise RuntimeError("Invalid or inconsistent GDB report")
        report.update(result)
    except BaseException:
        report.update(status="ERROR", error=traceback.format_exc())
    finally:
        try:
            stop_tree(client)
            if (ready and report.get("connection_attempted", True)
                    and report.get("teardown") != "reset_run"):
                with (out / "recovery.log").open("wb") as log:
                    finish = [item for command in backend["finish"] for item in ("-ex", command)]
                    subprocess.run(gdb_base + ["-ex", "set confirm off", "-ex",
                                   "target extended-remote " + endpoint] + finish,
                                   check=True, timeout=10, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, creationflags=FLAGS)
                report["teardown"] = "reset_run (host recovery)"
        except BaseException:
            report.update(status="ERROR", teardown_error=traceback.format_exc())
        finally:
            try:
                stop_tree(server)
            except BaseException:
                report.update(status="ERROR", cleanup_error=traceback.format_exc())
