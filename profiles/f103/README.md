# BluePill STM32F103C8T6 — подготовка профиля

Положите ваш IOC сюда: `profiles/f103/stm32-hwtest-bluepill.ioc`.
MCU: STM32F103C8T6, документированные 64 KiB Flash и 20 KiB RAM.
Не рассчитываем на неофициальные дополнительные 64 KiB.

В CubeMX выберите Project Location так, чтобы `Core/Src`, `Core/Inc` и IOC
оказались именно в этой папке. Имя проекта `stm32-hwtest-bluepill`, toolchain Makefile,
Keep User Code, генерация пар `.c/.h` для периферии. SWD оставить включённым.
Профиль ожидает Cube F1 V1.8.7; при другом пакете согласовать `cubefw_package` в YAML.

После генерации: `cmake --preset f103-debug`, `cmake --build --preset f103-debug`.
До появления IOC и main.c Configure намеренно сообщает, чего не хватает.
Core/CMakeLists.txt подхватывает generated `.c`; system/startup пока берутся из CMSIS,
linker script — из фреймворка. CubeMX linker/startup рядом с IOC пока не подключаются.
После получения IOC проверим clock tree, HAL-компоненты, startup и linker отдельно.

`target.toml` — начальное описание GDB/OpenOCD, на F103 ещё не проверено.
Проектных Python-тестов пока нет: F411-тесты автоматически не наследуются.
Не подключайте BluePill к F411 debug/hwtest preset.

Предлагаемые периферийные настройки: [план опытов](../../docs/PERIPHERAL_PLAN.md).
