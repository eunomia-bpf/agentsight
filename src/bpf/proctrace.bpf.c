// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process tracing BPF program
// Captures process creation (execve) and stdout output
#include "vmlinux.h"
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "proctrace.h"
#include "common.h"

// Target uid filter (optional, -1 means trace all uids)
const volatile uid_t targ_uid = -1;

// Track all child processes spawned by traced processes (for stdout capture)
struct
{
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_TRACED_PROCESSES);
    __type(key, u32);
    __type(value, u32);
} child_pids SEC(".maps");

// Pending execve events - stored on enter, submitted on successful exit
struct
{
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_TRACED_PROCESSES);
    __type(key, u32);  // pid
    __type(value, struct proc_event_t);
} pending_exec_events SEC(".maps");

// Per-CPU scratch space for building events (avoids stack overflow)
struct
{
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, struct proc_event_t);
} event_scratch SEC(".maps");

// Tracepoint for execve - captures new process execution
// For syscall tracepoints, we need to use the raw tracepoint format
struct sys_enter_execve_args
{
    unsigned short common_type;
    unsigned char common_flags;
    unsigned char common_preempt_count;
    int common_pid;
    int __syscall_nr;
    const char *filename;
    const char *const *argv;
    const char *const *envp;
};

SEC("tp/syscalls/sys_enter_execve")
int trace_execve_enter(struct sys_enter_execve_args *args)
{
    const char *filename = args->filename;
    const char *const *argv = args->argv;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    // Get parent PID and TID
    u32 ppid = 0;
    u32 ptid = 0;
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    ppid = BPF_CORE_READ(task, real_parent, tgid);
    ptid = BPF_CORE_READ(task, real_parent, pid);

    // Check if we should trace this process:
    // Trace if parent process (ppid) is in traced_processes
    // This captures new child processes spawned by tracked processes
    u32 value = 1;
    u8 *ppid_traced = bpf_map_lookup_elem(&traced_processes, &ppid);

    if (ppid_traced) {
        // Also track in child_pids for stdout capture
        bpf_map_update_elem(&child_pids, &pid, &value, BPF_ANY);
    } else {
        // Parent is not in the trace list - skip
        return 0;
    }

    // Get scratch space for building event (avoids stack overflow)
    u32 scratch_key = 0;
    struct proc_event_t *event = bpf_map_lookup_elem(&event_scratch, &scratch_key);
    if (!event)
        return 0;

    // Clear event data (BPF doesn't support memset, do it manually)
    // Only clear the header fields we use, args_buf is filled incrementally
    event->timestamp_ns = ts;
    event->pid = 0;
    event->tid = 0;
    event->ppid = 0;
    event->ptid = 0;
    event->uid = 0;
    event->event_type = 0;
    event->len = 0;
    event->buf_size = 0;
    event->buf_filled = 0;
    event->args_count = 0;
    event->args_size = 0;
    // Clear comm, filename (partial clear is fine)
    for (int i = 0; i < TASK_COMM_LEN; i++)
        event->comm[i] = 0;
    for (int i = 0; i < ARGSIZE; i++)
        event->filename[i] = 0;
    // Clear args_buf partially (first ARGSIZE bytes should be enough for most cases)
    for (int i = 0; i < ARGSIZE; i++)
        event->args_buf[i] = 0;
    event->pid = pid;
    event->tid = tid;
    event->ppid = ppid;
    event->ptid = ptid;
    event->uid = uid;
    event->event_type = PROCTRACE_EVENT_EXEC;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    // Read executable filename
    bpf_probe_read_user_str(&event->filename, sizeof(event->filename), filename);

    // Read argv[0] first
    const char *argp;
    int ret = bpf_probe_read_user(&argp, sizeof(argp), &argv[0]);
    if (ret < 0)
        goto store;

    ret = bpf_probe_read_user_str(event->args_buf, ARGSIZE, argp);
    if (ret < 0)
        goto store;

    event->args_count++;
    event->args_size += ret;

    // Read remaining arguments argv[1] ... argv[TOTAL_MAX_ARGS-1]
#pragma unroll
    for (int i = 1; i < TOTAL_MAX_ARGS; i++)
    {

        ret = bpf_probe_read_user(&argp, sizeof(argp), &argv[i]);
        if (ret < 0)
            goto store;

        // NULL pointer signals end of argv
        if (!argp)
            goto store;

        // Stop if we've reached the boundary
        if (event->args_size > LAST_ARG)
            goto store;

        ret = bpf_probe_read_user_str(&event->args_buf[event->args_size], ARGSIZE, argp);
        if (ret < 0)
            goto store;

        event->args_count++;
        event->args_size += ret;
    }

    // Try to read one more argument to detect truncation
    ret = bpf_probe_read_user(&argp, sizeof(argp), &argv[TOTAL_MAX_ARGS]);
    if (ret < 0)
        goto store;

    // argv[TOTAL_MAX_ARGS] is not NULL: there are more args than we captured
    if (argp)
        event->args_count++;

store:
    // Store event in pending map - will be submitted on successful exit
    bpf_map_update_elem(&pending_exec_events, &pid, event, BPF_ANY);
    return 0;
}

