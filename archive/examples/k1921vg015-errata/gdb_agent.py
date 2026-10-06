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
        bp = gdb.Breakpoint("experiment_done", type=gdb.BP_HARDWARE_BREAKPOINT)
        if bp.pending:
            raise RuntimeError("Pending completion breakpoint")
        gdb.execute("monitor reset")
        gdb.execute("continue")
        if int(gdb.parse_and_eval("completed")) != 0x12345678:
            raise RuntimeError("Experiment did not complete")
        table = config["table_address"]
        report["table"] = dict(address=hex(table), in_ram=config["table_in_ram"],
                               operand_bits=hex(int.from_bytes(inferior.read_memory(table + 5 * 4, 4), "little")))
        if report["table"]["operand_bits"] != "0x47c35000":
            raise RuntimeError("Expected powers_of_ten_float[5] = 100000")
        report["clock"] = int(gdb.parse_and_eval("SystemCoreClock"))
        report["addresses"] = {n: hex(int(gdb.parse_and_eval("&" + n)))
                               for n in ("flash_divisor", "ram_divisor")}
        names = ("from_chars", "flash_adjacent", "flash_nop", "ram_adjacent")
        report["results"] = {}
        for i, name in enumerate(names):
            row = {field: int(gdb.parse_and_eval(f"results[{i}].{field}"))
                   for field in ("count", "wrong", "ec_errors", "ptr_errors", "first", "last", "first_wrong", "infinity")}
            report["results"][name] = row
            if row["count"] != 1000:
                raise RuntimeError("Incomplete sample count")
        bp.delete()
        report["status"] = "OBSERVED"
except Exception as error:
    report["error"] = str(error)
    report["traceback"] = traceback.format_exc()
finally:
    if connected:
        try:
            gdb.execute("monitor reset")
            gdb.execute("monitor go")
            gdb.execute("disconnect")
        except Exception as error:
            report["finish_error"] = str(error)
            report["status"] = "ERROR"
    (out / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    gdb.execute("quit " + ("0" if report["status"] in ("PASS", "OBSERVED") else "2"))
