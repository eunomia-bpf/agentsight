# Usage

**English** | [中文](https://github.com/eunomia-bpf/agentsight/blob/master/docs/usage.zh-CN.md)

## Building from Source

### 1. Clone the repository and initialize submodules

```sh
git clone https://github.com/eunomia-bpf/agentsight.git
cd agentsight
git submodule update --init --recursive
```

If you have already cloned the repository but the submodule directories (`libbpf/` and `bpftool/`) are empty, run:

```sh
git submodule update --init --recursive
```

### 2. Install system dependencies

```sh
make install
```

This installs the required build dependencies: libelf, zlib, clang, llvm, Node.js, and the Rust toolchain.

### 3. Build

```sh
make build
```

After a successful build, the agentsight binary is located at `collector/target/release/agentsight`.

You can also build individual components:

```sh
make build-bpf       # eBPF C programs only
make build-rust      # Rust collector only
make build-frontend  # Frontend only
```

## Running from Source

Navigate to the repository root after `make build`. Commands that load eBPF
probes should be run with `sudo`, except `top`, which can run without sudo and
uses live eBPF capture whenever sudo is already available. Without eBPF
privileges, it falls back to process snapshots and agent-native sessions.

```sh
# Live view of local agent sessions
./collector/target/release/agentsight top

# Launch and record a command
sudo ./collector/target/release/agentsight record -- claude

# Inspect the latest saved run
./collector/target/release/agentsight report

# Attach to an already-running process family
sudo ./collector/target/release/agentsight record -c claude

# Debug-level configurable tracing
sudo ./collector/target/release/agentsight debug trace --server -c claude

# Raw SSL debug capture with HTTP parsing
sudo ./collector/target/release/agentsight debug ssl --http-parser
```

Use `top` for the normal live view. Use `record` when you want a durable
agent-run artifact; it starts SSL, process, system, and web-view collection with
no default event filters, and saves a local SQLite session for `report`,
`report prompts`, and other report queries.

Use `debug trace` only when you need low-level control over capture sources or
explicit filters. It is the advanced replacement for a raw trace command, not
the normal record/report workflow.

## Open this machine in the hosted app

Run the unprivileged binding command to open this Node in the default hosted
frontend at `https://app.agentsight.us`:

```sh
agentsight bind
```

The command starts an API on `127.0.0.1:7395` by default, opens a binding link,
and remains in the foreground while the app reads AgentSight data. Without
`--db`, it reads live processes and the local agent session index; pass
`--db <capture.db>` to select a saved capture explicitly. The first screen is a
live, machine-level `top` view of
running and stopped agents, token use, coding plans, CPU, and RSS. Select a
session to open its conversation, process tree and AI prompts, timeline, and
detailed events; session CPU/RSS stays in that session header rather than a
separate metrics page. Session detail keeps the newest 1,000 prompts, 2,000
responses, and 2,000 tool events under bounded text budgets. The Node access key is stored in the OS AgentSight config
directory and reused across restarts. A binding link carries it to the browser
only in the URL fragment, which the SPA immediately removes from the visible
URL. Chrome may ask you to allow Local network access for a loopback or LAN Node.

Use `agentsight bind --no-open` to copy the link manually or `agentsight bind
--qr` to print the same link as a QR code. The endpoint and presentation plane
are not hard-coded: use `--listen <IP>` and `--server-port <PORT>` to choose the
socket, `--endpoint <URL>` when the browser reaches it through a different
hostname, tunnel, or HTTPS reverse proxy, and `--app-url <URL>` to open a
self-hosted static app. For example:

```sh
agentsight bind --listen 0.0.0.0 --server-port 7395 \
  --endpoint https://node.example.net \
  --app-url https://agentsight.example.net/
```

An unspecified listen address requires an explicit browser-reachable
`--endpoint`. A non-loopback Node should use browser-trusted HTTPS; private
transport alone does not override browser mixed-content rules. Treat the access
key as a long-lived secret: anyone who has it can use the Node API whenever that
Node is reachable. Direct requests do not pass through AgentSight Cloud. When
Controller Relay is enabled, selected requests and responses transit the Cloud
runtime but are not persisted in D1; sign-in stores account, organization and
Node coordination data. Self-hosted sign-in also requires building the SPA with
`NEXT_PUBLIC_CONTROL_PLANE_URL` pointed at the matching Worker and setting that
Worker's `APP_ORIGIN` to the SPA origin.

## Share Agent Nebula

`vis` reads local Claude, Codex, and Gemini sessions without sudo and produces
one self-contained Agent Nebula artifact per output file:

```sh
cd your-repository
agentsight vis
```

The default artifact is `output/agent-nebula.gif`. Specify `-o` only when you
want another path or format:

```sh
agentsight vis . --global \
  --compact-rate 30s \
  -o output/agent-nebula.html \
  -o output/agent-nebula.png \
  -o output/agent-nebula.gif \
  -o output/agent-nebula.mp4
```

HTML works without external assets. PNG, SVG, and MP4 require Chromium; GIF
additionally requires FFmpeg. Repeated `-o` values reuse one session scan and layout.
GIF/MP4 default to a 30-second compact replay whose frames are spaced uniformly
by action index; use `--compact-rate full` for one media frame per action. HTML
always keeps the full action timeline.
See [the Chinese algorithm specification](repository-nebula.zh-CN.md) for the
event boundary, force model, frame count, and export invariants.
