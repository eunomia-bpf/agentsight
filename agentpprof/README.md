# agentpprof

`agentpprof` turns AI-agent activity into pprof-compatible operation-stack
profiles. It has two core profiling abstractions:

- An operation is a weighted record with fields. A prompt, LLM call, tool call,
  process event, file effect, network event, or imported benchmark action is one
  operation shape.
- An operation stack is the user-chosen list of fields used to recursively fold
  operations. Session, prompt, tool, process, and span identifiers can appear as
  fields, but they are not separate profiler objects.

For local history, `agentpprof` reads Codex and Claude Code JSONL sessions,
derives operation fields through deterministic tags and mappings, and writes a
standard pprof profile that can be inspected with existing pprof tooling. For
third-party trajectory datasets, pass normalized operation JSONL through
`--operation-file`.

The profiles are not CPU profiles. They are projections over agent activity:
token usage, operation counts, file effects, network effects, or elapsed
session time. AgentPProf's product artifact is the pprof profile; visualization,
search, focus, comparison, and drilldown belong to existing pprof-compatible
tools rather than a custom AgentPProf frontend.

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

### Differential pprof

For two executions of the same task, pass the trace under investigation as the
candidate and the reference execution as the base:

```bash
agentpprof \
  --operation-file bad-trace.jsonl \
  --diff-base-operation-file good-trace.jsonl \
  --view tokens \
  --stack 'task,subtask,strategy,action,object,result' \
  --deterministic-output \
  -o bad-minus-good.pb.gz

go tool pprof -top bad-minus-good.pb.gz
go tool pprof -http=:0 bad-minus-good.pb.gz
```

The output is one signed `candidate-minus-base` pprof: positive samples are
paths with more weight in the candidate, and negative samples are paths with
more weight in the base. Both inputs use the same explicit stack fields and
weighting view. The command intentionally rejects folded, JSON, and SVG output
for comparisons; existing pprof tools provide the visualization surface.

## Views

Use `--view` to choose the projection:

```bash
agentpprof -o tokens.pb.gz --view tokens
agentpprof -o operations.pb.gz --view operations
agentpprof -o files.pb.gz --view files
agentpprof -o network.pb.gz --view network
agentpprof -o time.pb.gz --view time
```

`--view` chooses which operation samples are measured and how they are weighted:

- `operations`: operation count across prompts, LLM calls, tools, or external operation JSONL.
- `tokens`: token count when reported by the agent log.
- `files`: file/path effect count.
- `network`: network/domain effect count.
- `time`: elapsed session time.

The view is independent from `--stack`. For example, the same operations can be
weighted by tokens and folded by prompt tags, or weighted by operation count and
folded by dataset/task/phase/action fields.

## Product Boundary

Every successful invocation writes exactly one standard pprof `.pb` or
`.pb.gz` artifact. The CLI rejects folded-stack, SVG, JSON, PNG, HTML, dashboard,
and trace-export output paths. AgentPProf has no frontend. Use existing
pprof-compatible tools for flamegraphs, focus, search, comparison, and source
drilldown. Standard trace JSON and normalized operation JSONL remain supported
as inputs only.

Path frames outside the selected project root are grouped into stable
`external/*` buckets so home-directory names are not emitted in profiles.

## Field Derivation

For local free-form prompts, the default tagger deterministically derives stable
operation fields such as prompt tags:

```bash
agentpprof -o tokens.pb.gz --tagger regex
```

Add project-specific deterministic rules with repeated `--tag-rule` arguments.
Rules use `KIND:TAG=REGEX`, are tried in command-line order before the built-in
rules, and support `session`, `prompt`, `llm`, or `all` as `KIND`:

```bash
agentpprof -o tokens.pb.gz \
  --tagger regex \
  --tag-rule prompt:review='(?i)review|diff|regression' \
  --tag-rule prompt:test='(?i)cargo test|pytest|unit test'
```

For model-produced one-word tags, run a llama.cpp-compatible server and use:

```bash
llama-server -m /path/to/model.gguf --port 8080
agentpprof -o tokens.pb.gz --tagger llm --llama-url http://127.0.0.1:8080
```

The LLM tagger may read an existing cache under the user cache directory, for
example `$XDG_CACHE_HOME/agentpprof/tags.json`. Override the read-only input
with `--cache`, or pass `--no-cache` to ignore it. AgentPProf never writes the
cache; tags created during a run are deduplicated only in memory.

