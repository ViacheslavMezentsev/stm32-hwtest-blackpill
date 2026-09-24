# STM32F429I-DISCO / OpenOCD

Проверка 2026-09-25 (run IDs в UTC 2026-09-24). Владелец подтвердил подключение
старой DISCO и после тестов — мигание зелёного LD3/PG13.

## Стенд и образ

- STM32F429ZIT6, встроенный ST-Link/V2 firmware V2J43S0, SWD, OpenOCD 0.12.0.
  Выбран отдельный serial через disco-f429zi.local.toml; BlackPill не затронут.
- DBGMCU_IDCODE 0x10036419, DEV_ID 0x419 соответствует профилю; Flash 2048 KiB.
  Cortex-M4 r0p1, шесть hardware breakpoints, четыре watchpoints по серверу.
- OpenOCD сообщил VTref около 2.879 В; это показание отладчика, не измерение
  точности питания внешним прибором. Запрошенная SWD скорость 1000 kHz.
- CubeF4 V1.28.3, GCC13.3.1, Debug -Og -g3, GDB14.2.90/Python3.11.4.
- ELF SHA-256: `d7346f72b1f29ea6864258d13e906cbd87c0ff1b494053b61565d3383f2e9641`.
  Flash 12744 B, SRAM 1896 B с heap/stack reserve, CCM 0.
- Закреплённый stm32-gdbtest b76d909: модуль не изменялся для F429.

## Проверки

Первый HW_BOOT записал ELF и проверил загрузочные секции чтением, включая .data
по Flash LMA. Далее полный CTest: **25/25 PASS**, из них **22/22 HW** и три host
(traceability, offline 10 contracts, host suite модуля — 65 тестов).

- Boot, PLL/HCLK/APB, GPIOG/PG13, blink/HAL tick — PASS.
- ADC1 IN18/17, DMA2 Stream0 init и повторные преобразования — PASS.
- TIM2 PSC7999/ARR99, callbacks и RTC LSI127/249 с повторным Alarm A — PASS.
- GPIO аргументы/условный breakpoint; RCC HAL_ERROR и NULL guards — PASS.
- ADC HAL_ERROR, подавление completion callback и timeout — PASS ожидаемой реакции.
- ADC factory provenance, правдоподобие величин, invalid/recovery и опорные
  векторы 30/110°C — PASS.
- Sleep/WFI с SysTick и TIM2 при временном отключении SysTick IRQ — PASS.

Все 22 завершения — reset_run; приложение оставлено работающим.
Видимое мигание LD3 подтверждено владельцем.
Локальные доказательства: build/f429zi-debug-hwtest/hwtest/runs и
hwtest/f429zi-validation.xml внутри той же build-папки. Serial и личные пути
не включаются в Git.

## Границы

Это доказательство для данного экземпляра/образа/backend. Остановки GDB влияют
на IRQ и время; проверка событий не измеряет период, точность LSI/ADC или ток.
Проверены ELF load sections, а не gaps/full-image CRC. LCD/LTDC/DMA2D, SDRAM/FMC,
гироскоп, USB, Stop и аппаратный CRC не настроены и не проверены.
ST GDB Server/J-Link на F429 и recovery при физическом обрыве ещё не проверялись.
Firmware отладчика, option bytes и защита Flash не менялись.

Настройки и команды: [профиль](../profiles/f429zi/README.md).
