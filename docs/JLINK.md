# J-Link: backend и приёмы Commander

Общий документ двух проектов: методы и история опытов сохраняются здесь. Механизм тестирования теперь принадлежит отдельному [stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/README.md). Разделы с прежними планами и числом тестов — журнал этапов; актуальные границы и планы: [архитектура v2](HWTEST_ARCHITECTURE_V2.md), [TODO](../TODO.md).

Проверено на BluePill STM32F103C8T6 / LED PB2, J-Link V9 (hardware V9.60),
пакет SEGGER V8.32, GDB 14.2.90.20240526-git / Python 3.11.4.
Общая прошивка и Python-сценарии не изменены. H503 остаётся отложенным.

## Запуск тестов

Локальный `Tests/stands/bluepill-jlink.local.toml` уже подготовлен для стенда.
Образец без serial — `Tests/stands/bluepill-jlink.example.toml`.
Выбор MCU берётся из проверенного отображения в backend:
STM32F103C8T6 → имя SEGGER STM32F103C8. Другие MCU пока отклоняются,
а не подменяются «похожим» устройством.

```powershell
python -B tools/gdbtest.py run --session build/f103c8-debug-hwtest/hwtest/session.json --test HW_BOOT --stand Tests/stands/bluepill-jlink.local.toml
```

Полный набор:

```powershell
$previousStand = $env:STM32_GDBTEST_STAND
try {
    $env:STM32_GDBTEST_STAND = (Resolve-Path Tests/stands/bluepill-jlink.local.toml).Path
    cmake --build --preset f103c8-check-hw
} finally {
    $env:STM32_GDBTEST_STAND = $previousStand
}
```

Без явного выбора session.json по-прежнему указывает прежний ST-Link/OpenOCD-стенд.
При физически подключённом J-Link использовать именно J-Link TOML.

## Диалект и доказательства

- `JLinkGDBServerCL.exe`: SWD 1000 kHz, явный USB serial, localhost only,
  strict device, timeout подключения 5000 ms, без single-run для recovery.
  Служебные SWO/Telnet/RTT порты заданы как 0; эти каналы не используются тестами.
- Запуск с noreset/nohalt/noir уменьшает автоматические действия сервера,
  но подключение GDB всё равно останавливает ядро: это видно в журнале.
- До тестов выполняется `monitor flash breakpoints = 0`. GDB использует
  hardware breakpoints и лимит профиля 6; Unlimited Flash Breakpoints не используются.
- Reset/halt: `monitor reset`. Finish/recovery: `monitor reset`, `monitor go`,
  `disconnect`. GDB командует MCU через RSP, а не через синтаксис Commander.
- Identity и сравнение Flash остаются в общем агенте перед `load`; запись делает
  J-Link, без CubeProgrammer. Включён verify download, дополнительно читается Flash.
- В отчёт попадают версия backend и отдельная firmware-строка J-Link; ST-LINK API
  version не выдумывается. Serial и командная строка не копируются в metadata.
  Полные локальные логи могут содержать serial/пути, они не предназначены для Git.

Результаты: **22 HW + 2 host CTest PASS**, отдельно 17 host unit tests PASS.
O0-сборка того же приложения и возврат к штатной Og-сборке дали HW_BOOT PASS,
flashed=true и image_verified=true. Verify-only для несовпадающего образа дал
ERROR без записи. Timeout=1 s в HW_RTC_ALARM дал ERROR и успешный host recovery;
последующие подключения и тесты работают. Процессы серверов после завершения закрыты.

Профили других MCU, RTT/SWV, watchpoints и RTOS plugin этим прогоном не проверены.
OpenOCD/ST backend сохранены; после физической замены отладчика их аппаратный
набор в этом этапе повторно не запускался. Их разделение проверено host-тестами.

## Разбор предоставленных VS Code примеров

Изучены launch.json и tasks.json соседнего проекта
`demo-stm32-cmake/stm32f1xx/03-blink`; сами файлы не редактировались.

