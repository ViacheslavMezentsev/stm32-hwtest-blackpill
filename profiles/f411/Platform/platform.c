#include "app.h"
#include "main.h"
#include "adc.h"
#include "rtc.h"

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
