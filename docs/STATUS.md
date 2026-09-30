# Текущее состояние стендового проекта

Срез: 2026-10-01. [Назначение проекта](../README.md).

## Интеграция автономной HAL-регрессии

Закреплён stm32-gdbtest `7f3c65b`, ТЗ 0.40. Три ветки fixture → CI → validation
включены в main модуля; Docs и полный Offline проверены для каждой ревизии.
В модуле теперь находятся [17 HAL-сценариев F030 и их приёмка](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_HAL_VALIDATION.md),
а также [каталог техник](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/TESTING_TECHNIQUES.md).
Ядро stm32_gdbtest не менялось относительно cea01f9; API_VERSION=1.
Firmware и активные профили этого потребителя сохранены.

Локальная проверка интеграции: Windows host 97 (8 платформенных skips) PASS;
247 локальных и закреплённых ссылок на файлы проверены без ошибок.
Linux Docker: пять сборок и 120/120 CTest (105 prepare) PASS.
Результаты — build/ci-reports/summary.json и JUnit/logs рядом.
На этой интеграционной ветке аппаратные тесты не запускались. NUCLEO-F030R8
остаётся с восстановленной исходной HAL-прошивкой после приёмки fixture.
Проверку GitHub Offline для нового SHA потребителя выполнить после push, до land.

## Интеграция пакета F030 и единых имён каталогов

Ветка `codex/module-f030-batch-tests`: gitlink `cea01f9`, ТЗ модуля 0.37.
Четыре ветки модуля включены в его main после проверки опубликованных SHA,
Docs и всех пяти jobs Offline. Добавлены ADC busy, RTC deadline и
[таблица приёмки 17 HAL → 18 CMSIS](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_ACCEPTANCE.md).
HAL-профили здесь сохраняются до отдельной HAL fixture в модуле.

Каталоги тестов потребителя и minimal-consumer переименованы в `tests`,
обновлены импорты, инструменты и документация. `remote.toml` и
`<profile>-remote.toml` исключены из Git; шаблоны остаются отслеживаемыми.
Модуль предпочитает `tests`, сохраняя чтение старых профилей `Tests`;
новые пакеты также используют `profile/tests`. API_VERSION остаётся 1.

Проверки без оборудования:
- Windows: host 97 (8 платформенных skips), F030 build и CTest 20/20;
  minimal-consumer build и offline 3/3 PASS.
- Linux Docker `hwtest-ci`, исходники в чувствительной к регистру файловой
  системе контейнера: пять сборок и 120/120 CTest PASS (105 prepare).
  Отчёты: `build/lowercase-integration/linux-reports/summary.json` и JUnit/logs рядом.
- Реальный импорт 22 модулей сценариев на Windows и Linux PASS;
  185 локальных Markdown-ссылок проверены без ошибок (исходная архитектура исключена).

Firmware не изменялась; HW-запусков на этой интеграционной ветке не было.
NUCLEO-F030R8/ST-Link остаётся на ранее восстановленной HAL-прошивке.
CI этой ветки нужно проверить после push, до land.

## Интеграция CMSIS RTC модуля

Ветка `codex/module-f030-cmsis-rtc`: gitlink обновлён до `5d09823`,
подтверждённого в main модуля после Docs и всех пяти jobs Offline SUCCESS.
[Протокол RTC Alarm A и ограничения](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_RTC.md).
Ядро не изменилось относительно `f494ab1`; firmware потребителя не менялась.
В модуле на новом ELF прошли 16/16 HW-сценариев, включая RTC и регрессию
прежних четырнадцати; HAL-прошивка стенда восстановлена.
Локально Windows host 96 (8 skips), F030 build и CTest host 20/20
(17 prepare) PASS. Лог — build/module-f030-cmsis-rtc-host.log;
JUnit — build/f030r8-debug-hwtest/module-f030-cmsis-rtc.xml.
При обновлении gitlink аппаратные тесты не запускались. GitHub CI
[36750479373](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36750479373)
на `50adc35`: пять профилей PASS; ветка включена в main.

## Интеграция CMSIS Sleep/WFI модуля

