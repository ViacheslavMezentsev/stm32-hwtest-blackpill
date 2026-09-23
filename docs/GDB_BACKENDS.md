# Серверы GDB: OpenOCD и ST-LINK

Общие тесты работают через GDB-Python и RSP. Backend задаёт запуск сервера,
готовность, reset/halt, завершение и recovery; он не меняет ожидания периферии.
Реализация выбора — `hwtest/backends.py`. J-Link пока не реализован и не проверен.

## Запуск ST-LINK на BluePill

Скопировать `Tests/stands/bluepill-stlink.example.toml` в
`Tests/stands/bluepill-stlink.local.toml`; указать свой serial, полный путь к
`ST-LINK_gdbserver.exe` и `programmer_dir` — каталог с `STM32_Programmer_CLI.exe`.
Локальный TOML исключён из Git. Для текущей машины локальная копия уже подготовлена.

Один тест:

```powershell
python -B hwtest/cli.py run --session build/f103-debug-hwtest/hwtest/session.json --test HW_BOOT --stand Tests/stands/bluepill-stlink.local.toml
```

Полный набор (переменная только в текущем PowerShell; сохранить предыдущее значение):

```powershell
$previousStand = $env:HWTEST_STAND
try {
    $env:HWTEST_STAND = (Resolve-Path Tests/stands/bluepill-stlink.local.toml).Path
    cmake --build --preset f103-check-hw
} finally {
    $env:HWTEST_STAND = $previousStand
}
```

Без переопределения остаётся существующий OpenOCD-стенд из session.json.
Компилятор и GDB-Python не меняются при выборе сервера: проверен xPack GCC13
с GDB 14.2.90.20240526-git / Python 3.11.4, а не GDB из поставки CubeCLT.

## Проверенные различия

| Операция | OpenOCD 0.12.0 | ST-LINK GDB Server 7.14.0 (CubeCLT 1.22.0) |
| --- | --- | --- |
| Выбор MCU | target/stm32f1x.cfg | Определение сервером ST; identity guard раннера сохраняется |
| Запуск | ST-Link interface + target; localhost | SWD, attach `-g`, persistent `-e`, serial, CubeProgrammer path |
| Готовность | Listening on port … for gdb connections | Waiting for debugger connection |
| Подключение GDB | extended-remote | extended-remote |
| Reset/halt | monitor reset halt | monitor reset |
| Прошивка | GDB load, OpenOCD flash driver | GDB load, сервер вызывает CubeProgrammer |
| Проверка образа | Чтение Flash до/после записи | То же; дополнительно включён серверный verify `-s` |
| Завершение | monitor reset run; disconnect | monitor reset; detach (возобновляет выполнение) |
| Внешний timeout | Новый GDB-клиент для recovery | Новый клиент к persistent-серверу; reset + detach |
| Runtime metadata | Версия OpenOCD, STLINK firmware/API | Версия ST server и firmware; API v2 баннером не сообщается, поле null |

Schema 1 target.toml сохранена ради совместимости: её openocd_target/reset-поля
использует только OpenOCD. ST получает команды из backend, а MCU identity,
Flash bounds, breakpoints и fault handlers — из общего профиля. Это промежуточная
совместимость, не универсальная новая схема профиля для всех серверов.

Сервер ST сам устанавливает аппаратное соединение до запуска клиента GDB.
Preflight GDB выполняется до подключения GDB/reset/load, но не является проверкой
до любого обращения сервера к SWD. Attach не означает отсутствие влияния отладчика.
При запросе 1000 kHz ST сообщил COM frequency 950 kHz; запрошенная частота — предел,
а не доказательство фактической частоты интерфейса.

Сервер ST открывает дополнительный порт для SWV (наблюдался GDB port + 1).
В установленной CLI-справке нет аналога OpenOCD bindto; эти процессы предназначены
для локального стенда. SWV в текущие тесты не включён. Shared mode `-t` не используется:
доступ обоих backend защищён одной блокировкой по serial, сервер принадлежит запуску.
Все logs/temp/CubeProgrammer-временные файлы направляются в репозиторий: cwd запуска,
`--temp-path`, `-f`, TEMP/TMP. После завершения дерево процессов закрывается.

## Результаты и границы

- BluePill: 22 HW + 2 host CTest PASS через ST; те же сценарии через OpenOCD.
- Проверена настоящая запись через ST: отдельная O0-сборка того же F103 проекта
  и затем восстановление штатного Og-образа. Оба запуска HW_BOOT дали PASS,
  flashed=true, image_verified=true. Тестовый код в MCU не добавлялся.
- O0-образ в режиме verify-only при другом образе Flash дал ERROR, flashed=false.
- Принудительный timeout=1 s в HW_RTC_ALARM дал ERROR и успешный host recovery;
  следующий запуск работал. Значение ERROR не заменяется на PASS из-за восстановления.
- host-тесты проверяют различия команд, обязательный CubeProgrammer path,
  ошибочные ключи TOML и парсинг версии без копирования serial/путей в metadata.

ST даёт доступ к собственным алгоритмам программирования и поддержке устройств
CubeProgrammer. Но «больше возможностей» нужно подтверждать для конкретной функции.
Ограничения аппаратных breakpoint, HAL, оптимизации и влияния halt остаются.
SWV, внешние flash loaders, multicore, debug authentication и новые семейства
не считаются проверенными этим прогоном. H503 по просьбе владельца отложен.
Option bytes, mass erase и обновление firmware отладчика не выполнялись.

`tools/observe_sleep.py` пока намеренно OpenOCD-only: он использует Tcl read_memory
при работающем MCU. Его нельзя автоматически перенаправить в ST через замену exe.
Для ST нужен отдельный подтверждённый способ чтения без halt. То же относится к
будущему J-Link: переносимость RSP не доказывает одинаковую семантику monitor/detach.

Источники: справка `ST-LINK_gdbserver.exe --help` установленного CubeCLT,
практические журналы в build/hwtest и
[ST UM2576: ST-LINK GDB server](https://www.st.com.cn/resource/en/user_manual/um2576-stm32cubeide-stlink-gdb-server-stmicroelectronics.pdf).
