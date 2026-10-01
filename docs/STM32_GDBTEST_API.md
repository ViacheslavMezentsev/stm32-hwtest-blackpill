# Подключение API stm32-gdbtest в стендовом проекте

Каноническое описание API, CLI, CMake и миграции находится в
[отдельном модуле](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/a0d6547ba83b7c911f8f3028cb064aeedd3e5a36/docs/ru/API.md).
Инструкция для человека и агента: [написание тестов](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/a0d6547ba83b7c911f8f3028cb064aeedd3e5a36/docs/ru/TEST_AUTHORING.md).

Здесь используется `tools/gdbtest.py`, который импортирует закреплённый подмодуль.
Проектные сценарии находятся в `tests/scenarios`, требования и контракты —
в `profiles/<MCU>/tests`. CMake подключает модуль после настройки firmware target.
Host-проверки выполняются через `tools/test_module_host.py` в копиях внутри build,
чтобы не создавать артефакты в зависимости. SELF_TESTS здесь не включается.

```powershell
python -B tools/gdbtest.py --version
python -B tools/gdbtest.py collect --tests profiles/f411ce/tests/board
python -B tools/test_module_host.py
```

Аппаратные команды и выбор стенда: [HWTEST](HWTEST.md).
Результаты отделения: [MODULE_SPLIT_PLAN](MODULE_SPLIT_PLAN.md).
