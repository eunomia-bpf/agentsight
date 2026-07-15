# Experiment Plan — Sequence-Local Refinement Of Existing Recurrence Induction

**Proposed:** 2026-07-15T05:58:00-07:00  
**State:** Approved after two independent review rounds  
**Paper RQ:** **RQ3 — How accurate are the tags?**  
**Scientific role:** post-hoc improvement of the existing release algorithm on
already-completed trajectories; not untouched confirmation

## One Tested Hypothesis

> On the complete existing OSWorld-Human and CodeTraceBench populations, using
> sequence-local recurrence context to suppress weak action-changing edges that
> are not local continuity minima yields an exact B-cubed Pareto improvement
> over the current operation-stack induction rule.

The experiment may accept or reject one refinement of the existing algorithm.
It cannot change RQ3, its positive paper-level hypothesis, the exact thesis, the
four-RQ architecture, the two core abstractions, or the original AgentProf
story.

## Why This Experiment Is Admitted

Step 0024's current rule uses the same learned score and cutoff for every
occurrence of an ordered action pair. The retained CodeTraceBench scorer shows
that the same pair often occurs both inside and between official stages. For
example, the current rule classifies every `execute -> inspect` occurrence as a
boundary, although the retained population contains both boundary and
non-boundary instances. Changing another global cutoff or pair score can only
flip that entire pair class; it cannot resolve the observed contextual
ambiguity.

The retained scorer shows that mixed-label action-pair types cover 3,367 of
3,691 OSWorld-Human decisions (91.2%) and 20,405 of 20,461 CodeTraceBench
decisions (99.7%). The complete retained outputs also expose contiguous runs of
weak edges: 1,423 such multi-edge runs on CodeTraceBench and 367 on
OSWorld-Human. A label-free feasibility pass over the already-retained raw NPMI
scores confirmed that a local-minimum rule changes decisions on both
populations. It did not calculate candidate boundary or B-cubed accuracy,
select a window, or compare variants.

The proposed change adds no field, feature family, score, cutoff, parameter,
dataset, benchmark, model, algorithm name, or target label. It retains NPMI,
both deterministic two-means calibrations, unseen-pair behavior, operation
motifs, outputs, and the existing `--induce-operation-stack` interface. It adds
only the immediate sequence relation needed to distinguish occurrences of the
same pair.

## The Single Algorithm Change

First compute every target edge exactly as in Step 0024. Its existing threshold
decision is a boundary exactly when the edge is unseen or its NPMI is below its
applied cutoff. The cutoff establishes only threshold eligibility; it is not
used to order neighboring edges.

The candidate changes only action-changing threshold boundaries:

1. A threshold continuation remains a continuation.
2. A same-action threshold boundary remains a boundary.
3. An action-changing threshold boundary remains a boundary only when its
   raw NPMI is no greater than the immediately preceding edge's raw NPMI and no
   greater than the immediately following edge's raw NPMI.
4. An unseen edge has comparison value negative infinity. A missing neighbor at
   the beginning or end of a session has comparison value positive infinity.
5. Exact equal NPMI values satisfy the comparison, so tied adjacent minima remain
   boundaries. No tie-break parameter is introduced.

This is a sequence-local interpretation of the same recurrence evidence: an
operation boundary is a threshold-weak transition that is also a local low
point in the existing raw NPMI continuity score. Raw NPMI is the same
commensurate quantity on every neighboring edge; the heterogeneous global and
cross-action cutoffs do not enter the local ordering. The rule has two
label-independent properties. The candidate boundary set is a subset of the
Step 0024 boundary set, and every same-action Step 0024 decision is identical.
The implementation must expose the pre-refinement `threshold_boundary` and
final `boundary` for every target edge and assert both properties.

No larger window, smoothing, score normalization, threshold search, fallback,
special action, phase field, raw command field, or second candidate is allowed.

## Existing Inputs And Comparisons

### OSWorld-Human

