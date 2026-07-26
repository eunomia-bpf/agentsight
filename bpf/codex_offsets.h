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

#define CODEX_MAX_RUSTLS_OFFSETS 64

struct codex_rustls_offset {
	size_t offset;
	bool vectored;
};

struct codex_rustls_offsets {
	struct codex_rustls_offset entries[CODEX_MAX_RUSTLS_OFFSETS];
	size_t count;
};

static const uint8_t codex_rustls_write_prefix[] = {
	0x41, 0x56, 0x53, 0x48, 0x83, 0xec, 0x48, 0x49,
	0x89, 0xfe, 0x48, 0x89, 0x74, 0x24, 0x10, 0x48,
	0x89, 0x54, 0x24, 0x18, 0x48, 0xc7, 0x44, 0x24,
	0x08, 0x00, 0x00, 0x00,
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

/* rustls 0.23 CommonState::buffer_plaintext, as emitted by rustc 1.92.
 * This stable prefix is shared by the supported stripped Grok binaries. */
static const uint8_t grok_rustls_buffer_plaintext_prefix[] = {
	0x55, 0x41, 0x57, 0x41, 0x56, 0x41, 0x55, 0x41,
	0x54, 0x53, 0x48, 0x83, 0xec, 0x68, 0x49, 0x89,
	0xd6, 0x48, 0x89, 0xfd, 0x48, 0x8b, 0x9f, 0x08,
	0x03, 0x00, 0x00, 0x4c, 0x8b, 0xa7, 0x10, 0x03,
	0x00, 0x00, 0x4c, 0x8b, 0xaf, 0x18, 0x03, 0x00,
	0x00, 0x48, 0xb8, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x80,
};

/* rustls 0.23.36 CommonState::buffer_plaintext, as emitted by rustc 1.95
 * for Codex 0.145. The later blocks validate its rustc 1.95 OutboundChunks
 * layout ({data, count, start, end} for Multiple) and send path. */
static const uint8_t codex_rustls_buffer_plaintext_prefix[] = {
	0x55, 0x41, 0x57, 0x41, 0x56, 0x41, 0x55, 0x41,
	0x54, 0x53, 0x48, 0x83, 0xec, 0x28, 0x49, 0x89,
	0xd6, 0x48, 0x89, 0xf3, 0x4c, 0x8b, 0xa7, 0x08,
	0x03, 0x00, 0x00, 0x48, 0xb8, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x80,
};
#define CODEX_RUSTLS_OUTBOUND_RANGE_OFFSET 0xd5
#define CODEX_RUSTLS_SEND_PLAIN_OFFSET 0x870
#define CODEX_RUSTLS_SEND_DATA_OFFSET 0xb78
static const uint8_t codex_rustls_outbound_range[] = {
	0x48, 0x8b, 0x43, 0x10, 0x48, 0x8b, 0x4b, 0x18,
	0x48, 0x29, 0xc1, 0x48, 0x83, 0x3b, 0x00, 0x48,
	0x0f, 0x44, 0xc8,
};
static const uint8_t codex_rustls_send_plain_prefix[] = {
	0x55, 0x41, 0x57, 0x41, 0x56, 0x41, 0x55, 0x41,
	0x54, 0x53, 0x48, 0x83, 0xec, 0x38, 0x49, 0x89,
	0xfc, 0x85, 0xd2, 0x74, 0x23, 0x4c, 0x8b, 0x16,
	0x4d, 0x85, 0xd2,
};
static const uint8_t codex_rustls_send_data_pointer[] = {
	0x48, 0x8b, 0x06,
};

/* Validate the OutboundChunks ABI used by the probe, not just the function
 * prologue. These blocks load the enum tag/count at +0, range at +16/+24,
 * and data pointer at +8. */
#define GROK_RUSTLS_OUTBOUND_TAG_OFFSET 0xd7
#define GROK_RUSTLS_OUTBOUND_RANGE_OFFSET 0xe7
#define GROK_RUSTLS_OUTBOUND_DATA_OFFSET 0x3f1
static const uint8_t grok_rustls_outbound_tag[] = {
	0x4c, 0x8b, 0x26,
};
static const uint8_t grok_rustls_outbound_range[] = {
	0x4c, 0x8b, 0x7e, 0x10, 0x48, 0x8b, 0x7e, 0x18,
	0x48, 0x89, 0xfb, 0x4c, 0x29, 0xfb, 0x4d, 0x85,
	0xe4, 0x49, 0x0f, 0x44, 0xdf,
};
static const uint8_t grok_rustls_outbound_data[] = {
	0x48, 0x8b, 0x46, 0x08, 0x4d, 0x85, 0xe4, 0x74,
	0x1d, 0x4c, 0x8d, 0x3c, 0x3b,
};

struct rustls_signature_block {
	size_t offset;
	const uint8_t *data;
	size_t len;
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

static bool codex_add_rustls_offset(struct codex_rustls_offsets *out,
				     size_t offset, bool vectored)
{
	if (out->count == CODEX_MAX_RUSTLS_OFFSETS)
		return false;
	out->entries[out->count++] = (struct codex_rustls_offset) {
		.offset = offset,
		.vectored = vectored,
	};
	return true;
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
			if (!codex_add_rustls_offset(out, offset, true))
				break;
		}
		search = offset + 1;
	}
	search = 0;
	while (search + sizeof(codex_rustls_write_prefix) <= (size_t)st.st_size) {
		size_t relative = codex_find_pattern(
			data + search, (size_t)st.st_size - search,
			codex_rustls_write_prefix, sizeof(codex_rustls_write_prefix));
		if (relative == (size_t)-1)
			break;
		search += relative;
		if (!codex_add_rustls_offset(out, search, false))
			break;
		search++;
	}

	munmap(data, (size_t)st.st_size);
	close(fd);
	return out->count > 0;
}

