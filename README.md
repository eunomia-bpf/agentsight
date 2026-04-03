# AgentSight

[中文版](README_CN.md)

eBPF-based observability tool for AI Agents on Linux, providing zero-intrusion monitoring of LLM API calls, token consumption, process behavior, and SSL/TLS traffic. AgentSight is an observability component of [ANOLISA](../../README.md).

## Features

- **Zero-Intrusion Monitoring** — eBPF kernel probes capture events without modifying agent code or configurations.
- **SSL/TLS Traffic Decryption** — uprobe-based interception of OpenSSL/GnuTLS library calls to capture plaintext HTTP traffic.
- **LLM Token Accounting** — Precise token counting with Hugging Face tokenizer support (Qwen series and more).
- **AI Agent Auto-Discovery** — Scans `/proc` and monitors `execve` events to dynamically detect running AI agent processes.
- **Streaming Response Support** — Parses Server-Sent Events (SSE) for tracking streamed LLM responses.
- **Audit Logging** — Complete audit trail of LLM calls and process operations with structured records.
- **Cloud Integration** — Native export to Alibaba Cloud SLS (Simple Log Service) for centralized log analysis.
- **GenAI Semantic Events** — Builds structured semantic events for LLM calls, tool usage, and agent interactions.

## Architecture

AgentSight operates a unified data pipeline:

```
┌──────────┐    ┌────────┐    ┌────────────┐    ┌──────────┐    ┌───────┐    ┌─────────┐
│  Probes  │───▶│ Parser │───▶│ Aggregator │───▶│ Analyzer │───▶│ GenAI │───▶│ Storage │
└──────────┘    └────────┘    └────────────┘    └──────────┘    └───────┘    └─────────┘
  eBPF events    HTTP/SSE      Req-Resp          Token/Audit     Semantic     SQLite /
  (kernel)       extraction    correlation       extraction      events       SLS export
```

| Stage | Description |
|-------|-------------|
| **Probes** | eBPF programs (sslsniff, proctrace, procmon) capture kernel events via ring buffer |
| **Parser** | Extracts structured HTTP messages, SSE events, and process exec data |
| **Aggregator** | Correlates request-response pairs; tracks process lifecycle via LRU cache |
| **Analyzer** | Produces audit records, token usage stats, and LLM API messages |
| **GenAI** | Transforms results into semantic events (LLM calls, tool use, agent interactions) |
| **Storage** | Persists to local SQLite database and optionally uploads to Alibaba Cloud SLS |

### eBPF Probes

| Probe | Source | Description |
|-------|--------|-------------|
| **sslsniff** | `src/bpf/sslsniff.bpf.c` | uprobe on SSL_read/SSL_write to capture plaintext from encrypted connections |
| **proctrace** | `src/bpf/proctrace.bpf.c` | Traces execve syscalls, captures command-line args, builds process tree |
| **procmon** | `src/bpf/procmon.bpf.c` | Lightweight process monitor for creation/exit events (agent discovery) |

### Project Structure

```
agentsight/
├── src/
│   ├── bpf/            # eBPF C programs (sslsniff, proctrace, procmon)
│   ├── probes/         # eBPF probe management and event polling
│   ├── parser/         # HTTP, SSE, and process event parsers
│   ├── aggregator/     # Request-response correlation and process aggregation
│   ├── analyzer/       # Token extraction, audit records, message parsing
│   ├── genai/          # GenAI semantic event builder and SLS uploader
│   ├── storage/        # SQLite-backed stores (audit, token, HTTP, GenAI)
│   ├── discovery/      # AI agent process scanner (/proc + eBPF)
│   ├── tokenizer/      # HuggingFace tokenizer integration for token counting
│   ├── bin/            # CLI entry points (agentsight, cli subcommands)
│   ├── unified.rs      # Main pipeline orchestrator
│   ├── config.rs       # Unified configuration management
│   └── event.rs        # Unified event type definitions
├── Cargo.toml
├── build.rs            # eBPF skeleton generation for three probes
└── agentsight.spec     # RPM packaging spec
```

## CLI Commands

### `agentsight trace`

Start eBPF-based tracing of AI agent activity.

```bash
# Foreground mode
sudo agentsight trace

# Daemon mode with SLS export
sudo agentsight trace --daemon \
  --sls-endpoint <endpoint> \
  --sls-project <project> \
  --sls-logstore <logstore>
```

