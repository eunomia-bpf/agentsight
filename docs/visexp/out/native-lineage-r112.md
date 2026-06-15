# R112 DB-Persisted Backfill Lineage Smoke

Last updated: 2026-06-14
Stage at update: execute/analyze
Source/command: `collector report materialize-observed`, `collector report export --no-observed-projection`, and `docs/visexp/effect_lineage_smoke.py`
Completeness: partial

R112 repeats the R111 workload on copies of the three real AgentSight SQLite
DBs. It first writes the observed agent-run envelope into first-class SQLite
`sessions` and `tool_calls` rows, then exports with observed projection disabled
so the snapshot must come from persisted DB rows.

## Result

| Run | DB session rows | DB tool rows | Exported sessions | Exported tool calls | Raw effects | Joined | Orphans | Raw join |
|-----|----------------:|-------------:|------------------:|--------------------:|------------:|-------:|--------:|---------:|
| codex-local | 1 | 1 | 1 | 1 | 90 | 48 | 42 | 53.333% |
| codex-attach | 1 | 1 | 1 | 1 | 168 | 86 | 82 | 51.190% |
| debug-ssl-auto | 1 | 1 | 1 | 1 | 60 | 48 | 12 | 80.000% |
| aggregate | 3 | 3 | 3 | 3 | 318 | 182 | 136 | 57.233% |

Aggregate join methods are `related_event_id=3`,
`pid_family_time_window=179`, and `none=136`.

## Boundary

This is stronger than R111 because the persisted-only export proves that
`sessions` and `tool_calls` rows exist in SQLite, not only in the export view.
It is still not full C4 proof: the rows are produced by explicit backfill, not
capture-time instrumentation; raw join remains 182/318, and 136 effects remain
orphaned.
