// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
/* Copyright (c) 2020 Facebook */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "process.h"
#include "process_ext/bpf_state.h"

#define S_IFMT 00170000
#define S_IFREG 0100000
#define FMODE_READ 1
#define FMODE_WRITE 2
#define FMODE_EXEC 0x20
#define FMODE_EXEC_FLAG_OLD 040000000
#define PF_KTHREAD 0x00200000
#define SB_KERNMOUNT (1 << 22)
#define NSFS_MAGIC 0x6e736673
#define PID_FS_MAGIC 0x50494446
#define INIT_USER_NS_INO 0xEFFFFFFDU
#define EEXIST 17
#define EINVAL 22

char LICENSE[] SEC("license") = "Dual BSD/GPL";

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, pid_t);
	__type(value, u64);
} exec_start SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 1024 * 1024);
} rb SEC(".maps");

/* A failed ring reservation is visible even if no later event is delivered. */
struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, u64);
} file_open_dropped SEC(".maps");

struct file_open_key {
	u64 start_time;
	u64 exec_id;
	u64 mnt;
	u64 dentry;
	u64 ino;
	u32 tgid;
	u32 access_layer;
};

struct {
	__uint(type, BPF_MAP_TYPE_LRU_HASH);
	__uint(max_entries, 65536);
	__type(key, struct file_open_key);
	__type(value, u8);
} file_opens_seen SEC(".maps");

const volatile unsigned long long min_duration_ns = 0;

#include "process_ext/bpf_common.h"

/* Bash readline uretprobe handler */
SEC("uretprobe//usr/bin/bash:readline")
int BPF_URETPROBE(bash_readline, const void *ret)
{
	struct event *e;
	char comm[TASK_COMM_LEN];
	u32 pid;

	if (!ret)
		return 0;
	if (!is_cgroup_tracked())
		return 0;

	/* Check if this is actually bash */
	bpf_get_current_comm(&comm, sizeof(comm));
	if (comm[0] != 'b' || comm[1] != 'a' || comm[2] != 's' || comm[3] != 'h' || comm[4] != 0)
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;

	/* Reserve sample from BPF ringbuf */
	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	/* Fill out the sample with bash readline data */
	e->type = EVENT_TYPE_BASH_READLINE;
	e->pid = pid;
	e->ppid = 0; /* Not relevant for bash commands */
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));
	bpf_probe_read_user_str(&e->command, sizeof(e->command), ret);

	/* Submit to user-space for post-processing */
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

	/* Get process info */
	pid = bpf_get_current_pid_tgid() >> 32;
	task = (struct task_struct *)bpf_get_current_task();

	/* remember time exec() was executed for this PID */
	ts = bpf_ktime_get_ns();
	bpf_map_update_elem(&exec_start, &pid, &ts, BPF_ANY);

	/* don't emit exec events when minimum duration is specified */
	if (min_duration_ns)
		return 0;

	/* reserve sample from BPF ringbuf */
	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	/* fill out the sample with data */
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

	/* successfully submit it to user-space for post-processing */
	bpf_ringbuf_submit(e, 0);
	return 0;
}

SEC("tp/sched/sched_process_exit")
int handle_exit(struct trace_event_raw_sched_process_template* ctx)
{
	struct task_struct *task;
	struct event *e;
	pid_t pid, tid;
	u64 id, ts, *start_ts, duration_ns = 0;

	if (!is_cgroup_tracked())
		return 0;

	/* get PID and TID of exiting thread/process */
	id = bpf_get_current_pid_tgid();
	pid = id >> 32;
	tid = (u32)id;

	/* ignore thread exits */
	if (pid != tid)
		return 0;

	/* if we recorded start of the process, calculate lifetime duration */
	start_ts = bpf_map_lookup_elem(&exec_start, &pid);
	ts = bpf_ktime_get_ns();
	if (start_ts)
		duration_ns = ts - *start_ts;
	else if (min_duration_ns)
		return 0;
	bpf_map_delete_elem(&exec_start, &pid);

	/* if process didn't live long enough, return early */
	if (min_duration_ns && duration_ns < min_duration_ns)
		return 0;

	/* reserve sample from BPF ringbuf */
	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	/* fill out the sample with data */
	task = (struct task_struct *)bpf_get_current_task();

	e->type = EVENT_TYPE_PROCESS;
	e->exit_event = true;
	e->duration_ns = duration_ns;
	e->pid = pid;
	e->ppid = BPF_CORE_READ(task, real_parent, tgid);
	e->timestamp_ns = ts;
	e->exit_code = (BPF_CORE_READ(task, exit_code) >> 8) & 0xff;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	{
		struct exit_mem_info mem = {};
		mem.hiwater_rss = BPF_CORE_READ(task, signal, maxrss);
		if (mem.hiwater_rss > 0) {
			u32 pid_key = pid;
			bpf_map_update_elem(&exit_mem, &pid_key, &mem, BPF_ANY);
		}
	}

	/* send data to user-space for post-processing */
	bpf_ringbuf_submit(e, 0);
	return 0;
}

