# R325 Operation Rank-Feature Ablation

- Profiler input: `docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl`
- Semantic AP wins vs width: 5/6
- Coarse AP wins vs width: 4/6
- Critical feature instances: 7
- Misleading feature instances: 3
- Coarse preferred by AP: 2/6

## Critical And Misleading Features

| Task | Stack | Feature | Class | Drop AP Delta | Drop WTFP Delta |
|---|---|---|---|---:|---:|
| satraj_unsafe | coarse | success | critical | -0.3948 | 0.0946 |
| satraj_unsafe | semantic | success | critical | -0.2682 | 0.0604 |
| agentreward_looping | coarse | loop-like | critical | -0.1363 | 0.2140 |
| agentreward_looping | semantic | loop-like | critical | -0.1183 | 0.0000 |
| agentreward_side_effect | semantic | write-action | critical | -0.0824 | 0.0000 |
| agentreward_side_effect | coarse | write-action | critical | -0.0754 | 0.0000 |
| agentnet_redundant_step | semantic | failure | critical | -0.0008 | 0.0554 |
| osworld_group_start | semantic | input-phase | misleading | -0.0136 | -0.1017 |
| osworld_group_start | coarse | input-phase | misleading | 0.0225 | -0.3261 |
| satraj_unsafe | semantic | loop-like | misleading | 0.1734 | 0.0000 |

## Stack Depth

| Task | Preferred | Semantic AP | Coarse AP | Group Reduction |
|---|---|---:|---:|---:|
| agentreward_looping | semantic | 0.8808 | 0.8174 | 24 |
| agentreward_side_effect | coarse | 0.3947 | 0.4252 | 24 |
| satraj_unsafe | coarse | 0.4772 | 0.6081 | 120 |
| agentnet_incorrect_step | semantic | 0.0847 | 0.0770 | 246 |
| agentnet_redundant_step | semantic | 0.0874 | 0.0772 | 218 |
| osworld_group_start | semantic | 0.2214 | 0.1860 | 141 |

Rust receives only scrubbed visible operations; hidden labels are not passed to Rust and are used only for offline scoring.
