"""Experimental K1921 lifecycle; reuse the unchanged module Target API."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

import gdb

sys.dont_write_bytecode = True
config = json.loads(Path(os.environ["K1921_POC_SESSION"]).read_text(encoding="utf-8"))
sys.path.insert(0, config["module"])
from stm32_gdbtest.target import Target, CheckFailed
from stm32_gdbtest.compatibility import inspect_gdb_api, require_gdb_api

out = Path(config["out"])
report = dict(status="ERROR", checks=[], stage=config["stage"],
              gdb=gdb.VERSION, python=sys.version.split()[0], flashed=False)
target = None
connected = False
try:
    for command in ("set pagination off", "set confirm off", "set breakpoint pending off",
                    "set remotetimeout 5", "set python print-stack full"):
        gdb.execute(command)
    require_gdb_api(inspect_gdb_api(gdb))
    gdb.execute("file " + json.dumps(config["elf"]))
    for symbol in ("main", "app_step", "sleep", "SystemCoreClock"):
        if gdb.lookup_global_symbol(symbol) is None:
            raise RuntimeError("Missing ELF symbol: " + symbol)
    gdb.execute("list app_step", to_string=True)
    macros = {name: gdb.execute("info macro " + name, to_string=True)
              for name in ("GPIOC", "RCU_CGCFGAHB_GPIOCEN_Msk")}
    if any("#define" not in text for text in macros.values()):
        raise RuntimeError("Required macro debug information is absent")
    report["macros"] = macros
    if config["stage"] == "offline":
        report["status"] = "PASS"
    else:
        gdb.execute("target extended-remote " + config["endpoint"])
        connected = True
        gdb.execute("monitor flash breakpoints = 0")
        gdb.execute("monitor reset")
        inferior = gdb.selected_inferior()
        report["architecture"] = inferior.architecture().name()
        if "riscv:rv32" not in report["architecture"]:
            raise RuntimeError("Expected RV32 before accessing target memory")
        chipid = int.from_bytes(inferior.read_memory(0x3000F100, 4), "little")
        report["identity"] = dict(chipid=chipid, expected_masked=0xDEADBEE0,
                                  mask=0xFFFFFFF0, evidence="RM v3 p300 PMUSYS.CHIPID")
        if chipid & 0xFFFFFFF0 != 0xDEADBEE0:
            raise RuntimeError("CHIPID differs from the reviewed K1921VG015 manual")
        image = Path(config["image"]).read_bytes()
        # RM section 7: 1 MiB. This is a documented bound, not a factory-size read.
        if not 0 < len(image) <= 1024 * 1024:
            raise RuntimeError("Image exceeds documented Flash capacity")
        def verify_regions():
            results = []
            for region in config["regions"]:
                offset, size, address = region["offset"], region["size"], region["address"]
                if offset < 0 or size <= 0 or offset + size > len(image) or address != 0x80000000 + offset:
                    raise RuntimeError("Invalid ELF load region")
                expected = image[offset:offset + size]
                actual = bytes(inferior.read_memory(address, size))
                results.append(dict(region, matches=actual == expected))
            report["load_regions"] = results
            return bool(results) and all(r["matches"] for r in results)

        if not verify_regions():
            if config["stage"] != "flash":
                raise RuntimeError("verify-only: Flash differs from selected image")
            (out / "previous-image-range.bin").write_bytes(bytes(inferior.read_memory(0x80000000, len(image))))
            gdb.execute("load")
            report["flashed"] = True
        if not verify_regions():
            raise RuntimeError("Flash readback differs")
        report["unloaded_gaps"] = []
        regions = sorted(config["regions"], key=lambda region: region["address"])
        for left, right in zip(regions, regions[1:]):
            start = left["address"] + left["size"]
            size = right["address"] - start
            if size > 0:
                report["unloaded_gaps"].append(dict(address=start, size=size,
                    observed_hex=bytes(inferior.read_memory(start, size)).hex(),
                    compared=False))
        report["image_verified"] = True
        report["image_sha256"] = hashlib.sha256(image).hexdigest()
        # No generic trap_entry breakpoint: it may handle normal interrupts too.
        target = Target(report, {"breakpoint_limit": 1, "fault_handlers": []})
        target.boot("monitor reset")
        target.reach("app_step")
        target.check("core clock", target.value("SystemCoreClock"), 50000000)
        target.check("GPIOC clock", target.value("(RCU->CGCFGAHB & RCU_CGCFGAHB_GPIOCEN_Msk) != 0"), 1)
        target.fields("RCU->CGCFGAHB_bit", {"GPIOCEN": 1})
        target.check("GPIOC reset released", target.value("(RCU->RSTDISAHB & RCU_RSTDISAHB_GPIOCEN_Msk) != 0"), 1)
        target.check("PC0 output enabled", target.value("GPIOC->OUTENSET & 1"), 1)
        initial = target.value("GPIOC->DATAOUT & 1")
        target.check("initial PC0 latch", initial, 1)
        if config["stage"] == "stall":
            (out / "stall-reached.json").write_text(json.dumps(report), encoding="utf-8")
            time.sleep(120)  # Deliberate GDB-Python stall, no test code in firmware.
        elif config["stage"] == "negative":
            target.check("deliberate wrong PC0 expectation", initial, 0)
        else:
            for expected in (0, 1, 0):
                target.reach("app_step")
                target.check("PC0 toggled", target.value("GPIOC->DATAOUT & 1"), expected)
            # Conditional hardware breakpoint and scalar argument via DWARF.
            target.reach("sleep", when="ms == 500")
            target.check("blink delay argument", target.value("ms"), 500)
            report["status"] = "PASS"
except CheckFailed:
    report.update(status="FAIL", error=traceback.format_exc())
except BaseException:
    report.update(status="ERROR", error=traceback.format_exc())
finally:
    if connected and report["status"] != "PASS":
        report["registers"] = {}
        for name in ("pc", "ra", "sp", "mstatus", "mcause", "mepc", "mtval"):
            try:
                report["registers"][name] = int(gdb.parse_and_eval("$" + name))
            except Exception as error:
                report["registers"][name] = str(error)
    try:
        if target:
            target.close()
        if connected:
            for command in ("monitor reset", "monitor go", "disconnect"):
                gdb.execute(command)
            report["teardown"] = "reset_run"
    except Exception:
        report.update(status="ERROR", teardown_error=traceback.format_exc())
    (out / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
gdb.execute("quit " + str({"PASS": 0, "FAIL": 1, "ERROR": 2}[report["status"]]))
