// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2023 Yusheng Zheng
//
// Based on sslsniff from BCC by Adrian Lopez & Mark Drayton.
// 15-Aug-2023   Yusheng Zheng   Created this.
#ifndef __SSLSNIFF_H
#define __SSLSNIFF_H

// A TLS record is at most 16KB, but rustls can accept several HTTP/2 frames in
// one plaintext write before fragmenting them into TLS records. 64KB covers
// those writes without returning to the old, verifier-hostile 256KB bound.
// This value is load-bearing: the conventional SSL probes call
//     bpf_ringbuf_reserve(&rb, sizeof(*data), 0)
// and struct probe_SSL_data_t embeds buf[MAX_BUF_SIZE], so each such event
// reserves the worst case regardless of payload. At 512KB per event a 2MB ring
// held only 3 concurrent events; the 4th reserve returned NULL and the handler
// dropped the event silently. 64KB against a 16MB ring gives 255 conventional
// SSL events. Rustls vectored probes reserve an additional 64KB verifier
// window, leaving 127 concurrent events. Oversized reads take the existing
// truncation path instead of vanishing.
#define MAX_BUF_SIZE (64 * 1024)
#define RING_BUFFER_SIZE (16 * 1024 * 1024)  // 16MB ring buffer
#define TASK_COMM_LEN 16
#define MAX_RUSTLS_IOVECS 8
#define RUSTLS_MAX_CAPTURE_SIZE MAX_BUF_SIZE
#define RUSTLS_VERIFIER_SLACK_SIZE RUSTLS_MAX_CAPTURE_SIZE
_Static_assert((RUSTLS_MAX_CAPTURE_SIZE
		& (RUSTLS_MAX_CAPTURE_SIZE - 1)) == 0,
	       "rustls verifier mask requires a power-of-two capture size");

struct probe_SSL_data_t {
    __u64 timestamp_ns;
    __u64 delta_ns;
    __u32 pid;
    __u32 tid;
    __u32 uid;
    __u64 connection_id;    // Stable TLS connection identity when available
    __u32 len;
    __u32 buf_size;         // Actual bytes copied to buf
    int buf_filled;
    int rw;
    char comm[TASK_COMM_LEN];
    __u8 buf[MAX_BUF_SIZE];
    int is_handshake;
};

#endif /* __SSLSNIFF_H */
