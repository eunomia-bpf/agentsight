# R401 Latest Real-Trace Operation-Stack Flamegraph

This artifact focuses on one real benchmark slice, AgentReward, from the tracked R300 operation file.
The overview omits session frames to avoid fragmentation. The drilldown adds session as a deeper recursive fold.

- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- filter: `dataset=agent-reward-bench`

## AgentReward overview

A readable benchmark-level workload-shape view without per-session fragmentation.

- operations: 1458
- unique stacks: 28
- compression ratio: 52.071
- max stack reuse: 451
- stack: `source,dataset,analysis_task,phase,tool,action,status`
- hidden label fields in stack: []

| analysis task | operations |
|---|---:|
| agentreward_looping | 729 |
| agentreward_side_effect | 729 |

| phase | operations |
|---|---:|
| navigate | 1070 |
| input | 220 |
| finish | 96 |
| browser-action | 56 |
| observe | 16 |

## AgentReward session drilldown

A deeper view that adds session only after the benchmark overview is readable.

- operations: 1458
- unique stacks: 170
- compression ratio: 8.576
- max stack reuse: 61
- stack: `source,dataset,analysis_task,session,phase,tool,action,status`
- hidden label fields in stack: []

| analysis task | operations |
|---|---:|
| agentreward_looping | 729 |
| agentreward_side_effect | 729 |

| phase | operations |
|---|---:|
| navigate | 1070 |
| input | 220 |
| finish | 96 |
| browser-action | 56 |
| observe | 16 |

