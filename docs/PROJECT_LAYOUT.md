# Дерево проекта после CMSIS-переноса

Активны два BlackPill MCU: F411CE/F401CC. Пакет структуры76d50b0 принят в main.
Репозиторий — потребитель stm32-gdbtest; ядро и общая матрица MCU развиваются отдельно.

| Путь | Назначение и статус |
| --- | --- |
| src/ | Активное CMSIS-приложение, собственные startup/platform и арифметика |
| cmsis/ | Неизменённые сторонние заголовки F4, licenses и source hashes |
| cmake/, ld/ | Toolchain, выбор BOARD, linker и опциональное HIL attach |
| hil/profiles/, hil/tests/board/ | Два MCU, общие14 сценариев и требования |
| hil/tests/native/ | Арифметика ADC на ПК, один CTest |
| hil/stands/ | Шаблоны и игнорируемые local TOML для новых HIL presets |
| modules/stm32-gdbtest/ | Единственный закреплённый Git-подмодуль |
| ci/, .github/ | Docker build/prepare, шесть сборок и31 CTest без MCU |
| .vscode/, resources/ | Задачи редактора и SVD; наличие SVD не означает активный профиль |
| legacy/hal/ | Справочный архив пяти HAL-профилей, User, сценариев и сборочных файлов |
| profiles/h503cb/ | Сохранённый CubeMX-проект STM32H503CBT6, вне presets/CI; развитие отложено |
| examples/ | Сохранены minimal-consumer, К1921 PoC и errata; не входят в текущую CI-матрицу |
| tests/ | Исторические experiments/gdb/bring-up и прежние stands; это не активные CMSIS-тесты |
| tools/gdbtest.py | Актуальный вход в CLI закреплённого модуля |
| tools/check_profile_offline.py, tools/hardware_smoke.py | Исторические HAL/offline и bring-up инструменты; не текущий CI |
| tools/observe_sleep.py | Отдельный опыт live Sleep, не штатный HIL case |
| tools/test_module_host.py | Отдельная host-регрессия ядра, не часть текущего consumer CI |
| docs/ | Текущие описания, методы и исторические протоколы |
| build/, .work/ | Игнорируемые сборки/доказательства и рабочий checkout модуля; не удалять без оценки |

`examples/` и `profiles/h503cb/` сохраняются по прямому решению владельца.
Папка profiles сейчас не определяет активную матрицу: её источник — hil/profiles
и presets. В текущей задаче эти сохранённые исходники не изменяются.

Старые локальные modules/stm32-cmake и modules/stm32-cmake-yml могут оставаться
на диске: gitlinks удалены, каталоги игнорируются и не нужны новой сборке.
Локальные Makefile, .mxproject, __pycache__ и private TOML тоже могут быть видны
на диске, но не являются частью активного дерева Git. Их здесь не очищаем.

Для HAL-воспроизведения нужен отдельный checkout314982a с его зависимостями:
перемещённый [архив](../legacy/hal/README.md) не обещает сборку на новом месте.
Не запускать старые CTest/session как текущую регрессию: пути и manifest связаны
с конкретной сборкой. [Артефакты](BUILD_ARTIFACTS.md), [текущий статус](STATUS.md),
[CI](CI.md), [запуск HIL](../hil/README.md).
