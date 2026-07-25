# Step 0078 result review

Timestamp: 2026-07-25T00:20:00-07:00
Reviewer: root orchestrator session
Verdict: ACCEPTED as bounded RQ1 supporting evidence

## Verification performed

- Reproducibility: re-ran `rank_agreement_eval.py` on the frozen workspace;
  `raw-results.json` md5 identical before and after
  (`bdde0a2ede798bf4bae0f6b71fa52c82`).
- Mass conservation: 7,229 operations and 51,904,621 tokens match the
  workspace README and `stacks.folded` sum exactly.
- Task-mapping provenance is documented against
  `script/agentreward_diff_pprof_eval.py` (read-only) and yields exactly the
  125 canonical tasks the workspace README declares.
- The executor's mid-run median discrepancy (0.9316 vs 0.9487) was caught and
  corrected by the executor before finalizing `results.md`; the final file
  matches `raw-results.json`.
- No existing repository file was modified; no git command was run
  (executor log confirms; working tree shows only new files in this step).

## Admissible claim (exact scope)

On the frozen 440-session/125-task AgentReward hierarchy, ranking the same
operations by operation count versus provider-reported tokens yields high but
imperfect rank agreement: mean per-task Kendall tau-b 0.886 [0.857, 0.915],
Spearman 0.935 [0.917, 0.953], pooled tau-b 0.929. In 10 of 77 rankable tasks
(13%), tau-b falls below 0.7, so the additive-measure choice changes which
operations dominate those tasks' profiles. 48 of 125 tasks have fewer than 3
distinct operations and cannot be ranked.

## What this does and does not support

- Supports: the fixed hierarchy replays under both measures with exact
  conservation; dominance is stable for most web-scale tasks; a measurable
  minority of tasks (and, separately, the long-horizon Git case) change
  dominant operations under a measure swap, which is where multi-measure
  replay has attribution value.
- Does not support: a universal claim that measure choice usually changes
  dominance at population scale. The paper must not state the population
  result as large divergence; the Git case remains the divergence exemplar
  and this result bounds how often such divergence occurs in this population.
- Structural caveat carried into any paper text: token mass concentrates on
  LLM nodes while counts concentrate on tool nodes, so high agreement partly
  reflects volume correlation.
