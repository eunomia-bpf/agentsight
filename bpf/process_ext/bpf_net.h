/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_NET_H
#define __PROCESS_EXT_BPF_NET_H

/*
 * Network evidence: bind/connect syscall attempts, successful TCP listeners,
 * and accepted TCP peers. Endpoint observations are independent of TLS and
 * HTTP connection identities.
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

static __always_inline void format_ipv6_port(char *detail, int detail_len,
					     const struct in6_addr *addr, u16 port)
{
	const char hex[] = "0123456789abcdef";
	int pos = 0;
	if (pos < detail_len - 1) detail[pos++] = '[';
#pragma unroll
	for (int i = 0; i < 16; i++) {
		u8 byte = addr->in6_u.u6_addr8[i];
		if (pos < detail_len - 1) detail[pos++] = hex[byte >> 4];
		if (pos < detail_len - 1) detail[pos++] = hex[byte & 15];
		if ((i & 1) && i != 15 && pos < detail_len - 1)
			detail[pos++] = ':';
	}
	if (pos < detail_len - 1) detail[pos++] = ']';
	if (pos < detail_len - 1) detail[pos++] = ':';
	unsigned int p = port;
	if (p >= 10000 && pos < detail_len - 1) detail[pos++] = '0' + (p / 10000) % 10;
	if (p >= 1000 && pos < detail_len - 1) detail[pos++] = '0' + (p / 1000) % 10;
	if (p >= 100 && pos < detail_len - 1) detail[pos++] = '0' + (p / 100) % 10;
	if (p >= 10 && pos < detail_len - 1) detail[pos++] = '0' + (p / 10) % 10;
	if (pos < detail_len - 1) detail[pos++] = '0' + p % 10;
	detail[pos] = '\0';
}

static __always_inline void format_sock_endpoint(struct sock *sk, bool peer,
						  char *detail, int detail_len)
{
	u16 family = BPF_CORE_READ(sk, __sk_common.skc_family);
	if (family == 2) { /* AF_INET */
		u32 ip = peer ? BPF_CORE_READ(sk, __sk_common.skc_daddr)
			      : BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
		u16 port = peer ? __builtin_bswap16(BPF_CORE_READ(sk, __sk_common.skc_dport))
				: BPF_CORE_READ(sk, __sk_common.skc_num);
		format_ipv4_port(detail, detail_len, ip, port);
	} else if (family == 10) { /* AF_INET6 */
		struct in6_addr addr = {};
		if (peer)
			BPF_CORE_READ_INTO(&addr, sk, __sk_common.skc_v6_daddr);
		else
			BPF_CORE_READ_INTO(&addr, sk, __sk_common.skc_v6_rcv_saddr);
		u16 port = peer ? __builtin_bswap16(BPF_CORE_READ(sk, __sk_common.skc_dport))
				: BPF_CORE_READ(sk, __sk_common.skc_num);
		format_ipv6_port(detail, detail_len, &addr, port);
	} else {
		format_family(detail, detail_len, family);
	}
}

SEC("kprobe/inet_listen")
int BPF_KPROBE(trace_inet_listen_enter, struct socket *sock)
{
	if (!trace_network || !is_event_tracked())
		return 0;
	u64 tid = bpf_get_current_pid_tgid();
	u64 ptr = (u64)sock;
	bpf_map_update_elem(&listen_socket_map, &tid, &ptr, BPF_ANY);
	return 0;
}

SEC("kretprobe/inet_listen")
int BPF_KRETPROBE(trace_inet_listen_exit, int ret)
{
	u64 tid = bpf_get_current_pid_tgid();
	u64 *ptr = bpf_map_lookup_elem(&listen_socket_map, &tid);
	if (!ptr)
		return 0;
	u64 sock_ptr = *ptr;
	bpf_map_delete_elem(&listen_socket_map, &tid);
	if (ret != 0)
		return 0;
	struct sock *sk = BPF_CORE_READ((struct socket *)sock_ptr, sk);
	if (!sk)
		return 0;


	struct agg_key key = {};
	key.pid = tid >> 32;
	key.event_type = EVENT_TYPE_NET_LISTEN;
	format_sock_endpoint(sk, false, key.detail, sizeof(key.detail));

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("kretprobe/inet_csk_accept")
int BPF_KRETPROBE(trace_inet_accept, struct sock *accepted)
{
	if (!trace_network || !accepted || !is_event_tracked())
		return 0;
	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_NET_ACCEPT;
	format_sock_endpoint(accepted, true, key.detail, sizeof(key.detail));
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

#endif /* __PROCESS_EXT_BPF_NET_H */
