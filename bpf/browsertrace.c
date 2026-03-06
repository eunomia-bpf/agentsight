// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2026 Yusheng Zheng
//
// Browser-focused plaintext tracing for Chrome/Firefox.
#include <argp.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <locale.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <wchar.h>

#include "browsertrace.skel.h"
#include "browsertrace.h"

#define INVALID_UID -1
#define INVALID_PID -1
#define DEFAULT_BUFFER_SIZE 8192
#define PERF_POLL_TIMEOUT_MS 100
#define TARGET_PID_CACHE_SIZE 256
#define BROWSER_EXTRA_LINK_CAP 16

#define warn(...) fprintf(stderr, __VA_ARGS__)

volatile sig_atomic_t exiting = 0;

const char *argp_program_version = "browsertrace 0.1";
const char *argp_program_bug_address = "https://github.com/eunomia-bpf/agentsight";
const char argp_program_doc[] =
	"Trace browser plaintext data for Chrome/Firefox and output JSON.\n"
	"\n"
	"USAGE: browsertrace --binary-path PATH [OPTIONS]\n"
	"\n"
	"EXAMPLES:\n"
	"    ./browsertrace --binary-path /opt/google/chrome/chrome\n"
	"    ./browsertrace --binary-path /usr/bin/firefox\n"
	"    ./browsertrace --binary-path /snap/firefox/current/usr/lib/firefox/firefox -p 1234\n";

struct env {
	pid_t pid;
	int uid;
	char *comm;
	char *binary_path;
} env = {
	.uid = INVALID_UID,
	.pid = INVALID_PID,
	.comm = NULL,
	.binary_path = NULL,
};

struct linked_tls_libraries {
	char nspr[PATH_MAX];
	char nss_ssl3[PATH_MAX];
};

struct chrome_plaintext_offsets {
	size_t request_copy_1;
	size_t request_copy_2;
	size_t request_copy_3;
	size_t response_copy;
	bool found;
};

struct target_pid_cache_entry {
	pid_t pid;
	bool valid;
	bool matched;
};

static struct bpf_link *browser_extra_links[BROWSER_EXTRA_LINK_CAP];
static struct target_pid_cache_entry target_pid_cache[TARGET_PID_CACHE_SIZE];
static bool verbose = false;
static char target_exec_path[PATH_MAX];
static char target_exec_basename[PATH_MAX];
static char *event_buf;

#define BINARY_PATH_KEY 1003

static const struct argp_option opts[] = {
	{"pid", 'p', "PID", 0, "Trace this PID only."},
	{"uid", 'u', "UID", 0, "Trace this UID only."},
	{"comm", 'c', "COMMAND", 0, "Trace only commands matching string."},
	{"verbose", 'v', NULL, 0, "Verbose debug output."},
	{"binary-path", BINARY_PATH_KEY, "PATH", 0, "Chrome/Firefox binary or wrapper path."},
	{},
};

static error_t parse_arg(int key, char *arg, struct argp_state *state)
{
	switch (key) {
	case 'p':
		env.pid = atoi(arg);
		break;
	case 'u':
		env.uid = atoi(arg);
		break;
	case 'c':
		env.comm = strdup(arg);
		break;
	case 'v':
		verbose = true;
		break;
	case BINARY_PATH_KEY:
		env.binary_path = strdup(arg);
		break;
	case ARGP_KEY_END:
		if (!env.binary_path)
			argp_error(state, "--binary-path is required");
		break;
	default:
		return ARGP_ERR_UNKNOWN;
	}

	return 0;
}

static const struct argp argp = {
	opts,
	parse_arg,
	NULL,
	argp_program_doc
};

static int libbpf_print_fn(enum libbpf_print_level level, const char *format,
						   va_list args)
{
	if (level == LIBBPF_DEBUG && !verbose)
		return 0;
	return vfprintf(stderr, format, args);
}

static void sig_int(int signo)
{
	exiting = 1;
}

static bool copy_string(char *dst, size_t dst_size, const char *src)
{
	if (!dst || !dst_size || !src)
		return false;

	snprintf(dst, dst_size, "%s", src);
	return true;
}

static const char *path_basename_ptr(const char *path)
{
	const char *slash;

	if (!path)
		return "";
	slash = strrchr(path, '/');
	return slash ? slash + 1 : path;
}

static bool path_has_basename(const char *path, const char *name)
{
	return strcmp(path_basename_ptr(path), name) == 0;
}

static bool target_is_chromium_family(const char *path)
{
	return path_has_basename(path, "chrome") ||
		   path_has_basename(path, "chromium") ||
		   path_has_basename(path, "chromium-browser") ||
		   path_has_basename(path, "google-chrome") ||
		   path_has_basename(path, "google-chrome-stable");
}

static bool target_is_firefox(const char *path)
{
	return path_has_basename(path, "firefox") ||
		   path_has_basename(path, "firefox-bin");
}