/* Syscall tracepoint for openat */
SEC("tp/syscalls/sys_enter_openat")
int trace_openat(struct trace_event_raw_sys_enter *ctx)
{
	struct event *e;
	pid_t pid;
	char filepath[MAX_FILENAME_LEN];
	int dfd, flags;
	const char *filename;

	if (!is_cgroup_tracked())
		return 0;

	pid = bpf_get_current_pid_tgid() >> 32;

	/* Get syscall arguments */
	dfd = (int)ctx->args[0];
	filename = (const char *)ctx->args[1];
	flags = (int)ctx->args[2];

	/* Read filename from user space */
	if (bpf_probe_read_user_str(filepath, sizeof(filepath), filename) < 0)
		return 0;

	/* Reserve sample from BPF ringbuf */
	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	/* Fill out the event */
	e->type = EVENT_TYPE_FILE_OPERATION;
	e->pid = pid;
	e->ppid = 0; /* Will be filled if needed */
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	/* Copy filepath and set file open details */
	bpf_probe_read_kernel_str(e->file_op.filepath, sizeof(e->file_op.filepath), filepath);
	e->file_op.fd = -1; /* Will be set on return if needed */
	e->file_op.flags = flags;
	e->file_op.is_open = true;
	e->file_op.resolved = false;

	/* Submit to user-space */
	bpf_ringbuf_submit(e, 0);
	return 0;
}

/* Syscall tracepoint for open */
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

	/* Get syscall arguments */
	filename = (const char *)ctx->args[0];
	flags = (int)ctx->args[1];

	/* Read filename from user space */
	if (bpf_probe_read_user_str(filepath, sizeof(filepath), filename) < 0)
		return 0;

	/* Reserve sample from BPF ringbuf */
	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e)
		return 0;

	/* Fill out the event */
	e->type = EVENT_TYPE_FILE_OPERATION;
	e->pid = pid;
	e->ppid = 0;
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));

	/* Copy filepath and set file open details */
	bpf_probe_read_kernel_str(e->file_op.filepath, sizeof(e->file_op.filepath), filepath);
	e->file_op.fd = -1;
	e->file_op.flags = flags;
	e->file_op.is_open = true;
	e->file_op.resolved = false;

	/* Submit to user-space */
	bpf_ringbuf_submit(e, 0);
	return 0;
}

static __always_inline void count_file_open_drop(void)
{
	u32 zero = 0;
	u64 *count = bpf_map_lookup_elem(&file_open_dropped, &zero);
	if (count)
		__sync_fetch_and_add(count, 1);
}

/* security_file_open runs after path resolution for open/openat/openat2,
 * io_uring and exec, including the ELF interpreter. fexit excludes denied
 * opens. The old syscall hooks remain available on kernels lacking this hook
 * or bpf_d_path. */
