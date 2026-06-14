# R110 Live Exact-Lineage Smoke

Last updated: 2026-06-14
Stage at update: execute/analyze
Source/command: `docs/visexp/live_lineage_harness.py` plus `docs/visexp/effect_lineage_smoke.py`
Completeness: partial

R110 tests C4 on real AgentSight SQLite DB exports. The raw DB exports contain
process/file/network effects but do not materialize session/tool ancestry, so a
plain checker run has 0% join rate. The harness adds a minimal agent-run
session/tool envelope around detected Codex/Claude root processes, tags those
roots with the local llama.cpp 3B model, and leaves low-level effects unchanged.

## Result

| Run | Roots | Raw effects | In-scope effects | Joined | Orphans | Join rate | Folded stacks |
|-----|------:|------------:|-----------------:|-------:|--------:|----------:|--------------:|
| codex-local | 2 | 90 | 48 | 48 | 0 | 100.0% | 20 |
| codex-attach | 2 | 168 | 86 | 86 | 0 | 100.0% | 23 |
| debug-ssl-auto | 4 | 60 | 48 | 48 | 0 | 100.0% | 33 |
| aggregate | 8 | 318 | 182 | 182 | 0 | 100.0% | 76 |

Join methods across the passing runs are `related_event_id` for root effects and
`pid_family_time_window` for descendant process-family effects.

## Boundary

This is live in-scope smoke evidence, not full C4 proof. Current AgentSight DB
export still needs native session/tool ancestry; otherwise many raw effects are
out of scope. The next C4 step is to move the harness envelope into collector
export or record tasks in a mode that persists `session -> tool_call ->
process* -> effect` directly.
