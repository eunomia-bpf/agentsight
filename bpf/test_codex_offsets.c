// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
#include <stdbool.h>
#include <linux/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "codex_offsets.h"
#include "sslsniff.h"

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
	uint8_t data[2048] = {};
	size_t offset = 0;
	int fd = mkstemp(template);

	check(fd >= 0, "created Grok signature fixture");
	if (fd < 0)
		return;
	memcpy(data + 32, "grok-cli rustls", sizeof("grok-cli rustls"));
	memcpy(data + 256, grok_rustls_buffer_plaintext_prefix,
	       sizeof(grok_rustls_buffer_plaintext_prefix));
	memcpy(data + 256 + GROK_RUSTLS_OUTBOUND_TAG_OFFSET,
	       grok_rustls_outbound_tag, sizeof(grok_rustls_outbound_tag));
	memcpy(data + 256 + GROK_RUSTLS_OUTBOUND_RANGE_OFFSET,
	       grok_rustls_outbound_range, sizeof(grok_rustls_outbound_range));
	memcpy(data + 256 + GROK_RUSTLS_OUTBOUND_DATA_OFFSET,
	       grok_rustls_outbound_data, sizeof(grok_rustls_outbound_data));
	check(write(fd, data, sizeof(data)) == sizeof(data),
	      "wrote Grok signature fixture");
	close(fd);

	check(grok_binary_has_tls_markers(template),
	      "requires Grok and rustls markers");
	check(grok_find_rustls_buffer_plaintext_offset(template, &offset)
		      && offset == 256,
	      "finds Grok/rustls buffer_plaintext signature");

	data[256 + GROK_RUSTLS_OUTBOUND_DATA_OFFSET] ^= 0xff;
	fd = open(template, O_WRONLY | O_TRUNC);
	check(fd >= 0, "opened Grok fixture for corruption");
	if (fd >= 0) {
		check(write(fd, data, sizeof(data)) == sizeof(data),
		      "wrote corrupted Grok fixture");
		close(fd);
		check(!grok_find_rustls_buffer_plaintext_offset(template, &offset),
		      "rejects a Grok signature with a changed ABI block");
	}

	memset(data, 0, sizeof(data));
	memcpy(data + 32, "grok-cli rustls", sizeof("grok-cli rustls"));
	memcpy(data + sizeof(data)
		     - sizeof(grok_rustls_buffer_plaintext_prefix),
	       grok_rustls_buffer_plaintext_prefix,
	       sizeof(grok_rustls_buffer_plaintext_prefix));
	fd = open(template, O_WRONLY | O_TRUNC);
	check(fd >= 0, "opened Grok fixture for near-EOF signature");
	if (fd >= 0) {
		check(write(fd, data, sizeof(data)) == sizeof(data),
		      "wrote near-EOF Grok signature fixture");
		close(fd);
		check(!grok_find_rustls_buffer_plaintext_offset(template, &offset),
		      "rejects a near-EOF Grok signature safely");
	}
	unlink(template);
}

