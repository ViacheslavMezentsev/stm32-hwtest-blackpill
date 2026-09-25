# Changelog

Все заметные изменения в этом проекте будут документироваться в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

## [Unreleased]

### Fixed

- Исправлены 48 ссылок документации через подмодуль stm32-gdbtest: теперь они
  ведут в отдельный репозиторий на закреплённый коммит, включая руководство автора
  из README. Исправлены два устаревших якоря разделов.

### Added

- Общий план периферии пяти профилей: фактическая IOC-матрица, отдельные условия
  MCU/платы/стенда, уровни проводки и оборудования, пакеты P1–P8 и критерии проверки.
  Уточнены границы текущего API и приостановленный статус H503; удалены устаревшие
  утверждения PERIPHERAL_PLAN о статусе F411 и поддержке только OpenOCD.


- F429: сравнены серии серверов — ST24/24 без паузы и24/24 с2с, OpenOCD22 PASS
  и USB ERROR на23-м; повторный полный ST набор22/22 PASS. Протокол устойчивости
  и методика отделения USB-ошибок от ошибок сценария; модуль не изменён.

- F429ZI/ST GDB Server: все 22 сценария получили PASS (18+4 после USB reconnect),
  запись/восстановление Og, verify-only и timeout/recovery; шаблон стенда и протокол
  F429_STLINK_VALIDATION.md с сохранением исходных четырёх USB ERROR.

- STM32F429I-DISCO/ST-Link V2/OpenOCD: 22/22 аппаратных сценария и 3/3 host
  проверки PASS, DEV_ID0x419/Flash2MiB, LD3 подтверждён; протокол F429_OPENOCD_VALIDATION.md.

- Профиль f429zi для старой STM32F429I-DISCO: сборка, Platform, 22 сценария,
  10 HAL-контрактов и шаблон OpenOCD. Traceability/offline PASS, HW ожидается.
  RTC исправлен на 127/249 в IOC и генерации; TIM2 7999/99 подтверждён.

- NUCLEO-F030R8/J-Link STLink/SWD: прошли 17/17 сценариев, LD2 подтверждён;
  обновлён подмодуль (mapping F030/J-Link), добавлены шаблон и протокол
  F030_JLINK_VALIDATION.md. Host65 и повторный pinned boot/offline — PASS.


- F030R8: target Cortex-M0, 17 подготовленных сценариев / 9 контрактов,
  preset с тестами и отдельный шаблон встроенного ST-Link. HW пока ожидается.
- Общая offline-проверка профиля: manifest/ELF/требования/HAL preflight без сервера,
  CTest host.profile_offline. Параметризованы ADC/TIM в общих сценариях;
  затронутая регрессия F411/OpenOCD и F103/J-Link — по 3/3.


- Offline-профиль NUCLEO-F030R8 (CubeF0 V1.11.6), preset f030r8-debug,
  PA5 LED и TIM3/ADC/RTC адаптер; инструкции и ограничения в README профиля.
- Расчёт F030 по TS_CAL1 и VREFINT_CAL с типовым наклоном, отдельный quality=3
  и native-проверки. Общий User освобождён от HAL/имён дескрипторов;
  аппаратные вызовы и HAL callbacks теперь принадлежат Platform.
- HAL macro contracts и точки наблюдения перенесены из User в Platform:
  регрессия F411/OpenOCD 22/22 и F103/J-Link 22/22, native ADC PASS.
  Ограничение контекста -g3 описано в STM32_TESTING_METHODS.md.


- Политики полного 16-KiB образа для F411CE/F103C8 и новая версия stm32-gdbtest:
  canonical BIN/ELF-контейнер, readback всех байтов и CRC-32/ISO-HDLC на ПК.
  A5/FF отрицательный опыт, verify-only, восстановление и HAL-макросы после load
  проверены на F411/OpenOCD и F103/J-Link; host65. Протокол FULL_IMAGE_CRC.md.

### Fixed

- Обновлён stm32-gdbtest: Flash проверяется по загружаемым секциям ELF/LMA,
  промежутки BIN больше не создают ложное несовпадение. Отдельно описан план
  канонического образа/CRC. Host53, F411/OpenOCD22, F103/J-Link22 — PASS.
- Зафиксирован возврат к двум STM32-стендам; стенд К1921 разобран владельцем.

### Added

- Диагностический пример errata К1921ВГ015: from_chars в xPack 13/14 и CloudBEAR
  14.1.0.7 с -mfix-cloudbear-0001, nop/RAM-контроли и точные битовые результаты.
  Протокол K1921VG015_ERRATA.md содержит варианты обхода и границы доказательства.

