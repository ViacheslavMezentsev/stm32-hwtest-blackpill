# WeAct BlackPill V3.1 — STM32F411CEU6

[Проект производителя](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1)


IOC: `profiles/f411/stm32-hwtest-blackpill.ioc`.
Открывайте перенесённый файл и генерируйте CubeMX-код в эту папку, чтобы Core/Src
и Core/Inc оставались здесь. Сохраняйте USER CODE; toolchain Makefile.
Общий `../../User` содержит прикладную прошивку, Platform — адаптер F411,
Tests — сценарии и требования,
target.toml — параметры цели HWTEST. Cube F4 V1.28.3, 512 KiB Flash / 128 KiB RAM.

Прежние presets `debug`, `release`, `debug-gcc14`, `debug-gcc15`, `debug-hwtest`
выбирают профиль f411. Запуск полного набора: `cmake --build --preset check-hw`.
После добавления новых CubeMX-файлов обновлять Core/CMakeLists.txt и hal_components
соответствующего YAML-профиля; файл IOC сам по себе не добавляет рабочий сценарий.

[План периферии](../../docs/PERIPHERAL_PLAN.md) · [Методика](../../docs/STM32_TESTING_METHODS.md).

Новый пересчёт ADC по заводским точкам собран; чистая арифметика проверена native-тестом.
Три новых HW_ADC_UNITS/INVALID/VECTORS и перенесённые общие сценарии ожидают
повторного аппаратного прогона после согласованной замены BluePill на BlackPill.
