"""
RU: ADC и DMA: конфигурация, публикация измерения, кто считает последовательности и серия измерений.
EN: ADC and DMA: configuration, measurement publication, who counts the sequences and a measurement series.
"""
from statistics import mean

from stm32_gdbtest import case, within


# Маска CMSIS без чтения целевой памяти.
ADC_MODE_BITS = 'ADC_CR2_ADON | ADC_CR2_DMA | ADC_CR2_DDS'

# Маска CMSIS без чтения целевой памяти.
DMA_FORMAT_BITS = 'DMA_SxCR_MSIZE | DMA_SxCR_PSIZE | DMA_SxCR_MINC'

# Маска CMSIS без чтения целевой памяти.
DMA_HALFWORD_BITS = 'DMA_SxCR_MSIZE_0 | DMA_SxCR_PSIZE_0 | DMA_SxCR_MINC'

# Маска CMSIS без чтения целевой памяти.
DMA_ERROR_BITS = 'DMA_LISR_TEIF0 | DMA_LISR_DMEIF0 | DMA_LISR_FEIF0'


# A valid 12-bit ADC sample excludes both rails (src/adc_units.cpp, valid_raw).
VALID_SAMPLE = within(1, 4094)


# Verify the scan sequence (temperature, then VREFINT) and the DMA stream that collects it.
@case("HW_ADC_INIT", labels=("adc",), contracts=("cmsis_adc_dma",))
def adc_init(t):
    adc = t.profile.data["board"]["adc"]

    # TECH-001: the macros are visible in platform.c; platform_adc_start() runs after the preparation.
    t.reach("platform_adc_start")

    sequence = (adc["temperature_channel"] << t.evaluate("ADC_SQR3_SQ1_Pos"))
    sequence |= adc["vrefint_channel"] << t.evaluate("ADC_SQR3_SQ2_Pos")

    # The temperature channel differs between F411 (18) and F401 (16); the board data names it.
    t.check("temperature, then VREFINT", t.mmio.read('ADC1.SQR3'), sequence)
    t.check("two conversions", t.mmio.read('ADC1.SQR1') & t.evaluate('ADC_SQR1_L'), t.evaluate("1 << ADC_SQR1_L_Pos"))
    t.check("scan mode", t.mmio.read('ADC1.CR1') & t.evaluate('ADC_CR1_SCAN'))
    t.check("ADC on with continuous DMA requests",
            t.mmio.read('ADC1.CR2') & (t.evaluate(ADC_MODE_BITS)),
            t.evaluate(ADC_MODE_BITS))
    t.check("internal channels enabled", t.mmio.read('ADC.CCR') & t.evaluate('ADC_CCR_TSVREFE'))
    t.check("halfword transfers, memory increment",
            t.mmio.read('DMA2_Stream0.CR') & (t.evaluate(DMA_FORMAT_BITS)),
            t.evaluate(DMA_HALFWORD_BITS))
    t.check("peripheral address is ADC1->DR", t.mmio.read('DMA2_Stream0.PAR'), t.evaluate("(unsigned int)&ADC1->DR"))


# Verify that one completed DMA sequence is published as a factory-calibrated measurement.
@case("HW_ADC_RUNTIME", labels=("adc",))
def adc_runtime(t):
    vdda_window = within(*t.profile.get("user.adc.vdda_mv"))

    # The second entry of loop() follows exactly one measurement.
    t.reach("loop")
    t.reach("loop")

    # A plausibility check of the published values, not metrology.
    t.check([
        ("one DMA sequence published", "app_state.adc_sequences", 1),
        ("factory calibration used", "app_state.measurement.quality", "ADC_FACTORY"),
        ("temperature sample", "app_state.temperature_raw", VALID_SAMPLE),
        ("VREFINT sample", "app_state.vrefint_raw", VALID_SAMPLE),
        ("VDDA within the application window, mV", "app_state.measurement.vdda_mv", vdda_window)
    ])


