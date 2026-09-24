# Минимальный потребитель HWTEST

Самостоятельный CMake-проект для STM32F411CEU6 / BlackPill с LED PC13.
Подключает исходный HWTEST через `STM32_GDBTEST_SOURCE_DIR`, без родительского CMake,
`stm32-cmake-yml`, YAML, общего User и сценариев основного приложения.
Модуль пока не опубликован; рабочее имя будущего модуля — **stm32-gdbtest**.

## Проверка без платы

В терминале из этого каталога:

```powershell
cmake --preset debug
cmake --build --preset debug
ctest --preset offline
```

Нужны Windows, CMake >=3.25 (presets schema6), Ninja, Python >=3.11, xPack GCC13
с GDB-Python и установленный CubeF4 V1.28.3. Значения `ARM_TOOLCHAIN_ROOT` и
`CUBE_F4_ROOT` по умолчанию вычисляются относительно USERPROFILE; другое размещение
задаётся через CMake cache / локальный CMakeUserPresets.json. Cube-пакет только читается.

`host.consumer_offline` проверяет post-link manifest двух translation units,
импорт собственного helper из корня потребителя, запрет выхода отчётов за корень,
наличие/раскрытие CMSIS-макросов в настоящем GDB и отрицательный вариант с
отсутствующим макросом. GDB-сервер не запускается. Логи: `build/offline`.
Имя CMake-target `consumer_app` намеренно отличается от `consumer-blink.elf`.

## Граница примера

Собственная прошивка содержит только GPIO blink с busy wait на reset HSI.
Startup минимален: core vectors, data/bss; периферийные IRQ и HAL не используются.
Задержка не является калиброванным временем. Test hooks в прошивке отсутствуют.
Тест `HW_CONSUMER_GPIO` проверяет clock/output mode при входе в `app_loop`.
Аппаратно проверено на F411CE + ST-Link/OpenOCD: Flash, verify-only, timeout/recovery
и повторный успешный тест. Основная прошивка восстановлена.
Результаты и команда воспроизведения: [CONSUMER_VALIDATION](../../docs/CONSUMER_VALIDATION.md).

Stand по умолчанию пустой. Для HW запуска нужно явно выбрать локальный
TOML через `--stand`, `STM32_GDBTEST_STAND` или CMake cache. Такой запуск может прошить
этот ELF вместо основного приложения; после проверки требуется восстановить его.
`ctest --preset offline` исключает HW; обычный CTest и `check-hw` включают его.
Обновлённые runner координируют доступ к одному отладчику между проектами
в одной Windows-сессии; второй запуск получает ERROR. Внешние vendor tools и
старые версии в других checkout не участвуют в этой блокировке.
См. [DEBUGGER_OWNERSHIP](../../docs/DEBUGGER_OWNERSHIP.md).

Границы CMake API, оставшиеся зависимости и план:
[MODULE_EXTRACTION](../../docs/MODULE_EXTRACTION.md).


Перенос исходников в отдельные каталоги с пробелами также проверен: сборка,
CTest3/3 и timeout/recovery работают при запрете записи в dependency через Windows
ACL. Воспроизведение из корня репозитория — Tests/experiments/check_readonly_consumer.ps1;
подробности и границы доказательства в CONSUMER_VALIDATION по ссылке выше.

Текущий namespace и контракт подключения: [STM32_GDBTEST_API](../../docs/STM32_GDBTEST_API.md).
После обновления повторить configure/build, старые HWTEST_* cache/env заменить по инструкции миграции.


В этом приложении STM32_GDBTEST_SOURCE_DIR теперь по умолчанию указывает на
../../modules/stm32-gdbtest. Для обновления старого cache: `cmake --preset debug -U STM32_GDBTEST_SOURCE_DIR`.
Подмодуль предварительно инициализировать; пример не обновляет его коммит автоматически.
