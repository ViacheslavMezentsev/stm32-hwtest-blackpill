# Rules for developers and AI agents

Communicate with the owner in Russian. Documentation is bilingual: Russian is primary
(`*.md`), English is the translation (`*.en.md`); this file is English only.

## Project

A small demo of [stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest)
(DDTT: debugger-driven testing on target) on WeAct BlackPill boards, built with CMake and
CMSIS only. Boards: `F411CE` (STM32F411CEU6, 512/128 KiB, temperature ADC channel 18) and
`F401CC` (STM32F401CCU6, 256/64 KiB, channel 16); both have the LED on PC13, active low,
and VREFINT on channel 17.

| Path | Contents |
| --- | --- |
| `src/` | Application: `setup()`/`loop()` (`program.cpp`), CMSIS platform (`platform.c`), ADC arithmetic (`adc_units.cpp`) |
| `cmsis/` | Unmodified CMSIS subset from STM32CubeF4 V1.28.3; do not edit or reformat |
| `ld/`, `cmake/` | Linker script template (Flash/RAM from `BOARD`), toolchain and HIL integration (`blackpill.cmake`) |
| `hil/` | HIL: `sessions/` (run configuration per board), `profiles/` (MCU descriptions), `boards/` (board data), `api.toml`, `tests/` (scenarios, requirements, contracts, native ADC test), `stands/` (examples) |
| `ci/` | Offline checks in Docker (`run_cmsis_checks.py`: builds, `prepare.*`, native ADC) |
| `modules/stm32-gdbtest` | Git submodule, pinned to v0.3.0 |
| `.claude/skills/` | Copies of the stm32-gdbtest skills (`stm32-gdbtest-integrate`, `-scenarios`, `-run`); refresh with the submodule |
| `docs/history/`, `archive/` | History of the project stm32-gdbtest was extracted from and retained material (HAL sources, K1921 and H503 examples, experiments); keep, do not update |

## Build and checks

```powershell
cmake --preset Debug_F411CE; cmake --build --preset Debug_F411CE
cmake --preset HIL_F411CE;   cmake --build --preset HIL_F411CE
ctest --preset HIL_F411CE-host          # no board: traceability and prepare.*
ctest --preset HIL_F411CE-hw            # on the board, needs hil/stands/f411ce.local.toml
python -B ci/run_cmsis_checks.py        # the CI check, inside the Docker image of ci/docker
clang-format --dry-run --Werror src/*.cpp src/*.c src/*.h
```

Requirements: CMake ≥ 3.25, Ninja, xPack GNU Arm 13.3.1-1.1 (`ARM_TOOLCHAIN_ROOT` or
`%USERPROFILE%/xpack-arm-none-eabi-gcc-13.3.1-1.1`), Python ≥ 3.11 for HIL.

## Rules

1. Keep `setup()`/`loop()`, `app_state`, `platform_fault`, `platform_tick` and the `platform_*`
   functions readable from GDB: the HIL scenarios depend on these names. Renaming them means
   updating `hil/tests` and `hil/tests/requirements.md` in the same commit. No test hooks in the firmware.
2. Every `@case` ID has a `## HW_...` section in `hil/tests/requirements.md`. Scenarios follow
   the stm32-gdbtest API of the pinned submodule (v0.3.0) and its scenario style
   (`skills/stm32-gdbtest-scenarios` in the module; check with
   `python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/tests/board/*.py`).
   Board-specific expectations belong in `hil/boards/<mcu>.toml`, scenario parameters in
   `hil/api.toml`. When the scenario count changes, update `SCENARIOS` in `ci/run_cmsis_checks.py`.
3. No LTO (`-fno-lto`). No HAL; registers through CMSIS names. The startup code does not run
   dynamic initialization of global C++ objects.
4. Format `src/` with the repository `.clang-format`; never reformat `cmsis/` or `archive/`.
5. Never commit `*.local.toml` or `*-remote.toml` stands, probe serial numbers, personal paths or `build/`.
6. Update `CHANGELOG.md` and `CHANGELOG.en.md` (`[Unreleased]`) for user-visible changes;
   keep RU and EN documents in sync. Mechanism documentation belongs to stm32-gdbtest; boards,
   wiring and measurements belong here.
7. Branches `<agent>/<task>` from an up-to-date `main`; signed Conventional Commits in
   English without links to chat sessions, ending with one `Co-authored-by:` line of the agent
   that took part. Push, `git land`, tags and releases are done by the owner, after the CI of the
   published branch is green.
8. Do not claim hardware results that were not run; state what was checked and how. Run hardware
   only on boards agreed with the owner; the K1921 stand in `archive/` is dismantled.
