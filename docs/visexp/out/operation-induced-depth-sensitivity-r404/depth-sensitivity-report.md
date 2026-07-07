# R404 Induced Stack Depth Sensitivity

This run varies Rust `--induce-max-depth` over the existing R300/R320 hidden-label tasks. It is an RQ3 mechanism/actionability ablation, not a new dataset and not an automatic selector.

## Main Interpretation

- Induced stack depth is a real profile-configuration knob: sweeping depths [1, 2, 3, 4, 5] changes hidden-label fidelity, inspection work, and fragmentation on the same six real labeled tasks without syncing new data or using hidden labels during profiling.
- The sweep is a post-hoc mechanism analysis, not an automatic depth selector. The median-AP best depth is 4 (AP 0.3034), while the lowest median work@5 depth is 5 (work 0.1067).

## Depth Summary

| Depth | Ranker | Tasks | Hidden | Median AP | Median work@5 | Median budget30 recall | Median groups |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | oracle_upper_bound | 6 | True | 0.2086 | 1.0 | 0.0 | 2.0 |
| 1 | query_aware | 6 | False | 0.1688 | 1.0 | 0.0 | 2.0 |
| 1 | visible_risk | 6 | False | 0.1688 | 1.0 | 0.0 | 2.0 |
| 1 | width | 6 | False | 0.2066 | 1.0 | 0.0 | 2.0 |
| 2 | oracle_upper_bound | 6 | True | 0.2223 | 1.0 | 0.2709 | 4.0 |
| 2 | query_aware | 6 | False | 0.1548 | 1.0 | 0.1446 | 4.0 |
| 2 | visible_risk | 6 | False | 0.1537 | 1.0 | 0.1446 | 4.0 |
| 2 | width | 6 | False | 0.2045 | 1.0 | 0.2709 | 4.0 |
| 3 | oracle_upper_bound | 6 | True | 0.338 | 0.7224 | 0.3606 | 7.5 |
| 3 | query_aware | 6 | False | 0.3009 | 0.7612 | 0.3371 | 7.5 |
| 3 | visible_risk | 6 | False | 0.1572 | 0.7111 | 0.2004 | 7.5 |
| 3 | width | 6 | False | 0.1855 | 0.8837 | 0.315 | 7.5 |
| 4 | oracle_upper_bound | 6 | True | 0.4559 | 0.4721 | 0.3961 | 15.0 |
| 4 | query_aware | 6 | False | 0.3034 | 0.2819 | 0.276 | 15.0 |
| 4 | visible_risk | 6 | False | 0.1459 | 0.3869 | 0.276 | 15.0 |
| 4 | width | 6 | False | 0.1377 | 0.744 | 0.3241 | 15.0 |
| 5 | oracle_upper_bound | 6 | True | 0.5269 | 0.3772 | 0.4003 | 28.0 |
| 5 | query_aware | 6 | False | 0.2993 | 0.1067 | 0.2795 | 28.0 |
| 5 | visible_risk | 6 | False | 0.1491 | 0.0754 | 0.2789 | 28.0 |
| 5 | width | 6 | False | 0.1363 | 0.6399 | 0.2602 | 28.0 |

## Best Depths By Task

| Task | Best AP depth | Best work@5 depth | Best budget30 recall depth | Best groups depth |
|---|---:|---:|---:|---:|
| agentnet_incorrect_step | 3 | 5 | 4 | 1 |
| agentnet_redundant_step | 5 | 5 | 5 | 1 |
| agentreward_looping | 4 | 5 | 5 | 1 |
| agentreward_side_effect | 3 | 5 | 3 | 1 |
| osworld_group_start | 5 | 5 | 3 | 1 |
| satraj_unsafe | 5 | 5 | 4 | 1 |

## Checks

- uses_tracked_r300_source: `True`
- uses_tracked_r320_baselines: `True`
- covers_all_six_tasks: `True`
- covers_all_depths: `True`
- all_rust_profiles_use_induction: `True`
- all_rust_depth_caps_match: `True`
- rust_stack_reconstruction_matches: `True`
- no_oracle_source_fields_selected: `True`
- hidden_labels_used_only_for_visible_rows: `True`
