/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __PROCESS_EXT_USERSPACE_H
#define __PROCESS_EXT_USERSPACE_H

#include <bpf/bpf.h>
#include <dirent.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

static inline void print_clock_sync_anchor(const char *phase)
{
	struct timespec mono = {0}, realtime = {0};
	if (clock_gettime(CLOCK_MONOTONIC, &mono) != 0)
		return;
	if (clock_gettime(CLOCK_REALTIME, &realtime) != 0)
		return;

	uint64_t mono_ns = (uint64_t)mono.tv_sec * 1000000000ULL + (uint64_t)mono.tv_nsec;
	uint64_t wall_ns = (uint64_t)realtime.tv_sec * 1000000000ULL + (uint64_t)realtime.tv_nsec;

	struct tm tm_utc;
	char wall_prefix[64];
	if (!gmtime_r(&realtime.tv_sec, &tm_utc))
		return;
	if (strftime(wall_prefix, sizeof(wall_prefix), "%Y-%m-%dT%H:%M:%S", &tm_utc) == 0)
		return;

	printf("{\"timestamp\":%llu,\"event\":\"CLOCK_SYNC\","
	       "\"phase\":\"%s\",\"mono_ns\":%llu,"
	       "\"wall_time_ns\":%llu,"
	       "\"wall_time\":\"%s.%09ldZ\"}\n",
	       (unsigned long long)mono_ns,
	       phase ? phase : "unknown",
	       (unsigned long long)mono_ns,
	       (unsigned long long)wall_ns,
	       wall_prefix, realtime.tv_nsec);
	fflush(stdout);
}

static inline bool normalize_cgroup_path(const char *input, char *output, size_t output_len)
{
	if (!input || !input[0] || !output || output_len == 0)
		return false;

	if (strncmp(input, "/sys/fs/cgroup", 14) == 0) {
		snprintf(output, output_len, "%s", input);
		return true;
	}
	if (input[0] == '/') {
		snprintf(output, output_len, "/sys/fs/cgroup%s", input);
		return true;
	}

	snprintf(output, output_len, "/sys/fs/cgroup/%s", input);
	return true;
}

static inline bool resolve_cgroup_id_from_path(const char *cgroup_path, uint64_t *out_id)
{
	if (!cgroup_path || !cgroup_path[0] || !out_id)
		return false;

	char normalized[512];
	if (!normalize_cgroup_path(cgroup_path, normalized, sizeof(normalized)))
		return false;

	struct stat st;
	if (stat(normalized, &st) != 0)
		return false;

	*out_id = (uint64_t)st.st_ino;
	return true;
}

static inline void clear_u64_set_map(int map_fd)
{
	uint64_t key = 0, next_key = 0;

	if (map_fd < 0)
		return;
	if (bpf_map_get_next_key(map_fd, NULL, &next_key) != 0)
		return;

	do {
		key = next_key;
		bpf_map_delete_elem(map_fd, &key);
	} while (bpf_map_get_next_key(map_fd, &key, &next_key) == 0);
}

static inline bool add_cgroup_path_inode_to_map(const char *path, int map_fd, int *added_count)
{
	struct stat st;
	uint64_t cgroup_id;
	uint8_t present = 1;

	if (stat(path, &st) != 0 || !S_ISDIR(st.st_mode))
		return false;
	cgroup_id = (uint64_t)st.st_ino;
	if (bpf_map_update_elem(map_fd, &cgroup_id, &present, BPF_ANY) == 0) {
		if (added_count)
			(*added_count)++;
		return true;
	}
	return false;
}

static inline int add_descendant_cgroup_ids(const char *root, int map_fd, int *added_count)
{
	DIR *dir = opendir(root);
	if (!dir)
		return -errno;

	struct dirent *entry;
	while ((entry = readdir(dir)) != NULL) {
		char child[1024];
		struct stat st;

		if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
			continue;

		if (snprintf(child, sizeof(child), "%s/%s", root, entry->d_name) >= (int)sizeof(child))
			continue;
		if (stat(child, &st) != 0 || !S_ISDIR(st.st_mode))
			continue;

		add_cgroup_path_inode_to_map(child, map_fd, added_count);
		add_descendant_cgroup_ids(child, map_fd, added_count);
	}

	closedir(dir);
	return 0;
}

static inline int populate_cgroup_filter_map(const char *cgroup_path, bool include_children, int map_fd)
{
	char normalized[512];
	int added = 0;

	if (map_fd < 0)
		return -EINVAL;
	if (!normalize_cgroup_path(cgroup_path, normalized, sizeof(normalized)))
		return -EINVAL;

	clear_u64_set_map(map_fd);
	if (!add_cgroup_path_inode_to_map(normalized, map_fd, &added))
		return -ENOENT;

	if (include_children) {
		int rc = add_descendant_cgroup_ids(normalized, map_fd, &added);
		if (rc < 0)
			return rc;
	}

	return added;
}

#endif /* __PROCESS_EXT_USERSPACE_H */
