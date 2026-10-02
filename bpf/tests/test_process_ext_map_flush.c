/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Unit tests for map_flush.h pure functions:
 *   - event_type_name()
 *   - json_escape()
 *   - print_summary_json()
 *
 * Compiled with -Itests/ so that <bpf/bpf.h> and <bpf/libbpf.h> resolve
 * to minimal stubs in tests/bpf/ rather than the real libbpf headers.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>

#ifdef __linux__
#include <linux/types.h>
#else
typedef uint32_t __u32;
typedef uint64_t __u64;
#endif

/* ---- headers under test ----------------------------------------------- */
#include "process.h"
#include "process_ext/types.h"
#include "process_ext/map_flush.h"

/* ---- test harness ------------------------------------------------------ */
#define RESET  "\033[0m"
#define RED    "\033[31m"
#define GREEN  "\033[32m"
#define YELLOW "\033[33m"
#define BLUE   "\033[34m"

static int tests_passed = 0;
static int tests_failed = 0;

static void test_assert(bool condition, const char *test_name)
{
	if (condition) {
		printf("[" GREEN "PASS" RESET "] %s\n", test_name);
		tests_passed++;
	} else {
		printf("[" RED "FAIL" RESET "] %s\n", test_name);
		tests_failed++;
	}
}

/* ======================================================================== */
/* Tests for event_type_name()                                               */
/* ======================================================================== */

static void test_event_type_name_known_types(void)
{
	printf("\n" BLUE "Testing event_type_name() — known types:" RESET "\n");

	test_assert(strcmp(event_type_name(EVENT_TYPE_FILE_DELETE),    "FILE_DELETE")    == 0,
	            "FILE_DELETE(10) -> \"FILE_DELETE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_FILE_RENAME),    "FILE_RENAME")    == 0,
	            "FILE_RENAME(11) -> \"FILE_RENAME\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_DIR_CREATE),     "DIR_CREATE")     == 0,
	            "DIR_CREATE(12) -> \"DIR_CREATE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_FILE_TRUNCATE),  "FILE_TRUNCATE")  == 0,
	            "FILE_TRUNCATE(13) -> \"FILE_TRUNCATE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_CHDIR),          "CHDIR")          == 0,
	            "CHDIR(14) -> \"CHDIR\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_WRITE),          "WRITE")          == 0,
	            "WRITE(15) -> \"WRITE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_NET_BIND),       "NET_BIND")       == 0,
	            "NET_BIND(20) -> \"NET_BIND\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_NET_LISTEN),     "NET_LISTEN")     == 0,
	            "NET_LISTEN(21) -> \"NET_LISTEN\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_NET_CONNECT),    "NET_CONNECT")    == 0,
	            "NET_CONNECT(22) -> \"NET_CONNECT\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_NET_ACCEPT),     "NET_ACCEPT")     == 0,
	            "NET_ACCEPT(23) -> \"NET_ACCEPT\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_PGRP_CHANGE),    "PGRP_CHANGE")    == 0,
	            "PGRP_CHANGE(30) -> \"PGRP_CHANGE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_SESSION_CREATE), "SESSION_CREATE") == 0,
	            "SESSION_CREATE(31) -> \"SESSION_CREATE\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_SIGNAL_SEND),    "SIGNAL_SEND")    == 0,
	            "SIGNAL_SEND(32) -> \"SIGNAL_SEND\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_PROC_FORK),      "PROC_FORK")      == 0,
	            "PROC_FORK(33) -> \"PROC_FORK\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_MMAP_SHARED),    "MMAP_SHARED")    == 0,
	            "MMAP_SHARED(40) -> \"MMAP_SHARED\"");
	test_assert(strcmp(event_type_name(EVENT_TYPE_COW_FAULT),      "COW_FAULT")      == 0,
	            "COW_FAULT(41) -> \"COW_FAULT\"");
}

static void test_event_type_name_unknown(void)
{
	printf("\n" BLUE "Testing event_type_name() — unknown type:" RESET "\n");

	test_assert(strcmp(event_type_name(0),   "UNKNOWN") == 0,
	            "type 0 -> \"UNKNOWN\"");
	test_assert(strcmp(event_type_name(99),  "UNKNOWN") == 0,
	            "type 99 -> \"UNKNOWN\"");
	test_assert(strcmp(event_type_name(255), "UNKNOWN") == 0,
	            "type 255 -> \"UNKNOWN\"");
}

