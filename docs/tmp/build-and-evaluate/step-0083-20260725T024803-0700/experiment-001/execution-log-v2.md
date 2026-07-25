# Execution log (v2) — step 0083 experiment-001 (opencode reader)

This log documents ONLY the v2 phase (addendum-001 reader change after kimi
quota exhaustion; addendum-002 prescriptive reader recipe). It is a NEW file;
the original `execution-log.md` (kimi phase) is left untouched per the hard
constraint "never modify existing files." All commands run from the repository
root or the experiment directory. No git commands were run; no existing
repository file was modified; no CLI-tool configuration or home directory was
inspected, read, or modified.

## v2 Phase 0 — context inherited from the kimi attempt

- The frozen HINTBench inputs, packet-size audit, frozen loaders, packet
  builders, parsers/fallbacks, AP/MAP machinery, and paired bootstrap are all
  unchanged from the kimi harness (`hint_index_study_eval.py`, documented in
  `execution-log.md` phases 1–3). They were re-verified at v2 harness load
  time by the same `require(...)` population checks (536 trajectories,
  12,877 operations, 400 target-bearing queries, 136 zero-positive).
- Kimi partials are SET ASIDE, not scored and not deleted: `raw-responses-full`
  (400), `raw-responses-semantic` (52), `raw-responses-raw` (3). Only the
  `raw-responses-*-v2` opencode outputs are scored.

## v2 Phase 1 — reader recipe (addendum-002)

- `opencode --version` → 1.17.18. Reader invocation is EXACTLY
  `opencode run --pure "<packet+instruction>"`, executed via `subprocess.run`
  with `cwd=<experiment-001>/reader-jail` (a fresh EMPTY directory created
  once with `mkdir -p reader-jail`), `stdin=/dev/null`, `capture_output=True`.
  No `-m`/`--agent`/`--command`/`--format` flags are added (addendum-002
  forbids invented flags and any config/agent-file touch).
- Observed default model: `glm-5.2` (from the `> build · glm-5.2` banner opencode
  writes to stderr; recorded per-attempt in `meta.reader_default_model`).
- Smoke test (1 trivial call, NOT a reported result): rc=0, ~5 s, clean JSON on
  stdout, no ANSI/prefix; the `> build · glm-5.2` banner goes to stderr. An
  inotify `No space left on device` warning appears on stderr (inotify
  watch-limit, not disk); harmless, does not affect stdout.
- Per-call timeout 600 s. argv delivery is used for every call (all HINTBench
  prompts < 30 KiB, far below the 128 KiB single-argv-string limit and the
  2 MiB ARG_MAX); the addendum-002 `prompt.txt` fallback is therefore never
  triggered (`meta.argv_fallback_triggered` is recorded False for every
  attempt, and the largest prompt is audited in the summary).

## v2 Phase 2 — harness (`hint_index_study_eval_v2.py`)

