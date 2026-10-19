"""
RU: TIM2 и RTC: конфигурация, публикация событий прерываний и перепланирование alarm, отказ ожидания LSI.
EN: TIM2 and RTC: configuration, interrupt event publication and alarm rescheduling, an LSI wait failure.
"""
from stm32_gdbtest import case


# HSI clocks TIM2 through the undivided APB1 bus (RM0383/RM0368: 16 MHz).
HSI_HZ = 16_000_000
# platform_fault code of src/platform.c: LSI did not become ready.
FAULT_LSI_TIMEOUT = 12
# wait_set() code argument of the LSI ready wait in platform_rtc_prepare().
WAIT_LSI_READY = 12
# Event counters are uint32_t and wrap around.
U32_MASK = 0xFFFFFFFF


# Verify the TIM2 configuration and that an update event reaches the application.
@case("HW_TIMER", labels=("timer",), contracts=("cmsis_timer_rtc",))
def timer(t):
    timers = t.profile.get("user.timers")
    t.reach("TIM2_IRQHandler")

    # The timer counts at tim2_tick_hz and overflows every tim2_period_ticks.
    t.check("prescaler", t.mmio.read('TIM2.PSC'), HSI_HZ // timers["tim2_tick_hz"] - 1)
    t.check("auto-reload", t.mmio.read('TIM2.ARR'), timers["tim2_period_ticks"] - 1)
    t.check("update interrupt enabled", t.mmio.read('TIM2.DIER') & t.evaluate('TIM_DIER_UIE'))
    t.check("counter enabled", t.mmio.read('TIM2.CR1') & t.evaluate('TIM_CR1_CEN'))
    before = t.read("app_state.timer_events")
    t.reach("loop")
    t.check("event delivered", (t.read("app_state.timer_events") - before) & U32_MASK >= 1)


# Verify that every completed TIM2 handler publishes one event and the core returns to thread mode.
@case("HW_TIMER_IRQ_PUBLICATION", labels=("timer", "irq"), contracts=("cmsis_timer_rtc",))
def timer_irq_publication(t):
    t.reach("TIM2_IRQHandler")

    # SVD задаёт адрес регистра независимо от текущей области макросов GDB.

    # TECH-003: a natural peripheral interrupt, not a software-pended exception; two handlers in a row.
    for _ in range(2):
        # The handler entry: the active exception is TIM2 and its update flag is still set.
        t.check("TIM2 exception",
                t.mmio.read('SCB.ICSR') & t.evaluate('SCB_ICSR_VECTACTIVE_Msk'),
                t.evaluate("TIM2_IRQn + 16"))
        t.check("update flag", t.mmio.read('TIM2.SR') & t.evaluate('TIM_SR_UIF'))
        before = t.read("app_state.timer_events")
        t.reach("TIM2_IRQHandler")
        t.check("one event per completed handler", t.read("app_state.timer_events"), (before + 1) & U32_MASK)

    # Back in loop() no exception is active.
    t.reach("platform_led_toggle")
    t.check("returned to thread mode", t.mmio.read("SCB.ICSR") & 0x1FF, 0)


# Verify the RTC prescalers, the first alarm two seconds after start and its rescheduling by loop().
@case("HW_RTC", timeout_s=30, labels=("rtc",), contracts=("cmsis_timer_rtc",))
def rtc(t):
    timers = t.profile.get("user.timers")
    t.reach("RTC_Alarm_IRQHandler")

    # LSI is divided down to 1 Hz; the calendar starts at 00:00:00, so the first alarm is at second 2 (BCD).
    t.check("asynchronous and synchronous prescalers",
            t.mmio.read('RTC.PRER'),
            t.evaluate(f"({timers['rtc_prediv_a']} << RTC_PRER_PREDIV_A_Pos) | {timers['rtc_prediv_s']}"))
    t.check("first alarm two seconds after start",
            t.mmio.read('RTC.ALRMAR') & (t.evaluate("RTC_ALRMAR_ST | RTC_ALRMAR_SU")),
            timers["rtc_alarm_delay_s"])
    t.check("alarm ignores the date", t.mmio.read('RTC.ALRMAR') & t.evaluate('RTC_ALRMAR_MSK4'))

    # loop() handles the event and arms the next alarm before it fires.
    t.reach("RTC_Alarm_IRQHandler")
    t.check("application handled an alarm", t.read("app_state.rtc_events") >= 1)
    t.check("next alarm rescheduled",
            (t.mmio.read("RTC.ALRMAR") & t.evaluate("RTC_ALRMAR_ST | RTC_ALRMAR_SU")) != timers["rtc_alarm_delay_s"])


# Verify that an LSI wait that can never succeed ends in platform_error() instead of hanging.
@case("HW_RTC_DEADLINE", labels=("rtc", "injection"))
def rtc_deadline(t):
    # TECH-015 and TECH-005: stop only at the LSI wait and make its condition impossible.
    t.reach("wait_set", condition=f"code == {WAIT_LSI_READY}")
    t.write("mask", 0)
    t.reach("platform_error")
    t.check("LSI wait error", t.read("platform_fault"), FAULT_LSI_TIMEOUT)
