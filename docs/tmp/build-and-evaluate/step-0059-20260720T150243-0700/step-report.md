# Step 0059 Report — Literal Well-Nested Online Task Stack

## Step Identity And Recovery

- started: 2026-07-20T15:02:43-07:00
- experiment completed: 2026-07-20T15:50:58-07:00
- report synchronized: 2026-07-20T16:02:03-07:00
- phase: BUILD_AND_EVALUATE
- current gate: REVIEW
- selected paper RQ: **RQ3 — How Accurate Are the Tags?**
- branch at entry and completion: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `862688d1720e`
- parent: Step 0058 global Qwen3.6-27B sufficiency test
- status: complete

### Recovery Node

Steps 0057--0058 showed that one whole-trajectory call collapses every
CodeTrace trajectory to one persistent task occurrence with both tested
checkpoints. The user's fixed main representation remains:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

System fields remain metadata or source evidence. The exact thesis remains
**“Agent observability needs profiling, not only debugging.”** The paper title,
attribution/localization/tag-accuracy/cost RQs, positive hypotheses, paper
story, paper files, canonical paper submodule, shared skills, and repository
instructions remained fixed.

The admitted uncertainty was whether the user's simplest live state machine—a
persistent variable-depth path with only `stay`, one-leaf `push`, and one-leaf
`pop`—would correct Step 0056's unrestricted path editing and exceed the current
recurrence constructor.

## EXPERIMENT Gate

### Plan And Three-Round Review Node

`experiment-001/experiment-plan.md` registers one mechanism change. It removes
`replace(target_depth,label)` and arbitrary-suffix `pop(target_depth)` and
exposes only:

```text
stay
push(label)
pop
```

Exact duplicate-active-leaf pushes remain identity-preserving stays. The model,
source-visible fields, temperature, seed, workload, complete-run obligation,
primary standard B-cubed metric, recurrence incumbent, Step 0056 mechanism
baseline, and paired task-cluster bootstrap remain fixed. No depth cap,
threshold, contraction, post-hoc pruning, model variant, prompt variant, or
alternate benchmark is admitted.

An independent subagent explicitly read and applied
`research-experiment-design` in three serial plan-review rounds. Round 1 removed
collapse/fragmentation diagnostics as hidden result gates. Rounds 2 and 3
returned **APPROVE** with zero remaining must-fix and confirmed that this is not
a renamed repeat of the prior unrestricted path editor. The record is
`experiment-001/plan-review.md`.

### Minimal Implementation And Two-Round Review Node

`script/rq3_well_nested_task_stack_eval.py` reuses the existing source-native
trajectory reconstruction, current task-stack prompt material, standard metric
implementations, and Step 0056 verified score rows. It implements only the new
three-action grammar, single-level pop, exact visible-leaf continuity, causal
cache identity, complete inference, and registered scorer.

An independent read-only implementation reviewer explicitly applied
`research-experiment-design`. Round 1 found two local defects:

1. an empty subtask suffix failed to treat the immutable root as the active
   leaf for exact duplicate identity; and
2. support redundantly required a positive point estimate in addition to the
   registered wholly positive paired interval.

Both were corrected locally. Direct behavior checks covered root-equal push and
single-level pop, cache replay remained stable, and Round 2 returned
**APPROVE — 0 must-fix**. No scientific input, prompt, model, metric, or gate
changed. The record is `experiment-001/implementation-review.md`.

### Real Preflight Node

One complete trajectory from each of the five source layouts passed through
the actual Qwen2.5-3B endpoint, parser, causal state application, operation
materialization, and standard scorer: five sessions, 84 turns, 100 operations,
95 adjacent pairs, and 23 human stage occurrences.

The model proposed 42 pushes and 42 stays; exact identity converted 17 pushes
to stays. No pop appeared in this small screen. That absence was recorded as a
diagnostic rather than turned into a new gate or a reason to tune. The complete
405-trajectory run proceeded unchanged. The record is
`experiment-001/real-preflight.md`.

### Complete Full-Run Node

The registered run completed:

- 405/405 sessions;
- 17,148/17,148 source-native turns;
- 20,866/20,866 unique operation assignments;
- 2,948 human stage occurrences in 251 task clusters;
- all four frameworks and all five source layouts;
- fixed Qwen2.5-3B Q4_K_M model artifact at temperature zero and seed
  `20260720`; and
- 27,230,342 model tokens in 2,010.24 seconds.

The applied controller contains 11,677 stays, 5,343 pushes, and 128 pops.
Exact identity accounts for 5,410 of the stays. Only 71 sessions contain any
pop, 334 never decrease depth, median per-session maximum depth is 11, p90 is
28, and the maximum is 122 including the root.

