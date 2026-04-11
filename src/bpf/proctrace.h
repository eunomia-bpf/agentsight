// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process tracing BPF program header
// Captures process creation (execve) and stdout output
#ifndef __PROCTRACE_H
#define __PROCTRACE_H

#define MAX_BUF_SIZE     4096
#define TASK_COMM_LEN    16
#define ARGSIZE          128   // Max bytes per single argument
#define TOTAL_MAX_ARGS   20    // Max number of arguments to read
#define LAST_ARG         (TOTAL_MAX_ARGS * ARGSIZE)  // Boundary check

// Maximum payload size for stdout data in a single event
#define MAX_STDOUT_PAYLOAD 1024

typedef signed char         s8;
typedef unsigned char       u8;
typedef signed short        s16;
typedef unsigned short      u16;
typedef signed int          s32;
typedef unsigned int        u32;
typedef signed long long    s64;
typedef unsigned long long  u64;
typedef _Bool bool;

// Event types (using unique prefix to avoid conflicts with kernel headers)
enum proctrace_event_type {
    PROCTRACE_EVENT_EXEC   = 1,  // Process execution (execve)
    PROCTRACE_EVENT_STDOUT = 2,  // Stdout output
    PROCTRACE_EVENT_EXIT   = 3,  // Process exit
};

// Common event header - all events start with this
struct proc_event_header {
    u32 source;             // EVENT_SOURCE_PROC (from common.h)
    u64 timestamp_ns;
    u32 pid;
    u32 tid;
    u32 ppid;               // Parent PID
    u32 ptid;               // Parent TID (thread ID that spawned this process)
    u32 uid;
    u32 event_type;         // enum proctrace_event_type
    u32 data_len;           // Length of variable data following this header
    char comm[TASK_COMM_LEN];
};

// Exec event specific data (variable length, follows header)
struct proc_exec_data {
    u32 args_count;         // Number of argv entries read
    u32 args_size;          // Total bytes used in args_buf
    char filename[ARGSIZE]; // Executable path from execve
    // Followed by: char args_buf[args_size] (variable length)
};

// Stdout event specific data (variable length, follows header)
struct proc_stdout_data {
    u32 fd;                 // File descriptor (1 for stdout, 2 for stderr)
    u32 payload_len;        // Actual payload length
    // Followed by: u8 payload[payload_len] (variable length)
};

// Exit event specific data (fixed length, follows header)
struct proc_exit_data {
    s32 exit_code;          // Process exit code
};

// Legacy process event structure (kept for backward compatibility)
// NOTE: This is kept for existing code, new code should use variable-length events
struct proc_event_t {
    u64 timestamp_ns;
    u32 pid;
    u32 tid;
    u32 ppid;               // Parent PID
    u32 ptid;               // Parent TID (thread ID that spawned this process)
    u32 uid;
    u32 event_type;         // enum proctrace_event_type
    u32 len;                // Data length for stdout
    u32 buf_size;           // Actual bytes copied to buf
    int buf_filled;
    u32 args_count;         // Number of argv entries read
    u32 args_size;          // Total bytes used in args_buf
    char comm[TASK_COMM_LEN];
    char filename[ARGSIZE]; // Executable path from execve
    char args_buf[TOTAL_MAX_ARGS * ARGSIZE]; // Argv strings packed end-to-end
    u8  buf[MAX_BUF_SIZE];  // stdout data or other payload
};

#endif /* __PROCTRACE_H */
