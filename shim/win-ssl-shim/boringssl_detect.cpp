// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// boringssl_detect.cpp -- port of bpf/sslsniff.c's BoringSSL byte-pattern
// detector for statically-linked / stripped binaries (Bun, Node, Claude embed
// BoringSSL with no exported SSL_* symbols). On Windows we scan the loaded
// module image in memory and return absolute function pointers.
//
// NOTE: the Linux detector scans the on-disk file; here we scan the mapped
// image. The function-prologue patterns live in .text either way, and the
// relative deltas between SSL_do_handshake/SSL_read/SSL_write hold within the
// embedded BoringSSL .text, so the same heuristic applies. The independent
// fallback search covers layout differences.
#include <windows.h>
#include <cstring>
#include <cstdint>

// x86-64 function-prologue patterns, identical to bpf/sslsniff.c.
static const unsigned char handshake_pat[] = {
    0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
    0x41, 0x55, 0x41, 0x54, 0x53, 0x48, 0x83, 0xec,
    0x28, 0x49, 0x89, 0xfc, 0x48, 0x8b, 0x47, 0x30
};
static const unsigned char read_pat[] = {
    0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
    0x53, 0x50, 0x48, 0x83, 0xbf, 0x98, 0x00, 0x00,
    0x00, 0x00, 0x74
};
static const unsigned char write_pat[] = {
    0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
    0x41, 0x55, 0x41, 0x54, 0x53, 0x48, 0x83, 0xec,
    0x18, 0x41, 0x89, 0xd7, 0x49, 0x89, 0xf6, 0x48,
    0x89, 0xfb
};
static const size_t WRITE_READ_DELTA = 0xCA0;

static size_t find_pattern(const unsigned char* data, size_t len,
                           const unsigned char* pat, size_t pat_len) {
    if (pat_len == 0 || len < pat_len) return (size_t)-1;
    for (size_t i = 0; i + pat_len <= len; ++i)
        if (memcmp(data + i, pat, pat_len) == 0) return i;
    return (size_t)-1;
}

bool boringssl_find_patterns(void* module_base, size_t module_size,
                             void** ssl_read, void** ssl_write) {
    const unsigned char* base = static_cast<const unsigned char*>(module_base);

    size_t read_off = find_pattern(base, module_size, read_pat, sizeof(read_pat));
    if (read_off == (size_t)-1) return false;

    // SSL_write at expected relative position, else search a window around read.
    size_t wr = read_off + WRITE_READ_DELTA;
    if (!(wr + sizeof(write_pat) <= module_size &&
          memcmp(base + wr, write_pat, sizeof(write_pat)) == 0)) {
        size_t start = read_off > 0x10000 ? read_off - 0x10000 : 0;
        size_t end = read_off + 0x10000;
        if (end > module_size) end = module_size;
        size_t off = find_pattern(base + start, end - start, write_pat, sizeof(write_pat));
        if (off == (size_t)-1) return false;
        wr = start + off;
    }

    *ssl_read  = const_cast<unsigned char*>(base + read_off);
    *ssl_write = const_cast<unsigned char*>(base + wr);
    return true;
}