Registered standard metrics are:

| Constructor | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| Step 0056 contiguous task occurrence | 0.754887 | 0.577432 | 0.654342 | 0.256606 | 0.049501 |
| **Step 0059 well-nested task occurrence** | **0.708301** | **0.613398** | **0.657442** | **0.239777** | **0.040877** |
| recurrence incumbent | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

Candidate minus Step 0056 has mean B-cubed delta `+0.003096` and 95% interval
`[-0.005868,+0.012359]`. Candidate minus recurrence has mean `-0.005515` and
interval `[-0.020053,+0.010075]`. Both use the fixed 10,000-resample paired
251-task bootstrap. The registered result is **inconclusive-not-adopted**. The
detailed record is `experiment-001/full-run.md`.

### Independent Result Review Node

A separate subagent explicitly read and applied `research-experiment-design`,
replayed every session cache and request, reconstructed every candidate path,
and independently recalculated all three standard metric bundles and both raw
10,000-draw bootstraps.

It reproduced all coverage, transition, metric, and interval values. All 128
pops remove exactly one leaf. Candidate and Step 0056 distinct request-hash
sets have zero overlap. Model SHA, 405 archive SHAs, label-free target schema,
and inference-before-score ordering all pass.
The first pass reproduced the then-current scorer. Outer audit Round 1 returned
**REVISE** because that scorer merged non-contiguous revisits of the same path,
despite the plan defining one occurrence as a maximal contiguous equal-path
run. The scorer was
corrected symmetrically for candidate and Step 0056 without rerunning inference.
A fresh result review reconstructed all 5,761 candidate and 6,264 Step 0056
occurrences, matched every corrected metric and bootstrap draw, and returned
**APPROVE — 0 must-fix**. The record is `experiment-001/result-review.md`.

## WRITE Gate

### Result-Disposition Node

The negative/inconclusive development candidate does not enter `docs/paper/`
and does not alter the positive paper story. No writing or idea-refinement
skill ran. `docs/idea-story.md`, `docs/user-instruction.md`, every paper file,
and the canonical clean paper submodule at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c` remain untouched.

Only bounded project memory was synchronized:

- `docs/design.md` records that well-nested legality is insufficient without
  reliable task-completion judgment;
- `docs/evaluation.md` records the full standard result and claim boundary; and
- `docs/implementation.md` records the evaluation-only adapter and its known
  scientific gap.

No shared skill, repository instruction, or production Rust implementation
changed.

## REVIEW Gate

### Scientific-Contract Audit Node

- The exact thesis, title, four RQs, positive hypotheses, intended hierarchy,
  and contribution scope are unchanged.
- The result rejects only one fixed Qwen2.5-3B transition policy; it does not
  reject a well-nested task-stack abstraction.
- Flat CodeTrace stages validate only session-local task-occurrence partition,
  not recursive ancestor meaning, open-vocabulary labels, cross-run equality,
  root canonicalization, or the lower semantic suffix.
- Push/pop/depth diagnostics explain the result but are not hidden gates.
- No negative row or failure figure enters the positive paper.
- No branch was created or switched; Git was independent of scientific gates.
- No human intervention was requested, and no claim, RQ, or story was narrowed.

### Efficiency And Next-State Node

The experiment reuses one existing complete benchmark population, one held
model, one source reconstruction, one prompt, one controller, one scorer, and
two already-materialized baselines. It adds no benchmark, threshold, metric,
score feature, oracle, sweep, or implementation subsystem.

The scientific bottleneck is now precise: the literal stack is legal, but the
fixed 3B policy opens responsibilities much more often than it recognizes their
completion and still promotes phase/action phrases to persistent tasks. Another
depth rule, contraction, label cleanup, threshold, or grammar synonym would not
change that bottleneck. The next BUILD_AND_EVALUATE decision must test a
non-equivalent source of task-completion judgment while preserving the same
main representation and fixed paper contract.

## Step Disposition

The independent outer audit returned **REVISE** once for the occurrence-identity
defect, then **APPROVE — 0 must-fix** after scorer repair, fresh result review,
numeric propagation, and stale-pointer cleanup. The audit record is
`outer-audit-20260720T161357-0700.md`.

Step 0059 is complete. The candidate is not adopted; recurrence remains the
validated automatic constructor. The paper remains unchanged. The next state is
BUILD_AND_EVALUATE / EXPERIMENT_GATE for one non-equivalent source of
task-completion judgment; no human intervention is required.
