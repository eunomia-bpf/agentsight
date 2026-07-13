# AgentNet reciprocal-transfer REAL PREFLIGHT report

**Completed:** 2026-07-13T03:51:57-07:00  
**Stage:** REAL PREFLIGHT  
**Execution status:** `VALID`  
**Scientific verdict:** `NOT_EVALUATED_PREFLIGHT`

## Purpose and boundary

This run exercised the complete approved pipeline on a fixed small subset to
find schema, label-separation, model, AgentProf, metric, bootstrap, and runtime
bugs before the complete population. It cannot support, contradict, tune, or
narrow the tested hypothesis. The generated base metrics are retained in the
ignored machine outputs for execution audit only and are not interpreted here.

## Command

```bash
python3 script/agentnet_cross_platform_eval.py preflight \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/preflight \
  --bootstraps 200 --max-bootstrap-attempts 1000 --seed 4204 \
  --tasks-per-platform 256
```

Selection uses the lexically first 256 original task IDs per platform. Every
released trajectory row for a selected task remains included.

## Population exercised

| Held-out fold | Tasks | Trajectories | Operations | Positives | Negatives | Unresolved | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Windows → Darwin | 256 | 261 | 4,844 | 907 | 3,937 | 0 | 100% |
| Darwin → Windows | 256 | 256 | 3,608 | 662 | 2,946 | 0 | 100% |

The five extra Darwin trajectories belong to selected repeated task IDs. Their
presence with an unchanged task count demonstrates that the reviewed
released-row/task-cluster semantics is active in the real path.

## Predictor boundary and convergence

| Predictor | Reference operations | Target operations | Target tasks / trajectories | Iterations / cap | Target-label input |
|---|---:|---:|---:|---:|---|
| Windows → Darwin | 3,608 | 4,844 | 256 / 261 | 5 / 1,000 | none |
| Darwin → Windows | 4,844 | 3,608 | 256 / 256 | 5 / 1,000 | none |

Both reference populations had complete labels and both classes. Each predictor
received only `projection.jsonl`, its reference-platform label file, fixed
platform names, settings, and output directory. The predictor parser has no
target-label argument. Both models converged without feature or threshold
changes.

The model reports list exactly the approved four pure source helpers and record
`legacy_normalize_agentnet_used=false` and `target_label_input=null`.

## Real AgentProf checks

AgentProf reported exactly `agentpprof 0.2.37` in both folds.

| Held-out platform | View | Groups | Operations reconstructed | Exact source counter |
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

For each view, the scorer independently reconstructed every group key,
operation count, full-precision predicted-risk sum, and density. Total risk
matched saved predictions within the declared floating-point tolerance.

## Bootstrap path

Each label-blind predictor saved all 1,000 deterministic attempt specifications
before target scoring. Each scorer processed 512 specifications in fixed
batches and retained the first 200 valid paired task-cluster draws. Both folds
finished with exactly 200 valid draws. No scorer called the predictor or
appended a draw.

The Darwin draw header contains 256 original task IDs even though the target has
261 trajectories. Therefore the two trajectories of a repeated task share one
bootstrap multiplicity as approved.

## Label-blind artifact invariance

Before target scoring, each fold saved predictions, group assignments, group
summaries, model/profile reports, and all draw specifications. After scoring,
the coordinator recomputed all six SHA-256 values per fold and found them
unchanged.

The dedicated regression suite also runs the same boundary through correct,
alternate same-platform, wrong-platform, and withheld label inputs. Scoring may
change or fail, but predictions, groups, profiles, and draw specifications
remain byte-identical. The current suite passes 10/10 tests with real AgentProf.

## Secondary-output sanity

The preflight produced the required base-only diagnostics: density-ranked group
counts and groups-to-50, sessions per hot group, annotation/domain coverage,
eligible domain slices, and additive-mass group-opening counts. Additive mass
contains no operation AP, recall@30, or work-to-50 and does not enter bootstrap
or verdict logic.

## Completion judgment

All approved preflight obligations passed:

- official prepared source could be read without sampling or collision;
- the repeated-task schema behaved as reviewed;
- target labels were unavailable to predictors;
- fixed models converged;
- real AgentProf counts and group keys were exact;
- full-precision risk mass was conserved;
- all draws existed before target scoring;
- the first required valid task draws completed; and
- preflight emitted no scientific judgment.

## Next transition requested

An independent `research-experiment-design` review must recompute these
execution checks and decide whether the implementation may run the entire
333,005-operation, 17,625-trajectory population with 10,000 valid draws per
fold. No paper or story change is authorized by this report.
