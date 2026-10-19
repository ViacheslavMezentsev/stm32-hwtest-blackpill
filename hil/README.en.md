# stm32-hwtest-blackpill HIL tests

[Русский](README.md)

[stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest) scenarios check the running
firmware on the board: the runner starts the debugger's GDB server, GDB resets the MCU, stops in
`main()` and runs a Python scenario. Reports are JSON and JUnit. No test code is added to the firmware.

## Contents

```text
hil/
  common/tests/   board/test_*.py, requirements.md, contracts.json, native/ (ADC arithmetic on the PC)
  common/stm32f4-test.svd  MMIO
  common/plans/   DDTT
  F411CE/         session.toml, target.toml, board.toml, stands/   (Flash 512 KiB, DEV_ID 0x431)
  F401CC/         session.toml, target.toml, board.toml, stands/   (Flash 256 KiB, DEV_ID 0x423)
  templates/      *.example.toml  (stlink, openocd, jlink)
  tools/          results.py
  api.toml        scenario parameters: deadlines, VDDA window, measurement series, timers
```

The board is chosen by the build: presets `f411ce-hil` and `f401cc-hil` set `BOARD` and
`BLACKPILL_HIL=ON`; `cmake/blackpill.cmake` attaches stm32-gdbtest 0.5.0 final candidate (8fdbb58) (`modules/stm32-gdbtest`)
with the run configuration `hil/<MCU>/session.toml` (`SESSION_CONFIG`) and the shared scenarios
`hil/common/tests`. The configuration ties the MCU description (`target.toml`), the shared `api.toml`
and the board data file (`board.toml`) together; scenarios read them through `t.profile`
(`t.profile.data["board"]`, `t.profile.get("user.timing.adc_deadline_ticks")`), so one scenario serves
both boards and board-specific expectations live in data, not in code. The scenarios use the API of
module API 3 and pass the module style test:
`python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/common/tests/board/*.py`.

## Stand

A stand is a local file describing the board's debugger. Copy an example from `hil/templates/` to
`hil/<MCU>/stands/local.toml` and set the debugger serial number (`*.local.toml` files are not committed):

| Board | Stand file | Presets |
| --- | --- | --- |
| BlackPill F411CE | `hil/F411CE/stands/local.toml` | `f411ce-hil`, `f411ce-hil-host`, `f411ce-hil-hw` |
| BlackPill F401CC | `hil/F401CC/stands/local.toml` | `f401cc-hil`, `f401cc-hil-host`, `f401cc-hil-hw` |

| Debugger | Example | Serial number |
| --- | --- | --- |
| ST-Link, ST-LINK GDB Server (STM32CubeCLT) | `templates/stlink.example.toml` | `STM32_Programmer_CLI -l st` |
| ST-Link, OpenOCD | `templates/openocd.example.toml` | the same ST-Link serial number |
| J-Link | `templates/jlink.example.toml` | decimal number from J-Link Commander |

Environment check without accessing the board:

```powershell
python -B modules/stm32-gdbtest/stm32_gdbtest/cli.py doctor --stand hil/F411CE/stands/local.toml
```

## Running

```powershell
cmake --preset f411ce-hil
cmake --build --preset f411ce-hil
ctest --preset f411ce-hil-host     # no board: requirement traceability and prepare.*
ctest --preset f411ce-hil-hw       # on the board: all hw.* (22 scenarios)
python hil/tools/results.py --runs build/f411ce-hil/hwtest/runs
```

The firmware is programmed only if the Flash image differs (`flash = "if-different"` in the stand).
Do not debug in VS Code and run the tests with the same debugger at the same time.

