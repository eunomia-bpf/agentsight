# Independent Experiment-Plan Review

**Round 1 completed:** 2026-07-16

**Reviewer:** independent subagent using `research-experiment-design`; read-only,
with no Git operation and no access to the paper submodule.

**Verdict:** **REVISE**

## Must-Fix Findings

1. **State the evaluated population accurately.** The released manifest
   contains 468 failed trajectories. The experiment's 405 trajectories are the
   complete pre-existing source-valid target population fixed in Step 0024
   before token analysis, not every failed trajectory in the release. The plan
   must report 405/468 and a minimal included-versus-excluded audit by framework
   and step count. It must not reconstruct excluded trajectories for this
   experiment.
2. **Use a truthful raw-action baseline.** The existing `action_change` field
   changes on normalized semantic action kind, not raw source identity. The
   source-native raw identity is the already-materialized `raw_action_key`.
   Construct the main contiguous baseline from changes in `raw_action_key` and
   retain `action_change`, if useful, only as an action-kind ablation.
3. **Cluster uncertainty by benchmark task.** The 405 trajectories represent
   251 distinct tasks, with up to five trajectories per task. The paired
   bootstrap must therefore resample tasks and retain all trajectories for
   each sampled task. A positive point delta whose confidence interval includes
   zero is inconclusive, not contradictory.
4. **Audit the equal split of multi-operation responses.** Report the count and
   token mass of responses that produce multiple official operations and
   whether those operations cross the gold or primary predicted partitions.
   If no response crosses, the split is irrelevant. If crossings exist, report
   an allocation-sensitivity analysis; a primary verdict that changes with the
   allocation is inconclusive.

## Accepted Parts

- The hypothesis and fixed RQ match.
- CodeTraceBench human stages are independent of the proposed partition.
- Ordinary B-cubed is an appropriate partition metric.
- The published weighted B-cubed extension is a reasonable resource-weighted
  secondary analysis when it is described as an extension rather than a
  universal token-attribution standard.
- The reuse-only adapter, source-recovery checks, controls, and phase/session
  roles are appropriate.
- No additional workload, baseline family, or new agent execution is needed.

## Revision Disposition

All four must-fix findings are accepted. In addition, in response to the
author's explicit instruction to use standard metrics, ordinary operation-level
B-cubed F1 becomes the primary decision metric. Token-weighted B-cubed becomes
a resource-sensitive secondary analysis, and no custom composite score is
admitted.

## Round 2

**Completed:** 2026-07-16

**Verdict:** **REVISE**

The reviewer confirmed that all four Round-1 findings were closed and accepted
the metric suite as concise rather than metric soup. One interpretation defect
remained: ordinary B-cubed can decide structural agreement but cannot launder a
negative resource-weighted result into a positive RQ1 resource-attribution
claim. The disposition is:

- ordinary B-cubed remains the sole primary metric;
- token-weighted B-cubed cannot rescue a failed ordinary primary;
- a supported ordinary result with a nonpositive allocation-stable weighted
  direction is `MIXED`, not positive resource-attribution evidence;
- only a supported ordinary result accompanied by a positive, allocation-stable
  weighted direction supports the intended RQ1 resource-attribution statement.

No new metric, workload, baseline, or experiment is added.

## Round 3

**Completed:** 2026-07-16

**Verdict:** **PASS**

The reviewer verified that the Round-2 interpretation defect is closed:
ordinary operation-level B-cubed P/R/F1 is the sole primary structural metric;
token-weighted B-cubed is secondary and cannot rescue a failed primary; a
supported ordinary result with a nonpositive allocation-stable weighted delta
is `MIXED`; and only a supported ordinary result with a positive stable weighted
direction supports the intended RQ1 resource-attribution statement. The metric
hierarchy is approved for real preflight without another metric, baseline,
workload, or experiment.
