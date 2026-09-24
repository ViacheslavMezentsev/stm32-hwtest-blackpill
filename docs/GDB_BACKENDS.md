# Серверы GDB: OpenOCD, ST-LINK и J-Link

Общие правила серверов и диалекты перенесены в [stm32-gdbtest](../modules/stm32-gdbtest/docs/BACKENDS.md).
Здесь — настройка наших стендов и аппаратные результаты.

Общие тесты работают через GDB-Python и RSP. Backend задаёт запуск сервера,
готовность, reset/halt, завершение и recovery; он не меняет ожидания периферии.
Реализация выбора находится в отдельном модуле. J-Link V8.32 проверен на BluePill:
[настройка, результаты и Commander](JLINK.md).

F429ZI DISCO также проверена через ST: 18 PASS, USB-сбой, затем 4 PASS после
переподключения; Flash/verify-only/timeout/recovery выполнены.
[Протокол и границы](F429_STLINK_VALIDATION.md).

## Запуск ST-LINK на BluePill

Скопировать `Tests/stands/bluepill-stlink.example.toml` в
`Tests/stands/bluepill-stlink.local.toml`; указать свой serial, полный путь к
`ST-LINK_gdbserver.exe` и `programmer_dir` — каталог с `STM32_Programmer_CLI.exe`.
Локальный TOML исключён из Git. Для текущей машины локальная копия уже подготовлена.

Один тест:

```powershell
python -B tools/gdbtest.py run --session build/f103c8-debug-hwtest/hwtest/session.json --test HW_BOOT --stand Tests/stands/bluepill-stlink.local.toml
```

Полный набор (переменная только в текущем PowerShell; сохранить предыдущее значение):

```powershell
$previousStand = $env:STM32_GDBTEST_STAND
try {
    $env:STM32_GDBTEST_STAND = (Resolve-Path Tests/stands/bluepill-stlink.local.toml).Path
    cmake --build --preset f103c8-check-hw
} finally {
    $env:STM32_GDBTEST_STAND = $previousStand
}
```

Без переопределения остаётся существующий OpenOCD-стенд из session.json.
Компилятор и GDB-Python не меняются при выборе сервера: проверен xPack GCC13
с GDB 14.2.90.20240526-git / Python 3.11.4, а не GDB из поставки CubeCLT.

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
другим backend: переносимость RSP не доказывает одинаковую семантику monitor/detach.
Для J-Link выполнен отдельный опыт Commander, описанный в JLINK.md.

Источники: справка `ST-LINK_gdbserver.exe --help` установленного CubeCLT,
практические журналы в build/hwtest и
[ST UM2576: ST-LINK GDB server](https://www.st.com.cn/resource/en/user_manual/um2576-stm32cubeide-stlink-gdb-server-stmicroelectronics.pdf).


## F411: OpenOCD и ST server

Оба сервера проверены на BlackPill F411 + ST-Link: по 24/24 CTest на одном ELF,
включая build manifest, семь HAL-контрактов, ADC/Sleep и timeout/recovery.
[Доказательства и ограничения](STM32_TESTING_METHODS.md#f411ce-hal-контракты-и-два-сервера-st-link-2026-09-24).
Для ST используйте копию `Tests/stands/blackpill-stlink.example.toml` в
`blackpill-stlink.local.toml` с локальными путями и serial. Для OpenOCD —
`blackpill.local.toml`. Выбирать файл явно через STM32_GDBTEST_STAND; аппаратный профиль
задаётся preset debug-hwtest. Два отладчика могут быть подключены одновременно,
но каждый запуск адресует только явно выбранный serial и MCU-профиль.
