# AgentSight on Windows — eBPF-for-Windows Migration Plan

> Status: in progress. This document is the authoritative plan and gap analysis for
> porting AgentSight's kernel-level agent observability to Windows, mapping to
> Microsoft's **eBPF for Windows** wherever the platform genuinely supports it and
> using Windows-native mechanisms (that emit the *same* event contract) where it
> does not.

## 0. TL;DR for reviewers

- eBPF-for-Windows is a **networking-focused** eBPF runtime. It has a conformant
  eBPF **instruction set** (passes `bpf_conformance`) and supports network hooks
  (XDP, BIND, CGROUP/SOCK_ADDR, SOCK_OPS) plus a **process create/exit** extension
  (`ntosebpfext`). It has **no uprobe / kprobe / tracepoint / syscall** program
  types.
- AgentSight's defining capability — capturing decrypted request/response bodies by
  hooking `SSL_write`/`SSL_read` with **uprobes** — therefore has **no eBPF
  equivalent on Windows** and must move to **Microsoft Detours** userspace API
  hooking. This is the Windows analog of a uprobe (same instruction boundary, same
  plaintext access).
- "Passing the conformance suite on Windows" is a property of the *runtime*, not of
  our programs. The achievable, meaningful goal for AgentSight's own programs is to
  be written in the **conformant ISA subset** so they pass the **PREVAIL verifier**
  and load via `netsh ebpf add program`. We ship a harness that (a) runs the real
  `bpf_conformance` suite against the installed runtime and (b) verifies each of our
  programs.
- The migration's north star: **the JSONL stdout contract is the stable seam.** Every
  Windows producer (eBPF loader, Detours shim, ConPTY capturer) emits the exact same
  JSON line shapes the Rust collector already parses, so the entire analyzer → view →
  sink → frontend pipeline is reused unchanged.

## 1. What AgentSight does today (Linux) and the exact mechanism inventory

Mechanisms in `bpf/*.bpf.c`, enumerated from source:

| Program | Attach mechanism (`SEC(...)`) | Purpose | Windows-eBPF mappable? |
|---|---|---|---|
| `sslsniff` | `uprobe`/`uretprobe` on `SSL_read`, `SSL_write`, `SSL_read_ex`, `SSL_write_ex`, `do_handshake` | TLS **plaintext** capture | **No** — no uprobe. → Detours shim |
| `process` | `tp/sched/sched_process_exec`, `tp/sched/sched_process_exit` | Process create/exit | **Partial** — `EBPF_PROGRAM_TYPE_PROCESS` (create/delete) |
| `process` | `uretprobe .../bash:readline` | Shell command capture | **No** — no uprobe. → Detours (optional) |
| `process` | `tp/syscalls/sys_enter_open(at)` | File-open tracking | **No** — no syscall hook. → ETW / minifilter (later) |
| `stdiocap` | `tp/syscalls/sys_enter_read/write`, `sys_exit_read/write` | stdio payload capture | **No** — no syscall hook. → ConPTY/pipe redirect |
| `browsertrace` | `uprobe` on NSS `PR_Read`/`PR_Write`/`SSL_ImportFD` | Browser TLS (experimental) | **No** — no uprobe. → Detours (later) |

Helpers used (all programs): `bpf_get_current_pid_tgid`, `bpf_get_current_uid_gid`,
`bpf_get_current_comm`, `bpf_ktime_get_ns`, `bpf_map_{lookup,update,delete}_elem`,
`bpf_ringbuf_{reserve,submit}`, `bpf_probe_read_user(_str)`, `bpf_probe_read_kernel_str`.
Map types: `BPF_MAP_TYPE_RINGBUF`, `BPF_MAP_TYPE_HASH`.

The userspace `bpf/*.c` binaries emit **JSONL to stdout**; `collector/`'s
`BinaryExecutor` spawns them and `parse_json_event` turns each line into an `Event`.
The SSL line shape (the most important contract) is, from `bpf/sslsniff.c`:

```json
{"function":"read|write|handshake","timestamp_ns":<u64>,"comm":"<str>","pid":<u32>,
 "len":<i32>,"buf_size":<u32>,"uid":<i32>,"tid":<u32>,"latency_ms":<f64>,
 "is_handshake":<bool>,"data":<json-string|null>,"truncated":<bool>}
```

`parse_json_event` requires exactly three fields to build an `Event`: a timestamp
field (`timestamp_ns`), `pid`, and `comm`. Everything else rides in the JSON payload.
**This is the seam we preserve on Windows.**

