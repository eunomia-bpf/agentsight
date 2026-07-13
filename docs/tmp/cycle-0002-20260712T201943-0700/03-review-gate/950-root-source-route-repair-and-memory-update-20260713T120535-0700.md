# Root Source-Route Repair And Canonical-Memory Update

**Node:** `950-root-source-route-repair-and-memory-update-20260713T120535-0700`  
**Timestamp:** 2026-07-13T12:05:35-07:00  
**Phase / cycle / gate:** BUILD_AND_EVALUATE / cycle 0002 / REVIEW  
**Role:** owning root bounded repair after outer-audit `REPAIR`  
**Status:** COMPLETE; pending fresh REVIEW outer verification  
**Scientific contract:** unchanged thesis, original story, and four fixed RQs  

## Repair Decision

The root replaces the ineligible AgentTelemetry source route with one eligible,
fresh HINTBench RQ2 experiment. This repairs only the source-selection edge. It
does not change the current-paper verdict, thesis, original AgentProf story,
operations, operation stacks, RQ2 meaning, positive hypothesis, or any other
RQ.

The prior root route in
[`850-root-routing-and-memory-update-20260713T111625-0700.md`](850-root-routing-and-memory-update-20260713T111625-0700.md)
remains an auditable historical node. It is superseded only where it selected
AgentTelemetry as the localization source. It is not rewritten or deleted.

## Why Repair Was Required

The first independent
[`REVIEW outer audit`](990-independent-outer-audit-20260713T112434-0700.md)
verified the current-paper rejection and story/RQ fidelity but returned
**REPAIR CURRENT GATE** on the final source edge. The accepted AgentTelemetry
paper and Zenodo artifact expose fault-detection run/cell outcomes, not released
official fault-bearing span/step identities or first-error gold. Deriving a
target from detector predicates would create new labels and partly define gold
with the detector itself.

The route could not be repaired by using AgentRx or TELBench as fresh
confirmation: cycle 0001 had already run all 73 released AgentRx trajectories
and all 1,000 TELBench cases as target populations. Their official metrics and
labels remain protocol/baseline precedents, but their targets have already
informed AgentProf mechanism diagnosis.

## Bounded Source-Selection Loop

The source repair used `research-literature-novelty` under a finite eligibility
boundary: official accessible artifact, raw agent steps, independent official
step/span gold, fresh target population, complete runnable scope, matched-
recall inspection, and no new benchmark or annotation program.

The completed nodes are:

1. [`200-bounded-fresh-localization-source-selection`](review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md), which selected HINTBench and retained Who&When as reserve;
2. [`300-independent-source-selection-review`](review-002/300-independent-source-selection-review-20260713T115642-0700.md), which returned bounded `REPAIR` on target accounting; and
3. [`400-independent-source-repair-verification`](review-002/400-independent-source-repair-verification-20260713T120251-0700.md), which independently recalculated the official snapshot and returned **PASS** after the bounded repair.

No general paper literature review, idea discussion, second benchmark,
experiment, paper edit, skill change, or human question was opened.

## Selected Official Source

**HINTBench current paper-linked 4open test snapshot.**

- paper: <https://arxiv.org/abs/2604.13954>
- official artifact: <https://anonymous.4open.science/r/HINTBench-B841>
- current test data: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json>
- evaluator: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py>
- license: Apache-2.0

The paper and README describe 629 test records, but the currently downloadable
official test file contains 536. FULL is therefore the complete, enumerable
current 536-record snapshot, not an unavailable advertised denominator.

## Independently Verified Source Facts

| Property | Verified current value |
|---|---:|
| Test records | 536 |
| Risky records | 400 |
| Safe records | 136 |
| Official risk annotations | 978 |
| Distinct `(trajectory, step_id)` target pairs | 938 |
| Distinct mappable targets | 935 |
| Distinct official targets absent from released trajectories | 3 |
| Risky records without any official target | 0 |
| Risky records without a mappable target | 0 |
| Safe records with a non-empty target list | 0 |

The three absent official target IDs are:

| Record | Target step | Rule |
|---:|---:|---|
| 170 | 7 | common unrecovered terminal miss for every method |
| 233 | 9 | common unrecovered terminal miss for every method |
| 516 | 13 | common unrecovered terminal miss for every method |

They remain in the primary intent-to-treat denominator. No method may remap
them to an adjacent step, infer them from text, or remove their annotations or
trajectories. A secondary 935-mappable-target result is a declared sensitivity,
not the primary result.

## Exactly One Next Experiment

### Fixed RQ

**RQ2: Does Profiler Output Correspond to Real Problems?**

### Name-free tested hypothesis

Across the complete current official HINTBench test snapshot, grouping
target-blind atomic trajectory steps by stable semantic responsibility and
ranking the resulting groups requires less atomic-step inspection to recover
at least 80% of official risky-step targets than the strongest comparator that
sees exactly the same raw steps and non-label fields.

