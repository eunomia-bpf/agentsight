// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// Shared contract between the AgentSight SSL shim DLL and its launcher.
#pragma once

// The launcher creates a named pipe and passes its name to the injected DLL via
// this environment variable. The DLL connects and streams JSONL records to it;
// the launcher relays them to its own stdout, which the Rust collector reads.
#define AS_SHIM_PIPE_ENV "AGENTSIGHT_SSL_PIPE"

// rw codes match bpf/sslsniff.c's rw_event[] ordering.
enum as_rw {
    AS_RW_READ      = 0, // "READ/RECV"
    AS_RW_WRITE     = 1, // "WRITE/SEND"
    AS_RW_HANDSHAKE = 2, // "HANDSHAKE"
};

// Max plaintext bytes captured per call (matches MAX_BUF_SIZE = 512 KB).
#define AS_MAX_BUF_SIZE (512 * 1024)
