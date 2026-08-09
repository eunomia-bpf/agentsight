# Supported Agents

AgentSight works with any process that makes TLS-encrypted API calls. This page covers agent-specific setup and quirks.

For general usage and the `record` command, see the [README](https://github.com/eunomia-bpf/agentsight#quick-start).

## Zero-Config: `record`

`record` is the simplest way to trace an agent. Put the command you want to run
after `record --`; AgentSight handles everything else:

```bash
sudo ./agentsight record -- claude
sudo ./agentsight record -- claude -p "review my last commit"
sudo ./agentsight record -- python my_agent.py
sudo ./agentsight record -- node ./cli.js
```

What `record -- <command>` does automatically:

1. **Discovers the SSL binary** — resolves the command via `$PATH`, follows
   symlinks (e.g. `claude` → `~/.local/share/claude/versions/2.1.150`), and
   chases shebang wrappers (e.g. a `#!/usr/bin/env node` script → the real
   `node` ELF) so uprobes attach to the correct executable.
2. **Derives the `--comm` process filter** from the command name.
3. **Launches the agent** with your terminal attached (its TUI/REPL works
   normally) while SSL + process + system monitoring runs quietly in the
   background.
4. **Stops automatically** when the agent process exits.

> **`sudo` note**: under `sudo`, `record` still finds *your* user-local installs
> (it reads `$SUDO_USER`'s home for `~/.local/bin`, `~/bin`, and `~/.nvm`), so
> `sudo ./agentsight record -- claude` traces the claude in your home directory,
> not a different one on root's `$PATH`.

Useful flags: `--binary-path <path>` to override auto-discovery, `--no-server`
to disable the web UI, and `--server-port <port>`.

## Claude Code

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
sudo ./agentsight debug trace --comm claude \
  --binary-path "$CLAUDE_BIN" --server --server-port 8080
```

This captures:
- **Conversation API**: `POST /v1/messages` requests with full prompt/response SSE streaming
- **Telemetry**: heartbeat, event logging, Datadog logs
- **Process activity**: file operations, subprocess executions

> **Note**: All SSL traffic in Claude flows through an internal "HTTP Client"
> thread, not the main "claude" thread. When `--binary-path` is specified,
> the `--comm` filter is automatically skipped for SSL monitoring (but still
> applied for process monitoring) to ensure traffic is captured correctly.

## Python AI Tools (aider, open-interpreter, etc.)

```bash
# Monitor aider, open-interpreter, or any Python-based AI tool
sudo ./agentsight record -c "python"

# Custom web UI port
sudo ./agentsight record -c "python" --server-port 8080
```

## Node.js AI Tools (Gemini CLI, etc.)

> **Important**: Node.js (both NVM and system installs) **statically links
> OpenSSL into the `node` binary** — there is no system `libssl.so` to hook.
> SSL capture therefore requires pointing sslsniff at the `node` binary itself.

The easiest way is `record -- <command>`, which discovers the `node` binary automatically:

```bash
# Gemini CLI runs on Node — record finds the right binary and traces it
sudo ./agentsight record -- gemini
```

With `record`, AgentSight now auto-discovers the Node binary from `-c node`
(it detects that Node embeds OpenSSL and attaches to the binary instead of a
system library), so this just works without `--binary-path`:

```bash
# Monitor Gemini CLI or other Node.js AI tools — binary auto-discovered
sudo ./agentsight record -c node

# Pin the binary explicitly if auto-discovery picks the wrong Node install
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node
```

> **Behind an HTTP/HTTPS proxy?** Traffic is still TLS-encrypted inside the
> Node process (the proxy only tunnels it), so AgentSight captures it the same
> way — at the `SSL_read`/`SSL_write` calls before encryption.

## IDE-Based Agents (Cursor, Antigravity, Windsurf)

Agents built into Electron IDEs do not work with `record` or `debug trace`, and
pointing `--binary-path` at the app does not change that. Three separate things
get in the way, and only the first one is obvious:

1. **Platform.** These are desktop apps, and most installs run on macOS or
   Windows. The eBPF probes are Linux-only, so on those systems there is
   nothing to attach to in the first place.

2. **Attach.** Electron bundles BoringSSL inside its framework binary
   (`Electron Framework`, hundreds of megabytes, stripped). The launcher that
   `--binary-path` auto-discovery resolves is a small stub with no SSL code in
   it, and the network stack runs in a helper process, so a `--comm` filter on
   the app name drops the traffic. This is the same class of problem as the
   Claude Code "HTTP Client" thread described above, only across processes
   instead of threads.

3. **Payload.** Even with probes attached to the right binary, capture alone
   is not enough. Cursor, for example, talks to its backend over the Connect
   protocol: HTTP/2 with protobuf message bodies. AgentSight handles HTTP/2
   framing, but it recognizes LLM calls by their JSON bodies, so protobuf
   traffic produces no LLM events. The capture succeeds and the timeline stays
   empty anyway.

For these agents, use the agent-native session path instead: AgentSight reads
the session files the IDE itself writes on disk, the same way it reads local
Claude Code, Codex, and Gemini CLI sessions. That route needs no eBPF, no
`sudo`, and works on macOS and Windows. Cursor is supported this way today;
the next section covers it.

## Cursor

There is nothing to launch or attach. If Cursor has run on the machine, its
agent sessions show up next to Claude Code, Codex, and Gemini CLI ones:

```bash
agentsight top             # live ranked view includes Cursor sessions
agentsight report --local  # summarize native sessions without a recorded DB
agentsight vis             # replay Cursor file activity in a repository
```

AgentSight reads two local sources, both strictly read-only and safe while
Cursor is running:

- **Transcripts** under `~/.cursor/projects/<workspace>/agent-transcripts/`:
  prompts, assistant output, tool calls, file activity, and per-event
  timestamps. When Cursor delegates work through its `Task` tool, the
  delegated runs are folded into the parent session, so a session that split
  its work across sub-agents still reports everything it did.
- **Cursor's state database** (`state.vscdb` under Cursor's user data
  directory): session start and end times, the model, and the working
  directory when the transcript doesn't carry one.

Two things not to expect:

- **Live request and response bodies.** That is TLS capture, which does not
  work on Electron IDEs for the reasons above. Cursor sessions show what the
  agent did, not the raw API traffic.
- **Token counts on current versions.** Cursor stopped recording per-turn
  usage locally around March 2026. Sessions old enough to carry usage events
  show token totals; newer ones show none, and that is expected rather than a
  capture failure.

## Containers and Kubernetes Pods

For an agent running inside a Docker container, pass the container to
`--binary-path` with the `docker://` scheme. AgentSight resolves the container's
process tree and attaches sslsniff to the right binary automatically:

```bash
# OpenClaw is a Node.js agent that runs in a container — works out of the box
sudo ./agentsight record -c node --binary-path docker://openclaw

# Accepts a container name or ID; supported by record, debug trace, and debug ssl
sudo ./agentsight debug trace --binary-path docker://openclaw --server
```

`docker inspect` reports the container's *init* process (often `tini`), which
has no SSL code. AgentSight walks the descendant process tree and attaches to the
first process whose binary actually embeds SSL (the `node` process). See
[docs/openclaw.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/experiment/openclaw.md) for the full walkthrough.

For a Kubernetes Pod, run AgentSight on the node that hosts the Pod and pass a
`k8s://` reference. AgentSight uses `kubectl` to read the Pod's `containerID`,
then uses Docker or CRI (`crictl`) to find the host PID before scanning the
container process tree:

```bash
# Single-container Pod in the default namespace
sudo ./agentsight record -c node --binary-path k8s://openclaw

# Pod in a namespace
sudo ./agentsight record -c node --binary-path k8s://agents/openclaw

# Multi-container Pod; specify the container name
sudo ./agentsight record -c node --binary-path k8s://agents/openclaw/gateway

# Supported by debug trace and debug ssl too
sudo ./agentsight debug trace --binary-path k8s://agents/openclaw/gateway --server
```

The accepted forms are `k8s://pod`, `k8s://namespace/pod`, and
`k8s://namespace/pod/container` (`kubernetes://` works as an alias). For
containerd or CRI-O clusters, `crictl` must be installed and configured on that
node. For Docker-backed clusters, Docker inspection is used directly. When
running under `sudo`, AgentSight falls back to the invoking user's
`~/.kube/config` if `KUBECONFIG` is not set; use `sudo -E` if you rely on a
custom `KUBECONFIG`.

## Browser Plaintext Capture

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

## Local MCP over stdio

For local MCP servers that communicate over `stdio` instead of HTTP/TLS, use
the standalone `stdiocap` BPF tool:

```bash
# Capture stdin/stdout/stderr payloads for a local MCP server process
sudo ./bpf/stdiocap -p <mcp_server_pid>
```

AgentSight also includes a minimal MCP fixture for local testing under
[`docs/mcp-test/README.md`](https://github.com/eunomia-bpf/agentsight/blob/master/docs/experiment/mcp-test/README.md). It provides both `stdio`
and HTTP test modes so you can generate predictable MCP traffic before wiring
it into the Rust collector.

## Advanced Monitoring

```bash
# Combined SSL and process monitoring with web interface
sudo ./agentsight debug trace --server

# Custom web UI port
sudo ./agentsight record -c "python" --server-port 8080
```

## Direct eBPF Program Usage

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
