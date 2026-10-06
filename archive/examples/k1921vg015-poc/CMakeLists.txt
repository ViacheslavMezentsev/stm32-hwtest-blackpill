cmake_minimum_required(VERSION 3.25)
project(k1921vg015_poc LANGUAGES C CXX ASM)
find_package(Python3 3.11 COMPONENTS Interpreter REQUIRED)
set(NIIET_DEVICE_DIR "$ENV{NIIET_DEVICE_DIR}" CACHE PATH "Read-only Device/K1921VG015 directory from reference SDK")
if(NOT EXISTS "${NIIET_DEVICE_DIR}/source/startup_k1921vg015.S")
    message(FATAL_ERROR "Set NIIET_DEVICE_DIR to the reference platform/Device/K1921VG015 directory")
endif()
add_executable(k1921-blink src/main.cpp
    "${NIIET_DEVICE_DIR}/source/plic.c"
    "${NIIET_DEVICE_DIR}/source/sys_init.c"
    "${NIIET_DEVICE_DIR}/source/mtimer.c"
    "${NIIET_DEVICE_DIR}/source/system_k1921vg015.c"
    "${NIIET_DEVICE_DIR}/source/startup_k1921vg015.S")
set_target_properties(k1921-blink PROPERTIES SUFFIX .elf C_STANDARD 17 CXX_STANDARD 17)
target_include_directories(k1921-blink PRIVATE "${NIIET_DEVICE_DIR}/include")
target_compile_definitions(k1921-blink PRIVATE HSECLK_VAL=16000000 SYSCLK_PLL)
# Match the reference ISA/ABI; no extra clock output on PC7 is needed for blink.
set(arch -march=rv32imfc_zba_zbb_zbc_zbs_zicsr -mabi=ilp32f)
target_compile_options(k1921-blink PRIVATE ${arch} -Og -g3 -mstrict-align
    -mno-save-restore -ffunction-sections -fdata-sections -fno-builtin -Wall
    "$<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions;-fno-rtti>")
target_link_options(k1921-blink PRIVATE ${arch} -nostartfiles --specs=nosys.specs
    --specs=nano.specs "-L${NIIET_DEVICE_DIR}/ldscripts" -Tk1921vg015_flash.ld
    -Wl,--gc-sections -Wl,--defsym=end=_end "-Wl,-Map=${CMAKE_BINARY_DIR}/k1921-blink.map")
set_property(TARGET k1921-blink APPEND PROPERTY LINK_DEPENDS
    "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_flash.ld"
    "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_common.lds"
    "${CMAKE_CURRENT_SOURCE_DIR}/snapshot.py")
add_custom_command(TARGET k1921-blink POST_BUILD
    COMMAND "${CMAKE_OBJCOPY}" -O binary "$<TARGET_FILE:k1921-blink>" "${CMAKE_BINARY_DIR}/k1921-blink.bin"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/snapshot.py"
        --elf "$<TARGET_FILE:k1921-blink>" --sdk "${NIIET_DEVICE_DIR}"
        --compiler "${CMAKE_C_COMPILER}" --objdump "${CMAKE_OBJDUMP}"
    BYPRODUCTS "${CMAKE_BINARY_DIR}/k1921-blink.bin" "${CMAKE_BINARY_DIR}/poc-manifest.json"
    VERBATIM)
