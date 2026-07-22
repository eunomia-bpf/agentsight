# Experiment Plan — Source-Native Task-Control pprof

## Product-Boundary Amendment

The later author instruction fixes one hard product rule: AgentPProf emits one
standard pprof profile and does not add or depend on a custom frontend or
renderer. The scientific question, task-state algorithm, workload, reference,
and metrics below are unchanged. The former custom SVG output is removed; the
same variable-depth stack is serialized by AgentPProf and inspected with
existing `go tool pprof` commands.

## Research Question

- Fixed paper question: **RQ3 — How Accurate Are the Tags?**
- Tested uncertainty: can AgentProf reconstruct the task hierarchy that a real
  agent explicitly creates and maintains, and attach every lower operation to
  that hierarchy without turning agent, model, session, tool, command, path,
  or status into task frames?
- This experiment tests faithful task-state observation. It does not claim to
  recover an unexpressed ideal human plan or judge whether the agent chose the
  right tasks.

## Hypothesis And Paper Value

**Hypothesis.** Across the complete eligible local Codex session population,
one deterministic source-native task-control projection will reconstruct every
explicit user-task occurrence, plan item, delegation, nested agent task, and
completion;
assign every ordinary operation to exactly one active task path; preserve all
additive resource weights; and produce a main profile of the form:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

The tested insight is that a task-semantic profile should expose the
agent's actual control structure. An incorrect, repeated, abandoned, or
unproductive declared subtask remains visible because that is precisely the
behavior an analyst needs to see. A benchmark's ideal solution is not allowed
to overwrite the agent's own decomposition.

A positive result establishes a real task-centric construction path and one
representative standard pprof for later RQ1/RQ2 evaluation. A failed projection
returns to parser/state-machine repair. Neither outcome changes the thesis,
the four RQs, or the intended task hierarchy.

## Complete Real Workload

The input population is every JSONL session below `~/.codex/sessions` that:

1. parses as a Codex session with one `session_meta` record;
2. contains a root user task or is linked by `parent_thread_id` to a parent
   `spawn_agent` task;
3. contains at least one actual task-control event: `update_plan`,
   `spawn_agent`, or a child-session task/completion event; and
4. contains at least one attributable model or tool operation.

Eligibility is determined from event types and links before constructing or
scoring task paths. No session is included or excluded based on task quality,
success, depth, resource use, or the eventual profile. The full run reports
all parse failures and unresolved parent links rather than silently dropping
them.

The source is real Codex usage, not a project-authored synthetic harness. The
current filesystem census contains 6,355 session files and about 46.4 GB; the
exact eligible session, task-control event, operation, byte, and depth counts
are outputs of real preflight and the complete run, not assumptions in this
plan.

## One Deterministic Task-State Rule

Only source-native task-control events may mutate persistent task state.

1. Each root-session user turn opens a new concrete-task occurrence. It owns
   subsequent operations in that session until the next root-session user turn;
   a later user turn ends the preceding occurrence without inventing a success,
   failure, or abandonment label.
2. Each session maintains its own active path. An `update_plan` item with
   status `in_progress` becomes the current child
   responsibility of that session. A later plan update completes, replaces,
   or resumes plan items exactly as the emitted statuses specify.
3. `spawn_agent` opens a separate child branch using the delegated task text.
   The child inherits a snapshot of the parent's active path at the spawn
   event. Later parent operations continue on the parent's own path and never
   enter a live child's branch; sibling children are independent.
4. The spawn function output's child thread/agent ID must equal the child
   session ID, and the child's `parent_thread_id` must equal the spawning
   session ID. The spawn call ID binds the delegated text to that child. A
   nickname, time proximity, or depth alone is never used to guess a link.
5. A child session's own active plan item nests below its delegated task. A
   nested child agent repeats the same rule, so depth is variable and uncapped.
6. A child completion closes only that child branch. It does not pop or mutate
   its concurrently executing parent or sibling branches.
7. Every ordinary LLM, tool, command, file, process, and network operation
   inherits the active task path at its event time and cannot create, rename,
   or close a persistent task frame.

There is no learned transition policy, per-operation Qwen classification,
recurrence score, threshold, depth limit, post-hoc contraction, or metadata
field hierarchy in the task prefix. Sessions without an explicit child task
remain at their concrete-task root; the system does not hallucinate missing
decomposition.

The lower suffix is kept separate:

- `phase/strategy` and `semantic action` summarize what the active task is
  doing now;
- `operation object` identifies the acted-on command, file, API, or other
  object;
- `result` records the visible outcome;
- agent, model, session, tool type, status, and raw paths remain filters,
  colors, measures, or detail fields.

This experiment must first make the persistent task prefix correct. Existing
deterministic lower-suffix adapters may be reused for the pprof example,
but their semantic accuracy is not adjudicated here.

## Independent Reference And Standard Metrics

The candidate projection and reference replay read the same immutable raw
events but use separate implementations and source-coordinate identities:

- the candidate consumes normalized AgentSight events and constructs the task
  stack used for profiling;
