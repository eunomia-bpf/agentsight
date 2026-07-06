# R360 Paper Core Result Tables

- Status: `pass`.
- Checks: 7/7.
- This is a table-consolidation gate, not a new empirical result.

## Core Table

| Core experiment | Workload | Key evidence | Scoped conclusion |
|---|---|---|---|
| E1: coverage, recursive folding, and field derivation | 15 public labeled trace families / 47,590 operations, plus local-session and standard-trace exchange fixtures. | recursive_depth_sweep_operations=13265 (R286); stack_depths_and_unique_stack_range=8 depths, 9->3757 stacks (R286); leave_dataset_out_positive_stack_reductions=6/9 (R285); prompt_session_free_profile_specs=12/12 (R342); real_operation_standard_trace_roundtrip=512 ops, 512 samples, 11 stacks, equal=True (R353) | Supported as operation/operation-stack coverage and configurability, not a new trace ecosystem compatibility claim. |
| E2: hidden-label localization and ranking | Six oracle-backed tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human. | labeled_profile_benchmark_scale=6 tasks / 4 datasets / 34539 ops / 3699 positives / 144 policy scores (R320); top5_inspection_work=0.0937 vs 1 (R320); top5_recall_wins_vs_fixed_session=5/6 (R320); median_group_fragmentation=157.5 vs 285 (R320); budget30_recall_wins_vs_flat=6/6 (R320); oracle_depth_unit_recall=0.4342; 20/24 rows beat fixed-session (R355) | Supported as a hidden-label profiler benchmark with baseline tradeoffs, not human utility. |
| E3: mechanism and actionability | The same six labeled tasks plus held-out OSWorld-Human boundary-backend operations. | profile_spec_patch_acceptance=5/6 (R354); patch_median_delta_ap_top5_lift_wtfp=0.0376 AP, 0.575 lift, -0.0859 first-positive work (R354); recursive_depth_actionability=9/12 AP variants, 6/6 tasks reduce groups (R342); boundary_field_patch=AP 0.2583 vs 0.2402; groups 74 vs 108 (R358); boundary_counterpoint=top5 work +0.0813; first-positive work +0.1581 (R358) | Supported as actionable profile-spec and field/ranker guidance, not an automatic selector or boundary detector. |
| E4: reproducibility and offline cost | 76 tracked profile specs over tracked operation JSONL inputs. | deterministic_profile_specs=76/76 semantic, 76/76 raw-byte, 152 invocations (R328); offline_runtime=median 1.6011s, p95 2.7672s (R328) | Supported as replayable offline profiling artifact evidence, not live overhead, human productivity, or trace-ecosystem compatibility. |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `four_core_experiment_rows` | pass | 4 generated rows. |
| `real_labeled_profile_scale_preserved` | pass | R320 scale tokens match the labeled profiler benchmark. |
| `baseline_tradeoff_tokens_present` | pass | R320 flat/fixed-session comparison tokens are present. |
| `actionability_tokens_present` | pass | R354/R358 actionability and boundary-field tokens are present. |
| `artifact_hygiene_gates_available` | pass | R338/R352/R357/R359 remain artifact-hygiene gates, not main empirical evidence. |
| `two_abstractions_and_nonclaims_visible` | pass | Current paper/docs preserve abstraction and must-not-claim text. |
| `fixed_session_baseline_scope_visible` | pass | Current paper/docs use fixed-session drilldown as the evaluated baseline and leave real span-tree imports for future ecosystem baselines. |
