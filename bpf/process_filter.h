/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* Copyright (c) 2020 Facebook */
#ifndef __PROCESS_FILTER_H
#define __PROCESS_FILTER_H

#include <stdbool.h>
#include <string.h>
#include "process.h"

/* Hash table for tracking PIDs in userspace */
#define TRACKED_PIDS_HASH_SIZE 2048
#define TRACKED_PIDS_HASH_MASK (TRACKED_PIDS_HASH_SIZE - 1)

struct tracked_pid_entry {
	pid_t pid;
	pid_t ppid;
	bool is_tracked;
	bool is_active;  /* false = empty slot */
};

struct pid_tracker {
	struct tracked_pid_entry entries[TRACKED_PIDS_HASH_SIZE];
	char **command_filters;
	int command_filter_count;
	enum filter_mode filter_mode;
	pid_t target_pid;  /* For -p option */
};

/* Simple hash function for PIDs */
static inline unsigned int pid_hash(pid_t pid)
{
	return (unsigned int)pid & TRACKED_PIDS_HASH_MASK;
}

/* Initialize the PID tracker */
static inline void pid_tracker_init(struct pid_tracker *tracker,
                                    char **command_filters,
                                    int command_filter_count,
                                    enum filter_mode filter_mode,
                                    pid_t target_pid)
{
	memset(tracker->entries, 0, sizeof(tracker->entries));
	tracker->command_filters = command_filters;
	tracker->command_filter_count = command_filter_count;
	tracker->filter_mode = filter_mode;
	tracker->target_pid = target_pid;
}

/* Find a PID in the tracker */
static inline struct tracked_pid_entry *pid_tracker_find(struct pid_tracker *tracker, pid_t pid)
{
	unsigned int hash = pid_hash(pid);
	unsigned int i;

	/* Linear probing */
	for (i = 0; i < TRACKED_PIDS_HASH_SIZE; i++) {
		unsigned int idx = (hash + i) & TRACKED_PIDS_HASH_MASK;
		struct tracked_pid_entry *entry = &tracker->entries[idx];

		if (!entry->is_active) {
			return NULL;  /* Empty slot, not found */
		}

		if (entry->pid == pid) {
			return entry;
		}
	}

	return NULL;  /* Table full or not found */
}

/* Add a PID to the tracker */
static inline bool pid_tracker_add(struct pid_tracker *tracker, pid_t pid, pid_t ppid)
{
	unsigned int hash = pid_hash(pid);
	unsigned int i;

	/* Check if already exists */
	struct tracked_pid_entry *existing = pid_tracker_find(tracker, pid);
	if (existing) {
		return true;  /* Already tracked */
	}

	/* Linear probing to find empty slot */
	for (i = 0; i < TRACKED_PIDS_HASH_SIZE; i++) {
		unsigned int idx = (hash + i) & TRACKED_PIDS_HASH_MASK;
		struct tracked_pid_entry *entry = &tracker->entries[idx];

		if (!entry->is_active) {
			entry->pid = pid;
			entry->ppid = ppid;
			entry->is_tracked = true;
			entry->is_active = true;
			return true;
		}
	}

	return false;  /* Table full */
}

/* Remove a PID from the tracker */
static inline void pid_tracker_remove(struct pid_tracker *tracker, pid_t pid)
{
	struct tracked_pid_entry *entry = pid_tracker_find(tracker, pid);
	if (entry) {
		entry->is_active = false;
	}
}

/* Check if a PID is tracked */
static inline bool pid_tracker_is_tracked(struct pid_tracker *tracker, pid_t pid)
{
	struct tracked_pid_entry *entry = pid_tracker_find(tracker, pid);
	return entry && entry->is_tracked;
}

/* Check if a command matches any filter */
static inline bool command_matches_any_filter(const char *comm,
                                              char **command_filters,
                                              int command_filter_count)
{
	for (int i = 0; i < command_filter_count; i++) {
		if (strcmp(comm, command_filters[i]) == 0) {
			return true;
		}
	}
	return false;
}

/* Check if we should track a process based on filters and parent tracking */
static inline bool should_track_process(struct pid_tracker *tracker,
                                       const char *comm,
                                       pid_t pid,
                                       pid_t ppid)
{
	/* Mode 0 (ALL): track everything */
	if (tracker->filter_mode == FILTER_MODE_ALL) {
		return true;
	}

	/* Mode 1 (PROC): track all processes but filter file operations */
	if (tracker->filter_mode == FILTER_MODE_PROC) {
		return true;
	}

	/* Mode 2 (FILTER): selective tracking */
	if (tracker->filter_mode == FILTER_MODE_FILTER) {
		/* Check if specific PID was requested */
		if (tracker->target_pid > 0 && pid == tracker->target_pid) {
			return true;
		}

		/* Check if parent is tracked */
		if (pid_tracker_is_tracked(tracker, ppid)) {
			return true;
		}

		/* Check if command matches any filter */
		if (tracker->command_filter_count > 0 &&
		    command_matches_any_filter(comm, tracker->command_filters, tracker->command_filter_count)) {
			return true;
		}
	}

	return false;
}

/* Check if file operations should be reported for a PID */
static inline bool should_report_file_ops(struct pid_tracker *tracker, pid_t pid)
{
	/* Mode 0 (ALL): report all file operations */
	if (tracker->filter_mode == FILTER_MODE_ALL) {
		return true;
	}

	/* Mode 1 (PROC) and Mode 2 (FILTER): only report for tracked PIDs */
	return pid_tracker_is_tracked(tracker, pid);
}

/* Check if bash readline should be reported */
static inline bool should_report_bash_readline(struct pid_tracker *tracker, pid_t pid)
{
	/* Mode 2 (FILTER): only report for tracked PIDs */
	if (tracker->filter_mode == FILTER_MODE_FILTER) {
		return pid_tracker_is_tracked(tracker, pid);
	}

	/* Mode 0 (ALL) and Mode 1 (PROC): report all */
	return true;
}

#endif /* __PROCESS_FILTER_H */
