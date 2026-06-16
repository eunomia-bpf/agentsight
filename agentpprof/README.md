# agentpprof

`agentpprof` builds pprof-compatible semantic profiles from local coding-agent
sessions. It maps agent concepts such as session tags, prompt tags, LLM calls,
tool calls, processes, and effects onto synthetic pprof stack frames, then
writes gzip-compressed `profile.proto` files that `go tool pprof` can read.

The files are semantic profiles, not CPU profiles. The sample value can be
tokens, tool events, file events, or network events.

## Run From This Repository

```bash
PYTHONPATH=agentpprof/src python3 -m agentpprof export \
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

Inspect with pprof:

```bash
go tool pprof -top .agentsight/agentpprof/latest/tokens.pb.gz
go tool pprof -traces .agentsight/agentpprof/latest/tools.pb.gz
go tool pprof -http=:0 .agentsight/agentpprof/latest/files.pb.gz
```

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

The pprof exporter reverses these stacks when serializing samples because pprof
stores the leaf frame first.