SEC("fexit/security_file_open")
int BPF_PROG(trace_file_open_exit, struct file *file)
{
	struct event *e;
	struct file_open_key key = {};
	struct task_struct *task, *leader;
	struct inode *inode;
	struct super_block *sb;
	struct vfsmount *vfs;
	struct mount *mnt;
	u64 ret;
	u32 mode, flags, access = 0;
	bool layer;
	u8 present = 1;
	long path_len;

	if (bpf_get_func_ret(ctx, &ret) || (int)ret || !is_event_tracked())
		return 0;
	task = (struct task_struct *)bpf_get_current_task();
	if (BPF_CORE_READ(task, flags) & PF_KTHREAD)
		return 0;
	inode = BPF_CORE_READ(file, f_inode);
	if ((BPF_CORE_READ(inode, i_mode) & S_IFMT) != S_IFREG)
		return 0;
	sb = BPF_CORE_READ(inode, i_sb);
	if (BPF_CORE_READ(sb, s_magic) == NSFS_MAGIC ||
	    BPF_CORE_READ(sb, s_magic) == PID_FS_MAGIC)
		return 0;
	vfs = BPF_CORE_READ(file, f_path.mnt);
	mnt = (void *)vfs - bpf_core_field_offset(struct mount, mnt);
	layer = ((long)BPF_CORE_READ(mnt, mnt_ns) == -EINVAL &&
		 !(BPF_CORE_READ(sb, s_flags) & SB_KERNMOUNT)) ||
		inode != BPF_CORE_READ(file, f_path.dentry, d_inode);
	/* Container-runtime overlay mounts use credentials from the initial
	 * user namespace. Their layer opens duplicate a logical file open. */
	if (layer && BPF_CORE_READ(file, f_cred, user_ns, ns.inum) == INIT_USER_NS_INO)
		return 0;

	mode = BPF_CORE_READ(file, f_mode);
	flags = BPF_CORE_READ(file, f_flags);
	if (mode & FMODE_READ)
		access |= FILE_ACCESS_READ;
	if (mode & FMODE_WRITE)
		access |= FILE_ACCESS_WRITE;
	/* On newer kernels __FMODE_EXEC is 0x20 in f_flags at this hook;
	 * older kernels can use the high flag bit or f_mode. */
	if ((mode & FMODE_EXEC) || (flags & (FMODE_EXEC | FMODE_EXEC_FLAG_OLD)))
		access |= FILE_ACCESS_EXEC;
	leader = BPF_CORE_READ(task, group_leader);
	key.start_time = BPF_CORE_READ(leader, start_time);
	key.exec_id = BPF_CORE_READ(leader, self_exec_id);
	key.tgid = bpf_get_current_pid_tgid() >> 32;
	key.mnt = (u64)vfs;
	key.dentry = (u64)BPF_CORE_READ(file, f_path.dentry);
	key.ino = BPF_CORE_READ(inode, i_ino);
	key.access_layer = access | (layer << 8);
	if (bpf_map_update_elem(&file_opens_seen, &key, &present, BPF_NOEXIST) == -EEXIST)
		return 0;

	e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
	if (!e) {
		bpf_map_delete_elem(&file_opens_seen, &key);
		count_file_open_drop();
		return 0;
	}
	e->type = EVENT_TYPE_FILE_OPERATION;
	e->pid = key.tgid;
	e->ppid = 0;
	e->exit_code = 0;
	e->duration_ns = 0;
	e->timestamp_ns = bpf_ktime_get_ns();
	e->exit_event = false;
	bpf_get_current_comm(&e->comm, sizeof(e->comm));
	e->file_op.fd = -1;
	e->file_op.flags = flags;
	e->file_op.is_open = true;
	e->file_op.resolved = true;
	e->file_op.layer = layer;
	e->file_op.access = access;
	e->file_op.dev = BPF_CORE_READ(sb, s_dev);
	e->file_op.ino = key.ino;
	path_len = bpf_d_path(&file->f_path, e->file_op.filepath,
			      sizeof(e->file_op.filepath));
	e->file_op.path_error = path_len < 0 ? (int)path_len : 0;
	if (path_len < 1)
		e->file_op.filepath[0] = '\0';
	bpf_ringbuf_submit(e, 0);
	return 0;
}

#include "process_ext/bpf_fs.h"
#include "process_ext/bpf_write.h"
#include "process_ext/bpf_net.h"
#include "process_ext/bpf_signals.h"
#include "process_ext/bpf_mem.h"
#include "process_ext/bpf_cow.h"
