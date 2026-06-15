// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// ssl_shim.dll -- AgentSight TLS-plaintext capture for Windows.
//
// eBPF-for-Windows has no uprobe, so the Linux uprobe-on-SSL_read/SSL_write
// technique (bpf/sslsniff.bpf.c) cannot be reproduced as eBPF. This DLL is the
// Windows analog: Microsoft Detours inline-hooks the same OpenSSL/BoringSSL
// functions at the same call boundary, giving the same plaintext. For each
// completed call it writes ONE JSONL line -- byte-for-byte the same shape
// bpf/sslsniff.c emits -- to a named pipe the launcher relays to stdout. The
// Rust collector's SSLFilter / HTTPParser / SSEProcessor consume it unchanged.
//
// Hooked: SSL_write, SSL_read, SSL_write_ex, SSL_read_ex (OpenSSL 1.1/3.x,
// BoringSSL). Resolution: dynamic (GetProcAddress on the loaded TLS module);
// static/stripped BoringSSL byte-pattern detection is wired via
// boringssl_find_patterns() (port of bpf/sslsniff.c's detector).
#include <windows.h>
#include <detours.h>
#include <string>
#include <cstdint>
#include "ssl_shim.h"
#include "json_util.h"

// ----- OpenSSL/BoringSSL function pointer types -----------------------------
typedef int (*ssl_rw_fn)(void* ssl, void* buf, int num);
typedef int (*ssl_rw_ex_fn)(void* ssl, void* buf, size_t num, size_t* readbytes);

static ssl_rw_fn    Real_SSL_read     = nullptr;
static ssl_rw_fn    Real_SSL_write    = nullptr;
static ssl_rw_ex_fn Real_SSL_read_ex  = nullptr;
static ssl_rw_ex_fn Real_SSL_write_ex = nullptr;

// ----- pipe transport (thread-safe) -----------------------------------------
static HANDLE           g_pipe = INVALID_HANDLE_VALUE;
static CRITICAL_SECTION g_lock;
static std::string      g_comm;     // process image base name (the "comm" field)
static LONGLONG         g_qpc_freq; // QueryPerformanceFrequency, for ns timestamps

static uint64_t now_ns() {
    LARGE_INTEGER c;
    QueryPerformanceCounter(&c);
    // monotonic ns; the collector's TimestampNormalizer maps to wall-clock.
    return static_cast<uint64_t>((c.QuadPart * 1000000000LL) / g_qpc_freq);
}

