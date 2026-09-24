# NUCLEO-F030R8 через J-Link STLink

Проверка 2026-09-25, время run IDs в UTC 2026-09-24.
Плата NUCLEO-F030R8/STM32F030R8T6, встроенный отладчик перепрошит владельцем
в J-Link STLink. Подключение USB + штатное SWD; остальные стенды не переключались.
Прошивка отладчика в ходе проверки не менялась.

## Идентификация

ST CubeProgrammer не перечислил этот отладчик как ST-Link. SEGGER Commander
ShowEmuList показал отдельный J-Link STLink наряду с прежним J-Link CE BluePill.
Выбор выполнялся по явному serial, сохранённому только в local TOML и build logs.

- SEGGER Commander/GDB Server V8.32, firmware J-Link STLink V21 (Aug 12 2019).
- SWD 1000 kHz, VTref 3.300 V, Cortex-M0 r0p0, CPUID 0x410CC200.
- DBGMCU_IDCODE 0x20006440: DEV_ID 0x440; Flash size register 64 KiB.
- Сервер подтвердил четыре hardware breakpoint. Flash breakpoints отключены.
- Во время первичного read-only подключения ядро уже работало; команда go
  вернула CPU is not halted. Это не ошибка связи/Flash; последующий runner
  выполнял штатные reset/halt/test/reset/go/disconnect.

## Сборка и механизм

CubeF0 V1.11.6, xPack ARM GCC13.3.1, Debug -Og -g3,
GDB14.2.90/Python3.11.4, preset f030r8-debug-hwtest.
ELF SHA-256: `cdf421fdad7c6b2637e1c8ce0a257097b373db084c7bb702587b423a3e1323d6`.
Flash payload 11348 B, RAM 1888 B с резервами heap/stack.

Модуль b76d909: добавлен только mapping STM32F030R8T6 → STM32F030R8.
Общая schema/Target API не менялись. Cortex-M0 профиль использует один fault BP
(HardFault) и CPUID/ICSR/SCR, без отсутствующих CFSR/HFSR.

Первый boot загрузил образ и проверил Flash чтением. Затем выполнены все
17 сценариев с той же реализацией backend из .work; после закрепления её
коммита в подмодуле повторены HW_BOOT, offline preflight и host65.
Режим Flash — ELF load sections, полный padded image/CRC на F030 не проверялся.

## Результаты

- HW_BOOT/CLOCK/GPIO/BLINK — PASS; LD2 на PA5 мигает, подтверждено владельцем.
- ADC/DMA init/runtime — PASS, два измерительных цикла с hadc и DMA1 Channel1.
- TIM3 init/IRQ и повторные RTC Alarm A — PASS.
- ADC HAL_ERROR injection, подавление DMA callback/timeout — PASS ожидаемой реакции.
- ADC units/invalid/recovery/factory anchor vectors — PASS.
- Sleep/SysTick и Sleep/TIM3 при временно выключенном SysTick IRQ — PASS.
- Всего 17/17; все завершения reset_run. MCU оставлен с приложением работающим.
- Пример измерения: VDDA 3306 mV, температура 32718 mC, quality=3.
  Это правдоподобие и вычислительная проверка, не измерение точности температуры.
- Host модуля 65/65; offline профиль 9 contracts PASS; повтор после gitlink PASS.

## Границы и дальнейшая работа

Подтверждена эта плата с этим J-Link STLink и версиями ПО. Не проверены
OpenOCD/ST server на F030, полный образ/CRC, recovery при обрыве USB,
физические энергопотребление/тайминги или другие модели Cortex-M0.
HAL NULL-инъекции требуют отдельного анализа исходников F0.

Возврат встроенного отладчика к ST-Link — отдельное действие владельца с
утилитой SEGGER; оно здесь не выполнялось. После возврата заново определить
serial/backend и повторить выбранные тесты. Процедуру и firmware не автоматизировать.
Логи и результаты находятся в build/f030-jlink и build/f030r8-debug-hwtest/hwtest/runs;
персональные serial не переносятся в Git.
