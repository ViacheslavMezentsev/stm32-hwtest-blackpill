# История проекта

stm32-hwtest-blackpill начинался как стенд для опытов с HAL на нескольких STM32 (F030, F103, F401,
F411, F429, H503) и RISC-V К1921ВГ015. Здесь появился механизм проверки прошивки через GDB-Python,
который затем выделен в отдельный модуль
[stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest). Документы ниже сохранены
без изменения содержания: числа тестов, версии модуля и пути в них соответствуют своему времени и
не описывают текущий проект. Актуальное описание — [README](../../README.md) и
[HIL-тесты](../../hil/README.md); материалы того же периода — в [архиве](../../archive/README.md).

The project began as a HAL test bench on several STM32 parts; stm32-gdbtest was extracted from it.
The documents below are kept unchanged (Russian) and describe their own time, not the current demo.

| Тема | Документы |
| --- | --- |
| Замысел и архитектура | [исходная архитектура](HWTEST_ARCHITECTURE.md), [архитектура v2](HWTEST_ARCHITECTURE_V2.md), [практика тестирования STM32](STM32_TESTING_METHODS.md), [совместимость](COMPATIBILITY.md) |
| Выделение модуля | [граница модуля](MODULE_EXTRACTION.md), [пошаговый переход](MODULE_SPLIT_PLAN.md), [подключение API](STM32_GDBTEST_API.md), [запуск в стендовом проекте](HWTEST.md), [карта документации двух проектов](DOCUMENTATION_MAP.md) |
| Переход HAL → CMSIS | [приёмка CMSIS-приложения](BLACKPILL_CMSIS_APPLICATION.md), [интеграция CMSIS-примеров](CMSIS_INTEGRATION.md), [дополнительные сценарии](CMSIS_RUNTIME_SCENARIOS.md), [F411-потребитель](F411_CONSUMER_INTEGRATION.md), [архив HAL](LEGACY_LAYOUT_REVIEW.md), [дерево после переноса](PROJECT_LAYOUT.md), [согласование с BluePill](REPOSITORY_ALIGNMENT.md) |
| Профили и MCU | [имена профилей и F401CC](PROFILE_MIGRATION.md), [аудит F401CC](F401_PROFILE_AUDIT.md), [F401CC по маркировке](F401_MARKING_EXPERIMENT.md), [H503 и CubeMX](H503_CUBEMX.md), [план периферии](PERIPHERAL_PLAN.md) |
| Механизм на стенде | [серверы GDB](GDB_BACKENDS.md), [J-Link](JLINK.md), [идентификация MCU](TARGET_IDENTITY.md), [владение отладчиком](DEBUGGER_OWNERSHIP.md), [ELF/HAL-контракты](HAL_CONTRACTS.md), [HAL-макросы](HAL_MACRO_GUIDE.md), [ELF load sections](ELF_LOAD_REGIONS.md), [полный образ и CRC](FULL_IMAGE_CRC.md) |
| Аппаратные протоколы | [первичная проверка BlackPill](HARDWARE_VALIDATION.md), [минимальный потребитель](CONSUMER_VALIDATION.md), [F030 через J-Link](F030_JLINK_VALIDATION.md), [F429 / OpenOCD](F429_OPENOCD_VALIDATION.md), [F429 / ST GDB Server](F429_STLINK_VALIDATION.md), [F429: повторные запуски](F429_SERVER_STABILITY.md), [измерения ADC](ADC_MEASUREMENTS.md) |
| RISC-V | [К1921ВГ015: proof-of-concept](K1921VG015_POC.md), [from_chars и errata](K1921VG015_ERRATA.md) |
| CI и сборка | [CI без оборудования](CI.md), [длительность тестов](TEST_TIMING.md), [артефакты сборки](BUILD_ARTIFACTS.md) |
| Состояние и планы | [состояние до выравнивания](STATUS.md), [история состояния](STATUS_HISTORY.md), [дорожная карта](TODO.md), [прежние правила агентов](AGENTS_BEFORE_ALIGNMENT.md) |

`gdb.pdf` — справочник GDB 19, не описание установленного GDB.
