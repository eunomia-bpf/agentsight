# Task spec: AgentReward 125-task rank-agreement experiment (RQ1)

You are an autonomous engineering agent executing ONE fixed experiment inside
the repository `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Scientific question (fixed — do not change)

On the complete frozen AgentReward operation hierarchy, does changing only the
additive measure (operation count vs provider-reported tokens) change which
recurring operations dominate? This is RQ1 (resource attribution) evidence.

## Input (read-only)

- Frozen annotation workspace:
  `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/trace.jsonl`
  (also `annotation.json`, `stacks.folded` in the same directory, and the
  workspace `README.md` one level up).
- Each trace node has: `id`, `parent`, `kind`, `data`, `metrics`
  (with `operations` and `tokens`), and a derived `path` (list of semantic
  operation tags).
- The population is 440 sessions over 125 tasks. Session-to-task mapping:
  discover it from the workspace README, the session `data` fields, or the
  pair manifest used by `script/agentreward_diff_pprof_eval.py` (READ ONLY —
  never modify that script). Document exactly where the task ID came from.

## Method (fixed)

1. For every weighted source node (operations > 0 or tokens > 0), its
   operation identity is the deepest semantic tag of its `path` (the leaf
   operation name). Also record the full path for a secondary path-level
   variant.
2. Per task (125 tasks): aggregate, over all sessions of that task, each
   operation name's total operation count and total token mass. Rank the
   operations of that task once by count and once by tokens.
3. Compute per-task Kendall's tau-b between the two rankings (standard
   definition; use scipy.stats.kendalltau which implements tau-b) and the
   corresponding Spearman rho (scipy.stats.spearmanr). Skip tasks with fewer
   than 3 distinct operations and report how many were skipped.
4. Aggregate: mean per-task tau-b and rho, each with a 10,000-draw bootstrap
   interval that resamples TASKS (cluster bootstrap), percentile method,
   fixed seed 20260724.
5. Secondary (same procedure): (a) pooled population-level ranking over all
   tasks combined; (b) path-level identity (full semantic path string)
   instead of leaf name.
6. Validity checks (report, not scores): total operation mass and token mass
   must equal the workspace totals; report them.

## Deliverables (all inside THIS directory)

- `rank_agreement_eval.py` — the complete script (stdlib + numpy/scipy only).
- `raw-results.json` — per-task tau-b/rho values plus aggregates.
- `results.md` — population description, exact provenance of the task
  mapping, the headline numbers with intervals, skipped-task count, validity
  checks, and an honest interpretation limited to what was measured. State
  clearly: this measures rank agreement between two additive measures on a
  fixed hierarchy; low agreement means the chosen measure changes which
  operations dominate.
- `execution-log.md` — commands you ran and their wall time.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command (no add/commit/push/checkout/reset).
- NEVER touch `docs/agentpprof-paper/` (submodule) or `docs/paper/`.
- Run the COMPLETE population (all 440 sessions, all eligible tasks).
- Use only standard metrics as specified; do not invent a composite score.
- If the task mapping cannot be established for some sessions, stop and
  write what you found into `results.md` rather than guessing.
