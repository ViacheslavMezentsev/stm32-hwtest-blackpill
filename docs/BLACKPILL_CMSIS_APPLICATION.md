# Приёмка CMSIS-приложения BlackPill

Рабочий пакет `codex/blackpill-cmsis-application`, база — план `18e4d14`.
Это перенос пользовательского приложения, а не замена его минимальным fixture:
сохранены асинхронные ADC/DMA, обработка событий TIM2, перепланирование RTC
на две секунды и Sleep/WFI. Ядро stm32-gdbtest не изменяется.

## Проверено локально

- F411CE и F401CC: сборки Debug/Release; по 15 offline CTest (14 prepare и traceability).
- F411CE + ST-Link/SWD/OpenOCD: 14 сценариев PASS, ещё 12 положительных
  повторов ADC/TIM2/RTC после четырёх инъекций ошибок — PASS.
- Внешний timeout после достижения loop: ожидаемый ERROR, host recovery reset_run;
  затем повторные ADC и RTC — PASS. Это отдельный негативный опыт, не ещё один PASS case.
- Прежняя HAL-прошивка восстановлена; HW_BOOT/HW_BLINK — PASS.

Локальные первичные результаты: `build/cmsis-application/20261001T171919Z/summary.json`;
проверка внешнего timeout — `build/cmsis-application/timeout/`.
Первый запуск выявил удаление неиспользуемого SystemCoreClock линкером;
SysTick теперь использует эту переменную. Старый отчёт сохранён в build.

## Границы приёмки

F401CC также прошёл 14 аппаратных сценариев и 12 повторов после инъекций.
Локальная серия `20261001T173253Z` остановилась при сборе отчёта последнего
сценария: параллельный prepare добавил JSON, нарушив предположение harness о
единственном новом файле. Сам HW_SLEEP_TIM2 имеет PASS; отдельно повторён с
PASS. Исходный ошибочный summary сохранён. Дополнительные результаты:
`build/cmsis-application/f401-recovery/summary.json` — Sleep, ожидаемый внешний
timeout ERROR с успешным host recovery, ADC/RTC PASS и HAL boot/blink restore PASS.

Debug/Release
сборка не заменяет проверку на плате; аппаратно проверены Debug-конфигурации обоих MCU.
Инициализация предполагает системный reset и исходный HSI16. Startup поддерживает
текущие статические данные; C++ динамическая инициализация глобальных объектов
не добавлена. Калибровочные векторы проверяют вычисления, а не точность датчика.

CI-runner собирает Debug/Release обоих MCU и проверяет 30 host CTest.
Новый runner прошёл на Windows и в Docker/Linux: по 30 host CTest,
четыре успешные сборки в каждой среде. Linux использовал отдельную копию
в build/cmsis-application/linux-source без доступа к USB и сети.

Этап принят: пакет314982a прошёл CI, затем76d50b0 завершил перестройку дерева,
README/VS Code и архивирование HAL. Текущие presets: Debug/Release/HIL для двух
MCU, шесть сборок и31 CTest; BLACKPILL_CMSIS больше не используется.
Числа30/четыре сборки выше относятся к первоначальной приёмке этого протокола.
[Текущий статус](STATUS.md), [дерево](PROJECT_LAYOUT.md),
[требования](../hil/tests/requirements.md).
