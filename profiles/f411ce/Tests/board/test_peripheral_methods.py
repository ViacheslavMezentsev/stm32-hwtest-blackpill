from stm32_gdbtest import case
from Tests.scenarios import peripheral_methods as scenarios
from profiles.f411ce.Tests.expectations import EXPECTED


@case("HW_GPIO_ARGUMENTS", labels=("gpio", "contract"), contracts=("gpio_arguments",))
def gpio_arguments(t):
    scenarios.gpio_arguments(t, EXPECTED)


@case("HW_GPIO_FILTERED_CALL", labels=("gpio", "contract"), contracts=("gpio_filtered_call",))
def gpio_filtered_call(t):
    scenarios.gpio_filtered_call(t, EXPECTED)


@case("HW_RCC_OSC_NULL", labels=("rcc", "injection"), contracts=("rcc_osc_null",))
def rcc_osc_null(t):
    scenarios.rcc_osc_null(t, EXPECTED)


@case("HW_RCC_CLOCK_NULL", labels=("rcc", "injection"), contracts=("rcc_clock_null",))
def rcc_clock_null(t):
    scenarios.rcc_clock_null(t, EXPECTED)
