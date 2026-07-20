# Experiment 001 Plan — Index-Free Responsibility Alignment

- proposed: 2026-07-20T05:28:39-07:00
- outer gate: EXPERIMENT
- paper RQ: **RQ3 — How accurate are the tags?**
- target paper story: unchanged
- predecessor: Step0050 valid complete numeric-index mechanism contradiction

## One Question And One Tested Hypothesis

This experiment asks one mechanism question inside fixed RQ3:

> Can an index-free semantic transition interface, motivated by the observed
> ordinal bias, recover human workflow-stage spans more accurately than both
> existing recurrence constructors?

The tested hypothesis is:

> On the complete 405-trajectory CodeTraceBench target population, using the
> same retained task-responsibility plans, model, and causal operation evidence,
> Qwen2.5-3B choosing an explicit `stay` or an exact responsibility string
> achieves higher micro unlabeled exact-span F1 than both current recurrence
> and multi-resolution recurrence.

This is a post-hoc mechanism-development experiment on reused trajectories. It
does not claim untouched confirmation. No outcome may change the exact thesis,
four RQs, contribution scope, or positive paper story.

## Fixed Semantic Boundary

The paper-level target remains:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, colors, side details, or bottom-level evidence. This experiment scores
only the one flat human workflow-stage level available in CodeTraceBench. It
cannot validate nested subtasks, generated label meaning, strategy, semantic
action, object, result, or the full task-semantic hierarchy.

## Why This Is The Smallest Causal Test

Step0050 completed all 405 trajectories, but 397 began with numeric index 1,
85.73% of candidate switches incremented the prior index by exactly one, and
index 0 covered only 0.8626% of operations. The representative trajectory
walked `1,2,3,4,5` and then assigned 271/275 operations to its last plan item.
Those source-side patterns directly implicate the ordinal interface.

The next experiment therefore does not change planner, plan labels, benchmark,
operation projection, model, metric, cutoff, or paper claim. It replaces the
complete numeric per-operation assignment interface with a semantic
`stay`/`switch-to-exact-text` interface. Because this changes both
representation and transition form, a win supports that interface bundle; it
cannot isolate numeric tokens as the sole cause.

## Reused Complete Inputs

Reuse without regeneration:

- all 405 normalized task-responsibility plans from
  `.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/sessions/`;
- all 20,866 complete source-visible operation records across 251 tasks and
  four frameworks;
- Step0050 numeric-index predictions;
- Step0050 matched plan-free Qwen predictions;
- completed multi-resolution and current recurrence assignments;
- the same 2,948 CodeTraceBench human stage intervals for scoring only.

The eight Step0050 sessions whose raw plan contained exact duplicates retain
the already registered stable-first-occurrence normalization. Plans are not
rewritten, reordered, expanded, contracted, or regenerated. A normalized plan
with one item remains one item; this experiment does not hide planner collapse.

## Index-Free Causal Candidate

Use the same Qwen2.5-3B-Instruct Q4_K_M GGUF, model SHA-256, temperature zero,
seed 20260720, 8,192-token input limit, tokenizer projection, task text,
operation ordinal, action kind, raw-action key, source action, and preceding
observation as Step0050.

For the first operation, there is no active responsibility. The model must
switch to one exact retained responsibility string:

```json
{"decision":"switch","responsibility":"configure ssh authentication"}
```

For later operations, it receives the active responsibility text and the same
ordered list of retained responsibility texts, without any numeric index,
position label, or instance number. It returns exactly one of:

```json
{"decision":"stay","responsibility":null}
```

```json
{"decision":"switch","responsibility":"deploy main branch"}
```

`stay` extends the current temporal instance. `switch` creates a new temporal
instance and must select an exact retained responsibility other than the
current one. Returning later to a previously used text is legal and creates a
new instance. A one-item plan permits only `stay` after its first operation.

The per-call GBNF enumerates exact allowed strings and does not expose hidden
indices. Invalid JSON, a nonexact string, illegal first `stay`, switching to
the current text, missing operation, or context overflow makes the run
incomplete. There is no semantic retry, rewrite, fuzzy match, fallback, or
score-driven edit.

This keeps two identities distinct:

- `responsibility_type`: reusable planner text;
- `stage_instance`: one contiguous run, extended only by `stay`.

## Evidence Isolation

Candidate inference does not open or serialize official stages, stage counts,
incorrect labels, solved state, scorer output, or resource weights. Each
decision sees no future operation and does not see the current action's result.
The current operation sees only its preceding observation, matching Step0050.

Although the root researcher has already seen Step0050 gold scores, the local
model receives no gold. The result is explicitly development evidence, not a
blind or held-out claim.

## Comparators

Main mechanism comparators:

1. current coarse recurrence: strongest existing result on this experiment's
   registered primary exact-span F1 (`0.068055`);
2. completed multi-resolution recurrence: current paper mechanism and strongest
   existing recurrence result on ordinary B-cubed, but lower on exact-span F1
   (`0.056435`).

Both are adoption baselines. Their completed assignments are reused without a
rerun.

Paired representation/control comparison:

1. Step0050 task-rooted numeric-index aligner: same retained plans, model, and
   source evidence, but a different representation and transition form. It
   diagnoses whether the complete index-free interface helps relative to its
   rejected predecessor; it does not by itself authorize adoption or prove
   that numeric tokens alone caused the change.

Reuse matched plan-free Qwen, phase change, raw-action-key change, action-kind
change, and one-session-span only as descriptive controls. No comparator is
rerun.

## Standard Outcomes

