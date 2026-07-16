// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Codex/aws-lc SSL entrypoint detection for stripped release binaries.
#ifndef __CODEX_OFFSETS_H
#define __CODEX_OFFSETS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <errno.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

struct codex_ssl_offsets {
	size_t ssl_write;
	size_t ssl_read;
	size_t ssl_do_handshake;
	bool write_is_ex;
	bool read_is_ex;
	bool found;
};

/* Derived from official Codex Linux symbols and validated against the
 * 0.144.1, 0.144.4, and 0.144.5 release binaries. */
static const uint8_t codex_awslc_write_ex[] = {
	0x55, 0x48, 0x89, 0xe5, 0x53, 0x50, 0x49, 0x89,
	0xc8, 0x31, 0xdb, 0x31, 0xc9, 0xe8, 0xbe, 0xfd,
	0xff, 0xff, 0x85, 0xc0, 0x0f, 0x4e, 0xc3, 0x48,
	0x83, 0xc4, 0x08, 0x5b, 0x5d, 0xc3,
};
static const uint8_t codex_awslc_read_ex[] = {
	0x55, 0x48, 0x89, 0xe5, 0xe8, 0xc7, 0xfb, 0xff,
	0xff, 0x31, 0xc9, 0x85, 0xc0, 0x0f, 0x4e, 0xc1,
	0x5d, 0xc3,
};
static const uint8_t codex_awslc_handshake[] = {
	0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
	0x53, 0x48, 0x83, 0xec, 0x28, 0x41, 0xbe, 0xff,
	0xff, 0xff, 0xff, 0x48, 0x85, 0xff, 0x0f, 0x84,
	0xdd, 0x00, 0x00, 0x00, 0x48, 0x89, 0xfb,
};

#define CODEX_AWSLC_WRITE_READ_DELTA 592
#define CODEX_AWSLC_READ_HANDSHAKE_DELTA 1680

static size_t codex_find_pattern(const uint8_t *data, size_t data_len,
				 const uint8_t *pattern, size_t pattern_len)
{
	size_t offset = 0;

	while (offset + pattern_len <= data_len) {
		const uint8_t *match = memchr(data + offset, pattern[0],
					      data_len - offset - pattern_len + 1);
		if (!match)
			break;
		offset = (size_t)(match - data);
		if (memcmp(match, pattern, pattern_len) == 0)
			return offset;
		offset++;
	}
	return (size_t)-1;
}

static bool codex_find_ssl_offsets(const char *binary_path,
				   struct codex_ssl_offsets *out)
{
	struct stat st;
	uint8_t *data;
	size_t write_off;
	int fd;

	memset(out, 0, sizeof(*out));
	fd = open(binary_path, O_RDONLY);
	if (fd < 0)
		return false;
	if (fstat(fd, &st) < 0 || st.st_size <= 0) {
		close(fd);
		return false;
	}
	data = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
	if (data == MAP_FAILED) {
		close(fd);
		return false;
	}

	write_off = codex_find_pattern(data, (size_t)st.st_size,
				       codex_awslc_write_ex,
				       sizeof(codex_awslc_write_ex));
	if (write_off != (size_t)-1
	    && write_off >= CODEX_AWSLC_WRITE_READ_DELTA
			    + CODEX_AWSLC_READ_HANDSHAKE_DELTA) {
		size_t read_off = write_off - CODEX_AWSLC_WRITE_READ_DELTA;
		size_t handshake_off = read_off - CODEX_AWSLC_READ_HANDSHAKE_DELTA;

		if (memcmp(data + read_off, codex_awslc_read_ex,
			   sizeof(codex_awslc_read_ex)) == 0
		    && memcmp(data + handshake_off, codex_awslc_handshake,
			      sizeof(codex_awslc_handshake)) == 0) {
			out->ssl_write = write_off;
			out->ssl_read = read_off;
			out->ssl_do_handshake = handshake_off;
			out->write_is_ex = true;
			out->read_is_ex = true;
			out->found = true;
		}
	}

	munmap(data, (size_t)st.st_size);
	close(fd);
	return out->found;
}

static bool codex_buf_contains(const uint8_t *buf, size_t len,
			       const char *needle)
{
	size_t needle_len = strlen(needle);

	return needle_len > 0 && len >= needle_len
	       && codex_find_pattern(buf, len, (const uint8_t *)needle,
				     needle_len) != (size_t)-1;
}

static bool codex_binary_has_tls_markers(const char *binary_path)
{
	static const char *markers[] = {
		"codex-cli", "@openai/codex", "rustls", "aws-lc", "aws_lc",
	};
	uint8_t buf[8192 + 32];
	size_t carry = 0;
	int fd = open(binary_path, O_RDONLY);

	if (fd < 0)
		return false;
	for (;;) {
		ssize_t n = read(fd, buf + carry, 8192);

		if (n < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (n == 0)
			break;
		size_t len = carry + (size_t)n;
		for (size_t i = 0; i < sizeof(markers) / sizeof(markers[0]); i++) {
			if (codex_buf_contains(buf, len, markers[i])) {
				close(fd);
				return true;
			}
		}
		carry = len < 32 ? len : 32;
		memmove(buf, buf + len - carry, carry);
	}
	close(fd);
	return false;
}

#endif