static bool file_is_elf(const char *path)
{
	unsigned char magic[4];
	ssize_t n;
	int fd = open(path, O_RDONLY);

	if (fd < 0)
		return false;

	n = read(fd, magic, sizeof(magic));
	close(fd);

	return n == (ssize_t)sizeof(magic) &&
		   magic[0] == 0x7f && magic[1] == 'E' &&
		   magic[2] == 'L' && magic[3] == 'F';
}

static bool path_dirname_copy(const char *path, char *dir, size_t dir_size)
{
	const char *slash;
	size_t len;

	if (!path || !dir || dir_size == 0)
		return false;

	slash = strrchr(path, '/');
	if (!slash)
		return copy_string(dir, dir_size, ".");

	len = slash - path;
	if (len == 0)
		len = 1;
	if (len >= dir_size)
		return false;

	memcpy(dir, path, len);
	dir[len] = '\0';
	return true;
}

static bool path_join(char *out, size_t out_size, const char *dir, const char *leaf)
{
	if (!out || !out_size || !dir || !leaf)
		return false;

	if (snprintf(out, out_size, "%s/%s", dir, leaf) >= (int)out_size)
		return false;
	return true;
}

static bool read_first_matching_line(const char *cmd, char *out, size_t out_size)
{
	FILE *fp;

	if (!cmd || !out || out_size == 0)
		return false;

	fp = popen(cmd, "r");
	if (!fp)
		return false;

	if (!fgets(out, out_size, fp)) {
		pclose(fp);
		return false;
	}

	out[strcspn(out, "\n")] = '\0';
	pclose(fp);
	return out[0] != '\0';
}

static bool parse_exec_target_from_script(const char *script_path, char *resolved,
										  size_t resolved_size)
{
	FILE *fp;
	char line[1024];
	char dir[PATH_MAX];

	if (!script_path || !resolved || resolved_size == 0)
		return false;

	fp = fopen(script_path, "r");
	if (!fp)
		return false;

	if (!path_dirname_copy(script_path, dir, sizeof(dir))) {
		fclose(fp);
		return false;
	}

	while (fgets(line, sizeof(line), fp)) {
		char *here = strstr(line, "$HERE/");
		if (here) {
			char suffix[PATH_MAX];
			size_t i = 0;

			here += strlen("$HERE/");
			while (here[i] && here[i] != '"' &&
				   !isspace((unsigned char)here[i]) &&
				   i < sizeof(suffix) - 1) {
				suffix[i] = here[i];
				i++;
			}
			suffix[i] = '\0';
			fclose(fp);
			return path_join(resolved, resolved_size, dir, suffix);
		}

		char *exec_pos = strstr(line, "exec ");
		if (!exec_pos)
			continue;
		exec_pos += strlen("exec ");
		while (*exec_pos == ' ' || *exec_pos == '\t')
			exec_pos++;
		if (strncmp(exec_pos, "-a ", 3) == 0) {
			char *after = strchr(exec_pos + 3, ' ');
			if (!after)
				continue;
			exec_pos = after + 1;
			while (*exec_pos == ' ' || *exec_pos == '\t')
				exec_pos++;
		}

		if (*exec_pos == '"' || *exec_pos == '\'') {
			char quote = *exec_pos++;
			char *end = strchr(exec_pos, quote);
			if (!end)
				continue;
			*end = '\0';
			fclose(fp);
			return copy_string(resolved, resolved_size, exec_pos);
		}

		if (*exec_pos == '/') {
			char token[PATH_MAX];
			size_t i = 0;

			while (exec_pos[i] &&
				   !isspace((unsigned char)exec_pos[i]) &&
				   i < sizeof(token) - 1) {
				token[i] = exec_pos[i];
				i++;
			}
			token[i] = '\0';
			fclose(fp);
			return copy_string(resolved, resolved_size, token);
		}
	}

	fclose(fp);
	return false;
}

static bool find_snap_packaged_binary(const char *app_name, char *resolved,
									  size_t resolved_size)
{
	char candidate[PATH_MAX];

	if (!app_name || !resolved || resolved_size == 0)
		return false;

	if (snprintf(candidate, sizeof(candidate), "/snap/%s/current/usr/lib/%s/%s",
				 app_name, app_name, app_name) < (int)sizeof(candidate) &&
		access(candidate, X_OK) == 0)
		return copy_string(resolved, resolved_size, candidate);

	if (snprintf(candidate, sizeof(candidate),
				 "find /snap/%s/current -type f -name '%s' 2>/dev/null | head -n 1",
				 app_name, app_name) >= (int)sizeof(candidate))
		return false;

	return read_first_matching_line(candidate, resolved, resolved_size);
}

