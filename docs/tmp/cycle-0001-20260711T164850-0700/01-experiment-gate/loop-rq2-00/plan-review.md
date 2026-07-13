# Plan Review — RQ2 Cross-Family Problem Localization

Review rounds are appended serially. A PASS before round 3 is provisional.

## Round 1 — 2026-07-11 — REVISE

### Scientific Findings

1. Pareto membership alone does not establish that output corresponds to real
   problems; every method could be near random. The plan needs an absolute
   correspondence criterion and a relative criterion matching the superiority
   claim.
2. AgentRewardBench, SATraj-OS, and AgentNet were already used in R403/R404 depth
   sweeps and cannot become untouched confirmatory families through a new split.
   AgentRx is the only proposed family that may still be confirmatory.
3. Group count and group-size distribution can create apparent work and
   fragmentation gains independently of semantics. The plan needs a matched
   partition control.
4. A name-based hidden-field denylist is inadequate because converters may expose
   outcome-derived proxy fields. The plan needs a deployment-time provenance
   allowlist.

### Required Plan Edits

- Add absolute thresholds versus random/prevalence and explicit relative
  superiority thresholds.
- Treat the three previously used families as development evidence; add untouched
  confirmatory data and a minimum usable-coverage rule.
- Materialize identical per-operation scores before grouping, use one identical
  aggregation rule across views, and add group-size/cardinality-matched controls.
- Define visible inputs by source provenance and exclude annotation-, result-, and
  outcome-derived values.

### Next Action

Revise the same plan and submit round 2 for external-precedent and baseline review.

## Round 2 — 2026-07-11 — REVISE

### Scientific Findings

1. AgentRx's public repository exposes 44 Magentic-One and 29 Tau ground-truth
   trajectories (73 across two domains), not all 115 trajectories/three domains
   described in the paper. The completion rule is feasible, but the primary
   positive must be the official root-cause failure step rather than every
   annotated recoverable failure.
2. TELBench's official `bare` and `drift` settings plus evaluator are the strongest
   same-task native baselines and must be run. AgentRx's native result must be run
   when a repository-supported backend is available or otherwise reported only as
   published context.
3. SQL `ROLLUP` levels overlap and cannot be pooled into one inspection ordering.
   SQL needs a disjoint partition and separately scored rollup levels.
4. TELBench has ordered spans but no native parent/child trace tree. A fixed-tree
   baseline must be concretely defined rather than asserted.
5. Matched partitions must preserve chronology and the exact AgentProf group-size
   multiset, not randomly shuffle operation membership.

### Required Plan Edits

Define AgentRx positives and public scope; add native DRIFT/bare rows; define
disjoint SQL and fixed sequential hierarchy baselines; use contiguous exact-size
matched partitions.

### Next Action

Revise the same plan and submit round 3 for metrics, data, leakage, and
executability review.

## Round 3 — 2026-07-11 — REVISE

### Scientific Findings

1. Reducing only work or only groups by 15% does not guarantee a better Pareto
   tradeoff if the other dimension becomes arbitrarily worse.
2. The current SQL/tag baseline does not receive the text/query representation
   used by AgentProf induction; a text-derived tag grouping is required for the
   “equally informed tag” comparison.
3. A development-only preflight does not exercise the new AgentRx/TELBench
   adapters, matched controls, or local official DRIFT path.
4. Allowing matched-control admission on “AP or work” creates an uncorrected
   metric-choice opportunity.

### Required Plan Edits

Add non-inferiority bounds to every relative-tradeoff branch; add a shared-score
text/query tag grouping; exercise unlabeled AgentRx/TELBench conversion plus one
official local DRIFT case during preflight; choose one primary matched-null metric.

### Next Action

Revise the plan and submit round 4 only for remaining decision-critical defects.

## Round 4 — 2026-07-11 — PASS

No decision-critical flaw remains. The plan now uses untouched AgentRx and
TELBench confirmation, credible fixed/SQL/tag/matched/native baselines, one
materialized ranker before grouping, provenance-based visible fields, absolute
correspondence and bounded tradeoff criteria, one matched-null primary metric,
and a real preflight covering every high-risk execution path.

### Next Action

Run the real preflight immediately. Preflight output is executability evidence
only and cannot support the paper claim.
