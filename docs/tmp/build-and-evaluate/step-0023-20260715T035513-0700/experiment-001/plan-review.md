# Independent Experiment-Plan Review

**Decision:** APPROVE
**Must-fix findings:** none
**Bounded wording follow-up:** APPROVE

The independent reviewer explicitly used `research-experiment-design`, read the
Step 0022 complete evidence and current implementation, and performed no edit
or experiment.

## Scientific Judgment

This is the smallest principled next test. It introduces one visible structural
condition, `left_action == right_action`, while composing two already-defined,
zero-parameter calibrations from the same NPMI and deterministic two-means:

- the global cutoff preserves exact Step 0020 same-action behavior;
- the cross-only cutoff changes only the action-changing stratum whose scale is
  distorted by identity-dominated calibration on CodeTraceBench.

This is not heuristic soup: it uses one association score, one clustering rule,
two fixed calibration populations, no fallback, and no user knob. A same-only
cutoff, extra score, HMM, window, learned gate, searched threshold, or new
benchmark would be a second, less-minimal candidate and is not admitted.

The fixed RQ3 mechanism hypothesis, positive paper hypothesis, thesis, four
RQs, and story remain unchanged. Both populations are explicitly observed
post-hoc development evidence, so the plan cannot claim untouched
generalization. The current Step 0020 recurrence is the correct main baseline;
Step 0022 is correctly a component comparison, with existing simple/external
controls preserved.

The exact Pareto verdict is complete and mechanical: no lower on either full
population and strictly higher on at least one is supported; one higher and one
lower is mixed; every other valid outcome is contradicted. Boundary metrics
remain non-veto diagnostics. Fixed folds, target-disjoint reference, scorer
isolation, five commands, terminal population totals, exact Rust/Python
equivalence, and mass conservation are adequate.

## Wording Follow-up

After approval, the root corrected one causal overstatement: Step 0022 changed
cross-action calibration and identity forcing together, so its aggregate
OSWorld regression cannot identify either component alone. Step 0023 is
therefore framed as the direct component-isolation test. The reviewer confirms
that this correction strengthens the one-change rationale, adds no scope,
parameter, candidate, metric, or execution requirement, and leaves APPROVE in
force.
