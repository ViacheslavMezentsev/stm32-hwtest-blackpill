# Выделение stm32-gdbtest: пошаговый переход

## Шаг1 — история подготовки (export tool и templates теперь в истории Git)

Новая история начинается с текущего проверенного снимка, без переноса промежуточной
Git-истории прототипа. Основной способ подключения — Git submodule. Публикация
Python-пакета остаётся дополнительным будущим способом, не условием отделения.

Состав экспортируется tools/prepare_module_export.py в новый каталог строго внутри
build; существующий каталог не перезаписывается. Runtime не меняется. В поставке:

- stm32_gdbtest: Python/CMake ядро;
- Tests/host и Tests/fixtures: автономная регрессия, без рабочей profiles основного проекта;
- examples/minimal-consumer, шаблон локального OpenOCD-стенда;
- README.md, CHANGELOG.md, TODO.md, AGENTS.md, API/TEST_AUTHORING/VERSIONING;
- LICENSE: точная копия существующей MIT License, Copyright2026 Viacheslav Mezentsev;
- SOURCE.md/EXPORT_MANIFEST.json: исходный commit, dirty-состояние и hashes файлов.

README/AGENTS и инструкции для человека/агента находятся в
[distribution/stm32-gdbtest](../modules/stm32-gdbtest/README.md). Fixtures —
синтетические/замороженные входные данные host-тестов; не HW-профили и не evidence HAL.
Рабочие MCU-профили, application User, HAL/CMSIS, Cube/toolchains, SVD, gdb.pdf,
локальные конфиги/serial, ELF/логи и Git metadata не экспортируются.

```powershell
python -B tools/prepare_module_export.py --out build/module-export/stm32-gdbtest
```

Это подготовка файлов, без git init/push/submodule add. Перед новым initial commit
повторить экспорт из чистого сохранённого main в новый каталог, проверить diff и
происхождение. Старый экспорт содержит dirty=true, поскольку подготовлен до коммита;
его manifest описывает реальные bytes, но не следует выдавать их за исходники HEAD.

Проверено в самостоятельной копии:44 host unittest PASS, CMake build и offline2/2
минимального F411 consumer PASS, hashes51 source files, MIT byte equality и local
Markdown links PASS. В основной рабочей копии host44 PASS. Стенды не использовались.
Экспорт не является аппаратно проверенным новым gitlink или готовым релизом.

## Шаг2 — действие владельца

Создать пустой репозиторий **stm32-gdbtest** в своём аккаунте. Не добавлять README,
LICENSE или .gitignore автоматически; файлы уже подготовлены. Сообщить URL.
Клонировать вне текущего workspace не требуется: дальнейшая локальная работа
остаётся внутри этого репозитория согласно ограничению владельца.

## Шаг3 — новая история

После получения URL сформировать свежий снимок, проверить его и создать initial
commit в отдельном локальном Git-репозитории внутри build. Задать remote origin;
предоставить владельцу точную команду push и рабочий каталог. Самостоятельно push
не выполнять. Не копировать историю текущего приложения. До публикации проверить
рабочее имя; его глобальная уникальность пока не заявляется.

## Шаг4 — настоящее подключение

После подтверждения push сверить remote commit, добавить modules/stm32-gdbtest,
зафиксировать gitlink. Перенести корневые include/пути/tests к новому размещению;
оставить проектные сценарии, MCU-профили и стенды в родительском репозитории.
Повторить host/build/offline, отрицательные сценарии и согласованный HW/recovery.
Только после этого удалить дубли исходного ядра. Новый submodule сам по себе
не доказывает работоспособность установки и требует повторной проверки.

## Версии

Предложение: MAJOR.MINOR.PATCH, теги **v0.1.0-rc.1 → v0.1.0**. После проверки
кандидата и стабильного подключения выпустить0.1.0. Пока остаётся0.1.0.dev0.
До1.0 PATCH — совместимые исправления, MINOR — возможности/изменения API с миграцией.
После1.0 несовместимый API увеличивает MAJOR. Released tags не перемещаются.
Это политика проекта на основе [SemVer2.0.0](https://semver.org/spec/v2.0.0.html);
[подробности](../modules/stm32-gdbtest/docs/VERSIONING.md).
Schema/API_VERSION независимы от release version; gitlink всегда фиксирует SHA.

Внешний host-контроллер оборудования отложен в TODO обоих проектов. Его драйверы
останутся у потребителя; будущий общий интерфейс должен обеспечить синхронизацию,
таймауты, cleanup и ожидаемый power-cycle/reconnect.


## Текущее состояние после создания remote

Владелец создал https://github.com/ViacheslavMezentsev/stm32-gdbtest;
ls-remote успешно завершился без refs (пустой remote на момент проверки).
В build/module-ready/stm32-gdbtest создан отдельный репозиторий с одним root commit
`f9d9f53`, веткой main и origin на указанный URL. Начальный снимок взят из чистого
2851520; runtime bytes сверены с проверенным export. Перед commit только README
получил фактический URL, его hash обновлён в EXPORT_MANIFEST с preparation note.
Никакого переноса старой истории, push, тега или gitlink ещё нет.

Каталог расположен в build, поэтому **не очищать build/module-ready до отправки
нового main**. Он игнорируется родительским Git и пока не имеет удалённой копии.
Git может запросить safe.directory из-за владельца каталога CodexSandboxOffline;
использовать точечное `git -c safe.directory=<absolute-module-path>` на время команды,
не менять глобальную конфигурацию. Следующий шаг: владелец push -u origin main из
этого отдельного репозитория; затем сверить SHA remote и перейти к шагу4.
Версия остаётся0.1.0.dev0, релизные теги не созданы. HW в этом этапе не использовался.


## Шаг4 — подключение выполнено

Remote main проверен: f9d9f53865cd02ecc2800912662fcb1bbd3fa3cd. Настроен настоящий
Git-подмодуль modules/stm32-gdbtest с публичным HTTPS origin; .gitmodules и gitlink
фиксируют зависимость. Основной CMake, consumer, scripts и GDB experiments используют
его исходники. Корневые дубли ядра, host tests/fixtures, distribution templates и
одноразовый export tool удалены после сравнения и проверки сборки. Их прежнее
содержимое остаётся в истории, новый исходный репозиторий — источник изменений ядра.

При configure не обновлять зависимость автоматически. После clone выполнять
`git submodule update --init --recursive`. Для CLI приложения: tools/gdbtest.py;
для внутренних host-тестов: tools/test_module_host.py (копия в build, modules не меняется).
Версия пока0.1.0.dev0; release tag будет отдельным следующим этапом, после публикации
проверенного gitlink в основном проекте.


Результаты перехода:44 host-теста в изолированных копиях PASS; f103c8/f401cc/f411ce
build и positive+11 negative ELF regression PASS. Минимальный consumer offline2/2;
read-only relocation из Git-подмодуля CTest3/3, timeout/recovery/restore PASS
(build/relocation validation/1a7eac91bda24bdba4bc807324f2acaf).
Полные F411/OpenOCD и F103/J-Link —24/24, оба reset_run. F411 observe_sleep без halt:
Sleep29/30,tick+1384ms (build/submodule-sleep). Подмодуль не изменён и не содержит
build-артефактов. На F401 в этом этапе только build/offline, платы не переключались.
Следующий шаг владельца — push main основного проекта с gitlink; затем подготовка
первого кандидата релиза в отдельном репозитории и обновление gitlink после его push.
