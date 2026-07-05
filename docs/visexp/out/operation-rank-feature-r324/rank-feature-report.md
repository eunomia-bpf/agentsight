# R324 Rust Operation Rank-Feature Probe

- Source operations for scoring: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- Profiler input: `docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl`
- Semantic AP wins vs width: 5/6
- Coarse AP wins vs width: 4/6

| Task | Stack | Groups | Width AP | Op-feature AP | Delta AP | Delta top-5 lift |
|---|---|---:|---:|---:|---:|---:|
| agentreward_looping | semantic | 40 | 0.7653 | 0.8808 | 0.1155 | 0.2820 |
| agentreward_looping | coarse | 16 | 0.6633 | 0.8174 | 0.1541 | 0.1934 |
| agentreward_side_effect | semantic | 40 | 0.3661 | 0.3947 | 0.0286 | -0.2728 |
| agentreward_side_effect | coarse | 16 | 0.3909 | 0.4252 | 0.0343 | 0.3763 |
| satraj_unsafe | semantic | 142 | 0.1000 | 0.4772 | 0.3772 | 6.2384 |
| satraj_unsafe | coarse | 22 | 0.0995 | 0.6081 | 0.5086 | 1.9550 |
| agentnet_incorrect_step | semantic | 289 | 0.0687 | 0.0847 | 0.0160 | 2.5010 |
| agentnet_incorrect_step | coarse | 43 | 0.0650 | 0.0770 | 0.0120 | 1.1263 |
| agentnet_redundant_step | semantic | 260 | 0.0863 | 0.0874 | 0.0011 | 0.8679 |
| agentnet_redundant_step | coarse | 42 | 0.0773 | 0.0772 | -0.0001 | -0.0425 |
| osworld_group_start | semantic | 173 | 0.2218 | 0.2214 | -0.0004 | -0.1277 |
| osworld_group_start | coarse | 32 | 0.1945 | 0.1860 | -0.0085 | -0.1459 |

Rust emits the ranked JSON from the scrubbed visible-operation input first. Hidden labels are used only for this offline scoring.
