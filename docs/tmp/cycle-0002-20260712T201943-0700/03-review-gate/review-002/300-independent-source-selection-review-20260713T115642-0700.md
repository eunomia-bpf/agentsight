# Independent HINTBench Source-Selection Review

**Node:** `review-002/300-independent-source-selection-review-20260713T115642-0700`  
**Timestamp:** 2026-07-13T11:56:42-07:00  
**Phase / cycle / gate:** BUILD_AND_EVALUATE / cycle 0002 / REVIEW  
**Role:** fresh independent source-selection reviewer using
`research-literature-novelty`  
**Declared coverage boundary:** HINTBench and Who&When official paper, repository,
data, license, and evaluator only  
**Verdict:** **REPAIR**  
**Git operations:** none  
**Files changed:** this report only

## Executive Verdict

**REPAIR**, with one bounded scientific correction. HINTBench remains an
eligible and preferable fresh source for the next fixed-RQ2 experiment. The
current file at the paper-linked official artifact is accessible, Apache-2.0
licensed, finite, independently annotated, and unused by this repository's
prior experiments. It can be defined honestly as one complete execution
population of **536 currently downloadable test records**, rather than as the
629-record benchmark described by the paper and README.

The source-selection report cannot pass unchanged because its preflight
condition says all 978 targets must map to existing atomic steps. Direct
whole-file verification shows:

- there are 978 official **risk annotation records**;
- those records refer to 938 distinct `(trajectory, step)` target pairs because
  40 annotations share a step with another annotation;
- 975 annotation records, covering 935 distinct target pairs, match an existing
  `trajectory[].step_id`; and
- three injected annotations refer to step IDs absent from their released
  trajectories.

The three absent targets are not a reason to change benchmark, RQ, hypothesis,
or matched-recall design. They require a fixed terminal rule: retain all three
in the denominator as unmappable misses for every method, report the primary
result both with this intent-to-treat rule and as a declared mappable-target
sensitivity, and never infer a replacement from an adjacent step. The primary
step-recall denominator must use the per-trajectory union of official step IDs,
consistent with the released evaluator's risk-step metric; it must not call all
978 annotation records 978 distinct steps.

After that correction, the source selection may enter root canonical memory.
No additional benchmark, search, checker, packet, paper edit, skill change, or
human decision is needed.

## Fixed Scientific Contract

The unchanged paper-level RQ is:

> **RQ2: Does profiler output correspond to real problems?**

The selected experiment retains the strong positive hypothesis in name-free
form:

> Across the complete current official HINTBench test snapshot, grouping
> target-blind atomic trajectory steps by stable semantic responsibility and
> ranking the resulting groups requires less atomic-step inspection to recover
> at least 80% of official risky-step targets than the strongest comparator
> that sees exactly the same raw steps and non-label fields.

This is step localization at matched recall, not run-level risk detection or
run triage. It does not rename or narrow RQ2. It does not add tag-label accuracy
(RQ3), profiler construction/runtime cost (RQ4), or any second experiment.

## Inputs Read In Full

### Current REVIEW repair

- `review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md`
- `990-independent-outer-audit-20260713T112434-0700.md`, including the
  AgentTelemetry source failure, source-selection must-fix, and transition
  decision

### Prior RQ2 evidence and reserve status

- cycle 0001 `loop-rq2-00/result-review.md`
- cycle 0001 `loop-rq2-00/grouping-result-review.md`
- cycle 0001 `loop-rq2-01/experiment-plan.md`
- cycle 0001 `loop-rq2-01/plan-review.md`
- cycle 0001 `loop-rq2-01/source-protocol-audit.md`
- cycle 0001 `loop-rq2-01/experiment-handoff.md`

### Current human and experiment memory

- `docs/user-instruction.md`
- `docs/evaluation.md`

The user-fixed four-RQ program, exact RQ2 wording, one-RQ/one-experiment rule,
complete-run requirement, and prohibition on shrinking the idea were therefore
read before source judgment.

## Primary Official Sources Opened

### HINTBench

- Paper: <https://arxiv.org/abs/2604.13954>
- Paper HTML: <https://arxiv.org/html/2604.13954>
- Paper-linked artifact: <https://anonymous.4open.science/r/HINTBench-B841>
- README: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/README.md>
- Current test file: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json>
- Current validation file: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json>
- Evaluator: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py>
- License: <https://anonymous.4open.science/api/repo/HINTBench-B841/file/LICENSE>

### Who&When

