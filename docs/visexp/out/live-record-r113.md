# R113 Live Record Harness

Last updated: 2026-06-14
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r113_live_record_harness.py --out docs/visexp/out`
Completeness: passed for this smoke

This run wraps real `codex exec` tasks with `agentsight record`, exports each SQLite DB,
and checks whether process/file/network effects inherit the capture-time agent-run envelope.
Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed;
rerun this harness to reproduce per-event evidence.

## Aggregate

- Tasks: 5 ({'lineage_ok': 5})
- Record status: {'ok': 5}; lineage status: {'ok': 5}
- Record-envelope rows: sessions=5, tool_calls=5, completed_tools=5
- Effects: joined=508 / 508 = 100.0%
- Orphans: 0 {}
- Join methods: {'pid_family_time_window': 258, 'root_pid_time_window': 250}

## Per Task

| Task | Record | Lineage | Sessions | Tools | Effects | Joined | Orphans | Join | Answer |
|------|--------|---------|---------:|------:|--------:|-------:|--------:|-----:|--------|
| `codex-count-r113` | ok | ok | 1 | 1 | 97 | 97 | 0 | 100.0% | r113_boundary=implementation |
| `codex-find-next` | ok | ok | 1 | 1 | 97 | 97 | 0 | 100.0% | Next action: expand R113-live beyond five read-only tasks, then run B5 small-mod |
| `codex-claim-c4` | ok | ok | 1 | 1 | 102 | 102 | 0 | 100.0% | partial |
| `codex-rg-baseline` | ok | ok | 1 | 1 | 104 | 104 | 0 | 100.0% | baseline_lines=6 |
| `codex-paper-boundary` | ok | ok | 1 | 1 | 108 | 108 | 0 | 100.0% | mentions_r113=yes |

## Boundary

R113-live proves that command-mode `record` creates capture-time session/tool rows
around real Codex agent tasks and that the exported process/file/network effects
inherit the agent-run envelope in this five-task smoke. This does not yet prove
full-history exact lineage, cross-repository robustness, user utility, or tag adequacy.
