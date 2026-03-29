// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process monitor BPF program
// Lightweight monitoring of process creation and exit
#include "vmlinux.h"
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "procmon.h"
#define NO_TRACED_PROCESSES_MAP
#include "common.h"

// Tracepoint for execve exit - captures process execution after it completes
// NOTE: We use sys_exit_execve instead of sys_enter_execve because:
// - At sys_enter_execve, the process hasn't completed execve yet
// - bpf_get_current_comm() returns the OLD process name
// - Reading /proc/[pid]/comm returns old values
// - At sys_exit_execve, execve has completed and process info is updated
SEC("tp/syscalls/sys_exit_execve")
int trace_execve_exit(struct trace_event_raw_sys_exit *ctx)
{
    // Check execve return value - skip if failed
    // ret == 0: success, ret < 0: error (e.g., -ENOENT, -EACCES)
    if (ctx->ret != 0)
        return 0;

    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    // Get parent PID
    u32 ppid = 0;
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    ppid = BPF_CORE_READ(task, real_parent, tgid);

    // Reserve space in ring buffer
    struct procmon_event *event = bpf_ringbuf_reserve(&rb, sizeof(*event), 0);
    if (!event)
        return 0;

    // Fill event
    event->source = EVENT_SOURCE_PROCMON;
    event->timestamp_ns = ts;
    event->pid = pid;
    event->tid = tid;
    event->ppid = ppid;
    event->uid = uid;
    event->event_type = PROCMON_EVENT_EXEC;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));

    bpf_ringbuf_submit(event, 0);
    return 0;
}

// Tracepoint for process exit
SEC("tp/sched/sched_process_exit")
int trace_process_exit(void *ctx)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;

    // Only trace main thread exit (pid == tid)
    if (pid != tid)
        return 0;

    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    // Reserve space in ring buffer
    struct procmon_event *event = bpf_ringbuf_reserve(&rb, sizeof(*event), 0);
    if (!event)
        return 0;

    // Fill event
    event->source = EVENT_SOURCE_PROCMON;
    event->timestamp_ns = ts;
    event->pid = pid;
    event->tid = tid;
    event->ppid = 0;
    event->uid = uid;
    event->event_type = PROCMON_EVENT_EXIT;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));

    bpf_ringbuf_submit(event, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