| Приём / замечание | Применение здесь |
| --- | --- |
| cortex-debug servertype=jlink, interface=swd, device | Соответствует прямому J-Link GDB Server, не OpenOCD с J-Link interface |
| CommandFile для JLink.exe | Удобен для воспроизводимых последовательностей и отдельного чтения MCU |
| В «Запустить (j-link)» написана кириллическая `п` | Для Commander запуск — латинская `g`; в GDB используется `monitor go` |
| r; h; q в задаче reset | Оставляет MCU остановленным; для нормальной работы нужна явная команда g |
| Вывод отправляется в nul, затем echo «Успешно/Ошибка» | Сохранять stdout/stderr, проверять код процесса; конечный echo не заменяет результат операции |
| Один flash.jlink для разных задач | Делать отдельные файлы внутри каталога запуска, исключить параллельное управление одним отладчиком |
| serialNumber закомментирован, -usb есть не во всех задачах | В автоматических тестах USB serial обязателен, индексы 0/1 и nickname не принимаются |
| ocd/jlink и ocd/cmsis-dap выбирают interface/stlink.cfg | Название конфигурации не выбирает адаптер; при переносе исправить interface отдельно |
| preRestartCommands включает load | В ручной отладке это намеренная прошивка; hwtest сначала сверяет identity и образ |

Для текущего проекта скопирован не набор shell-однострочников, а их смысл:
явная последовательность действий, журнал и проверяемое завершение. Изменения
профиля CubeMX/User для смены сервера не потребовались.

## Независимое наблюдение через Commander

После закрытия GDB Server выполнен командный файл: connect, чтение DBGMCU_IDCODE,
10 пар DHCSR/uwTick с sleep 37, q. Команд reset/halt/go/load/erase в нём не было.
Адрес uwTick получен через nm из текущего ELF, не перенесён константой из другого
проекта. Файл, журналы и JSON результата находятся в `build/jlink-observation`.
Результат: device ID 0x410, S_SLEEP в 10/10 выборках, S_HALT отсутствует,
uwTick +350 ms. Это подтверждает работающий MCU во время выборок, но не исключает
короткого влияния подключения и не измеряет энергопотребление.

Минимальный пример чтения для ручного опыта после остановки тестового раннера
(переменная `$jlinkSerial` должна содержать serial локального стенда):

```powershell
New-Item -ItemType Directory -Force build/jlink-read | Out-Null
@('connect', 'mem32 0xE0042000, 1', 'mem32 0xE000EDF0, 1', 'q') |
    Set-Content -Encoding ascii build/jlink-read/read.jlink
$commandFile = (Resolve-Path build/jlink-read/read.jlink).Path
Push-Location build/jlink-read
try {
    & 'C:/Program Files/SEGGER/JLink/JLink.exe' -NoGui 1 -ExitOnError 1 -USB $jlinkSerial -device STM32F103C8 -if SWD -speed 1000 -CommandFile $commandFile *> commander.log
    if ($LASTEXITCODE -ne 0) { throw 'Commander failed; inspect commander.log' }
} finally {
    Pop-Location
}
```

Пример не приобретает блокировку раннера: не запускать его одновременно с GDB,
другой Commander-сессией или VS Code. Нулевой exit code ещё не проверка содержимого
регистров: автоматизированный опыт дополнительно разбирал значения и их динамику.
`tools/observe_sleep.py` по-прежнему OpenOCD-only; опыт Commander пока отдельный,
не объявлен универсальной реализацией непрерывного наблюдения.

Для справки по установленному GDB Server использовать `-version`: попытка `-help`
в V8.32 не показала помощь, а запустила обычный путь подключения с неизвестным
параметром и завершилась на отсутствии device. Это ещё одна причина проверять
синтаксис именно используемой программы, а не переносить ключи от ST/OpenOCD.

Официальная документация: [J-Link GDB Server](https://kb.segger.com/J-Link_GDB_Server),
[J-Link Commander](https://kb.segger.com/J-Link_Commander).

## Повтор с общей identity/Flash политикой

2026-09-24 f103c8-check-hw: 24/24 PASS, DEV_ID0x410 совпадает; Flash128 KiB
против профиля64 KiB даёт warning, linker не расширяется. Strict HW_BOOT PASS.
Live Commander после сервера: S_SLEEP9/10, tick+354ms, без halt. Подробности, ELF
и границы доказательства: [TARGET_IDENTITY](TARGET_IDENTITY.md).
