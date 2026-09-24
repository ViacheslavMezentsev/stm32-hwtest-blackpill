# Предварительные проверки ELF/HAL-контрактов

Описание механизма/schema перенесено в [stm32-gdbtest](../modules/stm32-gdbtest/docs/CONTRACTS.md).
Ниже — ожидания HAL конкретных профилей и история проверок; ранние числа тестов исторические.

Сценарий объявляет необходимые контракты литерально:

```python
@case("HW_RCC_OSC_NULL", labels=("rcc", "injection"), contracts=("rcc_osc_null",))
def rcc_osc_null(t):
    scenarios.rcc_osc_null(t, EXPECTED)
```

AST-сборщик читает имена без импорта тестового кода. Определения находятся в
`profiles/<MCU>/Tests/contracts.json`, schema 1. Заполнены F103C8/F401CC/F411CE: семь прежних
сценариев функций/типов плюс HW_CLOCK, HW_GPIO, HW_TIM2_INIT с макросами. Другие сценарии явно имеют `contracts.status=NOT_REQUESTED`.
Это статус метаданных, не новый результат теста: протокол остаётся PASS/FAIL/ERROR.

## NULL, ошибки и границы доказательства

Для RCC F1 проверен исходник HAL 1.1.10 из Cube F1 1.8.7: OscConfig/ClockConfig
проверяют NULL и возвращают HAL_ERROR до разыменования/assert. Его хеш закреплён
в двух NULL-контрактах. Изменение файла требует повторного анализа, даже если
версия HAL не изменилась. Не обновлять этот хеш механически ради зелёного теста.
Это выборочная ручная проверка исходника; она не доказывает семантику всех
транзитивных заголовков и effective macros. build manifest также имеет ограничения
post-link снимка, описанные в [COMPATIBILITY](COMPATIBILITY.md).

HAL_ERROR=1 проверяется как enum перед force_return; тело HAL при такой инъекции
по-прежнему пропускается. Проверка callback void/signature не доказывает его IRQ
маршрут. Наличие аргумента в DWARF не гарантирует доступное значение при остановке:
optimized-out, pending breakpoint и реальные предусловия проверяются далее в Target.
LTO/inlining, stripped ELF или другая HAL-сигнатура могут дать инфраструктурный
ERROR без аппаратной неисправности. Полная семантика макросов, регистры, ABI/размеры всех структур,
полная семантика HAL и остальные сценарии пока не покрыты этим preflight.

## Воспроизведение без платы

После сборки выбранного профиля:

```powershell
python -B Tests/experiments/check_contract_preflight.py --session build/f103c8-debug-hwtest/hwtest/session.json
python -B Tests/experiments/check_contract_preflight.py --session build/f411ce-debug-hwtest/hwtest/session.json
```

Скрипт использует GDB и ELF сессии; отчёты — build/contract-validation/<profile>. Проверяет
семь контрактов (80 проверок) и семь отрицательных вариантов: отсутствующий
символ, неверные return type/arity/argument name/field type/enum value и неверный const квалификатор адресуемого типа. Все
отрицательные варианты должны дать ERROR без подключения. Это отдельная
интеграционная проверка, не включённая автоматически в CTest host-набор.

На BluePill F103 + J-Link V8.32 полный аппаратный набор прошёл 24/24 CTest:
22 HW и 2 host (в host.hwtest — 27 unittest). Семь HW-сценариев имеют preflight PASS,
пятнадцать — NOT_REQUESTED; все завершились image_verified и reset_run.
После уточнения ordered arguments/type_context повторно прошли 7/7 затронутых HW-сценариев.
Отдельно настоящий раннер с копией профиля отклонил неверную сигнатуру до сервера,
а подменённый reviewed-source hash — до запуска GDB. MCU при этих отказах не затронут.
H503 и F411/J-Link ещё не проверены. F411/ST-Link проверен через OpenOCD и ST server; результаты ниже.


## Перенос на F411

Cube F4 V1.28.3 содержит HAL 1.8.5, CMSIS Device 2.6.11 и Core 5.6.
У RCC_OscConfig и RCC_ClockConfig аргумент — указатель на const-структуру,
в отличие от F1 HAL 1.1.10. Профиль F411 явно требует `const RCC_…TypeDef *`;
движок разрешает const через GDB Type.const(), не стирает квалификатор ради совпадения.
Отрицательный offline-тест намеренно добавляет const для F103 и удаляет для F411:
оба варианта должны дать ERROR. Неверное имя аргумента проверяется отдельно,
с сохранением ожидаемого типа выбранного профиля.

NULL-пути повторно изучены в исходнике F4: возврат HAL_ERROR до разыменования/assert.
F411 contracts.json содержит собственный reviewed-source hash. Сигнатуры остальных
пяти контрактов совпали; это проверено по ELF, а не выведено из сходства имён HAL.

## Макросы (расширение schema 1)

Контракт может содержать macros с context и expressions без секции functions.
Для type/field/enum контрактов контекст функции остаётся обязательным. Пример,
ограничения грамматики, семантика context и правила проверки:
[HAL_MACRO_GUIDE](HAL_MACRO_GUIDE.md). Раскрытия сохраняются в contracts.macros
рядом с checks; preflight не доказывает runtime значение или чистоту выражения.
Регрессия реального GDB: 11 отрицательных вариантов, в том числе четыре macro-варианта.
