/* SPDX-License-Identifier: MIT
 * Tests the readline attach point selection: an undefined import must never be
 * accepted, and the probe must resolve to some ELF that defines the symbol.
 *
 * argv: <fixture_imports_readline> <fixture_defines_readline.so>
 */
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <limits.h>

#include "readline_probe.h"

#define RESET "\033[0m"
#define RED "\033[31m"
#define GREEN "\033[32m"

static int tests_passed = 0;
static int tests_failed = 0;

static void test_assert(bool condition, const char *test_name)
{
	printf("[%s%s%s] %s\n", condition ? GREEN : RED,
	       condition ? "PASS" : "FAIL", RESET, test_name);
	if (condition)
		tests_passed++;
	else
		tests_failed++;
}

int main(int argc, char **argv)
{
	char target[PATH_MAX];
	const char *found;

	if (argc >= 3) {
		/* The fixture's library lives beside it; the loader resolves the
		 * soname out of bash's dynamic section the same way. */
		char dir[PATH_MAX];
		char *slash;

		snprintf(dir, sizeof(dir), "%s", argv[2]);
		slash = strrchr(dir, '/');
		if (slash)
			*slash = '\0';
		setenv("LD_LIBRARY_PATH", dir, 1);
	}

	if (argc < 3) {
		fprintf(stderr, "usage: %s <imports-readline> <defines-readline.so>\n",
			argv[0]);
		return 2;
	}

	test_assert(!elf_defines_symbol(argv[1], READLINE_SYM),
		    "an undefined readline import is not an attach point");
	test_assert(elf_defines_symbol(argv[2], READLINE_SYM),
		    "a defined readline symbol is an attach point");

	found = readline_target_for(argv[1], target, sizeof(target));
	test_assert(found != NULL,
		    "a binary that imports readline resolves to a defining ELF");

	found = find_readline_target(target, sizeof(target));
	test_assert(found != NULL, "this host has a readline attach point");
	test_assert(found != NULL && elf_defines_symbol(found, READLINE_SYM),
		    "the selected attach point defines readline");

	printf("\nTests passed: %d, failed: %d\n", tests_passed, tests_failed);
	return tests_failed > 0 ? 1 : 0;
}