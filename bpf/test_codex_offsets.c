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

static char *write_fixture(bool valid)
{
	char template[] = "/tmp/agentsight-codex-offsets-test.XXXXXX";
	size_t handshake = 128;
	size_t read = handshake + CODEX_AWSLC_READ_HANDSHAKE_DELTA;
	size_t write_offset = read + CODEX_AWSLC_WRITE_READ_DELTA;
	size_t size = write_offset + sizeof(codex_awslc_write_ex) + 16;
	uint8_t *data = calloc(1, size);
	int fd = mkstemp(template);

	if (fd < 0 || !data)
		goto error;
	memcpy(data + handshake, codex_awslc_handshake,
	       sizeof(codex_awslc_handshake));
	memcpy(data + read, codex_awslc_read_ex, sizeof(codex_awslc_read_ex));
	memcpy(data + write_offset, codex_awslc_write_ex,
	       sizeof(codex_awslc_write_ex));
	if (!valid)
		data[read] ^= 0xff;
	if (write(fd, data, size) != (ssize_t)size)
		goto error;
	close(fd);
	free(data);
	return strdup(template);

error:
	if (fd >= 0) {
		close(fd);
		unlink(template);
	}
	free(data);
	return NULL;
}

static void test_signature_detection(void)
{
	struct codex_ssl_offsets offsets;
	char *path = write_fixture(true);

	check(path != NULL, "created aws-lc signature fixture");
	if (!path)
		return;
	check(codex_find_ssl_offsets(path, &offsets),
	      "finds validated Codex/aws-lc signatures");
	check(offsets.ssl_do_handshake == 128,
	      "reports SSL_do_handshake offset");
	check(offsets.ssl_read == 128 + CODEX_AWSLC_READ_HANDSHAKE_DELTA,
	      "reports SSL_read_ex offset");
	check(offsets.ssl_write == 128 + CODEX_AWSLC_READ_HANDSHAKE_DELTA
				       + CODEX_AWSLC_WRITE_READ_DELTA,
	      "reports SSL_write_ex offset");
	check(offsets.write_is_ex && offsets.read_is_ex,
	      "uses *_ex uprobes");
	unlink(path);
	free(path);

	path = write_fixture(false);
	check(path != NULL, "created invalid signature fixture");
	if (!path)
		return;
	check(!codex_find_ssl_offsets(path, &offsets),
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
	check(codex_binary_has_tls_markers(template),
	      "detects Codex TLS stack markers");
	unlink(template);
}

int main(void)
{
	printf("===== Codex offset tests =====\n");
	test_signature_detection();
	test_marker_detection();
	printf("Tests passed: %d\n", tests_run - tests_failed);
	printf("Tests failed: %d\n", tests_failed);
	return tests_failed == 0 ? 0 : 1;
}
