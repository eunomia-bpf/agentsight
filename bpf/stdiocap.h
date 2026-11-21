// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
#ifndef __STDIOCAP_H
#define __STDIOCAP_H

#define MAX_BUF_SIZE 8192
#define RING_BUFFER_SIZE (1024 * 1024)
#define TASK_COMM_LEN 16

/* Slots of the BPF-side `stats` array, in order. An empty capture is
 * explained by which slot is set: every enter filtered means the session
 * filter did not match the writer, exit_without_enter means the enter hook
 * never stored args for that thread, and a ringbuf slot means the event was
 * built but could not be submitted. */
enum stdiocap_stat {
	STDIO_STAT_ENTER = 0,
	STDIO_STAT_ENTER_FILTERED,
	STDIO_STAT_FILTER_UID,
	STDIO_STAT_FILTER_FD,
	STDIO_STAT_FILTER_NOT_TRACKED,
	STDIO_STAT_EXIT_NO_ARGS,
	STDIO_STAT_EXIT_ERROR,
	STDIO_STAT_RINGBUF_FULL,
	STDIO_STAT_EVENT,
	STDIO_STAT_COUNT,
};

struct stdiocap_event_t {
	__u64 timestamp_ns;
	__u64 delta_ns;
	__u32 pid;
	__u32 tid;
	__u32 uid;
	__s32 fd;
	__u32 len;
	__u32 buf_size;
	__u8 is_read;
	char comm[TASK_COMM_LEN];
	__u8 buf[MAX_BUF_SIZE];
};

#endif /* __STDIOCAP_H */
