# Архив / Archive

Материалы периода, когда в этом репозитории развивался механизм, позже выделенный в
[stm32-gdbtest](https://github.com/ViacheslavMezentsev/stm32-gdbtest). Они сохранены для истории
и не входят в текущую сборку, CI и HIL-тесты; пути внутри них могут указывать на прежнюю структуру.

| Каталог | Содержимое |
| --- | --- |
| `legacy/hal/` | исходники и профили прошивки на HAL до перехода на CMSIS (воспроизведение — checkout `314982a`) |
| `examples/k1921vg015-*` | опыты переноса на RISC-V К1921ВГ015 (стенд разобран) |
| `examples/minimal-consumer/` | ранняя копия минимального потребителя; актуальная — в stm32-gdbtest |
| `profiles/h503cb/` | проект CubeMX для STM32H503 (не поддерживается модулем) |
| `tests/` | прежние стенды, проверки GDB и аппаратные опыты |
| `tools/` | прежние утилиты: точка входа CLI, опыты со сном и аппаратный smoke-тест |
| `resources/` | SVD для F103 и H503 |

Протоколы и планы того же периода — в [истории](../docs/history/README.md).

Material from the period when the mechanism later extracted into stm32-gdbtest was developed in this
repository. It is kept for history and is not part of the current build, CI or HIL tests.
