# Step 0022 — Repair Recurrence Calibration On Existing Trajectories

**Started:** 2026-07-15T03:15:26-07:00
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

The positive RQ3 hypothesis remains unchanged. This step tests one mechanism
repair inside the current operation-stack constructor; it cannot change the RQ,
hypothesis, story, paper contribution, or reader-facing claim because of a
local result. It does not edit the authoritative `docs/agentpprof-paper`
submodule, global skills, KVM material, or any branch.

## EXPERIMENT Gate

### Node E001 — Recovery, Prior-Step Publication, And Gate Entry

**Question and entry.** Can the specific action-change degeneration verified in
Step 0021 be repaired directly on the trajectories that have already run,
without opening a new benchmark, feature family, cutoff sweep, or algorithm
story? The user's current instruction is explicit: improve the algorithm on the
existing completed trajectories rather than create a new experiment source.

**Inputs and method.** The root resumed on
`research/semantic-flamegraph-artifacts-v2` at
`d01a16d1f3e1a7dc24dbbd9e541b6de6672b1d9d` with a clean worktree and the
authoritative submodule clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. It read the Step 0021 plan,
result review, outer audit, current evaluation frontier, current user
instructions, and the existing Rust/Python recurrence implementations. Step
0021 was committed coherently. Its normal push failed with remote HTTP 500;
the remote remains at `f2e878acbd5324806e05a698c34f727fb3d37cd6`.
That publication backlog does not change the scientific state and will receive
another normal best-effort attempt at this step boundary; force push and branch
switching remain prohibited.

**Prior evidence.** Step 0021's complete CodeTraceBench run covers 405 target
sessions, 20,866 operations, and 20,461 adjacent pairs with zero reference
overlap and no scorer input to Rust. The independent reviewer confirms that
20,391/20,461 recurrence decisions equal direct action-change. In the disjoint
reference, self-transitions occupy 38,171/38,478 high-cluster occurrences
(99.202%), and `install -> other` is the only cross-action transition above the
current cutoff. This is a precise common bottleneck, not a reason to change RQ3.

**Decision.** EXPERIMENT admits exactly one candidate: identical actions remain
continuous by identity, while the existing occurrence-weighted one-dimensional
two-means cutoff is fit only to NPMI scores for transitions whose action changes.
The NPMI definition, visible `session`/`action` inputs, unseen-transition rule,
motif construction, zero-parameter interface, output model, benchmarks,
metrics, and fixed RQ remain unchanged. The proposal is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).
Independent plan review is required before implementation.

### Node E002 — Independent Plan Review

**Question.** Is the single self-transition calibration repair scientifically
isolated, simple, executable, and judged by a fixed result rule without adding
a subjective gate or hidden experiment family?

**Inputs and method.** A fresh Step 0022 read-only reviewer used
`research-experiment-design`, the Step 0021 raw diagnosis and outer audit, the
current Rust/Python implementation, and the proposed plan. It explicitly
checked current-recurrence baseline ownership, two-development-population
honesty, scorer isolation, verdict mechanics, full-run coverage, and unnecessary
complexity.

**Review and repair.** The first review returned REVISE for two plan-only
defects. The root removed an undefined secondary boundary-metric veto and made
the B-cubed result rule mechanical. It also added the five actual commands and
exact preflight/full/equivalence terminal counts. It did not add an ablation,
baseline, benchmark, feature, threshold, significance procedure, gate, or
second candidate. The bounded follow-up returns APPROVE with zero remaining
must-fix findings. The full review is
[`experiment-001/plan-review.md`](experiment-001/plan-review.md).

**Scientific impact and decision.** The one candidate is authorized for
implementation. Result classification is fixed before code changes:
strictly higher B-cubed F1 on both complete observed populations is supported,
exactly one is mixed, and neither is contradicted. Boundary metrics remain
diagnostics. Implementation may repair only correctness/execution defects and
may not change the candidate from result feedback.

### Node E003 — Implementation, Focused Tests, And Independent Audit

**Question.** Does the code implement exactly the approved one-change principle
in both the Python reference and release Rust path, with existing interfaces,
labels, metrics, and current-recurrence baselines preserved?

**Inputs and method.** The root changed the existing Python recurrence
evaluator and `agentpprof/src/profile.rs`: NPMI still uses all reference
transitions, same-action pairs are explicitly continuous, and only cross-action
occurrences enter the same deterministic two-means. The CodeTrace and OSWorld
evaluators now validate and report the committed Step 0021/0020 recurrence
summaries as the main baselines. Existing CLI/unit fixtures received external
reference sequences with multiple cross-action NPMI values because the
approved candidate intentionally rejects a reference without two distinct
cross-action scores.