static bool resolve_target_binary(const char *input_path, char *resolved,
								  size_t resolved_size)
{
	char current[PATH_MAX];
	char next[PATH_MAX];
	int depth;

	if (!input_path || !resolved || resolved_size == 0)
		return false;
	if (!copy_string(current, sizeof(current), input_path))
		return false;

	for (depth = 0; depth < 4; depth++) {
		char real[PATH_MAX];

		if (file_is_elf(current))
			return copy_string(resolved, resolved_size, current);

		if (parse_exec_target_from_script(current, next, sizeof(next))) {
			if (!copy_string(current, sizeof(current), next))
				return false;
			continue;
		}

		if (strncmp(current, "/snap/bin/", 10) == 0 &&
			find_snap_packaged_binary(path_basename_ptr(current), next,
									  sizeof(next))) {
			if (!copy_string(current, sizeof(current), next))
				return false;
			continue;
		}

		if (realpath(current, real) &&
			strcmp(path_basename_ptr(real), "snap") != 0) {
			if (file_is_elf(real))
				return copy_string(resolved, resolved_size, real);
			if (!copy_string(current, sizeof(current), real))
				return false;
			continue;
		}

		break;
	}

	return false;
}

static bool find_library_in_dir(const char *binary_path, const char *prefix,
								char *out, size_t out_size)
{
	DIR *dirp;
	struct dirent *entry;
	char dir[PATH_MAX];
	char candidate[PATH_MAX];

	if (!binary_path || !prefix || !out || out_size == 0)
		return false;
	if (!path_dirname_copy(binary_path, dir, sizeof(dir)))
		return false;

	dirp = opendir(dir);
	if (!dirp)
		return false;

	while ((entry = readdir(dirp)) != NULL) {
		if (strncmp(entry->d_name, prefix, strlen(prefix)) != 0)
			continue;
		if (!path_join(candidate, sizeof(candidate), dir, entry->d_name))
			continue;
		if (access(candidate, R_OK) == 0) {
			closedir(dirp);
			return copy_string(out, out_size, candidate);
		}
	}

	closedir(dirp);
	return false;
}

static bool find_linked_library(const char *binary_path, const char *lib_prefix,
								char *out, size_t out_size)
{
	char cmd[PATH_MAX + 64];
	char line[PATH_MAX * 2];
	FILE *fp;

	if (!binary_path || !lib_prefix || !out || out_size == 0)
		return false;
	if (snprintf(cmd, sizeof(cmd), "ldd '%s' 2>/dev/null", binary_path) >=
		(int)sizeof(cmd))
		return false;

	fp = popen(cmd, "r");
	if (!fp)
		return false;

	while (fgets(line, sizeof(line), fp)) {
		char *match = strstr(line, lib_prefix);
		char *arrow;
		char *path;
		char *end;

		if (!match)
			continue;

		arrow = strstr(line, "=>");
		if (!arrow)
			continue;
		path = arrow + 2;
		while (*path == ' ' || *path == '\t')
			path++;
		if (strncmp(path, "not found", 9) == 0)
			continue;
		end = path;
		while (*end && !isspace((unsigned char)*end))
			end++;
		*end = '\0';
		pclose(fp);
		return copy_string(out, out_size, path);
	}

	pclose(fp);
	return false;
}

static void detect_linked_tls_libraries(const char *binary_path,
										struct linked_tls_libraries *libs)
{
	memset(libs, 0, sizeof(*libs));
	if (!binary_path)
		return;

	find_library_in_dir(binary_path, "libnspr4.so", libs->nspr, sizeof(libs->nspr));
	if (!libs->nspr[0])
		find_linked_library(binary_path, "libnspr4.so",
							libs->nspr, sizeof(libs->nspr));

	find_library_in_dir(binary_path, "libssl3.so", libs->nss_ssl3,
						sizeof(libs->nss_ssl3));
	if (!libs->nss_ssl3[0])
		find_linked_library(binary_path, "libssl3.so",
							libs->nss_ssl3, sizeof(libs->nss_ssl3));
}

static void setup_target_process_filter(const char *requested_path,
										const char *resolved_target)
{
	memset(target_pid_cache, 0, sizeof(target_pid_cache));
	target_exec_path[0] = '\0';
	target_exec_basename[0] = '\0';

	if (resolved_target && resolved_target[0])
		copy_string(target_exec_path, sizeof(target_exec_path), resolved_target);

	if (resolved_target && resolved_target[0]) {
		copy_string(target_exec_basename, sizeof(target_exec_basename),
					path_basename_ptr(resolved_target));
	} else if (requested_path && requested_path[0]) {
		copy_string(target_exec_basename, sizeof(target_exec_basename),
					path_basename_ptr(requested_path));
	}
}

static size_t target_pid_cache_slot(pid_t pid)
{
	return ((unsigned int)pid) % TARGET_PID_CACHE_SIZE;
}

