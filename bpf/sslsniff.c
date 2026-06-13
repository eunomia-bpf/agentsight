// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2023 Yusheng Zheng
//
// Based on sslsniff from BCC by Adrian Lopez & Mark Drayton.
// 15-Aug-2023   Yusheng Zheng   Created this.
#include <argp.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <ctype.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <locale.h>
#include <wchar.h>
#include <string.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "sslsniff.skel.h"
#include "sslsniff.h"
#include "container_info.h"
#include "jsonl.h"

#define INVALID_UID -1
#define INVALID_PID -1
#define DEFAULT_BUFFER_SIZE 8192

#define __ATTACH_UPROBE(skel, binary_path, sym_name, prog_name, is_retprobe)   \
	do {                                                                       \
	  LIBBPF_OPTS(bpf_uprobe_opts, uprobe_opts, .func_name = #sym_name,        \
				  .retprobe = is_retprobe);                                    \
	  skel->links.prog_name = bpf_program__attach_uprobe_opts(                 \
		  skel->progs.prog_name, env.pid, binary_path, 0, &uprobe_opts);       \
	} while (false)

#define __CHECK_PROGRAM(skel, prog_name)               \
	do {                                               \
	  long __err = libbpf_get_error(skel->links.prog_name); \
	  if (__err) {                                     \
		skel->links.prog_name = NULL;                  \
		return (int)__err;                             \
	  }                                                \
	  if (!skel->links.prog_name) {                    \
		perror("no program attached for " #prog_name); \
		return -(errno ? errno : ENOENT);              \
	  }                                                \
	} while (false)

#define __ATTACH_UPROBE_CHECKED(skel, binary_path, sym_name, prog_name,     \
								is_retprobe)                                \
	do {                                                                    \
	  __ATTACH_UPROBE(skel, binary_path, sym_name, prog_name, is_retprobe); \
	  __CHECK_PROGRAM(skel, prog_name);                                     \
	} while (false)

#define ATTACH_UPROBE_CHECKED(skel, binary_path, sym_name, prog_name)     \
	__ATTACH_UPROBE_CHECKED(skel, binary_path, sym_name, prog_name, false)
#define ATTACH_URETPROBE_CHECKED(skel, binary_path, sym_name, prog_name)  \
	__ATTACH_UPROBE_CHECKED(skel, binary_path, sym_name, prog_name, true)

#define __ATTACH_UPROBE_OFFSET(skel, binary_path, offset, prog_name, is_retprobe) \
	do {                                                                          \
	  LIBBPF_OPTS(bpf_uprobe_opts, uprobe_opts, .retprobe = is_retprobe);         \
	  skel->links.prog_name = bpf_program__attach_uprobe_opts(                    \
		  skel->progs.prog_name, env.pid, binary_path, offset, &uprobe_opts);     \
	} while (false)

#define ATTACH_UPROBE_OFFSET_CHECKED(skel, binary_path, offset, prog_name)       \
	do {                                                                         \
	  __ATTACH_UPROBE_OFFSET(skel, binary_path, offset, prog_name, false);       \
	  __CHECK_PROGRAM(skel, prog_name);                                          \
	} while (false)

#define ATTACH_URETPROBE_OFFSET_CHECKED(skel, binary_path, offset, prog_name)    \
	do {                                                                         \
	  __ATTACH_UPROBE_OFFSET(skel, binary_path, offset, prog_name, true);        \
	  __CHECK_PROGRAM(skel, prog_name);                                          \
	} while (false)

volatile sig_atomic_t exiting = 0;

const char *argp_program_version = "sslsniff 0.1";
const char *argp_program_bug_address = "https://github.com/iovisor/bcc/tree/master/libbpf-tools";
const char argp_program_doc[] =
	"Sniff SSL data and output in JSON format.\n"
	"\n"
	"USAGE: sslsniff [OPTIONS]\n"
	"\n"
	"OUTPUT: Each SSL event is output as a JSON object on a separate line.\n"
	"eBPF capture is limited to 32KB per event due to kernel constraints.\n"
	"\n"
	"EXAMPLES:\n"
	"    ./sslsniff              # sniff OpenSSL and GnuTLS functions\n"
	"    ./sslsniff -p 181       # sniff PID 181 only\n"
	"    ./sslsniff -u 1000      # sniff only UID 1000\n"
	"    ./sslsniff -c curl      # sniff curl command only\n"
	"    ./sslsniff --no-openssl # don't show OpenSSL calls\n"
	"    ./sslsniff --no-gnutls  # don't show GnuTLS calls\n"
	"    ./sslsniff --no-nss     # don't show NSS calls\n"
	"    ./sslsniff --handshake # show handshake events\n"
	"    ./sslsniff --binary-path ~/.nvm/versions/node/v20.0.0/bin/node # attach to Node.js binary\n";

