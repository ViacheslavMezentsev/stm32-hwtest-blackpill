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
        t.check("expected exception",
                (t.mmio.read("SCB.ICSR") & t.evaluate("SCB_ICSR_VECTACTIVE_Msk")) == t.evaluate(exception))

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


# Восстанавливаем обе маски даже при отказе первой записи; W1S не требует readback.
def restore_irqs(t, enabled):
    try:
        t.mmio.write("NVIC.ISER0", enabled[0], allow_effects=True)
    finally:
        t.mmio.write("NVIC.ISER1", enabled[1], allow_effects=True)


# SysTick будит ядро при замаскированных внешних IRQ; флаги pending не снимаются.
@case("HW_SLEEP_SYSTICK", labels=("sleep", "systick"), contracts=("cmsis_sleep",))
def sleep_systick(t):
    idle = t.profile.get("user.timing.idle_ms")
    t.reach("app_idle")
    t.reach("platform_sleep")
    t.check("ordinary Sleep: no SLEEPONEXIT, no SLEEPDEEP",
            t.mmio.read("SCB.SCR") & t.evaluate("SCB_SCR_SLEEPONEXIT_Msk | SCB_SCR_SLEEPDEEP_Msk"), 0)
    enabled = [t.mmio.read("NVIC.ISER0"), t.mmio.read("NVIC.ISER1")]
    before = t.read("platform_tick")

    # try начинается до первой записи: частичная установка тоже требует очистки.
    try:
        t.mmio.write("NVIC.ICER1", enabled[1], allow_effects=True)
        t.mmio.write("NVIC.ICER0", enabled[0], allow_effects=True)
        reach_wfi_irq(t, "SysTick_Handler", "SysTick_IRQn + 16")
    finally:
        restore_irqs(t, enabled)
    t.reach("loop")
    t.check("idle interval completed, ticks", (t.read("platform_tick") - before) & U32_MASK >= idle - 1)
    t.check("ADC sequence retained", t.read("app_state.adc_sequences"), 1)


# TIM2 будит ядро при остановленном SysTick. COUNTFLAG и снятый pending не восстанавливаются.
@case("HW_SLEEP_TIM2", labels=("sleep", "timer"), contracts=("cmsis_sleep",))
def sleep_tim2(t):
    t.reach("app_idle")
    t.reach("platform_sleep")
    t.check("ordinary Sleep: no SLEEPONEXIT, no SLEEPDEEP",
            t.mmio.read("SCB.SCR") & t.evaluate("SCB_SCR_SLEEPONEXIT_Msk | SCB_SCR_SLEEPDEEP_Msk"), 0)
    control = t.mmio.read("SysTick.CTRL", allow_effects=True) & 7
    enabled = [t.mmio.read("NVIC.ISER0"), t.mmio.read("NVIC.ISER1")]
    timer_bit = t.evaluate("1 << TIM2_IRQn")
    clear_pending = t.evaluate("SCB_ICSR_PENDSTCLR_Msk")
    ticks, events = t.read("platform_tick"), t.read("app_state.timer_events")

    # ICER получает маску W1C, ICSR — только команду PENDSTCLR, без общего RMW.
    try:
        t.mmio.write("NVIC.ICER1", enabled[1], allow_effects=True)
        t.mmio.write("NVIC.ICER0", enabled[0] & ~timer_bit, allow_effects=True)
        t.mmio.write("SysTick.CTRL", 0)
        t.mmio.write("SCB.ICSR", clear_pending, allow_effects=True)
        reach_wfi_irq(t, "TIM2_IRQHandler", "TIM2_IRQn + 16")
        t.check("SysTick did not advance", t.read("platform_tick"), ticks)
    finally:
        try:
            t.mmio.write("SysTick.CTRL", control)
        finally:
            restore_irqs(t, enabled)
    t.reach("loop")
    t.check("timer event handled", (t.read("app_state.timer_events") - events) & U32_MASK >= 1)
    t.check("ADC sequence retained", t.read("app_state.adc_sequences"), 1)
