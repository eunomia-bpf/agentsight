# ETW file-open telemetry consumer.
add_executable(agentsight-file-etw file_etw.cpp)
target_include_directories(agentsight-file-etw PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(agentsight-file-etw PRIVATE tdh advapi32)