/* ======================================================================== */
/* Tests for json_escape()                                                   */
/* ======================================================================== */

static void test_json_escape_plain_string(void)
{
	printf("\n" BLUE "Testing json_escape() — plain string:" RESET "\n");

	char dst[128];
	json_escape("hello world", dst, sizeof(dst));
	test_assert(strcmp(dst, "hello world") == 0,
	            "plain string passes through unchanged");
}

static void test_json_escape_backslash(void)
{
	printf("\n" BLUE "Testing json_escape() — backslash:" RESET "\n");

	char dst[128];
	json_escape("a\\b", dst, sizeof(dst));
	test_assert(strcmp(dst, "a\\\\b") == 0,
	            "backslash is doubled: a\\b -> a\\\\b");
}

static void test_json_escape_double_quote(void)
{
	printf("\n" BLUE "Testing json_escape() — double quote:" RESET "\n");

	char dst[128];
	json_escape("say \"hi\"", dst, sizeof(dst));
	test_assert(strcmp(dst, "say \\\"hi\\\"") == 0,
	            "double quotes are escaped: \" -> \\\"");
}

static void test_json_escape_newline(void)
{
	printf("\n" BLUE "Testing json_escape() — newline:" RESET "\n");

	char dst[128];
	json_escape("line1\nline2", dst, sizeof(dst));
	test_assert(strcmp(dst, "line1\\nline2") == 0,
	            "newline is escaped: \\n -> \\\\n");
}

static void test_json_escape_tab(void)
{
	printf("\n" BLUE "Testing json_escape() — tab:" RESET "\n");

	char dst[128];
	json_escape("col1\tcol2", dst, sizeof(dst));
	test_assert(strcmp(dst, "col1\\tcol2") == 0,
	            "tab is escaped: \\t -> \\\\t");
}

static void test_json_escape_mixed(void)
{
	printf("\n" BLUE "Testing json_escape() — mixed special chars:" RESET "\n");

	char dst[256];
	/* Input: \  "  newline  tab  plain */
	json_escape("\\\"\n\t!", dst, sizeof(dst));
	test_assert(strcmp(dst, "\\\\\\\"\\n\\t!") == 0,
	            "mixed special characters all escaped correctly");
}

static void test_json_escape_empty_string(void)
{
	printf("\n" BLUE "Testing json_escape() — empty string:" RESET "\n");

	char dst[32] = "sentinel";
	json_escape("", dst, sizeof(dst));
	test_assert(dst[0] == '\0', "empty input produces empty output");
}

static void test_json_escape_truncation(void)
{
	printf("\n" BLUE "Testing json_escape() — truncation when dst is small:" RESET "\n");

	/* Destination has room for only 4 bytes including NUL. */
	char dst[4];
	json_escape("abcdefgh", dst, sizeof(dst));
	/* Must be NUL-terminated and at most 3 payload chars. */
	test_assert(strlen(dst) <= 3, "output is bounded by dst_size");
	test_assert(dst[sizeof(dst) - 1] == '\0' || dst[3] == '\0',
	            "output is NUL-terminated");
}

/* ======================================================================== */
/* Tests for print_summary_json()                                             */
/* ======================================================================== */

/*
 * Capture stdout by redirecting to a pipe, call print_summary_json(), then
 * read back the output.  Returns the number of bytes read (0 on error).
 */
static int capture_print_summary_json(const struct agg_key *key,
				      const struct agg_value *val,
				      char *buf, size_t buf_size)
{
	int pipefd[2];
	if (pipe(pipefd) != 0)
		return -1;

	fflush(stdout);
	int saved_stdout = dup(STDOUT_FILENO);
	if (saved_stdout < 0) {
		close(pipefd[0]);
		close(pipefd[1]);
		return -1;
	}

	if (dup2(pipefd[1], STDOUT_FILENO) < 0) {
		close(saved_stdout);
		close(pipefd[0]);
		close(pipefd[1]);
		return -1;
	}
	close(pipefd[1]);

	print_summary_json(key, val);
	fflush(stdout);

	/* Restore stdout */
	dup2(saved_stdout, STDOUT_FILENO);
	close(saved_stdout);

	/* Read captured output */
	ssize_t n = read(pipefd[0], buf, buf_size - 1);
	close(pipefd[0]);
	if (n < 0)
		return -1;
	buf[n] = '\0';
	return (int)n;
}

