"""
RU: Отказы ADC и DMA: инъекции в регистры, аргументы и обратный вызов; приложение реагирует штатно.
EN: ADC and DMA faults: injections into registers, arguments and the callback; the application reacts as designed.
"""
from stm32_gdbtest import case


# platform_fault codes of src/platform.c: the DMA stream is busy, the ADC is off.
FAULT_DMA_BUSY = 1
FAULT_ADC_OFF = 2
FAULT_ADC_TIMEOUT = 6

# SysTick counters are uint32_t and wrap around.
U32_MASK = 0xFFFFFFFF


# Выключение ADC проверяем отдельно; finally возвращает только прежний ADON.
@case("HW_ADC_DISABLED", labels=("adc", "injection"), contracts=("cmsis_adc_dma",))
def adc_disabled(t):
    t.reach("platform_adc_start")
    saved = t.mmio.read("ADC1.CR2")
    mask = t.evaluate("ADC_CR2_ADON")
    try:
        t.mmio.write("ADC1.CR2", saved & ~mask, allow_effects=True)
        t.reach("platform_error")
        t.check("disabled ADC error", t.read("platform_fault"), FAULT_ADC_OFF)
    finally:
        current = t.mmio.read("ADC1.CR2")
        restored = (current & ~mask) | (saved & mask)
        if restored != current:
            t.mmio.write("ADC1.CR2", restored, allow_effects=True)


# Маскируем только DMA IRQ, сохраняя его исходное разрешение.
@case("HW_ADC_TIMEOUT", labels=("adc", "injection"), contracts=("cmsis_adc_dma",))
def adc_timeout(t):
    deadline = t.profile.get("user.timing.adc_deadline_ticks")
    t.reach("platform_adc_start")
    word = t.evaluate("DMA2_Stream0_IRQn >> 5")
    bit = t.evaluate("1 << (DMA2_Stream0_IRQn & 31)")
    enabled = t.mmio.read(f"NVIC.ISER{word}") & bit
    before = t.read("platform_tick")
    try:
        t.mmio.write(f"NVIC.ICER{word}", bit, allow_effects=True)
        t.check("DMA interrupt disabled", t.mmio.read(f"NVIC.ISER{word}") & bit, 0)
        t.reach("platform_error")
        t.check("application deadline, ticks", (t.read("platform_tick") - before) & U32_MASK >= deadline)
        t.check("no publication", t.read("app_state.adc_sequences"), 0)
    finally:
        if enabled:
            t.mmio.write(f"NVIC.ISER{word}", enabled, allow_effects=True)


# Включаем уже настроенный поток без ADC trigger; NDTR/M0AR меняем только при EN=0.
@case("HW_ADC_BUSY", labels=("adc", "injection"), contracts=("cmsis_adc_dma",))
def adc_busy(t):
    t.reach("platform_adc_start")
    control = t.mmio.read("DMA2_Stream0.CR")
    enable = t.evaluate("DMA_SxCR_EN")
    if control & enable:
        raise RuntimeError("DMA must be disabled before injection")
    count = t.mmio.read("DMA2_Stream0.NDTR")
    address = t.mmio.read("DMA2_Stream0.M0AR")
    destination = t.evaluate("(unsigned int)samples")
    try:
        t.mmio.write("DMA2_Stream0.NDTR", 2)
        t.mmio.write("DMA2_Stream0.M0AR", destination)
        t.mmio.write("DMA2_Stream0.CR", control | enable, allow_effects=True)
        t.reach("platform_error")
        t.check("DMA ownership guard", t.read("platform_fault"), FAULT_DMA_BUSY)
    finally:
        current = t.mmio.read("DMA2_Stream0.CR")
        if current & enable:
            t.mmio.write("DMA2_Stream0.CR", current & ~enable, allow_effects=True)

        # Отказ остановки запрещает восстановление счётчика работающего DMA.
        for _ in range(8):
            if not t.mmio.read("DMA2_Stream0.CR") & enable:
                break
        else:
            raise RuntimeError("DMA disable not acknowledged; NDTR/M0AR restoration refused")
        t.mmio.write("DMA2_Stream0.NDTR", count)
        t.mmio.write("DMA2_Stream0.M0AR", address)
        t.mmio.write("DMA2_Stream0.CR", control, allow_effects=True)


