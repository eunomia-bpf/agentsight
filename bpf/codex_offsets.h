// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Codex CLI release fingerprints and SSL entrypoint offsets.
#ifndef __CODEX_OFFSETS_H
#define __CODEX_OFFSETS_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#define CODEX_HEAD_FINGERPRINT_SIZE 65536

struct codex_ssl_offsets {
	size_t ssl_write;
	size_t ssl_read;
	size_t ssl_do_handshake;
	bool write_is_ex;
	bool read_is_ex;
	bool found;
	const char *version;
};

struct codex_offset_entry {
	const char *version;
	off_t file_size;
	uint8_t head_sha256[32];
	size_t ssl_write;
	size_t ssl_read;
	size_t ssl_do_handshake;
	bool write_is_ex;
	bool read_is_ex;
};

static const struct codex_offset_entry codex_offset_table[] = {
	{
		.version = "0.142.5",
		.file_size = 285929520,
		.head_sha256 = {
			0xf0, 0xaa, 0xc9, 0x54, 0x9a, 0x69, 0x82, 0xa2,
			0xd2, 0x9d, 0xb2, 0x03, 0x6b, 0xe7, 0x7e, 0xfe,
			0x30, 0xed, 0x01, 0xb4, 0xcf, 0x8a, 0x91, 0x21,
			0x94, 0x53, 0xb1, 0x79, 0x59, 0x41, 0x9b, 0x5f,
		},
		.ssl_write = 218231264,
		.ssl_read = 218230672,
		.ssl_do_handshake = 218228992,
		.write_is_ex = true,
		.read_is_ex = true,
	},
	{
		.version = "0.141.0",
		.file_size = 276579568,
		.head_sha256 = {
			0xf0, 0x15, 0xdd, 0xd2, 0xa6, 0x87, 0xc1, 0xfc,
			0x0b, 0x3c, 0xe7, 0x0d, 0x89, 0x8c, 0x0a, 0x68,
			0xee, 0xab, 0x88, 0xad, 0x00, 0x40, 0xe7, 0x9b,
			0x0f, 0xe4, 0x9a, 0x85, 0x45, 0xff, 0x52, 0xa9,
		},
		.ssl_write = 210691872,
		.ssl_read = 210691280,
		.ssl_do_handshake = 210689600,
		.write_is_ex = true,
		.read_is_ex = true,
	},
	{
		.version = "0.137.0",
		.file_size = 227758400,
		.head_sha256 = {
			0x49, 0xb0, 0xa1, 0xc3, 0xa8, 0x31, 0x07, 0x1e,
			0x97, 0x66, 0xcd, 0x0d, 0xb8, 0x35, 0x37, 0xa5,
			0x27, 0x0a, 0x37, 0x4f, 0x8a, 0xc1, 0x17, 0x83,
			0x26, 0x4a, 0x5a, 0x35, 0x4c, 0x3b, 0x54, 0x4a,
		},
		.ssl_write = 172964768,
		.ssl_read = 172964176,
		.ssl_do_handshake = 172962496,
		.write_is_ex = true,
		.read_is_ex = true,
	},
};

struct codex_sha256_ctx {
	uint32_t state[8];
	uint64_t bit_len;
	uint8_t data[64];
	size_t data_len;
};

static inline uint32_t codex_rotr32(uint32_t x, uint32_t n)
{
	return (x >> n) | (x << (32 - n));
}

static void codex_sha256_transform(struct codex_sha256_ctx *ctx,
				   const uint8_t data[64])
{
	static const uint32_t k[64] = {
		0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
		0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
		0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
		0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
		0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
		0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
		0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
		0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
		0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
		0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
		0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
		0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
		0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
		0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
		0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
		0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
	};
	uint32_t a, b, c, d, e, f, g, h, t1, t2, m[64];

	for (int i = 0; i < 16; i++) {
		m[i] = ((uint32_t)data[i * 4] << 24) |
		       ((uint32_t)data[i * 4 + 1] << 16) |
		       ((uint32_t)data[i * 4 + 2] << 8) |
		       ((uint32_t)data[i * 4 + 3]);
	}
	for (int i = 16; i < 64; i++) {
		uint32_t s0 = codex_rotr32(m[i - 15], 7) ^
			      codex_rotr32(m[i - 15], 18) ^ (m[i - 15] >> 3);
		uint32_t s1 = codex_rotr32(m[i - 2], 17) ^
			      codex_rotr32(m[i - 2], 19) ^ (m[i - 2] >> 10);
		m[i] = m[i - 16] + s0 + m[i - 7] + s1;
	}

	a = ctx->state[0];
	b = ctx->state[1];
	c = ctx->state[2];
	d = ctx->state[3];
	e = ctx->state[4];
	f = ctx->state[5];
	g = ctx->state[6];
	h = ctx->state[7];

	for (int i = 0; i < 64; i++) {
		uint32_t s1 = codex_rotr32(e, 6) ^ codex_rotr32(e, 11) ^
			      codex_rotr32(e, 25);
		uint32_t ch = (e & f) ^ (~e & g);
		uint32_t s0 = codex_rotr32(a, 2) ^ codex_rotr32(a, 13) ^
			      codex_rotr32(a, 22);
		uint32_t maj = (a & b) ^ (a & c) ^ (b & c);

		t1 = h + s1 + ch + k[i] + m[i];
		t2 = s0 + maj;
		h = g;
		g = f;
		f = e;
		e = d + t1;
		d = c;
		c = b;
		b = a;
		a = t1 + t2;
	}

	ctx->state[0] += a;
	ctx->state[1] += b;
	ctx->state[2] += c;
	ctx->state[3] += d;
	ctx->state[4] += e;
	ctx->state[5] += f;
	ctx->state[6] += g;
	ctx->state[7] += h;
}

