# Experiment Plan — Recurrence-Based Operation-Stack Induction On Existing Trajectories

**Proposed:** 2026-07-15T00:23:59-07:00
**State:** REVISED AFTER INDEPENDENT REVIEW
**Paper RQ:** **RQ3 — How Accurate Are the Tags?**
**Scientific role:** post-hoc mechanism development on an already observed
population; not fresh independent confirmation

## One Tested Hypothesis

> On the complete existing OSWorld-Human population, a fixed target-blind
> cross-session recurrence inducer recovers the independently annotated human
> operation groups more accurately than the current cap-free
> information-gain inducer and the strongest simple control on both adjacent
> boundary F1 and operation-weighted B-cubed F1.

The experiment may accept or reject this algorithm replacement candidate. It may not
change RQ3, weaken its fixed positive paper-level hypothesis, replace the exact
paper thesis, alter the two core abstractions, or change the story inherited
from the read-only submodule.

Because the complete OSWorld-Human labels influenced both the failure diagnosis
and the exploratory candidate calculation, this experiment cannot complete a
missing RQ3 component or provide fresh confirmatory paper evidence. A supported
result authorizes a minimal implementation candidate and later independent
confirmation; it does not authorize quantitative promotion as a new RQ3 result
from this population.

## Why This Experiment Is Admitted

The user explicitly requires improvement on already executed trajectories
rather than a new benchmark. Steps 0017 and 0018 already show that the current
single-objective information-gain implementation is much better than the old
heuristic but remains below simple controls. Its failure is not merely an
arbitrary depth limit: cap-free recursion reaches boundary F1 0.4720 and
B-cubed F1 0.6720, while human groups often join heterogeneous action sequences
that an entropy-homogeneity objective tends to split.

The candidate changes the core objective rather than adding a score term,
threshold, field, or depth to the failed recursion. It asks whether a recurring
adjacent action transition supplies the stable cross-run identity that
profiling needs. This is directly relevant to operation-stack induction and the
original profiling story. It reuses the exact complete operation population,
official annotations, existing folds, metrics, current Rust baseline, and
simple controls.

The root already inspected an exploratory full-population calculation while
diagnosing the failure. Therefore the registered run is a reproducibility and
implementation decision, not a statistically untouched confirmation. Its
paper role remains bounded regardless of the result.

## Fixed Inputs

