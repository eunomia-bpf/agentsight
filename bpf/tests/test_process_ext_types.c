/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Unit tests for process_ext/types.h data structures and constants:
 *   - sizeof(struct agg_key) matches expected layout
 *   - sizeof(struct agg_value) matches expected layout
 *   - event_type_new enum values equal their documented constants
 *   - DETAIL_LEN constant value
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

/* ---- BPF type stubs --------------------------------------------------- */
#ifdef __linux__
#include <linux/types.h>
#else
typedef uint32_t __u32;
typedef uint64_t __u64;
#endif

#ifndef BPF_ANY
#define BPF_ANY 0
#endif

#include "process.h"
#include "process_ext/types.h"

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
/* DETAIL_LEN constant                                                       */
/* ======================================================================== */

static void test_detail_len_value(void)
{
	printf("\n" BLUE "Testing DETAIL_LEN constant:" RESET "\n");

	test_assert(DETAIL_LEN == 64, "DETAIL_LEN equals 64");
	printf("  DETAIL_LEN = %d\n", DETAIL_LEN);
}

/* ======================================================================== */
/* struct agg_key                                                            */
/* ======================================================================== */

static void test_agg_key_field_sizes(void)
{
	printf("\n" BLUE "Testing struct agg_key field sizes:" RESET "\n");

	/*
	 * Expected layout:
	 *   __u32  pid;              4 bytes
	 *   __u32  event_type;       4 bytes
	 *   char   detail[64];      64 bytes
	 *   __u16  port;              2 bytes
	 *   __u8   protocol;          1 byte
	 *   padding;                  1 byte
	 *   ---------------------
	 *   total: 76 bytes
	 */
	test_assert(sizeof((__u32){0}) == 4, "__u32 is 4 bytes");
	test_assert(sizeof(((struct agg_key *)0)->pid) == 4,
	            "agg_key.pid is 4 bytes");
	test_assert(sizeof(((struct agg_key *)0)->event_type) == 4,
	            "agg_key.event_type is 4 bytes");
	test_assert(sizeof(((struct agg_key *)0)->detail) == DETAIL_LEN,
	            "agg_key.detail is DETAIL_LEN bytes");
}

static void test_agg_key_total_size(void)
{
	printf("\n" BLUE "Testing struct agg_key total size:" RESET "\n");

	/*
	 * pid (4) + event_type (4) + process_start_ns (8) + detail[64]
	 * + port (2) + protocol (1) + local_endpoint[64] + alignment (5).
	 */
	size_t expected = 4 + 4 + 8 + DETAIL_LEN + 4 + DETAIL_LEN + 4;
	printf("  sizeof(struct agg_key) = %zu (expected %zu)\n",
	       sizeof(struct agg_key), expected);
	test_assert(sizeof(struct agg_key) == expected,
	            "sizeof(agg_key) includes network fields");
}

static void test_agg_key_field_offsets(void)
{
	printf("\n" BLUE "Testing struct agg_key field offsets:" RESET "\n");

	test_assert(offsetof(struct agg_key, pid) == 0,
	            "agg_key.pid is at offset 0");
	test_assert(offsetof(struct agg_key, event_type) == 4,
	            "agg_key.event_type is at offset 4");
	test_assert(offsetof(struct agg_key, detail) == 16,
	            "agg_key.detail is at offset 16");
}

static void test_agg_key_zero_initialisation(void)
{
	printf("\n" BLUE "Testing struct agg_key zero-initialisation:" RESET "\n");

	struct agg_key k = {0};
	test_assert(k.pid == 0,         "zero-init: pid == 0");
	test_assert(k.event_type == 0,  "zero-init: event_type == 0");
	test_assert(k.detail[0] == '\0',"zero-init: detail[0] == NUL");
}

/* ======================================================================== */
/* struct agg_value                                                          */
/* ======================================================================== */

static void test_agg_value_field_sizes(void)
{
	printf("\n" BLUE "Testing struct agg_value field sizes:" RESET "\n");

	test_assert(sizeof((__u64){0}) == 8, "__u64 is 8 bytes");
	test_assert(sizeof(((struct agg_value *)0)->count) == 8,
	            "agg_value.count is 8 bytes");
	test_assert(sizeof(((struct agg_value *)0)->total_bytes) == 8,
	            "agg_value.total_bytes is 8 bytes");
	test_assert(sizeof(((struct agg_value *)0)->first_ts) == 8,
	            "agg_value.first_ts is 8 bytes");
	test_assert(sizeof(((struct agg_value *)0)->last_ts) == 8,
	            "agg_value.last_ts is 8 bytes");
	test_assert(sizeof(((struct agg_value *)0)->comm) == TASK_COMM_LEN,
	            "agg_value.comm is TASK_COMM_LEN bytes");
	test_assert(sizeof(((struct agg_value *)0)->extra) == MAX_FILENAME_LEN,
	            "agg_value.extra is MAX_FILENAME_LEN bytes");
}

static void test_agg_value_total_size(void)
{
	printf("\n" BLUE "Testing struct agg_value total size:" RESET "\n");

	/*
	 * count(8) + total_bytes(8) + first_ts(8) + last_ts(8) = 32 bytes
	 * comm[16] + extra[127] = 143 bytes
	 * The compiler may add padding after comm to align the struct end, but
	 * at minimum size must be >= 32 + 16 + 127 = 175 bytes.
	 */
	size_t min_expected = 4 * 8 + TASK_COMM_LEN + MAX_FILENAME_LEN;
	printf("  sizeof(struct agg_value) = %zu (minimum expected %zu)\n",
	       sizeof(struct agg_value), min_expected);
	test_assert(sizeof(struct agg_value) >= min_expected,
	            "sizeof(agg_value) >= 4*8 + TASK_COMM_LEN + MAX_FILENAME_LEN");
}

