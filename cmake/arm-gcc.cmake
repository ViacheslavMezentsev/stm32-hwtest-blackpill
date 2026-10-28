# Toolchain GNU Arm Embedded (xPack) для Cortex-M4.
# Порядок поиска каталога (в нём bin/arm-none-eabi-gcc):
#   1. -DARM_TOOLCHAIN_ROOT=... или CMakeUserPresets.json;
#   2. переменная окружения ARM_TOOLCHAIN_ROOT;
#   3. xPack 14.2.1-1.1, затем 13.3.1-1.1 в %USERPROFILE% / $HOME / /opt;
#   4. arm-none-eabi-gcc из PATH.
# Найденный каталог запоминается в кэше сборки: после смены тулчейна выполните
# configure с --fresh (CMake Tools: «Delete Cache and Reconfigure»).
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
if(CMAKE_HOST_WIN32)
    set(tool_suffix .exe)
else()
    set(tool_suffix "")
endif()

if(NOT ARM_TOOLCHAIN_ROOT)
    if(DEFINED ENV{ARM_TOOLCHAIN_ROOT} AND NOT "$ENV{ARM_TOOLCHAIN_ROOT}" STREQUAL "")
        set(ARM_TOOLCHAIN_ROOT "$ENV{ARM_TOOLCHAIN_ROOT}")
    else()
        foreach(version 14.2.1-1.1 13.3.1-1.1)
            foreach(base "$ENV{USERPROFILE}" "$ENV{HOME}" "/opt")
                set(candidate "${base}/xpack-arm-none-eabi-gcc-${version}")
                if(NOT ARM_TOOLCHAIN_ROOT AND NOT "${base}" STREQUAL ""
                        AND EXISTS "${candidate}/bin/arm-none-eabi-gcc${tool_suffix}")
                    set(ARM_TOOLCHAIN_ROOT "${candidate}")
                endif()
            endforeach()
        endforeach()
        if(NOT ARM_TOOLCHAIN_ROOT)
            find_program(arm_gcc_in_path arm-none-eabi-gcc)
            if(arm_gcc_in_path)
                get_filename_component(arm_gcc_bin "${arm_gcc_in_path}" DIRECTORY)
                get_filename_component(ARM_TOOLCHAIN_ROOT "${arm_gcc_bin}" DIRECTORY)
            endif()
        endif()
    endif()
endif()
if(NOT ARM_TOOLCHAIN_ROOT)
    message(FATAL_ERROR "GNU Arm toolchain not found: set ARM_TOOLCHAIN_ROOT or put arm-none-eabi-gcc in PATH")
endif()
file(TO_CMAKE_PATH "${ARM_TOOLCHAIN_ROOT}" ARM_TOOLCHAIN_ROOT)
set(ARM_TOOLCHAIN_ROOT "${ARM_TOOLCHAIN_ROOT}" CACHE PATH "GNU Arm toolchain root (contains bin/)")
list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES ARM_TOOLCHAIN_ROOT)

set(CMAKE_C_COMPILER "${ARM_TOOLCHAIN_ROOT}/bin/arm-none-eabi-gcc${tool_suffix}")
set(CMAKE_CXX_COMPILER "${ARM_TOOLCHAIN_ROOT}/bin/arm-none-eabi-g++${tool_suffix}")
set(CMAKE_ASM_COMPILER "${CMAKE_C_COMPILER}")
