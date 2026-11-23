/* SPDX-License-Identifier: MIT
 * Fixture for the readline attach tests: a program that *imports* `readline`
 * without defining it, the shape of /usr/bin/bash on Arch/Artix (issue #250).
 * `readline` is only ever called through the function pointer, so the symbol
 * stays undefined in this object and is resolved from readline_fixture_def.so
 * at load time. */
extern int readline(const char *prompt);

static int (*const import_readline)(const char *) = readline;

int main(void)
{
	return import_readline("fixture> ") + 1;
}