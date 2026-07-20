# Step 0058 Report — Stronger-Model Sufficiency for the Task-Responsibility Stack

## Step Identity And Recovery

- started: 2026-07-20T13:52:48-07:00
- experiment completed: 2026-07-20T14:53:30-07:00
- phase: BUILD_AND_EVALUATE
- current gate: REVIEW
- selected paper RQ: **RQ3 — How Accurate Are the Tags?**
- branch at entry and completion: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `54ea58ee2ad5`
- parent: Step 0057 global Qwen2.5-3B segmentation
- status: complete

### Recovery Node

Step 0057 established that a fixed Qwen2.5-3B whole-trajectory call collapses
all 405 CodeTrace trajectories to one interval. The user's corrected
representation contract requires the main profile stack to be:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, prompt, tool, command, path, and status remain metadata,
filters, colors, measures, details, or source evidence. The exact thesis remains
**“Agent observability needs profiling, not only debugging.”** The title, four
attribution/localization/tag-accuracy/cost RQs, positive hypotheses, paper
story, paper files, canonical paper submodule, and shared skills remained fixed.

The admitted Step 0058 uncertainty was whether the same global interface is
sufficient with the already-held Qwen3.6-27B checkpoint. This is not a pure
capacity comparison because the checkpoints also differ in model generation,
training data, architecture, tokenizer, and checkpoint.

## EXPERIMENT Gate

### Experiment Plan And Serial Review Node

The registered plan is `experiment-001/experiment-plan.md`. It changes exactly
one candidate dimension: Qwen2.5-3B becomes the already-held local
Qwen3.6-27B checkpoint. The system prompt, output grammar, visible source
reconstruction, 32,768-token context, temperature zero, seed, complete selected
workload, recurrence baseline, causal control, and standard metrics remain
fixed.

One additional interpretation repair was registered before execution. The
flamegraph retains the complete six-part stack, but CodeTrace flat stages score
the persistent task occurrence: a maximal contiguous run with the same ordered
`concrete task -> nested subtask*` path. Changes only to
phase/action/object/result do not create a new task occurrence.

An independent subagent explicitly read and applied
`research-experiment-design` in three serial rounds:

1. Round 1 required replacing the invalid `capacity-controlled` causal wording
   with a checkpoint-specific stronger-model sufficiency claim, and fixing one
   DevAI trajectory before candidate scoring for a qualitative full-stack
   contract check.
2. Round 2 found one remaining `exact capacity control` phrase, which became
   `same-interface small-model control`.
3. Round 3 returned **APPROVE** with zero remaining scientific must-fix.

No reviewer added a metric, benchmark, gate, checker, threshold, prompt
variant, or paper change. The complete record is
`experiment-001/plan-review.md`.

### Minimal Evaluator Node

The existing Step 0057 evaluator was generalized only enough to execute the
approved comparison and correct the profiler identity:

- inference now records an explicit model name, file, SHA-256, server-reported
  path, and alias instead of importing the 3B identity;
- cache requests include the explicit model identity;
- the scorer uses maximal contiguous equal task/subtask paths as persistent
  task occurrences while retaining fine semantic segment identities and the
  full six-part stack;
- the renderer names the active model and reports both segment and task-
  occurrence counts; and
- a score cannot claim adoption before the independent qualitative semantic
  review.

The prompt, grammar, source clipping, workload, baselines, metric definitions,
and hidden-stage order were not changed. `py_compile`, CLI help, and a minimal
synthetic occurrence test passed. The synthetic test verified that lower-
suffix changes preserve one occurrence and that leaving and later returning to
the same visible path creates a new occurrence.

### Fixed External-Asset Node

The experiment reused only real assets already screened before the plan:

- the complete fixed 405-trajectory CodeTraceBench workload;
- the existing recurrence and causal assignments;
- the local Qwen3.6-27B Q4_K_M artifact previously used in the project; and
- the one public complete DevAI/OpenHands trajectory fixed before scoring:
  `39_Drug_Response_Prediction_SVM_GDSC_ML.json`.

The DevAI sample has seven concrete hierarchical requirements and 34 visible
trajectory steps. It is a qualitative responsibility reference, not temporal
gold and not part of the quantitative decision.

### Real Preflight Node

The real local server exposed alias `qwen3.6-27b`, one 32,768-token slot, and
the registered model file with SHA-256
`f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`.
The fixed longest complete trajectory from each of four frameworks completed:
4 sessions, 584 turns, and 584 operations.

All four outputs contained one segment and one task occurrence. Preflight
candidate B-cubed F1 was 0.163439; recurrence was 0.530705; boundary and
exact-span F1 were zero. The representative 200-operation profile was one
full-width stack and its root retained a source-native terminal-state suffix.
No parser, context, cache, coverage, or model-identity defect occurred. No
semantic tuning followed; the full workload proceeded as registered. The
detailed record is `experiment-001/real-preflight.md`.

### Complete Full-Run Node

The fixed run completed:

