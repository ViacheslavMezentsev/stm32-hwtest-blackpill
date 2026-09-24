# Идентификация MCU и размер Flash

HWTEST выполняет сценарии по явно выбранному профилю. DEV_ID, маркировка корпуса,
заводской размер Flash и название MCU в программе отладчика — отдельные признаки.
Расхождение не приводит к автоматической смене профиля, HAL, linker или ожиданий.

## Политика

По умолчанию `warn`: несовпадение DEV_ID выдаёт WARNING, затем тест продолжается.
`strict` завершает сценарий как ERROR до сравнения/записи Flash. Ошибка чтения
регистра остаётся ERROR в любом режиме. Выбор: CLI `--identity-policy`, затем
переменная `STM32_GDBTEST_IDENTITY_POLICY`, затем `warn`. Пример строгого набора:

```powershell
$env:STM32_GDBTEST_IDENTITY_POLICY = 'strict'
cmake --build --preset f401cc-check-hw
Remove-Item Env:STM32_GDBTEST_IDENTITY_POLICY
```

JSON/JUnit сохраняют `identity` (policy, expected, observed, raw, mask, выбранные
MCU/профиль), `warnings` и `flash_capacity`. PASS остаётся результатом сценария;
он не означает совпадение identity. CLI печатает предупреждение независимо от
PASS/FAIL. CTest скрывает stdout успешных тестов по умолчанию: для просмотра
предупреждений в терминале используйте `ctest --preset f401cc-hw -V`; они также
доступны в JSON/JUnit и LastTest.log. При таймауте GDB итоговый отчёт агента может
отсутствовать; отсутствие identity в таком ERROR не означает её совпадение.

## Flash перед записью

В target.toml schema 1 добавлен `flash_size_address` — адрес 16-битного регистра
размера Flash в KiB: F103 — 0x1FFFF7E0, F401/F411 — 0x1FFF7A22 (CMSIS устройств).
Старый профиль можно прочитать, но аппаратный запуск без этого поля отклоняется
до записи. После изменения target.toml нужна пересборка для нового build manifest.

До чтения/программирования образа агент читает размер и требует:
`0 < image_bytes <= min(profile_bytes, observed_bytes)`. Нулевое значение,
0xFFFF, ошибка чтения либо превышение границы — ERROR независимо от warn/strict.
Если образ помещается, отличие размера от профиля даёт отдельное предупреждение.
Большая память не расширяет выбранный linker/profile автоматически.

Это интерпретация заводского регистра по выбранному профилю, не физическое
тестирование всей памяти. При неизвестном MCU адрес может оказаться неверным;
warning не доказывает совместимость карты памяти и периферии. Для нового семейства
нужно проверить документацию и адрес, а не переносить его по аналогии.
Имена F103C8/CB в программах сами по себе не определяют доступную память.

## F401CC — штатный профиль

Экземпляр с маркировкой STM32F401CCU6, DEV_ID0x431 и Flash256K используется с
обычным f401cc: expected остаётся 0x423, наблюдаемое значение не подменяется.

```powershell
cmake --preset f401cc-debug-hwtest
cmake --build --preset f401cc-debug-hwtest
$env:STM32_GDBTEST_STAND = (Resolve-Path Tests/stands/blackpill.local.toml).Path
cmake --build --preset f401cc-check-hw
# Тот же ST-Link/SWD, другой backend:
$env:STM32_GDBTEST_STAND = (Resolve-Path Tests/stands/blackpill-stlink.local.toml).Path
cmake --build --preset f401cc-check-hw
```

2026-09-24 оба backend дали **24/24 CTest** (22 HW + 2 host); 35 host unittest.
Все 44 HW-отчёта содержат mismatch WARNING и прочитанные 262144 байта Flash.
ELF SHA-256: `252199144197d81984866e60f4f1e4ba54127293ce7ba12f140fc72d90dd7696`.
ADC: 3291 mV; 27323 m°C (OpenOCD), 27009 m°C (ST server). Strict на том же стенде:
ожидаемый ERROR, flashed=false, reset_run. Host-проверки также покрывают нехватку
Flash, больший чип, неверный/нечитаемый размер, совпадение identity и JUnit warnings.
F103/F411 пересобраны и прошли host; аппаратных запусков на них в этом этапе нет.

История эксперимента: [F401_MARKING_EXPERIMENT](F401_MARKING_EXPERIMENT.md).
Старый скрипт теперь делегирует штатному runner без override и не нужен для presets.
observe_sleep также поддерживает warn/strict, но только наблюдает работу: он
не проверяет Flash и должен запускаться после успешного основного набора.

## Проверка BluePill F103C8 / J-Link (2026-09-24)

Штатный f103c8-check-hw с явным bluepill-jlink.local.toml: **24/24 CTest PASS**,
22 HW, 257 проверок, два host CTest (35 unittest). Семь HAL-контрактов PASS;
offline положительный вариант PASS и семь отрицательных вариантов отвергнуты.
ELF SHA-256: `de65834024828db34fa542479fa892e1d14fa764f7d710b95dee595a5899c527`.
Образ 12376 байт записан один раз; все HW-запуски подтвердили содержимое Flash.

