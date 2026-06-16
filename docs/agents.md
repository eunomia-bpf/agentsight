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

## Docker Containers (OpenClaw, etc.)

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
