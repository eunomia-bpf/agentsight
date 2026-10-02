/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#ifndef AGENTSIGHT_SSLSNIFF_OUTPUT_H
#define AGENTSIGHT_SSLSNIFF_OUTPUT_H

#include "jsonl.h"

/*
 * The readable JSON string cannot round-trip arbitrary TLS plaintext. In
 * particular, a valid UTF-8 byte sequence in an HPACK block is decoded as a
 * Unicode character by JSON readers. Always include exact bytes so protocol
 * parsers can use data_hex instead of trying to reconstruct bytes from data.
 */
static inline void sslsniff_print_payload_fields(const char *buf,
						  unsigned int len)
{
	printf("\"data\":");
	json_print_escaped_quoted(buf, len);
	printf(",\"data_hex\":\"");
	for (unsigned int i = 0; i < len; i++)
		printf("%02x", (unsigned char)buf[i]);
	printf("\",");
}

#endif /* AGENTSIGHT_SSLSNIFF_OUTPUT_H */
