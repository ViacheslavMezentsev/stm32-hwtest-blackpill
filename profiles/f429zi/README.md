# STM32F429I-DISCO / f429zi

Минимальный стенд для STM32F429ZIT6 старой STM32F429I-DISCO (MB1075).
Сборка/offline и 22/22 аппаратных сценария через встроенный ST-Link/V2/OpenOCD
прошли; мигание LD3 подтверждено владельцем. [Протокол](../../docs/F429_OPENOCD_VALIDATION.md).
IOC использует шаблон STM32F429I-DISC1: это метаданные CubeMX, а не подтверждение
ревизии экземпляра. У старой DISCO встроенный ST-Link/V2, у DISC1 — V2-B.
Зелёный пользовательский LD3 подключён к PG13, активный уровень высокий.
Источник: [UM1670](https://www.st.com/resource/en/user_manual/um1670-discovery-kit-with-stm32f429zi-mcu-stmicroelectronics.pdf).

ST GDB Server также проверен: все 22 сценария получили PASS с переподключением USB
после 18-го; запись/verify-only/recovery выполнены.
Последующий полный ST прогон дал 22/22 PASS; в сериях OpenOCD тоже наблюдался
USB-сбой. [Устойчивость повторных запусков](../../docs/F429_SERVER_STABILITY.md). [Подробности и сбой](../../docs/F429_STLINK_VALIDATION.md).

## Конфигурация

- CubeF4 V1.28.3, GCC 13.3.1, Debug -Og -g3; общий User без изменений.
- HSI 16 МГц → PLL M=8/N=64/P=2 → SYSCLK 64 МГц, AHB /8 → HCLK 8 МГц.
  APB1/APB2 /1, TIM2 8 МГц, ADC PCLK2/2 = 4 МГц.
- TIM2 PSC=7999, ARR=99: номинально 100 мс. RTC LSI, делители 127/249:
  номинально 1 с при LSI 32 кГц, без гарантии точности внутреннего генератора.
- ADC1: температура IN18, VREFINT IN17, по 480 циклов; DMA2 Stream0/channel0,
  normal/halfword; IRQ ADC DMA, TIM2 и RTC Alarm включены.
- Platform читает заводские VREFINT/TS_CAL1/TS_CAL2; точки 30/110°C, VDDA 3.3 В,
  качество FACTORY. HAL TEMPSENSOR содержит служебный флаг; SQR проверяется отдельно.
- Flash 2 MiB, SRAM 192 KiB, отдельно CCM 64 KiB. DMA-буфер расположен в обычной
  SRAM; CCM для DMA недоступна. SDRAM, LCD, гироскоп, USB и аппаратный CRC не включены.
  PLLQ не обеспечивает 48 МГц; для USB потребуется отдельная настройка clock tree.
- target: Cortex-M4, DEV_ID 0x419, Flash size register 0x1FFF7A22.
  [RM0090](https://www.st.com/resource/zh/reference_manual/DM00031020.pdf),
  [datasheet](https://www.st.com/resource/en/datasheet/stm32f429ie.pdf).

## Сборка и проверка без платы

```powershell
cmake --preset f429zi-debug-hwtest
cmake --build --preset f429zi-debug-hwtest
ctest --test-dir build/f429zi-debug-hwtest -R '^host\.(traceability|profile_offline)$' --output-on-failure
```

Подготовлены 22 аппаратных сценария и 10 HAL-контрактов: boot, GPIO/RCC,
ADC/DMA, TIM2/RTC, арифметика и инъекции ошибок, Sleep/SysTick/TIM2.
Offline PASS означает согласованность manifest/ELF, требований и выбранных
контрактов, а не выполнение этих сценариев на MCU. RCC NULL guards повторно
сверены с CubeF4 V1.28.3 до переноса source review; hash оставлен прежним.
Сборка занимает Flash 12744 B, SRAM 1896 B с резервом heap/stack; CCM не используется.
Предупреждения newlib NoSys о read/write/close/lseek ожидаемы: файлового ввода-вывода нет.

## Аппаратный стенд

Подтверждённый владельцем стенд: DISCO + встроенный ST-Link/V2, SWD, backend OpenOCD.
USB подключается к CN1 ST-LINK; обе перемычки CN4 и JP3 установлены в штатное
положение ON. Внешний отладчик на CN2 не подключать одновременно.
Скопировать Tests/stands/disco-f429zi.example.toml в disco-f429zi.local.toml,
указать serial именно встроенного отладчика и путь OpenOCD. Это важно при
одновременно подключённом ST-Link BlackPill. Serial не включать в Git.
Сначала identity/Flash, boot/GPIO и подтверждение LD3, затем остальные сценарии.

При регенерации сохранить USER CODE-вызовы init/setup/loop и app.h; проверить
TIM2 7999/99 и RTC 127/249. Эти параметры согласованы с IOC. Ядро stm32-gdbtest
для добавления данного профиля не изменялось.
