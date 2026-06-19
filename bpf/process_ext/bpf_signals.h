/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_SIGNALS_H
#define __PROCESS_EXT_BPF_SIGNALS_H

/*
 * Process coordination tracepoints: setpgid, setsid, kill, fork.
 * Uses manual string formatting to avoid bpf_snprintf pointer issues.
 */

/* Helper: write unsigned int as decimal at buf+pos, return new pos */
static __always_inline int write_uint(char *buf, int pos, int buf_len, unsigned int val)
{
	char digits[12];
	int dlen = 0;
	if (val == 0) {
		digits[dlen++] = '0';
	} else {
		while (val > 0 && dlen < 11) {
			digits[dlen++] = '0' + (val % 10);
			val /= 10;
		}
	}
	for (int i = dlen - 1; i >= 0 && pos < buf_len - 1; i--)
		buf[pos++] = digits[i];
	return pos;
}

/* Helper: write signed int */
static __always_inline int write_int(char *buf, int pos, int buf_len, int val)
{
	if (val < 0 && pos < buf_len - 1) {
		buf[pos++] = '-';
		return write_uint(buf, pos, buf_len, (unsigned int)(-val));
	}
	return write_uint(buf, pos, buf_len, (unsigned int)val);
}

/* Helper: write literal string */
static __always_inline int write_str(char *buf, int pos, int buf_len, const char *s)
{
	for (int i = 0; s[i] && pos < buf_len - 1; i++)
		buf[pos++] = s[i];
	return pos;
}

SEC("tp/syscalls/sys_enter_setpgid")
int trace_setpgid(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_signals)
		return 0;
	if (!is_event_tracked())
		return 0;

	int target_pid = (int)ctx->args[0];
	int pgid = (int)ctx->args[1];

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_PGRP_CHANGE;

	int pos = 0;
	pos = write_str(key.detail, pos, DETAIL_LEN, "pid=");
	pos = write_int(key.detail, pos, DETAIL_LEN, target_pid);
	pos = write_str(key.detail, pos, DETAIL_LEN, ",pgid=");
	pos = write_int(key.detail, pos, DETAIL_LEN, pgid);
	key.detail[pos] = '\0';

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_setsid")
int trace_setsid(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_signals)
		return 0;
	if (!is_event_tracked())
		return 0;

	u32 pid = bpf_get_current_pid_tgid() >> 32;

	struct agg_key key = {};
	key.pid = pid;
	key.event_type = EVENT_TYPE_SESSION_CREATE;

	int pos = 0;
	pos = write_str(key.detail, pos, DETAIL_LEN, "sid=");
	pos = write_uint(key.detail, pos, DETAIL_LEN, pid);
	key.detail[pos] = '\0';

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_kill")
int trace_kill(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_signals)
		return 0;
	if (!is_event_tracked())
		return 0;

	int target_pid = (int)ctx->args[0];
	int sig = (int)ctx->args[1];

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_SIGNAL_SEND;

	int pos = 0;
	pos = write_str(key.detail, pos, DETAIL_LEN, "target=");
	pos = write_int(key.detail, pos, DETAIL_LEN, target_pid);
	pos = write_str(key.detail, pos, DETAIL_LEN, ",sig=");
	pos = write_int(key.detail, pos, DETAIL_LEN, sig);
	key.detail[pos] = '\0';

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/sched/sched_process_fork")
int trace_fork(struct trace_event_raw_sched_process_fork *ctx)
{
	if (!is_cgroup_tracked())
		return 0;

	track_child_pid_from_parent((u32)ctx->parent_pid, (u32)ctx->child_pid);

	if (!trace_signals)
		return 0;
	if (!is_pid_tracked())
		return 0;

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_PROC_FORK;
	/* detail left empty: aggregate fork count per parent pid */

	update_agg_map(&key, 1, 0);
	return 0;
}

#endif /* __PROCESS_EXT_BPF_SIGNALS_H */
