#include "app.h"
#include <cassert>
#include <initializer_list>

static void expect(AdcReading value, uint32_t mv, int32_t mc, AdcQuality quality)
{
    assert(value.vdda_mv == mv);
    assert(value.temperature_mdeg_c == mc);
    assert(value.quality == quality);
}

int main()
{
    expect(adc_convert_typical(1716, 1440), 3412, 25000, ADC_TYPICAL);
    expect(adc_convert_typical(2145, 1800), 2730, 25000, ADC_TYPICAL);
    expect(adc_convert_typical(1974, 1440), 3412, -25000, ADC_TYPICAL);
    expect(adc_convert_typical(1329, 1440), 3412, 100000, ADC_TYPICAL);
    expect(adc_convert_factory(900, 1500, 1500, 900, 1100), 3300, 30000, ADC_FACTORY);
    expect(adc_convert_factory(1000, 1500, 1500, 900, 1100), 3300, 70000, ADC_FACTORY);
    expect(adc_convert_factory(1100, 1500, 1500, 900, 1100), 3300, 110000, ADC_FACTORY);
    expect(adc_convert_factory(750, 1500, 1500, 900, 1100), 3300, -30000, ADC_FACTORY);
    expect(adc_convert_factory(990, 1650, 1500, 900, 1100), 3000, 30000, ADC_FACTORY);
    for (uint16_t invalid : {uint16_t(0), uint16_t(4095), uint16_t(65535)}) {
        expect(adc_convert_typical(1716, invalid), 0, 0, ADC_INVALID);
        expect(adc_convert_typical(invalid, 1440), 0, 0, ADC_INVALID);
        expect(adc_convert_factory(900, invalid, 1500, 900, 1100), 0, 0, ADC_INVALID);
        expect(adc_convert_factory(900, 1500, invalid, 900, 1100), 0, 0, ADC_INVALID);
    }
    expect(adc_convert_factory(900, 1500, 1500, 900, 900), 0, 0, ADC_INVALID);
    expect(adc_convert_factory(900, 1500, 1500, 1100, 900), 0, 0, ADC_INVALID);
    expect(adc_convert_typical(1716, 1), 0, 0, ADC_INVALID);
    expect(adc_convert_typical(1716, 4000), 0, 0, ADC_INVALID);
}
