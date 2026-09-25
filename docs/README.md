# Карта документации двух проектов

`stm32-gdbtest` — отдельная инфраструктура. `stm32-hwtest-blackpill` — проект
потребителя и стенд для её развития. Каноническое описание механизма меняется
вместе с кодом модуля; доказательства на платах фиксируются в этом репозитории.
Ссылки на документацию подмодуля ведут прямо в его GitHub-репозиторий на
закреплённый коммит. Относительный путь через modules работает локально, но
не позволяет GitHub открыть вложенный файл подмодуля. При обновлении gitlink
проверять и обновлять commit в таких ссылках вместе с документацией.

| Область | Владелец / источник |
| --- | --- |
| Текущее состояние и точный объём проверки | [стенд](STATUS.md), [модуль](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/STATUS.md) |
| Эксперимент переноса на RISC-V | [К1921ВГ015 PoC](K1921VG015_POC.md), [пример](../examples/k1921vg015-poc/README.md) |
| Проверка errata и библиотек RISC-V | [from_chars / К1921ВГ015](K1921VG015_ERRATA.md) |
| Полный образ / CRC по readback | [проверка на стендах](FULL_IMAGE_CRC.md), [политика модуля](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/IMAGES.md) |
| ELF load sections и полный образ/CRC | [протокол](ELF_LOAD_REGIONS.md), [контракт модуля](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/IMAGES.md) |
| API/CLI/CMake, миграция namespace | [модуль: API](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/API.md) |
| Ручное и агентное написание тестов | [модуль: TEST_AUTHORING](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/TEST_AUTHORING.md) |
| ELF/HAL contracts, macro preflight | [модуль: CONTRACTS](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/CONTRACTS.md), [HAL_MACRO_GUIDE](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/HAL_MACRO_GUIDE.md) |
| Build/runtime metadata | [модуль: MANIFESTS](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/MANIFESTS.md) |
| Серверные диалекты, identity/Flash, mutex | [BACKENDS](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/BACKENDS.md), [TARGET_IDENTITY](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/TARGET_IDENTITY.md), [DEBUGGER_OWNERSHIP](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/DEBUGGER_OWNERSHIP.md) |
| Версии и релизы модуля | [модуль: VERSIONING](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/VERSIONING.md), [TODO](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/TODO.md) |
| Сборка/стенды/запуски приложения | [README](../README.md), [HWTEST](HWTEST.md), [BUILD_ARTIFACTS](BUILD_ARTIFACTS.md) |
| Nucleo F030 / адаптация приложения | [профиль F030R8](../profiles/f030r8/README.md) и [аппаратный протокол](F030_JLINK_VALIDATION.md) — 17/17 через J-Link STLink |
| Discovery F429ZI | [профиль и настройки](../profiles/f429zi/README.md) — [22/22 HW через OpenOCD](F429_OPENOCD_VALIDATION.md) |
| Discovery F429 / ST server | [протокол, USB-сбой и восстановление](F429_STLINK_VALIDATION.md) |
| Повторные запуски F429 | [сравнение ST/OpenOCD, USB и пауз](F429_SERVER_STABILITY.md) |
| MCU, CubeMX, периферия | [Общая матрица пяти профилей, уровни стенда и пакеты P1–P8](PERIPHERAL_PLAN.md), [H503_CUBEMX](H503_CUBEMX.md), profiles/*/README.md |
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
