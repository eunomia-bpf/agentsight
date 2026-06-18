// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
/* Copyright (c) 2020 Facebook */
#include <argp.h>
#include <signal.h>
#include <stdio.h>
#include <time.h>
#include <sys/resource.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include "process.h"
#include "process.skel.h"
#include "process_utils.h"
#include "process_filter.h"
#include "container_info.h"
#include "process_ext/map_flush.h"
#include "process_ext/userspace.h"

#define MAX_COMMAND_LIST 256
#define MAX_SEED_PIDS 4096
#define FILE_DEDUP_WINDOW_NS 60000000000ULL  // 60 seconds in nanoseconds
#define MAX_FILE_HASHES 1024

// Rate limiting per second
#define MAX_PID_LIMITS 256
#define MAX_DISTINCT_FILES_PER_SEC 30
#define POLL_TIMEOUT_MS 1000
#define FLUSH_INTERVAL_S 5

struct per_second_limit {
    pid_t pid;
    uint64_t current_second;
    uint32_t distinct_file_count;
    bool should_warn_next;
};

struct seed_pid {
	pid_t pid;
	pid_t ppid;
};

// Simple hash table for FILE_OPEN deduplication
struct file_hash_entry {
    uint64_t hash;
    uint64_t timestamp_ns;
    uint32_t count;
    pid_t pid;
    char comm[TASK_COMM_LEN];
    char filepath[MAX_FILENAME_LEN];
    int flags;
};

static struct file_hash_entry file_hashes[MAX_FILE_HASHES];
static int hash_count = 0;

static struct per_second_limit pid_limits[MAX_PID_LIMITS];
static int pid_limit_count = 0;

static struct env {
	bool verbose;
	long min_duration_ms;
	char *command_list[MAX_COMMAND_LIST];
	int command_count;
	struct seed_pid seed_pids[MAX_SEED_PIDS];
	int seed_count;
	enum filter_mode filter_mode;
	pid_t pid;
	pid_t session_id;
	bool trace_fs;
	bool trace_net;
	bool trace_signals;
	bool trace_mem;
	bool trace_cow;
	char cgroup_filter_path[256];
	bool cgroup_filter_enabled;
	bool cgroup_filter_children;
} env = {
	.verbose = false,
	.min_duration_ms = 0,
	.command_count = 0,
	.seed_count = 0,
	.filter_mode = FILTER_MODE_PROC,
	.pid = 0,
	.session_id = 0,
};

/* Global PID tracker for userspace filtering */
static struct pid_tracker pid_tracker;
static int g_agg_map_fd = -1;
static int g_tracked_pids_fd = -1;
static int g_tracked_cgroups_fd = -1;
static int g_overflow_fd = -1;
static int g_exit_mem_fd = -1;
static long page_size_kb;

const char *argp_program_version = "process-tracer 1.0";
const char *argp_program_bug_address = "<bpf@vger.kernel.org>";
const char argp_program_doc[] =
	"BPF process tracer with 3-level filtering.\n"
	"\n"
	"It traces process start and exits with configurable filtering levels.\n"
	"Shows associated information (filename, process duration, PID and PPID, etc).\n"
	"\n"
	"USAGE: ./process [-d <min-duration-ms>] [-c <command1,command2,...>] [-p <pid>] [--session <sid>] [-m <mode>] [-v]\n"
	"       [--trace-fs] [--trace-net] [--trace-signals] [--trace-mem] [--trace-cow] [--trace-all]\n"
	"       [--cgroup-filter <path>] [--cgroup-filter-children] [--seed-pid <pid:ppid>]\n"
	"\n"
	"FILTER MODES:\n"
	"  0 (all):    Trace all processes and all read/write operations\n"
	"  1 (proc):   Trace all processes but only read/write for tracked PIDs\n"
	"  2 (filter): Only trace processes matching filters and their read/write\n"
	"\n"
	"EXAMPLES:\n"
	"  ./process -m 0                   # Trace everything\n"
	"  ./process -m 1                   # Trace all processes, selective read/write\n"
	"  ./process -c \"claude,python\"    # Trace only claude/python processes\n"
	"  ./process -c \"ssh\" -d 1000     # Trace ssh processes lasting > 1 second\n"
	"  ./process -p 1234                # Trace only PID 1234\n"
	"  ./process --session 1234         # Trace processes in session 1234\n";

#define SESSION_KEY 1001

enum {
	OPT_TRACE_FS = 256,
	OPT_TRACE_NET,
	OPT_TRACE_SIGNALS,
	OPT_TRACE_MEM,
	OPT_TRACE_COW,
	OPT_TRACE_ALL,
	OPT_CGROUP_FILTER,
	OPT_CGROUP_FILTER_CHILDREN,
	OPT_SEED_PID,
};

