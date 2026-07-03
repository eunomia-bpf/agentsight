# Design

Last updated: 2026-07-03
Stage at update: stage 3 design / stage 4 execute
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `docs/evaluation.md`
Completeness: partial

## Current State And Blocking Gate

Purpose: keep the current semantic-profiler design aligned with the active
implementation.

AgentSight's semantic profiler should expose only two core abstractions:
`operation` and `operation stack`. Prompt, session, tool call, process, file
event, network event, syscall, plan step, and subagent event are concrete
operation shapes or operation fields, not separate profiler abstractions.

The current blocking gate is stronger boundary detection evidence. R279-R286
show that external labeled trajectories can be projected through the current
Rust implementation and folded at multiple depths, but unsupervised or
model-backed boundary inference is still future work.

## System-Under-Test Model

Purpose: define the evaluated artifact.

The evaluated artifact is the Rust `agentpprof` CLI. It reads either local
Codex/Claude session histories or already-normalized operation JSONL and emits
pprof, folded-stack, SVG, or JSON projections.

The data model is:

```text
operation fields + weight
  -> optional operation-field mappings
  -> user-selected operation stack frames
  -> weighted profile projection
```

`--view` chooses which operations are sampled and how they are weighted.
`--op-map` and `--op-map-file` derive or overwrite operation fields before
stacking. `--stack` chooses the recursive stack shape. `--stack-rule` is a
frame-local override for one projection.

## Core Abstraction: Operation

Purpose: define the only sample-level object.

An operation is a weighted observation with string fields. Examples include:

- a user prompt operation with `op=prompt`;
- an LLM call operation with `op=llm`;
- a tool/API operation with `op=tool`;
- a file, process, network, or system observation represented as operation
  fields;
- an external dataset action row normalized into operation JSONL.

An operation can be coarse or fine. A single prompt can be one operation, or a
sequence of prompts can be mapped into a higher-level intent/task field before
folding. The profiler should not privilege prompt/session boundaries.

## Core Abstraction: Operation Stack

Purpose: define recursive folding.

An operation stack is an ordered list of frames selected from operation fields.
The same operation sequence can be folded at multiple depths:

```text
project,dataset
project,dataset,task
project,dataset,task,phase
project,dataset,task,phase,op,tool
project,dataset,task,phase,op,tool,action,status
```

R286 validates this directly on the same 13,265 external operations: the unique
stack count changes from 9 at dataset depth to 57 at phase depth, 226 at
tool/semantic depth, 455 at action depth, and 3,757 when fixed session is added.
This is expected behavior: users choose the stack depth that matches the
question instead of accepting a fixed prompt/session hierarchy.

## Mapping And Tagging

Purpose: align mapping/tagging with the two-abstraction model.

Mapping and tagging are first-class ways to derive operation fields. They do not
create a third profiler object. The current regex backend is deliberately close
to shell-style filtering: rules match the searchable `key=value` text of an
operation and write labels such as `task=web` or `phase=navigate`.

The intended contract is:

- mappings run before stack construction;
- later mappings can match fields derived by earlier mappings;
- first match wins per destination field;
- stack specs remain independent of the mapping backend;
- learned mappings can be generated from labeled traces and reused through the
same `--op-map-file` path.

## Assumptions And Invariants

Purpose: name the design constraints that tests should protect.

- All profile outputs must be derivable from operations and operation stacks.
- Local-session projections and external operation JSONL must share the same
  stack construction path.
- Adding `session`, `prompt`, `tool`, `process`, or `path` to a stack is a user
  projection choice, not a hard boundary in the profiler.
- Mapping rules must be visible and reproducible, either inline or in tracked
  files.
- Raw external samples stay outside git under `.agentsight/`; tracked artifacts
  contain folded stacks, summaries, and redacted analysis outputs.

## Design Risks And Validation Hooks

Purpose: keep open risks tied to experiments.

| Risk | Validation hook | Current evidence |
|---|---|---|
| Prompt/session boundaries leak back into the abstraction. | Run fixed-boundary ablations against recursive stacks. | R277 and R286 show fixed session greatly fragments stacks. |
| Hand-written mappings overfit one dataset family. | Held-out and leave-dataset-out mapping evaluation. | R282-R285 cover held-out sessions and 9 leave-out datasets. |
| Action labels are too shallow as boundary oracles. | Add step-instruction, solution-path, outcome, and failure-label scorers. | R287 adds tau-bench outcomes and expected task actions as a tool-agent-user source; AndroidControl, TRAIL, and AgentRewardBench remain deeper oracle candidates. |
| Visualizations collapse back to flamegraphs only. | Generate tree, transition, top-field, and depth-sweep HTML/JSON reports. | R273-R286 include non-flamegraph analyses. |
