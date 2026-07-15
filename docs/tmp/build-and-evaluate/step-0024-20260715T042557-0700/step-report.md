# Step 0024 — Make Cross-Action Repair Monotone

**Started:** 2026-07-15T04:25:57-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gate:** CLOSED
**Status:** Complete
**Completed:** 2026-07-15T05:32:14-07:00
**Owner:** root orchestrator

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The original AgentProf story and exactly four RQs—attribution,
localization, tag accuracy, and cost—remain fixed. The selected question is
verbatim:

> **RQ3 — How accurate are the tags?**

The positive RQ3 hypothesis, paper contribution, and story cannot change from a
local mechanism result. The authoritative `docs/agentpprof-paper` submodule is
read-only. This step changes no global skill, KVM material, or branch.

## EXPERIMENT Gate

### Node E001 — Recovery And Monotone Candidate Selection

**Question and entry.** Can the cross-action calibration repair be constrained
to never add a boundary relative to the current constructor, while reusing the
same already-completed trajectories and preserving the large CodeTraceBench
gain?

**Inputs and method.** The root resumed after Step 0023 completed all gates and
committed as `06d6b7ef7ce9a66cb98b8cba5a35c8268dc8681b`. A normal push again did
not advance the remote, which remains at
`f2e878acbd5324806e05a698c34f727fb3d37cd6`; publication is decoupled from the
scientific state. The root read Steps 0020–0023, their independent reviews/raw
summaries, current code, and fixed scientific contracts.

**Cumulative evidence.** Step 0023 preserves the CodeTraceBench B-cubed gain
from 0.475008 to 0.649173 but is 0.001580 below current on OSWorld-Human. The
entire OSWorld difference is 11 additional false-positive boundaries created
where the cross-action cutoff is higher than the global cutoff. The diagnosed
problem is the opposite: identity-dominated global calibration can make the
cutoff too high and split recurring cross-action continuity. A repair should
therefore be allowed to lower that cutoff, never raise it.

**Selection.** Admit one monotonic constraint inside the same constructor.
Same-action pairs use the current global cutoff. Action-changing pairs use the
smaller of the current global and cross-action cutoffs. Unseen pairs remain
boundaries. This uses the same NPMI and two existing two-means calibrations with
no parameter, field, model, threshold search, fallback, new name, or new
trajectory. For every seen target pair, the candidate boundary set is a subset
of the current boundary set: it may recover continuity but cannot add a
boundary.

The proposal is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).
Independent plan review is required before implementation.

### Node E002 — Independent Plan Review

**Question.** Is taking the smaller of the two already-audited cutoffs one
principled monotone repair, and are its validity property and scientific verdict
complete without adding another algorithm family?

**Inputs and method.** A fresh read-only reviewer explicitly used
`research-experiment-design`, Steps 0020–0023, current code, and the fixed
paper/idea/user/evaluation contracts. It inspected mechanism rationale,
minimality, monotonicity, baselines, leakage, commands, verdict, and story
preservation.

**Review.** The reviewer returns APPROVE with zero must-fix. It judges `min` the
unique parameter-free least-change composition that allows cross-action
calibration only to lower the current cutoff. Exact candidate-boundary subset
is an appropriate validity property that rules out Step 0023's fragmentation
failure but does not replace B-cubed accuracy. The full review is
[`experiment-001/plan-review.md`](experiment-001/plan-review.md).

**Scientific impact and decision.** Implementation is authorized exactly as
planned. No tolerance, dominance test, third cutoff, fallback, special case,
field, score, benchmark, name, or second candidate may be added.

### Node E003 — Implementation And Independent Audit

**Question.** Does the release implementation exactly realize the approved
monotone constraint, preserve the current constructor outside that constraint,
and have a test that would fail if the implementation silently kept using the
global cutoff for action changes?

**Inputs and method.** The root changed the existing Rust constructor and the
two existing complete-population evaluation paths. It added the raw global and
cross-action calibrations, the applied cross-action cutoff, and per-decision
current/candidate outcomes to the existing report. It did not add a feature,
parameter, fallback, algorithm name, input, or dataset. The Python/Rust
equivalence path now compares raw and applied cutoffs, current and candidate
decisions, segments, motifs, and mass exactly. Existing JSON calibration fields
remain exact global aliases for compatibility.

