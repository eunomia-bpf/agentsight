/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * jsonl.h — shared JSONL emit helpers for AgentSight userspace loaders.
 *
 * Every eBPF userspace program (sslsniff, stdiocap, process) emits one JSON
 * object per line on stdout. This header is the single owner of JSON string
 * escaping so a malformed escape cannot corrupt the JSONL stream in one
 * program but not another.
 */
#ifndef AGENTSIGHT_JSONL_H
#define AGENTSIGHT_JSONL_H

#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

/*
 * Validate a UTF-8 sequence starting at str. Returns the sequence length in
 * bytes, or 0 when invalid (bad start byte, truncated, overlong encoding,
 * surrogate, or out-of-range code point). Requires a UTF-8 locale to be set
 * by the caller's main() for mbrtowc().
 */
static inline int validate_utf8_char(const unsigned char *str, size_t remaining)
{
	unsigned char c;
	int expected_len = 0;
	char temp[5] = {0};
	wchar_t wc;
	mbstate_t state;
	size_t result;

	if (!str || remaining == 0)
		return 0;

	c = str[0];
	if (c < 0x80)
		return 1;

	if ((c & 0xE0) == 0xC0)
		expected_len = 2;
	else if ((c & 0xF0) == 0xE0)
		expected_len = 3;
	else if ((c & 0xF8) == 0xF0)
		expected_len = 4;
	else
		return 0;

	if (remaining < (size_t)expected_len)
		return 0;

	memcpy(temp, str, expected_len > 4 ? 4 : expected_len);
	memset(&state, 0, sizeof(state));
	result = mbrtowc(&wc, temp, expected_len, &state);
	if (result == (size_t)-1 || result == (size_t)-2 || result == 0)
		return 0;

	if (expected_len == 2) {
		unsigned int codepoint = ((c & 0x1F) << 6) | (str[1] & 0x3F);

		if (codepoint < 0x80)
			return 0; /* overlong */
	} else if (expected_len == 3) {
		unsigned int codepoint = ((c & 0x0F) << 12) |
					 ((str[1] & 0x3F) << 6) |
					 (str[2] & 0x3F);

		if (codepoint < 0x800)
			return 0; /* overlong */
		if (codepoint >= 0xD800 && codepoint <= 0xDFFF)
			return 0; /* surrogate */
	} else if (expected_len == 4) {
		unsigned int codepoint = ((c & 0x07) << 18) |
					 ((str[1] & 0x3F) << 12) |
					 ((str[2] & 0x3F) << 6) |
					 (str[3] & 0x3F);

		if (codepoint < 0x10000 || codepoint > 0x10FFFF)
			return 0;
	}

	return expected_len;
}

/*
 * Stream buf as JSON string contents (no surrounding quotes) to stdout.
 * Valid UTF-8 passes through; control characters and invalid bytes are
 * \uXXXX-escaped so the output line stays valid JSON for any input.
 */
static inline void json_print_escaped(const char *buf, unsigned int len)
{
	unsigned int i;

	for (i = 0; i < len; i++) {
		unsigned char c = buf[i];

		if (c == '"' || c == '\\')
			printf("\\%c", c);
		else if (c == '\n')
			printf("\\n");
		else if (c == '\r')
			printf("\\r");
		else if (c == '\t')
			printf("\\t");
		else if (c == '\b')
			printf("\\b");
		else if (c == '\f')
			printf("\\f");
		else if (c >= 32 && c <= 126)
			printf("%c", c);
		else if (c >= 128) {
			int utf8_len = validate_utf8_char(
				(const unsigned char *)&buf[i], len - i);
			if (utf8_len > 0) {
				int j;

				for (j = 0; j < utf8_len; j++)
					printf("%c", buf[i + j]);
				i += utf8_len - 1;
			} else {
				printf("\\u%04x", c);
			}
		} else {
			printf("\\u%04x", c);
		}
	}
}

/* Same as json_print_escaped but wrapped in double quotes. */
static inline void json_print_escaped_quoted(const char *buf, unsigned int len)
{
	printf("\"");
	json_print_escaped(buf, len);
	printf("\"");
}

/*
 * Escape a NUL-terminated string into dst for embedding in a JSON string
 * (minimal set: backslash, quote, newline, tab). Used where output is
 * composed into a fixed buffer instead of streamed.
 */
static inline void json_escape(const char *src, char *dst, size_t dst_size)
{
	size_t j = 0;

	for (size_t i = 0; src[i] && j < dst_size - 2; i++) {
		switch (src[i]) {
		case '\\': if (j + 2 < dst_size) { dst[j++] = '\\'; dst[j++] = '\\'; } break;
		case '"':  if (j + 2 < dst_size) { dst[j++] = '\\'; dst[j++] = '"'; } break;
		case '\n': if (j + 2 < dst_size) { dst[j++] = '\\'; dst[j++] = 'n'; } break;
		case '\t': if (j + 2 < dst_size) { dst[j++] = '\\'; dst[j++] = 't'; } break;
		default:   dst[j++] = src[i]; break;
		}
	}
	dst[j] = '\0';
}

#endif /* AGENTSIGHT_JSONL_H */
