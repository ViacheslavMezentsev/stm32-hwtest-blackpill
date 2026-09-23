#include "app.h"
#include "main.h"
#include "adc.h"
#include "tim.h"
#include "rtc.h"

volatile AppState app_state = {};
alignas( 4 ) static volatile uint16_t adc_samples[2];
static volatile bool adc_ready;
static uint32_t rtc_handled;

void init( void )
{
}

void setup( void )
{
    platform_adc_prepare();
    platform_rtc_prepare();
    platform_rtc_arm();
    if ( HAL_TIM_Base_Start_IT( &htim2 ) != HAL_OK ) Error_Handler();
}

void loop( void )
{
    adc_ready = false;
    if ( HAL_ADC_Start_DMA( &hadc1, ( uint32_t* ) adc_samples, 2 ) != HAL_OK ) Error_Handler();
    const uint32_t started = HAL_GetTick();
    while ( !adc_ready )
    {
        if ( ( uint32_t ) ( HAL_GetTick() - started ) >= 100 ) Error_Handler();
    }
    if ( HAL_ADC_Stop_DMA( &hadc1 ) != HAL_OK ) Error_Handler();
    app_state.temperature_raw = adc_samples[0];
    app_state.vrefint_raw     = adc_samples[1];
    ++app_state.adc_sequences;
    const uint32_t events = app_state.rtc_events;
    if ( events != rtc_handled )
    {
        platform_rtc_arm();
        rtc_handled = events;
    }
    HAL_GPIO_TogglePin( LED_USER_GPIO_Port, LED_USER_Pin );
    HAL_Delay( 500 );
}

extern "C" void HAL_ADC_ConvCpltCallback( ADC_HandleTypeDef* adc )
{
    if ( adc == &hadc1 ) adc_ready = true;
}

extern "C" void HAL_ADC_ErrorCallback( ADC_HandleTypeDef* adc )
{
    if ( adc == &hadc1 ) Error_Handler();
}

extern "C" void HAL_TIM_PeriodElapsedCallback( TIM_HandleTypeDef* timer )
{
    if ( timer == &htim2 ) ++app_state.timer_events;
}

extern "C" void HAL_RTC_AlarmAEventCallback( RTC_HandleTypeDef* rtc )
{
    if ( rtc == &hrtc ) ++app_state.rtc_events;
}
