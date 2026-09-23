from hwtest import case


@case("HW_BOOT", labels=("boot",))
def boot(t):
    t.reach("loop")


@case("HW_CLOCK", labels=("rcc",))
def clock(t):
    t.reach("loop")
    t.check("SystemCoreClock", t.value("SystemCoreClock"), 8000000)
    cfgr = t.value("RCC->CFGR")
    for name, shift, mask, expected in (("HSI", 2, 3, 0), ("AHB /1", 4, 15, 0),
                                        ("APB1 /1", 8, 7, 0), ("APB2 /1", 11, 7, 0)):
        t.check(name, (cfgr >> shift) & mask, expected)


@case("HW_GPIO", labels=("gpio",))
def gpio(t):
    t.reach("loop")
    t.check("GPIOC clock", (t.value("RCC->APB2ENR") >> 4) & 1, 1)
    t.check("PC13 output push-pull 2 MHz", (t.value("GPIOC->CRH") >> 20) & 15, 2)
    t.check("PC13 initial high", (t.value("GPIOC->ODR") >> 13) & 1, 1)



@case("HW_BLINK", labels=("gpio", "tick"))
def blink(t):
    t.reach("loop")
    tick = t.value("uwTick")
    for expected in (0, 1):
        t.reach("loop")
        t.check("PC13 toggled", (t.value("GPIOC->ODR") >> 13) & 1, expected)
        next_tick = t.value("uwTick")
        delta = (next_tick - tick) & 0xFFFFFFFF
        t.report.setdefault("loop_tick_deltas_ms", []).append(delta)
        t.check("HAL delay >= 500 ms", delta >= 500, True)
        tick = next_tick


@case("HW_RCC_ERROR", labels=("rcc", "injection"))
def rcc_error(t):
    t.reach("HAL_RCC_OscConfig")
    t.force_return("(HAL_StatusTypeDef)1")
    t.reach("Error_Handler")
