"""Explicit GDB entry point; never auto-loaded from ELF."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

import gdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hwtest.target import Target, CheckFailed


def main():
    session = json.loads(Path(os.environ["HWTEST_RUN"]).read_text(encoding="utf-8"))
    report = {"id": session["test"]["id"], "status": "ERROR", "checks": [],
              "gdb_version": gdb.VERSION, "python_version": sys.version.split()[0]}
    connected = False
    target = None
    try:
        for command in ("set pagination off", "set confirm off", "set breakpoint pending off",
                        "set remotetimeout 5", "set python print-stack full"):
            gdb.execute(command)
        image = Path(session["image"]).read_bytes()
        report["elf_sha256"] = hashlib.sha256(Path(session["elf"]).read_bytes()).hexdigest()
        report["bin_sha256"] = hashlib.sha256(image).hexdigest()
        gdb.execute("target extended-remote " + session["endpoint"])
        connected = True
        gdb.execute(session["reset_halt"])
        inferior = gdb.selected_inferior()
        matches = bytes(inferior.read_memory(0x08000000, len(image))) == image
        report["flashed"] = False
        if not matches and session["flash"] == "if-different":
            gdb.execute("load")
            report["flashed"] = True
            matches = bytes(inferior.read_memory(0x08000000, len(image))) == image
        if not matches:
            raise RuntimeError("Flash does not match the selected ELF image")
        report["image_verified"] = True
        target = Target(report)
        target.boot(session["reset_halt"])
        spec = importlib.util.spec_from_file_location("board_test", session["test"]["path"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        getattr(module, session["test"]["function"])(target)
        report["status"] = "PASS"
    except CheckFailed:
        report.update(status="FAIL", error=traceback.format_exc())
    except BaseException:
        report.update(status="ERROR", error=traceback.format_exc())
    finally:
        if report["status"] != "PASS" and connected:
            diagnostics = report["diagnostics"] = {}
            diagnostic_errors = {}
            for name in ("pc", "lr", "sp", "xPSR"):
                try:
                    diagnostics[name] = int(gdb.newest_frame().read_register(name))
                except Exception as exc:
                    diagnostic_errors[name] = str(exc)
            for name, address in (("CFSR", 0xE000ED28), ("HFSR", 0xE000ED2C)):
                try:
                    diagnostics[name] = int.from_bytes(
                        gdb.selected_inferior().read_memory(address, 4), "little")
                except Exception as exc:
                    diagnostic_errors[name] = str(exc)
            try:
                report["backtrace"] = gdb.execute("bt", to_string=True)
            except Exception as exc:
                diagnostic_errors["backtrace"] = str(exc)
            if diagnostic_errors:
                report["diagnostic_errors"] = diagnostic_errors
        try:
            if target:
                target.close()
            if connected:
                gdb.execute(session["reset_run"])
                gdb.execute("disconnect")
                report["teardown"] = "reset_run"
        except BaseException:
            report.update(status="ERROR", teardown_error=traceback.format_exc())
        Path(session["result"]).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
    gdb.execute("quit " + str({"PASS": 0, "FAIL": 1, "ERROR": 2}[report["status"]]))


main()
