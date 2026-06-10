/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __PROCESS_EXT_MAP_FLUSH_H
#define __PROCESS_EXT_MAP_FLUSH_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "process_ext/types.h"
#include "jsonl.h"

static const char *event_type_name(unsigned int type)
{
	switch (type) {
	case EVENT_TYPE_FILE_DELETE:    return "FILE_DELETE";
	case EVENT_TYPE_FILE_RENAME:   return "FILE_RENAME";
	case EVENT_TYPE_DIR_CREATE:    return "DIR_CREATE";
	case EVENT_TYPE_FILE_TRUNCATE: return "FILE_TRUNCATE";
	case EVENT_TYPE_CHDIR:         return "CHDIR";
	case EVENT_TYPE_WRITE:         return "WRITE";
	case EVENT_TYPE_NET_BIND:      return "NET_BIND";
	case EVENT_TYPE_NET_LISTEN:    return "NET_LISTEN";
	case EVENT_TYPE_NET_CONNECT:   return "NET_CONNECT";
	case EVENT_TYPE_PGRP_CHANGE:   return "PGRP_CHANGE";
	case EVENT_TYPE_SESSION_CREATE:return "SESSION_CREATE";
	case EVENT_TYPE_SIGNAL_SEND:   return "SIGNAL_SEND";
	case EVENT_TYPE_PROC_FORK:     return "PROC_FORK";
	case EVENT_TYPE_MMAP_SHARED:   return "MMAP_SHARED";
	case EVENT_TYPE_COW_FAULT:     return "COW_FAULT";
	default:                       return "UNKNOWN";
	}
}

static bool parse_fd_detail(const char *detail, int *fd_out)
{
	if (!detail || strncmp(detail, "fd=", 3) != 0)
		return false;

	char *end = NULL;
	long fd = strtol(detail + 3, &end, 10);
	if (end == detail + 3 || (end && *end != '\0'))
		return false;

	*fd_out = (int)fd;
	return true;
}

static bool resolve_fd_path(uint32_t pid, int fd, char *out, size_t out_size)
{
	char fd_link[64];
	char link_target[MAX_FILENAME_LEN];

	snprintf(fd_link, sizeof(fd_link), "/proc/%u/fd/%d", pid, fd);
	ssize_t n = readlink(fd_link, link_target, sizeof(link_target) - 1);
	if (n <= 0)
		return false;

	link_target[n] = '\0';
	strncpy(out, link_target, out_size - 1);
	out[out_size - 1] = '\0';
	return true;
}

static void print_summary_json(const struct agg_key *key, const struct agg_value *val)
{
	char detail_esc[MAX_FILENAME_LEN * 2];
	char detail_path[MAX_FILENAME_LEN];
	char extra_esc[MAX_FILENAME_LEN * 2];
	char comm_esc[TASK_COMM_LEN * 2];
	int fd = -1;
	bool parsed_fd = false;
	bool resolved_path = false;

	json_escape(val->extra, extra_esc, sizeof(extra_esc));
	json_escape(val->comm, comm_esc, sizeof(comm_esc));

	if (key->event_type == EVENT_TYPE_WRITE) {
		parsed_fd = parse_fd_detail(key->detail, &fd);
		if (parsed_fd)
			resolved_path = resolve_fd_path(key->pid, fd, detail_path, sizeof(detail_path));
	}

	if (resolved_path)
		json_escape(detail_path, detail_esc, sizeof(detail_esc));
	else
		json_escape(key->detail, detail_esc, sizeof(detail_esc));

	printf("{\"timestamp\":%llu,\"event\":\"SUMMARY\","
	       "\"comm\":\"%s\",\"pid\":%u,"
	       "\"type\":\"%s\",\"detail\":\"%s\","
	       "\"count\":%llu",
	       (unsigned long long)val->last_ts, comm_esc, key->pid,
	       event_type_name(key->event_type), detail_esc,
	       (unsigned long long)val->count);

	if (val->total_bytes > 0)
		printf(",\"total_bytes\":%llu", (unsigned long long)val->total_bytes);

	if (key->event_type == EVENT_TYPE_WRITE && parsed_fd) {
		printf(",\"fd\":%d", fd);
		printf(",\"path_resolved\":%s", resolved_path ? "true" : "false");
	}

	if (extra_esc[0])
		printf(",\"extra\":\"%s\"", extra_esc);

	printf("}\n");
}

static inline void flush_agg_map(int map_fd)
{
	struct agg_key key = {}, next_key;
	struct agg_value val;

	while (bpf_map_get_next_key(map_fd, &key, &next_key) == 0) {
		if (bpf_map_lookup_elem(map_fd, &next_key, &val) == 0 && val.count > 0) {
			print_summary_json(&next_key, &val);
			bpf_map_delete_elem(map_fd, &next_key);
		}
		key = next_key;
	}
	fflush(stdout);
}

static inline void flush_pid_from_agg_map(int map_fd, uint32_t target_pid)
{
	struct agg_key key = {}, next_key;
	struct agg_value val;
	struct agg_key to_delete[256];
	int del_count = 0;

	while (bpf_map_get_next_key(map_fd, &key, &next_key) == 0) {
		if (next_key.pid == target_pid) {
			if (bpf_map_lookup_elem(map_fd, &next_key, &val) == 0 && val.count > 0) {
				print_summary_json(&next_key, &val);
			}
			if (del_count < 256)
				to_delete[del_count++] = next_key;
		}
		key = next_key;
	}

	for (int i = 0; i < del_count; i++)
		bpf_map_delete_elem(map_fd, &to_delete[i]);
	fflush(stdout);
}

/* Check and report overflow count, returns the total count across all CPUs */
static inline uint64_t check_overflow(int overflow_map_fd)
{
	uint32_t zero = 0;
	int num_cpus = libbpf_num_possible_cpus();
	if (num_cpus <= 0)
		num_cpus = 256; /* safe upper bound */

	uint64_t *counts = calloc(num_cpus, sizeof(uint64_t));
	if (!counts)
		return 0;

	uint64_t total = 0;
	if (bpf_map_lookup_elem(overflow_map_fd, &zero, counts) == 0) {
		for (int i = 0; i < num_cpus; i++)
			total += counts[i];
	}

	if (total > 0) {
		printf("{\"timestamp\":0,\"event\":\"WARNING\",\"comm\":\"\",\"pid\":0,"
		       "\"type\":\"AGG_MAP_OVERFLOW\",\"overflow_count\":%llu}\n",
		       (unsigned long long)total);
		fflush(stdout);
		/* Reset counters */
		memset(counts, 0, num_cpus * sizeof(uint64_t));
		bpf_map_update_elem(overflow_map_fd, &zero, counts, BPF_ANY);
	}

	free(counts);
	return total;
}

#endif /* __PROCESS_EXT_MAP_FLUSH_H */
