from stm32_gdbtest import case

@case("HW_BOOT")
def boot(t):
 t.reach("loop")
 t.check("no fault",t.value("platform_fault"),0)
 t.check("reset clocks",t.value("SystemCoreClock"),16000000)
 t.check("HSI /1",t.value("*(unsigned int*)0x40023808 & 0xFCFC"),0)

@case("HW_GPIO")
def gpio(t):
 t.reach("platform_led_toggle")
 t.check("PC13 output",t.value("(GPIOC->MODER>>26)&3"),1)
 t.check("initial off",t.value("(GPIOC->ODR>>13)&1"),1)
 t.reach("platform_led_toggle")
 t.check("on",t.value("(GPIOC->ODR>>13)&1"),0)
 t.reach("platform_led_toggle")
 t.check("off",t.value("(GPIOC->ODR>>13)&1"),1)

@case("HW_ADC_INIT")
def adc_init(t):
 t.reach("platform_adc_start")
 f411=t.profile["mcu"] == "STM32F411CEU6"
 t.check("scan channels",t.value("ADC1->SQR3"),(18 if f411 else 16)|(17<<5))
 t.check("two ranks",t.value("ADC1->SQR1"),1<<20)
 t.check("DMA widths/increment",t.value("DMA2_Stream0->CR & 0x7C00"),0x2C00)

@case("HW_ADC_RUNTIME")
def adc_runtime(t):
 t.reach("loop")
 t.reach("loop")
 t.check("one DMA sequence published",t.value("app_state.adc_sequences"),1)
 t.check("factory quality",t.value("app_state.measurement.quality"),2)
 t.check("reference nonzero",t.value("app_state.vrefint_raw")>0,True)
 t.check("VDDA sanity",2000<t.value("app_state.measurement.vdda_mv")<4000,True)

@case("HW_TIMER")
def timer(t):
 t.reach("TIM2_IRQHandler")
 t.check("PSC",t.value("TIM2->PSC"),15999)
 t.check("ARR",t.value("TIM2->ARR"),99)
 before=t.value("app_state.timer_events")
 t.reach("loop")
 t.check("event delivered",t.value("app_state.timer_events")>before,True)

@case("HW_RTC", timeout_s=30)
def rtc(t):
 t.reach("RTC_Alarm_IRQHandler")
 t.check("prescalers",t.value("RTC->PRER"),(127<<16)|249)
 t.check("first alarm two seconds",t.value("RTC->ALRMAR") & 0x7F,2)
 t.reach("RTC_Alarm_IRQHandler")
 t.check("application rearmed",t.value("app_state.rtc_events")>=1,True)
 t.check("next alarm changed",(t.value("RTC->ALRMAR") & 0x7F)!=2,True)

@case("HW_ADC_DISABLED")
def disabled(t):
 t.reach("platform_adc_start")
 t.set_value("ADC1->CR2",t.value("ADC1->CR2") & ~1)
 t.reach("platform_error")
 t.check("disabled ADC error",t.value("platform_fault"),2)

@case("HW_ADC_TIMEOUT")
def timeout(t):
 t.reach("platform_adc_start")
 t.set_value("NVIC->ICER[1]",1<<24)
 before=t.value("platform_tick")
 t.reach("platform_error")
 t.check("application deadline",t.value("platform_tick")-before>=100,True)
 t.check("no publication",t.value("app_state.adc_sequences"),0)

@case("HW_RTC_DEADLINE")
def rtc_deadline(t):
 t.reach("wait_set",when="code == 12")
 t.set_value("mask",0)
 t.reach("platform_error")
 t.check("RTC wait error",t.value("platform_fault"),12)

@case("HW_ADC_INVALID")
def adc_invalid(t):
 for parameter,value in (("reference",0),("reference",4095),("temperature",0)):
  t.reach("platform_adc_convert")
  t.set_value(parameter,value)
  t.reach("loop")
  t.fields("app_state.measurement",{"quality":0,"vdda_mv":0,"temperature_mdeg_c":0})
 t.reach("loop")
 t.check("measurement recovers",t.value("app_state.measurement.quality"),2)

@case("HW_ADC_VECTORS")
def adc_vectors(t):
 for address,degrees in ((0x1FFF7A2C,30000),(0x1FFF7A2E,110000)):
  t.reach("platform_adc_convert")
  t.set_value("temperature",t.value(f"*(unsigned short*){address}"))
  t.set_value("reference",t.value("*(unsigned short*)0x1FFF7A2A"))
  t.reach("loop")
  t.fields("app_state.measurement",{"quality":2,"vdda_mv":3300,"temperature_mdeg_c":degrees})

@case("HW_ADC_BUSY")
def adc_busy(t):
 t.reach("platform_adc_start")
 t.set_value("DMA2_Stream0->NDTR",2)
 # Configure a valid destination before enabling the stream; no trigger is issued.
 t.set_value("DMA2_Stream0->M0AR",t.value("samples"))
 t.set_value("DMA2_Stream0->CR",t.value("DMA2_Stream0->CR")|1)
 t.reach("platform_error")
 t.check("DMA ownership guard",t.value("platform_fault"),1)
