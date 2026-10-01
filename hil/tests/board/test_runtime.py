"""Consumer adaptations of stm32-gdbtest TECH-001/002/003/004.

Source and evidence boundaries: docs/CMSIS_RUNTIME_SCENARIOS.md.
CMSIS expressions are evaluated in platform.c frames; numeric expectations are
independent of the macros used to select register fields.
"""
from stm32_gdbtest import case


@case("HW_CLOCK_GPIO_CONFIG")
def clock_gpio_config(t):
    # TECH-001: macro scope belongs to the selected ELF frame.
    t.reach("platform_led_toggle")
    t.check("HSI ready and enabled", t.value("RCC->CR & (RCC_CR_HSION | RCC_CR_HSIRDY)"), 3)
    t.check("HSI and bus dividers", t.value("RCC->CFGR & (RCC_CFGR_SWS | RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2)"), 0)
    t.check("core clock", t.value("SystemCoreClock"), 16000000)
    t.check("SysTick reload", t.value("SysTick->LOAD"), 15999)
    # Reading CTRL clears COUNTFLAG; this application uses the ISR tick counter.
    t.check("SysTick source and interrupt", t.value("SysTick->CTRL & (SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk)"), 7)
    t.check("GPIOC clock", t.value("RCC->AHB1ENR & RCC_AHB1ENR_GPIOCEN"), 4)
    t.check("PC13 output", t.value("GPIOC->MODER & GPIO_MODER_MODER13"), 1 << 26)
    t.check("PC13 push pull", t.value("GPIOC->OTYPER & GPIO_OTYPER_OT13"), 0)
    t.check("PC13 low speed", t.value("GPIOC->OSPEEDR & GPIO_OSPEEDER_OSPEEDR13"), 0)
    t.check("PC13 no pull", t.value("GPIOC->PUPDR & GPIO_PUPDR_PUPDR13"), 0)


@case("HW_TIMER_IRQ_PUBLICATION")
def timer_irq_publication(t):
    t.reach("TIM2_IRQHandler")
    # TECH-002: preserve an address before leaving the CMSIS macro scope.
    icsr = t.value("&SCB->ICSR")
    for _ in range(2):
        # TECH-003: natural peripheral IRQ, not a software-pended exception.
        t.check("TIM2 exception", t.value("SCB->ICSR & SCB_ICSR_VECTACTIVE_Msk"), 44)
        t.check("update flag", t.value("TIM2->SR & TIM_SR_UIF"), 1)
        before = t.value("app_state.timer_events")
        t.reach("TIM2_IRQHandler")
        t.check("one event per completed handler", t.value("app_state.timer_events"), (before + 1) & 0xFFFFFFFF)
    t.reach("platform_led_toggle")
    t.check("returned to thread mode", t.value(f"*(unsigned int*){icsr} & 0x1FF"), 0)


@case("HW_ADC_DMA_PUBLICATION")
def adc_dma_publication(t):
    t.reach("DMA2_Stream0_IRQHandler")
    t.check("DMA exception", t.value("SCB->ICSR & SCB_ICSR_VECTACTIVE_Msk"), 72)
    t.check("transfer complete", t.value("DMA2->LISR & DMA_LISR_TCIF0"), 1 << 5)
    t.check("no DMA errors", t.value("DMA2->LISR & (DMA_LISR_TEIF0 | DMA_LISR_DMEIF0 | DMA_LISR_FEIF0)"), 0)
    t.check("two samples transferred", t.value("DMA2_Stream0->NDTR"), 0)
    t.check("normal mode stream stopped", t.value("DMA2_Stream0->CR & DMA_SxCR_EN"), 0)
    samples = t.value("DMA2_Stream0->M0AR")
    raw = [t.value(f"((unsigned short*){samples})[{i}]") for i in range(2)]
    t.reach("app_adc_complete")
    t.check("not published before callback", t.value("app_state.adc_sequences"), 0)
    t.reach("platform_led_toggle")
    t.check("published exactly once", t.value("app_state.adc_sequences"), 1)
    t.check("temperature from DMA", t.value("app_state.temperature_raw"), raw[0])
    t.check("reference from DMA", t.value("app_state.vrefint_raw"), raw[1])
    t.check("factory result", t.value("app_state.measurement.quality"), 2)


@case("HW_ADC_CALLBACK_SUPPRESSED")
def adc_callback_suppressed(t):
    # TECH-004: void(void), real non-inlined frame; DMA already completed.
    # This models a lost notification, not a failed ADC or DMA transfer.
    t.reach("DMA2_Stream0_IRQHandler")
    t.check("DMA finished before injection", t.value("DMA2_Stream0->NDTR"), 0)
    t.check("completion pending", t.value("DMA2->LISR & DMA_LISR_TCIF0"), 1 << 5)
    t.reach("app_adc_complete")
    t.check("notification initially absent", t.value("adc_ready"), 0)
    t.force_return("")
    t.reach("platform_ticks")
    before = t.value("platform_tick")
    t.reach("platform_error")
    t.check("application deadline", (t.value("platform_tick") - before) & 0xFFFFFFFF >= 100, True)
    t.check("no publication", t.value("app_state.adc_sequences"), 0)
    t.check("notification remains absent", t.value("adc_ready"), 0)
    t.check("application timeout, not platform fault", t.value("platform_fault"), 0)
