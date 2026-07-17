# Experiment Plan: Local-Evidence-Preserving Semantic Ranking

**Proposed:** 2026-07-17T05:22:37-07:00
**Outer gate:** `EXPERIMENT_GATE`
**Skill:** `research-experiment-design`
**Status:** approved for real preflight after follow-up plan review
**Mode:** deterministic reuse of the three complete Step 0036 trajectory populations
**Planned role:** adaptive supporting mechanism development, not untouched confirmation

## Research Question

- **Paper RQ, unchanged:** **RQ2: Does profiler output correspond to real
  problems?**
- **Paper-level hypothesis, unchanged:** A fixed semantic profile should
  concentrate independently annotated failures, unsafe effects, redundant
  work, or task boundaries and reduce inspection versus flat, per-session,
  native, and raw-action views without using target labels.
- **One tested hypothesis:** When an operation already has a target-blind local
  diagnostic score, preserving every strict local-score preference and using
  semantic recurrence only to refine local-score ties ranks independently
  annotated problem operations better than local evidence alone, matched
  raw-action tie refinement, and the current semantic-group-only score.

This is one hypothesis inside RQ2. It does not answer the entire RQ, change the
four RQs, alter the thesis, or authorize a story rewrite.

## Why This Experiment Is Admitted

Step 0036 holds the external diagnostic signal fixed and exposes one common
mechanism boundary over 1,756 trajectories and 27,346 operations:

- current semantic grouping improves MAP and expected Recall@20% over matched
  raw-action grouping on all three workloads;
- the unpropagated atomic score decisively beats current AgentProf on both
  metrics in AgentProcessBench;
- current AgentProf improves over atomic on HINTBench MAP and TraceElephant
  Recall@20%, while the other atomic comparisons are mixed; and
- in HINTBench, group-level nonzero support reaches all 136 clean trajectories
  and 76.54% of their operations, whereas atomic support reaches 9.56% and
  0.742%.

The final fresh Step 0036 review is `VALID / SUPPORTED` with boundary research
value; its final hashes, complete recomputation, and interpretation are in
`step-0036-20260717T041400-0700/01-experiment-gate/experiment-001/result-review.md`.
The largest remaining explanation is therefore simple: group aggregation can
use recurrence to resolve weak or tied evidence, but it can also overwrite a
stronger operation-local ordering and broadcast support. A new dataset, model,
score term, cutoff, or hierarchy is unnecessary before testing that mechanism
directly on the same complete inputs.

Earlier entries in `docs/evaluation.md` froze further RQ2 score variants after
Step 0033. That was the correct decision before the Step 0035 whole-paper
review selected the missing atomic/fixed-budget decomposition and Step 0036
exposed this specific mechanism boundary. The user's later explicit objective
now asks for one improvement of the current algorithm on the already-run
trajectories rather than another benchmark or a new algorithm family. That
later direction supersedes the blanket freeze for this one candidate only;
`docs/evaluation.md` records the supersession and still forbids another metric,
cutoff, model, benchmark, hierarchy, or open-ended score search.

This experiment outranks immediate WRITE because the current paper's group-
only RQ2 ranking loses decisively to atomic evidence on one complete workload
and spreads support broadly on another. The candidate directly tests the
common cause with no new data collection or tuning surface. Stopping at Step
0036 would leave that mechanism knowingly unresolved; adding another writing
round cannot determine whether local-order preservation fixes it.

This experiment is paper-valued because a positive result would supply a
simple decision rule with explicit properties, rather than another heuristic
weight or benchmark-specific exception. A negative result would show that the
semantic score's gains cannot be recovered as a target-blind refinement of the
local signal and would close this candidate without shrinking RQ2.

Because the candidate was chosen after inspecting Step 0036 target-dependent
results, this is transparently **post-hoc adaptive development** on the same
three populations. Rank construction remains label-free conditional on the
fixed score columns, but candidate selection is not. Bootstrap intervals are
conditional descriptive uncertainty over these populations, not evidence from
an untouched test set. The experiment can support adoption of a simpler
mechanism on these observed complete workloads; it cannot by itself establish
new-population generalization.

## Fixed Inputs

The experiment reuses the corrected Step 0036 inputs and no others:

