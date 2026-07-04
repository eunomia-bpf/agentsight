# Design

Last updated: 2026-07-04
Stage at update: stage 5 analyze / stage 6 claim gate / stage 9 paper integration
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `agent-session`, `script/agent_trace_to_operations.py`, `script/operation_boundary_backend_eval.py`, `script/paper_claim_synthesis.py`, `script/reviewer_evidence_packet.py`, `script/paper_value_novelty_synthesis.py`, `docs/evaluation.md`, `agentpprof --profile-spec`
Completeness: partial

## Current State And Blocking Gate

Purpose: keep the current semantic-profiler design aligned with the active
implementation.

AgentSight's semantic profiler should expose only two core abstractions:
`operation` and `operation stack`. Prompt, session, tool call, process, file
event, network event, syscall, plan step, and subagent event are concrete
operation shapes or operation fields, not separate profiler abstractions.

The current blocking gate is not more dataset breadth. R279-R294 show that
external labeled trajectories can be projected through the current Rust
implementation and folded at multiple depths. R295 now synthesizes those
tracked artifacts into claim verdicts: C1 is supported, C2 is supported with
scoped limits, and C3 is partial because current boundary evidence is
deterministic mapping/tagging rather than unsupervised discovery. The remaining
paper-grade gaps are stronger boundary detection beyond deterministic rules and
user-facing utility evidence. R296 adds a reviewer evidence packet over
tracked/clean R282-R295 artifacts; it is a navigation layer over operation and
operation-stack outputs, not a new profiler abstraction. R297 adds the first
supervised boundary-backend expansion probe: the backend predicts
OSWorld-Human human-group boundaries on held-out sessions, writes
`learned_group_pattern` fields onto operations, and the existing Rust
operation-stack path folds those fields. R298 adds a paper-value and novelty
synthesis over tracked artifacts; it is an audit layer that maps real reviewer
problems to operation/operation-stack evidence, not a runtime abstraction.

## System-Under-Test Model

Purpose: define the evaluated artifact.

The evaluated artifact is the Rust `agentpprof` CLI. It reads either local
Codex/Claude session histories or already-normalized operation JSONL and emits
pprof, folded-stack, SVG, or JSON projections.

The data model is:

```text
agent-native transcript
  -> agent-session trace exchange format
  -> operation fields + weight
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

R294 adds a portable trace exchange step for local agent sessions. `agentpprof
--export-trace` writes the parsed `agent-session` IR as
`agentsight.agent-session.trace.v1`; `agentpprof --trace-file` imports the same
trace; and `script/agent_trace_to_operations.py` converts it to operation JSONL.
On the public Codex fixture, trace import and operation-file import both produce
6 samples / 5 stacks with byte-identical folded output under the same stack
spec. This is an interoperability layer before operations, not a profiler
abstraction.

R297 adds a supervised adjacent-boundary backend over OSWorld-Human. The model
is deliberately outside the core profiler abstraction: it reads adjacent
operation fields, excludes oracle/group labels from features, predicts held-out
human-group boundaries, and writes derived fields such as
`learned_group_pattern`, `learned_group_position`, and `learned_boundary_prev`
back onto operations. `agentpprof` then folds the augmented operation file with
the ordinary stack
`project,dataset,task,phase,learned_group_pattern,learned_group_position,action,status`.
This validates the intended extension point for boundary detection: backends
derive operation fields, while recursive folding remains an operation-stack
query.

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
- learned boundary backends can write derived fields such as
  `learned_group_pattern` before stack construction, but they do not create a
  boundary object in the profiler.
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
without freezing the stack shape; learned boundary fields such as R297's
`learned_group_pattern` should be stackable fields, not a separate boundary
abstraction. This is ordering over operation fields and query configuration,
not a separate abstraction.

## Assumptions And Invariants

Purpose: name the design constraints that tests should protect.

- All profile outputs must be derivable from operations and operation stacks.
- Local-session projections and external operation JSONL must share the same
  stack construction path.
- Agent-session trace import/export must be a loss-bounded exchange format that
  can be converted to operation JSONL and then profiled through the same stack
  path.
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
| Boundary detection remains only deterministic mapping. | Evaluate learned boundary backends that derive operation fields before stack construction and compare against held-out human or dataset boundaries. | R297 trains a supervised adjacent-boundary backend on OSWorld-Human, excludes oracle/group fields from features, reaches held-out human-group F1 0.7735, and folds predicted `learned_group_pattern` fields through Rust `agentpprof`. This is still supervised and OSWorld-only, not unsupervised discovery. |
| Profile experiments remain ad hoc shell commands. | Bundle reproducible operation-file, op-map, view, stack, and output choices in profile specs while preserving CLI overrides. | R293 adds an AgentNet profile spec that reproduces the R291 608-stack diagnostic profile and folds the same operations into an 83-stack override view. |
| Local agent sessions are hard to exchange or replay outside native logs. | Export parsed sessions as `agentsight.agent-session.trace.v1`, import them through `--trace-file`, and convert them to operation JSONL. | R294 public Codex fixture smoke shows direct trace import and converted operation-file import produce identical folded stacks. |
| Paper claims drift away from tracked artifact evidence. | Mechanically synthesize claim verdicts, reviewer value, novelty, and remaining gaps from tracked result JSON/folded artifacts while keeping unsupported claims explicit. | R295 reads R282-R294 artifacts and emits supported/partial verdicts plus unsupported final claims under `docs/visexp/out/paper-claim-synthesis-r295/`; R296 indexes those verdicts with reviewer questions, derived ratios, and source paths; R298 maps 6 real-problem evidence blocks and 4 novelty claims to tracked artifacts while marking unsupervised intent discovery and developer productivity as unsupported. |
| Visualizations collapse back to flamegraphs only. | Generate tree, transition, top-field, quality, grouped-stack, history-depth, depth-sweep, and reviewer-navigation HTML/JSON reports. | R273-R296 include non-flamegraph analyses, reproducible profile specs, trace-exchange smoke tests, and an 11-entry evidence packet under `docs/visexp/out/reviewer-evidence-packet-r296/`. |
