#include <stdint.h>
extern uint32_t _estack, _sidata, _sdata, _edata, _sbss, _ebss;
extern int main( void );
extern void SysTick_Handler( void ), TIM2_IRQHandler( void ), RTC_Alarm_IRQHandler( void ), DMA2_Stream0_IRQHandler( void );

void Default_Handler( void )
{
    for ( ;; )
    {
    }
}

void HardFault_Handler( void )
{
    for ( ;; )
    {
    }
}

void MemManage_Handler( void )
{
    for ( ;; )
    {
    }
}

void BusFault_Handler( void )
{
    for ( ;; )
    {
    }
}

void UsageFault_Handler( void )
{
    for ( ;; )
    {
    }
}

void Reset_Handler( void )
{
    uint32_t* src = &_sidata;
    for ( uint32_t* p = &_sdata; p < &_edata; )
        *p++ = *src++;
    for ( uint32_t* p = &_sbss; p < &_ebss; )
        *p++ = 0;
    main();
    for ( ;; )
    {
    }
}

__attribute__( ( section( ".isr_vector" ), used ) ) void ( *const vectors[] )( void ) = { ( void ( * )( void ) ) &_estack, Reset_Handler,
    Default_Handler, HardFault_Handler, MemManage_Handler, BusFault_Handler, UsageFault_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, SysTick_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, TIM2_IRQHandler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    RTC_Alarm_IRQHandler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    DMA2_Stream0_IRQHandler };
