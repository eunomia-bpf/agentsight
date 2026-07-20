# Experiment 001 Plan — Decoupled Responsibility Continuation

- proposed: 2026-07-20T06:41:36-07:00
- outer gate: EXPERIMENT
- paper RQ: **RQ3 — How accurate are the tags?**
- target paper story: unchanged
- predecessor: Step0051 valid complete contradiction with zero review must-fix

## One Question And One Tested Hypothesis

This experiment asks one mechanism question inside fixed RQ3:

> Does separating temporal-continuation judgment from responsibility-label
> selection recover human workflow-stage spans better than the completed
> recurrence constructors?

The tested hypothesis is:

> On the complete 405-trajectory CodeTraceBench target population, using the
> same retained task-responsibility plans, Qwen2.5-3B model, and causal
> operation evidence, an active-only binary continuation decision followed by
> exact semantic-label selection only after a predicted change achieves higher
> micro unlabeled exact-span F1 than both current recurrence and
> multi-resolution recurrence.

This is post-hoc mechanism development on reused trajectories. It cannot be
presented as untouched confirmation, and no outcome can change the exact
thesis, four fixed RQs, contribution scope, or positive paper story.

## Fixed Semantic Boundary

The paper-level target remains:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, colors, side details, or bottom-level evidence. CodeTraceBench exposes
only one flat human workflow-stage level for this score. This experiment cannot
validate nested subtasks, strategy, semantic action, object, result,
generated-label accuracy, variable-depth fidelity, or the complete semantic
flamegraph.

## Why This Is The Smallest New Mechanism

Step0051 removed numeric indices but combined continuation and exact-label
selection in one grammar. It made 20,465 switches, only 401 stays, and 16,528
exact `A -> B -> A` alternations. Independent reconstruction confirmed no
scorer, coverage, context, grammar, hash, or leakage defect. Its exact-span F1
was `0.008201`, with candidate-minus-current and candidate-minus-multires 95%
intervals wholly below zero.

The new candidate changes only that same-operation coupling. The boundary decision sees the
active responsibility text without an injected alternative-label inventory and returns only
`continue` or `change`. A second call selects an exact responsibility string
only when the first call predicts `change`. This does not add a feature,
threshold, depth cap, post-hoc contraction, system-field frame, benchmark, or
metric.

This is a two-stage factorization at the current operation, not complete causal
independence. A selected label becomes the active responsibility for later
operations, so label selection still affects future continuation decisions
through state. Comparisons diagnose the complete factorized interface change;
they cannot identify boundary-policy independence from label selection.

## Reused Complete Inputs

Reuse without regeneration:

- all 405 normalized Step0050 task-responsibility plans;
- all 20,866 retained source-visible operation records across 251 tasks and
  four frameworks;
- exact shared-evidence bytes and SHA-256 checks from Step0050/Step0051;
- Step0051 joint-interface predictions as a paired mechanism diagnostic;
- Step0050 numeric predictions as descriptive history;
- completed current and multi-resolution recurrence assignments;
- the same 2,948 CodeTraceBench human stage intervals for scoring only.

The eight source plans with exact duplicate strings retain the prior stable-
first-occurrence normalization. Plans are not regenerated, reordered, edited,
expanded, or contracted. One-item plans remain one-item plans.

## Decoupled Candidate

Use the same Qwen2.5-3B-Instruct Q4_K_M GGUF, SHA-256, temperature zero, seed
20260720, 8,192-token limit, tokenizer projection, public task text, operation
ordinal, action kind, raw-action key, source action, and preceding observation
as Step0050 and Step0051.

### First operation

There is no active responsibility. One exact-label call sees the public task,
the same source-only causal evidence for the current operation, and the
unordered retained responsibility strings. It selects one exact string:

```json
{"responsibility":"inspect repository"}
```

### Later operations: phase 1, continuation only

The model sees the source-only causal operation evidence and the active
responsibility text. It receives no injected alternative-responsibility
inventory, count, order, numeric plan index, or temporal-instance ID. It
returns exactly one of:

```json
{"decision":"continue"}
```

```json
{"decision":"change"}
```

The unchanged public task or causal evidence may naturally contain text
identical to a retained responsibility; such incidental exact-string mentions
are counted and reported rather than removed from the reused evidence.

`continue` extends the current temporal stage instance. The prompt states that
tool, command, file, observation, or local action changes do not themselves
imply a responsibility change; `change` is appropriate only when the concrete
work responsibility changes.

### Later operations: phase 2, label only after change

Only after a `change` decision does a second call see the public task, the same
source-only causal evidence for the current operation, the active
responsibility, and the unordered retained responsibility strings. It must copy
one exact string other than the active one:

```json
{"responsibility":"verify the fix"}
```

The selected string starts a new temporal stage instance. Returning later to a
previously used responsibility type is legal and starts a new instance. For a
one-item plan, no distinct label exists, so every later operation is
deterministically `continue` without a model call; this follows from the fixed
state space rather than a learned boundary.

Per-call GBNF permits only the registered response. There is no semantic retry,
rewrite, fuzzy match, fallback, score-driven edit, switch-to-active label, or
post-hoc merge. Invalid JSON, a nonexact label, a missing operation, context
overflow, or evidence mismatch makes the run incomplete.

## Evidence Isolation

Candidate inference does not open or serialize official stages, stage counts,
solved state, incorrect labels, scorer output, resource weights, future
operations, or the current action result. It does not open Step0051 score
outputs during inference. The local model receives no gold.

