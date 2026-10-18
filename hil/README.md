# HIL-тесты stm32-hwtest-blackpill

[English](README.en.md)

Сценарии [stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest) проверяют
работающую прошивку на плате: runner запускает GDB-сервер отладчика, GDB сбрасывает MCU,
останавливается в `main()` и выполняет сценарий на Python. Отчёты — JSON и JUnit. В прошивку
тестовый код не добавляется.

## Состав

```text
hil/
  common/tests/   board/test_*.py, requirements.md, contracts.json, native/ (арифметика ADC на ПК)
  common/plans/   DDTT
  F411CE/         session.toml, target.toml, board.toml, stands/   (Flash 512 КиБ, DEV_ID 0x431)
  F401CC/         session.toml, target.toml, board.toml, stands/   (Flash 256 КиБ, DEV_ID 0x423)
  templates/      *.example.toml  (stlink, openocd, jlink)
  tools/          results.py
  api.toml        параметры сценариев: сроки, окно VDDA, серия измерений, таймеры
```

Плату выбирает сборка: пресеты `f411ce-hil` и `f401cc-hil` задают `BOARD` и
`BLACKPILL_HIL=ON`, `cmake/blackpill.cmake` подключает stm32-gdbtest v0.4.0 (`modules/stm32-gdbtest`) с
конфигурацией прогона `hil/<MCU>/session.toml` (`SESSION_CONFIG`) и общими сценариями `hil/common/tests`.
Конфигурация связывает описание MCU (`target.toml`), общий `api.toml` и файл данных платы (`board.toml`):
сценарии читают их через `t.profile` (`t.profile.data["board"]`, `t.profile.get("user.timing.adc_deadline_ticks")`),
поэтому один сценарий обслуживает обе платы, а ожидания, зависящие от платы, лежат в данных, а не в коде.
Сценарии написаны на API модуля 0.4.0 и проверяются тестом стиля модуля:
`python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/common/tests/board/*.py`.

## Стенд

Стенд — локальный файл с отладчиком платы. Скопируйте нужный пример из `hil/templates/` в
`hil/<MCU>/stands/local.toml` и укажите серийный номер отладчика (файлы `*.local.toml` не коммитятся):

| Плата | Файл стенда | Пресеты |
| --- | --- | --- |
| BlackPill F411CE | `hil/F411CE/stands/local.toml` | `f411ce-hil`, `f411ce-hil-host`, `f411ce-hil-hw` |
| BlackPill F401CC | `hil/F401CC/stands/local.toml` | `f401cc-hil`, `f401cc-hil-host`, `f401cc-hil-hw` |

| Отладчик | Пример | Серийный номер |
| --- | --- | --- |
| ST-Link, ST-LINK GDB Server (STM32CubeCLT) | `templates/stlink.example.toml` | `STM32_Programmer_CLI -l st` |
| ST-Link, OpenOCD | `templates/openocd.example.toml` | тот же серийный номер ST-Link |
| J-Link | `templates/jlink.example.toml` | десятичный номер из J-Link Commander |

Проверка окружения без обращения к плате:

```powershell
python -B modules/stm32-gdbtest/stm32_gdbtest/cli.py doctor --stand hil/F411CE/stands/local.toml
```

## Запуск

```powershell
cmake --preset f411ce-hil
cmake --build --preset f411ce-hil
ctest --preset f411ce-hil-host     # без платы: трассировка требований и prepare.*
ctest --preset f411ce-hil-hw       # на плате: все hw.* (22 сценария)
python hil/tools/results.py --runs build/f411ce-hil/hwtest/runs
```

Прошивка записывается, только если образ во Flash отличается (`flash = "if-different"` в стенде).
Не запускайте отладку VS Code и тесты одновременно с одним отладчиком.

