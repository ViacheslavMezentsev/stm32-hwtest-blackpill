cmake_minimum_required(VERSION 3.19)

# The profile YAML supplies the generated system/startup explicitly.
file(GLOB generated_sources CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/Src/*.c")
list(FILTER generated_sources EXCLUDE REGEX "/system_stm32f1xx\\.c$")
target_sources(${PROJECT_NAME} PRIVATE ${generated_sources})
target_include_directories(${PROJECT_NAME} PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/Inc")