- Bare-metal пример К1921ВГ015 (RV32, PC0 blink) с read-only внешним SDK, presets и
  экспериментальным GDB-Python lifecycle через J-Link EDU v11/JTAG.
- Переиспользованы неизменённые Target API и блокировки stm32-gdbtest: 23 проверки
  поведения PASS, намеренный FAIL, внешний timeout/recovery и повторный PASS.
  Владелец подтвердил мигание; MCU оставлен running. Ядро модуля не изменялось.
- Проверка Flash по LMA загружаемых секций и четыре host-регрессии; выявлен ложный
  отказ сплошного BIN-сравнения на незагружаемом ELF gap. Протокол K1921VG015_POC.md
  описывает результаты и необходимые границы адаптеров для production-переноса.

### Changed

- README переработан как пользовательское введение: назначение, подход, состав, зависимости и навигация. Срез проверок и ограничений вынесен в docs/STATUS.md; добавлена Mermaid-схема.


### Changed

- Проект оформлен как стенд проверки самостоятельного stm32-gdbtest; обновлены README, архитектура v2 и планы.
- Канонические руководства API/contracts/macros/manifest/backend/identity/mutex перенесены в репозиторий модуля; здесь оставлены применение, аппаратные доказательства и общие методы.
- Подмодуль закреплён на `60eaaf4` (только документация). Проверены локальные Markdown-ссылки; firmware, ядро и тесты не менялись, новые аппаратные запуски не выполнялись.
- Добавлены карта документации и правила хранения build-артефактов; устаревшие сборки и воспроизводимые временные копии очищены выборочно, текущие ELF/manifest и журналы аппаратных опытов сохранены.


### Changed

- Подключён Git-подмодуль modules/stm32-gdbtest на опубликованный f9d9f53.
  CMake, consumer, CLI и experiments используют его; проверенные дубли ядра,
  host tests/fixtures и одноразовые export-шаблоны удалены из родительского проекта.
- tools/gdbtest.py — CLI приложения; tools/test_module_host.py выполняет host44
  в отдельных build-копиях без записи в подмодуль. После обновления нужен configure.
- Три MCU build/offline PASS; F411/OpenOCD24/24 и F103/J-Link24/24, read-only
  consumer3/3/timeout/recovery/restore PASS. F411 live Sleep29/30,tick+1384ms.
  Подмодуль чистый, основные прошивки работают. Релизный тег пока не создан.

- Создана новая локальная история stm32-gdbtest в build/module-ready/stm32-gdbtest:
  один initial commit f9d9f53, main, origin на созданный владельцем GitHub remote.
  Runtime совпадает с проверенным снимком; README уточняет URL. Push ожидается
  от владельца; submodule/gitlink и релизные теги пока не создавались.

- Подготовлен состав отдельного Git-модуля: distribution/stm32-gdbtest с README,
  CHANGELOG, TODO, AGENTS и инструкциями автору тестов/версионированием; MIT сохранена.
- Host-тесты отделены от рабочих MCU-профилей через Tests/fixtures. Export tool
  формирует новый снимок внутри build без Git init/network/push. Автономные host44,
  минимальный consumer build/offline2/2, hashes/LICENSE/doc links PASS.
- Согласован новый initial history и основной способ Git submodule; план MODULE_SPLIT_PLAN.md.
  Предложены v0.1.0-rc.1 → v0.1.0, теги пока не созданы. Внешний host-контроллер
  питания/кнопок/приборов отложен в TODO с синхронизацией и reconnect.

- Namespace hwtest перенесён в stm32_gdbtest: imports, CLI python -m stm32_gdbtest,
  STM32GDBTest.cmake/stm32_gdbtest_attach и префикс STM32_GDBTEST_. Версия
  исходного прототипа0.1.0.dev0/API_VERSION1; API/миграция описаны в STM32_GDBTEST_API.md.
  Старые aliases отсутствуют; старые stand/identity env вызывают явный отказ.
- Сохранены schemas/ID/пресеты/каталоги отчётов и mutex namespace. Три MCU build/offline
  PASS, host44 PASS; F411/OpenOCD и F103/J-Link24/24, read-only consumer3/3,
  timeout/recovery/restore PASS. C/C++ firmware не менялась. Упаковка ещё впереди.

