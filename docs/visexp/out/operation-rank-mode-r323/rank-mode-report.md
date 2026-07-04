# R323 Rust Rank-Mode Probe

- Source operations: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- Tasks: 6
- Rule-score AP wins vs width-boost: 4/6
- Rule-score AP@20 wins vs width-boost: 3/6
- Rule-score top-5 lift wins vs width-boost: 4/6

| Task | Width AP | Width-boost AP | Rule-score AP | Rule-score delta | Rule-score top-5 lift delta |
|---|---:|---:|---:|---:|---:|
| agentreward_looping | 0.7653 | 0.8242 | 0.8808 | 0.0566 | 0.2820 |
| agentreward_side_effect | 0.3661 | 0.3459 | 0.3549 | 0.0090 | -0.6891 |
| satraj_unsafe | 0.1000 | 0.0962 | 0.1748 | 0.0786 | 1.4301 |
| agentnet_incorrect_step | 0.0687 | 0.0748 | 0.0826 | 0.0078 | 2.4567 |
| agentnet_redundant_step | 0.0863 | 0.0900 | 0.0870 | -0.0030 | 0.7111 |
| osworld_group_start | 0.2218 | 0.2308 | 0.2222 | -0.0086 | -0.0907 |

This run is a rank-policy mechanism probe over existing operation-stack groups.
It uses the same visible rank rules as R322 and scores hidden labels only after
the Rust profiler has emitted the ranked JSON output.