static const struct argp_option opts[] = {
	{ "verbose", 'v', NULL, 0, "Verbose debug output" },
	{ "duration", 'd', "DURATION-MS", 0, "Minimum process duration (ms) to report" },
	{ "commands", 'c', "COMMAND-LIST", 0, "Comma-separated list of commands to trace (e.g., \"claude,python\")" },
	{ "pid", 'p', "PID", 0, "Trace this PID only" },
	{ "session", SESSION_KEY, "SID", 0, "Trace this process session and tracked PID descendants" },
	{ "mode", 'm', "FILTER-MODE", 0, "Filter mode: 0=all, 1=proc, 2=filter (default=1)" },
	{ "all", 'a', NULL, 0, "Deprecated: use -m 0 instead" },
	{ "trace-fs", OPT_TRACE_FS, NULL, 0, "Trace filesystem mutations (delete, rename, mkdir, write, truncate, chdir)" },
	{ "trace-net", OPT_TRACE_NET, NULL, 0, "Trace network operations (bind, listen, connect)" },
	{ "trace-signals", OPT_TRACE_SIGNALS, NULL, 0, "Trace process coordination (setpgid, setsid, kill, fork)" },
	{ "trace-mem", OPT_TRACE_MEM, NULL, 0, "Trace shared memory mappings (mmap MAP_SHARED)" },
	{ "trace-cow", OPT_TRACE_COW, NULL, 0, "Trace CoW page faults (kprobe/do_wp_page, high overhead)" },
	{ "trace-all", OPT_TRACE_ALL, NULL, 0, "Enable all tracing except --trace-cow" },
	{ "cgroup-filter", OPT_CGROUP_FILTER, "PATH", 0, "Hard filter by cgroup v2 path" },
	{ "cgroup-filter-children", OPT_CGROUP_FILTER_CHILDREN, NULL, 0, "Include descendants of --cgroup-filter path" },
	{ "seed-pid", OPT_SEED_PID, "PID[:PPID]", 0, "Seed an existing tracked PID supplied by the collector" },
	{},
};

static bool parse_seed_pid_arg(const char *arg, struct seed_pid *seed)
{
	char *end = NULL;
	char *ppid_start = NULL;
	long pid;
	long ppid = 0;

	errno = 0;
	pid = strtol(arg, &end, 10);
	if (errno || pid <= 0)
		return false;

	if (*end == ':') {
		ppid_start = end + 1;
		errno = 0;
		ppid = strtol(ppid_start, &end, 10);
		if (errno || end == ppid_start || ppid < 0)
			return false;
	}
	if (*end != '\0')
		return false;

	seed->pid = (pid_t)pid;
	seed->ppid = (pid_t)ppid;
	return true;
}

static error_t parse_arg(int key, char *arg, struct argp_state *state)
{
	char *token;
	char *saveptr;
	
	switch (key) {
	case 'v':
		env.verbose = true;
		break;
	case 'd':
		errno = 0;
		env.min_duration_ms = strtol(arg, NULL, 10);
		if (errno || env.min_duration_ms <= 0) {
			fprintf(stderr, "Invalid duration: %s\n", arg);
			argp_usage(state);
		}
		break;
	case 'p':
		errno = 0;
		env.pid = (pid_t)strtol(arg, NULL, 10);
		if (errno || env.pid <= 0) {
			fprintf(stderr, "Invalid PID: %s\n", arg);
			argp_usage(state);
		}
		env.filter_mode = FILTER_MODE_FILTER;
		break;
	case SESSION_KEY:
		errno = 0;
		env.session_id = (pid_t)strtol(arg, NULL, 10);
		if (errno || env.session_id <= 0) {
			fprintf(stderr, "Invalid session id: %s\n", arg);
			argp_usage(state);
		}
		env.filter_mode = FILTER_MODE_FILTER;
		break;
	case 'a':
		env.filter_mode = FILTER_MODE_ALL;
		break;
	case 'm':
		errno = 0;
		int mode = strtol(arg, NULL, 10);
		if (errno || mode < 0 || mode > 2) {
			fprintf(stderr, "Invalid filter mode: %s (must be 0, 1, or 2)\n", arg);
			argp_usage(state);
		}
		env.filter_mode = (enum filter_mode)mode;
		break;
	case 'c':
		env.filter_mode = FILTER_MODE_FILTER;
		/* Parse comma-separated command list */
		char *arg_copy = strdup(arg);
		if (!arg_copy) {
			fprintf(stderr, "Memory allocation failed\n");
			return ARGP_ERR_UNKNOWN;
		}
		
		token = strtok_r(arg_copy, ",", &saveptr);
		while (token && env.command_count < MAX_COMMAND_LIST) {
			/* Remove leading/trailing whitespace */
			while (*token == ' ' || *token == '\t') token++;
			char *end = token + strlen(token) - 1;
			while (end > token && (*end == ' ' || *end == '\t')) end--;
			*(end + 1) = '\0';
			
			if (strlen(token) > 0) {
				env.command_list[env.command_count] = strdup(token);
				if (!env.command_list[env.command_count]) {
					fprintf(stderr, "Memory allocation failed\n");
					free(arg_copy);
					return ARGP_ERR_UNKNOWN;
				}
				env.command_count++;
			}
			token = strtok_r(NULL, ",", &saveptr);
		}
		free(arg_copy);
		break;
	case OPT_TRACE_FS:
		env.trace_fs = true;
		break;
	case OPT_TRACE_NET:
		env.trace_net = true;
		break;
	case OPT_TRACE_SIGNALS:
		env.trace_signals = true;
		break;
	case OPT_TRACE_MEM:
		env.trace_mem = true;
		break;
	case OPT_TRACE_COW:
		env.trace_cow = true;
		break;
	case OPT_TRACE_ALL:
		env.trace_fs = true;
		env.trace_net = true;
		env.trace_signals = true;
		env.trace_mem = true;
		break;
	case OPT_CGROUP_FILTER:
		strncpy(env.cgroup_filter_path, arg, sizeof(env.cgroup_filter_path) - 1);
		env.cgroup_filter_path[sizeof(env.cgroup_filter_path) - 1] = '\0';
		env.cgroup_filter_enabled = true;
		break;
	case OPT_CGROUP_FILTER_CHILDREN:
		env.cgroup_filter_children = true;
		break;
	case OPT_SEED_PID:
		if (env.seed_count >= MAX_SEED_PIDS) {
			fprintf(stderr, "Too many --seed-pid entries (max %d)\n", MAX_SEED_PIDS);
			argp_usage(state);
		}
		if (!parse_seed_pid_arg(arg, &env.seed_pids[env.seed_count])) {
			fprintf(stderr, "Invalid seed pid: %s\n", arg);
			argp_usage(state);
		}
		env.seed_count++;
		break;
	case ARGP_KEY_ARG:
		argp_usage(state);
		break;
	default:
		return ARGP_ERR_UNKNOWN;
	}
	return 0;
}