| Сценарий | Что проверяет | Приёмы ([техники](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/v0.4.0/docs/ru/TESTING_TECHNIQUES.md)) |
| --- | --- | --- |
| `HW_BOOT` | `loop()` без отказа, SYSCLK от HSI 16 МГц без деления шин | таблица `check(rows)`, адрес регистра |
| `HW_CLOCK_GPIO_CONFIG` | HSI, делители, SysTick 1 мс, вывод PC13 | таблица, контракт, TECH-001 |
| `HW_GPIO` | светодиод выключен, включён, выключен на трёх переключениях | ожидания из `profile.data` |
| `HW_BOARD_PROFILE` | MCU, макрос устройства, DEV_ID, F_SIZE, таблица векторов, отказ чтения периферии | TECH-017, `memory`, `refused` |
| `HW_ADC_INIT` | каналы сканирования из файла данных, DMA полуслова с инкрементом | таблица, контракт |
| `HW_ADC_RUNTIME` | одна публикация, качество FACTORY, VDDA в окне `api.toml` | `within`, `profile.get` |
| `HW_ADC_DMA_PUBLICATION` | прерывание DMA, отсчёты из буфера опубликованы один раз после обратного вызова | TECH-003, `memory` |
| `HW_ADC_WRITER` | счётчик измерений пишет `loop()` из `main()` | `watch`, `frames`, TECH-013 |
| `HW_ADC_SERIES` | серия из пяти измерений: подряд, FACTORY, разброс VDDA и температуры | `record`/`records`, TECH-011 |
| `HW_ADC_DISABLED` | сброшенный ADON даёт код отказа 2 | `write` выражением, TECH-006 |
| `HW_ADC_TIMEOUT` | без прерывания DMA приложение выходит по сроку 100 тиков | `write` в NVIC, TECH-006 |
| `HW_ADC_BUSY` | занятый поток DMA даёт код отказа 1 | `write(rows)` |
| `HW_ADC_INVALID` | отсчёты 0 и 4095 дают INVALID, затем восстановление | `write` аргумента, TECH-005 |
| `HW_ADC_VECTORS` | калибровочные отсчёты дают 3300 мВ, 30 и 110 °C | `write(rows)`, TECH-007 |
| `HW_ADC_CALLBACK_SUPPRESSED` | потерянный обратный вызов — срок ожидания без публикации | `ret`, TECH-004 |
| `HW_TIMER` | TIM2 1 кГц / 100 мс, событие доходит до приложения | таблица, `profile.get` |
| `HW_TIMER_IRQ_PUBLICATION` | прерывание TIM2, одно событие на обработчик, возврат в поток | TECH-002, TECH-003 |
| `HW_RTC` | делители RTC, первый alarm через 2 с, перепланирование | таблица, контракт |
| `HW_RTC_DEADLINE` | невыполнимое ожидание LSI даёт код отказа 12 | `reach` с условием, TECH-015 |
| `HW_SLEEP_SYSTICK` | SysTick будит ядро из WFI, интервал idle завершается | `frames`, `memory`, TECH-008 |
| `HW_SLEEP_TIM2` | TIM2 будит ядро из WFI при остановленном SysTick | `write(rows)`, TECH-008 |

## Особенности

**Макросы CMSIS в сценариях.** GDB раскрывает макросы (`RCC`, `ADC_CR2_ADON`, …) в сборке с `-g3`
(все HIL-пресеты), если текущая остановка находится в единице трансляции с `stm32f4xx.h`. Это
`src/platform.c`: регистры проверяются в функциях `platform_*` и обработчиках прерываний, а данные
приложения — в `loop()` (`src/program.cpp`). Контракты `hil/common/tests/contracts.json` проверяют наличие
макросов в ELF ещё в `prepare.*`, без платы.

**LTO не используется.** Сценарии ставят точки на функции платформы и приложения и подменяют их
возврат; с LTO функции встраиваются и переставляются. Сборка — с `-fno-lto`.

**RTC и backup domain.** `setup()` устанавливает календарь 00-01-01 и alarm через две секунды;
backup domain не сбрасывается, несовместимый источник RTC даёт отказ. Это не проверка точности LSI,
сохранения backup domain или перехода через сутки.

**Сон.** Обычный WFI, не Stop: тесты проверяют пробуждение и прерванный контекст, а не ток.

**Результаты.** Каталог запуска `build/<плата>-hil/hwtest/runs/<время>-<ID>-<pid>/` содержит
`result.json`, журналы GDB и сервера, снимок ELF и build manifest.

**История.** Прежние HAL-пресеты, протоколы опытов и стенды — в [истории](../docs/history/README.md)
и [архиве](../archive/README.md); их результаты не относятся к текущей CMSIS-прошивке.

## Разработка через DDTT

[План](common/plans/ddtt-feedback.md) и [результат цикла](common/plans/ddtt-feedback-results.md):
сначала сценарий выявляет дефект на исходной прошивке, затем проверяет исправление и регрессию.
Навык — `.claude/skills/stm32-gdbtest-develop/SKILL.md`; его опытная копия сопровождает эту ветку,
а gitlink модуля остаётся на опубликованной 0.4.0. Остальные копии навыков обновлены для 0.4.0.
В отличие от stand-loop, разработке нужен checkout исходников и компилятор, а не только ZIP.
Профили используют target schema 2 с `[openocd]`; сессии включают `[results] capture = true`.

Новый сценарий: `HW_ADC_TIMEOUT_DIAGNOSTIC` (`common/tests/board/test_ddtt_feedback.py`).