The root researcher has seen prior scores, so the complete result remains
development evidence. Predictions are fixed across all 405 trajectories before
the separate scorer opens the official manifest.

## Comparators

Adoption comparators:

1. current coarse recurrence, exact-span F1 `0.068055`;
2. multi-resolution recurrence, exact-span F1 `0.056435` and ordinary
   B-cubed F1 `0.662740`.

Paired mechanism diagnostic:

1. Step0051 joint index-free interface, exact-span F1 `0.008201`, using the
   same plans, model, semantic strings, and causal evidence but coupling
   continuation and label selection in one response grammar.

The joint-interface comparison diagnoses the complete two-stage interface
change. It cannot prove boundary-policy independence, grammar branch order,
label visibility, or any other single component caused an effect. Numeric-index,
plan-free Qwen, phase,
raw-action, action-kind, and one-span outputs remain descriptive controls; none
is rerun.

## Standard Outcomes

- **Primary:** ordinary pooled micro unlabeled exact-span precision, recall,
  and F1 over contiguous temporal stage instances, following the constituent-
  boundary precision/recall precedent of
  [Black et al. 1991](https://aclanthology.org/H91-1060/).
- **Secondary:** ordinary unweighted per-operation B-cubed precision, recall,
  and F1, following
  [Bagga and Baldwin 1998](https://aclanthology.org/C98-1012/) and
  [Amigó et al. 2009](https://doi.org/10.1007/s10791-008-9066-8); and exact
  adjacent-boundary precision, recall, and F1 using the segmentation confusion-
  matrix precedent of
  [Fournier 2013](https://aclanthology.org/P13-1167/).
- **Diagnostics:** predicted instance count, continue/change rate,
  label-selection call count, responsibility utilization, non-adjacent label
  returns, exact `A -> B -> A` alternations, one-item forced continuations,
  per-framework results, invalid/incomplete count, prompt/completion tokens,
  request maximum, and wall time.

No token-weighted metric, reader-budget protocol, custom accuracy score,
generated-name accuracy, or task-success outcome is admitted.

## Statistics

For candidate minus each adoption comparator and separately candidate minus the
Step0051 joint-interface predecessor:

- bootstrap unit: CodeTraceBench task, retaining every trajectory in a sampled
  task cluster;
- 10,000 paired resamples;
- seed 20260720;
- recompute pooled exact-span F1 in every resample;
- report mean delta, 2.5th/97.5th percentiles, and positive fraction.

## Registered Decision

The hypothesis is **supported and the candidate is adopted** only if:

1. candidate exact-span F1 is strictly higher than both current and multi-
   resolution recurrence;
2. the paired task-cluster 95% interval for candidate minus each recurrence
   comparator is wholly above zero;
3. all 405 trajectories and 20,866 operations are assigned exactly once and
   all evidence, context, output, and temporal-instance checks pass.

It is **contradicted and not adopted** if either candidate-minus-recurrence 95%
interval is wholly at or below zero. It is **inconclusive and not adopted** in
all remaining valid cases, including a higher point estimate whose interval
crosses zero. It is **incomplete** if any fixed execution check fails.

Improvement over Step0051 cannot rescue a failed adoption rule. Secondary
metrics cannot override the primary result. No outcome authorizes changing the
thesis, RQs, contribution scope, story, or positive paper. A negative mechanism
result remains experiment history; a positive result remains post-hoc flat-
stage development evidence and does not establish the full hierarchy.

## Real Preflight And Full Execution

Real preflight will select one complete trajectory per framework using the same
fixed longest-context rule as Step0051. It must execute the actual two-phase
protocol, exact GBNF, evidence-hash checks, and output materialization without
opening gold. Policy degeneration is a scientific observation, not by itself
an implementation failure; if execution checks pass, the approved mechanism
runs unchanged on all 405 trajectories rather than stopping at a smoke subset.

The existing llama.cpp server configuration remains:

- llama.cpp build 9870, revision `2d973636e`;
- Qwen2.5-3B-Instruct Q4_K_M SHA-256
  `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`;
- NVIDIA GeForce RTX 5090;
- four slots/workers, temperature zero, seed 20260720.

Expected full inference time is approximately 30--50 minutes depending on the
number of label-selection calls. Fixed artifact roots and commands are:

```bash
python3 script/rq3_decoupled_responsibility_continuation_eval.py infer preflight \
  --source-sessions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/sessions \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/preflight

python3 script/rq3_decoupled_responsibility_continuation_eval.py infer full \
  --source-sessions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/sessions \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/full

python3 script/rq3_decoupled_responsibility_continuation_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/full \
  --joint-predictions .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full/predictions.jsonl \
  --numeric-predictions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/predictions.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/score
```

Each inference root contains per-session atomic caches, `predictions.jsonl`,
and `inference-summary.json`. The score root contains operation rows, boundary
rows, `summary.json`, `report.md`, and one 10,000-row bootstrap file per fixed
comparison. Only the score command accepts or opens the verified manifest.

## Result Ownership

This EXPERIMENT gate may add one evaluator and detailed Markdown provenance.
It may not edit `docs/paper/`, the canonical `docs/agentpprof-paper` submodule,
shared skills, thesis, RQs, contribution list, or story. Any paper incorporation
belongs to a later WRITE gate and only within the registered evidence boundary.

The planned paper role is supporting post-hoc mechanism-development evidence
for the flat stage-boundary component of RQ3 only. One-item deterministic
continuation is a structural restriction of the retained candidate state space,
not learned continuation success; report its five trajectories and operation
coverage separately in diagnostics.
