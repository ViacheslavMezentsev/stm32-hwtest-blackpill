# Текущее состояние стендового проекта

Срез: 2026-09-24. [Назначение проекта](../README.md).

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

Последний подтверждённый для текущего опыта стенд: К1921ВГ015 + J-Link EDU v11/JTAG.
Ранее проверенные STM32-стенды: F411CE + ST-Link/SWD и F103C8 + J-Link/SWD;
в опыте К1921 они не использовались.
Для каждого аппаратного запуска явно выбирать profile и локальный stand TOML.
Перед сменой платы/отладчика/проводки согласовать замену. UART/VCOM не подключён.

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
