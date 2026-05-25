# Monitoring OpenClaw with AgentSight

[OpenClaw](https://github.com/openclaw/openclaw) is a self-hosted personal AI
assistant that runs in Docker. It is built on **Node.js**, which **statically
links OpenSSL** into the `node` binary — there is no system `libssl.so` to hook,
so AgentSight must attach its SSL uprobe directly to the `node` executable.

AgentSight does this for you out of the box: point `--binary-path` at the
container with the `docker://` scheme and AgentSight resolves the right process
automatically. No `docker inspect`, no manual PID lookup, no code changes inside
OpenClaw.

```bash
# OpenClaw is running in a Docker container named "openclaw"
sudo ./agentsight record -c node --binary-path docker://openclaw
```

Open <http://127.0.0.1:7395> to watch OpenClaw's LLM prompts, tool calls, and
responses live — captured in plaintext at the kernel level.

## Why `docker://`?

`docker inspect --format '{{.State.Pid}}'` returns a container's **init**
process. OpenClaw's image runs `tini -s -- node openclaw.mjs gateway`, so the
init process is `tini`, which contains no SSL code. Attaching there would
capture nothing.

The `docker://<container>` scheme handles this: AgentSight looks up the init PID,
then walks the descendant process tree and attaches to the first process whose
executable actually embeds SSL (the `node` process). You see this in the log:

```
✓ Resolved container 'openclaw' (init PID 3176960) to SSL-embedding host PID 3177083 → /proc/3177083/exe
```

It accepts a container **name** or **ID**, and both `docker://name` and
`docker:name` forms work. The scheme is supported by the `record`, `trace`, and
`ssl` subcommands (anywhere `--binary-path` is accepted).

## End-to-end walkthrough

### 1. Start OpenClaw

```bash
docker run -d --name openclaw \
  -e OPENAI_API_KEY=sk-... \
  -e OPENCLAW_GATEWAY_TOKEN=your-token \
  ghcr.io/openclaw/openclaw:latest \
  node openclaw.mjs gateway
```

### 2. Attach AgentSight

```bash
sudo ./agentsight record -c node --binary-path docker://openclaw
```

`record` enables SSL + process + system monitoring and serves the web UI on port
7395 with agent-tuned filters. For finer control use `trace`:

```bash
sudo ./agentsight trace --binary-path docker://openclaw --server
```

Or raw SSL events only:

```bash
sudo ./agentsight ssl --binary-path docker://openclaw --http-parser
```

### 3. Trigger agent activity and view captures

Drive OpenClaw normally (via its channels, the gateway API, or `openclaw agent`).
Every HTTPS call OpenClaw makes to an LLM provider is decrypted at `SSL_write` /
`SSL_read` and surfaced in the UI. A captured request looks like:

```
POST /v1/responses HTTP/1.1
  host: api.openai.com
  authorization: Bearer sk-...        ← redacted by AuthHeaderRemover by default
  {"model":"...","input":[
    {"role":"developer","content":"You are a personal assistant ... ## Tooling ..."},
    {"role":"user","content":"What is eBPF?"}
  ]}
```

The full system prompt, tool definitions, and user message are all captured in
plaintext — no instrumentation inside OpenClaw required.

## How it works

```
OpenClaw container
  tini (init, State.Pid)            ← docker inspect points here
    └─ node openclaw.mjs gateway    ← AgentSight walks the tree and attaches here
         │ HTTPS to LLM API (OpenAI / Anthropic / …)
         ▼
   sslsniff (eBPF uprobe on SSL_read/SSL_write via /proc/<pid>/exe)
         │ decrypted plaintext
         ▼
   AgentSight analyzers → web UI / JSON log
```

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `container '<name>' is not running (host PID 0)` | The container is stopped. Start it and retry. |
| `docker inspect ... failed` | Wrong container name/ID, or the Docker CLI isn't on `$PATH`. AgentSight runs `docker inspect` under the hood. |
| No SSL events captured | Confirm the resolved PID is `node` (the log prints it). Plain HTTP is never captured — only TLS via `SSL_*`. |
| Resolved to the init PID, not node | OpenClaw isn't running inside the container yet, or no descendant embeds SSL. Wait for the gateway to be `ready`, then retry. |

## Notes

- OpenClaw pins a recent Node.js (v22+) whose statically-linked OpenSSL is
  detected by sslsniff's symbol lookup. This is the same mechanism that powers
  `record -c node` for NVM-installed Node (see the main README).
- The `--comm` filter is intentionally **not** passed to sslsniff when
  `--binary-path` is set: SSL traffic runs on a worker thread whose name differs
  from the process name, so a comm filter would drop all of it. `--binary-path`
  alone provides sufficient targeting.
