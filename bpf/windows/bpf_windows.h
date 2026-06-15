// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// Shared record layouts for AgentSight's eBPF-for-Windows programs.
//
// These structs travel kernel -> userspace over a BPF ring buffer
// (BPF_MAP_TYPE_RINGBUF via bpf_ringbuf_output). The userspace loader
// (collector/src/runners/windows_ebpf.rs, or the standalone bpf/windows tools)
// serializes each record into the SAME JSONL line shapes the Linux userspace
// binaries emit, so the entire Rust analyzer pipeline is reused unchanged.
//
// IMPORTANT design constraints for eBPF-for-Windows (see docs/windows-migration.md):
//   * No bpf_get_current_comm / bpf_get_current_uid_gid  -> identity comes from
//     the typed program context (process_md_t) and bpf_get_current_logon_id.
//   * Standalone bpf_ringbuf_reserve/submit is not yet exposed (issue #727)
//     -> build the record on a per-CPU scratch map / stack and emit it with
//     bpf_ringbuf_output().
//   * No bpf_probe_read_user -> ctx payloads (e.g. the command line) are read
//     directly from the verified context pointers.
#pragma once

#define AS_COMM_LEN 16
#define AS_PATH_LEN 256
#define AS_CMDLINE_LEN 1024

// Record kinds, mirrored into the JSON "event" field by the loader.
enum as_record_kind {
    AS_REC_PROCESS_EXEC = 1, // -> {"event":"EXEC", ...}
    AS_REC_PROCESS_EXIT = 2, // -> {"event":"EXIT", ...}
    AS_REC_NET_CONNECT  = 3, // -> {"event":"CONNECT", ...}
    AS_REC_NET_CLOSE    = 4, // -> {"event":"DISCONNECT", ...}
};

// One process lifecycle record. Emitted by process_win.bpf.c.
// Loader maps -> {"timestamp":ns,"event":"EXEC|EXIT","comm":..,"pid":..,
//                 "ppid":..,"full_command":..,"exit_code":..}
struct as_process_record {
    unsigned int  kind;          // enum as_record_kind
    unsigned int  pid;           // process_md_t.process_id (truncated)
    unsigned int  ppid;          // parent_process_id (truncated)
    int           exit_code;     // process_md_t.exit_code (exit only)
    unsigned long long timestamp_ns; // bpf_ktime_get_boot_ns()
    unsigned long long logon_id;     // bpf_get_current_logon_id()
    unsigned int  cmd_len;       // valid bytes in cmdline
    char          cmdline[AS_CMDLINE_LEN]; // image path + args, '\0'-padded
};

// One network connection record. Emitted by sockaddr_win / sockops_win.
// Loader maps -> {"timestamp":ns,"event":"CONNECT|DISCONNECT","pid":..,
//                 "comm":"net","family":..,"protocol":..,"daddr":..,"dport":..}
struct as_net_record {
    unsigned int  kind;          // enum as_record_kind
    unsigned int  pid;           // bpf_get_current_pid_tgid() >> 32
    unsigned int  family;        // AF_INET(2) / AF_INET6(23 on Windows)
    unsigned int  protocol;      // IPPROTO_TCP(6) / UDP(17)
    unsigned long long timestamp_ns;
    unsigned int  daddr_v4;      // network byte order (v4)
    unsigned char daddr_v6[16];  // v6
    unsigned short dport;        // network byte order
    unsigned short _pad;
};
