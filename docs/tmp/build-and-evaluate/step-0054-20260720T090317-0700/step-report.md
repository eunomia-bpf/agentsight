# Step 0054 Report — Stateful Task-Stack Construction

## Step Identity And Recovery

- started: 2026-07-20T09:03:17-07:00
- phase: BUILD_AND_EVALUATE
- current gate: REVIEW
- selected paper RQ: **RQ3 — How accurate are the tags?**
- branch at entry: `research/semantic-flamegraph-artifacts-v2`
- parent: Step 0053 source-native adjacent-boundary experiment
- status: complete; awaiting step-boundary Git publication

### Recovery Node

The orchestrator reread `docs/user-instruction.md`,
`docs/questions-for-author.md`, the complete `docs/idea-story.md`, the current
`docs/evaluation.md`, Step 0053's step report and outer audit, and the relevant
Step 0049 stateful-stack and task-hierarchy literature records. Repository
state was clean at commit `7f72a77c3`; the current branch and canonical
`docs/agentpprof-paper` submodule were not changed.

Step 0053 validly rejects only a fixed Qwen2.5-3B memoryless adjacent-pair
boundary policy. It does not reject a stateful task constructor. Step 0049's
earlier stack policy updated once per low-level operation, started without an
immutable source task root, and saw the preceding observation plus current
action rather than the agent's source-native task intent/progress/result. It
created a new frame on 99.96% of operations. These are concrete mechanism
differences, so a turn-level stateful constructor is not another cosmetic
prompt or cutoff variant.

The user-fixed target remains:

```text
concrete task
-> nested subtask
-> phase/strategy
-> semantic action
-> operation object
-> result
```

Agent/model/session/tool/command/path/status remain attributes, filters,
visual encodings, measures, or source evidence, never the primary semantic
path. The thesis remains exactly **“Agent observability needs profiling, not
only debugging.”** The four RQs and positive hypotheses remain unchanged.

The local `grok` CLI, `claude`, `codex`, and the Qwen2.5-3B llama.cpp server
are available. Step 0049 contains an older Grok/Claude/Codex whole-paper review;
it cannot stand in for the post-Step-0054 milestone review. A fresh multi-model
complete-paper review will run only after this step's experiment and permitted
paper synchronization complete.

### EXPERIMENT Gate Entry

`auto-research-orchestrator` selected `research-experiment-design` in full-loop
mode. The immediate admission question is whether changing the state update
from low-level operations to source-native agent turns, while preserving a
persistent variable-depth task stack, adds a real causal discriminator and can
support the intended task-semantic profile. The strongest alternative is a
GUIDE-style full-trajectory segmenter followed by typed lower frames. The plan
must compare their paper-decision value before admitting a new run, reuse the
complete CodeTraceBench trajectories and standard B-cubed scorer, and avoid
another per-operation free-label policy.

### Source-Only Turn Feasibility Screen

Before proposing another model run, the root agent reconstructed exact native
turn membership from all 405 public source trajectories and opened the verified
workflow stages only in a separate scoring pass. The population contains
20,866 operations in 17,148 native turns. MiniSWE, SWE-agent, and both OpenHands
layouts contain one retained operation per native turn in this population;
Terminus2 contains 7,201 operations in 3,483 response turns, including 1,426
multi-operation turns and a maximum of 22 operations in one turn.

Of 2,543 official adjacent stage boundaries, 167 fall within a single native
turn, all on Terminus2. Thus 6.57% of the flat gold boundaries cannot be
recovered by a constructor that updates its persistent task stack only between
turns. This is acceptable for testing a task-stack leaf, because individual
commands remain visible as lower semantic-action/object/result evidence, but it
must remain an explicit evaluation boundary.

The turn partition itself has ordinary B-cubed precision 0.9832, recall 0.2212,
and F1 0.3611. Treating every turn as a task is therefore another severe
over-segmentation baseline, not the algorithm. More importantly, 312 of 405
trajectories have one retained operation per turn. Turn granularity alone does
not distinguish the new candidate from the failed Step 0049 policy. The admitted
causal change must instead be the strict definition and persistence of a task
frame: an immutable concrete-task root, source-native intent/progress, and a
rule that tool, command, file, status, inspect, edit, test, retry, or one atomic
operation cannot by itself create a task node.

The resulting experiment plan is
`experiment-001/experiment-plan.md`. It tests only the task/subtask constructor.
The intended transient suffix `phase/strategy -> semantic action -> operation
object -> result` remains part of the design contract but is not silently
treated as validated by flat CodeTrace stage labels.

### Experiment Plan Review Node

