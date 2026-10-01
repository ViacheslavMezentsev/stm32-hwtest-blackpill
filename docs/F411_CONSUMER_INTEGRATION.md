# F411: основа самостоятельного CMSIS-потребителя

[Документация](README.md) · [Состояние](STATUS.md)

Ветка codex/f411-cmsis-consumer-integration от84a257e, 01.10.2026.
Подмодуль обновлён с91a7cd4 на da42cd74c27a01c21df47cd660e2533e9bcfc6d4:
[Docs](https://github.com/ViacheslavMezentsev/stm32-gdbtest/actions/runs/36892241040)
и [полный Offline](https://github.com/ViacheslavMezentsev/stm32-gdbtest/actions/runs/36892241064)
прошли до land; origin/main сверен. Каталог ядра stm32_gdbtest между ревизиями
не изменён. Версия0.1.0rc2/API1, ТЗ0.58; тег rc.2 не перемещён.

## Что проверено

Использован существующий examples/minimal-consumer: самостоятельный CMake,
собственные startup/linker/main и сценарии. Нет зависимости от родительского
YAML, HAL, User или исходников tests/firmware модуля. Добавлена переносимость
путей toolchain/Cube для Linux и проверка двух переключений PC13. Firmware не менялась.

Windows GCC13.3.1-1.1/GDB14.2.90: четыре offline CTest PASS — два prepare,
traceability, manifest/imports/положительный и отрицательный macro preflight.
Стандартные CLI/manifest/contracts/image verification используются без hooks.

Аппаратно: WeAct BlackPill V3.1 STM32F411CEU6, внешний ST-Link/SWD/OpenOCD0.12.0.
UART не подключён. HW_CONSUMER_GPIO и HW_CONSUMER_BLINK PASS; затем прежняя
HAL firmware потребителя восстановлена, HW_BOOT/HW_BLINK PASS, MCU running.
Busy-wait blink не проверяет точность времени или свечение LED.
Новый runtime timeout/recovery в этой серии не инжектировался; прежние протоколы
не выдаются за новое аппаратное доказательство. Другие платы не использовались.

CMSIS ELF SHA256: fb97f86281e45d6ee2af3a83485267b796bbd78de3a8c014fab1c2132e17b9c1.
Restore HAL ELF: f5abd37ea5c907b006ca600573355547eeddd516da57e6cf32980e1027511a21.
Отчёты: build/f411-consumer-integration/summary.json, запуск01.10.2026 16:45 UTC;
локальные serial/stand/артефакты не коммитятся.

## Следующий пакет

Это основа интеграции, не завершённый перенос основного приложения.
Далее собственный F411 CMSIS platform для User: SysTick/TIM2, ADC/DMA с заводской
калибровкой, RTC и Sleep; независимые профильные ожидания, отказы и recovery.
Переиспользовать проверенные приёмы модуля, не подключать tests/firmware как
библиотеку приложения. Сохранить origin/license для заимствованного кода.
После offline и HW приёмки можно заменить основной F411 HAL-профиль, затем
сократить остальные активные профили/presets/CI. Исторические протоколы,
материалы К1921/errata и приостановленный H503 требуют отдельной инвентаризации.
Оптимизация CI остаётся после переноса; этот этап намеренно ещё сохраняет
пять HAL-сборок, чтобы обновление gitlink не потеряло их регрессию.

## Локальная Linux-регрессия

Docker hwtest-ci, без сети: пять HAL-профилей и самостоятельный CMSIS consumer,
суммарно124 CTest PASS (120 HAL +4 consumer). Это результат двух запусков:
первоначально F030/F103 host-тесты не нашли Git-индекс временной копии подмодуля;
после его создания повторены F030/F103 и consumer. Исходный ERROR сохранён в
build/f411-consumer-integration/linux-first-summary.json; итоговая агрегация —
linux-final-summary.json, JSON/JUnit/logs — linux-source/build/ci-reports.
Это offline-доказательство, не Linux HW. Windows host98 (8 skips) PASS;
локальные файловые ссылки Markdown проверены, битых не найдено.
GitHub CI нового коммита ещё требуется перед land.
