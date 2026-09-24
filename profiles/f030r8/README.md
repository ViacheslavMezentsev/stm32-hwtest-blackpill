# NUCLEO-F030R8 — подготовка профиля

STM32F030R8T6, Cortex-M0, Flash 64 KiB, RAM 8 KiB. CubeF0 V1.11.6.
Профиль включён в сборку, но ещё не в аппаратные тесты stm32-gdbtest.
Плата не подключена; успешная сборка не подтверждает работу периферии.

## Сборка

```powershell
cmake --preset f030r8-debug
cmake --build --preset f030r8-debug
```

GCC 13.3.1, Debug -Og -g3, отдельный build/f030r8-debug.
ENABLE_HW_TESTING=ON пока отклоняется явно: target/HAL contracts и диагностика
Cortex-M0 требуют отдельной подготовки. Не использовать target от F103/F411.

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

## Следующие шаги

1. Добавить target.toml, карту памяти/identity F030 и отдельные contracts HAL.
2. Параметризовать hadc/htim3 и регистры в Python-сценариях; не копировать
   ожидания TIM2/ADC рангов F1/F4. Проверить диагностику Cortex-M0 и BP budget.
3. Подготовить локальный stand для встроенного ST-Link/V2-1 с явным serial,
   чтобы не выбрать подключённый ST-Link другой платы.
4. После согласования подключения: identity/Flash/boot/GPIO, затем ADC/DMA,
   TIM3/RTC и Sleep. Фактическую точность температуры проверять отдельно.

До этого этапа существующие стенды F411/ST-Link и F103/J-Link можно оставить.
Nucleo не требует отдельной копии User или изменений ядра тестирования ради
названия платы. Platform принадлежит этому приложению, а не stm32-gdbtest.
