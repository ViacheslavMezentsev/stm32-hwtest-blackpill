# Changelog

All notable changes to this project are documented in this file ([Русский](CHANGELOG.md)).
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Entries before the
documentation alignment are kept in the Russian changelog, most of them with an English summary.

## [Unreleased]

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