**Test history.** The first test run produced two expected invalid-fixture
failures: old unit fixtures contained only one cross-action score. After those
fixtures received valid reference data, the next compile exposed one root
placement error for `reference_path`, and the following run exposed the same
one-score issue in the legacy alias fixture. The root repaired only these test
fixtures and added one direct test of the new invariant. The terminal suite
passes 42 Rust unit, eight profile CLI, and three trace CLI tests. Python
compilation and diff checking pass, and `cargo build --release` completes for
`agentpprof 0.2.37`.

**Independent review.** A fresh read-only implementation auditor returned
REPAIR for two obsolete surrounding-script assumptions, not core algorithm
errors: fixed Step 0020 segment/motif totals in the equivalence script and
Step 0021 scientific-role metadata in the CodeTrace summary. The root removed
only those stale assumptions. Bounded follow-up returns PASS with zero
remaining must-fix. Details are
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md).

**Scientific impact and decision.** Implementation matches the approved
candidate and may enter REAL PREFLIGHT. No paper, idea story, design,
implementation canonical doc, RQ, hypothesis, or story has changed. The
candidate remains fixed regardless of preflight metrics.

### Node E004 — Two Real Preflights

**Question.** Do both existing real-data paths execute end to end with the new
binary and approved isolation, without treating diagnostic metrics as a
scientific result?

**Inputs and method.** The root ran the two exact preflight commands from the
approved plan in parallel after release build. OSWorld-Human selected fixed
fold 0: 45 held-out sessions, 521 operations, and 476 adjacent pairs, trained
from the other 242 sessions. CodeTraceBench selected the lexicographically
first complete 47-operation target and the full 2,229-session / 87,703-
operation target-disjoint reference.

**Results.** Both commands exit zero. OSWorld assigns every selected operation,
scores every pair once, excludes scorer fields, conserves all 521 units, and
reports `preflight-only; no scientific verdict`. Its reference calibration
uses 2,516 action changes and excludes 699 identity continuities. CodeTrace
scores all 46 pairs and 47 operations, loads complete official stages only
after Rust prediction, conserves all mass, and reports `tested_hypothesis: not
tested`. Its complete reference calibration uses 47,303 action changes and
excludes 38,171 identity continuities. The local pandas/bottleneck version
warning is non-fatal and does not affect parquet reading or output.

**Scientific impact and decision.** REAL PREFLIGHT passes only as an execution
and isolation check. Its boundary/B-cubed diagnostics are not interpreted and
did not change code, plan, or candidate. The approved next action is the three
complete runs: five-fold OSWorld Python evaluation, five-fold Rust/Python
equivalence, and all 405 CodeTraceBench targets.

### Node E005 — Complete Existing-Trajectory Runs

**Question.** Does the one approved calibration repair improve primary
B-cubed agreement on both already-completed populations without changing the
RQ, hypothesis, algorithm interface, benchmark, field set, or metric?

**Inputs and method.** The root ran exactly the three approved full commands
once with the fixed candidate. OSWorld-Human covers all five held-out folds:
287 sessions, 3,978 operations, and 3,691 adjacent pairs. CodeTraceBench covers
all 405 target-disjoint sessions, 20,866 operations, 20,461 adjacent pairs,
and 2,948 complete official stage intervals across four frameworks. No new
trajectory was collected and no result-driven parameter, cutoff, feature,
baseline, or second candidate was introduced.

**Results.** On OSWorld-Human, boundary F1 falls from 0.679922 to 0.542657 and
B-cubed F1 falls from 0.786170 to 0.742492. On CodeTraceBench, boundary F1
rises from 0.268506 to 0.287106 and B-cubed F1 rises from 0.475008 to 0.649173;
each of the four frameworks improves independently, although the pooled result
remains 0.005272 below phase-change. Rust and Python agree exactly on all
3,691 OSWorld decisions, 3,978 assignments, 2,107 segments, 42 unique motifs,
and all 3,978 units of mass. The complete record is
[`experiment-001/full-run.md`](experiment-001/full-run.md).

**Scientific impact and decision.** The fixed verdict is **MIXED** because the
primary metric improves on exactly one population. Excluding identity
repetitions from calibration repairs most of the CodeTraceBench degeneration,
but the same rule over-merges OSWorld-Human. This is a useful mechanism
boundary, not a universal algorithm improvement. The candidate is not adopted,
and no immediate tuning or second candidate is allowed inside this experiment.

### Node E006 — Independent Result Review And Candidate Restoration