This is the tested hypothesis inside fixed RQ2. It is not a new thesis, RQ, or
story.

### Primary decision

For each of the 400 risky trajectories, define the target set as the union of
official step IDs; duplicate annotations at the same step count once. Measure
the minimum atomic-step inspection fraction and count required to reach at
least 80% macro recall. The three absent official targets are common terminal
misses.

Support requires that AgentProf reaches the recall target and its paired
inspection-work reduction interval excludes zero against the strongest
same-information non-oracle baseline. Lower work obtained by lower recall is
not support.

### Competing positions, not separate experiments

1. Native sequential inspection: source order alone is sufficient.
2. Flat independent-step ranking: the target-blind score, not grouping,
   creates the benefit.
3. Flat same-information multidimensional aggregation: ordinary grouping over
   all fields visible to AgentProf captures the useful concentration.

Plan review admits the smallest strong set representing these positions. Every
method receives identical raw steps, allowed non-label fields, target-blind
scores, and tuning opportunity. An oracle may appear only as an upper bound.

### REAL PREFLIGHT eligibility facts

Before FULL, the real path must reproduce:

- 536 records, 400 risky, and 136 safe;
- 978 official annotations and 938 distinct target pairs;
- 935 mappable target pairs;
- exactly the three absent targets above;
- at least one mappable target in every risky trajectory; and
- no target in any safe trajectory.

The scorer uses released `trajectory[].step_id`, not array position. It
deterministically normalizes the two official target fields without reading
descriptions or deriving targets. If the artifact facts differ, the source
returns to REVIEW; the experiment does not improvise a mapping.

### FULL completion

One cell is `(current official test record, approved method, planned
repetition)`. FULL requires a terminal ordered-inspection outcome for every
cell across all 536 records, every admitted baseline, and every declared
repetition. All 978 annotations and all 938 distinct target identities remain
in scoring/accounting. Smoke runs, prefixes, and successful subsets are not
results.

Whatever the sign, the EXPERIMENT gate closes after result review and outer
audit and returns to whole-paper REVIEW.

## One-Experiment Boundary

The HINTBench run does not include:

- a second source or Who&When population;
- an RQ3 tag-accuracy experiment;
- an RQ4 cold/warm profiling-cost experiment;
- a new fault detector or annotation effort;
- an idea or story rewrite;
- a full writing loop; or
- a Git/hash/seal/packet/manifest/attestation/finalizer control system.

Safe trajectories remain negative controls inside the same RQ2 population;
they do not create a second target or enter the risky-step recall denominator.

## Reserve And Closed Sources

- **AgentTelemetry:** useful same-claim, taxonomy, fault-detection, and OTel
  baseline precedent; ineligible as the selected localization source because
  the accepted artifact lacks official step/span gold.
- **AgentRx/TELBench:** strong official localization protocols, but their
  released targets were fully used in cycle 0001 and cannot become fresh
  confirmation again.
- **Who&When:** eligible 184-trajectory reserve with official decisive-error
  steps; a prior large plan never reached implementation or FULL. It is not
  selected because HINTBench supplies a larger current population, multiple
  official target steps, and 136 safe negative controls.

No source branch remains open for the current choice.

## Canonical-Memory Repair

Only the HINTBench route and its target-accounting boundary were propagated.

### `docs/evaluation.md`

- Replaced AgentTelemetry with the selected HINTBench 536-record snapshot.
- Linked the outer-audit source failure, bounded source repair, and independent
  PASS.
- Recorded the 80% macro-recall inspection decision.
- Recorded 978 annotations, 938 distinct targets, 935 mappable targets, and the
  three common terminal misses.
- Kept RQ3/RQ4 outside the experiment.

The file is 202 lines and all local links resolve.

### `docs/background-related-work.md`

- Retained AgentTelemetry as fault-detection precedent while recording its lack
  of official localization gold.
- Added HINTBench as the selected fresh official RQ2 source.
- Replaced every live AgentTelemetry next-route statement with HINTBench.
- Preserved all prior closest-work and completed-branch boundaries.

The file is 191 lines and all local links resolve.

No paper, idea-story, user-instruction, author question, skill, AGENTS file,
source code, experiment result, or submodule file changed.

## Exact Handoff Pending Fresh Outer Verification

If a fresh REVIEW outer verifier confirms that the original 990 blocker and
the later target-accounting repair are closed, the gate may write `999` and
enter one `research-experiment-design` EXPERIMENT gate for fixed RQ2 on
HINTBench.

If verification finds a remaining source or memory contradiction, repair this
gate again without waiting for a human or changing the thesis/RQs. No further
open-ended search is authorized by the current evidence.