static bool lookup_target_pid_cache(pid_t pid, bool *matched)
{
	size_t start = target_pid_cache_slot(pid);
	size_t i;

	for (i = 0; i < TARGET_PID_CACHE_SIZE; i++) {
		struct target_pid_cache_entry *entry =
			&target_pid_cache[(start + i) % TARGET_PID_CACHE_SIZE];
		if (!entry->valid)
			return false;
		if (entry->pid != pid)
			continue;
		*matched = entry->matched;
		return true;
	}

	return false;
}

static void store_target_pid_cache(pid_t pid, bool matched)
{
	size_t start = target_pid_cache_slot(pid);
	size_t i;

	for (i = 0; i < TARGET_PID_CACHE_SIZE; i++) {
		struct target_pid_cache_entry *entry =
			&target_pid_cache[(start + i) % TARGET_PID_CACHE_SIZE];
		if (entry->valid && entry->pid != pid)
			continue;
		entry->pid = pid;
		entry->valid = true;
		entry->matched = matched;
		return;
	}

	target_pid_cache[start].pid = pid;
	target_pid_cache[start].valid = true;
	target_pid_cache[start].matched = matched;
}

static bool target_process_matches(pid_t pid)
{
	char proc_exe[64];
	char exe_path[PATH_MAX];
	ssize_t len;
	bool matched;

	if (!target_exec_path[0] && !target_exec_basename[0])
		return true;
	if (lookup_target_pid_cache(pid, &matched))
		return matched;

	snprintf(proc_exe, sizeof(proc_exe), "/proc/%d/exe", pid);
	len = readlink(proc_exe, exe_path, sizeof(exe_path) - 1);
	if (len <= 0) {
		store_target_pid_cache(pid, false);
		return false;
	}

	exe_path[len] = '\0';
	matched = false;
	if (target_exec_path[0] && strcmp(exe_path, target_exec_path) == 0)
		matched = true;
	else if (target_exec_basename[0] &&
			 strcmp(path_basename_ptr(exe_path), target_exec_basename) == 0)
		matched = true;

	store_target_pid_cache(pid, matched);
	return matched;
}

static size_t find_masked_pattern(const unsigned char *data, size_t data_len,
								  const unsigned char *pattern,
								  const char *mask, size_t pattern_len)
{
	size_t i;

	if (pattern_len > data_len || strlen(mask) != pattern_len)
		return (size_t)-1;

	for (i = 0; i <= data_len - pattern_len; i++) {
		size_t j;
		bool matched = true;

		for (j = 0; j < pattern_len; j++) {
			if (mask[j] == 'x' && data[i + j] != pattern[j]) {
				matched = false;
				break;
			}
		}
		if (matched)
			return i;
	}

	return (size_t)-1;
}

