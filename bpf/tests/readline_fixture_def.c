/* SPDX-License-Identifier: MIT
 * Fixture for the readline attach tests: a shared object that *defines*
 * `readline`, the counterpart of libreadline.so on a dynamic-link distro. */
int readline(const char *prompt)
{
	(void)prompt;
	return 0;
}