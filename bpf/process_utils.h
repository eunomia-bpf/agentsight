/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __PROCESS_UTILS_H
#define __PROCESS_UTILS_H

#include <errno.h>
#include <fcntl.h>
#include <gelf.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include "process.h"
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

/*
 * find_needed_library - Find the DT_NEEDED entry of @binary starting with @prefix.
 *
 * Copies the matching soname (e.g. "libreadline.so.8") into @buf.
 * Returns 0 on success, -ENOENT if no entry matches, or a negative error.
 */
static inline int find_needed_library(const char *binary, const char *prefix, char *buf, size_t len)
{
	Elf_Scn *scn = NULL;
	int fd, err = -ENOENT;
	Elf *elf;

	if (elf_version(EV_CURRENT) == EV_NONE)
		return -EINVAL;
	fd = open(binary, O_RDONLY | O_CLOEXEC);
	if (fd < 0)
		return -errno;
	elf = elf_begin(fd, ELF_C_READ, NULL);
	while (elf && err == -ENOENT && (scn = elf_nextscn(elf, scn))) {
		Elf_Data *data;
		GElf_Shdr shdr;
		GElf_Dyn dyn;

		if (!gelf_getshdr(scn, &shdr) || shdr.sh_type != SHT_DYNAMIC || !shdr.sh_entsize)
			continue;
		data = elf_getdata(scn, NULL);
		for (size_t i = 0; data && i < shdr.sh_size / shdr.sh_entsize; i++) {
			const char *name;

			if (!gelf_getdyn(data, i, &dyn) || dyn.d_tag != DT_NEEDED)
				continue;
			name = elf_strptr(elf, shdr.sh_link, dyn.d_un.d_val);
			if (name && strncmp(name, prefix, strlen(prefix)) == 0) {
				snprintf(buf, len, "%s", name);
				err = 0;
				break;
			}
		}
	}
	elf_end(elf);
	close(fd);
	return err;
}

#endif /* __PROCESS_UTILS_H */
