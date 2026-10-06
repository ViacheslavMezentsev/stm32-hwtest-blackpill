# HIL-тесты stm32-hwtest-blackpill

[English](README.en.md)

Сценарии [stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest) проверяют
работающую прошивку на плате: runner запускает GDB-сервер отладчика, GDB сбрасывает MCU,
останавливается в `main()` и выполняет сценарий на Python. Отчёты — JSON и JUnit. В прошивку
тестовый код не добавляется.

## Состав

```text
hil/
  sessions/<mcu>.toml          конфигурация прогона платы: описание MCU, api.toml, файл данных платы
  profiles/f411ce.toml         описание MCU: Flash 512 КиБ, DEV_ID 0x431, 6 точек останова
  profiles/f401cc.toml         то же, Flash 256 КиБ, DEV_ID 0x423
  boards/<mcu>.toml            файл данных платы: светодиод, RAM, каналы ADC, адреса заводских калибровок
  api.toml                     параметры сценариев: сроки, окно VDDA, серия измерений, таймеры
  tests/requirements.md        требования HW_* (общие для обеих плат)
  tests/contracts.json         контракты: макросы CMSIS в отладочной информации ELF
  tests/board/test_boot.py     HW_BOOT, HW_CLOCK_GPIO_CONFIG, HW_GPIO, HW_BOARD_PROFILE
  tests/board/test_adc.py      HW_ADC_INIT, HW_ADC_RUNTIME, HW_ADC_DMA_PUBLICATION, HW_ADC_WRITER, HW_ADC_SERIES
  tests/board/test_adc_faults.py  HW_ADC_DISABLED, HW_ADC_TIMEOUT, HW_ADC_BUSY, HW_ADC_INVALID,
                               HW_ADC_VECTORS, HW_ADC_CALLBACK_SUPPRESSED — инъекции
  tests/board/test_timers.py   HW_TIMER, HW_TIMER_IRQ_PUBLICATION, HW_RTC, HW_RTC_DEADLINE
  tests/board/test_sleep.py    HW_SLEEP_SYSTICK, HW_SLEEP_TIM2
  tests/native/                арифметика ADC на ПК (CTest, без платы)
  stands/*.example.toml        примеры стендов: ST-Link и OpenOCD
```

Плата выбирается сборкой: пресеты `HIL_F411CE` и `HIL_F401CC` задают `BOARD` и
`BLACKPILL_HIL=ON`, `cmake/blackpill.cmake` подключает stm32-gdbtest v0.3.0 (`modules/stm32-gdbtest`) с
конфигурацией прогона `hil/sessions/<mcu>.toml` (`SESSION_CONFIG`) и общими сценариями `hil/tests`.
Конфигурация связывает описание MCU, общий `api.toml` и файл данных платы: сценарии читают их
через `t.profile` (`t.profile.data["board"]`, `t.profile.get("user.timing.adc_deadline_ticks")`),
поэтому один сценарий обслуживает обе платы, а ожидания, зависящие от платы, лежат в данных, а не в коде.
Сценарии написаны на API 0.3.0 и проверяются тестом стиля модуля:
`python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/tests/board/*.py`.

## Стенд

Стенд — локальный файл с отладчиком платы. Скопируйте пример и укажите серийный номер отладчика
(файлы `*.local.toml` не коммитятся):

| Плата | Файл стенда | Пресеты |
| --- | --- | --- |
| BlackPill F411CE | `hil/stands/f411ce.local.toml` | `HIL_F411CE`, `HIL_F411CE-host`, `HIL_F411CE-hw` |
| BlackPill F401CC | `hil/stands/f401cc.local.toml` | `HIL_F401CC`, `HIL_F401CC-host`, `HIL_F401CC-hw` |

Проверка окружения без обращения к плате:

```powershell
python -B modules/stm32-gdbtest/stm32_gdbtest/cli.py doctor --stand hil/stands/f411ce.local.toml
```

## Запуск

```powershell
cmake --preset HIL_F411CE
cmake --build --preset HIL_F411CE
ctest --preset HIL_F411CE-host     # без платы: трассировка требований и prepare.*
ctest --preset HIL_F411CE-hw       # на плате: все hw.* (21 сценарий)
```

Прошивка записывается, только если образ во Flash отличается (`flash = "if-different"` в стенде).
Не запускайте отладку VS Code и тесты одновременно с одним отладчиком.

| Сценарий | Что проверяет | Приёмы ([техники](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/v0.3.0/docs/ru/TESTING_TECHNIQUES.md)) |
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
приложения — в `loop()` (`src/program.cpp`). Контракты `hil/tests/contracts.json` проверяют наличие
макросов в ELF ещё в `prepare.*`, без платы.

**LTO не используется.** Сценарии ставят точки на функции платформы и приложения и подменяют их
возврат; с LTO функции встраиваются и переставляются. Сборка — с `-fno-lto`.

**RTC и backup domain.** `setup()` устанавливает календарь 00-01-01 и alarm через две секунды;
backup domain не сбрасывается, несовместимый источник RTC даёт отказ. Это не проверка точности LSI,
сохранения backup domain или перехода через сутки.

**Сон.** Обычный WFI, не Stop: тесты проверяют пробуждение и прерванный контекст, а не ток.

**Результаты.** Каталог запуска `build/HIL_<плата>/hwtest/runs/<время>-<ID>-<pid>/` содержит
`result.json`, журналы GDB и сервера, снимок ELF и build manifest.

**История.** Прежние HAL-пресеты, протоколы опытов и стенды — в [истории](../docs/history/README.md)
и [архиве](../archive/README.md); их результаты не относятся к текущей CMSIS-прошивке.
