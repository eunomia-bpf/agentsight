# Experiment Plan — Cross-Action Recurrence Calibration

## Research Question And One Hypothesis

- **Paper RQ verbatim:** **RQ3: How accurate are the tags?**
- **Tested mechanism hypothesis:** Excluding identical-action repetitions from
  unsupervised cutoff calibration, while keeping those pairs continuous by
  identity, lets the same NPMI recurrence distinguish routine cross-action
  changes from operation-group boundaries and improves operation-partition
  fidelity on both existing development populations.
- **What cannot change:** RQ3, its positive paper hypothesis, the thesis, the
  four-RQ structure, and the paper story.

## Paper-Value Admission

Step 0021 showed that the release recurrence equals direct action-change on
99.6579% of complete CodeTraceBench pairs. Its reference high cluster is
99.202% self-transition occurrences, so identical-action recurrence sets the
scale for a question it cannot answer: which *changes* are routine continuity.
The proposed repair removes that scale mismatch without adding a feature,
weight, parameter, threshold, algorithm family, or benchmark.

This is the highest-value existing-trajectory action because it directly
addresses a verified implementation bottleneck and can replace the current
constructor if it improves both observed development populations. Another
benchmark would only repeat the known failure. A cutoff sweep, richer field
signature, window model, HMM, or score bundle would add degrees of freedom
before testing the simplest mechanism-derived prediction.

Both workloads are explicitly post-hoc development evidence. A positive result
can justify the implementation choice and the existing development-corpus row;
it cannot be described as untouched cross-family confirmation.
The planned paper role is supporting mechanism-development evidence. The real
assets and protocols remain the official OSWorld-Human/CodeTraceBench
annotations and the already-used B-cubed partition agreement metric.

## The Single Algorithm Change

The current constructor computes NPMI for every adjacent visible action pair,
fits deterministic occurrence-weighted one-dimensional two-means over all
transition occurrences, and treats a pair as continuous when its score is at
or above the midpoint cutoff.

The candidate changes only the calibration population:

1. compute the same NPMI for every adjacent action pair from the same disjoint
   reference sessions;
2. mark `left_action == right_action` continuous by identity;
3. fit the same deterministic occurrence-weighted two-means using only
   occurrences with `left_action != right_action`;
4. for action-changing target pairs, use the same cutoff and unseen-pair
   boundary rule;
5. form and name motifs exactly as before.

There is no fallback, tuning knob, searched cutoff, new field, or new algorithm
name. A reference without two distinct finite cross-action NPMI scores fails
clearly rather than silently reverting to the known distorted calibration.

## Existing Inputs And Comparisons

### OSWorld-Human

- Reuse the complete 287 sessions / 3,978 operations / 3,691 adjacent pairs /
  2,042 independent human groups.
- Preserve the fixed five session-disjoint folds and current scorer.
- Main baseline: committed Step 0020 release recurrence.
- Existing controls: always-boundary, action-change, phase-change, and the
  cap-free information-gain constructor; supervised extra-information remains
  context, not a matched unsupervised baseline.
- Run the existing Python evaluator once, then require exact Rust/Python
  equivalence on every fold, decision, motif, segment, cutoff, and conserved
  operation weight.

### CodeTraceBench

- Reuse the complete Step 0021 population: 2,229 target-disjoint reference
  sessions / 87,703 operations and 405 target sessions / 20,866 operations /
  20,461 adjacent pairs / 2,948 official stages across four frameworks.
- Main baseline: committed Step 0021 release recurrence.
- Existing controls: phase-change, action-change, always-boundary, and
  session-one-block; do not recompute or change their definitions.
- Run the existing adapter/scorer once after the Rust implementation passes
  preflight. Official stages remain scorer-only and load after prediction.

## Metrics And Interpretation

- **Primary metric:** operation-weighted B-cubed partition F1, reported
  separately for OSWorld-Human and CodeTraceBench.
- **Secondary diagnostics:** boundary precision/recall/F1, segment and motif
  counts, recurrence/action-change decision equality, cross-action calibration
  counts and centers, unseen transitions, and exact mass conservation.
- **Supported:** candidate B-cubed F1 strictly exceeds the committed current
  recurrence on both complete populations.
- **Mixed:** it improves exactly one population.
- **Contradicted:** it improves neither population's B-cubed F1.
- **Invalid/incomplete:** source, reference isolation, scorer leakage,
  cross-action calibration, execution, equivalence, coverage, or conservation
  fails.

No aggregate across datasets or across boundary/B-cubed metrics will decide the
result. Boundary metrics remain diagnostics and cannot change the scientific
verdict unless they expose an already-declared correctness or coverage defect.
The independent reviewer verifies and recomputes the fixed rule; it does not
introduce another decision gate.

## Execution Plan

1. Implement the same one-line principle in the existing Python evaluator and
   existing Rust `--induce-operation-stack` path; update only tests and report
   wording required by that behavior.
2. Run static checks and focused unit/CLI tests.
3. Run a real OSWorld preflight on one existing fold and a real CodeTraceBench
   preflight on one existing target. Preflight proves only execution,
   isolation, and output validity; its metrics are diagnostics and cannot
   select or alter the candidate.
4. Run all five complete OSWorld folds through the Python evaluator once.
5. Run complete five-fold Rust/Python equivalence once.
6. Run all 405 CodeTraceBench targets once.
7. Give a fresh result reviewer the approved plan, committed baselines, changed
   code, and complete raw outputs without a desired numerical verdict.

Authoritative commands after the reviewed implementation and focused tests:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-cross-action-recurrence-v1/preflight

python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-cross-action-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-cross-action-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-cross-action-codetracebench-v1/preflight

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-cross-action-codetracebench-v1/full
```

Planned output roots:

- `.agentsight/experiments/rq3-cross-action-recurrence-v1/`
- `.agentsight/experiments/rq3-cross-action-rust-equivalence-v1/`
- `.agentsight/experiments/rq3-cross-action-codetracebench-v1/`

The implementation may be repaired only for a correctness or execution defect.
No result-driven feature, cutoff, input, workload, or decision-rule change is
allowed in this experiment. If the hypothesis is mixed or contradicted, record
the result and return to the next outer review without a second candidate.

Terminal completion requires the OSWorld preflight to cover all sessions in
fold 0, the OSWorld full run to emit exactly 3,691 pair decisions and 3,978
assignments across all five folds, and Rust/Python equivalence to match all five
folds, decisions, assignments, segments, motifs, NPMI values, cutoffs, and mass.
The CodeTraceBench preflight uses the lexicographically first complete target;
the full run must emit exactly 20,461 pair decisions and 20,866 assignments for
all 405 targets. Both full summaries must include the candidate and committed
current-recurrence B-cubed/boundary metrics, exact reference isolation, scorer
exclusion, complete coverage, and conserved operation weight.

## Paper Decision

If supported and independently valid, update `docs/design.md` and
`docs/implementation.md`, replace the current development-corpus recurrence
numbers in the paper only where the new implementation actually owns them, and
retain the post-hoc-development qualifier. If mixed or contradicted, preserve
the fixed positive RQ3 hypothesis and reader-facing strongest supported story;
record the mechanism result in `docs/evaluation.md` and let outer REVIEW select
the next mechanism or paper-level action.
