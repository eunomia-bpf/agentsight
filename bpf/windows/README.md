# AgentSight eBPF programs for Windows

These are the **eBPF-for-Windows** ports of the parts of AgentSight that map onto
hooks the Windows runtime actually supports. See `docs/windows-migration.md` for the
full gap analysis and why the rest (TLS plaintext, stdio, syscalls) is handled by
Windows-native producers instead of eBPF.

| File | Program type | Replaces (Linux) | Emits (`event`) |
|---|---|---|---|
| `process_win.bpf.c` | `EBPF_PROGRAM_TYPE_PROCESS` (ntosebpfext) | `process.bpf.c` exec/exit tracepoints | `EXEC`, `EXIT` |
| `sockaddr_win.bpf.c` | `EBPF_PROGRAM_TYPE_CGROUP_SOCK_ADDR` | (additive — no Linux equivalent) | `CONNECT` |
| `sockops_win.bpf.c` | `EBPF_PROGRAM_TYPE_SOCK_OPS` | (additive) | `CONNECT`, `DISCONNECT` |
| `bpf_windows.h` | — | shared record layout | — |

Each program builds a fixed-size record on a per-CPU scratch map and ships it to
userspace with `bpf_ringbuf_output` (Windows does not yet expose ringbuf
reserve/submit — issue #727). The userspace loader serializes each record to the
**same JSONL line shapes** the Linux binaries emit, so the Rust collector pipeline is
unchanged.

## Prerequisites (Windows dev host)

1. LLVM/clang with the `bpf` target.
2. eBPF-for-Windows runtime (MSI from the project's GitHub Releases). For loading
   unsigned/dev native drivers, enable test signing: `bcdedit /set testsigning on`
   then reboot.
3. eBPF-for-Windows headers (NuGet package `eBPF-for-Windows`) and, for
   `process_win`, the `ntosebpfext` process-hook header on the include path.

## Build

```powershell
clang -target bpf -O2 -g -I bpf\windows -I <ebpf-for-windows-include> `
      -c bpf\windows\process_win.bpf.c -o build\process_win.o
clang -target bpf -O2 -g -I bpf\windows -I <ebpf-for-windows-include> `
      -c bpf\windows\sockaddr_win.bpf.c -o build\sockaddr_win.o
clang -target bpf -O2 -g -I bpf\windows -I <ebpf-for-windows-include> `
      -c bpf\windows\sockops_win.bpf.c  -o build\sockops_win.o
```

## Verify (the programs' "conformance" gate — PREVAIL)

```powershell
netsh ebpf show verification build\process_win.o  process
netsh ebpf show verification build\sockaddr_win.o cgroup/connect4
netsh ebpf show verification build\sockops_win.o  sockops
```

A clean verification means the program is in the conformant subset and is safe to
load. To also prove the **runtime** itself is ISA-conformant, run
`conformance/run_conformance.ps1` (see that folder).

## Load

```powershell
netsh ebpf add program build\process_win.o
netsh ebpf show programs
```