static void connect_pipe() {
    char name[256];
    DWORD n = GetEnvironmentVariableA(AS_SHIM_PIPE_ENV, name, sizeof(name));
    if (n == 0 || n >= sizeof(name)) return;
    // The launcher created the pipe server; wait briefly then open the client.
    WaitNamedPipeA(name, 2000);
    g_pipe = CreateFileA(name, GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
}

// Emit one record matching bpf/sslsniff.c's printf sequence exactly.
static void emit(int rw, const void* buf, int captured_len, int total_len) {
    if (g_pipe == INVALID_HANDLE_VALUE) return;

    static const char* rw_event[] = { "READ/RECV", "WRITE/SEND", "HANDSHAKE" };
    int cap = captured_len;
    if (cap < 0) cap = 0;
    if (cap > AS_MAX_BUF_SIZE) cap = AS_MAX_BUF_SIZE;

    std::string line;
    line.reserve(static_cast<size_t>(cap) + 256);
    line += "{";
    line += "\"function\":\""; line += rw_event[rw]; line += "\",";
    line += "\"timestamp_ns\":" + std::to_string(now_ns()) + ",";
    line += "\"comm\":\""; line += g_comm; line += "\",";
    line += "\"pid\":" + std::to_string(GetCurrentProcessId()) + ",";
    line += "\"len\":" + std::to_string(total_len) + ",";
    line += "\"buf_size\":" + std::to_string(cap) + ",";
    line += "\"uid\":0,";
    line += "\"tid\":" + std::to_string(GetCurrentThreadId()) + ",";
    line += "\"latency_ms\":0,";
    line += "\"is_handshake\":";
    line += (rw == AS_RW_HANDSHAKE) ? "true," : "false,";
    if (cap > 0) {
        line += "\"data\":";
        as_json::append_escaped_quoted(line, static_cast<const char*>(buf), cap);
        line += ",";
        line += (cap < total_len) ? "\"truncated\":true,\"bytes_lost\":"
                                        + std::to_string(total_len - cap)
                                  : "\"truncated\":false";
    } else {
        line += "\"data\":null,\"truncated\":false";
    }
    line += "}\n";

    EnterCriticalSection(&g_lock);
    DWORD written = 0;
    WriteFile(g_pipe, line.data(), static_cast<DWORD>(line.size()), &written, nullptr);
    LeaveCriticalSection(&g_lock);
}

// ----- detours --------------------------------------------------------------
static int Mine_SSL_read(void* ssl, void* buf, int num) {
    int ret = Real_SSL_read(ssl, buf, num);
    if (ret > 0) emit(AS_RW_READ, buf, ret, ret); // buf is filled on return
    return ret;
}
static int Mine_SSL_write(void* ssl, void* buf, int num) {
    int ret = Real_SSL_write(ssl, buf, num);
    if (ret > 0) emit(AS_RW_WRITE, buf, ret, num); // plaintext is in buf pre-call
    return ret;
}
static int Mine_SSL_read_ex(void* ssl, void* buf, size_t num, size_t* readbytes) {
    int ret = Real_SSL_read_ex(ssl, buf, num, readbytes);
    if (ret == 1 && readbytes && *readbytes > 0)
        emit(AS_RW_READ, buf, static_cast<int>(*readbytes), static_cast<int>(*readbytes));
    return ret;
}
static int Mine_SSL_write_ex(void* ssl, void* buf, size_t num, size_t* written) {
    int ret = Real_SSL_write_ex(ssl, buf, num, written);
    if (ret == 1 && written && *written > 0)
        emit(AS_RW_WRITE, buf, static_cast<int>(*written), static_cast<int>(num));
    return ret;
}

// Port of bpf/sslsniff.c BoringSSL byte-pattern detection for stripped static
// binaries. Returns base offsets into the main module for SSL_read/SSL_write;
// declared here, implemented in boringssl_detect.cpp. Returns false if absent.
extern bool boringssl_find_patterns(void* module_base, size_t module_size,
                                    void** ssl_read, void** ssl_write);

// Resolve SSL_* either dynamically (exported symbols) or via static pattern.
static void resolve_functions() {
    const char* mods[] = { "libssl-3.dll", "libssl-3-x64.dll", "libssl-1_1.dll",
                           "libssl-1_1-x64.dll", "ssleay32.dll", "libssl.dll" };
    HMODULE h = nullptr;
    for (const char* m : mods) {
        h = GetModuleHandleA(m);
        if (h) break;
    }
    if (h) {
        Real_SSL_read     = (ssl_rw_fn)GetProcAddress(h, "SSL_read");
        Real_SSL_write    = (ssl_rw_fn)GetProcAddress(h, "SSL_write");
        Real_SSL_read_ex  = (ssl_rw_ex_fn)GetProcAddress(h, "SSL_read_ex");
        Real_SSL_write_ex = (ssl_rw_ex_fn)GetProcAddress(h, "SSL_write_ex");
        return;
    }
    // Statically-linked / stripped (BoringSSL in Bun/Node/Claude): pattern scan
    // the main module, mirroring the Linux --binary-path fallback.
    HMODULE main = GetModuleHandleA(nullptr);
    if (main) {
        MODULEINFO mi{};
        if (GetModuleInformation(GetCurrentProcess(), main, &mi, sizeof(mi))) {
            void *rd = nullptr, *wr = nullptr;
            if (boringssl_find_patterns(main, mi.SizeOfImage, &rd, &wr)) {
                Real_SSL_read  = (ssl_rw_fn)rd;
                Real_SSL_write = (ssl_rw_fn)wr;
            }
        }
    }
}

static void attach_all() {
    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    if (Real_SSL_read)     DetourAttach(&(PVOID&)Real_SSL_read,     Mine_SSL_read);
    if (Real_SSL_write)    DetourAttach(&(PVOID&)Real_SSL_write,    Mine_SSL_write);
    if (Real_SSL_read_ex)  DetourAttach(&(PVOID&)Real_SSL_read_ex,  Mine_SSL_read_ex);
    if (Real_SSL_write_ex) DetourAttach(&(PVOID&)Real_SSL_write_ex, Mine_SSL_write_ex);
    DetourTransactionCommit();
}

static void detach_all() {
    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    if (Real_SSL_read)     DetourDetach(&(PVOID&)Real_SSL_read,     Mine_SSL_read);
    if (Real_SSL_write)    DetourDetach(&(PVOID&)Real_SSL_write,    Mine_SSL_write);
    if (Real_SSL_read_ex)  DetourDetach(&(PVOID&)Real_SSL_read_ex,  Mine_SSL_read_ex);
    if (Real_SSL_write_ex) DetourDetach(&(PVOID&)Real_SSL_write_ex, Mine_SSL_write_ex);
    DetourTransactionCommit();
}

static void capture_comm() {
    char path[MAX_PATH];
    DWORD n = GetModuleFileNameA(nullptr, path, sizeof(path));
    if (n == 0) { g_comm = "unknown"; return; }
    const char* base = path;
    for (DWORD i = 0; i < n; ++i) if (path[i] == '\\' || path[i] == '/') base = path + i + 1;
    g_comm = base; // e.g. "node.exe", "claude.exe"
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
    if (DetourIsHelperProcess()) return TRUE;
    switch (reason) {
        case DLL_PROCESS_ATTACH: {
            DetourRestoreAfterWith();
            DisableThreadLibraryCalls(hModule);
            InitializeCriticalSection(&g_lock);
            LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_qpc_freq = f.QuadPart;
            capture_comm();
            connect_pipe();
            resolve_functions();
            attach_all();
            break;
        }
        case DLL_PROCESS_DETACH:
            detach_all();
            if (g_pipe != INVALID_HANDLE_VALUE) CloseHandle(g_pipe);
            DeleteCriticalSection(&g_lock);
            break;
    }
    return TRUE;
}
