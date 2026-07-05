# agentpprof

`agentpprof` turns local AI coding-agent sessions into pprof-compatible semantic
profiles. It reads Codex and Claude Code JSONL history, assigns short semantic
tags to sessions, prompts, LLM calls, and effects, and writes outputs that can
be inspected with standard pprof or flamegraph tooling.
It can also read normalized operation JSONL from third-party trajectory
datasets via `--operation-file`.

The profiles are not CPU profiles. They are projections over agent activity:
token usage, tool events, file effects, network effects, or elapsed session
time.

## Install

From this repository, matching the checked artifact smoke:

```bash
cargo install --path agentpprof --locked --force
```

Published registry releases may lag this research branch. Use the source-tree
install above when reproducing the paper artifacts.

For local development without installing:

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- -o tokens.pb.gz --view tokens
```

## Public Fixture Smoke

For a reproducible first run that does not read private local agent histories,
use the committed synthetic Codex fixture. Artifact reviewers should prefer
this explicit `--session-file` command because it avoids default discovery of
local Codex/Claude histories.

```bash
agentpprof \
  --project-root . \
  --project-name agentsight-public-fixture \
  --session-file agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --tagger regex \
  --no-cache \
  --view tokens \
  -o tokens.pb.gz

go tool pprof -top tokens.pb.gz
```

The fixture checks parser, projection, and pprof readback behavior only. It is
not evidence of developer utility, tag adequacy, or real-history privacy.

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
agentpprof -o operations.pb.gz --view operations
agentpprof -o files.pb.gz --view files
agentpprof -o network.pb.gz --view network
agentpprof -o time.pb.gz --view time
```

Widths mean different things by view:

- `operations`: operation count across prompts, LLM calls, tools, or external operation JSONL.
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
single quick-look stack chart built from the folded stacks; use folded output
with standard tools such as inferno or flamegraph.pl when you need canonical
merged-prefix flamegraphs. JSON output includes redacted session summaries and
the stack table. Passing `--include-previews` writes prompt, command, and
LLM-output previews into JSON; avoid it for public artifacts unless the source
sessions are already sanitized. Path frames outside the selected project root
are grouped into stable `external/*` buckets so home-directory names are not
emitted in public profiles. See `../docs/flamegraph/` for a public fixture
gallery and view-by-view usage examples.

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
repeatable demos, tests, or public artifacts, prefer explicit `--session-file`
inputs like the fixture above.

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

## Operation JSONL Input

Codex and Claude session files are one source of operations, not a separate
profiling abstraction. For external datasets or converters, pass one or more
operation JSONL files:

```bash
agentpprof -o external.folded --view operations \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --stack 'project,agent,dataset,task,session,phase,op,action,target,status'
```

Each JSONL line is one sampled operation:

```json
{"value":1,"fields":{"project":"external-agent-traces","agent":"human-demo","dataset":"weblinx-chat","task":"web-navigation","phase":"click","op":"action","action":"click","target":"login","status":"gold"}}
```

Field values may be strings, numbers, booleans, arrays, or JSON objects. The
chosen `--stack` decides which fields become stack frames. `--op-map` can derive
or overwrite operation fields before stacking, and `--stack-rule` can override a
single frame while building the stack. `--op-map-file` reads the same
`FIELD:LABEL=REGEX` rules from a text file, one rule per line; blank lines and
`#` comments are ignored.
Use `script/agent_trace_datasets.py` to sample known labeled datasets into this
format without committing raw external data.

```bash
agentpprof -o external.folded --view operations \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --op-map-file docs/visexp/out/operation-map-infer-r281/inferred-op-map.txt \
  --op-map 'task:web=(dataset=weblinx-chat|tool=browser)' \
  --op-map 'phase:navigate=(action=click|action=goto|action=load)' \
  --stack 'project,dataset,task,phase,op,tool,action,status'
```

For labeled external traces, `script/operation_map_infer.py` can generate an
op-map file from observed `dataset`, `tool`, `task`, and `action` labels:

```bash
python3 script/operation_map_infer.py \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --out op-map.txt \
  --json-out op-map.json
```

## Standard Trace Exchange

Local Codex/Claude sessions can be exported directly as Chrome Trace Event JSON
when another tool wants a standard trace container:

