# R237 Agent Execution Witness Network Capture

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r237_agent_execution_witness_network_capture.py`
Completeness: partial

R237 diagnoses whether agent-launched network probes execute with a runtime-only witness
and whether the same witness port appears in target network capture rows.

## Aggregate

- Tasks: 4; ok tasks: 2.
- Capture statuses: {'captured_joined': 2, 'collector_lineage_orphaned': 1, 'witness_unlinked_to_capture': 1}.
- Launchers: {'claude': 1, 'codex': 1, 'direct-python': 2}.
- Runtime witness ok tasks: 4/4.
- Witness-port linked tasks: 3/4.
- Required-action task gate: 2/4.
- Target network effects: 8/9 joined.
- Negative controls: observed=7, joined=0.
- Gates: runtime_witness=True, witness_port_capture=False, positive_controls=True, claude_capture=False, direct_orphan_resolved=False, boundary_resolved=False.
- Metric boundary: scoped_lineage_oracle_precision_pct and scoped_lineage_oracle_recall_pct are computed over observed in-scope and negative effects. R237 support is governed by runtime witness, witness-port capture, target-network join, and negative-control gates.

## Tasks

| Task | Launcher | Status | Capture status | Witness | Port rows | Target network | Orphan reasons | Neg joined |
|------|----------|--------|----------------|---------|----------:|---------------:|----------------|-----------:|
| `r237-direct-http-witness` | direct-python | ok | captured_joined | True | 1 | 4/4 | none | 0 |
| `r237-direct-multiprocess-witness` | direct-python | partial | collector_lineage_orphaned | True | 1 | 0/1 | missing_tool_ancestry:1 | 0 |
| `r237-codex-http-witness` | codex | ok | captured_joined | True | 1 | 4/4 | none | 0 |
| `r237-claude-http-witness` | claude | partial | witness_unlinked_to_capture | True | 0 | 0/0 | none | 0 |

## Boundary

R237 partially localizes the remaining boundary: all runtime witnesses pass and positive-control witness ports are captured, but the Claude-launched HTTP witness port is not linked to any target network row and the direct multiprocess control still has missing_tool_ancestry orphan rows. This supports a named collector/launcher boundary, not broad Claude-launched network coverage.
