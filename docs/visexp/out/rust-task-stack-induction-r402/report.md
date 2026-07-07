# R402 Rust Task-Stack Induction

This artifact replays the Rust `agentpprof --induce-task-stack` implementation on one tracked real-trace slice.
It is a mechanism and visualization artifact: it shows that Rust derives recursive `task:` stacks without a user-provided field order.
It is not the paper's hidden-label localization accuracy result.

- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- filters: `dataset=agent-reward-bench;analysis_task=agentreward_looping`
- query terms: `['loop', 'repeat']`

## Rust induced task stack

- operations: 729
- unique stacks: 47
- compression ratio: 15.511
- stack: `task`
- selected source fields: `['action', 'repeat_signal', 'repeat_state', 'step_error']`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'1': 1, '2': 22, '3': 24}`
- stop reasons: `{'no_material_split': 14, 'small_node': 33}`
- split decisions: 10

| weight | stack |
|---:|---|
| 131 | `task:same-action-run;task:click` |
| 125 | `task:single;task:loop-like;task:click` |
| 108 | `task:single;task:none;task:click` |
| 49 | `task:light-repeat;task:click;task:loop-like` |
| 47 | `task:single;task:loop-like;task:fill` |
| 25 | `task:same-action-window;task:click` |
| 23 | `task:same-action-run;task:send_msg_to_user` |
| 21 | `task:light-repeat;task:click;task:none` |
| 20 | `task:same-action-run;task:hover` |
| 17 | `task:same-action-window;task:fill` |

## Rust induced task stack with session candidate

- operations: 729
- unique stacks: 91
- compression ratio: 8.011
- stack: `task`
- selected source fields: `['action', 'repeat_run', 'repeat_signal', 'repeat_state', 'session', 'step_error']`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'1': 11, '2': 46, '3': 26, '4': 8}`
- stop reasons: `{'max_depth': 8, 'no_material_split': 22, 'small_node': 61}`
- split decisions: 32

| weight | stack |
|---:|---|
| 35 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2;task:click;task:none;task:single` |
| 30 | `task:workarena.servicenow.dashboard-retrieve-catalog-and-max-order-apple-watch-l2` |
| 30 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:none;task:click` |
| 24 | `task:visualwebarena.76;task:3plus` |
| 24 | `task:visualwebarena.resized.580;task:3plus` |
| 24 | `task:workarena.servicenow.two-changes-wide-basic-varied-risk-change-request-scheduling-l2;task:3plus` |
| 21 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:loop-like;task:single;task:click` |
| 20 | `task:visualwebarena.88;task:same-action-run` |
| 19 | `task:webarena.723;task:3plus` |
| 18 | `task:workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2;task:send_msg_to_user` |

