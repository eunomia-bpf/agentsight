# Experiment Result: Existing-Trajectory Reference Calibration

**Completed:** 2026-07-15
**Run status before independent review:** complete; validity pending review
**Tested hypothesis before independent review:** supported by root summary
**Scientific role:** supporting RQ3 algorithm evidence

## Tested Hypothesis

The experiment tested whether one scalar cutoff selected by
operation-weighted B-cubed F1 on reference-only group annotations improves the
current Step 0024 action-transition NPMI recurrence constructor on both
complete target populations, without changing the NPMI score, visible action
input, unseen-transition rule, or segment construction.

The exact paper thesis, four RQs, story, and contributions were not tested or
changed by this local mechanism experiment.

## Complete Command

```bash
python3 script/rq3_reference_calibrated_existing_traces_eval.py \
  --mode full \
  --out .agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full
```

## Complete Population

| Population | Score reference | Calibration annotations | Target |
|---|---:|---:|---:|
| OSWorld-Human | four other folds per target fold | four other folds per target fold | 287 sessions / 3,978 operations / 3,691 pairs / 2,042 groups |
| CodeTraceBench | 2,229 sessions / 87,703 operations | 483 solved sessions / 18,152 operations / 2,886 stages | 405 failed sessions / 20,866 operations / 20,461 pairs / 2,948 stages |

Every OSWorld session was a target exactly once. CodeTrace target IDs were
absent from the score reference and calibration subset. For OSWorld, target
predictions were persisted before the corresponding target annotation loader
ran. For CodeTrace, an isolated extractor decoded the broad manifest but
returned only the explicitly selected rows: failed-target stage rows were
unavailable to the fitting/prediction process, and the selected failed-target
rows were extracted only after target predictions were persisted.

## Primary Result

| Population | Current Step 0024 B-cubed F1 | Reference-calibrated B-cubed F1 | Delta |
|---|---:|---:|---:|
| OSWorld-Human | 0.786169543748 | 0.801087216271 | +0.014917672522 |
| CodeTraceBench | 0.649173103932 | 0.666563572806 | +0.017390468874 |

Under the fixed plan, strict improvement on both complete populations is the
`supported` relation. This classification remains provisional until a fresh
reviewer recomputes the raw results and audits isolation.

### OSWorld-Human diagnostics

| Method | B-cubed precision | B-cubed recall | B-cubed F1 | Boundary F1 | Predicted groups |
|---|---:|---:|---:|---:|---:|
| Current Step 0024 | 0.855872 | 0.726966 | 0.786170 | 0.679922 | 2,656 |
| Reference-calibrated | 0.917000 | 0.711190 | 0.801087 | 0.733953 | 2,941 |

The candidate improves partition precision and boundary F1 while reducing
partition recall slightly. It is an optional supervised calibration mode, not
an equal-information-budget replacement for the label-free default.

### CodeTraceBench diagnostics

| Method | B-cubed precision | B-cubed recall | B-cubed F1 | Boundary F1 | Predicted groups |
|---|---:|---:|---:|---:|---:|
| Current Step 0024 | 0.828579 | 0.533630 | 0.649173 | 0.287106 | 6,897 |
| Reference-calibrated | 0.734523 | 0.610115 | 0.666564 | 0.236176 | 5,331 |

Here the same scalar improves partition recall enough to raise B-cubed F1,
while reducing partition precision and adjacent-boundary F1. The planned
primary effect is partition fidelity; boundary F1 is a diagnostic and does not
invalidate the partition claim. This tradeoff must remain explicit.

The candidate's CodeTrace B-cubed F1 by framework is:

| Framework | Sessions | Candidate B-cubed F1 |
|---|---:|---:|
| OpenHands | 213 | 0.677986 |
| SWE-agent | 28 | 0.689245 |
| Terminus2 | 93 | 0.629515 |
| mini-SWE-agent | 71 | 0.689372 |

These framework rows are diagnostics; the plan's verdict is based on the
complete population and does not require every framework to beat its local
baseline.

## Execution Deviations And Repairs

The first complete invocation finished and persisted all five OSWorld folds,
then exited 139 before any CodeTrace target prediction. The failure occurred in
the native Parquet stage-filter path. Replacing the large filtered read with an
isolated `multiprocessing` extraction produced the exact 483 calibration rows,
but the second complete invocation again exited 139 during the Arrow/process
runtime handoff and still wrote no CodeTrace target prediction or target
metric.

The final execution-only repair replaced `multiprocessing` with a normal,
separate Python subprocess that reads the manifest, writes only the explicitly
selected stage rows, and terminates. The parent checks the exact selected IDs
before using that file. Calibration extraction happens before fitting; failed-
target extraction is invoked only after all target predictions are persisted.
An independent implementation reviewer checked this repair and found no
remaining must-fix. The successful complete invocation used the unchanged
algorithm, cutoff candidates, tie rule, sources, target population, metrics,
and verdict.

The failed full invocations exposed the already-fixed complete OSWorld result
before stopping, but no partial result changed the candidate, plan, or
interpretation, and no failed invocation produced a CodeTrace target metric.
The final successful invocation recomputed all five OSWorld folds and the
complete CodeTrace population from the fixed inputs.

## Raw Evidence

Root:

```text
.agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full/
```

It contains:

- five OSWorld fold prediction files totaling 3,691 decisions;
- 3,691 pooled OSWorld pair rows and 3,978 operation assignments;
- 20,461 CodeTrace target predictions and pair rows;
- 20,866 CodeTrace operation assignments;
- exact selected calibration/target manifest rows and their selected-ID lists;
- calibration reports, per-fold/per-framework metrics, the pooled summary, and
  the generated Markdown report.

## Provisional Scientific Interpretation

The result supports a narrow but useful improvement to the existing algorithm:
when independently grouped historical trajectories are available, the same
NPMI recurrence score can use one reference-fitted cutoff to improve complete-
population operation partition fidelity on both reused real workloads. This
does not replace the zero-annotation mode, establish literal tag names, answer
all of RQ3, or authorize a new story. It is a reason to consider porting this
single optional calibration path into `agentpprof` after independent result
review, rather than inventing another constructor or collecting another
dataset.

No paper, product, skill, canonical idea/user document, or read-only submodule
was changed during this experiment.
