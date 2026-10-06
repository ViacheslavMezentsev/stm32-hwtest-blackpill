# Архив HAL / HAL archive

Справочные исходники до перехода на CMSIS. Это не самостоятельный собираемый
проект после перемещения: пути старой сборки привязаны к прежнему корню.
Для воспроизведения используйте отдельный checkout коммита `314982a` основного
репозитория с его подмодулями. Современная HAL-регрессия и техники находятся
в stm32-gdbtest; текущий consumer использует src/ и hil/.

Historical sources, not a standalone build after relocation. To reproduce the
old environment, check out parent repository commit `314982a` with its submodules.
The active application uses src/ and hil/. Hardware results remain in docs/.
