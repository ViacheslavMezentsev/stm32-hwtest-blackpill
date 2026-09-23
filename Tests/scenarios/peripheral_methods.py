"""Application scenarios shared by explicitly configured MCU profiles."""

def gpio_arguments(t, expected):
    t.reach("HAL_GPIO_Init", when=f"GPIOx == {expected['led_port']}")
    t.fields("*GPIO_Init", {
        "Pin": expected["led_pin"],
        "Mode": "GPIO_MODE_OUTPUT_PP",
        "Pull": "GPIO_NOPULL",
        "Speed": "GPIO_SPEED_FREQ_LOW",
    })
    t.reach("loop")
    t.check("LED mode applied", t.value(expected["gpio_mode_expression"]), expected["gpio_mode"])

def gpio_filtered_call(t, expected):
    initial = expected["led_initial"]
    t.reach("HAL_GPIO_TogglePin",
            when=f"GPIOx == {expected['led_port']} && GPIO_Pin == {expected['led_pin']} && ({expected['led_level']}) == {1 - initial}")
    t.check("ODR before selected toggle", t.value(expected["led_level"]), 1 - initial)
    t.reach("loop")
    t.check("ODR after selected toggle", t.value(expected["led_level"]), initial)


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