static void test_print_summary_json_basic_fields(void)
{
	printf("\n" BLUE "Testing print_summary_json() — basic JSON fields:" RESET "\n");

	struct agg_key key;
	struct agg_value val;

	memset(&key, 0, sizeof(key));
	memset(&val, 0, sizeof(val));

	key.pid        = 1234;
	key.event_type = EVENT_TYPE_FILE_DELETE;
	strncpy(key.detail, "/tmp/foo.txt", DETAIL_LEN - 1);

	val.last_ts      = 9876543210ULL;
	val.count        = 7;
	val.total_bytes  = 0; /* not printed when 0 */
	strncpy(val.comm, "myproc", TASK_COMM_LEN - 1);

	char buf[1024];
	int n = capture_print_summary_json(&key, &val, buf, sizeof(buf));

	test_assert(n > 0, "print_summary_json produced non-empty output");
	printf("  Output: %s", buf);

	/* Required fields */
	test_assert(strstr(buf, "\"timestamp\":9876543210") != NULL,
	            "output contains correct timestamp");
	test_assert(strstr(buf, "\"event\":\"SUMMARY\"") != NULL,
	            "output contains event:SUMMARY");
	test_assert(strstr(buf, "\"comm\":\"myproc\"") != NULL,
	            "output contains correct comm");
	test_assert(strstr(buf, "\"pid\":1234") != NULL,
	            "output contains correct pid");
	test_assert(strstr(buf, "\"type\":\"FILE_DELETE\"") != NULL,
	            "output contains correct type");
	test_assert(strstr(buf, "\"detail\":\"/tmp/foo.txt\"") != NULL,
	            "output contains correct detail");
	test_assert(strstr(buf, "\"count\":7") != NULL,
	            "output contains correct count");
}

static void test_network_summary_endpoint_fields(void)
{
	struct agg_key key = {0};
	struct agg_value val = {0};
	char buf[1024];
	key.pid = 42;
	key.process_start_ns = 123456;
	val.count = 1;
	val.last_ts = 789;
	strncpy(val.comm, "agent", TASK_COMM_LEN - 1);

	key.event_type = EVENT_TYPE_NET_LISTEN;
	strncpy(key.detail, "127.0.0.1:8080", DETAIL_LEN - 1);
	capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(strstr(buf, "\"process_start_ns\":123456") != NULL,
		    "network summary includes process instance");
	test_assert(strstr(buf, "\"local_endpoint\":\"127.0.0.1:8080\"") != NULL,
		    "listener summary has local endpoint");

	key.event_type = EVENT_TYPE_NET_ACCEPT;
	strncpy(key.detail, "127.0.0.1:54321", DETAIL_LEN - 1);
	capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(strstr(buf, "\"peer_endpoint\":\"127.0.0.1:54321\"") != NULL,
		    "accept summary has peer endpoint");
}

static void test_print_summary_json_optional_total_bytes(void)
{
	printf("\n" BLUE "Testing print_summary_json() — optional total_bytes field:" RESET "\n");

	struct agg_key key;
	struct agg_value val;

	memset(&key, 0, sizeof(key));
	memset(&val, 0, sizeof(val));

	key.pid        = 1;
	key.event_type = EVENT_TYPE_WRITE;
	val.last_ts    = 1ULL;
	val.count      = 1;
	val.total_bytes = 0; /* should be absent */
	strncpy(val.comm, "a", TASK_COMM_LEN - 1);

	char buf[1024];
	int n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty (zero total_bytes)");
	test_assert(strstr(buf, "\"total_bytes\"") == NULL,
	            "total_bytes absent when 0");

	/* Now set total_bytes > 0 */
	val.total_bytes = 4096;
	n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty (non-zero total_bytes)");
	test_assert(strstr(buf, "\"total_bytes\":4096") != NULL,
	            "total_bytes present when non-zero");
}

