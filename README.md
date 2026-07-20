# AgentSight: System-wide AI agent profiling and monitoring with eBPF

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eunomia-bpf/agentsight/actions/workflows/ci.yml/badge.svg)](https://github.com/eunomia-bpf/agentsight/actions/workflows/ci.yml)
[![arXiv:2508.02736](https://img.shields.io/badge/arXiv-2508.02736-b31b1b.svg)](https://arxiv.org/abs/2508.02736)
[![DOI:10.1145/3766882.3767169](https://img.shields.io/badge/DOI-10.1145%2F3766882.3767169-blue.svg)](https://dl.acm.org/doi/10.1145/3766882.3767169)

**English** | [中文](https://github.com/eunomia-bpf/agentsight/blob/master/README.zh-CN.md)

AI agents can run commands, rewrite files, spawn processes, and contact remote services—but when a run fails, stalls, or behaves unexpectedly, their logs rarely tell the whole story.

AgentSight is a local-first `top`/`strace`-like observability tool for AI agents. It connects prompts, model calls, and tool decisions to their real effects on your machine.

- **See what the agent is doing now.** Monitor active sessions, processes, resource, model and tool calls, file and network activity.
- **Understand failures and improve agent behavior.** Connect prompts and skills to errors, then turn them into better instructions and skills.
- **Find where time, tokens, and resources go.** Spot slow steps, retry loops, repeated model or tool calls, token-heavy sessions, and resource-hungry processes.
- **Audit data movement and security-sensitive effects.** See which services received requests, which files changed, and whether agents stayed and give safety/security suggestions.
- **Use it with your existing agents.** Run AgentSight around Claude Code, Codex, Gemini CLI, OpenCode, OpenClaw, or any command—without an SDK, proxy, or vendor integration.

No SDK, no proxy, no vendor integration. AgentSight observes with eBPF and TLS traffic tracing, so it works even when the agent is a
closed-source CLI. **✨ Zero SDK Required**

## Quick Start

```bash
cargo install agentsight
# or: wget https://github.com/eunomia-bpf/agentsight/releases/latest/download/agentsight && chmod +x agentsight
agentsight vis
agentsight top
```

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/agentsight-agent-nebula.gif" alt="Agent Nebula replay of Agent development across the AgentSight repository" width="1000">
  <p><em>Agent Nebula replays how coding agents read, write, create, rename, and delete files across this repository</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/top-mode-demo.png" alt="AgentSight top live session view" width="1000">
  <p><em>Live sessions ranked by model, session tokens, health, process family, tool calls, file activity, and network activity</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/semantic-flamegraph-top200.svg" alt="Semantic flamegraph of the top 200 agent stacks" width="1000">
  <p><em>Width is system-effect weight; the uneven stack height shows prompt, tool-call, process, and effect paths ending at different depths. See the <a href="docs/agentpprof.md#example-flamegraphs">agentpprof guide</a> for the other profiles and how widths and stack depths are drawn.</em></p>
</div>

## 🚀 Why AgentSight?

### Traditional Observability vs. System-Level Monitoring

Application-level tools such as [LangSmith](https://docs.langchain.com/langsmith/observability-concepts), [Langfuse](https://langfuse.com/docs/observability/overview), and [Phoenix](https://arize.com/docs/phoenix/) are great for traces, prompts, tokens, evals, and latency when you own the application code. Gateway/proxy tools such as [Helicone](https://docs.helicone.ai/getting-started/integration-method/gateway) are useful when you can route provider traffic through a managed endpoint.

AgentSight focuses on the layer those tools often miss: what the agent actually does at the system boundary. It observes existing binaries and CLI agents without SDKs or proxies, then correlates LLM traffic with process execution, file access, and system activity.

| **Challenge** | **Application-Level Tools** | **AgentSight Solution** |
|---------------|----------------------------|------------------------|
| **Framework Adoption** | ❌ SDK, callback, or gateway integration per app | ✅ Drop-in system tracer, no code changes |
| **Closed-Source CLIs** | ❌ Limited to what the tool exposes or logs | ✅ Observes existing binaries and CLI agents from outside |
| **Agent-Controlled Logs** | ❌ Logs can be incomplete, disabled, or modified | ✅ Kernel-level events independent of app logging |
| **TLS LLM Traffic** | ❌ Visible when routed through SDKs/proxies | ✅ Captures plaintext at SSL/TLS calls without a proxy |
| **System Actions** | ❌ Often misses subprocesses and local file activity | ✅ Tracks process execution, file access, and resource use |
| **Cross-Boundary Behavior** | ❌ Traces usually stop at framework/process boundaries | ✅ Correlates LLM traffic with process and file events |

AgentSight captures critical interactions that application-level tools miss:

- Subprocess executions that bypass instrumentation
- Plaintext LLM payloads at SSL/TLS call boundaries
- File operations and system resource access  
- Cross-boundary behavior across LLM, process, and file events

## Usage

### Prerequisites

- **Linux kernel**: 4.1+ with eBPF support (5.0+ recommended)
- **sudo access**: optional for `top`; eBPF is enabled automatically when sudo is already available

For source builds, see [docs/build.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/build.md).

### Installation

#### Cargo or Release Binary

For local use, install with `cargo install agentsight` or download the latest
release binary, then start with `agentsight top`. Use the examples below when
you want to record a specific command or inspect saved sessions.

#### Docker

Docker is useful for container, CI, or isolated Linux environments, but it still needs privileged host access for eBPF. See [docs/docker.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/docker.md).

#### Build from Source

Build requirements and source build commands live in [docs/build.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/build.md).

### Replay a Repository Session

Run `agentsight vis` inside a Git worktree. It scans matching local Claude,
Codex, and Gemini sessions without sudo, then writes an animated replay to
`output/agent-nebula.gif`:

```bash
cd your-repository
agentsight vis
```

GIF export requires local Chromium and FFmpeg. Use
`agentsight vis -o output/agent-nebula.html` for a self-contained HTML artifact
that needs neither dependency to generate.

### Querying Past Sessions

Every `record` session is automatically saved to an `agentsight-*.db` SQLite
file in the current directory. Start with the live and record commands, then
use `agentsight report` for structured queries:

```bash
agentsight top                               # live ranked view; uses eBPF when sudo is already available
agentsight monitor install-service           # install/start the background monitor service
agentsight report --db run.db                 # summary of a specific saved run
sudo agentsight record -- claude             # record a command
agentsight report                            # high-level latest-run summary (default)
agentsight report list                       # recorded sessions in this directory
agentsight report prompts --json             # full LLM request/response JSON
agentsight report token                      # token usage from latest DB, or local agent sessions
agentsight report token --group-by dir       # token usage by session/process working directory
agentsight report audit --json               # process spawns, file opens, API calls
agentsight report serve                      # open the web UI for the latest session in this directory
agentsight report export -o snapshot.json    # export for web dashboard
agentsight report --local                    # summarize native Claude/Codex/Gemini sessions
```

### Offline Agent pprof Profiles

Use `agentpprof` when you want a no-sudo pprof/folded-stack/SVG summary of
local Codex or Claude session history:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- \
  --project-root . \
  --view tokens \
  -o agent.pb.gz

go tool pprof -top agent.pb.gz
```

The `tokens` view is the best first flamegraph for cost analysis: it aggregates
real local Codex/Claude development sessions by project, agent, session tag,
prompt tag, model, and token kind.

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/bpf-benchmark-tokens.svg" alt="agentpprof token flamegraph from real bpf-benchmark development sessions" width="1000">
  <p><em>Offline token profile generated from real local bpf-benchmark coding-agent sessions</em></p>
</div>

See [agentpprof/README.md](agentpprof/README.md) for CLI details and the
[agentpprof profiling guide](docs/agentpprof.md#example-flamegraphs) for
flamegraph examples, rendering, view selection, and deterministic tagging rules.

### Web Interface

During a session, visit [http://127.0.0.1:7395](http://127.0.0.1:7395) for live traffic, process trees, and metrics:
- **Timeline View**: http://127.0.0.1:7395/timeline
- **Process Tree**: http://127.0.0.1:7395/tree
- **Event Log**: http://127.0.0.1:7395/logs
- **Metrics View**: http://127.0.0.1:7395/metrics

For a saved SQLite session, run `agentsight report serve --db run.db` and open the same routes.

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-tree.png" alt="AgentSight Demo - Process Tree Visualization" width="800">
  <p><em>Process tree visualization for agent subprocesses and file activity</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-timeline.png" alt="AgentSight Demo - Timeline Visualization" width="800">
  <p><em>Timeline visualization for LLM, process, file, and network events</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-metrics.png" alt="AgentSight Demo - Metrics Visualization" width="800">
  <p><em>Metrics visualization for memory and CPU usage</em></p>
</div>

<div align="center">
  <p><strong>Try the <a href="https://agentsight.us">live demo</a></strong> to explore a real recorded Claude Code session in the browser.</p>
</div>

### Supported Agents

> **Privileges:** eBPF probes need root. Use `sudo` for live capture commands.

`record` auto-discovers binaries, SSL libraries, and container processes. Works out of the box for:

| Agent | Command |
|-------|---------|
| Claude Code | `sudo ./agentsight record -- claude` |
| Gemini CLI | `sudo ./agentsight record -- gemini` |
| Python (aider, open-interpreter, …) | `sudo ./agentsight record -c python` |
| Docker containers (OpenClaw, …) | `sudo ./agentsight record -c node --binary-path docker://openclaw` |
| Any command | `sudo ./agentsight record -- <command>` |

See [docs/agents.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/agents.md) for agent-specific setup, SSL quirks, browser capture, MCP stdio, and advanced flags.

### OpenTelemetry Export

AgentSight can export captured LLM calls as OpenTelemetry **GenAI**
(`gen_ai.*`) spans over OTLP/HTTP — standards-compliant agent telemetry for any
agent, with zero in-process instrumentation.

```bash
sudo ./agentsight debug trace --otel --otel-endpoint http://localhost:4318
```

See [docs/otel.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/otel.md) for
collector setup and backend integration.

## ❓ Frequently Asked Questions

**Q: What permissions does AgentSight need?**
A: `top` uses live eBPF process capture when you run it with sudo or your user already has passwordless/cached sudo. Without eBPF privileges, it falls back to process snapshots and native agent session files. With `record -- <command>`, the monitored agent still runs as your normal user; only the probes are elevated.

**Q: What's the performance impact?**
A: Our evaluation reports less than 3% CPU overhead for typical traced agent workloads.

**Q: Where does captured data go?**
A: `record` stores sessions as `agentsight-*.db` files in the current directory by default, and `report` reads the latest matching file from that directory unless you pass `--db`. When no default DB exists, report commands warn and fall back to local Claude/Codex/Gemini agent sessions where available. `monitor` stores its weekly background DBs under `~/.agentsight/monitor`, while `top` only shows live sessions. Use `agentsight report`, `agentsight report list`, `agentsight report audit --json`, and `agentsight report token` to inspect prior runs. Captured data can include prompts, responses, paths, headers, and network targets, so treat logs and DBs as sensitive.

**Q: Why doesn't AgentSight capture traffic from Claude Code, Node.js, or Gemini CLI?**
A: These applications statically link their SSL library (BoringSSL for Claude/Bun, OpenSSL for **all** Node.js — both NVM and system installs) into their own binary instead of using system `libssl.so`, so there's nothing for sslsniff to hook by default. AgentSight handles this for you: `record -- <command>` always discovers the binary, and `record -c node` now auto-discovers the Node binary too. For Claude attach mode, pass `--binary-path`. See the "Zero-Config: record" and "Monitoring Node.js AI Tools" sections.

**Q: What should I check if tracing fails?**
A: Verify you are on Linux with eBPF support, have `sudo` or `CAP_BPF`/`CAP_SYS_ADMIN`, and are using `record -- <command>` or the correct `--binary-path` for statically linked agents.

## 🤝 Contributing

We welcome contributions! After cloning and building (see [docs/build.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/build.md)), you can:

```bash
# Run tests
make test

# Frontend development server
cd frontend && npm run dev

# Build debug versions with AddressSanitizer
make -C bpf debug
```

### Key Resources

- [CLAUDE.md](https://github.com/eunomia-bpf/agentsight/blob/master/CLAUDE.md) - Project guidelines and architecture
- [docs/design/README.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/design/README.md) - archived design notes and research drafts

## 📄 License

MIT License - see [LICENSE](https://github.com/eunomia-bpf/agentsight/blob/master/LICENSE) for details.

---

**💡 The Future of AI Observability**: As AI agents become more autonomous and capable of self-modification, traditional observability approaches become insufficient. AgentSight provides independent, system-level monitoring for safe AI deployment at scale.