**Question.** Are the complete outcomes valid and exactly recomputable, and
does the scientific decision preserve the strongest supported current
constructor without rewriting the paper from one mixed mechanism result?

**Inputs and method.** A fresh read-only result reviewer reconstructed every
primary score, diagnostic score, confusion count, population count,
per-framework result, calibration count, and equivalence total from raw
artifacts. It also inspected the approved plan, current source diff, fixed
paper contract, Step 0020/0021 baselines, and authoritative submodule.

**Review.** The reviewer returns PASS with zero must-fix and zero optional
findings. It confirms `VALID / COMPLETE / MIXED`, exact Rust/Python equivalence,
target/scorer isolation, complete coverage, and mass conservation. The review
is [`experiment-001/result-review.md`](experiment-001/result-review.md).

**Restoration and verification.** Following the fixed decision, the root
restored only Step 0022-owned candidate modifications. There is no tracked
candidate-code diff. The preserved current implementation passes 41 Rust unit,
eight profile CLI, and three trace CLI tests; Python compilation and diff
checking pass. The Step 0020 constructor remains the release implementation
and continues to own the paper-facing 0.680/0.786 result.

**Scientific impact and decision.** EXPERIMENT closes with a valid mixed
mechanism boundary. WRITE may update only canonical evaluation history; it may
not change the paper, design, implementation, RQ3, positive hypothesis, thesis,
or story. A different mechanism, if later selected, must begin in a new outer
cycle rather than being improvised from these results.

## Ranked Open Objections

1. The one calibration repair may improve partition agreement by merging
   routine action changes but reduce boundary fidelity through over-merging.
2. Both OSWorld-Human and CodeTraceBench are now observed development
   populations; even a positive result cannot become untouched cross-family
   confirmation.
3. Literal stage/tag names and the full phase/action components of RQ3 remain
   outside this experiment.
4. AAAI reproducibility completion remains separate from this mechanism step.

## WRITE Gate

### Node W001 — Canonical History Update Without Paper Rewrite

**Question.** Does this mixed mechanism result require any reader-facing paper
change, or only a canonical evaluation-history update?

**Inputs and method.** The root read the complete result review, current paper,
idea story, user instructions, evaluation frontier, and authoritative
submodule. It verified the exact thesis, exactly four fixed RQs, and the
unchanged Step 0020 implementation/result ownership. It also inspected the
paper diff and submodule status directly.

**Output.** `docs/evaluation.md` now records the Step 0022 full-population
tradeoff, exact evidence role, independent verdict, candidate non-adoption, and
raw artifact roots. `docs/paper/` has no diff. The authoritative
`docs/agentpprof-paper` submodule remains clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

**Scientific impact and decision.** WRITE completes with no paper, thesis,
RQ, hypothesis, design, implementation, or story change. A mixed candidate
that was not adopted cannot overwrite the current paper result. REVIEW must
now audit the full cycle, restoration, canonical history, research taste, and
next routing independently.

## REVIEW Gate

### Node R001 — Independent Outer Audit

**Question.** Did EXPERIMENT and WRITE complete their assigned scopes with
continuous provenance, correct evidence, candidate restoration, no story
drift, and an efficient next routing?

**Inputs and method.** A fresh reviewer with no Step 0022 planning,
implementation, execution, result-review, or writing role explicitly used the
`auto-research-orchestrator` outer-audit procedure. It read the complete step,
raw summaries, canonical evaluation frontier, fixed paper/idea/user contracts,
source status, Step 0020/0021 evidence, and authoritative submodule.

**Review.** The outer audit returns PASS with zero must-fix findings. It
independently confirms the two complete populations, exact primary deltas,
corrected 11,392 versus 47,303 calibration counts, Rust/Python equivalence,
fixed `VALID / COMPLETE / MIXED` verdict, candidate restoration, unchanged
Step 0020 implementation, zero paper diff, clean submodule, and unchanged
thesis/four RQs. It judges the step simple, aggressive, high-information, and
properly separated from paper-story authorization. The full audit is
[`outer-audit-20260715T035157-0700.md`](outer-audit-20260715T035157-0700.md).

**Scientific impact and decision.** REVIEW closes Step 0022 without repair.
The next outer state remains `BUILD_AND_EVALUATE -> EXPERIMENT_GATE`. Its
selection question is whether one recurrence criterion can distinguish
identity repetition, recurring cross-action continuity, and true boundaries
without Step 0022's OSWorld over-merging, while reusing the same trajectories.
This routing is not candidate authorization and causes no paper, thesis, RQ,
hypothesis, or story change.