- Межпроектный Windows mutex для отладчика в одной Windows-сессии; ST-Link общий
  для OpenOCD/ST server, J-Link отдельный. Занятость/WAIT_ABANDONED дают ERROR
  до подключения; legacy lock сохранён. Observe_sleep использует тот же механизм.
- Host41 PASS с реальными конкурирующими процессами; F411 read-only consumer
  CTest3/3 + recovery/restore/Sleep PASS, F103/J-Link BOOT/BLINK PASS.
  Границы защиты и аварийных дочерних серверов: DEBUGGER_OWNERSHIP.md.

- Проверены перенесённые исходники модуля/потребителя в путях с пробелами под
  Windows ACL Deny Write/Delete: build/offline, CTest3/3 и HW timeout/recovery PASS.
  Добавлен check_readonly_consumer.ps1; lifecycle experiment принимает пути копий
  и опцию CTest. ACL и основная прошивка восстановлены, HW_BOOT/HW_BLINK PASS.

- Минимальный consumer аппаратно проверен на F411CE/ST-Link/OpenOCD: Flash,
  verify-only, намеренный Python timeout и host recovery, повторный PASS.
  Добавлен воспроизводимый check_consumer_lifecycle.py с восстановлением основной
  прошивки в finally; HW_BOOT/HW_BLINK/live Sleep PASS. Отчёт CONSUMER_VALIDATION.md.

- Согласовано рабочее имя stm32-gdbtest; добавлен самостоятельный minimal-consumer
  без stm32-cmake-yml (собственные firmware/profile/tests). Build и 2/2 offline CTest PASS.
- CMake/runner разделяют корни модуля и потребителя; YAML необязателен для manifest,
  имя target независимо от ELF, stand выбирается потребителем, SELF_TESTS опционален.
- Три основных профиля: build/host и offline contract regression PASS; 37 unittest.
  Аппаратных запусков в этом этапе нет; межпроектная блокировка пока не реализована.

- Проверки GPIO/RCC в трёх профилях переведены на HAL-предикаты и CMSIS-маски;
  добавлены ADC1/TIM2/DMA clock checks, TIM2 ARR через GET_AUTORELOAD.
- Offline macro contracts с явным source context, наличием и раскрытием в ELF;
  регрессия трёх профилей включает11 отрицательных вариантов. F411/OpenOCD
  и F103/J-Link 24/24 PASS; F401 для этих изменений пока только build/offline.
- HAL_MACRO_GUIDE.md: каталог Exported Macros, побочные эффекты и правила тестов.
  MODULE_EXTRACTION.md: границы и варианты имени будущего модуля, без переименования.

- F411CE/ST-Link: новая identity/Flash политика подтверждена аппаратно, OpenOCD
  и ST server strict 24/24 PASS, DEV_ID/Flash совпадают; live Sleep PASS.
- Отдельный опыт check_f411_macros.py подтвердил вычисление HAL-предикатов
  GPIOC/ADC1/SPI1 из ELF через GDB. Описаны контекст макросов, именованные маски
  и независимые проверки регистров; штатные сценарии пока не переписывались.

- Второй экземпляр F401CC: DEV_ID0x423/Flash256K, штатный OpenOCD 24/24 PASS.
  ST server/strict после USB-сбоя и переподключения также 24/24 PASS, live Sleep PASS.
  Неудачный прогон (9 ERROR до сервера) сохранён, результаты отделены от первой платы.

- BluePill F103C8/J-Link: новая identity/Flash политика проверена аппаратно,
  24/24 CTest PASS. DEV_ID0x410 совпадает, Flash-регистр сообщает 128 KiB при
  профиле64 KiB: warning без расширения linker. Strict boot PASS; после сервера
  Commander подтвердил работающий MCU/Sleep. См. docs/TARGET_IDENTITY.md.

- F401CC переведён на штатные presets: DEV_ID mismatch по умолчанию WARNING,
  выбранный профиль сохраняется. Общий strict через CLI/env, identity/warnings
  в JSON/JUnit; экспериментальный скрипт теперь только legacy-обёртка.
- Перед Flash проверяется 16-битный заводской размер памяти и граница профиля;
  адреса добавлены для F103/F401/F411. Неверный размер/переполнение остаются ERROR.
- F401CC: 24/24 CTest через OpenOCD и ST GDB Server на одном ELF, строгий отказ
  до Flash, live Sleep после ST detach. Host: 35 unittest, включая новую политику.
  Документация: docs/TARGET_IDENTITY.md.

### Fixed