### `agentsight token`

Query token consumption data.

```bash
# Today's token usage
agentsight token

# This week, compared to last week
agentsight token --period week --compare

# Detailed breakdown by role and type
agentsight token --detail

# JSON output
agentsight token --json
```

### `agentsight audit`

Query audit events (LLM calls, process operations).

```bash
# Recent audit events
agentsight audit

# Filter by PID and event type
agentsight audit --pid 12345 --type llm

# Summary statistics
agentsight audit --summary
```

### `agentsight serve`

Start the HTTP API server and serve the embedded Dashboard UI.

```bash
# Start with default settings (binds to 127.0.0.1:7396)
agentsight serve

# Bind to all interfaces on a custom port
agentsight serve --host 0.0.0.0 --port 8080

# Point to a specific database file
agentsight serve --db /path/to/genai_events.db
```

### `agentsight discover`

Discover AI agents running on the system.

```bash
# Scan for running agents
agentsight discover

# List all known agent types
agentsight discover --list

# Verbose output with executable paths
agentsight discover --verbose
```

## Dashboard

The Dashboard is a React-based web UI for visualizing conversation history, trace details, and token statistics. It is embedded into the `agentsight serve` binary at compile time.

### Build the Dashboard

```bash
cd src/agentsight

# Build frontend and embed into frontend-dist/ (required before cargo build)
make build-frontend

# Then build the Rust binary with the embedded UI
make build

# Or do both in one step
make build-all
```

### Scenario 1 — Collect data and view the Dashboard simultaneously

Run the tracer and the API server in two separate terminals:

```bash
# Terminal 1: start eBPF tracing (writes to SQLite)
sudo agentsight trace

# Terminal 2: start the API server (reads from the same SQLite)
agentsight serve
```

Open `http://127.0.0.1:7396` in your browser. The Dashboard auto-refreshes as new data arrives.

> **Running on a remote server?** Bind to all interfaces and access via the server's public IP:
> ```bash
> agentsight serve --host 0.0.0.0 --port 7396
> ```
> Then open `http://<server-public-ip>:7396` in your local browser.
> Make sure port 7396 is allowed in the server's firewall / security group rules.

### Scenario 2 — Browse historical data only

No tracing needed. Just start the server pointing at an existing database:

```bash
agentsight serve --db /path/to/genai_events.db
```

Open `http://127.0.0.1:7396` to explore recorded conversations and traces.

### Dashboard Development

To iterate on the frontend without rebuilding the Rust binary:

```bash
cd src/agentsight/dashboard
npm install
npm run dev          # starts webpack-dev-server on http://localhost:3004
```

When finished, run `make build-frontend && cargo build --release` to embed the updated UI.

## Quick Start

### Prerequisites

| Component | Version |
|-----------|---------|
| Linux kernel | >= 5.8 (BTF support) |
| Rust | >= 1.80 |
| clang / llvm | >= 11 (for eBPF compilation) |
| libbpf | >= 0.8 |

### Build from Source

```bash
cd src/agentsight
cargo build --release
```

The binary is output to `target/release/agentsight`.

### Install via RPM

```bash
sudo yum install agentsight
```

Installs:
- `/usr/local/bin/agentsight` — CLI binary

### Start Tracing

```bash
# Requires root for eBPF
sudo agentsight trace
```

## Configuration

Key configuration options via `AgentsightConfig`:

| Category | Option | Description |
|----------|--------|-------------|
| Storage | `db_path` | SQLite database file path |
| Storage | `data_retention_days` | Data retention period |
| Probes | `target_uid` | Filter events by UID |
| Probes | `poll_timeout_ms` | Ring buffer poll timeout |
| HTTP | `connection_cache_capacity` | LRU cache size for connection tracking |
| SLS | `sls_endpoint` / `sls_project` / `sls_logstore` | Alibaba Cloud SLS export settings |
| Tokenizer | `tokenizer_file` | Path or URL to HuggingFace tokenizer |

## Supported LLM Providers

Token parsing supports multiple LLM API formats:

- OpenAI / OpenAI-compatible APIs
- Anthropic (Claude, including cache token handling)
- Google Gemini
- Qwen (with native chat template support)

## Origins

This project is derived from [https://github.com/eunomia-bpf/agentsight.git](https://github.com/eunomia-bpf/agentsight.git).

## License

Apache License 2.0 — see [LICENSE](../../LICENSE) for details.