static struct chrome_plaintext_offsets
find_chrome_plaintext_offsets(const char *binary_path)
{
	struct chrome_plaintext_offsets result = { .found = false };
	int fd = -1;
	struct stat st;
	unsigned char *data = NULL;

	static const unsigned char request_copy_1_pat[] = {
		0x4c, 0x89, 0xe7, 0x4c, 0x89, 0xf6, 0x4c, 0x89,
		0xfa, 0xe8, 0x00, 0x00, 0x00, 0x00, 0x43, 0xc6,
		0x04, 0x3c, 0x00, 0x48, 0x8d, 0x5d, 0xb8, 0x80,
		0x7b, 0x17, 0x00
	};
	static const char request_copy_1_mask[] = "xxxxxxxxxx????xxxxxxxxxxxxx";

	static const unsigned char request_copy_2_pat[] = {
		0x4c, 0x89, 0xf7, 0x48, 0x89, 0xde, 0x4c, 0x89,
		0xea, 0xe8, 0x00, 0x00, 0x00, 0x00, 0x43, 0xc6,
		0x04, 0x2e, 0x00, 0x49, 0xbd, 0xf6, 0xff, 0xff,
		0xff, 0xff, 0xff, 0xff, 0x7f
	};
	static const char request_copy_2_mask[] = "xxxxxxxxxx????xxxxxxxxxxxxxxx";

	static const unsigned char request_copy_3_pat[] = {
		0x48, 0x89, 0xdf, 0x4c, 0x89, 0xe6, 0x4c, 0x89,
		0xfa, 0xe8, 0x00, 0x00, 0x00, 0x00, 0x42, 0xc6,
		0x04, 0x3b, 0x00, 0x4c, 0x8b, 0x65, 0x90, 0x4d,
		0x8b, 0x7c, 0x24, 0x08
	};
	static const char request_copy_3_mask[] = "xxxxxxxxxx????xxxxxxxxxxxxxx";

	static const unsigned char response_copy_pat[] = {
		0x48, 0x8b, 0xb0, 0x80, 0x00, 0x00, 0x00, 0x48,
		0x8b, 0x7d, 0xb8, 0x4c, 0x89, 0xfa, 0xe8, 0x00,
		0x00, 0x00, 0x00, 0x49, 0x8b, 0x46, 0x30, 0x48,
		0x8b, 0x88, 0x88, 0x00, 0x00, 0x00
	};
	static const char response_copy_mask[] = "xxxxxxxxxxxxxxx????xxxxxxxxxxx";

	fd = open(binary_path, O_RDONLY);
	if (fd < 0) {
		fprintf(stderr, "Failed to open %s: %s\n", binary_path, strerror(errno));
		return result;
	}

	if (fstat(fd, &st) < 0) {
		fprintf(stderr, "Failed to stat %s: %s\n", binary_path, strerror(errno));
		close(fd);
		return result;
	}

	data = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
	if (data == MAP_FAILED) {
		fprintf(stderr, "Failed to mmap %s: %s\n", binary_path, strerror(errno));
		close(fd);
		return result;
	}

	result.request_copy_1 = find_masked_pattern(data, st.st_size,
												 request_copy_1_pat,
												 request_copy_1_mask,
												 sizeof(request_copy_1_pat));
	result.request_copy_2 = find_masked_pattern(data, st.st_size,
												 request_copy_2_pat,
												 request_copy_2_mask,
												 sizeof(request_copy_2_pat));
	result.request_copy_3 = find_masked_pattern(data, st.st_size,
												 request_copy_3_pat,
												 request_copy_3_mask,
												 sizeof(request_copy_3_pat));
	result.response_copy = find_masked_pattern(data, st.st_size,
												response_copy_pat,
												response_copy_mask,
												sizeof(response_copy_pat));

	if (result.request_copy_1 != (size_t)-1)
		result.request_copy_1 += 9;
	if (result.request_copy_2 != (size_t)-1)
		result.request_copy_2 += 9;
	if (result.request_copy_3 != (size_t)-1)
		result.request_copy_3 += 9;
	if (result.response_copy != (size_t)-1)
		result.response_copy += 14;

	result.found = result.request_copy_1 != (size_t)-1 &&
				   result.request_copy_2 != (size_t)-1 &&
				   result.request_copy_3 != (size_t)-1 &&
				   result.response_copy != (size_t)-1;

	if (result.found && verbose) {
		fprintf(stderr, "Chrome plaintext copy points detected in %s:\n", binary_path);
		fprintf(stderr, "  request_copy_1: 0x%lx\n", result.request_copy_1);
		fprintf(stderr, "  request_copy_2: 0x%lx\n", result.request_copy_2);
		fprintf(stderr, "  request_copy_3: 0x%lx\n", result.request_copy_3);
		fprintf(stderr, "  response_copy:  0x%lx\n", result.response_copy);
	}

	munmap(data, st.st_size);
	close(fd);
	return result;
}

static void destroy_link(struct bpf_link **link)
{
	if (!link || !*link)
		return;

	bpf_link__destroy(*link);
	*link = NULL;
}

static void destroy_extra_links(void)
{
	size_t i;

	for (i = 0; i < BROWSER_EXTRA_LINK_CAP; i++)
		destroy_link(&browser_extra_links[i]);
}

static void destroy_browser_links(struct browsertrace_bpf *skel)
{
	destroy_extra_links();
	if (!skel)
		return;

	destroy_link(&skel->links.probe_nss_import_fd_enter);
	destroy_link(&skel->links.probe_nss_import_fd_exit);
	destroy_link(&skel->links.probe_nss_close_enter);
	destroy_link(&skel->links.probe_chrome_plaintext_request_1);
	destroy_link(&skel->links.probe_chrome_plaintext_request_2);
	destroy_link(&skel->links.probe_chrome_plaintext_request_3);
	destroy_link(&skel->links.probe_chrome_plaintext_response);
}

static int remember_extra_link(struct bpf_link *link)
{
	size_t i;

	for (i = 0; i < BROWSER_EXTRA_LINK_CAP; i++) {
		if (browser_extra_links[i])
			continue;
		browser_extra_links[i] = link;
		return 0;
	}

	return -ENOSPC;
}

static int attach_symbol_program(struct bpf_program *prog, struct bpf_link **link,
								 pid_t pid, const char *binary_path,
								 const char *symbol, bool retprobe,
								 const char *label)
{
	LIBBPF_OPTS(bpf_uprobe_opts, opts,
				.func_name = symbol,
				.retprobe = retprobe);
	struct bpf_link *attached = bpf_program__attach_uprobe_opts(
		prog, pid, binary_path, 0, &opts);
	long err;

	if (!attached) {
		fprintf(stderr, "Failed to attach %s to %s: %s\n",
				label, binary_path, strerror(errno));
		return -errno;
	}

	err = libbpf_get_error(attached);
	if (err) {
		fprintf(stderr, "Failed to attach %s to %s: %s\n",
				label, binary_path, strerror((int)-err));
		return (int)err;
	}

	*link = attached;
	return 0;
}