| Workload | Complete population | Target-bearing / clean trajectories | Fixed local signal | Fixed semantic and raw grouping scores |
|---|---:|---:|---|---|
| AgentProcessBench | 1,000 trajectories, 8,509 operations | 614 / 386 | retained per-operation harmful-judge fraction | retained semantic and raw-action group means |
| HINTBench | 536 trajectories, 12,877 operations | 400 / 136 | retained binary localizer hit | corrected retained semantic and raw-action Wilson scores |
| TraceElephant | 220 trajectories, 5,960 operations | 220 / 0 | retained independent-step localizer score | retained semantic and raw-action profile scores |

Authoritative roots:

- `docs/visexp/out/agentprocessbench-rq2/full/`
- `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/`
- `.agentsight/experiments/traceelephant-rq2-v1/`
- corrected Step 0036 decomposition:
  `.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full/`

No model, prompt, prediction, tag, operation stack, field order, group
membership, localizer, benchmark record, or target annotation is regenerated.
The HINT field order remains
`action,environment,phase,status`, as selected on its retained validation
population and independently rechecked after numerical-zero correction.

## Proposed Ranking Rule

For operation `i`, let:

- `a_i` be its fixed operation-local diagnostic score;
- `s_i` be the fixed current AgentProf semantic-group score inherited by that
  operation; and
- `r_i` be the fixed matched raw-action-group score inherited by that
  operation.

The candidate ranks operations by the descending lexicographic key

```text
(a_i, s_i)
```

The local score is therefore always decisive when two operations have
different local evidence. Semantic recurrence is consulted only when their
local scores are exactly equal. Equal pairs remain a tied tier.

For standard numeric AP implementations, sort all distinct key pairs in
ascending lexicographic order and replace each pair with its integer ordinal.
This is an exact order-preserving representation, not an epsilon-weighted sum.

### Fixed properties checked before labels

1. **Strict-local-order preservation:** if `a_i > a_j`, the candidate must rank
   `i` above `j`, independent of `s_i` and `s_j`.
2. **No arbitrary weight or threshold:** the rule has no coefficient, margin,
   learned calibration, cutoff, or benchmark-specific branch.
3. **Tie identity:** operations with identical `(a_i, s_i)` remain tied; source
   row order cannot decide the primary result.
4. **Support preservation:** the candidate's positive-support predicate is the
   existing local predicate, not the semantic secondary key. It must therefore
   match atomic support exactly on every clean operation and trajectory.
5. **Target blindness:** `a_i`, `s_i`, and group membership are all constructed
   without human/benchmark correctness targets.
6. **Profile preservation:** the existing operation stacks and additive profile
   weights are unchanged; this experiment changes only how a diagnostic query
   orders existing operations.

The semantic secondary score is same-signal peer aggregation under the existing
semantic grouping, not an independent evidence source.

The rule is intentionally smaller than an additive blend, Bayesian prior,
learned ranker, thresholded propagation rule, or feature bank. Those would add
degrees of freedom before this parameter-free causal discriminator is tested.

## Comparisons

### Proposed method

- **Local score with semantic tie refinement:** `(a_i, s_i)`.

### Main baselines

1. **Local score with raw-action tie refinement:** `(a_i, r_i)`. This is the
   strongest matched organization baseline because it gives raw action the
   identical local-first composition and information budget.
2. **Atomic/local score only:** `(a_i)`. This is the strongest no-grouping
   baseline and tests whether recurrence adds anything beyond the fixed local
   signal.
3. **Current AgentProf semantic score only:** `(s_i)`. This is the incumbent
   mechanism and tests whether local-order preservation is an actual
   improvement rather than merely another valid view.

The already reported raw-action-only and session results remain Step 0036
context; they are not additional main baselines in this experiment.

## Metrics

The experiment adds no new metric.

### Primary

- Non-interpolated AP for every target-bearing trajectory using
  `sklearn.metrics.average_precision_score`, followed by arithmetic MAP per
  complete workload. The three fixed primary contrasts in each workload are
  candidate minus matched local-plus-raw, candidate minus atomic/local-only,
  and candidate minus incumbent semantic-only.

### Secondary

- Exact-`K` analytic tie-averaged expected Recall@20%-of-operations using the
  unchanged Step 0036 definition, cutoff-tier best/worst bounds, and equal
  per-trajectory operation budgets.
- The existing HINT mapped-versus-official-target sensitivity that treats its
  three projection-absent targets as unrecovered.
- Exact atomic-support identity on clean trajectories and operations. This is
  a required algorithm property, not a new benchmark metric or claimed
  improvement.

