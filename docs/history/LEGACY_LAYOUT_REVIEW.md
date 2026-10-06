# Архив HAL: состав выполненного переноса

База: принятый коммит `314982a`. Перенос согласован владельцем и выполнен.
CMSIS-приложение обеих плат прошло аппаратную приёмку; сейчас оформляются
отдельные HIL presets и пользовательская документация. Старые файлы сохранены в legacy/hal; CI проверяет два CMSIS-профиля и native ADC.

## Перенос tracked-файлов без удаления истории

| Исходный путь | Путь архива | Tracked-файлов |
| --- | --- | --- |
| `User/` | `legacy/hal/User/` | 4 |
| `profiles/f030r8/` | `legacy/hal/profiles/f030r8/` | 34 |
| `profiles/f103c8/` | `legacy/hal/profiles/f103c8/` | 38 |
| `profiles/f401cc/` | `legacy/hal/profiles/f401cc/` | 38 |
| `profiles/f411ce/` | `legacy/hal/profiles/f411ce/` | 39 |
| `profiles/f429zi/` | `legacy/hal/profiles/f429zi/` | 36 |
| `tests/scenarios/` | `legacy/hal/tests/scenarios/` | 5 |
| `tests/native/` | `legacy/hal/tests/native/` | 3 |

Также перенесены прежние HAL `CMakeLists.txt`, `stm32_config.yml`
и таблица legacy presets в `legacy/hal/`. Архив является справочным: он не обещает
сборку после перемещения, поскольку многие пути были привязаны к корню проекта.
Для воспроизведения прежней сборки нужен отдельный checkout коммита `314982a`.
Относительные ссылки обновлены и проверены.
Native ADC-тест скопирован в hil/tests/native и подключён к src/adc_units.cpp;
его CTest включён в CI.

## Зависимости и CI

Из индекса и .gitmodules исключены gitlinks `modules/stm32-cmake` и `modules/stm32-cmake-yml`
с сохранением локальных checkout и истории Git.
Они не требуются CMSIS-сборке; `modules/stm32-gdbtest` остаётся закреплённым.
CI проверяет два CMSIS-профиля (Debug/Release/HIL), больше не
скачивает CubeF0/F1/F4 и yq и не запускает старую пяти-профильную HAL-матрицу.

## Не затрагивается

- `profiles/h503cb` (приостановлен владельцем).
- `examples/k1921vg015-poc`, `examples/k1921vg015-errata` и их протоколы.
- `docs/HWTEST_ARCHITECTURE.md`, HAL-методика и история аппаратных результатов.
- `build/`, `.work/`, локальные стенды, serial, ELF и аппаратные отчёты.
- Соседние репозитории и глобальные настройки Git.
