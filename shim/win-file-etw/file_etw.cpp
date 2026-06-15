// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// agentsight-file-etw.exe -- file-open telemetry via ETW.
//
// The Linux `process` program tracks file opens with sys_enter_openat
// tracepoints. eBPF-for-Windows has no syscall hooks, so this uses the
// Microsoft-Windows-Kernel-File ETW provider instead -- a real-time consumer
// that emits the SAME FILE_OPEN JSONL `bpf/process.c` emits
// ({"timestamp":..,"event":"FILE_OPEN","comm":..,"pid":..,"filepath":..,"flags":..}).
//
// Links tdh.lib, advapi32.lib.
// Usage: agentsight-file-etw.exe [--pid <pid>]   (admin required for ETW)
#include <windows.h>
#include <evntrace.h>
#include <evntcons.h>
#include <tdh.h>
#include <string>
#include <vector>
#include <cstdio>

#pragma comment(lib, "tdh.lib")
#pragma comment(lib, "advapi32.lib")

// Microsoft-Windows-Kernel-File provider GUID and the "Create" event id.
static const GUID KERNEL_FILE_PROVIDER =
    { 0xedd08927, 0x9cc4, 0x4e65, { 0xb9, 0x70, 0xc2, 0x56, 0x0f, 0xb5, 0xc2, 0x89 } };
static const USHORT EVENT_KERNEL_FILE_CREATE = 12; // NameCreate / Create

static TRACEHANDLE g_session = 0;
static std::wstring g_session_name = L"AgentSightFileTrace";
static DWORD g_filter_pid = 0;

static std::string narrow(const wchar_t* w) {
    if (!w) return {};
    int n = WideCharToMultiByte(CP_UTF8, 0, w, -1, nullptr, 0, nullptr, nullptr);
    std::string s(n > 0 ? n - 1 : 0, '\0');
    if (n > 0) WideCharToMultiByte(CP_UTF8, 0, w, -1, &s[0], n, nullptr, nullptr);
    return s;
}

static void emit_escaped(std::string& out, const std::string& s) {
    static const char hex[] = "0123456789abcdef";
    for (unsigned char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            default:
                if (c < 0x20) { out += "\\u00"; out += hex[c>>4]; out += hex[c&0xf]; }
                else out += (char)c;
        }
    }
}

// Pull a single string property out of an event via TDH.
static std::wstring get_string_prop(PEVENT_RECORD ev, const wchar_t* name) {
    PROPERTY_DATA_DESCRIPTOR desc{};
    desc.PropertyName = (ULONGLONG)name;
    desc.ArrayIndex = ULONG_MAX;
    ULONG size = 0;
    if (TdhGetPropertySize(ev, 0, nullptr, 1, &desc, &size) != ERROR_SUCCESS || size == 0)
        return {};
    std::vector<BYTE> buf(size);
    if (TdhGetProperty(ev, 0, nullptr, 1, &desc, size, buf.data()) != ERROR_SUCCESS)
        return {};
    return std::wstring((wchar_t*)buf.data());
}

static void WINAPI on_event(PEVENT_RECORD ev) {
    if (ev->EventHeader.EventDescriptor.Id != EVENT_KERNEL_FILE_CREATE) return;
    DWORD pid = ev->EventHeader.ProcessId;
    if (g_filter_pid && pid != g_filter_pid) return;

    std::string path = narrow(get_string_prop(ev, L"FileName").c_str());
    if (path.empty()) return;

    // FILETIME (100ns since 1601) -> approximate ns timestamp; the collector's
    // TimestampNormalizer handles cross-source alignment.
    ULONGLONG ft = ((ULONGLONG)ev->EventHeader.TimeStamp.HighPart << 32) |
                   ev->EventHeader.TimeStamp.LowPart;

    std::string l = "{";
    l += "\"timestamp\":" + std::to_string(ft * 100ULL) + ",";
    l += "\"event\":\"FILE_OPEN\",";
    l += "\"comm\":\"\",";
    l += "\"pid\":" + std::to_string(pid) + ",";
    l += "\"count\":1,";
    l += "\"filepath\":\"";
    emit_escaped(l, path);
    l += "\",\"flags\":0}";
    fwrite(l.data(), 1, l.size(), stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

int main(int argc, char** argv) {
    for (int i = 1; i < argc; ++i)
        if (std::string(argv[i]) == "--pid" && i + 1 < argc) g_filter_pid = atoi(argv[++i]);

    // Start a real-time session.
    size_t props_size = sizeof(EVENT_TRACE_PROPERTIES) + (g_session_name.size() + 1) * sizeof(wchar_t);
    std::vector<BYTE> propbuf(props_size, 0);
    auto* props = (EVENT_TRACE_PROPERTIES*)propbuf.data();
    props->Wnode.BufferSize = (ULONG)props_size;
    props->Wnode.ClientContext = 1; // QPC
    props->Wnode.Flags = WNODE_FLAG_TRACED_GUID;
    props->LogFileMode = EVENT_TRACE_REAL_TIME_MODE;
    props->LoggerNameOffset = sizeof(EVENT_TRACE_PROPERTIES);

    ControlTraceW(0, g_session_name.c_str(), props, EVENT_TRACE_CONTROL_STOP); // clean stale
    ULONG st = StartTraceW(&g_session, g_session_name.c_str(), props);
    if (st != ERROR_SUCCESS) { fprintf(stderr, "StartTrace failed: %lu (admin?)\n", st); return 1; }

    ENABLE_TRACE_PARAMETERS params{};
    params.Version = ENABLE_TRACE_PARAMETERS_VERSION_2;
    st = EnableTraceEx2(g_session, &KERNEL_FILE_PROVIDER, EVENT_CONTROL_CODE_ENABLE_PROVIDER,
                        TRACE_LEVEL_INFORMATION, 0x10 /*KERNEL_FILE_KEYWORD_CREATE*/, 0, 0, &params);
    if (st != ERROR_SUCCESS) { fprintf(stderr, "EnableTraceEx2 failed: %lu\n", st); }

    EVENT_TRACE_LOGFILEW log{};
    log.LoggerName = (LPWSTR)g_session_name.c_str();
    log.ProcessTraceMode = PROCESS_TRACE_MODE_REAL_TIME | PROCESS_TRACE_MODE_EVENT_RECORD;
    log.EventRecordCallback = on_event;
    TRACEHANDLE h = OpenTraceW(&log);
    if (h == INVALID_PROCESSTRACE_HANDLE) { fprintf(stderr, "OpenTrace failed\n"); return 1; }

    ProcessTrace(&h, 1, nullptr, nullptr); // blocks until session stops
    CloseTrace(h);
    ControlTraceW(g_session, nullptr, props, EVENT_TRACE_CONTROL_STOP);
    return 0;
}
