# NUCLEO-F030R8 — подготовка профиля

STM32F030R8T6, Cortex-M0, Flash 64 KiB, RAM 8 KiB. CubeF0 V1.11.6.
Профиль сборки и 17 аппаратных сценариев подготовлены для stm32-gdbtest.
Сценарии ещё не выполнены на Nucleo.
Плата не подключена; успешная сборка не подтверждает работу периферии.

## Сборка

```powershell
cmake --preset f030r8-debug
cmake --build --preset f030r8-debug
```

GCC 13.3.1, Debug -Og -g3, отдельный build/f030r8-debug.
Для подготовки тестов без подключения платы:

```powershell
cmake --preset f030r8-debug-hwtest
cmake --build --preset f030r8-debug-hwtest
ctest --test-dir build/f030r8-debug-hwtest -R '^host.(traceability|profile_offline)$' --output-on-failure
```

host.profile_offline проверяет manifest/ELF, сбор сценариев, требования и все
запрошенные HAL-контракты отдельным GDB без запуска сервера. Её можно вызвать
напрямую: `python -B tools/check_profile_offline.py --session build/f030r8-debug-hwtest/hwtest/session.json`.
Функции/макросы проверяются офлайн, семантика MMIO/IRQ требует платы.
Запуск CTest без фильтра включает аппаратные сценарии — пока не выполнять.

Конфигурация по умолчанию указывает на отсутствующий nucleo-f030r8.local.toml,
а не на действующий BlackPill/BluePill. Шаблон: Tests/stands/nucleo-f030r8.example.toml.
Не копировать serial другого ST-Link; встроенный отладчик выбирается явно.

## Проверенная генерация CubeMX

- PA5 / LED_USER: push-pull, no pull, low speed, начальный Low; LD2 активен High.
- SYSCLK/HCLK/PCLK: HSI 8 MHz, без PLL и зависимости от ST-Link MCO.
- TIM3: PSC=7999, ARR=99, update каждые 100 ms; IRQ с HAL handler.
- ADC: HSI14, 12 bit, scan forward, температура IN16 затем VREFINT IN17,
  sampling 239.5 cycles; DMA1 Channel1, Normal, halfword, memory increment.
- RTC: LSI, делители 127/311. При номинальных 40 kHz период 0.9984 s;
  разброс LSI не позволяет считать это точными часами. Alarm A и IRQ включены.
- CRC включён; DMA и RTC инициализируются в main.
- В USER CODE main добавлены app.h, init/setup/loop. Сохранять при регенерации.

Источники: [UM1724](https://www.st.com/resource/en/user_manual/dm00105823-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf),
[DS9773](https://www.st.com/resource/en/datasheet/stm32f030r8.pdf),
сгенерированные Core и установленный CubeF0 V1.11.6.

## Адаптер приложения

Общий User больше не включает HAL. Platform выбирает hadc/htim3, запускает
одно измерение DMA, передаёт завершение и IRQ в обычные callbacks приложения,
управляет LED/Sleep и временем. Это production-код приложения, не тестовые hooks.
Соглашение буфера: два выровненных uint16_t, температура перед VREFINT.
При другом порядке каналов адаптер обязан нормализовать данные.

ADC калибруется перед первым запуском. VDDA вычисляется по VREFINT_CAL,
температура — по TS_CAL1 при 30 C / 3.3 V и типовому отрицательному наклону
4.3 mV/C. TS_CAL2 для F030 не используется, даже если общий LL header F0
объявляет такой адрес. ADC_FACTORY_SINGLE_POINT=3 означает одну заводскую
точку и типовой наклон; это не точность двухточечной калибровки F411.
Чистая арифметика проверяется в Tests/native.

## Цель и диагностика Cortex-M0

По [RM0360, §26.4.1, §26.7](https://www.st.com/resource/en/reference_manual/dm00091010-stm32f030x4x6x8xc-and-stm32f070x6xb-advanced-armbased-32bit-mcus-stmicroelectronics.pdf):
DBGMCU_IDCODE=0x40015800, DEV_ID=0x440, четыре hardware breakpoint.
CMSIS stm32f030x8.h задаёт FLASHSIZE_BASE=0x1FFFF7CC (16-bit KiB).
В target.toml задан HardFault_Handler и регистры pc/lr/sp/xPSR, CPUID/ICSR/SCR.
Не читать CFSR/HFSR и не ставить BP на отсутствующие MemManage/BusFault/UsageFault.
Один BP занят HardFault, для последовательного reach нужен ещё один.
DEV_ID mismatch сохраняет общую политику warning; Flash ограничен 64 KiB.
Наличие четырёх BP на конкретном стенде ещё предстоит подтвердить сервером.

## Проверки и границы

- Собран firmware с post-link manifest; offline GDB: 17 сценариев / 9 контрактов PASS.
- Traceability PASS; намеренно отсутствующий macro и неверный ELF hash manifest
  дают ERROR без подключения. Проверка identity/размера на искусственных данных
  проверяет адреса и границы профиля, а не установленный MCU.
- Общие сценарии получают adc_handle/timer_handle/timer_enabled из EXPECTED.
  F103/F401/F411 сохраняют прежние ID HW_TIM2_IRQ, F030 использует HW_TIM3_IRQ.
- ADC/DMA runtime, TIM IRQ и Sleep/timer после параметризации повторены:
  F411/ST-Link/OpenOCD 3/3, F103/J-Link 3/3. F030 HW пока PENDING.
- Не перенесены NULL-инъекции RCC без отдельного source review HAL F0.
  Нет утверждения о полном покрытии или точности физических измерений.

## Подключение для первого запуска

Теперь можно подключить NUCLEO-F030R8 через USB к её встроенному ST-Link/V2-1,
со штатными SWD-перемычками CN2. Дополнительный внешний отладчик не нужен.
Существующие F411/ST-Link и F103/J-Link можно оставить подключёнными.
После подтверждения владельца определить serial Nucleo и записать локальный stand.
Сначала identity/Flash/boot/GPIO, затем оставшиеся ADC/DMA/TIM3/RTC/Sleep.
Не запускать GDB Server до подтверждения подключения и выбора serial.

Platform принадлежит приложению. Для этих тестов ядро stm32-gdbtest менять
не потребовалось; переносимость подтверждена пока только offline-проверкой.
