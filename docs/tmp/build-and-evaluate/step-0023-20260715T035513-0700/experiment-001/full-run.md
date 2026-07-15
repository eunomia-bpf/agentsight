# Complete Existing-Trajectory Run

**Status:** VALID / COMPLETE
**Scientific verdict:** MIXED
**Role:** supporting post-hoc mechanism-development evidence

## Question

Does applying the current global recurrence cutoff to same-action pairs and
the cross-action-calibrated cutoff to action-changing pairs produce an exact
Pareto improvement over the current operation-stack constructor on both
already-completed trajectory populations?

The experiment changes no trace source, normalized operation, input field,
NPMI definition, clustering rule, parameter, metric, motif construction, paper
RQ, hypothesis, thesis, or story.

## Complete Commands

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-conditioned-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-conditioned-recurrence-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-conditioned-recurrence-codetracebench-v1/full
```

All commands completed once with the fixed candidate. OSWorld-Human covers all
five held-out folds: 287 sessions, 3,978 operations, 3,691 pairs, and 2,042
independent human groups. CodeTraceBench covers all 405 target-disjoint
sessions, 20,866 operations, 20,461 pairs, and 2,948 complete official stages
across four frameworks.

## Primary Results

| Population | Current B-cubed F1 | Candidate B-cubed F1 | Delta | Relation |
|---|---:|---:|---:|---|
| OSWorld-Human | 0.786170 | 0.784589 | -0.001580 | lower |
| CodeTraceBench | 0.475008 | 0.649173 | +0.174165 | higher |

The fixed exact-Pareto rule therefore yields **MIXED**. Candidate boundary F1
is 0.678114 versus current 0.679922 on OSWorld-Human and 0.287106 versus
current 0.268506 on CodeTraceBench.

On OSWorld-Human, the candidate and current constructor have identical TP
(1,402), FN (353), B-cubed precision (0.855872), and same-action behavior. The
cross-action cutoff adds 11 false-positive boundaries, producing 2,667 groups
instead of 2,656 and lowering B-cubed recall from 0.726966 to 0.724267. This is
far smaller than Step 0022's regression to 0.742492 but is still strictly below
current under the approved rule.

On CodeTraceBench, the candidate exactly equals the Step 0022 component:
boundary F1 0.287106, B-cubed precision 0.828579, recall 0.533630, F1 0.649173,
and 6,897 groups. This occurs because current same-action decisions already
match Step 0022 there, so conditioning preserves the full cross-action gain.
The candidate improves B-cubed over current in each framework: OpenHands
0.489098 to 0.661593, SWE-agent 0.461036 to 0.707955, Terminus2 0.438572 to
0.593876, and mini-SWE-agent 0.533086 to 0.683439.

## Calibration And Equivalence

The OSWorld folds use 11,392 action-changing and 3,372 same-action reference
occurrences in total. Global cutoffs are 0.231168, 0.321453, 0.337659,
0.237265, and 0.305633; cross-action cutoffs are 0.280594, 0.283253, 0.297296,
0.295724, and 0.267110. CodeTraceBench uses 47,303 action-changing and 38,171
same-action occurrences, with global cutoff 0.122991 and cross-action cutoff
-0.055739.

Rust exactly matches Python across all five OSWorld folds: 3,691 boundary
decisions, 3,978 motif assignments, 2,667 segments, 44 unique motifs, and all
3,978 units of mass. Both cutoffs, NPMI values, applied calibration population,
segment boundaries, and motif names agree within the declared tolerance or
exactly as applicable.

## Decision

The candidate is valid and identifies a strong cross-action repair, but it does
not satisfy the fixed overall replacement rule because OSWorld-Human is
strictly lower. It must not replace the current Step 0020 implementation.
Only Step 0023-owned code, test, and evaluator changes will be restored after
independent result review. The complete result remains in experiment and
canonical evaluation history; it does not change the paper, fixed RQ3 positive
hypothesis, thesis, contribution, or story. No second candidate is introduced
inside this experiment.

## Raw Evidence

- `.agentsight/experiments/rq3-conditioned-recurrence-v1/full/`
- `.agentsight/experiments/rq3-conditioned-recurrence-rust-equivalence-v1/full/`
- `.agentsight/experiments/rq3-conditioned-recurrence-codetracebench-v1/full/`