// Tracepoint for execve exit - only submit event if execve succeeded
struct sys_exit_execve_args
{
    unsigned short common_type;
    unsigned char common_flags;
    unsigned char common_preempt_count;
    int common_pid;
    int __syscall_nr;
    long ret;
};

// Maximum size for exec event (header + exec_data + full args_buf)
#define MAX_EXEC_EVENT_SIZE (sizeof(struct proc_event_header) + sizeof(struct proc_exec_data) + LAST_ARG)

SEC("tp/syscalls/sys_exit_execve")
int trace_execve_exit(struct sys_exit_execve_args *args)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    long ret = args->ret;

    // Look up pending event
    struct proc_event_t *pending = bpf_map_lookup_elem(&pending_exec_events, &pid);
    if (!pending)
        return 0;

    if (ret != 0) {
        // execve failed, discard the pending event
        bpf_map_delete_elem(&pending_exec_events, &pid);
        bpf_map_delete_elem(&child_pids, &pid);
        return 0;
    }

    // Clamp args_size to valid range
    u32 args_size = pending->args_size;
    if (args_size > LAST_ARG)
        args_size = LAST_ARG;
    
    // Use fixed maximum size for ringbuffer reservation (BPF verifier requirement)
    // The actual data length is recorded in data_len field
    struct proc_event_header *event = bpf_ringbuf_reserve(&rb, MAX_EXEC_EVENT_SIZE, 0);
    if (!event) {
        bpf_map_delete_elem(&pending_exec_events, &pid);
        return 0;
    }

    // Fill header
    event->source = EVENT_SOURCE_PROC;
    event->timestamp_ns = pending->timestamp_ns;
    event->pid = pending->pid;
    event->tid = pending->tid;
    event->ppid = pending->ppid;
    event->ptid = pending->ptid;
    event->uid = pending->uid;
    event->event_type = PROCTRACE_EVENT_EXEC;
    event->data_len = sizeof(struct proc_exec_data) + args_size;
    for (int i = 0; i < TASK_COMM_LEN; i++)
        event->comm[i] = pending->comm[i];

    // Fill exec_data
    struct proc_exec_data *exec_data = (void *)(event + 1);
    exec_data->args_count = pending->args_count;
    exec_data->args_size = args_size;
    for (int i = 0; i < ARGSIZE; i++)
        exec_data->filename[i] = pending->filename[i];

    // Copy variable-length args_buf
    u8 *args_dst = (void *)(exec_data + 1);
    for (int i = 0; i < LAST_ARG && i < args_size; i++)
        args_dst[i] = pending->args_buf[i];

    bpf_ringbuf_submit(event, 0);

    // Add this process to traced_processes so its children will be traced too
    // This enables recursive tracking of all descendant processes
    u32 value = 1;
    bpf_map_update_elem(&traced_processes, &pid, &value, BPF_ANY);

    // Clean up pending event
    bpf_map_delete_elem(&pending_exec_events, &pid);
    return 0;
}

