# H503: настройка CubeMX и проверка генерации

Проверен исходный `profiles/h503/stm32-hwtest-blackpill.ioc`: CubeMX 6.18.0,
CubeH5 V1.7.0, STM32H503CBTx, LQFP48. Владелец подтвердил STM32H503CBT6;
linker задаёт 128 KiB Flash и 32 KiB RAM. Это пока исходная генерация, не
собранный и не проверенный аппаратно профиль hwtest.

[Проект WeAct](https://github.com/WeActStudio/WeActStudio.STM32H503CoreBoard)
в README называет CBU6, тогда как наш экземпляр и IOC — CBT6. MCU в IOC оставляем
по маркировке владельца. [Схема V1.0](https://github.com/WeActStudio/WeActStudio.STM32H503CoreBoard/blob/master/Hardware/WeAct-STM32H503Cx_CoreBoard_V10%20SchDoc.pdf)
найдена, но её содержимое при этой проверке получить не удалось. PC13 ниже —
выбор текущего IOC, ещё не подтверждение LED/полярности по схеме конкретной платы.

## Что уже есть

| Блок | Фактическая генерация | Решение |
| --- | --- | --- |
| DEBUG | Serial Wire, PA13/PA14 | Оставить |
| RCC | HSI 64 MHz → SYSCLK 64 MHz → AHB /8; HCLK и APB1/2/3 8 MHz; PLL не запущен | Оставить для первого опыта |
| PWR/Flash | Voltage scale 3, FLASH_LATENCY_3, programming delay 1 | Оставить параметры CubeMX, не снижать latency вручную |
| GPIO | PC13 LED_USER, push-pull, no pull, low speed, начальный RESET | Проверить по плате; начальный уровень выбрать по полярности LED |
| ADC1 | 12 bit, right aligned, 2 ranks, software start, single-ended, 640.5 cycles | Сохранить; добавить DMA для общего приложения |
| ADC clock | ADCDAC kernel HCLK 8 MHz, ADC asynchronous /2 | Реальный clock ADC 4 MHz, а не 8 MHz из поля kernel clock |
| TIM2 | PSC=7999, ARR=99, internal clock 8 MHz | Период 100 ms; включить IRQ |
| RTC | LSI, 24-hour, async=127, sync=255; без alarm и IRQ | Исправить делитель, включить календарь/Alarm A и IRQ |
| CRC / ICACHE | CRC включён; ICACHE direct mapped, 1-way | Для старта оставить |
| GPDMA | Не настроен, ADC DMA handle не связан | Нужен до подключения общего User |

Значения частот PLL/SPI в IOC не означают, что эти блоки работают:
в `SystemClock_Config()` стоит `PLLState = RCC_PLL_NONE`. Источник истины при
проверке — IOC вместе с кодом и затем регистрами, а не отдельная строка частоты.

## Последовательность в CubeMX

Названия вкладок могут немного отличаться; после генерации проверять указанные
поля HAL и обработчики, а не только состояние галочек.

1. **Project Manager**: MCU STM32H503CBTx, пакет CubeH5 V1.7.0; не мигрировать
   автоматически на другой пакет. Генерация внутри `profiles/h503`, отдельные
   `.c/.h` на периферию и Keep User Code. Текущий Makefile допустим для генерации;
   рабочую сборку позже подключаем через общий YAML и отдельный CMake preset.
2. **System Core → DEBUG**: Serial Wire. **SYS**: timebase SysTick.
   **RCC / Clock Configuration**: сохранить HSI /1, SYSCLK HSI, AHB /8,
   APB1/2/3 /1, LSI enabled, RTC source LSI, ADCDAC source HCLK.
   HSE/LSE пока не включать; значение HSE 8 MHz в конфигурации не доказывает
   частоту установленного кварца. TIM2 kernel должен остаться 8 MHz.
3. **ADC1 → Parameter Settings**: сохранить Temperature Sensor rank 1,
   VREFINT rank 2, sampling 640.5 cycles для обоих, 12 bit/right alignment,
   single-ended, Scan enabled, Number of conversions 2. Continuous и
   Discontinuous disabled, software trigger, external edge none,
   AutoWait/oversampling disabled, DMA continuous requests disabled,
   overrun data preserved. Калибровку вызывает Platform перед стартом:
   `HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED)`; одного MX_ADC1_Init мало.
4. **GPDMA1**: выбрать свободный канал, например Channel 0, в обычном режиме
   Standard Request / Normal, request ADC1. Не выбирать linked-list/circular
   для первой конечной передачи. Детальные поля — ниже.
5. **TIM2 → NVIC Settings**: включить TIM2 global interrupt. Prescaler 7999,
   Counter Period 99 оставить. Приоритет можно взять 5, subpriority 0.
   В коде нужен `TIM2_IRQHandler()` → `HAL_TIM_IRQHandler(&htim2)`.
   Счёт начинается после `HAL_TIM_Base_Start_IT`, а не после MX_TIM2_Init.
6. **RTC**: Activate Clock Source и Activate Calendar; формат 24-hour,
   Binary mode disabled. Для номинальных 32000 Hz LSI выставить asynchronous
   prescaler 127, synchronous prescaler **249**: 32000/(128×250)=1 Hz.
   Текущие 127/255 дают 0.9765625 Hz, то есть номинальную секунду 1.024 s;
   собственная погрешность LSI остаётся и после исправления.
   Включить внутренний **Alarm A**, без выхода RTC на пин; задать валидные
   стартовые дату/время и alarm. Для простого секундного опыта можно задать
   00:00:01 и маски date/weekday, hours, minutes (seconds не маскировать).
   Это начальная конфигурация; последующие события каждую секунду обеспечит
   прикладной перевзвод alarm, а не эта маска сама по себе.
7. **RTC → NVIC**: включить доступное RTC global interrupt, например 5/0.
   У H503 в startup это **RTC_IRQHandler**, не F4 RTC_Alarm_IRQHandler.
   Сгенерированный обработчик должен вызывать `HAL_RTC_AlarmIRQHandler(&hrtc)`.
   Wakeup timer, tamper, timestamp пока не нужны. После reset учитывать,
   что backup domain может сохранить время/флаги предыдущего запуска.
8. **ICACHE / PWR / CORTEX / BOOTPATH**: текущий ICACHE 1-way оставить;
   это кэш инструкций, а не требование чистить D-cache для ADC-буфера.
   Оставить обычный LEGACY boot и текущие настройки privilege. H503 не имеет
   TrustZone; не переносить secure/nonsecure разбиение от H563. Sleep/WFI
   реализует приложение; Stop/Standby, watchdog и изменение option bytes
   не нужны для первого запуска.

## GPDMA1: конечная передача ADC

| Поле | Значение для первой конфигурации |
| --- | --- |
| Request | ADC1 (`GPDMA1_REQUEST_ADC1`) |
| Direction | Peripheral to memory |
| Mode | Normal / standard request, без linked list |
| Block hardware request | Single burst (`DMA_BREQ_SINGLE_BURST`) |
| Source / destination increment | Fixed / incremented |
| Source / destination data width | Half word / half word |
| Source / destination burst length | 1 / 1 |
| Transfer event | Block transfer complete (`DMA_TCEM_BLOCK_TRANSFER`) |
| Trigger | Masked / disabled; запросы поступают от ADC |
| Data exchange / alignment | No exchange, right aligned / zero padded |
| Priority | Low достаточно при одном активном канале |
| Port allocation | Начать с допустимых CubeMX defaults; сверить доступ к ADC DR и SRAM по RM |
| NVIC | IRQ выбранного GPDMA1 channel, например 5/0 |

После генерации должны появиться `HAL_DMA_Init`, связь
`__HAL_LINKDMA(..., DMA_Handle, ...)`, включение clock/NVIC и обработчик
выбранного канала с `HAL_DMA_IRQHandler`. Инициализация clock GPDMA должна
предшествовать ADC MSP/DMA init. Проверить порядок вызовов в main.

В CubeH5 V1.7.0 `HAL_ADC_Start_DMA(..., 2)` принимает **два отсчёта**.
Внутри HAL при source halfword это переводится в **4 байта** для
`HAL_DMA_Start_IT`. Не заменять 2 на 4 в общем User: получится другая длина!
Аппаратный счётчик GPDMA выражается в байтах; тестовые ожидания нужно адаптировать.

Первое отдельное исследование ADC можно провести без DMA, но для двух рангов
нельзя просто останавливаться между чтениями DR: следующий результат может
перезаписаться/потеряться. Для пошагового polling-опыта нужна отдельная
одноранговая либо discontinuous-конфигурация. Текущий общий User использует DMA.

## Что проверим после регенерации

- TIM2, RTC и выбранный GPDMA IRQ присутствуют и связаны с HAL, не Default_Handler.
- ADC DMA handle и clock/init order корректны; ранги и длина не изменились.
- RTC prescalers 127/249, календарь/Alarm A и NVIC действительно сгенерированы.
- SWD, LED и частоты сохранены; CubeMX не добавил нежелательных внешних выводов.
- Общая CMake/YAML-интеграция: сейчас h503 ещё отсутствует. Локальный
  `Core/CMakeLists.txt` пока не перечисляет adc.c, crc.c, rtc.c, tim.c;
  это отдельная работа интеграции, не ошибка настройки периферии CubeMX.
- `main.c` уже вызывает init/setup/loop, но H503 Platform ещё нет. До сборки
  потребуется адаптер калибровки/RTC и параметры температуры 30/130°C.
- SVD добавлен владельцем, но сам по себе не обеспечивает backend поддержки H503.

Регенерация не означает готовность прошивки к плате. Следующий шаг — интеграция
отдельной сборки и проверка ELF/контрактов. Подключение H503 согласуем отдельно.

## Основания рекомендаций

Аудит выполнен по IOC и Core нового профиля, startup/linker, общему User и
установленному CubeH5 V1.7.0: `stm32h5xx_hal_adc.c` (перевод длины DMA),
`stm32h5xx_hal_adc_ex.h`, `stm32h5xx_ll_adc.h`, примерам RTC NUCLEO-H503RB.
Пример ADC DMA для H563 использован только для сверки названий HAL-полей,
его circular linked-list конфигурация сюда не переносится.
Аппаратные ограничения сверять по [документации ST H503 (DS/RM/errata)](https://www.st.com/en/microcontrollers-microprocessors/stm32h503/documentation.html).