struct env {
	pid_t pid;
	pid_t session_id;
	int uid;
	char *comm;
	bool openssl;
	bool gnutls;
	bool nss;
	bool handshake;
	char *extra_lib;
} env = {
	.uid = INVALID_UID,
	.pid = INVALID_PID,
	.session_id = INVALID_PID,
	.openssl = true,
	.gnutls = false,
	.nss = false,
	.handshake = false,
	.comm = NULL,
};

#define EXTRA_LIB_KEY 1003
#define SESSION_KEY 1004

static const struct argp_option opts[] = {
	{"pid", 'p', "PID", 0, "Sniff this PID only."},
	{"session", SESSION_KEY, "SID", 0, "Sniff this process session only."},
	{"uid", 'u', "UID", 0, "Sniff this UID only."},
	{"comm", 'c', "COMMAND", 0, "Sniff only commands matching string."},
	{"no-openssl", 'o', NULL, 0, "Do not show OpenSSL calls."},
	{"no-gnutls", 'g', NULL, 0, "Do not show GnuTLS calls."},
	{"no-nss", 'n', NULL, 0, "Do not show NSS calls."},
	{"handshake", 'h', NULL, 0, "Show handshake events."},
	{"verbose", 'v', NULL, 0, "Verbose debug output"},
	{"binary-path", EXTRA_LIB_KEY, "PATH", 0, "Attach to specific binary (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)."},
	{},
};

static bool verbose = false;

/*
 * BoringSSL function offset detection for stripped binaries.
 *
 * When a binary (e.g., Bun-based apps like Claude CLI) statically links
 * BoringSSL and strips symbols, we can still find SSL_write/SSL_read/
 * SSL_do_handshake by searching for their unique function prologue byte
 * patterns. These patterns are derived from Bun v1.3.x profile builds.
 */
struct boringssl_offsets {
	size_t ssl_write;
	size_t ssl_read;
	size_t ssl_do_handshake;
	bool found;
};

static size_t find_pattern(const unsigned char *data, size_t data_len,
						   const unsigned char *pattern, size_t pattern_len)
{
	if (pattern_len > data_len)
		return (size_t)-1;
	for (size_t i = 0; i <= data_len - pattern_len; i++) {
		if (memcmp(data + i, pattern, pattern_len) == 0)
			return i;
	}
	return (size_t)-1;
}

static struct boringssl_offsets find_boringssl_offsets(const char *binary_path) {
	struct boringssl_offsets result = { .found = false };
	int fd = -1;
	struct stat st;
	unsigned char *data = NULL;
	size_t file_size;

	/* BoringSSL SSL_do_handshake prologue (24 bytes) */
	static const unsigned char handshake_pat[] = {
		0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
		0x41, 0x55, 0x41, 0x54, 0x53, 0x48, 0x83, 0xec,
		0x28, 0x49, 0x89, 0xfc, 0x48, 0x8b, 0x47, 0x30
	};

	/* BoringSSL SSL_read prologue (19 bytes) */
	static const unsigned char read_pat[] = {
		0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
		0x53, 0x50, 0x48, 0x83, 0xbf, 0x98, 0x00, 0x00,
		0x00, 0x00, 0x74
	};

	/* BoringSSL SSL_write prologue (26 bytes) */
	static const unsigned char write_pat[] = {
		0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
		0x41, 0x55, 0x41, 0x54, 0x53, 0x48, 0x83, 0xec,
		0x18, 0x41, 0x89, 0xd7, 0x49, 0x89, 0xf6, 0x48,
		0x89, 0xfb
	};

