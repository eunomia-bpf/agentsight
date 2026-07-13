# Bounded Fresh Localization Source Selection

**Node:** `review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700`  
**Timestamp:** 2026-07-13T11:46:36-07:00  
**Phase / cycle / gate:** BUILD_AND_EVALUATE / cycle 0002 / REVIEW  
**Role:** timeboxed selector using `research-literature-novelty`  
**Fixed target:** RQ2, real-problem localization  
**Decision:** **SELECT HINTBench**  
**Git operations:** none  
**Files changed:** this report only

## Decision

Use the current official HINTBench 4open snapshot as the one fresh source for
the next RQ2 experiment.

Define FULL as exactly the 536 records currently enumerable in the official
`data/hintbench.json`, not the paper/README claim of 629 test records and not
the README's 709 test-plus-validation total.

The 536-record snapshot remains eligible because it is accessible, licensed,
contains raw trajectories, and supplies independent official numeric step
annotations for every risky trajectory. Those annotations identify 938
distinct trajectory-step targets: 935 match released atomic steps and three
official step IDs are absent from their released trajectories. The three remain
common terminal misses for every method and are never remapped or deleted. The
count and schema mismatch is a material REAL PREFLIGHT caveat, not permission
to invent missing records or labels.

Who&When is an eligible reserve but is not selected. Exactly one source enters
the next experiment.

## Fixed Scientific Question

This node serves only the unchanged RQ2:

> Does profiler output correspond to real problems?

It does not change the thesis, story, operations, operation stacks, or any RQ.
It does not add tag-accuracy or profiling-cost work.

## Name-Free Hypothesis

Across the complete current official test snapshot, grouping target-blind
atomic trajectory steps by stable semantic responsibility and ranking the
resulting groups requires less atomic-step inspection to recover at least 80%
of the official risky-step targets than the strongest comparator that sees
exactly the same raw steps and non-label fields.

The mechanism must win through organization, not extra fields, target identity,
additional tuning, or a stronger localizer.

## Bounded Verification

The parent constrained this repair to HINTBench and Who&When. No broader search
or paper-wide literature review was reopened.

Verification asked only:

1. Is an official artifact accessible?
2. Does it expose raw steps and independent official step gold?
3. Can one finite population run to terminal status without new labels?

The bounded queries were:

- `HINTBench arXiv official artifact 4open risk_origin_step affected_steps`
- `Who&When multi-agent failure attribution ICML 2025 official Hugging Face dataset decisive error step`

Only primary papers and official artifacts support the decision.

## Primary URLs

### HINTBench

- Paper: https://arxiv.org/abs/2604.13954
- Artifact: https://anonymous.4open.science/r/HINTBench-B841
- README: https://anonymous.4open.science/api/repo/HINTBench-B841/file/README.md
- Test data: https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json
- Validation data: https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json
- Evaluator: https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py
- License: https://anonymous.4open.science/api/repo/HINTBench-B841/file/LICENSE

### Who&When

- Paper: https://openreview.net/forum?id=GazlTYxZss
- Repository: https://github.com/ag2ai/Agents_Failure_Attribution
- Dataset: https://huggingface.co/datasets/Kevin355/Who_and_When

## HINTBench: Claimed And Actual State

The paper reports 629 trajectories: 523 risky, 106 safe, about 33 steps each.

The README reports:

- test: 629 total, 523 risky, 106 safe;
- validation: 80 total, 60 risky, 20 safe; and
- total: 709 trajectories.

The current official test JSON instead contains:

- 536 records;
- 400 risky and 136 safe;
- mean raw trajectory-array length 24.024;
- raw length range 3--42; and
- fields `env`, `id`, `is_risky`, `risk_labels`, `task_id`, `trajectory`.

Its 978 official risk-annotation records comprise:

- 518 `source: injected` records;
- 460 `source: additional` records;
- 464 numeric `risk_origin_step` targets; and
- 514 numeric `step_id` targets.

Every risk-label record has exactly one of those numeric target fields. Every
one of the 400 risky trajectories has at least one target. None of the 136 safe
trajectories has a non-empty risk-label array.

The 978 annotations refer to 938 distinct `(trajectory, step_id)` targets
because multiple risk annotations may share one step. Of those distinct
targets, 935 match an existing released `trajectory[].step_id`. Three injected
annotations point to absent step IDs in records 170, 233, and 516. Each affected
trajectory also has other valid official targets. The absent targets remain in
the primary denominator as unrecovered terminal targets for every method; no
adjacent-step or array-position fallback is permitted.

The current test schema has no `affected_steps`. Risk records may additionally
contain official type, category, description, and annotation-support fields.

The current validation JSON contains the advertised 80 records, split 60 risky
and 20 safe, with 169 `injected_risks` records. It uses
`risk_origin_step`/`affected_steps`. One validation origin did not satisfy a
naive zero-based raw-array bound, so index semantics must be checked rather
than assumed.

The released evaluator calculates step precision, recall, and F1 but reads
ground truth from `injected_risks`. It does not read the current test file's
`risk_labels`. Unchanged evaluation would therefore erase test gold.

Minimal deterministic glue may normalize official `risk_origin_step` and
`step_id` into one target field. It may not infer labels from descriptions,
drop difficult records, or claim use of the unchanged official evaluator.

The artifact is Apache-2.0 licensed.

## Who&When: Actual State

The official release contains 184 JSON trajectories:

- 126 algorithm-generated; and
- 58 hand-crafted.

Each record includes raw `history`, `question`, `question_ID`, `ground_truth`,
`mistake_agent`, `mistake_step`, `mistake_reason`, and `is_corrected`.
`mistake_step` is the official decisive-error label. The repository provides
inference/evaluation code and uses the MIT license.

