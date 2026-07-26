# Event-Workdir Fix — Trajectory vs Corrected v4 Oracle (2026-07-25)

Fixes the last genuine projection-side bug from the RQ7 conformance audit:
the projection froze the **session-initial** cwd, while the frozen question
spec (`experiment-001/private/question-spec.md`) says **"Event workdir
overrides session cwd."**

## The bug and the fix

Evidence case (frozen experiment-001, agentsight): Claude record 313 of
`7ad7c67d-e6e3-4e64-afa1-4327e4497858.jsonl` carries
`"cwd": "/home/yunwei37/workspace/agentsight/collector"` and issues
`cat -n collector/src/view/mod.rs` (call `toolu_01QdMaxMofN8AJdpWurjqbnR`).
Lexical resolution against the event workdir yields
`agentsight/collector/collector/src/view/mod.rs` — a different artifact —
but the projection resolved against the session-initial cwd (repo root) and
attributed the read to P0 `collector/src/view/mod.rs`, inflating
agentsight-B1/B2 by one each.

Root cause: `agent-session/src/parser.rs` captured the row `cwd` only into the
session accumulator when it was still empty (`if acc.cwd.is_none()`), so every
tool event inherited the first record's cwd. Per-record cwd movement (Claude
rows, Codex `session_meta`/`turn_context` payload cwd) was discarded.

Fix (minimal, cwd precedence only — no refactor):

- `agent-session/src/parser.rs` (`parse_jsonl`): track `current_cwd`, updated
  on **every** record carrying `cwd`/`payload/cwd`; the session-initial
  `acc.cwd` is still recorded as before. The Claude and Codex tool-event
  construction now passes `current_cwd.or(acc.cwd)` as the fallback cwd, so
  precedence is: explicit input `workdir` > event record cwd > session-initial
  cwd. Relative operands are still resolved lexically downstream
  (`agentvis/src/repository.rs::resolve_path`), which excludes paths that
  escape the worktree — unchanged.
- No changes to `agentvis/src/repository.rs` production code, the oracle, or
  the answer layer were needed.

Regression tests (all pass):

- `agent-session/src/parser.rs`:
  `claude_event_workdir_overrides_session_cwd_for_relative_paths`
  (session cwd baseline, event-workdir move, explicit-input-workdir override),
  `codex_turn_context_event_workdir_overrides_session_cwd`.
- `agentvis/src/repository.rs`:
  `relative_operands_resolve_against_event_workdir_and_exclude_outside`
  (doubled-prefix resolution, outside-root workdir excluded, `..` escape
  excluded).
- Suites: agent-session 24/24, agentvis 55/55.

## Verification against the corrected v4 oracle

Projection rebuilt at the fix and re-extracted over the same frozen corpus
(`research-rq1 --cutoff-ms 1784758608524`, six roots,
`HOME=experiment-001/private/frozen-home`; output in `projection/raw/` here;
12/12 candidates for every project). The experiment's answer layer
(`proposed_edges`/`relation_values` @ `7e5464eca`, call-ledger session join,
0 unmapped events) was replayed over the new traces and scored against
`../corrected-oracle/corrected-answers.csv` (all 120 rows, full comparison in
`trajectory-vs-v4.csv`; replay script `rerun_workdir_fix.py`).

**Per-family totals (trajectory vs v4):**

| Family | Correct | Wrong | Abstain |
|---|---:|---:|---:|
| A | 12 | 18 | 0 |
| B | 30 | 0 | 0 |
| C | 30 | 0 | 0 |
| D | 30 | 0 | 0 |
| **B+C** | **60/60** | **0** | **0** |

Rows changed vs the pre-fix HEAD run — exactly the two target rows, nothing
else (full 120-row diff; no regression):

| Row | pre-fix | post-fix | v4 expected |
|---|---:|---:|---:|
| agentsight-B1 | 22 | 21 | 21 |
| agentsight-B2 | 18 | 17 | 17 |

Post-fix evidence event (projection/raw/events/agentsight.json, call
`toolu_01QdMaxMofN8AJdpWurjqbnR`):
`actions = [{"worktree_id": "e58fce112c6e", "path":
"collector/collector/src/view/mod.rs", "access": "read"}]` — the read now
lands on the doubly-nested path (its own artifact), not on P0.

**A-family note (out of scope):** A stays 12/30 vs the v4 oracle — the known
drop. The workdir fix changes **zero** A rows: A-family trajectory answers in
this answer layer come from the official ProcGrep atom arrays, and the
pre-fix→post-fix diff over all 120 rows touched only agentsight-B1/B2. The
A-vs-v4 mismatches originate in the v4 oracle's re-derived atom counts, not
in the projection.

## Code diff summary

- `agent-session/src/parser.rs` (+78/−9): `current_cwd` tracking in
  `parse_jsonl`, two call-site precedence changes (Claude, Codex), two
  regression tests.
- `agentvis/src/repository.rs` (+19/−0): one resolution/exclusion regression
  test; no production-code change.

## Bottom line

With the event-workdir fix, the HEAD projection's trajectory answers match the
corrected v4 source-direct oracle on **all 60 B+C questions (60/60)** and all
30 D questions, with a full-120-row comparison showing the fix touched exactly
the two agentsight rows it was meant to fix. Together with the three
hardening fixes verified earlier (session join, fail-drop, path extraction),
no known genuine projection bug remains against the corrected oracle.
