# Experiment Plan — Condition The Existing Recurrence Cutoff

## Research Question And One Hypothesis

- **Paper RQ verbatim:** **RQ3: How accurate are the tags?**
- **Tested mechanism hypothesis:** Applying the current all-transition NPMI
  cutoff to same-action pairs and the cross-action-calibrated NPMI cutoff to
  action-changing pairs preserves useful repeated-action boundaries while
  recognizing recurring cross-action continuity, producing a Pareto
  improvement over the current constructor on the two existing complete
  trajectory populations.
- **What cannot change:** RQ3, its positive paper hypothesis, the thesis, the
  four-RQ structure, and the AgentProf story.

## Paper-Value Admission

Step 0022 already isolates the common bottleneck on complete real trajectories.
The current Step 0020 global cutoff scores OSWorld-Human well but is dominated
by self-transitions on CodeTraceBench. Step 0022 jointly recalibrates action
changes and forces every identical-action pair continuous; together those
decisions fix most CodeTraceBench partition disagreement but lower
OSWorld-Human. Their aggregate result does not identify which component causes
the regression. The next scientific question is therefore not whether to
collect another benchmark. It is whether preserving the current same-action
decision while conditioning action changes on their own recurrence scale
retains both gains.

This is the smallest direct test of that explanation. It reuses the same NPMI,
same occurrence weighting, same deterministic two-means, same visible fields,
same unseen rule, same motif construction, same implementation path, same
complete normalized trajectories, and same scorers. It adds no parameter,
feature, threshold search, model family, experiment source, or algorithm name.
It is one conditional decision rule, not a score bundle.

Both populations are observed post-hoc development evidence. A positive result
can justify an implementation choice and strengthen the existing development-
corpus mechanism row; it cannot be described as untouched generalization or a
complete answer to all of RQ3.

## The Single Algorithm Change

Learn two deterministic cutoffs from the same disjoint reference sequences:

1. Compute the unchanged NPMI for every adjacent visible action pair.
2. Fit the existing occurrence-weighted one-dimensional two-means to all
   transition occurrences, yielding the current global cutoff.
3. Fit the same two-means to action-changing occurrences only, yielding the
   already-tested cross-action cutoff.
4. For a seen target pair with `left_action == right_action`, apply the global
   cutoff exactly as Step 0020 does.
5. For a seen target pair with `left_action != right_action`, apply the
   cross-action cutoff exactly as Step 0022 does.
6. Treat an unseen pair as a boundary and form/name motifs exactly as before.

This rule distinguishes low-recurrence same-action boundaries, high-recurrence
identity repetition, recurring cross-action continuity, and low-recurrence
cross-action boundaries without accessing scorer labels. There is no fallback:
a reference that cannot produce two finite distinct action-changing scores
fails clearly. No result may add another stratum, cutoff, exception, or input.

## Existing Inputs And Comparisons

### OSWorld-Human

- Reuse the complete 287 sessions, 3,978 operations, 3,691 adjacent pairs, and
  2,042 independent human groups already normalized and run in Steps 0020/0022.
- Preserve the fixed five session-disjoint folds and existing scorer.
- Main baseline: committed Step 0020 current recurrence.
- Existing Step 0022 candidate is a diagnostic component comparison, not a new
  baseline family.
- Keep existing always-boundary, action-change, phase-change, and cap-free
  information-gain controls unchanged.

### CodeTraceBench

- Reuse the complete 2,229 target-disjoint reference sessions / 87,703
  operations and 405 targets / 20,866 operations / 20,461 adjacent pairs /
  2,948 official stages already normalized and run in Steps 0021/0022.
- Main baseline: committed Step 0021 current recurrence.
- Keep existing phase-change, action-change, always-boundary, and
  session-one-block controls unchanged.
- Rust prediction continues to receive only unit-weight `session` and `action`;
  official stages load only afterward in the scorer.

No trace collection, source download, benchmark normalization, task selection,
or label change is authorized. The candidate reruns only the existing local
operation inputs through the current evaluator and release path.

## Metrics And Fixed Verdict

- **Primary metric:** operation-weighted B-cubed partition F1, reported
  separately on complete OSWorld-Human and complete CodeTraceBench.
- **Secondary diagnostics:** boundary precision/recall/F1, exact decision
  overlap with Step 0020 and Step 0022 by transition stratum, segment/motif
  counts, both cutoff populations/centers, unseen transitions, per-framework
  CodeTraceBench B-cubed, exact Rust/Python equivalence, and mass conservation.
- **Supported:** B-cubed F1 is no lower than current recurrence on either
  complete population and is strictly higher on at least one.
- **Mixed:** B-cubed F1 is strictly higher on one population and strictly lower
  on the other.
- **Contradicted:** every other valid complete outcome.
- **Invalid/incomplete:** source identity, scorer isolation, reference
  disjointness, calibration engagement, execution, equivalence, coverage, or
  conservation fails.

The supported rule is exact Pareto improvement and has no tolerance. No mean
across datasets or metrics decides the result. Boundary metrics remain
diagnostics and cannot veto the fixed primary verdict unless they expose a
declared correctness, coverage, or scorer defect.

## Execution Plan

1. Implement only the conditioned cutoff in the existing Python recurrence
   evaluator and existing Rust `--induce-operation-stack` path. Extend existing
   reports/tests only enough to make both cutoffs and stratum decisions
   auditable.
2. Run static checks, focused current/candidate unit tests, and a release build.
3. Have an independent implementation reviewer verify the one-change
   semantics before any metric-bearing full run.
4. Run one real preflight on fixed OSWorld fold 0 and the lexicographically
   first complete CodeTraceBench target. Preflight verifies execution,
   isolation, coverage, and engagement only; its metrics cannot change the
   candidate or verdict.
5. Run all five OSWorld folds, full Rust/Python equivalence, and all 405
   CodeTraceBench targets once.
6. Give a fresh result reviewer the approved plan, current baselines, code
   diff, and complete raw artifacts without a desired numerical outcome.

Authoritative commands after reviewed implementation:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-conditioned-recurrence-v1/preflight

python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-conditioned-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-conditioned-recurrence-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-conditioned-recurrence-codetracebench-v1/preflight

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-conditioned-recurrence-codetracebench-v1/full
```

Terminal completion requires exactly 3,691 OSWorld pair decisions, 3,978
assignments, all five folds, exact Rust/Python decisions/assignments/segments/
motifs/NPMI/cutoffs/mass, and exactly 20,461 CodeTraceBench decisions plus
20,866 assignments across all 405 targets. Both full reports must reproduce
the committed current recurrence and Step 0022 component results on identical
scorer keys while reporting the candidate separately.

## Result Discipline And Paper Decision

Implementation may repair only correctness or execution defects. Preflight or
full metrics cannot add a feature, cutoff, fallback, workload, or second
candidate. If the result is supported and independently valid, the conditioned
rule may replace the current Rust decision path; update design,
implementation, evaluation history, and only paper rows actually owned by the
new release result, retaining the post-hoc-development qualifier. If mixed or
contradicted, restore only candidate code, preserve the fixed positive RQ3
hypothesis and strongest reader-facing story, record the complete mechanism
result in `docs/evaluation.md`, and return to outer REVIEW without another
candidate inside this experiment.
