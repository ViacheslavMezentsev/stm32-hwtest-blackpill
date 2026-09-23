"""Run inside GDB-Python; checks the already flashed BlackPill Debug image.

This is a board bring-up check, not the reusable hwtest framework.
The caller owns OpenOCD and enforces an external wall-clock timeout.
"""

import hashlib
import json
import os
from pathlib import Path
import traceback

import gdb


checks = []
report = {"status": "ERROR", "checks": checks}
result_path = Path(os.environ["HWTEST_RESULT"])


def check(name, actual, expected, failure=AssertionError):
    ok = actual == expected
    checks.append(dict(name=name, actual=actual, expected=expected, passed=ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}: {actual!r} (expected {expected!r})")
    if not ok:
        raise failure(name)


def value(expression):
    return int(gdb.parse_and_eval(expression))


def clear_breakpoints():
    for bp in gdb.breakpoints() or ():
        bp.delete()


def reach(function):
    bp = gdb.Breakpoint(function, type=gdb.BP_HARDWARE_BREAKPOINT, temporary=True)
    try:
        gdb.execute("continue")
        check(f"reached {function}", gdb.selected_frame().name(), function)
    finally:
        if bp.is_valid():
            bp.delete()


def boot():
    clear_breakpoints()
    gdb.execute("monitor reset halt")
    for function in ("HardFault_Handler", "MemManage_Handler", "BusFault_Handler", "UsageFault_Handler"):
        gdb.Breakpoint(function, type=gdb.BP_HARDWARE_BREAKPOINT)
    reach("main")


exit_code = 2
connected = False
try:
    for command in ("set pagination off", "set confirm off", "set breakpoint pending off",
                    "set remotetimeout 5", "set print pretty off"):
        gdb.execute(command)
    elf = Path(gdb.current_progspace().filename)
    report["elf_sha256"] = hashlib.sha256(elf.read_bytes()).hexdigest()
    # The host generates this BIN from the same ELF immediately before the run.
    binary = Path(os.environ["HWTEST_IMAGE"]).read_bytes()
    report["bin_sha256"] = hashlib.sha256(binary).hexdigest()
    gdb.execute("target extended-remote " + os.environ["HWTEST_ENDPOINT"])
    connected = True
    gdb.execute("monitor halt")
    actual_flash = bytes(gdb.selected_inferior().read_memory(0x08000000, len(binary)))
    check("Flash matches BIN including initialized data load image", actual_flash == binary, True,
          failure=RuntimeError)

    boot()
    reach("loop")
    check("SystemCoreClock", value("SystemCoreClock"), 8000000)
    # Field positions from STM32Cube F4 V1.28.3 stm32f411xe.h.
    cfgr = value("RCC->CFGR")
    check("SYSCLK source HSI", (cfgr >> 2) & 3, 0)
    check("AHB divide by 2", (cfgr >> 4) & 15, 8)
    check("APB1 divide by 1", (cfgr >> 10) & 7, 0)
    check("APB2 divide by 4", (cfgr >> 13) & 7, 5)
    check("GPIOC clock enabled", (value("RCC->AHB1ENR") >> 2) & 1, 1)
    check("PC13 output mode", (value("GPIOC->MODER") >> 26) & 3, 1)
    check("PC13 push-pull", (value("GPIOC->OTYPER") >> 13) & 1, 0)
    check("PC13 no pull", (value("GPIOC->PUPDR") >> 26) & 3, 0)
    check("PC13 low speed", (value("GPIOC->OSPEEDR") >> 26) & 3, 0)
    check("PC13 initial output", (value("GPIOC->ODR") >> 13) & 1, 0)
    tick = value("uwTick")
    for expected in (1, 0):
        reach("loop")
        check("PC13 toggled", (value("GPIOC->ODR") >> 13) & 1, expected)
        next_tick = value("uwTick")
        delta = (next_tick - tick) & 0xFFFFFFFF
        report.setdefault("loop_tick_deltas_ms", []).append(delta)
        check("HAL tick advanced by at least 500 ms", delta >= 500, True)
        tick = next_tick

    boot()
    reach("HAL_RCC_OscConfig")
    # GDB return already removes the callee frame; do not finish the caller.
    gdb.execute("return (HAL_StatusTypeDef)1")
    reach("Error_Handler")
    report["status"] = "PASS"
    exit_code = 0
except AssertionError:
    report["status"] = "FAIL"
    report["error"] = traceback.format_exc()
    exit_code = 1
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if connected:
        try:
            clear_breakpoints()
            gdb.execute("monitor reset run")
            gdb.execute("disconnect")
            report["teardown"] = "reset_run"
        except Exception:
            report["teardown_error"] = traceback.format_exc()
            report["status"] = "ERROR"
            exit_code = 2
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if "error" in report:
        print(report["error"])
    print("Hardware smoke result: " + report["status"])
    gdb.execute(f"quit {exit_code}")
