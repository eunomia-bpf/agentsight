# Independent Result Review: Existing-Trajectory Reference Calibration

**Reviewed:** 2026-07-15
**Skill used:** `research-experiment-design`
**Review type:** fresh read-only raw-result reconstruction
**Disposition:** **APPROVE**, with two reporting qualifications recorded below
**Candidate or repair authorized by this review:** none

## Scope And Independence

I completely read the current `research-experiment-design` skill, the complete
Step 0030 experiment plan, plan review, implementation review and both focused
follow-ups, preflight report, result report, the complete 970-line evaluator,
and every directly imported helper. I also read the paper's fixed RQ3 question,
hypothesis, protocol, result, and limitation text and the complete current
`docs/evaluation.md` frontier.

I independently reconstructed the experiment from the final raw root
`.agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full/`.
The reconstruction did not import the Step 0030 evaluator or accept its
`summary.json` classifications. It independently implemented transition NPMI,
cutoff enumeration, B-cubed, boundary metrics, fold assignment, segment
assignment, and manifest-stage expansion. It also read the retained Step 0024
raw OSWorld-Human and CodeTraceBench pair/operation files rather than accepting
the Step 0030 copy of the baseline numbers.

I did not edit the plan, evaluator, product, paper, canonical documents,
skills, submodule, or Git. This report is my only write. I did not design or
run a second candidate.

## Completion And Raw Coverage

The successful final run is complete.

| Population | Sessions | Operations | Adjacent pairs | Oracle groups/stages |
|---|---:|---:|---:|---:|
| OSWorld-Human | 287 | 3,978 | 3,691 | 2,042 |
| CodeTraceBench failed target | 405 | 20,866 | 20,461 | 2,948 |

The pooled OSWorld files contain 3,691 unique `(session, position)` pair rows
and 3,978 unique `(session, operation_index)` assignment rows. The CodeTrace
files contain 20,461 and 20,866 corresponding unique rows. Every session's
operation indices are consecutive; reconstructing segments from the raw pair
booleans reproduces every stored candidate assignment. The five OSWorld fold
files jointly target every one of the 287 sessions exactly once. The final run
does not stop at a favorable fold, framework, or population.

## Independent Metric Reconstruction

### OSWorld-Human

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 | Groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current Step 0024 | 0.591810890671 | 0.798860398860 | 0.679922405432 | 0.855871535451 | 0.726965621631 | 0.786169543748 | 2,656 |
| Reference-calibrated | 0.609645817634 | 0.921937321937 | 0.733953277387 | 0.916999628384 | 0.711189966640 | 0.801087216271 | 2,941 |

The candidate's B-cubed delta is `+0.014917672522`. Its boundary confusion
counts are TP 1,618, FP 1,036, FN 137, and TN 900. The current constructor's
counts are TP 1,402, FP 967, FN 353, and TN 969.

The Step 0030 `current` decision for every one of the 3,691 pairs is identical
to the retained Step 0024 raw `recurrence` decision. Reconstructing Step 0024
groups from those raw decisions gives exactly 2,656 groups and B-cubed F1
`0.7861695437481889`, identical to the Step 0030 raw-row reconstruction. The
retained Step 0024 summary stores `0.7861695437481895`; the difference is
`6.66e-16` from floating summation order, not a decision, group, or reported-
precision difference. Boundary F1 is literally identical in raw and summary.

### CodeTraceBench

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 | Groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current Step 0024 | 0.199784349969 | 0.510027526543 | 0.287105700055 | 0.828579403968 | 0.533630051887 | 0.649173103932 | 6,897 |
| Reference-calibrated | 0.179049939099 | 0.346834447503 | 0.236176194939 | 0.734522797060 | 0.610114777543 | 0.666563572806 | 5,331 |

The candidate's B-cubed delta is `+0.017390468874`. Its boundary confusion
counts are TP 882, FP 4,044, FN 1,661, and TN 13,874. The current constructor's
counts are TP 1,297, FP 5,195, FN 1,246, and TN 12,723.