Ветка `codex/module-f030-cmsis-sleep`: gitlink обновлён до `f494ab1`,
подтверждённого в main модуля после Docs и всех пяти jobs Offline SUCCESS.
[Протокол Sleep/WFI и границы доказательств](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_SLEEP.md).
Ядро не изменилось относительно `a84b742`; firmware потребителя не менялась.
В модуле аппаратно прошли два новых сценария: SysTick и TIM3 с проверкой
прерванного контекста после WFI. Предыдущие 12 сценариев выполнялись ранее
на том же ELF; это не единый повторный прогон 14 сценариев. HAL восстановлен.
Локально Windows host 96 (8 skips), F030 build и CTest host 20/20
(17 prepare) PASS. Лог — build/module-f030-cmsis-sleep-host.log;
JUnit — build/f030r8-debug-hwtest/module-f030-cmsis-sleep.xml.
При обновлении gitlink аппаратные тесты не запускались. GitHub CI
[36746792618](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36746792618)
на `05a417d`: пять профилей PASS, отчёты сохранены, ветка включена в main.

## Интеграция CMSIS ADC units модуля

Ветка `codex/module-f030-cmsis-adc-units`: gitlink обновлён до `a84b742`,
подтверждённого в main модуля после Docs и всех пяти jobs Offline SUCCESS.
[Протокол физических единиц и численных тестов](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_ADC_UNITS.md).
Ядро не изменилось относительно `a6c0426`; firmware потребителя не менялась.
Локально Windows host 96 (8 skips), F030 build и CTest host 20/20
(17 prepare) PASS. Лог — build/module-f030-cmsis-adc-units-host.log;
JUnit — build/f030r8-debug-hwtest/module-f030-cmsis-adc-units.xml.
Аппаратный запуск при обновлении gitlink не выполнялся. GitHub CI
[36737821520](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36737821520)
на `0f999e2`: пять профилей PASS, отчёты сохранены, ветка включена в main.

## Интеграция CMSIS ADC/DMA модуля

Ветка `codex/module-f030-cmsis-adc-dma`: gitlink обновлён до `a6c0426`,
подтверждённого в main модуля после Docs и всех пяти jobs Offline SUCCESS.
[Протокол ADC/DMA и границы](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_ADC_DMA.md).
Ядро не изменилось относительно `5883316`; firmware потребителя не менялась.
Локально Windows host 96 (8 skips), F030 build и CTest host 20/20
(17 prepare) PASS. Лог — build/module-f030-cmsis-adc-dma-host.log;
JUnit — build/f030r8-debug-hwtest/module-f030-cmsis-adc-dma.xml.
Аппаратный запуск при обновлении gitlink не выполнялся. GitHub CI
[36732675311](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36732675311)
на `b31739a`: пять профилей PASS, отчёты сохранены, ветка включена в main.

## Интеграция CMSIS TIM3/IRQ модуля

Ветка `codex/module-f030-cmsis-timer`: gitlink обновлён до `5883316`,
подтверждённого в main модуля после успешных Docs и всех пяти jobs Offline.
[Протокол TIM3/IRQ](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_TIMER.md).
Ядро не изменилось относительно `40fafac`; firmware потребителя не менялась.
Локально Windows host 96 (8 skips), F030 build, CTest host 20/20
(17 prepare) PASS. Лог — build/module-f030-cmsis-timer-host.log,
JUnit — build/f030r8-debug-hwtest/module-f030-cmsis-timer.xml.
Аппаратный запуск при обновлении gitlink не выполнялся. GitHub CI
[36723196223](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36723196223)
на `be4a196`: пять профилей PASS, отчёты сохранены, ветка включена в main.

## Интеграция CMSIS baseline модуля

Ветка `codex/module-f030-cmsis-baseline`: gitlink обновлён до `40fafac`,
подтверждённого в main stm32-gdbtest. Его Docs и Offline (пять jobs) прошли.
[CMSIS F030: протокол и ограничения](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/7f3c65b5c2b848e67309af63615152385de8976f/docs/ru/F030_CMSIS_BASELINE.md).
Ядро модуля не изменилось относительно `4601888`; firmware этого проекта также
не менялась. Локально Windows host: 96 тестов (8 skips), сборка F030 и
20/20 host CTest, включая 17 prepare, PASS. Новый аппаратный прогон не нужен
для изменения ссылок/gitlink и не выполнялся. GitHub CI [36715492319](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36715492319)
прошёл на `b986b1a`: пять профилей PASS, отчёты сохранены. Ветка включена в main.

