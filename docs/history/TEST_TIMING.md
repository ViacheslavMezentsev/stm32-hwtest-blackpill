# Измерение длительности и первая оптимизация

Потребитель на базе f4b7d75, модуль da42cd7; xPack Arm GCC13.3.1-1.1.
Изменяется только организация offline CTest в CI. Firmware, сценарии, модуль,
reset/Flash/identity/manifest и recovery не изменены.

## Offline: одинаковые 15 проверок одного MCU

F401CC HIL, 14 prepare + traceability, три повтора для каждого j=1/2/4.
Новый `ci/benchmark_prepare.py` меняет порядок j между повторами, сохраняет
JUnit/логи и проверяет полный состав без skipped/error/failure. Перед запуском
проверяет, что команды являются prepare-only или trace, а не HW.

| Среда | j=1, медиана | j=2, медиана | j=4, медиана |
| --- | ---: | ---: | ---: |
| Windows, локальный ПК | 4,144 с | 2,194 с | 1,241 с |
| Docker/Linux, лимит2 CPU, bind mount Windows | 6,729 с | 3,122 с | 1,769 с |

j=2 уменьшил wall-time этого этапа примерно на47% и54% соответственно.
Это не ускорение всего CI на такую величину: сборка контейнера, configure/build,
сохранение артефактов и очереди GitHub сюда не входят. Docker bind mount и текущие
cache/нагрузка влияют на результат; эти числа не являются прогнозом Ubuntu runner.

По умолчанию CI использует **два** offline-процесса. Четыре в этих опытах быстрее,
но два выбраны как умеренная исходная настройка; параметр позволяет сравнивать
1/2/4 на других машинах. У каждого prepare остаются собственные snapshot, manifest
проверки, GDB preflight и отчёт. Объединения результатов/кэширования доказательств нет.

Windows и Linux с j=2: шесть firmware-сборок и31 CTest PASS. Проверены также
отказы benchmark на неполном составе и команде без prepare-only до её выполнения.

## Аппаратный исходный замер

BlackPill F401CC + внешний ST-Link/SWD/OpenOCD, последовательный CTest j=1:
**14/14 PASS за38,177 с**. Затем отдельный HW_GPIO PASS, CMSIS-приложение оставлено
работающим. Первый запуск мог включать смену прошивки; это не серия warm-start
замеров. Отладчик выбирался явно прежним локальным stand TOML.

| Сценарий | Wall-time CTest |
| --- | ---: |
| HW_BOOT | 4,722 с |
| HW_RTC | 5,381 с |
| HW_ADC_INVALID | 4,286 с |
| Остальные11 | 1,442–2,954 с каждый |

Эти значения включают lifecycle runner и действия сценария. Из них нельзя
выделить точное время сервера/GDB или считать всё накладными расходами: RTC и
повторные ADC-наблюдения намеренно ждут выполнения firmware.
Аппаратные сценарии **не распараллелены**, их reset/teardown сохранены.
Новый опыт внешнего host-timeout не выполнялся, поскольку механизм не менялся;
прежнее доказательство recovery — [приёмка](BLACKPILL_CMSIS_APPLICATION.md).

## Повторение и артефакты

```sh
cmake --preset HIL_F401CC
cmake --build --preset HIL_F401CC
python -B ci/benchmark_prepare.py --board F401CC --repeats 3
python -B ci/run_checks.py --prepare-jobs 1
python -B ci/run_checks.py --prepare-jobs 2
```

Benchmark пишет уникальный каталог build/test-timing/<UTC>/ с summary/JUnit/logs.
CI сохраняет timings.json рядом с summary в build/ci-reports/cmsis; каждой стадии
записывается wall-time и статус, включая неуспех. Это локальное время стадий,
не длительность всего GitHub job. CI-отчёты последующего запуска заменяют предыдущие:
для A/B сравнения сохраните каталог перед повтором.

Локальные доказательства этого опыта:
- Windows benchmark: build/test-timing/20261001T191635.957819Z/summary.json.
- Linux benchmark: build/consumer-layout/linux-source/build/test-timing/20261001T191712.656368Z/summary.json.
- HW: build/test-timing/hardware/summary.json, suite.xml и final-gpio.log.

Метки времени артефактов приведены в UTC; serial и личные пути не публикуются.

## Дальнейшие шаги

1. Сравнить длительности опубликованного CI на том же runner.
2. Если существенны накладные расходы HW, добавить раздельные lifecycle timings
   в stm32-gdbtest, обновив его ТЗ/документацию и отрицательные проверки.
3. Только после измерений рассматривать cache неизменяемых данных или повторное
   использование server. Это изменения семантики и изоляции, требующие отдельной
   приёмки, а не следствие нынешнего безопасного параллелизма prepare.
