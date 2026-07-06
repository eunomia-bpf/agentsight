# R364 Core Experiment Sufficiency Audit

- Status: `pass`.
- Checks: 15/15.
- Core experiments: 4.

## Sufficiency Matrix

| Experiment | Primary experiment | Success criterion | Claim gate |
|---|---|---|---|
| RQ1/E1: generality, recursive folding, and field derivation | R286 recursive stack-depth sweep, with R342 profile-spec composition, R353 trace exchange, and R366 field-derivation synthesis as support. | The same operation input folds across depths (9->3757 stacks), profile specs stay prompt/session-free (12/12), standard-trace import/export preserves 512 samples and 11 stacks, and R366 records 6 mechanism rows plus 5 boundary-family rows without adding a new profiler object. | Supported as operation/operation-stack coverage and configurability, not a new trace ecosystem compatibility claim. |
| RQ2/E2: hidden-label localization and ranking | R320 hidden-label profile accuracy, with R333/R334/R355 budget, fragmentation, and oracle-depth slices. | Operation-stack task-query ranking uses 0.0937 top-5 work vs 1.0 flat, beats fixed-session drilldown top-5 recall on 5/6 tasks, reduces median groups from 285.0 to 157.5, and beats fixed-session budget-30 unit recall on 20/24 oracle-depth rows. | Supported as a hidden-label profiler benchmark with baseline tradeoffs, not human utility. |
| RQ3/E3: mechanism and actionability | R354 executable profile-spec patches, with R358 boundary-derived-field ablation for the OSWorld-Human rejection. | R354 accepts 5/6 patches with median AP delta 0.0376 and top-5 lift delta 0.5750; R358 improves held-out OSWorld-Human AP from 0.2402 to 0.2583 and groups from 108 to 74 using supervised boundary-derived fields as visible operation fields; R366 folds 7 critical and 3 misleading feature rows into the same E3 mechanism story. | Supported as actionable profile-spec and field/ranker guidance, not an automatic selector or boundary detector. |
| RQ4/E4: replayability, offline cost, and artifact hygiene | R328 deterministic replay over 76 tracked profile specs; R338/R352/R356/R357/R359/R360/R361/R363 remain artifact-hygiene and paper-structure gates, not hidden-label accuracy results. | R328 records 76/76 semantic deterministic specs and 76/76 raw-byte deterministic specs over 152 invocations, with median runtime 1.601s and p95 2.767s. | Supported as systems/reproducibility evidence, not a hidden-label accuracy result, live overhead, human productivity, or trace-ecosystem compatibility. |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `three_empirical_plus_one_reproducibility_block` | pass | Exactly RQ1/E1-RQ4/E4 are represented, RQ1/E1-RQ3/E3 are empirical profiling blocks, RQ4/E4 is replayability/overhead/artifact hygiene, and no paper-facing E5/RQ5 is present. |
| `required_sufficiency_fields_complete` | pass | Every core experiment row has primary experiment, oracle, baselines, metrics, success criterion, failure interpretation, scope, target, and sources. |
| `primary_experiments_are_substantial` | pass | Primary experiments are named for all RQ1/E1-RQ4/E4 and are not chronological run lists. |
| `baseline_and_metric_surface_covers_main_claim` | pass | E2 includes the required baselines and localization/ranking metrics. |
| `fixed_session_baseline_scope` | pass | The evaluated baseline is fixed-session drilldown; real span-tree imports remain future work. |
| `query_aware_is_task_query_tuning_surface` | pass | Query-aware policies are scoped as task-query tuning heuristics rather than a universal label-free ranker. |
| `boundary_backend_is_supervised_ablation` | pass | R358/R366 are scoped to supervised held-out boundary-derived fields and suitability checks, not automatic boundary discovery. |
| `actionability_has_executable_and_boundary_mechanisms` | pass | E3 includes executable profile-spec patches, OSWorld-Human boundary-field ablation, and field/ranker mechanism counterpoints. |
| `field_derivation_is_internal_to_e1_e3` | pass | R366 field-derivation evidence is represented inside E1/E3, with no fifth paper-facing experiment. |
| `negative_results_preserved` | pass | Metric, action-transfer, and boundary-field counterpoints remain visible. |
| `visual_targets_are_not_flamegraph_only` | pass | R363 provides five non-flamegraph-only paper views for E2/E3 plus oracle depth. |
| `upstream_gates_pass` | pass | R360/R361/R363 pass, R352 is level_4, and R357 has 4/4 accepts with 0 blockers. |
| `self_audits_are_artifact_hygiene_not_empirical_evidence` | pass | R338/R352/R356/R357/R359/R360/R363 are treated as artifact and claim-hygiene gates, not empirical profiler accuracy evidence. |
| `two_abstraction_and_source_policy_preserved` | pass | Operation/operation-stack remain the only profiler abstractions, and the no-new-data policy is visible. |
| `tracked_source_artifacts_available` | pass | All source artifacts are tracked; current paper/docs may be dirty while this audit is being generated. |

## Non-Claims

- This is not a new empirical result.
- This is not a human or agent analyst study.
- This does not fetch, sync, create, or relabel datasets.
- This does not add a fifth core experiment.
