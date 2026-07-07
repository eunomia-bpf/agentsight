# R401 Latest Real-Trace Operation-Stack Flamegraph

This artifact focuses on one real benchmark slice and one diagnostic query:
`dataset=agent-reward-bench;analysis_task=agentreward_looping` from the tracked R300 operation file.
It does not ask for a field order. Source fields are candidate mapping inputs, and the rendered stack uses only `task:` frames.
R401 is a visualization/profiler-shape artifact; it is not paper-level localization accuracy evidence.

- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- filter: `dataset=agent-reward-bench;analysis_task=agentreward_looping`
- folding policy: `query-conditioned-greedy-task-stack-induction`

## AgentReward induced task stack

A query-conditioned task stack induced from visible operation fields, without session as a candidate.

- operations: 729
- unique stacks: 43
- compression ratio: 16.953
- max stack reuse: 131
- visual stack frame: `task`
- source fields selected by induction: `['action', 'repeat_signal', 'repeat_state', 'step_error']`
- hidden/oracle source-field overlap: `[]`
- max stack depth: 3
- stack depth histogram: `{'1': 1, '2': 28, '3': 14}`
- stop reasons: `{'no_material_split': 14, 'small_node': 29}`

| task_level_1 | operations |
|---|---:|
| single | 365 |
| same-action-run | 187 |
| light-repeat | 114 |
| same-action-window | 59 |
| target-window | 4 |

| task_level_2 | operations |
|---|---:|
| click | 459 |
| fill | 109 |
| send_msg_to_user | 40 |
| hover | 27 |
| select_option | 25 |
| scroll | 19 |
| goto | 14 |
| go_back | 13 |
| noop | 8 |
| report_infeasible | 8 |

| task_level_3 | operations |
|---|---:|
| loop-like | 251 |
| none | 174 |
| error | 5 |
| ok | 5 |

| selected source field | node weight | score | path |
|---|---:|---:|---|
| repeat_state | 729 | 0.342396 | `<root>` |
| action | 365 | 0.250416 | `task:single` |
| repeat_signal | 233 | 0.179535 | `task:single;task:click` |
| repeat_signal | 64 | 0.157395 | `task:single;task:fill` |
| repeat_signal | 23 | 0.12864 | `task:single;task:select_option` |
| repeat_signal | 13 | 0.273313 | `task:single;task:send_msg_to_user` |
| action | 187 | 0.334836 | `task:same-action-run` |
| action | 114 | 0.244992 | `task:light-repeat` |
| repeat_signal | 70 | 0.133101 | `task:light-repeat;task:click` |
| repeat_signal | 22 | 0.127777 | `task:light-repeat;task:fill` |
| action | 59 | 0.476606 | `task:same-action-window` |
| step_error | 10 | 0.093347 | `task:same-action-window;task:scroll` |

## AgentReward induced task stack with session candidate

The same induction policy with session available as a candidate split when it explains visible variation.

- operations: 729
- unique stacks: 91
- compression ratio: 8.011
- max stack reuse: 35
- visual stack frame: `task`
- source fields selected by induction: `['action', 'repeat_signal', 'repeat_state', 'session', 'step_error']`
- hidden/oracle source-field overlap: `[]`
- max stack depth: 4
- stack depth histogram: `{'1': 11, '2': 50, '3': 26, '4': 4}`
- stop reasons: `{'no_material_split': 25, 'small_node': 66}`

| task_level_1 | operations |
|---|---:|
| workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2 | 102 |
| workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2 | 100 |
| visualwebarena.resized.580 | 33 |
| assistantbench.improved.validation.15 | 30 |
| assistantbench.improved.validation.17 | 30 |
| assistantbench.improved.validation.9 | 30 |
| visualwebarena.569 | 30 |
| visualwebarena.76 | 30 |
| visualwebarena.88 | 30 |
| webarena.723 | 30 |

| task_level_2 | operations |
|---|---:|
| click | 230 |
| same-action-run | 124 |
| fill | 87 |
| single | 69 |
| send_msg_to_user | 31 |
| light-repeat | 27 |
| select_option | 24 |
| go_back | 13 |
| same-action-window | 13 |
| goto | 10 |

| task_level_3 | operations |
|---|---:|
| single | 76 |
| none | 37 |
| ok | 37 |
| loop-like | 36 |
| light-repeat | 34 |
| error | 22 |
| same-action-window | 10 |
| same-action-run | 7 |
| target-window | 1 |

| task_level_4 | operations |
|---|---:|
| none | 35 |
| single | 21 |
| light-repeat | 9 |
| loop-like | 9 |

| selected source field | node weight | score | path |
|---|---:|---:|---|
| session | 729 | 0.400594 | `<root>` |
| action | 102 | 0.324113 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2` |
| repeat_signal | 60 | 0.279775 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:click` |
| repeat_state | 30 | 0.079147 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:click;task:loop-like` |
| repeat_state | 15 | 0.55353 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:fill` |
| repeat_signal | 13 | 0.302761 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:select_option` |
| action | 100 | 0.376739 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2` |
| repeat_state | 61 | 0.155056 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2;task:click` |
| repeat_signal | 44 | 0.087784 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2;task:click;task:single` |
| repeat_state | 33 | 0.459271 | `task:visualwebarena.resized.580` |
| repeat_state | 30 | 0.338871 | `task:assistantbench.improved.validation.15` |
| action | 30 | 0.470308 | `task:assistantbench.improved.validation.17` |

