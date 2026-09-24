# Минимальный HWTEST для BlackPill и BluePill

## Границы реализации

Поддерживается Windows и один выбранный SWD-стенд: F411/F103 через OpenOCD,
F103 также проверен через ST-LINK GDB Server 7.14.0 и J-Link GDB Server V8.32.
[Выбор сервера и различия](GDB_BACKENDS.md).
UART/VCOM не нужен. Прошивка не содержит тестового кода. Проверен Debug на GCC 13.3.1,
GDB 14.2.90.20240526-git с Python 3.11.4 и OpenOCD 0.12.0.
Host Python >= 3.11 требуется для стандартного TOML-парсера.

Код и тесты BlackPill находятся в profiles/f411ce. F103 находится в profiles/f103c8; на F103 прошли 22 аппаратных сценария; F411 ранее прошёл 17, новый пересчёт ожидает аппаратной проверки. См. [профили](PERIPHERAL_PLAN.md).
HWTEST получает target.toml через session.json и проверяет DBGMCU ID до прошивки.

Это реализация Level 1 из архитектурного документа: явное подключение после
`stm32_yml_setup_project`. Мультиплатформенность, другие отладчики, multi-node,
JUnit-сервис CI и автоматический SKIP не заявлены. Отсутствие выбранного стенда
или отладчика — ERROR; оно не должно создавать ложный зелёный прогон.

## Настройка

```powershell
Copy-Item Tests/stands/blackpill.example.toml Tests/stands/blackpill.local.toml
```

Указать в локальном TOML реальный `serial`, при необходимости путь `executable`
к OpenOCD. Номер можно получить командой `STM32_Programmer_CLI -l stlink-only`.
Локальные файлы `Tests/stands/*.local.toml` не включаются в Git.

`flash = "if-different"`: при несовпадении прошить ELF, проверить Flash чтением,
затем начать тест. `flash = "verify-only"`: никогда не прошивать; несовпадение — ERROR.
Сравнение включает начальные данные `.data` по их загрузочному адресу во Flash.
Реализация предполагает обычный связный образ F411 с началом Flash `0x08000000`.

Путь стенда выбирается при запуске: `--stand` → `STM32_GDBTEST_STAND` в окружении →
`STM32_GDBTEST_STAND` из CMake session.json. Смена стенда через окружение не требует пересборки.
Другие исполняемые файлы GDB выбираются CMake-параметром `STM32_GDBTEST_GDB`.

## Команды

```powershell
cmake --preset f411ce-debug-hwtest
cmake --build --preset f411ce-check-hw
```

`check-hw` сначала собирает ELF, затем запускает все CTest-проверки и создаёт
`build/f411ce-debug-hwtest/hwtest/ctest-junit.xml`.

```powershell
# Повторный прогон уже собранного проекта, до четырёх CTest jobs:
ctest --preset f411ce-hw
# Без платы:
ctest --preset f411ce-host
# Отдельная проверка:
ctest --preset f411ce-hw -R '^hw.HW_CLOCK$'
# Host CLI, например с другим локальным стендом:
python -B tools/gdbtest.py run --session build/f411ce-debug-hwtest/hwtest/session.json --test HW_BOOT --stand Tests/stands/blackpill.local.toml
```

Прямой `ctest` не собирает прошивку. Для цикла «изменить → собрать → проверить»
используйте `check-hw`. Новые `test_*.py` и изменения метаданных учитываются при
следующей конфигурации/сборке CMake.

## Слои

| Файл | Ответственность |
| --- | --- |
| stm32_gdbtest/cmake/STM32GDBTest.cmake | session.json, регистрация CTest, цель check-hw |
| stm32_gdbtest/collect.py | AST-сбор `@case` без импорта тестов; сверка ID требований |
| stm32_gdbtest/runner.py | снимок ELF, GDB/backend, сроки ожидания, восстановление |
| stm32_gdbtest/backends.py | запуск, готовность, reset и finish OpenOCD/ST-LINK/J-Link |
| stm32_gdbtest/processes.py | блокировка отладчика и завершение созданных деревьев процессов |
| stm32_gdbtest/openocd.py | TOML стенда, аргументы сервера по профилю |
| stm32_gdbtest/profile.py | проверка схемы target.toml |
| stm32_gdbtest/agent.py | подключение, проверка/загрузка образа, запуск теста, диагностика |
| stm32_gdbtest/target.py | breakpoint events, проверки, чтение значений и fault injection |
| stm32_gdbtest/reports.py | JSON/JUnit и различение FAIL/ERROR |
| profiles/f411ce/Tests/board/test_blackpill.py | пять базовых сценариев поведения прошивки |
| profiles/f411ce/Tests/board/test_peripheral_methods.py | четыре сценария проверки контрактов и инъекций |
| profiles/f411ce/Tests/requirements.md | проверяемые требования с такими же ID |

