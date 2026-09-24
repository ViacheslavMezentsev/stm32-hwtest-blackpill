# stm32-hwtest-blackpill

Минимальный проект для будущего неинвазивного board-тестирования STM32 через GDB-Python.
Несмотря на историческое название репозитория, проект используется с двумя платами.
Отладчик для обеих: WeAct ST-Link v2 с USB-VCOM; подключение SWD, UART/VCOM пока не подключён.

## Используемые платы

| Плата и ревизия | MCU | Профиль | Пользовательский LED | Проект производителя |
| --- | --- | --- | --- | --- |
| WeAct BlackPill V3.1 | STM32F411CEU6 | `profiles/f411ce` | PC13 | [WeActStudio.MiniSTM32F4x1](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1) |
| WeAct BluePill V1.1 | STM32F103C8T6 | `profiles/f103c8` | PB2 | [BluePill-Plus](https://github.com/WeActStudio/BluePill-Plus) |

Ревизии указаны для используемых экземпляров со слов владельца. Имя BluePill
само по себе не задаёт pinout: эта WeAct BluePill V1.1 использует PB2.
Сейчас к стенду подключена BluePill; замену платы согласовываем перед запуском
другого аппаратного профиля. CubeMX-проекты и настройки отладки разделены по MCU.

## Текущее состояние

Обе платы проверены через SWD. Общая прошивка переключает пользовательский LED
примерно каждые 500 мс (полный период — около 1 с). F411 использует HSI 16 МГц,
HCLK 8 МГц, APB1 8 МГц / APB2 2 МГц; F103 — HSI/HCLK/APB1/APB2 8 МГц.
Приложение также выполняет ADC temperature/VREFINT через DMA, считает TIM2 IRQ и RTC alarm.
Во время ожидания LED используется обычный Sleep/WFI с активным SysTick; Stop пока не включён.
Semihosting не требуется. Аппаратный smoke-тест подтвердил запуск, настройки
RCC/GPIO, переключение LED, ход SysTick и обработку ошибки HAL.
Реализована минимальная интеграция hwtest/CTest: 22 аппаратных сценария для каждого профиля (на F103 все проверены, новые F411 ожидают стенда),
прошивка при несовпадении образа, логи и JSON/JUnit. UART/VCOM пока не используется.
Запуск: [HWTEST](docs/HWTEST.md). Первичная проверка: [протокол](docs/HARDWARE_VALIDATION.md).
Методы, границы покрытия и путь к самостоятельному модулю: [практика STM32](docs/STM32_TESTING_METHODS.md).

## Профили MCU

- [profiles/f411ce](profiles/f411ce/README.md): действующий BlackPill, его IOC/Core/Platform и тесты.
- [profiles/f103c8](profiles/f103c8/README.md): BluePill с пользовательским IOC и сгенерированной периферией; прошли 22 аппаратных теста и две host-проверки.

Профиль выбирает `STM32_YML_PROFILE` через stm32-cmake-yml. Старые presets относятся
к F411; `f103c8-debug` собирает F103; оба профиля используют общий прикладной цикл из `User/`.
Для разных MCU обязательны отдельные build-каталоги. Параметры GDB/OpenOCD находятся
в `profiles/<MCU>/target.toml`; оба профиля проверены на своих платах через SWD.
Предложения по ADC/DMA/TIM/RTC/PWR и настройки CubeMX: [план периферии](docs/PERIPHERAL_PLAN.md).

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
cmake --preset f411ce-debug
cmake --build --preset f411ce-debug
```

Другие пары configure/build presets: `f411ce-release`, `f411ce-debug-gcc14`, `f411ce-debug-gcc15`.
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
2. Выполнить `CMake: Select Configure Preset` → `f411ce-debug`.
3. Выполнить `CMake: Configure`, затем `CMake: Build`.
4. После подключения платы выбрать `BlackPill / ST-Link / OpenOCD` и запустить отладку.

Отладочный профиль прошивает ELF выбранной CMake-цели и останавливается в `main`.
GDB по умолчанию берётся из GCC 13; для другого расположения измените пользовательскую
настройку `toolchain` VS Code. OpenOCD проверен через CLI; запуск из интерфейса VS Code ещё не проверен.
VCOM не используется для SWD-прошивки и не настроен в прошивке.

## Аппаратные тесты

Скопируйте `Tests/stands/blackpill.example.toml` в `blackpill.local.toml` в том же
каталоге и укажите серийный номер ST-Link. Локальный файл игнорируется Git.
Текущий подключённый стенд уже настроен локально.

```powershell
cmake --preset f411ce-debug-hwtest
cmake --build --preset f411ce-check-hw
```

Вторая команда собирает ELF и запускает CTest. Режим `flash = "if-different"`
разрешает прошивку выбранного ELF при несовпадении Flash. Для проверки без записи
используйте `flash = "verify-only"`. Отчёты: `build/f411ce-debug-hwtest/hwtest/`.
Только проверки инфраструктуры без платы: `ctest --preset f411ce-host`.

## Первоначальная проверка сборки (до расширения периферии)

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
Сгенерированные CubeMX `profiles/f411ce/Core/Src/syscalls.c` и `sysmem.c` сейчас не включены в сборку.

## Дальнейшая работа

- Фактическая архитектура: [HWTEST_ARCHITECTURE_V2.md](docs/HWTEST_ARCHITECTURE_V2.md).
- Исходный замысел: [HWTEST_ARCHITECTURE.md](docs/HWTEST_ARCHITECTURE.md).
- План: [TODO.md](TODO.md); журнал: [CHANGELOG.md](CHANGELOG.md).
- Правила: [AGENTS.md](AGENTS.md).
- Перед реализацией GDB-Python изучены исходный BOARD_TEST и раздел 23.3 руководства GDB.

## SVD и руководство GDB

`docs/gdb.pdf` хранится в репозитории; Python API описан в разделе 23.3.
Это руководство GDB 19, доступность API сверяется с реально установленным GDB.
В `.vscode/launch.json` каждая конфигурация Cortex-Debug имеет свой `svdFile`:
BlackPill — `resources/STM32F411.svd`, BluePill — `resources/STM32F103.svd`.
Ручное комментирование в settings.json не требуется. Перед запуском выберите
соответствующий CMake preset (`f411ce-debug` / `f103c8-debug`): ELF по-прежнему берётся
из активной цели CMake. Отображение регистров в UI VS Code отдельно не проверялось.
SVD описывает регистры семейства; наличие блока на конкретном MCU сверяется с reference manual.

Пересчёт ADC, источники параметров, статус качества и отдельные численные проверки:
[ADC units](docs/ADC_MEASUREMENTS.md).

Планируемый третий профиль — **h503cb** для готовящейся платы STM32H503:
[этапы и периферия](docs/PERIPHERAL_PLAN.md#будущий-профиль-h503cb-порядок-ввода).
Получены IOC и генерация для подтверждённого владельцем STM32H503CBT6 (128 KiB Flash,
32 KiB RAM), CubeH5 V1.7.0. В сборку профиль пока не включён.
[Настройки CubeMX и результаты аудита](docs/H503_CUBEMX.md),
[проект платы WeAct](https://github.com/WeActStudio/WeActStudio.STM32H503CoreBoard).
LED/ревизию конкретной платы ещё сверяем; подключение H503 согласуем отдельно.
Совместимость общего API с GDB/Python, HAL/CMSIS и сервером отладки описана в
[COMPATIBILITY](docs/COMPATIBILITY.md); наличие общего API не означает одинаковых HAL-контрактов.


Тесты BluePill также проверены напрямую через ST-LINK GDB Server из CubeCLT 1.22.0:
[выбор backend, запуск и сравнение с OpenOCD](docs/GDB_BACKENDS.md).
Меняется локальный TOML стенда, общие Python-сценарии остаются теми же.

BluePill также проверена с прямым **J-Link GDB Server V8.32** (24/24 CTest):
[запуск J-Link и приёмы Commander](docs/JLINK.md). При подключённом J-Link
выбирать `bluepill-jlink.local.toml`; конфигурация по умолчанию не выбирает его автоматически.

BlackPill F411 проверена через OpenOCD и ST-LINK GDB Server на одном ELF: по 24/24 CTest, включая ADC/Sleep, manifest, HAL-контракты и timeout/recovery. [Практические результаты](docs/STM32_TESTING_METHODS.md#f411ce-hal-контракты-и-два-сервера-st-link-2026-09-24).

Профили переименованы в f103c8/f401cc/f411ce/h503cb; F401CC готов к первому аппаратному прогону. [Новые presets, результаты сборки и порядок подключения](docs/PROFILE_MIGRATION.md).
