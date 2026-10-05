/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* Copyright (c) 2020 Facebook */
#ifndef __PROCESS_H
#define __PROCESS_H

#define TASK_COMM_LEN 16
#define MAX_FILENAME_LEN 127
#define MAX_FILE_PATH_LEN 4096
#define MAX_COMMAND_FILTERS 10
#define MAX_TRACKED_PIDS 4096
#define MAX_COMMAND_LEN 256

enum filter_mode {
	FILTER_MODE_ALL = 0,      /* Trace all processes and all read/write operations */
	FILTER_MODE_PROC = 1,     /* Trace all processes but only read/write for tracked PIDs */
	FILTER_MODE_FILTER = 2,   /* Only trace processes matching filters and their read/write */
};

enum event_type {
	EVENT_TYPE_PROCESS = 0,
	EVENT_TYPE_BASH_READLINE = 1,
	EVENT_TYPE_FILE_OPERATION = 2,
};

struct event {
	enum event_type type;
	int pid;
	int ppid;
	unsigned exit_code;
	unsigned long long duration_ns;
	unsigned long long timestamp_ns;
	char comm[TASK_COMM_LEN];
	char full_command[MAX_COMMAND_LEN];     /* full command line with args */
	union {
		char filename[MAX_FILENAME_LEN];     /* for process events */
		char command[MAX_COMMAND_LEN];       /* for bash readline events */
		struct {                             /* for file operation events */
			char filepath[MAX_FILE_PATH_LEN];
			int fd;
			int flags;
			bool is_open;  /* true for open/openat, false for close */
			bool resolved; /* security_file_open, not a syscall entry */
			bool layer;
			unsigned char access; /* FILE_ACCESS_* */
			int path_error;
			unsigned int dev;
			unsigned long long ino;
		} file_op;
	};
	bool exit_event;
};

#define FILE_ACCESS_READ  1
#define FILE_ACCESS_WRITE 2
#define FILE_ACCESS_EXEC  4

struct command_filter {
	char comm[TASK_COMM_LEN];
};

struct pid_info {
	pid_t pid;
	pid_t ppid;
	bool is_tracked;
};

#endif /* __PROCESS_H */
