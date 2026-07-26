// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2023 Yusheng Zheng
//
// Based on sslsniff from BCC by Adrian Lopez & Mark Drayton.
// 15-Aug-2023   Yusheng Zheng   Created this.
#include <vmlinux.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_endian.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "sslsniff.h"

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUFFER_SIZE);
} rb SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, __u32);
    __type(value, size_t*);
} readbytes_ptrs SEC(".maps");

#define MAX_ENTRIES 10240

#define min(x, y)                      \
    ({                                 \
        typeof(x) _min1 = (x);         \
        typeof(y) _min2 = (y);         \
        (void)(&_min1 == &_min2);      \
        _min1 < _min2 ? _min1 : _min2; \
    })

/* ssl_data per-CPU array removed - ring buffer allocates memory directly */

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);
    __type(value, __u64);
} start_ns SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);
    __type(value, __u64);
} bufs SEC(".maps");

const volatile pid_t targ_pid = 0;
const volatile uid_t targ_uid = -1;
const volatile bool rustls_chunks_pointer_first = false;

struct rustls_iovec {
    const void *base;
    size_t len;
};

/* rustls::msgs::message::OutboundChunks is passed indirectly by the Rust ABI.
 * Single stores { 0, data, len }. Rustc 1.92 stores Multiple as
 * { chunk_count, data, start, end }, while rustc 1.95 stores it as
 * { data, chunk_count, start, end }. Userspace selects the detected ABI. */
struct rustls_outbound_chunks {
    size_t count;
    const void *data;
    size_t start_or_len;
    size_t end;
};

/* Variable-size verifier proofs do not retain the relationship between a
 * dynamic destination and copy length after unrolled iovec states merge.
 * Rustls events reserve one extra capture window so the verifier can accept
 * destination + copy_size independently; the runtime capacity clamp keeps
 * every reported byte inside event.buf. The userspace event ABI is unchanged
 * because event remains the first member. */
struct rustls_probe_data_t {
    struct probe_SSL_data_t event;
    __u8 verifier_slack[RUSTLS_VERIFIER_SLACK_SIZE];
};

static __always_inline bool trace_allowed(u32 uid, u32 pid)
{
    /* filters */
    if (targ_pid && targ_pid != pid)
        return false;
    if (targ_uid != -1) {
        if (targ_uid != uid) {
            return false;
        }
    }
    return true;
}

static __always_inline void submit_rustls_write(struct probe_SSL_data_t *data,
                                                 u32 pid, u32 tid, u32 uid,
                                                 u64 connection_id, u64 total,
                                                 u32 copied)
{
    data->timestamp_ns = bpf_ktime_get_ns();
    data->delta_ns = 0;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->connection_id = connection_id;
    data->len = total > (__u32)-1 ? (__u32)-1 : (__u32)total;
    data->buf_size = copied;
    data->buf_filled = copied > 0;
    data->rw = 1;
    data->is_handshake = false;
    bpf_get_current_comm(&data->comm, sizeof(data->comm));
    bpf_ringbuf_submit(data, 0);
}

static __always_inline u32 copy_rustls_iovec(
    struct probe_SSL_data_t *data, const struct rustls_iovec *iovec, u32 copied)
{
    size_t remaining = iovec->len;
    const char *source = iovec->base;
    size_t copy_size;
    u32 capacity;
    u32 destination;

    if (remaining == 0 || copied >= RUSTLS_MAX_CAPTURE_SIZE)
        return copied;
    capacity = RUSTLS_MAX_CAPTURE_SIZE - copied;
    destination = copied;
    /* Keep the mask visible so the verifier retains a scalar bound after
     * states from unrolled iovec loops merge. rustls_probe_data_t provides
     * one verifier-only capture window after event.buf; the runtime capacity
     * clamp still keeps copied and buf_size within the public capture window. */
    barrier_var(destination);
    destination &= RUSTLS_MAX_CAPTURE_SIZE - 1;
    copy_size = remaining;
    if (copy_size > RUSTLS_MAX_CAPTURE_SIZE)
        copy_size = RUSTLS_MAX_CAPTURE_SIZE;
    if (copy_size > capacity)
        copy_size = capacity;
    /* Reassert the independent size bound after the capacity assignment;
     * the verifier does not retain capacity <= capture size here. */
    barrier_var(copy_size);
    if (copy_size > RUSTLS_MAX_CAPTURE_SIZE)
        copy_size = RUSTLS_MAX_CAPTURE_SIZE;
    if (copy_size == 0)
        return copied;
    if (bpf_probe_read_user(data->buf + destination, copy_size, source))
        return copied;
    copied += copy_size;
    return copied;
}