For external operations and reproducible experiments, prefer `--op-map`,
`--op-map-file`, and `--profile-spec`. These mechanisms derive operation fields
before stack construction without adding another profiler abstraction.
Profile specs can also carry local-session tagging controls (`tagger`,
`preset`, and `tag_rules`) so prompt/session tag derivation is replayed with the
same configuration as external operation mappings and stack queries.

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
agentpprof -o external.pb.gz --view operations \
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
single frame while building the stack. `--where` selects a query subset after
mapping and before folding. `--op-map-file` reads the same `FIELD:LABEL=REGEX`
rules from a text file, one rule per line; blank lines and `#` comments are
ignored.
Use `script/agent_trace_datasets.py` to sample known labeled datasets into this
format without committing raw external data.

### Agent-marked operation boundaries

An Agent or another segmentation backend can identify semantic transitions by
source operation ID without relabeling every row. Pass one JSON mark file:

```json
{
  "sequence_field": "session_id",
  "id_field": "operation_id",
  "operation_names": {
    "review": "Review research evidence",
    "validate": "Validate experiment evidence"
  },
  "marks": [
    {
      "sequence": "session-1",
      "start_operation_id": "op-0001",
      "operation_ids": ["review"]
    },
    {
      "sequence": "session-1",
      "start_operation_id": "op-0042",
      "operation_ids": ["review", "validate"]
    }
  ]
}
```

```bash
agentpprof \
  --operation-file operations.jsonl \
  --operation-mark-file operation-marks.json \
  --view operations \
  -o marked.pb.gz
```

A mark is a stable-ID boundary produced by an Agent or another segmentation
backend; it is not a product human-annotation workflow. Every
operation inherits the latest full operation-ID path in its sequence; unequal
path lengths produce variable-depth stacks, and the shared name pool lets equal
semantic IDs aggregate across sessions. With no explicit `--stack`, this mode
uses `operation`; an explicit stack must contain that field.

The input fails closed when a sequence or ID field is missing or multivalued,
IDs repeat within a sequence, the first source operation is unmarked, marks are
unknown or out of order, a path is empty, or a semantic ID is absent from the
name pool. Display names, source sequences, and source IDs must also remain unique after pprof
normalization. The configured source sequence and operation ID are preserved as
the pprof `source_session` and `evidence_id` labels.

This first interface is intentionally limited to normalized `--operation-file`
input with `--view operations`; it does not yet mark expanded local-session
token/file/network/time samples or combine mark files with signed differences.
Operation marks and `--induce-operation-stack` are mutually exclusive because
both derive the `operation` field. Regex mappings may normalize fields or help
an Agent retrieve candidate source IDs, but neither mappings nor
`--stack-rule operation:...` override a marked semantic path.

```bash
agentpprof -o external.pb.gz --view operations \
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

## Standard Trace Input

Chrome/Perfetto Trace Event JSON is an input adapter, not a product output:

```bash
agentpprof --standard-trace-file fixture-chrome-trace.json --view operations \
  --stack 'project,agent,task,phase,tool,status' \
  -o fixture.pb.gz
```

After import, AgentPProf folds ordinary operations with the selected stack and
writes the same single pprof artifact as every other input mode.

## Archived Python Prototype

The earlier Python exporter under `docs/visexp/agentpprof-python/` is archived
research material. It is not an AgentPProf product path and must not be used to
add alternative outputs or a custom visualization surface.

## Stack Projections

`--view` selects the measured operation samples and their weights. `--op-map`
derives reusable operation fields, `--where` selects a query subset after
mapping, and `--stack` selects the operation stack shape. A stack frame can come
directly from an operation field or from the first matching `--stack-rule` for
that frame:

```bash
agentpprof -o files.pb.gz --view files \
  --stack 'project,agent,task,phase,op,tool,path,status' \
  --op-map-file project-op-map.txt \
  --op-map 'task:verify=(effect=test|cmd=cargo|path=tests)' \
  --op-map 'task:explore=(effect=read|tool=read)' \
  --op-map 'phase:inspect=(effect=read)' \
  --where 'task=verify' \
  --stack-rule 'path:tests=(path=tests)'
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
Diagnostic selection belongs in the explicit mapped fields and `--where`
predicate; visualization and interactive ranking belong to the pprof consumer.

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