## 2. eBPF-for-Windows: verified capability surface

Sourced from `microsoft/ebpf-for-windows` (`include/ebpf_structs.h`,
`ebpf_program_attach_type_guids.h`, `ebpf_nethooks.h`, `bpf_helper_defs.h`, `docs/`),
`microsoft/ntosebpfext`, and `Alan-Jowett/bpf_conformance`.

### 2.1 Program types & hooks (what exists)

- `EBPF_PROGRAM_TYPE_XDP` — inbound packets (over WFP).
- `EBPF_PROGRAM_TYPE_BIND` — `bind()` permit/deny/redirect.
- `EBPF_PROGRAM_TYPE_CGROUP_SOCK_ADDR` — `connect()` / `recv_accept` / connect
  authorization, IPv4/IPv6.
- `EBPF_PROGRAM_TYPE_SOCK_OPS` — connection established / torn-down notifications.
- `EBPF_PROGRAM_TYPE_SAMPLE` — test-only.
- `EBPF_PROGRAM_TYPE_PROCESS` (extension `ntosebpfext`) — **process create/delete only**
  via `PsSetCreateProcessNotifyRoutineEx`; ctx `process_md_t` gives PID/parent,
  command line, timestamps, exit code, token SID.
- `EBPF_PROGRAM_TYPE_NETEVENT` (separate extension) — network-event notifications.

### 2.2 What does NOT exist (the hard blockers)

