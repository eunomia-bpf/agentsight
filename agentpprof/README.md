# agentpprof

`agentpprof` is a Rust CLI for pprof-style semantic profiles over local AI
coding-agent history. It reads local Codex and Claude JSONL sessions through
AgentSight's `agent-session` crate, asks a llama.cpp-compatible server for one
lowercase word per session, prompt, and LLM call, then writes reusable JSON,
folded stacks, SVG flamegraphs, and a local dashboard.

The profiles are semantic profiles, not CPU profiles. Width can represent tool
events or token counts, depending on the projection.

## Install

```bash
cargo install agentpprof
```

From this repository during development:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- run \
  --project-root . \
  --out .agentsight/agentpprof/latest
```

## Run

Start a local llama.cpp server with a real GGUF model:

```bash
llama-server -m /path/to/model.gguf --port 8080
```

Generate a report:

```bash
agentpprof run --project-root /path/to/repo
```

Pass repeated `--session-file /path/to/session.jsonl` values to analyze a
specific set of local sessions instead of scanning the newest files under the
Codex and Claude roots.

The default llama.cpp API endpoint is `http://127.0.0.1:8080`. Override it with:

```bash
agentpprof run \
  --llama-url http://127.0.0.1:8080 \
  --model local
```

`agentpprof` has no heuristic label path. If the LLM server is missing, or if
the model does not return one valid lowercase word after retry, the run fails.
The default scope is session + prompt for system-effect views, plus per-LLM-call
tags for token views. For a faster exploratory run, pass
`--tag-llm-calls false`; the default is `true`.

## Outputs

Default output directory:

```text
.agentsight/agentpprof/latest/
```

Important files:

- `agentpprof.json`: redacted machine-readable analysis for AgentSight or other
  tools.
- `tags.json`: reusable local tag cache containing one-word tags, hashes, and
  LLM provenance, not raw prompt text.
- `index.html`: dashboard with tag bars, command/effect bars, timeline,
  semantic flamegraphs, dimension projections, and mixed baseline buckets.
- `*.svg`: standalone charts.
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

`agentpprof.json` uses stable top-level sections:

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

## Benchmark Models

Benchmark real local models by letting `agentpprof` start one llama.cpp server
per model:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- bench \
  --llama-server /path/to/llama-server \
  --runs 2 \
  --out .agentsight/agentpprof/model-benchmarks.json \
  --model 3b=/path/to/model-3b.gguf \
  --model 1b=/path/to/model-1b.gguf \
  --model 0.6b=/path/to/model-0.6b.gguf
```

Use repeated `--server-arg` values for model-specific llama.cpp options, for
example `--server-arg=--reasoning --server-arg=off` for no-thinking tag runs.

The benchmark writes latency, success count, and invalid-output errors for each
real model. It does not synthesize model responses.

## Python Prototype

The earlier Python pprof exporter now lives under
`docs/visexp/agentpprof-python/`. It is kept as research material and is not the
default user entrypoint.

## Development Test

```bash
cargo test --manifest-path agentpprof/Cargo.toml
```
