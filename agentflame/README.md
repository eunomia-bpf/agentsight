# AgentFlame

AgentFlame is a local, LLM-only tagger and visualization tool for AI coding
agent session history. It reads local Codex and Claude JSONL sessions, asks a
local llama.cpp server for one lowercase word per session, prompt, and LLM call,
then writes reusable JSON plus semantic flamegraphs and dashboard charts. Pass
`--no-tag-llm-calls` only when you intentionally want token views to inherit
prompt tags for a faster exploratory run.

It is intentionally separate from the AgentSight collector. The first mode is
zero-instrumentation history analysis. AgentSight can later reuse
`agentflame.json` and `tags.json` to correlate exact
`tool_call -> shell -> child process -> file/network effect` streams with the
same semantic frames.

## Run

Start a local llama.cpp server:

```bash
llama-server -m /path/to/model.gguf --port 8080
```

Generate an AgentFlame report:

```bash
python3 -m agentflame --project-root /path/to/repo --open
```

From this repository during development:

```bash
PYTHONPATH=agentflame python3 -m agentflame --project-root . --out .agentsight/agentflame/latest
```

The default llama.cpp API endpoint is `http://127.0.0.1:8080`. Override it with:

```bash
PYTHONPATH=agentflame python3 -m agentflame run \
  --llama-url http://127.0.0.1:8080 \
  --model local
```

AgentFlame does **not** fall back to regex labels. If the LLM server is missing,
or if the model does not return one valid lowercase word, the run fails.
This applies to every enabled tag scope. The default scope is session+prompt for
system-effect views, plus per-LLM-call tags for token views. `--no-tag-llm-calls`
disables only the LLM-call scope.

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
PYTHONPATH=agentflame python3 -m unittest discover agentflame/tests
```