- Adapted from `hint_index_study_eval.py` with ONLY the changes below
  (everything else byte-identical in logic):
  1. `call_opencode` replaces `call_kimi` (Phase 1 recipe above).
  2. `build_prompt` appends the addendum-002 closing sentence to EVERY packet
     (initial + retry): "Answer directly in strict JSON only. Do not use any
     tools, do not read or write any files, do not run any commands."
  3. `extract_json_object` now returns the FIRST JSON object in stdout
     (balanced-brace scan, ANSI stripped; fenced ```json preferred) per
     addendum-002 point 4. Self-tested on 8 cases (plain, leading-prose,
     ANSI+bullet, fenced, nested-brace-in-string, array-only→None, empty→None,
     two-objects-first-wins).
  4. Outputs go to NEW `*-v2` paths: `packets-*-v2/`, `raw-responses-*-v2/`,
     `bootstrap-*-v2.json`, `raw-results-v2.json`, `summary-v2.json`,
     `validate-summary-v2.json`. No existing file is modified.
  5. Conditions run SEQUENTIALLY (full → semantic → raw), each as its own
     parallel `ThreadPoolExecutor` phase with resume (cached v2 responses are
     reused on re-entry), then scored together (`score_all`).
  6. `validate` mode runs full-trace only on `--validate-n` queries and records
     `parse_ok` / `recipe_pass` (>=2/3).
- `python3 -m py_compile` → OK.

## v2 Phase 3 — validation (≤3 queries, never reported as a result)

- Command: `python3 hint_index_study_eval_v2.py validate --workers 3`
  (log: `validate-v2.stdout.log` / `validate-v2.stderr.log`).
- Result: rc=0, 3/3 work items complete in 61.5 s wall. All three parsed OK on
  the first attempt (no retries, no fallbacks). `parse_ok=3/3`,
  `recipe_pass=True` → the full run may proceed (addendum-002 point 5).
- Mean validation AP (3 queries, NOT a result): full-trace 0.6778.
- Leakage scan of the 3 raw responses for repo paths / target identifiers
  (regex: agentsight, .agentsight, docs/tmp, reader-jail, /home/yunwei,
  raw-responses, hint_index_study, HINTBench, fixed-groups): 0 hits.

## v2 Phase 4 — full sequential run

- Command: `setsid nohup python3 -u hint_index_study_eval_v2.py full --workers 8
  > full-run-v2.stdout.log 2> full-run-v2.stderr.log < /dev/null &`
  (detached; resume support means an interrupted condition is completed rather
  than restarted).
- Worker pool: 8 concurrent `opencode run --pure` processes per phase.
- Resume at launch: full-trace phase reported `to_call=397 cached=3` (the 3
  validation queries are reused).
- Conditions run in order: phase1 full-trace (400), phase2 semantic-skeleton
  (400, two-stage), phase3 raw-action-skeleton (400, two-stage). Scoring
  (MAP, paired 10,000-draw trajectory-cluster bootstrap with the frozen seeds,
  content-efficiency delta, costs, index-hit) runs once after phase3.
- Final wall (from `full-run-v2.stdout.log`): harness 7,627.6 s (~2.12 h);
  phase1 full-trace 400/400 at elapsed 1,617 s; phase2 semantic 400/400 at
  elapsed 4,661 s; phase3 raw 400/400 at elapsed 7,617 s; `[score]` line at
  7,627.6 s. **0 errors** across all 1,200 work items (plus 3 reused
  validation items).
- Deterministic-fallback tally: 0 full-trace original-order failures; 0
  stage-1 largest-groups fallbacks; 0 stage-2 original-order failures; 1
  full-trace and 1 raw query used the single format retry then parsed
  (`ok_after_retry`); semantic parsed first-try on all 400.
- Stored-MAP reproduction: `local_only` 0.4105587754001585 and
  `local_agentprof` 0.5174888725910552 both reproduced to < 1e-12.
- Final MAP: full-trace 0.623466, raw-action-skeleton 0.554539,
  semantic-skeleton 0.527282, Direct+AgentProf 0.517489, Direct-only 0.410559.
  Full pairwise table, content deltas, costs, and the explicit evaluation of
  the two registered hypotheses are in `results.md`.

## v2 Phase 5 — leakage spot-check and deliverables

- Leakage spot-check (addendum-001 point 1): 12 responses sampled across
  `raw-responses-{full,semantic,raw}-v2/` (seed 20260830); scanned for
  repository paths, target files, benchmark identifiers, and CLI config paths
  (regex: agentsight, .agentsight, docs/tmp, reader-jail, /home/yunwei,
  raw-responses, hint_index_study, HINTBench, fixed-groups, .claude,
  .config/opencode, rq2-, cycle-0003). **0 hits.** The reader-jail worked;
  the packet was the only input.
- Deliverables written (all NEW files; no existing file modified):
  `hint_index_study_eval_v2.py`, `packets-*-v2/`, `raw-responses-*-v2/`,
  `raw-results-v2.json`, `summary-v2.json`, `bootstrap-deltas-*-v2.json` (10),
  `bootstrap-content-delta-*-v2.json` (3), `validate-summary-v2.json`,
  `validate-v2.stdout.log`, `validate-v2.stderr.log`, `full-run-v2.stdout.log`,
  `full-run-v2.stderr.log`, `reader-jail/`, `results.md`, this
  `execution-log-v2.md`. The kimi-phase `execution-log.md` and all kimi
  `raw-responses-*` (no `-v2`) are left untouched (set aside, not scored).