static const struct argp argp = {
	.options = opts,
	.parser = parse_arg,
	.doc = argp_program_doc,
};

static int libbpf_print_fn(enum libbpf_print_level level, const char *format, va_list args)
{
	if (level == LIBBPF_DEBUG && !env.verbose)
		return 0;
	return vfprintf(stderr, format, args);
}

static volatile bool exiting = false;

static bool process_in_target_session(pid_t pid)
{
	if (env.session_id <= 0)
		return false;
	return getsid(pid) == env.session_id;
}

static bool should_track_event_process(struct pid_tracker *tracker,
				       const char *comm,
				       pid_t pid,
				       pid_t ppid)
{
	if (process_in_target_session(pid))
		return true;
	if (env.session_id > 0)
		return should_track_pid_lineage(tracker, pid, ppid);
	return should_track_process(tracker, comm, pid, ppid);
}

static void add_tracked_pid_to_bpf(pid_t pid)
{
	if (g_tracked_pids_fd < 0 || pid <= 0)
		return;
	uint32_t bpf_pid = (uint32_t)pid;
	uint8_t present = 1;
	bpf_map_update_elem(g_tracked_pids_fd, &bpf_pid, &present, BPF_ANY);
}

static void remove_tracked_pid_from_bpf(pid_t pid)
{
	if (g_tracked_pids_fd < 0 || pid <= 0)
		return;
	uint32_t bpf_pid = (uint32_t)pid;
	bpf_map_delete_elem(g_tracked_pids_fd, &bpf_pid);
}

static void json_escape_field(const char *src, char *dst, size_t dst_size)
{
	json_escape(src ? src : "", dst, dst_size);
}

#define SET_AUTOLOAD(name, enabled) bpf_program__set_autoload(skel->progs.name, enabled)

static void configure_optional_programs(struct process_bpf *skel)
{
	SET_AUTOLOAD(trace_unlinkat, env.trace_fs);
	SET_AUTOLOAD(trace_unlink, env.trace_fs);
	SET_AUTOLOAD(trace_renameat2, env.trace_fs);
	SET_AUTOLOAD(trace_renameat, env.trace_fs);
	SET_AUTOLOAD(trace_rename, env.trace_fs);
	SET_AUTOLOAD(trace_mkdirat, env.trace_fs);
	SET_AUTOLOAD(trace_mkdir, env.trace_fs);
	SET_AUTOLOAD(trace_ftruncate, env.trace_fs);
	SET_AUTOLOAD(trace_chdir, env.trace_fs);
	SET_AUTOLOAD(trace_write_enter, env.trace_fs);
	SET_AUTOLOAD(trace_write_exit, env.trace_fs);
	SET_AUTOLOAD(trace_pwrite64_enter, env.trace_fs);
	SET_AUTOLOAD(trace_pwrite64_exit, env.trace_fs);
	SET_AUTOLOAD(trace_writev_enter, env.trace_fs);
	SET_AUTOLOAD(trace_writev_exit, env.trace_fs);

	SET_AUTOLOAD(trace_bind, env.trace_net);
	SET_AUTOLOAD(trace_listen, env.trace_net);
	SET_AUTOLOAD(trace_connect, env.trace_net);

	SET_AUTOLOAD(trace_setpgid, env.trace_signals);
	SET_AUTOLOAD(trace_setsid, env.trace_signals);
	SET_AUTOLOAD(trace_kill, env.trace_signals);
	SET_AUTOLOAD(trace_fork, env.trace_signals);

	SET_AUTOLOAD(trace_mmap, env.trace_mem);
	SET_AUTOLOAD(trace_cow_fault, env.trace_cow);
}