- Reuse all 287 sessions, 3,978 operations, 3,691 adjacent pairs, 2,042 human
  groups, and the existing five session-disjoint folds.
- Candidate input remains only unit weight plus visible `session` and `action`.
- Main baseline is the release Step 0024 recurrence output.
- Existing information-gain and simple controls remain diagnostics; no new
  baseline family is added.

### CodeTraceBench

- Reuse the same target-disjoint reference of 2,229 sessions and 87,703
  operations.
- Reuse all 405 targets, 20,866 operations, 20,461 adjacent pairs, and 2,948
  official stages.
- Candidate input remains only unit weight plus visible `session` and `action`.
  Official stages load only after prediction.
- Main baseline is the release Step 0024 recurrence output. The already-scored
  phase-change, action-change, and one-session views remain unchanged
  diagnostics.

No source collection, download, conversion, normalization, task selection,
label update, or new trajectory execution is authorized.

## Metrics And Fixed Verdict

- **Primary:** operation-weighted B-cubed F1 separately on each complete
  population.
- **Diagnostics:** boundary precision/recall/F1; exact subset of Step 0024
  decisions; unchanged same-action decisions; suppressed action-changing
  threshold-boundary count; group/motif counts; raw NPMI scores and cutoffs;
  unseen edges; per-framework CodeTraceBench B-cubed; exact Rust/Python
  equivalence; complete coverage; and additive mass.
- **Supported:** B-cubed F1 is no lower than Step 0024 on either complete
  population and strictly higher on at least one.
- **Mixed:** strictly higher on one population and strictly lower on the other.
- **Contradicted:** every other valid complete outcome.
- **Invalid/incomplete:** source identity, scorer separation, reference
  disjointness, decision-subset property, same-action preservation, execution,
  equivalence, coverage, or conservation fails.

The comparison is exact and has no tolerance. Boundary metrics and per-framework
results diagnose the mechanism but do not replace the fixed two-population
B-cubed verdict. Because both populations have already influenced mechanism
development, even a supported result remains implementation-selection evidence.

## Implementation And Execution

1. Modify the existing Rust decision pass to calculate all Step 0024 threshold
   decisions before session-local refinement. Keep the policy and CLI name.
2. Add only the matching sequence-local post-processing to the existing
   OSWorld Python reference and equivalence checks. Extend the existing
   CodeTraceBench scorer to validate the two declared decision properties.
3. Add focused Rust and CLI fixtures in which neighboring raw NPMI scores distinguish
   two occurrences without adding any input field or threshold.
4. Run formatting, focused/current tests, Python compilation, release build,
   and an independent implementation audit before real preflight.
5. Run OSWorld fold 0 and the first complete CodeTraceBench target as
   execution-only REAL PREFLIGHT. Metrics cannot modify the rule.
6. Run all five OSWorld folds, exact Rust/Python equivalence, and all 405
   CodeTraceBench targets once, followed by independent raw-result review.

Planned commands after implementation review:

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-contextual-recurrence-v1/preflight

python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-contextual-recurrence-v1/full

python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-contextual-recurrence-rust-equivalence-v1/full

python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-contextual-recurrence-codetracebench-v1/preflight

python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-contextual-recurrence-codetracebench-v1/full
```

Terminal completion requires all 3,691 OSWorld decisions and 3,978 assignments,
five folds, exact Rust/Python score/cutoff/threshold/final-decision/segment/motif
equivalence, and all 20,461 CodeTraceBench decisions and 20,866 assignments.
Every final boundary must be a Step 0024 threshold boundary and every
same-action decision must be unchanged.

## Result And Paper Discipline

No preflight or full result may change the candidate. If supported and valid,
the local refinement may replace the release decision pass and only its owned
design, implementation, evaluation, and paper text may enter WRITE. If mixed or
contradicted, restore only this candidate's code changes, retain the result in
research history, and return to outer REVIEW. No outcome changes the fixed RQ3
hypothesis, thesis, four RQs, contribution, or story, and no second candidate is
allowed inside Step 0025.
