#include <K1921VG015.h>
#include <system_k1921vg015.h>
extern "C" {
#include <mtimer.h>
}

// Ordinary application operation, also useful as a debugger observation point.
extern "C" void app_step(void)
{
    sleep(500);
    GPIOC->DATAOUTTGL = 1u;
}

int main(void)
{
    SystemInit();
    SystemCoreClockUpdate();
    InterruptEnable();
    RCU->CGCFGAHB_bit.GPIOCEN = 1;
    RCU->RSTDISAHB_bit.GPIOCEN = 1;
    GPIOC->OUTENSET = 1u;
    GPIOC->DATAOUTSET = 1u;
    while (1) {
        app_step();
    }
}