	/* Known relative distances between functions (from Bun v1.3.x) */
	static const size_t READ_HANDSHAKE_DELTA = 0x6F0;
	static const size_t WRITE_READ_DELTA = 0xCA0;

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

	if (st.st_size <= 0) {
		fprintf(stderr, "Invalid binary size for %s\n", binary_path);
		close(fd);
		return result;
	}
	file_size = (size_t)st.st_size;

	data = malloc(file_size);
	if (!data) {
		fprintf(stderr, "Failed to allocate %zu bytes for %s\n", file_size, binary_path);
		close(fd);
		return result;
	}
	size_t total = 0;
	while (total < file_size) {
		ssize_t n = read(fd, data + total, file_size - total);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			fprintf(stderr, "Failed to read %s: %s\n", binary_path, strerror(errno));
			goto out;
		}
		if (n == 0)
			break;
		total += (size_t)n;
	}
	if (total != file_size) {
		fprintf(stderr, "Short read from %s: %zu of %zu bytes\n",
				binary_path, total, file_size);
		goto out;
	}

	/* Find SSL_read (most unique pattern), then validate nearby functions */
	size_t read_off = find_pattern(data, file_size, read_pat, sizeof(read_pat));
	if (read_off == (size_t)-1) {
		if (verbose)
			fprintf(stderr, "BoringSSL: SSL_read pattern not found\n");
		goto out;
	}

	/* Check if SSL_do_handshake is at expected relative position */
	if (read_off >= READ_HANDSHAKE_DELTA) {
		size_t expected_hs = read_off - READ_HANDSHAKE_DELTA;
		if (memcmp(data + expected_hs, handshake_pat, sizeof(handshake_pat)) == 0) {
			result.ssl_do_handshake = expected_hs;
		}
	}
	if (result.ssl_do_handshake == 0) {
		/* Fallback: search independently */
		size_t hs_off = find_pattern(data, file_size, handshake_pat, sizeof(handshake_pat));
		if (hs_off == (size_t)-1) {
			if (verbose)
				fprintf(stderr, "BoringSSL: SSL_do_handshake pattern not found\n");
			goto out;
		}
		result.ssl_do_handshake = hs_off;
	}

	result.ssl_read = read_off;

	/* Check if SSL_write is at expected relative position */
	size_t expected_wr = read_off + WRITE_READ_DELTA;
	if (expected_wr + sizeof(write_pat) <= file_size &&
		memcmp(data + expected_wr, write_pat, sizeof(write_pat)) == 0) {
		result.ssl_write = expected_wr;
	} else {
		/* Fallback: search near read function. Some standalone Bun apps
		 * place SSL_write before SSL_read even though Claude/Bun place it
		 * after SSL_read. */
		size_t search_start = read_off > 0x10000 ? read_off - 0x10000 : 0;
		size_t search_end = read_off + 0x10000;
		if (search_end > file_size)
			search_end = file_size;
		size_t wr_off = find_pattern(data + search_start,
									 search_end - search_start,
									 write_pat, sizeof(write_pat));
		if (wr_off == (size_t)-1) {
			if (verbose)
				fprintf(stderr, "BoringSSL: SSL_write pattern not found near SSL_read\n");
			goto out;
		}
		result.ssl_write = search_start + wr_off;
	}

	result.found = true;
	if (verbose) {
		fprintf(stderr, "BoringSSL detected in %s:\n", binary_path);
		fprintf(stderr, "  SSL_do_handshake offset: 0x%lx\n", result.ssl_do_handshake);
		fprintf(stderr, "  SSL_read offset:         0x%lx\n", result.ssl_read);
		fprintf(stderr, "  SSL_write offset:        0x%lx\n", result.ssl_write);
	}

out:
	free(data);
	close(fd);
	return result;
}

