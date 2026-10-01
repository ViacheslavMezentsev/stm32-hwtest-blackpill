# Текущее состояние стендового проекта

Срез: 2026-10-02. [Назначение проекта](../README.md).

## CMSIS consumer F411CE/F401CC

Пакет `314982a` принят в main после полного CI (154 CTest).
Обе платы прошли 14 HW-сценариев, повторы после инъекций и timeout/recovery;
[протокол](BLACKPILL_CMSIS_APPLICATION.md). В принятом пакете76d50b0 добавлены
отдельные Debug/Release/HIL presets и README RU/EN. Загружаемый HIL-образ каждого
MCU побайтово совпадает с сохранённой аппаратно проверенной прошивкой.
HAL-исходники перенесены в legacy/hal, build-зависимости исключены из gitlinks:
[состав архива](LEGACY_LAYOUT_REVIEW.md). Новый CI: шесть CMSIS-сборок и 31 CTest,
включая native ADC. Windows и новый Docker/Linux прошли (шесть сборок и 31 CTest
в каждой среде). [Полный CI76d50b0](https://github.com/ViacheslavMezentsev/stm32-hwtest-blackpill/actions/runs/36909298172)
завершён SUCCESS, пакет включён в main.
Загружаемые образы совпадают с аппаратно принятыми, новые HW-запуски не выполнялись.
VS Code JSON/SVD/пути проверены по конфигурации; интерактивный запуск редактора не проверялся.

## Измерение времени

Рабочий пакет после f4b7d75: offline CI j=2, Windows/Linux31 CTest PASS;
F401CC/ST-Link/OpenOCD14/14 за38,177с, финальный GPIO PASS, оставлена CMSIS firmware.
HW lifecycle не оптимизирован; [замеры и границы](TEST_TIMING.md).
Опубликованный CI нового пакета ещё не проверен.

## Сохранённые материалы

examples/ и profiles/h503cb/ остаются вне активной матрицы по решению владельца.
Назначение прочих каталогов — [карта дерева](PROJECT_LAYOUT.md).

[История состояния и прежних проверок](STATUS_HISTORY.md) сохранена отдельно.
