# R404 Induced Stack Depth Sensitivity

This run varies Rust `--induce-max-depth` over the existing R300/R320 hidden-label tasks. It is an RQ3 mechanism/actionability ablation, not a new dataset and not an automatic selector.

## Main Interpretation

- Induced stack depth is a real profile-configuration knob: sweeping depths [1, 2, 3, 4, 5] changes hidden-label fidelity, inspection work, and fragmentation on the same six real labeled tasks without syncing new data or using hidden labels during profiling.
- The sweep is a post-hoc mechanism analysis, not an automatic depth selector. The median-AP best depth is 3 (AP 0.2865), while the lowest median work@5 depth is 5 (work 0.4727).

## Depth Summary

| Depth | Ranker | Tasks | Hidden | Median AP | Median work@5 | Median budget30 recall | Median groups |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | oracle_upper_bound | 6 | True | 0.21 | 1.0 | 0.0 | 2.0 |
| 1 | query_aware | 6 | False | 0.1702 | 1.0 | 0.0 | 2.0 |
| 1 | visible_risk | 6 | False | 0.1702 | 1.0 | 0.0 | 2.0 |
| 1 | width | 6 | False | 0.21 | 1.0 | 0.0 | 2.0 |
| 2 | oracle_upper_bound | 6 | True | 0.2114 | 1.0 | 0.1243 | 4.0 |
| 2 | query_aware | 6 | False | 0.1635 | 1.0 | 0.0923 | 4.0 |
| 2 | visible_risk | 6 | False | 0.1624 | 1.0 | 0.0923 | 4.0 |
| 2 | width | 6 | False | 0.1948 | 1.0 | 0.1243 | 4.0 |
| 3 | oracle_upper_bound | 6 | True | 0.2873 | 0.9503 | 0.144 | 7.0 |
| 3 | query_aware | 6 | False | 0.2865 | 0.8753 | 0.1099 | 7.0 |
| 3 | visible_risk | 6 | False | 0.1573 | 0.8942 | 0.0844 | 7.0 |
| 3 | width | 6 | False | 0.1856 | 0.9688 | 0.144 | 7.0 |
| 4 | oracle_upper_bound | 6 | True | 0.3042 | 0.8095 | 0.1787 | 12.0 |
| 4 | query_aware | 6 | False | 0.2762 | 0.653 | 0.1505 | 12.0 |
| 4 | visible_risk | 6 | False | 0.1514 | 0.7735 | 0.1518 | 12.0 |
| 4 | width | 6 | False | 0.1806 | 0.9122 | 0.1518 | 12.0 |
| 5 | oracle_upper_bound | 6 | True | 0.3582 | 0.6886 | 0.1835 | 16.5 |
| 5 | query_aware | 6 | False | 0.2478 | 0.4727 | 0.1636 | 16.5 |
| 5 | visible_risk | 6 | False | 0.1505 | 0.4283 | 0.1519 | 16.5 |
| 5 | width | 6 | False | 0.1786 | 0.876 | 0.1505 | 16.5 |

## Best Depths By Task

| Task | Best AP depth | Best work@5 depth | Best budget30 recall depth | Best groups depth |
|---|---:|---:|---:|---:|
| agentnet_incorrect_step | 1 | 5 | 1 | 5 |
| agentnet_redundant_step | 1 | 5 | 1 | 5 |
| agentreward_looping | 5 | 4 | 4 | 1 |
| agentreward_side_effect | 3 | 5 | 1 | 1 |
| osworld_group_start | 2 | 5 | 5 | 1 |
| satraj_unsafe | 4 | 5 | 4 | 1 |

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
