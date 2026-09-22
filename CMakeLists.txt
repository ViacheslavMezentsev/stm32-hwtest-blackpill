cmake_minimum_required(VERSION 3.19)

set(STM32_YML_PROFILE f411 CACHE STRING "MCU profile: f411 or f103")
set_property(CACHE STM32_YML_PROFILE PROPERTY STRINGS f411 f103)
if(NOT STM32_YML_PROFILE MATCHES "^(f411|f103)$")
    message(FATAL_ERROR "Unknown MCU profile '${STM32_YML_PROFILE}'; choose f411 or f103")
endif()
if(DEFINED HWTEST_CONFIGURED_PROFILE AND NOT HWTEST_CONFIGURED_PROFILE STREQUAL STM32_YML_PROFILE)
    message(FATAL_ERROR "Use a separate build directory for each MCU profile")
endif()
set(HWTEST_CONFIGURED_PROFILE "${STM32_YML_PROFILE}" CACHE INTERNAL "Build directory MCU")
set(BOARD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/profiles/${STM32_YML_PROFILE}")
if(STM32_YML_PROFILE STREQUAL "f103" AND
   (NOT EXISTS "${BOARD_DIR}/stm32-hwtest-bluepill.ioc" OR NOT EXISTS "${BOARD_DIR}/Core/Src/main.c"))
    message(FATAL_ERROR "F103 awaits profiles/f103/stm32-hwtest-bluepill.ioc and CubeMX Core/Src/main.c; see profiles/f103/README.md")
endif()

# Используется набор скриптов для STM32: https://github.com/ObKo/stm32-cmake
set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/modules/stm32-cmake/cmake/stm32_gcc.cmake")

# Определяем путь к нашему фреймворку.
set(STM32_YML_FRAMEWORK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/modules/stm32-cmake-yml")

if(NOT EXISTS "${CMAKE_TOOLCHAIN_FILE}" OR NOT EXISTS "${STM32_YML_FRAMEWORK_DIR}/stm32_yml.cmake")
    message(FATAL_ERROR "Missing build submodules. Run: git submodule update --init --recursive")
endif()

# Добавляем путь к фреймворку в CMAKE_MODULE_PATH.
list(APPEND CMAKE_MODULE_PATH "${STM32_YML_FRAMEWORK_DIR}")

# Подключаем главный файл фреймворка.
include(stm32_yml)

# (Опционально) Если вы хотите использовать нестандартное имя для конфига.
#set(PROJECT_CONFIG_FILE "config.yml" CACHE STRING "..." FORCE)

# Вызываем подготовительную функцию.
# Она прочитает YAML и вернет нам имя проекта и список языков.
stm32_yml_prepare_project_data(PROJECT_NAME PROJECT_LANGUAGES)

project(${PROJECT_NAME} LANGUAGES ${PROJECT_LANGUAGES})

# Вызываем основную функцию настройки.
stm32_yml_setup_project(${PROJECT_NAME})

option(ENABLE_HW_TESTING "Enable selected profile hardware tests" OFF)
if(ENABLE_HW_TESTING)
    enable_testing()
    include(hwtest/cmake/HwTest.cmake)
    hwtest_attach(${PROJECT_NAME} PROFILE_DIR "${BOARD_DIR}")
endif()
