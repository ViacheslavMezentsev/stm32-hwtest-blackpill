# Дополнительные CMSIS-сценарии BlackPill

Проверка 2026-10-02. Четыре сценария в [test_runtime.py](../hil/tests/board/test_runtime.py)
дополняют прежние 14. Прошивка src и подмодуль v0.1.0-rc.2/a0d6547 не изменены.

## Происхождение и адаптация

Источник приёмов — [каталог TECH](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/da42cd74c27a01c21df47cd660e2533e9bcfc6d4/docs/ru/TESTING_TECHNIQUES.md)
и [F401 CMSIS fixture](https://github.com/ViacheslavMezentsev/stm32-gdbtest/tree/da42cd74c27a01c21df47cd660e2533e9bcfc6d4/tests/firmware/profiles/f401cc/tests/board).
Эти материалы появились после rc.2; они служат образцом, а исполнение использует
только API закреплённого rc.2. Проверки адаптированы к нашим platform_* и app_state,
а не скопированы вместе с firmware fixture.

| Сценарий | Техники | Что подтверждает |
| --- | --- | --- |
| HW_CLOCK_GPIO_CONFIG | TECH-001 | HSI16, делители, SysTick reload, электрические настройки PC13 |
| HW_TIMER_IRQ_PUBLICATION | TECH-002/003 | Естественный IRQ44 с UIF, два точных приращения счётчика, возврат в thread mode |
| HW_ADC_DMA_PUBLICATION | TECH-003 | IRQ72, завершение двух DMA transfers без ошибок, связь отсчётов с публикацией |
| HW_ADC_CALLBACK_SUPPRESSED | TECH-004 | Возврат из void callback без уведомления вызывает application timeout, без публикации |

Макросы CMSIS вычисляются в platform.c; ожидаемые значения берутся из требований,
не из проверяемых макросов. Адрес ICSR сохраняется до смены frame. Чтение SysTick CTRL
сбрасывает COUNTFLAG; приложение пользуется счётчиком IRQ, поэтому это допустимо здесь.
`force_return` применяется к реальной функции void(void) без LTO: DMA уже завершён,
подавляется только уведомление. Это не доказательство отказа ADC/DMA.

## Результаты и ограничения

- Windows и чистый Linux Docker (без сети/USB): в каждой среде шесть Debug/Release/HIL сборок, 39 CTest PASS (18 prepare + traceability
  на каждый MCU и один native ADC).
- F401CC + ST-Link/SWD, OpenOCD 0.12.0: полный набор **18/18 PASS**, 42,41 с.
  После инъекции отдельно проверены обычный ADC и GPIO; teardown reset_run успешен.
- F411CE: аппаратно приняты прежние 14 сценариев. Новые четыре требуют отдельного
  запуска после согласованной замены платы; prepare не подтверждает аппаратный результат.

Локальные артефакты: build/cmsis-runtime/f401cc-hardware.xml, restore.xml и
build/HIL_F401CC/hwtest/runs. ELF SHA256:
`d1881b7f085bcee7e05bdbc567935385c06e9ed05be98f32488971f48a7a7425`;
образ SHA256: `944ff629dd6d569eff05d03e9b9e377cef00a2cc8c0afd48bdf5e7de5213834f`.
Они совпадают с прежней прошивкой. DEV_ID mismatch остаётся предупреждением по
политике профиля, не подтверждением другой модели MCU.

IRQ наблюдаются с остановками GDB: это не измерение jitter, скорости DMA или
частоты внешним прибором. Проверка регистров GPIO не доказывает физический уровень
на выводе. Число сценариев не является процентом покрытия кода. Prepare здесь
проверяет подготовку и traceability, но не исполняет выражения новых сценариев на MCU.
