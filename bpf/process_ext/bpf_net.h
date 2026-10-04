/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_NET_H
#define __PROCESS_EXT_BPF_NET_H

/*
 * Network tracepoints: bind, listen, connect, plus successful datagram binds.
 * Extract addr:port for bind/connect, fd for listen.
 * Uses format_ipv4_port() and format_fd_detail() from bpf_common.h.
 */

/* Read sockaddr_in from userspace and format as "A.B.C.D:PORT" */
static __always_inline void read_and_format_sockaddr(struct trace_event_raw_sys_enter *ctx,
						     char *detail, int detail_len)
{
	struct sockaddr_in addr = {};
	const void *user_addr = (const void *)ctx->args[1];

	if (bpf_probe_read_user(&addr, sizeof(addr), user_addr) < 0) {
		detail[0] = '?';
		detail[1] = '\0';
		return;
	}

	u32 ip = addr.sin_addr.s_addr;
	u16 port = __builtin_bswap16(addr.sin_port);
	format_ipv4_port(detail, detail_len, ip, port);
}

/* Write "family=N" into buf */
static __always_inline void format_family(char *buf, int buf_len, u16 family)
{
	/* "family=" prefix */
	if (buf_len < 8) return;
	__builtin_memcpy(buf, "family=", 7);
	/* Use format_fd_detail trick for the number */
	int pos = 7;
	char digits[6];
	int dlen = 0;
	unsigned int f = family;
	if (f == 0) {
		digits[dlen++] = '0';
	} else {
		while (f > 0 && dlen < 5) {
			digits[dlen++] = '0' + (f % 10);
			f /= 10;
		}
	}
	for (int i = dlen - 1; i >= 0 && pos < buf_len - 1; i--)
		buf[pos++] = digits[i];
	buf[pos] = '\0';
}

/* Full IPv6 form fits in DETAIL_LEN without depending on bpf_snprintf. */
static __always_inline void format_ipv6(char *buf, const u8 *ip)
{
#pragma unroll
	for (int i = 0; i < 16; i++) {
		u8 hi = ip[i] >> 4, lo = ip[i] & 15;
		int pos = 2 * i + i / 2;
		buf[pos] = hi < 10 ? '0' + hi : 'a' + hi - 10;
		buf[pos + 1] = lo < 10 ? '0' + lo : 'a' + lo - 10;
		if (i % 2 && i != 15)
			buf[pos + 2] = ':';
	}
	buf[39] = '\0';
}

SEC("tp/syscalls/sys_enter_bind")
int trace_bind(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_network)
		return 0;
	if (!is_event_tracked())
		return 0;

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_NET_BIND;

	u16 family = 0;
	const void *user_addr = (const void *)ctx->args[1];
	bpf_probe_read_user(&family, sizeof(family), user_addr);

	if (family == 2) /* AF_INET */
		read_and_format_sockaddr(ctx, key.detail, sizeof(key.detail));
	else
		format_family(key.detail, sizeof(key.detail), family);

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_listen")
int trace_listen(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_network)
		return 0;
	if (!is_event_tracked())
		return 0;

	int fd = (int)ctx->args[0];

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_NET_LISTEN;
	format_fd_detail(key.detail, sizeof(key.detail), fd);

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_connect")
int trace_connect(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_network)
		return 0;
	if (!is_event_tracked())
		return 0;

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_NET_CONNECT;

	u16 family = 0;
	const void *user_addr = (const void *)ctx->args[1];
	bpf_probe_read_user(&family, sizeof(family), user_addr);

	if (family == 2)
		read_and_format_sockaddr(ctx, key.detail, sizeof(key.detail));
	else
		format_family(key.detail, sizeof(key.detail), family);

	update_agg_map(&key, 1, 0);
	return 0;
}

/* A syscall-entry bind cannot see the port assigned for bind(..., port=0).
 * Read the socket after a successful bind and add a NET_BIND summary with
 * protocol and assigned port for UDP, UDP-Lite, and ICMP echo sockets. */
