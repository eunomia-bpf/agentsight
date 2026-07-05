# agentpprof Design Note

`agentpprof` is the replacement direction for the earlier AgentFlame prototype.
The key change is that the output is not only folded stacks or custom HTML. It
also writes gzip-compressed pprof `profile.proto` files that standard
`go tool pprof` can parse.

## Why pprof

The project needs a developer-native abstraction for agent analysis. pprof is a
good fit because it already has a stable mental model:

- a profile is a set of weighted samples;
- each sample has a stack;
- repeated stack prefixes aggregate naturally;
- different sample types can represent different costs.

For coding agents, the stack is synthetic rather than a CPU call stack. A stack
frame can be `prompt:debug`, `call:tool:read`, `process:rg`, or
`file:collector/src/main.rs`. This makes pprof an interchange layer for semantic
agent profiles.

## Projection Model

The raw event graph remains:

```text
session -> prompt/turn -> {llm_call, tool_call}
tool_call -> process/effect/target
llm_call -> token usage
```

`agentpprof` exports multiple pprof projections from that graph. Each
projection also emits a folded stack file and a direct SVG flamegraph.

### Token Profile

Sample value and flamegraph width: token count.

```text
project:<repo>;
agent:<codex|claude>;
session:<session_tag>;
prompt:<prompt_tag>;
call:llm/<llm_call_tag>;
model:<model>;
token:<input|output|cache|estimate>
```

### Tool Profile

Sample value and flamegraph width: observed tool event count.

```text
project:<repo>;
agent:<codex|claude>;
session:<session_tag>;
prompt:<prompt_tag>;
call:tool/<tool_tag>;
effect:<effect>;
target:<file_or_domain_group>;
tool:<tool_kind>;
process:<entrypoint>
```

`process` is the leaf because `go tool pprof -top` should show actionable hot
commands, not `status:observed`.

### File Profile

Sample value and flamegraph width: observed file-target event count.

```text
project:<repo>;
agent:<codex|claude>;
session:<session_tag>;
prompt:<prompt_tag>;
effect:<effect>;
process:<entrypoint>;
file:<group>
```

### Network Profile

Sample value and flamegraph width: observed network-target event count.

```text
project:<repo>;
agent:<codex|claude>;
session:<session_tag>;
prompt:<prompt_tag>;
effect:<effect>;
process:<entrypoint>;
domain:<domain>
```

## Rust vs. Python

The published user entrypoint is the Rust `agentpprof/` CLI. It depends on the
shared `agent-session` crate for local transcript discovery and normalized
session summaries, then enriches those sessions into prompt/tool/LLM-call
semantic stacks.

The Python implementation under `docs/visexp/agentpprof-python/` is retained as
a research prototype for pprof export experiments, visualization experiments,
and clustering/tagging iteration. It is not the default package boundary.

The intended split is:

```text
collector/      Rust: exact runtime capture and provenance
agent-session/  Rust: shared local agent transcript parser and session IR
agentpprof/     Rust: user CLI, semantic tags, folded stacks, reports
docs/visexp/agentpprof-python/
                Python: research prototype and pprof export experiments
frontend/       TypeScript: pprof/artifact browsing inside AgentSight
```

## Profile Specs and Deterministic Artifacts

The Rust CLI also supports an operation JSONL path for paper experiments.
`--profile-spec` records the operation input, mapping files, predicates, view,
stack fields, rank rules, and output path in a JSON configuration. Command-line
flags still override spec defaults, so the spec is a reproducibility wrapper
around the same operation/operation-stack query surface rather than a new
profiler abstraction.

For byte-stable artifact checks, `--deterministic-output` or a profile-spec
`deterministic_output` field replaces JSON `generated_at` and pprof profile time
with fixed values. This mode is intended for reproducibility tests and should
not be interpreted as a live-capture overhead measurement.

## Compatibility Boundary

`agentpprof` profiles are semantic profiles, not CPU profiles. pprof will still
render them correctly because the `profile.proto` structure is valid:

- `Profile.sample_type` describes the selected measure;
- `Sample.location_id` stores the synthetic stack, leaf first;
- `Function.name` stores each semantic frame;
- `Sample.label` stores drilldown identifiers such as source, session, prompt,
  effect, and tool.

The current Python prototype encoder writes the profile proto subset directly,
with no runtime dependency on `protobuf` or `protoc`. The unit test uses
`go tool pprof -top` as the compatibility oracle.

The direct flamegraph renderer uses the same samples. It builds a prefix tree
from root-to-leaf semantic stacks and draws rectangles whose width is the
cumulative sample value for that projection. This avoids confusing pprof's
`-svg` call graph output with a flamegraph.

## Current Limitations

- The default tagger is a deterministic bootstrap tagger. It is useful for
  smoke tests but not the research-quality semantic layer.
- Prompt tags still have a long tail and generic `work` bucket. The next step is
  task segmentation plus clustering, then one-word cluster labels.
- Local session logs provide approximate tool/process/effect attribution. Exact
  child-process and file/network lineage should come from AgentSight collector
  snapshots when available.
- Token counts reflect the source session logs. Codex token events may be dense;
  deduplication policy should be made explicit before using token totals as an
  evaluation number.

## Next Step

Make `agentpprof` the source of truth for semantic exports:

1. add small-LLM or embedding-cluster tag backends;
2. import AgentSight runtime lineage snapshots as exact process/effect samples;
3. add `agentpprof diff` for comparing two sessions or two branches;
4. add a frontend view that can open the generated pprof files and folded stacks;
5. move the remaining useful Python prototype pieces into the Rust package or
   keep them as explicit research artifacts.
