# MMIO/SVD in BlackPill

[Русский](MMIO_SVD.md)

The module is pinned to a7b09516abac467839ee9efc8ee286835c6001e0, the final 0.5.0 candidate
with API 3. No core changes are needed. Ordinary def scenarios remain synchronous.
All 22 scenario IDs and firmware sources are preserved.

Both profiles select the [project SVD](../hil/common/stm32f4-test.svd) through
[mmio].svd in session.toml. It is a minimal description of 40 registers and factory
values used by these scenarios, not a full vendor SVD. Addresses of 37 entries are
compared with CMSIS in the ELF using GDB without target remote. Three calibration
addresses are checked separately against board.toml and DS9716/DS10314 constants.
Access/effects follow RM0368/RM0383 and PM0214. Address checks do not validate the
effect model itself.

## Access and cleanup

| Object | Scenario rule |
| --- | --- |
| RCC, GPIO, TIM, RTC, ADC, DMA, SCB | t.mmio.read; evaluate CMSIS masks without peripheral reads |
| NVIC ISER/ICER | W1S/W1C: ready mask, allow_effects=True, no automatic readback |
| SCB ICSR | PENDSTCLR mask only, no whole-register read-modify-write |
| SysTick CTRL | allow_effects=True read clears COUNTFLAG; save control bits only |
| ADC CR2 | Explicit effect consent; restore the changed ADON bit on failure |
| DMA Stream0 | Change NDTR/M0AR with EN=0; clear and check EN before restoration |
| Factory values | Read-only 16-bit access; SRAM, arguments and app state retain the ordinary API |

ICER is deliberately write-only in the project SVD: hardware supports reads, but
scenarios read state through ISER. ADC DR has readAction=clear, DMA LIFCR is WO/W1C,
and TIM SR is W0C. Access without consent for declared effects is rejected before
transport. This does not guarantee a single physical bus transaction beyond the GDB server.

try/finally starts before the first mutation. The host model checks partial installation,
lost acknowledgements, observation exceptions and DMA disable failure. If EN remains
set after eight explicit reads, NDTR/M0AR restoration is refused and the error retained.
Sleep cleanup attempts both IRQ banks even if the first write fails. This restores
changed settings, not elapsed time, COUNTFLAG, pending events, samples or the complete
peripheral state. All 22 scenarios pass on the F411CE stand; F401CC hardware acceptance is still pending.

## Offline route

    cmake --preset f411ce-hil -DSTM32_GDBTEST_STAND=
    cmake --build --preset f411ce-hil
    ctest --preset f411ce-hil-host --output-on-failure

Replace f411ce with f401cc for the second profile. Each has 22 prepare tests plus
host.traceability, host.mmio (12 checks) and host.svd_elf: 25 CTest entries.
CI also builds Debug/Release, runs native ADC and checks scenario style.
HIL retains unused debug types for CMSIS verification; no test hooks are introduced.
The records limit is 256 to accommodate MMIO intent/result and WFI retries.

Windows/Linux checks cover builds, prepare, access/effects, cleanup, inspect from another
cwd and SVD retention through pack/open_package. Offline PASS is not HW PASS;
pre-migration hardware results do not validate the new MMIO transport.
