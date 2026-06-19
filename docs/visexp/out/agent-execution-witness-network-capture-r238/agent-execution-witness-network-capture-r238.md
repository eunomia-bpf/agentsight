# R238 Agent Execution Witness Network Capture

Last updated: 2026-06-19
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r237_agent_execution_witness_network_capture.py`
Completeness: partial

R238 diagnoses whether agent-launched network probes execute with a runtime-only witness
and whether the same witness port appears in target network capture rows.

## Aggregate

- Tasks: 4; ok tasks: 2.
- Capture statuses: {'captured_joined': 2, 'captured_partial': 1, 'collector_lineage_orphaned': 1}.
- Launchers: {'direct-python': 2, 'codex': 1, 'claude': 1}.
- Runtime witness ok tasks: 4/4.
- Witness-port linked tasks: 4/4.
- Required-action task gate: 3/4.
- Target network effects: 13/16 joined.
- Negative controls: observed=186, joined=0.
- Gates: runtime_witness=True, witness_port_capture=True, positive_controls=True, claude_capture=False, direct_orphan_resolved=True, boundary_resolved=False.
- Metric boundary: scoped_lineage_oracle_precision_pct and scoped_lineage_oracle_recall_pct are computed over observed in-scope and negative effects. R238 support is governed by runtime witness, witness-port capture, target-network join, and negative-control gates.

## Tasks

| Task | Launcher | Status | Capture status | Witness | Port rows | Target network | Orphan reasons | Neg joined |
|------|----------|--------|----------------|---------|----------:|---------------:|----------------|-----------:|
| `r237-direct-http-witness` | direct-python | ok | captured_joined | True | 1 | 4/4 | none | 0 |
| `r237-direct-multiprocess-witness` | direct-python | ok | captured_joined | True | 1 | 3/3 | none | 0 |
| `r237-codex-http-witness` | codex | partial | captured_partial | True | 1 | 4/5 | missing_process_time_match:1 | 0 |
| `r237-claude-http-witness` | claude | partial | collector_lineage_orphaned | True | 1 | 2/4 | missing_process_time_match:2 | 0 |

## Boundary

R238 partially localizes the remaining boundary: runtime witnesses pass, direct positive controls pass, witness ports are captured, and negative controls remain clean, but agent-launched Codex/Claude rows still have target-network orphan or missing-action cases. This supports a named collector/launcher boundary, not broad Claude-launched network coverage.
