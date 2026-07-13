# RQ2 Revision-0 Final Result Review

## Final Verdict

- **Evidence validity:** PASS.
- **Validity classification:** admitted.
- **Claim effect:** contradictory.
- **Approved completion rule:** satisfied.
- **Immutable RQ:** “Does profiler output correspond to real problems?”

Revision 0 closes here. The experiment is complete and scientifically usable,
but it falsifies the current positive mechanism claim. This does not authorize
narrowing the RQ or removing the multi-resolution semantic profiling
contribution. It authorizes conclusion-claim revision 1 under the same RQ.

## Independent Evidence Check

A fresh reviewer independently rebuilt all 20 methods for AgentRx and TELBench
across checks 410–412, all 600 matched-null rows, and the seed-410 1,000-draw
bootstrap streams from official labels and raw groups. It found zero coverage,
duplication, metric, cardinality, ordering, or bootstrap mismatches.

Completed matrix:

- development: 540/540 cells, five tasks, three deterministic checks;
- AgentRx: 73/73 trajectories, 3,265 operations, 73 positives, Tau and
  Magentic-One;
- TELBench: 1,000/1,000 cases, 11,934 spans, 2,552 positives;
- matched controls: 100 per family/check, 300 pooled per family;
- actual induction engagement: 160 AgentRx and 621 TELBench splits.

The separate-process visible projection and post-materialization label boundary
passed review. Official annotated-trajectory membership selected the 73 AgentRx
evaluation trajectories, but failure locations and TELBench error labels first
entered after all deployable rankings were materialized.

## Claim Decision

AgentRx induced AP is 0.02584 at prevalence 0.02236; AP-minus-prevalence has
95% interval [-0.00035, 0.00798], recall within 30% work is 0.3425, and the tag
baseline needs less work and one rather than 32 groups at 25% recall.

TELBench induced AP is 0.21487 at prevalence 0.21384; AP-minus-prevalence has
95% interval [-0.00718, 0.01804], recall within 30% work is 0.1900, and the
session baseline has higher AP and needs 0.236 rather than 0.646 work at 25%
recall. Width-only ordering also dominates the learned-risk leaf ordering.

Both matched-null intervals include equality in the required direction. All
three predeclared criteria—absolute correspondence, relative Pareto advantage,
and semantic grouping beyond cardinality—fail on both families. This is a
strong contradictory result, not an inconclusive one.

## Native TELBench Context

Both official bare and DRIFT paths produced exactly 1,000 unique runs,
predictions, and evaluator rows with no missing or extra IDs.

| Setting | Macro-F1 | Micro-F1 | First-error accuracy | Fallbacks | Total tokens |
|---|---:|---:|---:|---:|---:|
| bare | 0.1521 | 0.1704 | 0.0900 | 51 | 4,426,588 |
| DRIFT | 0.3655 | 0.3793 | 0.1270 | 167 | 10,235,927 |

The no-fallback intersection contains 824 cases. On the same official evaluator,
bare/DRIFT macro-F1 is 0.1655/0.3930 and micro-F1 is 0.1834/0.3962. These rows
are valid contextual end-to-end evidence, including runtime/model failures, but
fallback rates of 5.1% and 16.7% prevent treating them as a clean
algorithm-only comparison. They do not determine the grouping claim.

## Disclosed Deviations

- Native worker concurrency changed only at completed 100-case recovery
  boundaries: 8, then 16, then 32. Scientific inputs stayed fixed.
- SQL controls are separately scored SQLite prefix `GROUP BY` views, not the
  `ROLLUP` keyword.
- Secondary cold/warm timing and formatted per-domain/top-5 tables are not in
  the primary report. Raw per-domain results exist; these omissions cannot
  rescue the failed predeclared criteria.
- The standalone native JSON predates the clean-intersection sensitivity;
  `full-results.json`, the sensitivity artifact, and the full report contain the
  authoritative combined state.

## Transition to Claim Revision 1

Return to PROPOSE for the same RQ. The source-backed principle is **scope before
localization**: retain and navigate internal semantic scopes rather than
flattening the operation stack into leaf partitions.

Revision 1 should test a query- and risk-conditioned coarse-to-fine semantic
profile tree with internal-node Hit@K and downstream exact localization. The
current AgentRx/TELBench outcomes have informed mechanism design, so they become
development/diagnostic and external-replication families. Use the qualified
fresh official confirmation assets:

- Who&When: 184 multi-agent failure trajectories;
- TRAIL: 148 GAIA and SWE-Bench traces with exact error spans.

Write a new experiment plan, review it for three to five rounds, run a real
preflight, execute the complete fresh matrix, and independently review the
result. Do not retune revision 0, change the RQ, or replace the ambitious
multi-resolution contribution with a leaf-grouping proxy.
