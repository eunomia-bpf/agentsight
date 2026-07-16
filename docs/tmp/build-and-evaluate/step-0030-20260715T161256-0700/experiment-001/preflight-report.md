# Real Preflight Report

**Experiment:** existing-trajectory reference calibration
**Completed:** 2026-07-15
**Decision:** **GO — execute the unchanged complete run**
**Scientific hypothesis evaluated:** no

## Command

```bash
python3 script/rq3_reference_calibrated_existing_traces_eval.py \
  --mode preflight \
  --out .agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/preflight
```

The first terminal invocation emitted only the environment's existing pandas /
`bottleneck` version warning and left the completed OSWorld files visible when
the root immediately inspected the output root. The root reran the exact same
command without changing the plan, script, input, cutoff rule, metric, or
output path. That invocation returned status 0, printed the valid preflight
summary, and completed both real-data paths. This spends the second and final
preflight attempt; no further preflight retry is authorized or necessary.

## Real Paths Exercised

### OSWorld-Human fold 0

- full four-fold reference/calibration path;
- 45 target sessions, 521 operations, and 476 adjacent target pairs;
- one persisted prediction for every target pair;
- target oracle loading only after `fold-0-predictions.jsonl` exists;
- 521 scored operation assignments and 300 target oracle groups.

### CodeTraceBench first complete target

- complete 2,229-session / 87,703-operation score reference;
- complete 483-session / 18,152-operation / 2,886-stage solved calibration
  subset;
- one real failed target with 47 operations, 46 pairs, and 10 complete official
  stages;
- target predictions persisted before failed-target stage loading;
- complete pair and operation assignment coverage.

## Checks

- The run used only already-normalized trajectories and the existing verified
  manifest.
- The one NPMI score and one reference-fitted scalar cutoff executed end to
  end.
- The registered population assertions passed.
- Prediction-before-target-oracle ordering passed on both sources.
- Every selected pair and operation was written exactly once.
- No product, paper, skill, canonical idea/user document, or submodule changed.
- The displayed preflight B-cubed values are diagnostics only and did not
  change the candidate, command, completion rule, or expected interpretation.

## Return

The approved real data, fitting, persistence, and scoring paths are executable.
Proceed once to the complete five-fold OSWorld-Human and 405-target
CodeTraceBench run. A partial prefix cannot count as the result.