static __always_inline int trace_datagram_bind(void *ctx, struct sock *sk)
{
	u64 ret;
	u16 family, protocol, port;
	struct agg_key key = {};

	if (!trace_network || !sk || !is_event_tracked() ||
	    bpf_get_func_ret(ctx, &ret) || (int)ret)
		return 0;
	family = BPF_CORE_READ(sk, __sk_common.skc_family);
	if (family != 2 && family != 10) /* AF_INET, AF_INET6 */
		return 0;
	if (BPF_CORE_READ_BITFIELD_PROBED(sk, sk_type) != 2) /* SOCK_DGRAM */
		return 0;
	protocol = BPF_CORE_READ_BITFIELD_PROBED(sk, sk_protocol);
	if (protocol != 17 && protocol != 136 && protocol != 1 && protocol != 58)
		return 0;
	port = BPF_CORE_READ(sk, __sk_common.skc_num);
	if (!port)
		return 0;

	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_NET_BIND;
	key.port = port;
	key.protocol = protocol;
	if (family == 2) {
		u32 ip = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
		format_ipv4_port(key.detail, sizeof(key.detail), ip, port);
	} else {
		u8 ip[16] = {};
		BPF_CORE_READ_INTO((struct in6_addr *)ip, sk, __sk_common.skc_v6_rcv_saddr);
		format_ipv6(key.detail, ip);
	}
	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("fexit/inet_bind_sk")
int BPF_PROG(trace_datagram_bind4_sk, struct sock *sk)
{
	return trace_datagram_bind(ctx, sk);
}

SEC("fexit/inet6_bind_sk")
int BPF_PROG(trace_datagram_bind6_sk, struct sock *sk)
{
	return trace_datagram_bind(ctx, sk);
}

SEC("fexit/inet_bind")
int BPF_PROG(trace_datagram_bind4, struct socket *sock)
{
	return trace_datagram_bind(ctx, BPF_CORE_READ(sock, sk));
}

SEC("fexit/inet6_bind")
int BPF_PROG(trace_datagram_bind6, struct socket *sock)
{
	return trace_datagram_bind(ctx, BPF_CORE_READ(sock, sk));
}

/* One NET_ACCEPT summary per process, listener port, and remote address.
 * The LRU bounds memory and allows a peer to be reported again after eviction. */
SEC("fexit/inet_csk_accept")
int BPF_PROG(trace_accept_peer, struct sock *sk)
{
	u64 ret;
	struct sock *child;
	struct accept_peer_key peer = {};
	struct agg_key key = {};
	u8 present = 1;

	if (!trace_network || !is_event_tracked() ||
	    bpf_get_func_ret(ctx, &ret) || !ret)
		return 0;
	child = (struct sock *)ret;
	peer.family = BPF_CORE_READ(sk, __sk_common.skc_family);
	if (peer.family != 2 && peer.family != 10)
		return 0;
	peer.pid = bpf_get_current_pid_tgid() >> 32;
	peer.port = BPF_CORE_READ(sk, __sk_common.skc_num);
	struct task_struct *task = (struct task_struct *)bpf_get_current_task();
	peer.start_time = BPF_CORE_READ(task, group_leader, start_time);
	if (peer.family == 2)
		BPF_CORE_READ_INTO((u32 *)peer.peer, child, __sk_common.skc_daddr);
	else
		BPF_CORE_READ_INTO((struct in6_addr *)peer.peer, child,
			__sk_common.skc_v6_daddr);
	if (bpf_map_update_elem(&accept_peers_seen, &peer, &present, BPF_NOEXIST) == -EEXIST)
		return 0;

	key.pid = peer.pid;
	key.event_type = EVENT_TYPE_NET_ACCEPT;
	key.port = peer.port;
	key.protocol = 6; /* TCP */
	if (peer.family == 2)
		format_ipv4_port(key.detail, sizeof(key.detail), *(u32 *)peer.peer, peer.port);
	else
		format_ipv6(key.detail, peer.peer);
	update_agg_map(&key, 1, 0);
	return 0;
}

#endif /* __PROCESS_EXT_BPF_NET_H */
