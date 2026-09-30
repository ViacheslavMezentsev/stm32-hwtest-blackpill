# Проверки без оборудования

Workflow [Offline](../.github/workflows/offline.yml) собирает пять активных
профилей и выполняет CTest с меткой `host`: host-тесты модуля в отдельной копии,
трассировку требований, проверку ELF/contracts и штатные `prepare.*`.
GDB-Python читает ELF, но сервер и MCU не запускаются. Это проверка подготовки
тестов, а не аппаратный PASS и не выполнение firmware в эмуляторе.

Первый слой: Debug, GCC 13.3.1-1.1, f030r8/f103c8/f401cc/f411ce/f429zi.
Ожидаются 20 CTest-тестов для F030 и по 25 для остальных (всего 120,
из них 105 prepare). Отсутствующий тест, пропуск CTest-теста или неверный
JUnit приводит к ошибке. Внутренние platform-specific skips host unittest
допустимы и видны в логе. H503 и эксперименты К1921 в матрицу не входят.

## Окружение и локальный запуск

Нужен Docker с Linux containers (linux/amd64). Из корня репозитория:

```powershell
git submodule update --init --recursive
docker build --progress plain -f ci/docker/Dockerfile -t hwtest-ci .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" hwtest-ci
```

Для одного профиля допишите после `hwtest-ci`:
`python3 -B ci/run_checks.py --profile f030r8`.
В Linux используйте дополнительно `--user "$(id -u):$(id -g)"` и
`-e HOME=/workspace/build/ci-reports`, как в workflow.
USB и Docker privileged не нужны; аппаратный стенд оставьте без изменений.

[Lock-файл](../ci/dependencies.lock.json) закрепляет digest Ubuntu 24.04,
SHA256 архивов GCC/CMake/Ninja/yq и коммиты CubeF0 1.11.6, F1 1.8.7,
F4 1.28.3. Пакеты apt берутся из Ubuntu repositories: их версии сохраняются
в образе `/opt/hwtest-ci/packages.txt`, но не закреплены snapshot-репозиторием.
Поэтому окружение ещё не является побитово воспроизводимым.
Установщик заимствован из stm32-cmake-yml; его MIT-лицензия сохранена рядом.
Сборка образа требует сети, выполнение проверок — нет.

Для CubeF1 явно закреплён HAL v1.1.10 (`77fbb30`): gitlink официального
CubeF1 1.8.7 (`fee494a`) включает более поздний `2d61b77`, добавляющий `const`
в RCC API. Установленный CubeMX-пакет с тем же номером использует прежние
сигнатуры. Сравнение всех файлов Inc/Src с HAL v1.1.10 показало только различия
окончаний строк; RCC source hash совпадает побайтово. Первоначальный CI правильно
отклонил новый RCC по reviewed-source контракту. Контракты и их hashes не менялись.

CI-presets изолированы в `build/ci-<profile>`; аппаратные build не используются.
Runner удаляет унаследованные HWTEST/STM32_GDBTEST overrides и требует пустой stand.
Отчёты — `build/ci-reports`: configure/build/CTest logs, JUnit и summary с хешем
ELF. Workflow сохраняет также ELF/HEX/BIN/MAP и каталог hwtest с manifest.
Имя GitHub artifact содержит SHA проекта; gitlink фиксирует ревизию модуля.
Host timeout увеличен до 120 секунд (CTest 150): Linux lifecycle-тесты включают
реальное ожидание истечения heartbeat, поэтому прежних 30 секунд недостаточно.

Перед land требуется полный успешный job `Offline / profiles` именно для
опубликованного SHA. Локальный Docker PASS не заменяет результат GitHub.
Release, GCC 14/15, format, native tests, проверка ссылок и emulator jobs — следующие
подэтапы; отсутствие этих jobs сейчас не означает, что они проверены.

## Что берём из QEMU и Renode в stm32-cmake-yml

Изучена ревизия `ab7a5648c8b89a7fd9999404d08072ee6b94959b`:
[workflow](https://github.com/ViacheslavMezentsev/stm32-cmake-yml/blob/ab7a5648c8b89a7fd9999404d08072ee6b94959b/.github/workflows/firmware.yml),
[QEMU runner](https://github.com/ViacheslavMezentsev/stm32-cmake-yml/blob/ab7a5648c8b89a7fd9999404d08072ee6b94959b/ci/run_qemu_smoke.py),
[Renode runner](https://github.com/ViacheslavMezentsev/stm32-cmake-yml/blob/ab7a5648c8b89a7fd9999404d08072ee6b94959b/ci/run_renode_smoke.py).

| Механизм | QEMU | Renode |
| --- | --- | --- |
| Запуск | ELF через `-kernel`, semihosting | ELF в минимальной платформе, semihosting UART |
| Результат | Маркеры, метаданные и exit code | Маркеры, guest exit через hook и отчёт |
| Модель | netduino2 / netduinoplus2 | CPU, NVIC/SysTick, память и ограниченные заглушки |
| Отрицательные случаи | failure, hang, повреждение CRC | Аналогичные проверки результата |
| GDB-сценарии | Не используются | Не используются |

Важное ограничение: F030-код в QEMU там выполняется на Cortex-M3 netduino2,
а в Renode используется Cortex-M0. Для F401/F411 QEMU использует модель F405.
Это startup smoke совместимого кода, не подтверждение точной эмуляции MCU.
Профиль F429 нашего стенда требует отдельного выбора и проверки модели.

Для следующего этапа полезны единый ELF с хешем для двух эмуляторов,
явная матрица ожидаемых запусков, таймаут и отрицательный контроль. Предлагаемый
порядок: один simulator-only startup/configuration образ, затем GDB-подключение
и ограниченный сценарий через stm32-gdbtest, после этого расширение матрицы.
HAL clock/ADC polling нельзя считать работающим поверх RAM-заглушек; нужно
явно определить точку остановки и обходы только для simulator build.
Semihosting и эти обходы должны отсутствовать в аппаратном ELF. Этот слой пока
не реализован; периферийные HW-сценарии остаются на физических платах.
