# Task spec: raw-action skeleton control on TraceElephant (RQ2)

You are an autonomous engineering agent executing ONE fixed experiment inside
the repository `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Scientific question (fixed — do not change)

Holding the two-stage profile-guided reading protocol of step 0080 fixed,
does replacing the semantic operation paths in the skeleton with raw action
labels degrade attention concentration (lower MAP and/or more source content
opened)? This isolates whether semantic naming itself — not grouping plus
drilldown in general — directs a strong reader's attention.

## Baseline to replicate exactly

Step 0080: `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/`
Reuse its harness structure, provenance, scoring, and fallback rules. Its
`profile_reader_eval.py` may be COPIED into this directory and minimally
modified; never edit the original.

## The single manipulated variable

Stage-1 and stage-2 skeletons group operations by RAW ACTION identity instead
of semantic operation path:

- Use the same raw-action identity that the step-0072 Direct+Raw+Evidence
  information-matched baseline used for TraceElephant. Look for it in the
  frozen step-0072 artifacts (e.g. `fixed-groups.jsonl` fields adjacent to
  `source_preserving_agent`, or the projection's native action field —
  confirm which field step 0072's raw-action condition actually read by
  inspecting `.agentsight/experiments/rq2-canonical-tags-v2-current/` and
  `rq2-current-agent-local-first-v1/` provenance, and document the exact
  field and file in results.md). If you cannot determine the exact frozen
  raw-action identity, STOP and write results.md explaining what you found.
- Skeleton lines list each raw-action group and its member ordinals/IDs,
  exactly mirroring step 0080's format otherwise.
- Everything else is byte-identical in spirit: task text, operation_id,
  ordinal, ≤5-group stage-1 selection, stage-2 source_summary for selected
  groups' members only, same reader flags, same one-retry rules, same
  deterministic fallbacks and completion.

## Scoring and comparisons (identical machinery to 0080)

- sklearn non-interpolated AP per query; MAP over 220 queries.
- Paired deltas (10,000 trajectory-cluster resamples within strata, fixed
  seeds you document) against: profile_reader (step 0080), direct_reader
  (step 0079), local_agentprof, local_only.
- Cost table exactly as step 0080, including mean/median content-opened
  fraction and mean selected evidence operations and groups available.
- Also report: number of raw-action groups per trajectory (mean/median) and
  the size of the largest group, next to step 0080's 13.70 mean groups.

## Deliverables (all inside THIS directory)

- `raw_action_reader_eval.py`, `packets-stage1/`, `packets-stage2/`,
  `raw-responses/`, `raw-results.json`, `results.md`, `execution-log.md` —
  same structure and content requirements as step 0080, plus the raw-action
  identity provenance note.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command. NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- No target, outcome, judge, or localizer signal in any packet.
- Complete 220-query run; ≤3-query validation never reported as a result.
