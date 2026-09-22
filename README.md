# stm32-hwtest-blackpill

Минимальный проект для будущего неинвазивного board-тестирования STM32 через GDB-Python.
Плата: WeAct BlackPill v3 (STM32F411CEU6). Пробник: WeAct ST-Link v2 с USB-VCOM.

## Текущее состояние

Сборка восстановлена и проверена на плате через SWD. Прошивка переключает PC13 каждые
500 мс (полный период — около 1 с), использует HSI 16 МГц, APB1/APB2 8 МГц.
Semihosting не требуется. Аппаратный smoke-тест подтвердил запуск, настройки
RCC/GPIO, переключение PC13, ход SysTick и обработку ошибки HAL.
UART/VCOM и полноценная интеграция hwtest/CTest пока не реализованы.
Команды и результаты: [аппаратная проверка](docs/HARDWARE_VALIDATION.md).

## Зависимости

- Windows, Git, CMake >= 3.21 (для presets), Ninja, Mike Farah yq v4 в PATH.
- xPack ARM GCC 13.3.1-1.1 в `%USERPROFILE%/xpack-arm-none-eabi-gcc-13.3.1-1.1`.
- STM32Cube F4 V1.28.3 в `%USERPROFILE%/STM32Cube/Repository/STM32Cube_FW_F4_V1.28.3`.
- Для отладки: OpenOCD в PATH; VS Code с расширениями из `.vscode/extensions.json`.

Подмодули закреплены в Git:

| Модуль | Commit |
| --- | --- |
| stm32-cmake | `ecc5acc082effc4793eb7cbed8d8b7bd4896ca6e` |
| stm32-cmake-yml 0.9.2 | `3d4028eac2ac03c5d14478ed180c706e3825587a` |

HAL/CMSIS берутся из установленного Cube-пакета; автоматически он не скачивается.
Presets передают `CMAKE_USER_HOME` из `USERPROFILE`.

## Сборка в PowerShell

```powershell
git submodule update --init --recursive
cmake --preset debug
cmake --build --preset debug
```

Другие пары configure/build presets: `release`, `debug-gcc14`, `debug-gcc15`.
Для GCC 14/15 ожидаются одноимённые каталоги xPack в папке пользователя.
Каждый preset имеет собственный каталог `build/<preset>`.

Артефакты: `stm32-hwtest-blackpill.elf`, `.bin`, `.hex`, `.map`, `.lss`.
Debug использует `-Og -g3`; Release — стандартный `-O3 -DNDEBUG` и `-g3`.
C++ exceptions и RTTI выключены. Linker script выбран явно; Flash 512 КБ,
RAM 128 КБ, резерв heap 512 байт и stack 1 КБ.

Для других путей создайте игнорируемый Git файл `CMakeUserPresets.json`:

```json
{
  "version": 3,
  "configurePresets": [{
    "name": "local-debug",
    "inherits": "debug",
    "environment": { "CMAKE_USER_HOME": "D:/STM32Packages" },
    "cacheVariables": { "STM32_TOOLCHAIN_PATH": "D:/Toolchains/arm-gcc" }
  }],
  "buildPresets": [{ "name": "local-debug", "configurePreset": "local-debug" }]
}
```

Здесь Cube-пакет должен лежать в `D:/STM32Packages/STM32Cube/Repository`.
После смены toolchain используйте отдельный preset/build-каталог.

## VS Code

1. Установить рекомендованные расширения.
2. Выполнить `CMake: Select Configure Preset` → `debug`.
3. Выполнить `CMake: Configure`, затем `CMake: Build`.
4. После подключения платы выбрать `BlackPill / ST-Link / OpenOCD` и запустить отладку.

Отладочный профиль прошивает ELF выбранной CMake-цели и останавливается в `main`.
GDB по умолчанию берётся из GCC 13; для другого расположения измените пользовательскую
настройку `toolchain` VS Code. OpenOCD проверен через CLI; запуск из интерфейса VS Code ещё не проверен.
VCOM не используется для SWD-прошивки и не настроен в прошивке.

## Проверка сборки

Проверено: CMake 4.4.3, Ninja 1.13.2, yq 4.53.6, Cube F4 V1.28.3.

| Preset | GCC | Flash, байт | RAM с резервами heap/stack, байт |
| --- | --- | ---: | ---: |
| debug | 13.3.1 | 4316 | 1584 |
| release | 13.3.1 | 4584 | 1584 |
| debug-gcc14 | 14.2.1 | 4376 | 1584 |
| debug-gcc15 | 15.2.1 | 4456 | 1584 |

Проверены наличие всех артефактов, единственные startup/system в сборке,
define `STM32F411xE`, начальный SP `0x20020000`, reset-вектор во Flash,
символы основных функций и отсутствие semihosting/BKPT в машинном коде.

Линкер выдаёт предупреждения NoSys об отсутствии `_read`, `_write`, `_close`,
`_lseek`: файловый ввод-вывод не реализован. Эти функции удалены сборщиком
неиспользуемых секций и отсутствуют в конечном ELF; предупреждения не подавляются.
Перед добавлением printf/UART потребуется реализация соответствующего retargeting.
Сгенерированные CubeMX `Core/Src/syscalls.c` и `sysmem.c` сейчас не включены в сборку.

## Дальнейшая работа

- Архитектура: [docs/HWTEST_ARCHITECTURE.md](docs/HWTEST_ARCHITECTURE.md).
- План: [TODO.md](TODO.md); журнал: [CHANGELOG.md](CHANGELOG.md).
- Правила: [AGENTS.md](AGENTS.md).
- До реализации GDB-Python изучить `../buck-boost-course/99_BOARD_TEST` и `Tests`.
