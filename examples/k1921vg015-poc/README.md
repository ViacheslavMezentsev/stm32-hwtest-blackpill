# К1921ВГ015: bare-metal proof-of-concept

Blink PC0 на К1921ВГ015 (ВМ-310S6, RV32) и проверки через J-Link/JTAG/GDB-Python.
Пример исследует переносимость `stm32-gdbtest`: использует неизменённые Target API,
проверку наличия GDB API и межпроектную блокировку. Производственный runner,
schema target, STM32 identity/Flash guard и CMake attach здесь не используются.
Это эксперимент, а не объявленная поддержка RISC-V в модуле.

## Исходники и зависимости

Windows, CMake >=3.25/Ninja, Python >=3.11; xPack RISC-V GCC 13.3.0-2,
`riscv-none-elf-gdb-py3.exe` (обычный gdb.exe этой поставки без Python), J-Link 8.32.
J-Link должен знать устройство K1921VG015 в окружении запуска. Stand выбирает
явный USB serial, полный JTAG, 1000 kHz. По журналу на стенде два JTAG TAP,
Total IRLen=8; настройка цепочки остаётся за сервером устройства.

Справочный проект: `demo-niiet-cmake/k1921vg015/01-default`. Путь к его
`platform/Device/K1921VG015` задаётся `NIIET_DEVICE_DIR`. CMake только читает
vendor startup, system/plic/mtimer, заголовки и linker scripts; они не скопированы
в этот репозиторий и не перелицензированы. Пример требует именно проверенного
варианта SDK; локальный manifest фиксирует хеши его файлов.

Свой `src/main.cpp` повторяет назначение справочного blink: SystemInit,
обновление SystemCoreClock, GPIOC/PC0, задержка 500 мс, переключение LED.
Функция app_step — обычная операция приложения, без тестовых флагов или hooks.
Операция DATAOUTTGL — прямая запись маски, без лишнего read-modify-write;
CKO_PLL0 не включён, тактовый выход PC7 для blink не нужен. RTOS и semihosting нет.

## Сборка

Из каталога этого примера, подставив свой путь к SDK:

```powershell
$env:NIIET_DEVICE_DIR = 'D:/path/to/01-default/platform/Device/K1921VG015'
cmake --preset debug
cmake --build --preset debug
python -B run.py offline
python -B -m unittest test_regions -v
```

Toolchain переопределяется cache-параметром RISCV_TOOLCHAIN_ROOT. Сборка и все отчёты
находятся в `../../build/k1921vg015-poc`, ничего не пишется в SDK или подмодули.
ISA `rv32imfc_zba_zbb_zbc_zbs_zicsr`, ABI ilp32f, `-Og -g3`.

## Аппаратный запуск

Скопировать stand.example.toml в корневой `Tests/stands/k1921-jlink.local.toml`,
указать свой USB serial. Перед запуском подтвердить К1921ВГ015/J-Link/JTAG,
закрыть использующую этот отладчик сессию IDE. Команды из **корня репозитория**:

```powershell
python -B examples/k1921vg015-poc/run.py flash --stand Tests/stands/k1921-jlink.local.toml
python -B examples/k1921vg015-poc/run.py verify --stand Tests/stands/k1921-jlink.local.toml
```

flash записывает ELF при отличии загружаемых секций. verify не записывает Flash.
Оба режима делают reset, используют hardware BP и завершаются reset/go/disconnect.
Пример заменяет приложение на плате и оставляет **собственный blink** работающим;
автоматического восстановления прежней пользовательской прошивки нет.
previous-image-range.bin сохраняет лишь затронутый диапазон, не полный backup.

Отказные опыты, на том же согласованном стенде:

```powershell
python -B examples/k1921vg015-poc/run.py negative --stand Tests/stands/k1921-jlink.local.toml
# Ожидаемый FAIL, exit 1: намеренно неверное ожидание PC0.
python -B examples/k1921vg015-poc/run.py stall --stand Tests/stands/k1921-jlink.local.toml
# Ожидаемый ERROR, exit 2: внешний timeout 12 s и отдельный recovery-клиент.
python -B examples/k1921vg015-poc/run.py verify --stand Tests/stands/k1921-jlink.local.toml
# После отказных опытов должен снова пройти положительный сценарий.
```

В runs сохраняются ELF/BIN/manifest, GDB/server logs, session и result.json;
stall-reached.json подтверждает, что timeout возник уже после достижения приложения.
PoC не генерирует JUnit/CTest и пока не использует collection/@case.
Ошибка запуска сервера может завершиться host-исключением без agent result.json.
Логи содержат локальные пути и serial; не публиковать их без проверки.

## Границы и результат

Проверены boot, макросы, clock/reset GPIOC, выход PC0, три переключения latch,
условный breakpoint в sleep(ms==500), аргумент по DWARF, FAIL, timeout/recovery
и повторный PASS. Владелец подтвердил видимое мигание. Номинальные 500 мс
не измерены внешним эталоном; GPIO latch не заменяет физическое измерение вывода.

Идентификатор PMUSYS.CHIPID проверяется по РП v3 стр.300, маска 0xFFFFFFF0;
в этом PoC используется строгий отказ при расхождении. Размер Flash — документированная
граница 1 MiB, не измеренный заводской регистр. Проверяются Flash LMA секций,
а не заполнители между ними. Отдельный poc-manifest — снимок ELF/BIN и исходников
после линковки, не production build-manifest и не доказательство происхождения всех объектов.

Исключения/IRQ/DMA, force_return, исчерпание hardware BP, низкое потребление,
выполнение из RAM и другие MCU в объём опыта не входят. Используется одна BP
одновременно; не предполагается совпадение бюджета с Cortex-M.

[Полный протокол и выводы для архитектуры](../../docs/K1921VG015_POC.md).