- 405/405 sessions;
- 17,148/17,148 source-native turns;
- 20,866/20,866 operations;
- 2,948 human stage occurrences across 251 task clusters;
- 2,869,593 prompt tokens and 23,804 completion tokens; and
- 2,361.36 seconds of inference wall time.

All 405 raw responses contained exactly one segment. Persistent task-path
construction therefore also yielded exactly one task occurrence per session.
The model emitted depth-one subtask paths in 362 sessions and no subtask frame
in 43; it never emitted an internal boundary.

The registered standard metrics were:

| Method | B³ P | B³ R | B³ F1 | Exact-span F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B task occurrence | 0.173563 | 1.000000 | 0.295788 | 0.000000 | 0.000000 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.056435 | 0.265571 |
| Causal Qwen2.5-3B path | 0.735681 | 0.581999 | 0.649878 | 0.049501 | 0.256606 |

The 10,000-resample candidate-minus-recurrence B-cubed F1 interval is
`[-0.381647, -0.350845]`, with positive fraction zero. Candidate minus causal
is `[-0.373469, -0.332215]`. The registered quantitative interpretation is
`contradicted-not-adopted`. The full record is `experiment-001/full-run.md`.

### Independent Result Review Node

A separate subagent explicitly read and applied `research-experiment-design`
and independently reconstructed the result from target JSONL, verified Parquet,
raw session responses, predictions, and both comparison assignments. It did not
trust the summary.

The reviewer reproduced every population count, occurrence assignment,
standard score, and bootstrap draw. The independently generated 10,000 draws
had maximum absolute difference zero from the saved draws. It also independently
verified the model artifact SHA-256.

The registered qualitative responsibility-frame contract **fails**:

- 93 task roots contain terminal-state or terminal-screen material;
- the representative 275-operation profile assigns one initial-package-setup
  stack across later Nginx/SSL configuration, deployment hooks, repeated SSH
  diagnosis, port changes, and a degraded conclusion; and
- the fixed DevAI reference exposes task responsibilities that visibly change
  across data loading, feature selection, model implementation, evaluation,
  repair, artifact inspection, and report generation.

The final verdict is **APPROVE — 0 must-fix** for the validity of the run, with
the tested hypothesis contradicted and the constructor rejected. The record is
`experiment-001/result-review.md`.

## WRITE Gate

### Result-Disposition Node

The negative development candidate does not enter `docs/paper/` and does not
change the positive paper story. Only `docs/design.md`, `docs/evaluation.md`,
and `docs/implementation.md` were synchronized with the bounded conclusion:
the fixed global one-shot interface fails with both tested checkpoints and is
closed.

No writing or idea-refinement skill ran. `docs/idea-story.md`,
`docs/user-instruction.md`, every file under `docs/paper/`, and the clean
canonical paper submodule at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c` remain untouched. No shared skill
or repository instruction changed.

## REVIEW Gate

### Scientific-Contract Audit Node

- The exact thesis remains **“Agent observability needs profiling, not only
  debugging.”**
- The title, four RQs, positive hypotheses, intended task hierarchy, and paper
  contribution scope remain unchanged.
- The failed candidate is called a whole-trajectory summary, not a recovered
  task-semantic hierarchy or accepted paper mechanism.
- Flat CodeTrace stages are used only for the active task-occurrence partition,
  not as validation of nested topology, open-vocabulary label meaning, or the
  lower semantic suffix.
- A 3B-to-27B difference is not called a parameter-capacity effect.
- No negative result, failed figure, or new story enters the paper.
- No branch was created or switched; Git did not determine any scientific gate.
- No shared skill, repository instruction, paper submodule, or user-intent file
  changed.
- Uncertainty did not pause for human intervention or narrow the intended
  claim.

### Efficiency And Branch-Closure Node

The step reused the same 405 source reconstructions, 17,148 turn assignments,
20,866 operations, fixed recurrence and causal outputs, one already-held model,
one prompt, one standard scorer, and one complete run. It added no benchmark,
metric, threshold, score term, oracle, model sweep, prompt sweep, or paper
experiment. The all-session collapse closes the global one-shot branch.

The next non-equivalent mechanism target is the user's simpler online stack
controller: hold a persistent variable-depth task path and classify each next
semantic operation as keep, push, or pop. Phase/action/object/result may change
without replacing the task occurrence. This is a motivated next candidate, not
an already-proved solution, and it must receive its own reviewed plan before
execution.

## Step Disposition

### Outer Audit Node

A fresh independent subagent explicitly read and applied
`auto-research-orchestrator`, independently reconstructed the raw coverage,
candidate scores, recurrence score, terminal-state contamination, and model
SHA, and audited the complete diff and lifecycle. It returned **APPROVE — 0
must-fix** for EXPERIMENT, WRITE, REVIEW, direction preservation, efficiency,
maintenance, and next-state routing. The record is
`outer-audit-20260720T145853-0700.md`.

The fixed global Qwen3.6-27B constructor is rejected; the paper remains
unchanged. The next state remains BUILD_AND_EVALUATE / EXPERIMENT_GATE for one
online persistent-stack experiment. No human intervention is required.