An independent reviewer explicitly used `research-experiment-design` and read
the complete proposed plan. Round 1 required three bounded corrections: freeze
the exact JSON transition grammar and target-depth semantics, make the
persistent-task versus transient-evidence boundary operational, and state that
the full-population ordinary B-cubed decision is the adoption boundary rather
than adding per-framework vetoes. The root revised only those points. Round 2
returned `APPROVE` with zero must-fix items. The serial review is recorded in
`experiment-001/plan-review.md`.

### Real Preflight Node

The fixed evaluator passed syntax, grammar, source-layout, and operation-to-turn
coverage checks. A real five-trajectory preflight covered every source layout,
100 operations, 84 native turns, and one Terminus2 response containing seven
operations. Every transition was legal and every operation was assigned once.
The preflight also exposed a high new-frame rate and phase-like labels, but the
registered protocol correctly forbade prompt tuning after seeing this behavior.
The full run therefore used the unchanged prompt, grammar, model, and seed.
Details are in `experiment-001/real-preflight.md`.

### Full Experiment Node

The official inference completed all 405 trajectories, 17,148 native turns,
and 20,866 operations. All 17,148 Qwen2.5-3B calls succeeded on the first
attempt, the active stack was never truncated, and inference remained isolated
from human stages and baseline assignments. The policy emitted 6,534 pushes,
6,249 replacements, 4,363 stays, and two pops. Its new-frame rate was 0.745451;
operation depth including the immutable root ranged from 1 to 69.

The candidate reached ordinary B-cubed precision/recall/F1
0.931958/0.333171/0.490861. It improved over the prior raw operation stack
(0.247572 F1) and native-turn singleton control (0.361145 F1), but lost to the
multi-resolution recurrence constructor (0.662740 F1). Across 10,000 paired
task-cluster resamples, candidate-minus-recurrence B-cubed F1 had mean
-0.172258 and 95% interval [-0.206653,-0.136663], with no positive resample.
The registered hypothesis is contradicted and the fixed policy is not adopted.

The most useful mechanism observation is identity churn: 6,246 new frames
repeat the preceding active leaf label, and 2,732 replacements preserve the
complete visible label path while changing only hidden frame identity. This is
a concrete failure of task continuity, not evidence for putting agent, model,
tool, command, path, or status into the semantic stack. The complete record is
`experiment-001/full-run.md`.

### Independent Result Review Node

A different independent reviewer explicitly used
`research-experiment-design` and reconstructed coverage, source joins, stack
transitions, ordinary B-cubed and secondary metrics, bootstrap uncertainty,
framework heterogeneity, and gold isolation directly from raw artifacts. It
requested two wording corrections: use exact `phaseN`/`phase-N` terminology and
describe identity churn as prominent and testable rather than proven to be the
primary cause. After those corrections it returned `APPROVE`, zero must-fix,
valid run, contradicted tested hypothesis, and decisive mechanism evidence.
The review is `experiment-001/independent-result-review.md`.

## WRITE Gate

### Scientific-Contract Audit Node

- thesis: unchanged, exactly **“Agent observability needs profiling, not only
  debugging.”**
- RQs: unchanged; RQ3 remains tag accuracy and the four fixed RQs remain
  attribution, localization, tag accuracy, and cost.
- positive hypothesis: unchanged; one failed development policy does not answer
  the complete RQ or shrink the intended claim.
- intended main path: unchanged and now explicit in design/evaluation memory as
  `concrete task -> nested subtask -> phase/strategy -> semantic action ->
  operation object -> result`.
- metadata boundary: agent/model/session/tool/command/path/status remain
  metadata, filters, encodings, measures, or source-linked evidence.
- paper: unchanged. A contradicted development mechanism is not inserted into
  the positive paper and does not authorize story rewriting.
- canonical submodule: untouched.

### Canonical Memory Update Node

The root made only targeted current-state updates:

1. `docs/evaluation.md` records the complete standard result, rejected policy,
   and identity-continuity frontier next to Step 0053;
2. `docs/design.md` records that task identity must precede deeper topology and
   that adding system fields cannot repair the hierarchy;
3. `docs/implementation.md` identifies the two development evaluators and
   explicitly states that the stateful backend is neither integrated nor
   adopted; and
4. `docs/user-instruction.md` already preserves the user's full latest task-
   semantic hierarchy correction verbatim, so it was not duplicated.

No writing skill was invoked, no paper prose was edited, and no Git action was
performed inside the gate.

## REVIEW Gate

### Gate Entry And Progress Diagnostic Node

The root entered REVIEW only after the approved experiment plan, real
preflight, complete full run, independent result review, scientific-contract
audit, and targeted canonical-memory update were present. The deterministic
progress reporter saw four RQ identifiers, no open author question, current
evaluation/report activity, and one heuristic unresolved marker. Its only
warning was five historical post-BOOTSTRAP full-writing directories. Step 0054
did not run full writing, so that historical warning does not invalidate or
redirect this step.

### Profiling-Identity Diagnostic Node

