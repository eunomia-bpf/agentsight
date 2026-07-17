// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Codex/rustls plaintext write detection for stripped release binaries.
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

#define CODEX_MAX_RUSTLS_WRITEV_OFFSETS 32

struct codex_rustls_offsets {
	size_t write_vectored[CODEX_MAX_RUSTLS_WRITEV_OFFSETS];
	size_t count;
};

/* rustls 0.23 PlaintextSink::write_vectored. Branch displacements differ
 * between compiler releases, so validate the stable blocks around them. */
static const uint8_t codex_rustls_writev_prefix[] = {
	0x55, 0x41, 0x57, 0x41, 0x56, 0x41, 0x55, 0x41,
	0x54, 0x53, 0x48, 0x83, 0xec, 0x68, 0x48, 0x85,
	0xd2, 0x74,
};
static const uint8_t codex_rustls_writev_iov[] = {
	0x49, 0x89, 0xfe, 0x48, 0x83, 0xfa, 0x01, 0x75,
};
static const uint8_t codex_rustls_writev_copy[] = {
	0xf3, 0x0f, 0x6f, 0x06, 0xf3, 0x0f, 0x7f, 0x44,
	0x24, 0x10,
};

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

static bool codex_find_rustls_offsets(const char *binary_path,
				      struct codex_rustls_offsets *out)
{
	struct stat st;
	uint8_t *data;
	size_t search = 0;
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

	while (search + sizeof(codex_rustls_writev_prefix) <= (size_t)st.st_size) {
		size_t relative = codex_find_pattern(
			data + search, (size_t)st.st_size - search,
			codex_rustls_writev_prefix,
			sizeof(codex_rustls_writev_prefix));
		if (relative == (size_t)-1)
			break;
		size_t offset = search + relative;
		if (offset + 28 + sizeof(codex_rustls_writev_copy)
				<= (size_t)st.st_size
		    && memcmp(data + offset + 19, codex_rustls_writev_iov,
			      sizeof(codex_rustls_writev_iov)) == 0
		    && memcmp(data + offset + 28, codex_rustls_writev_copy,
			      sizeof(codex_rustls_writev_copy)) == 0) {
			if (out->count == CODEX_MAX_RUSTLS_WRITEV_OFFSETS) {
				out->count = 0;
				break;
			}
			out->write_vectored[out->count++] = offset;
		}
		search = offset + 1;
	}

	munmap(data, (size_t)st.st_size);
	close(fd);
	return out->count > 0;
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
	uint8_t buf[8192 + 32];
	bool has_codex = false;
	bool has_rustls = false;
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
		has_codex |= codex_buf_contains(buf, len, "codex-cli")
			     || codex_buf_contains(buf, len, "@openai/codex");
		has_rustls |= codex_buf_contains(buf, len, "rustls");
		if (has_codex && has_rustls) {
			close(fd);
			return true;
		}
		carry = len < 32 ? len : 32;
		memmove(buf, buf + len - carry, carry);
	}
	close(fd);
	return false;
}

#endif
