// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// sockops_win.bpf.c -- connection established / torn-down notifications on
// eBPF-for-Windows via EBPF_PROGRAM_TYPE_SOCK_OPS. Complements sockaddr_win:
// connect4/6 records the intent, sockops records the actual lifecycle so the
// collector can correlate connection open/close with LLM HTTP calls.
//
// Build / verify:
//   clang -target bpf -O2 -g -Ibpf/windows -c bpf/windows/sockops_win.bpf.c \
//         -o build/sockops_win.o
//   netsh ebpf show verification build/sockops_win.o sockops
#include "bpf_helpers.h"
#include "ebpf_nethooks.h" // bpf_sock_ops_t, BPF_SOCK_OPS_*
#include "bpf_windows.h"

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} sockops_rb SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct as_net_record);
} sockops_scratch SEC(".maps");

SEC("sockops")
int as_sockops(bpf_sock_ops_t *ctx)
{
    unsigned int kind;
    switch (ctx->op) {
    case BPF_SOCK_OPS_TCP_CONNECT_CB:        // outbound established
    case BPF_SOCK_OPS_PASSIVE_ESTABLISHED_CB: // inbound established
        kind = AS_REC_NET_CONNECT;
        break;
    case BPF_SOCK_OPS_RTO_CB: // teardown / loss signal -> treat as close
        kind = AS_REC_NET_CLOSE;
        break;
    default:
        return 0;
    }

    __u32 zero = 0;
    struct as_net_record *r = bpf_map_lookup_elem(&sockops_scratch, &zero);
    if (!r)
        return 0;

    __builtin_memset(r, 0, sizeof(*r));
    r->kind = kind;
    r->pid = (unsigned int)(bpf_get_current_pid_tgid() >> 32);
    r->family = ctx->family;
    r->timestamp_ns = bpf_ktime_get_boot_ns();
    r->daddr_v4 = ctx->remote_ip4;
    r->dport = (unsigned short)ctx->remote_port;

    bpf_ringbuf_output(&sockops_rb, r, sizeof(*r), 0);
    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
