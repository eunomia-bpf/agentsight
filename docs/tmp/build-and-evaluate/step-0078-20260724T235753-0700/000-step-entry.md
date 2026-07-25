# Step 0078 entry: RQ1 population-scale rank agreement (delegated to kimi)

Timestamp: 2026-07-24T23:57:53-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `kimi` CLI agent, orchestrated by the root session

## Why this step exists

The RQ evidence audit (step 0077, `rq-evidence-audit.md`) requires that the
final RQ1 package not rely on the single Git case alone:

> Reuse the complete 125-task AgentReward population and its frozen operation
> hierarchy to rank the same operations once by count and once by provider
> tokens. Report per-task Kendall's tau-b (with a task-cluster bootstrap
> interval) and the corresponding Spearman correlation as standard
> rank-agreement measurements.

This tests at population scale whether changing only the additive measure
changes which recurring responsibilities dominate. It is a deterministic
computation over the already frozen annotation workspace; no LLM, no new
annotation, no outcome labels.

## Fixed constraints

- RQ1 subject unchanged: resource attribution. No RQ rewording.
- Population fixed: the frozen 440-session AgentReward workspace at
  `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/`.
- Standard metrics only: Kendall's tau-b and Spearman rank correlation,
  with a 10,000-draw task-cluster bootstrap interval.
- Complete run over all 125 mixed-outcome tasks; no smoke-only subset.
- The executor must not modify any existing repository file, must not run
  any git command, and must not touch the `docs/agentpprof-paper/` submodule.
- All new files stay inside this step directory.

The full task specification given to the executor is in
`experiment-001/task-spec.md`. Raw results and the executor's report land in
`experiment-001/`. Result review follows in this directory before any paper
use.
