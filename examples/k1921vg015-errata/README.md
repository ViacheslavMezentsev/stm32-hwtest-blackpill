# Диагностика errata К1921ВГ015: from_chars и Flash

Отдельное диагностическое приложение для воспроизведения ошибки из пункта 5
[errata от 15.04.2026](https://niiet.ru/wp-content/uploads/2026/04/errata_K1921VG015_Rev4_lqfp100.pdf).
Оно намеренно содержит измерительный код; обычный blink и production STM32-тесты
не меняются. Результаты и границы выводов — [протокол](../../docs/K1921VG015_ERRATA.md).

Требуется прежний [PoC](../k1921vg015-poc/README.md), его собранный blink для
восстановления, внешний SDK NIIET только для чтения, xPack GCC 13/14, CloudBEAR
14.1.0.7 и явный локальный TOML стенда К1921ВГ015/J-Link EDU v11/JTAG.
GDB-Python используется из xPack 13; компилятор и отладчик выбираются независимо.

Из этого каталога, после задания `NIIET_DEVICE_DIR`:

```powershell
foreach ($variant in @('gcc13','gcc14','cloudbear14','gcc14-ram','cloudbear14-ram')) {
    cmake --preset $variant
    if ($LASTEXITCODE -ne 0) { throw 'configure failed' }
    cmake --build --preset $variant
    if ($LASTEXITCODE -ne 0) { throw 'build failed' }
}
```

Из корня репозитория, только при подключённом согласованном стенде:

```powershell
python -B examples/k1921vg015-errata/series.py --stand Tests/stands/k1921-jlink.local.toml
```

Для offline-дизассемблирования и проверки ключа обхода:

```powershell
python -B examples/k1921vg015-errata/inspect.py build/k1921-errata-cloudbear14
```

`series.py` восстанавливает blink в `finally`; проверить успешность восстановления
в выводе. Прямой запуск `run.py flash --build ... --stand ...` оставляет диагностическое
приложение на плате и требует отдельного восстановления. Внешний предел клиента —
300 секунд, включая загрузку и readback; отчёт `OBSERVED` означает завершённое
наблюдение, а не отсутствие аппаратных ошибок. `wrong`, `infinity`, `ec_errors`
и `ptr_errors` надо читать отдельно. Неполный запуск — `ERROR`.

В каждом из четырёх сценариев 1000 вызовов. GDB ставит единственный аппаратный
breakpoint в `experiment_done` после всех вычислений, проверяет таблицу и читает
счётчики. Образ проверяется по ELF load regions. Локальные отчёты/снимки/логи
сохраняются в `build/k1921-errata-*/runs`, в Git они не включаются.

У CloudBEAR важен полный `-march=rv32imfc_zicsr_zifencei_zba_zbb_zbc_zbs`:
с сокращённой строкой, подходящей xPack, этот пакет выбирал несовместимую RV64
библиотеку. `-mfix-cloudbear-0001` включён для компиляции приложения/SDK,
но не пересобирает архивы и не исправляет явно написанный inline assembler.

RAM-варианты перемещают `.rodata`/`.rodata.*` в `.data` локальной копией linker
script, созданной в build. Startup переносит их из Flash в RAM. `.srodata` остаётся
на прежнем месте. Это диагностический контроль с расходом RAM, не готовое
универсальное исправление всех инструкций из errata. В этих вариантах также
переезжает `flash_divisor`, поэтому его имя не означает физическую Flash:
проверять адрес в отчёте. Post-link проверка отклоняет неверное размещение таблицы.
