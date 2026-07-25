# Task spec: profile-guided reader on TraceElephant (RQ2/RQ4)

You are an autonomous engineering agent executing ONE fixed experiment inside
the repository `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Scientific question (fixed — do not change)

Does the once-built semantic profile act as an index for a strong query-aware
reader: retaining ranking quality while reading materially less trajectory
content than the full-trace reader of step 0079?

## Inputs (all read-only, all frozen)

- Everything step 0079 used (reuse its located provenance; see
  `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/results.md`):
  packets source fields, `projection.jsonl` operations and stable IDs,
  `targets.jsonl`, stored per-query AP for Direct-only (`local_only`),
  Direct+AgentProf (`local_agentprof`).
- Step 0079's own per-query results
  (`step-0079-.../experiment-001/raw-results.json`): the `direct_reader` AP
  per query and per-query packet_chars/wall_seconds, for paired comparison.
- The frozen target-blind semantic group assignment used by the step-0072
  Agent+Evidence condition (the operation -> semantic operation path mapping
  on TraceElephant). Locate it under `.agentsight/experiments/` (the
  step-0072 artifacts reference it; `rq2-a0-v1` and
  `rq2-current-agent-local-first-v1` are the places to look). If a complete
  per-operation semantic path mapping cannot be located, STOP and write what
  you found into `results.md`. Do not construct new groups.

## Protocol (fixed): two single-turn stages per query

Reader = `grok` CLI, identical fixed decoding flags as step 0079
(`--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`,
`-p`/`--prompt-file`), one format retry per stage.

**Stage 1 — profile skeleton (no source content).** Packet contains:
1. the benchmark task/query text;
2. the trajectory's profile skeleton: every operation's `operation_id`,
   ordinal, and its semantic operation path from the frozen mapping, grouped
   by path prefix (one line per group listing its member ordinals/IDs);
   NO source_summary, NO native free text.
Instruction: select up to 5 groups (path prefixes) most likely to contain
the decisive mistake, as strict JSON.

**Stage 2 — focused evidence.** Packet contains:
1. the same task text and profile skeleton;
2. full `source_summary` (as used in step 0079 packets) for ONLY the member
   operations of the stage-1 selected groups.
Instruction: return a ranked list of source operation IDs (most likely
responsible first), strict JSON, same as step 0079.

Deterministic completion: operations not ranked by the reader are appended
in original trace order. If stage 1 fails twice, fall back to selecting the
largest 5 groups (deterministic) and tally it; if stage 2 fails twice, score
original-order and tally it.

## Scoring (identical to 0072/0079)

- sklearn non-interpolated AP per query from the completed ranking; MAP over
  all 220 target-bearing queries.
- Paired deltas vs `direct_reader` (0079), `local_agentprof`, `local_only`:
  10,000 paired resamples of trajectory clusters within benchmark strata,
  fixed seeds, report point delta and 95% interval for each.
- Cost: per-query stage-1 chars, stage-2 chars, total chars, wall seconds;
  report mean/median totals side by side with step 0079's (44,589 mean
  chars, 29.9 s mean). Also report the fraction of trajectory source
  content opened (stage-2 evidence chars / step-0079 full packet chars).

## Deliverables (all inside THIS directory)

- `profile_reader_eval.py` — complete harness.
- `packets-stage1/`, `packets-stage2/`, `raw-responses/` — exact artifacts.
- `raw-results.json` — per-query AP, selections, costs, paired deltas.
- `results.md` — provenance (exact path of the group mapping), MAP table
  (this condition vs direct_reader vs local_agentprof vs local_only), paired
  intervals, cost table with the content-opened fraction, failure tallies,
  honest interpretation scoped to what was measured.
- `execution-log.md` — commands and wall time.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command. NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- No target, outcome, judge, or localizer signal in any reader packet:
  stage-1/stage-2 packets carry only task text, operation IDs/ordinals,
  semantic paths, and (stage 2, selected groups only) source_summary.
- Complete 220-query run; ≤3-query validation never reported as a result.