## Жизненный цикл и отчёты

Каждый запуск создаёт уникальный каталог в `build/f411ce-debug-hwtest/hwtest/runs`.
В нём: копия `firmware.elf`, полученный из неё `image.bin`, `prepare.log`,
`server.log`, `gdb.log`, `run.json`, `agent-result.json`, итоговые `result.json`
и `junit.xml`; при аварийном восстановлении — `recovery.log`.
Раннер не меняет сборочный ELF и не использует старые отчёты.

Каждый тест сверяет образ с Flash под блокировкой, затем заново делает reset/halt
и достигает main. На выходе — reset/run и закрытие процессов. Если GDB завис,
хост завершает его дерево и пытается восстановить reset/run отдельным подключением.
Ошибка восстановления отражается в отчёте; это не гарантия восстановления при
физическом отключении USB/питания.

Коды: 0 PASS; 1 FAIL проверки поведения; 2 ERROR инфраструктуры/таймаута.
JUnit использует соответственно отсутствие ошибки, `failure` и `error`.
Записываются SHA-256 ELF/BIN, факт прошивки, результаты отдельных проверок,
версии GDB/Python, события остановки. При ошибке на цели собираются PC/LR/SP/xPSR,
CFSR/HFSR и backtrace, когда связь ещё доступна.

CTest `RESOURCE_LOCK` сериализует аппаратные тесты даже при `-j`.
Файловая блокировка в `build/probe-locks` дополнительно защищает от второго запуска
из этого checkout, включая старый smoke-раннер. Она не координирует другие checkout
или сторонние отладчики. Нельзя одновременно запускать VS Code debug и hwtest.

Таймаут GDB — из `@case(timeout_s=...)` (20 секунд по умолчанию), ограничивает
подключение/проверку/прошивку/исполнение вместе. У подготовки, старта сервера и
восстановления есть отдельные пределы. CTest даёт ещё 90 секунд на эти операции.
Убивать CTest или Python принудительно извне не является поддержанным teardown:
MVP использует taskkill для своих дочерних процессов, а не Windows Job Object.

Все записываемые проектом артефакты, временные каталоги и блокировки находятся
в текущем репозитории. Подмодули, соседние проекты и установленные инструменты
не изменяются. Ограничение пути вывода проверяется перед созданием файлов.

## Учтённые правила GDB Python

Изучен раздел 23.3 локального `docs/gdb.pdf` (GDB 19). Его новые API не считаются
доступными автоматически: у используемого GDB нет `gdb.interrupt` и
`Value.is_unavailable`. Таймаут находится в отдельном host-процессе.

GDB API вызывается только из главного потока. Причина остановки определяется через
`gdb.events.stop` и номер ожидаемого breakpoint; одного имени кадра недостаточно.
В callback фиксируются примитивные значения, поскольку временная точка затем удаляется.
Кадры и lazy values не сохраняются между `continue`; значения извлекаются до продолжения.
В fault injection используется `return`, без следующего `finish` вызывающей функции.

## Проверка реализации

- `check-hw`: 14/14 PASS — двенадцать аппаратных тестов, трассируемость и набор из девяти host-тестов.
- `ctest --preset f411ce-hw` с jobs=4: аппаратные проверки не пересекаются.
- Намеренно неверное ожидание: FAIL/код 1, JUnit failure.
- Перевод PC на fault-handler вместо ожидаемого loop: FAIL, причина остановки и регистры сохранены.
- Несовпадающий ELF в verify-only: ERROR/код 2, запись не выполняется.
- Изменённое начальное значение `.data`: автоматическая прошивка с `flashed=true`;
  следующий штатный тест восстановил правильный ELF с повторной верификацией.
- Отсутствующий выбранный серийный номер: ERROR, лог OpenOCD сохранён.
- Таймаут 0.01 с и зависание в Error_Handler с таймаутом 2 с: ERROR и host recovery.
- После отказных сценариев HW_BLINK снова PASS, плата оставлена выполнять обычную прошивку.

