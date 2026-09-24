# Идентификация MCU и размер Flash

HWTEST выполняет сценарии по явно выбранному профилю. DEV_ID, маркировка корпуса,
заводской размер Flash и название MCU в программе отладчика — отдельные признаки.
Расхождение не приводит к автоматической смене профиля, HAL, linker или ожиданий.

## Политика

По умолчанию `warn`: несовпадение DEV_ID выдаёт WARNING, затем тест продолжается.
`strict` завершает сценарий как ERROR до сравнения/записи Flash. Ошибка чтения
регистра остаётся ERROR в любом режиме. Выбор: CLI `--identity-policy`, затем
переменная `HWTEST_IDENTITY_POLICY`, затем `warn`. Пример строгого набора:

```powershell
$env:HWTEST_IDENTITY_POLICY = 'strict'
cmake --build --preset f401cc-check-hw
Remove-Item Env:HWTEST_IDENTITY_POLICY
```

JSON/JUnit сохраняют `identity` (policy, expected, observed, raw, mask, выбранные
MCU/профиль), `warnings` и `flash_capacity`. PASS остаётся результатом сценария;
он не означает совпадение identity. CLI печатает предупреждение независимо от
PASS/FAIL. CTest скрывает stdout успешных тестов по умолчанию: для просмотра
предупреждений в терминале используйте `ctest --preset f401cc-hw -V`; они также
доступны в JSON/JUnit и LastTest.log. При таймауте GDB итоговый отчёт агента может
отсутствовать; отсутствие identity в таком ERROR не означает её совпадение.

## Flash перед записью

В target.toml schema 1 добавлен `flash_size_address` — адрес 16-битного регистра
размера Flash в KiB: F103 — 0x1FFFF7E0, F401/F411 — 0x1FFF7A22 (CMSIS устройств).
Старый профиль можно прочитать, но аппаратный запуск без этого поля отклоняется
до записи. После изменения target.toml нужна пересборка для нового build manifest.

До чтения/программирования образа агент читает размер и требует:
`0 < image_bytes <= min(profile_bytes, observed_bytes)`. Нулевое значение,
0xFFFF, ошибка чтения либо превышение границы — ERROR независимо от warn/strict.
Если образ помещается, отличие размера от профиля даёт отдельное предупреждение.
Большая память не расширяет выбранный linker/profile автоматически.

Это интерпретация заводского регистра по выбранному профилю, не физическое
тестирование всей памяти. При неизвестном MCU адрес может оказаться неверным;
warning не доказывает совместимость карты памяти и периферии. Для нового семейства
нужно проверить документацию и адрес, а не переносить его по аналогии.
Имена F103C8/CB в программах сами по себе не определяют доступную память.

## F401CC — штатный профиль

Экземпляр с маркировкой STM32F401CCU6, DEV_ID0x431 и Flash256K используется с
обычным f401cc: expected остаётся 0x423, наблюдаемое значение не подменяется.

```powershell
cmake --preset f401cc-debug-hwtest
cmake --build --preset f401cc-debug-hwtest
$env:HWTEST_STAND = (Resolve-Path Tests/stands/blackpill.local.toml).Path
cmake --build --preset f401cc-check-hw
# Тот же ST-Link/SWD, другой backend:
$env:HWTEST_STAND = (Resolve-Path Tests/stands/blackpill-stlink.local.toml).Path
cmake --build --preset f401cc-check-hw
```

2026-09-24 оба backend дали **24/24 CTest** (22 HW + 2 host); 35 host unittest.
Все 44 HW-отчёта содержат mismatch WARNING и прочитанные 262144 байта Flash.
ELF SHA-256: `252199144197d81984866e60f4f1e4ba54127293ce7ba12f140fc72d90dd7696`.
ADC: 3291 mV; 27323 m°C (OpenOCD), 27009 m°C (ST server). Strict на том же стенде:
ожидаемый ERROR, flashed=false, reset_run. Host-проверки также покрывают нехватку
Flash, больший чип, неверный/нечитаемый размер, совпадение identity и JUnit warnings.
F103/F411 пересобраны и прошли host; аппаратных запусков на них в этом этапе нет.

История эксперимента: [F401_MARKING_EXPERIMENT](F401_MARKING_EXPERIMENT.md).
Старый скрипт теперь делегирует штатному runner без override и не нужен для presets.
observe_sleep также поддерживает warn/strict, но только наблюдает работу: он
не проверяет Flash и должен запускаться после успешного основного набора.
