// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// agentsight-ssl-shim.exe -- launcher/relay for ssl_shim.dll.
//
// This is the binary the Rust collector spawns (it plays the role bpf/sslsniff
// plays on Linux): it injects ssl_shim.dll into the target, owns a named pipe
// the DLL streams JSONL to, and relays that JSONL to its own stdout. The Rust
// BinaryExecutor already knows how to read line-delimited JSON from a child's
// stdout, so nothing downstream changes.
//
// Usage:
//   agentsight-ssl-shim.exe --dll <ssl_shim.dll> -- <command> [args...]   (launch)
//   agentsight-ssl-shim.exe --dll <ssl_shim.dll> --pid <pid>              (attach)
#include <windows.h>
#include <detours.h>
#include <string>
#include <vector>
#include <cstdio>
#include "ssl_shim.h"

static void die(const char* msg) {
    fprintf(stderr, "[ssl-shim] %s (err=%lu)\n", msg, GetLastError());
    ExitProcess(1);
}

// Relay the pipe to stdout until the writer (child) closes it.
static void relay(HANDLE pipe) {
    char buf[65536];
    DWORD n = 0;
    while (ReadFile(pipe, buf, sizeof(buf), &n, nullptr) && n > 0) {
        fwrite(buf, 1, n, stdout);
        fflush(stdout);
    }
}

// Inject into an already-running process via remote LoadLibrary.
static bool inject_existing(DWORD pid, const char* dll) {
    HANDLE proc = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION |
                              PROCESS_VM_WRITE | PROCESS_QUERY_INFORMATION,
                              FALSE, pid);
    if (!proc) return false;
    size_t len = strlen(dll) + 1;
    void* remote = VirtualAllocEx(proc, nullptr, len, MEM_COMMIT, PAGE_READWRITE);
    if (!remote) { CloseHandle(proc); return false; }
    WriteProcessMemory(proc, remote, dll, len, nullptr);
    auto load = (LPTHREAD_START_ROUTINE)GetProcAddress(
        GetModuleHandleA("kernel32.dll"), "LoadLibraryA");
    HANDLE th = CreateRemoteThread(proc, nullptr, 0, load, remote, 0, nullptr);
    if (!th) { CloseHandle(proc); return false; }
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
    CloseHandle(proc);
    return true;
}

int main(int argc, char** argv) {
    std::string dll;
    DWORD attach_pid = 0;
    std::vector<std::string> cmd;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--dll" && i + 1 < argc) dll = argv[++i];
        else if (a == "--pid" && i + 1 < argc) attach_pid = (DWORD)atoi(argv[++i]);
        else if (a == "--") { for (int j = i + 1; j < argc; ++j) cmd.push_back(argv[j]); break; }
    }
    if (dll.empty()) die("missing --dll <ssl_shim.dll>");

    // Create the named pipe the DLL will connect to.
    char pipe_name[256];
    snprintf(pipe_name, sizeof(pipe_name),
             "\\\\.\\pipe\\agentsight-ssl-%lu", GetCurrentProcessId());
    HANDLE pipe = CreateNamedPipeA(
        pipe_name, PIPE_ACCESS_INBOUND, PIPE_TYPE_BYTE | PIPE_WAIT,
        1, 0, 1 << 20, 0, nullptr);
    if (pipe == INVALID_HANDLE_VALUE) die("CreateNamedPipe failed");
    SetEnvironmentVariableA(AS_SHIM_PIPE_ENV, pipe_name);

    if (attach_pid != 0) {
        if (!inject_existing(attach_pid, dll.c_str())) die("inject (attach) failed");
    } else if (!cmd.empty()) {
        std::string line;
        for (size_t i = 0; i < cmd.size(); ++i) { if (i) line += ' '; line += cmd[i]; }
        STARTUPINFOA si{}; si.cb = sizeof(si);
        PROCESS_INFORMATION pi{};
        const char* dlls[] = { dll.c_str() };
        if (!DetourCreateProcessWithDllExA(
                cmd[0].c_str(), line.empty() ? nullptr : &line[0],
                nullptr, nullptr, TRUE, CREATE_SUSPENDED, nullptr, nullptr,
                &si, &pi, dlls[0], nullptr))
            die("DetourCreateProcessWithDllEx failed");
        ResumeThread(pi.hThread);
        CloseHandle(pi.hThread);
    } else {
        die("need either --pid <pid> or -- <command>");
    }

    // Block until the DLL (in the target) opens its end, then relay to stdout.
    ConnectNamedPipe(pipe, nullptr);
    relay(pipe);
    CloseHandle(pipe);
    return 0;
}
