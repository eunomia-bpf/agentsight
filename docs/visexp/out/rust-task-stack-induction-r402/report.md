# R402 Rust Task-Stack Induction

This artifact replays the Rust `agentpprof --induce-task-stack` implementation on one tracked real-trace slice.
It is a mechanism and visualization artifact: it shows that Rust derives recursive `task:` stacks from adjacent boundary evidence without a user-provided field order.
It is not the paper's hidden-label localization accuracy result.

- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- filters: `dataset=agent-reward-bench;analysis_task=agentreward_looping`
- query terms: `['loop', 'repeat']`

## Rust induced task stack

- operations: 729
- unique stacks: 15
- compression ratio: 48.6
- stack: `task`
- selected source fields: `['action', 'repeat_run', 'repeat_signal', 'repeat_state']`
- split source-field counts: `{'action': 3, 'repeat_run': 4, 'repeat_signal': 5, 'repeat_state': 2}`
- split evidence-field counts: `{'action': 3, 'repeat_run': 5, 'repeat_signal': 5, 'repeat_state': 8}`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'2': 1, '3': 3, '4': 11}`
- stop reasons: `{'max_depth': 14, 'no_material_split': 1}`
- split decisions: 14

| weight | stack |
|---:|---|
| 162 | `task:repeat_state_single;task:repeat_signal_loop-like;task:repeat_run_1;task:repeat_signal_loop-like` |
| 130 | `task:repeat_state_single;task:repeat_signal_none` |
| 76 | `task:repeat_state_single;task:repeat_signal_none;task:repeat_signal_loop-like` |
| 69 | `task:repeat_state_single;task:repeat_signal_loop-like;task:repeat_run_1;task:repeat_signal_none` |
| 64 | `task:repeat_state_same-action-run;task:repeat_run_3plus;task:action_click;task:repeat_run_1` |
| 41 | `task:repeat_state_same-action-run;task:repeat_run_1;task:repeat_state_single;task:repeat_signal_loop-like` |
| 27 | `task:repeat_state_same-action-run;task:repeat_run_1;task:repeat_state_same-action-window;task:action_fill` |
| 27 | `task:repeat_state_same-action-run;task:repeat_run_3plus;task:action_hover` |
| 26 | `task:repeat_state_single;task:repeat_signal_loop-like;task:repeat_run_3plus` |
| 24 | `task:repeat_state_same-action-run;task:repeat_run_3plus;task:action_click;task:repeat_run_3plus` |

## Rust induced task stack with session candidate

- operations: 729
- unique stacks: 15
- compression ratio: 48.6
- stack: `task`
- selected source fields: `['repeat_run', 'repeat_signal', 'repeat_state', 'session']`
- split source-field counts: `{'repeat_run': 1, 'repeat_signal': 2, 'session': 11}`
- split evidence-field counts: `{'repeat_run': 4, 'repeat_signal': 4, 'repeat_state': 6, 'session': 13}`
- oracle source-field overlap: `[]`
- stack depth histogram: `{'2': 7, '3': 6, '4': 2}`
- stop reasons: `{'max_depth': 14, 'no_material_split': 1}`
- split decisions: 14

| weight | stack |
|---:|---|
| 130 | `task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-l2` |
| 77 | `task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:session_workarena.servicenow.dashboard-retrieve-catalog-and-max-order-apple-watch-l2;task:repeat_signal_loop-like` |
| 61 | `task:session_visualwebarena.resized.580;task:session_assistantbench.improved.validation.17;task:session_assistantbench.improved.validation.9` |
| 60 | `task:session_visualwebarena.resized.580;task:session_assistantbench.improved.validation.15;task:session_visualwebarena.88` |
| 60 | `task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:repeat_signal_loop-like` |
| 60 | `task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:session_workarena.servicenow.dashboard-retrieve-catalog-and-max-order-apple-watch-l2;task:session_workarena.servicenow.two-changes-wide-basic-uniform-risk-change-request-scheduling-l2` |
| 48 | `task:session_visualwebarena.resized.580;task:repeat_run_1` |
| 39 | `task:session_workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2;task:session_workarena.servicenow.dashboard-retrieve-catalog-and-max-order-apple-watch-l2;task:session_workarena.servicenow.two-changes-wide-basic-uniform-risk-change-request-scheduling-l2;task:session_workarena.servicenow.two-changes-wide-priority-uniform-risk-change-request-scheduling-l2` |
| 34 | `task:session_visualwebarena.resized.580;task:session_assistantbench.improved.validation.17` |
| 30 | `task:session_visualwebarena.resized.580;task:repeat_run_3plus` |

