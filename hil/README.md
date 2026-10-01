# BlackPill CMSIS HIL

CMSIS-конфигурация приложения: BOARD=F411CE/F401CC.
Debug_F411CE/Debug_F401CC собирают src без HAL; HIL_F411CE/HIL_F401CC
дополнительно подключают сценарии и manifest. CMSIS теперь включён по умолчанию. Старые HAL-конфигурации находятся в legacy/hal и не входят в текущие presets. Профили в hil/profiles задают память и identity;
общие сценарии hil/tests/board используют выбранный MCU для ожидания канала ADC.
Запускать через штатный tools/gdbtest.py с явными --session и --stand.

18 сценариев: boot/HSI, GPIO blink, ADC init/runtime/invalid/vectors/busy/disabled/timeout,
TIM2, RTC rearm/deadline, Sleep от SysTick и от TIM2; clock/GPIO configuration,
IRQ publication и подавление ADC callback ([приёмы и результаты](../docs/CMSIS_RUNTIME_SCENARIOS.md)). Source-level HAL contracts
не применяются к этой firmware. Макросы зависят от текущего frame; MMIO проверяется
в platform.c, данные приложения — в loop. Число тестов не является покрытием кода.

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
