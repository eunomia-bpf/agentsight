# ConPTY stdio capture. Needs Windows 10 1809+ (CreatePseudoConsole).
add_executable(agentsight-stdio-cap stdio_cap.cpp)
target_include_directories(agentsight-stdio-cap PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
