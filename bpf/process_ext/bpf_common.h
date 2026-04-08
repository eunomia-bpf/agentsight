/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_NEW_BPF_COMMON_H
#define __PROCESS_NEW_BPF_COMMON_H

/*
 * Common BPF helpers for process_new: PID filtering + unified map update.
 * Included by process_new.bpf.c BEFORE all feature modules.
 * References maps and flags defined in the glue file.
 */

static __always_inline bool is_pid_tracked(void)
{
	if (!filter_pids)
		return true;  /* no filter mode: trace all */
	u32 pid = bpf_get_current_pid_tgid() >> 32;
	return bpf_map_lookup_elem(&tracked_pids, &pid) != NULL;
}

static __always_inline bool is_cgroup_tracked(void)
{
	if (!filter_cgroup)
		return true;
	u64 cgroup_id = bpf_get_current_cgroup_id();
	if (cgroup_id == target_cgroup_id)
		return true;
	if (!filter_cgroup_children)
		return false;
	return bpf_map_lookup_elem(&tracked_cgroups, &cgroup_id) != NULL;
}

static __always_inline bool is_event_tracked(void)
{
	return is_cgroup_tracked() && is_pid_tracked();
}

static __always_inline void update_agg_map(struct agg_key *key, u64 count, u64 bytes)
{
	struct agg_value *val = bpf_map_lookup_elem(&event_agg_map, key);
	if (val) {
		__sync_fetch_and_add(&val->count, count);
		if (bytes)
			__sync_fetch_and_add(&val->total_bytes, bytes);
		val->last_ts = bpf_ktime_get_ns();
		bpf_get_current_comm(val->comm, sizeof(val->comm));
	} else {
		struct agg_value new_val = {};
		new_val.count = count;
		new_val.total_bytes = bytes;
		new_val.first_ts = bpf_ktime_get_ns();
		new_val.last_ts = new_val.first_ts;
		bpf_get_current_comm(new_val.comm, sizeof(new_val.comm));

		if (bpf_map_update_elem(&event_agg_map, key, &new_val, BPF_NOEXIST) < 0) {
			/* map full: bump overflow counter */
			u32 zero = 0;
			u64 *overflow = bpf_map_lookup_elem(&agg_overflow_count, &zero);
			if (overflow)
				__sync_fetch_and_add(overflow, 1);
		}
	}
}

/* Format "fd=N" into a detail buffer without bpf_snprintf */
static __always_inline void format_fd_detail(char *buf, int buf_len, int fd)
{
	/* "fd=" prefix */
	if (buf_len < 4) return;
	buf[0] = 'f'; buf[1] = 'd'; buf[2] = '=';

	/* Convert fd to decimal string */
	int pos = 3;
	bool neg = false;
	unsigned int ufd;
	if (fd < 0) {
		neg = true;
		ufd = (unsigned int)(-fd);
	} else {
		ufd = (unsigned int)fd;
	}

	/* Write digits in reverse */
	char digits[12];
	int dlen = 0;
	if (ufd == 0) {
		digits[dlen++] = '0';
	} else {
		while (ufd > 0 && dlen < 11) {
			digits[dlen++] = '0' + (ufd % 10);
			ufd /= 10;
		}
	}

	if (neg && pos < buf_len - 1)
		buf[pos++] = '-';

	for (int i = dlen - 1; i >= 0 && pos < buf_len - 1; i--)
		buf[pos++] = digits[i];

	buf[pos] = '\0';
}

/* Format "N.N.N.N:PORT" for IPv4 addresses without bpf_snprintf */
/* Fully unrolled for BPF verifier (no loops / back-edges) */
static __always_inline void write_octet(char *buf, int buf_len, int *pos, u8 val)
{
	if (val >= 100 && *pos < buf_len - 1) buf[(*pos)++] = '0' + val / 100;
	if (val >= 10  && *pos < buf_len - 1) buf[(*pos)++] = '0' + (val / 10) % 10;
	if (*pos < buf_len - 1)               buf[(*pos)++] = '0' + val % 10;
}

static __always_inline void format_ipv4_port(char *buf, int buf_len, u32 ip, u16 port)
{
	int pos = 0;
	u8 o0 = ip & 0xFF;
	u8 o1 = (ip >> 8) & 0xFF;
	u8 o2 = (ip >> 16) & 0xFF;
	u8 o3 = (ip >> 24) & 0xFF;

	/* Octet 0 */
	write_octet(buf, buf_len, &pos, o0);
	/* Octet 1 */
	if (pos < buf_len - 1) buf[pos++] = '.';
	write_octet(buf, buf_len, &pos, o1);
	/* Octet 2 */
	if (pos < buf_len - 1) buf[pos++] = '.';
	write_octet(buf, buf_len, &pos, o2);
	/* Octet 3 */
	if (pos < buf_len - 1) buf[pos++] = '.';
	write_octet(buf, buf_len, &pos, o3);

	/* :PORT — max 5 digits, write manually */
	if (pos < buf_len - 1) buf[pos++] = ':';
	unsigned int p = port;
	/* Extract each digit (max 65535 = 5 digits) */
	char d4 = '0' + (p / 10000) % 10;
	char d3 = '0' + (p / 1000) % 10;
	char d2 = '0' + (p / 100) % 10;
	char d1 = '0' + (p / 10) % 10;
	char d0 = '0' + p % 10;
	if (p >= 10000 && pos < buf_len - 1) buf[pos++] = d4;
	if (p >= 1000  && pos < buf_len - 1) buf[pos++] = d3;
	if (p >= 100   && pos < buf_len - 1) buf[pos++] = d2;
	if (p >= 10    && pos < buf_len - 1) buf[pos++] = d1;
	if (pos < buf_len - 1) buf[pos++] = d0;

	buf[pos] = '\0';
}

#endif /* __PROCESS_NEW_BPF_COMMON_H */
