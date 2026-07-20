# Complete Run — Multi-Resolution Recurrence

**Completed:** 2026-07-19  
**Execution status:** VALID / COMPLETE  
**Root reading of registered result:** SUPPORTED, pending independent raw-result
reconstruction

## Unchanged Execution

The exact implementation that passed REAL PREFLIGHT ran once on both approved
complete populations. No code, field, cutoff, population, baseline, metric,
bootstrap unit, or interpretation changed between preflight and full execution.

## OSWorld-Human — Five-Fold Rust Fallback

The existing Rust/Python equivalence evaluator routed all five detail-free
session folds through the modified release constructor. This is the
implementation review's required Rust evidence route; the Python-only score
path was not used to claim fallback.

- 287 sessions;
- 3,978 operations;
- 3,691 adjacent boundary decisions;
- 2,042 official human groups;
- 3,691/3,691 Rust decisions equal to the approved Step 0024 Python reference;
- all NPMI scores and cutoffs equal within `1e-12`;
- 2,656/2,656 segments and all 3,978 motif assignments equal;
- 3,978 units of profile mass conserved;
- detail-free inputs contain only `session` and `action`;
- no detail model appears in the Rust output.

Exact decision identity preserves the registered Step 0024 OSWorld metrics:
ordinary B-cubed F1 `0.786170` and exact boundary F1 `0.679922`. This is a
fallback validity result, not a second performance gain.

Raw root:
`.agentsight/experiments/rq3-multiresolution-recurrence-v1/full/osworld-equivalence/`.

## CodeTraceBench — Complete Existing Population

The modified release constructor learned both resolutions from the same 2,229
target-disjoint reference sessions / 87,703 operations and predicted all 405
existing source-valid failed targets before official stages loaded.

Complete target coverage:

- 405 sessions from four agent frameworks;
- 251 distinct tasks;
- 20,866 operations;
- 20,461 adjacent decisions;
- 2,948 complete official stages;
- every operation assigned once, every edge scored once, and all mass
  conserved.

### Standard Ordinary B-cubed Partition Metric

| Method | Precision | Recall | F1 | Predicted groups |
|---|---:|---:|---:|---:|
| Multi-resolution recurrence | 0.782026 | 0.575029 | **0.662740** | 6,018 |
| Current coarse recurrence | 0.828579 | 0.533630 | 0.649173 | 6,897 |
| Phase-change control | 0.685564 | 0.626030 | 0.654445 | 5,980 |
| Raw-action-key change | 0.891296 | 0.388437 | 0.541070 | 12,231 |

Candidate minus current is `+0.013567` B-cubed F1. The predeclared paired
task-cluster bootstrap over all 251 tasks gives:

- 10,000 deterministic resamples;
- mean delta `+0.013507`;
- median delta `+0.013527`;
- 95% interval `[+0.008712,+0.018043]`;
- positive fraction `1.000`.

The candidate improves over current in all four frameworks:

| Framework | Current F1 | Candidate F1 | Delta |
|---|---:|---:|---:|
| OpenHands | 0.661593 | 0.676295 | +0.014702 |
| SWE-agent | 0.707955 | 0.708893 | +0.000938 |
| Terminus2 | 0.593876 | 0.605471 | +0.011595 |
| mini-SWE-agent | 0.683439 | 0.691523 | +0.008084 |

### Mechanism and Boundary Diagnostic

The detailed resolution observes 18,082 target transitions and backs off on
2,379 unseen transitions. It rescues 879 coarse boundaries and adds zero. The
predicted partition therefore moves from 6,897 to 6,018 groups, closer to the
2,948 official stages.

Exact adjacent-boundary F1 is diagnostic rather than the registered partition
primary: it changes from `0.287106` to `0.265571` as recall falls from
`0.510028` to `0.425875`. The same candidate remains above raw-action-key
change (`0.257220`) and phase change (`0.225425`) on boundary F1. This records
the expected partition-granularity tradeoff and does not replace the standard
B-cubed decision rule.

Raw root:
`.agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/`,
including input JSONL, command, stdout/stderr, profile, 20,461 pair decisions,
20,866 assignments, summary, report, and all 10,000 bootstrap deltas.

## Registered Root Disposition

All validity properties pass. CodeTrace ordinary B-cubed is higher and its
paired task-cluster interval is wholly positive. OSWorld is exactly identical
through the modified Rust constructor. Therefore the complete outcome reaches
the plan's **SUPPORTED** branch, subject to a fresh reviewer independently
reconstructing the raw result and confirming that no material framework
heterogeneity invalidates the interpretation.

If independent review passes, the mechanism may replace the release
constructor and only its directly owned design, implementation, evaluation,
algorithm-history, and active-paper text may enter WRITE. The result cannot
change the thesis, four RQs, positive paper-level RQ3 hypothesis, contribution,
or original AgentProf story.