static bool rustls_find_plaintext_offset(
	const char *binary_path, const uint8_t *prefix, size_t prefix_len,
	const struct rustls_signature_block *blocks, size_t block_count,
	size_t *offset)
{
	struct stat st;
	uint8_t *data;
	size_t required_len = prefix_len;
	size_t search = 0;
	int fd;

	for (size_t i = 0; i < block_count; i++) {
		if (blocks[i].offset > SIZE_MAX - blocks[i].len)
			return false;
		size_t end = blocks[i].offset + blocks[i].len;

		if (end > required_len)
			required_len = end;
	}
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
	while (search <= (size_t)st.st_size
	       && required_len <= (size_t)st.st_size - search) {
		size_t relative = codex_find_pattern(
			data + search, (size_t)st.st_size - search,
			prefix, prefix_len);
		size_t found;
		bool matches = true;

		if (relative == (size_t)-1)
			break;
		found = search + relative;
		if (required_len > (size_t)st.st_size - found)
			break;
		for (size_t i = 0; i < block_count; i++) {
			if (memcmp(data + found + blocks[i].offset,
				   blocks[i].data, blocks[i].len) != 0) {
				matches = false;
				break;
			}
		}
		if (matches) {
			*offset = found;
			munmap(data, (size_t)st.st_size);
			close(fd);
			return true;
		}
		search = found + 1;
	}
	munmap(data, (size_t)st.st_size);
	close(fd);
	return false;
}

static bool grok_find_rustls_buffer_plaintext_offset(const char *binary_path,
						      size_t *offset)
{
	const struct rustls_signature_block blocks[] = {
		{
			.offset = GROK_RUSTLS_OUTBOUND_TAG_OFFSET,
			.data = grok_rustls_outbound_tag,
			.len = sizeof(grok_rustls_outbound_tag),
		},
		{
			.offset = GROK_RUSTLS_OUTBOUND_RANGE_OFFSET,
			.data = grok_rustls_outbound_range,
			.len = sizeof(grok_rustls_outbound_range),
		},
		{
			.offset = GROK_RUSTLS_OUTBOUND_DATA_OFFSET,
			.data = grok_rustls_outbound_data,
			.len = sizeof(grok_rustls_outbound_data),
		},
	};

	return rustls_find_plaintext_offset(
		binary_path, grok_rustls_buffer_plaintext_prefix,
		sizeof(grok_rustls_buffer_plaintext_prefix), blocks,
		sizeof(blocks) / sizeof(blocks[0]), offset);
}

static bool codex_find_rustls_buffer_plaintext_offset(const char *binary_path,
						       size_t *offset)
{
	const struct rustls_signature_block blocks[] = {
		{
			.offset = CODEX_RUSTLS_OUTBOUND_RANGE_OFFSET,
			.data = codex_rustls_outbound_range,
			.len = sizeof(codex_rustls_outbound_range),
		},
		{
			.offset = CODEX_RUSTLS_SEND_PLAIN_OFFSET,
			.data = codex_rustls_send_plain_prefix,
			.len = sizeof(codex_rustls_send_plain_prefix),
		},
		{
			.offset = CODEX_RUSTLS_SEND_DATA_OFFSET,
			.data = codex_rustls_send_data_pointer,
			.len = sizeof(codex_rustls_send_data_pointer),
		},
	};

	return rustls_find_plaintext_offset(
		binary_path, codex_rustls_buffer_plaintext_prefix,
		sizeof(codex_rustls_buffer_plaintext_prefix), blocks,
		sizeof(blocks) / sizeof(blocks[0]), offset);
}

static bool codex_buf_contains(const uint8_t *buf, size_t len,
			       const char *needle)
{
	size_t needle_len = strlen(needle);

	return needle_len > 0 && len >= needle_len
	       && codex_find_pattern(buf, len, (const uint8_t *)needle,
				     needle_len) != (size_t)-1;
}

static bool binary_has_rustls_markers(const char *binary_path,
				      const char *marker_a,
				      const char *marker_b)
{
	uint8_t buf[8192 + 32];
	bool has_agent = false;
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
		has_agent |= codex_buf_contains(buf, len, marker_a)
			     || (marker_b
				 && codex_buf_contains(buf, len, marker_b));
		has_rustls |= codex_buf_contains(buf, len, "rustls");
		if (has_agent && has_rustls) {
			close(fd);
			return true;
		}
		carry = len < 32 ? len : 32;
		memmove(buf, buf + len - carry, carry);
	}
	close(fd);
	return false;
}

static bool codex_binary_has_tls_markers(const char *binary_path)
{
	return binary_has_rustls_markers(binary_path, "codex-cli",
					 "@openai/codex");
}

static bool grok_binary_has_tls_markers(const char *binary_path)
{
	return binary_has_rustls_markers(binary_path, "grok-cli", NULL);
}

#endif
