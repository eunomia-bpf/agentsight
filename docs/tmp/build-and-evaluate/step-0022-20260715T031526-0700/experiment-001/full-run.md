# Complete Existing-Trajectory Run

**Status:** VALID / COMPLETE
**Scientific verdict:** MIXED
**Role:** supporting post-hoc mechanism-boundary evidence

## Question

Does the one approved repair—fit the existing occurrence-weighted NPMI
two-means cutoff only on action-changing transitions while keeping identical
actions continuous by identity—improve the current recurrence constructor on
both already-completed trajectory populations?

This experiment does not change RQ3, its positive hypothesis, the AgentProf
story, any input field, benchmark, metric, parameter, algorithm name, or paper
claim. It evaluates one modification to the current constructor on existing
OSWorld-Human and CodeTraceBench artifacts.

## Complete Commands

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-cross-action-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-cross-action-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-cross-action-codetracebench-v1/full
```

All three commands completed once. OSWorld-Human covers every one of the fixed
five held-out folds: 287 sessions, 3,978 operations, and 3,691 adjacent pairs.
CodeTraceBench covers all 405 target-disjoint sessions, 20,866 operations,
20,461 adjacent pairs, and 2,948 complete official stage intervals from four
frameworks.

## Results

| Population | Current boundary F1 | Candidate boundary F1 | Current B-cubed F1 | Candidate B-cubed F1 | B-cubed delta |
|---|---:|---:|---:|---:|---:|
| OSWorld-Human | 0.679922 | 0.542657 | 0.786170 | 0.742492 | -0.043677 |
| CodeTraceBench | 0.268506 | 0.287106 | 0.475008 | 0.649173 | +0.174165 |

On CodeTraceBench, B-cubed F1 improves independently in OpenHands
(0.489098 to 0.661593), SWE-agent (0.461036 to 0.707955), Terminus2
(0.438572 to 0.593876), and mini-SWE-agent (0.533086 to 0.683439). The pooled
candidate remains 0.005272 below the external phase-change control at
0.654445. Its boundary confusion is TP 1,297, FP 5,195, FN 1,246, TN 12,723;
B-cubed precision and recall are 0.828579 and 0.533630.

On OSWorld-Human, the candidate boundary confusion is TP 970, FP 850, FN 785,
TN 1,086; B-cubed precision and recall are 0.734479 and 0.750682. The five
training folds contribute 11,392 action-changing calibration occurrences in
total, while 3,372 same-action occurrences are handled by the identity rule.
CodeTraceBench contributes 47,303 action-changing calibration occurrences and
38,171 same-action occurrences.

The release Rust implementation exactly matches the fixed Python candidate on
all five OSWorld-Human folds: 3,691 boundary decisions, 3,978 operation
assignments, 2,107 segments, 42 unique motifs, and all 3,978 units of mass.
All NPMI values and cutoffs agree within `1e-12`.

## Interpretation And Decision

The preregistered mechanical verdict is **MIXED** because B-cubed F1 improves
on exactly one of the two complete observed populations. Removing identity
transitions from the two-cluster calibration fixes much of the CodeTraceBench
degeneration but over-merges OSWorld-Human. Therefore it is not a universal
repair and does not replace the Step 0020 recurrence constructor.

This result establishes a precise mechanism boundary: identity repetition can
dominate the old cutoff, but simply excluding it conflates useful recurring
cross-action continuity with true group boundaries on a different population.
No second candidate or result-driven tuning is admitted in this experiment.
Only Step 0022-owned candidate code changes were restored after result review;
the current Step 0020 Rust implementation and paper numbers remain unchanged.

## Raw Evidence

- `.agentsight/experiments/rq3-cross-action-recurrence-v1/full/`
- `.agentsight/experiments/rq3-cross-action-rust-equivalence-v1/full/`
- `.agentsight/experiments/rq3-cross-action-codetracebench-v1/full/`
