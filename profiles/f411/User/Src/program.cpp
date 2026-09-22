#include "main.h"


/**
 * \brief   Выполняет инициализацию.
 *
 */
void init( void )
{
}


/**
 * \brief   Выполняет дополнительные настройки.
 *
 */
void setup( void )
{
}


/**
 * \brief   Выполняется периодически в теле основного цикла.
 *
 */
void loop( void )
{
    // Переключаем выход порта (мигаем светодиодом).
    HAL_GPIO_TogglePin( LED_USER_GPIO_Port, LED_USER_Pin );

    HAL_Delay( 500 );
}
