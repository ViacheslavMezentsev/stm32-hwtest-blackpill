# BluePill STM32F103C8T6 — подготовка профиля

IOC и сгенерированный код добавлены: `profiles/f103/stm32-hwtest-bluepill.ioc`.
MCU: STM32F103C8T6, документированные 64 KiB Flash и 20 KiB RAM.
Не рассчитываем на неофициальные дополнительные 64 KiB.

В CubeMX выберите Project Location так, чтобы `Core/Src`, `Core/Inc` и IOC
оказались именно в этой папке. Имя проекта `stm32-hwtest-bluepill`, toolchain Makefile,
Keep User Code, генерация пар `.c/.h` для периферии. SWD оставить включённым.
Профиль ожидает Cube F1 V1.8.7; при другом пакете согласовать `cubefw_package` в YAML.

После генерации: `cmake --preset f103-debug`, `cmake --build --preset f103-debug`.
Сборка проверена на GCC13. Core/CMakeLists.txt подхватывает generated `.c`;
сгенерированные system/startup/linker подключены явно через YAML без дублирования.
User пока не включён в сборку, main содержит пустой цикл после инициализации.
Общий User/адаптеры профилей и runtime-сценарии будут отдельным этапом.

`target.toml` — начальное описание GDB/OpenOCD, на F103 ещё не проверено.
Проектных Python-тестов пока нет: F411-тесты автоматически не наследуются.
Не подключайте BluePill к F411 debug/hwtest preset.

Предлагаемые периферийные настройки: [план опытов](../../docs/PERIPHERAL_PLAN.md).
