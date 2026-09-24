# STM32F429I-DISCO / ST GDB Server

Проверка 2026-09-25, run IDs в UTC 2026-09-24. Тот же подтверждённый стенд
DISCO/STM32F429ZIT6 со встроенным ST-Link/V2/SWD, что и в
[прогоне OpenOCD](F429_OPENOCD_VALIDATION.md).

## Условия

ST GDB Server 7.14.0 из CubeCLT 1.22.0, CubeProgrammer 2.23.0,
firmware ST-Link V2J43S0. Запрошено 1000 kHz, сервер сообщил 950 kHz и VTref 2.88 В.
Обновление firmware не выполнялось. Явный serial только в локальном
Tests/stands/disco-f429zi-stlink.local.toml. Шаблон — одноимённый example.toml.
Профиль/ELF/GDB и модуль не менялись относительно OpenOCD:
ELF `d7346f72b1f29ea6864258d13e906cbd87c0ff1b494053b61565d3383f2e9641`.

## Первый прогон: частичный результат

Первичный HW_BOOT PASS. Затем CTest дал 18 PASS и четыре ERROR:
HW_ADC_INVALID, HW_ADC_VECTORS, HW_SLEEP_SYSTICK, HW_SLEEP_TIMER.
Во всех четырёх случаях сервер завершился до готовности с сообщением
Target USB comms error / Please reconnect the ST-LINK USB cable.
Сами сценарии не выполнились; это не свидетельство неверного ADC/Sleep.
Первый ошибочный run: 20260924T204136.678004Z-HW_ADC_INVALID-40220.
Полный отчёт: build/f429zi-debug-hwtest/hwtest/f429zi-stlink-validation.xml;
server.log и result.json сохранены в hwtest/runs.

До сбоя прошли GPIO/RCC, init ADC/DMA/TIM2/RTC, runtime IRQ/Alarm,
HAL_ERROR/NULL-инъекции, ADC timeout и проверка правдоподобия физических величин.
Причина USB-сбоя пока не установлена. Само сообщение не доказывает проблему
кабеля, firmware или runner. Автоматический повтор не превращает ERROR в PASS.

## После переподключения USB

Владелец переподключил CN1, сохранив стенд. Все четыре незавершённых сценария
прошли: HW_ADC_INVALID, HW_ADC_VECTORS, HW_SLEEP_SYSTICK, HW_SLEEP_TIMER.
Отдельный отчёт: hwtest/f429zi-stlink-retry.xml. Итого каждый из 22 сценариев
получил PASS, но непрерывного успешного прогона 22/22 через ST не было.
Первичные четыре ERROR остаются в отчёте; стабильность длительной серии требует
отдельного исследования, без автоматического обновления firmware.

## Прошивка и recovery

Без изменения исходников собран отдельный O0-образ той же программы:
build/f429zi-stlink-o0, Flash19380 B, SRAM1896 B, offline10 contracts PASS.
SHA-256 `694f6a2a6cda89f41f2411c0362c27b5bd69ff31fce1f4a0b12753cb53e07d0f`.

- O0 HW_BOOT с verify-only при Og в MCU: ожидаемый ERROR (Flash mismatch),
  flashed=false; run 20260924T204326.037698Z-HW_BOOT-19932.
- O0 HW_BOOT с if-different: PASS, flashed=true, image_verified=true;
  run 20260924T204347.576878Z-HW_BOOT-37972.
- Восстановление Og: PASS, flashed=true, image_verified=true;
  run 20260924T204351.140959Z-HW_BOOT-65268.
- HW_RTC_ALARM с внешним timeout=1 с: ожидаемый ERROR, завершение
  reset_run (host recovery); run 20260924T204407.360961Z-HW_RTC_ALARM-38452.
  Это принудительное ограничение времени, не доказательство ошибки RTC.
- Последующий HW_BLINK: PASS, flashed=false, image_verified=true, reset_run;
  run 20260924T204409.476676Z-HW_BLINK-10824. MCU оставлен работающим со штатным Og.

ST завершает сеанс monitor reset + detach; команды OpenOCD не подставляются.
Проверены ELF load sections, не gaps/full-image CRC. Проверка записи затронула
начало Flash; программирование обоих банков целиком не доказано. Recovery по
таймауту не обещает восстановление после физического USB-сбоя.
LCD/SDRAM, внешние loaders, option bytes и firmware отладчика не менялись.

## Повторение

Скопировать Tests/stands/disco-f429zi-stlink.example.toml в одноимённый
.local.toml и указать локальные пути/serial. Для одного сценария:

```powershell
python -B tools/gdbtest.py run --session build/f429zi-debug-hwtest/hwtest/session.json --test HW_BOOT --stand Tests/stands/disco-f429zi-stlink.local.toml
```

Default CMake session остаётся OpenOCD; ST выбирается явно через --stand либо
переменную STM32_GDBTEST_STAND на время CTest (см. GDB_BACKENDS.md).