#undef SET_AUTOLOAD

// Rate limiting check function
static bool should_rate_limit_file(const struct event *e, uint64_t timestamp_ns, bool *add_warning) {
    uint64_t current_second = timestamp_ns / 1000000000ULL;  // Convert to seconds
    *add_warning = false;
    
    // Find/create entry for this PID
    struct per_second_limit *limit = NULL;
    for (int i = 0; i < pid_limit_count; i++) {
        if (pid_limits[i].pid == e->pid) {
            limit = &pid_limits[i];
            break;
        }
    }
    
    if (!limit && pid_limit_count < MAX_PID_LIMITS) {
        limit = &pid_limits[pid_limit_count++];
        limit->pid = e->pid;
        limit->current_second = current_second;
        limit->distinct_file_count = 0;
        limit->should_warn_next = false;
    }
    
    if (!limit) return false;
    
    // New second - reset and check if we need to warn
    if (limit->current_second != current_second) {
        if (limit->should_warn_next) {
            *add_warning = true;
            limit->should_warn_next = false;
        }
        limit->current_second = current_second;
        limit->distinct_file_count = 0;
    }
    
    limit->distinct_file_count++;
    
    // Check if over limit
    if (limit->distinct_file_count > MAX_DISTINCT_FILES_PER_SEC) {
        limit->should_warn_next = true;  // Warn on next event
        return true;  // Drop this event
    }
    
    return false;
}

// Shared function to print FILE_OPEN events
static void print_file_open_event(const struct event *e, uint64_t timestamp_ns, uint32_t count, const char *extra_fields)
{
	char comm_esc[TASK_COMM_LEN * 2 + 1];
	char filepath_esc[MAX_FILENAME_LEN * 2 + 1];

	json_escape_field(e->comm, comm_esc, sizeof(comm_esc));
	json_escape_field(e->file_op.filepath, filepath_esc, sizeof(filepath_esc));

	printf("{");
	printf("\"timestamp\":%llu,", (unsigned long long)timestamp_ns);
	printf("\"event\":\"FILE_OPEN\",");
	printf("\"comm\":\"%s\",", comm_esc);
	printf("\"pid\":%d,", e->pid);
	printf("\"count\":%u,", count);
	printf("\"filepath\":\"%s\",", filepath_esc);
	printf("\"flags\":%d", e->file_op.flags);
	
	if (extra_fields && strlen(extra_fields) > 0) {
		printf(",%s", extra_fields);
	}

	print_container_fields(e->pid);

	printf("}\n");
	fflush(stdout);
}


// Hash function for FILE_OPEN events
static uint64_t hash_file_open(const struct event *e)
{
	uint64_t hash = 5381;
	hash = ((hash << 5) + hash) + e->pid;
	
	// Hash the filepath for FILE_OPEN events
	const char *str = e->file_op.filepath;
	while (*str) {
		hash = ((hash << 5) + hash) + *str++;
	}
	
	return hash;
}