- ICML/OpenReview paper page: <https://openreview.net/forum?id=GazlTYxZss>
- Official repository: <https://github.com/ag2ai/Agents_Failure_Attribution>
- Official dataset page: <https://huggingface.co/datasets/Kevin355/Who_and_When>
- Locally available official repository snapshot under
  `/tmp/rq2_sources_revision1/Agents_Failure_Attribution/`, including all 184
  released JSON files, `Automated_FA/evaluate.py`, `paper.pdf`, and `LICENSE`

No other benchmark or literature family was searched. HINTBench and Who&When
were the complete declared source tree for this review.

## HINTBench Official Claims Versus Current Artifact

### Paper and README claims

The arXiv paper identifies the linked 4open repository as its code/data
artifact. It describes:

- 629 test trajectories;
- 523 risky and 106 safe trajectories;
- 33 messages/steps on average;
- 1,418 risk steps; and
- step-level risk localization as an official benchmark task.

The README describes the same 629-record test split plus an 80-record
validation split, for 709 total records. Its documented example uses
`injected_risks`, `risk_origin_step`, and `affected_steps`. It says trajectory
length is counted at the message level and exposes an official evaluator for
risk detection and risk-step localization.

### Fresh whole-file verification of the current test download

The current `data/hintbench.json` was downloaded directly from the official
paper-linked endpoint and enumerated in full. It contains:

| Property | Directly verified current value |
|---|---:|
| Records | 536 |
| Risky records | 400 |
| Safe records | 136 |
| Risk annotation records | 978 |
| `source: injected` annotations | 518 |
| `source: additional` annotations | 460 |
| Annotations with `risk_origin_step` | 464 |
| Annotations with `step_id` | 514 |
| Annotations with both target fields | 0 |
| Annotations with neither target field | 0 |
| Non-numeric targets | 0 |
| Risky records without annotations | 0 |
| Safe records with non-empty annotations | 0 |
| Distinct `(trajectory, target step)` pairs | 938 |
| Duplicate annotation records sharing a target step | 40 |

Every current test record uses top-level fields `env`, `id`, `is_risky`,
`risk_labels`, `task_id`, and `trajectory`. The test file does not expose the
README's top-level `injected_risks`, and its annotations do not expose
`affected_steps`.

The current validation file independently enumerates to the advertised 80
records, split 60 risky and 20 safe, with 169 `injected_risks` records. It uses
the README-style schema. The test and validation files therefore belong to two
different released schema states even though the current evaluator accepts one
`--data-file` interface.

### Evaluator incompatibility

The official evaluator's scoring path reads gold from
`item.get("injected_risks", [])`. Its `risk_steps_set` accepts `risk_steps`, or
falls back to the union of `risk_origin_step` and `affected_steps`. Its
step-level metric unions the resulting step IDs within each sample before
computing precision, recall, and F1.

Running this evaluator unchanged on the current test file would therefore see
an empty gold-risk list for every record because the file instead uses
`risk_labels`. The source-selection report correctly rejects an unchanged
evaluator claim and permits only deterministic field-format glue. The
experiment must say it reuses the published task and step-union scoring rule,
not that it runs the current evaluator unchanged.

### License and access

The paper-linked data, README, evaluator, and license endpoints all responded.
The repository license is Apache License 2.0. The current snapshot is therefore
accessible and usable for the planned research comparison.

## The Three Unmappable Official Targets

Almost all official targets match an existing `trajectory[].step_id`. The only
exceptions are:

| Record `id` | `task_id` | Official target | Annotation | Released step-ID gap |
|---:|---|---:|---|---|
| 170 | `propertyRisk_task_0009_risk_v7` | 7 | injected `factual_unsupported_claim` | steps jump 6 to 8 |
| 233 | `publicTransit_task_0006_risk_v6` | 9 | injected `factual_unsupported_claim` | steps jump 8 to 11 |
| 516 | `sportsIntelligence_v11_task_0012_risk_v1` | 13 | injected `factual_evidence_contradiction` | steps jump 12 to 14 |

The released trajectories have unique `step_id` values, but 216 of 536
trajectories are not a contiguous zero-based sequence. Across all annotations,
28 target values would be out of range if interpreted blindly as zero-based
array positions, while seven would be out of range under a one-based array
interpretation. Array position is therefore not a globally valid substitute
for the released `step_id` field.

Each of the three affected trajectories contains other valid official targets,
so no risky trajectory becomes wholly targetless. That fact does not authorize
guessing that the missing target means the preceding or following visible
message. A conditional rule such as “use exact `step_id`, otherwise use array
position” would silently construct three new labels from dataset irregularity
and could favor one ranking. The paper, README, and evaluator provide no primary
evidence for such a hybrid rule.

The scientifically neutral treatment is:

1. include all three official target identities in the intent-to-treat target
   population;
