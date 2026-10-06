"""Application scenarios shared by explicitly configured MCU profiles."""

def boot(t, expected):
    t.reach("loop")

def clock(t, expected):
    t.reach("platform_adc_start")
    t.check("SystemCoreClock", t.value("SystemCoreClock"), 8000000)
    for name, expression, value in expected["clock"]:
        t.check(name, t.value(expression), value)


def gpio(t, expected):
    t.reach("platform_adc_start")
    for name, expression, value in expected["gpio"]:
        t.check(name, t.value(expression), value)


def blink(t, expected):
    t.reach("platform_adc_start")
    tick = t.value("uwTick")
    for level in (1 - expected["led_initial"], expected["led_initial"]):
        t.reach("platform_adc_start")
        t.check("LED pin toggled", t.value(expected["led_level"]), level)
        next_tick = t.value("uwTick")
        delta = (next_tick - tick) & 0xFFFFFFFF
        t.report.setdefault("loop_tick_deltas_ms", []).append(delta)
        t.check("HAL delay >= 500 ms", delta >= 500, True)
        tick = next_tick

def rcc_error(t, expected):
    t.reach("HAL_RCC_OscConfig")
    t.force_return("(HAL_StatusTypeDef)1")
    t.reach("Error_Handler")
