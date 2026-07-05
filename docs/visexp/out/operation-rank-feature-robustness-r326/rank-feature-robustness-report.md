# R326 Operation Rank-Feature Robustness

- Profiler input: `docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl`
- Global equal semantic AP wins vs width: 4/6
- Global equal coarse AP wins vs width: 5/6
- Task equal AP within 0.02 of weighted task policy: 8/12
- Repaired policy AP improves over task weighted on R325-misleading cases: 2/3
- Repaired policy WTFP improves over task weighted on R325-misleading cases: 2/3
- Repaired policy improves both AP and WTFP on R325-misleading cases: 1/3

## Policy Summary

| Task | Stack | Policy | AP | Delta AP vs width | WTFP |
|---|---|---|---:|---:|---:|
| agentreward_looping | semantic | task_weighted | 0.8808 | 0.1155 | 0.2058 |
| agentreward_looping | semantic | task_equal | 0.8509 | 0.0856 | 0.2058 |
| agentreward_looping | semantic | global_equal | 0.8647 | 0.0994 | 0.2058 |
| agentreward_looping | semantic | r325_repaired | 0.8808 | 0.1155 | 0.2058 |
| agentreward_looping | coarse | task_weighted | 0.8174 | 0.1541 | 0.1399 |
| agentreward_looping | coarse | task_equal | 0.7864 | 0.1231 | 0.1399 |
| agentreward_looping | coarse | global_equal | 0.8151 | 0.1518 | 0.1399 |
| agentreward_looping | coarse | r325_repaired | 0.8174 | 0.1541 | 0.1399 |
| agentreward_side_effect | semantic | task_weighted | 0.3947 | 0.0286 | 0.0645 |
| agentreward_side_effect | semantic | task_equal | 0.3141 | -0.0520 | 0.0645 |
| agentreward_side_effect | semantic | global_equal | 0.2390 | -0.1271 | 0.2058 |
| agentreward_side_effect | semantic | r325_repaired | 0.3947 | 0.0286 | 0.0645 |
| agentreward_side_effect | coarse | task_weighted | 0.4252 | 0.0343 | 0.0933 |
| agentreward_side_effect | coarse | task_equal | 0.3601 | -0.0308 | 0.0933 |
| agentreward_side_effect | coarse | global_equal | 0.2181 | -0.1728 | 0.4733 |
| agentreward_side_effect | coarse | r325_repaired | 0.4252 | 0.0343 | 0.0933 |
| satraj_unsafe | semantic | task_weighted | 0.4772 | 0.3772 | 0.0112 |
| satraj_unsafe | semantic | task_equal | 0.4897 | 0.3897 | 0.0112 |
| satraj_unsafe | semantic | global_equal | 0.1087 | 0.0087 | 0.4299 |
| satraj_unsafe | semantic | r325_repaired | 0.6506 | 0.5506 | 0.0112 |
| satraj_unsafe | coarse | task_weighted | 0.6081 | 0.5086 | 0.0380 |
| satraj_unsafe | coarse | task_equal | 0.6084 | 0.5089 | 0.0380 |
| satraj_unsafe | coarse | global_equal | 0.1338 | 0.0343 | 0.3277 |
| satraj_unsafe | coarse | r325_repaired | 0.6081 | 0.5086 | 0.0380 |
| agentnet_incorrect_step | semantic | task_weighted | 0.0847 | 0.0160 | 0.0001 |
| agentnet_incorrect_step | semantic | task_equal | 0.0999 | 0.0312 | 0.0001 |
| agentnet_incorrect_step | semantic | global_equal | 0.0992 | 0.0305 | 0.0135 |
| agentnet_incorrect_step | semantic | r325_repaired | 0.0847 | 0.0160 | 0.0001 |
| agentnet_incorrect_step | coarse | task_weighted | 0.0770 | 0.0120 | 0.0123 |
| agentnet_incorrect_step | coarse | task_equal | 0.0842 | 0.0192 | 0.0109 |
| agentnet_incorrect_step | coarse | global_equal | 0.0867 | 0.0217 | 0.0317 |
| agentnet_incorrect_step | coarse | r325_repaired | 0.0770 | 0.0120 | 0.0123 |
| agentnet_redundant_step | semantic | task_weighted | 0.0874 | 0.0011 | 0.0051 |
| agentnet_redundant_step | semantic | task_equal | 0.0894 | 0.0031 | 0.0051 |
| agentnet_redundant_step | semantic | global_equal | 0.0942 | 0.0079 | 0.0197 |
| agentnet_redundant_step | semantic | r325_repaired | 0.0874 | 0.0011 | 0.0051 |
| agentnet_redundant_step | coarse | task_weighted | 0.0772 | -0.0001 | 0.0463 |
| agentnet_redundant_step | coarse | task_equal | 0.0768 | -0.0005 | 0.0129 |
| agentnet_redundant_step | coarse | global_equal | 0.0854 | 0.0081 | 0.0463 |
| agentnet_redundant_step | coarse | r325_repaired | 0.0772 | -0.0001 | 0.0463 |
| osworld_group_start | semantic | task_weighted | 0.2214 | -0.0004 | 0.1311 |
| osworld_group_start | semantic | task_equal | 0.2051 | -0.0167 | 0.0294 |
| osworld_group_start | semantic | global_equal | 0.2045 | -0.0173 | 0.0274 |
| osworld_group_start | semantic | r325_repaired | 0.2078 | -0.0140 | 0.0294 |
| osworld_group_start | coarse | task_weighted | 0.1860 | -0.0085 | 0.4024 |
| osworld_group_start | coarse | task_equal | 0.1988 | 0.0043 | 0.0763 |
| osworld_group_start | coarse | global_equal | 0.2073 | 0.0128 | 0.0145 |
| osworld_group_start | coarse | r325_repaired | 0.2085 | 0.0140 | 0.0763 |

## R325-Guided Repairs

| Task | Stack | Dropped features | Delta AP | Delta WTFP |
|---|---|---|---:|---:|
| satraj_unsafe | semantic | loop-like | 0.1734 | 0.0000 |
| osworld_group_start | semantic | input-phase | -0.0136 | -0.1017 |
| osworld_group_start | coarse | input-phase | 0.0225 | -0.3261 |

Rust receives only scrubbed visible operations. Global/task-equal policies are label-free ranking policies; the repaired policy is a post-hoc actionability check driven by R325's offline scoring findings.
