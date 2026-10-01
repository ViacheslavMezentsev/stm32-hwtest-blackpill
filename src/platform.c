#include "app.h"
#include "stm32f4xx.h"
uint32_t SystemCoreClock = 16000000U;
volatile uint32_t platform_tick;
volatile uint32_t platform_fault;

void platform_error( void )
{
    for ( ;; )
        __WFI();
}

static void fail( uint32_t code )
{
    platform_fault = code;
    platform_error();
}

static void wait_set( volatile uint32_t* reg, uint32_t mask, uint32_t code )
{
    uint32_t start = platform_tick;
    while ( ( *reg & mask ) == 0 )
    {
        if ( ( uint32_t ) ( platform_tick - start ) >= 1000 ) fail( code );
    }
}

uint32_t platform_ticks( void )
{
    return platform_tick;
}

void SysTick_Handler( void )
{
    ++platform_tick;
}

void platform_sleep( void )
{
    __WFI();
}

void platform_led_toggle( void )
{
    GPIOC->ODR ^= ( 1U << 13 );
}

void platform_init( void )
{
    /* Reset HSI16; no PLL. This startup is entered after a system reset. */
    SCB->CPACR |= ( 0xFU << 20 );
    __DSB();
    __ISB();
    SysTick_Config( SystemCoreClock / 1000U );
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOCEN;
    ( void ) RCC->AHB1ENR;
    GPIOC->BSRR     = 1U << 13;
    GPIOC->MODER    = ( GPIOC->MODER & ~( 3U << 26 ) ) | ( 1U << 26 );
    GPIOC->OTYPER  &= ~( 1U << 13 );
    GPIOC->OSPEEDR &= ~( 3U << 26 );
    GPIOC->PUPDR   &= ~( 3U << 26 );
}

void platform_timer_start( void )
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
    ( void ) RCC->APB1ENR;
    RCC->APB1RSTR |= RCC_APB1RSTR_TIM2RST;
    RCC->APB1RSTR &= ~RCC_APB1RSTR_TIM2RST;
    TIM2->PSC      = 15999;
    TIM2->ARR      = 99;
    TIM2->EGR      = TIM_EGR_UG;
    TIM2->SR       = 0;
    NVIC_ClearPendingIRQ( TIM2_IRQn );
    NVIC_SetPriority( TIM2_IRQn, 2 );
    TIM2->DIER = TIM_DIER_UIE;
    NVIC_EnableIRQ( TIM2_IRQn );
    TIM2->CR1 = TIM_CR1_CEN;
}

void TIM2_IRQHandler( void )
{
    if ( TIM2->SR & TIM_SR_UIF )
    {
        TIM2->SR = ~TIM_SR_UIF;
        app_timer_event();
    }
}

#define DMA_FLAGS ( DMA_LIFCR_CFEIF0 | DMA_LIFCR_CDMEIF0 | DMA_LIFCR_CTEIF0 | DMA_LIFCR_CHTIF0 | DMA_LIFCR_CTCIF0 )

void platform_adc_prepare( void )
{
    RCC->AHB1ENR |= RCC_AHB1ENR_DMA2EN;
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    ( void ) RCC->APB2ENR;
    RCC->APB2RSTR |= RCC_APB2RSTR_ADCRST;
    RCC->APB2RSTR &= ~RCC_APB2RSTR_ADCRST;
    ADC->CCR       = ADC_CCR_TSVREFE;
    ADC1->CR1      = ADC_CR1_SCAN;
#ifdef STM32F411xE
    ADC1->SMPR1 = ADC_SMPR1_SMP18 | ADC_SMPR1_SMP17;
    ADC1->SQR3  = 18U | ( 17U << 5 );
#else
    ADC1->SMPR1 = ADC_SMPR1_SMP16 | ADC_SMPR1_SMP17;
    ADC1->SQR3  = 16U | ( 17U << 5 );
#endif
    ADC1->SQR1     = ADC_SQR1_L_0;
    ADC1->SQR2     = 0;
    ADC1->CR2      = ADC_CR2_ADON | ADC_CR2_DMA | ADC_CR2_DDS;
    uint32_t start = platform_tick;
    while ( ( uint32_t ) ( platform_tick - start ) < 2 )
        __WFI();
    DMA2_Stream0->CR  = DMA_SxCR_MINC | DMA_SxCR_PSIZE_0 | DMA_SxCR_MSIZE_0 | DMA_SxCR_TCIE | DMA_SxCR_TEIE | DMA_SxCR_DMEIE;
    DMA2_Stream0->FCR = 0;
    DMA2_Stream0->PAR = ( uint32_t ) &ADC1->DR;
    DMA2->LIFCR       = DMA_FLAGS;
    NVIC_ClearPendingIRQ( DMA2_Stream0_IRQn );
    NVIC_SetPriority( DMA2_Stream0_IRQn, 1 );
    NVIC_EnableIRQ( DMA2_Stream0_IRQn );
}