| Scenario | Checks | Techniques ([catalogue](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/8fdbb58be35689376a70eb1973bea7096de6f45d/docs/en/TESTING_TECHNIQUES.md)) |
| --- | --- | --- |
| `HW_BOOT` | `loop()` without a fault, SYSCLK from the 16 MHz HSI, undivided buses | `check(rows)` table, register address |
| `HW_CLOCK_GPIO_CONFIG` | HSI, dividers, 1 ms SysTick, PC13 pin | table, contract, TECH-001 |
| `HW_GPIO` | LED off, on, off over three toggles | expectations from `profile.data` |
| `HW_BOARD_PROFILE` | MCU, device macro, DEV_ID, F_SIZE, vector table, refused peripheral read | TECH-017, `memory`, `refused` |
| `HW_ADC_INIT` | scan channels from the board data, halfword DMA with increment | table, contract |
| `HW_ADC_RUNTIME` | one publication, FACTORY quality, VDDA within the `api.toml` window | `within`, `profile.get` |
| `HW_ADC_DMA_PUBLICATION` | DMA interrupt, buffer samples published once after the callback | TECH-003, `memory` |
| `HW_ADC_WRITER` | the measurement counter is written by `loop()` from `main()` | `watch`, `frames`, TECH-013 |
| `HW_ADC_SERIES` | a series of five measurements: consecutive, FACTORY, VDDA and temperature spread | `record`/`records`, TECH-011 |
| `HW_ADC_DISABLED` | a cleared ADON gives fault code 2 | `write` with an expression, TECH-006 |
| `HW_ADC_TIMEOUT` | without the DMA interrupt the application leaves after 100 ticks | `write` to NVIC, TECH-006 |
| `HW_ADC_BUSY` | a busy DMA stream gives fault code 1 | `write(rows)` |
| `HW_ADC_INVALID` | samples 0 and 4095 give INVALID, then recovery | argument `write`, TECH-005 |
| `HW_ADC_VECTORS` | calibration samples give 3300 mV, 30 and 110 °C | `write(rows)`, TECH-007 |
| `HW_ADC_CALLBACK_SUPPRESSED` | a lost callback leads to the deadline without publication | `ret`, TECH-004 |
| `HW_TIMER` | TIM2 1 kHz / 100 ms, the event reaches the application | table, `profile.get` |
| `HW_TIMER_IRQ_PUBLICATION` | TIM2 interrupt, one event per handler, return to thread mode | TECH-002, TECH-003 |
| `HW_RTC` | RTC prescalers, first alarm after 2 s, rescheduling | table, contract |
| `HW_RTC_DEADLINE` | an LSI wait that cannot succeed gives fault code 12 | `reach` with a condition, TECH-015 |
| `HW_SLEEP_SYSTICK` | SysTick wakes the core from WFI, the idle interval completes | `frames`, `memory`, TECH-008 |
| `HW_SLEEP_TIM2` | TIM2 wakes the core from WFI with SysTick stopped | `write(rows)`, TECH-008 |

## Notes

**CMSIS macros in scenarios.** GDB expands macros (`RCC`, `ADC_CR2_ADON`, …) in a `-g3` build
(all HIL presets) when the current stop is in a translation unit that includes `stm32f4xx.h`. That is
`src/platform.c`: registers are checked in the `platform_*` functions and interrupt handlers, the
application data in `loop()` (`src/program.cpp`). The contracts in `hil/common/tests/contracts.json` check
that the macros are in the ELF already in `prepare.*`, without a board.

**No LTO.** The scenarios stop at platform and application functions and substitute their returns;
with LTO functions are inlined and reordered. The build uses `-fno-lto`.

**RTC and the backup domain.** `setup()` sets the calendar to 00-01-01 and an alarm two seconds
later; the backup domain is not reset and an incompatible RTC source is a fault. This is not a check
of LSI accuracy, backup retention or day rollover.

**Sleep.** Ordinary WFI, not Stop: the tests check the wake-up and the interrupted context, not current.

**Results.** The run directory `build/<board>-hil/hwtest/runs/<time>-<ID>-<pid>/` holds
`result.json`, GDB and server logs, the ELF snapshot and the build manifest.

**History.** Former HAL presets, experiment protocols and stands are in the
[history](../docs/history/README.md) and the [archive](../archive/README.md); their results do not
apply to the current CMSIS firmware.

## Development through DDTT

[Plan](common/plans/ddtt-feedback.en.md) and [cycle results](common/plans/ddtt-feedback-results.en.md):
the scenario first exposes the defect in baseline firmware, then checks its fix and regression.
Skill: `.claude/skills/stm32-gdbtest-develop/SKILL.md`; this branch includes a trial copy while
the module gitlink is pinned to 8fdbb58 (0.5.0 final candidate, API 3). All six skill copies match this revision.
Unlike stand-loop execution, development needs a source checkout and compiler, not just a ZIP.
Profiles use target schema 2 with `[openocd]`; sessions enable `[results] capture = true`.

New scenario: `HW_ADC_TIMEOUT_DIAGNOSTIC` (`common/tests/board/test_ddtt_feedback.py`).

[MMIO/SVD migration and offline checks](../docs/MMIO_SVD.en.md).
