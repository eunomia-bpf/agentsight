# agentpprof

`agentpprof` turns local AI coding-agent sessions into pprof-compatible semantic
profiles. It reads Codex and Claude Code JSONL history, assigns short semantic
tags to sessions, prompts, LLM calls, and effects, and writes outputs that can
be inspected with standard pprof or flamegraph tooling.

The profiles are not CPU profiles. They are projections over agent activity:
token usage, tool events, file effects, network effects, or elapsed session
time.

## Install

```bash
cargo install agentpprof
```

From this repository:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- -o tokens.pb.gz --view tokens
```

## pprof Output

Generate a semantic profile for the current repository:

```bash
agentpprof --project-root . -o tokens.pb.gz --view tokens
```

Open it with standard Go pprof:

```bash
go tool pprof -top tokens.pb.gz
go tool pprof -http=:0 tokens.pb.gz
```

## Views

Use `--view` to choose the projection:

```bash
agentpprof -o tokens.pb.gz --view tokens
agentpprof -o files.pb.gz --view files
agentpprof -o network.pb.gz --view network
agentpprof -o time.pb.gz --view time
```

Widths mean different things by view:

- `tokens`: token count when reported by the agent log.
- `files`: file/path effect count.
- `network`: network/domain effect count.
- `time`: elapsed session time.

## Other Formats

The default format is pprof protobuf, gzipped when the output path ends in
`.gz`. The output extension also selects common formats:

```bash
agentpprof -o tokens.folded --view tokens
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

## Tags

The default tagger is deterministic:

```bash
agentpprof -o tokens.pb.gz --tagger regex
```

Add project-specific deterministic rules with repeated `--tag-rule`
arguments. Rules use `KIND:TAG=REGEX`, are tried in command-line order before
the built-in rules, and support `session`, `prompt`, `llm`, or `all` as
`KIND`:

```bash
agentpprof -o tokens.svg \
  --tagger regex \
  --tag-rule prompt:review='(?i)review|diff|regression' \
  --tag-rule prompt:test='(?i)cargo test|pytest|unit test'
```

For model-produced one-word tags, run a llama.cpp-compatible server and use:

```bash
llama-server -m /path/to/model.gguf --port 8080
agentpprof -o tokens.pb.gz --tagger llm --llama-url http://127.0.0.1:8080
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
agentpprof -o tokens.pb.gz --session-file ~/.codex/sessions/.../session.jsonl
agentpprof -o tokens.pb.gz --agent codex
agentpprof -o tokens.pb.gz --session-id 019ec5
agentpprof -o tokens.pb.gz --session-tag profile
agentpprof -o tokens.pb.gz --prompt-tag review
```

No output directory is created unless the explicit `-o/--output` path contains
one.

## Python Prototype

The earlier experimental Python exporter now lives under
`docs/visexp/agentpprof-python/` as research material:

```bash
PYTHONPATH=docs/visexp/agentpprof-python/src python3 -m agentpprof export \
  --project-root . \
  --out .agentsight/agentpprof/latest \
  --max-sessions 12
```

The export writes:

- `tokens.pb.gz`
- `tools.pb.gz`
- `files.pb.gz`
- `network.pb.gz`
- matching folded stacks
- `*.flame.svg` semantic flamegraphs
- `agentpprof.json`
- optional `*.top.txt` reports when `go tool pprof` is available

Open the generated flamegraphs directly:

```bash
xdg-open .agentsight/agentpprof/latest/tools.flame.svg
xdg-open .agentsight/agentpprof/latest/tokens.flame.svg
```

## Stack Projections

Token profile:

```text
project:<repo>;agent:<codex|claude>;session:<tag>;prompt:<tag>;call:llm/<tag>;model:<model>;token:<kind>
```

Width: token count.

Tool/effect profile:

```text
project:<repo>;agent:<codex|claude>;session:<tag>;prompt:<tag>;call:tool/<tag>;tool:<kind>;process:<cmd>;effect:<effect>;target:<group>;status:<status>
```

Width: observed tool event count.

File and network profiles use the same semantic session/prompt context, but
make `file:<group>` or `domain:<domain>` the leaf frame. Their widths are file
target event count and network target event count.

The Python pprof exporter reverses semantic stacks when serializing samples
because pprof stores the leaf frame first.

## Development

```bash
cargo test --manifest-path agentpprof/Cargo.toml
PYTHONPATH=docs/visexp/agentpprof-python/src pytest docs/visexp/agentpprof-python/tests
```