The Step 0024 CodeTrace raw files cover the exact same 405 session IDs,
20,866 operations, 20,461 adjacent pairs, per-operation actions, frameworks,
and 2,948 official stage assignments. Independent scoring of those retained
raw rows reproduces Step 0024 boundary F1 `0.28710570005534036` and B-cubed F1
`0.6491731039323719` exactly. Thus the current comparison is not a stale or
population-mismatched summary comparison.

Independent candidate B-cubed F1 by framework is 0.677985637446 on OpenHands,
0.689244870648 on SWE-agent, 0.629514964355 on Terminus2, and
0.689372134907 on mini-SWE-agent. These rows reproduce the raw summary and
remain diagnostics, as predeclared.

## Cutoff Enumeration And Selection

I independently rebuilt each action-transition table from the source-visible
actions, enumerated one cutoff below the lowest distinct observed score, every
adjacent-score midpoint, and one cutoff above the largest score, optimized
operation-weighted B-cubed on calibration groups, and applied the exact
smallest-cutoff tie rule.

| Population/fold | Calibration sessions | Distinct scores | Candidates | Exact best ties | Selected cutoff | Calibration B-cubed F1 |
|---|---:|---:|---:|---:|---:|---:|
| OSWorld fold 0 | 242 | 99 | 100 | 1 | 0.274482784767 | 0.805014548223 |
| OSWorld fold 1 | 232 | 101 | 102 | 1 | 0.326138235948 | 0.804009193121 |
| OSWorld fold 2 | 227 | 102 | 103 | 1 | 0.250125493253 | 0.806970183943 |
| OSWorld fold 3 | 225 | 93 | 94 | 1 | 0.415066162347 | 0.800463023550 |
| OSWorld fold 4 | 222 | 103 | 104 | 1 | 0.282964131526 | 0.792774798961 |
| CodeTrace solved reference | 483 | 73 | 74 | 1 | -0.098246630349 | 0.695599516312 |

Every selected cutoff, candidate count, tie count, and calibration objective
matches the stored result exactly. Recomputing every target pair from the
source action sequence, independently reconstructed NPMI table, and selected
cutoff reproduces every raw candidate score and boundary. No boundary metric,
framework identity, target result, or target oracle participates in selection.
Unseen transitions remain boundaries.

OSWorld uses one fitted scalar per training-fold instance, which is the
predeclared five-fold application of the same scalar-calibration procedure;
CodeTrace uses one scalar for its complete failed-target population. This is
not a hidden cutoff sweep over target outcomes.

## Isolation And Leakage Audit

### OSWorld-Human

The independent source reconstruction yields fold sizes 45, 55, 60, 62, and
65 under the fixed hash rule. For each fold, only the other four folds build
the NPMI table and provide calibration group identities. The candidate receives
only visible action sequences. In the reviewed call path, the target-fold
oracle loader is invoked only after `fold-<f>-predictions.jsonl` is written;
the five persisted fold files precede pooled scorer outputs. Eligibility still
uses the predeclared `group_alignment=exact`, nonempty-group, at-least-two-
operation criterion. That selects the registered annotated population but
does not expose target group identities to fitting or prediction.

### CodeTraceBench

The independently reconstructed sets are:

- complete normalized reference: 2,634 sessions / 108,569 operations;
- target-disjoint score reference: 2,229 sessions / 87,703 operations;
- solved calibration: 483 sessions / 18,152 operations / 2,886 stages;
- failed target: 405 sessions / 20,866 operations / 2,948 stages; and
- manifest rows without a normalized non-target reference: 112 sessions.

The 405 target IDs have empty intersection with both the 2,229 score-reference
IDs and 483 calibration IDs. The selected-ID files equal the reconstructed
sets exactly. The 483 calibration and 405 target extracted rows are exact
copies of their official manifest rows, have the expected solved values and
step counts, and expand to complete, consecutive, nonoverlapping stages over
all 18,152 and 20,866 operations.

The final artifacts show `target-predictions.jsonl` persisted at
16:57:30.313 before the selected target-stage artifact at 16:57:30.554. The
parent fitting process receives only selected calibration-stage rows before
cutoff fitting; selected failed-target rows reach it only after target
predictions. The isolated extractor internally decodes the manifest's broad
stage column before filtering, so the scientifically exact wording is that
failed-target stage rows were **unavailable to the fitting/prediction process**,
not that no operating-system process decoded those bytes before prediction.
The extractor has no output or return channel for unselected rows, and exact-ID
checks reject extra or missing rows. I find no target-oracle path into the
candidate.

