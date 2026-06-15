# Links the eBPF-for-Windows libbpf surface (ebpfapi). Provide the NuGet
# `eBPF-for-Windows` include dir and lib dir via -DEBPF_INCLUDE / -DEBPF_LIB,
# or have them on the default search path.
add_executable(agentsight-ebpf-loader loader.cpp)
target_include_directories(agentsight-ebpf-loader PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    $ENV{EBPF_FOR_WINDOWS_INCLUDE})
if(DEFINED ENV{EBPF_FOR_WINDOWS_LIB})
    target_link_directories(agentsight-ebpf-loader PRIVATE $ENV{EBPF_FOR_WINDOWS_LIB})
endif()
target_link_libraries(agentsight-ebpf-loader PRIVATE ebpfapi)
