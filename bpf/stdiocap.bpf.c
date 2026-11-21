// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
#include <vmlinux.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "stdiocap.h"

struct io_args_t {
	__u64 buf;
	__u64 start_ns;
	__s32 fd;
	__u8 is_read;
};

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, RING_BUFFER_SIZE);
} rb SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, __u64);
	__type(value, struct io_args_t);
} io_args SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, __u32);
	__type(value, __u64);
} tracked_pids SEC(".maps");

const volatile __u32 targ_pid = 0;
const volatile __u32 targ_uid = 0xffffffffU;
const volatile bool trace_stdio_only = true;
const volatile __u32 max_capture_bytes = MAX_BUF_SIZE;
const volatile bool use_tracked_pids = false;

/* Where a run's writes get lost, counted in the kernel so an empty capture
 * names the path instead of only reporting that nothing arrived. A zero
 * event count with zeroes on the others means no hook ran at all. */
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, STDIO_STAT_COUNT);
	__type(key, __u32);
	__type(value, __u64);
} stats SEC(".maps");

static __always_inline void count(enum stdiocap_stat slot)
{
	__u32 key = slot;
	__u64 *value = bpf_map_lookup_elem(&stats, &key);

	if (value)
		__sync_fetch_and_add(value, 1);
}

static __always_inline bool tracked_or_descendant(__u32 pid)
{
	struct task_struct *task;
	__u64 present = 1;

	if (bpf_map_lookup_elem(&tracked_pids, &pid))
		return true;

	task = (struct task_struct *)bpf_get_current_task();
#pragma unroll
	for (int i = 0; i < 8; i++) {
		struct task_struct *parent = BPF_CORE_READ(task, real_parent);
		__u32 ppid;

		if (!parent)
			break;
		ppid = BPF_CORE_READ(parent, tgid);
		if (!ppid || ppid == pid)
			break;
		if (bpf_map_lookup_elem(&tracked_pids, &ppid)) {
			bpf_map_update_elem(&tracked_pids, &pid, &present, BPF_ANY);
			return true;
		}
		task = parent;
	}

	return false;
}

static __always_inline bool trace_allowed(__u32 uid, __u32 pid, int fd)
{
	/* Count the branch that rejects, so "every enter filtered" says which
	 * condition dropped the writer instead of only that one did. */
	if (targ_uid != 0xffffffffU && targ_uid != uid) {
		count(STDIO_STAT_FILTER_UID);
		return false;
	}
	if (trace_stdio_only && (fd < 0 || fd > 2)) {
		count(STDIO_STAT_FILTER_FD);
		return false;
	}
	if (use_tracked_pids) {
		if (tracked_or_descendant(pid))
			return true;
		count(STDIO_STAT_FILTER_NOT_TRACKED);
		return false;
	}
	if (targ_pid && targ_pid != pid) {
		count(STDIO_STAT_FILTER_NOT_TRACKED);
		return false;
	}
	return true;
}

static __always_inline int enter_common(int fd, const void *buf, bool is_read)
{
	__u64 pid_tgid = bpf_get_current_pid_tgid();
	__u32 pid = pid_tgid >> 32;
	__u32 uid = bpf_get_current_uid_gid();
	struct io_args_t args = {};

	count(STDIO_STAT_ENTER);
	if (!trace_allowed(uid, pid, fd)) {
		count(STDIO_STAT_ENTER_FILTERED);
		return 0;
	}

	args.buf = (__u64)buf;
	args.start_ns = bpf_ktime_get_ns();
	args.fd = fd;
	args.is_read = is_read;
	bpf_map_update_elem(&io_args, &pid_tgid, &args, BPF_ANY);
	return 0;
}

static __always_inline int exit_common(long ret)
{
	__u64 pid_tgid = bpf_get_current_pid_tgid();
	__u32 pid = pid_tgid >> 32;
	__u32 tid = (__u32)pid_tgid;
	__u32 uid = bpf_get_current_uid_gid();
	struct io_args_t *args;
	struct stdiocap_event_t *event;
	__u32 copy_size;

	args = bpf_map_lookup_elem(&io_args, &pid_tgid);
	if (!args) {
		count(STDIO_STAT_EXIT_NO_ARGS);
		return 0;
	}

	if (ret <= 0) {
		count(STDIO_STAT_EXIT_ERROR);
		bpf_map_delete_elem(&io_args, &pid_tgid);
		return 0;
	}

	event = bpf_ringbuf_reserve(&rb, sizeof(*event), 0);
	if (!event) {
		count(STDIO_STAT_RINGBUF_FULL);
		bpf_map_delete_elem(&io_args, &pid_tgid);
		return 0;
	}

	event->timestamp_ns = bpf_ktime_get_ns();
	event->delta_ns = event->timestamp_ns - args->start_ns;
	event->pid = pid;
	event->tid = tid;
	event->uid = uid;
	event->fd = args->fd;
	event->len = ret > 0xffffffffL ? 0xffffffffU : (__u32)ret;
	event->is_read = args->is_read;
	bpf_get_current_comm(&event->comm, sizeof(event->comm));

	copy_size = event->len;
	if (copy_size > max_capture_bytes)
		copy_size = max_capture_bytes;
	if (copy_size > MAX_BUF_SIZE)
		copy_size = MAX_BUF_SIZE;
	event->buf_size = copy_size;

	if (copy_size > 0)
		bpf_probe_read_user(event->buf, copy_size, (const void *)args->buf);

	count(STDIO_STAT_EVENT);
	bpf_ringbuf_submit(event, 0);
	bpf_map_delete_elem(&io_args, &pid_tgid);
	return 0;
}

SEC("tp/syscalls/sys_enter_read")
int trace_enter_read(struct trace_event_raw_sys_enter *ctx)
{
	return enter_common((int)ctx->args[0], (const void *)ctx->args[1], true);
}

SEC("tp/syscalls/sys_exit_read")
int trace_exit_read(struct trace_event_raw_sys_exit *ctx)
{
	return exit_common(ctx->ret);
}

SEC("tp/syscalls/sys_enter_write")
int trace_enter_write(struct trace_event_raw_sys_enter *ctx)
{
	return enter_common((int)ctx->args[0], (const void *)ctx->args[1], false);
}

SEC("tp/syscalls/sys_exit_write")
int trace_exit_write(struct trace_event_raw_sys_exit *ctx)
{
	return exit_common(ctx->ret);
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";
