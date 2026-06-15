# AgentSight Windows TLS shim (`win-ssl-shim`)

The Windows replacement for `bpf/sslsniff` — the part of AgentSight that
eBPF-for-Windows **cannot** do (no uprobe; see `docs/windows-migration.md`).

It uses **Microsoft Detours** to inline-hook `SSL_write` / `SSL_read` /
`SSL_write_ex` / `SSL_read_ex` inside the target process — the same call boundary
the Linux uprobe used, so it captures the same TLS **plaintext**. For each call it
emits one JSONL line in the **exact** shape `bpf/sslsniff.c` emits:

```json
{"function":"WRITE/SEND","timestamp_ns":123,"comm":"node.exe","pid":42,"len":31,
 "buf_size":31,"uid":0,"tid":7,"latency_ms":0,"is_handshake":false,
 "data":"GET / HTTP/1.1\r\n...","truncated":false}
```

so the Rust collector's `SSLFilter` / `HTTPParser` / `SSEProcessor` consume it with
zero changes.

## Pieces

- `ssl_shim.cpp` — the injected DLL: resolves the SSL functions (dynamic export
  lookup, or `boringssl_detect.cpp` byte-pattern scan for statically-linked
  Bun/Node/Claude), attaches Detours hooks, streams JSONL to a named pipe.
- `boringssl_detect.cpp` — port of the Linux BoringSSL detector for stripped static
  binaries.
- `injector.cpp` → `agentsight-ssl-shim.exe` — the launcher the collector spawns:
  creates the pipe, injects the DLL (launch via `DetourCreateProcessWithDllEx`, or
  attach via remote `LoadLibrary`), relays the pipe to stdout.
- `json_util.h` — JSON escaping matching `bpf/jsonl.h`.

## Build

```powershell
vcpkg install detours:x64-windows-static
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=<vcpkg>\scripts\buildsystems\vcpkg.cmake
cmake --build build --config Release
```

## Run (standalone)

```powershell
# Launch and trace a command
build\Release\agentsight-ssl-shim.exe --dll build\Release\ssl_shim.dll -- node app.js
# Attach to an existing process
build\Release\agentsight-ssl-shim.exe --dll build\Release\ssl_shim.dll --pid 1234
```

The Rust collector drives this automatically via `WindowsSslRunner`
(`collector/src/runners/windows_ssl.rs`).

## Notes / limitations

- Injection requires the launcher to run with rights to the target (admin for
  cross-session/elevated targets).
- The DLL captures plaintext only for libraries that route through the OpenSSL/
  BoringSSL `SSL_*` API. Schannel/CNG (native WinHTTP/.NET `HttpClient`) does **not**
  go through `SSL_*`; covering it is future work (a separate Schannel/SSPI hook set)
  and is tracked in `docs/windows-migration.md` §6.
