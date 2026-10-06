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
    t.check([
        ("prescaler", "TIM2->PSC", HSI_HZ // timers["tim2_tick_hz"] - 1),
        ("auto-reload", "TIM2->ARR", timers["tim2_period_ticks"] - 1),
        ("update interrupt enabled", "TIM2->DIER & TIM_DIER_UIE"),
        ("counter enabled", "TIM2->CR1 & TIM_CR1_CEN")
    ])
    before = t.read("app_state.timer_events")
    t.reach("loop")
    t.check("event delivered", (t.read("app_state.timer_events") - before) & U32_MASK >= 1)


# Verify that every completed TIM2 handler publishes one event and the core returns to thread mode.
@case("HW_TIMER_IRQ_PUBLICATION", labels=("timer", "irq"), contracts=("cmsis_timer_rtc",))
def timer_irq_publication(t):
    t.reach("TIM2_IRQHandler")

    # TECH-002: the register address is kept as a number, valid outside the macro scope.
    icsr = t.evaluate("(unsigned int)&SCB->ICSR")

    # TECH-003: a natural peripheral interrupt, not a software-pended exception; two handlers in a row.
    for _ in range(2):
        # The handler entry: the active exception is TIM2 and its update flag is still set.
        t.check([
            ("TIM2 exception", "SCB->ICSR & SCB_ICSR_VECTACTIVE_Msk", "TIM2_IRQn + 16"),
            ("update flag", "TIM2->SR & TIM_SR_UIF")
        ])
        before = t.read("app_state.timer_events")
        t.reach("TIM2_IRQHandler")
        t.check("one event per completed handler", t.read("app_state.timer_events"), (before + 1) & U32_MASK)

    # Back in loop() no exception is active.
    t.reach("platform_led_toggle")
    t.check("returned to thread mode", t.evaluate(f"*(volatile unsigned int *)0x{icsr:08X} & 0x1FF"), 0)


# Verify the RTC prescalers, the first alarm two seconds after start and its rescheduling by loop().
@case("HW_RTC", timeout_s=30, labels=("rtc",), contracts=("cmsis_timer_rtc",))
def rtc(t):
    timers = t.profile.get("user.timers")
    alarm_seconds = "RTC->ALRMAR & (RTC_ALRMAR_ST | RTC_ALRMAR_SU)"
    t.reach("RTC_Alarm_IRQHandler")

    # LSI is divided down to 1 Hz; the calendar starts at 00:00:00, so the first alarm is at second 2 (BCD).
    t.check([
        ("asynchronous and synchronous prescalers", "RTC->PRER",
         f"({timers['rtc_prediv_a']} << RTC_PRER_PREDIV_A_Pos) | {timers['rtc_prediv_s']}"),
        ("first alarm two seconds after start", alarm_seconds, timers["rtc_alarm_delay_s"]),
        ("alarm ignores the date", "RTC->ALRMAR & RTC_ALRMAR_MSK4")
    ])

    # loop() handles the event and arms the next alarm before it fires.
    t.reach("RTC_Alarm_IRQHandler")
    t.check("application handled an alarm", t.read("app_state.rtc_events") >= 1)
    t.check("next alarm rescheduled", t.evaluate(alarm_seconds) != timers["rtc_alarm_delay_s"])


# Verify that an LSI wait that can never succeed ends in platform_error() instead of hanging.
@case("HW_RTC_DEADLINE", labels=("rtc", "injection"))
def rtc_deadline(t):
    # TECH-015 and TECH-005: stop only at the LSI wait and make its condition impossible.
    t.reach("wait_set", condition=f"code == {WAIT_LSI_READY}")
    t.write("mask", 0)
    t.reach("platform_error")
    t.check("LSI wait error", t.read("platform_fault"), FAULT_LSI_TIMEOUT)
