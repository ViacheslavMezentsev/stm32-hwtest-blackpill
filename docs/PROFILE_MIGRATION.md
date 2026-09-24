# Имена MCU-профилей и готовность F401CC

## Переименование

| Было | Стало | MCU |
| --- | --- | --- |
| f103 | f103c8 | STM32F103C8T6 |
| f401 | f401cc | STM32F401CCU6 |
| f411 | f411ce | STM32F411CEU6 |
| h503 | h503cb | STM32H503CBT6 |

Имя обозначает вариант MCU; производитель, ревизия платы и pinout указываются
отдельно. Полный артикул MCU сохраняется в YAML/target.toml. H503CB только перенесён:
содержимое CubeMX сохранено, профиль по-прежнему отложен и не включён в CMake.

Изменены каталоги, YAML-ключи, target.toml name, Python imports, presets и актуальные
ссылки. Старые имена профилей/presets больше не принимаются. Build-папки и отчёты
прошлых запусков не переименованы и не удалены. Сохранён исходный документ архитектуры;
его пути исторические. Старые сессии с прежними путями не использовать для новых запусков.

Для F411CE прежние debug/release/debug-hwtest/check-hw получили префикс f411ce-.
Для F103C8 вместо f103- используется f103c8-. Примеры новых команд:

```powershell
cmake --preset f401cc-debug-hwtest
cmake --build --preset f401cc-debug-hwtest
ctest --test-dir build/f401cc-debug-hwtest -L host --output-on-failure
python -B Tests/experiments/check_contract_preflight.py --session build/f401cc-debug-hwtest/hwtest/session.json
```

Аналогично f411ce-debug-hwtest и f103c8-debug-hwtest. Аппаратные цели:
f401cc-check-hw, f411ce-check-hw, f103c8-check-hw — запускать только на объявленном стенде.
В VS Code каждой launch-конфигурации назначены собственный ELF, SVD и задачи
configure/build соответствующего профиля. Это исключает выбор чужого ELF через
активную CMake launch target. Работа UI VS Code отдельно не проверялась.

## F401CC: что подготовлено

WeAct BlackPill v3.0 с STM32F401CCU6: 256 KiB Flash, 64 KiB RAM. Пользователь
исправил IOC: PC13 output push-pull, Low, TIM2 NVIC/handler включены. Подключены
общий User и отдельный Platform; main вызывает setup/loop только в USER CODE.
Добавлены target.toml, 22 сценария/требования, семь HAL-контрактов и SVD.

Различия относительно F411CE сохранены:

- HCLK 8 MHz, APB1 4 MHz (TIM2 8 MHz), APB2 8 MHz; PSC=7999/ARR=99.
- Температурный канал ADC — **16**, VREFINT — 17; проверено препроцессором
  Cube F4 V1.28.3 для STM32F401xC. F411 использует физический канал 18.
- Калибровка: VREFINT 0x1FFF7A2A, TS_CAL1 0x1FFF7A2C, TS_CAL2 0x1FFF7A2E;
  [datasheet ST](https://www.st.com/resource/en/datasheet/stm32f401vc.pdf) задаёт 30/110°C, VDDA 3.3 V.
- DEV_ID 0x423 по [RM0368](https://www.st.com/resource/en/reference_manual/dm00096844-stm32f401xbc-and-stm32f401xde-advanced-armbased-32bit-mcus-stmicroelectronics.pdf).
  Код отличает F401xB/C от F411, но сам по себе не различает объём Flash B/C.
  Полный MCU задаётся владельцем; память нужно дополнительно сверить при подключении.

## Проверено без платы

Все три активных профиля собраны в новых build-папках на GCC 13.3.1:

| Профиль | Flash, байт | RAM с резервами, байт |
| --- | ---: | ---: |
| f401cc | 12224 | 1904 |
| f411ce | 12220 | 1904 |
| f103c8 | 12376 | 1840 |

На каждом профиле пройдены host.traceability/host.hwtest и offline-проверка семи
контрактов с семью отрицательными вариантами. F401CC содержит STM32F401xC,
начальный SP 0x20010000 и reset-вектор во Flash. Manifest создан для собственного ELF.
Это готовность к первому аппаратному прогону, **не аппаратный PASS**.
После переименования новые аппаратные прогоны F103/F411 ещё не выполнялись;
прежние результаты относятся к прежним сборкам.

stm32-cmake-yml остаётся закреплён на 3d4028e (0.9.2). Пользователь запросил обновление,
но две попытки fetch завершились сбросом соединения GitHub. Обновление не заявляется
выполненным: после восстановления связи проверить upstream, обновить gitlink и повторить
сборки. Для текущих профилей изучены CFG-PROFILES, CFG-SOURCES и E005 этой версии;
новые имена состоят из букв/цифр. Подмодуль локально не редактировался.

## Подключение

Можно заменить BlackPill F411 у ST-Link на BlackPill F401CC, сохранив SWDIO, SWCLK,
GND и корректное питание; питание выключить на время перестановки. BluePill/J-Link
можно оставить подключённой. После подтверждения владельца сначала сверить identity
и объём Flash, затем boot/GPIO, полный набор OpenOCD и далее ST server.
J-Link mapping F401CC пока не добавлен. H503CB остаётся отложенным.
