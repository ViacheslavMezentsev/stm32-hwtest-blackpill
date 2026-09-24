# Работа над стендовым проектом

- Этот репозиторий — прошивка, MCU-профили и стенд для проверки отдельного stm32-gdbtest.
  Ядро и его документация принадлежат отдельному проекту. Сначала читать README.md,
  docs/README.md, docs/HWTEST_ARCHITECTURE_V2.md и TODO.md. История опытов — в docs,
  старые значения числа тестов/планы внутри протоколов не заменяют текущий статус.
- Основная среда: Windows, PowerShell, VS Code, CMake/Ninja, xPack ARM GCC.
  Собирать через presets; MCU/toolchain имеют отдельные build. Базово:
  cmake --preset f411ce-debug, cmake --build --preset f411ce-debug.
- Конфигурация firmware — stm32_config.yml; CMake оставлять тонкой интеграцией.
  Перед изменением YAML читать документацию/skills фактически закреплённого stm32-cmake-yml.
- Зависимости modules — Git-подмодули на фиксированных коммитах. Не писать в них
  build/temp/reports и не менять без задачи. Для доработки stm32-gdbtest использовать
  отдельный checkout .work/stm32-gdbtest внутри workspace; правила — его AGENTS.md.
  Не удалять этот Git checkout очисткой build. Сначала push модуля, затем родителя.
- Все изменения, временные файлы, отчёты и блокировки — только внутри этого workspace.
  Соседние проекты/установленные инструменты только читать/запускать. Не менять global config.
  Не коммитить build, serial, личные пути, local TOML и CMakeUserPresets.json.
- Рабочие ветки codex/...; агент создаёт локальные коммиты и сливает проверенные ветки
  в локальный main. PR только по договорённости. Push делает пользователь; дать точные команды.
- Вести CHANGELOG.md (Keep a Changelog) и TODO.md без сроков. Документация механизма
  обновляется в модуле; аппаратура/профили/измерения здесь. Общая архитектура/методика
  остаётся здесь со ссылками на независимый модуль. Навигация — docs/README.md.

## Firmware и тесты

- Активные профили f103c8/f401cc/f411ce. CubeMX генерирует внутри profiles/<MCU>;
  User общий, Platform — адаптер конкретного MCU. Правки генерации по возможности
  в USER CODE, согласованные с IOC. Не добавлять тестовый код/hooks в firmware.
- Форматировать только C/C++ в User по .clang-format (dry-run --Werror); CubeMX/Core,
  Platform и подмодули не форматировать. Навык cpp-clang-format использован по запросу владельца.
- До новых Python/GDB решений сверять приёмы ../buck-boost-course/99_BOARD_TEST,
  Tests/BBC_SW_LLR и исходную docs/HWTEST_ARCHITECTURE.md. Они изучены; не переносить
  личные пути, serial, подавление ошибок. Исходный архитектурный документ не переписывать.
- docs/gdb.pdf §23.3 описывает GDB19; фактический xPack GCC13 содержит GDB14.2.90.
  Проверять API presence; -g3 сохраняет macro debug info, но не неиспользуемые функции.
  GDB API только в главном потоке, внешний timeout обязателен. Python breakpoint может
  быть pending вопреки CLI pending off: проверять явно.
- Проектные сценарии Tests/scenarios, @case/ожидания/контракты — profiles/<MCU>/Tests.
  Не переносить app-specific логику в ядро. API/CLI/contracts/macros описаны в модуле.
  CLI приложения: python -B tools/gdbtest.py. Host ядра: python -B tools/test_module_host.py
  (65 тестов в отдельных build/module-host копиях). CMake attach здесь без SELF_TESTS.
- Manifest привязывает ELF и target.toml после линковки; после смены toolchain чистая
  сборка. Runtime metadata, build manifest и ELF/HAL preflight — разные доказательства.
  Source review hashes не обновлять без анализа HAL. F1/F4 RCC различаются const.
  NOT_REQUESTED не означает совместимость. Предикаты/CMSIS masks использовать осмысленно,
  физические ожидания брать независимо; MMIO GET может иметь побочный эффект.
- F103: LED PB2 подтверждён владельцем; F411/F401 PC13. Получать pin/port/level из EXPECTED.
  RTC IRQ мост F103 в Platform: при регенерации не допустить дубли handler/NVIC.
- ADC: User/Src/adc_units.cpp — арифметика, Platform — калибровка. F103 TYPICAL,
  F411 FACTORY; м°C не означают точность 0.001°C. F401 channel16, F411 channel18
  (HAL TEMPSENSOR у F411 содержит служебный флаг). Native tests — Tests/native.
- app_idle — Sleep/WFI с SysTick, не Stop. SWD/DBGMCU влияют на clocks/потребление;
  S_SLEEP не измеряет ток. observe_sleep — проектный OpenOCD-only инструмент,
  передавать проектный root для output/temp, не писать в подмодуль.

## Стенды и доказательства

- Текущие стенды подтверждены владельцем: F411CE + ST-Link/SWD, F103C8 + J-Link/SWD и NUCLEO-F030R8 + встроенный J-Link STLink/SWD.
  Опыты К1921ВГ015 завершены, его стенд разобран; не запускать его HW-команды.
  Перед каждым HW набором назвать плату/MCU, отладчик, backend и соединения, явно
  сказать оставить или изменить стенд. При подтверждённом текущем стенде повторное
  разрешение не нужно; смена требует ответа владельца. USB не подтверждает разводку.
- F411 OpenOCD: Tests/stands/blackpill.local.toml; ST server: blackpill-stlink.local.toml.
  F103 J-Link: bluepill-jlink.local.toml. Выбирать stand явно, не полагаться на default.
  UART/VCOM пока не подключать. Термин в русских текстах — «отладчик».
