# Аппаратная проверка минимального потребителя

## Стенд и границы

2026-09-24: WeAct BlackPill V3.1 / STM32F411CEU6, ST-Link по SWD,
OpenOCD, identity policy strict. DEV_ID=0x431, Flash512 KiB.
xPack GCC13.3.1, GDB14.2.90.20240526-git / Python3.11.4, CMSIS из CubeF4 V1.28.3.
BluePill/J-Link не использовалась. Подключения и настройки MCU не менялись.

Потребитель: [minimal-consumer](../examples/minimal-consumer/README.md).
Собственные CMake, firmware, target.toml, Python-тест и helper, без HAL/YAML/framework.
Прошивка не содержит тестовых hooks. Проверка касается runtime GPIO clock/mode,
а не электрического сигнала или визуальной оценки LED.

## Воспроизводимый опыт

Сначала собрать основной f411ce-debug-hwtest и debug потребителя.
Затем из корня репозитория, после подтверждения указанного стенда:

```powershell
python -B Tests/experiments/check_consumer_lifecycle.py --stand Tests/stands/blackpill.local.toml
```

Скрипт проверяет manifest **обоих** ELF до аппаратных действий. В блоке finally
пытается восстановить основную прошивку и выполняет HW_BOOT/HW_BLINK. Ошибка
восстановления остаётся ошибкой опыта и требует внимания; finally не гарантирует
восстановление после отключения питания/обрыва USB/принудительного завершения host.
Локальный TOML должен использовать OpenOCD и flash=if-different. Его verify-only
копия, injected Python-тест и все отчёты остаются в игнорируемом build потребителя.

| Этап | Результат |
| --- | --- |
| HW_CONSUMER_GPIO | PASS, flashed=true, image_verified=true, reset_run |
| Повтор verify-only | PASS, flashed=false, image_verified=true, reset_run |
| Задержка Python после app_loop | Ожидаемый ERROR / TimeoutExpired через 5 s |
| Recovery после timeout | reset_run (host recovery), без teardown_error |
| Повтор после recovery | PASS, verify-only, flashed=false |
| Восстановление HW_BOOT | PASS, flashed=true, image_verified=true, reset_run |
| HW_BLINK основного приложения | PASS, flashed=false, reset_run |

Задержка вводится только в Python: после достижения app_loop записывается marker,
затем sleep60. Marker подтверждает, что таймаут произошёл внутри теста, а не при
запуске сервера. GDB API вызывается только в основном потоке. ERROR этого этапа
не скрывается и остаётся в JSON/JUnit; общий опыт PASS требует именно ожидаемого
таймаута, marker, успешного recovery и следующего положительного теста.

После восстановления отдельное observe_sleep без halt/reset/Flash: PASS,
S_SLEEP30/30, tick+1414ms, never_halted=true, not_deep_sleep=true. MCU оставлен
работающим с основной прошивкой. Это не измерение энергопотребления.

ELF SHA-256:

- consumer: `fb97f86281e45d6ee2af3a83485267b796bbd78de3a8c014fab1c2132e17b9c1`;
- основное приложение: `dedd1d59c9fadd1ce32c715016260344eb2b33da5c1f92ee14032810672b3009`.

Локальные доказательства: `examples/minimal-consumer/build/lifecycle/summary.json`,
подкаталоги этапов с result.json/JUnit/GDB/server/recovery logs и marker;
`build/consumer-restored-sleep` — отдельное наблюдение восстановленной прошивки.
Серийные номера и персональные пути в Git не включаются.

## Переносимость: что подтверждено

Снимки SHA-256 и mtime файлов hwtest до/после consumer+recovery совпали, новых
файлов там нет. Каталоги основного проекта build/hwtest-tmp и build/probe-locks
также не изменились до начала восстановления. Это подтверждает отсутствие
**наблюдаемых изменений** этих каталогов; это не трассировка каждой файловой
операции и не проверка read-only checkout. Отчёты, temp и lock потребителя
созданы внутри его корня. Реальный агент импортировал собственный consumer_support.

Использовался runner API; аппаратный вызов через CTest отдельно не проверялся.
Перенос зависимости в другой checkout, публичный namespace, общая блокировка
отладчика между проектами и независимая установка пока остаются задачами.
Следующий шаг — проверка переноса и read-only dependency, затем механизм общей
блокировки. План и границы: [MODULE_EXTRACTION](MODULE_EXTRACTION.md).