SEC("uprobe/rustls_write")
int BPF_UPROBE(probe_rustls_write, void *conn, const void *buf, size_t len)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u32 copied = len > RUSTLS_MAX_CAPTURE_SIZE
        ? RUSTLS_MAX_CAPTURE_SIZE : (u32)len;

    if (!trace_allowed(uid, pid) || !buf || len == 0)
        return 0;
    struct rustls_probe_data_t *storage =
        bpf_ringbuf_reserve(&rb, sizeof(*storage), 0);
    if (!storage)
        return 0;
    struct probe_SSL_data_t *data = &storage->event;
    if (bpf_probe_read_user(data->buf, copied, buf)) {
        bpf_ringbuf_discard(data, 0);
        return 0;
    }
    submit_rustls_write(data, pid, tid, uid, (u64)conn, len, copied);
    return 0;
}

SEC("uprobe/rustls_write_vectored")
int BPF_UPROBE(probe_rustls_write_vectored, void *conn,
               const struct rustls_iovec *iovecs, size_t iovcnt)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 total = 0;
    u32 copied = 0;

    if (!trace_allowed(uid, pid) || !iovecs || iovcnt == 0)
        return 0;

    struct rustls_probe_data_t *storage =
        bpf_ringbuf_reserve(&rb, sizeof(*storage), 0);
    if (!storage)
        return 0;
    struct probe_SSL_data_t *data = &storage->event;

#pragma unroll
    for (int i = 0; i < MAX_RUSTLS_IOVECS; i++) {
        struct rustls_iovec iovec = {};

        if ((size_t)i >= iovcnt)
            break;
        if (bpf_probe_read_user(&iovec, sizeof(iovec), &iovecs[i]))
            break;
        total += iovec.len;
        copied = copy_rustls_iovec(data, &iovec, copied);
    }

    if (iovcnt > MAX_RUSTLS_IOVECS && total <= copied)
        total = (__u64)copied + 1;
    submit_rustls_write(data, pid, tid, uid, (u64)conn, total, copied);
    return 0;
}

static __always_inline int capture_rustls_plaintext_chunks(
    const struct rustls_outbound_chunks *chunks, u64 connection_id)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    struct rustls_outbound_chunks outbound = {};
    u64 total;
    u64 inspected_total = 0;
    u32 copied = 0;

    if (!trace_allowed(uid, pid) || !chunks)
        return 0;
    if (bpf_probe_read_user(&outbound, sizeof(outbound), chunks))
        return 0;

    if (rustls_chunks_pointer_first && outbound.count != 0) {
        size_t count = (size_t)outbound.data;

        outbound.data = (const void *)outbound.count;
        outbound.count = count;
    }

    if (outbound.count == 0) {
        total = outbound.start_or_len;
        if (!outbound.data || total == 0)
            return 0;
        copied = total > RUSTLS_MAX_CAPTURE_SIZE
            ? RUSTLS_MAX_CAPTURE_SIZE : (u32)total;
        struct rustls_probe_data_t *storage =
            bpf_ringbuf_reserve(&rb, sizeof(*storage), 0);
        if (!storage)
            return 0;
        struct probe_SSL_data_t *data = &storage->event;
        if (bpf_probe_read_user(data->buf, copied, outbound.data)) {
            bpf_ringbuf_discard(data, 0);
            return 0;
        }
        submit_rustls_write(data, pid, tid, uid, connection_id, total, copied);
        return 0;
    }

    /* PlaintextSink constructs Multiple with start=0 and end=total length.
     * Skip any other layout instead of risking a shifted capture. */
    if (!outbound.data || outbound.start_or_len != 0 || outbound.end == 0)
        return 0;
    total = outbound.end;

    /* OutboundChunks::Multiple may describe a sub-range ending inside a
     * slice. This probe supports the start=0, whole-slice prefix used by the
     * CLI. Reject any inspected slice that crosses end rather than reporting
     * stale bytes past the plaintext range. */
#pragma unroll
    for (int i = 0; i < MAX_RUSTLS_IOVECS; i++) {
        struct rustls_iovec iovec = {};

        if ((size_t)i >= outbound.count)
            break;
        if (bpf_probe_read_user(&iovec, sizeof(iovec),
                                &((const struct rustls_iovec *)outbound.data)[i]))
            return 0;
        if (inspected_total > total || iovec.len > total - inspected_total)
            return 0;
        inspected_total += iovec.len;
    }

    struct rustls_probe_data_t *storage =
        bpf_ringbuf_reserve(&rb, sizeof(*storage), 0);
    if (!storage)
        return 0;
    struct probe_SSL_data_t *data = &storage->event;