// Get count for FILE_OPEN operations (handles deduplication internally)
static uint32_t get_file_open_count(const struct event *e, uint64_t timestamp_ns, char *warning_msg, size_t warning_msg_size)
{
	if (e->type != EVENT_TYPE_FILE_OPERATION || !e->file_op.is_open) {
		return 1;  // Return count of 1 for non-FILE_OPEN operations
	}
	
	// Initialize warning message
	warning_msg[0] = '\0';
	
	// Rate limiting check
	bool add_warning = false;
	if (should_rate_limit_file(e, timestamp_ns, &add_warning)) {
		return 0;  // Drop this event
	}
	
	// Build warning message if needed
	if (add_warning) {
		snprintf(warning_msg, warning_msg_size, "\"rate_limit_warning\":\"Previous second exceeded %d file limit\"", MAX_DISTINCT_FILES_PER_SEC);
	}
	
	uint64_t hash = hash_file_open(e);
	
	// Clean up expired entries first
	for (int i = 0; i < hash_count; i++) {
		if (timestamp_ns - file_hashes[i].timestamp_ns > FILE_DEDUP_WINDOW_NS) {
			// Print aggregated result if count > 1
			if (file_hashes[i].count > 1) {
				if (env.verbose) {
					fprintf(stderr, "DEBUG: Aggregation window expired for FILE_OPEN, count=%u\n", 
						file_hashes[i].count);
				}
				// Create fake event structure for aggregated output
				struct event fake_event = {
					.type = EVENT_TYPE_FILE_OPERATION,
					.pid = file_hashes[i].pid,
					.ppid = 0,
					.exit_code = 0,
					.duration_ns = 0,
					.exit_event = false,
					.file_op = {
						.fd = -1,
						.flags = file_hashes[i].flags,
						.is_open = true
					}
				};
				strncpy(fake_event.comm, file_hashes[i].comm, TASK_COMM_LEN - 1);
				fake_event.comm[TASK_COMM_LEN - 1] = '\0';
				strncpy(fake_event.file_op.filepath, file_hashes[i].filepath, MAX_FILENAME_LEN - 1);
				fake_event.file_op.filepath[MAX_FILENAME_LEN - 1] = '\0';
				print_file_open_event(&fake_event, timestamp_ns, file_hashes[i].count, "\"window_expired\":true");
			}
			
			// Remove expired entry
			file_hashes[i] = file_hashes[hash_count - 1];
			hash_count--;
			i--;
		}
	}
	
	// Check if this hash already exists
	for (int i = 0; i < hash_count; i++) {
		if (file_hashes[i].hash == hash) {
			file_hashes[i].count++;
			file_hashes[i].timestamp_ns = timestamp_ns;
			if (env.verbose) {
				fprintf(stderr, "DEBUG: Aggregating FILE_OPEN for PID %d, count now %u\n", 
					e->pid, file_hashes[i].count);
			}
			return 0;  // Return 0 to indicate this should be skipped (duplicate)
		}
	}
	
	// Add new hash entry if we have space
	if (hash_count < MAX_FILE_HASHES) {
		file_hashes[hash_count].hash = hash;
		file_hashes[hash_count].timestamp_ns = timestamp_ns;
		file_hashes[hash_count].count = 1;
		file_hashes[hash_count].pid = e->pid;
		strncpy(file_hashes[hash_count].comm, e->comm, TASK_COMM_LEN - 1);
		file_hashes[hash_count].comm[TASK_COMM_LEN - 1] = '\0';
		strncpy(file_hashes[hash_count].filepath, e->file_op.filepath, MAX_FILENAME_LEN - 1);
		file_hashes[hash_count].filepath[MAX_FILENAME_LEN - 1] = '\0';
		file_hashes[hash_count].flags = e->file_op.flags;
		hash_count++;
		if (env.verbose) {
			fprintf(stderr, "DEBUG: Created new aggregation entry for FILE_OPEN, PID %d (total entries: %d)\n", 
				e->pid, hash_count);
		}
	} else if (env.verbose) {
		fprintf(stderr, "DEBUG: Max aggregation entries reached (%d), cannot track more\n", MAX_FILE_HASHES);
		// just print the event
		print_file_open_event(e, timestamp_ns, 1, NULL);
	}
	
	return 1;  // Return count of 1 for first occurrence
}

// Flush all pending FILE_OPEN aggregations for a specific PID
static void flush_pid_file_opens(pid_t pid, uint64_t timestamp_ns)
{
	int flushed_count = 0;
	for (int i = 0; i < hash_count; i++) {
		if (file_hashes[i].pid == pid && file_hashes[i].count > 1) {
			if (env.verbose) {
				fprintf(stderr, "DEBUG: Flushing FILE_OPEN aggregation on process exit, PID %d, count=%u\n", 
					pid, file_hashes[i].count);
			}
			// Create fake event structure for aggregated output
			struct event fake_event = {
				.type = EVENT_TYPE_FILE_OPERATION,
				.pid = file_hashes[i].pid,
				.ppid = 0,
				.exit_code = 0,
				.duration_ns = 0,
				.exit_event = false,
				.file_op = {
					.fd = -1,
					.flags = file_hashes[i].flags,
					.is_open = true
				}
			};
			strncpy(fake_event.comm, file_hashes[i].comm, TASK_COMM_LEN - 1);
			fake_event.comm[TASK_COMM_LEN - 1] = '\0';
			strncpy(fake_event.file_op.filepath, file_hashes[i].filepath, MAX_FILENAME_LEN - 1);
			fake_event.file_op.filepath[MAX_FILENAME_LEN - 1] = '\0';
			print_file_open_event(&fake_event, timestamp_ns, file_hashes[i].count, "\"reason\":\"process_exit\"");
			flushed_count++;
		}
	}
	
	// Remove all entries for this PID
	int removed_count = 0;
	for (int i = 0; i < hash_count; i++) {
		if (file_hashes[i].pid == pid) {
			// Remove this entry by moving last entry to this position
			file_hashes[i] = file_hashes[hash_count - 1];
			hash_count--;
			removed_count++;
			i--; // Recheck this position since we moved an entry here
		}
	}
	
	if (env.verbose && removed_count > 0) {
		fprintf(stderr, "DEBUG: Cleared %d FILE_OPEN aggregation entries for PID %d (flushed %d)\n", 
			removed_count, pid, flushed_count);
	}
}

