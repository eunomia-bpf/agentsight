# Step 0023 — Condition Recurrence Without New Trajectories

**Started:** 2026-07-15T03:55:13-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gate:** EXPERIMENT
**Status:** Complete
**Owner:** root orchestrator

## Fixed Scientific Contract

This step preserves the exact thesis **“Agent observability needs profiling,
not only debugging.”**, the original AgentProf story, and exactly four fixed
RQs: attribution, localization, tag accuracy, and cost. The selected question
remains verbatim:

> **RQ3 — How accurate are the tags?**

The positive RQ3 hypothesis remains unchanged. A local mechanism result cannot
change the RQ, hypothesis, contribution, paper story, or reader-facing thesis.
The authoritative `docs/agentpprof-paper` submodule remains read-only. This
step does not change global skills, KVM material, or any branch.

## EXPERIMENT Gate

### Node E001 — Recovery, Step 0022 Closure, And Candidate Selection

**Question and entry.** Can the existing recurrence constructor be improved
directly on already-completed OSWorld-Human and CodeTraceBench trajectories,
without collecting a new trace, opening a benchmark, adding an input feature,
or replacing the operation-stack algorithm?

**Inputs and method.** The root resumed on the unchanged branch
`research/semantic-flamegraph-artifacts-v2` after Step 0022 completed all three
gates and committed as `07cd31af621e442704c7e959e6be8bbaf88a9d41`.
The normal push did not advance the remote, which remains 80 commits behind the
local branch at `f2e878acbd5324806e05a698c34f727fb3d37cd6`; publication state is
decoupled from science and does not block this cycle. The root read the full
Step 0022 plan, complete result, result review, outer audit, current Step 0020
implementation, fixed scientific contracts, and both sets of existing raw
artifacts.

**Cumulative evidence.** Step 0020's global NPMI cutoff is strong on
OSWorld-Human at B-cubed F1 0.786170 but degenerates toward action-change on
CodeTraceBench at 0.475008. Step 0022 changes two coupled decisions: it fits the
cutoff only on action changes and forces identical actions continuous. That
candidate raises CodeTraceBench to 0.649173 but lowers OSWorld-Human to
0.742492. Because Step 0022 changed those two decisions together, the aggregate
result cannot attribute the OSWorld regression to either one alone. It
motivates the direct component-isolation test below.

**Selection.** Admit one minimal conditioned decision inside the same
operation-stack constructor: same-action pairs use the current Step 0020
global cutoff, while action-changing pairs use the Step 0022 cross-action
cutoff. Both cutoffs are learned by the same existing deterministic
occurrence-weighted two-means over the same NPMI; there is no user parameter,
field, model family, sweep, or new name. This directly preserves current
same-action behavior while isolating the cross-action calibration component.

The full proposal is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).
Independent plan review is required before any implementation.

### Node E002 — Independent Plan Review

**Question.** Is the conditioned cutoff one simple and scientifically
motivated candidate, and can its full outcome be judged mechanically on the
existing trajectories without adding a hidden experiment family?

**Inputs and method.** A read-only reviewer explicitly used
`research-experiment-design`, the complete Step 0022 evidence, current
Step 0020 implementation, fixed user/idea/evaluation contracts, and the
proposed plan. It checked mechanism isolation, candidate simplicity, baseline
ownership, leakage, complete commands, verdict mechanics, and story
preservation.

**Review.** The reviewer returns APPROVE with zero must-fix. It judges the
single `left_action == right_action` condition a principled stratification of
two already-defined zero-parameter calibrations, not heuristic soup. A bounded
follow-up after the root removed a causal overstatement also returns APPROVE:
Step 0022's aggregate cannot identify which coupled component caused the
OSWorld regression, so Step 0023 correctly tests that component isolation.
Details are [`experiment-001/plan-review.md`](experiment-001/plan-review.md).

**Scientific impact and decision.** The plan is authorized exactly as written.
Implementation may add the global and cross-action cutoff reports and the one
conditional decision only. No additional field, cutoff, fallback, special
case, benchmark, metric, name, or candidate is allowed.

### Node E003 — Implementation, Tests, And Independent Audit

**Question.** Do Python and Rust implement exactly the approved conditional
calibration, with scorer isolation, auditable stratum decisions, and no hidden
mechanism or experiment expansion?