static error_t parse_arg(int key, char *arg, struct argp_state *state) {
	switch (key) {
	case 'p':
		env.pid = atoi(arg);
		break;
	case SESSION_KEY:
		errno = 0;
		env.session_id = (pid_t)strtol(arg, NULL, 10);
		if (errno || env.session_id <= 0) {
			fprintf(stderr, "Invalid session id: %s\n", arg);
			argp_usage(state);
		}
		break;
	case 'u':
		env.uid = atoi(arg);
		break;
	case 'c':
		env.comm = strdup(arg);
		break;
	case 'o':
		env.openssl = false;
		break;
	case 'g':
		env.gnutls = false;
		break;
	case 'n':
		env.nss = false;
		break;
	case 'h':
		env.handshake = true;
		break;
	case 'v':
		verbose = true;
		break;
	case EXTRA_LIB_KEY:
		env.extra_lib = strdup(arg);
		break;
	default:
		return ARGP_ERR_UNKNOWN;
	}
	return 0;
}

#define PERF_POLL_TIMEOUT_MS 100
#define warn(...) fprintf(stderr, __VA_ARGS__)

static struct argp argp = {
	opts,
	parse_arg,
	NULL,
	argp_program_doc
};

static int libbpf_print_fn(enum libbpf_print_level level, const char *format,
						   va_list args) {
	if (level == LIBBPF_DEBUG && !verbose)
		return 0;
	return vfprintf(stderr, format, args);
}

/* handle_lost_events removed - ring buffer doesn't have lost events like perf buffer */

static void sig_int(int signo) { 
	exiting = 1;
}

int attach_openssl(struct sslsniff_bpf *skel, const char *lib) {
	ATTACH_UPROBE_CHECKED(skel, lib, SSL_write, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, SSL_write, probe_SSL_write_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, SSL_read, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, SSL_read, probe_SSL_read_exit);

	ATTACH_UPROBE_CHECKED(skel, lib, SSL_write_ex, probe_SSL_write_ex_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, SSL_write_ex, probe_SSL_write_ex_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, SSL_read_ex, probe_SSL_read_ex_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, SSL_read_ex, probe_SSL_read_ex_exit);

	ATTACH_UPROBE_CHECKED(skel, lib, SSL_do_handshake,
							probe_SSL_do_handshake_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, SSL_do_handshake,
								probe_SSL_do_handshake_exit);

	return 0;
}

int attach_gnutls(struct sslsniff_bpf *skel, const char *lib) {
	ATTACH_UPROBE_CHECKED(skel, lib, gnutls_record_send, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, gnutls_record_send, probe_SSL_write_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, gnutls_record_recv, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, gnutls_record_recv, probe_SSL_read_exit);

	return 0;
}

int attach_nss(struct sslsniff_bpf *skel, const char *lib) {
	ATTACH_UPROBE_CHECKED(skel, lib, PR_Write, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, PR_Write, probe_SSL_write_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, PR_Send, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, PR_Send, probe_SSL_write_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, PR_Read, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, PR_Read, probe_SSL_read_exit);
	ATTACH_UPROBE_CHECKED(skel, lib, PR_Recv, probe_SSL_rw_enter);
	ATTACH_URETPROBE_CHECKED(skel, lib, PR_Recv, probe_SSL_read_exit);

	return 0;
}

int attach_openssl_by_offset(struct sslsniff_bpf *skel, const char *lib,
							 struct boringssl_offsets *offsets) {
	ATTACH_UPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_write, probe_SSL_rw_enter);
	ATTACH_URETPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_write, probe_SSL_write_exit);
	ATTACH_UPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_read, probe_SSL_rw_enter);
	ATTACH_URETPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_read, probe_SSL_read_exit);

	/* BoringSSL does not have SSL_write_ex/SSL_read_ex, skip those */

	if (env.handshake) {
		ATTACH_UPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_do_handshake,
									 probe_SSL_do_handshake_enter);
		ATTACH_URETPROBE_OFFSET_CHECKED(skel, lib, offsets->ssl_do_handshake,
										 probe_SSL_do_handshake_exit);
	}

	return 0;
}


/*
 * Find the path of a library using ldconfig.
 */
char *find_library_path(const char *libname) {
	char cmd[128];
	static char path[512];
	FILE *fp;

	// Construct the ldconfig command with grep
	snprintf(cmd, sizeof(cmd), "ldconfig -p | grep %s", libname);

	// Execute the command and read the output
	fp = popen(cmd, "r");
	if (fp == NULL) {
		perror("Failed to run ldconfig");
		return NULL;
	}

	// Read the first line of output which should have the library path
	if (fgets(path, sizeof(path) - 1, fp) != NULL) {
		// Extract the path from the ldconfig output
		char *start = strrchr(path, '>');
		if (start && *(start + 1) == ' ') {
			memmove(path, start + 2, strlen(start + 2) + 1);
			char *end = strchr(path, '\n');
			if (end) {
				*end = '\0';  // Null-terminate the path
			}
			pclose(fp);
			return path;
		}
	}

	pclose(fp);
	return NULL;
}

