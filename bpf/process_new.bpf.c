// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
/* process_new.bpf.c — Extended process tracer with aggregation.
 * Independent from process.bpf.c; copies core handlers + adds new modules.
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "process.h"
#include "process_new.h"

char LICENSE[] SEC("license") = "Dual BSD/GPL";

/* ========== Shared maps (existing functionality) ========== */

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, pid_t);
	__type(value, u64);
} exec_start SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 256 * 1024);
} rb SEC(".maps");

/* ========== New maps (aggregation infrastructure) ========== */

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 16384);
	__type(key, struct agg_key);
	__type(value, struct agg_value);
} event_agg_map SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, MAX_TRACKED_PIDS);
	__type(key, u32);
	__type(value, u8);
} tracked_pids SEC(".maps");

/* Optional cgroup subtree filter (used when --cgroup-filter-children is set) */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, MAX_TRACKED_CGROUPS);
	__type(key, u64);
	__type(value, u8);
} tracked_cgroups SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, u64);
} agg_overflow_count SEC(".maps");

/* Per-process memory info at exit (BPF-side, read by userspace) */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 4096);
	__type(key, u32);    /* pid */
	__type(value, struct exit_mem_info);
} exit_mem SEC(".maps");

/* write-family enter/exit pairing context (not aggregation) */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, u64);   /* pid_tgid */
	__type(value, int);  /* fd */
} write_ctx_map SEC(".maps");

/* ========== Feature flags ========== */

const volatile unsigned long long min_duration_ns = 0;
const volatile bool filter_pids = false;
const volatile bool filter_cgroup = false;
const volatile bool filter_cgroup_children = false;
const volatile unsigned long long target_cgroup_id = 0;
const volatile bool trace_fs_mutations = false;
const volatile bool trace_network = false;
const volatile bool trace_signals = false;
const volatile bool trace_memory = false;
const volatile bool trace_cow = false;

/* ========== Common helpers (before all modules) ========== */
#include "process_ext/bpf_common.h"

/* ========== Existing handlers (copied from process.bpf.c) ========== */

/* Bash readline uretprobe handler */
SEC("uretprobe//usr/bin/bash:readline")
int BPF_URETPROBE(bash_readline, const void *ret)
{
	struct event *e;
	char comm[TASK_COMM_LEN];
	u32 pid;

	if (!is_cgroup_tracked())
		return 0;

	if (!ret)
		return 0;

	bpf_get_current_comm(&comm, sizeof(comm));
	if (comm[0] != 'b' || comm[1] != 'a' || comm[2] != 's' || comm[3] != 'h' || comm[4] != 0)
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	e->type = EVENT_TYPE_BASH_READLINE;
	e->pid = pid;
	e->ppid = 0;
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));
	bpf_probe_read_user_str(&e->command, sizeof(e->command), ret);

	bpf_ringbuf_submit(e, 0);
	return 0;
}

SEC("tp/sched/sched_process_exec")
int handle_exec(struct trace_event_raw_sched_process_exec *ctx)
{
	struct task_struct *task;
	unsigned fname_off;
	struct event *e;
	pid_t pid;
	u64 ts;

	if (!is_cgroup_tracked())
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;
	task = (struct task_struct *)bpf_get_current_task();

	ts = bpf_ktime_get_ns();
	bpf_map_update_elem(&exec_start, &pid, &ts, BPF_ANY);

	if (min_duration_ns)
		return 0;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	e->type = EVENT_TYPE_PROCESS;
	e->exit_event = false;
	e->pid = pid;
	e->ppid = BPF_CORE_READ(task, real_parent, tgid);
	e->timestamp_ns = ts;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	fname_off = ctx->__data_loc_filename & 0xFFFF;
	bpf_probe_read_str(&e->filename, sizeof(e->filename), (void *)ctx + fname_off);
	/* Capture full command line with arguments from mm->arg_start */
	struct mm_struct *mm = BPF_CORE_READ(task, mm);
	unsigned long arg_start = BPF_CORE_READ(mm, arg_start);
	unsigned long arg_end = BPF_CORE_READ(mm, arg_end);
	unsigned long arg_len = arg_end - arg_start;

	if (arg_len > MAX_COMMAND_LEN - 1)
		arg_len = MAX_COMMAND_LEN - 1;

	if (arg_len > 0) {
		/*
		 * Read the full argv block using bpf_probe_read_user (not _str).
		 * _str stops at first \0 and only captures argv[0].
		 * _user reads raw bytes: "chmod\0+x\0/path\0" -- we get all args.
		 *
		 * We always read exactly MAX_COMMAND_LEN-1 bytes (a compile-time
		 * constant) so that BPF verifiers on all kernel versions can
		 * prove the access is bounded.  This may read past arg_end into
		 * environment variables, but userspace trims to arg_len.
		 *
		 * NO LOOPS in BPF -- all post-processing (\0->space, trimming)
		 * is done in userspace to stay within the verifier instruction
		 * limit on kernel 5.15 (1,000,000 insns).
		 */
		long ret = bpf_probe_read_user(e->full_command,
					MAX_COMMAND_LEN - 1,
					(void *)arg_start);
		if (ret < 0) {
			bpf_probe_read_kernel_str(e->full_command,
					  sizeof(e->full_command),
					  e->comm);
			e->full_command[MAX_COMMAND_LEN - 1] = '\0';
		} else {
			e->full_command[MAX_COMMAND_LEN - 1] = '\0';
		}
		/* Store actual arg_len in exit_code for userspace trimming.
		 * exec events don't use exit_code, so this field is free. */
		arg_len &= (MAX_COMMAND_LEN - 1);
		e->exit_code = (unsigned)arg_len;
	} else {
		bpf_probe_read_kernel_str(e->full_command,
				  sizeof(e->full_command), e->comm);
		e->exit_code = 0;
	}

	bpf_ringbuf_submit(e, 0);
	return 0;
}