static void test_print_summary_json_optional_extra(void)
{
	printf("\n" BLUE "Testing print_summary_json() — optional extra field:" RESET "\n");

	struct agg_key key;
	struct agg_value val;

	memset(&key, 0, sizeof(key));
	memset(&val, 0, sizeof(val));

	key.pid        = 1;
	key.event_type = EVENT_TYPE_FILE_RENAME;
	val.last_ts    = 1ULL;
	val.count      = 1;
	strncpy(val.comm, "mv", TASK_COMM_LEN - 1);
	val.extra[0] = '\0'; /* empty — should be absent */

	char buf[1024];
	int n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty (empty extra)");
	test_assert(strstr(buf, "\"extra\"") == NULL,
	            "extra absent when empty");

	/* Set a non-empty extra */
	strncpy(val.extra, "/new/name.txt", MAX_FILENAME_LEN - 1);
	n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty (non-empty extra)");
	test_assert(strstr(buf, "\"extra\":\"/new/name.txt\"") != NULL,
	            "extra present when non-empty");
}

static void test_print_summary_json_escaped_fields(void)
{
	printf("\n" BLUE "Testing print_summary_json() — escaped special characters:" RESET "\n");

	struct agg_key key;
	struct agg_value val;

	memset(&key, 0, sizeof(key));
	memset(&val, 0, sizeof(val));

	key.pid        = 1;
	key.event_type = EVENT_TYPE_WRITE;
	/* detail with double-quote */
	strncpy(key.detail, "path/with\"quote", DETAIL_LEN - 1);
	val.last_ts    = 1ULL;
	val.count      = 1;
	/* comm with backslash */
	strncpy(val.comm, "a\\b", TASK_COMM_LEN - 1);

	char buf[1024];
	int n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty");
	printf("  Output: %s", buf);

	test_assert(strstr(buf, "\\\"quote") != NULL,
	            "double-quote in detail is escaped");
	test_assert(strstr(buf, "a\\\\b") != NULL,
	            "backslash in comm is escaped");
}

static void test_print_summary_json_newline_terminated(void)
{
	printf("\n" BLUE "Testing print_summary_json() — output ends with newline:" RESET "\n");

	struct agg_key key;
	struct agg_value val;

	memset(&key, 0, sizeof(key));
	memset(&val, 0, sizeof(val));
	key.pid        = 1;
	key.event_type = EVENT_TYPE_CHDIR;
	val.last_ts    = 1ULL;
	val.count      = 1;
	strncpy(val.comm, "sh", TASK_COMM_LEN - 1);

	char buf[1024];
	int n = capture_print_summary_json(&key, &val, buf, sizeof(buf));
	test_assert(n > 0, "output is non-empty");
	test_assert(buf[n - 1] == '\n', "output ends with newline");
}

/* ======================================================================== */
/* Summary                                                                   */
/* ======================================================================== */

static void print_test_summary(void)
{
	printf("\n" YELLOW "===== Test Summary =====" RESET "\n");
	printf("Tests passed: " GREEN "%d" RESET "\n", tests_passed);
	printf("Tests failed: " RED   "%d" RESET "\n", tests_failed);
	printf("Total tests:  %d\n", tests_passed + tests_failed);
	if (tests_failed == 0)
		printf(GREEN "All tests passed!" RESET "\n");
	else
		printf(RED "Some tests failed!" RESET "\n");
}

int main(void)
{
	printf(BLUE "===== map_flush.h Test Suite =====" RESET "\n");
	printf("Testing functions from process_ext/map_flush.h\n");

	/* event_type_name */
	test_event_type_name_known_types();
	test_event_type_name_unknown();

	/* json_escape */
	test_json_escape_plain_string();
	test_json_escape_backslash();
	test_json_escape_double_quote();
	test_json_escape_newline();
	test_json_escape_tab();
	test_json_escape_mixed();
	test_json_escape_empty_string();
	test_json_escape_truncation();

	/* print_summary_json */
	test_print_summary_json_basic_fields();
	test_network_summary_endpoint_fields();
	test_print_summary_json_optional_total_bytes();
	test_print_summary_json_optional_extra();
	test_print_summary_json_escaped_fields();
	test_print_summary_json_newline_terminated();

	print_test_summary();
	return (tests_failed > 0) ? 1 : 0;
}