- the reference reads raw Codex task-control records, parent links, emitted
  plan statuses, and event order directly, then expands the resulting active
  path over raw operation timestamps.

Task identity for accuracy is not pprof frame text. A root occurrence is
identified by `(session ID, root user-event index)`. A delegated task is
identified by `(spawn call ID, child thread ID)`. A plan item is identified by
its first raw `(update_plan call ID, item index)` and retains that identity
across later status-only updates with byte-identical item text and duplicate
ordinal; edited or newly inserted text creates a new source occurrence. Raw
text is retained as its display label, but truncation, escaping, or other
display cleanup cannot change scored identity.

The reference does not use candidate paths, profile output, emitted frames,
or resource aggregates. This measures source fidelity, not agreement with an
LLM-authored pseudo-gold hierarchy.

The one primary standard metric is **operation-level exact-path accuracy**:
the fraction of eligible ordinary operations whose complete ordered task path
matches the independent reference exactly. Secondary diagnostics are exact
task-transition precision/recall/F1, unresolved-operation count, unresolved
parent-link count, depth distribution, and task-frame coverage.

Structural invariants are required for a valid run:

- every eligible operation appears exactly once;
- every emitted task path begins with one concrete task root;
- parent/child paths respect the uniquely linked spawn result, source-reported
  session ancestry, per-session event order, and parent-path snapshot;
- no agent/model/session/tool/command/path/status value is a persistent task
  frame; and
- event count, elapsed-time weight, and token weight are each conserved before
  and after folding.

Exact fidelity is the expected outcome because the task controls are explicit.
Any mismatch is a constructor defect, not evidence that task-centric profiling
is scientifically false.

## Real Preflight

Preflight runs the real parser and constructor on the first lexicographic
eligible root session family, including all linked descendants. It must:

1. parse actual JSONL and resolve the root/child session links;
2. show at least one concrete root, plan item or delegation, inherited ordinary
   operation, and completion/return when those events exist in the family;
3. compare candidate and independent-reference paths operation by operation;
4. verify resource conservation and the metadata exclusion rule; and
5. emit one standard pprof whose main frames are tasks, subtasks, and the lower
   semantic evidence suffix rather than system fields, then read it with
   `go tool pprof`.

Preflight repairs only parsing, ordering, linkage, and pprof serialization
defects. It
does not change task meanings, add inferred task frames, select a prettier
session, or substitute for the complete run.

## Full Run And Outputs

After preflight, process the complete eligible population to completion. Keep
the implementation thin by reusing AgentSight's existing Codex parser,
operation representation, additive aggregation, and pprof serialization.

Required outputs are:

- population and parse report;
- normalized task-control and operation records;
- independent reference paths and candidate paths;
- exact-path and transition metrics;
- ancestry, uniqueness, metadata-exclusion, and resource-conservation checks;
- distributions of task depth, operations/tokens/time per task, repeated task
  paths, source-declared completions and explicit failures when present, and
  paths still open at capture end;
- one declared representative task-centric `.pb.gz`, decoded and queried with
  stock `go tool pprof`; and
- a detailed Markdown full-run report plus independent result review.

The representative root session is selected before profile construction as the eligible
family with the largest number of explicit task-control transitions, breaking
ties lexicographically. It is not selected by visual appearance or success.

## Interpretation Boundary

A positive result is supporting source-fidelity evidence for faithful profiling
of **explicit source-native task state** in real Codex sessions, not a complete
RQ3 answer. It directly enables analysis of where an agent spent resources,
repeated work, delegated subtasks, returned from children, or still had an open
task when capture ended.

It does not yet show that an LLM can infer tasks when an agent emits no task
controls, that two paraphrased labels across unrelated runs have the same
canonical identity, or that the declared decomposition is the ideal human
solution. Those are separate experiments. WorkArena, TaskBench, RoboCerebra,
and similar public assets may test parts of those questions, but none should be
mixed into this source-fidelity experiment or used to replace the agent's
actual task history.

## Plan Review

This plan receives exactly three serial independent review rounds. Review
checks whether the task-state semantics answer the intended
question, whether the reference is independent enough to catch implementation
errors, whether the workload is complete, whether the primary metric is
standard and interpretable, whether metadata can leak into task frames, and
whether any machinery can be removed. Implementation begins only after the
reviewed plan receives PASS with no must-fix issue.

## Execution Path

- evaluator: `script/source_native_task_stack_eval.py`
- raw output: `.agentsight/experiments/source-native-task-stack-v1/`
- pprof output: `docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz`
- planned command:

```bash
python3 script/source_native_task_stack_eval.py \
  --sessions-root /home/yunwei37/.codex/sessions \
  --output .agentsight/experiments/source-native-task-stack-v1

cargo run --manifest-path agentpprof/Cargo.toml -- \
  --operation-file .agentsight/experiments/source-native-task-stack-v1/full/pprof-operations.jsonl \
  --view operations \
  --stack task,phase,action,object,result \
  --format pprof \
  --deterministic-output \
  --output docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz

go tool pprof -top \
  docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz
```