static void print_exec_event(const struct event *e)
{
	char comm_esc[TASK_COMM_LEN * 2 + 1];
	char filename_esc[MAX_FILENAME_LEN * 2 + 1];
	char command_esc[MAX_COMMAND_LEN * 2 + 1];
	const char *full_command = postprocess_full_command(e->full_command, MAX_COMMAND_LEN, e->exit_code);

	json_escape_field(e->comm, comm_esc, sizeof(comm_esc));
	json_escape_field(e->filename, filename_esc, sizeof(filename_esc));
	json_escape_field(full_command, command_esc, sizeof(command_esc));

	printf("{");
	printf("\"timestamp\":%llu,", e->timestamp_ns);
	printf("\"event\":\"EXEC\",");
	printf("\"comm\":\"%s\",", comm_esc);
	printf("\"pid\":%d,", e->pid);
	printf("\"ppid\":%d", e->ppid);
	printf(",\"filename\":\"%s\"", filename_esc);
	printf(",\"full_command\":\"%s\"", command_esc);

	print_container_fields(e->pid);
	printf("}\n");
	fflush(stdout);
}

static void print_exit_event(const struct event *e)
{
	char comm_esc[TASK_COMM_LEN * 2 + 1];

	json_escape_field(e->comm, comm_esc, sizeof(comm_esc));

	printf("{");
	printf("\"timestamp\":%llu,", e->timestamp_ns);
	printf("\"event\":\"EXIT\",");
	printf("\"comm\":\"%s\",", comm_esc);
	printf("\"pid\":%d,", e->pid);
	printf("\"ppid\":%d", e->ppid);
	printf(",\"exit_code\":%u", e->exit_code);
	if (e->duration_ns)
		printf(",\"duration_ms\":%llu", e->duration_ns / 1000000);

	if (g_exit_mem_fd >= 0) {
		uint32_t mem_pid = (uint32_t)e->pid;
		struct exit_mem_info emem = {};
		if (bpf_map_lookup_elem(g_exit_mem_fd, &mem_pid, &emem) == 0) {
			printf(",\"vm_hwm_kb\":%llu",
			       (unsigned long long)(emem.hiwater_rss * page_size_kb));
			bpf_map_delete_elem(g_exit_mem_fd, &mem_pid);
		}
	}

	print_container_fields(e->pid);
	printf("}\n");
	fflush(stdout);
}

static void print_bash_readline_event(const struct event *e)
{
	char comm_esc[TASK_COMM_LEN * 2 + 1];
	char command_esc[MAX_COMMAND_LEN * 2 + 1];

	json_escape_field(e->comm, comm_esc, sizeof(comm_esc));
	json_escape_field(e->command, command_esc, sizeof(command_esc));

	printf("{");
	printf("\"timestamp\":%llu,", e->timestamp_ns);
	printf("\"event\":\"BASH_READLINE\",");
	printf("\"comm\":\"%s\",", comm_esc);
	printf("\"pid\":%d,", e->pid);
	printf("\"command\":\"%s\"", command_esc);
	print_container_fields(e->pid);
	printf("}\n");
	fflush(stdout);
}

static void sig_handler(int sig)
{
	exiting = true;
}

static int seed_initial_pids(struct pid_tracker *tracker)
{
	int tracked_count = 0;

	for (int i = 0; i < env.seed_count; i++) {
		pid_t pid = env.seed_pids[i].pid;
		pid_t ppid = env.seed_pids[i].ppid;
		bool already_tracked = pid_tracker_is_tracked(tracker, pid);

		if (pid_tracker_add(tracker, pid, ppid)) {
			if (!already_tracked) {
				add_tracked_pid_to_bpf(pid);
				tracked_count++;
			}
		} else if (env.verbose) {
			fprintf(stderr, "Warning: Failed to add seeded PID %d to tracker (table full)\n", pid);
		}
	}

	return tracked_count;
}

