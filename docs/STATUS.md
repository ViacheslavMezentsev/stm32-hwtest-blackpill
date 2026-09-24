# Текущее состояние стендового проекта

Срез: 2026-09-25. [Назначение проекта](../README.md).

## Платы и стенды

| Плата | MCU / профиль | LED | Проект производителя |
| --- | --- | --- | --- |
| WeAct BlackPill V3.1 | STM32F411CEU6 / f411ce | PC13 | [MiniSTM32F4x1](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1) |
| WeAct BluePill V1.1 / BluePill-Plus | STM32F103C8T6 / f103c8 | PB2 | [BluePill-Plus](https://github.com/WeActStudio/BluePill-Plus) |
| WeAct BlackPill v3.0 | маркировка STM32F401CCU6 / f401cc | PC13 | [MiniSTM32F4x1](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1) |
| WeAct STM32H503 Core Board | STM32H503CBT6 / h503cb | требует сверки | [STM32H503CoreBoard](https://github.com/WeActStudio/WeActStudio.STM32H503CoreBoard) |

Ревизии и маркировки — по экземплярам владельца. F401 проверен на двух экземплярах
с различными DEV_ID; [результаты и ограничения](TARGET_IDENTITY.md).
H503 приостановлен: генерация сохранена, профиль ещё не включён в сборку.

Текущие подтверждённые стенды: F411CE + ST-Link/SWD, F103C8 + J-Link/SWD и NUCLEO-F030R8 + встроенный J-Link STLink/SWD.
Опыты К1921ВГ015 завершены, его стенд разобран владельцем.
Для каждого аппаратного запуска явно выбирать profile и локальный stand TOML.
Перед сменой платы/отладчика/проводки согласовать замену. UART/VCOM не подключён.

## F429ZI через встроенный ST-Link/V2

[STM32F429I-DISCO](../profiles/f429zi/README.md): сборка GCC13/CubeF4 V1.28.3,
Flash 12744 B, SRAM 1896 B, CCM 0. Подготовлены 22 сценария / 10 контрактов;
traceability и offline ELF/HAL preflight PASS. Через OpenOCD выполнены 22/22 HW,
весь CTest 25/25, LD3 подтверждён. [Протокол](F429_OPENOCD_VALIDATION.md).

ST GDB Server 7.14.0: 18 PASS + USB error, после переподключения оставшиеся 4 PASS;
запись O0/Og, verify-only и timeout/recovery проверены. Непрерывные 22/22 пока
подтверждены только для OpenOCD. [Протокол ST](F429_STLINK_VALIDATION.md).

## F030R8 и граница User/Platform

[NUCLEO-F030R8](../profiles/f030r8/README.md) проверен аппаратно через J-Link STLink:
GCC13/CubeF0 V1.11.6, Flash 11348 B / 64 KiB, RAM 1888 B / 8 KiB
(включая linker reserve heap/stack). На Nucleo/J-Link STLink/SWD выполнены 17/17 HW, LD2 подтверждён.
Подготовлены target Cortex-M0, 17 сценариев и 9 контрактов; offline-проверка PASS.
Для запуска используется nucleo-f030r8-jlink.local.toml с serial встроенного J-Link STLink.
GDB без подключения нашёл app/Platform callbacks и LED/ADC macros в Platform.

User теперь не включает HAL. Адаптеры четырёх профилей обслуживают ADC/DMA,
таймер, LED/Sleep и перенаправляют HAL callbacks в app_*.
Native ADC: прежние формулы и F030 single-point, корректные и неверные входы — PASS.
Собраны F030/F103/F401/F411. После исправления контекста макросов повторены
F411CE/ST-Link/OpenOCD 22/22 и F103C8/J-Link 22/22; оба MCU оставлены running.
Прогоны выполнены в режиме ELF load sections. Новые HW-проверки F401 ещё ожидаются; F030/J-Link — 17/17 PASS.
См. [наблюдение о контексте макросов](STM32_TESTING_METHODS.md#контекст-hal-макросов-после-отделения-platform).

Текущий этап F030: общий offline checker прошёл на четырёх профилях, включая
traceability и ELF contracts. Отрицательные absent macro/stale manifest отклонены.
После параметризации hadc/TIM повторены F411/OpenOCD 3/3 и F103/J-Link 3/3;
это выборочная регрессия поверх предыдущего полного прогона, F030 позднее проверен через J-Link STLink: 17/17 PASS, [протокол](F030_JLINK_VALIDATION.md).

## Что проверено

Отдельный [PoC К1921ВГ015](K1921VG015_POC.md): bare-metal blink PC0, RISC-V GDB-Python,
неизменённый Target API, пять Flash load sections, 23 проверки поведения, намеренный
FAIL, timeout/recovery и повторный PASS. Видимое мигание подтверждено владельцем.
Пример оставлен на плате работающим. Это экспериментальный lifecycle, не поддержка
К1921 production runner/schema stm32-gdbtest. Выявлено ограничение сравнения sparse ELF.

Общий `User/` выполняет LED blink, ADC temperature/VREFINT через DMA, TIM2 IRQ,
RTC alarm и Sleep/WFI с SysTick. Адаптация MCU — `profiles/<MCU>/Platform`.
CubeMX генерирует код отдельно внутри каждого профиля. Stop пока не реализован.

После подключения отдельного модуля: три профиля собраны и прошли offline-контракты;
F411/OpenOCD и F103/J-Link — по **24/24 CTest** (22 HW + 2 host), host-модуль —
44 unittest. Минимальный consumer, read-only dependency, timeout/recovery и
восстановление основной прошивки также проверены. Это объём сценариев, не процент
покрытия кода и не гарантия всех STM32. Последняя аппаратная проверка F401 была
до переноса macro-сценариев; повтор новых сценариев требует согласованного стенда.

## Сборка и зависимости

Windows, PowerShell, Git, CMake/Ninja, Mike Farah yq v4. Presets требуют CMake >=3.21;
HW-интеграция и минимальный consumer — CMake >=3.25, host Python >=3.11.
Базовый toolchain — xPack ARM GCC 13.3.1-1.1 с GDB-Python; GCC14/15 — отдельные presets.
CubeF4 V1.28.3 и CubeF1 V1.8.7 берутся из установленного STM32Cube Repository.
Toolchain/Cube по умолчанию ищутся в USERPROFILE, локальные пути не коммитить.

Подмодули `stm32-cmake`, `stm32-cmake-yml` и `stm32-gdbtest` закреплены gitlink
основного репозитория; точные коммиты показывает `git submodule status`.
Обновление зависимости — отдельное изменение с регрессией, не автоматическая часть configure.

```powershell
git submodule update --init --recursive
cmake --preset f411ce-debug-hwtest
cmake --build --preset f411ce-debug-hwtest
ctest --preset f411ce-host
```

Для других MCU: `f103c8-debug-hwtest`, `f401cc-debug-hwtest` и соответствующие host presets.
Обычная сборка без HWTEST: `f411ce-debug`; другие варианты — `cmake --list-presets`.
Debug использует `-Og -g3`. Макросы из debug info не сохраняют неиспользуемые функции.
Каждый MCU/toolchain имеет отдельный build; после замены компилятора нужна чистая сборка.

Локальные настройки — игнорируемый `CMakeUserPresets.json`, наследование от точного
preset, например `f411ce-debug`, переменные `CMAKE_USER_HOME` и `STM32_TOOLCHAIN_PATH`.
В VS Code выбрать configure preset, собрать; Cortex-Debug и SVD настроены по профилям.
SVD находятся в `resources`; руководство GDB 19, раздел 23.3 — `docs/gdb.pdf`.
Фактический GDB 14.2.90 проверяется по наличию API, а не по номеру GCC.


## Команды и доказательства

Аппаратные запуски: [HWTEST](HWTEST.md). CLI проекта — `python -B tools/gdbtest.py`;
host ядра — `python -B tools/test_module_host.py`. Протоколы опытов находятся в
[карте документации](README.md); подробности consumer — [CONSUMER_VALIDATION](CONSUMER_VALIDATION.md).
Числа выше относятся к интеграционной проверке после отделения модуля, а не к
новому прогону при каждой правке документации. Версию зависимости фиксирует gitlink.
Планы — [TODO](../TODO.md), изменения — [CHANGELOG](../CHANGELOG.md).

## К1921ВГ015: библиотеки и errata

В отдельном диагностическом примере воспроизведён неверный from_chars на
xPack 13/14 и CloudBEAR 14.1.0.7 Windows даже с ключом обхода у приложения.
Проверены nop и размещение таблиц в RAM; детали, hashes и пределы
вывода — [протокол](K1921VG015_ERRATA.md). Blink восстановлен, 23 проверки PASS.
Production-код модуля не изменён.

## Проверка загружаемых секций ELF

Модуль проверяет Flash по LMA секций, пропуская незагружаемые промежутки; BIN
имеет gap-fill 0xFF. Host53/53, F411/OpenOCD22/22, F103/J-Link22/22; штатный
CTest HW_BOOT после обновления подмодуля PASS на обоих. Полный образ/CRC —
следующий отдельный этап. [Протокол и границы доказательства](ELF_LOAD_REGIONS.md).

## Полный образ, 2026-09-25

Полные 16 KiB, fillFF, canonical BIN/ELF-контейнер и CRC-32/ISO-HDLC по readback
проверены на F411/OpenOCD и F103/J-Link. Host65/65; HW_BOOT/HW_GPIO, реальная
перезапись A5/FF, ожидаемый ERROR verify-only и восстановление PASS.
CRC не вычислялся периферией MCU, прошивка не менялась; полный набор22 в этом
этапе не повторялся. [Протокол и команды](FULL_IMAGE_CRC.md).