**Inputs and method.** The root modified only the existing recurrence path,
tests, OSWorld evaluator, equivalence checker, and CodeTraceBench adapter. Both
implementations compute unchanged NPMI, fit the current global two-means plus
the cross-action two-means, apply global only to same-action pairs and cross
only to action changes, keep unseen pairs as boundaries, and preserve motif
construction. Existing committed summaries supply current and Step 0022
component comparisons only after prediction.

**Tests.** Valid reference fixtures now exercise both target strata and two
distinct cross-action scores. The terminal suite passes 41 Rust unit, eight
profile CLI, and three trace CLI tests. Python compilation, release build,
formatting, and diff checking pass.

**Independent review and repair.** A fresh read-only implementation reviewer
returned REPAIR for one stale Step 0020 summary sentence that asserted local
improvement before a result. The root made only the requested metadata repair:
OSWorld reports an exact higher/equal/lower relation, while the Pareto verdict
requires both full populations. Bounded follow-up returns PASS with zero
remaining must-fix. Details are
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md).

**Scientific impact and decision.** The fixed candidate may enter REAL
PREFLIGHT. No paper, design, implementation canonical doc, idea story, RQ,
hypothesis, thesis, or contribution has changed. Preflight is execution-only
and cannot tune or select the candidate.

### Node E004 — Two Real Existing-Trajectory Preflights

**Question.** Do the two existing real-data paths execute the approved
conditional rule end to end, engage both strata, preserve isolation/coverage,
and emit no scientific verdict?

**Inputs and method.** After the audited release build, the root ran the exact
two approved preflight commands in parallel. OSWorld-Human selected fixed fold
0: 45 held-out sessions, 521 operations, and 476 pairs, trained from the other
242 sessions. CodeTraceBench selected the lexicographically first complete
47-operation target and the complete target-disjoint 2,229-session / 87,703-
operation reference.

**Execution results.** Both commands exit zero. OSWorld scores every selected
pair once, assigns every operation, conserves all 521 units, and reports
`preflight-only; no scientific verdict`. Its reference has 699 same-action and
2,516 action-changing transitions, with global cutoff 0.231168 and cross-action
cutoff 0.280594. CodeTraceBench scores all 46 pairs, assigns 47 operations,
conserves all mass, loads official stages after Rust prediction, and reports
`tested_hypothesis: not tested`. Its reference has 38,171 same-action and
47,303 action-changing transitions; the selected target engages 19 global and
27 cross-action decisions. The local pandas/bottleneck warning is non-fatal.

**Scientific impact and decision.** REAL PREFLIGHT passes only execution,
engagement, isolation, coverage, and conservation. Displayed metrics are not
interpreted and did not change the candidate or plan. The three complete runs
are authorized once each on the same existing trajectories.

### Node E005 — Three Complete Existing-Trajectory Runs

**Question.** Does the fixed conditioned rule meet exact Pareto improvement on
both complete populations?

**Inputs and method.** The root ran the approved OSWorld five-fold evaluator,
five-fold Rust/Python equivalence, and all-target CodeTraceBench evaluator once
in parallel. No trace was recollected, no normalized operation changed, and no
result-driven rule, threshold, parameter, or candidate was added.

**Results.** OSWorld-Human candidate B-cubed F1 is 0.784589 versus current
0.786170, delta -0.001580; boundary F1 is 0.678114 versus 0.679922. The
candidate preserves current same-action decisions but adds 11 false-positive
cross-action boundaries and 11 groups. CodeTraceBench candidate B-cubed F1 is
0.649173 versus current 0.475008, delta +0.174165; boundary F1 is 0.287106
versus 0.268506. It exactly equals the Step 0022 component and improves
B-cubed over current in all four frameworks. Rust/Python equivalence passes on
3,691 decisions, 3,978 assignments, 2,667 segments, 44 motifs, and all 3,978
units. Full details are
[`experiment-001/full-run.md`](experiment-001/full-run.md).

**Scientific impact and decision.** The fixed verdict is **MIXED**: one
population is strictly lower and one strictly higher. The repair reduces the
Step 0022 OSWorld regression from -0.043677 to -0.001580 while retaining its
CodeTraceBench gain, but exact Pareto support is not met. The candidate is
frozen pending independent result review; no second candidate is allowed.

### Node E006 — Independent Result Review

**Question.** Are the complete results valid and exactly supported by raw
artifacts, and what implementation/paper decision follows from the fixed rule?