SEC("tp/sched/sched_process_exit")
int handle_exit(struct trace_event_raw_sched_process_template *ctx)
{
	struct task_struct *task;
	struct event *e;
	pid_t pid, tid;
	u64 id, ts, *start_ts, duration_ns = 0;

	if (!is_cgroup_tracked())
		return 0;

	id = bpf_get_current_pid_tgid();
	pid = id >> 32;
	tid = (u32)id;

	if (pid != tid)
		return 0;

	start_ts = bpf_map_lookup_elem(&exec_start, &pid);
	ts = bpf_ktime_get_ns();
	if (start_ts)
		duration_ns = ts - *start_ts;
	else if (min_duration_ns)
		return 0;
	bpf_map_delete_elem(&exec_start, &pid);

	if (min_duration_ns && duration_ns < min_duration_ns)
		return 0;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	task = (struct task_struct *)bpf_get_current_task();

	e->type = EVENT_TYPE_PROCESS;
	e->exit_event = true;
	e->duration_ns = duration_ns;
	e->pid = pid;
	e->ppid = BPF_CORE_READ(task, real_parent, tgid);
	e->timestamp_ns = ts;
	e->exit_code = (BPF_CORE_READ(task, exit_code) >> 8) & 0xff;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	/* Capture peak RSS from task->signal->maxrss.
	 * At sched_process_exit, task->mm is already NULL (exit_mm() ran first),
	 * but signal->maxrss was set during exit_mm() and holds peak RSS in KB. */
	{
		struct exit_mem_info mem = {};
		mem.hiwater_rss = BPF_CORE_READ(task, signal, maxrss);
		if (mem.hiwater_rss > 0) {
			u32 pid_key = pid;
			bpf_map_update_elem(&exit_mem, &pid_key, &mem, BPF_ANY);
		}
	}

	bpf_ringbuf_submit(e, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_openat")
int trace_openat(struct trace_event_raw_sys_enter *ctx)
{
	struct event *e;
	pid_t pid;
	char filepath[MAX_FILENAME_LEN];
	int flags;
	const char *filename;

	if (!is_cgroup_tracked())
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;

	filename = (const char *)ctx->args[1];
	flags = (int)ctx->args[2];

	if (bpf_probe_read_user_str(filepath, sizeof(filepath), filename) < 0)
		return 0;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	e->type = EVENT_TYPE_FILE_OPERATION;
	e->pid = pid;
	e->ppid = 0;
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	bpf_probe_read_kernel_str(e->file_op.filepath, sizeof(e->file_op.filepath), filepath);
	e->file_op.fd = -1;
	e->file_op.flags = flags;
	e->file_op.is_open = true;

	bpf_ringbuf_submit(e, 0);
	return 0;
}

SEC("tp/syscalls/sys_enter_open")
int trace_open(struct trace_event_raw_sys_enter *ctx)
{
	struct event *e;
	pid_t pid;
	char filepath[MAX_FILENAME_LEN];
	int flags;
	const char *filename;

	if (!is_cgroup_tracked())
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;

	filename = (const char *)ctx->args[0];
	flags = (int)ctx->args[1];

	if (bpf_probe_read_user_str(filepath, sizeof(filepath), filename) < 0)
		return 0;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	e->type = EVENT_TYPE_FILE_OPERATION;
	e->pid = pid;
	e->ppid = 0;
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	bpf_probe_read_kernel_str(e->file_op.filepath, sizeof(e->file_op.filepath), filepath);
	e->file_op.fd = -1;
	e->file_op.flags = flags;
	e->file_op.is_open = true;

	bpf_ringbuf_submit(e, 0);
	return 0;
}

/* ========== New modules ========== */
#include "process_ext/bpf_fs.h"
#include "process_ext/bpf_write.h"
#include "process_ext/bpf_net.h"
#include "process_ext/bpf_signals.h"
#include "process_ext/bpf_mem.h"
#include "process_ext/bpf_cow.h"
