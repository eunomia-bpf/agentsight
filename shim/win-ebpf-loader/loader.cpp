// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// agentsight-ebpf-loader.exe -- loads AgentSight's eBPF-for-Windows programs,
// polls their ring buffers, and serializes each record to the SAME JSONL the
// Linux `process` binary emits. This is the piece that makes the eBPF half of
// the Windows port actually run; collector/src/runners/windows_ebpf.rs spawns
// it and reads its stdout.
//
// Links the Windows libbpf surface (ebpfapi.dll, NuGet `eBPF-for-Windows`).
//
// Usage:
//   agentsight-ebpf-loader.exe --process  --object-dir <dir> [--pid <pid>]
//   agentsight-ebpf-loader.exe --network  --object-dir <dir>
#include <windows.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <string>
#include <vector>
#include <cstdio>
#include <csignal>
#include "../../bpf/windows/bpf_windows.h"

static volatile bool g_running = true;
static void on_sigint(int) { g_running = false; }

// --- JSON emit (matches bpf/process.c line shapes) --------------------------
static void emit_escaped(std::string& out, const char* s, size_t n) {
    static const char hex[] = "0123456789abcdef";
    for (size_t i = 0; i < n && s[i]; ++i) {
        unsigned char c = (unsigned char)s[i];
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:
                if (c < 0x20) { out += "\\u00"; out += hex[c>>4]; out += hex[c&0xf]; }
                else out += (char)c;
        }
    }
}

static void print_line(const std::string& line) {
    fwrite(line.data(), 1, line.size(), stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

static int on_process(void* /*ctx*/, void* data, size_t size) {
    if (size < sizeof(as_process_record)) return 0;
    auto* r = (const as_process_record*)data;
    std::string l = "{";
    l += "\"timestamp\":" + std::to_string(r->timestamp_ns) + ",";
    l += (r->kind == AS_REC_PROCESS_EXEC) ? "\"event\":\"EXEC\"," : "\"event\":\"EXIT\",";
    l += "\"comm\":\"";
    // comm = first token of cmdline (image path basename), best-effort.
    {
        const char* c = r->cmdline; size_t n = r->cmd_len; size_t base = 0;
        for (size_t i = 0; i < n && c[i] && c[i] != ' '; ++i)
            if (c[i] == '\\' || c[i] == '/') base = i + 1;
        size_t end = base;
        while (end < n && c[end] && c[end] != ' ') ++end;
        emit_escaped(l, c + base, end - base);
    }
    l += "\",";
    l += "\"pid\":" + std::to_string(r->pid) + ",";
    l += "\"ppid\":" + std::to_string(r->ppid);
    if (r->kind == AS_REC_PROCESS_EXEC) {
        l += ",\"full_command\":\"";
        emit_escaped(l, r->cmdline, r->cmd_len);
        l += "\"";
    } else {
        l += ",\"exit_code\":" + std::to_string(r->exit_code);
    }
    l += "}";
    print_line(l);
    return 0;
}

static int on_net(void* /*ctx*/, void* data, size_t size) {
    if (size < sizeof(as_net_record)) return 0;
    auto* r = (const as_net_record*)data;
    std::string l = "{";
    l += "\"timestamp\":" + std::to_string(r->timestamp_ns) + ",";
    l += (r->kind == AS_REC_NET_CONNECT) ? "\"event\":\"CONNECT\"," : "\"event\":\"DISCONNECT\",";
    l += "\"comm\":\"net\",";
    l += "\"pid\":" + std::to_string(r->pid) + ",";
    l += "\"family\":" + std::to_string(r->family) + ",";
    l += "\"protocol\":" + std::to_string(r->protocol) + ",";
    if (r->family == 2 /*AF_INET*/) {
        unsigned a = r->daddr_v4;
        char ip[32];
        snprintf(ip, sizeof(ip), "%u.%u.%u.%u",
                 a & 0xff, (a >> 8) & 0xff, (a >> 16) & 0xff, (a >> 24) & 0xff);
        l += "\"daddr\":\""; l += ip; l += "\",";
    }
    unsigned short p = (unsigned short)((r->dport >> 8) | (r->dport << 8)); // ntohs
    l += "\"dport\":" + std::to_string(p);
    l += "}";
    print_line(l);
    return 0;
}

// Set the program's `targ_pid` global (in its .rodata) before load, if present.
static void set_targ_pid(bpf_object* obj, unsigned int pid) {
    if (!pid) return;
    bpf_map* rodata = bpf_object__find_map_by_name(obj, ".rodata");
    if (!rodata) return;
    // Initial-value buffer is laid out as the C globals; for our single global
    // this is the leading u32. A real build uses a skeleton; this keeps the
    // loader self-contained.
    size_t sz = 0;
    void* val = (void*)bpf_map__initial_value(rodata, &sz);
    if (val && sz >= sizeof(unsigned int)) *(unsigned int*)val = pid;
}

struct LoadSpec { const char* file; const char* map; ring_buffer_sample_fn cb; };

static ring_buffer* load_one(const std::string& dir, const LoadSpec& s, unsigned pid) {
    std::string path = dir + "\\" + s.file;
    bpf_object* obj = bpf_object__open(path.c_str());
    if (!obj) { fprintf(stderr, "[loader] open %s failed\n", path.c_str()); return nullptr; }
    set_targ_pid(obj, pid);
    if (bpf_object__load(obj)) { fprintf(stderr, "[loader] load %s failed\n", path.c_str()); return nullptr; }
    bpf_program* prog;
    bpf_object__for_each_program(prog, obj) {
        if (bpf_program__attach(prog) == nullptr)
            fprintf(stderr, "[loader] attach %s failed (continuing)\n", bpf_program__name(prog));
    }
    bpf_map* m = bpf_object__find_map_by_name(obj, s.map);
    if (!m) { fprintf(stderr, "[loader] map %s not found\n", s.map); return nullptr; }
    return ring_buffer__new(bpf_map__fd(m), s.cb, nullptr, nullptr);
}

int main(int argc, char** argv) {
    std::string object_dir = ".";
    bool process = false, network = false;
    unsigned pid = 0;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--process") process = true;
        else if (a == "--network") network = true;
        else if (a == "--object-dir" && i + 1 < argc) object_dir = argv[++i];
        else if (a == "--pid" && i + 1 < argc) pid = (unsigned)atoi(argv[++i]);
    }
    if (!process && !network) { fprintf(stderr, "need --process or --network\n"); return 2; }
    signal(SIGINT, on_sigint);

    std::vector<ring_buffer*> rbs;
    if (process)
        if (auto* rb = load_one(object_dir, {"process_win.o", "process_rb", on_process}, pid)) rbs.push_back(rb);
    if (network) {
        if (auto* rb = load_one(object_dir, {"sockaddr_win.o", "net_rb", on_net}, 0)) rbs.push_back(rb);
        if (auto* rb = load_one(object_dir, {"sockops_win.o", "sockops_rb", on_net}, 0)) rbs.push_back(rb);
    }
    if (rbs.empty()) { fprintf(stderr, "[loader] nothing loaded\n"); return 1; }

    while (g_running)
        for (auto* rb : rbs)
            ring_buffer__poll(rb, 200);

    for (auto* rb : rbs) ring_buffer__free(rb);
    return 0;
}
