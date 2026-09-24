# Работа над проектом

- Платы: WeAct BlackPill V3.1 (STM32F411CEU6, LED PC13) и WeAct BluePill V1.1 / BluePill-Plus (STM32F103C8T6, LED PB2); ST-Link v2 с USB-VCOM. Официальные проекты указаны в README.
- Основная среда: Windows, PowerShell, VS Code, CMake/Ninja, xPack ARM GCC.
- Конфигурацию прошивки вести в `stm32_config.yml`; CMake оставлять тонким слоем интеграции stm32-cmake-yml.
- Зависимости в `modules/` — Git-подмодули с закреплёнными коммитами. Не редактировать их как исходники проекта без отдельной причины.
- Перед изменением YAML читать соответствующую документацию и skills фактически подключённой версии фреймворка.
- До реализации Python-скриптов управления отладчиком и использования GDB-Python обязательно изучить `../buck-boost-course/99_BOARD_TEST`, включая `Tests`. Сопоставить готовые решения с `docs/HWTEST_ARCHITECTURE.md`; не переносить зашитые пути, номера отладчиков и подавление ошибок.
- HW-тесты не должны добавлять тестовый код в прошивку. Успешная сборка не означает успешную аппаратную проверку.
- Изменения CubeMX-кода по возможности помещать в USER CODE-секции. Настройки периферии согласовывать с `.ioc`.
- Собирать через presets. Для смены компилятора использовать отдельную build-папку. Базовая проверка: `cmake --preset debug`, затем `cmake --build --preset debug`.
- Вести `CHANGELOG.md` (Keep a Changelog) и `TODO.md` с отмеченными этапами без сроков.
- Рабочие ветки: `codex/...`. Агент самостоятельно создаёт локальные коммиты и сливает проверенные ветки в локальный main. PR нужен только по отдельной договорённости. Push выполняет пользователь; сообщать ему точную команду и не выполнять push самостоятельно.
- Все изменения файлов, временные файлы, блокировки и отчёты размещать только внутри текущего репозитория. Другие проекты и установленные инструменты доступны только для чтения/запуска. Не менять глобальные настройки и содержимое подмодулей.
- ST-Link SWD-стенд разрешено использовать для прошивки и тестов. Сейчас одновременно подключены BlackPill F411 + ST-Link и BluePill F103 + J-Link; выбирать preset/stand явно. UART/VCOM пока не подключён.
- Раздел 23.3 `docs/gdb.pdf` и исходный BOARD_TEST изучены. PDF описывает GDB 19, фактический GDB в xPack GCC 13 — 14.2.90; наличие API проверять, не выводить из номера GCC. Не вызывать GDB API из фоновых потоков; сохранять внешний таймаут.
- Не добавлять в Git build-артефакты, персональные пути, локальные конфиги стенда и серийные номера отладчиков.
- Развивать docs/STM32_TESTING_METHODS.md как практическую основу самостоятельного модуля: для каждого нового метода фиксировать доказательство, влияние отладчика, ограничения, положительный и отрицательный опыт. Изучены наборы Tests/BBC_SW_LLR соседнего 99_BOARD_TEST; переносить приёмы с проверкой применимости к MCU/HAL.
- Разделять общую инфраструктуру, профиль MCU/стенда и проектные тесты. Не объявлять покрытие кода по числу тестов и поддержку других STM32 без проверки.
- MCU-профили: profiles/f411 и profiles/f103; выбор STM32_YML_PROFILE. CubeMX генерирует код внутри соответствующего каталога. Для нового MCU использовать отдельный build; общий User подключён к обоим профилям, адаптеры — profiles/<MCU>/Platform. Исходные 17 HW-сценариев проверены на обоих MCU; текущие 22 HW + 2 host проверены на F103/J-Link и F411/ST-Link через OpenOCD/ST server, включая ADC/Sleep/manifest/HAL. Любую следующую замену платы согласовывать с пользователем.
- Общий YAML содержит профили сборки, target.toml внутри профиля — настройки HWTEST. Периферийный план: docs/PERIPHERAL_PLAN.md. Не считать -g3 средством сохранения неиспользуемых функций в ELF.
- Форматировать только C/C++ в User по корневой .clang-format (clang-format --dry-run --Werror); не применять форматирование к CubeMX/Core, Platform и подмодулям. Навык cpp-clang-format использован по запросу пользователя.
- F103: RTC IRQ в IOC включён, но текущая генерация пропускает NVIC/handler; мост находится в Platform/platform.c. При регенерации исключить дублирование обработчика.
- GDB Python может создать pending breakpoint вопреки CLI pending off; сохранять явную проверку bp.pending и внешний таймаут.
- Проектные общие сценарии — Tests/scenarios; обёртки @case и MCU-ожидания — profiles/<MCU>/Tests. Не переносить приложение-специфичную логику в hwtest.
- ADC: User/Src/adc_units.cpp — чистая арифметика; Platform читает калибровку. F103 quality=TYPICAL, F411=FACTORY; м°C не означают точность 0.001°C. Native tests — Tests/native, build/adc-native. Новые ADC-сценарии проверены аппаратно на F103 и F411.
- Pinout подключённой WeAct F103: LED_USER на PB2 (подтверждено пользователем), не типовой PC13. F411 остаётся PC13. Общие GPIO-сценарии обязаны получать порт/пин/уровень из EXPECTED профиля.
- app_idle использует обычный Sleep/WFI с активным SysTick; Stop ещё не реализован. На F103 проверены 24/24 CTest и S_SLEEP без halt через tools/observe_sleep.py. Не считать это измерением энергопотребления: SWD и DBGMCU влияют на тактирование.
- В русских описаниях использовать термин «отладчик». Английские API/probe и существующую TOML-схему не переименовывать ради терминологии.
- Совместимость зависит от GDB/Python, Cube/HAL/CMSIS, ABI/оптимизации, backend/прошивки отладчика, MCU и платы. Следовать docs/COMPATIBILITY.md; различать runtime manifest/API presence, post-link build manifest и выборочный ELF/HAL preflight.
- h503 — планируемый профиль, не добавлен в CMake/YAML. Получены IOC/Core/SVD для подтверждённого владельцем STM32H503CBT6, 128 KiB Flash/32 KiB RAM, CubeH5 V1.7.0. Инструкция docs/H503_CUBEMX.md; перед интеграцией проверить DMA/IRQ/RTC, pinout и backend. Не переносить ADC-калибровку 30/110°C F411 на H503; не приписывать H503 TrustZone по аналогии с H563.

