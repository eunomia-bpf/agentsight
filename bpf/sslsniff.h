// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2023 Yusheng Zheng
//
// Based on sslsniff from BCC by Adrian Lopez & Mark Drayton.
// 15-Aug-2023   Yusheng Zheng   Created this.
#ifndef __SSLSNIFF_H
#define __SSLSNIFF_H

// A TLS record is at most 16KB, so 32KB is ample for one SSL_read/SSL_write.
// This value is load-bearing: the probes call
//     bpf_ringbuf_reserve(&rb, sizeof(*data), 0)
// and struct probe_SSL_data_t embeds buf[MAX_BUF_SIZE], so EVERY event reserves
// the worst case regardless of payload. At 512KB per event a 2MB ring held only
// 3 concurrent events; the 4th reserve returned NULL and the handler dropped the
// event silently (no truncated flag, since the event is never created). Responses
// whose HTTP headers alone filled those slots lost their body with no signal.
// 32KB against a 16MB ring gives 511 concurrent events; oversized reads now take
// the existing truncation path instead of vanishing.
#define MAX_BUF_SIZE (32 * 1024)
#define RING_BUFFER_SIZE (16 * 1024 * 1024)  // 16MB ring buffer
#define TASK_COMM_LEN 16
#define MAX_RUSTLS_IOVECS 8
#define RUSTLS_COPY_CHUNK_SIZE (4 * 1024)
#define RUSTLS_MAX_CAPTURE_SIZE MAX_BUF_SIZE
#define MAX_RUSTLS_CHUNKS_PER_IOV 8

struct probe_SSL_data_t {
    __u64 timestamp_ns;
    __u64 delta_ns;
    __u32 pid;
    __u32 tid;
    __u32 uid;
    __u32 len;
    __u32 buf_size;         // Actual bytes copied to buf
    int buf_filled;
    int rw;
    char comm[TASK_COMM_LEN];
    __u8 buf[MAX_BUF_SIZE];
    int is_handshake;
};

#endif /* __SSLSNIFF_H */
