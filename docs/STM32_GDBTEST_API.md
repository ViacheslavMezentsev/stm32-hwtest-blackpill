# Подключение API stm32-gdbtest в стендовом проекте

Каноническое описание API, CLI, CMake и миграции находится в
[отдельном модуле](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/API.md).
Инструкция для человека и агента: [написание тестов](https://github.com/ViacheslavMezentsev/stm32-gdbtest/blob/b76d909f903df513156019a32479c5e3c2b2e0c3/docs/TEST_AUTHORING.md).

Здесь используется `tools/gdbtest.py`, который импортирует закреплённый подмодуль.
Проектные сценарии находятся в `Tests/scenarios`, требования и контракты —
в `profiles/<MCU>/Tests`. CMake подключает модуль после настройки firmware target.
Host-проверки выполняются через `tools/test_module_host.py` в копиях внутри build,
чтобы не создавать артефакты в зависимости. SELF_TESTS здесь не включается.

```powershell
python -B tools/gdbtest.py --version
python -B tools/gdbtest.py collect --tests profiles/f411ce/Tests/board
python -B tools/test_module_host.py
```

Аппаратные команды и выбор стенда: [HWTEST](HWTEST.md).
Результаты отделения: [MODULE_SPLIT_PLAN](MODULE_SPLIT_PLAN.md).