static void test_agg_value_field_offsets(void)
{
	printf("\n" BLUE "Testing struct agg_value field offsets:" RESET "\n");

	test_assert(offsetof(struct agg_value, count) == 0,
	            "agg_value.count is at offset 0");
	test_assert(offsetof(struct agg_value, total_bytes) == 8,
	            "agg_value.total_bytes is at offset 8");
	test_assert(offsetof(struct agg_value, first_ts) == 16,
	            "agg_value.first_ts is at offset 16");
	test_assert(offsetof(struct agg_value, last_ts) == 24,
	            "agg_value.last_ts is at offset 24");
	test_assert(offsetof(struct agg_value, comm) == 32,
	            "agg_value.comm is at offset 32");
}

static void test_agg_value_zero_initialisation(void)
{
	printf("\n" BLUE "Testing struct agg_value zero-initialisation:" RESET "\n");

	struct agg_value v = {0};
	test_assert(v.count == 0,       "zero-init: count == 0");
	test_assert(v.total_bytes == 0, "zero-init: total_bytes == 0");
	test_assert(v.first_ts == 0,    "zero-init: first_ts == 0");
	test_assert(v.last_ts == 0,     "zero-init: last_ts == 0");
	test_assert(v.comm[0] == '\0',  "zero-init: comm[0] == NUL");
	test_assert(v.extra[0] == '\0', "zero-init: extra[0] == NUL");
}

/* ======================================================================== */
/* enum event_type_new values                                                */
/* ======================================================================== */

static void test_event_type_new_filesystem_values(void)
{
	printf("\n" BLUE "Testing event_type_new — filesystem event values:" RESET "\n");

	test_assert((int)EVENT_TYPE_FILE_DELETE   == 10, "FILE_DELETE == 10");
	test_assert((int)EVENT_TYPE_FILE_RENAME   == 11, "FILE_RENAME == 11");
	test_assert((int)EVENT_TYPE_DIR_CREATE    == 12, "DIR_CREATE == 12");
	test_assert((int)EVENT_TYPE_FILE_TRUNCATE == 13, "FILE_TRUNCATE == 13");
	test_assert((int)EVENT_TYPE_CHDIR         == 14, "CHDIR == 14");
	test_assert((int)EVENT_TYPE_WRITE         == 15, "WRITE == 15");
}

static void test_event_type_new_network_values(void)
{
	printf("\n" BLUE "Testing event_type_new — network event values:" RESET "\n");

	test_assert((int)EVENT_TYPE_NET_BIND    == 20, "NET_BIND == 20");
	test_assert((int)EVENT_TYPE_NET_LISTEN  == 21, "NET_LISTEN == 21");
	test_assert((int)EVENT_TYPE_NET_CONNECT == 22, "NET_CONNECT == 22");
}

static void test_event_type_new_process_values(void)
{
	printf("\n" BLUE "Testing event_type_new — process coordination event values:" RESET "\n");

	test_assert((int)EVENT_TYPE_PGRP_CHANGE    == 30, "PGRP_CHANGE == 30");
	test_assert((int)EVENT_TYPE_SESSION_CREATE == 31, "SESSION_CREATE == 31");
	test_assert((int)EVENT_TYPE_SIGNAL_SEND    == 32, "SIGNAL_SEND == 32");
	test_assert((int)EVENT_TYPE_PROC_FORK      == 33, "PROC_FORK == 33");
}

static void test_event_type_new_memory_values(void)
{
	printf("\n" BLUE "Testing event_type_new — memory event values:" RESET "\n");

	test_assert((int)EVENT_TYPE_MMAP_SHARED == 40, "MMAP_SHARED == 40");
	test_assert((int)EVENT_TYPE_COW_FAULT   == 41, "COW_FAULT == 41");
}

static void test_event_type_new_no_collision_with_legacy(void)
{
	printf("\n" BLUE "Testing event_type_new — no collision with legacy event_type enum:" RESET "\n");

	/*
	 * The legacy enum event_type has values 0, 1, 2.  All new event types
	 * must be >= 10 so they do not overlap.
	 */
	test_assert((int)EVENT_TYPE_FILE_DELETE > (int)EVENT_TYPE_FILE_OPERATION,
	            "new event types are all greater than legacy EVENT_TYPE_FILE_OPERATION(2)");
}

/* ======================================================================== */
/* process.h constants used by process_ext/types.h                          */
/* ======================================================================== */

static void test_process_h_constants(void)
{
	printf("\n" BLUE "Testing constants from process.h:" RESET "\n");

	test_assert(TASK_COMM_LEN    == 16,  "TASK_COMM_LEN == 16");
	test_assert(MAX_FILENAME_LEN == 127, "MAX_FILENAME_LEN == 127");
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
	printf(BLUE "===== process_ext/types.h Test Suite =====" RESET "\n");
	printf("Testing data structures and constants from process_ext/types.h\n");

	/* DETAIL_LEN */
	test_detail_len_value();

	/* struct agg_key */
	test_agg_key_field_sizes();
	test_agg_key_total_size();
	test_agg_key_field_offsets();
	test_agg_key_zero_initialisation();

	/* struct agg_value */
	test_agg_value_field_sizes();
	test_agg_value_total_size();
	test_agg_value_field_offsets();
	test_agg_value_zero_initialisation();

	/* enum event_type_new */
	test_event_type_new_filesystem_values();
	test_event_type_new_network_values();
	test_event_type_new_process_values();
	test_event_type_new_memory_values();
	test_event_type_new_no_collision_with_legacy();

	/* process.h constants */
	test_process_h_constants();

	print_test_summary();
	return (tests_failed > 0) ? 1 : 0;
}
