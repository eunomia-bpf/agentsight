# Experiment Plan — Monotone Cross-Action Calibration

## Research Question And One Hypothesis

- **Paper RQ verbatim:** **RQ3: How accurate are the tags?**
- **Tested mechanism hypothesis:** Letting cross-action calibration only lower,
  never raise, the current global recurrence cutoff recovers recurring
  cross-action continuity without adding current-relative boundaries and
  yields an exact B-cubed Pareto improvement on the two existing complete
  trajectory populations.
- **Fixed paper contract:** RQ3, its positive paper hypothesis, the thesis,
  four-RQ architecture, contribution, and AgentProf story cannot change.

## Paper-Value Admission

Step 0023 is already a complete component isolation. It retains the
CodeTraceBench improvement but adds exactly 11 false-positive OSWorld
boundaries when a fold's cross-action cutoff exceeds its global cutoff. This is
not a reason to collect another benchmark or enrich the score. It exposes one
directional mismatch: the repair for identity-inflated calibration should only
merge current boundaries whose cross-action recurrence supports continuity; it
should never create a new boundary.

The proposed `min(global_cutoff, cross_action_cutoff)` is the smallest rule with
that property. It adds no learned gate, threshold, tolerance, feature, score,
window, model, benchmark, or algorithm term. It is a monotonic constraint on
the two already-audited calibrations. Both full populations remain explicitly
post-hoc development evidence; even a positive result is an implementation-
selection result, not untouched cross-family confirmation or all of RQ3.

## The Single Algorithm Change

For the same disjoint reference sequences and visible `action` field:

1. Compute unchanged adjacent-transition NPMI.
2. Fit unchanged deterministic occurrence-weighted two-means to all transition
   occurrences, yielding `global_cutoff`.
3. Fit the same two-means to action-changing occurrences, yielding
   `cross_action_cutoff`.
4. A seen same-action target pair uses `global_cutoff`.
5. A seen action-changing target pair uses
   `min(global_cutoff, cross_action_cutoff)`.
6. An unseen pair remains a boundary; segment and motif construction are
   unchanged.

The candidate has a direct property independent of labels: for every seen
pair, its applied cutoff is no greater than the current global cutoff.
Therefore every current continuation remains a continuation; the candidate can
only remove current boundaries. The implementation/report must assert this
decision-set monotonicity. No fallback or third cutoff is allowed.

## Existing Inputs And Comparisons

### OSWorld-Human

- Reuse all 287 sessions, 3,978 operations, 3,691 pairs, 2,042 human groups,
  and the fixed five session-disjoint folds already run in Steps 0020–0023.
- Main baseline: current Step 0020 recurrence.
- Component comparisons: Step 0022 cross-action/identity rule and Step 0023
  conditioned rule; no new baseline family.
- Existing simple/external controls remain unchanged diagnostics.

### CodeTraceBench

- Reuse the complete target-disjoint reference (2,229 sessions / 87,703
  operations) and all 405 targets / 20,866 operations / 20,461 pairs / 2,948
  official stages already run in Steps 0021–0023.
- Main baseline: current Step 0021 recurrence.
- Component comparisons: Steps 0022 and 0023; existing controls unchanged.
- Rust continues to see only unit-weight `session` and `action`; official stages
  and committed scored summaries load after prediction.

No source collection, download, normalization, task selection, or label change
is authorized.

## Metrics And Fixed Verdict

- **Primary:** operation-weighted B-cubed F1 separately on each complete
  population.
- **Diagnostics:** boundary precision/recall/F1, exact current-relative decision
  subset, removed-boundary count, segment/motif counts, both calibration
  populations/centers/cutoffs, unseen pairs, per-framework CodeTraceBench
  B-cubed, Rust/Python equivalence, coverage, and mass.
- **Supported:** B-cubed F1 is no lower than current on either complete
  population and strictly higher on at least one.
- **Mixed:** strictly higher on one and strictly lower on the other.
- **Contradicted:** every other valid complete outcome.
- **Invalid/incomplete:** source identity, scorer isolation, reference
  disjointness, monotonic decision subset, calibration, execution, equivalence,
  coverage, or conservation fails.

The comparison is exact and has no tolerance. Boundary metrics are diagnostics
unless they expose a declared validity failure. No aggregate mean or secondary
metric can replace the fixed two-population B-cubed rule.

## Execution

1. Implement only the `min` constraint in the existing Python and Rust paths;
   expose both raw cutoffs and the applied cross-action cutoff.
2. Add focused monotonicity tests/report assertions and run static checks,
   current tests, and release build.
3. Require independent implementation review before metrics.
4. Run fixed OSWorld fold 0 and the first complete CodeTraceBench target as
   execution-only preflights; do not interpret metrics.
5. Run all five OSWorld folds, full Rust/Python equivalence, and all 405
   CodeTraceBench targets once.
6. Require independent raw-result reconstruction and the fixed verdict.

Approved commands after implementation review:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-monotone-recurrence-v1/preflight

python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-monotone-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-monotone-recurrence-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/preflight

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full
```

Terminal completion requires 3,691 OSWorld decisions, 3,978 assignments, five
folds, exact Rust/Python NPMI/raw/applied cutoffs/decisions/segments/motifs/mass,
and 20,461 CodeTraceBench decisions plus 20,866 assignments across 405 targets.
Every candidate boundary set must be a subset of the matching current boundary
set for seen pairs.

## Result And Paper Discipline

No preflight/full result may change the candidate. If supported and valid, the
monotone rule may replace the current decision path and update design,
implementation, canonical evaluation, and paper rows actually owned by the
release result, retaining the post-hoc-development qualifier. If mixed or
contradicted, restore only candidate changes, record the mechanism result, and
return to outer REVIEW. In every outcome, the fixed RQ3 positive hypothesis,
thesis, four RQs, contribution, and story remain unchanged; no second candidate
is allowed inside Step 0024.
