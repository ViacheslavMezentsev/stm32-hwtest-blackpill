# Подготовка самостоятельного модуля

Статус: рабочее имя **stm32-gdbtest** согласовано владельцем. Проверен первый
проект-потребитель (build/offline и F411/ST-Link/OpenOCD lifecycle); пакет не опубликован. Python/CLI/CMake переведены на namespace stm32_gdbtest;
[API и миграция](STM32_GDBTEST_API.md), версия прототипа0.1.0.dev0. Это подготовка отделения, не завершённая поставка модуля.

## Функциональная граница

Модуль запускает проверки реальной прошивки через GDB-Python и выбранный сервер,
проверяет ELF-контракты, управляет временем/ресурсами и формирует JSON/JUnit.
В него входят runner, agent, Target API, backend adapters, contracts, отчёты и
тонкая интеграция CMake. Настройки MCU/платы и пользовательские сценарии остаются
в проекте-потребителе; интеграция stm32-cmake-yml не должна быть обязательной для
Python API. Сначала нужен минимальный проект-потребитель внутри текущего репозитория.

## Имя

Рабочее имя **stm32-gdbtest** отражает STM32 и запуск через GDB-Python.
Python остаётся механизмом реализации, отдельно удлинять название до gdbpy-test
не требуется. Имена текущей интеграции и будущей поставки:

| Поверхность | Состояние |
| --- | --- |
| Репозиторий / подмодуль | stm32-gdbtest / modules/stm32-gdbtest |
| Python distribution / import | stm32-gdbtest / stm32_gdbtest |
| CLI | python -m stm32_gdbtest; console executable при упаковке |
| CMake package / functions | STM32GDBTest / stm32_gdbtest_attach |
| Environment prefix | STM32_GDBTEST_ |

Предварительный веб-поиск точных строк stm32-gdbtest/mcu-gdbtest не дал надёжного
подтверждения занятости или свободы имён. **Уникальность не установлена**.
Перед публикацией проверить GitHub/GitLab, PyPI (включая нормализацию дефисов,
точек и подчёркиваний), похожие названия embedded test tools, CLI и CMake namespaces.
Повторить проверку перед публикацией; отсутствие результатов поиска не резервирует имя.

## Перед отделением

- Завершить и описать контракт параметров profile/stand/session и macro preflight.
- Build/offline, аппаратный lifecycle, перенос исходного дерева и read-only dependency проверены; межпроектное владение реализовано в одной Windows-сессии; закрепить публичный API.
- Namespace package/CLI/CMake перенесён; API и миграция описаны в STM32_GDBTEST_API.md.
- Закреплять модуль коммитом в Git submodule; тесты пользователя не хранить внутри зависимости.
- Опубликовать матрицу реально проверенных MCU/HAL/GDB/backend и ограничения Windows.

Рекомендации для авторов тестов: [HAL_MACRO_GUIDE](HAL_MACRO_GUIDE.md).

## Потребитель: фактический результат

[examples/minimal-consumer](../examples/minimal-consumer/README.md) — отдельный
CMake project с собственными C/startup/linker, target.toml, requirements, contract
registry, тестом и Python helper. STM32F411CE/CMSIS, без HAL и stm32-cmake-yml.
Зависимость подключается путём `STM32_GDBTEST_SOURCE_DIR`; сейчас путь ведёт в этот
checkout. Перенос исходного дерева в отдельный каталог внутри репозитория и работа с
Windows ACL read-only копией проверены. Установка пакета пока не проверялась.

- `stm32_gdbtest_attach(target PROFILE_DIR <absolute-path> [MANIFEST_INPUTS <files>]
  [SELF_TESTS])`: пути к коду модуля определяются от файла STM32GDBTest.cmake;
  `PROJECT_SOURCE_DIR` задаёт корень потребителя. Build должен быть внутри него.