static int attach_symbol_program_extra(struct bpf_program *prog, pid_t pid,
									   const char *binary_path,
									   const char *symbol, bool retprobe,
									   const char *label)
{
	struct bpf_link *link = NULL;
	int err;

	err = attach_symbol_program(prog, &link, pid, binary_path, symbol, retprobe,
								label);
	if (err)
		return err;

	err = remember_extra_link(link);
	if (err) {
		destroy_link(&link);
		fprintf(stderr, "Failed to track %s link: %s\n",
				label, strerror(-err));
	}

	return err;
}

static int attach_offset_program(struct bpf_program *prog, struct bpf_link **link,
								 pid_t pid, const char *binary_path,
								 size_t offset, const char *label)
{
	LIBBPF_OPTS(bpf_uprobe_opts, opts);
	struct bpf_link *attached = bpf_program__attach_uprobe_opts(
		prog, pid, binary_path, offset, &opts);
	long err;

	if (!attached) {
		fprintf(stderr, "Failed to attach %s to %s: %s\n",
				label, binary_path, strerror(errno));
		return -errno;
	}

	err = libbpf_get_error(attached);
	if (err) {
		fprintf(stderr, "Failed to attach %s to %s: %s\n",
				label, binary_path, strerror((int)-err));
		return (int)err;
	}

	*link = attached;
	return 0;
}

static int attach_nss(struct browsertrace_bpf *skel, pid_t pid,
					  const char *nspr_lib, const char *nss_ssl3_lib)
{
	int err;

	if (!nspr_lib || !nspr_lib[0])
		return -ENOENT;

	if (nss_ssl3_lib && nss_ssl3_lib[0]) {
		err = attach_symbol_program(skel->progs.probe_nss_import_fd_enter,
									&skel->links.probe_nss_import_fd_enter,
									pid, nss_ssl3_lib, "SSL_ImportFD", false,
									"probe_nss_import_fd_enter");
		if (err)
			goto error;
		err = attach_symbol_program(skel->progs.probe_nss_import_fd_exit,
									&skel->links.probe_nss_import_fd_exit,
									pid, nss_ssl3_lib, "SSL_ImportFD", true,
									"probe_nss_import_fd_exit");
		if (err)
			goto error;
	} else {
		return -ENOENT;
	}

	err = attach_symbol_program_extra(skel->progs.probe_nss_rw_enter,
									  pid, nspr_lib, "PR_Write", false,
									  "probe_nss_rw_enter(PR_Write)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_write_exit,
									  pid, nspr_lib, "PR_Write", true,
									  "probe_nss_write_exit(PR_Write)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_rw_enter,
									  pid, nspr_lib, "PR_Send", false,
									  "probe_nss_rw_enter(PR_Send)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_write_exit,
									  pid, nspr_lib, "PR_Send", true,
									  "probe_nss_write_exit(PR_Send)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_rw_enter,
									  pid, nspr_lib, "PR_Read", false,
									  "probe_nss_rw_enter(PR_Read)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_read_exit,
									  pid, nspr_lib, "PR_Read", true,
									  "probe_nss_read_exit(PR_Read)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_rw_enter,
									  pid, nspr_lib, "PR_Recv", false,
									  "probe_nss_rw_enter(PR_Recv)");
	if (err)
		goto error;
	err = attach_symbol_program_extra(skel->progs.probe_nss_read_exit,
									  pid, nspr_lib, "PR_Recv", true,
									  "probe_nss_read_exit(PR_Recv)");
	if (err)
		goto error;
	err = attach_symbol_program(skel->progs.probe_nss_close_enter,
								&skel->links.probe_nss_close_enter,
								pid, nspr_lib, "PR_Close", false,
								"probe_nss_close_enter");
	if (err)
		goto error;

	return 0;

error:
	destroy_browser_links(skel);
	return err;
}

static int attach_chrome_plaintext(struct browsertrace_bpf *skel, pid_t pid,
								   const char *binary_path,
								   const struct chrome_plaintext_offsets *offsets)
{
	int err;

	err = attach_offset_program(skel->progs.probe_chrome_plaintext_request_1,
								&skel->links.probe_chrome_plaintext_request_1,
								pid, binary_path, offsets->request_copy_1,
								"probe_chrome_plaintext_request_1");
	if (err)
		goto error;
	err = attach_offset_program(skel->progs.probe_chrome_plaintext_request_2,
								&skel->links.probe_chrome_plaintext_request_2,
								pid, binary_path, offsets->request_copy_2,
								"probe_chrome_plaintext_request_2");
	if (err)
		goto error;
	err = attach_offset_program(skel->progs.probe_chrome_plaintext_request_3,
								&skel->links.probe_chrome_plaintext_request_3,
								pid, binary_path, offsets->request_copy_3,
								"probe_chrome_plaintext_request_3");
	if (err)
		goto error;
	err = attach_offset_program(skel->progs.probe_chrome_plaintext_response,
								&skel->links.probe_chrome_plaintext_response,
								pid, binary_path, offsets->response_copy,
								"probe_chrome_plaintext_response");
	if (err)
		goto error;

	return 0;

error:
	destroy_browser_links(skel);
	return err;
}

