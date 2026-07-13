# AgentNet REAL PREFLIGHT rerun after emitted-key repair

**Completed:** 2026-07-13T04:02:30-07:00  
**Recorded:** 2026-07-13T04:04:43-07:00  
**Stage:** REAL PREFLIGHT  
**Execution status:** `VALID`  
**Scientific verdict:** `NOT_EVALUATED_PREFLIGHT`

## Why this rerun was required

The first FULL attempt stopped before target scoring because one raw-action
stack key differed from AgentProf's public emitted representation. AgentProf
0.2.37 trims a trailing underscore when it makes a pprof-safe frame value, so
three operations whose source target was `backspace_` were emitted under
`backspace-`. Expected and observed operation counts were already identical;
only this public key encoding differed.

The narrow repair added `agentprof_frame_value` and applies it only when the
evaluation reconstructs visible AgentProf stack keys. It does not change the
source projection, predictor features, model, target labels, views, baselines,
metrics, bootstrap, hypothesis, RQ, paper, or story. The repair was exercised
on both complete label-blind target populations before this rerun and was
independently reviewed as a faithful mirror of AgentProf's emitted frame
encoding.

Because REAL PREFLIGHT is the approved transition immediately before FULL, it
was rerun from the complete fixed command after this repair rather than relying
only on synthetic or population-counter checks.

## Exact command

```bash
python3 script/agentnet_cross_platform_eval.py preflight \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/preflight \
  --bootstraps 200 --max-bootstrap-attempts 1000 --seed 4204 \
  --tasks-per-platform 256
```

The command completed at `2026-07-13T04:02:30-07:00`. It replaced the ignored
preflight machine-output directory and exercised the repaired emitted-key path
through prediction, five real AgentProf profiles, independent reconstruction,
draw generation, and target scoring.

## Fixed populations exercised

Selection remained the lexically first 256 original task IDs per platform.
Every released trajectory row belonging to those tasks remained present.

| Reciprocal fold | Reference operations | Target tasks | Target trajectories | Target operations | Positives | Negatives | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Windows → Darwin | 3,608 | 256 | 261 | 4,844 | 907 | 3,937 | 0 |
| Darwin → Windows | 4,844 | 256 | 256 | 3,608 | 662 | 2,946 | 0 |

The five additional Darwin trajectories still belong to repeated released
rows for selected original task IDs. Task IDs, not synthetic trajectory IDs,
remain the bootstrap clusters.

## Predictor and target-label boundary

Both fixed logistic-regression predictors converged in 5 iterations under the
1,000-iteration cap. Each model report records `target_label_input=null`,
`legacy_normalize_agentnet_used=false`, seed 4204, and exactly the four approved
source helpers:

- `agentnet_code_action`;
- `agentnet_action_target`;
- `agentnet_action_phase`; and
- `repeat_features_for_signatures`.

The Windows predictor used only the visible projection and Windows labels
before predicting Darwin. The Darwin predictor analogously used only the
visible projection and Darwin labels before predicting Windows.

## Repaired real-AgentProf reconstruction

Both folds report exactly `agentpprof 0.2.37`. Every reconstructed view is
exact and conserves every operation:

| Target | View | Groups | Operations | Exact |
|---|---|---:|---:|---|
| Darwin | flat | 1 | 4,844 | yes |
| Darwin | fixed session | 261 | 4,844 | yes |
| Darwin | source native | 1,047 | 4,844 | yes |
| Darwin | raw action | 547 | 4,844 | yes |
| Darwin | semantic | 739 | 4,844 | yes |
| Windows | flat | 1 | 3,608 | yes |
| Windows | fixed session | 256 | 3,608 | yes |
| Windows | source native | 1,092 | 3,608 | yes |
| Windows | raw action | 551 | 3,608 | yes |
| Windows | semantic | 729 | 3,608 | yes |

The scorer independently reconstructed group keys and risk density from the
saved predictions. `agentprof_count_conservation=true` for both targets, and
the total full-precision risk mass differs across reconstructed views only by
floating-point summation order (at approximately `2e-12`). The trailing-
underscore regression is included in the dedicated test suite.

## Bootstrap and output separation

Each label-blind fold wrote all 1,000 deterministic task-cluster attempt
specifications before target scoring. Each scorer examined the first fixed
512-specification batch and retained exactly the first 200 valid paired draws.
No scorer regenerated predictions, profiles, groups, or draws.

The coordinator recomputed the six label-blind artifact digests for each fold
after scoring. All 12 artifacts were unchanged, including predictions, group
assignments, group summaries, model and profile reports, and the pre-saved
draw file.

Top-level status remains:

```text
status=VALID
scientific_verdict=NOT_EVALUATED_PREFLIGHT
tested_hypothesis_only=false
```

The ignored machine report includes base metric values because the complete
pipeline was exercised. Their sign and magnitude are deliberately not used in
this execution judgment and cannot support, contradict, tune, or narrow the
tested hypothesis.

## Regression verification

After the rerun:

```text
python3 -m unittest script/test_agentnet_cross_platform_eval.py
Ran 11 tests in 3.427s
OK
```

The suite includes the repaired trailing-underscore case, real AgentProf
execution, and alternate, wrong-platform, and withheld-target-label boundary
checks.

## Transition request

This report requests a fresh independent `research-experiment-design` review
of the repaired REAL PREFLIGHT. Only that review may authorize restarting FULL
on all 17,625 released trajectories / 339,005 operations, with exactly 10,000
valid task-cluster draws per fold, a 50,000-attempt cap, and seed 4204. This
report authorizes no paper or story change.

The operation total was corrected during independent read-back from the
unchanged platform counts (`239,710 + 99,295`) before FULL authorization.