// Global buffer allocated once and reused
static char *event_buf = NULL;

// Function to print the event from the perf buffer in JSON format
void print_event(struct probe_SSL_data_t *event, const char *evt) {
	static unsigned long long start = 0;  // Use static to retain value across function calls
	unsigned int buf_size;

	// Safety check for global buffer
	if (!event_buf) {
		fprintf(stderr, "Error: global buffer not allocated\n");
		return;
	}

	// Use the actual bytes copied from eBPF
	if (event->buf_filled == 1) {
		buf_size = event->buf_size;
		// Additional safety check to prevent buffer overflow
		if (buf_size > MAX_BUF_SIZE) {
			buf_size = MAX_BUF_SIZE;
		}
		if (buf_size > 0) {
			memcpy(event_buf, event->buf, buf_size);
			event_buf[buf_size] = '\0';  // Null terminate
		}
	} else {
		buf_size = 0;
	}

	if (env.comm && strcmp(env.comm, event->comm) != 0) {
		return;
	}
	if (env.session_id > 0 && getsid(event->pid) != env.session_id) {
		return;
	}

	if (start == 0) {
		start = event->timestamp_ns;
	}

	char *rw_event[] = {
		"READ/RECV",
		"WRITE/SEND",
		"HANDSHAKE"
	};

	// Start JSON object
	printf("{");
	
	// Basic fields - always include all fields
	printf("\"function\":\"%s\",", rw_event[event->rw]);
	printf("\"timestamp_ns\":%llu,", event->timestamp_ns);
	printf("\"comm\":\"%s\",", event->comm);
	printf("\"pid\":%d,", event->pid);
	printf("\"len\":%d,", event->len);
	printf("\"buf_size\":%u,", event->buf_size);

	// Always include extra fields (UID, TID)
	printf("\"uid\":%d,", event->uid);
	printf("\"tid\":%d,", event->tid);

	// Always include latency field
	if (event->delta_ns) {
		printf("\"latency_ms\":%.3f,", (double)event->delta_ns / 1000000);
	} else {
		printf("\"latency_ms\":0,");
	}

	// Always include handshake field
	printf("\"is_handshake\":%s,", event->is_handshake ? "true" : "false");

	// Data field - always include both text and hex
	if (buf_size > 0) {
		// Text data
		printf("\"data\":");
		json_print_escaped_quoted(event_buf, buf_size);
		printf(",");

		// Add truncated info if data was truncated
		if (buf_size < event->len) {
			printf("\"truncated\":true,\"bytes_lost\":%d", event->len - buf_size);
		} else {
			printf("\"truncated\":false");
		}
	} else {
		printf("\"data\":null,\"truncated\":false");
	}

	// Container info (ns_pid, container_id) if applicable
	print_container_fields(event->pid);

	// Close JSON object
	printf("}\n");
	fflush(stdout);
}

static int handle_event(void *ctx, void *data, size_t data_sz) {
	struct probe_SSL_data_t *e = data;
	if (e->is_handshake) {
		if (env.handshake) {
			print_event(e, "ringbuf_SSL_do_handshake");
		}
	} else {
		print_event(e, "ringbuf_SSL_rw");
	}
	return 0;
}

