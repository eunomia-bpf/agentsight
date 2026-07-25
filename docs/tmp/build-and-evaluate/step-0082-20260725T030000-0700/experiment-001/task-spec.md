# Task spec: profile-guided reader v2 on TraceElephant (lean + widths)

You are an autonomous engineering agent executing ONE fixed experiment inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Baseline to modify

Step 0080: `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/`.
COPY its harness into this directory and apply ONLY the two protocol changes
below. Same frozen inputs and provenance (semantic group mapping =
`.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
field `source_preserving_agent`), same reader CLI and flags, same one-retry
and fallback rules, same deterministic completion, same scoring and paired
bootstrap machinery.

## Change A — width-annotated stage-1 skeleton

Each group line additionally carries, computed from the frozen projection
and packets (no new sources): member operation count, and the group's
additive mass for whichever additive measure the frozen artifacts expose
(token mass if present in the projection/workspace records; otherwise
operation count only — document which). Format example:
`<semantic path>  [ops=12, tokens=48213]  members: <ordinals/IDs>`.
Stage-1 instruction unchanged: select up to 5 groups, ordered, strict JSON.

## Change B — lean stage 2

Stage-2 packet contains ONLY: the task text, and for each member operation
of the selected groups its operation_id, ordinal, and source_summary. NO
skeleton re-send, NO paths for unopened operations. Instruction: rank the
opened operation IDs (most likely responsible first), strict JSON; the
deterministic completion appends all unopened operations in original trace
order exactly as in step 0080.

## Measurement additions

- Compute logical token counts per packet with tiktoken `o200k_base` inside
  the harness (stage-1, stage-2, total per query) and report mean/median
  alongside: step-0079 full-trace mean 12,615 tokens/query and step-0080
  two-stage mean 15,991 tokens/query.
- Report content-opened fraction exactly as step 0080 (stage-2 evidence
  chars / step-0079 full packet chars).

## Scoring and comparisons

- sklearn non-interpolated AP; MAP over the complete 220 queries.
- Paired deltas (10,000 trajectory-cluster resamples within strata,
  documented seeds) vs: profile_reader (0080), raw_action_reader (0081,
  `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/raw-results.json`),
  direct_reader (0079), local_agentprof, local_only.
- Index-hit rate: recompute the step-0080 analysis-001 hit definition
  (every target operation's group among selected groups) for this run and
  report next to 0080's 154/220.

## Deliverables (all inside THIS directory)

`profile_reader_v2_eval.py`, `packets-stage1/`, `packets-stage2/`,
`raw-responses/`, `raw-results.json`, `results.md` (with the registered
targets from `000-step-entry.md` explicitly evaluated: MAP >= 0.48; total
logical tokens < 12,615/query; content opened <= 53%), `execution-log.md`.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command (including `git stash`).
- NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- No target, outcome, judge, or localizer signal in any packet.
- Complete 220-query run; <=3-query validation never reported as a result.