static int attach_browser_target(struct browsertrace_bpf *skel, const char *attach_target,
								 const struct linked_tls_libraries *libs)
{
	if (target_is_chromium_family(attach_target)) {
		struct chrome_plaintext_offsets offsets =
			find_chrome_plaintext_offsets(attach_target);

		if (!offsets.found) {
			fprintf(stderr, "No Chrome plaintext copy points found in %s\n",
					attach_target);
			return -ENOENT;
		}

		fprintf(stderr, "Chrome plaintext copy points detected! Attaching by offset...\n");
		return attach_chrome_plaintext(skel, env.pid, attach_target, &offsets);
	}

	if (target_is_firefox(attach_target)) {
		if (verbose) {
			fprintf(stderr, "Using Firefox/NSS backend for %s\n", attach_target);
			fprintf(stderr, "  NSS PR path: %s\n",
					libs->nspr[0] ? libs->nspr : "not found");
			fprintf(stderr, "  NSS SSL path: %s\n",
					libs->nss_ssl3[0] ? libs->nss_ssl3 : "not found");
		}
		if (!libs->nspr[0] || !libs->nss_ssl3[0])
			return -ENOENT;
		return attach_nss(skel, env.pid, libs->nspr, libs->nss_ssl3);
	}

	fprintf(stderr, "Unsupported browser target: %s\n", attach_target);
	return -EINVAL;
}

static int validate_utf8_char(const unsigned char *str, size_t remaining)
{
	unsigned char c;
	int expected_len = 0;
	char temp[5] = {0};
	wchar_t wc;
	mbstate_t state;
	size_t result;

	if (!str || remaining == 0)
		return 0;

	c = str[0];
	if (c < 0x80)
		return 1;

	if ((c & 0xE0) == 0xC0)
		expected_len = 2;
	else if ((c & 0xF0) == 0xE0)
		expected_len = 3;
	else if ((c & 0xF8) == 0xF0)
		expected_len = 4;
	else
		return 0;

	if (remaining < (size_t)expected_len)
		return 0;

	memcpy(temp, str, expected_len > 4 ? 4 : expected_len);
	memset(&state, 0, sizeof(state));
	result = mbrtowc(&wc, temp, expected_len, &state);
	if (result == (size_t)-1 || result == (size_t)-2 || result == 0)
		return 0;

	if (expected_len == 2) {
		unsigned int codepoint = ((c & 0x1F) << 6) | (str[1] & 0x3F);
		if (codepoint < 0x80)
			return 0;
	} else if (expected_len == 3) {
		unsigned int codepoint = ((c & 0x0F) << 12) |
								 ((str[1] & 0x3F) << 6) |
								 (str[2] & 0x3F);
		if (codepoint < 0x800)
			return 0;
		if (codepoint >= 0xD800 && codepoint <= 0xDFFF)
			return 0;
	} else if (expected_len == 4) {
		unsigned int codepoint = ((c & 0x07) << 18) |
								 ((str[1] & 0x3F) << 12) |
								 ((str[2] & 0x3F) << 6) |
								 (str[3] & 0x3F);
		if (codepoint < 0x10000 || codepoint > 0x10FFFF)
			return 0;
	}

	return expected_len;
}