# Verify the natural DMA interrupt and that its two samples are published exactly once, after the callback.
@case("HW_ADC_DMA_PUBLICATION", labels=("adc", "irq"), contracts=("cmsis_adc_dma",))
def adc_dma_publication(t):
    t.reach("DMA2_Stream0_IRQHandler")

    # TECH-003: a natural peripheral interrupt with a completed transfer, not a software-pended exception.
    t.check("DMA2 stream 0 exception",
            t.mmio.read('SCB.ICSR') & t.evaluate('SCB_ICSR_VECTACTIVE_Msk'),
            t.evaluate("DMA2_Stream0_IRQn + 16"))
    t.check("transfer complete", t.mmio.read('DMA2.LISR') & t.evaluate('DMA_LISR_TCIF0'))
    t.check("no DMA errors", t.mmio.read('DMA2.LISR') & (t.evaluate(DMA_ERROR_BITS)), 0)
    t.check("two samples transferred", t.mmio.read('DMA2_Stream0.NDTR'), 0)
    t.check("normal mode stream stopped", t.mmio.read('DMA2_Stream0.CR') & t.evaluate('DMA_SxCR_EN'), 0)

    # The samples are read from the DMA destination in SRAM before the application copies them.
    buffer = t.memory(t.mmio.read('DMA2_Stream0.M0AR'), 4)
    temperature, reference = int.from_bytes(buffer[:2], "little"), int.from_bytes(buffer[2:], "little")
    t.reach("app_adc_complete")
    t.check("not published before the callback", t.read("app_state.adc_sequences"), 0)

    t.reach("platform_led_toggle")

    # loop() publishes the copy before it toggles the LED, once per measurement.
    t.check([
        ("published exactly once", "app_state.adc_sequences", 1),
        ("temperature from DMA", "app_state.temperature_raw", temperature),
        ("reference from DMA", "app_state.vrefint_raw", reference),
        ("factory result", "app_state.measurement.quality", "ADC_FACTORY")
    ])


# Find who counts the measurements: loop(), called from main(), after the measurement is stored.
@case("HW_ADC_WRITER", labels=("adc", "watch"))
def adc_writer(t):
    # TECH-013: a write watch point stops just after the store that changes the counter.
    with t.watch("app_state.adc_sequences"):
        t.check("the stop is the watch point", t.resume()["stop"]["kind"], "watchpoint")
        chain = t.frames(4)["frames"]
        t.record("writer", dict(frames=chain))
        t.check("loop() counts the sequence, called from main()", [frame["name"] for frame in chain[:2]],
                ["loop", "main"])

    # The measurement is complete before it is counted.
    t.check([
        ("the first sequence counted", "app_state.adc_sequences", 1),
        ("measurement stored before counting", "app_state.measurement.quality", "ADC_FACTORY")
    ])


# Collect a series of measurements and check that consecutive values are stable.
@case("HW_ADC_SERIES", timeout_s=30, labels=("adc", "records"))
def adc_series(t):
    count = t.profile.get("user.series.count")
    factory = t.evaluate("ADC_FACTORY")

    # TECH-011: one record per measurement, taken where loop() has just published it.
    for _ in range(count):
        t.reach("platform_led_toggle")
        t.record("adc", dict(sequence=t.read("app_state.adc_sequences"), **t.read("app_state.measurement")))

    # The series is evaluated in Python from the records, without touching the target again.
    series = [record["data"] for record in t.records("adc")]
    vdda = [item["vdda_mv"] for item in series]
    temperature = [item["temperature_mdeg_c"] for item in series]
    t.check("one record per sequence", [item["sequence"] for item in series], list(range(1, count + 1)))
    t.check("factory quality throughout", all(item["quality"] == factory for item in series))
    t.check("mean VDDA within the application window, mV", mean(vdda), within(*t.profile.get("user.adc.vdda_mv")))
    t.check("VDDA spread, mV", max(vdda) - min(vdda), within(0, t.profile.get("user.series.vdda_spread_mv")))
    t.check("temperature spread, m°C", max(temperature) - min(temperature),
            within(0, t.profile.get("user.series.temperature_spread_mdeg_c")))
