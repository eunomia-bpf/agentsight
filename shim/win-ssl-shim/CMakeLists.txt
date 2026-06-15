# Build the AgentSight Windows TLS shim (DLL + launcher).
#
# Requires Microsoft Detours. Easiest via vcpkg:
#   vcpkg install detours:x64-windows-static
#   cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=<vcpkg>/scripts/buildsystems/vcpkg.cmake
#   cmake --build build --config Release
cmake_minimum_required(VERSION 3.20)
project(agentsight_win_ssl_shim CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(detours CONFIG REQUIRED)

# The injected DLL.
add_library(ssl_shim SHARED ssl_shim.cpp boringssl_detect.cpp)
target_link_libraries(ssl_shim PRIVATE ${DETOURS_LIBRARY} detours::detours psapi)
target_include_directories(ssl_shim PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# The launcher/relay the Rust collector spawns.
add_executable(agentsight-ssl-shim injector.cpp)
target_link_libraries(agentsight-ssl-shim PRIVATE detours::detours)
target_include_directories(agentsight-ssl-shim PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
