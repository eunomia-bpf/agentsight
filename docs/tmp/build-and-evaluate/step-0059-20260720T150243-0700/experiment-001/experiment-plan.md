# Experiment Plan — Three-Transition Well-Nested Task Stack

## Research Question

- Paper question, unchanged: **RQ3 — How Accurate Are the Tags?**
- Tested uncertainty: can a persistent online task stack with only
  `stay`, `push(label)`, and single-level `pop` recover human task-progress
  occurrences more accurately than the current recurrence constructor?
- Why it matters: the desired profile needs tasks that remain active across
  many lower semantic operations, grow to uneven depth when a nested
  responsibility begins, and return to their parent when that responsibility
  ends.

## One Hypothesis And Paper Value

**Hypothesis.** On the same complete CodeTraceBench population, replacing the
Step 0056 transition language with a well-nested three-action controller—while
retaining exact same-leaf identity continuity—will make task-path occurrences
persist across phase/action/object/result changes and raise ordinary
operation-level B-cubed F1 above the current multi-resolution recurrence
constructor with a wholly positive paired task-cluster interval.

The scientific intervention is the transition language, not a new feature,
threshold, score, depth cap, benchmark, or model:

```text
stay        keep the complete active task path
push(label) append one genuinely nested task goal
pop         remove exactly the active leaf and resume its parent
```

There is no `replace` and no arbitrary ancestor target. A sibling task can
begin only after the active leaf returns to its parent. This makes the
controller a literal well-nested stack rather than an unrestricted path editor.

- Positive consequence: adopt the task/subtask-prefix constructor for further
  full-stack integration, without claiming that flat stages validate ancestor
  names or the lower semantic suffix.
- Contradictory or inconclusive consequence: reject this fixed controller and
  retain the recurrence constructor; do not tune the prompt, model, depth, or
  transition vocabulary.
- Direct thesis challenge: none. The exact thesis remains **“Agent
  observability needs profiling, not only debugging.”**

## Why This Is Not A Repeat

Step 0054 and Step 0056 used four transition kinds:

- `stay`;
- `push(label)`;
- `pop(target_depth)`, which can discard an arbitrary suffix; and
- `replace(target_depth,label)`, which discards a suffix and creates a fresh
  sibling frame in one turn.

The Step 0056 exact-leaf invariant removed duplicate-label identity churn, but
the applied full run still created 3,020 pushes and 2,983 replacements, made
only three pure pops, reached depth 28 including the root, and left 184
sessions with no depth decrease. Its B-cubed F1 was 0.649878 versus 0.662740 for
recurrence.

This experiment removes the two unrestricted path-edit operations responsible
for sibling churn and multi-level jumps. It directly tests the user's simpler
stack contract. It does not reopen global one-shot segmentation or change the
main representation.

## Fixed Representation Contract

The final intended profile remains:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

This experiment tests only the persistent
`concrete task -> nested subtask*` prefix. The root is immutable. Subtask depth
is variable and uncapped. Phase, strategy, semantic action, operation object,
and result are evidence about the active task and are not inserted as
persistent task frames. Agent, model, session, prompt, tool, command, raw path,
and status remain metadata or source evidence.

The profiler-visible identity is the complete ordered task-label path. A
maximal contiguous run of one exact visible path is a task occurrence. Hidden
frame IDs retain controller lineage only and do not define the scored semantic
partition.

## Fixed Online Interface

For each source-native agent turn, the model sees:

- the immutable concrete task;
- the current active task/subtask labels;
- the next turn's source-native intent, progress, and planned action; and
- the preceding visible result.

The model returns exactly one legal transition. At root, only `stay` and
`push(label)` are legal. Above root, `stay`, `push(label)`, and `pop` are legal.
The output contains no target depth. A push appends one concise concrete
task-goal label with a completion condition; it must not name a phase, tool,
command, file, path, status, result, inspect/edit/test/retry primitive, or
atomic operation.

The already-supported exact identity invariant is retained as the starting
mechanism rather than retested:

