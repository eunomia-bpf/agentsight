# Step 0025 — Improve Existing Induction On Reused Trajectories

**Started:** 2026-07-15T05:41:05-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gate:** EXPERIMENT
**Status:** Complete
**Owner:** root orchestrator

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The original AgentProf story and exactly four RQs—attribution,
localization, tag accuracy, and cost—remain fixed. The selected question is
verbatim:

> **RQ3 — How accurate are the tags?**

This step may improve only the existing operation-stack induction algorithm on
already-completed trajectories. It must not introduce a new benchmark, dataset,
feature family, algorithm name, paper story, thesis, RQ, or positive hypothesis.
It must prefer a single principled correction to a shared observed error over
threshold search or a collection of special cases. The authoritative
`docs/agentpprof-paper` submodule is read-only. No global skill, KVM material,
or branch may change.

## EXPERIMENT Gate

### Node E001 — Recovery And Existing-Trajectory Constraint

**Question and entry.** Can the existing operation-stack induction algorithm be
improved directly on the trajectories already completed, without replacing it
with a new algorithm or running a new benchmark?

**Inputs and method.** The root resumed from completed Step 0024 at commit
`6b1f0a7995464ea029ba3ccbc8ab457afe20d437`, read the current user instructions,
author questions, Step 0024 report and outer audit, and verified the current
branch and authoritative submodule. The working tree was clean. The branch is
82 commits ahead of its remote because the last normal pushes failed with an
HTTP 500; publication remains decoupled from scientific progress.

**Recovered state.** Step 0024 closed the cross-action recurrence-calibration
repair on the complete existing OSWorld-Human and CodeTraceBench populations.
It did not authorize another constructor family. Its result is strong but
bounded: the current operation-stack induction improves CodeTraceBench B-cubed
F1 from 0.475008 to 0.649173 while leaving OSWorld-Human unchanged, yet its
comparison to the external phase-change baseline remains mixed by metric and
framework. The paper also identifies phase/action/literal-tag fidelity as an
unanswered part of RQ3. Neither fact permits a story or RQ change.

**User constraint and decision rule.** Reuse the retained trajectories and raw
outputs first. Admit one modification only if error analysis shows a common,
mechanistically explainable failure of the existing algorithm and the proposed
change preserves its inputs, objective, outputs, and name. Merely trying another
cutoff, score, dataset, or isolated special case is not admissible. Any candidate
must be compared on the same complete populations and hidden labels already
used by Step 0024.

**Next action.** Audit the retained decision-level errors and existing paper
promise, then write one Markdown experiment plan for either (a) the smallest
principled correction supported by those errors or (b) a documented no-admit
decision if no such correction exists. An independent plan reviewer must approve
the plan before implementation or full recomputation.

### Node E002 — Error Audit, Paper-Value Admission, And Plan Approval

**Question.** Is there a shared error in the retained complete trajectories that
cannot be repaired by another pair-level cutoff, and can one least-change
sequence-local refinement test it without introducing a new algorithm family or
experiment source?

**Inputs and method.** The root reconstructed the retained Step 0024 decisions,
official scorer labels, raw NPMI values, calibrations, and sequence order. It did
not run a candidate accuracy calculation. Mixed-label ordered action-pair types
cover 3,367/3,691 OSWorld-Human decisions (91.2%) and 20,405/20,461
CodeTraceBench decisions (99.7%). Thus a rule that depends only on pair identity
cannot distinguish most occurrence-level boundary contexts. The retained output
also contains 367 and 1,423 multi-edge weak runs, respectively.

**Admission.** Admit one sequence-local refinement of the existing recurrence
algorithm. Step 0024 still determines threshold eligibility using unchanged
NPMI and calibrations. A same-action threshold decision remains unchanged. An
action-changing threshold boundary remains only when its raw NPMI is no greater
than each available immediate neighbor. Unseen and missing-neighbor values are
fixed in the plan. The final boundary set must be a subset of Step 0024. No
field, feature, score, cutoff, parameter, window, dataset, benchmark, model,
name, or second candidate is added.