- **Primary:** ordinary micro unlabeled exact-span precision, recall, and F1
  over contiguous stage instances, following the constituent-boundary
  precision/recall precedent of
  [Black et al. 1991](https://aclanthology.org/H91-1060/). A predicted span is
  the exact `(session,start_step,end_step)` interval of one contiguous
  `stage_instance`; a gold span is the corresponding official interval. True
  positives are exact interval matches. Counts are pooled over all 405
  trajectories before computing precision, recall, and harmonic-mean F1.
- **Secondary:** ordinary unweighted per-operation B-cubed as introduced by
  [Bagga and Baldwin 1998](https://aclanthology.org/C98-1012/) and formally
  analyzed by
  [Amigó et al. 2009](https://doi.org/10.1007/s10791-008-9066-8). For each
  operation `i`, precision is `|P(i) intersect G(i)| / |P(i)|` and recall is
  `|P(i) intersect G(i)| / |G(i)|`; average each over all 20,866 operations,
  then take their harmonic mean. Also report exact adjacent-boundary
  precision, recall, and F1 using the segmentation confusion-matrix precedent
  of [Fournier 2013](https://aclanthology.org/P13-1167/): each adjacent pair is
  positive exactly when its two operations have different instances, with no
  tolerance; pool TP, FP, and FN over all 20,461 pairs.
- **Diagnostics:** predicted instance count, stay/switch rate, responsibility
  utilization, non-adjacent responsibility returns, per-framework results,
  malformed/incomplete count, model calls, prompt/completion tokens, and wall
  time.

No token-weighted measure, reader protocol, inspection-budget cutoff, custom
accuracy score, or generated-label accuracy is admitted.

## Statistics

For candidate minus each main mechanism comparator and separately candidate
minus the numeric representation/control:

- bootstrap unit: underlying CodeTraceBench task, retaining every trajectory
  in each sampled task cluster;
- 10,000 paired resamples;
- seed 20260720;
- recompute pooled micro exact-span F1 in every resample;
- report mean delta, 2.5th/97.5th percentiles, and positive fraction.

## Registered Decision

The hypothesis is **supported and the index-free mechanism is adopted** only
if all of the following hold:

1. candidate exact-span F1 is strictly higher than current recurrence and
   multi-resolution recurrence;
2. the paired task-cluster 95% interval for candidate minus each recurrence
   comparator is wholly above zero;
3. all 405 trajectories and 20,866 operations are assigned exactly once and
   every evidence, context, grammar, and temporal-instance check passes.

It is **promising but not adopted** if the candidate is higher than both
recurrence comparators but either interval includes zero. It is
**contradicted** if a complete valid run does not beat both recurrence
comparators. It is **incomplete** if any coverage, isolation, context, output,
or assignment check fails.

A wholly positive candidate-minus-numeric interval supports only the narrower
diagnosis that the complete index-free semantic transition interface improves
over the numeric predecessor. It cannot prove numeric tokens alone caused the
effect and cannot rescue a failed adoption rule against either recurrence
comparator. Secondary metrics cannot override the primary rule.

No result authorizes changing thesis, RQs, contribution scope, or story. A
negative mechanism result remains experiment history and does not enter the
positive paper. A positive result remains post-hoc development evidence and
authorizes only a later evidence-owned WRITE describing that bounded
development result; it does not constitute held-out confirmation or authorize
a claim that the full task-semantic hierarchy has been recovered.

## Registered Runtime And Commands

Use the already retained local runtime:

- llama.cpp build 9870, revision `2d973636e`;
- Qwen2.5-3B-Instruct Q4_K_M SHA-256
  `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`;
- NVIDIA GeForce RTX 5090;
- four parallel slots/workers, temperature zero, seed 20260720;
- expected candidate-only full inference time approximately 35--45 minutes,
  derived from Step0050's 42,137-call 71.96-minute run.

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf \
  -ngl 99 -c 65536 -np 4 --host 127.0.0.1 --port 18182 \
  --seed 20260720 --temp 0 --metrics \
  --log-file .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/llama-server.log

python3 script/rq3_index_free_responsibility_alignment_eval.py infer preflight \
  --source-sessions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/sessions \
  --numeric-predictions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/predictions.jsonl \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/preflight

python3 script/rq3_index_free_responsibility_alignment_eval.py infer full \
  --source-sessions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/sessions \
  --numeric-predictions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/predictions.jsonl \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full

python3 script/rq3_index_free_responsibility_alignment_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/full \
  --numeric-predictions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/predictions.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-index-free-responsibility-alignment-v1/score
```

Inference exits successfully only after its summary records `status=complete`,
405 sessions, 20,866 unique predictions, one assignment per source operation,
and no invalid output or context overflow. Scoring exits successfully only
after 405 sessions, 20,866 operations, 20,461 pairs, 2,948 official stages,
251 task clusters, all three named recurrence/control comparisons, and 10,000
bootstrap rows per comparison are materialized under the exact paths above.

## Lean Execution

1. Complete exactly three serial independent scientific plan reviews. Repair
   only concrete must-fix issues between them; do not add gates or new claims.
2. Implement candidate-only inference by reusing Step0050 extraction,
   projection, retained plans, baselines, and corrected scorer.
3. Run one real preflight covering one complete trajectory per framework while
   keeping stages closed. If a concrete implementation defect appears, repair
   it narrowly in the same report; do not restart plan review or change the
   scientific contract.
4. Run all 20,866 candidate decisions to completion from empty index-free
   caches.
5. Score once with the fixed standard metrics and perform one independent
   complete-result reconstruction.

Raw outputs remain under
`.agentsight/experiments/rq3-index-free-responsibility-alignment-v1/`. The
tracked experiment directory retains this plan, exactly three reviews, one
preflight report, a complete-run report, and one independent result review.