The first independent implementation review correctly returned FAIL: the
initial fixture checked only the no-added-boundary invariant and did not hit a
decision that the candidate must actually change. The root repaired only that
test weakness, adding a `fill -> click` decision whose NPMI lies between the two
cutoffs. The Rust unit and external-reference CLI tests now require
`applied < global`, current boundary `true`, candidate boundary `false`, one
removed boundary, and zero added boundaries.

**Verification.** The repaired implementation passes 42 Rust unit tests, 8
profile CLI tests, 3 trace CLI tests, Python compilation for all three affected
scripts, `git diff --check`, and an optimized release build. A second read-only
review using `research-experiment-design` returns PASS with zero must-fix and
approves REAL PREFLIGHT. It confirms exact Rust/Python/CodeTraceBench semantics,
decision-set monotonicity, scorer isolation, compatibility aliases, and the
absence of hidden scope expansion. The full audit is
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md).

**Scientific impact and decision.** This node validates implementation, not
the hypothesis. The approved execution-only OSWorld fold-0 and one-target
CodeTraceBench preflights may run. Their metrics cannot choose or alter the
candidate.

### Node E004 — REAL PREFLIGHT

**Question.** Do both existing real-data paths execute the approved release
candidate end to end while preserving input isolation, complete selected
coverage, current-boundary subset, and additive mass?

**Inputs and method.** The root ran the approved OSWorld fold-0 preflight and
the first CodeTraceBench target with no code or plan change between them. The
preflight outputs are retained at their registered experiment paths. Metrics
were diagnostic only and did not select or alter the candidate.

**Result.** Both paths are VALID. OSWorld completes 45 sessions, 521 operations,
and 476 decisions with zero added current-relative boundaries and conserved
mass. CodeTraceBench completes one 47-operation target and 46 decisions; Rust
predicts before official stages load, removes eight current boundaries, adds
zero, and conserves all weight. Its summary explicitly records the tested
hypothesis as `not tested`. Full details and commands are in
[`experiment-001/real-preflight.md`](experiment-001/real-preflight.md).

**Scientific impact and decision.** This remains execution evidence only. The
candidate, plan, metrics, and fixed verdict are unchanged. The complete
OSWorld, Rust/Python equivalence, and CodeTraceBench runs may execute once.

### Node E005 — Complete Run And Independent Result Review

**Question.** Does the monotone candidate preserve the current OSWorld-Human
result while retaining the already-observed CodeTraceBench gain under the
fixed exact two-population replacement rule?

**Inputs and method.** With no change after preflight, the root ran all five
existing OSWorld folds, complete Rust/Python equivalence, and all 405 existing
CodeTraceBench targets once. A separate read-only reviewer explicitly used
`research-experiment-design` and reconstructed population counts, confusion
counts, B-cubed metrics, current-relative decisions, per-framework results,
coverage, isolation, equivalence, and conservation from retained raw outputs.

**Result.** The experiment is `VALID / COMPLETE / SUPPORTED`. OSWorld-Human is
exactly equal to current: B-cubed F1 0.786170 and boundary F1 0.679922, with all
3,691 current/candidate decisions identical. CodeTraceBench B-cubed F1 rises
from 0.475008 to 0.649173 and boundary F1 from 0.268506 to 0.287106; the
candidate removes 5,974 current boundaries, adds zero, and improves B-cubed in
all four frameworks. Rust/Python equivalence covers 3,691 decisions, 3,978
assignments, 2,656 segments, 44 motifs, and all 3,978 mass.

The exact rule requires no lower B-cubed F1 on both populations and strictly
higher on at least one. Equal plus higher therefore yields SUPPORTED. The full
run is [`experiment-001/full-run.md`](experiment-001/full-run.md); the
independent reconstruction is
[`experiment-001/result-review.md`](experiment-001/result-review.md).

**Scientific impact and decision.** Adopt the monotone candidate as the
release constructor. It is supporting post-hoc implementation-selection
evidence on two reused complete populations, not untouched confirmation or all
of RQ3. Route only algorithm-owned design, implementation, evaluation, and
paper text to WRITE. The thesis, four RQs, positive RQ3 hypothesis,
contribution, and original AgentProf story remain unchanged. The external
phase-change comparison remains a paper-review obligation even though it is
not part of the fixed current-versus-candidate adoption rule.