Using B-cubed for reference fitting and held-out target evaluation is ordinary
supervised calibration, not metric circularity. The reference and target group
assignments are disjoint. Prior project observation of both development
populations limits novelty/generalization wording but does not invalidate this
within-population held-out calibration test.

## Execution Deviations

The final successful invocation recomputed all five OSWorld folds and the
complete CodeTrace target after two earlier full invocations stopped in native
Parquet/process handling. The final repair moves selected-row extraction into
a normal short-lived subprocess and checks the exact selected IDs. Static
review and raw reconstruction show that this changed neither visible inputs,
NPMI, cutoff candidates, tie handling, segment construction, metrics, nor the
fixed interpretation. No CodeTrace target prediction or CodeTrace target
metric existed before the execution-only repair, and no second candidate was
introduced.

One sentence in `experiment-result.md` is too broad: “No partial or failed
invocation contributed a candidate target metric” cannot literally include
OSWorld, because the failed full invocations completed and persisted all five
OSWorld folds, and the evaluator computes the OSWorld metrics before entering
CodeTrace. The scientifically accurate statement is that no partial result was
used to alter the candidate or interpretation, and no failed invocation
produced a CodeTrace target metric. The final run independently recomputed the
complete matrix. This is a reporting correction, not a validity failure.

## Baseline Fairness And Information Budget

Step 0024 is the correct matched-mechanism baseline: same action-transition
score, unseen-transition rule, target inputs, and partition scorer. The
candidate has additional group annotations on reference sessions, whereas
Step 0024 is label-free. Therefore the result establishes the value of an
optional **reference-calibrated** mode; it does not establish equal-information
superiority over the default constructor. The plan and result report state
this distinction, and the current paper already separates its supervised and
label-free rows. Any paper promotion must preserve that separation.

The OSWorld supervised nine-field predictor and the CodeTrace visible
phase-change partition remain interpretation comparators, not defeated main
baselines. The result does not establish literal tag-name correctness,
phase/action identity, an untouched cross-family confirmation, or a complete
RQ3 answer.

## CodeTrace Boundary-F1 Tradeoff

The CodeTrace boundary-F1 decrease does not invalidate the predeclared tested
hypothesis. The plan's claim-matched primary effect is operation-weighted
B-cubed partition fidelity and classifies support by strict B-cubed improvement
on both complete populations. Boundary F1 was predeclared as a diagnostic and
as a veto only if it exposed incorrect coverage, assignment, comparison, or a
different exact claim. None of those conditions occurs: every operation is
assigned once, oracle and target coverage are exact, and the candidate's
partition is scored independently.

Scientifically, the CodeTrace scalar merges the current 6,897 groups into
5,331. That lowers boundary F1 from 0.287106 to 0.236176 and lowers B-cubed
precision from 0.828579 to 0.734523, but raises B-cubed recall from 0.533630 to
0.610115 enough to raise partition F1. This is a real fragmentation/merging
tradeoff. It forbids wording such as “improves boundary detection” or “improves
all tag-accuracy metrics,” but it does not contradict the declared partition-
fidelity hypothesis.

## Required Separate Judgments

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional RQ evidence
next paper decision: Keep Step 0024 as the label-free default and do not change the thesis, four RQs, or story. The orchestrator may port exactly this already-tested scalar reference-calibration path as an optional supervised mode, then route it to WRITE as additional RQ3 partition-fidelity evidence only if the paper explicitly states the annotation advantage and the CodeTrace boundary-F1 tradeoff. Do not claim boundary-detection improvement, literal tag correctness, whole-RQ3 completion, or equal-information superiority, and do not start a second candidate from this review.
```

There is no experiment-validity must-fix. Before canonical promotion, correct
the two wording points above: partial failed invocations did expose OSWorld
results without changing the candidate, and target stage rows were isolated
from the fitter rather than literally never decoded by any subprocess.
