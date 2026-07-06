# Paper Evaluation Rubric R352

R352 maps the existing tracked profiler-evaluation artifacts to an OSDI-style profiling-paper rubric. It is not a new empirical result, does not download or sync datasets, and does not rerun the profiler.

## Verdict

- Overall: pass.
- Rubric level: level_4_scoped_profile_benchmark.
- Checks: 26/26.
- Required checks: 26/26.

## Rubric Checks

| Area | Check | Status | Evidence |
|---|---|---|---|
| claim_evidence_alignment | paper_integrity_gate_passes | pass | R338 passes 350 number checks, 78 source-policy checks, and 16 guardrail checks. |
| claim_evidence_alignment | reviewer_gate_accepts_scoped_claim | pass | R351 records 4/4 ACCEPT, zero blocking issues, and all mechanical checks passing. |
| claim_evidence_alignment | two_abstractions_only | pass | The current evidence and paper text keep only operation and operation stack as profiler abstractions. |
| workload_and_setup | real_labeled_workload_scale | pass | R320 scores 6 tasks over 4 public labeled trace families, 34,539 operations, and 3,699 positives. |
| workload_and_setup | baseline_and_ranker_surface_present | pass | R320 covers flat, fixed-session, dataset-native, raw-action, operation-stack, and oracle drilldown views with 15 visible non-oracle policies and 144 policy scores. |
| workload_and_setup | source_policy_uses_existing_datasets | pass | R320/R333/R331 use existing tracked operation JSONL from four real labeled trace families; no dataset sync or creation is recorded. |
| fidelity_accuracy | localization_metrics_cover_profiler_claim | pass | R344 covers AP/AUPRC-style score, nDCG, P/R/F1@5, budgeted recall/F1, work-to-first-positive, and group fragmentation across 50 comparisons. |
| fidelity_accuracy | hot_groups_recover_real_positives | pass | R350/R346 show top-5 operation-stack packets contain positives on 6/6 tasks, top-1 on 5/6, at median top-5 work 0.0937. |
| fidelity_accuracy | hidden_label_leakage_control | pass | R320 leakage check passes with no overlap between visible rank fields and hidden oracle labels. |
| baseline_tradeoff | operation_stack_beats_flat_on_inspection_work | pass | Operation-stack top-ranked evidence uses less top-5 work than flat summaries on 6/6 tasks. |
| baseline_tradeoff | operation_stack_reduces_fixed_session_fragmentation | pass | Operation-stack beats fixed-session top-5 recall on 5/6 tasks, uses fewer groups on 4/6, and wins fixed-25%-recall group cost on 5/6. |
| baseline_tradeoff | counterpoints_are_preserved | pass | R344 has 16 counterpoint verdicts; R350 keeps baseline counterpoints for 6/6 packets; fixed-session lower-WTFP remains 4/6. |
| actionability | diagnostic_cards_have_concrete_actions | pass | R335/R345/R350 produce concrete optimization actions for all 6 tasks and non-default action packets for 6/6 tasks. |
| actionability | objective_level_knobs_are_not_universal_selector | pass | R341/R348 show 36 objective-level actions with 27 non-default best rows and 25 view changes, while R349 keeps exact action transfer weak at 7/60. |
| actionability | diagnostic_lenses_are_disaggregated | pass | R345 disaggregates 6 diagnostic lenses over 36 objective rows; every task needs at least 3 best views and non-operation-stack views win 25/36 objectives. |
| generality | multiple_trace_families_and_problem_types | pass | The main benchmark spans AgentRewardBench, AgentNet, OSWorld-Human, and SATraj safety traces with six problem tasks. |
| generality | sequence_scope_and_boundary_scope_are_scored | pass | R339 scores sequence/session-scope recall tradeoffs, while R342 confirms 12/12 recursive stack specs are prompt/session-free. |
| mechanism_isolation | recursive_stack_depth_and_mapping_are_isolated | pass | R342 isolates recursive stack depth over 12 specs; coarse depth reduces groups on 6/6 tasks and depth changes the best objective on 3/6, while R335 records both positive and negative mapping effects. |
| mechanism_isolation | query_aware_ranking_and_feature_ablation_are_visible | pass | R335 identifies ranker gains, critical features, and misleading features; R340 selects policies without target hidden labels. |
| mechanism_isolation | negative_control_calibrates_signal | pass | R331 fixes visible group/ranking order and shows operation-stack query-aware AP exceeds the permutation null on 6/6 tasks without rerunning the profiler. |
| robustness_statistics | bootstrap_uncertainty_has_support_and_counterpoints | pass | R330 task-family bootstrap has 10 supported checks and 10 mixed/counterpoint checks, preserving statistical uncertainty. |
| robustness_statistics | heldout_policy_transfer_is_scoped_guardrail | pass | R340/R349 provide held-out visible policy-transfer guardrails: 96 decisions, 62/96 within tolerance in R340, and 35/60 within tolerance but only 7/60 exact action in R349. |
| reproducibility_overhead | profile_spec_cost_and_determinism_are_reported | pass | R327/R328 cover 76 specs and 152 invocations; R328 clean rerun gives 76/76 semantic and raw-byte deterministic outputs. |
| reproducibility_overhead | no_network_or_dataset_sync_in_final_gates | pass | R338/R350/R351 require no network access, use tracked evidence, and do not sync/create/relabel datasets. |
| claim_scope_guardrails | must_not_claim_boundaries_visible | pass | Paper text and R338 visibly exclude human utility, automatic boundary/action selection, single-view dominance, and full ecosystem compatibility claims. |
| claim_scope_guardrails | rubric_claim_is_scoped_profiler_claim | pass | R351 and the paper scope the result as a hidden-label profiler benchmark, not a human/agent analyst study. |

## Residual Risks

| Risk | Status | Handling |
|---|---|---|
| human_or_agent_analyst_utility | not_claimed | R352 is a profiler-output benchmark audit; it does not support analyst accuracy, time, or productivity claims. |
| automatic_intent_boundary_discovery | not_claimed | Recursive stack fields and existing labels are evaluated, but the paper does not claim complete automatic boundary discovery. |
| complete_trace_ecosystem_compatibility | not_claimed | Trace import/export examples remain artifact-level exchange evidence, not full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility. |
| automatic_action_selector | counterpoint_preserved | R349 exact action transfer remains 7/60 and non-default exact action remains 2/42. |
| universal_budget_dominance | counterpoint_preserved | R350 strict 30% work packets hold for 4/6 tasks, so the claim is bounded rather than universal. |
| broader_family_coverage | future_work | The main label-scored claim uses six tasks from four oracle-rich families; broader tool/API/mobile coverage remains optional future generality. |
