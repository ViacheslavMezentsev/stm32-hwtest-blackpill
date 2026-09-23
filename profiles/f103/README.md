# BluePill STM32F103C8T6 — проверенный профиль

IOC и сгенерированный код добавлены: `profiles/f103/stm32-hwtest-bluepill.ioc`.
MCU: STM32F103C8T6, документированные 64 KiB Flash и 20 KiB RAM.
Не рассчитываем на неофициальные дополнительные 64 KiB.

В CubeMX выберите Project Location так, чтобы `Core/Src`, `Core/Inc` и IOC
оказались именно в этой папке. Имя проекта `stm32-hwtest-bluepill`, toolchain Makefile,
Keep User Code, генерация пар `.c/.h` для периферии. SWD оставить включённым.
Профиль ожидает Cube F1 V1.8.7; при другом пакете согласовать `cubefw_package` в YAML.

После генерации: `cmake --preset f103-debug`, `cmake --build --preset f103-debug`.
Сборка проверена на GCC13. Core/CMakeLists.txt подхватывает generated `.c`;
сгенерированные system/startup/linker подключены явно через YAML без дублирования.
Общий `../../User` подключён к main через USER CODE-секции. `Platform` содержит
калибровку ADC F1 и настройку RTC alarm. На BluePill прошли 20 аппаратных тестов
и две host-проверки (22/22 CTest), включая ADC/DMA, TIM2 IRQ и повторный RTC alarm.

`target.toml` проверен на подключённой плате (DBGMCU device ID 0x410).
`Tests/board` содержит отдельные F103-ожидания; F411-тесты автоматически не наследуются.
Не подключайте BluePill к F411 debug/hwtest preset.

Предлагаемые периферийные настройки: [план опытов](../../docs/PERIPHERAL_PLAN.md).

## Аппаратный запуск

Создайте `Tests/stands/bluepill.local.toml` по `bluepill.example.toml`, задайте
свой ST-Link и путь OpenOCD. Локальный файл не хранится в Git.

```powershell
cmake --preset f103-debug-hwtest
cmake --build --preset f103-check-hw
# Повторить без пересборки:
ctest --preset f103-hw
```

Отчёт: `build/f103-debug-hwtest/hwtest/ctest-junit.xml`.

## RTC и повторная генерация

В текущем IOC RTC Alarm IRQ включён, но CubeMX-код не содержит ни обработчика,
ни включения NVIC. Поэтому `Platform/platform.c` предоставляет
`RTC_Alarm_IRQHandler` и настройку NVIC. После новой генерации проверьте этот
разрыв: если CubeMX начнёт генерировать обработчик, удалите пользовательский
мост из Platform, чтобы избежать двух определений. Generated Core не редактировался.
Это рабочий адаптер приложения, не тестовая вставка.
