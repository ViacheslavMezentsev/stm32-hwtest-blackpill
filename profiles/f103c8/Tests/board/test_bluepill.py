from stm32_gdbtest import case
from Tests.scenarios import board as scenarios
from profiles.f103c8.Tests.expectations import EXPECTED


@case("HW_BOOT", labels=("boot",))
def boot(t):
    scenarios.boot(t, EXPECTED)


@case("HW_CLOCK", labels=("rcc",), contracts=("clock_macros",))
def clock(t):
    scenarios.clock(t, EXPECTED)


@case("HW_GPIO", labels=("gpio",), contracts=("gpio_macros",))
def gpio(t):
    scenarios.gpio(t, EXPECTED)


@case("HW_BLINK", labels=("gpio", "tick"))
def blink(t):
    scenarios.blink(t, EXPECTED)


@case("HW_RCC_ERROR", labels=("rcc", "injection"), contracts=("rcc_error",))
def rcc_error(t):
    scenarios.rcc_error(t, EXPECTED)