- Удалены повторные setup()/loop() в USER CODE профиля f401cc. Второй setup
  приводил в Error_Handler при повторном запуске TIM2. На текущем экземпляре
  с маркировкой F401CC/DEV_ID0x431: 22/22 HW PASS через OpenOCD с явным override,
  два host CTest PASS, live Sleep PASS. ADC: 3,289 В / 27,1 °C; профиль и ожидания
  не ослаблены. Подробности: docs/F401_MARKING_EXPERIMENT.md.

### Added

- Эксперимент неизменённого f401cc на маркированном F401CC с DEV_ID0x431:
  отдельный скрипт с отмеченным runtime identity override; init ADC/DMA, TIM2, RTC PASS.
  Boot/clock дали timeout из-за двойного setup в main; стек подтвердил повторный
  запуск TIM2. См. docs/F401_MARKING_EXPERIMENT.md; стандартный профиль не ослаблен.

- Зафиксировано первое подключение предполагаемой F401CC: SWD доступен, но
  DEV_ID=0x431 при Flash 256 KiB не совпадает с профилем. Прошивка и HW-сценарии
  отложены; владелец подтвердил маркировку F401CC и те же регистры в CubeProgrammer.
  Описан план отдельной экспериментальной конфигурации; см. PROFILE_MIGRATION.md.

- Профиль f401cc: исправленная генерация владельца, User/Platform, требования,
  HAL-контракты, presets и SVD. Сборка и offline-проверки пройдены; HW ещё не проверен.
- PROFILE_MIGRATION.md: переименование f103/f401/f411/h503 в f103c8/f401cc/f411ce/h503cb,
  новые build/presets и отдельные ELF/задачи VS Code. Старые артефакты сохранены.

- F401_PROFILE_AUDIT.md: аудит пользовательского F401CC, отличия вариантов WeAct,
  исправления CubeMX и недостающие части интеграции; профиль пока не готов к HWTEST.

- F411: семь HAL-контрактов, собственный reviewed-source hash RCC, const-указатели
  в общем preflight; offline-регрессия F1/F4 включает отрицательный const-вариант.
- BlackPill/ST-Link: по 24/24 CTest через OpenOCD и ST GDB Server на одном ELF,
  ADC с заводской калибровкой, Sleep и timeout/recovery. Матрица и архитектура обновлены;
  добавлен пример локального стенда BlackPill/ST server.

- HWTEST_ARCHITECTURE_V2.md: фактические слои и запуск, конфигурация, матрица
  аппаратной проверки, ограничения, отличия от исходного замысла и ближайшие этапы.
  README ссылается на оба документа; исходная архитектура сохранена без изменений.

- Offline ELF/HAL preflight до запуска GDB-сервера: литеральные @case contracts,
  профильный JSON, сигнатуры/аргументы/поля/enum и reviewed-source hash для NULL.
  F103: семь сценариев, 80 проверок; шесть отрицательных вариантов в реальном GDB.
  Полная регрессия BluePill/J-Link 24/24 CTest; host-набор — 27 unittest.
  HAL_CONTRACTS.md описывает применение, C/C++ type context и границы доказательства.

- Build manifest schema 1 после линковки: ELF/profile SHA-256, зависимости Ninja,
  исходники/объекты, версии и хеши Cube/HAL/CMSIS/компилятора, выбранные compile flags.
  Раннер проверяет привязку до запуска сервера и сохраняет снимок в JSON/JUnit.
  Описаны ограничения post-link подхода и совместимость старых session.json.
  BluePill/J-Link: 24/24 CTest PASS; 23 host unittest, отказ устаревшего manifest
  до сервера и восстановление отсутствующего manifest через build проверены.

- Матрица F103/F411 × отладчик/backend и порядок ближайших этапов; правило
  объявления стенда перед каждым аппаратным набором и подтверждения переключений.

- J-Link GDB Server backend и пример локального стенда, явный USB serial/device,
  аппаратные точки без Flash breakpoints, команды setup/reset/finish и runtime firmware.
- BluePill/J-Link: 24/24 CTest PASS, запись и возврат образа, verify-only отказ,
  timeout/recovery. Commander после выхода подтвердил Sleep и продвижение uwTick.
- JLINK.md: запуск и анализ предоставленных VS Code/Commander примеров.

- Backend ST-LINK GDB Server: отдельный локальный TOML и команды запуска/reset/finish,
  persistent recovery, CubeProgrammer Flash verify и runtime version metadata.