int main(int argc, char **argv) {
	LIBBPF_OPTS(bpf_object_open_opts, open_opts);
	struct sslsniff_bpf *obj = NULL;
	struct ring_buffer *rb = NULL;
	int err;

	err = argp_parse(&argp, argc, argv, 0, NULL, NULL);
	if (err)
		return err;

	// Set locale for UTF-8 support
	setlocale(LC_ALL, "");

	libbpf_set_print(libbpf_print_fn);

	obj = sslsniff_bpf__open_opts(&open_opts);
	if (!obj) {
		warn("failed to open BPF object\n");
		goto cleanup;
	}

	obj->rodata->targ_uid = env.uid;
	obj->rodata->targ_pid = env.pid == INVALID_PID ? 0 : env.pid;

	err = sslsniff_bpf__load(obj);
	if (err) {
		warn("failed to load BPF object: %d\n", err);
		goto cleanup;
	}

	// Allocate global buffer once
	event_buf = malloc(MAX_BUF_SIZE + 1);
	if (!event_buf) {
		warn("failed to allocate event buffer\n");
		err = -ENOMEM;
		goto cleanup;
	}

	if (env.openssl) {
		char *openssl_path = find_library_path("libssl.so");
		if (verbose)
			fprintf(stderr, "OpenSSL path (host ldconfig): %s\n",
					openssl_path ? openssl_path : "not found");

		if (openssl_path) {
			attach_openssl(obj, openssl_path);
		} else {
			warn("OpenSSL library not found\n");
		}
	}
	if (env.gnutls) {
		char *gnutls_path = find_library_path("libgnutls.so");
		if (verbose) {
			fprintf(stderr, "GnuTLS path: %s\n", gnutls_path ? gnutls_path : "not found");
		}
		if (gnutls_path) {
			attach_gnutls(obj, gnutls_path);
		} else {
			warn("GnuTLS library not found\n");
		}
	}
	if (env.nss) {
		char *nss_path = find_library_path("libnspr4.so");
		if (verbose) {
			fprintf(stderr, "NSS path: %s\n", nss_path ? nss_path : "not found");
		}
		if (nss_path) {
			attach_nss(obj, nss_path);
		} else {
			warn("NSS library not found\n");
		}
	}

	// Handle custom binary path for statically-linked SSL (e.g., NVM Node.js, Bun apps)
	if (env.extra_lib) {
		err = -ENOENT;

		if (verbose) {
			fprintf(stderr, "Attaching to binary: %s\n", env.extra_lib);
		}
		if (access(env.extra_lib, R_OK) != 0) {
			err = -errno;
			warn("Cannot access binary-path %s: %s\n",
				 env.extra_lib, strerror(errno));
			goto cleanup;
		}
		// First try symbol-based attachment (works for binaries with symbols)
		LIBBPF_OPTS(bpf_uprobe_opts, test_opts, .func_name = "SSL_write",
					.retprobe = false);
		struct bpf_link *test_link = bpf_program__attach_uprobe_opts(
			obj->progs.probe_SSL_rw_enter, env.pid, env.extra_lib, 0, &test_opts);
		long test_err = test_link ? libbpf_get_error(test_link) : -(errno ? errno : EIO);
		if (test_link && !test_err) {
			// Symbol found - use standard symbol-based attachment
			bpf_link__destroy(test_link);
			if (verbose)
				fprintf(stderr, "Using symbol-based attachment for %s\n", env.extra_lib);
			err = attach_openssl(obj, env.extra_lib);
		} else if (test_err != -ENOENT) {
			err = (int)test_err;
			warn("Failed to probe SSL_write in %s: libbpf error %ld\n",
				 env.extra_lib, test_err);
		} else {
			// Symbol not found - try BoringSSL pattern detection
			if (verbose)
				fprintf(stderr, "Symbols not found, trying BoringSSL pattern detection...\n");
			struct boringssl_offsets offsets = find_boringssl_offsets(env.extra_lib);
			if (offsets.found) {
				fprintf(stderr, "BoringSSL detected! Attaching by offset...\n");
				err = attach_openssl_by_offset(obj, env.extra_lib, &offsets);
			} else {
				warn("Failed to attach to %s: no SSL symbols or BoringSSL patterns found\n",
					 env.extra_lib);
			}
		}

		if (err) {
			warn("binary-path attach failed for %s; refusing to continue with partial SSL capture\n",
				 env.extra_lib);
			goto cleanup;
		}
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
	if (env.extra_lib) {
		free(env.extra_lib);
		env.extra_lib = NULL;
	}
	if (env.comm) {
		free(env.comm);
		env.comm = NULL;
	}
	ring_buffer__free(rb);
	sslsniff_bpf__destroy(obj);
	return err != 0;
}