## Интеграция переименования tests

Ветка `codex/module-tests-path`: gitlink stm32-gdbtest обновлён до
`46018881d62ce43f80fd79947a31631d745e7f3b`, опубликованного в main модуля.
Обёртка копирует tests/host и tests/fixtures; отсутствие файлов host-тестов
отклоняется до запуска (отрицательная проверка PASS).
Windows host: 96 тестов, 8 platform-specific skips, OK.
Linux Docker/GCC13: пять сборок и 120/120 CTest (105 prepare) PASS.
Логи/JUnit/ELF hashes — `build/ci-reports/`; Windows —
`build/module-tests-path/windows-host.log`. Проверены 49 ссылок на файлы модуля.
Firmware/API не менялись, новый HW-прогон не выполнялся.
Ветка включена в main `8c5b212`; этот раздел сохраняет результаты предыдущего этапа.

## Первый Linux CI build/prepare

Ветка `codex/offline-ci`: [workflow и локальный запуск](CI.md), Docker Linux/amd64,
GCC 13.3.1-1.1, Debug. Локально собраны пять профилей: F030 — 20/20 CTest,
F103/F401/F411/F429 — по 25/25; всего 120, включая 105 prepare. Host-suite
модуля в Linux: 96 тестов, 4 platform-specific skips. Сервер/USB не использовались.

Первый общий прогон обнаружил несовпадение RCC API в GitHub-пакете CubeF1.
После сверки и закрепления HAL v1.1.10 F103 пересобран начисто и повторён
отдельно; остальные четыре профиля прошли в первом прогоне. Контракты не ослаблены.
JUnit и логи — `build/ci-reports/`; исходный итог — `initial-summary.json`,
повтор F103 — `summary.json`. Эмуляторы пока не запускаются.
GitHub [Offline run 36700820252](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36700820252)
для опубликованного `7a198d14c005ce624fea9d3e00961011fd7bb028` проверен:
полный job profiles SUCCESS, все пять профилей PASS, артефакт сохранён.
Land остаётся отдельным действием владельца.

## Обновление модуля: проверки без оборудования

Ветка `codex/module-refresh`: stm32-gdbtest закреплён на
`bc0762502cd7d82c9e44aee8ec7740bea72564f1` (после 0.1.0-rc.1, API 1).
Исходники модуля не менялись. Обёртка host-тестов теперь копирует также
`tools/linux-stand.lock.json` и `ci/dependencies.lock.json`: без них новый тест
согласованности зависимостей ошибочно падал в неполной изолированной копии.

Windows, xPack GCC 13.3.1-1.1, существующие presets `<profile>-debug-hwtest`:

| Профиль | Сборка | CTest `-L host` | Из них `prepare.*` |
| --- | --- | --- | --- |
| f411ce | PASS | 25/25 | 22 |
| f103c8 | PASS | 25/25 | 22 |
| f401cc | PASS | 25/25 | 22 |
| f030r8 | PASS | 20/20 | 17 |
| f429zi | PASS | 25/25 | 22 |

Всего 120 CTest-проверок, включая 105 prepare. Host-набор модуля:
96 тестов, OK, 8 пропусков; количество пропусков относится к этому окружению.
Команды: `cmake --preset <profile>-debug-hwtest`, соответствующий build preset,
`ctest --test-dir build/<profile>-debug-hwtest -L host --output-on-failure`.
Локальные логи — `build/module-refresh/`, JUnit —
`build/<profile>-debug-hwtest/hwtest/module-refresh-junit.xml`, подробные результаты
prepare с хэшами ELF — в `hwtest/runs/` соответствующей сборки.