- OpenOCD0.12.0/ST server7.14.0 (CubeCLT1.22.0), J-Link8.32 проверялись; диалекты
  reset/finish различаются. J-Link mapping пока F103C8, Flash breakpoints выключены.
  Не включать автоматически mass erase, option bytes, shared mode и firmware update.
- DEV_ID mismatch по умолчанию WARNING и продолжение по выбранному target; strict
  отклоняет до Flash. Ошибка чтения или образ больше profile/observed Flash — ERROR.
  Не расширять linker по названию MCU/размеру из программы. F401 маркировка и DEV_ID
  различались на экземплярах; F103 Flash128K против профиля64K не доказывает верхние64K.
- После отделения модуля: host44, три MCU build/offline; F411/OpenOCD24/24,
  F103/J-Link24/24, consumer3/3, timeout/recovery/restore PASS. Новые macro-сценарии
  F401 аппаратно ещё не повторены. Старые F401/ST и F411/ST результаты исторические.
  Успешная сборка/host-тесты не означают HW PASS; число тестов не покрытие кода.
- Mutex координирует участвующие runners в одной Windows-сессии, ST/OpenOCD имеют
  общий ключ ST-Link serial. Vendor tools/VS Code не участвуют. После crash освобождение
  mutex не гарантирует завершение server; WAIT_ABANDONED — ERROR до подключения.
- H503CB приостановлен владельцем. STM32H503CBT6, 128KiB Flash/32KiB RAM, CubeH5 1.7.0;
  IOC/Core/SVD сохранены, YAML/CMake не включены. Не менять генерацию до сообщения.
  Далее проверять pinout/DMA/IRQ/RTC/backend по docs/H503_CUBEMX.md; не переносить
  F411 ADC-калибровку или TrustZone H563 по аналогии.
- Развивать docs/STM32_TESTING_METHODS.md: доказательство, влияние отладчика, ограничения,
  положительный/отрицательный опыт. Для очистки следовать docs/BUILD_ARTIFACTS.md;
  аппаратные ошибки/отчёты, текущие ELF/manifest и Git checkout сохранять.

- README — краткое пользовательское введение (зачем/что/как/зависимости/ссылки). Точные результаты, версии и ограничения поддерживать в docs/STATUS.md; хронологию — в CHANGELOG и протоколах. Не превращать README в журнал текущей работы.

- К1921 PoC — examples/k1921vg015-poc, внешний NIIET_DEVICE_DIR только читать;
  build/k1921vg015-poc, explicit Tests/stands/k1921-jlink.local.toml. Собран GCC13.3.0-2,
  GDB15.1/Python3.12.2 (-py3), -Og -g3. Не менять production STM32 guards ради запуска PoC.
  CHIPID0xDEADBEE1 по RM p300, Flash1MiB по разделу7 — документированная граница,
  не заводской размер. Проверка по ELF load regions, включая .data LMA; gaps не сравнивать.
  Host4, offline PASS, HW23checks PASS, negative FAIL, timeout ERROR+recovery0, repeatPASS;
  LED подтверждён владельцем, собственный blink оставлен running. Не использовать
  generic trap_entry как fault trap. Полный runner/schema/IRQ/force_return/low-power
  пока не портированы; протокол docs/K1921VG015_POC.md. У серверного процесса должен
  быть доступ к определениям K1921VG015 в пользовательском окружении SEGGER.

- Диагностика errata К1921 — examples/k1921vg015-errata; намеренно отдельный
  измерительный firmware, обычный blink не менять. Протокол K1921VG015_ERRATA.md.
  CloudBEAR требует полного march для multilib; ключ приложения не исправляет архивы.
  HW series восстанавливает blink; OBSERVED не означает отсутствие ошибок.
  Не выводить безопасность по одному успешному запуску или single-step.

- ELF load sections: LMA, Flash bounds до сервера, BIN gap-fill 0xFF.
  В режиме секций image_verified не означает проверку gaps/full-image CRC. Модуль docs/IMAGES.md;
  текущий протокол docs/ELF_LOAD_REGIONS.md: host53, F411/OpenOCD22 и F103/J-Link22.

- Опциональный full-image: profiles/f411ce и f103c8/full-image.toml, первые16KiB,
  fillFF. CLI --image-policy или абсолютный STM32_GDBTEST_IMAGE_POLICY; по умолчанию
  остаются секции. CRC считается на ПК по readback, не MCU peripheral.
  Контейнер program.elf грузить вместе с symbol-file исходного firmware.elf.
  Host65, A5/FF/verify-only/restore и GPIO после реальной записи проверены на двух
  стендах. Снимать env image policy для обычного режима; docs/FULL_IMAGE_CRC.md.

- F030R8: offline preset f030r8-debug, CubeF0 V1.11.6, LED PA5 active-high,
  hadc/TIM3, ADC scan IN16/17. target/contracts/M0 review и J-Link STLink/SWD 17/17 PASS.
  TS_CAL1 + типовой slope, quality=3; не читать TS_CAL2 по общему LL header.
  User HAL-free, Platform обслуживает HAL callbacks через app_* callbacks.
  Общие Python-сценарии используют adc_handle/timer_handle/timer_enabled из EXPECTED.
  Nucleo подключена к встроенному J-Link STLink: явно выбирать
  Tests/stands/nucleo-f030r8-jlink.local.toml; LD2 подтверждён, MCU running.
  Не путать с BluePill J-Link; firmware отладчика не менять. Offline: tools/check_profile_offline.py --session build/.../hwtest/session.json.