- GDB_BACKENDS.md: настройка и сравнение серверов; общие сценарии BluePill дали
  24/24 CTest PASS на ST и OpenOCD. Проверены запись/возврат образа, отказ verify-only,
  внешний timeout/recovery и работа MCU после ST detach.

- Runtime compatibility schema 1 в JSON/JUnit: GDB/Python, OpenOCD, firmware/API
  ST-Link, источник сведений и явные отсутствующие значения.
- Проверка наличия обязательного GDB Python API перед подключением к MCU;
  host-регрессии отсутствующего API, частичного отчёта и исключения личных данных
  из извлекаемых токенов версии. BluePill: 24/24 CTest PASS; отрицательный
  опыт в реальном GDB подтвердил ERROR без подключения к MCU.
  Build-time HAL/CMSIS manifest добавлен следующим этапом (см. выше).

- Исходная генерация profiles/h503 для STM32H503CBT6 и предоставленный SVD.
  Профиль пока не включён в сборку и не проверен аппаратно.
- H503_CUBEMX.md: аудит IOC/Core, пошаговые настройки GPDMA, TIM2/RTC IRQ,
  RTC LSI prescalers и границы следующей интеграции.

- План будущего h503: уточнение MCU/платы, backend, CubeH5, ADC/GPDMA/TIM/RTC/PWR
  и последующее расширение периферии; профиль пока не включён в сборку.
- COMPATIBILITY.md: границы общего API, зависимости от HAL/CMSIS/GDB/backend,
  будущие manifest и preflight, правила адаптации сценариев и результатов.

- README описывает обе платы: WeAct BlackPill V3.1 / STM32F411CEU6 и WeAct BluePill V1.1 /
  STM32F103C8T6, проекты производителя, профили и разные выводы LED.
- Обычный Sleep/WFI в ожидании LED с активным SysTick; общие сценарии SysTick/TIM2 IRQ.
  На BluePill 24/24 CTest PASS, F411 собран; его новые сценарии ожидают аппаратного прогона.
- tools/observe_sleep.py: отдельное чтение DHCSR/SCR/uwTick/DBGMCU_CR без halt/reset/flash,
  JSON/лог внутри build. Sleep подтверждён; намеренный halt дал FAIL, после resume — PASS.

- Пересчёт ADC в VDDA (мВ) и температуру (м°C), с признаком INVALID/TYPICAL/FACTORY:
  типовые параметры F103, заводские точки F411, защита от нулевых/насыщенных отсчётов.
- Три новых аппаратных сценария: реальные величины, известные опорные точки,
  некорректные отсчёты и восстановление. На BluePill 22/22 CTest PASS.
- Native C++ проверки обеих формул, включая F411 interpolation/compensation и
  повреждённые калибровочные параметры; отдельный preset Tests/native, 1/1 PASS.

- Набор F103: 17 аппаратных сценариев и требования, presets f103-debug-hwtest,
  f103-check-hw/f103-hw и пример локального стенда. На BluePill 19/19 CTest PASS.
- Регрессия GDB-Python для неизвестного символа без подключения платы.


- Общий `User` для F411/F103 и адаптеры `Platform`: конечные ADC/DMA измерения,
  TIM2 IRQ, повторный RTC alarm с перевзводом в основном цикле; ADC-калибровка F1.
- Пять runtime/ошибочных сценариев BlackPill: DMA callback и публикация двух пар
  сырых значений, TIM2 IRQ, два RTC alarm, HAL_ERROR и потерянное DMA completion.
  Все 17 аппаратных тестов прошли; обе host-проверки прошли после исправления
  кодировки дополненного requirements.md. Debug F411/F103 собраны на GCC13.
- Руководство `docs/gdb.pdf` и предоставленные SVD F103/F411; отдельный `svdFile`
  в каждой конфигурации Cortex-Debug, без ручного переключения комментариев.

- Интегрирован обновлённый CubeMX-код F411/F103 с ADC/DMA/CRC/RTC/TIM.
- Три проверки конфигурации F411: последовательность ADC и DMA, TIM2, RTC;
  ожидания RCC обновлены под HCLK 8 МГц/APB1 8 МГц/APB2 2 МГц.
- Подключены необходимые HAL Ex-компоненты и сгенерированные startup/system/linker F103.
  Обе Debug-сборки прошли; на BlackPill 14/14 CTest PASS. F103 аппаратно не проверен.
- Каталоги профилей f411/f103: действующий F411 перенесён вместе с CubeMX-кодом и тестами;
  F103 подготовлен под пользовательский IOC, без заявления об аппаратной поддержке.
