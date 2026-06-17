# agentpprof

`agentpprof` turns local AI coding-agent sessions into pprof-compatible semantic
profiles. It reads Codex and Claude Code JSONL history through AgentSight's
`agent-session` crate, assigns one-word tags to sessions, prompts, and LLM
calls, and writes one explicit output file.

The profiles are not CPU profiles. They are projections over agent activity:
tool events, file effects, network effects, or token usage.

## Install

```bash
cargo install agentpprof
```

From this repository:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- -o agent.pb.gz
```

## pprof Output

Generate a semantic task profile for the current repository:

```bash
agentpprof --project-root . -o agent.pb.gz
```

Open it with standard Go pprof:

```bash
go tool pprof -top agent.pb.gz
go tool pprof -http=:0 agent.pb.gz
```

The default `tasks` view makes prompt tags the pprof leaf frame, so `pprof -top`
shows where the agent spent most of its session activity semantically.

## Views

Use `--view` to choose the projection:

```bash
agentpprof -o tasks.pb.gz --view tasks
agentpprof -o tools.pb.gz --view tools
agentpprof -o tokens.pb.gz --view tokens
agentpprof -o files.pb.gz --view files
agentpprof -o network.pb.gz --view network
```

Widths mean different things by view:

- `tasks`: event count across tool and LLM-call activity.
- `tools`: tool event count, including tool category, process chain, effect,
  path/domain, and status frames.
- `tokens`: token count when reported by the agent log; otherwise bounded text
  estimates. Very large unsafe estimates are recorded as `unknown=1` so one
  replayed transcript cannot dominate the profile with bogus token width.
- `files`: file/path effect count.
- `network`: network/domain effect count.

## Other Formats

The default format is pprof protobuf, gzipped when the output path ends in
`.gz`. The output extension also selects common formats:

```bash
agentpprof -o tasks.folded --view tasks
agentpprof -o tokens.svg --view tokens
agentpprof -o files.json --view files
```

Folded stacks are compatible with common flamegraph tooling. SVG output is a
single quick-look stack chart built from the folded stacks; use folded output
with standard tools such as inferno or flamegraph.pl when you need canonical
merged-prefix flamegraphs. JSON output includes redacted session summaries and
the stack table.

## Tags

The default tagger is deterministic:

```bash
agentpprof -o agent.pb.gz --tagger regex
```

For model-produced one-word tags, run a llama.cpp-compatible server and use:

```bash
llama-server -m /path/to/model.gguf --port 8080
agentpprof -o agent.pb.gz --tagger llm --llama-url http://127.0.0.1:8080
```

LLM tags are cached under the user cache directory by default, for example
`$XDG_CACHE_HOME/agentpprof/tags.json`. Override with `--cache`, or pass
`--no-cache` to avoid saving new entries.

## Selecting Sessions

By default, `agentpprof` scans recent local Codex and Claude Code sessions that
match `--project-root`.

Useful selectors:

```bash
agentpprof -o agent.pb.gz --session-file ~/.codex/sessions/.../session.jsonl
agentpprof -o agent.pb.gz --agent codex
agentpprof -o agent.pb.gz --session-id 019ec5
agentpprof -o agent.pb.gz --session-tag profile
agentpprof -o agent.pb.gz --prompt-tag review
```

No output directory is created unless the explicit `-o/--output` path contains
one.

## Development

```bash
cargo test --manifest-path agentpprof/Cargo.toml
```
