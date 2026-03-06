// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2026 Yusheng Zheng
//
// Browser-focused plaintext tracing for Chrome/Firefox.
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "browsertrace.h"

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUFFER_SIZE);
} rb SEC(".maps");

#define MAX_ENTRIES 10240

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

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);
    __type(value, __u64);
} nss_import_fds SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u64);
    __type(value, __u8);
} nss_ssl_fds SEC(".maps");

const volatile pid_t targ_pid = 0;
const volatile uid_t targ_uid = -1;

static __always_inline bool trace_allowed(u32 uid, u32 pid)
{
    if (targ_pid && targ_pid != pid)
        return false;
    if (targ_uid != (uid_t)-1 && targ_uid != uid)
        return false;
    return true;
}

static __always_inline int store_rw_enter(void *buf)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();

    if (!trace_allowed(uid, pid))
        return 0;

    bpf_map_update_elem(&bufs, &tid, &buf, BPF_ANY);
    bpf_map_update_elem(&start_ns, &tid, &ts, BPF_ANY);
    return 0;
}

static __always_inline int emit_plaintext_buffer(void *buf, size_t len, int rw)
{
    struct probe_SSL_data_t *data;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();
    u32 buf_copy_size;
    int ret;

    if (!trace_allowed(uid, pid))
        return 0;
    if ((long)len <= 0 || len > MAX_BUF_SIZE * 8ULL)
        return 0;

    data = bpf_ringbuf_reserve(&rb, sizeof(*data), 0);
    if (!data)
        return 0;

    data->timestamp_ns = ts;
    data->delta_ns = 0;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->len = len > 0xffffffffULL ? 0xffffffffU : (u32)len;
    data->buf_filled = 0;
    data->buf_size = 0;
    data->rw = rw;
    data->is_handshake = false;

    buf_copy_size = data->len;
    if (buf_copy_size > MAX_BUF_SIZE)
        buf_copy_size = MAX_BUF_SIZE;

    bpf_get_current_comm(&data->comm, sizeof(data->comm));

    ret = bpf_probe_read_user(&data->buf, buf_copy_size, buf);
    if (!ret) {
        data->buf_filled = 1;
        data->buf_size = buf_copy_size;
    }

    bpf_ringbuf_submit(data, 0);
    return 0;
}

static __always_inline bool is_tracked_nss_fd(void *fd)
{
    u64 key = (u64)fd;

    return bpf_map_lookup_elem(&nss_ssl_fds, &key) != NULL;
}

static __always_inline int browsertrace_exit(struct pt_regs *ctx, int rw)
{
    struct probe_SSL_data_t *data;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    u32 tid = (u32)pid_tgid;
    u32 uid = bpf_get_current_uid_gid();
    u64 ts = bpf_ktime_get_ns();
    u64 *bufp;
    u64 *tsp;
    u32 buf_copy_size;
    int len;
    int ret = 0;

    if (!trace_allowed(uid, pid))
        return 0;

    bufp = bpf_map_lookup_elem(&bufs, &tid);
    if (!bufp)
        return 0;

    tsp = bpf_map_lookup_elem(&start_ns, &tid);
    if (!tsp)
        return 0;

    len = PT_REGS_RC(ctx);
    if (len <= 0)
        return 0;

    data = bpf_ringbuf_reserve(&rb, sizeof(*data), 0);
    if (!data)
        return 0;

    data->timestamp_ns = ts;
    data->delta_ns = ts - *tsp;
    data->pid = pid;
    data->tid = tid;
    data->uid = uid;
    data->len = (u32)len;
    data->buf_filled = 0;
    data->buf_size = 0;
    data->rw = rw;
    data->is_handshake = false;

    buf_copy_size = (u32)len;
    if (buf_copy_size > MAX_BUF_SIZE)
        buf_copy_size = MAX_BUF_SIZE;

    bpf_get_current_comm(&data->comm, sizeof(data->comm));
    ret = bpf_probe_read_user(&data->buf, buf_copy_size, (void *)*bufp);

    bpf_map_delete_elem(&bufs, &tid);
    bpf_map_delete_elem(&start_ns, &tid);

    if (!ret) {
        data->buf_filled = 1;
        data->buf_size = buf_copy_size;
    }

    bpf_ringbuf_submit(data, 0);
    return 0;
}

SEC("uprobe/PR_Write")
int BPF_UPROBE(probe_nss_rw_enter, void *fd, void *buf, int num)
{
    if (!is_tracked_nss_fd(fd))
        return 0;

    return store_rw_enter(buf);
}

SEC("uprobe/SSL_ImportFD")
int BPF_UPROBE(probe_nss_import_fd_enter, void *model, void *fd)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 tid = (u32)pid_tgid;
    u64 fd_ptr = (u64)fd;

    bpf_map_update_elem(&nss_import_fds, &tid, &fd_ptr, BPF_ANY);
    return 0;
}

SEC("uretprobe/SSL_ImportFD")
int BPF_URETPROBE(probe_nss_import_fd_exit)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 tid = (u32)pid_tgid;
    u64 ret_fd = PT_REGS_RC(ctx);
    u8 one = 1;
    u64 *imported_fd = bpf_map_lookup_elem(&nss_import_fds, &tid);

    if (ret_fd)
        bpf_map_update_elem(&nss_ssl_fds, &ret_fd, &one, BPF_ANY);
    if (imported_fd && *imported_fd)
        bpf_map_update_elem(&nss_ssl_fds, imported_fd, &one, BPF_ANY);

    bpf_map_delete_elem(&nss_import_fds, &tid);
    return 0;
}

SEC("uprobe/PR_Close")
int BPF_UPROBE(probe_nss_close_enter, void *fd)
{
    u64 fd_key = (u64)fd;

    bpf_map_delete_elem(&nss_ssl_fds, &fd_key);
    return 0;
}

SEC("uprobe/chrome_plaintext_request_1")
int BPF_UPROBE(probe_chrome_plaintext_request_1, void *dst, void *src, size_t len)
{
    return emit_plaintext_buffer(src, len, 1);
}

SEC("uprobe/chrome_plaintext_request_2")
int BPF_UPROBE(probe_chrome_plaintext_request_2, void *dst, void *src, size_t len)
{
    return emit_plaintext_buffer(src, len, 1);
}

SEC("uprobe/chrome_plaintext_request_3")
int BPF_UPROBE(probe_chrome_plaintext_request_3, void *dst, void *src, size_t len)
{
    return emit_plaintext_buffer(src, len, 1);
}

SEC("uprobe/chrome_plaintext_response")
int BPF_UPROBE(probe_chrome_plaintext_response, void *dst, void *src, size_t len)
{
    return emit_plaintext_buffer(src, len, 0);
}

SEC("uretprobe/PR_Read")
int BPF_URETPROBE(probe_nss_read_exit)
{
    return browsertrace_exit(ctx, 0);
}

SEC("uretprobe/PR_Write")
int BPF_URETPROBE(probe_nss_write_exit)
{
    return browsertrace_exit(ctx, 1);
}

char LICENSE[] SEC("license") = "GPL";
