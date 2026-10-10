# stm32-hwtest-blackpill HIL tests

[Русский](README.md)

[stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest) scenarios check the running
firmware on the board: the runner starts the debugger's GDB server, GDB resets the MCU, stops in
`main()` and runs a Python scenario. Reports are JSON and JUnit. No test code is added to the firmware.

## Contents

```text
hil/
  sessions/<mcu>.toml          board run configuration: MCU description, api.toml, board data file
  profiles/f411ce.toml         MCU description: Flash 512 KiB, DEV_ID 0x431, 6 breakpoints
  profiles/f401cc.toml         the same, Flash 256 KiB, DEV_ID 0x423
  boards/<mcu>.toml            board data file: LED, RAM, ADC channels, factory calibration addresses
  api.toml                     scenario parameters: deadlines, VDDA window, measurement series, timers
  tests/requirements.md        HW_* requirements (shared by both boards, Russian)
  tests/contracts.json         contracts: CMSIS macros in the ELF debug info
  tests/board/test_boot.py     HW_BOOT, HW_CLOCK_GPIO_CONFIG, HW_GPIO, HW_BOARD_PROFILE
  tests/board/test_adc.py      HW_ADC_INIT, HW_ADC_RUNTIME, HW_ADC_DMA_PUBLICATION, HW_ADC_WRITER, HW_ADC_SERIES
  tests/board/test_adc_faults.py  HW_ADC_DISABLED, HW_ADC_TIMEOUT, HW_ADC_BUSY, HW_ADC_INVALID,
                               HW_ADC_VECTORS, HW_ADC_CALLBACK_SUPPRESSED — injections
  tests/board/test_timers.py   HW_TIMER, HW_TIMER_IRQ_PUBLICATION, HW_RTC, HW_RTC_DEADLINE
  tests/board/test_sleep.py    HW_SLEEP_SYSTICK, HW_SLEEP_TIM2
  tests/native/                ADC arithmetic on the PC (CTest, no board)
  stands/*.example.toml        stand examples: ST-Link and OpenOCD
```

The board is chosen by the build: presets `HIL_F411CE` and `HIL_F401CC` set `BOARD` and
`BLACKPILL_HIL=ON`; `cmake/blackpill.cmake` attaches stm32-gdbtest v0.4.0 (`modules/stm32-gdbtest`)
with the run configuration `hil/sessions/<mcu>.toml` (`SESSION_CONFIG`) and the shared scenarios
`hil/tests`. The configuration ties the MCU description, the shared `api.toml` and the board data
file together; scenarios read them through `t.profile` (`t.profile.data["board"]`,
`t.profile.get("user.timing.adc_deadline_ticks")`), so one scenario serves both boards and
board-specific expectations live in data, not in code. The scenarios use the API of module 0.4.0 and pass the
module style test: `python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/tests/board/*.py`.

## Stand

A stand is a local file describing the board's debugger. Copy an example and set the debugger serial
number (`*.local.toml` files are not committed):

| Board | Stand file | Presets |
| --- | --- | --- |
| BlackPill F411CE | `hil/stands/f411ce.local.toml` | `HIL_F411CE`, `HIL_F411CE-host`, `HIL_F411CE-hw` |
| BlackPill F401CC | `hil/stands/f401cc.local.toml` | `HIL_F401CC`, `HIL_F401CC-host`, `HIL_F401CC-hw` |

Environment check without accessing the board:

```powershell
python -B modules/stm32-gdbtest/stm32_gdbtest/cli.py doctor --stand hil/stands/f411ce.local.toml
```

## Running

```powershell
cmake --preset HIL_F411CE
cmake --build --preset HIL_F411CE
ctest --preset HIL_F411CE-host     # no board: requirement traceability and prepare.*
ctest --preset HIL_F411CE-hw       # on the board: all hw.* (22 scenarios)
```

The firmware is programmed only if the Flash image differs (`flash = "if-different"` in the stand).
Do not debug in VS Code and run the tests with the same debugger at the same time.

| Scenario | Checks | Techniques ([catalogue](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/v0.4.0/docs/en/TESTING_TECHNIQUES.md)) |
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
application data in `loop()` (`src/program.cpp`). The contracts in `hil/tests/contracts.json` check
that the macros are in the ELF already in `prepare.*`, without a board.

**No LTO.** The scenarios stop at platform and application functions and substitute their returns;
with LTO functions are inlined and reordered. The build uses `-fno-lto`.

**RTC and the backup domain.** `setup()` sets the calendar to 00-01-01 and an alarm two seconds
later; the backup domain is not reset and an incompatible RTC source is a fault. This is not a check
of LSI accuracy, backup retention or day rollover.

**Sleep.** Ordinary WFI, not Stop: the tests check the wake-up and the interrupted context, not current.

**Results.** The run directory `build/HIL_<board>/hwtest/runs/<time>-<ID>-<pid>/` holds
`result.json`, GDB and server logs, the ELF snapshot and the build manifest.

**History.** Former HAL presets, experiment protocols and stands are in the
[history](../docs/history/README.md) and the [archive](../archive/README.md); their results do not
apply to the current CMSIS firmware.

## Development through DDTT

[Plan](plans/ddtt-feedback.en.md) and [cycle results](plans/ddtt-feedback-results.en.md):
the scenario first exposes the defect in baseline firmware, then checks its fix and regression.
Skill: `.claude/skills/stm32-gdbtest-develop/SKILL.md`; this branch includes a trial copy while
the module gitlink remains on released 0.4.0. Other skill copies are refreshed for 0.4.0.
Unlike stand-loop execution, development needs a source checkout and compiler, not just a ZIP.
Profiles use target schema 2 with `[openocd]`; sessions enable `[results] capture = true`.

New scenario: `HW_ADC_TIMEOUT_DIAGNOSTIC` (`tests/board/test_ddtt_feedback.py`).
