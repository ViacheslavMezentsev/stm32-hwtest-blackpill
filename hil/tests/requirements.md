# Требования к CMSIS-приложению

Каждый сценарий начинается со сброса. Остановки GDB влияют на время; эти проверки не измеряют энергопотребление и не доказывают покрытие кода.

## HW_BOOT

Приложение достигает loop без platform_fault; SystemCoreClock равен 16 МГц, делители RCC соответствуют HSI без деления.

## HW_GPIO

PC13 настроен выходом; активный низкий LED последовательно проходит состояния выключен, включён, выключен.

## HW_ADC_INIT

ADC сканирует два канала: температуру (18 для F411, 16 для F401), затем VREFINT (17). DMA использует halfword и инкремент памяти.

## HW_ADC_RUNTIME

Одна завершённая DMA-последовательность публикуется в приложении; качество FACTORY, VREFINT ненулевой, VDDA в широком диапазоне 2–4 В. Это проверка правдоподобия, не метрология.

## HW_TIMER

TIM2 с PSC=15999 и ARR=99 доставляет событие в приложение; номинальный период при HSI16 составляет 100 мс.

## HW_RTC

RTC использует делители 127/249; первый alarm назначен на вторую секунду, обработанное событие приводит к следующему alarm. Точность LSI не проверяется.

## HW_ADC_DISABLED

Принудительное отключение ADON перед запуском приводит к platform_error с кодом 2.

## HW_ADC_TIMEOUT

При запрещённом DMA IRQ приложение достигает platform_error спустя не менее 100 тиков, не публикуя измерение.

## HW_RTC_DEADLINE

Инъекция невыполнимого условия ожидания LSI завершается platform_error с кодом 12 вместо бесконечного ожидания.

## HW_ADC_INVALID

Нулевые/предельные входные значения отвергаются с нулевым результатом и качеством INVALID; следующее нормальное измерение восстанавливается.

## HW_ADC_VECTORS

Подстановка заводских калибровочных отсчётов даёт 3300 мВ и 30/110 °C; проверяется арифметика, не фактическая температура кристалла.

## HW_ADC_BUSY

Занятый DMA stream отвергается кодом 1 до запуска новой конверсии.

## HW_SLEEP_SYSTICK

С отключёнными периферийными IRQ SysTick выводит процессор из WFI; приложение завершает интервал idle и продолжает измерения.

## HW_SLEEP_TIM2

При остановленном SysTick TIM2 выводит процессор из WFI без продвижения platform_tick; после восстановления масок приложение продолжает работу.

## HW_CLOCK_GPIO_CONFIG

HSI16, bus dividers, SysTick 1 ms and PC13 electrical configuration match the application.

## HW_TIMER_IRQ_PUBLICATION

Natural TIM2 IRQ has exception 44 and UIF; two completed handlers each publish one event, then return to thread mode.

## HW_ADC_DMA_PUBLICATION

Natural DMA IRQ has exception 72, TCIF without errors and NDTR=0. Both samples are published exactly once after the callback.

## HW_ADC_CALLBACK_SUPPRESSED

Suppressing the void callback after DMA completion causes the application deadline (100 ticks), without publication. A separate normal ADC run after reset checks recovery.
