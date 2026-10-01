# BlackPill CMSIS HIL

Опциональная CMSIS-конфигурация приложения: BOARD=F411CE/F401CC.
Debug_F411CE/Debug_F401CC собирают src без HAL. Старые presets сохраняют HAL
до завершения перехода структуры. Профили в hil/profiles задают память и identity;
общие сценарии hil/tests/board используют выбранный MCU для ожидания канала ADC.
Запускать через штатный tools/gdbtest.py с явными --session и --stand.

14 сценариев: boot/HSI, GPIO blink, ADC init/runtime/invalid/vectors/busy/disabled/timeout,
TIM2, RTC rearm/deadline, Sleep от SysTick и от TIM2. Source-level HAL contracts
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
