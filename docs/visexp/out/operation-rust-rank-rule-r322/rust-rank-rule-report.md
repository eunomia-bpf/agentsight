# R322 Rust Visible Rank-Rule Probe

- Source operations: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- Tasks: 6
- AP wins: 4/6
- AP@20 wins: 4/6
- Top-5 recall wins: 2/6
- Top-5 lift wins: 3/6

| Task | AP width | AP rank | Delta | AP@20 delta | Top-5 recall delta | Top-5 lift delta |
|---|---:|---:|---:|---:|---:|---:|
| agentreward_looping | 0.7653 | 0.8242 | 0.0589 | 0.0615 | 0.0000 | 0.0000 |
| agentreward_side_effect | 0.3661 | 0.3459 | -0.0202 | -0.0202 | 0.0495 | 0.4163 |
| satraj_unsafe | 0.1000 | 0.0962 | -0.0038 | -0.0108 | 0.0000 | 0.0000 |
| agentnet_incorrect_step | 0.0687 | 0.0748 | 0.0061 | 0.0052 | -0.0023 | 0.0443 |
| agentnet_redundant_step | 0.0863 | 0.0900 | 0.0037 | 0.0049 | 0.0205 | 0.1568 |
| osworld_group_start | 0.2218 | 0.2308 | 0.0090 | 0.0049 | 0.0000 | 0.0000 |

This run is an implementation probe. It verifies that the Rust JSON profiler can emit
operation-stack groups ranked by visible stack text, while hidden labels are used only
for offline scoring.
