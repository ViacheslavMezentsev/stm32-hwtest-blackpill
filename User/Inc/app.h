#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void init( void );
void setup( void );
void loop( void );

/* Application telemetry; raw ADC values are not calibrated physical units. */
typedef struct
{
    uint32_t adc_sequences;
    uint32_t timer_events;
    uint32_t rtc_events;
    uint16_t temperature_raw;
    uint16_t vrefint_raw;
} AppState;

extern volatile AppState app_state;
void platform_adc_prepare( void );
void platform_rtc_prepare( void );
void platform_rtc_arm( void );
#ifdef __cplusplus
}
#endif
