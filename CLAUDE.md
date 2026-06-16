# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AgentSight is an eBPF-based observability framework for monitoring AI agent behavior through SSL/TLS traffic interception and process monitoring. It captures unencrypted request/response data at the kernel level without requiring any code changes to target applications.

## Build & Test Commands

```bash
# Full build (eBPF + Rust collector + frontend)
make build

# Individual components
make build-bpf                          # eBPF C programs only
cd collector && cargo build --release   # Rust collector only
cd frontend && npm install && npm run build  # Frontend only

# Tests
cd bpf && make test              # C unit + runtime tests
cd collector && cargo test       # Rust tests
cd frontend && npm run lint      # Frontend linting

# Run a single Rust test
cd collector && cargo test test_name

# Debug builds with AddressSanitizer
cd bpf && make debug
cd bpf && make sslsniff-debug

# Install system dependencies (Ubuntu/Debian)
make install
```

## Running

```bash
# Live agent sessions
sudo ./agentsight top

# Launch and record a command
sudo ./agentsight record -- claude

# Record Claude Code (requires --binary-path for statically-linked BoringSSL)
sudo ./agentsight record -c claude --binary-path ~/.local/share/claude/versions/<version>

# Record Python AI tools
sudo ./agentsight record -c python

# Record with NVM Node.js (statically-linked OpenSSL)
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node

# Direct eBPF program usage
sudo ./bpf/sslsniff --binary-path <path>
sudo ./bpf/process -c python

# Web UI available at http://127.0.0.1:7395 when using record/stat live capture.
# debug trace needs --server.
```

## Architecture

```
eBPF Programs (kernel) → JSON stdout → Rust Runners → Analyzer Chain → Output/Frontend/Files
```

### Key Components

- **`bpf/`** — C eBPF programs. `sslsniff` hooks SSL_read/SSL_write via uprobes; `process` tracks process lifecycle via tracepoints; `stdiocap` captures stdio payloads. All emit JSONL to stdout via the shared `bpf/jsonl.h` helpers. `browsertrace` is experimental (`make experimental`) and not embedded in the collector.
- **`collector/src/`** — Rust streaming pipeline (flat module layout):
  - `runners/` — Execute eBPF binaries and parse their JSON output into event streams (BinaryRunner, ProcessRunner, SystemRunner, AgentRunner, FakeRunner for tests)
  - `analyzers/` — Pluggable stream processors: SSEProcessor, HTTPParser, SSLFilter, HTTPFilter, AuthHeaderRemover, TimestampNormalizer, MaterializingAnalyzer (feeds the materialized view)
  - `sources/` — Non-eBPF inputs: agent-native session files (`~/.claude`, `~/.codex`), `/proc` snapshots, saved SQLite databases
  - `view/` — MaterializedView: projects events into rows (llm_calls, audit_events, process_nodes, ...) and serves snapshots
  - `sinks/` — ViewSink implementations: SQLite row store, OTel exporter (maps LLM call rows to OpenTelemetry `gen_ai.*` spans via OTLP/HTTP JSON; enabled by `debug trace --otel`, see `docs/otel.md`)
  - `output/` — CLI/TUI rendering of snapshots
  - `event.rs` — Standardized `Event` struct with JSON payloads; `model.rs` — view row types + ViewSink trait
  - `binary_extractor.rs` — Extracts embedded eBPF binaries to temp files at runtime
- **`collector/src/main.rs`** — CLI entry point. Main subcommands: `top`, `monitor`, `record`, `report` (`summary`, `token`, `audit`, `prompts`, `export`, `list`), and `debug` (`ssl`, `process`, `stdio`, `trace`, `system`).
- **`collector/src/server/`** — Hyper-based embedded web server serving frontend assets and `/api/events`
- **`frontend/`** — Next.js/React/TypeScript visualization with timeline, process tree, and log views

### Data Flow

Runners use a fluent builder pattern: `SslRunner::new().with_args(&args).add_analyzer(Box::new(HTTPParser::new())).run().await`

Each Runner produces an `EventStream` (async Stream of Events). Analyzers transform streams in sequence. The `AgentRunner` orchestrates multiple runners concurrently via `RunnerOrchestrator`.

### Timestamp Convention

All timestamps are nanoseconds since boot (`bpf_ktime_get_ns()`). `Event::datetime()` converts to wall-clock time using boot time from `/proc/stat`.

## Critical: `--binary-path` and `--comm` Interaction

Applications that statically link SSL (Claude/Bun uses BoringSSL, NVM Node.js uses OpenSSL) require `--binary-path` because there's no system `libssl.so` to hook. When `--binary-path` is specified:

