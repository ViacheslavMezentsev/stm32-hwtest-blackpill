# Требования к минимальной прошивке

## HW_BOOT
После сброса программа достигает main и основного цикла loop без аварийной остановки.

## HW_CLOCK
После инициализации SystemCoreClock равен 8000000, SYSCLK использует HSI 16 МГц,
AHB имеет делитель 2, APB1 — 1, APB2 — 4 (PCLK1=8 МГц, PCLK2=2 МГц).

## HW_GPIO
Включено тактирование GPIOC. PC13 настроен как push-pull output,
без подтяжки, с низкой скоростью. До первого переключения ODR13 равен 0.

## HW_BLINK
На двух последовательных проходах loop ODR13 принимает значения 1 и 0.
Между проходами uwTick увеличивается минимум на 500 мс с учётом переполнения uint32.
Это проверка программного состояния и HAL-времени, не измерение электрического сигнала.

## HW_RCC_ERROR
Если HAL_RCC_OscConfig принудительно возвращает HAL_ERROR,
SystemClock_Config передаёт управление Error_Handler.

## HW_GPIO_ARGUMENTS
Вызов HAL_GPIO_Init для GPIOC получает PC13, push-pull output, no-pull,
low-speed. После инициализации MODER13 подтверждает режим output.

## HW_GPIO_FILTERED_CALL
Условная остановка выбирает вызов HAL_GPIO_TogglePin для PC13 с ODR13=1,
пропуская первый вызов с ODR13=0. После выбранного вызова ODR13 равен 0.

## HW_RCC_OSC_NULL
Подмена RCC_OscInitStruct на NULL при входе в HAL_RCC_OscConfig запускает
реальную проверку аргумента HAL; её ошибка приводит к Error_Handler.

## HW_ADC_DMA_INIT
ADC1 имеет два ранга: Temperature Sensor и VREFINT, выборку 480 циклов,
делитель PCLK2/2 (ADC=1 МГц), scan без continuous. DMA2 Stream0 channel0 настроен
peripheral-to-memory, normal, halfword/halfword и memory increment.
Это проверка конфигурации; преобразования ещё не запускаются.

## HW_TIM2_INIT
TIM2 настроен PSC=7999, ARR=99 при тактировании 8 МГц (номинальный период 100 мс),
но счётчик ещё не запущен. Реальная периодичность IRQ этим тестом не проверяется.

## HW_RTC_INIT
RTC тактируется от готового LSI, делители равны 127/255, внешний выход выключен.
Точность RTC и получение alarm-события этим тестом не проверяются.

## HW_RCC_CLOCK_NULL
Подмена RCC_ClkInitStruct на NULL при входе в HAL_RCC_ClockConfig запускает
реальную проверку аргумента HAL; её ошибка приводит к Error_Handler.
