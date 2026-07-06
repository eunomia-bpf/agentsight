# R365 Paper Headline Case Studies

- Status: `pass`.
- Checks: 6/6.
- This is not a new empirical result and does not rerun the profiler.

## Headline Rows

| Row | Block | Role | Main numbers | Counterpoint |
|---|---|---|---|---|
| H1 | E2 | hidden-label localization and inspection work | 6 tasks / 4 datasets / 34539 operations / 3699 positives; Work@5 0.0937 vs flat 1; R@30% 0.39 vs fixed-session 0.3559. | Fixed-session still has lower first-positive work (0.0044); dataset-native has higher top-5 recall (0.8665) at high work. |
| H2 | E2 | fixed-boundary fragmentation tradeoff | Median groups 157.5 vs fixed-session 285; top-5 recall wins vs fixed-session 5/6; 30% budget inspects fewer groups on 5/6 tasks. | The fixed-session result is a fragmentation result, not work dominance: operation_stack:query_aware has lower work-to-50%-recall on only 1/6 tasks, lower top-5 work on only 2/6 tasks, and lower work-to-first-positive on only 2/6 tasks. |
| H3 | E2/E3 | oracle-depth adequacy | 24/24 rows lower top-5 unit work than flat; 20/24 rows beat fixed-session unit recall; 22/24 rows use fewer groups to 50% positives. | session-level AgentRewardBench labels do not prove latent subtask boundaries; positive-run units are a cross-dataset proxy, not human intent annotations |
| H4 | E3 | profile-configuration actionability | 27/36 objective rows need non-default actions; 25/36 require view changes; R354 accepts 5/6 patches with median AP delta 0.0376 and top-5 lift delta 0.575. | These are visible-profile configuration actions, not an automatic patch selector or human-productivity result. |
| H5 | E3 | boundary-field mechanism ablation | AP 0.2583 vs semantic-width 0.2402; groups 74 vs 108; top-5 recall delta 0.1111. | Boundary-derived fields improve AP and reduce groups, but they increase top-5 operation work and first-positive work on this held-out subset. |

## Task Cards

| Task | Policy | Work@5 | Recall@5 | Patch | Action |
|---|---|---|---|---|---|
| agentreward_looping | dataset_native:query_aware | 0.4938 | 0.6508 | accept_patch (0.1155) | Keep repeat_signal in the stack, but add prevalence-aware ranking because looping positives are common. |
| agentreward_side_effect | fixed_session:width | 0.1454 | 0.1139 | accept_patch (0.0591) | Increase weight on write/input actions or use a deeper side-effect mapping before ranking. |
| satraj_unsafe | operation_stack:query_aware | 0.042 | 0.2621 | accept_patch (0.5081) | Use environment + phase + action stack fields; prioritize risky environments and write actions. |
| agentnet_incorrect_step | raw_action_stack:width | 0.0014 | 0.0034 | accept_patch (0.016) | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| agentnet_redundant_step | raw_action_stack:width | 0.0089 | 0.0177 | accept_patch (0.0011) | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| osworld_group_start | flat:width | 0.4074 | 0.3874 | reject_patch_or_needs_new_mapping (-0.0004) | Use group-depth or boundary-derived fields for higher recall; action-depth alone fragments starts. |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `headline_rows_cover_e2_e3_claim` | pass | Headline rows preserve E2 localization/tradeoff, E3 actionability, oracle-depth, and boundary-field numbers. |
| `six_task_cards_with_counterpoints` | pass | All six oracle-backed tasks have an action card and explicit counterpoint. |
| `visible_non_oracle_actionability` | pass | Task cards are based on visible-policy action cards and R354 profile-spec patches. |
| `paper_text_mentions_r365` | pass | Evaluation ledger and paper drafts mention the R365 headline/case-study selector. |
| `no_new_data_or_profiler_rerun` | pass | All inputs are tracked artifacts or current paper/docs; the script does not fetch data or rerun the profiler. |
| `two_abstractions_only` | pass | The paper text keeps outputs as operation/operation-stack evidence rather than new profiler abstractions. |