static int handle_event(void *ctx, void *data, size_t data_sz)
{
	const struct event *e = data;
	struct pid_tracker *tracker = (struct pid_tracker *)ctx;

	switch (e->type) {
		case EVENT_TYPE_PROCESS:
			if (e->exit_event) {
				// EXIT event: check if tracked before reporting
				bool is_tracked = pid_tracker_is_tracked(tracker, e->pid);

				// Remove from tracker regardless
				pid_tracker_remove(tracker, e->pid);
				remove_tracked_pid_from_bpf(e->pid);

				// Only report if tracked (or if in ALL/PROC mode)
				if (!is_tracked && tracker->filter_mode == FILTER_MODE_FILTER) {
					break;
				}

				// Check if this PID has pending rate limit warning
				bool add_warning = false;
				for (int i = 0; i < pid_limit_count; i++) {
					if (pid_limits[i].pid == e->pid && pid_limits[i].should_warn_next) {
						add_warning = true;
						// Remove this entry
						pid_limits[i] = pid_limits[--pid_limit_count];
						break;
					}
				}

				print_exit_event(e);
				if (add_warning) {
					printf("{\"timestamp\":%llu,\"event\":\"WARNING\","
					       "\"comm\":\"\",\"pid\":%d,"
					       "\"type\":\"FILE_RATE_LIMIT\","
					       "\"message\":\"Process had %d+ file ops per second\"}\n",
					       e->timestamp_ns, e->pid, MAX_DISTINCT_FILES_PER_SEC);
					fflush(stdout);
				}

			// Flush all pending FILE_OPEN aggregations for this PID
			flush_pid_file_opens(e->pid, e->timestamp_ns);
			if (g_agg_map_fd >= 0)
				flush_pid_from_agg_map(g_agg_map_fd, e->pid);
		} else {
			bool should_track = should_track_event_process(tracker, e->comm, e->pid, e->ppid);

			if (should_track) {
				pid_tracker_add(tracker, e->pid, e->ppid);
				add_tracked_pid_to_bpf(e->pid);

				print_exec_event(e);
			} else if (tracker->filter_mode == FILTER_MODE_FILTER) {
				break;
			} else {
				if (tracker->filter_mode == FILTER_MODE_PROC) {
					pid_tracker_add(tracker, e->pid, e->ppid);
					add_tracked_pid_to_bpf(e->pid);
				}
				print_exec_event(e);
			}
		}
			break;

		case EVENT_TYPE_BASH_READLINE:
			// Check if should report bash readline for this PID
			if (!should_report_bash_readline(tracker, e->pid)) {
				break;
			}

			print_bash_readline_event(e);
			break;

		case EVENT_TYPE_FILE_OPERATION:
			// Only handle FILE_OPEN events, skip FILE_CLOSE
			if (!e->file_op.is_open) {
				break;
			}

			// Check if should report file ops for this PID
			if (!should_report_file_ops(tracker, e->pid)) {
				break;
			}

			// Get count for this FILE_OPEN operation
			char warning_msg[128];
			uint32_t count = get_file_open_count(e, e->timestamp_ns, warning_msg, sizeof(warning_msg));

			// Skip if this is a duplicate (count == 0)
			if (count == 0) {
				break;
			}

			// Report the FILE_OPEN event with count
			print_file_open_event(e, e->timestamp_ns, count, strlen(warning_msg) > 0 ? warning_msg : NULL);
			break;

		default:
			// For unknown events, always report immediately
			printf("{");
			printf("\"timestamp\":%llu,", e->timestamp_ns);
			printf("\"event\":\"UNKNOWN\",");
			printf("\"event_type\":%d", e->type);
			printf("}\n");
			fflush(stdout);
			break;
	}

	return 0;
}

