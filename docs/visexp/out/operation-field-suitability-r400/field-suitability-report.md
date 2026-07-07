# R400 Field-Derivation Suitability

- Status: `pass`.
- Checks: 5/5.
- This is a synthesis over existing real labeled trace artifacts; it does not sync data or rerun the profiler.

## Decision Rules

| decision_id | knob | use_when | avoid_when | evidence | counterpoint | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | deterministic mapping | the goal is cross-dataset semantic aggregation or stack compression | the task needs fine action-boundary fidelity | Held-out mapping over 3990 operations reduces unique stacks 284->209 and improves compression 14.049->19.091; dataset->task V-measure 0.8374->0.8531. Across 9 held-out datasets / 13265 operations, mapped stacks reduce stack count on 6/9 datasets, never increase it (0 negative), and yield 1162.005 weighted stack reduction per 1k ops. | It deliberately coarsens action labels: action->phase V-measure 0.9343->0.7416 and adjacent phase/action boundary F1 0.9677->0.7774. Mean task/dataset V-measure is unchanged at 0.7778; some datasets are already well structured and do not benefit. | accept_for_compression_caution_for_boundaries |
| D2 | profile-spec stack depth and predicates | the same operation source must be folded into task-specific views | a single default stack is being treated as universally optimal | 12 profile-spec variants compose operation files, predicates, operation rank rules, rule-score ranking, and explicit stack depth; 12/12 are prompt/session-frame free. AP improves versus width in 9/12 variants and first-positive work in 10/12. | Depth is objective-dependent: 3/6 tasks choose different stack depths for AP and first-positive work. | accept_as_query_surface |
| D3 | operation-level rank features | feature ablations identify task-specific positive signals | a feature is known to be misleading for the task family | 7 critical feature rows: Leave-one-feature ablation identifies 7 critical feature rows across safety, looping, side-effect, and step-quality tasks. Examples include success, loop-like, write-action, and failure fields. | 3 misleading feature rows: It also finds 3 misleading feature rows, including OSWorld input-phase and SATraj loop-like cases. | accept_with_ablation_guard |
| D4 | supervised boundary-derived fields | adjacent-boundary labels are available and learned fields beat simple sequence/field baselines | a simple visible field already explains the boundary or the oracle is not an adjacent boundary | 1 accept, 3 caution, and 1 reject decisions across 5 family rows. Boundary backends beat the best simple baseline on 4/5 tested rows; OSWorld-Human R297 reaches F1 0.7735 versus best baseline 0.7090, and R299 also improves AgentNet quality-state boundaries. | 1/5 rows remain counterpoints; AgentRewardBench looping is better explained by repeat_signal_change than the learned backend. | accept_only_after_suitability_check |
| D5 | boundary-derived profile repair | visible phase/action fields fail on human-boundary localization | inspection work is the primary objective and fixed-session is cheaper | On held-out OSWorld-Human, learned-boundary fields improve AP 0.2402->0.2583, reduce groups 108->74, and raise top-5 recall by 0.1111. AP gain 0.0181 and group reduction 34. | Inspection-cost metrics are mixed: top-5 work changes by +0.0813 and first-positive work by +0.1581. Top-5 work delta 0.0813; first-positive work delta 0.1581. | accept_for_ap_and_fragmentation_caution_for_work |

## Boundary-Family Decisions

| candidate | dataset | learned_f1 | best_baseline | best_baseline_f1 | delta_vs_best_baseline_f1 | decision | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| osworld_human_group_r297 | osworld-human | 0.7735 | always_boundary | 0.709 | 0.0645 | accept | learned fields beat always_boundary by 0.0645 F1 with high absolute F1 |
| osworld_human_group | osworld-human | 0.6916 | always_boundary | 0.6706 | 0.021 | caution | learned fields beat always_boundary by 0.021 F1, but the margin or absolute F1 is modest |
| agentnet_step_correct | agentnet | 0.3197 | always_boundary | 0.2155 | 0.1042 | caution | learned fields beat always_boundary by 0.1042 F1, but the margin or absolute F1 is modest |
| agentnet_step_redundant | agentnet | 0.3361 | always_boundary | 0.2645 | 0.0716 | caution | learned fields beat always_boundary by 0.0716 F1, but the margin or absolute F1 is modest |
| agentreward_looping | agentrewardbench | 0.7833 | repeat_signal_change | 1 | -0.2167 | reject | simple baseline repeat_signal_change is stronger by 0.2167 F1 |

## Checks

| check | status | evidence |
| --- | --- | --- |
| decision_rules_cover_profile_knobs | pass | rules=['boundary-derived profile repair', 'deterministic mapping', 'operation-level rank features', 'profile-spec stack depth and predicates', 'supervised boundary-derived fields'] |
| family_decisions_include_counterpoints | pass | family decisions={'accept': 1, 'caution': 3, 'reject': 1} |
| actionability_is_configuration_not_selector | pass | Rules choose profile knobs and guardrails rather than a label-free automatic selector. |
| two_abstractions_only | pass | All decisions derive operation fields or choose operation-stack queries; no third profiler object is introduced. |
| no_new_data_or_profiler_rerun | pass | The script reads tracked R325/R358/R366 artifacts only. |
