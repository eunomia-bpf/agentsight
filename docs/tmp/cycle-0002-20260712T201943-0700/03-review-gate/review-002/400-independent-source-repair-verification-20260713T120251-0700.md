# Independent HINTBench Source-Repair Verification

**Node:** `review-002/400-independent-source-repair-verification-20260713T120251-0700`  
**Timestamp:** 2026-07-13T12:02:51-07:00  
**Phase / cycle / gate:** BUILD_AND_EVALUATE / cycle 0002 / REVIEW  
**Role:** fresh independent verifier using `research-literature-novelty`  
**Fixed scope:** bounded HINTBench target-accounting repair for RQ2 only  
**Verdict:** **PASS**  
**Git operations:** none  
**Files changed:** this report only

## Executive Verdict

**PASS.** The repaired source-selection report closes all four bounded
must-fixes from the independent source review without changing the selected
source, the fixed RQ, or the positive hypothesis.

The current official HINTBench test endpoint contains 536 records: 400 risky
and 136 safe. Its 978 official risk-annotation records refer to 938 distinct
`(trajectory, step_id)` target pairs. Exactly 935 distinct pairs match released
atomic steps. The remaining three official target identities are the already
identified steps in records 170, 233, and 516. The repair now retains those
three as common terminal misses for every method; it neither remaps nor drops
them. Every risky trajectory still has at least one mappable official target,
and no safe trajectory has a non-empty target list.

The primary metric is now unambiguously defined over the per-trajectory union
of official step IDs, with duplicate annotations at the same step counted once.
FULL means all 536 records currently enumerable from the official test endpoint,
not the paper/README's 629-record population. These rules make the source
selection scientifically executable while preserving the stronger matched-
recall localization hypothesis.

No further source search, source substitution, label construction, RQ change,
paper edit, process contract, or human decision is needed before ordinary REAL
PREFLIGHT in the next EXPERIMENT gate.

## Declared Coverage Boundary

This verification was intentionally restricted to:

1. the repaired source-selection report;
2. the independent source-selection review that issued the four bounded
   must-fixes;
3. the REVIEW outer audit's one source-route blocker;
4. `docs/user-instruction.md`; and
5. the current official HINTBench test JSON and evaluator, opened only to
   independently verify the decisive counts and scoring unit.

No open-ended literature search was performed. No new benchmark or candidate
source was considered. Who&When remains the reserve named by the repaired
handoff and was not reopened.

## Inputs Read In Full

- `review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md`
- `review-002/300-independent-source-selection-review-20260713T115642-0700.md`
- `03-review-gate/990-independent-outer-audit-20260713T112434-0700.md`
- `docs/user-instruction.md`

The human constraints read before judgment include the exact fixed RQ program,
the prohibition on shrinking the idea, the preference for real published
benchmarks and complete runs, the one-RQ/one-experiment boundary, the ban on
waiting for human intervention, and the separation of Git from scientific
judgment.

## Primary Artifact Verification

The only external evidence opened was the paper-linked official HINTBench
artifact:

- current test JSON:
  <https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json>
- current evaluator:
  <https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py>

The current JSON was enumerated in full at verification time. For each
annotation, the verifier used its official numeric `risk_origin_step` when
present or its official numeric `step_id` otherwise. A target was classified as
mappable only when that exact value occurred in the same record's released
`trajectory[].step_id` values. No annotation description, array-position
fallback, adjacent-step inference, or new label was used.

### Independently recomputed population

| Property | Verified value |
|---|---:|
| Current test records | 536 |
| Risky records | 400 |
| Safe records | 136 |
| Official risk-annotation records | 978 |
| Annotations using `risk_origin_step` | 464 |
| Annotations using `step_id` | 514 |
| Distinct `(trajectory, target step)` pairs | 938 |
| Duplicate annotations sharing a pair | 40 |
| Mappable annotation records | 975 |
| Unmappable annotation records | 3 |
| Distinct mappable target pairs | 935 |
| Distinct unmappable target pairs | 3 |
| Risky records without any official target | 0 |
| Risky records without any mappable target | 0 |
| Safe records with non-empty risk labels | 0 |

### Independently recomputed unmappable targets

| Record `id` | `task_id` | Official target step | Status |
|---:|---|---:|---|
| 170 | `propertyRisk_task_0009_risk_v7` | 7 | absent from released trajectory; common terminal miss |
| 233 | `publicTransit_task_0006_risk_v6` | 9 | absent from released trajectory; common terminal miss |
| 516 | `sportsIntelligence_v11_task_0012_risk_v1` | 13 | absent from released trajectory; common terminal miss |

The official evaluator independently confirms the relevant scoring primitive:
it unions the official risk-step identities within each sample before computing
step precision, recall, and F1. It reads `injected_risks`, so the repaired report
correctly permits deterministic field normalization for the current test
schema and correctly forbids claiming that the evaluator runs unchanged. The
planned primary metric preserves the within-trajectory union but computes the
declared macro recall across the 400 risky trajectories.

