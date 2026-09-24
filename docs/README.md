# Карта документации двух проектов

`stm32-gdbtest` — отдельная инфраструктура. `stm32-hwtest-blackpill` — проект
потребителя и стенд для её развития. Каноническое описание механизма меняется
вместе с кодом модуля; доказательства на платах фиксируются в этом репозитории.
Ссылки в modules показывают документацию именно закреплённой версии зависимости.

| Область | Владелец / источник |
| --- | --- |
| Текущее состояние и точный объём проверки | [стенд](STATUS.md), [модуль](../modules/stm32-gdbtest/docs/STATUS.md) |
| Эксперимент переноса на RISC-V | [К1921ВГ015 PoC](K1921VG015_POC.md), [пример](../examples/k1921vg015-poc/README.md) |
| Проверка errata и библиотек RISC-V | [from_chars / К1921ВГ015](K1921VG015_ERRATA.md) |
| ELF load sections и полный образ/CRC | [протокол](ELF_LOAD_REGIONS.md), [контракт модуля](../modules/stm32-gdbtest/docs/IMAGES.md) |
| API/CLI/CMake, миграция namespace | [модуль: API](../modules/stm32-gdbtest/docs/API.md) |
| Ручное и агентное написание тестов | [модуль: TEST_AUTHORING](../modules/stm32-gdbtest/docs/TEST_AUTHORING.md) |
| ELF/HAL contracts, macro preflight | [модуль: CONTRACTS](../modules/stm32-gdbtest/docs/CONTRACTS.md), [HAL_MACRO_GUIDE](../modules/stm32-gdbtest/docs/HAL_MACRO_GUIDE.md) |
| Build/runtime metadata | [модуль: MANIFESTS](../modules/stm32-gdbtest/docs/MANIFESTS.md) |
| Серверные диалекты, identity/Flash, mutex | [BACKENDS](../modules/stm32-gdbtest/docs/BACKENDS.md), [TARGET_IDENTITY](../modules/stm32-gdbtest/docs/TARGET_IDENTITY.md), [DEBUGGER_OWNERSHIP](../modules/stm32-gdbtest/docs/DEBUGGER_OWNERSHIP.md) |
| Версии и релизы модуля | [модуль: VERSIONING](../modules/stm32-gdbtest/docs/VERSIONING.md), [TODO](../modules/stm32-gdbtest/TODO.md) |
| Сборка/стенды/запуски приложения | [README](../README.md), [HWTEST](HWTEST.md), [BUILD_ARTIFACTS](BUILD_ARTIFACTS.md) |
| MCU, CubeMX, периферия | [PERIPHERAL_PLAN](PERIPHERAL_PLAN.md), [H503_CUBEMX](H503_CUBEMX.md), profiles/*/README.md |
| Результаты и применение механизма | HAL_CONTRACTS, HAL_MACRO_GUIDE, GDB_BACKENDS, JLINK, TARGET_IDENTITY, DEBUGGER_OWNERSHIP в этой папке |
| Измерения и отдельные опыты | [ADC_MEASUREMENTS](ADC_MEASUREMENTS.md), [CONSUMER_VALIDATION](CONSUMER_VALIDATION.md), [F401_MARKING_EXPERIMENT](F401_MARKING_EXPERIMENT.md), [HARDWARE_VALIDATION](HARDWARE_VALIDATION.md) |
| Общие архитектура/методы/совместимость | [HWTEST_ARCHITECTURE_V2](HWTEST_ARCHITECTURE_V2.md), [STM32_TESTING_METHODS](STM32_TESTING_METHODS.md), [COMPATIBILITY](COMPATIBILITY.md) — остаются здесь, со ссылками на модуль |
| История замысла и миграции | [исходная архитектура](HWTEST_ARCHITECTURE.md), [MODULE_SPLIT_PLAN](MODULE_SPLIT_PLAN.md), [PROFILE_MIGRATION](PROFILE_MIGRATION.md), [F401_PROFILE_AUDIT](F401_PROFILE_AUDIT.md) |

Исходный HWTEST_ARCHITECTURE.md сохраняется без изменений; его скелеты не являются
актуальным API. gdb.pdf — справочный документ GDB 19, не описание установленного GDB.
Исторические протоколы фиксируют число тестов и состояние на момент опыта;
фраза «ещё не проверено» внутри такого протокола не заменяет текущую сводку README.

Новый материал о реализации — в модуль; о проводке, firmware, ожиданиях, измерениях —
сюда. Если документ связывает оба проекта, оставить его здесь и ссылаться на модуль,
не копировать его API. Сводка результатов содержит MCU/backend/ELF и границы опыта.