Average precision and recall are standard information-retrieval metrics.
McSherry and Najork's ECIR 2008 analysis establishes why equal scores define a
partial order and require explicit tie treatment; this experiment replaces a
tie only when the fixed same-signal semantic aggregation supplies a secondary
order, and otherwise retains the tie:
`https://marc.najork.org/papers/ecir2008.pdf`.

No pooled AP, Work@50/80, new cutoff, NDCG, custom composite, clean-support
threshold sweep, or cross-benchmark aggregate is admitted.

## Statistical Comparison

For each workload, compute paired per-trajectory differences between the
candidate and each of the three main baselines for MAP and expected
Recall@20%. Reuse the Step 0036 cluster bootstrap exactly:

- AgentProcessBench: the 178 task clusters represented among target-bearing
  queries, sampled within the four benchmark families;
- HINTBench: all 400 target-bearing trajectory clusters within 44 released
  environment strata;
- TraceElephant: all 220 target-bearing trajectory clusters within five cells;
  and
- 10,000 draws with base seed `20260717` and nearest-rank 95% intervals.

The deterministic seed for an array is
`20260717 + 100 * benchmark_index + 10 * metric_index + baseline_index`, where
benchmark order is AgentProcessBench, HINTBench, TraceElephant; metric order is
MAP then Recall@20%; and baseline order is local-plus-raw, atomic, incumbent
semantic-only. Clean trajectories are not AP queries and do not enter these
bootstrap universes; they participate only in the support-property check.

Each workload is interpreted separately. Three workloads are not three iid
samples for a cross-benchmark significance test.

## Expected And Alternative Outcomes

### Exact Result Classification

For each workload, classify the **primary MAP hypothesis** using all three
fixed candidate-minus-baseline intervals:

- **supported:** all three point effects are positive and all three 95%
  interval lower bounds are greater than zero;
- **contradicted:** at least one 95% interval upper bound is less than zero;
- **inconclusive:** every other case, including equality, an interval spanning
  zero, or a mixture without a supported loss.

The complete tested hypothesis is supported only if all three workloads are
supported, contradicted if any workload is contradicted, and inconclusive
otherwise. This is an intersection rule, not a cross-benchmark p-value; the
workloads are never treated as iid samples.

Expected Recall@20% is secondary. Its workload/baseline intervals are reported
with the same signs, but cannot promote the primary verdict. A secondary
interval wholly below zero forbids a fixed-budget dominance claim for that
comparison even when MAP is positive. HINT target sensitivity is a scope check,
and atomic-support identity is a correctness veto; neither is an alternate
success path. Any support-identity or strict-local-order violation makes the
run invalid rather than contradictory.

### Expected result

The candidate should have higher MAP than local-only, matched local-plus-raw,
and incumbent semantic-only ranking on each complete workload, with the same
direction for expected Recall@20%. AgentProcessBench should recover the strong
local ordering that semantic-only aggregation diluted; HINTBench and
TraceElephant should use semantic recurrence to resolve their large binary or
sparse local-score ties. Clean support must remain exactly atomic by
construction.

The classification above governs the outcome. A supported loss to incumbent
semantic-only participates exactly like a loss to the other two baselines and
shows that semantic propagation—not tie refinement—created the incumbent's
benefit. Do not tune a weight, introduce a third score key, change a threshold,
remove a workload, or modify the tested hypothesis after seeing the result.

### Paper decisions

- **Supported on all three workloads:** adopt local-first semantic refinement
  as the RQ2 diagnostic ordering rule for the evaluated workloads, retain the
  same operation-stack construction and paper story, and replace the current
  group-only ranking table with the reviewed adaptive-development result. Do
  not describe it as untouched generalization.
- **Contradictory or inconclusive:** retain the Step 0036 evidence boundary, do not
  modify the paper's thesis/RQs, and close this parameter-free candidate. The
  orchestrator then decides whether another paper-level uncertainty outranks
  further scoring work.

## Leakage And Fairness

- All four rankings use the same operations and the same retained local and
  group scores.
- A pure rank-key function receives only canonicalized `a_i`, `s_i`, and `r_i`
  columns. Rank keys and integer ordinal tiers are materialized without reading
  the attached correctness labels. The existing loaders may attach labels to
  the operation object, but the rank-key function must not accept them.
