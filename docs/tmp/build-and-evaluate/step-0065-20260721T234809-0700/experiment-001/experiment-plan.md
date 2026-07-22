# Experiment Plan: RQ3 recursive operation segmentation

Timestamp: 2026-07-21T23:48:09-07:00
Status: approved after three serial independent review rounds; interface and
collection cases executed, automatic-backend comparison pending

## Research Question

- RQ exactly as written in the paper: **RQ3: How accurate are the tags?**
- Specific uncertainty tested here: whether a backend-neutral, ID-addressed
  recursive segmentation interface can turn source-native operations into
  variable-depth operation paths, and whether an agent-assisted backend places
  useful task-progress boundaries without falling back to one segment per
  trace or one leaf per primitive action.
- Why the answer matters: the current Rust constructor emits one flat
  recurrence segment identity. It cannot produce the task decomposition,
  repeated work, abandoned paths, or conclusion-bearing branches that users
  expect from an agent profile.

## Paper-Value Admission

- Planned role: **supporting flat-partition experiment for RQ3**, plus two
  product-facing many-session case studies: variable-depth review-operation
  stacks and aggregate bad-good differential profiling.
- Largest credible paper story this experiment could unlock: AgentProf accepts
  task-boundary evidence from agents or traditional algorithms through
  one operation-stack interface, while a recursive agent backend recovers a
  useful variable-depth responsibility hierarchy over real trajectories.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  the current paper claims operation stacks, but its automatic constructor is
  flat and the visible hierarchy can degenerate into system fields.
- Independent evidence added beyond existing runs: the prior AgentCap case
  hard-coded source line ranges outside AgentPProf; prior Qwen runs edited a
  stack online or emitted all segments in one response. This run instead makes
  stable source-operation IDs the common boundary interface and recursively
  refines intervals.
- Why the result is not tautological, already settled, or dominated: exact
  replay of Agent-produced marks is only an interface correctness control.
  Scientific evidence comes from unseen source content and independent flat
  stage labels, not from reproducing the Agent's own annotations.
- Paper decision if positive: adopt the ID-addressed interface and retain
  agent assistance as an available annotation workflow. This experiment alone
  does not authorize claims of correct nested ancestors, cross-session semantic
  identity, semantic naming accuracy, or a validated automatic default.
- Paper decision if contradictory, mixed, or inconclusive: retain the supplied
  mark interface as a product feature, do not call the agent backend accurate,
  and use the error pattern to choose a genuinely different boundary backend;
  do not alter the fixed RQ or thesis.
- Best alternative experiment and why this one has higher decision value:
  another recurrence threshold or online push/pop policy is easier but repeats
  branches already shown flat, under-segmented, or depth-monotone. The proposed
  interface changes the information and control boundary directly.

## Expected And Alternative Outcomes

- Current expected answer: supplied stable-ID marks will reproduce the intended
  stacks exactly; a recursive whole-interval agent will avoid the earlier
  all-singleton and all-one-segment failures on real cases, but the small local
  model may still require agent review or correction.
- Strongest competing explanation: useful task decomposition may come entirely
  from Agent naming and not from recursive segmentation; a source-native
  hierarchy or the current flat recurrence may match independent partitions.
- Result that would contradict the expectation: the agent backend again
  collapses or fragments most traces, fails to produce meaningful unequal
  depth, or underperforms the current recurrence on ordinary B-cubed without a
  compensating real-case diagnostic benefit.

## Published Precedent And Real Assets

- Closest published protocol: ordinary B-cubed clustering evaluation as
  introduced by Bagga and Baldwin (1998) for partition agreement, plus exact
  adjacent-boundary precision/recall/F1 as a diagnostic. WorkArena++ and GUIDE
  remain conceptual precedents for composed
  tasks and trajectory segmentation; no unavailable implementation is treated
  as an executed baseline.
- Official system/model/data/benchmark/tool and version: current Rust
  AgentPProf; four complete real AgentCap Codex sessions; the complete retained
  405-trajectory CodeTraceBench population with official human stages; local
  llama.cpp with the already-held Qwen2.5-3B checkpoint for the first automatic
  backend.
- What is reused: normalized operation inputs, stable evidence IDs, current
  recurrence outputs and previous one-shot Qwen results, Go pprof rendering,
  and existing CodeTrace scoring paths.
