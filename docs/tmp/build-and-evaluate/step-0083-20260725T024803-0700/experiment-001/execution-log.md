# Execution log — step 0083 experiment-001 (HINTBench index-study replication)

All commands run from the repository root unless noted. No git commands were
run; no existing repository file was modified. All outputs were written only
inside this experiment directory.

## Phase 1 — frozen input verification (read-only)

Verified presence and population alignment of every frozen HINTBench input
(documented in `script/rq2_current_agent_local_first.py` provenance):

- Source packets: `.agentsight/experiments/rq2-a0-v1/full/hint/packets/batch-01..08.json`
  — 536 sessions, schema identical to the TraceElephant packets
  (`task`, `operations[]` with `operation_id`, `ordinal`, `native_path`,
  `source_summary`). Packet operation order == projection `display_id` order
  for all 536 trajectories.
- Operation projection with stable IDs:
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/operations/test-projection.jsonl`
  — 12,877 operations, 536 record_keys.
- Annotated targets:
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/sources/test.json`
  — targets extracted exactly as `load_labels('hint')`
  (`injected_risks`/`risk_labels` → `risk_origin_step`/`step_id`, matched on
  `display_id`): 400 target-bearing queries, 136 zero-positive.
- Stored per-query AP (local_only, local_agentprof):
  `.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
  — 400 HINTBench rows; query ids, target counts, and strata
  (`raw_fields.environment`) match the recomputed labels exactly. Stored MAP:
  local_only 0.4105587754001585, local_agentprof 0.5174888725910552.
- Semantic group mapping:
  `.agentsight/experiments/rq2-canonical-tags-v2-current/hint/results/fixed-groups.jsonl`
  — 12,877 rows; `source_preserving_agent` extends `automatic_agent` by
  exactly 3 source-evidence frames everywhere.
- Raw identity: `raw_fields.action` of the same frozen projection (the
  HINTBench equivalent of method-index `methods.raw.operation_leaves`;
  `load_hint_sources` reads exactly this field). 412 unique raw actions.

Packet-size audit: full-trace packets min 3,279 / median 11,574 / max 20,466
chars — all far below ARG_MAX, so `kimi -p` argv delivery covers the complete
population and no prompt-file fallback is needed.

## Phase 2 — reader CLI check

- `kimi --version` → 0.29.1 at `/home/yunwei37/.local/bin/kimi`.
- Default model `kimi-code/k3` (`~/.kimi-code/config.toml`), pinned explicitly
  with `-m kimi-code/k3`.
- Smoke test: `kimi -p 'Return ONLY strict JSON: {"ok": true}'` → rc=0,
  stdout `• {"ok": true}` in ~7 s. The `• ` prefix is tolerated by the JSON
  extractor (first-`{`-to-last-`}` span).
- Fixed reader invocation: `kimi -p <packet+instruction> -m kimi-code/k3
  --output-format text --skills-dir <empty-dir>`, cwd = dedicated empty
  directory (`kimi-cwd/`) so no project AGENTS.md, skills, or workspace files
  enter the reader context. stdin = /dev/null. Timeout 900 s per call.

## Phase 3 — harness

- `hint_index_study_eval.py` written (adapted from the frozen step-0079
  `direct_reader_eval.py`, step-0080 `profile_reader_eval.py`, and step-0081
  `raw_action_reader_eval.py`; instruction texts verbatim, parsers/fallbacks/
  bootstrap identical). `python3 -m py_compile` → OK.

## Phase 4 — validation (≤3 queries, never reported as a result)

- Command: `python3 hint_index_study_eval.py validate --workers 8`
  (log: `validate.stdout.log`, summary: `validate-summary.json`)
- First attempt failed on a harness driver bug (`op_paths` not passed to the
  two-stage processor; fixed in `hint_index_study_eval.py`, recompiled,
  re-run). No reader output was produced by the failed attempt.
- Re-run: rc=0, 9/9 work items complete in 113.4 s wall. All stages parsed
  OK on first attempt (no retries, no fallbacks). Mean validation APs
  (3 queries, NOT a result): full 0.803, semantic 0.519, raw 0.736.
  Spot-checked raw responses: strict JSON, valid IDs, `• ` stdout prefix
  handled by the extractor. Prompt token counts (o200k_base) recorded per
  attempt.

## Phase 5 — full population run

- Command: `python3 hint_index_study_eval.py full --workers 12`
  (log: `full-run.stdout.log`; 1,200 work items = 400 queries × 3
  conditions; the 9 validation items are reused from cache).
- Worker pool: 12 concurrent reader processes (bounded ThreadPoolExecutor).
- Result: see below (filled in after completion).
