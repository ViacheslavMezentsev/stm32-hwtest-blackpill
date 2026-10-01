# CI без оборудования

Workflow [Offline](../.github/workflows/offline.yml) собирает CMSIS-приложение
для F411CE и F401CC в Debug, Release и HIL. HIL включает отладочную информацию,
manifest и Python-сценарии. Сервер GDB и USB не используются.

Для каждой платы проверяются 14 prepare и traceability: всего 30 CTest.
Ещё один native CTest проверяет арифметику `src/adc_units.cpp` на ПК.
Итого **31 CTest и шесть firmware-сборок**. Пропущенные/отсутствующие тесты,
неуспешный JUnit или ошибка сборки приводят к неуспеху CI.
Результаты: `build/ci-reports/cmsis/`, ELF/HEX/BIN и HIL manifests сохраняются
артефактом workflow. Счётчик тестов не является покрытием кода.

Offline CTest по умолчанию использует два процесса. Переопределение:
`python -B ci/run_checks.py --prepare-jobs 1` (допустимы1/2/4). Это не
параллелизм аппаратных сценариев. `timings.json` сохраняет длительности стадий.
[Замеры, воспроизведение и ограничения](TEST_TIMING.md).

## Запуск

```powershell
python -B ci/run_checks.py
docker build --progress plain -f ci/docker/Dockerfile -t hwtest-ci .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" hwtest-ci
```

Локально нужны CMake 3.25+, Ninja, Python 3.11+, xPack Arm GCC с GDB-Python
и отдельный native C++ compiler (например, GCC/MinGW). Docker поставляет их
сам: [lock-файл](../ci/dependencies.lock.json) закрепляет GCC/CMake/Ninja и
Ubuntu digest. Cube/HAL и yq больше не загружаются. Пакеты apt не закреплены
snapshot-репозиторием; перечень сохраняется в `/opt/hwtest-ci/packages.txt`.
Сборка образа требует сети, запуск проверок — нет.

На Linux в CI передаются `--user "$(id -u):$(id -g)"` и HOME внутри build.
CI-runner очищает STM32_GDBTEST_/HWTEST_ переменные окружения и проверяет, что
session не выбирает стенд. Для hardware используйте HIL_* отдельно и явно
настройте local TOML. Emulation F4 пока не принята; prepare не запускает firmware.

Прежняя пяти-профильная HAL-матрица описана в
[исторической версии](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/blob/314982afd04a709e4b0de52b5a2ff2e79632a05e/docs/CI.md).