**Independent review.** Round 1 returned REVISE because the first plan ordered
heterogeneous `npmi - applied_cutoff` margins and incorrectly called them local
continuity values. The root accepted that finding and revised the plan to use
raw NPMI only for local ordering, leaving cutoffs solely as eligibility tests.
The second and final review returns APPROVE with zero must-fix. Raw NPMI values
within a session share one reference model and transition sample space and are
therefore commensurate across the existing calibration strata.

The approved plan is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md), with
reviews in
[`experiment-001/plan-review-round-1.md`](experiment-001/plan-review-round-1.md)
and
[`experiment-001/plan-review-round-2.md`](experiment-001/plan-review-round-2.md).

**Scientific impact and decision.** Implement exactly the approved refinement
and its discriminating tests. Do not read candidate accuracy metrics before an
independent implementation audit authorizes REAL PREFLIGHT. This remains
post-hoc implementation-selection work under fixed RQ3 and fixed story.

### Node E003 — Implementation And Independent Audit

**Question.** Does the release implementation preserve Step 0024 eligibility,
apply only the approved raw-NPMI local refinement, construct final segments from
the refined decisions, and compare complete results to the correct Step 0024
baseline?

**Inputs and method.** The root changed the existing Rust decision pass to
materialize `threshold_boundary` before sequence-local refinement. Only an
action-changing threshold boundary is reconsidered; it remains final when its
raw NPMI is no greater than each available neighbor. Same-action decisions are
unchanged. The existing OSWorld-Human Python reference, CodeTraceBench scorer,
and exact Rust/Python equivalence path now expose and validate the same
threshold/final relation. Complete baseline pointers were updated from the old
global/Step 0023 artifacts to Step 0024.

The code adds no input, feature, score, cutoff, parameter, fallback, algorithm
name, dataset, benchmark, or second candidate. A direct unit fixture and a full
CLI fixture distinguish a non-minimum threshold edge from its lower-NPMI
neighbors and verify final segment construction.

**Verification and review.** All 43 Rust unit tests, 9 profile CLI tests, and 3
standard-trace CLI tests pass. Formatting, Clippy with warnings denied, Python
compilation, optimized release build, and `git diff --check` pass. A fresh
read-only reviewer explicitly used `research-experiment-design`, checked all
Rust/Python/scorer/baseline paths, and returned PASS with zero must-fix. It did
not run or inspect candidate accuracy. The review is
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md).

**Scientific impact and decision.** The implementation is valid but the
hypothesis remains untested. REAL PREFLIGHT is authorized exactly on
OSWorld-Human fold 0 and the first complete CodeTraceBench target. Diagnostic
metrics cannot change the rule or verdict.

### Node E004 — REAL PREFLIGHT

**Question.** Do both existing real-data paths execute the approved local
refinement with complete selected coverage, scorer separation, decision-subset
and same-action properties, and additive mass?

**Inputs and method.** The root ran the approved OSWorld-Human fold-0 evaluator
and the first sorted complete CodeTraceBench target using the reviewed release
binary. No code, plan, candidate, or metric changed between implementation
review and execution.

**Result.** Both paths are VALID. OSWorld-Human covers 45 sessions, 521
operations, and 476 decisions, suppresses 94 Step 0024 threshold boundaries,
adds none, preserves same-action decisions, and conserves all 521 units.
CodeTraceBench covers one 47-operation target and 46 decisions against the full
2,229-session/87,703-operation disjoint reference, suppresses 7 threshold
boundaries, adds none, preserves same-action decisions, and conserves all 47
units. Official stages load only after the Rust path predicts. Both summaries
classify displayed accuracy values as diagnostics and the hypothesis as not
tested. Full details are in
[`experiment-001/real-preflight.md`](experiment-001/real-preflight.md).

**Scientific impact and decision.** GO. Execute all five OSWorld-Human folds,
exact Rust/Python equivalence, and all 405 CodeTraceBench targets once. The
candidate and exact two-population B-cubed verdict remain fixed.

### Node E005 — Complete Run And Independent Result Review

**Question.** Does the approved sequence-local refinement yield an exact
B-cubed Pareto improvement over Step 0024 on both complete reused populations?

