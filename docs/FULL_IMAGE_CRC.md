# Полный образ и CRC по readback, 2026-09-25

Реализован опциональный режим отдельного stm32-gdbtest: явный диапазон,
заполнение дырок/хвоста, программирование полного payload и сравнение всех
байтов вместе с CRC-32/ISO-HDLC. Обычный режим ELF load sections сохранён.
Канонический контракт — [IMAGES модуля](../modules/stm32-gdbtest/docs/IMAGES.md).

## Конфигурация стенда

Платы и соединения не менялись: F411CE/ST-Link/OpenOCD/SWD и
F103C8/J-Link GDB Server/SWD. Код firmware, CubeMX и linker scripts не изменены.
Файлы `profiles/f411ce/full-image.toml` и `profiles/f103c8/full-image.toml`
задают первые **16 KiB**: `[0x08000000, 0x08004000)`, fill 255.
Это не вся Flash и не универсальный размер для будущего firmware; при росте
ELF за границу runner отклонит запуск до сервера. Граница соответствует сектору
16 KiB F411 и страницам F103. Не включать другие данные проекта в эту область.

```powershell
python -B tools/gdbtest.py run --session build/f411ce-debug-hwtest/hwtest/session.json --test HW_GPIO --stand Tests/stands/blackpill.local.toml --image-policy profiles/f411ce/full-image.toml
python -B tools/gdbtest.py run --session build/f103c8-debug-hwtest/hwtest/session.json --test HW_GPIO --stand Tests/stands/bluepill-jlink.local.toml --image-policy profiles/f103c8/full-image.toml
```

Для CTest путь передавать абсолютным:

```powershell
$env:STM32_GDBTEST_IMAGE_POLICY = (Resolve-Path profiles/f411ce/full-image.toml).Path
$env:STM32_GDBTEST_STAND = (Resolve-Path Tests/stands/blackpill.local.toml).Path
ctest --test-dir build/f411ce-debug-hwtest -R '^hw.HW_GPIO$' --output-on-failure
Remove-Item Env:STM32_GDBTEST_IMAGE_POLICY
Remove-Item Env:STM32_GDBTEST_STAND
```

Отсутствие CLI-флага не отключает установленную переменную среды. Режим
не включается глобально и не меняет умолчания профилей/обычных CTest.

## Механизм

Из исходного ELF формируется полный BIN с явным заполнением. Для GDB он
упаковывается в `program.elf` с одной секцией по Flash start. Перед сервером
проверяются границы и обратное преобразование контейнера в тот же BIN.
После load восстанавливаются символы исходного ELF. Это позволяет писать
одинаковые байты внешним программатором (BIN по указанному start) и GDB
(контейнер), сохраняя типы и макросы приложения.

CRC вычисляется **на ПК в GDB-Python по полному readback**, не аппаратным CRC
STM32 и не вызовом функции приложения. Все байты включены; встроенное CRC-поле
не добавляется/не исключается. Параметры, источник вычисления и результаты
сохраняются в result.json. Побайтовое сравнение обязательно даже при совпавшей CRC.

Проверка/стирание/запись вне диапазона не обещаны: backend программирует с учётом
erase-геометрии. Mass erase не добавлен. Другие MCU/backend и смещённое приложение
этим опытом не объявлены поддержанными.

## Доказательства

Host: **65/65**, включая 12 новых тестов политики, CRC-вектора `123456789`,
нечётной длины, повреждения payload/gap/tail, short read, CRC-коллизии-модели
и отказа до процессов при неверной политике.

На каждой плате выполнены:

1. Full FF + HW_BOOT — PASS.
2. Запись полного образа с fill `0xA5` — PASS, flashed=true.
3. Повтор A5 в verify-only — PASS, flashed=false.
4. Политика FF в verify-only поверх A5 — ожидаемый ERROR, flashed=false;
   обнаружено отличие хвоста и CRC.
5. Обычный ELF-sections verify-only поверх того же A5 — PASS: payload совпадает.
6. Восстановление FF — PASS, полный readback и CRC совпали, reset/run.
7. HW_GPIO с контрактом HAL — PASS; отдельно повторены реальные записи A5/FF
   с HW_GPIO в том же запуске, подтверждены макросы после load/symbol-file.

| Плата | Полный диапазон | CRC при FF | CRC при A5 |
| --- | ---: | --- | --- |
| F411CE | 16384 байта | `0x5D500B47` | `0x9AC7A594` |
| F103C8 | 16384 байта | `0x131CFC98` | `0xA0F967BE` |

Payload STM32 в этих ELF непрерывен; аппаратный отрицательный опыт изменяет
хвост (4164/4008 байт), а внутренний gap покрыт host-тестом. Сценарии STM32
в этом этапе не расширялись до прежнего полного набора 22 теста на MCU:
тот набор проверен на этапе [ELF load sections](ELF_LOAD_REGIONS.md).
F103 сохраняет предупреждение о 128 KiB против 64 KiB в профиле; весь опыт
укладывается в 16 KiB. К1921 стенд разобран и не использовался.

Сводка A5/FF опыта: `build/full-image-validation/matrix.json`. Подробные snapshots
и отчёты — профильные `build/*-debug-hwtest/hwtest/runs`. Финальные HW_GPIO с
реальной записью FF: F411 `20260924T190341.615003Z-HW_GPIO-50772`,
F103 `20260924T190347.553267Z-HW_GPIO-57544` (имена каталогов в UTC).
Обе платы оставлены работающими с FF-образом.

Первый preparatory run отклонён **до сервера**: objcopy применяет изменение
адреса к исходному имени `.data` до rename в `.firmware`. Использование нового
имени оставило LMA=0; guard правильно отказал. Команда исправлена, последующие
контейнеры проверены по адресу/длине и roundtrip. Этот ERROR не аппаратный сбой.

Полный FF BIN SHA256: F411
`d1745d558f668cb7faada70d21c3754ca84764fa3627ad7e270947513422f3cf`, F103
`421dce0240d93e75ef7a61c4c38a4b1d716fca01675e6fd18b3eaa18e801eadf`.
Исходные ELF hashes совпадают с предыдущим протоколом ELF_LOAD_REGIONS.md.

После закрепления подмодуля повторены host65/65 и штатный CTest HW_GPIO
с STM32_GDBTEST_IMAGE_POLICY: PASS на обеих платах.

## Следующие шаги

- CRC-поле/исключения и сверка с алгоритмом MCU, включая порядок подачи слов.
- Подготовка/экспорт canonical image без запуска стенда и удобная интеграция VS Code.
- Проверка полного режима через ST GDB Server; пока проверены OpenOCD и J-Link.
- Production-политика разделов Flash и сохранения соседних данных при erase.