Проверено существование целей 48 ссылок на документацию новой ревизии модуля.
Аппаратная регрессия F411 описана ниже; остальные старые результаты не подтверждают
регрессию `bc07625`. CI этого потребителя ещё не реализован.

### F411CE / ST-Link, 2026-09-30

Код потребителя `ac8c655`, модуль `bc07625`; публикация обоих SHA подтверждена.
BlackPill F411CE, SWD, без UART и дополнительных перемычек; выбранные локальные
стенды — `blackpill.local.toml` и `blackpill-stlink.local.toml`.
ELF SHA-256: `f5abd37ea5c907b006ca600573355547eeddd516da57e6cf32980e1027511a21`.
DEV_ID=0x431 совпал с профилем, регистр размера Flash — 512 KiB.

- OpenOCD: HW_BOOT через CLI, затем остальные 21 сценарий через CTest — **22/22 PASS**.
  При первом HW_BOOT обнаружено отличие образа, выполнена запись и проверка
  загружаемых ELF-секций, включая LMA .data. Gaps/full-image CRC не проверялись.
- ST-LINK GDB Server: полный набор CTest — **22/22 PASS** на том же ELF.
- Все 44 успешных отчёта содержат `teardown=reset_run`; MCU оставлен работающим.
  Проверены штатные периферийные сценарии и инъекции; отдельный опыт внешнего
  timeout/recovery и full-image на этой ревизии здесь не повторялся.

Первый ST-запуск дал ERROR до подключения: sandbox не имел доступа к каталогу
STM32CubeCLT и сообщал об отсутствии executable. Повтор с разрешённым доступом
подтвердил наличие сервера и прошёл полностью; это не USB-сбой стенда.
Исходный лог сохранён в `build/module-refresh/f411ce-stlink.log`, успешные логи —
`f411ce-openocd.log` и `f411ce-stlink-access.log` того же каталога. JSON в
`build/f411ce-debug-hwtest/hwtest/runs/`, начиная с
`20260930T082259.544617Z-HW_BOOT-12744`; JUnit — `hwtest/module-refresh-*-junit.xml`.
Результат следующего стенда F103C8/J-Link приведён ниже.

### WeAct BluePill-Plus / F103C8 / J-Link, 2026-09-30

Владелец уточнил название подключённой платы: **WeAct BluePill-Plus**, LED PB2.
Выбран прежний профиль `f103c8` (STM32F103C8T6, 64 KiB), SWD,
`bluepill-jlink.local.toml`; название платы не является основанием менять MCU-профиль.
Код потребителя `d9636a4`, модуль `bc07625`; опубликованный SHA потребителя сверён.
ELF SHA-256: `d919d062e99ec90c4a61e4776513d8681128a0c05c180d001b3b5e6f27e2c0dd`.

Полный CTest `-L hw -j 1 --stop-on-failure` — **22/22 PASS**, все отчёты содержат
`teardown=reset_run`. MCU оставлен работающим. Первый HW_BOOT записал отличавшийся
образ и проверил ELF load sections; full-image CRC и отдельный внешний timeout/recovery
не повторялись. DEV_ID=0x410 совпал; регистр Flash показал 128 KiB при профиле 64 KiB.
Получено ожидаемое WARNING, образ помещается в обе границы. Linker не расширялся,
верхние 64 KiB не проверялись, маркировка MCU из этого показания не выводится.

Лог — `build/module-refresh/f103c8-jlink.log`, JUnit —
`build/f103c8-debug-hwtest/hwtest/module-refresh-jlink-junit.xml`, JSON —
`hwtest/runs/` той же сборки, начиная с `20260930T082955.143719Z-HW_BOOT-13108`.
Результаты NUCLEO-F030R8, F429 и F401 приведены ниже.

### NUCLEO-F030R8 / встроенный J-Link STLink, 2026-09-30

Код потребителя `db033af`, модуль `bc07625`; публикация ветки сверена.
SWD, J-Link GDB Server 8.32, firmware J-Link STLink V21 без обновления,
явный stand `nucleo-f030r8-jlink.local.toml`. DEV_ID=0x440, Flash64 KiB совпали.
ELF SHA-256: `cdf421fdad7c6b2637e1c8ce0a257097b373db084c7bb702587b423a3e1323d6`.