#pragma unroll
    for (int i = 0; i < MAX_RUSTLS_IOVECS; i++) {
        struct rustls_iovec iovec = {};

        if ((size_t)i >= outbound.count)
            break;
        if (bpf_probe_read_user(&iovec, sizeof(iovec),
                                &((const struct rustls_iovec *)outbound.data)[i]))
            break;
        copied = copy_rustls_iovec(data, &iovec, copied);
    }
    if (copied == 0) {
        bpf_ringbuf_discard(data, 0);
        return 0;
    }
    submit_rustls_write(data, pid, tid, uid, connection_id, total, copied);
    return 0;
}

SEC("uprobe/rustls_buffer_plaintext")
int BPF_UPROBE(probe_rustls_buffer_plaintext, void *state,
               const struct rustls_outbound_chunks *chunks, void *sendable)
{
    return capture_rustls_plaintext_chunks(chunks, (u64)state);
}

SEC("uprobe/do_handshake")
int BPF_UPROBE(probe_SSL_rw_enter, void *ssl, void *buf, int num) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    /* store arg info for later lookup */
    bpf_map_update_elem(&bufs, &tid, &buf, BPF_ANY);
    bpf_map_update_elem(&start_ns, &tid, &ts, BPF_ANY);
    return 0;
}

static int SSL_exit(struct pt_regs *ctx, int rw) {
    int ret = 0;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    /* store arg info for later lookup */
    u64 *bufp = bpf_map_lookup_elem(&bufs, &tid);
    if (bufp == 0)
        return 0;

    u64 *tsp = bpf_map_lookup_elem(&start_ns, &tid);
    if (!tsp)
        return 0;
    u64 delta_ns = ts - *tsp;

    int len = PT_REGS_RC(ctx);
    if (len <= 0)  // no data
        return 0;

    /* reserve space in ring buffer */
    struct probe_SSL_data_t *data = bpf_ringbuf_reserve(&rb, sizeof(*data), 0);
    if (!data)
        return 0;

    data->timestamp_ns = ts;
    data->delta_ns = delta_ns;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->connection_id = 0;
    data->len = (u32)len;
    data->buf_filled = 0;
    data->buf_size = 0;
    data->rw = rw;
    data->is_handshake = false;
    u32 buf_copy_size = min((size_t)MAX_BUF_SIZE, (size_t)len);

    bpf_get_current_comm(&data->comm, sizeof(data->comm));

    if (bufp != 0)
        ret = bpf_probe_read_user(&data->buf, buf_copy_size, (char *)*bufp);

    bpf_map_delete_elem(&bufs, &tid);
    bpf_map_delete_elem(&start_ns, &tid);

    if (!ret) {
        data->buf_filled = 1;
        data->buf_size = buf_copy_size;
    } else {
        data->buf_filled = 0;
        data->buf_size = 0;
    }

    /* submit to ring buffer */
    bpf_ringbuf_submit(data, 0);
    return 0;
}

SEC("uretprobe/SSL_read")
int BPF_URETPROBE(probe_SSL_read_exit) {
    return (SSL_exit(ctx, 0));
}

SEC("uretprobe/SSL_write")
int BPF_URETPROBE(probe_SSL_write_exit) {
    return (SSL_exit(ctx, 1));
}

SEC("uprobe/SSL_write_ex")
int BPF_UPROBE(probe_SSL_write_ex_enter, void *ssl, void *buf, size_t num, size_t *readbytes) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    bpf_map_update_elem(&bufs, &tid, &buf, BPF_ANY);
    bpf_map_update_elem(&start_ns, &tid, &ts, BPF_ANY); 
    
    bpf_map_update_elem(&readbytes_ptrs, &tid, &readbytes, BPF_ANY);

    return 0;
}

SEC("uprobe/SSL_read_ex")
int BPF_UPROBE(probe_SSL_read_ex_enter, void *ssl, void *buf, size_t num, size_t *readbytes) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    bpf_map_update_elem(&bufs, &tid, &buf, BPF_ANY);
    bpf_map_update_elem(&start_ns, &tid, &ts, BPF_ANY); 

    bpf_map_update_elem(&readbytes_ptrs, &tid, &readbytes, BPF_ANY);

    return 0;
}

