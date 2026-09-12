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
cargo run --manifest-path ext/pprof/Cargo.toml -- -o agent.pb.gz
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

Each sample is an operation field bag. The default stack is
`task,skill,phase,action,object,repeat,result,outcome` (plus `token` for the
tokens view). `project`/`agent`/`session` are pprof sample labels rather than
default stack frames (`go tool pprof -tags`). Override the stack with `--stack`,
rewrite fields with `--op-map` / `--op-map-file`, and select a subset with
`--where`. Folded, SVG, and JSON outputs keep the full operation stack for
drilldown.

## Views

Use `--view` to choose the projection:

```bash
agentpprof -o operations.pb.gz --view operations
agentpprof -o tokens.pb.gz --view tokens
agentpprof -o files.pb.gz --view files
agentpprof -o network.pb.gz --view network
agentpprof -o time.pb.gz --view time
```

Widths mean different things by view:

- `operations`: one count per prompt, tool, or LLM operation.
- `tokens`: token count when reported by the agent log; otherwise bounded text
  estimates. Very large unsafe estimates are recorded as `unknown=1` so one
  replayed transcript cannot dominate the profile with bogus token width.
- `files`: file/path effect count.
- `network`: network/domain effect count.
- `time`: duration in seconds between successive timestamped events.

## Other Formats

The default format is pprof protobuf, gzipped when the output path ends in
`.gz`. The output extension also selects common formats:

```bash
agentpprof -o operations.folded --view operations
agentpprof -o tokens.svg --view tokens
agentpprof -o files.json --view files
```

Folded stacks are compatible with common flamegraph tooling. SVG output is a
single prefix-merged flamegraph built from the folded stacks. JSON output
includes redacted session summaries and the stack table. Passing
`--include-previews` writes prompt, command, and LLM-output previews into JSON;
avoid it for public artifacts unless the source sessions are already sanitized.
Path frames outside the selected project root are grouped into stable
`external/*` buckets so home-directory names are not emitted in public
profiles.
See `../docs/flamegraph-example/` for a flamegraph gallery and view-by-view usage
examples.

## Tags

The default tagger is deterministic:

```bash
agentpprof -o agent.pb.gz --tagger regex
```

Add project-specific deterministic rules with repeated `--tag-rule`
arguments. Rules use `KIND:TAG=REGEX`, are tried in command-line order before
the built-in rules, and support `session`, `prompt`, `llm`, or `all` as
`KIND`:

```bash
agentpprof -o operations.svg \
  --tagger regex \
  --tag-rule prompt:review='(?i)review|diff|regression' \
  --tag-rule prompt:test='(?i)cargo test|pytest|unit test'
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
Those logs can contain prompts, paths, model outputs, and tool results. For
repeatable private investigations, use explicit `--session-file` inputs.

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
cargo test --manifest-path ext/pprof/Cargo.toml
```
