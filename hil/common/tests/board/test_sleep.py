"""
RU: Обычный сон WFI: SysTick и TIM2 будят ядро, прерванный контекст — команда WFI; не измерение тока.
EN: Ordinary WFI sleep: SysTick and TIM2 wake the core, the interrupted context is a WFI; not a current measurement.
"""
from stm32_gdbtest import case


# Thumb encoding of WFI (ARMv7-M ARM, A7.7.261).
WFI_OPCODE = 0xBF30
# An interrupt can arrive before WFI executes, so the observation is retried a bounded number of times.
WFI_ATTEMPTS = 8
# Counters are uint32_t and wrap around.
U32_MASK = 0xFFFFFFFF


# TECH-008: stop in the handler and confirm that the interrupted code is the WFI of platform_sleep().
def reach_wfi_irq(t, handler, exception):
    # Each attempt stops at the next handler entry and looks at the code it interrupted.
    for attempt in range(WFI_ATTEMPTS):
        t.reach(handler)
        t.check("expected exception", t.evaluate(f"(SCB->ICSR & SCB_ICSR_VECTACTIVE_Msk) == {exception}"))

        # The exception entry may appear as a signal frame between the handler and the interrupted code.
        interrupted = next((frame for frame in t.frames(6)["frames"][1:] if frame["method"] != "signal"), None)
        t.check("the interrupted frame is known", interrupted is not None and interrupted["pc"] is not None)
        halfword = int.from_bytes(t.memory(interrupted["pc"] - 2, 2), "little")
        t.record("interrupted", dict(attempt=attempt, function=interrupted["name"], pc=interrupted["pc"],
                                     preceding_halfword=halfword))
        if interrupted["name"] == "platform_sleep" and halfword == WFI_OPCODE:
            t.check("interrupted instruction is WFI", halfword, WFI_OPCODE)
            return
    t.check("WFI interrupted context observed", False)


# Verify that SysTick alone wakes the core from WFI and the idle interval completes.
@case("HW_SLEEP_SYSTICK", labels=("sleep", "systick"), contracts=("cmsis_sleep",))
def sleep_systick(t):
    idle = t.profile.get("user.timing.idle_ms")
    t.reach("app_idle")
    t.reach("platform_sleep")
    t.check("ordinary Sleep: no SLEEPONEXIT, no SLEEPDEEP",
            t.evaluate("SCB->SCR & (SCB_SCR_SLEEPONEXIT_Msk | SCB_SCR_SLEEPDEEP_Msk)"), 0)

    # TECH-006: all peripheral interrupts are masked, SysTick is a core exception and stays.
    enabled = [t.read("NVIC->ISER[0]"), t.read("NVIC->ISER[1]")]

    # ICER is write-one-to-clear: writing the enabled set masks exactly those interrupts.
    t.write([("NVIC->ICER[1]", enabled[1]), ("NVIC->ICER[0]", enabled[0])])
    before = t.read("platform_tick")
    try:
        reach_wfi_irq(t, "SysTick_Handler", "SysTick_IRQn + 16")
    finally:
        # The saved enable set is restored even when the observation fails.
        t.write([("NVIC->ISER[0]", enabled[0]), ("NVIC->ISER[1]", enabled[1])])

    # The idle interval ends on SysTick and the application goes on measuring.
    t.reach("loop")
    t.check("idle interval completed, ticks", (t.read("platform_tick") - before) & U32_MASK >= idle - 1)
    t.check("ADC sequence retained", t.read("app_state.adc_sequences"), 1)


# Verify that TIM2 wakes the core from WFI with SysTick stopped, without advancing the tick.
@case("HW_SLEEP_TIM2", labels=("sleep", "timer"), contracts=("cmsis_sleep",))
def sleep_tim2(t):
    t.reach("app_idle")
    t.reach("platform_sleep")
    t.check("ordinary Sleep: no SLEEPONEXIT, no SLEEPDEEP",
            t.evaluate("SCB->SCR & (SCB_SCR_SLEEPONEXIT_Msk | SCB_SCR_SLEEPDEEP_Msk)"), 0)

    control = t.evaluate("SysTick->CTRL & (SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | "
                         "SysTick_CTRL_ENABLE_Msk)")
    enabled = [t.read("NVIC->ISER[0]"), t.read("NVIC->ISER[1]")]

    # TECH-006: only the TIM2 interrupt stays enabled; SysTick is stopped and its pending request cleared.
    t.write([
        ("NVIC->ICER[1]", enabled[1]),
        ("NVIC->ICER[0]", f"{enabled[0]} & ~(1 << TIM2_IRQn)"),
        ("SysTick->CTRL", 0),
        ("SCB->ICSR", "SCB_ICSR_PENDSTCLR_Msk")
    ])
    ticks, events = t.read("platform_tick"), t.read("app_state.timer_events")
    try:
        reach_wfi_irq(t, "TIM2_IRQHandler", "TIM2_IRQn + 16")
        t.check("SysTick did not advance", t.read("platform_tick"), ticks)
    finally:
        # The saved SysTick control and enable set are restored even when the observation fails.
        t.write([("SysTick->CTRL", control), ("NVIC->ISER[0]", enabled[0]), ("NVIC->ISER[1]", enabled[1])])

    # With the masks restored the application handles the timer event and goes on measuring.
    t.reach("loop")
    t.check("timer event handled", (t.read("app_state.timer_events") - events) & U32_MASK >= 1)
    t.check("ADC sequence retained", t.read("app_state.adc_sequences"), 1)
