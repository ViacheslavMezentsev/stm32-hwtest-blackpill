cmake_minimum_required(VERSION 3.25)
project(k1921vg015_errata LANGUAGES C CXX ASM)
find_package(Python3 3.11 COMPONENTS Interpreter REQUIRED)
set(NIIET_DEVICE_DIR "$ENV{NIIET_DEVICE_DIR}" CACHE PATH "Read-only Device/K1921VG015 directory from reference SDK")
if(NOT EXISTS "${NIIET_DEVICE_DIR}/source/startup_k1921vg015.S")
    message(FATAL_ERROR "Set NIIET_DEVICE_DIR to the reference platform/Device/K1921VG015 directory")
endif()
add_executable(k1921-errata main.cpp
    "${NIIET_DEVICE_DIR}/source/plic.c"
    "${NIIET_DEVICE_DIR}/source/sys_init.c"
    "${NIIET_DEVICE_DIR}/source/mtimer.c"
    "${NIIET_DEVICE_DIR}/source/system_k1921vg015.c"
    "${NIIET_DEVICE_DIR}/source/startup_k1921vg015.S")
set_target_properties(k1921-errata PROPERTIES SUFFIX .elf C_STANDARD 17 CXX_STANDARD 17)
target_include_directories(k1921-errata PRIVATE "${NIIET_DEVICE_DIR}/include")
target_compile_definitions(k1921-errata PRIVATE HSECLK_VAL=16000000 SYSCLK_PLL)
# Match the reference ISA/ABI; no extra clock output on PC7 is needed for blink.
set(RISCV_ARCH "rv32imfc_zba_zbb_zbc_zbs_zicsr" CACHE STRING "ISA selecting a compatible multilib")
set(arch -march=${RISCV_ARCH} -mabi=ilp32f)
target_compile_options(k1921-errata PRIVATE ${arch} -Og -g3 -mstrict-align
    -mno-save-restore -ffunction-sections -fdata-sections -fno-builtin -Wall
    "$<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions;-fno-rtti>")

option(FROM_CHARS_RODATA_RAM "Move all .rodata to initialized RAM" OFF)
set(experiment_linker k1921vg015_flash.ld)
if(FROM_CHARS_RODATA_RAM)
    # Derived scripts live only in this build directory; the reference SDK is read-only.
    file(READ "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_common.lds" common)
    string(REPLACE "*(.rodata) *(.rodata.*)" "" common "${common}")
    string(REPLACE "__DATA_BEGIN__ = .;" "__DATA_BEGIN__ = .;\n    *(.rodata .rodata.*)" common "${common}")
    file(WRITE "${CMAKE_BINARY_DIR}/ram-common.lds" "${common}")
    file(READ "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_flash.ld" flash)
    string(REPLACE "k1921vg015_common.lds" "${CMAKE_BINARY_DIR}/ram-common.lds" flash "${flash}")
    file(WRITE "${CMAKE_BINARY_DIR}/ram-flash.ld" "${flash}")
    set(experiment_linker "${CMAKE_BINARY_DIR}/ram-flash.ld")
endif()
target_link_options(k1921-errata PRIVATE ${arch} -nostartfiles --specs=nosys.specs
     "-L${NIIET_DEVICE_DIR}/ldscripts" "-T${experiment_linker}"
    -Wl,--gc-sections -Wl,--defsym=end=_end "-Wl,-Map=${CMAKE_BINARY_DIR}/k1921-errata.map")
set_property(TARGET k1921-errata APPEND PROPERTY LINK_DEPENDS
    "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_flash.ld"
    "${NIIET_DEVICE_DIR}/ldscripts/k1921vg015_common.lds"
    "${CMAKE_CURRENT_SOURCE_DIR}/snapshot.py")
add_custom_command(TARGET k1921-errata POST_BUILD
    COMMAND "${CMAKE_OBJCOPY}" -O binary "$<TARGET_FILE:k1921-errata>" "${CMAKE_BINARY_DIR}/k1921-errata.bin"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/snapshot.py"
        --elf "$<TARGET_FILE:k1921-errata>" --sdk "${NIIET_DEVICE_DIR}"
        --compiler "${CMAKE_C_COMPILER}" --objdump "${CMAKE_OBJDUMP}"
        --arch "${RISCV_ARCH}" --ram "${FROM_CHARS_RODATA_RAM}"
    BYPRODUCTS "${CMAKE_BINARY_DIR}/k1921-errata.bin" "${CMAKE_BINARY_DIR}/poc-manifest.json"
    VERBATIM)


option(CLOUDBEAR_FIX "Compile application with vendor errata workaround" OFF)
if(CLOUDBEAR_FIX)
  target_compile_options(k1921-errata PRIVATE -mfix-cloudbear-0001)
endif()