static void codex_sha256_init(struct codex_sha256_ctx *ctx)
{
	ctx->data_len = 0;
	ctx->bit_len = 0;
	ctx->state[0] = 0x6a09e667;
	ctx->state[1] = 0xbb67ae85;
	ctx->state[2] = 0x3c6ef372;
	ctx->state[3] = 0xa54ff53a;
	ctx->state[4] = 0x510e527f;
	ctx->state[5] = 0x9b05688c;
	ctx->state[6] = 0x1f83d9ab;
	ctx->state[7] = 0x5be0cd19;
}

static void codex_sha256_update(struct codex_sha256_ctx *ctx,
				const uint8_t *data, size_t len)
{
	for (size_t i = 0; i < len; i++) {
		ctx->data[ctx->data_len++] = data[i];
		if (ctx->data_len == 64) {
			codex_sha256_transform(ctx, ctx->data);
			ctx->bit_len += 512;
			ctx->data_len = 0;
		}
	}
}

static void codex_sha256_final(struct codex_sha256_ctx *ctx, uint8_t hash[32])
{
	size_t i = ctx->data_len;

	ctx->data[i++] = 0x80;
	if (i > 56) {
		while (i < 64)
			ctx->data[i++] = 0;
		codex_sha256_transform(ctx, ctx->data);
		i = 0;
	}
	while (i < 56)
		ctx->data[i++] = 0;

	ctx->bit_len += ctx->data_len * 8;
	for (int j = 0; j < 8; j++)
		ctx->data[63 - j] = (uint8_t)(ctx->bit_len >> (j * 8));
	codex_sha256_transform(ctx, ctx->data);

	for (int j = 0; j < 8; j++) {
		hash[j * 4] = (uint8_t)(ctx->state[j] >> 24);
		hash[j * 4 + 1] = (uint8_t)(ctx->state[j] >> 16);
		hash[j * 4 + 2] = (uint8_t)(ctx->state[j] >> 8);
		hash[j * 4 + 3] = (uint8_t)ctx->state[j];
	}
}

static bool codex_head_sha256(int fd, uint8_t hash[32])
{
	struct codex_sha256_ctx ctx;
	uint8_t buf[4096];
	size_t remaining = CODEX_HEAD_FINGERPRINT_SIZE;

	if (lseek(fd, 0, SEEK_SET) < 0)
		return false;

	codex_sha256_init(&ctx);
	while (remaining > 0) {
		size_t want = remaining < sizeof(buf) ? remaining : sizeof(buf);
		ssize_t n = read(fd, buf, want);

		if (n < 0) {
			if (errno == EINTR)
				continue;
			return false;
		}
		if (n == 0)
			break;
		codex_sha256_update(&ctx, buf, (size_t)n);
		remaining -= (size_t)n;
	}
	codex_sha256_final(&ctx, hash);
	return true;
}

static bool codex_find_ssl_offsets(const char *binary_path,
				   struct codex_ssl_offsets *out)
{
	struct stat st;
	uint8_t hash[32];
	int fd;

	memset(out, 0, sizeof(*out));
	fd = open(binary_path, O_RDONLY);
	if (fd < 0)
		return false;
	if (fstat(fd, &st) < 0 || !codex_head_sha256(fd, hash)) {
		close(fd);
		return false;
	}
	close(fd);

	for (size_t i = 0; i < sizeof(codex_offset_table) / sizeof(codex_offset_table[0]); i++) {
		const struct codex_offset_entry *entry = &codex_offset_table[i];

		if (st.st_size != entry->file_size)
			continue;
		if (memcmp(hash, entry->head_sha256, sizeof(hash)) != 0)
			continue;
		out->ssl_write = entry->ssl_write;
		out->ssl_read = entry->ssl_read;
		out->ssl_do_handshake = entry->ssl_do_handshake;
		out->write_is_ex = entry->write_is_ex;
		out->read_is_ex = entry->read_is_ex;
		out->found = true;
		out->version = entry->version;
		return true;
	}
	return false;
}

static bool codex_buf_contains(const uint8_t *buf, size_t len,
			       const char *needle)
{
	size_t needle_len = strlen(needle);

	if (needle_len == 0 || len < needle_len)
		return false;
	for (size_t i = 0; i <= len - needle_len; i++) {
		if (memcmp(buf + i, needle, needle_len) == 0)
			return true;
	}
	return false;
}

static bool codex_binary_has_tls_markers(const char *binary_path)
{
	static const char *markers[] = {
		"codex-cli",
		"@openai/codex",
		"rustls",
		"aws-lc",
		"aws_lc",
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
			close(fd);
			return false;
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

#endif /* __CODEX_OFFSETS_H */