Первый набор: HW_BOOT PASS, затем HW_CLOCK ERROR до готовности GDB-сервера
(10 с, последняя строка `Connecting to target...`). Набор остановлен.
Повтор HW_CLOCK в пользовательском окружении — PASS; владелец подтвердил,
что поставил галочку в окне SEGGER. После этого полный повторный набор
CTest `-L hw -j 1 --stop-on-failure` завершён: **17/17 PASS**, все отчёты
содержат `teardown=reset_run`, MCU оставлен работающим.
Таймаут согласуется с известным ожиданием подтверждения условий J-Link STLink;
это не FAIL проверки тактирования. Само повышение прав не объявляется исправлением.

Исходный лог `build/module-refresh/f030r8-jlink.log` сохранён; успешный повтор —
`f030r8-jlink-repeat.log`. JUnit в `build/f030r8-debug-hwtest/hwtest/`:
`module-refresh-jlink-junit.xml` и `module-refresh-jlink-repeat-junit.xml`.
JSON в `hwtest/runs/` той же сборки: ошибка
`20260930T083707.053326Z-HW_CLOCK-30568`, повторный набор начинается
с `20260930T083812.526015Z-HW_BOOT-28740`.
Перед дальнейшими сериями J-Link STLink подтверждать окно условий SEGGER.
Возврат Nucleo к штатной firmware ST-Link владелец выполнит самостоятельно;
новый backend/USB-идентификатор пока не подтверждены.

### STM32F429I-DISCO / ST-Link/V2, 2026-09-30

Код потребителя `fed7335`, модуль `bc07625`; встроенный ST-Link/V2, USB CN1.
Явные стенды `disco-f429zi.local.toml` и `disco-f429zi-stlink.local.toml`.
ELF SHA-256: `d7346f72b1f29ea6864258d13e906cbd87c0ff1b494053b61565d3383f2e9641`.
DEV_ID=0x419, регистр Flash — 2048 KiB.

Полные последовательные наборы CTest `-L hw -j 1 --stop-on-failure`:
OpenOCD **22/22 PASS**, затем ST-LINK GDB Server **22/22 PASS**.
Все 44 отчёта содержат `teardown=reset_run`; MCU оставлен работающим.
USB-сбоя в этих наборах не было; это не доказывает устранение ранее наблюдавшейся
нестабильности длинных серий. Отдельные full-image и timeout/recovery не повторялись.

Логи: `build/module-refresh/f429zi-openocd.log` и `f429zi-stlink.log`.
JUnit: `build/f429zi-debug-hwtest/hwtest/module-refresh-openocd-junit.xml`
и `module-refresh-stlink-junit.xml`; JSON — `hwtest/runs/` той же сборки.
Результат последнего профиля F401CC приведён ниже.

### BlackPill F401CC / внешний ST-Link, 2026-09-30

Владелец заменил F411 на плату STM32F401CCU6 у внешнего ST-Link, SWD.
Код потребителя `53d9332`, модуль `bc07625`; выбран профиль f401cc и явные
стенды `blackpill.local.toml` / `blackpill-stlink.local.toml`.
ELF SHA-256: `05ae583ae8b3559f2f0b3b2c6f960eba821992f6a2c9e1185100479f736b95e1`.
Этот экземпляр: DEV_ID=0x423 и Flash256 KiB совпали с профилем, предупреждений нет.
Это не отменяет ранее зафиксированных отличий DEV_ID у других экземпляров F401.

OpenOCD **22/22 PASS**, затем ST-LINK GDB Server **22/22 PASS**, включая новые
macro-сценарии; все 44 отчёта — `teardown=reset_run`, MCU оставлен работающим.
Логи: `build/module-refresh/f401cc-openocd.log` и `f401cc-stlink.log`.
JUnit — `build/f401cc-debug-hwtest/hwtest/module-refresh-*-junit.xml`, JSON —
`hwtest/runs/` той же сборки, начиная с `20260930T085031.248295Z-HW_BOOT-12964`.

### Итог базовой регрессии bc07625