**Inputs and method.** With no code or plan change after preflight, the root ran
all five OSWorld-Human folds, complete Rust/Python equivalence, and all 405
CodeTraceBench targets once. A fresh reviewer explicitly used
`research-experiment-design` and independently reconstructed every primary and
diagnostic result from retained decisions, assignments, hidden keys, and Step
0024 baselines.

**Result.** The run is PASS / COMPLETE / MIXED. OSWorld-Human B-cubed F1 falls
from 0.786170 to 0.746958 and boundary F1 from 0.679922 to 0.547227.
CodeTraceBench B-cubed F1 rises from 0.649173 to 0.671671 while boundary F1
falls from 0.287106 to 0.272388. CodeTraceBench B-cubed improves in all four
frameworks, but that local gain cannot override the complete OSWorld loss.

The candidate suppresses 842 of 2,369 Step 0024 OSWorld boundaries and 2,067 of
6,492 CodeTraceBench boundaries. All final decisions are threshold subsets;
same-action decisions are unchanged. Rust/Python agree on all 3,691 OSWorld
decisions, 3,978 assignments, 1,814 segments, 139 motifs, and mass. Both source
populations, scorer isolation, target/reference separation, and CodeTraceBench
coverage are exact.

The complete report is
[`experiment-001/full-run.md`](experiment-001/full-run.md); independent review
is
[`experiment-001/result-review.md`](experiment-001/result-review.md).

**Scientific impact and decision.** The exact Pareto hypothesis is
contradicted. Do not adopt this candidate. Restore only its code/test/evaluator
changes, retain the result as a local precision/recall mechanism boundary, and
keep Step 0024 as the release algorithm. The fixed RQ3 hypothesis, thesis, four
RQs, contribution, and story do not change. No second candidate is authorized
inside Step 0025.

## WRITE Gate

### Node W001 — No-Change Disposition

The complete result rejects the candidate under its fixed rule. The candidate
implementation was removed exactly, and the five touched algorithm, test, and
evaluator files now have zero diff against the Step 0024 release commit. The
restored release passes all 42 Rust unit tests, 8 profile CLI tests, and 3
standard-trace CLI tests, plus formatting, Clippy with warnings denied,
optimized release build, Python compilation, and `git diff --check`.

No paper prose, result, RQ, positive hypothesis, thesis, contribution, or story
change is authorized. WRITE therefore completes with a no-change disposition.
Only the timestamped experiment history and concise current-frontier notes in
`docs/evaluation.md` and `docs/idea-story.md` record why the local candidate was
rejected and why Step 0024 remains authoritative.

## REVIEW Gate

### Node R001 — Independent Outer Audit

A fresh read-only auditor explicitly used `auto-research-orchestrator` and
returns PASS with zero must-fix. It confirms the fixed MIXED verdict, exact code
restoration, no-change WRITE disposition, unchanged paper/story/RQs/thesis,
and complete report trail.

The audit rejects a tempting sign-based combination of Step 0024 and Step 0025.
Although NPMI zero denotes independence, cutoff sign is completely confounded
with population identity in the current evidence: all OSWorld folds are
positive and favor Step 0024, while CodeTraceBench is negative and favors Step
0025. Selecting the refinement from that sign after observing both results
would indirectly select each population's winner rather than test a falsifiable
common mechanism.

The full audit is [`outer-audit.md`](outer-audit.md). Step 0025 closes PASS with
Step 0024 as the unchanged release algorithm and no paper modification.

## Open Objections

1. It is not yet known whether remaining mistakes share one correctable cause
   or are irreducible label/benchmark disagreement.
2. Improving aggregate B-cubed while worsening boundary precision, a framework,
   or work is not automatically a paper-level improvement.
3. Reusing development populations makes any successful result implementation
   selection evidence, not untouched confirmation; the paper must preserve that
   boundary.

## Next Node

Step 0026 may enter EXPERIMENT paper-value admission, but no implementation is
authorized. It must find one benchmark-independent common error mechanism in
the retained raw decisions before candidate scoring or record no-admit and
close the refinement branch.