void platform_adc_start( volatile uint16_t* samples )
{
    if ( DMA2_Stream0->CR & DMA_SxCR_EN ) fail( 1 );
    if ( !( ADC1->CR2 & ADC_CR2_ADON ) ) fail( 2 );
    DMA2->LIFCR         = DMA_FLAGS;
    DMA2_Stream0->M0AR  = ( uint32_t ) samples;
    DMA2_Stream0->NDTR  = 2;
    ADC1->CR2          &= ~ADC_CR2_DMA;
    ADC1->SR            = 0;
    ADC1->CR2          |= ADC_CR2_DMA;
    DMA2_Stream0->CR   |= DMA_SxCR_EN;
    ADC1->CR2          |= ADC_CR2_SWSTART;
}

void platform_adc_stop( void )
{
    DMA2_Stream0->CR &= ~DMA_SxCR_EN;
    uint32_t start    = platform_tick;
    while ( DMA2_Stream0->CR & DMA_SxCR_EN )
    {
        if ( ( uint32_t ) ( platform_tick - start ) >= 20 ) fail( 3 );
    }
    if ( ADC1->SR & ADC_SR_OVR ) fail( 4 );
}

void DMA2_Stream0_IRQHandler( void )
{
    uint32_t flags = DMA2->LISR;
    DMA2->LIFCR    = DMA_FLAGS;
    if ( flags & ( DMA_LISR_TEIF0 | DMA_LISR_DMEIF0 | DMA_LISR_FEIF0 ) ) fail( 5 );
    if ( flags & DMA_LISR_TCIF0 ) app_adc_complete();
}

AdcReading platform_adc_convert( uint16_t temperature, uint16_t reference )
{
    return adc_convert_factory( temperature, reference, *( const uint16_t* ) 0x1FFF7A2A, *( const uint16_t* ) 0x1FFF7A2C,
        *( const uint16_t* ) 0x1FFF7A2E );
}

static void rtc_unlock( void )
{
    RTC->WPR = 0xCA;
    RTC->WPR = 0x53;
}

void platform_rtc_prepare( void )
{
    RCC->APB1ENR |= RCC_APB1ENR_PWREN;
    ( void ) RCC->APB1ENR;
    PWR->CR |= PWR_CR_DBP;
    wait_set( &PWR->CR, PWR_CR_DBP, 10 );
    uint32_t source = RCC->BDCR & RCC_BDCR_RTCSEL;
    if ( source && source != RCC_BDCR_RTCSEL_1 ) fail( 11 );
    RCC->CSR |= RCC_CSR_LSION;
    wait_set( &RCC->CSR, RCC_CSR_LSIRDY, 12 );
    RCC->BDCR |= RCC_BDCR_RTCSEL_1 | RCC_BDCR_RTCEN;
    rtc_unlock();
    RTC->CR = 0;
    wait_set( &RTC->ISR, RTC_ISR_ALRAWF, 13 );
    RTC->ISR = RTC_ISR_INIT;
    wait_set( &RTC->ISR, RTC_ISR_INITF, 14 );
    RTC->PRER = ( 127U << 16 ) | 249;
    RTC->TR   = 0;
    RTC->DR   = 0x2101;
    RTC->ISR  = 0;
    wait_set( &RTC->ISR, RTC_ISR_RSF, 15 );
    RTC->WPR    = 0xFF;
    EXTI->FTSR &= ~EXTI_FTSR_TR17;
    EXTI->RTSR |= EXTI_RTSR_TR17;
    EXTI->PR    = EXTI_PR_PR17;
    EXTI->IMR  |= EXTI_IMR_MR17;
    NVIC_ClearPendingIRQ( RTC_Alarm_IRQn );
    NVIC_SetPriority( RTC_Alarm_IRQn, 2 );
    NVIC_EnableIRQ( RTC_Alarm_IRQn );
}

static uint32_t bcd( uint32_t x )
{
    return ( x / 10U ) * 16U + x % 10U;
}

static uint32_t unbcd( uint32_t x )
{
    return ( x >> 4 ) * 10U + ( x & 15U );
}

void platform_rtc_arm( void )
{
    rtc_unlock();
    RTC->CR &= ~( RTC_CR_ALRAE | RTC_CR_ALRAIE );
    wait_set( &RTC->ISR, RTC_ISR_ALRAWF, 13 );
    uint32_t tr = RTC->TR;
    ( void ) RTC->DR; /* Unlock shadow after reading time. */
    uint32_t seconds  = ( unbcd( ( tr >> 16 ) & 0x3F ) * 3600U + unbcd( ( tr >> 8 ) & 0x7F ) * 60U + unbcd( tr & 0x7F ) + 2U ) % 86400U;
    RTC->ALRMAR       = RTC_ALRMAR_MSK4 | ( bcd( seconds / 3600U ) << 16 ) | ( bcd( ( seconds / 60U ) % 60U ) << 8 ) | bcd( seconds % 60U );
    RTC->ALRMASSR     = 0;
    RTC->ISR          = ~( RTC_ISR_ALRAF | RTC_ISR_INIT );
    EXTI->PR          = EXTI_PR_PR17;
    RTC->CR          |= RTC_CR_ALRAE | RTC_CR_ALRAIE;
    RTC->WPR          = 0xFF;
}

void RTC_Alarm_IRQHandler( void )
{
    if ( RTC->ISR & RTC_ISR_ALRAF )
    {
        RTC->ISR = ~( RTC_ISR_ALRAF | RTC_ISR_INIT );
        EXTI->PR = EXTI_PR_PR17;
        app_rtc_event();
    }
}
