"""Configuration checks only: no claims about conversions, IRQ timing or RTC alarms."""
from hwtest import case


@case("HW_ADC_DMA_INIT", labels=("adc", "dma", "init"))
def adc_dma_init(t):
    t.reach("setup")
    t.fields("hadc1", {"Instance": "ADC1", "Init.NbrOfConversion": 2,
                       "Init.ContinuousConvMode": 0, "Init.ScanConvMode": 1,
                       "Init.ClockPrescaler": "ADC_CLOCK_SYNC_PCLK_DIV2"})
    t.check("ADC sequence length", (t.value("ADC1->SQR1") >> 20) & 15, 1)
    sqr3 = t.value("ADC1->SQR3")
    # F411 HAL's TEMPSENSOR constant includes a routing flag, not only the SQR channel.
    t.check("rank 1 temperature (physical channel 18)", sqr3 & 31, 18)
    t.check("rank 2 VREFINT", (sqr3 >> 5) & 31, t.value("ADC_CHANNEL_VREFINT"))
    for channel in (17, 18):
        t.check(f"channel {channel} sampling 480 cycles",
                (t.value("ADC1->SMPR1") >> (3 * (channel - 10))) & 7, 7)
    t.fields("hdma_adc1", {"Instance": "DMA2_Stream0", "Init.Channel": "DMA_CHANNEL_0",
                           "Init.Direction": "DMA_PERIPH_TO_MEMORY", "Init.Mode": "DMA_NORMAL",
                           "Init.MemInc": "DMA_MINC_ENABLE",
                           "Init.PeriphDataAlignment": "DMA_PDATAALIGN_HALFWORD",
                           "Init.MemDataAlignment": "DMA_MDATAALIGN_HALFWORD"})


@case("HW_TIM2_INIT", labels=("tim", "init"))
def tim2_init(t):
    t.reach("setup")
    t.check("TIM2 prescaler", t.value("TIM2->PSC"), 7999)
    t.check("TIM2 period", t.value("TIM2->ARR"), 99)
    t.check("TIM2 not started", t.value("TIM2->CR1") & 1, 0)


@case("HW_RTC_INIT", labels=("rtc", "init"))
def rtc_init(t):
    t.reach("setup")
    t.check("RTC source LSI", (t.value("RCC->BDCR") >> 8) & 3, 2)
    t.check("RTC clock enabled", (t.value("RCC->BDCR") >> 15) & 1, 1)
    t.check("LSI ready", (t.value("RCC->CSR") >> 1) & 1, 1)
    t.check("RTC asynchronous divider", (t.value("RTC->PRER") >> 16) & 127, 127)
    t.check("RTC synchronous divider", t.value("RTC->PRER") & 32767, 255)
    t.check("RTC output disabled", (t.value("RTC->CR") >> 21) & 3, 0)