static void test_codex_buffer_signature_detection(void)
{
	char template[] = "/tmp/agentsight-codex-buffer-offset-test.XXXXXX";
	uint8_t data[4096] = {};
	size_t offset = 0;
	const size_t fixture_offset = 256;
	int fd = mkstemp(template);

	check(fd >= 0, "created Codex buffer signature fixture");
	if (fd < 0)
		return;
	memcpy(data + 32, "codex-cli rustls", sizeof("codex-cli rustls"));
	memcpy(data + fixture_offset, codex_rustls_buffer_plaintext_prefix,
	       sizeof(codex_rustls_buffer_plaintext_prefix));
	memcpy(data + fixture_offset + CODEX_RUSTLS_OUTBOUND_RANGE_OFFSET,
	       codex_rustls_outbound_range,
	       sizeof(codex_rustls_outbound_range));
	memcpy(data + fixture_offset + CODEX_RUSTLS_SEND_PLAIN_OFFSET,
	       codex_rustls_send_plain_prefix,
	       sizeof(codex_rustls_send_plain_prefix));
	memcpy(data + fixture_offset + CODEX_RUSTLS_SEND_DATA_OFFSET,
	       codex_rustls_send_data_pointer,
	       sizeof(codex_rustls_send_data_pointer));
	check(write(fd, data, sizeof(data)) == sizeof(data),
	      "wrote Codex buffer signature fixture");
	close(fd);

	check(codex_find_rustls_buffer_plaintext_offset(template, &offset)
		      && offset == fixture_offset,
	      "finds Codex/rustls buffer_plaintext signature");

	data[fixture_offset + CODEX_RUSTLS_SEND_DATA_OFFSET] ^= 0xff;
	fd = open(template, O_WRONLY | O_TRUNC);
	check(fd >= 0, "opened Codex buffer fixture for corruption");
	if (fd >= 0) {
		check(write(fd, data, sizeof(data)) == sizeof(data),
		      "wrote corrupted Codex buffer fixture");
		close(fd);
		check(!codex_find_rustls_buffer_plaintext_offset(template, &offset),
		      "rejects a Codex buffer signature with a changed ABI block");
	}
	unlink(template);
}

static size_t planned_rustls_iovec_capture(const size_t *lengths, size_t count)
{
	size_t copied = 0;

	for (size_t i = 0; i < count && i < MAX_RUSTLS_IOVECS; i++) {
		size_t copy_size;
		size_t capacity;

		if (copied >= RUSTLS_MAX_CAPTURE_SIZE)
			break;
		capacity = RUSTLS_MAX_CAPTURE_SIZE - copied;
		copy_size = lengths[i] > RUSTLS_MAX_CAPTURE_SIZE
			? RUSTLS_MAX_CAPTURE_SIZE : lengths[i];
		if (copy_size > capacity)
			copy_size = capacity;
		copied += copy_size;
	}
	return copied;
}

static bool rustls_iovec_prefix_within_end(const size_t *lengths, size_t count,
					   size_t end)
{
	size_t inspected = 0;

	for (size_t i = 0; i < count && i < MAX_RUSTLS_IOVECS; i++) {
		if (inspected > end || lengths[i] > end - inspected)
			return false;
		inspected += lengths[i];
	}
	return true;
}

static void test_rustls_iovec_capture_plan(void)
{
	const size_t three_slices[] = { 20 * 1024, 1024, 32 };
	const size_t full_buffer[] = { RUSTLS_MAX_CAPTURE_SIZE };
	const size_t split_at_boundary[] = {
		RUSTLS_MAX_CAPTURE_SIZE - 2 * 1024,
		2 * 1024,
	};
	const size_t end_inside_last_slice[] = { 2 * 1024, 2 * 1024 };

	check(planned_rustls_iovec_capture(three_slices, 3)
		      == 21 * 1024 + 32,
	      "captures a third slice after a 20 KiB first slice");
	check(planned_rustls_iovec_capture(full_buffer, 1)
		      == RUSTLS_MAX_CAPTURE_SIZE,
	      "fills the rustls capture budget from one large slice");
	check(planned_rustls_iovec_capture(split_at_boundary, 2)
		      == RUSTLS_MAX_CAPTURE_SIZE,
	      "fills the capture budget across a non-chunk-aligned split");
	check(!rustls_iovec_prefix_within_end(
		      end_inside_last_slice, 2, 3 * 1024),
	      "rejects a rustls Multiple end cursor inside a slice");
}

int main(void)
{
	printf("===== Codex offset tests =====\n");
	test_signature_detection();
	test_marker_detection();
	test_grok_signature_detection();
	test_codex_buffer_signature_detection();
	test_rustls_iovec_capture_plan();
	printf("Tests passed: %d\n", tests_run - tests_failed);
	printf("Tests failed: %d\n", tests_failed);
	return tests_failed == 0 ? 0 : 1;
}
