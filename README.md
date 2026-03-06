# AgentSight: Zero-Instrumentation LLM Agent Observability with eBPF

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/eunomia-bpf/agentsight)

AgentSight is a observability tool designed specifically for monitoring LLM agent behavior through SSL/TLS traffic interception and process monitoring. Unlike traditional application-level instrumentation, AgentSight observes at the system boundary using eBPF technology, providing comprehensive insights into AI agent interactions with minimal performance overhead.

**✨ Zero Instrumentation Required** - No code changes, no new dependencies, no SDKs. Works with any AI framework or application out of the box.

## Quick Start

```bash
wget https://github.com/eunomia-bpf/agentsight/releases/latest/download/agentsight && chmod +x agentsight
# Record Claude Code activity (Bun-based, requires --binary-path for statically-linked BoringSSL)
sudo ./agentsight record -c claude --binary-path ~/.local/share/claude/versions/$(claude --version | head -1)
# Record agent behavior from claude (old version)
sudo ./agentsight record -c "claude"
# Record agent behavior from gemini-cli (comm is "node")
sudo ./agentsight record -c "node"
# For Python AI tools (e.g. aider, open-interpreter)
sudo ./agentsight record -c "python"
# For Node.js apps with NVM (statically-linked OpenSSL)
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node
```