Пять профилей: сборка и 120/120 CTest host/prepare PASS. Аппаратные наборы:
F411/F401/F429 — по 22/22 через OpenOCD и ST server, F103 — 22/22 через J-Link,
F030 — полный повтор17/17 через встроенный J-Link STLink после окна SEGGER.
Первоначальные ошибки доступа к CubeCLT и запуска J-Link сохранены выше.
Отдельные full-image/внешний timeout/recovery в эту базовую регрессию не входят.
Следующий этап — CI потребителя. Перепрошивка отладчика Nucleo владельцем потребует
отдельной проверки нового backend; сейчас внешний ST-Link занят F401, а не F411.

## Платы и стенды

### Восстановленный ST-Link NUCLEO-F030R8, 2026-09-30

Владелец самостоятельно восстановил штатную firmware **V2J45M31** и подключил
только Nucleo. Новый serial хранится исключительно в локальных stand TOML.
На модуле `bc07625`, базе потребителя `e1038ea` проверены полные наборы:
**OpenOCD17/17 PASS**, **ST-LINK GDB Server17/17 PASS**, без окна SEGGER.
Все 34 отчёта содержат `teardown=reset_run`; MCU оставлен работающим.
DEV_ID=0x440, Flash64 KiB; ELF не менялся:
`cdf421fdad7c6b2637e1c8ce0a257097b373db084c7bb702587b423a3e1323d6`.

Явные стенды: `nucleo-f030r8.local.toml` (OpenOCD) и
`nucleo-f030r8-stlink.local.toml` (ST server из CubeCLT1.22.0).
Версия CubeProgrammer2.23.0 в сообщении владельца относится к его USB-инвентаризации,
а не к инструментам этих тестовых запусков. Firmware отладчика агент не менял.
CMake default для новых F030 build переключён на OpenOCD; существующий cache
обновлён явно и проверено поле stand в session.json. Старый J-Link шаблон и протокол
сохранены; пользоваться его прежним serial для текущей платы нельзя.

Логи — `build/module-refresh/f030r8-restored-openocd.log` и
`f030r8-restored-stlink.log`; JUnit — `build/f030r8-debug-hwtest/hwtest/`
`stlink-restore-openocd-junit.xml` и `stlink-restore-stlink-junit.xml`.
JSON — `hwtest/runs/` той же сборки, начиная с
`20260930T094132.018831Z-HW_BOOT-32340`. Full-image и внешний timeout/recovery
в этой проверке смены backend отдельно не выполнялись.