**Inputs and method.** A fresh read-only result reviewer explicitly used
`research-experiment-design` and reconstructed both complete populations,
scores, component decisions, per-framework outcomes, cutoffs, counts,
equivalence, isolation, coverage, and conservation from raw files.

**Review.** The reviewer returns PASS for `VALID / COMPLETE` with zero validity
blockers and confirms the overall hypothesis verdict **MIXED**. It verifies that
the candidate exactly retains Step 0020 same-action decisions, uses Step 0022
cross-action decisions, and equals Step 0022 on CodeTraceBench. The full review
is [`experiment-001/result-review.md`](experiment-001/result-review.md).

**Scientific impact and decision.** The candidate fails the fixed replacement
rule and must not replace current Step 0020. Restore only Step 0023-owned code,
test, and script modifications, retain all raw/Markdown evidence, and make no
paper, RQ, hypothesis, thesis, contribution, or story change. No new candidate
is admitted inside Step 0023.

**Restoration and verification.** The root restored only Step 0023-owned
changes in `agentpprof/src/profile.rs`, its focused tests, and the three
recurrence evaluators. No tracked candidate-code diff remains. The restored
current implementation passes 41 Rust unit, eight profile CLI, and three trace
CLI tests; Python compilation and diff checking pass. The paper has no diff and
the authoritative submodule remains clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

## Ranked Open Objections

1. The conditioned cutoff preserves same-action decisions but can raise the
   current cross-action cutoff and added 11 false boundaries on OSWorld-Human;
   the next outer selection must decide whether a monotone repair is warranted.
2. Two observed populations are post-hoc mechanism-development evidence, not
   untouched cross-family confirmation.
3. Literal name correctness and the full phase/action scope of RQ3 remain
   outside this one partition-construction experiment.
4. Any later repair must remain one simple principle rather than accumulate
   fallback thresholds or special cases.

## WRITE Gate

### Node W001 — Canonical Mechanism History Without Paper Rewrite

**Question.** Does the valid mixed component-isolation result require a paper
change, or only an update to canonical evaluation history?

**Inputs and method.** The root read the complete plan, reviews, raw-result
summary, current paper, idea story, user instructions, evaluation frontier,
and authoritative submodule. It verified the exact thesis, exactly four fixed
RQs, unchanged positive RQ3 hypothesis, candidate non-adoption, and current
Step 0020 result ownership.

**Output.** `docs/evaluation.md` now records the exact Step 0023 population
relations, 11-boundary OSWorld difference, CodeTraceBench component equality,
equivalence totals, fixed MIXED verdict, raw roots, and candidate restoration.
`docs/paper/`, `docs/idea-story.md`, `docs/design.md`, and
`docs/implementation.md` have no Step 0023 change.

**Scientific impact and decision.** WRITE completes without changing the
paper, thesis, RQs, hypothesis, contribution, design, implementation, or story.
REVIEW must independently audit the full cycle and select the next outer action
without introducing a second candidate inside Step 0023.

## REVIEW Gate

### Node R001 — Independent Outer Audit

**Question.** Did the full cycle preserve scientific contracts and one-candidate
discipline, restore rejected code exactly, maintain auditable provenance, and
select the next high-value action without extending this experiment?

**Inputs and method.** A fresh reviewer explicitly used the
`auto-research-orchestrator` outer-audit procedure and read the full Step 0023
record, raw summaries, current source/test state, evaluation history, fixed
paper/idea/user contracts, and authoritative submodule.

**Review.** The audit returns PASS with zero must-fix. It confirms complete
EXPERIMENT and WRITE gates, exact `VALID / COMPLETE / MIXED` evidence,
independent reviews, candidate restoration, current 41+8+3 passing tests, zero
paper/submodule drift, unchanged thesis/four RQs/positive hypothesis/story, and
no new trajectory, field, parameter, term, sweep, or second candidate. The full
audit is
[`outer-audit-20260715T042408-0700.md`](outer-audit-20260715T042408-0700.md).

**Scientific impact and decision.** REVIEW closes Step 0023 without repair.
The next state is `BUILD_AND_EVALUATE -> EXPERIMENT_GATE`. Its selection
question is whether cross-action calibration can be monotone—never raise the
current global cutoff—while retaining the CodeTraceBench gain and avoiding the
11 added OSWorld boundaries. This is not implementation authorization inside
Step 0023 and changes no scientific contract.
