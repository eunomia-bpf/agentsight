# AgentFlame

AgentFlame is a Rust CLI for semantic flamegraphs over local AI coding-agent
history. It reads local Codex and Claude JSONL sessions with
`normalize-chat-sessions`, asks a real llama.cpp-compatible server for exactly
one lowercase word per session, prompt, and LLM call, then writes reusable JSON,
folded stacks, flamegraphs, and dashboard charts.

It is intentionally separate from the AgentSight collector. The first mode is
zero-instrumentation history analysis. AgentSight can later reuse
`agentflame.json` and `tags.json` to correlate exact
`tool_call -> shell -> child process -> file/network effect` streams with the
same semantic frames.

## Run

Build the CLI:

```bash
cargo build --release --manifest-path agentflame/Cargo.toml
```

Start a local llama.cpp server with a real GGUF model:

```bash
llama-server -m /path/to/model.gguf --port 8080
```

Generate an AgentFlame report:

```bash
./agentflame/target/release/agentflame run --project-root /path/to/repo
```

From this repository during development:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- run \
  --project-root . \
  --out .agentsight/agentflame/latest
```

Pass repeated `--session-file /path/to/session.jsonl` values to analyze a
specific set of real local sessions instead of scanning the newest files under
the Codex and Claude roots.

The default llama.cpp API endpoint is `http://127.0.0.1:8080`. Override it with:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- run \
  --llama-url http://127.0.0.1:8080 \
  --model local
```

AgentFlame has no heuristic label path. If the LLM server is missing, or if the
model does not return one valid lowercase word after retry, the run fails. The
default scope is session + prompt for system-effect views, plus per-LLM-call
tags for token views. For a faster exploratory run, pass
`--tag-llm-calls false`; the default is `true`.

## Benchmark Models

Benchmark real local models by letting AgentFlame start one llama.cpp server per
model:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench \
  --llama-server /path/to/llama-server \
  --runs 2 \
  --out .agentsight/agentflame/model-benchmarks.json \
  --model 3b=/path/to/model-3b.gguf \
  --model 1b=/path/to/model-1b.gguf \
  --model 0.6b=/path/to/model-0.6b.gguf
```

Use repeated `--server-arg` values for model-specific llama.cpp options, for
example `--server-arg=--reasoning --server-arg=off` for no-thinking tag runs.

The benchmark writes latency, success count, and invalid-output errors for each
real model. It does not synthesize model responses.

## AgentSight Web

When AgentSight Web is started from the project root, the `/agentflame` tab reads:

```text
.agentsight/agentflame/latest/agentflame.json
```

and serves generated SVG/HTML artifacts through:

```text
/api/v1/agentflame/artifacts/<artifact>
```

This keeps semantic tagging out of the collector hot path. AgentFlame owns local
history parsing and one-word LLM tags; AgentSight owns exact runtime provenance
and can join those tags with `tool_call -> shell -> child process ->
file/network effect` data.

## Outputs

Default output directory:

```text
.agentsight/agentflame/latest/
```

Important files:

- `agentflame.json`: redacted machine-readable analysis for AgentSight or other
  tools.
- `tags.json`: reusable local tag cache containing one-word tags, hashes, and
  LLM provenance, not raw prompt text.
- `index.html`: dashboard with summary cards, tag bars, command/effect bars,
  timeline, semantic flamegraphs, dimension projections, and mixed baseline
  buckets.
- `*.svg`: standalone charts also embedded by AgentSight Web.
- `semantic-system.folded.txt`: prompt/session-tagged system footprint stacks.
- `semantic-token.folded.txt`: prompt/session/LLM-tagged token stacks.
- `session-system.folded.txt`, `prompt-system.folded.txt`,
  `session-token.folded.txt`, `prompt-token.folded.txt`, `llm-token.folded.txt`:
  dimension projections.

## Folded Stack Shape

System-effect stacks use:

```text
project:<repo>;agent:<agent>;session:<sessionTag>;prompt:<promptTag>;call:tool/<kind>;process:<p0>;process:<p1>;effect:<effect>;path:<group>;status:<status>
```

Token stacks use:

```text
project:<repo>;agent:<agent>;session:<sessionTag>;prompt:<promptTag>;call:llm/<llmCallTag>;model:<model>;kind:<tokenKind>
```

The `process:*` segment can repeat. Offline session-history mode derives the
visible process entrypoint from shell commands, including simple shell wrappers
such as `bash -lc`. Exact child-process nesting is supplied by AgentSight runtime
trace data when the report is correlated with a captured snapshot.

## JSON Contract

`agentflame.json` uses stable top-level sections:

- `project`: project name and root.
- `inputs`: session roots and scan limits.
- `llm_tagger`: LLM request/cache/failure stats.
- `sessions`: per-session counts and redacted prompt tag rows.
- `summary`: stack totals, top prompt tags, command summaries, timeline, and
  baseline-mixing examples.
- `prompt_tags`: prompt hash to tag mapping.
- `artifacts`: relative paths to folded stacks and dashboard files.

This contract is meant to be consumed by AgentSight Web without re-reading raw
agent history.

## Development Test

```bash
cargo test --manifest-path agentflame/Cargo.toml
```
