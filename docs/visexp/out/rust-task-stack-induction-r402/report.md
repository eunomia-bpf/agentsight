# R402 Rust Operation-Stack Induction

This artifact replays the Rust `agentpprof --induce-operation-stack` implementation on one tracked real-trace slice.
It is a mechanism and visualization artifact: it shows that Rust derives recursive operation-stack segments from adjacent boundary evidence without a user-provided field order.
It is not the paper's hidden-label localization accuracy result.

- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- filters: `dataset=agent-reward-bench;analysis_task=agentreward_looping`
- query terms: `['loop', 'repeat']`

## Rust induced operation stack

- operations: 729
- unique stacks: 15
- compression ratio: 48.6
- stack: `operation`
- selected evidence fields: `['action', 'phase', 'repeat_run', 'repeat_state', 'step_error']`
- split evidence primary-field counts: `{'action': 6, 'repeat_run': 4, 'repeat_state': 4}`
- split evidence-field counts: `{'action': 8, 'phase': 2, 'repeat_run': 7, 'repeat_state': 10, 'step_error': 1}`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'2': 1, '3': 1, '4': 13}`
- stop reasons: `{'max_depth': 14, 'no_material_split': 1}`
- split decisions: 14

| weight | stack |
|---:|---|
| 485 | `operation:1+single;operation:click;operation:click+navigate;operation:single` |
| 51 | `operation:1+single;operation:click;operation:click+navigate;operation:same_action_window` |
| 51 | `operation:3plus+same_action_run;operation:1;operation:1+single;operation:1+single+ok` |
| 25 | `operation:3plus+same_action_run;operation:same_action_run+3plus;operation:hover;operation:same_action_run+3plus+hover` |
| 24 | `operation:3plus+same_action_run;operation:1` |
| 19 | `operation:3plus+same_action_run;operation:same_action_run+3plus;operation:click` |
| 13 | `operation:1+single;operation:right-segment;operation:single;operation:go_back` |
| 13 | `operation:3plus+same_action_run;operation:1;operation:1+single;operation:3plus+same_action_run+error` |
| 11 | `operation:3plus+same_action_run;operation:same_action_run+3plus;operation:click;operation:1+single` |
| 9 | `operation:1+single;operation:click;operation:left-segment;operation:single` |

## Rust induced operation stack with session candidate

- operations: 729
- unique stacks: 16
- compression ratio: 45.563
- stack: `operation`
- selected evidence fields: `['action', 'phase', 'repeat_run', 'repeat_state', 'session']`
- split evidence primary-field counts: `{'action': 4, 'repeat_run': 2, 'repeat_state': 2, 'session': 7}`
- split evidence-field counts: `{'action': 8, 'phase': 2, 'repeat_run': 7, 'repeat_state': 10, 'session': 8}`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'3': 2, '4': 14}`
- stop reasons: `{'max_depth': 16}`
- split decisions: 15

| weight | stack |
|---:|---|
| 504 | `operation:1+single;operation:click;operation:click+navigate;operation:single` |
| 32 | `operation:1+single;operation:click;operation:click+navigate;operation:workarena_servicenow_dashboard_retrieve_catalog+same_action_run` |
| 30 | `operation:3plus+same_action_run;operation:1;operation:assistantbench_improved_validation_15+1+single;operation:assistantbench_improved_validation_15` |
| 28 | `operation:3plus+same_action_run;operation:1;operation:assistantbench_improved_validation_15+1+single;operation:assistantbench_improved_validation_16` |
| 25 | `operation:3plus+same_action_run;operation:visualwebarena_88+same_action_run+3plus;operation:visualwebarena_88+hover;operation:same_action_run+3plus+hover` |
| 24 | `operation:3plus+same_action_run;operation:1;operation:visualwebarena_76+3plus+same_action_run` |
| 19 | `operation:3plus+same_action_run;operation:visualwebarena_88+same_action_run+3plus;operation:webarena_723+click` |
| 13 | `operation:1+single;operation:assistantbench_improved_validation_17;operation:single;operation:go_back` |
| 11 | `operation:3plus+same_action_run;operation:visualwebarena_88+same_action_run+3plus;operation:webarena_723+click;operation:1+single` |
| 9 | `operation:1+single;operation:click;operation:webarena_155;operation:single` |

