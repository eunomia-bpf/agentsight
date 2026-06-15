# Top-level build for AgentSight's Windows native producers.
#   cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=<vcpkg>/scripts/buildsystems/vcpkg.cmake
#   cmake --build build --config Release
cmake_minimum_required(VERSION 3.20)
project(agentsight_win_shims CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(win-ssl-shim)      # Detours TLS plaintext (uprobe replacement)
add_subdirectory(win-ebpf-loader)   # loads bpf/windows/*.o, emits process/net JSONL
add_subdirectory(win-stdio-cap)     # ConPTY stdio capture
add_subdirectory(win-file-etw)      # ETW file-open telemetry
