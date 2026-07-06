# R366 Operation-Field Derivation Mechanism Audit

- Status: `pass`.
- Checks: 6/6.
- This is not a new dataset, profiler rerun, or human/agent analyst result.

## Mechanism Rows

| Row | Block | Mechanism | Evidence | Counterpoint |
|---|---|---|---|---|
| M1 | E1 | deterministic operation-field mapping | Held-out mapping over 3990 operations reduces unique stacks 284->209 and improves compression 14.049->19.091; dataset->task V-measure 0.8374->0.8531. | It deliberately coarsens action labels: action->phase V-measure 0.9343->0.7416 and adjacent phase/action boundary F1 0.9677->0.7774. |
| M2 | E1 | leave-dataset-out mapping generalization | Across 9 held-out datasets / 13265 operations, mapped stacks reduce stack count on 6/9 datasets, never increase it (0 negative), and yield 1162.005 weighted stack reduction per 1k ops. | Mean task/dataset V-measure is unchanged at 0.7778; some datasets are already well structured and do not benefit. |
| M3 | E1/E3 | profile-spec composition of mappings, predicates, rank rules, and stack depth | 12 profile-spec variants compose operation files, predicates, operation rank rules, rule-score ranking, and explicit stack depth; 12/12 are prompt/session-frame free. AP improves versus width in 9/12 variants and first-positive work in 10/12. | Depth is objective-dependent: 3/6 tasks choose different stack depths for AP and first-positive work. |
| M4 | E3 | operation-level rank-feature ablation | Leave-one-feature ablation identifies 7 critical feature rows across safety, looping, side-effect, and step-quality tasks. Examples include success, loop-like, write-action, and failure fields. | It also finds 3 misleading feature rows, including OSWorld input-phase and SATraj loop-like cases. |
| M5 | E1/E3 | supervised adjacent-boundary field derivation | Boundary backends beat the best simple baseline on 4/5 tested rows; OSWorld-Human R297 reaches F1 0.7735 versus best baseline 0.7090, and R299 also improves AgentNet quality-state boundaries. | 1/5 rows remain counterpoints; AgentRewardBench looping is better explained by repeat_signal_change than the learned backend. |
| M6 | E3 | boundary-derived profile patch | On held-out OSWorld-Human, learned-boundary fields improve AP 0.2402->0.2583, reduce groups 108->74, and raise top-5 recall by 0.1111. | Inspection-cost metrics are mixed: top-5 work changes by +0.0813 and first-positive work by +0.1581. |

## Boundary Families

| Candidate | Dataset | Learned F1 | Best baseline | Delta | Verdict |
|---|---|---|---|---|---|
| osworld_human_group_r297 | osworld-human | 0.7735 | always_boundary (0.709) | 0.0645 | supports_boundary_field_derivation |
| osworld_human_group | osworld-human | 0.6916 | always_boundary (0.6706) | 0.021 | supports_backend |
| agentnet_step_correct | agentnet | 0.3197 | always_boundary (0.2155) | 0.1042 | supports_backend |
| agentnet_step_redundant | agentnet | 0.3361 | always_boundary (0.2645) | 0.0716 | supports_backend |
| agentreward_looping | agentrewardbench | 0.7833 | repeat_signal_change (1) | -0.2167 | counterpoint_simple_field_wins |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `mechanism_rows_cover_mapping_ranking_boundary` | pass | Rows cover deterministic mapping, leave-dataset-out mapping, profile-spec composition, rank-feature ablation, boundary backends, and boundary profile patches. |
| `counterpoints_preserved` | pass | The audit preserves mapping coarsening, simple-field baseline, and inspection-cost counterpoints. |
| `boundary_backend_suitability_not_universal` | pass | Learned boundary backend beats the best simple baseline on 4/5 rows, leaving explicit counterpoints. |
| `no_new_data_or_profiler_rerun` | pass | All inputs are tracked artifacts or current paper/docs; this script only synthesizes existing results. |
| `paper_text_mentions_r366_scope` | pass | Evaluation ledger and paper drafts mention R366's scoped field-derivation role. |
| `two_abstractions_only` | pass | The paper keeps mapping/tagging/boundary outputs as operation fields folded into operation stacks. |
