# Step 0026 — Existing-Trajectory Algorithm Admission

**Started:** 2026-07-15T06:38:27-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Outer gate:** EXPERIMENT  
**Status:** Complete  
**Owner:** root orchestrator

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** Attribution, localization, tag accuracy, and cost remain the
exact four RQs. The selected question is unchanged:

> **RQ3 — How accurate are the tags?**

This step answers whether one more modification of the existing operation-stack
induction algorithm is scientifically admissible from the already-completed
OSWorld-Human and CodeTraceBench trajectories. It may diagnose retained raw
decisions, but it may not run candidate metrics, introduce a benchmark, change
the paper/story/RQs/hypothesis, rename the algorithm, modify a skill or branch,
or treat implementation activity as progress by itself.

## EXPERIMENT Gate

### Node E001 — Step 0025 Recovery

Step 0025 tested one sequence-local refinement of Step 0024 on the two complete
retained populations. It improved CodeTraceBench B-cubed F1 from 0.649173 to
0.671671 but reduced OSWorld-Human from 0.786170 to 0.746958 and reduced
boundary F1 on both. Independent review classified the result PASS / COMPLETE /
MIXED. The candidate code was removed exactly, the Step 0024 release passed all
restoration checks, and no paper change was made.

Independent outer review also rejected selecting the two rules from the sign
of the learned cross-action cutoff. Cutoff sign is fully confounded with the
two population identities after their outcomes are known, so that shortcut
would merely choose each population's winner. Step 0025 was committed as
`3766dca3e028acb5cacf1240aa62fd4048a9b3a6`. A normal push failed with GitHub
HTTP 500; no force push or branch change was attempted.

### Node E002 — Common-Error Audit

The root reconstructed Step 0024 and Step 0025 decision errors directly from
the retained complete outputs. No candidate rule or candidate accuracy was
executed. The full audit is
[`common-error-audit.md`](common-error-audit.md).

The central result is observational aliasing, not one shared correctable
decision defect. Ordered action-pair identity has mixed boundary labels for
91.2% of OSWorld-Human decisions and 99.7% of CodeTraceBench decisions. Even a
four-action local context remains mixed for 53.8% and 81.5% of decisions.
Immediate context raises the in-sample majority-class ceiling materially on
OSWorld-Human but barely on CodeTraceBench, so “add local context” is not a
common mechanism prediction.

Step 0025's suppressed boundaries also have opposite scientific meaning. Of
842 suppressed OSWorld decisions, 504 are real boundaries and 338 are
continuations. Of 2,067 suppressed CodeTraceBench decisions, only 348 are real
boundaries and 1,719 are continuations. This explains the mixed outcome and
shows that another local suppression shape would be selection among already
observed population granularities, not a demonstrated shared repair.

The retained labels use different group granularity: 1,755/3,691 OSWorld pairs
are positive boundaries versus 2,543/20,461 CodeTraceBench pairs. Step 0024
therefore over-segments both relative to labels but at very different base
rates. Same-action false negatives and cross-action false positives occur in
both, but identical visible pairs and even local contexts carry both labels;
the current `session` plus `action` input cannot identify which occurrence is
which without a new observable signal or an explicit resolution contract.

### Node E003 — Paper-Value Decision

**Decision: NO-ADMIT.** No further candidate is authorized on these two
development populations under the current action-only flat-segmentation
contract.

This is not a claim that Step 0024 is mathematically optimal. It is a scoped
decision that the retained evidence does not support one benchmark-independent
mechanism correction. A cutoff, score, local window, run thinning, support
bucket, sign gate, or benchmark-specific fallback chosen now would tune already
observed labels without changing the paper-level RQ3 answer. Re-running the same
inputs after such choices would produce more numbers but not stronger evidence.

The Step 0024 release remains current. A future algorithm experiment requires
one genuinely new scientific discriminator—for example an observable semantic
field with a stated causal role, an explicit multi-resolution output contract,
or untouched evidence that distinguishes annotation granularity. Such work is
not admitted inside this existing-trajectory request and must not be smuggled
in as another small recurrence tweak.

## WRITE Gate

### Node W001 — No-Change Disposition

No paper or code change is authorized. This admission audit does not alter a
result, algorithm, RQ, positive hypothesis, thesis, contribution, or story.

## REVIEW Gate

### Node R001 — Independent Paper-Value Audit

A fresh read-only reviewer explicitly used `research-experiment-design`,
independently reconstructed every stated raw count, context-mixing diagnostic,
Step 0025 suppression label, and session-length B-cubed delta, and returns PASS
with zero must-fix.

The review confirms that over-segmentation is a shared symptom but not a shared
selector. Every examined small correction is non-monotone, directionally
opposed, or population-confounded. A new MDL objective, sequence model, or
multi-resolution contract may be future research, but is not authorized as one
more small tweak on these already-observed labels. The scoped no-admit decision
does not claim that all future sequence models are mathematically impossible.

The full review is [`admission-review.md`](admission-review.md). REVIEW closes
PASS. Step 0024 remains the release and the current paper remains unchanged.

## Next Node

Return to the outer orchestrator with the existing-trajectory refinement branch
closed. The next paper-level action must come from a fresh outer REVIEW decision,
not another recurrence tweak on these two development populations.