DEV_ID=0x410 совпал с профилем. Регистр 0x1FFFF7E0 сообщил **128 KiB** при
**64 KiB** в профиле; во всех 22 отчётах предупреждение о размере, без смены
MCU/профиля или расширения linker. Это пример отдельного расхождения ёмкости,
а не DEV_ID. Прочитанный размер не означает проверку работоспособности верхних
64 KiB или доказательство полного артикула F103CB; верхняя область не тестировалась.

Дополнительный HW_BOOT в strict: PASS, warning размера сохранён. Strict относится
к совпадению DEV_ID; размер всегда ограничивает образ независимо от политики.
ADC: 3302 mV, 27663 m°C, quality=TYPICAL (1), без эталонной проверки точности.
После выхода сервера J-Link Commander прочитал 10 пар DHCSR/uwTick без
halt/reset/go/load: S_SLEEP в 9/10, S_HALT отсутствует, uwTick +354 ms.
Подключение отладчика может влиять на работу; ток не измерялся. Плата оставлена
работающей. BlackPill/ST-Link в этом этапе не использовалась.

Локальные отчёты: build/f103c8-debug-hwtest/hwtest/runs (набор с
20260924T090853.939947Z), live-наблюдение — build/f103c8-identity-live.
Для F411 новая проверка Flash пока подтверждена только host-тестами, нужен стенд.

## Второй экземпляр F401CC / ST-Link (2026-09-24)

Владелец подключил другую плату с маркировкой STM32F401CCU6 вместо первого
экземпляра. На этом экземпляре оба backend прочитали полный IDCODE **0x00016423**,
а DEV_ID (IDCODE & 0xFFF) — **0x423**, то есть совпадение с профилем f401cc.
Flash-регистр — 256 KiB. Это отличается от первого экземпляра с DEV_ID0x431;
полный IDCODE не следует сравнивать непосредственно с 12-битным DEV_ID.

Без изменения прошивки/ожиданий, тот же ELF
`252199144197d81984866e60f4f1e4ba54127293ce7ba12f140fc72d90dd7696`:

- OpenOCD/warn: **24/24 CTest PASS**, 22 HW; образ 12216 байт записан один раз.
  Предупреждений identity/Flash нет. ADC: 3286 mV, 28837 m°C, FACTORY.
- ST server/strict: **13 HW PASS**, затем **9 ERROR до готовности сервера**;
  оба host CTest PASS. Сервер сообщил USB communication error при инициализации
  ST-Link. Эти ERROR не являются результатами проверок периферии MCU.
- Последующее подключение OpenOCD для live Sleep также не удалось; журнал
  показал некорректные сведения об отладчике и unsupported transport.
  Работа MCU после этого сбоя не подтверждена наблюдением. Последний успешный
  HW-сценарий завершился reset_run; это не заменяет проверку текущего состояния.

После подтверждённого владельцем переподключения USB ST-Link, без смены платы
и SWD, полный повтор ST server/strict дал **24/24 CTest PASS** (22 HW,
248 проверок, два host CTest/35 unittest). Identity/Flash совпали во всех
успешных запусках; warnings отсутствуют. ADC: 3286 mV, 28837 m°C, FACTORY —
то же показание в двух наборах, без проверки точности внешним эталоном.

Последующее live-наблюдение через OpenOCD/strict без halt/reset: PASS,
S_SLEEP30/30, uwTick+1433 ms, S_HALT не наблюдался, SLEEPDEEP=0.
Вторая плата оставлена работающей. Firmware отладчика и его настройки не менялись;
причина USB-сбоя не установлена, переподключение восстановило доступ в этом опыте.
BluePill/J-Link не трогали.

Отчёты отделены от первого экземпляра:
`build/f401cc-board2-validation/summary.json`, openocd-ctest.xml, stlink-ctest.xml (неудачный), stlink-retry-ctest.xml (успешный);
live-retry/result.json;
полные журналы находятся по путям из summary. Первый полный успешный OpenOCD
прогон подтверждает стандартный f401cc на экземпляре с ожидаемым DEV_ID.

## F411CE после переключения ST-Link (2026-09-24)

Подтверждённая владельцем F411CE/ST-Link, обычный f411ce-check-hw, strict:
OpenOCD **24/24 PASS**, ST GDB Server **24/24 PASS**. В каждом наборе 22 HW,
248 проверок и два host CTest (35 unittest). DEV_ID0x431 и Flash512 KiB совпадают;
предупреждений нет. Новая Flash guard теперь аппаратно проверена на всех трёх
активных профилях. Наборы не проверяют всю ёмкость памяти.

ELF SHA-256: `dedd1d59c9fadd1ce32c715016260344eb2b33da5c1f92ee14032810672b3009`,
образ12220 байт уже совпал с Flash; запись не потребовалась. ADC: 3300mV,
26838m°C (OpenOCD) / 27155m°C (ST), FACTORY. После ST live OpenOCD/strict PASS:
Sleep29/30, tick+1413ms, S_HALT не наблюдался, SLEEPDEEP=0. Плата оставлена
работающей; BluePill/J-Link не использовалась.

Отдельный опыт чтения HAL-макросов через GDB на этом же ELF — PASS;
методика и ограничения: [STM32_TESTING_METHODS](STM32_TESTING_METHODS.md#hal-макросы-в-gdb-проверка-на-f411ce).
Он не добавлен к числу штатных сценариев. Локальные данные:
build/f411ce-debug-hwtest/hwtest/runs, build/f411ce-macros, build/f411ce-identity-live.
