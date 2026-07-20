# Step 0055 Report — Visible Task-Semantic Profile Identity

## Step Identity And Recovery

- started: 2026-07-20T10:37:01-07:00
- phase: BUILD_AND_EVALUATE
- current gate: REVIEW
- selected paper RQ: **RQ3 — How accurate are the tags?**
- branch at entry: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `0e0749d13dd8`
- parent: Step 0054 source-native stateful task-instance experiment
- status: complete; awaiting step-boundary Git publication

### Recovery Node

The orchestrator entered from Step 0054's completed independent outer audit.
The paper thesis remains exactly **“Agent observability needs profiling, not
only debugging.”** The four fixed RQs and positive hypotheses remain unchanged.
The intended primary stack remains:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent/model/session/tool/command/path/status remain metadata, filters, visual
encodings, measures, or source-linked evidence. The canonical paper and
`docs/agentpprof-paper` submodule are unchanged.

Step 0054 completed a valid 405-trajectory online inference run but registered
hidden `active_leaf_instance` as the candidate partition. Its outer audit found
that this is not necessarily the identity emitted by a profiler: flamegraphs
fold equal visible stack labels, while hidden frame IDs retain occurrence
lineage. The next node must correct that construct mismatch before another
model run.

### Retrospective Diagnostic Disclosure

The result direction was inspected during Step 0054 REVIEW. Exact visible paths
reached ordinary B-cubed F1 0.567111; paths with adjacent identical task labels
treated idempotently reached 0.631815; multi-resolution recurrence reached
0.662740. The collapsed-path paired interval remained negative. Step 0055 is
therefore not a preregistered discovery or an attempt to rescue a positive
claim. It is a formally reviewed, independently recomputed construct-correction
audit needed to make the profiler output and scorer refer to the same object.

## EXPERIMENT Gate

### Gate Entry Node

`auto-research-orchestrator` selected `research-experiment-design` in full-loop
mode. The candidate changes only the score/output identity over fixed
predictions. It makes no model call and does not change transitions, labels,
depth, input evidence, benchmark population, human stages, incumbent, metric,
or uncertainty procedure. The plan is
`experiment-001/experiment-plan.md`.

### Experiment Plan Review Node

A fresh independent reviewer explicitly used `research-experiment-design`.
Round 1 found that the initial plan incorrectly treated adjacent identical
labels as if standard flamegraph folding removed them, and that the construct
effect and constructor-adoption comparison did not have separate uncertainty
tests. The root revised only those points: exact complete visible path is now
primary, contraction is secondary, and visible-minus-hidden and visible-minus-
recurrence receive distinct paired bootstraps. Round 2 returned `APPROVE` with
zero must-fix. The complete serial record is
`experiment-001/plan-review.md`.

### Real Preflight Node

The approved evaluator passed syntax and executed on five complete real
trajectories, one per source layout. It joined 100 operations and 95 adjacent
pairs exactly, preserved full visible frame sequences, separated session
namespace from the stack, reproduced hidden-instance control values, and made
no model call. Small-preflight scores were treated only as wiring diagnostics;
the plan was not tuned. The record is `experiment-001/real-preflight.md`.

### Full Experiment Node

The full score-only run completed all 405 trajectories and 20,866 operations
without a model call. Hidden-instance and recurrence controls reproduce Step
0054 exactly. Exact complete visible path raises ordinary B-cubed F1 from
0.490861 to 0.567111; the paired visible-minus-hidden interval is
[+0.060647,+0.092940]. The construct effect is supported. Exact visible path
still trails recurrence at 0.662740, with paired interval
[-0.123890,-0.068765], so the online constructor is not adopted.

Adjacent-identical-label contraction is retained only as a secondary mechanism
diagnostic. Its B-cubed F1 is 0.631815: repeated directly nested labels account
for part of the remaining gap under this scorer, but standard flamegraph
identity itself does not remove them and the diagnostic still does not beat
recurrence.

The complete record is `experiment-001/full-run.md`; raw outputs are under
`.agentsight/experiments/rq3-stateful-visible-path-identity-v1/full/`.

### Independent Result Review Node

A different fresh reviewer explicitly used `research-experiment-design`, made
no model call, and independently reconstructed path identities, all standard
metrics, both paired bootstraps, framework slices, global fold counts, and the
AgentProf folded-stack behavior from raw fixed inputs rather than trusting the
new evaluator. It returned `APPROVE` with zero must-fix.

The review exactly reproduces 405 sessions, 20,866 operations, 9,585 exact
visible groups, B-cubed F1 0.567111, both paired intervals, and all global and
framework results. It also confirms from the AgentProf implementation that
every ordered frame is preserved: adjacent contraction is not the actual
flamegraph identity. The review is
`experiment-001/independent-result-review.md`.