- Профиль содержит target.toml и Tests/{board,requirements.md,contracts.json}.
  Manifest больше не требует YAML; если YAML есть, он учитывается. Дополнительные
  конфиги/linker нужно перечислять в MANIFEST_INPUTS для hash и relink dependency.
- Имя target передаётся manifest отдельно от имени ELF. Проектные helper доступны
  агенту из корня потребителя; импорт stm32_gdbtest сохраняет приоритет кода модуля.
- Session root определяет каталоги отчётов, temp, locks и cwd агента.
  Для старых sessions без root сохранён fallback на корень checkout модуля.
- Stand выбирается явно; прежний board-specific default остался в корневом
  CMake основного приложения. SELF_TESTS включает внутренние host-тесты модуля
  только для его разработки; потребителю они не навязываются.

Проверено: GCC13 build, manifest без YAML, различающиеся target/ELF names,
2/2 host CTest потребителя, импорт его теста/helper, положительный и отрицательный
macro preflight в GDB без подключения. Основные f103c8/f401cc/f411ce пересобраны:
на каждом 2/2 host CTest (37 unittest внутри host.hwtest), positive +11 negative
ELF regression. Это результаты первого build/offline этапа.

Следующий аппаратный этап завершён: consumer Flash/verify-only PASS, намеренный
Python timeout с host recovery, повтор PASS, восстановление основной прошивки и
HW_BOOT/HW_BLINK PASS. Наблюдаемых изменений файлов модуля/служебных каталогов
родителя при consumer-run нет. Подробности, SHA и ограничения доказательства:
[CONSUMER_VALIDATION](CONSUMER_VALIDATION.md).

## Что ещё мешает самостоятельной поставке

- Windows/Ninja и один firmware target, созданный в верхнем CMake-каталоге;
  несколько stm32_gdbtest_attach в одной сборке пока не поддерживаются.
- Manifest по-прежнему требует Cube package metadata и CMSIS/HAL version macros;
  произвольные vendor trees, object libraries и prebuilt библиотеки не покрыты.
- Межпроектное владение реализовано named mutex в одной Windows-сессии;
  legacy/external tools и аварийные дочерние серверы имеют ограничения,
  см. [DEBUGGER_OWNERSHIP](DEBUGGER_OWNERSHIP.md).
- Перенос исходного дерева и Windows ACL read-only режим подтверждены сборкой,
  CTest3/3 и HW/recovery. Git submodule/install workflow и другие среды ещё не проверены. Вспомогательные experiment/observe_sleep скрипты
  основного проекта ещё не являются переносимым API модуля.
- Затем выделить согласованный namespace, описать публичный API/versioning и
  подключение закреплённым подмодулем; выполнить повторную проверку имени перед публикацией.


Дополнительное доказательство отделимости: CMake/CLI/runner/GDB agent работают
из копии stm32_gdbtest в пути с пробелами при ACL Deny Write/Delete. Четыре контрольные
операции записи отклонены ОС; CTest3/3, timeout/recovery и восстановление приложения
прошли. [Полный протокол](CONSUMER_VALIDATION.md#перенос-и-read-only-dependency-следующий-опыт).
Общая блокировка теперь проверена на разных процессах/копиях и учитывает один
ST-Link при разных backend. Границы сессии и аварийного завершения описаны в
[DEBUGGER_OWNERSHIP](DEBUGGER_OWNERSHIP.md). Следующий этап — упаковка и отдельный состав поставки.


## Согласованное отделение

Основной вариант поставки — Git submodule с новой историей от проверенного снимка.
Шаг1 подготовлен: MIT, самостоятельные host fixtures, пример, README/CHANGELOG/TODO/AGENTS,
ручное и агентное написание тестов. [Пошаговый план](MODULE_SPLIT_PLAN.md).
Владелец следующим шагом создаёт пустой remote; до этого нет initial Git истории,
публикации, тега или gitlink. Кандидат версии: v0.1.0-rc.1 → v0.1.0.
