# BlackPill CMSIS HIL

CMSIS-конфигурация приложения: BOARD=F411CE/F401CC.
Debug_F411CE/Debug_F401CC собирают src без HAL; HIL_F411CE/HIL_F401CC
дополнительно подключают сценарии и manifest. Старые HAL-конфигурации находятся в legacy/hal и
не входят в текущие presets. Модуль — stm32-gdbtest v0.3.0 (`modules/stm32-gdbtest`).

```text
hil/
  sessions/<mcu>.toml          конфигурация прогона (SESSION_CONFIG): описание MCU, api.toml, файл данных
  profiles/<mcu>.toml          описание MCU: Flash, DEV_ID, точки останова
  boards/<mcu>.toml            файл данных платы: светодиод, RAM, каналы ADC, адреса заводских калибровок
  api.toml                     параметры сценариев: сроки, окно VDDA, серия измерений, таймеры
  tests/requirements.md        требования HW_* (общие для обеих плат)
  tests/contracts.json         контракты макросов CMSIS по группам сценариев
  tests/board/test_boot.py     HW_BOOT, HW_CLOCK_GPIO_CONFIG, HW_GPIO, HW_BOARD_PROFILE
  tests/board/test_adc.py      HW_ADC_INIT, HW_ADC_RUNTIME, HW_ADC_DMA_PUBLICATION, HW_ADC_WRITER, HW_ADC_SERIES
  tests/board/test_adc_faults.py  HW_ADC_DISABLED, HW_ADC_TIMEOUT, HW_ADC_BUSY, HW_ADC_INVALID,
                                  HW_ADC_VECTORS, HW_ADC_CALLBACK_SUPPRESSED
  tests/board/test_timers.py   HW_TIMER, HW_TIMER_IRQ_PUBLICATION, HW_RTC, HW_RTC_DEADLINE
  tests/board/test_sleep.py    HW_SLEEP_SYSTICK, HW_SLEEP_TIM2
```

21 сценарий на API 0.3.0: таблицы `check(rows)` и `write(rows)`, ожидания именами CMSIS и из файла
данных платы (`t.profile.data["board"]`), параметры из `api.toml` (`t.profile.get(...)`), подмена
возврата `ret`, ожидаемый отказ `refused`, точка наблюдения `watch` с `frames`, серия измерений
через `record`/`records`. Новые в 0.3.0: `HW_BOARD_PROFILE`, `HW_ADC_WRITER`, `HW_ADC_SERIES`.
Стиль проверяет тест модуля:
`python modules/stm32-gdbtest/tests/host/test_scenario_style.py hil/tests/board/*.py`.
Макросы зависят от текущего frame: MMIO проверяется в функциях platform.c, данные приложения — в
loop(). Число сценариев не является покрытием кода.

```powershell
cmake --preset HIL_F411CE; cmake --build --preset HIL_F411CE
ctest --preset HIL_F411CE-host     # без платы: трассировка требований и prepare.*
ctest --preset HIL_F411CE-hw       # на плате, стенд hil/stands/f411ce.local.toml
```

RTC при setup устанавливает календарь00-01-01, затем Alarm A через2 секунды;
app_state.rtc_events инициирует следующее перепланирование в loop. Backup domain
не сбрасывается; несовместимый источник RTC вызывает ошибку. Это не проверка
точности LSI/backup retention/rollover. Sleep — обычный WFI, не Stop/измерение тока.
ADC использует HSI16, PCLK2/2=8MHz, 480 cycles, два halfword в normal DMA2 stream0;
F411 CH18/17, F401 CH16/17. Физическая точность температуры не измеряется.

Аппаратная приёмка обоих MCU и recovery описаны в
[протоколе](../docs/BLACKPILL_CMSIS_APPLICATION.md). Опубликованный CI проверяется
отдельно перед принятием ветки. UART не требуется. Не выбирать стенд по USB enumeration.

## Переход со старых presets

| Прежний HAL preset | Текущая CMSIS-конфигурация |
| --- | --- |
| f411ce-debug / f411ce-release | Debug_F411CE / Release_F411CE |
| f401cc-debug / f401cc-release | Debug_F401CC / Release_F401CC |
| f411ce-debug-hwtest | HIL_F411CE |
| f401cc-debug-hwtest | HIL_F401CC |

Это переход реализации HAL → CMSIS, а не переименование той же сборки.
Не используйте старые build-каталоги с новыми presets. Старые private stand TOML
остались в tests/stands; новые HIL_* hardware presets читают явно выбранный
hil/stands/<mcu>.local.toml. При необходимости перенесите настройки своего
ST-Link вручную, не коммитя serial. HIL_*-host не подключается к отладчику.
Native арифметика проверяется отдельно в hil/tests/native и автоматически в CI.
