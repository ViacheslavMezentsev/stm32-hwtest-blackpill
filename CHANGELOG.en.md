# Changelog

All notable changes to this project are documented in this file ([Русский](CHANGELOG.md)).
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Entries before the
documentation alignment are kept in the Russian changelog, most of them with an English summary.

## [Unreleased]

- The stm32-gdbtest submodule is pinned to release v0.6.0 (e68a455, API_VERSION=3); the six skill copies are refreshed and scenarios gains the 0.6.0 routes. Stepping through a scenario uses only `run --interactive`: the module 0.5.x fallback (PYTHONUSERBASE hook, 300 s limit, `manual-runs`) is removed. Scenarios and SVD are unchanged.
- The stm32-gdbtest submodule moves to a7b0951, the final 0.5.0 candidate after the live-observer example's hardware assessment fix (core and API unchanged, version 0.5.0). Skill copies are unchanged.
- Final 0.5.0 candidate acceptance: the stm32-gdbtest submodule moves to 8fdbb58 (version 0.5.0, API_VERSION=3) and the skill copies are refreshed (Agent Skills format, TTDD). Scenarios and SVD are unchanged; host checks run on this gitlink, hardware checks in the P5b campaign.
- Migrate 22 scenarios to API 3/MMIO with a required project SVD (40 registers/values), explicit NVIC/SysTick/ADC/DMA effects and exception cleanup. Pin the module to cb03e86 (0.5.0 candidate), refresh six skills. Add 12 host regressions and SVD/CMSIS checks for F411CE/F401CC; CI checks 25 host/prepare tests per profile. All 22 hw scenarios pass on the F411CE stand; F401CC hardware acceptance is pending.

- Renamed the CMake presets to lowercase (`f411ce-debug/-release/-hil`, `f401cc-*`) with a hidden `base`, like stm32-hwtest-bluepill; updated `.vscode`, `ci/run_cmsis_checks.py`, README and AGENTS. The `hil/` directory now follows the bluepill layout: per-board `hil/F411CE|F401CC/{session,target,board}.toml` and `stands/`, shared `hil/common/{tests,plans}/`, `hil/templates/*.example.toml`, `hil/tools/results.py`. `.clang-format` synced with bluepill.

- Pinned the module to v0.4.0, target schema 2 and capture; refreshed skills and added a trial DDTT development loop.
- An ADC notification timeout now leaves platform_fault code 6. Added HW_ADC_TIMEOUT_DIAGNOSTIC and updated the suppressed callback expectation; 22 scenarios total.

- The project looks like stm32-hwtest-bluepill: README, `hil/README` (RU and EN) and `AGENTS.md` follow the
  common demo layout. Historical documents moved unchanged to `docs/history/` (index in
  `docs/history/README.md`); material outside the demo moved to `archive/` (HAL sources, K1921 and H503
  examples, former stands, experiments and tools); links between them are recomputed. Added `CHANGELOG.en.md`.
- stm32-gdbtest updated to v0.3.0. The board is described by the run configuration `hil/sessions/<mcu>.toml`
  (`SESSION_CONFIG` instead of `PROFILE`): the MCU description, the shared `hil/api.toml` and the board data
  file `hil/boards/<mcu>.toml`. The 18 scenarios are rewritten on API 0.3.0 and three are added
  (`HW_BOARD_PROFILE`, `HW_ADC_WRITER`, `HW_ADC_SERIES`), 21 in total; the offline CI expects 21 `prepare`
  tests. The stm32-gdbtest agent skills are copied to `.claude/skills/`.