| Плата | MCU / профиль | LED | Проект производителя |
| --- | --- | --- | --- |
| WeAct BlackPill V3.1 | STM32F411CEU6 / f411ce | PC13 | [MiniSTM32F4x1](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1) |
| WeAct BluePill V1.1 / BluePill-Plus | STM32F103C8T6 / f103c8 | PB2 | [BluePill-Plus](https://github.com/WeActStudio/BluePill-Plus) |
| WeAct BlackPill v3.0 | маркировка STM32F401CCU6 / f401cc | PC13 | [MiniSTM32F4x1](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1) |
| WeAct STM32H503 Core Board | STM32H503CBT6 / h503cb | требует сверки | [STM32H503CoreBoard](https://github.com/WeActStudio/WeActStudio.STM32H503CoreBoard) |

Ревизии и маркировки — по экземплярам владельца. F401 проверен на двух экземплярах
с различными DEV_ID; [результаты и ограничения](TARGET_IDENTITY.md).
H503 приостановлен: генерация сохранена, профиль ещё не включён в сборку.

Сейчас владелец подключил только NUCLEO-F030R8 со штатным ST-Link/SWD.
Другие стенды перед новым запуском требуют подтверждения подключения.
Опыты К1921ВГ015 завершены, его стенд разобран владельцем.
Для каждого аппаратного запуска явно выбирать profile и локальный stand TOML.
Перед сменой платы/отладчика/проводки согласовать замену. UART/VCOM не подключён.

## F429ZI через встроенный ST-Link/V2

[STM32F429I-DISCO](../profiles/f429zi/README.md): сборка GCC13/CubeF4 V1.28.3,
Flash 12744 B, SRAM 1896 B, CCM 0. Подготовлены 22 сценария / 10 контрактов;
traceability и offline ELF/HAL preflight PASS. Через OpenOCD выполнены 22/22 HW,
весь CTest 25/25, LD3 подтверждён. [Протокол](F429_OPENOCD_VALIDATION.md).

ST GDB Server 7.14.0: 18 PASS + USB error, после переподключения оставшиеся 4 PASS;
запись O0/Og, verify-only и timeout/recovery проверены. Последующий полный ST
прогон дал непрерывные 22/22 PASS. В сериях boot: ST24/24 без паузы и24/24 с2с,
OpenOCD22 PASS и USB ERROR на23-м. Причина не установлена, пауза не признана
исправлением. [Протокол ST](F429_STLINK_VALIDATION.md), [устойчивость](F429_SERVER_STABILITY.md).

## F030R8 и граница User/Platform

[NUCLEO-F030R8](../profiles/f030r8/README.md) проверен аппаратно через J-Link STLink:
GCC13/CubeF0 V1.11.6, Flash 11348 B / 64 KiB, RAM 1888 B / 8 KiB
(включая linker reserve heap/stack). На Nucleo/J-Link STLink/SWD выполнены 17/17 HW, LD2 подтверждён.
Подготовлены target Cortex-M0, 17 сценариев и 9 контрактов; offline-проверка PASS.
Для запуска используется nucleo-f030r8-jlink.local.toml с serial встроенного J-Link STLink.
GDB без подключения нашёл app/Platform callbacks и LED/ADC macros в Platform.

User теперь не включает HAL. Адаптеры четырёх профилей обслуживают ADC/DMA,
таймер, LED/Sleep и перенаправляют HAL callbacks в app_*.
Native ADC: прежние формулы и F030 single-point, корректные и неверные входы — PASS.
Собраны F030/F103/F401/F411. После исправления контекста макросов повторены
F411CE/ST-Link/OpenOCD 22/22 и F103C8/J-Link 22/22; оба MCU оставлены running.
Прогоны выполнены в режиме ELF load sections. На момент этого исторического этапа
новые HW-проверки F401 ожидались; они завершены в регрессии bc07625 выше.
F030/J-Link — 17/17 PASS.
См. [наблюдение о контексте макросов](STM32_TESTING_METHODS.md#контекст-hal-макросов-после-отделения-platform).

Текущий этап F030: общий offline checker прошёл на четырёх профилях, включая
traceability и ELF contracts. Отрицательные absent macro/stale manifest отклонены.
После параметризации hadc/TIM повторены F411/OpenOCD 3/3 и F103/J-Link 3/3;
это выборочная регрессия поверх предыдущего полного прогона, F030 позднее проверен через J-Link STLink: 17/17 PASS, [протокол](F030_JLINK_VALIDATION.md).

## Что проверено

Отдельный [PoC К1921ВГ015](K1921VG015_POC.md): bare-metal blink PC0, RISC-V GDB-Python,
неизменённый Target API, пять Flash load sections, 23 проверки поведения, намеренный
FAIL, timeout/recovery и повторный PASS. Видимое мигание подтверждено владельцем.
Пример оставлен на плате работающим. Это экспериментальный lifecycle, не поддержка
К1921 production runner/schema stm32-gdbtest. Выявлено ограничение сравнения sparse ELF.

Общий `User/` выполняет LED blink, ADC temperature/VREFINT через DMA, TIM2 IRQ,
RTC alarm и Sleep/WFI с SysTick. Адаптация MCU — `profiles/<MCU>/Platform`.
CubeMX генерирует код отдельно внутри каждого профиля. Stop пока не реализован.

После подключения отдельного модуля: три профиля собраны и прошли offline-контракты;
F411/OpenOCD и F103/J-Link — по **24/24 CTest** (22 HW + 2 host), host-модуль —
44 unittest. Минимальный consumer, read-only dependency, timeout/recovery и
восстановление основной прошивки также проверены. Это объём сценариев, не процент
покрытия кода и не гарантия всех STM32. Последняя аппаратная проверка F401 была
до переноса macro-сценариев; повтор новых сценариев требует согласованного стенда.

## Сборка и зависимости

Windows, PowerShell, Git, CMake/Ninja, Mike Farah yq v4. Presets требуют CMake >=3.21;
HW-интеграция и минимальный consumer — CMake >=3.25, host Python >=3.11.
Базовый toolchain — xPack ARM GCC 13.3.1-1.1 с GDB-Python; GCC14/15 — отдельные presets.
CubeF4 V1.28.3 и CubeF1 V1.8.7 берутся из установленного STM32Cube Repository.
Toolchain/Cube по умолчанию ищутся в USERPROFILE, локальные пути не коммитить.

Подмодули `stm32-cmake`, `stm32-cmake-yml` и `stm32-gdbtest` закреплены gitlink
основного репозитория; точные коммиты показывает `git submodule status`.
Обновление зависимости — отдельное изменение с регрессией, не автоматическая часть configure.

```powershell
git submodule update --init --recursive
cmake --preset f411ce-debug-hwtest
cmake --build --preset f411ce-debug-hwtest
ctest --preset f411ce-host
```

Для других MCU: `f103c8-debug-hwtest`, `f401cc-debug-hwtest` и соответствующие host presets.
Обычная сборка без HWTEST: `f411ce-debug`; другие варианты — `cmake --list-presets`.
Debug использует `-Og -g3`. Макросы из debug info не сохраняют неиспользуемые функции.
Каждый MCU/toolchain имеет отдельный build; после замены компилятора нужна чистая сборка.

Локальные настройки — игнорируемый `CMakeUserPresets.json`, наследование от точного
preset, например `f411ce-debug`, переменные `CMAKE_USER_HOME` и `STM32_TOOLCHAIN_PATH`.
В VS Code выбрать configure preset, собрать; Cortex-Debug и SVD настроены по профилям.
SVD находятся в `resources`; руководство GDB 19, раздел 23.3 — `docs/gdb.pdf`.
Фактический GDB 14.2.90 проверяется по наличию API, а не по номеру GCC.


## Команды и доказательства

Аппаратные запуски: [HWTEST](HWTEST.md). CLI проекта — `python -B tools/gdbtest.py`;
host ядра — `python -B tools/test_module_host.py`. Протоколы опытов находятся в
[карте документации](README.md); подробности consumer — [CONSUMER_VALIDATION](CONSUMER_VALIDATION.md).
Числа выше относятся к интеграционной проверке после отделения модуля, а не к
новому прогону при каждой правке документации. Версию зависимости фиксирует gitlink.
Планы — [TODO](../TODO.md), изменения — [CHANGELOG](../CHANGELOG.md).

## К1921ВГ015: библиотеки и errata

В отдельном диагностическом примере воспроизведён неверный from_chars на
xPack 13/14 и CloudBEAR 14.1.0.7 Windows даже с ключом обхода у приложения.
Проверены nop и размещение таблиц в RAM; детали, hashes и пределы
вывода — [протокол](K1921VG015_ERRATA.md). Blink восстановлен, 23 проверки PASS.
Production-код модуля не изменён.

## Проверка загружаемых секций ELF

Модуль проверяет Flash по LMA секций, пропуская незагружаемые промежутки; BIN
имеет gap-fill 0xFF. Host53/53, F411/OpenOCD22/22, F103/J-Link22/22; штатный
CTest HW_BOOT после обновления подмодуля PASS на обоих. Полный образ/CRC —
следующий отдельный этап. [Протокол и границы доказательства](ELF_LOAD_REGIONS.md).

## Полный образ, 2026-09-25

Полные 16 KiB, fillFF, canonical BIN/ELF-контейнер и CRC-32/ISO-HDLC по readback
проверены на F411/OpenOCD и F103/J-Link. Host65/65; HW_BOOT/HW_GPIO, реальная
перезапись A5/FF, ожидаемый ERROR verify-only и восстановление PASS.
CRC не вычислялся периферией MCU, прошивка не менялась; полный набор22 в этом
этапе не повторялся. [Протокол и команды](FULL_IMAGE_CRC.md).
