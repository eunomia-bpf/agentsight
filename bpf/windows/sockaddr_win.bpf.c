// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// sockaddr_win.bpf.c -- AgentSight outbound-connection telemetry on
// eBPF-for-Windows via EBPF_PROGRAM_TYPE_CGROUP_SOCK_ADDR.
//
// There is no Linux equivalent program in AgentSight today; this is additive
// network visibility that DOES map cleanly onto a supported Windows hook. It
// fires on connect() for IPv4/IPv6 and emits an as_net_record (-> "CONNECT"
// JSONL). It always proceeds (observability only, never blocks).
//
// Build / verify:
//   clang -target bpf -O2 -g -Ibpf/windows -c bpf/windows/sockaddr_win.bpf.c \
//         -o build/sockaddr_win.o
//   netsh ebpf show verification build/sockaddr_win.o cgroup/connect4
#include "bpf_helpers.h"
#include "ebpf_nethooks.h" // bpf_sock_addr_t, BPF_SOCK_ADDR_VERDICT_PROCEED
#include "bpf_windows.h"

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} net_rb SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct as_net_record);
} net_scratch SEC(".maps");

static __inline int emit_connect(bpf_sock_addr_t *ctx, unsigned int family)
{
    __u32 zero = 0;
    struct as_net_record *r = bpf_map_lookup_elem(&net_scratch, &zero);
    if (!r)
        return BPF_SOCK_ADDR_VERDICT_PROCEED;

    __builtin_memset(r, 0, sizeof(*r));
    r->kind = AS_REC_NET_CONNECT;
    r->pid = (unsigned int)(bpf_get_current_pid_tgid() >> 32);
    r->family = family;
    r->protocol = ctx->protocol;
    r->timestamp_ns = bpf_ktime_get_boot_ns();
    r->dport = (unsigned short)ctx->user_port;

    if (family == AF_INET) {
        r->daddr_v4 = ctx->user_ip4;
    } else {
        // user_ip6 is a 4 x u32 array in bpf_sock_addr_t.
        __builtin_memcpy(r->daddr_v6, &ctx->user_ip6[0], sizeof(r->daddr_v6));
    }

    bpf_ringbuf_output(&net_rb, r, sizeof(*r), 0);
    return BPF_SOCK_ADDR_VERDICT_PROCEED;
}

SEC("cgroup/connect4")
int as_connect4(bpf_sock_addr_t *ctx)
{
    return emit_connect(ctx, AF_INET);
}

SEC("cgroup/connect6")
int as_connect6(bpf_sock_addr_t *ctx)
{
    return emit_connect(ctx, AF_INET6);
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
