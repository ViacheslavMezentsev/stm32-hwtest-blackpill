# Требования к минимальной прошивке

## HW_BOOT
После сброса программа достигает main и основного цикла loop без аварийной остановки.

## HW_CLOCK
После инициализации SystemCoreClock равен 16000000, SYSCLK использует HSI,
AHB имеет делитель 1, APB1 и APB2 — делитель 2.

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

## HW_RCC_CLOCK_NULL
Подмена RCC_ClkInitStruct на NULL при входе в HAL_RCC_ClockConfig запускает
реальную проверку аргумента HAL; её ошибка приводит к Error_Handler.
