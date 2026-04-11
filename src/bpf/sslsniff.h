// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2023 Yusheng Zheng
//
// Based on sslsniff from BCC by Adrian Lopez & Mark Drayton.
// 15-Aug-2023   Yusheng Zheng   Created this.
#ifndef __SSLSNIFF_H
#define __SSLSNIFF_H

#define MAX_BUF_SIZE (8 * 512 * 1024)  // 512KB eBPF buffer size (kernel limit)
#define TASK_COMM_LEN 16

typedef signed char         s8;
typedef unsigned char       u8;
typedef signed short        s16;
typedef unsigned short      u16;
typedef signed int          s32;
typedef unsigned int        u32;
typedef signed long long    s64;
typedef unsigned long long  u64;
typedef _Bool bool;
typedef u32 __be32;
typedef u64 __be64;

struct probe_SSL_data_t {
    u32 source;           // EVENT_SOURCE_SSL (from common.h)
    u64 timestamp_ns;
    u64 delta_ns;
    u32 pid;
    u32 tid;
    u32 uid;
    u32 len;
    u32 buf_size;         // Actual bytes copied to buf
    int buf_filled;
    int rw;
    char comm[TASK_COMM_LEN];
    u8 buf[MAX_BUF_SIZE];
    int is_handshake;
    u64 ssl_ptr;          // SSL connection pointer for connection tracking
};

#endif /* __SSLSNIFF_H */