## Ranked Open Objections

1. Monotone merging can still over-merge true groups even though it cannot add
   false boundaries.
2. Both populations are observed post-hoc development evidence, not untouched
   confirmation.
3. Literal tag names and the complete phase/action scope of RQ3 remain outside
   this mechanism test.
4. The `min` constraint must remain the only change; no tolerance, dominance
   threshold, fallback, or special case is admissible.

## WRITE Gate

### Node W001 — Adopted-Implementation Sync

**Question.** Can the supported constructor and its directly owned result be
synchronized without changing the original story, thesis, contribution,
positive RQ3 hypothesis, or four-RQ structure?

**Inputs and method.** The root read the complete `docs/idea-story.md` from its
permanent baseline through the current frontier before editing. It updated only
the current recurrence algorithm and result boundary in `docs/design.md`,
`docs/implementation.md`, `docs/evaluation.md`, `docs/idea-story.md`, and the
active `docs/paper/`. The read-only authoritative submodule was not touched.
Steps 0022/0023 remain in experiment history; no negative mechanism result was
promoted into the paper.

**Output.** Design and implementation now specify global and cross-action
two-means plus the parameter-free applied cutoff
`min(global, cross_action)` for action changes. Canonical evaluation records
the exact equal-plus-higher adoption verdict and all raw roots. The paper keeps
the exact thesis, four RQs, two-object model, contribution, and original
motivation. It adds the monotone rule and its reused-population result: OSWorld
unchanged and CodeTraceBench B-cubed 0.475 to 0.649 across four frameworks
relative to the prior global constructor. Whole-paper review later required
the complete external phase-change tradeoff and exact 405-trajectory scope;
those repairs are recorded under REVIEW. The official CodeTracer/CodeTraceBench
paper is cited from the source repository's supplied BibTeX.

**Verification.** After REVIEW repairs and meaning-preserving tightening, the
AAAI paper builds successfully to nine letter-size pages, with complete paper
content ending on page seven and references beginning on page eight. The final
log has no undefined citation. The result is explicitly called post-hoc
implementation selection rather than confirmation of all RQ3.

**Scientific impact and decision.** WRITE sync is complete. No
narrative-evolution entry is added because no idea or story changed;
`docs/idea-story.md` records Step 0024 only as a mechanism/frontier update and
compares it with the fixed original baseline.

## REVIEW Gate

### Node R001 — Cross-Document Consistency Audit

**Question.** Do algorithm, results, scope, post-hoc boundaries, story, and
next-action pointers agree across the implementation, canonical documents,
idea history, paper, and retained evidence?

**Inputs and method.** An independent read-only reviewer explicitly used
`check-terminology-infoflow` across design, implementation, evaluation, idea
history, the active paper and bibliography, and the retained Step 0024 raw
results. The reviewer did not edit files.

**First result and repair.** No algorithm, number, thesis, RQ, or story
contradiction was found. Four stale pointers still routed RQ1, Step 0024,
historical Step 0019, or idea history to WRITE; one CodeTraceBench bibliography
annotation was overly broad. The root corrected only those pointers and
described the source as providing author-annotated stage labels and structured
step metadata. The same reviewer re-read the repairs and returned PASS with
zero must-fix.

**Final result.** After later whole-paper repairs, the reviewer ran again and
returned PASS with zero must-fix. It confirmed global/cross/min algorithm
identity, OSWorld equality, the 405 source-valid failed CodeTraceBench scope,
prior-global and external phase-change numbers, post-hoc interpretation,
NeMo/CodeTracer scope, fixed thesis/four RQs, and current pointers. The full
report is
[`cross-document-consistency-audit.md`](cross-document-consistency-audit.md).

**Scientific impact and decision.** Cross-document consistency is complete.
No new experiment, WRITE loop, idea change, or story update is authorized.

### Node R002 — Whole-Paper Attack, Repair, And Re-Review

**Question.** Does the complete paper make the strongest accurate Step 0024
claim while exposing the closest baseline and closest profiler work,
preserving the AgentProf story, and staying within seven paper-content pages?

**Inputs and method.** A separate read-only reviewer explicitly used
`iter-review-critique`, read the complete paper and Step 0024 evidence, rebuilt
the CodeTraceBench comparisons from retained raw output, and searched primary
sources for closest profiler work. It did not edit or request a new experiment.

