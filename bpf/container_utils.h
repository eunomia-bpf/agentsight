// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Container-aware library path resolution for uprobe attachment.
// Resolves SSL library paths inside container mount namespaces
// via /proc/<pid>/maps and /proc/<pid>/root/.

#ifndef __CONTAINER_UTILS_H
#define __CONTAINER_UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <limits.h>
#include <errno.h>
#include <stdbool.h>
#include <sys/types.h>
#include <bpf/libbpf.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

#define MAX_CONTAINER_LIBS 64

/* ---------- data structures ---------- */

struct pid_lib_entry {
    pid_t pid;
    char  lib_path[PATH_MAX]; /* host-perspective path */
};

struct dynamic_links {
    struct bpf_link **links;
    int count;
    int capacity;
};

/* ---------- dynamic link management ---------- */

static struct dynamic_links g_extra_links = {
    .links = NULL, .count = 0, .capacity = 0
};

static void add_dynamic_link(struct bpf_link *link)
{
    if (!link)
        return;
    if (g_extra_links.count >= g_extra_links.capacity) {
        int new_cap = g_extra_links.capacity ? g_extra_links.capacity * 2 : 16;
        struct bpf_link **tmp = realloc(g_extra_links.links,
                                        new_cap * sizeof(struct bpf_link *));
        if (!tmp) {
            fprintf(stderr, "realloc dynamic_links failed\n");
            return;
        }
        g_extra_links.links = tmp;
        g_extra_links.capacity = new_cap;
    }
    g_extra_links.links[g_extra_links.count++] = link;
}

static void cleanup_dynamic_links(void)
{
    for (int i = 0; i < g_extra_links.count; i++)
        bpf_link__destroy(g_extra_links.links[i]);
    free(g_extra_links.links);
    g_extra_links.links = NULL;
    g_extra_links.count = 0;
    g_extra_links.capacity = 0;
}

/* ---------- container library path resolution ---------- */

/*
 * Find the host-perspective path of a library loaded by a specific PID.
 *
 * For container processes the in-container path (e.g. /usr/lib/libssl.so.3)
 * is translated to /proc/<pid>/root/usr/lib/libssl.so.3 so that
 * bpf_program__attach_uprobe_opts() can locate the correct ELF on the host
 * filesystem.
 */
static char *find_library_path_for_pid(pid_t pid, const char *libname,
                                       bool verbose)
{
    static char host_path[PATH_MAX];
    char maps_path[64];
    char line[4096];
    FILE *fp;

    snprintf(maps_path, sizeof(maps_path), "/proc/%d/maps", pid);
    fp = fopen(maps_path, "r");
    if (!fp) {
        if (verbose)
            fprintf(stderr, "Failed to open %s: %s\n",
                    maps_path, strerror(errno));
        return NULL;
    }

    while (fgets(line, sizeof(line), fp)) {
        /* only consider executable/read-only mappings with matching lib name */
        if (strstr(line, libname) == NULL)
            continue;
        if (strstr(line, "r-xp") == NULL && strstr(line, "r--p") == NULL)
            continue;

        char *path = strchr(line, '/');
        if (!path)
            continue;

        char *nl = strchr(path, '\n');
        if (nl)
            *nl = '\0';

        /* convert to host-perspective path via /proc/<pid>/root */
        snprintf(host_path, sizeof(host_path), "/proc/%d/root%s", pid, path);

        if (access(host_path, R_OK) == 0) {
            fclose(fp);
            if (verbose)
                fprintf(stderr,
                        "Found %s for PID %d: %s -> %s\n",
                        libname, pid, path, host_path);
            return host_path;
        }
    }

    fclose(fp);
    return NULL;
}

/*
 * Scan /proc for all processes that have loaded `libname`, returning
 * deduplicated (by host path) entries.
 */
static int find_pids_with_library(const char *libname,
                                  struct pid_lib_entry *entries,
                                  int max_entries,
                                  bool verbose)
{
    DIR *proc_dir;
    struct dirent *ent;
    int count = 0;

    /* Heap-allocated dedup array to avoid 256KB stack allocation */
    char (*seen)[PATH_MAX] = calloc(MAX_CONTAINER_LIBS, PATH_MAX);
    int  seen_count = 0;

    if (!seen) {
        fprintf(stderr, "Failed to allocate dedup buffer\n");
        return 0;
    }

    proc_dir = opendir("/proc");
    if (!proc_dir) {
        free(seen);
        return 0;
    }

    while ((ent = readdir(proc_dir)) && count < max_entries) {
        pid_t pid = atoi(ent->d_name);
        if (pid <= 0)
            continue;

        char *path = find_library_path_for_pid(pid, libname, false);
        if (!path)
            continue;

        /* dedup */
        bool dup = false;
        for (int i = 0; i < seen_count; i++) {
            if (strcmp(seen[i], path) == 0) {
                dup = true;
                break;
            }
        }
        if (dup)
            continue;

        if (seen_count < MAX_CONTAINER_LIBS) {
            strncpy(seen[seen_count], path, PATH_MAX - 1);
            seen[seen_count][PATH_MAX - 1] = '\0';
            seen_count++;
        }

        entries[count].pid = pid;
        strncpy(entries[count].lib_path, path, PATH_MAX - 1);
        entries[count].lib_path[PATH_MAX - 1] = '\0';
        count++;

        if (verbose)
            fprintf(stderr, "Discovered container SSL lib: %s (via PID %d)\n",
                    path, pid);
    }

    closedir(proc_dir);
    free(seen);
    return count;
}

#endif /* __CONTAINER_UTILS_H */
