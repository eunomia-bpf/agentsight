// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process monitor BPF program header
// Lightweight process creation and exit monitoring
#ifndef __PROCMON_H
#define __PROCMON_H

#define TASK_COMM_LEN    16

typedef signed char         s8;
typedef unsigned char       u8;
typedef signed short        s16;
typedef unsigned short      u16;
typedef signed int          s32;
typedef unsigned int        u32;
typedef signed long long    s64;
typedef unsigned long long  u64;

// Event types for process monitor
enum procmon_event_type {
    PROCMON_EVENT_EXEC  = 1,  // Process exec
    PROCMON_EVENT_EXIT  = 2,  // Process exit
};

// Process monitor event - fixed size for simplicity
struct procmon_event {
    u32 source;             // EVENT_SOURCE_PROCMON
    u64 timestamp_ns;
    u32 pid;
    u32 tid;
    u32 ppid;               // Parent PID
    u32 uid;
    u32 event_type;         // enum procmon_event_type
    char comm[TASK_COMM_LEN];
};

#endif /* __PROCMON_H */
