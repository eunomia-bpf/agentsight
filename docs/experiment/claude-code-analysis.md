# Claude Code CLI: Architecture Analysis & SSL Monitoring

This document records the complete reverse
 engineering process of the Claude
Code CLI binary, every approach attempted, commands executed, failures
encountered, and the current status of SSL traffic interception.

**Target**: Claude Code v2.1.39
**Date**: 2026-02-13
**Platform**: Linux x86-64 (kernel 6.15.11)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 1: Initial Reconnaissance](#phase-1-initial-reconnaissance)
3. [Phase 2: Understanding Why Standard Hooking Fails](#phase-2-understanding-why-standard-hooking-fails)
4. [Phase 3: Identifying the Runtime](#phase-3-identifying-the-runtime)
5. [Phase 4: Finding BoringSSL Function Offsets](#phase-4-finding-boringssl-function-offsets)
6. [Phase 5: Implementing Byte-Pattern Detection](#phase-5-implementing-byte-pattern-detection)
7. [Phase 6: Testing — Partial Success](#phase-6-testing--partial-success)
8. [Phase 7: The Two-Path TLS Problem](#phase-7-the-two-path-tls-problem)
9. [Phase 8: Deep Investigation of the Native Fetch TLS Path](#phase-8-deep-investigation-of-the-native-fetch-tls-path)
10. [Phase 9: Breakthrough — Full /v1/messages Capture](#phase-9-breakthrough--full-v1messages-capture)
11. [Current Status & Next Steps](#current-status--next-steps)
12. [Appendix: Claude Binary Architecture](#appendix-claude-binary-architecture)

---

## Executive Summary

Claude Code CLI is a **Bun v1.3.9-canary** application with **BoringSSL**
statically linked and symbols stripped. We successfully modified `sslsniff` to
auto-detect BoringSSL functions via byte-pattern matching and can now capture
**ALL SSL/TLS traffic** including the conversation API (`/v1/messages`).

### What works

| Traffic Type | Endpoint | HTTP Client | Captured? |
|---|---|---|---|
| Heartbeat | `GET /api/hello` | axios/1.8.4 | YES |
| Telemetry | `POST /api/event_logging/batch` | axios/1.8.4 | YES |
| Datadog logs | `POST /api/v2/logs` | axios/1.8.4 | YES |
| **Conversation API** | **POST /v1/messages?beta=true** | **Bun native fetch** | **YES** |

All traffic flows through a single **HTTP Client** thread via BoringSSL
`SSL_write`/`SSL_read`. The initial hypothesis that Bun's native `fetch()`
used a separate TLS path was incorrect — it uses the same BoringSSL functions
through uSockets. Earlier test captures missed `/v1/messages` due to timing
(no new messages were submitted during the capture window).

### Captured data includes

- **Request**: Full HTTP headers (Authorization, anthropic-beta, etc.) and JSON body (model, messages array, system prompt)
- **Response**: Complete SSE streaming events (message_start, content_block_delta with text/tool_use, message_stop)
- **Protocol**: HTTP/1.1 over TLS (not HTTP/2)

---

## Phase 1: Initial Reconnaissance

### Goal

Determine if the existing `sslsniff` can monitor Claude out of the box.

### Commands & Results

```bash
# Check if claude is running
$ ps aux | grep claude
yunwei37  847282 14.8  0.6 75318520 838308 pts/7 Rl+ claude

# Try standard sslsniff with comm filter
$ sudo timeout 10 ./bpf/sslsniff -c claude
# Result: NO OUTPUT — nothing captured in 10 seconds

# Check sslsniff help for relevant options
$ sudo ./bpf/sslsniff -h
# Lists: -p PID, -c COMMAND, --binary-path PATH, etc.
```

**Result**: Standard sslsniff captures nothing from claude processes.

### Root Cause Investigation

```bash
# Check claude binary type
$ file ~/.local/share/claude/versions/2.1.39
ELF 64-bit LSB executable, x86-64, dynamically linked

# Check dynamic library dependencies
$ ldd ~/.local/share/claude/versions/2.1.39
    libc.so.6
    libpthread.so.0
    libdl.so.2
    libm.so.6
    libstdc++.so.6.0.33
    libgcc_s.so.1
# NOTE: NO libssl.so or libcrypto.so!

# Check loaded libraries at runtime
$ sudo cat /proc/847282/maps | grep "\.so" | awk '{print $NF}' | sort -u
    /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
    /usr/lib/x86_64-linux-gnu/libc.so.6
    /usr/lib/x86_64-linux-gnu/libdl.so.2
    /usr/lib/x86_64-linux-gnu/libgcc_s.so.1
    /usr/lib/x86_64-linux-gnu/libm.so.6
    /usr/lib/x86_64-linux-gnu/libnss_mdns4_minimal.so.2
    /usr/lib/x86_64-linux-gnu/libpthread.so.0
    /usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33
# CONFIRMED: no SSL library loaded at runtime either
```

**Conclusion**: Claude uses a statically-linked SSL library embedded in the binary.

---

## Phase 2: Understanding Why Standard Hooking Fails

### Attempt: Use --binary-path to hook SSL in the Claude binary directly

```bash
$ sudo ./bpf/sslsniff -c claude \
    --binary-path ~/.local/share/claude/versions/2.1.39
# ERROR:
# libbpf: elf: 'SSL_write' is 0 in symtab for '...2.1.39':
#   try using shared library path instead
# no program attached for probe_SSL_rw_enter: No such file or directory
```

**Why it fails**: sslsniff uses `bpf_program__attach_uprobe_opts` with
`.func_name = "SSL_write"`, which searches the binary's symbol table. Since
all SSL symbols are stripped, the lookup returns offset 0 and libbpf rejects it.

### Verify: Are SSL symbols really stripped?

```bash
# Check static symbol table
$ readelf -s ~/.local/share/claude/versions/2.1.39 | grep -i "ssl_write\|ssl_read"
# (no output)

# Check dynamic symbol table
$ readelf --dyn-syms ~/.local/share/claude/versions/2.1.39 | grep -i ssl
# (no output)

# Use gdb to search
$ sudo gdb -batch -p 847282 -ex "info functions SSL"
# All functions matching regular expression "SSL":
# (no results)
```

**Confirmed**: All SSL/BoringSSL symbols are completely stripped from the binary.

---

## Phase 3: Identifying the Runtime

### Discovering Bun

```bash
# Search for runtime identification strings
$ strings ~/.local/share/claude/versions/2.1.39 | grep "node_module_register"
node_module_register
# → Uses Node.js API

$ strings ~/.local/share/claude/versions/2.1.39 | grep "bun-vfs"
/bun-vfs$$/node_modules/crypto/index.js
# → Uses Bun virtual filesystem!

$ strings ~/.local/share/claude/versions/2.1.39 | grep "Bun v"
Bun v1.3.9-canary.51+d5628db23 (Linux x64 baseline)
# → Exact Bun version identified
```

### Discovering BoringSSL

```bash
$ strings ~/.local/share/claude/versions/2.1.39 | grep "boring"
BoringSSLError
openssl_is_boringssl
../../../vendor/boringssl/ssl/ssl_buffer.cc
../../../vendor/boringssl/ssl/ssl_lib.cc
../../../vendor/boringssl/crypto/fipsmodule/bn/...
# (many more BoringSSL source paths)
```

### Exported symbols confirm Bun

```bash
$ readelf -s ~/.local/share/claude/versions/2.1.39 | grep "BUN_1.2" | grep "FUNC" | wc -l
556
# 556 exported functions with BUN_1.2 version tag
# Includes: uv_write, uv_read_start, napi_*, v8::* etc.
```

### Binary Properties Summary

| Property | Value |
|---|---|
| Binary path | `~/.local/share/claude/versions/2.1.39` |
| Symlink target | `/home/yunwei37/.local/share/claude/versions/2.1.39` |
| File size | 222,867,057 bytes (~213 MB) |
| Runtime | Bun v1.3.9-canary.51+d5628db23 |
| Build variant | Linux x64 baseline |
| SSL library | BoringSSL (statically linked, fully stripped) |
| Exported symbols | 556 functions (BUN_1.2), 981 dynamic symbols total |
| USDT probes | 3 (libstdcxx: catch, throw, rethrow — not useful for SSL) |

---

## Phase 4: Finding BoringSSL Function Offsets

### Strategy: Cross-reference with Bun profile build

Since Bun is open-source, release builds include a "profile" variant with
debug symbols. The function code is identical between profile and stripped
builds; only symbols differ.

### Step 1: Download the matching profile build

```bash
# List available assets for bun v1.3.9
$ gh release view bun-v1.3.9 --repo oven-sh/bun --json assets \
    --jq '.assets[].name' | grep linux-x64
bun-linux-x64-baseline-profile.zip   # <-- This one (Claude uses "baseline")
bun-linux-x64-baseline.zip
bun-linux-x64-profile.zip
bun-linux-x64.zip

# Download the baseline profile build
$ gh release download bun-v1.3.9 --repo oven-sh/bun \
    --pattern "bun-linux-x64-baseline-profile.zip"
$ unzip bun-linux-x64-baseline-profile.zip
```

### Step 2: Extract SSL function symbols from the profile build

```bash
$ readelf -s bun-profile | grep -E " SSL_write$| SSL_read$| SSL_do_handshake$"
 97928: 0000000005f3fe00   379 FUNC    LOCAL  HIDDEN    16 SSL_write
 97985: 0000000005f3ea70  1506 FUNC    LOCAL  HIDDEN    16 SSL_do_handshake
 97988: 0000000005f3f160   247 FUNC    LOCAL  HIDDEN    16 SSL_read
```

### Step 3: Calculate file offsets from virtual addresses

The profile build's ELF program headers:

```
LOAD  offset=0x000000  VA=0x200000   size=0x28dfef0  (R)    ← data
LOAD  offset=0x28dff00 VA=0x2ae0f00  size=0x38c80f0  (R E)  ← code
```

Conversion formula: `file_offset = (VA - seg_VA) + seg_file_offset`

```python
# Profile build function file offsets:
SSL_write:        VA=0x5f3fe00 → FileOff=0x5d3ee00
SSL_read:         VA=0x5f3f160 → FileOff=0x5d3e160
SSL_do_handshake: VA=0x5f3ea70 → FileOff=0x5d3da70
```

### Step 4: Extract function byte prologues

```bash
$ xxd -s 0x5d3ee00 -l 48 bun-profile  # SSL_write
05d3ee00: 5548 89e5 4157 4156 4155 4154 5348 83ec
05d3ee10: 1841 89d7 4989 f648 89fb 488b 4730 c780

$ xxd -s 0x5d3e160 -l 48 bun-profile  # SSL_read
05d3e160: 5548 89e5 4157 4156 5350 4883 bf98 0000
05d3e170: 0000 742b baf3 5a31 00bf 1000 0000 be42

$ xxd -s 0x5d3da70 -l 48 bun-profile  # SSL_do_handshake
05d3da70: 5548 89e5 4157 4156 4155 4154 5348 83ec
05d3da80: 2849 89fc 488b 4730 c780 c400 0000 0000
```

### Step 5: Search for patterns in the Claude binary

```python
# Python script using mmap to search for byte patterns
# SSL_write pattern (26 bytes):
#   55 48 89 e5 41 57 41 56 41 55 41 54 53 48 83 ec
#   18 41 89 d7 49 89 f6 48 89 fb
#
# Result: 13 matches (many false positives from common prologues)
# Last match at 0x5c39b20 — closest to SSL_read match

# SSL_read pattern (19 bytes):
#   55 48 89 e5 41 57 41 56 53 50 48 83 bf 98 00 00
#   00 00 74
#
# Result: 1 match at 0x5c38e80 ← unique!

# SSL_do_handshake pattern (24 bytes):
#   55 48 89 e5 41 57 41 56 41 55 41 54 53 48 83 ec
#   28 49 89 fc 48 8b 47 30
#
# Result: 1 match at 0x5c38790 ← unique!
```

### Step 6: Validate with relative distances

```
=== Profile build relative distances ===
read - handshake = 0x6F0 (1776 bytes)
write - read     = 0xCA0 (3232 bytes)

=== Claude binary relative distances ===
read - handshake = 0x6F0 (1776 bytes)  ← IDENTICAL
write - read     = 0xCA0 (3232 bytes)  ← IDENTICAL

*** PERFECT MATCH ***
```

### Step 7: Verify byte-level match

```bash
# Compare 128 bytes of SSL_write between profile and Claude
$ xxd -s 0x5d3ee00 -l 128 bun-profile
$ xxd -s 0x5c39b20 -l 128 claude-binary

# Result: nearly identical! Only address references differ
# (expected, since binaries are linked at different addresses)
```

### Final verified offsets in Claude binary

```
SSL_do_handshake: 0x5c38790
SSL_read:         0x5c38e80
SSL_write:        0x5c39b20
```

---

## Phase 5: Implementing Byte-Pattern Detection

### Changes to sslsniff.c

Added three components:

#### 1. Offset-based uprobe macros

```c
#define __ATTACH_UPROBE_OFFSET(skel, binary_path, offset, prog_name, is_retprobe) \
    do {                                                                          \
      LIBBPF_OPTS(bpf_uprobe_opts, uprobe_opts, .retprobe = is_retprobe);         \
      skel->links.prog_name = bpf_program__attach_uprobe_opts(                    \
          skel->progs.prog_name, env.pid, binary_path, offset, &uprobe_opts);     \
    } while (false)
```

Key difference from symbol-based macro: `func_name` is omitted (NULL), and
the `offset` parameter is passed directly as the file offset.

#### 2. `find_boringssl_offsets()` function

- Opens the target binary with `mmap()`
- Searches for three unique byte patterns (SSL_read → SSL_do_handshake → SSL_write)
- Validates matches using known relative distances (0x6F0 and 0xCA0)
- Falls back to broader search if distances don't match

#### 3. Two-stage `--binary-path` handler

```c
// First: try symbol-based attachment
struct bpf_link *test_link = bpf_program__attach_uprobe_opts(..., "SSL_write", ...);
if (test_link) {
    // Standard path: symbols available
    attach_openssl(obj, env.extra_lib);
} else {
    // Fallback: pattern detection for stripped binaries
    struct boringssl_offsets offsets = find_boringssl_offsets(env.extra_lib);
    if (offsets.found) {
        attach_openssl_by_offset(obj, env.extra_lib, &offsets);
    }
}
```

### Build & Test

```bash
$ make -C bpf
# Compiles successfully with no errors

$ cd collector && cargo build --release
# Builds successfully

$ cd bpf && make test
# 24/24 C tests passed

$ cd collector && cargo test
# 89/89 Rust tests passed
```

---

## Phase 6: Testing — Partial Success

### Verbose output confirms BoringSSL detection

```bash
$ sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39 --verbose
# stderr output:
Attaching to binary: /home/yunwei37/.local/share/claude/versions/2.1.39
Symbols not found, trying BoringSSL pattern detection...
BoringSSL detected in /home/yunwei37/.local/share/claude/versions/2.1.39:
  SSL_do_handshake offset: 0x5c38790
  SSL_read offset:         0x5c38e80
  SSL_write offset:        0x5c39b20
BoringSSL detected! Attaching by offset...
```

### First capture: telemetry traffic

```bash
$ sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39
```

Captured 3 events within seconds:

```json
{"function":"WRITE/SEND","comm":"HTTP Client","pid":847282,
 "data":"GET /api/hello HTTP/1.1\r\nHost: api.anthropic.com\r\nUser-Agent: axios/1.8.4\r\n\r\n"}

{"function":"READ/RECV","comm":"HTTP Client","pid":847282,
 "data":"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n..."}

{"function":"READ/RECV","comm":"HTTP Client","pid":847282,
 "data":"0\r\n\r\n"}
```

### Extended capture (8 seconds): more traffic including event logging

Captured POST to `/api/event_logging/batch` with full telemetry data including:
- Session IDs, device IDs
- Event types: `tengu_permission_request_option_selected`, `tengu_unary_event`, etc.
- Model information: `claude-opus-4-6`
- Growthbook experiment events
- Cost threshold events

### Failure: `--comm claude` filter doesn't work

```bash
$ sudo ./bpf/sslsniff -c claude --binary-path ~/.local/share/claude/versions/2.1.39
# NO OUTPUT for 20 seconds
```

**Root cause**: SSL traffic comes from thread named `HTTP Client`, not `claude`.
The eBPF `bpf_get_current_comm()` returns the **thread** name, not the process
name. Bun's HTTP client runs in a separate thread.

**Fix**: Omit the `-c` filter when monitoring Claude, or the collector should
not pass `--comm` for the SSL runner when using `--binary-path`.

---

## Phase 7: The Two-Path TLS Problem

### Discovery: No `/v1/messages` API calls captured

After 60 seconds of monitoring during active conversation:

```bash
$ sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39 \
    2>/dev/null > /tmp/capture.log
$ sleep 60
# Result: 92 lines captured

# Check endpoints:
$ python3 -c "..." /tmp/capture.log
# Unique endpoints seen:
#   GET /api/hello
#   POST /api/event_logging/batch
#   POST /api/v2/logs
#
# Messages API check:
$ grep -c "messages\|v1/message" /tmp/capture.log
# 0  ← NONE!
```

**The actual conversation API (`/v1/messages`) was never captured.**

### Thread analysis reveals the cause

```bash
$ for tid in $(ls /proc/847282/task/); do
    comm=$(cat /proc/847282/task/$tid/comm)
    echo "TID=$tid comm=$comm"
  done

TID=847282 comm=claude
TID=847284 comm=claude
TID=847285-847291 comm=HeapHelper (7 threads)
TID=847297 comm=HTTP Client        # ← axios telemetry uses this
TID=847298-847333 comm=Bun Pool 0-6
TID=847323 comm=File Watcher
TID=890093+ comm=JITWorker
```

All captured traffic came from TID=847297 (`HTTP Client` thread) via the
`axios/1.8.4` HTTP client library. The main conversation API uses Bun's
native `fetch()` which goes through a completely different TLS path.

### Root cause: Bun's dual TLS architecture

Bun has **two independent TLS implementations**:

1. **Node.js compatibility path** (used by `axios`, `node:https`):
   - Goes through standard BoringSSL `SSL_write`/`SSL_read`
   - Runs on the `HTTP Client` thread
   - **Our hooks capture this path** ✓

2. **Bun native path** (used by `fetch()`, Bun's HTTP client):
   - Uses **uSockets** library with custom BIO callbacks
   - Does NOT call `SSL_write`/`SSL_read`
   - Uses `ssl_on_data` callback for received data
   - Runs on the main `claude` thread
   - **Our hooks do NOT capture this path** ✗

### uSockets function analysis

From the Bun profile build:

```bash
$ readelf -W -s bun-profile | grep -E "ssl_on_|BIO_s_custom|us_internal_ssl"

48809: 040f6cc0    18 FUNC LOCAL  BIO_s_custom_create
48810: 040f6cf0    74 FUNC LOCAL  BIO_s_custom_write     # encrypted data out
48811: 040f6d40   101 FUNC LOCAL  BIO_s_custom_read      # encrypted data in
48812: 040f6ce0    14 FUNC LOCAL  BIO_s_custom_ctrl
48825: 040f77b0   732 FUNC LOCAL  ssl_on_data            # plaintext data received
48826: 040f7a90   164 FUNC LOCAL  ssl_on_writable         # writable notification
48831: 040f6db0   417 FUNC LOCAL  ssl_on_open             # connection opened
48824: 040f7690   136 FUNC LOCAL  ssl_on_close            # connection closed
```

### uSockets functions located in Claude binary

Using 32-byte pattern matching with 64-byte verification:

```python
# Search results (verified with 64-byte similarity check):
ssl_on_data:          claude offset=0x3dde620 (64/64 bytes match)
ssl_on_writable:      claude offset=0x3dde900 (63/64 bytes match)
ssl_on_open:          claude offset=0x3dddc20 (64/64 bytes match)
ssl_on_close:         claude offset=0x3dde500 (60/64 bytes match)
BIO_s_custom_write:   claude offset=0x3dddb60 (64/64 bytes match)
BIO_s_custom_read:    claude offset=0x3dddbb0 (63/64 bytes match)
```

**Important**: Initial pattern search for `ssl_on_data` returned a false
positive at offset 0x27d8050 (only 25% byte match). The prologue
`55 48 89 e5 41 57 41 56 41 55 41 54 53 48 83 ec` is extremely common
across all functions. Using 32+ byte patterns with 64-byte validation
eliminated the false positive.

### Failed attempt: bpftrace verification

```bash
$ sudo bpftrace -e '
uprobe:/home/yunwei37/.local/share/claude/versions/2.1.39:0x3dde620 { ... }
' -c "sleep 10"
# ERROR: Could not resolve address: ...0x3dde620
```

bpftrace was unable to resolve the offset. This may be a bpftrace limitation
with large stripped ELF executables. The libbpf-based sslsniff approach
(using `bpf_program__attach_uprobe_opts` directly) works correctly for the
BoringSSL hooks, suggesting the same approach would work for uSockets hooks.

---

## Current Status & Next Steps

### Current status

| Component | Status |
|---|---|
| BoringSSL pattern detection | ✅ Working |
| sslsniff offset-based attachment | ✅ Working |
| Telemetry/heartbeat capture | ✅ Working |
| `/v1/messages` (prompt) capture | ✅ **Working** (see Phase 9) |
| Collector integration | ✅ `--binary-path` passed through |

### How to capture Claude traffic

```bash
# Start monitoring BEFORE submitting a message to Claude:
sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39

# The --comm filter does NOT work because traffic comes from "HTTP Client" thread
# Do NOT use: sudo ./bpf/sslsniff -c claude --binary-path ...
```

All traffic (telemetry + conversation API) flows through the `HTTP Client`
thread via BoringSSL. The capture must be running when a new message is
submitted to capture the POST /v1/messages request and SSE response stream.

### Remaining work

1. ~~**Collector `--comm` filter fix**~~: **FIXED** — `collector/src/main.rs`
   now skips passing `--comm` to sslsniff when `--binary-path` is specified.
   The process runner still receives `--comm` for process monitoring.

2. **HTTP response decompression**: Responses may use `br` (Brotli) or `gzip`
   encoding. The collector's HTTP decompressor should handle these.

3. **Large message reassembly**: Conversation context can be very large (the
   full message history is sent with each request). The fixed-size
   `MAX_BUF_SIZE` in `sslsniff.h` may truncate large requests. Multiple
   SSL_write calls may need to be reassembled.

### Files modified

| File | Changes |
|---|---|
| `bpf/sslsniff.c` | Added `find_boringssl_offsets()`, `attach_openssl_by_offset()`, offset-based uprobe macros, two-stage `--binary-path` handler |
| `collector/src/main.rs` | Fixed `--comm` filter: skip passing `-c` to sslsniff when `--binary-path` is specified (SSL traffic uses "HTTP Client" thread name, not process name) |
| `docs/claude-code-analysis.md` | This document |

---

## Appendix: Claude Binary Architecture

### ELF Program Headers

```
Type    Offset     VirtAddr           FileSiz    MemSiz     Flg
LOAD    0x000000   0x0000000000200000 0x27d6908  0x27d6908  R     ← rodata
LOAD    0x27d6c00  0x0000000002ae7c00 0x38cc010  0x38cc010  R E   ← code
LOAD    0x60a2c10  0x00000000063b4c10 0x08fd88   0x1753e0   RW    ← data/bss
Entry point: 0x2ae7c00
```

### Thread Model (full)

| Thread Name | Count | Purpose |
|---|---|---|
| `claude` | 2 | Main thread + event loop |
| `HeapHelper` | 7 | Garbage collection assistance |
| `HTTP Client` | 1 | axios HTTP client (telemetry, heartbeat) |
| `Bun Pool 0-6` | 7 | Bun thread pool (async I/O) |
| `File Watcher` | 1 | File system monitoring |
| `JITWorker` | 2-3 | Just-in-time compilation |

### Network Endpoints Observed

| Host | Endpoint | Method | Purpose | Client |
|---|---|---|---|---|
| api.anthropic.com | `/api/hello` | GET | Heartbeat | axios |
| api.anthropic.com | `/api/event_logging/batch` | POST | Telemetry | axios |
| api.anthropic.com | `/v1/messages` | POST | Conversation | Bun fetch |
| http-intake.logs.us5.datadoghq.com | `/api/v2/logs` | POST | Datadog logging | axios |

### Multi-Process Architecture

Claude Code runs multiple processes:

```bash
$ pgrep -a claude
847282 claude   # Main session (19-21 threads, active conversation)
890428 claude   # Sub-process (20 threads, also sends telemetry)
269932 claude   # Other user's session
```

Both PID 847282 and 890428 emit telemetry traffic via their respective
`HTTP Client` threads. The sub-process (890428) appears to handle some
independent tasks.

### Key HTTP Headers

```
Authorization: Bearer sk-ant-oat01-...
Content-Type: application/json
User-Agent: claude-code/2.1.39
anthropic-beta: oauth-2025-04-20
x-service-name: claude-code
```

Telemetry payloads include: session_id, device_id, model name, event types
(permission requests, accept/submit events, cost thresholds, Growthbook
experiments), platform info (linux, node v24.3.0, is_running_with_bun: true).

---

## Phase 8: Deep Investigation of the Native Fetch TLS Path

### Goal

Determine exactly how Bun's native `fetch()` handles TLS encryption for the
`/v1/messages` API, since BoringSSL `SSL_read`/`SSL_write` hooks only capture
the axios telemetry path.

### Step 1: Verify ssl_on_data is NOT the native fetch path

We confirmed via disassembly that `ssl_on_data` in the Claude binary calls
`SSL_read` at exactly our hooked offset (0x5c38e80):

```
# Profile build: ssl_on_data calls SSL_read at offset +0xA1
40f7851: e8 0a 79 e4 01    call 5f3f160 <SSL_read>

# Claude binary: same relative call at ssl_on_data + 0xA1
03dde6c1: e8 ba a7 e5 01    → target = 0x5c38e80 ✓ (matches our hook)
```

But when traced with ftrace uprobes, `ssl_on_data` only fires from the
**HTTP Client** thread (axios), never from the main thread:

```bash
$ sudo bash -c 'echo "p:my_ssl_on_data /path/to/claude:0x3dde620" > \
    /sys/kernel/tracing/uprobe_events'
$ sudo bash -c 'echo 1 > /sys/kernel/tracing/events/uprobes/my_ssl_on_data/enable'
$ sleep 3

# Result: ONLY HTTP Client thread
HTTP Client-847297  [016] my_ssl_on_data: (0x40ef620)
HTTP Client-847297  [016] my_ssl_on_data: (0x40ef620)
HTTP Client-890449  [017] my_ssl_on_data: (0x40ef620)
```

### Step 2: Confirm SSL_read is only called from HTTP Client

Registered a uprobe directly on SSL_read (offset 0x5c38e80) and traced for
10 seconds during active conversation:

```bash
$ sudo bash -c 'echo "p:ssl_read_trace /path/to/claude:0x5c38e80" > \
    /sys/kernel/tracing/uprobe_events'
# ... enable and wait 10 seconds ...

# Result: 18 calls, ALL from HTTP Client
     18 HTTP Client
```

**No SSL_read calls from the main `claude` thread, Bun Pool threads, or
any other thread.**

### Step 3: Check for multiple copies of SSL_read

Searched the entire Claude binary for the SSL_read byte-pattern prologue:

```python
pattern = bytes([0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56,
                 0x53, 0x50, 0x48, 0x83, 0xbf, 0x98, 0x00, 0x00,
                 0x00, 0x00, 0x74])

# Result: Only 1 match at offset 0x5c38e80
# There is NO second copy of SSL_read in the binary.
```

### Step 4: Find ALL callers of SSL_read and SSL_write

Scanned the entire code section of the Bun profile build for `e8` (CALL)
instructions targeting SSL_read (VA 0x5f3f160) and SSL_write (VA 0x5f3fe00):

```
=== Functions calling SSL_read (2 call sites) ===
1. VA=0x369a330 → SSLWrapper.handleTraffic  (ssl_wrapper.zig:491)
2. VA=0x40f7851 → ssl_on_data              (uSockets callback)

=== Functions calling SSL_write (4 call sites) ===
1. VA=0x34fa553 → http.ProxyTunnel.write              (ProxyTunnel.zig:351)
2. VA=0x35c9308 → deps.uws.UpgradedDuplex.encodeAndWrite (UpgradedDuplex.zig:356)
3. VA=0x3a42208 → http.websocket_client.WebSocketProxyTunnel.write
4. VA=0x40fde0e → us_socket_write                      (uSockets C library)
```

### Step 5: Verify SSLWrapper.handleTraffic is NOT called

Located `SSLWrapper.handleTraffic` in the Claude binary at file offset
0x3390c30 (pattern-matched from profile build). Verified it also calls
SSL_read at the correct offset. Then traced it:

```bash
$ sudo bash -c 'echo "p:ssl_wrapper_trace /path/to/claude:0x3390c30" > \
    /sys/kernel/tracing/uprobe_events'
# ... enabled for 10 seconds ...

# Result: 0 calls. SSLWrapper.handleTraffic is NEVER invoked.
```

### Step 6: Verify BIO_s_custom_write/read are NOT used by native fetch

Traced the uSockets custom BIO functions:

```bash
# BIO_s_custom_write at offset 0x3dddb60
# BIO_s_custom_read at offset 0x3dddbb0

# Result after 5 seconds:
=== BIO_s_custom_write calls ===
      7 HTTP Client
=== BIO_s_custom_read calls ===
      5 HTTP Client
```

**All BIO custom callbacks also only fire from HTTP Client thread.**

### Step 7: Investigate kernel TLS (kTLS)

Checked if kTLS was the mechanism bypassing SSL_read/SSL_write:

```bash
$ lsmod | grep tls
tls    155648  26    # Module loaded!

$ cat /proc/net/tls_stat
TlsCurrTxSw    0
TlsCurrRxSw    0
TlsTxSw        0
TlsRxSw        0
# All counters are 0 → kTLS is NOT actively used
```

**kTLS ruled out.** Module is loaded but no connections use it.

### Step 8: Trace network syscalls from Claude

#### Main thread (TID=959023) syscalls

The main Claude thread only performs:
- `read(fd=6, count=8)` — eventfd (event loop notification)
- `read(fd=7, count=8)` — timerfd (timer events)
- `write(fd=13, ...)` — /dev/pts/7 (terminal output)
- `write(fd=6, count=8)` — eventfd (signaling event loop)
- Occasional `write(fd=18, count=0x6c7)` — socket to api.anthropic.com

```
FD 6  → anon_inode:[eventfd]     (event loop)
FD 7  → anon_inode:[timerfd]     (timer)
FD 8  → anon_inode:[timerfd]     (timer)
FD 13 → /dev/pts/7               (terminal)
FD 14 → anon_inode:[eventpoll]   (epoll)
FD 17 → socket (api.anthropic.com:443)
FD 18 → socket (api.anthropic.com:443)
FD 19 → socket (api.anthropic.com:443)
FD 25 → socket (api.anthropic.com:443)
```

**Key finding**: The main thread does NOT read from network sockets. It only
writes to them occasionally. It spends most time on `epoll_pwait2(fd=4)`
processing events and writing to the terminal.

#### Cross-thread analysis

Traced ALL write-related syscalls (`write`, `writev`, `sendmsg`, `sendto`)
across ALL system processes for 5 seconds. Filtered for Claude threads:

**No Claude thread writes to socket FDs during normal response streaming.**
The main thread writes ONLY to terminal (fd=13) and eventfd (fd=6).

### Step 9: Check for io_uring

```bash
# Traced io_uring_enter and io_uring events for 3 seconds
# Result: NO io_uring events from Claude or any process
```

**io_uring ruled out.** Bun uses `epoll_pwait2` as its event loop.

### Step 10: Investigate Bun's socket.write() source code

Examined Bun's source code (v1.3.9) to understand the TLS write path:

```zig
// From src/deps/uws/socket.zig
pub fn write(this: ThisSocket, data: []const u8) i32 {
    return switch (this.socket) {
        .upgradedDuplex => |socket| socket.encodeAndWrite(data),
        .connected => |socket| socket.write(is_ssl, data),
        .connecting, .detached => 0,
    };
}
```

For `.connected` SSL sockets, `socket.write(is_ssl=true, data)` delegates to
the C-level `us_socket_write` → `SSL_write`. For `.upgradedDuplex`,
`encodeAndWrite` also calls `SSL_write`.

The Bun HTTP client uses BoringSSL through uSockets, imported as:
```zig
const BoringSSL = bun.BoringSSL.c;
```

### Analysis: Why don't we capture /v1/messages traffic?

Despite exhaustive investigation, the BoringSSL `SSL_read`/`SSL_write`
functions are **only called from the HTTP Client thread**. All evidence
points to a timing/observation issue rather than a different TLS library:

1. **All SSL functions (SSL_read, SSL_write, BIO_s_custom_write/read,
   ssl_on_data)** fire exclusively from the "HTTP Client" thread
2. **Bun's source code** confirms BoringSSL is used for all TLS, through
   the uSockets library
3. **Only ONE copy** of SSL_read exists in the binary
4. **kTLS and io_uring** are not used
5. The native fetch socket write path (`.connected` → `us_socket_write`
   → `SSL_write`) is the same code path as axios

#### Hypothesis: Connection lifecycle timing

The most likely explanation is that **all TLS traffic flows through the
HTTP Client thread**, including the `/v1/messages` API calls. The reason
we haven't captured `/v1/messages` in test captures is:

1. The API request (POST /v1/messages) is sent at the **start of each turn**
   — before our monitoring captures begin
2. The streaming SSE response is received quickly over the existing
   HTTP/2 connection
3. By the time we start tracing, the response data has already been
   received and buffered
4. The main thread is simply writing buffered response to the terminal

To verify this, a capture must span the **exact moment** the user submits
a new message to Claude, triggering a fresh `/v1/messages` POST request.

### Process Architecture (Updated)

```
PID 959023 (claude -c --dangerously-skip-permissions)
├── TID 959023  claude          ← Main thread: JS execution, terminal I/O, epoll
├── TID 959024  claude          ← Secondary event loop
├── TID 959025-959031  HeapHelper (7) ← GC threads
├── TID 959035  HTTP Client     ← ALL SSL/TLS traffic (axios + native fetch?)
├── TID 959036-959625  Bun Pool 0-11 (12) ← Worker threads
├── TID 959061  File Watcher    ← FS monitoring
├── TID 994361+ JITWorker (3)   ← JIT compilation
└── TID 997844  t Helper Thread ← Unknown

Also running:
PID 890428 (claude) — background process, 18 threads, 3 API connections
PID 302782, 313517 — Node.js-based Claude processes (no API connections)
PID 269932, 845341, 894340 — Other sessions
```

### Summary of all BoringSSL functions traced

| Function | Offset (Claude) | Called from | Purpose |
|---|---|---|---|
| SSL_read | 0x5c38e80 | HTTP Client only | Read decrypted data |
| SSL_write | 0x5c39b20 | HTTP Client only | Write data for encryption |
| SSL_do_handshake | 0x5c38790 | (not traced) | TLS handshake |
| ssl_on_data | 0x3dde620 | HTTP Client only | uSockets data callback |
| ssl_on_writable | 0x3dde900 | (not traced) | uSockets writable callback |
| BIO_s_custom_write | 0x3dddb60 | HTTP Client only | Custom BIO write |
| BIO_s_custom_read | 0x3dddbb0 | HTTP Client only | Custom BIO read |
| SSLWrapper.handleTraffic | 0x3390c30 | NEVER called | Zig SSL wrapper (unused?) |

### Next steps

1. **Long-running capture spanning message submission**: Run sslsniff
   continuously while a user submits a new message to Claude, to capture
   the initial POST /v1/messages request and streaming response
2. **HTTP/2 frame decoding**: The /v1/messages traffic may use HTTP/2
   over a persistent connection. Captured data would be binary HTTP/2
   frames, not plaintext HTTP/1.1. Need HTTP/2 frame parser to extract
   the actual request/response data
3. **Alternative: Hook at the Zig/JS layer**: Instead of hooking at the
   BoringSSL level, hook higher-level Bun functions that handle HTTP
   request/response data before/after TLS encryption

---

## Phase 9: Breakthrough — Full /v1/messages Capture

### Goal

Resolve the mystery of why `/v1/messages` traffic was never captured despite
all evidence pointing to BoringSSL as the only TLS implementation.

### Key Insight: Timing Was the Issue

The Phase 8 investigation conclusively proved that **all TLS traffic** flows
through the HTTP Client thread via BoringSSL `SSL_write`/`SSL_read`. The reason
previous captures missed `/v1/messages` was simple: **no new messages were
submitted during the capture window**.

The `/v1/messages` POST request is sent at the start of each conversation turn.
If sslsniff starts after the request has already been sent, and the SSE
streaming response completes before the next capture check, the traffic is missed.

### Experiment: Self-referential capture

Since this analysis is being performed by a Claude Code instance (PID 959023),
the act of making tool calls generates `/v1/messages` API traffic. By starting
sslsniff **before** making more tool calls, we can capture our own API traffic.

```bash
# Start sslsniff in background
$ sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39 \
    2>/tmp/sslsniff_stderr.log > /tmp/sslsniff_capture.log &

# sslsniff attaches successfully:
# "BoringSSL detected! Attaching by offset..."

# Then continue making tool calls (which generates API traffic)
# After ~30 seconds, analyze the capture:
```

### Results: Complete capture of ALL traffic

```
Total events captured: 3,088 lines
├── HTTP Client(pid=959023): 2,985 events  (this session)
└── HTTP Client(pid=996386): 103 events    (other Claude process)

Functions:
├── READ/RECV: 3,043 events (SSE streaming responses)
└── WRITE/SEND: 45 events (requests + telemetry)

HTTP Endpoints captured:
├── POST /v1/messages?beta=true: 12 requests  ← CONVERSATION API!
├── POST /api/event_logging/batch: 5 requests
├── POST /api/v2/logs: 2 requests
└── GET /api/hello: 2 requests

SSE response events: 2,072 (content_block_delta, message_start, etc.)
```

### Captured request details

Full HTTP/1.1 request with all headers and JSON body:

```
POST /v1/messages?beta=true HTTP/1.1
Accept: application/json
Authorization: Bearer sk-ant-oat01-...
Content-Type: application/json
User-Agent: claude-cli/2.1.39 (external, cli)
X-Stainless-Arch: x64
X-Stainless-Lang: js
X-Stainless-OS: Linux
X-Stainless-Package-Version: 0.73.0
X-Stainless-Runtime: node
X-Stainless-Runtime-Version: v24.3.0
X-Stainless-Timeout: 600
anthropic-beta: oauth-2025-04-20,interleaved-thinking-2025-05-14,...
anthropic-version: 2023-06-01
x-app: cli
Host: api.anthropic.com
Accept-Encoding: gzip, deflate, br, zstd

{"model":"claude-haiku-4-5-20251001","messages":[...full conversation...],...}
```

### Captured SSE streaming response

```
event: message_start
data: {"type":"message_start","message":{"model":"claude-haiku-4-5-20251001",
  "id":"msg_01LUTkpAXp558VX17nfxzG3x","usage":{"input_tokens":390,...}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text",...}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta",
  "text":"..."}}
```

### Why Phase 7 / Phase 8 were misleading

The original Phase 7 hypothesis was that Bun uses two separate TLS paths:
1. `axios` → BoringSSL SSL_write/SSL_read (captured)
2. `fetch()` → uSockets with different TLS path (not captured)

This was **incorrect**. Both paths use the same BoringSSL functions through
the same HTTP Client thread. The confusion arose because:

1. **Timing**: Previous test captures ran for 60 seconds but during that window
   no new `/v1/messages` POST requests were made. The response streaming had
   already completed before sslsniff started.
2. **Thread naming**: The `HTTP Client` thread handles ALL HTTP traffic, not
   just axios. Bun's native fetch also dispatches through this thread.
3. **uSockets**: The ssl_on_data / us_socket_write functions are intermediate
   layers that ultimately call SSL_read/SSL_write, which our hooks capture.

### Architecture correction

```
BEFORE (incorrect hypothesis):
  axios    → BoringSSL SSL_write/SSL_read → HTTP Client thread  (captured ✓)
  fetch()  → uSockets custom TLS path    → Main thread          (not captured ✗)

AFTER (correct architecture):
  axios    → Node.js http → BoringSSL SSL_write/SSL_read → HTTP Client  (captured ✓)
  fetch()  → uSockets     → BoringSSL SSL_write/SSL_read → HTTP Client  (captured ✓)
```

Both code paths converge at the same BoringSSL functions on the HTTP Client
thread. No additional hooks are needed.
