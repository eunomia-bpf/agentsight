# AgentReward 125-task rank-agreement experiment (RQ1) — results

## Question

On the complete frozen AgentReward operation hierarchy, does changing only the
additive measure (operation count vs provider-reported tokens) change which
recurring operations dominate?

This measures **rank agreement between two additive measures on a fixed
hierarchy**; low agreement means the chosen measure changes which operations
dominate.

## Population

- Frozen workspace: `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/`
  (`trace.jsonl`, 15,338 nodes: 440 session, 440 prompt, 7,229 llm, 7,229 tool).
- 440 sessions over **125 canonical tasks**; all 440 sessions parsed and all
  125 tasks retained (no session failed the mapping).
- Weighted source nodes: 7,229 llm nodes carry `metrics.tokens` only; 7,229
  tool nodes carry `metrics.operations = 1` only. Operation identity = deepest
  tag of the node's `path` (leaf variant); full path string for the
  path-level variant. Nodes reach their session by walking `parent` links.

## Task-ID provenance

Each session node's `data.source_session` is the sanitized label key
`<benchmark>__<task_id>__<model>` constructed by `Label.key` in
`script/agentreward_diff_pprof_eval.py:53-58`. The task ID is the middle
`__`-separated segment, canonicalized with `canonical_task_id()` from the same
script (`script/agentreward_diff_pprof_eval.py:90-91`):
`task_id.replace(".resized.", ".")`. The task key used here is
`<benchmark>/<canonical_task_id>`. All 440 `source_session` values split into
exactly 3 segments; this yields exactly 125 distinct canonical tasks, matching
the workspace README's "440 real trajectories across 125 mixed-outcome tasks".

## Method (as fixed by task-spec.md)

Per task, each operation identity's total operation count and total token mass
are aggregated over all sessions of that task; operations are ranked once by
count and once by tokens. Per-task Kendall's tau-b
(`scipy.stats.kendalltau`, which implements tau-b) and Spearman rho
(`scipy.stats.spearmanr`) are computed between the two rankings. Tasks with
fewer than 3 distinct operations are skipped. Aggregates are mean per-task
tau-b and rho with a 10,000-draw percentile bootstrap interval resampling
**tasks** (cluster bootstrap), seed 20260724 (`numpy.random.default_rng`).
Secondary analyses: pooled population-level ranking over all tasks combined,
and the same per-task procedure with full-path identity.

## Validity checks (report, not scores)

| Check | Value | Match |
|---|---|---|
| Operation mass, trace.jsonl | 7,229 | == workspace README's 7,229 operation samples: **yes** |
| Token mass, trace.jsonl | 51,904,621 | == sum of `stacks.folded` (51,904,621): **yes** |

## Headline numbers

### Primary: leaf operation name

- Tasks scored: **77**; tasks skipped (< 3 distinct operations): **48** of 125.
- Mean per-task Kendall tau-b: **0.8863**, 95% cluster-bootstrap CI
  **[0.8568, 0.9147]**.
- Mean per-task Spearman rho: **0.9350**, 95% CI **[0.9166, 0.9527]**.
- Median tau-b 0.9487; minimum per-task tau-b 0.552;
  10 of 77 scored tasks have tau-b < 0.7 (lowest:
  `webarena/webarena.718`, tau-b 0.552, rho 0.754, 6 operations).
- Pooled population-level ranking (30 distinct leaf operations):
  tau-b **0.9286**, rho **0.9878**. Top-5 by count vs by tokens agree on the
  top 4 in the same order (`recover interaction`, `search`, `navigate`,
  `inspect`) and differ at rank 5 (`configure` by count vs `research` by
  tokens).

### Secondary: full-path identity

- Tasks scored: **80**; skipped: **45** of 125.
- Mean per-task tau-b: **0.8741**, 95% CI **[0.8438, 0.9031]**; mean rho
  **0.9302**, 95% CI **[0.9109, 0.9484]**.
- Pooled: tau-b **0.8721**, rho **0.9743**. Top-5 paths by count and by
  tokens share 4 of 5 entries but in different order (e.g.
  `execute visual task / search` is rank 3 by count, rank 2 by tokens;
  `execute website task / recover interaction` is rank 2 by count, rank 4 by
  tokens).

Full per-task values and pooled top-10 lists are in `raw-results.json`.

## Interpretation (limited to what was measured)

On this fixed hierarchy, the two additive measures rank recurring operations
**similarly but not identically**. The dominant operations are largely stable
under a measure swap: pooled tau-b ≈ 0.87–0.93, and the same recovery/search/
navigation operations head both rankings. The agreement is not perfect,
though: about 13% of scored tasks (10/77 leaf, 12/80 path) show tau-b below
0.7, meaning that for those tasks the choice between counting operations and
counting tokens changes which operations dominate the profile. Caveats: 48 of
125 tasks (38%) are too small (fewer than 3 distinct operations) to rank at
all, so the per-task means describe only the 77 operationally diverse tasks;
token mass is concentrated on llm nodes while operation counts live on tool
nodes, so agreement partly reflects that high-traffic operations generate
both. This is rank-agreement evidence only — it does not by itself say which
measure is more faithful to any cost an engineer cares about.