During REVIEW, the root checked whether the registered candidate key matched
the object a profiler exposes. It did not: the registered scorer groups by
`active_leaf_instance`, including hidden unique frame IDs, while pprof/flamegraph
folding normally groups equal visible label paths. A read-only diagnostic over
the already fixed predictions found:

| Identity | Groups | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| hidden active-frame instance | 13,041 | 0.490861 | 0.261643 |
| complete visible label path | 9,585 | 0.567111 | 0.262350 |
| visible path with adjacent identical task labels idempotently collapsed | 6,290 | 0.631815 | 0.264670 |
| multi-resolution recurrence | 6,018 | 0.662740 | 0.265571 |

For collapsed visible paths minus recurrence, the 251-task/10,000-resample
paired interval is [-0.048340,-0.013442], with mean -0.031109 and positive
fraction 0.0005. Terminus2 is positive (+0.067372 B-cubed F1); OpenHands,
SWE-agent, and MiniSWE remain negative. These values were inspected before a
new plan and are therefore retrospective diagnostics, not a preregistered
positive result. They show both that visible semantic identity materially
changes the answer and that identity correction alone does not yet beat the
incumbent.

The diagnostic also exposes a gold boundary. CodeTrace stage IDs are
session-local contiguous occurrences, not cross-run responsibility classes.
Session may namespace the accuracy computation without becoming a stack frame;
global recurring-path folding must be reported separately and cannot be called
validated by these stage IDs.

### Independent Outer Audit And Meta-Review Node

A fresh reviewer with no plan, implementation, execution, writing, or prior
result-review role explicitly used `auto-research-orchestrator` and performed a
read-only outer audit plus meta-review. Its verdict was **CONDITIONAL PASS**:

- EXPERIMENT passes for complete, isolated, standard-metric evaluation of a
  hidden task-instance stage constructor;
- WRITE correctly kept the paper, idea story, thesis, four RQs, positive
  hypotheses, and canonical submodule unchanged;
- the registered result cannot be generalized to the profiling-visible-path
  constructor until the identity mismatch receives a reviewed score-only
  audit; and
- no new skill, project instruction, integrity mechanism, human decision, or
  paper rewrite is justified.

The complete independent review is `outer-audit.md`. Its three meta-review
conclusions are:

1. **Research quality and maintenance:** real assets, complete execution, and
   standard metrics are sound; construct alignment between internal controller
   identity and external profile identity is the material defect.
2. **Efficiency and repeated failure:** the full run was expensive but not
   wasted because it exposed a stable pathology. Do not spend a step on the
   already-known 2,732 replacement-only repair, and do not immediately tune the
   prompt, depth, phase filter, pruning, or fuzzy threshold.
3. **Direction:** remain in BUILD_AND_EVALUATE and return to EXPERIMENT for one
   reviewed score-only visible-path identity audit over fixed outputs.

### Root Disposition And Ranked Open Objections

The root accepts every must-fix item. `docs/evaluation.md` and
`docs/implementation.md` now distinguish hidden occurrence identity from
visible profiling identity, and this REVIEW section corrects the stale gate
metadata. The paper and idea story remain unchanged.

Ranked open objections carried forward are:

1. visible label-path profiling identity has only retrospective diagnostics,
   not an independently reviewed registered score;
2. CodeTrace does not validate cross-run equivalence of generated task paths;
3. flat stages do not validate recursive ancestors or the lower
   phase/action/object/result suffix;
4. the fixed 3B policy still emits phase-like frames, almost never pops, and
   permits runaway depth; and
5. exact task roots do not yet normalize paraphrased recurring responsibility.

The size and historical density of `docs/evaluation.md` is a maintenance issue,
but compacting it is deliberately deferred to a bounded housekeeping WRITE
step so it cannot become a new blocker or contaminate the next experiment.

### REVIEW Transition

Milestone whole-paper review is skipped because the paper did not change and
no mechanism was adopted. The next outer transition is:

```text
Step 0054 complete
-> Step 0055 EXPERIMENT
-> reviewed score-only visible semantic-path identity audit
-> if still below recurrence, at most one causal exact-same-leaf identity run
-> if that fails, retire this online Qwen2.5-3B transition branch
```

Step 0055 may use only exact visible labels, adjacent-label idempotence, and the
fixed outputs. It may not add fuzzy matching, embeddings, phase deletion, path
pruning, a depth cap, system-field stack keys, or another model call. If the
score-only audit confirms the known remaining gap, the one permitted causal
test changes only this invariant: a `push` or `replace` label exactly equal to
the active visible leaf preserves the current frame and ancestry as `stay`.

- completed: 2026-07-20T10:32:11-07:00
- paper synchronization: not entered; no positive adopted evidence
- next phase: BUILD_AND_EVALUATE
- next gate: EXPERIMENT