2. mark each as `official-target-step-absent` before any method ranking;
3. score it as an unrecovered terminal target for every method;
4. never drop the containing trajectory or annotation;
5. report a secondary sensitivity over the 935 distinct mappable target pairs;
   and
6. disclose that the current artifact has 938 distinct target pairs, of which
   three lack released step content.

This preserves official labels without handmade localization.

## What “FULL” May Mean Here

The paper/README/current-file inconsistency does not disqualify the source, but
it changes the only defensible completion claim.

**Permitted FULL definition:** every one of the 536 records currently
enumerable at the official test-file endpoint, crossed with every approved
method and planned repetition, including all 136 safe records and all 978
annotation records under the terminal rule above.

**Forbidden descriptions:**

- “the full published 629-record HINTBench test set”;
- “all 1,418 published HINTBench risk steps”;
- “the official evaluator ran unchanged”; or
- any comparison of a new 536-record number with a paper table as though the
  evaluated populations were identical.

The experiment may reuse the published task, annotation rationale, and
step-localization protocol. It must label its source as the **current official
536-record artifact snapshot** and treat the 629/523/106/1,418 discrepancy as a
source-version limitation. Complete execution then has a finite, auditable
meaning without pretending that missing paper-era records were run.

## No Handmade Labels And No Prior Target Consumption

HINTBench already supplies all target identities used by the experiment. The
allowed adapter merely reads one of two official numeric target fields and
normalizes it into one internal field. It must not infer risk from descriptions,
move an absent target to a neighboring message, create affected-step ranges,
or ask an author/LLM to relabel the data.

A repository-wide exact search found no HINTBench source, target ID, experiment
output, or result path outside the new source-selection report. After excluding
that report, `HINTBench` has no match in the project. The only unrelated
`risk_labels` match is an existing generic unit-test name. The 536-record
HINTBench outcome population is therefore fresh to AgentProf; prior agents have
not selected the method from these targets.

## Who&When Reserve Verification

The official repository and local official snapshot contain exactly:

- 126 algorithm-generated JSON trajectories;
- 58 hand-crafted JSON trajectories; and
- 184 trajectories total.

All 184 expose raw `history`, `question`, `question_ID`, `ground_truth`,
`mistake_agent`, `mistake_step`, and `mistake_reason`. All `mistake_step` values
are released as strings. The schema varies: algorithm-generated files use
`is_correct`, while hand-crafted files use `is_corrected`; some files include
`labels`, `level`, `system_prompt`, or `mistake_type`. The blanket statement
that every record has `is_corrected` is therefore inaccurate but irrelevant to
the official decisive-step target.

The official evaluator reads `mistake_agent` and `mistake_step`. It uses
substring containment rather than exact integer equality, so the prior plan's
exact-step adapter remains the scientifically stronger primary metric. The
repository is MIT licensed and provides inference/evaluation code.

### Why Who&When has not already been FULL-executed

Cycle 0001 `loop-rq2-01` completed a source audit and five serial reviews of a
much larger Who&When-plus-TRAIL experiment plan. Round 5 remained `REVISE`
because all mandatory criteria could still pass after partially filling a
terminal scope, failing to prove useful whole-scope localization. The handoff
explicitly states:

- implementation was not started;
- real preflight was not started;
- FULL execution was not started; and
- no empirical result was produced.

Who&When is therefore unconsumed confirmation data, not a benchmark rejected by
an outcome. It remains the correct reserve because it has a clean official
decisive-step target, an official evaluator, and an executable 184-record
population. It is not selected now because HINTBench supplies a larger current
population, multiple annotations per risky trajectory, and 136 safe negative
controls. Exactly one source enters the next experiment.

## Baselines, Metric, And One-Experiment Boundary

The three baseline positions in the source-selection report are three competing
scientific explanations inside one matrix:

1. native sequential inspection tests whether source order alone is enough;
2. flat independent-step ranking tests whether scoring alone explains the gain;
3. flat same-information multidimensional aggregation tests whether ordinary
   grouping over all visible fields explains the gain.

They are not three experiments. They receive the same raw steps, allowed
non-label fields, target-blind scores, and tuning opportunity as the proposed
semantic organization. An oracle may be reported only as a ceiling, not as a
main baseline.

The single primary decision remains atomic-step inspection work at 80% macro
recall against the strongest same-information non-oracle comparator. “Macro”
must be defined over the 400 risky trajectories, using the per-trajectory union
of official target step IDs, as the official risk-step evaluator does. Safe
trajectories stay in the full run as negative controls and measure unnecessary
prioritization; they do not create a target-recall denominator.