// Maximum size for stdout event (header + stdout_data + max payload)
#define MAX_STDOUT_EVENT_SIZE (sizeof(struct proc_event_header) + sizeof(struct proc_stdout_data) + MAX_STDOUT_PAYLOAD)

SEC("tp/syscalls/sys_enter_write")
int trace_write_enter(struct syscall_trace_enter *ctx) 
{
    // write syscall args: fd (args[0]), buf (args[1]), count (args[2])
    unsigned int fd = ctx->args[0];
    const char *buf = (const char *)ctx->args[1];
    u64 count = ctx->args[2];
    
    // Only capture stdout (fd=1) / stderr (fd=2) and non-empty writes
    if ((fd != 1 && fd != 2) || count == 0)
        return 0;
    
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();
    
    // Check if this process should be traced
    u8 *traced = bpf_map_lookup_elem(&child_pids, &pid);
    if (!traced)
        return 0;
    
    // Calculate actual payload size (limit to MAX_STDOUT_PAYLOAD)
    u32 payload_len = count;
    if (payload_len > MAX_STDOUT_PAYLOAD)
        payload_len = MAX_STDOUT_PAYLOAD;
    
    // Use fixed maximum size for ringbuffer reservation (BPF verifier requirement)
    // The actual data length is recorded in data_len field
    struct proc_event_header *event = bpf_ringbuf_reserve(&rb, MAX_STDOUT_EVENT_SIZE, 0);
    if (!event)
        return 0;
    
    // Fill header
    event->source = EVENT_SOURCE_PROC;
    event->timestamp_ns = ts;
    event->pid = pid;
    event->tid = tid;
    event->ppid = 0;
    event->uid = uid;
    event->event_type = PROCTRACE_EVENT_STDOUT;
    event->data_len = sizeof(struct proc_stdout_data) + payload_len;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    
    // Fill stdout_data
    struct proc_stdout_data *stdout_data = (void *)(event + 1);
    stdout_data->fd = fd;
    stdout_data->payload_len = payload_len;
    
    // Copy variable-length payload
    u8 *payload_dst = (void *)(stdout_data + 1);
    int ret = bpf_probe_read_user(payload_dst, payload_len, buf);
    if (ret != 0) {
        // Read failed, submit with zero payload
        stdout_data->payload_len = 0;
        event->data_len = sizeof(struct proc_stdout_data);
    }
    
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

    if (pid != tid)
        return 0;

    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();
    
    // Check if this process should be traced
    u8 *traced = bpf_map_lookup_elem(&child_pids, &pid);
    if (!traced)
        return 0;
    
    bpf_map_delete_elem(&child_pids, &pid);
    bpf_map_delete_elem(&traced_processes, &pid);
    // Reserve space in ring buffer for exit event (fixed size)
    struct proc_event_header *event = bpf_ringbuf_reserve(
        &rb, 
        sizeof(struct proc_event_header) + sizeof(struct proc_exit_data), 
        0
    );
    if (!event)
        return 0;
    
    // Fill header
    event->source = EVENT_SOURCE_PROC;
    event->timestamp_ns = ts;
    event->pid = pid;
    event->tid = tid;
    event->ppid = 0;
    event->uid = uid;
    event->event_type = PROCTRACE_EVENT_EXIT;
    event->data_len = sizeof(struct proc_exit_data);
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    
    // Fill exit_data
    struct proc_exit_data *exit_data = (void *)(event + 1);
    exit_data->exit_code = 0;  // TODO: Get actual exit code from sched_process_exit
    
    bpf_ringbuf_submit(event, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
