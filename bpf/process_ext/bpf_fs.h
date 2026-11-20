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

/* Copy a NUL-terminated string between two stacks buffers.
 *
 * bpf_probe_read_kernel_str() expects a kernel address and returns -EFAULT for a
 * stack pointer, so using it for stack->stack copies wrote nothing. Copy the
 * bytes directly, bounded like the kernel helper was.
 */
static __always_inline void copy_str_to(char *dst, int dst_len, const char *src)
{
	#pragma unroll
	for (int i = 0; i < DETAIL_LEN; i++) {
		if (i >= dst_len - 1)
			break;
		char c = src[i];
		dst[i] = c;
		if (c == '\0')
			return;
	}
	if (dst_len > 0)
		dst[dst_len - 1] = '\0';
}
/* Spell out a failed bpf_probe_read_user_str() in the aggregate, so a URL/pipe
 * style path that cannot be read still shows up as its event type instead of
 * disappearing: without this the hook returned 0 and the whole event was
 * dropped, which reads downstream as "the hook never fired".
 */
static __always_inline void write_path_read_failure(char *buf, int buf_len, long rc)
{
	static const char prefix[] = "<user path unreadable: ";
	int pos = 0;

	#pragma unroll
	for (int i = 0; i < sizeof(prefix) - 1 && pos < buf_len - 1; i++)
		buf[pos++] = prefix[i];
	if (rc < 0 && pos < buf_len - 1) {
		buf[pos++] = '-';
		rc = -rc;
	}

	/* An errno fits in five digits (ERFKILL is 132), and every byte here
	 * competes with the caller's aggregate buffers under the 512-byte BPF
	 * stack limit. */
	char digits[5];
	int dlen = 0;
	/* A bounded loop here is not unrolled by the optimizer, and the verifier
	 * then sees a back edge in every fs hook; spell the five digits out. */
	#pragma unroll
	for (int i = 0; i < 5; i++) {
		digits[dlen++] = '0' + (int)(rc % 10);
		rc /= 10;
		if (rc == 0)
			break;
	}
	#pragma unroll
	for (int i = 0; i < 5; i++) {
		if (i >= dlen || pos >= buf_len - 1)
			break;
		buf[pos++] = digits[dlen - 1 - i];
	}
	buf[pos] = '\0';
}

/* Shared helper: aggregate a file path event with extra info */
static __always_inline int agg_path_event(const char *user_path, u32 event_type)
{
	if (!trace_fs_mutations)
		return 0;
	if (!is_event_tracked())
		return 0;

	char filepath[MAX_FILENAME_LEN] = {};
	/* A failed read no longer drops the event. The aggregate keeps its type
	 * and pid, detail stays empty, and extra says why the path is missing. */
	long path_rc = bpf_probe_read_user_str(filepath, sizeof(filepath), user_path);

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
		if (path_rc >= 0)
			copy_str_to(val->extra, sizeof(val->extra), filepath);
		else
			write_path_read_failure(val->extra, sizeof(val->extra), path_rc);
	} else {
		struct agg_value new_val = {};
		new_val.count = 1;
		new_val.first_ts = bpf_ktime_get_ns();
		new_val.last_ts = new_val.first_ts;
		bpf_get_current_comm(new_val.comm, sizeof(new_val.comm));
		if (path_rc >= 0)
			copy_str_to(new_val.extra, sizeof(new_val.extra), filepath);
		else
			write_path_read_failure(new_val.extra, sizeof(new_val.extra), path_rc);

		if (bpf_map_update_elem(&event_agg_map, &key, &new_val, BPF_NOEXIST) < 0) {
			u32 zero = 0;
			u64 *overflow = bpf_map_lookup_elem(&agg_overflow_count, &zero);
			if (overflow)
				__sync_fetch_and_add(overflow, 1);
		}
	}
	return 0;
}

/* --- path family: delete / rename / mkdir --- */

/* The per-syscall `tp/syscalls/sys_enter_*` hooks never fired on the CI
 * kernel: all eight path hooks were entered zero times while the fd-based
 * hooks (write, ftruncate) aggregated normally. `raw_syscalls:sys_enter`
 * carries the syscall id and all six raw arguments and copies no user string
 * into the event, so one program covers the whole family.
 */
SEC("tp/raw_syscalls/sys_enter")
int trace_raw_path(struct trace_event_raw_sys_enter *ctx)
{
	const char *path;
	u32 event_type;

	switch (ctx->id) {
#ifdef __TARGET_ARCH_x86
	case 258:  /* __NR_mkdirat(dirfd, path, mode) */
		path = (const char *)ctx->args[1];
		event_type = EVENT_TYPE_DIR_CREATE;
		break;
	case 263:  /* __NR_unlinkat(dirfd, path, mode) */
		path = (const char *)ctx->args[1];
		event_type = EVENT_TYPE_FILE_DELETE;
		break;
	case 264:  /* __NR_renameat(olddirfd, oldpath, newdirfd, newpath) */
	case 316:  /* __NR_renameat2(..., flags) */
		/* newpath is args[3] */
		path = (const char *)ctx->args[3];
		event_type = EVENT_TYPE_FILE_RENAME;
		break;
	/* The plain variants exist only in the x86 table. */
	case 83:  /* __NR_mkdir(path, mode) */
		path = (const char *)ctx->args[0];
		event_type = EVENT_TYPE_DIR_CREATE;
		break;
	case 87:  /* __NR_unlink(path) */
		path = (const char *)ctx->args[0];
		event_type = EVENT_TYPE_FILE_DELETE;
		break;
	case 82:  /* __NR_rename(oldpath, newpath) */
		path = (const char *)ctx->args[1];
		event_type = EVENT_TYPE_FILE_RENAME;
		break;
#elif defined(__TARGET_ARCH_arm64)
	/* The generic table that arm64 uses; there is no plain mkdir/unlink
	 * there, only the *at forms. */
	case 34:  /* __NR_mkdirat(dirfd, path, mode) */
		path = (const char *)ctx->args[1];
		event_type = EVENT_TYPE_DIR_CREATE;
		break;
	case 35:  /* __NR_unlinkat(dirfd, path, flags) */
		path = (const char *)ctx->args[1];
		event_type = EVENT_TYPE_FILE_DELETE;
		break;
	case 38:   /* __NR_renameat(olddirfd, oldpath, newdirfd, newpath) */
	case 276:  /* __NR_renameat2(..., flags) */
		/* newpath is args[3] */
		path = (const char *)ctx->args[3];
		event_type = EVENT_TYPE_FILE_RENAME;
		break;
#endif
	default:
		return 0;
	}

	return agg_path_event(path, event_type);
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
	copy_str_to(key.detail, sizeof(key.detail), path);

	update_agg_map(&key, 1, 0);
	return 0;
}

#endif /* __PROCESS_EXT_BPF_FS_H */
