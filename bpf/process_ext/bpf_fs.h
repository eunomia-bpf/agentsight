/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_FS_H
#define __PROCESS_EXT_BPF_FS_H

/*
 * Filesystem mutation tracepoints.
 * Hook both old (unlink, mkdir, rename) and *at variants (unlinkat, mkdirat, renameat2)
 * because glibc/Python may use either depending on version.
 * All aggregate into event_agg_map via update_agg_map().
 */

/* Extract parent directory prefix from a path (truncate at last '/') */
static __always_inline void extract_dir_prefix(const char *path, char *out, int out_len)
{
	int last_slash = 0;

	#pragma unroll
	for (int i = 0; i < DETAIL_LEN - 1; i++) {
		if (i >= out_len - 1)
			break;
		char c = path[i];
		if (c == '\0')
			break;
		if (c == '/')
			last_slash = i;
		out[i] = c;
	}

	if (last_slash > 0)
		out[last_slash] = '\0';
}

/* Shared helper: aggregate a file path event with extra info */
static __always_inline int agg_path_event(const char *user_path, u32 event_type)
{
	if (!trace_fs_mutations)
		return 0;
	if (!is_event_tracked())
		return 0;

	char filepath[MAX_FILENAME_LEN];
	if (bpf_probe_read_user_str(filepath, sizeof(filepath), user_path) < 0)
		return 0;

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = event_type;
	key.process_start_ns = current_process_start_ns();
	extract_dir_prefix(filepath, key.detail, sizeof(key.detail));

	struct agg_value *val = bpf_map_lookup_elem(&event_agg_map, &key);
	if (val) {
		__sync_fetch_and_add(&val->count, 1);
		val->last_ts = bpf_ktime_get_ns();
		bpf_get_current_comm(val->comm, sizeof(val->comm));
		bpf_probe_read_kernel_str(val->extra, sizeof(val->extra), filepath);
	} else {
		struct agg_value new_val = {};
		new_val.count = 1;
		new_val.first_ts = bpf_ktime_get_ns();
		new_val.last_ts = new_val.first_ts;
		bpf_get_current_comm(new_val.comm, sizeof(new_val.comm));
		bpf_probe_read_kernel_str(new_val.extra, sizeof(new_val.extra), filepath);

		if (bpf_map_update_elem(&event_agg_map, &key, &new_val, BPF_NOEXIST) < 0) {
			u32 zero = 0;
			u64 *overflow = bpf_map_lookup_elem(&agg_overflow_count, &zero);
			if (overflow)
				__sync_fetch_and_add(overflow, 1);
		}
	}
	return 0;
}

/* --- unlink / unlinkat → FILE_DELETE --- */

SEC("tp/syscalls/sys_enter_unlinkat")
int trace_unlinkat(struct trace_event_raw_sys_enter *ctx)
{
	return agg_path_event((const char *)ctx->args[1], EVENT_TYPE_FILE_DELETE);
}

SEC("tp/syscalls/sys_enter_unlink")
int trace_unlink(struct trace_event_raw_sys_enter *ctx)
{
	return agg_path_event((const char *)ctx->args[0], EVENT_TYPE_FILE_DELETE);
}

/* --- rename / renameat / renameat2 → FILE_RENAME --- */

SEC("tp/syscalls/sys_enter_renameat2")
int trace_renameat2(struct trace_event_raw_sys_enter *ctx)
{
	/* newpath is args[3] */
	return agg_path_event((const char *)ctx->args[3], EVENT_TYPE_FILE_RENAME);
}

SEC("tp/syscalls/sys_enter_renameat")
int trace_renameat(struct trace_event_raw_sys_enter *ctx)
{
	/* renameat(olddirfd, oldpath, newdirfd, newpath): newpath is args[3] */
	return agg_path_event((const char *)ctx->args[3], EVENT_TYPE_FILE_RENAME);
}

SEC("tp/syscalls/sys_enter_rename")
int trace_rename(struct trace_event_raw_sys_enter *ctx)
{
	/* rename(oldpath, newpath): newpath is args[1] */
	return agg_path_event((const char *)ctx->args[1], EVENT_TYPE_FILE_RENAME);
}

/* --- mkdir / mkdirat → DIR_CREATE --- */

SEC("tp/syscalls/sys_enter_mkdirat")
int trace_mkdirat(struct trace_event_raw_sys_enter *ctx)
{
	return agg_path_event((const char *)ctx->args[1], EVENT_TYPE_DIR_CREATE);
}

SEC("tp/syscalls/sys_enter_mkdir")
int trace_mkdir(struct trace_event_raw_sys_enter *ctx)
{
	return agg_path_event((const char *)ctx->args[0], EVENT_TYPE_DIR_CREATE);
}

SEC("tp/syscalls/sys_enter_ftruncate")
int trace_ftruncate(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_fs_mutations)
		return 0;
	if (!is_event_tracked())
		return 0;

	int fd = (int)ctx->args[0];

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_FILE_TRUNCATE;
	format_fd_detail(key.detail, sizeof(key.detail), fd);

	update_agg_map(&key, 1, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_chdir")
int trace_chdir(struct trace_event_raw_sys_enter *ctx)
{
	if (!trace_fs_mutations)
		return 0;
	if (!is_event_tracked())
		return 0;

	char path[DETAIL_LEN];
	const char *user_path = (const char *)ctx->args[0];
	if (bpf_probe_read_user_str(path, sizeof(path), user_path) < 0)
		return 0;

	struct agg_key key = {};
	key.pid = bpf_get_current_pid_tgid() >> 32;
	key.event_type = EVENT_TYPE_CHDIR;
	bpf_probe_read_kernel_str(key.detail, sizeof(key.detail), path);

	update_agg_map(&key, 1, 0);
	return 0;
}

#endif /* __PROCESS_EXT_BPF_FS_H */
