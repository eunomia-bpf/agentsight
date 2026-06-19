# R240 Lineage Guard Regression

Last updated: 2026-06-19
Stage at update: supplement / regression
Source/command: `python3 docs/visexp/r240_lineage_guard_regression.py`
Completeness: passed

## Result

- Events checked: 5.
- Joined events: 3.
- Orphan events: 2.
- Join methods: {'command_root_pid_self_time_window': 1, 'pid_family_time_window': 2, 'none': 2}.
- Orphan reasons: {'missing_tool_ancestry': 1, 'missing_process_time_match': 1}.

## External Regression Tests

- `make -C bpf test`: passed (BPF process runtime tests, including target-child network summary capture).
- `cd collector && cargo test wait_for_process_runner_start`: passed (Rust process-tracer readiness wait unit tests).

## Boundary

This is checker-regression evidence. It proves the command-root fallback
does not join a sibling process that merely shares the same root PID, and
that root self events still join only inside the tool time window. It does
not prove live agent-launched target-network coverage. The external test
commands are regression checks only; they are not C5/C6 outcome evidence.