- The candidate itself was selected after inspecting these test-population
  results. This adaptivity is disclosed and limits interpretation; there is
  exactly one resulting composition and no further candidate selection.
- No benchmark-specific weight or exception is permitted.
- Every target-bearing and clean trajectory is retained; HINT's three absent
  target steps remain common misses in the sensitivity.
- Equal key pairs remain complete tiers in AP and Recall@20%.
- The matched raw-action baseline receives the same local-first rule; a failed
  or constant baseline is invalid rather than a candidate win.
- The current semantic-only and atomic baselines must reproduce corrected Step
  0036 exactly before any candidate comparison is valid.

## Execution

### Real preflight

Run the complete input, key-construction, ordinal encoding, AP, Recall@20%, and
support-identity path on one real target-bearing trajectory from each workload
and one real clean trajectory from AgentProcessBench and HINTBench. Preflight
must show:

- all candidate and baseline keys cover every selected operation;
- strict-local-order and equal-key-tier checks pass;
- atomic and incumbent metrics match the corresponding Step 0036 rows for the
  selected trajectories; and
- candidate clean support is exactly atomic support.

Preflight is not a paper result.

Planned command:

```bash
python script/rq2_local_first_semantic_ranking.py preflight \
  --agentprocess-root docs/visexp/out/agentprocessbench-rq2/full \
  --hint-root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
  --trace-root .agentsight/experiments/traceelephant-rq2-v1 \
  --step0036-root .agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full \
  --bootstraps 10000 --seed 20260717 \
  --out .agentsight/experiments/rq2-local-first-semantic-ranking-v1/preflight
```

### Full run

The full run must consume all 1,756 trajectories and 27,346 operations in one
deterministic invocation, score all 1,234 target-bearing trajectories, retain
all 522 clean trajectories for the support-identity check, and emit all planned
10,000-draw paired comparisons.

Planned command:

```bash
python script/rq2_local_first_semantic_ranking.py full \
  --agentprocess-root docs/visexp/out/agentprocessbench-rq2/full \
  --hint-root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
  --trace-root .agentsight/experiments/traceelephant-rq2-v1 \
  --step0036-root .agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full \
  --bootstraps 10000 --seed 20260717 \
  --out .agentsight/experiments/rq2-local-first-semantic-ranking-v1/full
```

Planned raw-result roots:

```text
.agentsight/experiments/rq2-local-first-semantic-ranking-v1/full/
.agentsight/experiments/rq2-local-first-semantic-ranking-v1/preflight/
```

Planned implementation:

```text
script/rq2_local_first_semantic_ranking.py
```

The implementation should import the corrected Step 0036 loaders, canonical
score handling, AP, Recall@20%, and bootstrap functions rather than duplicate
or modify the underlying benchmark adapters.

Before constructing keys, canonicalize every `a_i`, `s_i`, and `r_i` with the
Step 0036 numerical-zero policy. Assign ascending integer ordinals to sorted
distinct canonicalized tuples, so larger ordinals mean higher lexicographic
rank. Persist one `rank-keys.jsonl` row per operation with workload, query,
operation index, canonicalized component scores, all three relevant tuples,
and their ordinals, but no correctness target. Persist the pair-to-ordinal
mapping or equivalent distinct-key table so a reviewer can reconstruct every
tier.

Support never uses a positive ordinal. It uses the fixed local score directly:

- AgentProcessBench: `a_i > 0.5 * risk_scale`;
- HINTBench: canonicalized `a_i > 0`;
- TraceElephant: N/A because no clean trajectory exists.

Report local-score tier count, tiers actually split by semantic recurrence,
and affected operation count as mechanism-engagement checks, not success
metrics.

## Completion Rule

The experiment is complete only when:

1. all three complete populations and all four rankings are present;
2. incumbent semantic-only and atomic results reproduce corrected Step 0036;
3. every strict-local-order, tie, support-identity, score-coverage, and
   target-blind construction check passes;
4. all per-query AP and Recall@20% rows plus 18 paired bootstrap arrays
   (three workloads × two metrics × three baselines) contain 10,000 draws;
5. HINT target-mapping sensitivity is present; and
6. a fresh independent result reviewer reconstructs the keys, metrics,
   bootstrap effects, baseline engagement, leakage boundary, and exact claim
   scope from raw artifacts.

No result enters `docs/evaluation.md` or `docs/paper/` before that independent
result review.
