cmake_minimum_required(VERSION 3.10)
project(StressTest)

set(CMAKE_CXX_STANDARD 17)

# Set up the executable
add_executable(stress_test src/main.cpp)

# Set the output directory for the executable
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# Static linking (only on Linux)
if(UNIX AND NOT APPLE)
    set(CMAKE_EXE_LINKER_FLAGS "-static")
endif()