static void print_event(struct probe_SSL_data_t *event)
{
	static unsigned long long start;
	unsigned int buf_size;
	unsigned int i;

	if (!event_buf) {
		fprintf(stderr, "Error: global buffer not allocated\n");
		return;
	}

	if (event->buf_filled == 1) {
		buf_size = event->buf_size;
		if (buf_size > MAX_BUF_SIZE)
			buf_size = MAX_BUF_SIZE;
		if (buf_size > 0) {
			memcpy(event_buf, event->buf, buf_size);
			event_buf[buf_size] = '\0';
		}
	} else {
		buf_size = 0;
	}

	if (env.comm && strcmp(env.comm, event->comm) != 0)
		return;
	if (!target_process_matches(event->pid))
		return;

	if (start == 0)
		start = event->timestamp_ns;

	printf("{");
	printf("\"function\":\"%s\",", event->rw == 0 ? "READ/RECV" : "WRITE/SEND");
	printf("\"timestamp_ns\":%llu,", event->timestamp_ns);
	printf("\"comm\":\"%s\",", event->comm);
	printf("\"pid\":%d,", event->pid);
	printf("\"len\":%d,", event->len);
	printf("\"buf_size\":%u,", event->buf_size);
	printf("\"uid\":%d,", event->uid);
	printf("\"tid\":%d,", event->tid);
	printf("\"latency_ms\":%.3f,", (double)event->delta_ns / 1000000);
	printf("\"data\":");
	if (buf_size == 0) {
		printf("null,\"truncated\":false}\n");
		fflush(stdout);
		return;
	}

	printf("\"");
	for (i = 0; i < buf_size; i++) {
		unsigned char c = event_buf[i];

		if (c == '"' || c == '\\') {
			printf("\\%c", c);
		} else if (c == '\n') {
			printf("\\n");
		} else if (c == '\r') {
			printf("\\r");
		} else if (c == '\t') {
			printf("\\t");
		} else if (c == '\b') {
			printf("\\b");
		} else if (c == '\f') {
			printf("\\f");
		} else if (c >= 32 && c <= 126) {
			printf("%c", c);
		} else if (c >= 128) {
			int utf8_len = validate_utf8_char((unsigned char *)&event_buf[i],
											  buf_size - i);
			if (utf8_len > 0) {
				int j;
				for (j = 0; j < utf8_len; j++)
					printf("%c", event_buf[i + j]);
				i += utf8_len - 1;
			} else {
				printf("\\u%04x", c);
			}
		} else {
			printf("\\u%04x", c);
		}
	}
	printf("\",");

	if (buf_size < event->len)
		printf("\"truncated\":true,\"bytes_lost\":%d}\n", event->len - buf_size);
	else
		printf("\"truncated\":false}\n");
	fflush(stdout);
}

static int handle_event(void *ctx, void *data, size_t data_sz)
{
	struct probe_SSL_data_t *event = data;

	(void)ctx;
	(void)data_sz;
	print_event(event);
	return 0;
}

int main(int argc, char **argv)
{
	LIBBPF_OPTS(bpf_object_open_opts, open_opts);
	struct browsertrace_bpf *obj = NULL;
	struct ring_buffer *rb = NULL;
	struct linked_tls_libraries libs = {};
	char resolved_target[PATH_MAX] = {};
	const char *attach_target;
	int err;

	err = argp_parse(&argp, argc, argv, 0, NULL, NULL);
	if (err)
		return err;

	setlocale(LC_ALL, "");
	libbpf_set_print(libbpf_print_fn);

	obj = browsertrace_bpf__open_opts(&open_opts);
	if (!obj) {
		warn("failed to open BPF object\n");
		goto cleanup;
	}

	obj->rodata->targ_uid = env.uid;
	obj->rodata->targ_pid = env.pid == INVALID_PID ? 0 : env.pid;

	err = browsertrace_bpf__load(obj);
	if (err) {
		warn("failed to load BPF object: %d\n", err);
		goto cleanup;
	}

	event_buf = malloc(MAX_BUF_SIZE + 1);
	if (!event_buf) {
		warn("failed to allocate event buffer\n");
		err = -ENOMEM;
		goto cleanup;
	}

	if (!resolve_target_binary(env.binary_path, resolved_target,
							   sizeof(resolved_target))) {
		warn("failed to resolve browser binary from %s\n", env.binary_path);
		err = -ENOENT;
		goto cleanup;
	}

	attach_target = resolved_target;
	setup_target_process_filter(env.binary_path, attach_target);
	detect_linked_tls_libraries(attach_target, &libs);

	if (verbose)
		fprintf(stderr, "Attaching to browser target: %s\n", attach_target);

	err = attach_browser_target(obj, attach_target, &libs);
	if (err) {
		warn("failed to attach browser backend for %s: %s\n",
			 attach_target, strerror(-err));
		goto cleanup;
	}

	rb = ring_buffer__new(bpf_map__fd(obj->maps.rb), handle_event, NULL, NULL);
	if (!rb) {
		err = -errno;
		warn("failed to open ring buffer: %d\n", err);
		goto cleanup;
	}

	if (signal(SIGINT, sig_int) == SIG_ERR) {
		warn("can't set signal handler: %s\n", strerror(errno));
		err = 1;
		goto cleanup;
	}

	while (!exiting) {
		err = ring_buffer__poll(rb, PERF_POLL_TIMEOUT_MS);
		if (err < 0 && err != -EINTR) {
			warn("error polling ring buffer: %s\n", strerror(-err));
			goto cleanup;
		}
		err = 0;
	}

cleanup:
	if (event_buf) {
		free(event_buf);
		event_buf = NULL;
	}
	if (env.binary_path) {
		free(env.binary_path);
		env.binary_path = NULL;
	}
	if (env.comm) {
		free(env.comm);
		env.comm = NULL;
	}
	ring_buffer__free(rb);
	destroy_browser_links(obj);
	browsertrace_bpf__destroy(obj);
	return err != 0;
}
