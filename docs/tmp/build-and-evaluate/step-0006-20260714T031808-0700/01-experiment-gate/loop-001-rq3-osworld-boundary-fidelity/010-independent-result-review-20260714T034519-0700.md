# RQ3 Independent Result Review

## Node record

- Reviewed: 2026-07-14T03:45:19-07:00
- Reviewer: independent subagent using `research-experiment-design`
- Inputs: approved plan 005, runner, full raw artifacts, and result report 009
- Run status: **valid**
- Tested-hypothesis verdict: **supported**
- Research value: **supporting RQ evidence**
- Overall verdict: **PASS**
- Must-fix items: none

## Independent boundary recomputation

The reviewer read all 3,691 unique rows from `oof-predictions.jsonl` and
recomputed confusion counts and metrics without trusting `summary.json`.

| Method | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Learned | 1,373 | 589 | 382 | 1,347 | 0.699796 | 0.782336 | **0.738768** |
| Always boundary | 1,755 | 1,936 | 0 | 0 | 0.475481 | 1.000000 | 0.644510 |
| Action change | 1,098 | 1,750 | 657 | 186 | 0.385534 | 0.625641 | 0.477080 |
| Phase change | 471 | 597 | 1,284 | 1,339 | 0.441011 | 0.268376 | 0.333688 |

The learned tagger's absolute F1 gain over the strongest simple control is
0.094258. The full-run report's counts and displayed metrics are correct.

Independent fold recomputation gives learned versus always-boundary F1 of
0.814947 vs 0.697674, 0.729685 vs 0.619217, 0.691071 vs 0.663158,
0.749254 vs 0.675926, and 0.750656 vs 0.572202. The learned method wins in all
five folds.

## Independent B-cubed recomputation

The reviewer joined the 3,978 learned-group operation rows back to the source
human groups by session and turn. The learned partition came from the raw
predicted field; action-change and phase-change groups were independently
reconstructed from adjacent source fields. No partition value from the summary
was used in the computation.

| Method | Groups | Precision | Recall | B-cubed F1 | Distortion |
|---|---:|---:|---:|---:|---:|
| Learned | 2,249 | 0.835863 | 0.797096 | **0.816019** | 0.183981 |
| Always boundary | 3,978 | 1.000000 | 0.513323 | 0.678405 | 0.321595 |
| Phase change | 1,355 | 0.565077 | 0.809217 | 0.665461 | 0.334539 |
| Action change | 3,135 | 0.818318 | 0.551852 | 0.659174 | 0.340826 |

Every method covers 3,978 unit-weight items and the same 2,042 oracle groups.
The learned partition's absolute gain over the strongest simple control is
0.137614 B-cubed F1.

## Coverage and leakage audit

- independently reconstructed population: 287 sessions, 3,978 operations,
  3,691 pairs, and 2,042 human groups;
- 3,691 OOF rows have 3,691 unique session/current-line keys and exactly match
  the eligible adjacent pairs;
- pair labels and all three controls match the source with zero errors;
- the five fold files match the corresponding OOF rows exactly;
- independent SHA-256 fold counts are 45, 55, 60, 62, and 65 sessions;
- the folds are mutually exclusive and cover all 287 sessions;
- train/test session overlap is zero in every fold;
- independently replaying the fixed model yields zero prediction mismatches;
- recorded thresholds differ from replay only by at most floating-point
  roundoff of 4.3e-13;
- the runner feature list contains no oracle, group, or learned field;
- learned operation visible fields, values, and group boundaries match their
  source and OOF rows with zero mismatches.

## Current-profiler audit

- input rows and independently summed input mass: 3,978 / 3,978;
- profile stack entries and independently summed output mass: 2,249 / 3,978;
- stdout status, samples, and unique stacks: `ok`, 3,978, and 2,249;
- the complete raw stack-to-weight map equals an independent aggregation of the
  learned-group operation rows;
- stderr is empty;
- binary, command, stack, and release version 0.2.37 match the plan.

## Decision and paper boundary

Both predeclared conditions strictly beat their strongest simple control, so
the joint `SUPPORTED` verdict is correct. The evidence may be written into the
paper only as supervised, held-out task-instance boundary fidelity and grouped
operation-count preservation on OSWorld-Human. It does not alone support an
unsupervised detector, cross-family generalization, or the complete task,
phase, and action portions of RQ3.