## Four Must-Fix Closure Audit

| Must-fix from report 300 | Repaired report 200 | Verification |
|---|---|---|
| Distinguish 978 annotations from distinct step targets | States 978 annotation records and 938 distinct `(trajectory, step_id)` targets; explains the shared-step duplicates | **Closed** |
| Replace the false all-targets-map condition | States 935 mappable distinct targets and identifies records 170, 233, and 516 as three terminal unmappable misses | **Closed** |
| Use per-trajectory target union for primary recall | Defines each risky trajectory's target set as the union of official step IDs; duplicate annotations at one step count once | **Closed** |
| Define FULL by the current downloadable population | Defines FULL as every one of the current 536 test records and explicitly rejects 629 as an executed denominator | **Closed** |

The repaired preflight no longer contains the invalid proposition that all 978
annotation records map to released steps. It requires the exact independently
verified counts instead and treats any future count mismatch as source
ineligibility rather than permission to repair labels.

## Source Eligibility And Freshness

HINTBench remains eligible after the repair:

- the current source is finite and enumerable;
- it exposes raw atomic trajectories and independent official numeric step
  targets;
- it supplies 400 risky trajectories and 136 safe negative controls;
- every risky trajectory has at least one mappable official target;
- no handmade remapping or dropping is needed;
- all three absent target identities can be handled symmetrically for every
  method; and
- the source-version discrepancy is disclosed instead of hidden.

An exact repository path scan found `HINTBench` only in the new bounded
source-selection and its independent review. There is no earlier AgentProf
HINTBench result, implementation, target-consumption report, or outcome path.
The source is therefore still fresh for method selection and FULL execution.

Who&When remains an eligible reserve only. The repaired report selects exactly
one source and does not combine populations.

## Experiment-Boundary Audit

The repaired handoff remains one complete RQ2 localization experiment:

- **RQ:** only fixed RQ2, real-problem localization;
- **positive hypothesis:** stable semantic-responsibility grouping reduces
  atomic-step inspection at matched recall;
- **primary decision:** inspection fraction/count at at least 80% macro recall;
- **comparison:** strongest same-information, non-oracle baseline;
- **target unit:** per-trajectory union of official risky-step IDs;
- **population:** all current 536 test records, including all 136 safe records;
- **terminal handling:** the three absent official steps miss equally for every
  method, and parse/model/runtime failures are scored rather than omitted; and
- **completion:** every approved method-record-repetition cell reaches a
  terminal result; smoke runs and successful subsets are not results.

The baseline positions remain competing explanations within the same one-RQ
matrix, not separate experiments. The handoff does not add tag-accuracy work,
profiling-runtime work, a second benchmark, or a second RQ. Safe records are
retained as negative controls without being inserted into the risky-target
recall denominator.

## Prohibited-Complexity And Human-Intent Audit

The repair introduces none of the prohibited machinery. It creates no hash
binding, seal, packet, attestation, finalizer, private key, immutable manifest,
or non-Markdown contract. It does not condition scientific passage on Git and
performs no Git operation. It does not request or wait for human approval.

The repair also does not narrow the thesis, RQ2, operation abstraction,
operation-stack abstraction, or intended positive result. It addresses an
artifact irregularity through transparent accounting and then proceeds with
the larger external matched-recall test, consistent with the user's direction
to hypothesize boldly and verify carefully.

## Residual Caveat And Next Node

The 536-versus-629 source-version discrepancy and the three absent step IDs
remain material limitations of the official artifact. They are no longer
source-selection blockers because the repaired handoff states them explicitly,
defines a finite current FULL population, keeps the three labels in the primary
denominator, and requires a mappable-target sensitivity rather than silently
changing gold.

The next node may therefore be one ordinary `research-experiment-design`
EXPERIMENT gate for fixed RQ2:

```text
approved HINTBench source handoff
  -> Markdown experiment plan and 3--5 scientific reviews
  -> REAL PREFLIGHT on the real current artifact
  -> FULL execution across all 536 records and admitted methods
  -> result review
  -> whole-paper REVIEW regardless of result sign
```

No source-search branch remains open. If REAL PREFLIGHT reproduces counts other
than 536 records, 978 annotations, 938 distinct target pairs, 935 mappable
pairs, and the same three absent IDs, it must return the source to REVIEW rather
than improvise a mapping. That is an ordinary empirical source check, not a new
control protocol.

## Final Verdict

**PASS.** All four bounded must-fixes are closed. HINTBench remains a fresh,
eligible, real-world external source for one fixed-RQ2 matched-recall
localization experiment; Who&When remains reserve only. The repaired report is
ready for root canonical propagation and subsequent complete execution.
