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

`agentpprof` exports multiple pprof projections from that graph.

### Token Profile

Sample value: token count.

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

Sample value: observed tool event count.

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

Sample value: observed file-target event count.

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

Sample value: observed network-target event count.

```text
project:<repo>;
agent:<codex|claude>;
session:<session_tag>;
prompt:<prompt_tag>;
effect:<effect>;
process:<entrypoint>;
domain:<domain>
```

## Python vs. Rust

The old Rust `agentflame/` code is useful as a prototype and reference, but it
should not be the long-term semantic layer.

Python is the better default for `agentpprof` because:

- session parsing, clustering, embedding, and small-model tagging will move
  faster in Python;
- pprof export is an offline analysis path, not a collector hot path;
- it can be shipped as a standalone package and imported by notebooks,
  evaluation scripts, or AgentSight Web;
- Rust can stay focused on low-overhead collection and exact system provenance.

The intended split is:

```text
collector/      Rust: exact runtime capture and provenance
agentpprof/     Python: local history parsing, semantic tags, pprof export
frontend/       TypeScript: pprof/artifact browsing inside AgentSight
```

## Compatibility Boundary

`agentpprof` profiles are semantic profiles, not CPU profiles. pprof will still
render them correctly because the `profile.proto` structure is valid:

- `Profile.sample_type` describes the selected measure;
- `Sample.location_id` stores the synthetic stack, leaf first;
- `Function.name` stores each semantic frame;
- `Sample.label` stores drilldown identifiers such as source, session, prompt,
  effect, and tool.

The current Python encoder writes the profile proto subset directly, with no
runtime dependency on `protobuf` or `protoc`. The unit test uses
`go tool pprof -top` as the compatibility oracle.

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
5. retire `agentflame/` after feature parity and migration tests.
