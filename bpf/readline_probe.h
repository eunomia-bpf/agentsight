/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef __READLINE_PROBE_H
#define __READLINE_PROBE_H

/*
 * Where to attach bash's readline uretprobe.
 *
 * `process.bpf.c` carries `SEC("uretprobe")` and the probe is attached by
 * name at run time rather than by section auto-attach, because the ELF to
 * attach differs between systems. On a distro whose bash links readline
 * dynamically the symbol is in bash's `.dynsym` but undefined there
 * (`SHN_UNDEF`; `nm -D /usr/bin/bash` shows `U readline`), and libbpf's
 * symbol search drops every symbol whose section cannot be looked up, so
 * attaching to `/usr/bin/bash` fails with -ENOENT. A skeleton attach is
 * all-or-nothing, so that one probe took the whole process monitor down.
 *
 * The definition lives in `libreadline.so.N` in that case. `elf_defines_symbol`
 * is the test that tells the two apart: an undefined import must never be
 * accepted as an attach point.
 */

#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <gelf.h>
#include <libelf.h>

#define READLINE_SYM "readline"

static inline bool elf_defines_symbol(const char *path, const char *name)
{
	Elf *elf;
	Elf_Scn *section = NULL;
	int fd;
	bool found = false;

	if (!path || !name)
		return false;
	if (elf_version(EV_CURRENT) == EV_NONE)
		return false;
	fd = open(path, O_RDONLY);
	if (fd < 0)
		return false;
	elf = elf_begin(fd, ELF_C_READ, NULL);
	if (!elf)
		goto out;
	while (!found && (section = elf_nextscn(elf, section)) != NULL) {
		GElf_Shdr header;
		Elf_Data *data = NULL;

		if (!gelf_getshdr(section, &header)
		    || (header.sh_type != SHT_DYNSYM
			&& header.sh_type != SHT_SYMTAB)
		    || header.sh_entsize == 0)
			continue;
		while (!found && (data = elf_getdata(section, data)) != NULL) {
			size_t count = data->d_size / header.sh_entsize;
			size_t i;

			for (i = 0; i < count; i++) {
				const char *sym_name;
				GElf_Sym sym;

				if (!gelf_getsym(data, (int)i, &sym))
					continue;
				if (GELF_ST_TYPE(sym.st_info) != STT_FUNC)
					continue;
				/* An import has no section, and only a
				 * definition gives the uprobe an address. */
				if (sym.st_shndx == SHN_UNDEF)
					continue;
				sym_name = elf_strptr(elf, header.sh_link,
						      sym.st_name);
				if (sym_name && strcmp(sym_name, name) == 0) {
					found = true;
					break;
				}
			}
		}
	}
out:
	if (elf)
		elf_end(elf);
	close(fd);
	return found;
}

/*
 * Path of `soname`. `ldconfig -p` is the system's own answer (the same source
 * `sslsniff.c` uses for libssl); the directory scan covers images without an
 * ldconfig cache, including the multiarch and Arch/Fedora layouts.
 */
static inline bool resolve_library(const char *soname, char *out,
				   size_t out_len)
{
	static const char *const dirs[] = {
		"/lib", "/usr/lib", "/lib64", "/usr/lib64",
		"/lib/x86_64-linux-gnu", "/usr/lib/x86_64-linux-gnu",
		"/lib/aarch64-linux-gnu", "/usr/lib/aarch64-linux-gnu",
	};
	size_t soname_len = strlen(soname);
	const char *search_path;
	FILE *fp = popen("ldconfig -p 2>/dev/null", "r");
	size_t i;

	if (fp) {
		char line[512];

		while (fgets(line, sizeof(line), fp)) {
			char *arrow = strrchr(line, '>');
			char *path, *key_end, *newline;

			if (!arrow || arrow[1] != ' ')
				continue;
			path = arrow + 2;
			newline = strchr(path, '\n');
			if (newline)
				*newline = '\0';
			/* `libreadline.so.8 (libc6,x86-64) => /lib/x86_64...`:
			 * the key is the text before the space, not the path. */
			key_end = line;
			while (key_end < arrow && *key_end != ' '
			       && *key_end != '\t')
				key_end++;
			if ((size_t)(key_end - line) != soname_len
			    || memcmp(line, soname, soname_len) != 0)
				continue;
			if (strlen(path) >= out_len)
				continue;
			strcpy(out, path);
			pclose(fp);
			return true;
		}
		pclose(fp);
	}

	search_path = getenv("LD_LIBRARY_PATH");
	while (search_path && *search_path) {
		const char *colon = strchr(search_path, ':');
		size_t len = colon ? (size_t)(colon - search_path) : strlen(search_path);
		char dir[PATH_MAX];
		int written;

		if (len == 0)
			strcpy(dir, ".");
		else if (len < sizeof(dir)) {
			memcpy(dir, search_path, len);
			dir[len] = '\0';
		} else
			dir[0] = '\0';
		written = dir[0] ? snprintf(out, out_len, "%s/%s", dir, soname) : -1;
		if (written > 0 && (size_t)written < out_len
		    && access(out, R_OK) == 0)
			return true;
		if (!colon)
			break;
		search_path = colon + 1;
	}

	for (i = 0; i < sizeof(dirs) / sizeof(dirs[0]); i++) {
		int written = snprintf(out, out_len, "%s/%s", dirs[i], soname);

		if (written > 0 && (size_t)written < out_len
		    && access(out, R_OK) == 0)
			return true;
	}
	return false;
}

