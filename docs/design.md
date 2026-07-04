# Design

Last updated: 2026-07-03
Stage at update: stage 3 design / stage 4 execute
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `docs/evaluation.md`, `agentpprof --profile-spec`
Completeness: partial

## Current State And Blocking Gate

Purpose: keep the current semantic-profiler design aligned with the active
implementation.

AgentSight's semantic profiler should expose only two core abstractions:
`operation` and `operation stack`. Prompt, session, tool call, process, file
event, network event, syscall, plan step, and subagent event are concrete
operation shapes or operation fields, not separate profiler abstractions.

The current blocking gate is not more dataset breadth. R279-R293 show that
external labeled trajectories can be projected through the current Rust
implementation and folded at multiple depths. The remaining paper-grade gaps
are stronger boundary detection beyond deterministic rules, user-facing utility
evidence, and tighter synthesis of which trajectory families actually support
the main claims.

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

R289 extends the same model to SATraj-OS desktop computer-use traces. The stack
does not add a GUI, safety, prompt, or OS-specific object: `safety`,
`attack_type`, `status`, `action`, and `repeat_signal` are ordinary operation
fields that can be selected or omitted from the operation stack.

R290 extends the same model to OSWorld-Human human desktop trajectories. The
same single-action sequence can be viewed at action depth
(`...phase,op,tool,action,status`) or grouped-action depth
(`...phase,group_pattern,group_position,status`) by changing only `--stack`.
The benchmark's `human_group` labels are carried as operation fields for
evaluation and optional drilldown only when flattened `grouped-action` labels
exactly match the `single-action` sequence. Non-exact rows are marked through
`group_alignment` and remain usable for action profiling, but not for
grouped-boundary scoring. These labels are not a new profiler abstraction.

R291 extends the same model to AgentNet human desktop trajectories. The sampled
1,000 Ubuntu tasks produce 16,741 PyAutoGUI operations and can be folded with
frames such as `environment`, `phase`, `action`, `status`, `step_correct`,
`step_redundant`, and `repeat_signal`. Task outcome, alignment score,
efficiency score, difficulty, step correctness, and redundancy are operation
fields: they may be projected, scored, or omitted without introducing a
quality-label, desktop, or prompt/session abstraction.

R292 extends the same model to a supplemental ScaleCUA Ubuntu navigation stream
sample. The sampled 5,000 rows produce 5,000 computer-use operations across 131
sessions with `platform`, `environment`, `trajectory_type`, `history_state`,
and `history_depth` fields. This run is useful for proving previous-operation
context is still just operation data, but it is not a main boundary oracle
because the sampled subset is mostly click/terminate.

R293 packages the AgentNet operation-stack query as a reusable profile spec.
The spec references the existing R291 operation JSONL and op-map file, produces
the same 16,741-operation / 608-stack diagnostic projection, and a CLI stack
override on the same spec folds the identical operations into 83 coarser
stacks. This validates reproducible configuration without adding a profile-spec
object to the paper model: the evaluated objects remain operations and
operation stacks.

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
- operation-family mappings must run before generic action-verb mappings;
- stack specs remain independent of the mapping backend;
- learned mappings can be generated from labeled traces and reused through the
  same `--op-map-file` path.
- `--profile-spec` may bundle `--view`, `--stack`, `--op-map-file`,
  `--operation-file`, output, and project metadata for reproducibility, but
  command-line rules still override spec defaults and no new profiler
  abstraction is introduced.

R285, R289, R290, R291, R292, and R293 are the current regression tests for mapping
precedence. Tool/API operations should derive `phase=api` from tool/API
structure before generic verbs such as `search` or `create`; desktop
computer-use operations should derive `phase=input` for `key`/`type` before
generic web rules map `type` to `modify`; desktop clicks such as AgentNet
`tripleClick` should normalize into the existing navigate family; OSWorld-Human
grouped-action patterns should be derivable from validated action sequences and
group metadata without binding stacks to prompt/session boundaries; ScaleCUA
history state and depth should remain selectable fields rather than a new
trajectory-history object; profile specs should make those choices repeatable
without freezing the stack shape. This is ordering over operation fields and
query configuration, not a separate abstraction.

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
| Hand-written mappings overfit one dataset family. | Held-out and leave-dataset-out mapping evaluation plus operation-family precedence checks. | R282-R285 cover held-out sessions and 9 leave-out datasets; R289/R290/R291 add desktop computer-use precedence checks; R292 adds a supplemental GUI history-depth field check. |
| Action labels are too shallow as boundary oracles. | Add step-instruction, solution-path, outcome, side-effect, looping, repetition, safety/attack, grouped-action, step-quality, and failure-label scorers. | R287 adds tau-bench outcomes and expected task actions; R288 adds AgentRewardBench expert success, side-effect, looping, optimality, and action-derived `repeat_signal` fields; R289 adds SATraj safety and attack labels; R290 adds OSWorld-Human grouped-action boundary labels; R291 adds AgentNet step correctness and redundancy labels. AndroidControl and TRAIL remain deeper oracle candidates. |
| Profile experiments remain ad hoc shell commands. | Bundle reproducible operation-file, op-map, view, stack, and output choices in profile specs while preserving CLI overrides. | R293 adds an AgentNet profile spec that reproduces the R291 608-stack diagnostic profile and folds the same operations into an 83-stack override view. |
| Visualizations collapse back to flamegraphs only. | Generate tree, transition, top-field, quality, grouped-stack, history-depth, and depth-sweep HTML/JSON reports. | R273-R293 include non-flamegraph analyses and reproducible profile specs. |