- Source: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl`.
- Eligible population: every sequence with at least two operations,
  `group_alignment=exact`, and an official `human_group` annotation.
- Expected coverage: 287 sessions, 3,978 operations, 3,691 adjacent pairs,
  2,042 human groups, and unit weight for every operation.
- Visible induction field: the existing categorical `action` field only.
- Scorer-only fields: `human_group` and every group, label, learned, oracle,
  target, or reference derivative already excluded by the existing RQ3 loader.
- Ordering: integer `turn` within each whole session.
- Folds: the existing five session-blocked folds, exactly
  `sha256("r297-oof-v1:" + session_id) mod 5`.

No operation, label, fold, feature, or benchmark is added or removed after
plan approval.

## Fixed Candidate Algorithm

For each held-out fold, learn only from the visible action sequences in the
other four folds.

Let `c_L(a)` be the number of training transitions whose left action is `a`,
`c_R(b)` the number whose right action is `b`, `c(a,b)` the number whose ordered
pair is `(a,b)`, and `B` the total adjacent-pair count in the four training
folds. These are marginals and a joint distribution over the same transition
sample space. For every observed pair, calculate normalized pointwise mutual
information:

```text
p_L(a) = c_L(a) / B
p_R(b) = c_R(b) / B
p(a,b) = c(a,b) / B
PMI(a,b)  = ln(p(a,b) / (p_L(a) p_R(b)))
NPMI(a,b) = PMI(a,b) / -ln(p(a,b))
```

Use deterministic one-dimensional two-means to divide the *occurrence-weighted
training transition scores* into low- and high-association clusters:

1. initialize the two centers to the minimum and maximum observed NPMI;
2. assign each score to the nearest center, with exact ties assigned to the
   lower center;
3. replace each center with its cluster mean;
4. require convergence within 100 iterations;
5. define the cutoff as the midpoint between the ordered final centers.

For each adjacent pair in a held-out session:

- start a new operation group when its pair was unseen in training or its NPMI
  is strictly below the fold cutoff;
- otherwise continue the current operation group.

The first action always starts a group. The frame name for a predicted group is
`action=` followed by the run-length-compressed action sequence joined with
`-then-`; for example, `click,click,type,press` becomes
`action=click-then-type-then-press`. Frame sanitization uses the existing
AgentProf safe-frame path. Identical visible motifs therefore receive identical
cross-session names. Session-local numeric group IDs may appear only in scorer
bookkeeping, never as profile identity.

Degenerate behavior is fixed before execution. A fold with zero training
transitions is invalid. If `p(a,b)=1`, its NPMI is the standard limiting value
`1`; if any other probability, logarithm, or quotient is non-finite, the fold
is invalid. The two-means input must contain at least two distinct finite
scores; either empty cluster or failure to converge within 100 iterations is
invalid. An unseen held-out pair always starts a new group as stated above.

There is no label-selected threshold, smoothing constant, depth, recursion,
query term, minimum group size, or hidden fallback. An empty cluster, non-finite
score, incomplete fold, or missing action makes the run invalid rather than
silently changing the algorithm.

## Comparisons

All comparisons use the identical 3,978 operations and 3,691 scorer pairs.

1. **Current cap-free information-gain inducer:** reuse the independently
   verified Step 0018 artifacts at
   `.agentsight/experiments/rq3-rust-inducer-depth-v1/full/`, committed at
   `7218564980d12fe3f493eed245fac03f0980cf2d`, and reconstruct their
   `depth_unbounded` rows against the same source. The artifact was produced by
   `agentpprof 0.2.37`, policy
   `recursive-information-gain-operation-stack-induction`, with maximum depth
   255 and no depth-cap stop. This is the main implementation baseline.
2. **Always boundary, action change, and phase change:** reuse and independently
   recompute the existing simple controls. The strongest per metric is the
   simple-control threshold the candidate must exceed.
3. **Supervised out-of-fold Bernoulli boundary tagger:** reuse Step 0006 as an
   extra-information comparator, not a baseline the unsupervised candidate
   must beat.

No other algorithm, field tuple, cutoff method, fold seed, or ablation is
admitted in this experiment.

The information budgets intentionally differ. The candidate estimates
label-free action-transition recurrence from the other four session folds,
then applies it to held-out sessions. The current Rust inducer operates on each
session separately and receives no cross-session corpus statistics. This is the
scientific mechanism contrast—cross-run recurring identity versus per-run
entropy segmentation—not a hidden claim of an implementation-only,
same-information comparison. Both remain target-blind at prediction time.

## Metrics And Registered Interpretation

Primary metrics are unchanged from the existing RQ3 experiment:

- micro adjacent-boundary precision, recall, and F1 over all held-out pairs;
- operation-weighted B-cubed precision, recall, and F1 over session-local
  predicted and official groups.

Required diagnostics are predicted group count, per-fold cutoff and centers,
unseen held-out pair count, unique recurring motif count, maximum/median group
length, and exact mass conservation. These diagnose the mechanism but do not
create additional success conditions. Boundary F1 and B-cubed test only
session-local segmentation and partition fidelity. They do not score whether a
motif's literal frame name is correct, whether it is a valid phase/action
identity across task families, or whether the mechanism generalizes beyond the
already observed OSWorld-Human corpus.

- **Supported:** the candidate exceeds the cap-free information-gain baseline
  and the strongest simple control on both boundary F1 and B-cubed F1.
- **Contradicted:** it improves neither primary metric over the cap-free
  baseline, or clears neither metric's strongest simple control.
- **Mixed:** every other complete valid outcome.
- **Invalid/inconclusive:** population, fold isolation, scorer separation,
  finite-score, complete-prediction, frame, integration, or mass checks fail.

The result is post-hoc mechanism-development evidence under every branch.
`Supported` means the candidate warrants a minimal Rust port and later
independent confirmation if the paper needs a general automatic-inducer claim.
It does not make this population new, validate motif-name identity, complete a
missing RQ3 component, or authorize a whole-RQ claim.

## Minimal Implementation And Reuse

Add one focused evaluation adapter that reuses the existing OSWorld loader,
session grouping, fold function, binary metrics, B-cubed scorer, safe-frame
normalization, Step 0018 baseline rows, Step 0006 comparator, and current
AgentProf operation-file interface. The adapter implements only the fixed NPMI,
two-means, held-out prediction, motif construction, reports, and invariant
checks above.

Do not modify the Rust inducer before the candidate passes the complete run and
independent result review. A supported result then receives a separate minimal
Rust port plus exact Python-versus-Rust output-equivalence tests; no second
scientific experiment is required for that mechanical port.

## REAL PREFLIGHT

Run the real algorithm on fold 0 only, covering every fold-0 held-out session,
not a synthetic fixture. Preflight succeeds only when training and held-out
sessions are disjoint; all expected fold-0 operations and pairs receive one
prediction; every score and center is finite; hidden fields are absent from
training inputs; motif frames are valid; and one current AgentProf profile over
the held-out candidate fields conserves all held-out mass. Preflight is
dependency and implementation evidence, not a paper result.

Planned command:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-recurrence-inducer-v1/preflight
```

## FULL RUN

Run all five folds, concatenate their held-out predictions exactly once,
recompute every candidate and comparison metric, construct recurring motif
frames, and invoke current release AgentProf once on the complete candidate
operation file. The run is complete only at the exact 287/3,978/3,691/2,042
coverage and exact 3,978 input/profile mass.

Planned command:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-recurrence-inducer-v1/full
```

Raw reports remain under the declared `.agentsight/experiments/` directory.
The step report and independent result review record exact commands and result
locations. No smoke-only result substitutes for the complete run.
