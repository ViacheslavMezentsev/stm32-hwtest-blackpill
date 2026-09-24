#include <K1921VG015.h>
#include <system_k1921vg015.h>
#include <charconv>
#include <cstdint>
#include <cstring>

// Deliberately diagnostic firmware, separate from the unmodified blink application.
extern "C" {
struct Result { uint32_t count, wrong, ec_errors, ptr_errors, first, last, first_wrong, infinity; };
volatile Result results[4];
volatile uint32_t completed;
extern const float flash_divisor;
const float flash_divisor __attribute__((section(".rodata.errata"))) = 100000.0f;
float ram_divisor = 100000.0f;

__attribute__((noinline)) float divide_adjacent(const float *p) {
    float result;
    asm volatile("li t0, 0x3f800000\n\tfmv.w.x fa5, t0\n\t"
                 "flw fa4, 0(%1)\n\tfdiv.s %0, fa5, fa4"
                 : "=f"(result) : "r"(p) : "t0", "fa4", "fa5", "memory");
    return result;
}
__attribute__((noinline)) float divide_nop(const float *p) {
    float result;
    asm volatile("li t0, 0x3f800000\n\tfmv.w.x fa5, t0\n\t"
                 "flw fa4, 0(%1)\n\tnop\n\tfdiv.s %0, fa5, fa4"
                 : "=f"(result) : "r"(p) : "t0", "fa4", "fa5", "memory");
    return result;
}
__attribute__((noinline)) void experiment_done() { asm volatile("nop" ::: "memory"); }
}

static void record(unsigned slot, float value, bool ec = false, bool ptr = false) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    volatile Result &r = results[slot];
    if (r.count == 0) r.first = bits;
    r.last = bits;
    if (bits != 0x3727c5acu && r.wrong == 0) r.first_wrong = bits;
    r.infinity += bits == 0x7f800000u;
    r.wrong += bits != 0x3727c5acu;
    r.ec_errors += ec;
    r.ptr_errors += ptr;
    ++r.count;
}
int main() {
    SystemInit();
    SystemCoreClockUpdate();
    // No interrupts or breakpoints inside the measured instruction sequences.
    for (unsigned i = 0; i < 1000; ++i) {
        char text[] = "1e-5";
        float parsed = 0;
        auto fc = std::from_chars(text, text + 4, parsed, std::chars_format::general);
        record(0, parsed, fc.ec != std::errc(), fc.ptr != text + 4);
        record(1, divide_adjacent(&flash_divisor));
        record(2, divide_nop(&flash_divisor));
        record(3, divide_adjacent(&ram_divisor));
    }
    completed = 0x12345678;
    experiment_done();
    for (;;) asm volatile("nop");
}