1. sslsniff tries symbol lookup first, then falls back to **BoringSSL byte-pattern detection** for stripped binaries
2. The `--comm` filter is **NOT passed to sslsniff** (only to the process runner) — because `bpf_get_current_comm()` returns the thread name, not the process name. Claude's SSL traffic runs on an "HTTP Client" thread, so `-c claude` would filter out all SSL traffic.

This logic is in `build_trace_agent()` in `collector/src/cmd_trace.rs`.

## Development Patterns

### Adding a New Analyzer

1. Implement `Analyzer` trait in `collector/src/framework/analyzers/`
2. Core method: `async fn analyze(&self, events: EventStream) -> EventStream`
3. Export in `analyzers/mod.rs`
4. Attach via `.add_analyzer(Box::new(MyAnalyzer::new()))` on any runner

### Adding a New Runner

1. Implement `Runner` trait in `collector/src/framework/runners/`
2. Use `BinaryExecutor` for running external binaries and parsing JSON output
3. Use fluent builder pattern for configuration
4. Export in `runners/mod.rs`

### Adding a New eBPF Program

1. Create `name.bpf.c` (kernel) and `name.c` (userspace) in `bpf/`
2. Add to `APPS` variable in `bpf/Makefile`
3. Use CO-RE pattern with architecture-specific `vmlinux.h` from `vmlinux/`
4. Output JSON to stdout; debug info to stderr

## CLI Subcommands

- **`top`** — Primary live view. Run as `sudo ./agentsight top`; it loads eBPF probes and also reads agent-native sessions when present.
- **`record`** — Optimized recording. Use `sudo ./agentsight record -- <command>` to launch and trace a command, or `sudo ./agentsight record -c <comm>` / `-p <pid>` to attach. It enables SSL, process, stdio when applicable, system monitoring, materialized view sinks, and the web UI by default.
- **`stat`** — Query the latest saved session, or run `sudo ./agentsight stat -- <command>` and print counters when the command exits.
- **`report [summary|token|audit|prompts|export|list]`** — Query saved local SQLite sessions; these usually do not need sudo. `report` with no subcommand defaults to `summary`.
- **`debug trace`** — Most flexible live capture. Toggle `--ssl`, `--process`, `--stdio`, `--system`, and `--server` independently. Supports `--ssl-filter`, `--http-filter`, `--binary-path`, and `--otel`.
- **`debug ssl` / `debug process` / `debug stdio` / `debug system`** — Raw component-level debug entrypoints. Use `sudo` because they load eBPF probes or inspect privileged process state.

## SSL Binary Auto-Discovery (record/debug trace)

In `build_trace_agent()`, when SSL is enabled and `--binary-path` is absent, the binary is auto-discovered from `--comm`: `resolve_binary_path(comm)` resolves the binary, and it is adopted **only if `binary_embeds_ssl()` returns true** (the binary contains the `SSL_write` symbol-name string). This fixes `record -c node` (Node statically links OpenSSL — no system `libssl.so` to hook) while leaving dynamically-linked runtimes like Python on sslsniff's system-libssl + comm-filter path. `record -- <command>` resolves the launched command directly because it targets one known process tree.

## Containerized Agents: `docker://` Binary Path

`--binary-path docker://<name|id>` (or `docker:<name|id>`) targets an agent
running in a Docker container. `resolve_container_binary_path()` in
`collector/src/main.rs` runs `docker inspect --format '{{.State.Pid}}'` to get
the container's init PID, then `find_ssl_pid_in_tree()` walks the descendant
process tree (via `/proc/<pid>/task/<pid>/children`) and returns the first
process whose `/proc/<pid>/exe` embeds SSL. This is needed because the init PID
is often a wrapper like `tini` (OpenClaw runs `tini -s -- node openclaw.mjs
gateway`) that contains no SSL code. The scheme is handled by the trace builder
used by `record`/`debug trace` and by raw `debug ssl`. See
`docs/experiment/openclaw.md`. `parse_container_ref()` has unit tests.

## Common Issues

- **No SSL capture from Claude/Bun**: Must use `--binary-path` pointing to the actual binary, or use `sudo ./agentsight record -- claude` so AgentSight resolves the launched command. BoringSSL is statically linked and stripped.
- **No SSL capture from Node.js / Gemini CLI**: All Node.js statically links OpenSSL. `record -c node` now auto-discovers the Node binary; `sudo ./agentsight record -- gemini` also works. An HTTP/HTTPS proxy does not affect capture (TLS still happens in-process at `SSL_*`).
- **`--comm` filter drops all SSL events**: SSL runs on "HTTP Client" thread, not the process name thread. Fixed: `--comm` is auto-skipped for sslsniff when `--binary-path` is set.
- **eBPF permission errors**: Requires `sudo` or `CAP_BPF` + `CAP_SYS_ADMIN`.
- **Port 7395 conflict**: Default web server port. Change with `--server-port`.
