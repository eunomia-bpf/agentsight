# R329 Leave-Target Rank-Policy Transfer

- Profiler input: `docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl`
- Leave-task semantic AP wins vs width: 4/6
- Leave-dataset semantic AP wins vs width: 4/6
- Leave-task within 0.02 AP of target-equal policy: 7/12
- Leave-dataset within 0.02 AP of target-equal policy: 7/12

## Held-Out Selections

| Target | Dataset | Stack | Protocol | Selected policy | Delta AP | Gap to oracle | Delta WTFP |
|---|---|---|---|---|---:|---:|---:|
| agentreward_looping | agent-reward-bench | semantic | leave_task | source_equal_satraj_unsafe | 0.0649 | 0.0345 | -0.1413 |
| agentreward_looping | agent-reward-bench | semantic | leave_dataset | source_equal_satraj_unsafe | 0.0649 | 0.0345 | -0.1413 |
| agentreward_looping | agent-reward-bench | coarse | leave_task | source_equal_satraj_unsafe | 0.0888 | 0.0630 | -0.3141 |
| agentreward_looping | agent-reward-bench | coarse | leave_dataset | source_equal_satraj_unsafe | 0.0888 | 0.0630 | -0.3141 |
| agentreward_side_effect | agent-reward-bench | semantic | leave_task | source_equal_satraj_unsafe | -0.0586 | 0.0551 | -0.1413 |
| agentreward_side_effect | agent-reward-bench | semantic | leave_dataset | source_equal_satraj_unsafe | -0.0586 | 0.0551 | -0.1413 |
| agentreward_side_effect | agent-reward-bench | coarse | leave_task | source_equal_satraj_unsafe | -0.0885 | 0.0843 | -0.2030 |
| agentreward_side_effect | agent-reward-bench | coarse | leave_dataset | source_equal_satraj_unsafe | -0.0885 | 0.0843 | -0.2030 |
| satraj_unsafe | satraj-os-safety | semantic | leave_task | source_equal_agentnet_incorrect_step | -0.0123 | 0.0210 | -0.5661 |
| satraj_unsafe | satraj-os-safety | semantic | leave_dataset | source_equal_agentnet_incorrect_step | -0.0123 | 0.0210 | -0.5661 |
| satraj_unsafe | satraj-os-safety | coarse | leave_task | global_equal | 0.0343 | 0.0791 | -0.4984 |
| satraj_unsafe | satraj-os-safety | coarse | leave_dataset | global_equal | 0.0343 | 0.0791 | -0.4984 |
| agentnet_incorrect_step | agentnet | semantic | leave_task | source_equal_satraj_unsafe | 0.0254 | 0.0051 | -0.0686 |
| agentnet_incorrect_step | agentnet | semantic | leave_dataset | source_equal_satraj_unsafe | 0.0254 | 0.0051 | -0.0686 |
| agentnet_incorrect_step | agentnet | coarse | leave_task | source_equal_satraj_unsafe | 0.0159 | 0.0058 | -0.1013 |
| agentnet_incorrect_step | agentnet | coarse | leave_dataset | source_equal_satraj_unsafe | 0.0159 | 0.0058 | -0.1013 |
| agentnet_redundant_step | agentnet | semantic | leave_task | source_equal_satraj_unsafe | 0.0023 | 0.0090 | -0.0751 |
| agentnet_redundant_step | agentnet | semantic | leave_dataset | source_equal_satraj_unsafe | 0.0023 | 0.0056 | -0.0751 |
| agentnet_redundant_step | agentnet | coarse | leave_task | source_equal_satraj_unsafe | 0.0024 | 0.0077 | -0.1275 |
| agentnet_redundant_step | agentnet | coarse | leave_dataset | source_equal_satraj_unsafe | 0.0024 | 0.0057 | -0.1275 |
| osworld_group_start | osworld-human | semantic | leave_task | source_equal_satraj_unsafe | 0.0001 | 0.0027 | -0.1286 |
| osworld_group_start | osworld-human | semantic | leave_dataset | source_equal_satraj_unsafe | 0.0001 | 0.0027 | -0.1286 |
| osworld_group_start | osworld-human | coarse | leave_task | source_equal_satraj_unsafe | -0.0048 | 0.0204 | -0.3879 |
| osworld_group_start | osworld-human | coarse | leave_dataset | source_equal_satraj_unsafe | -0.0048 | 0.0204 | -0.3879 |

Policy selection uses labels from non-target tasks only. The target task labels are used only after profiling to score the emitted ranking.