**Initial result.** The first verdict was FAIL / 5 of 10 / Weak Reject for two
paper omissions, not an algorithm or result failure. First, the paper reported
B-cubed 0.475 to 0.649 without equally exposing that external phase change has
lower boundary F1 (0.225 versus 0.287), slightly higher pooled B-cubed F1 (0.654
versus 0.649), and two of four framework-level B-cubed wins, or precisely
scoping the 405 targets to source-valid failed verified-split trajectories.
Second, Related Work omitted the NVIDIA NeMo Agent Toolkit profiler.

**Repair.** The root kept the attractive current-relative result but labeled
the comparator and post-hoc/reused scope in the abstract, introduction,
contribution, RQ3, limitations, and conclusion. RQ3 now includes the complete
external phase-change tradeoff. Related Work accurately contrasts NeMo's
instrumented supported-workflow profiler with AgentProf's heterogeneous offline
histories and source-linked conserved projections, and positions CodeTracer's
hierarchical localization/replay traces. The NPMI equation cites Bouma and the
two-means calibration cites MacQueen. No experiment, benchmark, story, RQ, or
contribution was added. Repeated prose was tightened without removing
scientific facts so complete paper content again ends on page seven.

**Final result.** The same reviewer re-read the repaired paper and returned
PASS with zero must-fix and zero necessary should-fix. The full audit is
[`whole-paper-review.md`](whole-paper-review.md).

**Scientific impact and decision.** The complete-paper REVIEW inner loop is
closed. No additional experiment is required by this review.

### Node R003 — Verification Before Outer Audit

**Question.** Are the release implementation, scripts, paper, and authoritative
submodule valid for independent outer closure?

**Verification.** All 42 Rust unit tests, 8 profile CLI tests, and 3 standard
trace CLI tests pass. The three affected Python evaluators compile. `git diff
--check` passes. The paper builds to nine US-letter pages with references
starting on page eight and no undefined citation. The authoritative
`docs/agentpprof-paper` submodule remains clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. The branch remains
`research/semantic-flamegraph-artifacts-v2`; no branch operation occurred.

**Scientific impact and decision.** EXPERIMENT, WRITE, and REVIEW inner loops
were complete. At this point Step 0024 awaited only the independent outer audit; Git
publication remains decoupled from gate closure.

### Node R004 — Canonical Memory Repair And Final Re-Audit

**Question.** Does the canonical literature and current-state memory reflect
the completed Step 0024 review and outer decision, rather than preserving stale
Step 0020 or future-review routes?

**Inputs and method.** The first outer audit included
`docs/background-related-work.md`, which the earlier consistency scope had
omitted. The root then iterated with the same independent
`check-terminology-infoflow` reviewer over background, evaluation, and idea
history until no must-fix remained.

**Repairs.** Background memory now records Steps 0020--0024, the adopted
global/cross/min rule, exact OSWorld/CodeTraceBench/external-phase evidence,
post-hoc boundary, and NeMo/CodeTracer closest-work positions. Evaluation and
idea history now state that the whole-paper re-review and outer audit are
complete and PASS, historicalize the earlier Step 0018 4/10 verdict, and close
the recurrence and RQ2 packet branches without a future experiment route.

**Result and decision.** Final consistency re-audit returns PASS with zero
must-fix. The complete audit history is in
[`cross-document-consistency-audit.md`](cross-document-consistency-audit.md).

## Independent Outer Audit And Closure

An independent read-only auditor explicitly used
`auto-research-orchestrator`, checked all inner reports, raw evidence, current
diff, canonical memory, paper, tests, submodule, and branch boundaries, and did
not defer to inner verdicts. After the minimal canonical-memory repair, it
returns PASS with zero must-fix and confirms no return edge to EXPERIMENT,
WRITE, or REVIEW.

Direction, efficiency, and maintenance all PASS. The algorithm remains one
minimal supporting mechanism under the original story, directly reuses two
complete existing trajectory populations, and requires no skill or AGENTS
change. The full report is
[`outer-audit-20260715T053214-0700.md`](outer-audit-20260715T053214-0700.md).

Step 0024 is complete. The recurrence branch remains closed; Git publication
is a decoupled step-boundary persistence action rather than a scientific gate.
