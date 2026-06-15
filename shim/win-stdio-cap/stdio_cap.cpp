// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// agentsight-stdio-cap.exe -- Windows stdio capture via ConPTY.
//
// eBPF-for-Windows has no syscall hooks, so the Linux `stdiocap` (tracepoints on
// read/write) has no eBPF path. The ConPTY pseudoconsole is the Windows analog:
// we launch the agent inside a pseudoconsole, observe everything it reads/writes,
// and tee it to the real console so the user's experience is unchanged. Each
// chunk is emitted as one JSONL line in the SAME shape `bpf/stdiocap.c` emits
// (direction/fd/data/...), on our stdout, which the collector consumes.
//
// Maps to AgentSight's `record -- <command>` model (handles must be set up before
// the child starts); attach-to-existing is not possible for stdio on Windows.
//
// Usage: agentsight-stdio-cap.exe -- <command> [args...]
#include <windows.h>
#include <string>
#include <thread>
#include <cstdio>
#include "../win-ssl-shim/json_util.h"

static HANDLE g_pty_in_w = INVALID_HANDLE_VALUE;  // we write -> child stdin
static HANDLE g_pty_out_r = INVALID_HANDLE_VALUE;  // we read  <- child stdout
static HANDLE g_conout = INVALID_HANDLE_VALUE;     // real console out (tee)
static HANDLE g_conin = INVALID_HANDLE_VALUE;      // real console in
static CRITICAL_SECTION g_emit_lock;
static LONGLONG g_qpc_freq;
static DWORD g_pid;

static uint64_t now_ns() {
    LARGE_INTEGER c; QueryPerformanceCounter(&c);
    return (uint64_t)((c.QuadPart * 1000000000LL) / g_qpc_freq);
}

// fd: 0 stdin, 1 stdout (we model ConPTY output as fd 1).
static void emit(bool is_read, int fd, const char* buf, int n) {
    std::string l;
    l.reserve((size_t)n + 192);
    l += "{";
    l += is_read ? "\"direction\":\"READ\"," : "\"direction\":\"WRITE\",";
    l += "\"timestamp_ns\":" + std::to_string(now_ns()) + ",";
    l += "\"comm\":\"stdio\",";
    l += "\"pid\":" + std::to_string(g_pid) + ",";
    l += "\"tid\":0,\"uid\":0,";
    l += "\"fd\":" + std::to_string(fd) + ",";
    l += is_read ? "\"fd_role\":\"stdin\"," : "\"fd_role\":\"stdout\",";
    l += "\"fd_target\":null,";
    l += "\"len\":" + std::to_string(n) + ",";
    l += "\"buf_size\":" + std::to_string(n) + ",";
    l += "\"latency_ms\":0,";
    l += "\"data\":";
    as_json::append_escaped_quoted(l, buf, (size_t)n);
    l += ",\"truncated\":false}\n";

    EnterCriticalSection(&g_emit_lock);
    fwrite(l.data(), 1, l.size(), stdout);
    fflush(stdout);
    LeaveCriticalSection(&g_emit_lock);
}

// Child output: capture (WRITE) + tee to the real console.
static void output_pump() {
    char buf[16384]; DWORD n = 0;
    while (ReadFile(g_pty_out_r, buf, sizeof(buf), &n, nullptr) && n > 0) {
        emit(/*is_read=*/false, /*fd=*/1, buf, (int)n);
        DWORD w = 0;
        WriteFile(g_conout, buf, n, &w, nullptr); // user still sees output
    }
}

// User keystrokes: capture (READ) + forward to the child's pty stdin.
static void input_pump() {
    char buf[4096]; DWORD n = 0;
    while (ReadFile(g_conin, buf, sizeof(buf), &n, nullptr) && n > 0) {
        emit(/*is_read=*/true, /*fd=*/0, buf, (int)n);
        DWORD w = 0;
        WriteFile(g_pty_in_w, buf, n, &w, nullptr);
    }
}

int main(int argc, char** argv) {
    std::string cmd;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--") {
            for (int j = i + 1; j < argc; ++j) { if (j > i + 1) cmd += ' '; cmd += argv[j]; }
            break;
        }
    }
    if (cmd.empty()) { fprintf(stderr, "usage: agentsight-stdio-cap -- <command>\n"); return 2; }

    InitializeCriticalSection(&g_emit_lock);
    LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_qpc_freq = f.QuadPart;
    g_conout = CreateFileA("CONOUT$", GENERIC_WRITE, FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
    g_conin  = CreateFileA("CONIN$",  GENERIC_READ,  FILE_SHARE_READ,  nullptr, OPEN_EXISTING, 0, nullptr);

    // Pipes: pty_in (we write child stdin), pty_out (we read child stdout).
    HANDLE in_r, out_w;
    if (!CreatePipe(&in_r, &g_pty_in_w, nullptr, 0)) { fprintf(stderr, "CreatePipe in failed\n"); return 1; }
    if (!CreatePipe(&g_pty_out_r, &out_w, nullptr, 0)) { fprintf(stderr, "CreatePipe out failed\n"); return 1; }

    HPCON hpc = nullptr;
    COORD size = { 120, 30 };
    if (CreatePseudoConsole(size, in_r, out_w, 0, &hpc) != S_OK) {
        fprintf(stderr, "CreatePseudoConsole failed (needs Win10 1809+)\n");
        return 1;
    }
    CloseHandle(in_r);
    CloseHandle(out_w);

    // Launch the command attached to the pseudoconsole.
    STARTUPINFOEXA si{}; si.StartupInfo.cb = sizeof(si);
    SIZE_T bytes = 0;
    InitializeProcThreadAttributeList(nullptr, 1, 0, &bytes);
    si.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, bytes);
    InitializeProcThreadAttributeList(si.lpAttributeList, 1, 0, &bytes);
    UpdateProcThreadAttribute(si.lpAttributeList, 0,
        PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE, hpc, sizeof(hpc), nullptr, nullptr);

    PROCESS_INFORMATION pi{};
    std::string mutable_cmd = cmd;
    if (!CreateProcessA(nullptr, &mutable_cmd[0], nullptr, nullptr, FALSE,
                        EXTENDED_STARTUPINFO_PRESENT, nullptr, nullptr,
                        &si.StartupInfo, &pi)) {
        fprintf(stderr, "CreateProcess failed (err=%lu)\n", GetLastError());
        return 1;
    }
    g_pid = pi.dwProcessId;

    std::thread out_t(output_pump);
    std::thread in_t(input_pump);

    WaitForSingleObject(pi.hProcess, INFINITE);

    // Child gone: closing the pty drains the output pump.
    ClosePseudoConsole(hpc);
    if (out_t.joinable()) out_t.join();
    // input pump is detached from process lifetime; let it die with the process.
    in_t.detach();

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return 0;
}