static int ex_SSL_exit(struct pt_regs *ctx, int rw, int len) {
    int ret = 0;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    /* store arg info for later lookup */
    u64 *bufp = bpf_map_lookup_elem(&bufs, &tid);
    if (bufp == 0)
        return 0;

    u64 *tsp = bpf_map_lookup_elem(&start_ns, &tid);
    if (!tsp)
        return 0;
    u64 delta_ns = ts - *tsp;

    if (len <= 0)  // no data
        return 0;

    /* reserve space in ring buffer */
    struct probe_SSL_data_t *data = bpf_ringbuf_reserve(&rb, sizeof(*data), 0);
    if (!data)
        return 0;

    data->timestamp_ns = ts;
    data->delta_ns = delta_ns;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->connection_id = 0;
    data->len = (u32)len;
    data->buf_filled = 0;
    data->buf_size = 0;
    data->rw = rw;
    data->is_handshake = false;
    
    /* Explicit bounds clamping to satisfy eBPF verifier
     * Use bitmask first to ensure value range, then clamp to actual max */
    u32 buf_copy_size = (u32)len & 0xFFFFF;  /* Mask to 20 bits (1MB-1) */
    if (buf_copy_size > MAX_BUF_SIZE)
        buf_copy_size = MAX_BUF_SIZE;

    bpf_get_current_comm(&data->comm, sizeof(data->comm));

    if (bufp != 0)
        ret = bpf_probe_read_user(&data->buf, buf_copy_size, (char *)*bufp);

    bpf_map_delete_elem(&bufs, &tid);
    bpf_map_delete_elem(&start_ns, &tid);

    if (!ret) {
        data->buf_filled = 1;
        data->buf_size = buf_copy_size;
    } else {
        data->buf_filled = 0;
        data->buf_size = 0;
    }

    /* submit to ring buffer */
    bpf_ringbuf_submit(data, 0);
    
    return 0;
}

SEC("uretprobe/SSL_write_ex")
int BPF_URETPROBE(probe_SSL_write_ex_exit)
{
    u32 tid = (u32)bpf_get_current_pid_tgid();
    size_t **readbytes_ptr = bpf_map_lookup_elem(&readbytes_ptrs, &tid);
    if (!readbytes_ptr)
        return 0;

    size_t written = 0;
    bpf_probe_read_user(&written, sizeof(written), *readbytes_ptr);
    bpf_map_delete_elem(&readbytes_ptrs, &tid);

    int ret = PT_REGS_RC(ctx);
    int len = (ret == 1) ? written : 0;

    return ex_SSL_exit(ctx, 1, len);
}

SEC("uretprobe/SSL_read_ex")
int BPF_URETPROBE(probe_SSL_read_ex_exit)
{
    u32 tid = (u32)bpf_get_current_pid_tgid();
    size_t **readbytes_ptr = bpf_map_lookup_elem(&readbytes_ptrs, &tid);
    if (!readbytes_ptr)
        return 0;

    size_t written = 0;
    bpf_probe_read_user(&written, sizeof(written), *readbytes_ptr);
    bpf_map_delete_elem(&readbytes_ptrs, &tid);

    int ret = PT_REGS_RC(ctx);
    int len = (ret == 1) ? written : 0;

    return ex_SSL_exit(ctx, 0, len);
}

SEC("uprobe/do_handshake")
int BPF_UPROBE(probe_SSL_do_handshake_enter, void *ssl) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u64 ts = bpf_ktime_get_ns();
    u32 uid = bpf_get_current_uid_gid();

    if (!trace_allowed(uid, pid)) {
        return 0;
    }

    /* store arg info for later lookup */
    bpf_map_update_elem(&start_ns, &tid, &ts, BPF_ANY);
    return 0;
}

SEC("uretprobe/do_handshake")
int BPF_URETPROBE(probe_SSL_do_handshake_exit) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();
    int ret = 0;

    /* use kernel terminology here for tgid/pid: */
    u32 tgid = pid_tgid >> 32;

    /* store arg info for later lookup */
    if (!trace_allowed(tgid, pid)) {
        return 0;
    }

    u64 *tsp = bpf_map_lookup_elem(&start_ns, &tid);
    if (tsp == 0)
        return 0;

    ret = PT_REGS_RC(ctx);
    if (ret <= 0)  // handshake failed
        return 0;

    /* reserve space in ring buffer */
    struct probe_SSL_data_t *data = bpf_ringbuf_reserve(&rb, sizeof(*data), 0);
    if (!data)
        return 0;

    data->timestamp_ns = ts;
    data->delta_ns = ts - *tsp;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->connection_id = 0;
    data->len = ret;
    data->buf_filled = 0;
    data->buf_size = 0;
    data->rw = 2;
    data->is_handshake = true;
    bpf_get_current_comm(&data->comm, sizeof(data->comm));
    bpf_map_delete_elem(&start_ns, &tid);

    /* submit to ring buffer */
    bpf_ringbuf_submit(data, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