Visit [http://127.0.0.1:7395](http://127.0.0.1:7395) to view the recorded data.

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-tree.png" alt="AgentSight Demo - Process Tree Visualization" width="800">
  <p><em>Real-time process tree visualization showing AI agent interactions and file operations</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-timeline.png" alt="AgentSight Demo - Timeline Visualization" width="800">
  <p><em>Real-time timeline visualization showing AI agent interactions and system calls</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-metrics.png" alt="AgentSight Demo - Metrics Visualization" width="800">
  <p><em>Real-time metrics visualization showing AI agent memory and CPU usage</em></p>
</div>

## 🚀 Why AgentSight?

### Traditional Observability vs. System-Level Monitoring

| **Challenge** | **Application-Level Tools** | **AgentSight Solution** |
|---------------|----------------------------|------------------------|
| **Framework Adoption** | ❌ New SDK/proxy for each framework | ✅ Drop-in daemon, no code changes |
| **Closed-Source Tools** | ❌ Limited visibility into operations | ✅ Complete visibility into prompts & behaviors |
| **Dynamic Agent Behavior** | ❌ Logs can be silenced or manipulated | ✅ Kernel-level hooks for reliable monitoring |
| **Encrypted Traffic** | ❌ Only sees wrapper outputs | ✅ Captures real unencrypted requests/responses |
| **System Interactions** | ❌ Misses subprocess executions | ✅ Tracks all process behaviors & file operations |
| **Multi-Agent Systems** | ❌ Isolated per-process tracing | ✅ Global correlation and analysis |

AgentSight captures critical interactions that application-level tools miss:

- Subprocess executions that bypass instrumentation
- Raw encrypted payloads before agent processing
- File operations and system resource access  
- Cross-agent communications and coordination

## 🏗️ Architecture

```ascii
┌─────────────────────────────────────────────────┐
│              AI Agent Runtime                   │
│   ┌─────────────────────────────────────────┐   │
│   │    Application-Level Observability      │   │
│   │  (LangSmith, Helicone, Langfuse, etc.)  │   │
│   │         🔴 Can be bypassed               │   │
│   └─────────────────────────────────────────┘   │
│                     ↕ (Can be bypassed)         │
├─────────────────────────────────────────────────┤ ← System Boundary
│  🟢 AgentSight eBPF Monitoring (Kernel-level)   │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │   SSL Traffic   │  │    Process Events   │   │
│  │   Monitoring    │  │    Monitoring       │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Rust Streaming Analysis Framework       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────┐  │
│  │   Runners   │  │  Analyzers   │  │ Output │  │
│  │ (Collectors)│  │ (Processors) │  │        │  │
│  └─────────────┘  └──────────────┘  └────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Frontend Visualization                │
│     Timeline • Process Tree • Event Logs       │
└─────────────────────────────────────────────────┘
```

### Core Components

1. **eBPF Data Collection** (Kernel Space)
   - **SSL Monitor**: Intercepts SSL/TLS read/write operations via uprobe hooks
   - **Process Monitor**: Tracks process lifecycle and file operations via tracepoints
   - **<3% Performance Overhead**: Operates below application layer with minimal impact

2. **Rust Streaming Framework** (User Space)
   - **Runners**: Execute eBPF programs and stream JSON events (SSL, Process, Agent, Combined)
   - **Analyzers**: Pluggable processors for HTTP parsing, chunk merging, filtering, logging
   - **Event System**: Standardized event format with rich metadata and JSON payloads

3. **Frontend Visualization** (React/TypeScript)
   - Interactive timeline, process tree, and log views
   - Real-time data streaming and analysis
   - See "Web Interface Access" section for details

### Data Flow Pipeline

```
eBPF Programs → JSON Events → Runners → Analyzer Chain → Frontend/Storage/Output
```

## Usage

### Prerequisites

- **Linux kernel**: 4.1+ with eBPF support (5.0+ recommended)
- **Root privileges**: Required for eBPF program loading
- **Rust toolchain**: 1.88.0+ (for building collector)
- **Node.js**: 18+ (for frontend development)
- **Build tools**: clang, llvm, libelf-dev

### Installation

#### Option 1: Using Docker (Recommended)

AgentSight runs in Docker with `--privileged` for eBPF, `--pid=host` to access host processes, `-v /sys:/sys:ro` for process monitoring, and `-v /usr:/usr:ro -v /lib:/lib:ro` for SSL library access (required to attach uprobes to shared libraries like `libssl.so`). Example:

```bash
# Monitor Python AI tools
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm python --log-file /logs/record.log

# Monitor Claude Code (mount home dir for binary access)
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $HOME/.local/share/claude:/claude:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm claude --binary-path /claude/versions/2.1.39 --log-file /logs/record.log
```

#### Option 2: Build from Source

```bash
# Clone repository with submodules
git clone https://github.com/eunomia-bpf/agentsight.git --recursive
cd agentsight

# Install system dependencies (Ubuntu/Debian)
make install

# Build all components (frontend, eBPF, and Rust)
make build

# Or build individually:
# make build-frontend  # Build frontend assets
# make build-bpf       # Build eBPF programs
# make build-rust      # Build Rust collector

```

### Usage Examples

#### Monitoring Claude Code

Claude Code is a Bun-based application with BoringSSL statically linked and
symbols stripped. AgentSight auto-detects BoringSSL functions via byte-pattern
matching when `--binary-path` is provided:

```bash
# Find the Claude binary version
CLAUDE_BIN=~/.local/share/claude/versions/$(claude --version | head -1)

# Record all Claude activity with web UI
sudo ./agentsight record -c claude --binary-path "$CLAUDE_BIN"
# Open http://127.0.0.1:7395 to view timeline

# Advanced: full trace with custom filters
sudo ./agentsight trace --ssl true --process true --comm claude \
  --binary-path "$CLAUDE_BIN" --server true --server-port 8080
```

This captures:
- **Conversation API**: `POST /v1/messages` requests with full prompt/response SSE streaming
- **Telemetry**: heartbeat, event logging, Datadog logs
- **Process activity**: file operations, subprocess executions

> **Note**: All SSL traffic in Claude flows through an internal "HTTP Client"
> thread, not the main "claude" thread. When `--binary-path` is specified,
> the `--comm` filter is automatically skipped for SSL monitoring (but still
> applied for process monitoring) to ensure traffic is captured correctly.

#### Monitoring Python AI Tools

```bash
# Monitor aider, open-interpreter, or any Python-based AI tool
sudo ./agentsight record -c "python"

# Custom port and log file
sudo ./agentsight record -c "python" --server-port 8080 --log-file /tmp/agent.log
```

#### Monitoring Node.js AI Tools (Gemini CLI, etc.)

For Node.js applications installed via NVM that statically link OpenSSL, use
`--binary-path` to point to the actual Node.js binary:

```bash
# Monitor Gemini CLI or other Node.js AI tools
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node

# Or with system Node.js (uses dynamic libssl, no --binary-path needed)
sudo ./agentsight record -c node
```

#### Advanced Monitoring

```bash
# Combined SSL and process monitoring with web interface
sudo ./agentsight trace --ssl true --process true --server true

# Custom port and log file
sudo ./agentsight record -c "python" --server-port 8080 --log-file /tmp/agent.log
```

#### Browser Plaintext Capture

For browser-specific plaintext capture, use the standalone `browsertrace` BPF
tool instead of `sslsniff`:

```bash
# Chrome / Chromium
sudo ./bpf/browsertrace --binary-path /opt/google/chrome/chrome

# Firefox on Ubuntu Snap
sudo ./bpf/browsertrace --binary-path /snap/firefox/current/usr/lib/firefox/firefox
```

> **Note**: On Ubuntu, `/usr/bin/firefox` is often a wrapper script rather than
> the real browser ELF. Point `browsertrace` at the actual Firefox binary.

#### Local MCP over stdio

For local MCP servers that communicate over `stdio` instead of HTTP/TLS, use
the standalone `stdiocap` BPF tool:

```bash
# Capture stdin/stdout/stderr payloads for a local MCP server process
sudo ./bpf/stdiocap -p <mcp_server_pid>
```

AgentSight also includes a minimal MCP fixture for local testing under
[`docs/mcp-test/README.md`](docs/mcp-test/README.md). It provides both `stdio`
and HTTP test modes so you can generate predictable MCP traffic before wiring
it into the Rust collector.

#### Direct eBPF Program Usage

```bash
# Run sslsniff directly on Claude binary
sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39

# Run sslsniff on NVM Node.js
sudo ./bpf/sslsniff --binary-path ~/.nvm/versions/node/v20.0.0/bin/node --verbose

# Run browsertrace directly on Chrome
sudo ./bpf/browsertrace --binary-path /opt/google/chrome/chrome

# Run stdiocap directly on a local MCP server PID
sudo ./bpf/stdiocap -p 12345

# Run process tracer
sudo ./bpf/process -c python
```

#### Web Interface Access

All monitoring commands with `--server` flag provide web visualization at:
- **Timeline View**: http://127.0.0.1:7395/timeline
- **Process Tree**: http://127.0.0.1:7395/tree
- **Raw Logs**: http://127.0.0.1:7395/logs


## ❓ Frequently Asked Questions

### General

**Q: How does AgentSight differ from traditional APM tools?**
A: AgentSight operates at the kernel level using eBPF, providing system-level monitoring that is independent of application code. Traditional APM requires instrumentation that can be modified or disabled.

**Q: What's the performance impact?**
A: Less than 3% CPU overhead due to optimized eBPF kernel-space data collection.

**Q: Can agents detect they're being monitored?**  
A: Detection is extremely difficult since monitoring occurs at the kernel level without code modification.

### Technical

**Q: Which Linux distributions are supported?**
A: Any distribution with kernel 4.1+ (5.0+ recommended). Tested on Ubuntu 20.04+, CentOS 8+, RHEL 8+.

**Q: Can I monitor multiple agents simultaneously?**  
A: Yes, use combined monitoring modes for concurrent multi-agent observation with correlation.

**Q: How do I filter sensitive data?**  
A: Built-in analyzers can remove authentication headers and filter specific content patterns.

**Q: Why doesn't AgentSight capture traffic from Claude Code or NVM Node.js?**
A: These applications statically link their SSL library (BoringSSL for Claude/Bun, OpenSSL for NVM Node.js) instead of using system `libssl.so`. Use `--binary-path` to point to the actual binary so AgentSight can auto-detect SSL functions via byte-pattern matching. See the "Monitoring Claude Code" and "Monitoring Node.js AI Tools" sections for examples.

**Q: Why does `--comm claude` not capture SSL traffic?**
A: Claude Code's SSL traffic runs on an internal "HTTP Client" thread, not the main "claude" thread. The `--comm` filter in sslsniff matches thread name (from `bpf_get_current_comm()`), not process name. When using `--binary-path`, the collector automatically skips the `--comm` filter for SSL monitoring.

### Troubleshooting

**Q: "Permission denied" errors**  
A: Ensure you're running with `sudo` or have `CAP_BPF` and `CAP_SYS_ADMIN` capabilities.

**Q: "Failed to load eBPF program" errors**
A: Verify kernel version meets requirements (see Prerequisites). Update vmlinux.h for your architecture if needed.


## 🤝 Contributing

We welcome contributions! After cloning and building (see Installation above), you can:

```bash
# Run tests
make test

# Frontend development server
cd frontend && npm run dev

# Build debug versions with AddressSanitizer
make -C bpf debug
```

### Key Resources

- [CLAUDE.md](CLAUDE.md) - Project guidelines and architecture
- [collector/DESIGN.md](collector/DESIGN.md) - Framework design details
- [docs/why.md](docs/why.md) - Problem analysis and motivation

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**💡 The Future of AI Observability**: As AI agents become more autonomous and capable of self-modification, traditional observability approaches become insufficient. AgentSight provides independent, system-level monitoring for safe AI deployment at scale.
