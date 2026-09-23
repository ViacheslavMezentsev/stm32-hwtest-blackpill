"""Observe real peripheral IRQs and repeated application work, without target calls."""
from hwtest import case


@case("HW_ADC_DMA_RUNTIME", labels=("adc", "dma", "runtime"))
def adc_dma_runtime(t):
    for sequence in (1, 2):
        t.reach("HAL_ADC_ConvCpltCallback")
        t.check("ADC callback handle", t.value("adc"), t.value("&hadc1"))
        t.check("DMA exhausted", t.value("DMA1_Channel1->CNDTR"), 0)
        t.reach("loop")
        t.check("published sequence", t.value("app_state.adc_sequences"), sequence)
        for field in ("temperature_raw", "vrefint_raw"):
            raw = t.value("app_state." + field)
            t.report.setdefault("adc_raw", []).append({"field": field, "raw": raw})
            t.check(field + " non-saturated", 0 < raw < 4095, True)


@case("HW_TIM2_IRQ", labels=("tim", "irq", "runtime"))
def tim2_irq(t):
    t.reach("HAL_TIM_PeriodElapsedCallback")
    t.check("TIM callback handle", t.value("timer"), t.value("&htim2"))
    before = t.value("app_state.timer_events")
    t.reach("HAL_TIM_PeriodElapsedCallback")
    t.check("TIM callback increment", t.value("app_state.timer_events"), before + 1)
    t.check("TIM2 enabled", t.value("TIM2->CR1") & 1, 1)


@case("HW_RTC_ALARM", timeout_s=30, labels=("rtc", "irq", "runtime"))
def rtc_alarm(t):
    for expected in (0, 1):
        t.reach("HAL_RTC_AlarmAEventCallback")
        t.check("RTC callback handle", t.value("rtc"), t.value("&hrtc"))
        t.check("RTC repeated alarm", t.value("app_state.rtc_events"), expected)
    t.reach("loop")
    t.check("RTC second event published", t.value("app_state.rtc_events"), 2)


@case("HW_ADC_START_ERROR", labels=("adc", "injection"))
def adc_start_error(t):
    t.reach("HAL_ADC_Start_DMA")
    t.force_return("(HAL_StatusTypeDef)1")
    t.reach("Error_Handler")
    t.check("no sequence published", t.value("app_state.adc_sequences"), 0)


@case("HW_ADC_DMA_TIMEOUT", labels=("adc", "dma", "injection"))
def adc_dma_timeout(t):
    t.reach("HAL_ADC_ConvCpltCallback")
    # Suppress completion publication; DMA itself already completed.
    t.force_return("")
    t.reach("Error_Handler")
    t.check("no stale samples published", t.value("app_state.adc_sequences"), 0)
