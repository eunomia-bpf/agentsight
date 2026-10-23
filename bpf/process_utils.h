/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __PROCESS_UTILS_H
#define __PROCESS_UTILS_H

#include <string.h>
#include <sys/types.h>

#include "process.h"

/* Kernel sb->s_dev uses the 12:20 major/minor layout, not glibc dev_t. */
static inline unsigned int kernel_dev_major(unsigned int dev)
{
	return dev >> 20;
}

static inline unsigned int kernel_dev_minor(unsigned int dev)
{
	return dev & ((1u << 20) - 1);
}
/*
 * postprocess_full_command - Convert raw argv bytes to a readable command string.
 *
 * BPF reads raw argv memory which contains \0 between arguments and may
 * include environment variable data past arg_end.  This function:
 *   1. Copies data to a local buffer (ringbuf consumer memory is read-only)
 *   2. Trims to actual arg_len (from e->exit_code) to remove env var leakage
 *   3. Replaces \0 separators with spaces
 *
 * Returns pointer to a static buffer (NOT thread-safe, single consumer).
 */
static inline const char *postprocess_full_command(const char *buf, int buf_size, unsigned int arg_len)
{
	static char cmd_buf[MAX_COMMAND_LEN];

	if (arg_len == 0 || arg_len > (unsigned int)(buf_size - 1)) {
		/* No arg_len info: just copy the first null-terminated string */
		int len = 0;
		while (len < buf_size - 1 && buf[len] != '\0')
			len++;
		if (len > 0)
			memcpy(cmd_buf, buf, len);
		cmd_buf[len] = '\0';
		return cmd_buf;
	}

	memcpy(cmd_buf, buf, arg_len);
	cmd_buf[arg_len] = '\0';

	/* Replace \0 separators between argv entries with spaces */
	for (int i = 0; i < (int)arg_len - 1; i++) {
		if (cmd_buf[i] == '\0')
			cmd_buf[i] = ' ';
	}

	return cmd_buf;
}

#endif /* __PROCESS_UTILS_H */