/* The soname bash links when readline is a shared object, e.g.
 * `libreadline.so.8`, read out of the binary's dynamic section. */
static inline bool readline_soname(const char *bash_path, char *out,
				   size_t out_len)
{
	Elf *elf;
	Elf_Scn *section = NULL;
	int fd;
	bool found = false;

	out[0] = '\0';
	fd = open(bash_path, O_RDONLY);
	if (fd < 0)
		return false;
	elf = elf_begin(fd, ELF_C_READ, NULL);
	if (!elf)
		goto out;
	while (!found && (section = elf_nextscn(elf, section)) != NULL) {
		GElf_Shdr header;
		Elf_Data *data = NULL;

		if (!gelf_getshdr(section, &header)
		    || header.sh_type != SHT_DYNAMIC
		    || header.sh_entsize == 0)
			continue;
		while (!found && (data = elf_getdata(section, data)) != NULL) {
			size_t count = data->d_size / header.sh_entsize;
			size_t i;

			for (i = 0; i < count; i++) {
				const char *name;
				GElf_Dyn dyn;

				if (!gelf_getdyn(data, (int)i, &dyn))
					continue;
				if (dyn.d_tag != DT_NEEDED)
					continue;
				name = elf_strptr(elf, header.sh_link,
						  dyn.d_un.d_val);
				if (!name || strncmp(name, "libreadline", 11))
					continue;
				if (strlen(name) >= out_len)
					continue;
				strcpy(out, name);
				found = true;
				break;
			}
		}
	}
out:
	if (elf)
		elf_end(elf);
	close(fd);
	return found;
}

/*
 * Attach point for one bash binary: the binary itself when it defines
 * `readline`, else the library its dynamic section names. NULL means neither
 * defines it, and the caller leaves the probe unattached.
 */
static inline const char *readline_target_for(const char *bash_path, char *out,
					      size_t out_len)
{
	char soname[64];
	char lib[PATH_MAX];

	if (bash_path && elf_defines_symbol(bash_path, READLINE_SYM)
	    && strlen(bash_path) < out_len) {
		strcpy(out, bash_path);
		return out;
	}
	if (!bash_path || !readline_soname(bash_path, soname, sizeof(soname)))
		return NULL;
	if (!resolve_library(soname, lib, sizeof(lib)))
		return NULL;
	if (!elf_defines_symbol(lib, READLINE_SYM) || strlen(lib) >= out_len)
		return NULL;
	strcpy(out, lib);
	return out;
}

/*
 * Pick the ELF for the readline uretprobe. Returns the path in `out`, or NULL
 * when neither bash nor libreadline defines the symbol (the caller then leaves
 * the probe unattached instead of failing the whole run).
 */
static inline const char *find_readline_target(char *out, size_t out_len)
{
	static const char *const bash_paths[] = {
		"/usr/bin/bash", "/bin/bash", "/usr/local/bin/bash",
	};
	size_t i;

	for (i = 0; i < sizeof(bash_paths) / sizeof(bash_paths[0]); i++) {
		if (readline_target_for(bash_paths[i], out, out_len))
			return out;
	}
	return NULL;
}

#endif /* __READLINE_PROBE_H */
