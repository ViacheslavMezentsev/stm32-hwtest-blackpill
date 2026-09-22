# WeAct BlackPill v3 — STM32F411CEU6

IOC: `profiles/f411/stm32-hwtest-blackpill.ioc`.
Открывайте перенесённый файл и генерируйте CubeMX-код в эту папку, чтобы Core/Src
и Core/Inc оставались здесь. Сохраняйте USER CODE; toolchain Makefile.
User содержит прикладную прошивку, Tests — её сценарии и требования,
target.toml — параметры цели HWTEST. Cube F4 V1.28.3, 512 KiB Flash / 128 KiB RAM.

Прежние presets `debug`, `release`, `debug-gcc14`, `debug-gcc15`, `debug-hwtest`
выбирают профиль f411. Запуск полного набора: `cmake --build --preset check-hw`.
После добавления новых CubeMX-файлов обновлять Core/CMakeLists.txt и hal_components
соответствующего YAML-профиля; файл IOC сам по себе не добавляет рабочий сценарий.

[План периферии](../../docs/PERIPHERAL_PLAN.md) · [Методика](../../docs/STM32_TESTING_METHODS.md).
