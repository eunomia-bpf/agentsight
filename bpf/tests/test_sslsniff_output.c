/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "sslsniff_output.h"

static void assert_payload_output(const unsigned char *payload, unsigned int len,
				  const char *expected_hex)
{
	char output[256] = {0};
	FILE *capture = tmpfile();
	assert(capture);
	fflush(stdout);
	int saved_stdout = dup(STDOUT_FILENO);
	assert(saved_stdout >= 0);
	assert(dup2(fileno(capture), STDOUT_FILENO) >= 0);

	sslsniff_print_payload_fields((const char *)payload, len);
	fflush(stdout);
	assert(dup2(saved_stdout, STDOUT_FILENO) >= 0);
	close(saved_stdout);
	assert(fseek(capture, 0, SEEK_SET) == 0);
	size_t size = fread(output, 1, sizeof(output) - 1, capture);
	assert(!ferror(capture));
	output[size] = '\0';
	fclose(capture);

	assert(strncmp(output, "\"data\":", 7) == 0);
	assert(strstr(output, expected_hex));
}

int main(void)
{
	/* HPACK can contain valid UTF-8 octets that JSON merges into one codepoint. */
	const unsigned char hpack[] = {0x00, 0xc3, 0xa9, 0xff, 0x22};
	assert_payload_output(hpack, sizeof(hpack),
			      "\"data_hex\":\"00c3a9ff22\",");
	const unsigned char ascii[] = {'G', 'E', 'T'};
	assert_payload_output(ascii, sizeof(ascii), "\"data_hex\":\"474554\",");
	puts("SSL payload JSON retains exact bytes for binary and text data");
	return 0;
}
