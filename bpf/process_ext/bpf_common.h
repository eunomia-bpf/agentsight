/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_COMMON_H
#define __PROCESS_EXT_BPF_COMMON_H

/*
 * Common BPF helpers for process extension modules: PID filtering and
 * aggregated map updates. Included by process.bpf.c before feature modules.
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
	/* A PID can be reused inside the aggregation window. Derive the same
	 * process-instance key used by TLS capture from the group leader. */
	struct task_struct *task = (struct task_struct *)bpf_get_current_task();
	struct task_struct *leader = BPF_CORE_READ(task, group_leader);
	if (!leader)
		leader = task;
	if (bpf_core_field_exists(leader->start_boottime))
		key->process_start_ns = BPF_CORE_READ(leader, start_boottime);
	else
		key->process_start_ns = BPF_CORE_READ(leader, start_time);
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

/* Format "fd=N" into a detail buffer. */
static __always_inline void format_fd_detail(char *buf, int buf_len, int fd)
{
	u64 args[1] = { (u64)(s64)fd };
	bpf_snprintf(buf, buf_len, "fd=%d", args, sizeof(args));
}

/* Format "N.N.N.N:PORT" for IPv4 addresses. */
static __always_inline void format_ipv4_port(char *buf, int buf_len, u32 ip, u16 port)
{
	/* The helper avoids variable stack-pointer arithmetic which some verifier
	 * versions reject after Clang folds the hand-written decimal formatter. */
	u64 args[5] = { ip & 255, (ip >> 8) & 255, (ip >> 16) & 255,
			(ip >> 24) & 255, port };
	bpf_snprintf(buf, buf_len, "%d.%d.%d.%d:%d", args, sizeof(args));
}

#endif /* __PROCESS_EXT_BPF_COMMON_H */
