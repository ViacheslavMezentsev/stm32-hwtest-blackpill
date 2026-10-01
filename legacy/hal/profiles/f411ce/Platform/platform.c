#include "app.h"
#include "main.h"
#include "adc.h"
#include "tim.h"
#include "rtc.h"
#include "stm32f4xx_ll_adc.h"

void platform_adc_prepare(void)
{
    /* F411 has no F1-style ADC calibration procedure. */
}

void platform_rtc_prepare(void)
{
    if (HAL_RTC_DeactivateAlarm(&hrtc, RTC_ALARM_A) != HAL_OK) Error_Handler();
    if (HAL_RTC_DeactivateAlarm(&hrtc, RTC_ALARM_B) != HAL_OK) Error_Handler();
}

void platform_rtc_arm(void)
{
    RTC_TimeTypeDef time = {0};
    RTC_DateTypeDef date = {0};
    RTC_AlarmTypeDef alarm = {0};
    if (HAL_RTC_GetTime(&hrtc, &time, RTC_FORMAT_BIN) != HAL_OK) Error_Handler();
    /* F4 shadow registers require GetDate after GetTime. */
    if (HAL_RTC_GetDate(&hrtc, &date, RTC_FORMAT_BIN) != HAL_OK) Error_Handler();
    uint32_t seconds = (time.Hours * 3600U + time.Minutes * 60U + time.Seconds + 2U) % 86400U;
    alarm.AlarmTime.Hours = seconds / 3600U;
    alarm.AlarmTime.Minutes = (seconds / 60U) % 60U;
    alarm.AlarmTime.Seconds = seconds % 60U;
    alarm.Alarm = RTC_ALARM_A;
    alarm.AlarmMask = RTC_ALARMMASK_DATEWEEKDAY;
    alarm.AlarmSubSecondMask = RTC_ALARMSUBSECONDMASK_ALL;
    alarm.AlarmDateWeekDaySel = RTC_ALARMDATEWEEKDAYSEL_DATE;
    alarm.AlarmDateWeekDay = 1;
    if (HAL_RTC_SetAlarm_IT(&hrtc, &alarm, RTC_FORMAT_BIN) != HAL_OK) Error_Handler();
}

AdcReading platform_adc_convert(uint16_t temperature, uint16_t reference)
{
    return adc_convert_factory(temperature, reference, *VREFINT_CAL_ADDR,
                               *TEMPSENSOR_CAL1_ADDR, *TEMPSENSOR_CAL2_ADDR);
}

void platform_timer_start(void)
{
    if (HAL_TIM_Base_Start_IT(&htim2) != HAL_OK) Error_Handler();
}

void platform_adc_start(volatile uint16_t* samples)
{
    if (HAL_ADC_Start_DMA(&hadc1, (uint32_t*)samples, 2) != HAL_OK) Error_Handler();
}

void platform_adc_stop(void)
{
    if (HAL_ADC_Stop_DMA(&hadc1) != HAL_OK) Error_Handler();
}

void platform_led_toggle(void) { HAL_GPIO_TogglePin(LED_USER_GPIO_Port, LED_USER_Pin); }
void platform_sleep(void) { HAL_PWR_EnterSLEEPMode(PWR_MAINREGULATOR_ON, PWR_SLEEPENTRY_WFI); }
uint32_t platform_ticks(void) { return HAL_GetTick(); }
void platform_error(void) { Error_Handler(); }

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* adc)
{
    if (adc == &hadc1) app_adc_complete();
}

void HAL_ADC_ErrorCallback(ADC_HandleTypeDef* adc)
{
    if (adc == &hadc1) Error_Handler();
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* timer)
{
    if (timer == &htim2) app_timer_event();
}

void HAL_RTC_AlarmAEventCallback(RTC_HandleTypeDef* rtc)
{
    if (rtc == &hrtc) app_rtc_event();
}