Cycle 0001 audited and planned over these 184 files, but `loop-rq2-01` has no
FULL execution report. Who&When is therefore not rejected for prior outcomes.
It loses this exactly-one choice because HINTBench supplies a larger qualifying
population, multiple step targets, and safe negative controls.

## Qualification Matrix

| Hard condition | HINTBench | Who&When |
|---|---|---|
| Official artifact accessible | Pass | Pass |
| Raw steps/spans | `trajectory` arrays | `history` arrays |
| Official step gold | 978 annotations / 938 distinct targets; 935 released steps plus 3 common terminal misses | one `mistake_step` per failure |
| Handmade labels needed | No; field normalization only | No |
| Fresh outcome source | Pass | Pass; plan but no FULL outcome |
| Enumerable FULL population | 536 current test records | 184 released files |
| Complete run feasible | Pass | Pass |
| License | Apache-2.0 | MIT |
| Main caveat | count/schema/evaluator mismatch | prompt/evaluator adapters |
| Decision | **Selected** | reserve only |

## Why HINTBench Is Selected

The current HINTBench test snapshot is larger: 536 versus 184 trajectories.
Its 400 risky trajectories contain 978 official annotations over 938 distinct
step targets rather than one target per failed trajectory. Its 136 safe
trajectories expose unnecessary inspection and false prioritization without
invented labels.

Who&When is schema-cleaner, but HINTBench tests the stronger localization claim
once its bounded compatibility issue passes REAL PREFLIGHT. The nominally
missing records are not needed to define FULL because the current official
snapshot itself is finite and enumerable.

## Smallest Strong Same-Information Baseline Positions

Every method receives identical raw turns, allowed non-label fields,
target-blind scores, and tuning budget.

1. **Native sequential inspection:** source order alone is sufficient.
2. **Flat independent-step ranking:** the score creates the benefit; hierarchy
   adds nothing.
3. **Flat multidimensional aggregation:** ordinary grouping over every field
   visible to the proposed method captures all useful concentration; ordered
   stacks add nothing.

Retain a published HINTBench localizer only if it is runnable on the normalized
snapshot with identical visible input. Do not add redundant prompt variants.

## Primary Fixed-Recall Metric

Primary metric: atomic trajectory-step inspection fraction at 80% macro recall
of official risky-step targets. For each risky trajectory, the target set is
the union of official step IDs, so duplicate annotations at one step count once.
The three absent official step IDs remain in that union as terminal misses for
every method.

For each method, find the smallest approved inspection budget reaching at least
0.80 macro recall over all 400 risky test trajectories. At matched recall,
compare paired step fraction and count.

Support requires reaching the recall target and a paired uncertainty interval
for work reduction that excludes zero against the strongest same-information
non-oracle baseline.

Safe trajectories remain in FULL as negative controls but do not enter the
target-recall denominator.

## REAL PREFLIGHT

Already verified:

- artifact, data, evaluator, and license URLs respond;
- the current test population is exactly 536;
- all risky records have official numeric targets;
- safe records have none; and
- evaluator and test schema disagree.

Before FULL, REAL PREFLIGHT must:

1. normalize the two official target fields deterministically;
2. establish that released `trajectory[].step_id`, rather than array position,
   is the target identity;
3. verify 978 annotations, 938 distinct target pairs, 935 mappable pairs, and
   the three fixed absent targets in records 170, 233, and 516;
4. prove every risky record retains at least one mappable target and no safe
   record gains a target;
5. run one complete real trajectory through every method and scorer without
   using gold during ranking; and
6. record the 536/629 and schema deviations explicitly.

If deterministic normalization produces counts or absent-target identities
other than those above, mark the source ineligible and return to REVIEW. Never
delete, relabel, move an absent target to an adjacent step, or downgrade to
run-level detection.

## FULL Completion Unit

One cell is `(official test trajectory, approved method)` with a terminal
ordered inspection result and target-blind raw output.

FULL requires:

- all 536 test trajectories;
- the proposed method and every admitted baseline;
- all 978 official annotations and all 938 distinct targets represented in
  accounting, including the three common terminal misses;
- all 136 safe trajectories represented;
- every plan-declared stochastic repetition; and
- a terminal outcome for every cell.

Validation may support development and adapter checks only. It is not appended
to held-out test. The nominal 629 count is never an executed denominator.

## Terminal Behavior

- A no-target prediction is scored, not omitted.
- Each of the three official targets whose step ID is absent from the released
  trajectory is an unrecovered terminal miss for every method; report the
  935-mappable-target result only as a declared sensitivity.
- Bounded-retry parse, context, model, or runtime failure is a terminal miss.
- Smoke runs, prefixes, and successful subsets are not results.
- FULL ends only when every planned cell is complete or terminal.
- Supported, contradicted, or inconclusive outcomes return to full-paper REVIEW.
- No outcome changes the fixed thesis, story, or RQ.

## Tree Update

```text
RQ2 real-problem localization
└── fresh official source repair
    ├── AgentTelemetry -> closed: no official step/span gold
    ├── Who&When -> eligible reserve, not selected
    └── HINTBench -> selected: official current 536-record test snapshot
```

Next: one `research-experiment-design` EXPERIMENT gate using this hypothesis,
the three baseline positions, the 80%-recall metric, and the preflight above.

Do not reopen general search, add another benchmark, edit the paper, or modify
canonical memory in this node. The root owns later canonical updates.

## Final Verdict

**PASS SOURCE SELECTION: HINTBench.**

The current official snapshot is accessible, finite, fresh, licensed, raw-step
complete, and independently step-labeled. Its version mismatch is bounded by
whole-snapshot REAL PREFLIGHT and does not justify weaker RQ2 evidence.
