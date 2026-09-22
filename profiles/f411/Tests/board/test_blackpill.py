from hwtest import case


@case("HW_BOOT", labels=("boot",))
def boot(t):
    t.reach("loop")


@case("HW_CLOCK", labels=("rcc",))
def clock(t):
    t.reach("loop")
    t.check("SystemCoreClock", t.value("SystemCoreClock"), 16000000)
    cfgr = t.value("RCC->CFGR")
    for name, shift, mask, expected in (("HSI", 2, 3, 0), ("AHB /1", 4, 15, 0),
                                        ("APB1 /2", 10, 7, 4), ("APB2 /2", 13, 7, 4)):
        t.check(name, (cfgr >> shift) & mask, expected)


@case("HW_GPIO", labels=("gpio",))
def gpio(t):
    t.reach("loop")
    for name, expression, shift, mask, expected in (
            ("GPIOC clock", "RCC->AHB1ENR", 2, 1, 1),
            ("PC13 output", "GPIOC->MODER", 26, 3, 1),
            ("PC13 push-pull", "GPIOC->OTYPER", 13, 1, 0),
            ("PC13 no pull", "GPIOC->PUPDR", 26, 3, 0),
            ("PC13 low speed", "GPIOC->OSPEEDR", 26, 3, 0),
            ("PC13 initial low", "GPIOC->ODR", 13, 1, 0)):
        t.check(name, (t.value(expression) >> shift) & mask, expected)


@case("HW_BLINK", labels=("gpio", "tick"))
def blink(t):
    t.reach("loop")
    tick = t.value("uwTick")
    for expected in (1, 0):
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
