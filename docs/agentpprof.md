# AgentPProf: profiling AI-agent work with standard pprof

AgentPProf is a no-sudo offline profiler for Codex and Claude Code histories,
portable agent traces, Chrome/Perfetto traces, and normalized operation JSONL.
It turns agent activity into weighted semantic operation stacks.

## Hard Product Boundary

Every successful run writes exactly one standard `.pb` or `.pb.gz` pprof
profile. AgentPProf has no custom frontend and no folded-stack, SVG, PNG, HTML,
JSON, dashboard, or trace-export product path. Existing pprof-compatible tools
provide flamegraphs, search, focus, comparison, and drilldown.

The command prints a small JSON status record to stdout, but that status is not
a second profile or visualization artifact. Standard and portable trace formats
are inputs only.

## Install

```bash
cargo install --path agentpprof --locked --force
```

## First Profile

```bash
agentpprof --project-root . --view tokens -o tokens.pb.gz
go tool pprof -top tokens.pb.gz
go tool pprof -tags tokens.pb.gz
go tool pprof -http=:0 tokens.pb.gz
```

Use an explicit public fixture when private local histories must not be read:

```bash
agentpprof \
  --project-root . \
  --project-name agentsight-public-fixture \
  --session-file agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --tagger regex \
  --no-cache \
  --view operations \
  -o fixture.pb.gz
```

## Views

`--view` selects the measured quantity; `--stack` independently selects its
semantic hierarchy.

| View | Sample weight |
|---|---|
| `operations` | observed operation count |
| `tokens` | reported input, output, cache, or reasoning tokens |
| `files` | file/path effects |
| `network` | domain/network effects |
| `time` | elapsed time inferred from source timestamps |

Examples:

```bash
agentpprof --view operations -o operations.pb.gz
agentpprof --view tokens     -o tokens.pb.gz
agentpprof --view files      -o files.pb.gz
agentpprof --view network    -o network.pb.gz
agentpprof --view time       -o time.pb.gz
```

These are semantic profiles, not CPU profiles. Width represents the selected
agent-work measure.

## Task-Semantic Stacks

The default stack keeps task structure in the main hierarchy and stores system
details as evidence labels. A useful task-oriented shape is:

```text
task -> subtask -> phase/strategy -> semantic action -> object -> result -> outcome
```

Agent, model, session, tool type, command, path, status, source identifier, call
identifier, and timestamp remain available for filtering and evidence
drilldown. They should not replace task structure as the main hierarchy.

For normalized operation input, choose explicit fields:

```bash
agentpprof \
  --operation-file operations.jsonl \
  --view operations \
  --stack 'task,subtask,phase,action,object,result,outcome' \
  -o operations.pb.gz
```

Each JSONL row is one weighted operation:

```json
{"value":1,"fields":{"task":"write paper","subtask":"write abstract","action":"edit","object":"main.tex","result":"completed"}}
```

`--op-map`, `--op-map-file`, and `--where` derive and select visible operation
fields before stack construction. `--stack-rule` can override one selected
frame. A JSON `--profile-spec` can record the same input and configuration, but
its output must still be one `.pb` or `.pb.gz` pprof.

## Supported Inputs

- native Codex and Claude Code session JSONL;
- `--session-file` for explicit native files;
- `--trace-file` for the portable `agentsight.agent-session.trace.v1` wrapper;
- `--standard-trace-file` for Chrome/Perfetto Trace Event JSON;
- `--operation-file` for normalized operation JSONL.

All input adapters normalize records into operations before profiling. They do
not create additional profiler abstractions or outputs.

## Differential Profile

For two executions of the same task, write one signed candidate-minus-base
pprof:

```bash
agentpprof \
  --operation-file bad-trace.jsonl \
  --diff-base-operation-file good-trace.jsonl \
  --view tokens \
  --stack 'task,subtask,phase,action,object,result,outcome' \
  -o bad-minus-good.pb.gz
```

Candidate samples are positive and base samples are negative. Base samples
carry `pprof::base=true`, the standard label that makes stock pprof use the
base total as its comparison denominator and show a combined differential
flamegraph. Each raw sample retains `comparison_side` and source-evidence
labels, so a pprof consumer can focus a side or recover the corresponding
source record.

## Source Evidence And Privacy

Profiles preserve semantic frames plus source kind, source session, evidence or
call identifier, response phase, outcome, and timestamp labels when available.
Raw prompts and model responses are not required as stack labels. Paths outside
the selected project root are grouped into stable external buckets.

Local histories may still be sensitive. Prefer explicit sanitized inputs for
public artifacts and inspect labels with `go tool pprof -tags` before sharing.

## Development

```bash
cargo test --manifest-path agent-session/Cargo.toml
cargo test --manifest-path agentpprof/Cargo.toml
```

The canonical CLI reference is:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- --help
```