Support still requires reaching 80% recall and a paired work-reduction interval
excluding zero against the strongest comparator. This metric is analyst
inspection work intrinsic to RQ2 localization, not an RQ4 profiler-runtime
program. Risk taxonomy labels may characterize subgroups but cannot become an
RQ3 tag-accuracy result.

## Corrected REAL PREFLIGHT Boundary

The bounded real preflight should do only the following source-critical work:

1. enumerate 536 records, 400 risky records, 136 safe records, and 978 official
   annotation records;
2. normalize `risk_origin_step` and `step_id` without reading descriptions or
   deriving new targets;
3. verify 938 distinct target pairs, classify 935 as mappable and the three
   listed above as terminal unmappable targets;
4. verify every risky record retains at least one mappable target and every safe
   record has none;
5. run one complete real record through every approved method and the scorer
   with gold absent from ranking; and
6. record that the current artifact differs from paper, README, validation
   schema, and unchanged evaluator.

Preflight must not require the false proposition that all 978 annotations map
to existing steps. It must not repair the three labels, remove them, or return
to open-ended source search merely because they remain terminal misses.

## FULL And Terminal Behavior

One cell is `(current official test record, approved method, planned
repetition)`. FULL requires a terminal ordered-inspection result for every cell
across all 536 records. It also requires all approved baseline cells, all
declared repetitions, and all 978 annotations to appear in scoring/accounting.

- no-target output is scored, not omitted;
- bounded parse/model/runtime failure is a terminal miss;
- each of the three absent official steps is a terminal miss for all methods;
- safe records are retained as negative controls;
- prefixes, smoke runs, and successful subsets are never results; and
- every supported, contradicted, or inconclusive outcome returns to whole-paper
  REVIEW without changing the thesis, RQ2, or positive hypothesis.

This is one complete localization experiment. It does not add a separate
detector, tagger evaluation, profiler-cost study, or benchmark.

## Source Qualification Matrix

| Qualification | HINTBench current snapshot | Who&When reserve |
|---|---|---|
| Official primary link | Paper-linked 4open artifact | ICML paper-linked repository/data |
| Accessible finite population | 536 current test records | 184 released files |
| Official localization gold | 978 annotations / 938 distinct target pairs | one decisive-error step per trajectory |
| Mappable released step targets | 935 distinct; 3 terminal absent targets | 184 released step labels |
| Safe negative controls | 136 | none in the failure benchmark |
| Handmade labels required | No | No |
| Prior FULL AgentProf outcome | None | None; plan ended before implementation |
| License | Apache-2.0 | MIT |
| Main source caveat | paper/README/schema/evaluator mismatch | schema variation and weak substring evaluator |
| Selection | **Selected after bounded repair** | eligible reserve |

## Impact On Novelty, Evaluation, And Search Tree

HINTBench is an external task/metric precedent and a fresh official evaluation
asset, not a source of a new paper thesis. It strengthens RQ2 by demanding
localization of independently annotated risky steps across a complete held-out
population. It does not establish novelty by itself and does not alter
operations, operation stacks, the profiling thesis, or any RQ.

The source tree is now finite:

```text
RQ2 real-problem localization
└── official target-bearing source repair
    ├── AgentTelemetry -> closed: official artifact lacks step/span gold
    ├── Who&When -> eligible reserve; prior plan only, no FULL result
    └── HINTBench -> selected after bounded target-accounting repair
        ├── 536 current records define FULL
        ├── 978 annotations / 938 distinct step targets
        └── 3 absent step IDs -> common terminal misses, never remapped
```

No open search branch remains for this source decision.

## Bounded Must-Fix

Before root canonical update, replace only the invalid target-accounting
language in the source handoff:

1. distinguish 978 annotation records from 938 distinct risky-step target
   pairs;
2. replace “prove all 978 targets map” with the fixed 935-mappable plus
   three-terminal-unmappable rule;
3. use the per-trajectory union of step IDs for the primary step-recall metric,
   retaining annotation-level/type analyses only as secondary; and
4. describe FULL as all 536 currently released test records, not the published
   629-record population.

Do not add a benchmark, checker, manifest, hash, seal, packet, evaluator rewrite,
paper/skill change, or human approval. Do not move the three targets to adjacent
steps and do not remove their trajectories. HINTBench remains the selected
source after this correction.

## Final Verdict

**REPAIR.** The scientific route is sound and remains fixed RQ2 on HINTBench.
The only blocker is inaccurate target accounting in the handoff: three of the
938 distinct official target-step identities have no released atomic step, and
978 counts annotations rather than distinct steps. Treat those three as common
terminal misses, preserve all 536 records, and then the source selection is
ready for canonical propagation and one complete matched-recall experiment.