Fault-handler для негативного сценария достигался искусственным изменением PC:
это проверка классификации остановки, не испытание аппаратного механизма HardFault.
Тесты GPIO читают ODR и HAL tick; электрические уровни, физическое свечение LED
и точность частоты осциллятора этой проверкой не измеряются.

Новые методы `reach(when=...)`, `fields`, `set_value`, результаты опытов
и ограничения переносимости описаны в [STM32_TESTING_METHODS.md](STM32_TESTING_METHODS.md).


## BluePill F103 и форматирование User

Для BluePill используйте `Tests/stands/bluepill.local.toml`, configure preset
`f103c8-debug-hwtest`, build preset `f103c8-check-hw`, test preset `f103c8-hw`.
Не запускайте F411 preset на BluePill. Тесты/требования раздельные, IDs локальны
профилю; отчёты сохраняются в соответствующем build-каталоге.

Форматирование касается только исходников `User`; конфигурация — корневая
`.clang-format`, проверенная версия инструмента — 23.1.1.

```powershell
clang-format -i User/Inc/app.h User/Src/program.cpp User/Src/adc_units.cpp
clang-format --dry-run --Werror User/Inc/app.h User/Src/program.cpp User/Src/adc_units.cpp
```

CubeMX/Core и зависимости в эту команду не входят. Семантика User не менялась.
Отдельная регрессия API GDB без платы (нужен GDB с Python):

```powershell
arm-none-eabi-gdb-py3 -q -nx -batch -ex "source Tests/gdb/check_breakpoint.py"
```

Проверяется немедленный отказ на неизвестный символ и удаление pending breakpoint.
`set breakpoint pending off` само по себе не запрещает создание pending breakpoint
через Python API в установленном GDB; Target проверяет свойство `Breakpoint.pending`.


## Общие проектные сценарии

`Tests/scenarios` содержит общие проверки приложения. `profiles/<MCU>/Tests/board`
сохраняет функции с буквальными `@case` для AST-сбора; обёртки передают
`Tests/expectations.py` своего профиля. Три init-теста остаются локальными:
они непосредственно описывают различные регистры ADC/DMA/TIM/RTC.
При добавлении MCU не копируйте алгоритм сценария: задайте его ожидания и
требования. При изменении поведения приложения меняйте общий сценарий и
проверяйте все доступные профили. Совпадение ID между профилями допустимо —
сбор и отчёты ведутся отдельно. `hwtest` ничего не знает об app_state и ADC units.

Новые проверки пересчёта и native-команды описаны в [ADC_MEASUREMENTS](ADC_MEASUREMENTS.md).


## LED не мигает

Проверяйте pinout конкретной платы: текущая WeAct F103 использует PB2,
BlackPill F411 — PC13. Отсутствие свечения не доказывает halt/Stop.
Тесты завершаются reset_run и отключением GDB; в E07 дополнительно проверена
работа PB2/SysTick/ADC после этого, без новых halt/reset. Метод и ограничения
описаны в [STM32_TESTING_METHODS](STM32_TESTING_METHODS.md#e07--правильный-gpio-тест-не-доказывает-соответствие-плате).


## Наблюдение Sleep после тестов

```powershell
cmake --preset f103c8-debug-hwtest
cmake --build --preset f103c8-check-hw
python -B tools/observe_sleep.py --session build/f103c8-debug-hwtest/hwtest/session.json
```

Наблюдатель не прошивает, не сбрасывает и не останавливает MCU. Он проверяет ID
профиля, читает DHCSR/SCR, uwTick по адресу из ELF и DBGMCU_CR. PASS требует хотя бы
одного S_SLEEP, отсутствия S_HALT/SLEEPDEEP и продвижения uwTick. OpenOCD запускается
с выключенными серверными портами, используется общая блокировка отладчика.
Есть внешний таймаут; результаты — build/sleep-observation/result.json и openocd.log.

Перед наблюдением нужен успешный check-hw: наблюдатель сам не сверяет Flash с ELF.
Он использует путь стенда из session.json. Допустимы --samples 5..100,
--interval-ms 10..500, --out внутри текущего репозитория. По умолчанию 30 выборок
с паузой 37 мс; это не измерение процента времени сна или энергопотребления.
Проверка на halted MCU должна дать FAIL, а не трактовать отсутствие работы как Sleep.
См. опыт E08 в [методике](STM32_TESTING_METHODS.md).