```bash
agentpprof --session-file agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --export-standard-trace fixture-chrome-trace.json

agentpprof --standard-trace-file fixture-chrome-trace.json --view operations \
  --stack 'project,agent,op,phase,tool,status' \
  -o fixture.folded --format folded
```

Use the scripts when a workflow needs explicit intermediate files in AgentSight
operation JSONL:

```bash
agentpprof --session-file agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --export-trace fixture-agent-trace.json

python3 script/agent_trace_chrome_trace.py export \
  --trace-file fixture-agent-trace.json \
  --out fixture-chrome-trace.json

python3 script/agent_trace_chrome_trace.py import \
  --trace-file fixture-chrome-trace.json \
  --out fixture-operations.jsonl

agentpprof --operation-file fixture-operations.jsonl --view operations \
  --stack 'project,agent,op,phase,tool,status' \
  -o fixture.folded --format folded
```

The Chrome/Perfetto trace is an exchange format, not a third profiling object.
After import, `agentpprof` still folds ordinary operation JSONL with the chosen
operation stack. `python3 script/agent_trace_chrome_exchange_eval.py` reproduces
the fixture round trip and checks that direct trace import, direct operation
import, and Chrome-trace import produce the same folded output.

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

`--view` selects the measured operation samples and their weights. `--op-map`
derives reusable operation fields, `--where` selects a query subset after
mapping, and `--stack` selects the operation stack shape. A stack frame can come
directly from an operation field or from the first matching `--stack-rule` for
that frame:

```bash
agentpprof -o files.json --format json --view files \
  --stack 'project,agent,task,phase,op,tool,path,status' \
  --op-map-file project-op-map.txt \
  --op-map 'task:verify=(effect=test|cmd=cargo|path=tests)' \
  --op-map 'task:explore=(effect=read|tool=read)' \
  --op-map 'phase:inspect=(effect=read)' \
  --where 'task=verify' \
  --stack-rule 'path:tests=(path=tests)' \
  --rank-mode rule-score \
  --rank-rule 'verify-risk:2=phase:execute|status:error' \
  --rank-op-rule 'error-density:3=status=error'
```

Operation mapping and stack rules match a searchable `key=value` string built
from operation fields such as `prompt`, `prompt_preview`, `op`, `tool`,
`category`, `command`, `cmd`, `process`, `effect`, `status`, `path`, `domain`,
`llm`, `llm_preview`, `model`, and `token`, plus any fields supplied by
`--operation-file`. Mapping rules are evaluated in order against the fields
derived so far; the first match wins for each derived field. Inline `--op-map`
rules run before `--op-map-file` rules, so command-line rules can override a
shared mapping file. `--where FIELD=REGEX` and `--where FIELD!=REGEX` run after
mapping and before stack construction; multiple predicates are ANDed.
`--rank-rule LABEL:WEIGHT=REGEX` orders JSON operation-stack groups by visible
folded-stack text. `--rank-op-rule LABEL:WEIGHT=REGEX` matches individual
`field=value` operation tokens after mapping/filtering and aggregates matched
operation weight inside each folded group. Both ranking surfaces affect only
JSON output, not pprof, folded, or SVG output. The default `--rank-mode
width-boost` keeps width as the primary signal; `--rank-mode rule-score` ranks
by matched visible rules first and uses width as a tie-breaker.

Token profile:

```text
project:<repo>;agent:<codex|claude>;session:<tag>;prompt:<tag>;phase:<tag>;op:llm;call:llm/<tag>;model:<model>;token:<kind>
```

Width: token count.

Tool/effect path:

```text
project:<repo>;agent:<codex|claude>;session:<tag>;prompt:<tag>;phase:<tag>;op:tool;tool:<kind>;process:<cmd>;path:<group>;effect:<effect>;status:<status>
```

Width: observed tool event count.

File and network profiles use the configured semantic context, then continue
down the operation path to `path:<group>` or `domain:<domain>`. Their widths are
file target event count and network target event count.
Drop `prompt` from `--stack` when several prompts should fold into one inferred
task, or add more stack frames when a task should recursively fold into
subtasks or phases.

The Python pprof exporter reverses semantic stacks when serializing samples
because pprof stores the leaf frame first.

## Development

```bash
cargo test --manifest-path agentpprof/Cargo.toml
PYTHONPATH=docs/visexp/agentpprof-python/src pytest docs/visexp/agentpprof-python/tests
```
