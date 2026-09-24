from stm32_gdbtest import case
from Tests.scenarios import peripheral_runtime as scenarios
from profiles.f429zi.Tests.expectations import EXPECTED


@case("HW_ADC_DMA_RUNTIME", labels=("adc", "dma", "runtime"))
def adc_dma_runtime(t):
    scenarios.adc_dma_runtime(t, EXPECTED)


@case("HW_TIM2_IRQ", labels=("tim", "irq", "runtime"))
def tim2_irq(t):
    scenarios.timer_irq(t, EXPECTED)


@case("HW_RTC_ALARM", timeout_s=30, labels=("rtc", "irq", "runtime"))
def rtc_alarm(t):
    scenarios.rtc_alarm(t, EXPECTED)


@case("HW_ADC_START_ERROR", labels=("adc", "injection"), contracts=("adc_start_error",))
def adc_start_error(t):
    scenarios.adc_start_error(t, EXPECTED)


@case("HW_ADC_DMA_TIMEOUT", labels=("adc", "dma", "injection"), contracts=("adc_dma_timeout",))
def adc_dma_timeout(t):
    scenarios.adc_dma_timeout(t, EXPECTED)


@case("HW_ADC_UNITS", labels=("adc", "units"))
def adc_units(t):
    scenarios.adc_units(t, EXPECTED)


@case("HW_ADC_INVALID", labels=("adc", "units"))
def adc_invalid(t):
    scenarios.adc_invalid(t, EXPECTED)


@case("HW_ADC_VECTORS", labels=("adc", "units"))
def adc_vectors(t):
    scenarios.adc_vectors(t, EXPECTED)