int main(int argc, char **argv)
{
	struct ring_buffer *rb = NULL;
	struct process_bpf *skel;
	int err;

	/* Parse command line arguments */
	err = argp_parse(&argp, argc, argv, 0, NULL, NULL);
	if (err)
		return err;
	if (env.cgroup_filter_children && !env.cgroup_filter_enabled) {
		fprintf(stderr, "--cgroup-filter-children requires --cgroup-filter <path>\n");
		return 1;
	}

	/* filter_mode is set via -m flag or -a flag, defaults to FILTER_MODE_PROC */
	page_size_kb = sysconf(_SC_PAGESIZE) / 1024;
	if (page_size_kb <= 0)
		page_size_kb = 4;

	/* Initialize userspace PID tracker */
	pid_tracker_init(&pid_tracker, env.command_list, env.command_count, env.filter_mode, env.pid);

	/* Set up libbpf errors and debug info callback */
	libbpf_set_print(libbpf_print_fn);

	/* Cleaner handling of Ctrl-C */
	signal(SIGINT, sig_handler);
	signal(SIGTERM, sig_handler);

	/* Load and verify BPF application */
	skel = process_bpf__open();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	configure_optional_programs(skel);

	/* Parameterize BPF code with minimum duration */
	skel->rodata->min_duration_ns = env.min_duration_ms * 1000000ULL;
	skel->rodata->trace_fs_mutations = env.trace_fs;
	skel->rodata->trace_network = env.trace_net;
	skel->rodata->trace_signals = env.trace_signals;
	skel->rodata->trace_memory = env.trace_mem;
	skel->rodata->trace_cow = env.trace_cow;

	bool need_pid_filter = env.filter_mode == FILTER_MODE_FILTER;
	skel->rodata->filter_pids = need_pid_filter;

	bool need_cgroup_filter = false;
	uint64_t cgroup_filter_id = 0;
	if (env.cgroup_filter_enabled) {
		if (!resolve_cgroup_id_from_path(env.cgroup_filter_path, &cgroup_filter_id)) {
			fprintf(stderr, "Failed to resolve cgroup filter path: %s\n",
			        env.cgroup_filter_path);
			err = -EINVAL;
			goto cleanup;
		}
		need_cgroup_filter = true;
	}
	skel->rodata->filter_cgroup = need_cgroup_filter;
	skel->rodata->filter_cgroup_children = env.cgroup_filter_children;
	skel->rodata->target_cgroup_id = cgroup_filter_id;

	/* Load & verify BPF programs */
	err = process_bpf__load(skel);
	if (err) {
		fprintf(stderr, "Failed to load and verify BPF skeleton\n");
		goto cleanup;
	}

	g_agg_map_fd = bpf_map__fd(skel->maps.event_agg_map);
	g_tracked_pids_fd = bpf_map__fd(skel->maps.tracked_pids);
	g_tracked_cgroups_fd = bpf_map__fd(skel->maps.tracked_cgroups);
	g_overflow_fd = bpf_map__fd(skel->maps.agg_overflow_count);
	g_exit_mem_fd = bpf_map__fd(skel->maps.exit_mem);

	if (need_cgroup_filter && env.cgroup_filter_children) {
		int cgroups = populate_cgroup_filter_map(env.cgroup_filter_path, true, g_tracked_cgroups_fd);
		if (cgroups < 0) {
			fprintf(stderr, "Failed to populate descendant cgroups from %s: %s\n",
			        env.cgroup_filter_path, strerror(-cgroups));
			err = cgroups;
			goto cleanup;
		}
		if (env.verbose)
			fprintf(stderr, "Loaded cgroup subtree filter entries: %d\n", cgroups);
	}

	int tracked_count = seed_initial_pids(&pid_tracker);
	
	/* Output configuration as JSON */
	if (env.verbose) {
		fprintf(stderr, "Loaded process: trace_fs=%d trace_net=%d trace_signals=%d "
			"trace_mem=%d trace_cow=%d filter_pids=%d filter_cgroup=%d "
			"filter_cgroup_children=%d cgroup_id=%llu seed_pids=%d seeded_tracked=%d\n",
			env.trace_fs, env.trace_net, env.trace_signals,
			env.trace_mem, env.trace_cow, need_pid_filter, need_cgroup_filter,
			env.cgroup_filter_children, (unsigned long long)cgroup_filter_id,
			env.seed_count, tracked_count);
	}

	/* Attach tracepoints */
	err = process_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF skeleton\n");
		goto cleanup;
	}

	/* Set up ring buffer polling with pid_tracker as context */
	rb = ring_buffer__new(bpf_map__fd(skel->maps.rb), handle_event, &pid_tracker, NULL);
	if (!rb) {
		err = -1;
		fprintf(stderr, "Failed to create ring buffer\n");
		goto cleanup;
	}

	uint64_t last_flush_time = 0;
	uint64_t last_cgroup_refresh_time = 0;
	print_clock_sync_anchor("start");

	/* Process events */
	while (!exiting) {
		int poll_ms = POLL_TIMEOUT_MS;

		err = ring_buffer__poll(rb, poll_ms);
		/* Ctrl-C will cause -EINTR */
		if (err == -EINTR) {
			err = 0;
			break;
		}
		if (err < 0) {
			fprintf(stderr, "Error polling perf buffer: %d\n", err);
			break;
		}

		uint64_t now = (uint64_t)time(NULL);
		if (need_cgroup_filter && env.cgroup_filter_children &&
		    now - last_cgroup_refresh_time >= 2) {
			int rc = populate_cgroup_filter_map(env.cgroup_filter_path, true, g_tracked_cgroups_fd);
			if (rc < 0 && env.verbose) {
				fprintf(stderr, "Warning: failed to refresh cgroup subtree map: %s\n",
				        strerror(-rc));
			}
			last_cgroup_refresh_time = now;
		}
		if (now - last_flush_time >= FLUSH_INTERVAL_S) {
			if (g_agg_map_fd >= 0)
				flush_agg_map(g_agg_map_fd);
			if (g_overflow_fd >= 0)
				check_overflow(g_overflow_fd);
			last_flush_time = now;
		}

	}

	if (g_agg_map_fd >= 0)
		flush_agg_map(g_agg_map_fd);
	print_clock_sync_anchor("end");

cleanup:
	/* Clean up */
	ring_buffer__free(rb);
	process_bpf__destroy(skel);
	
	/* Free allocated command strings */
	for (int i = 0; i < env.command_count; i++) {
		free(env.command_list[i]);
	}
	
	/* Clean up FILE_OPEN deduplication tracking */
	hash_count = 0;
	
	/* Clean up rate limiting tracking */
	pid_limit_count = 0;

	return err < 0 ? -err : 0;
}
