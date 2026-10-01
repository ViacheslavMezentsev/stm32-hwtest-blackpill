#include "app.h"
extern "C" void platform_init( void );

int main( void )
{
    platform_init();
    init();
    setup();
    for ( ;; )
        loop();
}
