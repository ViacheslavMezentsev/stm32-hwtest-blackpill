from hwtest import case
from Tests.scenarios import power
from profiles.f411.Tests.expectations import EXPECTED


@case("HW_SLEEP_SYSTICK", labels=("pwr", "sleep"))
def sleep_systick(t):
    power.sleep_systick(t, EXPECTED)


@case("HW_SLEEP_TIMER", labels=("pwr", "sleep", "injection"))
def sleep_timer(t):
    power.sleep_timer(t, EXPECTED)
