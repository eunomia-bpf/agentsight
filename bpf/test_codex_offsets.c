// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "codex_offsets.h"

static int tests_run;
static int tests_failed;

static void check(bool condition, const char *name)
{
	tests_run++;
	if (condition) {
		printf("[PASS] %s\n", name);
	} else {
		printf("[FAIL] %s\n", name);
		tests_failed++;
	}
}

static void hash_to_hex(const uint8_t hash[32], char out[65])
{
	static const char digits[] = "0123456789abcdef";

	for (int i = 0; i < 32; i++) {
		out[i * 2] = digits[hash[i] >> 4];
		out[i * 2 + 1] = digits[hash[i] & 0xf];
	}
	out[64] = '\0';
}

static void test_sha256_abc(void)
{
	struct codex_sha256_ctx ctx;
	uint8_t hash[32];
	char hex[65];

	codex_sha256_init(&ctx);
	codex_sha256_update(&ctx, (const uint8_t *)"abc", 3);
	codex_sha256_final(&ctx, hash);
	hash_to_hex(hash, hex);
	check(strcmp(hex,
		     "ba7816bf8f01cfea414140de5dae2223"
		     "b00361a396177a9cb410ff61f20015ad") == 0,
	      "sha256 implementation matches known abc digest");
}

static char *write_temp_file(const char *contents)
{
	char template[] = "/tmp/agentsight-codex-offsets-test.XXXXXX";
	int fd = mkstemp(template);

	if (fd < 0)
		return NULL;
	if (write(fd, contents, strlen(contents)) < 0) {
		close(fd);
		unlink(template);
		return NULL;
	}
	close(fd);
	return strdup(template);
}

static void test_marker_detection(void)
{
	char *path = write_temp_file("prefix rustls aws-lc suffix");

	check(path != NULL, "created marker temp file");
	if (!path)
		return;
	check(codex_binary_has_tls_markers(path),
	      "detects Codex TLS stack marker strings");
	unlink(path);
	free(path);
}

static void test_nonmatching_binary_misses_table(void)
{
	struct codex_ssl_offsets offsets;
	char *path = write_temp_file("not a codex release binary");

	check(path != NULL, "created nonmatching temp file");
	if (!path)
		return;
	check(!codex_find_ssl_offsets(path, &offsets),
	      "nonmatching binary does not hit Codex offset table");
	unlink(path);
	free(path);
}

int main(void)
{
	printf("===== Codex offset tests =====\n");
	test_sha256_abc();
	test_marker_detection();
	test_nonmatching_binary_misses_table();
	printf("Tests passed: %d\n", tests_run - tests_failed);
	printf("Tests failed: %d\n", tests_failed);
	return tests_failed == 0 ? 0 : 1;
}
