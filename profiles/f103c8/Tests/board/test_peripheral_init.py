"""Configuration checks only: no claims about conversions, IRQ timing or RTC alarms."""
from hwtest import case


@case("HW_ADC_DMA_INIT", labels=("adc", "dma", "init"))
def adc_dma_init(t):
    t.reach("setup")
    t.fields("hadc1", {"Instance": "ADC1", "Init.NbrOfConversion": 2,
                       "Init.ContinuousConvMode": 0, "Init.ScanConvMode": "ADC_SCAN_ENABLE"})
    t.check("ADC sequence length", (t.value("ADC1->SQR1") >> 20) & 15, 1)
    t.check("ADC PCLK2 /8", (t.value("RCC->CFGR") >> 14) & 3, 3)
    sqr3 = t.value("ADC1->SQR3")
    t.check("rank 1 temperature (physical channel 16)", sqr3 & 31, 16)
    t.check("rank 2 VREFINT", (sqr3 >> 5) & 31, t.value("ADC_CHANNEL_VREFINT"))
    for channel in (16, 17):
        t.check(f"channel {channel} sampling 239.5 cycles",
                (t.value("ADC1->SMPR1") >> (3 * (channel - 10))) & 7, 7)
    t.fields("hdma_adc1", {"Instance": "DMA1_Channel1",
                           "Init.Direction": "DMA_PERIPH_TO_MEMORY", "Init.Mode": "DMA_NORMAL",
                           "Init.MemInc": "DMA_MINC_ENABLE",
                           "Init.PeriphDataAlignment": "DMA_PDATAALIGN_HALFWORD",
                           "Init.MemDataAlignment": "DMA_MDATAALIGN_HALFWORD"})


@case("HW_TIM2_INIT", labels=("tim", "init"), contracts=("tim_init_macros",))
def tim2_init(t):
    t.reach("setup")
    t.check("TIM2 prescaler", t.value("TIM2->PSC"), 7999)
    t.check("TIM2 period", t.value("__HAL_TIM_GET_AUTORELOAD(&htim2)"), 99)
    t.check("TIM2 not started", t.value("TIM2->CR1 & TIM_CR1_CEN"), 0)


@case("HW_RTC_INIT", labels=("rtc", "init"))
def rtc_init(t):
    t.reach("setup")
    t.check("RTC source LSI", (t.value("RCC->BDCR") >> 8) & 3, 2)
    t.check("RTC clock enabled", (t.value("RCC->BDCR") >> 15) & 1, 1)
    t.check("LSI ready", (t.value("RCC->CSR") >> 1) & 1, 1)
    prescaler = ((t.value("RTC->PRLH") & 15) << 16) | t.value("RTC->PRLL")
    t.check("RTC LSI prescaler", prescaler, 39999)
    t.check("RTC output disabled", t.value("BKP->RTCCR") & 0x380, 0)