- **No uprobe / uretprobe** → cannot hook `SSL_*` in a target process.
- **No kprobe, no tracepoint, no syscall** program types → cannot do
  `sys_enter_openat` / `sys_enter_read|write`. (Tracked: issues #206, #382, #734,
  #732 — all open/design-stage, no committed roadmap.)
- Consequence: `sslsniff`, `stdiocap`, the `readline` and `openat` parts of
  `process`, and `browsertrace` have **no eBPF path** on Windows.

### 2.3 Maps & helpers we can rely on

- Maps: `HASH`, `ARRAY`, per-CPU variants, `LRU_HASH`, `LPM_TRIE`, `QUEUE`, `STACK`,
  **`RINGBUF`**, **`PERF_EVENT_ARRAY`**, maps-of-maps. (We use HASH + RINGBUF.)
- Output to userspace: **ring buffer** is primary and libbpf-compatible
  (`ring_buffer__new/poll/consume`), plus a Windows async-callback mode. Perf event
  array also supported.
- Helpers present: `bpf_map_*`, `bpf_ringbuf_output`, `bpf_perf_event_output`,
  `bpf_tail_call`, `bpf_ktime_get_ns`, `bpf_ktime_get_boot_ns`,
  `bpf_get_prandom_u32`, `bpf_get_smp_processor_id`, `bpf_printk`, `bpf_csum_diff`,
  and Windows identity helpers: `bpf_get_current_pid_tgid`,
  `bpf_get_current_logon_id`, `bpf_is_current_admin`,
  `bpf_get_current_process_start_key`, `bpf_get_socket_cookie`, plus safe
  `bpf_memcpy_s`/`bpf_strncpy_s`.
- **Important divergences from Linux** that our programs must respect:
  - No `bpf_get_current_uid_gid` / `bpf_get_current_comm` — use `process_md_t`
    fields and `bpf_get_current_logon_id`.
  - Standalone `bpf_ringbuf_reserve`/`submit` is **not yet exposed** (issue #727);
    use **`bpf_ringbuf_output`** with a stack/map-scratch record instead.
  - No `bpf_probe_read_user` (no userspace probe context) — context data is read
    directly from the typed ctx struct.

### 2.4 Toolchain, loading, signing

- Compile: `clang -target bpf -O2 -g -c x.bpf.c -o x.o` (same front end).
- Verify + run, three modes: **native/AOT** via `bpf2c` (generates a signed `.sys`
  driver; required under HVCI/Secure Boot), **JIT** (`eBPFSvc.exe`, fails under
  HVCI), **interpreted** (debug builds only).
- Tooling: `ebpfapi.dll` exposes libbpf APIs; `netsh ebpf` and a Windows `bpftool`.
- Loaders are **source-compatible** with libbpf but must be recompiled against the
  Windows headers (NuGet `eBPF-for-Windows`) and linked to `ebpfapi.dll`; the
  `bpf()` syscall ABI is **not** binary-compatible (see `docs/BpfSyscallCompatibility.md`).
- Dev requires **test-signing mode** for native drivers; production uses Microsoft
  PRS signing.

### 2.5 The conformance suite, precisely

- `Alan-Jowett/bpf_conformance` measures a **runtime's** conformance to the eBPF
  **ISA**: it feeds bytecode + initial memory to a runtime plugin and checks `r0`.
  It tests instruction semantics (ALU, jumps, load/store, atomics, byteswap) — **not**
  program types, hooks, maps, or helpers.
- eBPF-for-Windows runs these vectors against its `bpf2c`, PREVAIL verifier, and uBPF
  JIT/interpreter; `docs/isa-support.rst` is the per-opcode matrix.
- **Therefore:** "AgentSight passes conformance on Windows" is a category error for
  our *programs*. Our two concrete, checkable obligations are:
  1. The installed **runtime** passes `bpf_conformance` (we provide a harness that
     proves it on the target host).
  2. **Our programs** are written in the conformant subset and pass the **PREVAIL
     verifier** (`netsh ebpf show verification <obj> <section>`) and load. The
     harness checks this per program.

## 3. Target architecture on Windows

```
                         ┌─────────────────────────── unchanged ───────────────────────────┐
 producers (new, Win)    │  collector pipeline (reused as-is)                                │
                         │                                                                    │
 [eBPF: process_win] ──┐ │  Runner → EventStream → Analyzers → MaterializedView → Sinks →    │
 [eBPF: sockaddr_win]──┼─JSONL→  (SSEProcessor, HTTPParser, SSLFilter, ...) → SQLite/OTel/Web │
 [eBPF: sockops_win] ──┘ │                                                                    │
 [Detours: ssl-shim] ──JSONL→ (identical probe_SSL_data line shape)                           │
 [ConPTY: stdio-cap] ──JSONL→ (identical stdio line shape)                                    │
                         └────────────────────────────────────────────────────────────────────┘
```

Seam = the JSONL line shapes in §1. Producers differ per-OS; everything downstream is
shared Rust.

### 3.1 Component mapping

| Linux component | Windows replacement | Tech | Emits |
|---|---|---|---|
| `sslsniff` (uprobe) | `win-ssl-shim` | Detours DLL + injector | `probe_SSL_data` JSONL (identical) |
| `process` exec/exit (tp) | `process_win.bpf.c` | eBPF `EBPF_PROGRAM_TYPE_PROCESS` + loader | process JSONL |
| `process` openat (tp) | `win-file-etw` | ETW `Microsoft-Windows-Kernel-File` | file-open JSONL |
| `process` readline (uprobe) | (optional) ConPTY input capture | ConPTY | command JSONL |
| `stdiocap` (tp read/write) | `win-stdio-cap` | ConPTY | stdio JSONL |
| (eBPF load + ringbuf drain) | `win-ebpf-loader` | Windows libbpf (`ebpfapi.dll`) | process/net JSONL |
| network visibility (n/a today) | `sockaddr_win.bpf.c` + `sockops_win.bpf.c` | eBPF | connection JSONL (new, additive) |

### 3.2 Collector changes (Rust)

- `runners/common.rs`: cfg-gate the Linux-only privilege path (`libc::geteuid`,
  `sudo` wrapping, `process_group(0)`). On Windows, run the producer directly
  (elevation handled by the host / manifest), keep the identical stdout-JSONL stream
  reader.
- New `runners/windows_ssl.rs` (`cfg(windows)`): launches `win-ssl-shim` (launch or
  attach), forwards its JSONL as an `EventStream` named `"ssl"` so existing analyzers
  (SSLFilter/HTTPParser/SSEProcessor) bind unchanged.
- New `runners/windows_ebpf.rs` (`cfg(windows)`): loads `process_win.o` /
  `sockaddr_win.o` via the Windows libbpf API (`ebpfapi.dll`), polls the ring buffer,
  serializes records to the same JSONL the Linux userspace emitted.
- `cmd_trace.rs`: `#[cfg(windows)]` builder wires the Windows runners instead of the
  eBPF binaries; the `--binary-path` BoringSSL logic carries over to the shim.

## 4. Phased delivery

- **Phase 0 — Plan & gap analysis** (this doc). ✅
- **Phase 1 — Windows eBPF programs (conformant subset)**: `process_win`,
  `sockaddr_win`, `sockops_win` + `bpf_windows.h`. Goal: compile with clang bpf
  target and pass PREVAIL verification on a Windows host.
- **Phase 2 — Conformance & verification harness**: run `bpf_conformance` vs the
  installed runtime; verify each program; ISA `.data` smoke vectors.
- **Phase 3 — TLS plaintext via Detours**: `win-ssl-shim` DLL + injector emitting the
  identical SSL JSONL. This restores AgentSight's core value on Windows.
- **Phase 4 — Collector Windows runners**: cfg-gated runners; cross-compile clean;
  Linux build unaffected.
- **Phase 5 — stdio (ConPTY) + file-open (ETW)** and build/CI (`build-windows.ps1`,
  GH Actions windows-latest job, signing notes). **Implemented:**
  `shim/win-stdio-cap/` (ConPTY, emits the `stdiocap` JSONL),
  `shim/win-file-etw/` (Microsoft-Windows-Kernel-File provider, emits FILE_OPEN
  JSONL), `shim/win-ebpf-loader/` (loads `bpf/windows/*.o` via the Windows libbpf
  API and emits process/net JSONL), and the Rust `WindowsStdioRunner`. With these,
  every Linux telemetry pillar has a Windows producer: TLS plaintext (Detours),
  process+network (eBPF), stdio (ConPTY), file-open (ETW).

## 5. What can and cannot be verified from the current (Linux) dev environment

Honest scope statement, so no result is overclaimed:

- **Verified here:**
  - Linux build is unaffected by the cfg-gating: `cd collector && cargo check`
    exits 0 (regression guard for the `runners/common.rs` changes); `cargo test
    --bins` = 105 passed / 1 ignored / 0 failed.
  - The cfg structure is sound: the Linux-only privilege path (`geteuid`/`sudo`/
    `process_group`/`killpg`) is now `#[cfg(unix)]`, with Windows fallbacks.
  - **Conformance vectors EXECUTED** on the uBPF reference runtime (the same
    interpreter eBPF-for-Windows uses for interpreted mode): `8/8` ISA vectors pass
    (`bpf/windows/conformance/run_local_ubpf.py`), covering immediate/register ALU,
    logical, shift, and jeq/jne/jgt jumps. This proves the vectors are valid eBPF ISA
    and a conformant runtime executes them correctly. It does **not** prove
    eBPF-for-Windows itself passes — see below.
- **Blocked in this sandbox (environment, not code):** `cargo check --target
  x86_64-pc-windows-gnu` fails **only** in the `libsqlite3-sys` build script, which
  needs a mingw C cross-compiler (`x86_64-w64-mingw32-gcc`) that is not installed and
  cannot be installed here (no sudo/network). This is a native-dependency toolchain
  gap; it stops the build *before* reaching AgentSight's Rust source. The fix is to
  build on a Windows host / CI with the **MSVC** target (`x86_64-pc-windows-msvc`),
  where SQLite builds natively — this is exactly what `.github/workflows/windows.yml`
  does (`cargo check --target x86_64-pc-windows-msvc`).
- **Cannot verify here (requires a Windows host with eBPF-for-Windows installed +
  test-signing):** loading the programs, `netsh ebpf show verification`, running
  `bpf_conformance` against the runtime, Detours injection, end-to-end capture. §7 and
  `bpf/windows/conformance/` document the exact commands; the `windows.yml` CI job is
  the intended gate (note: `clang` is also not installed in this Linux sandbox, so the
  eBPF→bytecode compile likewise runs in CI / on a provisioned host).

## 6. Risks / open questions

- `bpf_ringbuf_output` record-size limits and the lack of reserve/submit may force a
  per-CPU scratch map for large records; SSL bodies (up to 512 KB) do **not** flow
  through eBPF anyway (they come from the Detours shim), so eBPF records stay small.
- `EBPF_PROGRAM_TYPE_PROCESS` requires the `ntosebpfext` extension to be installed;
  if unavailable we fall back to ETW `Microsoft-Windows-Kernel-Process`.
- Native-driver signing for production deployment (PRS) is an operational, not code,
  task.

## 7. Runbook: building & proving on a Windows host

See `bpf/windows/README.md` and `bpf/windows/conformance/`. Summary:

```powershell
# 1. Install runtime (test-signing dev): MSI from ebpf-for-windows Releases, then
bcdedit /set testsigning on   # reboot

# 2. Build programs
clang -target bpf -O2 -g -c bpf\windows\process_win.bpf.c -o build\process_win.o
# (repeat for sockaddr_win / sockops_win)

# 3. Verify each program against PREVAIL (this is our programs' "conformance")
netsh ebpf show verification build\process_win.o process

# 4. Run the ISA conformance suite against the installed runtime
pwsh bpf\windows\conformance\run_conformance.ps1

# 5. Load
netsh ebpf add program build\process_win.o
```