- target.toml и проверка схемы: Flash, DBGMCU ID, OpenOCD target, точки/ловушки,
  диагностика и reset-команды; проверка MCU до записи Flash.
- План ADC/DMA/TIM2/RTC/PWR/CRC, различия F1/F4 и пояснение роли -g3.
- Preset f103-debug, ранний отказ для неизвестного/неготового профиля и смены MCU в одном build.
- Практическая методика STM32_TESTING_METHODS: разбор BBC_SW_LLR, каталог способов,
  ограничения наблюдения/покрытия, журнал опытов и границы будущего общего модуля.
- Target API reach(when=...), fields и set_value; журнал инъекций set_value/force_return.
- Четыре аппаратных сценария: контракт GPIO, выбор повторного вызова, NULL-аргументы RCC.
  Совместный CTest-прогон 11/11; проверены неверное поле, недостижимое условие и неизвестный символ.
- Минимальный hwtest с отдельными слоями оркестратора, OpenOCD и GDB Target API.
- Пять аппаратных тестов CTest с ID требований, статическим AST-сбором и проверкой трассируемости.
- Presets debug-hwtest/check-hw/host, локальный TOML стенда, JSON и JUnit для каждого запуска.
- Проверка Flash по снимку ELF, автоматическая прошивка при несовпадении и режим verify-only.
- Host-тесты сбора метаданных, блокировки и отчётов; аппаратная проверка FAIL/ERROR,
  неожиданной остановки, таймаута во время исполнения и последующего восстановления.
- Аппаратный smoke-тест GDB-Python и Windows-раннер с блокировкой отладчика,
  таймаутом, восстановлением запуска платы, логами и JSON-результатами.
- Протокол успешной проверки BlackPill через STM32CubeProgrammer и OpenOCD;
  проверены несовпадение образа и аварийный таймаут.
- Подмодули stm32-cmake и stm32-cmake-yml с публичными URL и закреплёнными коммитами.
- Presets Debug/Release для GCC 13 и отдельные Debug-сборки для GCC 14/15.
- Правила работы агентов и дорожная карта; обязательное изучение исходного BOARD_TEST перед реализацией GDB-Python.
- Инструкция сборки и результаты проверки четырёх presets в README.

### Changed

- Русская терминология документации унифицирована: «отладчик»; английские API и TOML сохранены.
- План периферии актуализирован: оба текущих профиля существуют, Sleep F103 проверен;
  H503 отдельно обозначен как будущий и аппаратно непроверенный.

- 14 прежних и три новых сценария используют Tests/scenarios; MCU-ожидания
  остаются в profiles/<MCU>/Tests/expectations.py, специфичные init-проверки — в профилях.
  Формат @case и универсальный hwtest не менялись. Обе прошивки собраны;
  аппаратная проверка нового пересчёта F411 ожидает согласованной замены платы.

- Форматирование только User по .clang-format и навыку cpp-clang-format;
  проверено clang-format 23.1.1, семантика приложения сохранена.

- Файлы блокировки и временные артефакты размещаются внутри текущего проекта.
- Правила работы допускают самостоятельные локальные коммиты и слияния в main; push остаётся за пользователем.
- Базовая прошивка мигает PC13 без зависимости от semihosting.
- Настройки VS Code приведены к STM32F411 и OpenOCD/ST-Link.
- Конфигурация YAML сокращена до используемых параметров; закреплён STM32Cube F4 V1.28.3.

### Fixed

- LED подключённой WeAct F103 перенесён с PC13 на PB2 в IOC; точечно согласованы
  два define и тактирование GPIOB в generated коде, без форматирования/полной регенерации.
- Общие GPIO-сценарии получают порт, пин и выражение уровня из профиля; F411 остаётся PC13.
  На BluePill 22/22 CTest PASS; после закрытия GDB наблюдались running, рост SysTick/ADC
  и переключение PB2 в ODR/IDR без halt/reset. Пользователь подтвердил мигание LED.

- Пользовательский RTC IRQ/NVIC мост F103: текущая генерация CubeMX пропускает
  обработчик, хотя IRQ включён в IOC. Generated файлы не менялись.
- Target отвергает pending breakpoint сразу, вместо ожидания общего таймаута.

- Пути зависимостей теперь находятся внутри проекта.
- Удалены пользовательские syscall-заглушки с некорректными сигнатурами; выбрана библиотека NoSys.
- Явно выбран linker script F411 и устранено принудительное исключение библиотек C-runtime.