- Necessary deviations or custom glue: one small Rust reader/applier for sparse
  operation marks and one research adapter that asks a backend to return mark
  IDs and operation names. No frontend or second product output is added.

## Comparison

- Proposed system or method: recursive, query-conditioned operation
  segmentation whose decisions refer only to stable source-operation IDs; a
  shared operation-name pool canonicalizes labels across sessions before
  folding.
- Main baseline on CodeTraceBench: current cross-session recurrence, which
  represents the position that low-level repeated transition structure is
  sufficient.
- Why each main baseline needs a matched run instead of citation alone: only
  recurrence requires matched CodeTrace comparison, and its retained outputs
  are reused. Source-native and one-shot results are reused where their inputs
  match; they are not rerun merely to add rows.
- Controls, labeled separately: Agent-written marks test exact interface
  semantics; a deterministic existing-task-field adapter on AgentCap tests
  backend neutrality. The older one-shot Qwen run is only a historical
  diagnostic unless its visible inputs and scoring target are exactly matched.
- Conclusion if each main baseline matches or wins: the agent backend is not
  the default automatic constructor unless it adds a visible, task-semantic
  user benefit that the matched baseline lacks; metric ties do not authorize a
  superiority claim.
- Information, tuning, and compute fairness: target stage/group labels remain
  unopened during CodeTrace annotation. Recurrence sees action-transition
  recurrence across the label-free corpus; the Agent sees the user query and
  indexed normalized operation summaries for one trajectory. These information
  budgets differ and will be stated, not described as matched. The operation
  name pool for the automatic run is initialized and updated only from the user
  query and visible source operations. AgentCap manual names and CodeTrace stage
  strings are never used to seed or canonicalize the CodeTrace pool. A literal
  target-label visibility audit runs before inference.
- Split or leakage rule when relevant: CodeTrace official stages and AgentCap
  manual paths are scoring references only. They are not placed in model
  prompts, operation names, candidate boundary lists, or stop decisions.

## Workloads And Metrics

- Real workloads or tasks:
  1. four complete AgentCap review sessions (326 normalized operations) for the
     end-to-end product case and internal manual-reference diagnosis;
  2. the complete retained AgentRewardBench mixed-outcome population (440 real
     trajectories, 125 tasks, and 338 bad-good pairs) for one aggregate signed
     differential-profile case;
  3. all 405 retained CodeTraceBench trajectories (20,866 operations) for the
     complete standard flat-partition accuracy comparison after preflight.
- Primary metrics: ordinary operation-level B-cubed precision/recall/F1 on
  CodeTraceBench. Each predicted cluster key is the complete visible semantic
  operation-ID path assigned to an operation, scoped to its trajectory; the
  official stage is the reference cluster. This tests flat occurrence
  partition agreement only. No custom weighted variant is paper-facing.
- Correctness check or ground truth: official CodeTrace human stage intervals;
  exact supplied-mark replay, full operation coverage, and mass conservation
  are implementation checks rather than scientific scores.
- Secondary diagnostics: exact adjacent-boundary precision/recall/F1,
  predicted/gold group count, depth distribution, new-frame rate, and
  qualitative case questions about decomposition, repetition, high-cost paths,
  and missing conclusions.
- Repetitions, seeds, and uncertainty: deterministic decoding for the local
  model; paired task-cluster bootstrap for final CodeTrace B-cubed differences
  if a complete run is reached.
- Cost estimate when material: model calls are per semantic interval, not per
  primitive operation; interval summaries and completed decisions are reused.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| interface | control | AgentCap | Agent-written stable-ID marks | 1 | proves sparse inheritance, variable depth, aggregation, and pprof readback |
| backend | control | AgentCap | existing source task paths through the same contract | 1 | proves backend neutrality |
| preflight | proposed | AgentCap | recursive Qwen agent annotation | 1 deterministic run | decides whether the automatic path is executable and qualitatively nondegenerate |
| main | proposed / baseline | CodeTraceBench | recursive agent vs retained recurrence and one-shot results | 1 deterministic run | supplies or rejects additional RQ3 evidence |
| case 1 | product case | all four AgentCap review sessions | one aggregate pprof, stock pprof tools | 4 fixed questions | tests decomposition, repeated repair work, conclusions, and cross-session exceptions |
| case 2 | product case | all 338 AgentRewardBench bad-good pairs | one aggregate signed pprof, stock pprof tools | 4 fixed questions | tests broad bad-side/good-side path localization beyond scalar scores |