- H503 приостановлен владельцем до отдельного сообщения; настройки/генерацию не менять. Действующие стенды — F411/ST-Link и F103/J-Link.
- compatibility schema 1 в отчёте — только runtime metadata и наличие GDB API до подключения; post-link HAL/CMSIS/compiler manifest находится в отдельном build_manifest; выборочный ELF/HAL preflight описан в docs/HAL_CONTRACTS.md.

- Backend выбирается локальным TOML: openocd, stlink либо jlink. ST 7.14.0/CubeCLT 1.22.0 проверен на F103: 24/24, Flash/recovery. Диалекты в hwtest/backends.py; ST finish=monitor reset+detach. Observe_sleep пока OpenOCD-only. Не включать shared mode, mass erase, option-byte изменения или обновление firmware отладчика автоматически. См. docs/GDB_BACKENDS.md.

- Сейчас BluePill подключена к J-Link, BlackPill — к ST-Link; для HW запусков выбирать Tests/stands/bluepill-jlink.local.toml явно (session default остаётся ST-Link). J-Link V8.32 проверен 24/24; mapping MCU пока только STM32F103C8T6→STM32F103C8. Не включать Flash breakpoints: setup их отключает, используются hardware BP. Finish=reset/go/disconnect. См. docs/JLINK.md; приложенные launch/tasks изучены, внешний проект не изменять.

- Перед каждым новым набором аппаратных тестов заранее сообщать плату/MCU, отладчик, backend и требуемые соединения; явно говорить, оставить текущий стенд или изменить его. Для подтверждённого текущего стенда повторное разрешение не требуется. При смене платы/отладчика/проводки дождаться подтверждения владельца до аппаратных действий. Наличие USB-устройства не заменяет подтверждение разводки.

- HWTEST CMake создаёт post-link build-manifest.json (Windows/Ninja); новые session требуют его совпадения с ELF и target.toml до запуска сервера. Не восстанавливать версии библиотек из текущих исходников во время HW-run. После замены toolchain — чистый build; границы доказательства описаны в docs/COMPATIBILITY.md.

- F103/F411: семь сценариев в каждом профиле объявляют contracts в @case; schema 1 в profiles/<MCU>/Tests/contracts.json. Проверки выполняются отдельным offline GDB до сервера; NULL требует совпадения reviewed-source hash с build manifest. Не обновлять hash без анализа поведения HAL. NOT_REQUESTED не означает проверенную совместимость; F411 адаптирован к HAL 1.8.5 с const RCC-указателями; профильные reviewed-source hashes различаются.

- F411/ST-Link: OpenOCD 0.12.0 и ST server 7.14.0 дали 24/24 на одном ELF; timeout/recovery проверены. Для ST выбирать blackpill-stlink.local.toml, для OpenOCD — blackpill.local.toml. Локальный serial обновлён под подключённый ST-Link, не переносить его в Git.