# Verify that invalid samples give an empty INVALID measurement and the next normal one recovers.
@case("HW_ADC_INVALID", labels=("adc", "injection"))
def adc_invalid(t):
    # TECH-005 and TECH-007: one rail or zero sample per pass, substituted at the conversion entry.
    for argument, value in (("reference", 0), ("reference", 4095), ("temperature", 0)):
        t.reach("platform_adc_convert")
        t.write(argument, value)
        t.reach("loop")

        # The measurement of this pass is rejected as a whole.
        t.check([
            (f"{argument}={value}: INVALID quality", "app_state.measurement.quality", "ADC_INVALID"),
            (f"{argument}={value}: no VDDA", "app_state.measurement.vdda_mv", 0),
            (f"{argument}={value}: no temperature", "app_state.measurement.temperature_mdeg_c", 0)
        ])

    # The next measurement uses the real samples again.
    t.reach("loop")
    t.check("measurement recovers", t.evaluate("app_state.measurement.quality == ADC_FACTORY"))


# Verify the conversion arithmetic with the factory calibration samples as inputs: 3300 mV, 30 and 110 °C.
@case("HW_ADC_VECTORS", labels=("adc", "injection"))
def adc_vectors(t):
    adc = t.profile.data["board"]["adc"]
    reference = t.mmio.read("FACTORY.VREFINT_CAL")
    anchors = (("FACTORY.TS_CAL1", adc["ts_cal1_mdeg_c"]), ("FACTORY.TS_CAL2", adc["ts_cal2_mdeg_c"]))

    # TECH-007: a calibration sample as the input gives exactly its calibration point.
    for register, degrees in anchors:
        t.reach("platform_adc_convert")

        # Both arguments are replaced by the factory samples read from the system memory.
        t.write([("temperature", t.mmio.read(register)), ("reference", reference)])
        t.reach("loop")

        # The published measurement is the calibration point itself.
        t.check([
            (f"{degrees} m°C: factory quality", "app_state.measurement.quality", "ADC_FACTORY"),
            (f"{degrees} m°C: calibration VDDA", "app_state.measurement.vdda_mv", adc["calibration_vdda_mv"]),
            (f"{degrees} m°C: calibration temperature", "app_state.measurement.temperature_mdeg_c", degrees)
        ])


# Verify the application deadline when the completion callback is lost after a finished DMA transfer.
@case("HW_ADC_CALLBACK_SUPPRESSED", labels=("adc", "injection"), contracts=("cmsis_adc_dma",))
def adc_callback_suppressed(t):
    deadline = t.profile.get("user.timing.adc_deadline_ticks")
    t.reach("DMA2_Stream0_IRQHandler")

    # The transfer is complete before the injection: this models a lost notification, not a DMA failure.
    t.check("DMA finished before the injection", t.mmio.read('DMA2_Stream0.NDTR'), 0)
    t.check("completion pending", t.mmio.read('DMA2.LISR') & t.evaluate('DMA_LISR_TCIF0'))

    # TECH-004: app_adc_complete() is void(void); returning at its entry skips the notification.
    t.reach("app_adc_complete")
    t.check("notification initially absent", t.read("adc_ready"), False)
    t.ret()
    t.reach("platform_ticks")
    before = t.read("platform_tick")

    # loop() waits for the deadline and reports it through platform_error().
    t.reach("platform_error")
    t.check("application deadline, ticks", (t.read("platform_tick") - before) & U32_MASK >= deadline)

    # Nothing is published; the diagnostic distinguishes an application deadline from platform faults.
    t.check([
        ("no publication", "app_state.adc_sequences", 0),
        ("notification remains absent", "adc_ready", 0),
        ("application ADC timeout", "platform_fault", FAULT_ADC_TIMEOUT)
    ])