```text
if proposal is push(label) and label equals the active visible leaf exactly:
    apply stay
else:
    apply the proposed stay, push, or pop
```

There is no label normalization, fuzzy comparison, embedding, contraction,
phase filter, post-hoc pruning, or maximum depth.

## Fixed Model, Workload, And Isolation

- Model: the existing Qwen2.5-3B-Instruct Q4_K_M local controller used in
  Steps 0054--0056.
- Decoding: temperature zero, seed `20260720`, the same bounded source fields
  and output budget.
- Complete workload: all 405 preselected reconstructable failed CodeTraceBench
  trajectories, 17,148 source-native turns, and 20,866 operations across all
  four frameworks and five source layouts.
- Human stages, stage count, recurrence assignments, scores, framework, model,
  session, and status remain invisible during inference.
- Existing Step 0056 responses may be reused only for a byte-identical complete
  request. Because the transition grammar and system contract change, no
  nonidentical response is reusable.

## Comparisons And Standard Metrics

- Main baseline: current multi-resolution recurrence assignments on the same
  operations.
- Mechanism baseline: Step 0056 exact-same-leaf online task paths.
- Primary standard metric: ordinary operation-level B-cubed precision, recall,
  and F1 against session-local human workflow-stage occurrences.
- Primary uncertainty: 10,000 paired bootstrap resamples over the fixed 251
  task clusters for candidate minus recurrence B-cubed F1.
- Mechanism-effect interval: the same paired bootstrap for candidate minus
  Step 0056.
- Standard secondary metrics: adjacent-boundary precision/recall/F1 and exact
  span precision/recall/F1.
- Descriptive diagnostics: proposed/applied transition counts, duplicate-leaf
  stays, task depth, depth decreases, new-frame rate, phase-like labels,
  coverage, and model usage. They do not create extra gates.

Flat CodeTrace stages validate only the session-local task-occurrence
partition. They do not validate ancestor topology, open-vocabulary label
meaning, cross-run semantic equality, or the lower suffix.

## Planned Execution

1. Implement a thin evaluator by reusing the Step 0054 source reconstruction,
   prompt material, parser/scorer utilities, and Step 0056 exact-leaf rule.
   Change only the system contract, three-action grammar, single-level pop, and
   resulting request identity.
2. Run one real complete trajectory per source layout through the actual local
   Qwen2.5-3B endpoint. Repair wiring only; do not tune semantic behavior.
3. Complete all 405 trajectories even if preflight is negative.
4. Open verified human stages only after all task paths are durable, then
   compute the registered metrics and intervals.
5. Obtain one independent raw-result review before disposition.

The complete candidate uses one model, one transition language, one prompt,
one full run, and one scorer. No prompt variants, replace variant, pop-count
variant, depth rule, model sweep, threshold, calibration, or paper edit is
admitted.

## Execution Paths And Completion

- New thin evaluator:
  `script/rq3_well_nested_task_stack_eval.py`
- Reused source/controller utilities:
  `script/rq3_stateful_native_turn_task_stack_eval.py`
- Candidate artifacts:
  `.agentsight/experiments/rq3-well-nested-task-stack-v1/`
- Model server: existing local Qwen2.5-3B Q4_K_M, eight native 8,192-token
  slots, eight workers.

Full completion requires 405/405 sessions, 17,148/17,148 turns,
20,866/20,866 uniquely assigned operations, one legal applied transition per
turn, all registered standard metrics and paired intervals, and one independent
result review. Smoke cases cannot substitute for the complete workload.

## Decision

- Supported: candidate-minus-recurrence B-cubed F1 has a 95% interval wholly
  above zero and complete coverage holds.
- Contradicted: the interval upper bound is at most zero.
- Inconclusive: the interval crosses zero.

Any outcome changes only the tested constructor decision. It cannot narrow or
replace the thesis, story, contribution, RQ, or positive hypothesis. Negative
development evidence remains internal and does not enter the paper.
