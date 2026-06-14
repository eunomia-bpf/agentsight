# R111 Native Export Lineage Smoke

Last updated: 2026-06-14
Stage at update: execute/analyze
Source/command: `collector report export` plus `docs/visexp/effect_lineage_smoke.py`
Completeness: partial

R111 repeats the R110 DB workload after moving the minimal agent-run envelope
into native collector export. The exported snapshots now contain `sessions` and
`tool_calls` without running `docs/visexp/live_lineage_harness.py`.

## Result

| Run | Sessions | Tool calls | Raw effects | Joined | Orphans | Raw join | Folded stacks |
|-----|---------:|-----------:|------------:|-------:|--------:|---------:|--------------:|
| codex-local | 1 | 1 | 90 | 48 | 42 | 53.333% | 20 |
| codex-attach | 1 | 1 | 168 | 86 | 82 | 51.190% | 23 |
| debug-ssl-auto | 1 | 1 | 60 | 48 | 12 | 80.000% | 33 |
| aggregate | 3 | 3 | 318 | 182 | 136 | 57.233% | 76 |

Aggregate join methods are `related_event_id=3`,
`pid_family_time_window=179`, and `none=136`.

## Boundary

This is stronger than R110 because the exported AgentSight snapshot itself now
contains session/tool envelope rows. It is still not full C4 proof: only
182/318 raw effects join, 136 effects remain orphaned, and the session/tool
envelope is export-derived from observed prompts rather than persisted as
first-class DB capture state.
