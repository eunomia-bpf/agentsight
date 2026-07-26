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

static void add_writev_signature(uint8_t *data, size_t offset,
				 uint8_t first_branch, uint8_t second_branch)
{
	memcpy(data + offset, codex_rustls_writev_prefix,
	       sizeof(codex_rustls_writev_prefix));
	data[offset + 18] = first_branch;
	memcpy(data + offset + 19, codex_rustls_writev_iov,
	       sizeof(codex_rustls_writev_iov));
	data[offset + 27] = second_branch;
	memcpy(data + offset + 28, codex_rustls_writev_copy,
	       sizeof(codex_rustls_writev_copy));
}

static char *write_fixture(bool valid)
{
	char template[] = "/tmp/agentsight-codex-offsets-test.XXXXXX";
	uint8_t data[2048] = {};
	int fd = mkstemp(template);

	if (fd < 0)
		return NULL;
	memcpy(data + 32, "codex-cli rustls", sizeof("codex-cli rustls"));
	add_writev_signature(data, 256, 0x24, 0x23);
	if (valid) {
		add_writev_signature(data, 1024, 0x23, 0x22);
		memcpy(data + 1536, codex_rustls_write_prefix,
		       sizeof(codex_rustls_write_prefix));
	} else {
		data[256 + 28] ^= 0xff;
	}
	if (write(fd, data, sizeof(data)) != sizeof(data)) {
		close(fd);
		unlink(template);
		return NULL;
	}
	close(fd);
	return strdup(template);
}

static void test_signature_detection(void)
{
	struct codex_rustls_offsets offsets;
	char *path = write_fixture(true);

	check(path != NULL, "created rustls signature fixture");
	if (!path)
		return;
	check(codex_find_rustls_offsets(path, &offsets),
	      "finds Codex/rustls write_vectored signatures");
	check(offsets.count == 3, "reports every rustls write entrypoint");
	check(offsets.entries[0].offset == 256 && offsets.entries[0].vectored
	      && offsets.entries[1].offset == 1024 && offsets.entries[1].vectored
	      && offsets.entries[2].offset == 1536 && !offsets.entries[2].vectored,
	      "classifies direct and vectored writes");
	check(codex_binary_has_tls_markers(path), "requires Codex and rustls markers");
	unlink(path);
	free(path);

	path = write_fixture(false);
	check(path != NULL, "created invalid signature fixture");
	if (!path)
		return;
	check(!codex_find_rustls_offsets(path, &offsets),
	      "rejects a partial signature match");
	unlink(path);
	free(path);
}

static void test_marker_detection(void)
{
	char template[] = "/tmp/agentsight-codex-marker-test.XXXXXX";
	const char contents[] = "prefix rustls aws-lc suffix";
	int fd = mkstemp(template);

	check(fd >= 0, "created marker fixture");
	if (fd < 0)
		return;
	check(write(fd, contents, sizeof(contents)) == sizeof(contents),
	      "wrote marker fixture");
	close(fd);
	check(!codex_binary_has_tls_markers(template),
	      "rejects TLS markers without a Codex marker");
	unlink(template);
}

static void test_grok_signature_detection(void)
{
	char template[] = "/tmp/agentsight-grok-offset-test.XXXXXX";
	uint8_t data[1024] = {};
	size_t offset = 0;
	int fd = mkstemp(template);

	check(fd >= 0, "created Grok signature fixture");
	if (fd < 0)
		return;
	memcpy(data + 32, "grok-cli rustls", sizeof("grok-cli rustls"));
	memcpy(data + 256, grok_rustls_buffer_plaintext_prefix,
	       sizeof(grok_rustls_buffer_plaintext_prefix));
	check(write(fd, data, sizeof(data)) == sizeof(data),
	      "wrote Grok signature fixture");
	close(fd);

	check(grok_binary_has_tls_markers(template),
	      "requires Grok and rustls markers");
	check(grok_find_rustls_buffer_plaintext_offset(template, &offset)
		      && offset == 256,
	      "finds Grok/rustls buffer_plaintext signature");

	data[256 + sizeof(grok_rustls_buffer_plaintext_prefix) - 1] ^= 0xff;
	fd = open(template, O_WRONLY | O_TRUNC);
	check(fd >= 0, "opened Grok fixture for corruption");
	if (fd >= 0) {
		check(write(fd, data, sizeof(data)) == sizeof(data),
		      "wrote corrupted Grok fixture");
		close(fd);
		check(!grok_find_rustls_buffer_plaintext_offset(template, &offset),
		      "rejects a partial Grok signature match");
	}
	unlink(template);
}

int main(void)
{
	printf("===== Codex offset tests =====\n");
	test_signature_detection();
	test_marker_detection();
	test_grok_signature_detection();
	printf("Tests passed: %d\n", tests_run - tests_failed);
	printf("Tests failed: %d\n", tests_failed);
	return tests_failed == 0 ? 0 : 1;
}
