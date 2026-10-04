/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __PROCESS_EXT_TYPES_H
#define __PROCESS_EXT_TYPES_H

#include "process.h"

#define DETAIL_LEN 64
#define MAX_TRACKED_CGROUPS 16384

struct agg_key {
	__u32 pid;
	__u32 event_type;
	char detail[DETAIL_LEN];
	__u16 port;      /* assigned local port for successful datagram binds */
	__u8 protocol;   /* IP protocol; zero for existing summary records */
};

struct agg_value {
	__u64 count;
	__u64 total_bytes;
	__u64 first_ts;
	__u64 last_ts;
	char comm[TASK_COMM_LEN];
	char extra[MAX_FILENAME_LEN];
};

struct exit_mem_info {
	__u64 hiwater_rss;
};

enum process_ext_event_type {
	EVENT_TYPE_FILE_DELETE = 10,
	EVENT_TYPE_FILE_RENAME = 11,
	EVENT_TYPE_DIR_CREATE = 12,
	EVENT_TYPE_FILE_TRUNCATE = 13,
	EVENT_TYPE_CHDIR = 14,
	EVENT_TYPE_WRITE = 15,
	EVENT_TYPE_NET_BIND = 20,
	EVENT_TYPE_NET_LISTEN = 21,
	EVENT_TYPE_NET_CONNECT = 22,
	EVENT_TYPE_NET_ACCEPT = 23,
	EVENT_TYPE_PGRP_CHANGE = 30,
	EVENT_TYPE_SESSION_CREATE = 31,
	EVENT_TYPE_SIGNAL_SEND = 32,
	EVENT_TYPE_PROC_FORK = 33,
	EVENT_TYPE_MMAP_SHARED = 40,
	EVENT_TYPE_COW_FAULT = 41,
};

#endif /* __PROCESS_EXT_TYPES_H */