The fixed questions and interpretation rules are recorded separately in
`case-study-protocol.md` and `case-study-2-protocol.md`. Each case treats a
collection of complete sessions as its unit; individual traces are source
drilldowns only.

## Execution

- Authoritative workflow: AgentPProf consumes normalized operations plus one
  read-only operation-mark file and emits one `.pb`/`.pb.gz`; an Agent or other
  backend produces the mark input. A mark is an addressable boundary produced
  by an Agent or algorithm, not a product human-annotation workflow.
- Mark file contract: it declares a sequence field, a replay-stable source
  operation-ID field, a pool from canonical semantic operation IDs to unique
  display names, and sparse per-sequence marks of
  `(sequence value, start source-operation ID, semantic operation-ID path)`.
  Every source operation must have exactly one nonempty sequence value and one
  nonempty ID; IDs must be unique within the sequence. Each present sequence
  must have a mark at its first source operation. Marks must be ordered,
  nonduplicated, refer to existing source IDs, contain a nonempty path, and use
  only IDs defined in the pool. Every later source operation inherits the most
  recent full path in its own sequence. Violations fail rather than silently
  falling back.
- Recursive Agent contract: every call is
  `segment(interval, current_operation_id, ancestor_path)`. The root semantic
  operation ID is chosen from the user request before the first call. `STOP`
  takes no argument and assigns `ancestor_path + current_operation_id` to the
  entire interval. `SPLIT(split_before_source_operation_id, left_id, right_id,
  reason)` creates two named sibling operations, then recurses on the left and
  right intervals with `left_id` and `right_id` as their respective current
  operation IDs and `ancestor_path + current_operation_id` as their ancestor
  path. The current node therefore enters both child paths exactly once; an
  internal binary-search range without a semantic responsibility is not a
  current operation and is never emitted. A one-operation interval must
  `STOP`. Any larger interval stops when the Agent cannot name both sides as
  distinct responsibilities or progress states. Field changes, regex matches,
  tools, files, commands, and statuses alone do not justify a split. There is
  no fixed depth cap.
- Regex is permitted only for parsing, normalization, and retrieving candidate
  source IDs. It is not a semantic boundary backend and cannot authorize a
  split without Agent semantic judgment.
- Real preflight case: one complete AgentCap session annotated by the recursive
  backend, then folded and opened with stock Go pprof.
- Full completion rule: every planned CodeTrace session reaches a terminal
  annotation result; every operation receives one path; the full matrix is
  scored and reviewed. A partial prefix is not a paper result.
- Raw-result path:
  `.agentsight/experiments/rq3-recursive-operation-segmentation-v1/`.
- Checkpoint or recovery approach: completed per-session annotation files are
  reused by stable session/evidence IDs; this is experiment data, not a gate or
  product output.

## Interpretation

- Positive result: the recursive Agent materially improves ordinary B-cubed
  over the current recurrence or matches it while producing useful
  variable-depth task paths on real product cases without fragmentation. The
  metric authorizes only flat partition evidence; the cases demonstrate
  usability but are not independent nested accuracy evidence.
- Negative or contradictory result: ID-addressed marks remain a valid user-facing
  interface, but the tested agent backend is rejected and its failure mode is
  recorded; the RQ3 hypothesis remains unchanged.
- Mixed or inconclusive result: keep the backend optional/assisted, record the
  ambiguous decisions, and do not present it as validated automatic hierarchy
  recovery.
- Target paper figure or table: only after a valid positive full result; this
  step first retains standard pprof case artifacts and a standard-metric table.

## Reproducibility Notes

- Software and data versions: recorded from the current branch, local
  llama.cpp binary, model file, and retained official datasets at execution.
- Config and seed notes: deterministic decoding; no target-label tuning.
- Known deviations: AgentCap Agent-produced paths are an internal product case,
  not public gold. CodeTrace stages score segmentation but cannot alone validate
  every nested ancestor name.

## Change Scope

This change may touch AgentPProf's annotation input path, focused Rust/Python
tests, the research adapter, usage/implementation documentation, ignored raw
artifacts, and this step's reports. It must not touch the frontend, paper
narrative, shared writing/research skills, another branch, or AgentPProf's
pprof-only product-output rule.
