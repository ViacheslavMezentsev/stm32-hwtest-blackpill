"""Methods derived from BBC_SW_LLR, exercised on the unmodified BlackPill firmware."""

from hwtest import case


@case("HW_GPIO_ARGUMENTS", labels=("gpio", "contract"))
def gpio_arguments(t):
    t.reach("HAL_GPIO_Init", when="GPIOx == GPIOC")
    t.fields("*GPIO_Init", {
        "Pin": "GPIO_PIN_13",
        "Mode": "GPIO_MODE_OUTPUT_PP",
        "Pull": "GPIO_NOPULL",
        "Speed": "GPIO_SPEED_FREQ_LOW",
    })
    t.reach("loop")
    t.check("PC13 mode applied", (t.value("GPIOC->MODER") >> 26) & 3, 1)


@case("HW_GPIO_FILTERED_CALL", labels=("gpio", "contract"))
def gpio_filtered_call(t):
    # First call sees ODR13=0. Select the second call, after the first toggle.
    t.reach("HAL_GPIO_TogglePin",
            when="GPIOx == GPIOC && GPIO_Pin == GPIO_PIN_13 && (GPIOC->ODR & GPIO_PIN_13) != 0")
    t.check("ODR before selected toggle", (t.value("GPIOC->ODR") >> 13) & 1, 1)
    t.reach("loop")
    t.check("ODR after selected toggle", (t.value("GPIOC->ODR") >> 13) & 1, 0)


@case("HW_RCC_OSC_NULL", labels=("rcc", "injection"))
def rcc_osc_null(t):
    t.reach("HAL_RCC_OscConfig")
    t.set_value("RCC_OscInitStruct", "0")
    t.check("NULL injected", t.value("RCC_OscInitStruct"), 0)
    t.reach("Error_Handler")


@case("HW_RCC_CLOCK_NULL", labels=("rcc", "injection"))
def rcc_clock_null(t):
    t.reach("HAL_RCC_ClockConfig")
    t.set_value("RCC_ClkInitStruct", "0")
    t.check("NULL injected", t.value("RCC_ClkInitStruct"), 0)
    t.reach("Error_Handler")
