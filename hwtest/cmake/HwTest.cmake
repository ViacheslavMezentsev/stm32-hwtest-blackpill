include_guard(GLOBAL)

function(hwtest_register id timeout labels)
    add_test(NAME hw.${id}
        COMMAND "${Python3_EXECUTABLE}" "${HWTEST_ROOT}/hwtest/cli.py" run
            --session "${HWTEST_SESSION}" --test "${id}")
    # GDB deadline plus preparation, server startup, recovery and process cleanup.
    math(EXPR outer_timeout "${timeout} + 90")
    set_tests_properties(hw.${id} PROPERTIES TIMEOUT ${outer_timeout}
        LABELS "hw;${labels}" RESOURCE_LOCK stm32_swd)
endfunction()

function(hwtest_attach target)
    cmake_parse_arguments(HW "" "PROFILE_DIR" "" ${ARGN})
    if(NOT HW_PROFILE_DIR OR NOT EXISTS "${HW_PROFILE_DIR}/target.toml")
        message(FATAL_ERROR "hwtest_attach requires PROFILE_DIR with target.toml")
    endif()
    find_package(Python3 3.11 COMPONENTS Interpreter REQUIRED)
    set(HWTEST_ROOT "${PROJECT_SOURCE_DIR}")
    set(HWTEST_TESTS "${HW_PROFILE_DIR}/Tests/board")
    set(HWTEST_PROFILE "${HW_PROFILE_DIR}/target.toml")
    set(HWTEST_SESSION "${CMAKE_BINARY_DIR}/hwtest/session.json")
    if(NOT CMAKE_GENERATOR STREQUAL "Ninja")
        message(FATAL_ERROR "HWTEST build manifest currently requires Ninja")
    endif()
    set_property(TARGET ${target} PROPERTY EXPORT_COMPILE_COMMANDS ON)
    set(HWTEST_MANIFEST "${CMAKE_BINARY_DIR}/hwtest/build-manifest.json")
    set(manifest_script "${HWTEST_ROOT}/hwtest/build_manifest.py")
    file(GLOB manifest_ioc "${HW_PROFILE_DIR}/*.ioc")
    set_property(TARGET ${target} APPEND PROPERTY LINK_DEPENDS
        "${manifest_script}" "${HWTEST_PROFILE}" "${HWTEST_ROOT}/stm32_config.yml" ${manifest_ioc})
    add_custom_command(TARGET ${target} POST_BUILD
        COMMAND "${Python3_EXECUTABLE}" -B "${manifest_script}"
            --root "${HWTEST_ROOT}" --build "${CMAKE_BINARY_DIR}"
            --elf "$<TARGET_FILE:${target}>" --profile "${HWTEST_PROFILE}"
            --out "${HWTEST_MANIFEST}" --ninja "${CMAKE_MAKE_PROGRAM}"
        BYPRODUCTS "${HWTEST_MANIFEST}" VERBATIM)
    if(STM32_YML_PROFILE STREQUAL "f411")
        set(stand_name blackpill)
    else()
        set(stand_name bluepill)
    endif()
    set(HWTEST_STAND "${HWTEST_ROOT}/Tests/stands/${stand_name}.local.toml" CACHE FILEPATH "Local stand TOML")
    get_filename_component(compiler_bin "${CMAKE_C_COMPILER}" DIRECTORY)
    find_program(HWTEST_GDB NAMES arm-none-eabi-gdb-py3 arm-none-eabi-gdb
        HINTS "${compiler_bin}" REQUIRED)
    set(session "{}")
    foreach(key IN ITEMS elf gdb tests root out stand profile build_manifest)
        if(key STREQUAL "elf")
            set(value "$<TARGET_FILE:${target}>")
        elseif(key STREQUAL "gdb")
            set(value "${HWTEST_GDB}")
        elseif(key STREQUAL "tests")
            set(value "${HWTEST_TESTS}")
        elseif(key STREQUAL "root")
            set(value "${HWTEST_ROOT}")
        elseif(key STREQUAL "out")
            set(value "${CMAKE_BINARY_DIR}/hwtest/runs")
        elseif(key STREQUAL "profile")
            set(value "${HWTEST_PROFILE}")
        elseif(key STREQUAL "build_manifest")
            set(value "${HWTEST_MANIFEST}")
        else()
            set(value "${HWTEST_STAND}")
        endif()
        string(REPLACE "\\" "/" value "${value}")
        string(REPLACE "\"" "\\\"" value "${value}")
        string(JSON session SET "${session}" "${key}" "\"${value}\"")
    endforeach()
    file(GENERATE OUTPUT "${HWTEST_SESSION}" CONTENT "${session}\n")
    execute_process(COMMAND "${Python3_EXECUTABLE}" "${HWTEST_ROOT}/hwtest/cli.py" collect
        --tests "${HWTEST_TESTS}" --cmake "${CMAKE_BINARY_DIR}/hwtest/tests.cmake"
        RESULT_VARIABLE rc)
    if(NOT rc EQUAL 0)
        message(FATAL_ERROR "Hardware test collection failed")
    endif()
    include("${CMAKE_BINARY_DIR}/hwtest/tests.cmake")
    file(GLOB test_sources CONFIGURE_DEPENDS "${HWTEST_TESTS}/test_*.py")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${test_sources}
        "${HWTEST_ROOT}/hwtest/collect.py")
    add_test(NAME host.traceability COMMAND "${Python3_EXECUTABLE}" "${HWTEST_ROOT}/hwtest/cli.py"
        trace --tests "${HWTEST_TESTS}" --requirements "${HW_PROFILE_DIR}/Tests/requirements.md")
    add_test(NAME host.hwtest COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover
        -s "${HWTEST_ROOT}/Tests/host" -v)
    set_tests_properties(host.traceability host.hwtest PROPERTIES LABELS host TIMEOUT 30
        WORKING_DIRECTORY "${HWTEST_ROOT}" ENVIRONMENT "PYTHONDONTWRITEBYTECODE=1")
    add_custom_target(check-hw
        COMMAND "${CMAKE_CTEST_COMMAND}" --test-dir "${CMAKE_BINARY_DIR}" --output-on-failure
            --output-junit "${CMAKE_BINARY_DIR}/hwtest/ctest-junit.xml"
        DEPENDS ${target} USES_TERMINAL)
endfunction()
