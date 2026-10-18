"""
RU: Потеря уведомления ADC оставляет диагностический код таймаута перед остановкой.
EN: A lost ADC notification leaves a diagnostic timeout code before the application halts.
"""
from stm32_gdbtest import case


# Give an application ADC timeout a distinct diagnostic code, independently of the firmware enum.
@case("HW_ADC_TIMEOUT_DIAGNOSTIC", labels=("adc", "injection"), contracts=("cmsis_adc_dma",))
def adc_timeout_diagnostic(t):
    deadline = t.profile.get("user.timing.adc_deadline_ticks")
    t.reach("platform_adc_start")

    # Clear only the DMA interrupt enable; the ADC and DMA transfer may still complete normally.
    word, bit = "DMA2_Stream0_IRQn >> 5", "1 << (DMA2_Stream0_IRQn & 31)"
    t.write(f"NVIC->ICER[{word}]", bit)
    t.check("DMA notification disabled", t.evaluate(f"NVIC->ISER[{word}] & ({bit})"), 0)
    before = t.read("platform_tick")

    # Retain the failure state before checking the new diagnostic requirement.
    t.reach("platform_error")
    elapsed = (t.read("platform_tick") - before) & 0xFFFFFFFF
    t.record("adc.timeout", {"elapsed_ticks": elapsed, "fault": t.read("platform_fault")})
    t.check("deadline elapsed", elapsed >= deadline)
    t.check("no publication", t.read("app_state.adc_sequences"), 0)
    t.check("application ADC timeout code", t.read("platform_fault"), 6)
