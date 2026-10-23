// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "process_utils.h"

#define RESET   "\033[0m"
#define RED     "\033[31m"
#define GREEN   "\033[32m"
#define YELLOW  "\033[33m"
#define BLUE    "\033[34m"

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

static void test_postprocess_full_command_with_arg_len(void)
{
	char raw[] = "python\0script.py\0--model\0gpt-5";
	const char *cmd = postprocess_full_command(raw, sizeof(raw), sizeof(raw) - 1);

	test_assert(strcmp(cmd, "python script.py --model gpt-5") == 0,
		    "postprocess_full_command converts argv NULs to spaces");
}

static void test_postprocess_full_command_without_arg_len(void)
{
	char raw[] = "python\0SECRET_ENV=value";
	const char *cmd = postprocess_full_command(raw, sizeof(raw), 0);

	test_assert(strcmp(cmd, "python") == 0,
		    "postprocess_full_command falls back to argv0 when arg_len is missing");
}

static void test_postprocess_full_command_rejects_oversized_arg_len(void)
{
	char raw[] = "node\0server.js";
	const char *cmd = postprocess_full_command(raw, sizeof(raw), sizeof(raw) + 10);

	test_assert(strcmp(cmd, "node") == 0,
		    "postprocess_full_command ignores oversized arg_len");
}

static void test_kernel_dev_number_decoding(void)
{
	test_assert(kernel_dev_major(0x10300001u) == 259 &&
		    kernel_dev_minor(0x10300001u) == 1,
		    "kernel device 259:1 decodes from raw 0x10300001");
	test_assert(kernel_dev_major(1149u) == 0 &&
		    kernel_dev_minor(1149u) == 1149,
		    "kernel device 0:1149 decodes from raw 1149");
	test_assert(kernel_dev_major(0xffffffffu) == 4095 &&
		    kernel_dev_minor(0xffffffffu) == 1048575,
		    "kernel device decoding retains all major/minor bits");
}

static void print_test_summary(void)
{
	printf("\n" YELLOW "===== Test Summary =====" RESET "\n");
	printf("Tests passed: " GREEN "%d" RESET "\n", tests_passed);
	printf("Tests failed: " RED "%d" RESET "\n", tests_failed);
	printf("Total tests:  %d\n", tests_passed + tests_failed);

	if (tests_failed == 0)
		printf(GREEN "All tests passed!" RESET "\n");
	else
		printf(RED "Some tests failed!" RESET "\n");
}

int main(void)
{
	printf(BLUE "===== Process Utils Test Suite =====" RESET "\n");

	test_postprocess_full_command_with_arg_len();
	test_postprocess_full_command_without_arg_len();
	test_postprocess_full_command_rejects_oversized_arg_len();

	print_test_summary();

	return tests_failed > 0 ? 1 : 0;
}
