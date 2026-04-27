/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* container_info.h — Userspace helpers for container metadata.
 * Provides ns_pid and container_id extraction from /proc.
 * Shared by process_new.c and sslsniff.c.
 */
#ifndef __CONTAINER_INFO_H
#define __CONTAINER_INFO_H

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>

/* Read namespace PID from /proc/<pid>/status NSpid line.
 * Returns the innermost namespace PID, or -1 if not in a namespace. */
static int get_ns_pid(pid_t host_pid)
{
	char path[64];
	char line[256];
	snprintf(path, sizeof(path), "/proc/%d/status", host_pid);
	FILE *f = fopen(path, "r");
	if (!f)
		return -1;
	int ns_pid = -1;
	while (fgets(line, sizeof(line), f)) {
		if (strncmp(line, "NSpid:", 6) == 0) {
			char *p = line + 6;
			int last_pid = -1;
			int count = 0;
			while (*p) {
				while (*p == '\t' || *p == ' ')
					p++;
				if (*p >= '0' && *p <= '9') {
					last_pid = (int)strtol(p, &p, 10);
					count++;
				} else {
					break;
				}
			}
			if (count >= 2)
				ns_pid = last_pid;
			break;
		}
	}
	fclose(f);
	return ns_pid;
}

/* Read container ID from /proc/<pid>/cgroup (docker/containerd format).
 * Writes short (12-char) container ID to out. Returns 0 on success. */
static int get_container_id(pid_t host_pid, char *out, size_t out_len)
{
	char path[64];
	char line[512];
	snprintf(path, sizeof(path), "/proc/%d/cgroup", host_pid);
	FILE *f = fopen(path, "r");
	if (!f)
		return -1;
	out[0] = '\0';
	while (fgets(line, sizeof(line), f)) {
		char *p = line;
		while (*p) {
			int hex_len = 0;
			char *start = p;
			while ((*p >= '0' && *p <= '9') || (*p >= 'a' && *p <= 'f')) {
				hex_len++;
				p++;
			}
			if (hex_len == 64) {
				int copy_len = (int)out_len - 1 < 12 ? (int)out_len - 1 : 12;
				memcpy(out, start, copy_len);
				out[copy_len] = '\0';
				fclose(f);
				return 0;
			}
			if (hex_len == 0)
				p++;
		}
	}
	fclose(f);
	return -1;
}

/* Print container JSON fields: ,\"ns_pid\":N,\"container_id\":\"xxx\"
 * Prints nothing if not in a container. */
static void print_container_fields(pid_t host_pid)
{
	int ns_pid = get_ns_pid(host_pid);
	if (ns_pid > 0) {
		printf(",\"ns_pid\":%d", ns_pid);
		char container_id[16];
		if (get_container_id(host_pid, container_id, sizeof(container_id)) == 0 &&
		    container_id[0] != '\0') {
			printf(",\"container_id\":\"%s\"", container_id);
		}
	}
}

#endif /* __CONTAINER_INFO_H */