## WRITE Gate

### Scientific-Contract Audit Node

- thesis: unchanged, exactly **“Agent observability needs profiling, not only
  debugging.”**
- RQs: unchanged; RQ3 remains tag accuracy and is not replaced by this local
  mechanism question.
- positive hypothesis: unchanged; constructor adoption failed, while the local
  output-construct correction succeeded.
- primary hierarchy: unchanged as `concrete task -> nested subtask ->
  phase/strategy -> semantic action -> operation object -> result`.
- metadata boundary: unchanged; session namespaces the score but is not a
  semantic frame, and agent/model/tool/command/path/status remain metadata or
  evidence.
- paper and canonical submodule: unchanged. The result corrects development
  evaluation semantics but does not adopt a new paper mechanism.

### Canonical Memory Update Node

The root made only current-frontier updates:

1. `docs/evaluation.md` records the independently approved visible-path
   construct effect and negative recurrence adoption comparison;
2. `docs/design.md` distinguishes visible label-path folding from internal
   instance lineage and from adjacent-label normalization; and
3. `docs/implementation.md` records the thin score-only evaluator and the fixed
   constructor's remaining gap.

No writing skill, idea refinement, paper edit, user-instruction duplication, or
Git action occurred inside the gate.

## REVIEW Gate

### Gate Entry And Progress Diagnostic Node

REVIEW began after the approved plan, real preflight, complete 405-trajectory
score, independent raw recomputation, scientific-contract audit, and targeted
canonical-memory update were present. The progress reporter saw current report
and evaluation activity, four RQ identifiers, no open author question, and one
heuristic unresolved marker. Its only warning was five historical post-
BOOTSTRAP full-writing directories; Step 0055 ran no writing loop or paper edit.

### Independent Outer Audit And Meta-Review Node

A fresh reviewer with no Step 0055 planning, implementation, execution, or
result-review role explicitly used `auto-research-orchestrator` and performed a
read-only outer audit. It returned **APPROVE FOR ROUTING** with zero scientific,
experiment-validity, or paper-drift must-fix. The complete audit is
`outer-audit.md`.

The reviewer independently confirms:

1. EXPERIMENT validly separates visible representation, session-local accuracy,
   and online-constructor adoption using standard metrics and complete real
   data;
2. WRITE correctly updates only design/evaluation/implementation memory while
   leaving the paper, idea story, thesis, RQs, and canonical submodule intact;
3. Step 0055 is efficient because it reuses fixed outputs and makes no model
   call; and
4. one final exact-same-leaf causal replay has decision value because changing
   the applied stack changes every later model-visible context and cannot be
   reproduced by post-hoc contraction.

### Root Disposition And Ranked Open Objections

The root accepts both step-close fixes. This report now records completed
REVIEW, and `docs/evaluation.md` describes the Step 0055 audit in completed
rather than future tense.

Ranked objections carried forward are:

1. the fixed online task-stack constructor remains below recurrence;
2. the complete recursive hierarchy and lower semantic suffix remain
   unvalidated by flat stages;
3. CodeTrace cannot validate cross-run semantic equality;
4. the online policy still exhibits phase-like labels, rare pops, and excessive
   depth; and
5. canonical memory remains history-heavy and should be compacted only after
   this bounded branch reaches a decision.

None changes the thesis, four RQs, positive hypotheses, or target hierarchy.

### REVIEW Transition

Milestone whole-paper review is skipped because no new constructor was adopted
and the paper did not change. The next state is BUILD_AND_EVALUATE /
EXPERIMENT_GATE for exactly one causal intervention:

```text
if proposed transition is push or replace
and proposed label == current active visible leaf label exactly:
    apply stay
else:
    apply the original transition unchanged
```

The next experiment keeps the same prompt, model, source-native evidence,
grammar, full 405-trajectory population, recurrence comparator, ordinary
B-cubed primary metric, paired task-cluster adoption rule, and no-depth-cap
policy. It adds no normalization, fuzzy match, phase deletion, contraction,
field, threshold, model, or second intervention. Unchanged response prefixes
may be reused only where the complete request is byte-identical; after the
first changed applied transition, later turns require causal replay.

If the candidate does not exceed recurrence with a wholly positive paired 95%
interval, the online Qwen2.5-3B branch closes. The negative result remains in
experiment history, while the thesis, RQs, positive RQ3 hypothesis, and
task-semantic hierarchy remain unchanged.

- completed: 2026-07-20T11:02:24-07:00
- paper synchronization: not entered; no constructor adopted
- next phase: BUILD_AND_EVALUATE
- next gate: EXPERIMENT
