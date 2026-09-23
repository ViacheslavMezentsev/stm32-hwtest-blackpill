"""Application scenarios shared by explicitly configured MCU profiles."""

def gpio_arguments(t, expected):
    t.reach("HAL_GPIO_Init", when="GPIOx == GPIOC")
    t.fields("*GPIO_Init", {
        "Pin": "GPIO_PIN_13",
        "Mode": "GPIO_MODE_OUTPUT_PP",
        "Pull": "GPIO_NOPULL",
        "Speed": "GPIO_SPEED_FREQ_LOW",
    })
    t.reach("loop")
    t.check("PC13 mode applied", t.value(expected["gpio_mode_expression"]), expected["gpio_mode"])

def gpio_filtered_call(t, expected):
    initial = expected["led_initial"]
    t.reach("HAL_GPIO_TogglePin",
            when=f"GPIOx == GPIOC && GPIO_Pin == GPIO_PIN_13 && ((GPIOC->ODR >> 13) & 1) == {1 - initial}")
    t.check("ODR before selected toggle", (t.value("GPIOC->ODR") >> 13) & 1, 1 - initial)
    t.reach("loop")
    t.check("ODR after selected toggle", (t.value("GPIOC->ODR") >> 13) & 1, initial)


def rcc_osc_null(t, expected):
    t.reach("HAL_RCC_OscConfig")
    t.set_value("RCC_OscInitStruct", "0")
    t.check("NULL injected", t.value("RCC_OscInitStruct"), 0)
    t.reach("Error_Handler")

def rcc_clock_null(t, expected):
    t.reach("HAL_RCC_ClockConfig")
    t.set_value("RCC_ClkInitStruct", "0")
    t.check("NULL injected", t.value("RCC_ClkInitStruct"), 0)
    t.reach("Error_Handler")
