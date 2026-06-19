# R236 Multiprocess/Claude Network Capture Boundary

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r236_multiprocess_claude_network_capture.py`
Completeness: partial

R236 diagnoses R235's partial network-capture boundary. It is not user evidence.

## Aggregate

- Tasks: 4; ok tasks: 1.
- Capture statuses: {'lineage_orphaned': 2, 'captured_joined': 1, 'capture_missing_target_network': 1}.
- Launchers: {'direct-python': 2, 'codex': 1, 'claude': 1}.
- Target-row observed tasks: 3/4.
- Direct/agent target-row observed tasks: 2/1.
- Lineage orphaned tasks: 2; agent missing-target tasks: 1.
- Required-action task gate: 2/4.
- Target network effects: 5/7 joined.
- Negative controls: observed=11, joined=0.
- Metric boundary: precision_pct and recall_pct are scoped lineage-oracle metrics over observed in-scope and negative effects; target-network capture support is governed by target-row observation, required-action, join, and broad-support gates.
- Gates: direct_delayed=False, direct_rows_observed=True, agent_rows_observed=True, codex_delayed=True, claude_delayed=False, partial_localized=True, broad_supported=False.

## Tasks

| Task | Launcher | Status | Capture status | Probe | Target network | Required actions | Snapshot network | Neg joined |
|------|----------|--------|----------------|-------|---------------:|------------------|-----------------:|-----------:|
| `r236-direct-multiprocess-fast` | direct-python | partial | lineage_orphaned | multiprocess_tcp:ok | 2/3 | ok | 3 | 0 |
| `r236-direct-multiprocess-delayed` | direct-python | partial | lineage_orphaned | multiprocess_tcp:ok | 0/1 | NET_BIND,NET_LISTEN | 1 | 0 |
| `r236-codex-multiprocess-delayed` | codex | ok | captured_joined | multiprocess_tcp:ok | 3/3 | ok | 13 | 0 |
| `r236-claude-http-delayed` | claude | partial | capture_missing_target_network | http:ok | 0/0 | NET_BIND,NET_LISTEN,NET_CONNECT | 0 | 0 |

## Boundary

R236 partially localizes the R235 boundary: direct Python controls can produce target network rows and negative controls stay clean; the Codex delayed multiprocess probe can also join target rows. However, direct rows can still orphan and the Claude-launched delayed HTTP probe exports zero target rows despite probe_result_ok. Therefore probe_result_ok is not sufficient execution/capture evidence; the next gate must add a non-synthesizable runtime witness and inspect the collector lineage invariant.
