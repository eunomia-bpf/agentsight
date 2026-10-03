/* SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause */
#ifndef __PROCESS_EXT_BPF_STATE_H
#define __PROCESS_EXT_BPF_STATE_H

#include "process_ext/types.h"

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 16384);
	__type(key, struct agg_key);
	__type(value, struct agg_value);
} event_agg_map SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, MAX_TRACKED_PIDS);
	__type(key, u32);
	__type(value, u8);
} tracked_pids SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, MAX_TRACKED_CGROUPS);
	__type(key, u64);
	__type(value, u8);
} tracked_cgroups SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, u64);
} agg_overflow_count SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 4096);
	__type(key, u32);
	__type(value, struct exit_mem_info);
} exit_mem SEC(".maps");

struct accept_peer_key {
	__u64 start_time;
	__u32 pid;
	__u16 port;
	__u16 family;
	__u8 peer[16];
};

struct {
	__uint(type, BPF_MAP_TYPE_LRU_HASH);
	__uint(max_entries, 16384);
	__type(key, struct accept_peer_key);
	__type(value, __u8);
} accept_peers_seen SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8192);
	__type(key, u64);
	__type(value, int);
} write_ctx_map SEC(".maps");

/* Keep the socket across inet_listen entry/return so only successful listens
 * are reported, with the assigned port (including implicit/ephemeral binds). */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 4096);
	__type(key, u64);
	__type(value, u64);
} listen_socket_map SEC(".maps");

const volatile bool filter_pids = false;
const volatile bool filter_cgroup = false;
const volatile bool filter_cgroup_children = false;
const volatile unsigned long long target_cgroup_id = 0;
const volatile bool trace_fs_mutations = false;
const volatile bool trace_network = false;
const volatile bool trace_signals = false;
const volatile bool trace_memory = false;
const volatile bool trace_cow = false;

#endif /* __PROCESS_EXT_BPF_STATE_H */
