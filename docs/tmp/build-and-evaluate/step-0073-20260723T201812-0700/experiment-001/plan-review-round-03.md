# Plan Review Round 03 — Convergence and Minimality Audit

**Reviewer role:** independent read-only convergence reviewer
**Verdict:** **NEEDS ONE MINIMAL REVISION**

## Convergence assessment

The scientific design has converged:

- one fixed RQ3 hypothesis is tested on one manifest-defined complete
  follow-on population;
- ordinary unweighted B-cubed F1 is the single standard primary metric;
- exact boundary F1 and per-framework rows are secondary diagnostics, not
  alternate success paths;
- multi-resolution recurrence is the decisive strongest runnable baseline;
- native tree tests the only other material explanation, while native turn is
  correctly a diagnostic control;
- ACT*ONOMY is not numerically runnable on these boundaries and is properly
  handled by citation rather than a proxy implementation;
- the plan does not expand into semantic-name accuracy, nested topology,
  user utility, a new backend, a new benchmark, or external generalization.

No baseline, metric, workload, model run, ablation, or additional reviewer
should be added.

## Remaining must-fix

Remove the requirement that the independent result reviewer reproduce
**every one of the 10,000 bootstrap draws** exactly and do so without importing
the scorer. That is unnecessary equivalence checking, not additional
scientific evidence. Require the reviewer to reconstruct the manifest subset,
recompute the aggregate and per-framework metrics, independently recompute the
paired 95% interval from the fixed seed/protocol, verify the decision, and
inspect the scorer for the registered resampling semantics. Exact equality of
all individual draws is optional and must not become another completion gate.

With that single deletion, the plan is both top-conference adequate and
minimal.
