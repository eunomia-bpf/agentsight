# Step 0034 — Cross-Domain Calibration Of Existing Recurrence Scores

**Entered:** 2026-07-16T17:52:04-07:00

**Phase:** `BUILD_AND_EVALUATE`

**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`

**Current state:** complete; next transition is a fresh root-selected
`EXPERIMENT_GATE`

**Fixed thesis:** **Agent observability needs profiling, not only debugging.**

**Selected paper question:** **RQ3 — How Accurate Are the Tags?**

## Resume And Entry Audit

Step 0033 is complete, independently reviewed, and committed as `c5367c58` on
the unchanged `research/semantic-flamegraph-artifacts-v2` branch. Its two normal
push attempts did not advance the remote; the branch begins this step 92 commits
ahead. The push backlog is persistence-only and does not block research. The
read-only `docs/agentpprof-paper` submodule remains clean at `7f80c433`.

At gate entry, the root read the complete `docs/user-instruction.md`,
`docs/questions-for-author.md`, `docs/idea-story.md`, `docs/evaluation.md`,
`docs/background-related-work.md`, `docs/design.md`, `docs/implementation.md`,
the paper's four RQs and complete RQ3 section, the completed Step 0033 report
and outer verdict, and the current recurrence/calibration artifacts. There are
no open author questions. The exact thesis, four RQs, two core abstractions,
submodule-derived story, and positive RQ3 hypothesis remain fixed.

The user asks to continue experimentation, improve the algorithm on already-run
trajectories instead of inventing another benchmark, prefer real published
assets, keep the experiment simple and complete, and never shrink the story or
wait for human judgment. The gate therefore rejects another RQ2 metric, score,
cutoff, benchmark, or reader run: Step 0033 already holds strong diagnostic
scores fixed and shows the effect of grouping on all three complete RQ2
workloads. Repeating that comparison would be redundant.

## EXPERIMENT_GATE

### Node 001 — Bounded Literature And Existing-Artifact Screen

**Context and status.** At 2026-07-16T17:52:04-07:00, the root opened one
claim-oriented source screen before experiment admission. Its detailed search,
verification, coverage decision, and baseline handoff are in
[`literature-20260716T175204-0700/literature-report.md`](literature-20260716T175204-0700/literature-report.md).

**Question and inputs.** The screen asked whether a threshold learned from one
grouped trajectory domain can be transferred to another after converting the
same recurrence score to a within-domain empirical percentile. It checked the
current Step 0024 label-free recurrence, Step 0030 per-domain grouped-reference
calibration, official AAAI/ACL/EMNLP primary sources on cross-domain threshold
transfer and rank calibration, and the complete local OSWorld-Human and
CodeTraceBench artifacts.

**Result and decision.** Published work establishes source-to-target threshold
transfer and rank/score normalization as credible protocols, but no source
settles the AgentProf question or supplies an operation-stack implementation.
The existing artifacts expose a load-bearing calibration problem: the selected
raw NPMI cutoff is `-0.0982` on CodeTraceBench but `0.2501`--`0.4151` across
OSWorld folds. Per-domain grouped calibration improves B-cubed F1, but it does
not show that one calibration policy transfers to unseen agent/task domains.
The selected candidate keeps the current NPMI recurrence score and changes only
the scale on which its cutoff is expressed: the occurrence-weighted empirical
CDF percentile within each unlabeled reference population. This is one
calibration improvement to the existing algorithm, not a new RQ, benchmark,
score term, feature set, or named abstraction.

**Paper-value disposition.** The candidate is admitted for formal plan review
because a positive result would remove a major post-hoc/per-domain objection to
the automatic constructor and directly strengthen RQ3's unseen-family
prediction. A contradictory result would keep the current label-free default
and per-domain optional calibration and would bound only cross-domain cutoff
transfer. It would not change RQ3, the thesis, the story, or the two-object
model. Another RQ2 comparison, another literal taxonomy cell, and another
action-pair feature/threshold tweak were rejected as lower-value or explicitly
closed branches.

### Node 002 — Experiment Plan And Independent Review

The selected experiment will use one integrated bidirectional matrix over the
already complete OSWorld-Human and CodeTraceBench populations. Source group
labels may fit one percentile threshold; target group labels remain unavailable
until all target predictions are fixed. Current label-free recurrence is the
single main baseline. Raw-cutoff transfer is the normalization ablation, and
per-domain calibration is an annotation-spending upper-bound control. B-cubed
F1 is primary and boundary F1 is secondary. No target-domain tuning, new trace,
new model, new benchmark, or paper edit is permitted before plan review.

The formal plan is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md), with
the complete serial review in
[`experiment-001/plan-review.md`](experiment-001/plan-review.md). The first
review found one blocker: the plan scheduled paired bootstrap intervals but did
not use them to distinguish a supported point ordering from an inconclusive
one. The root made only that repair, naming 95% percentile intervals and making
the positive, mixed, contradictory, and inconclusive rules mutually exclusive.
It also corrected `unseen-family`/`decisive` wording to supporting cross-domain
evidence on complete reused populations. The same reviewer then returned
`plan status: PASS` in round two. It requested no new workload, baseline,
algorithm, implementation layer, or paper change.

No preflight or target metric was run before approval. The approved next node
is one real preflight through both source-fit and target-prediction paths.

### Node 003 — Real Preflight

The approved command completed in 7.9 seconds with `run_status: valid` and
`tested_hypothesis: not tested`. It fitted the full 483-session solved
CodeTrace source, persisted predictions for one real held-out OSWorld session,
and only then constructed its two-group oracle mapping. The fixed OSWorld
eligibility loader had parsed label-bearing rows but returned only actions; no
group identity or boundary entered prediction. The run subsequently fitted the
complete OSWorld grouped source, persisted predictions for one real failed
CodeTrace session, and only then loaded its 10 official stages. The two target
cases contain 11/47 operations and 10/46 adjacent pairs respectively; every
operation and pair is represented once under candidate, raw-transfer, and
current label-free recurrence.

The right-continuous empirical CDF is finite, bounded, and monotone. The source
fits select CodeTrace percentile/raw cutoffs `0.223273`/`-0.098247` and
OSWorld percentile/raw cutoffs `0.702384`/`0.266551`. Preflight scores are
dependency diagnostics only; they are not inspected to revise a cutoff,
method, outcome rule, or paper claim. The complete run must use the identical
implementation and fixed plan.

### Node 004 — Complete Bidirectional Run

The unchanged implementation completed every registered cell and classified
the tested hypothesis `contradicted`. On OSWorld-Human, percentile transfer
reaches B-cubed F1 `0.677607` versus current label-free `0.786170` (delta
`-0.108562`, paired 95% interval `[-0.138246, -0.078428]`). On
CodeTraceBench, it reaches `0.473242` versus `0.649173` (delta `-0.175931`,
interval `[-0.189732, -0.161417]`). Both are complete-population losses.

The normalization nevertheless beats direct raw-cutoff transfer in both
directions: `+0.037077` on OSWorld and `+0.074719` on CodeTrace, with wholly
positive intervals. It fixes numerical scale mismatch but not the domain
difference in desired group semantics: the candidate over-merges OSWorld to
1,316 groups and over-fragments CodeTrace to 12,941. All 24,844 operations,
24,152 adjacent pairs, and 20,000 stratified paired-bootstrap draws complete;
the label-free baselines reproduce Step 0024 exactly.

The complete result and proposed interpretation are in
[`experiment-001/result-report.md`](experiment-001/result-report.md), with raw
assignments, pair decisions, bootstrap draws, and summary under
`.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/full/`.
Following the approved terminal rule, no Rust port, alternate normalization,
target-specific percentile, paper edit, RQ change, or story change occurs. A
fresh result reviewer must now recompute the claims and determine validity,
research value, paper impact, and next paper decision.

### Node 005 — Independent Result Review

The fresh reviewer parsed all 68,996 raw records and independently rebuilt the
visible-input NPMI associations, empirical CDFs, source fits, every target
decision, standard B-cubed and exact-boundary metric, and a second stratified
paired bootstrap. It returns `VALID / CONTRADICTED / SUPPORTING / MECHANISM OR
WORKLOAD BOUNDARY`; its complete audit is
[`experiment-001/result-review.md`](experiment-001/result-review.md).

The review reproduces all populations and metric values, confirms the current
label-free baseline and equal-information raw-transfer comparison are fair,
and finds no target-outcome-informed retry. Its independent intervals preserve
all four signs. It records two non-invalidating deviations: the OSWorld reader
parses label-bearing rows solely for fixed eligibility before returning only
actions, and the cutoff fitter uses an empty-interval midpoint between observed
CDF values. Neither exposes group identity to prediction or changes any target
decision. Because the registered positive rule fails, no Rust port is required.
The reviewer directs no paper, thesis, RQ, hypothesis, or story change.

## WRITE_GATE

### Entry And Scientific-Contract Audit

WRITE entered after the independently valid contradictory result. The root
reread the result review, current paper RQ3 section, complete Initial Narrative
and evolution history, and user instructions. The experiment tests only whether
one scalar grouped-source recurrence cutoff transfers across two domains. Its
failure does not directly challenge the fixed thesis, four RQs, operation and
operation-stack abstractions, evaluation promise, or original story. The
scientific contract is unchanged; no idea disposition, story rewrite, claim
narrowing, or `docs/idea-story.md` entry is authorized.

### Targeted Writing Disposition

The reader-facing result entry condition fails: the approved plan and result
review both require no paper row for a contradicted development mechanism. No
targeted paper-writing skill, prose rewrite, figure, result table, abstract,
introduction, design, conclusion, or bibliography edit runs. The complete
mechanism boundary instead enters the internal canonical memory in
`docs/evaluation.md`; `docs/background-related-work.md` now records that
published threshold/rank precedent motivates the test but does not overcome
domain-dependent grouping semantics. The plan, reviews, result report, and raw
artifacts remain linked rather than copied.

### Paper Verification And Exit

`make -C docs/paper` reports the current PDF up to date. The active AAAI-27
paper remains nine US-letter pages, all fonts shown by `pdffonts` are embedded
Type 1, main content ends on page seven, and pages eight and nine contain only
references. The exact thesis appears unchanged, the evaluation still declares
exactly the four fixed RQs, and neither `docs/paper/` nor the read-only
`docs/agentpprof-paper` gitlink has a worktree change. The submodule remains at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

WRITE exits with an explicit paper-edit skip and a complete internal evidence
update. The handoff is the unchanged full paper plus this cycle's negative
mechanism record for whole-paper REVIEW and outer audit.

## REVIEW_GATE

### Entry And Review Scope

REVIEW entered with the complete valid negative result, the unchanged paper,
the EXPERIMENT/WRITE records above, and the fixed scientific contract. The root
reread the complete user instruction and idea history before disposition. The
user's persistent request asks both whether the paper is AAAI-ready and what
scientific iteration remains, so one user-requested milestone review was
permitted despite the `BUILD_AND_EVALUATE` phase. It did not receive authority
to rewrite the story, reopen a settled RQ merely by preference, or set the next
experiment.

The fresh reviewer completed four serial read-only nodes under
[`milestone-review-001`](milestone-review-001/): blind full-paper read,
external primary-source search, source-grounded reread, and cycle audit. It
classified the paper cross-domain and returned `reject / not submission-ready`
at the current AAAI-27 bar. The most material attacks are that known pprof,
Perfetto, causal-monitoring, process-abstraction, and agent-analytics primitives
make generic aggregation novelty unsafe; R114 proves scoped lineage and
lossless folding but not independent semantic-responsibility correctness; the
R170 mixedness result uses prompt tags as both grouping input and separation
reference; and RQ3 still lacks literal phase and untouched finalized-constructor
evidence. It also requested stronger RQ2 human/developer consequence evidence,
broader reproduction material, and several narrative reductions.

### Root Disposition Of Reviewer Evidence

Reviewer findings are evidence rather than authority. The root disposition is:

1. **Accept Step 0034 validity and stop condition.** The standard B-cubed and
   exact-boundary metrics, complete populations, paired uncertainty, and raw
   recomputation establish a valid contradiction of scalar percentile
   transfer. Further OSWorld/CodeTrace recurrence cutoff, percentile,
   normalization, or equivalent scalar search is closed.
2. **Accept the RQ1 evidence distinction, not a smaller RQ1.** Direct inspection
   confirms that R114 establishes source lineage and conservation, whereas
   R170 mixedness is conditional on a prompt tag that also defines the grouping
   reference. The root therefore marks independent attribution improvement as
   open and selects one same-input RQ1 comparison as the next candidate. This
   preserves the exact positive hypothesis and seeks more evidence rather than
   narrowing it.
3. **Accept the closest-work pressure as experiment and later-writing input.**
   The source frontier now records pprof/Perfetto/Pivot Tracing, process
   abstraction, current cross-trace agent analytics, CHIEF, Signals, and the
   standard B-cubed precedent. It does not adopt the reviewer's proposed
   integration-only replacement claim or modify the paper in this step.
4. **Reject automatic RQ2 reopening.** Step 0033 answers the frozen problem-
   correspondence/ranking promise with one standard primary metric over all
   three complete workloads. Human productivity, remediation, and official-
   benchmark SOTA would be stronger additional evidence, but were not the
   frozen RQ2 completion condition and are not the next experiment.
5. **Reject story shrinkage and mechanism deletion.** The exact thesis, four
   RQs, operations, operation stacks, three contributions, and submodule-derived
   problem/motivation remain fixed. Reviewer proposals to replace the thesis
   with an integration claim, demote the operation stack, or delete existing
   positive evidence are not accepted.
6. **Defer acknowledged RQ3 and submission issues.** Literal phase identity,
   an untouched finalized-constructor test, a serious process-abstraction
   baseline, claim-oriented Related Work, hierarchy/causality explanation, and
   final reproducibility cleanup remain ranked paper-wide objections. They do
   not invalidate Step 0034 and follow the higher-value RQ1 experiment rather
   than creating another local metric or taxonomy cell now.

### Independent Outer Audit And Meta-Review

The independent reviewer then wrote the step's only outer audit:
[`outer-audit-20260716T190334-0700.md`](outer-audit-20260716T190334-0700.md).
It returns **PASS — `VALID / COMPLETE / CONTRADICTED / SUPPORTING MECHANISM
BOUNDARY`**. It independently covers EXPERIMENT, WRITE, and REVIEW; confirms
that B-cubed plus exact-boundary P/R/F1 are established and claim-matched;
approves the no-paper-change disposition; verifies no scientific-contract,
paper, submodule, design, implementation, idea-story, or skill drift; and
closes the percentile branch. Its next-action language is explicitly advisory
and leaves experiment selection to the root.

**Direction.** Step 0034 passes its declared scope but contributes only useful
bounded falsification. The ambitious paper remains visible and unchanged. The
paper-wide milestone verdict remains reject/not ready, so submission is not the
next transition.

**Efficiency.** One simple candidate, one equal-information ablation, one
operational baseline, complete real populations, and one primary metric kept
the node internally economical. Its marginal paper value is low after many
recurrence studies; the branch closure prevents further proxy optimization.

**Maintenance.** `docs/evaluation.md` now distinguishes source-lineage evidence
from independent attribution improvement, records standard-metric validity and
the next candidate, and preserves the complete Step 0034 boundary.
`docs/background-related-work.md` records the new primary-source and metric
frontier. `docs/idea-story.md`, `docs/design.md`, `docs/implementation.md`,
`AGENTS.md`, all shared skills, and the paper remain unchanged. The step exposes
no new stable repository workflow warranting another rule or skill.

### Ranked Open Objections

1. **Next:** independently defined RQ1 responsibility attribution under
   same-input information and established source-native/labeled-profiler
   alternatives, reusing complete real trajectories first.
2. **Then:** RQ3 literal phase identity and untouched final-constructor evidence
   against a serious process-abstraction/hierarchical baseline.
3. **Before submission:** isolate the novelty delta against current population
   analytics and profiling/query primitives in both evidence and Related Work.
4. **Before submission:** make ordered-field and cross-layer lineage semantics
   precise enough for concurrency, missing links, and conflicting fields.
5. **Final writing phase:** complete claim-oriented citation coverage,
   reproducibility disclosures, artifact hygiene, and a fresh AAAI format and
   acceptance review.

None of objections 2--5 invalidates this step's result or justifies reopening
the closed percentile branch. The reviewer-only RQ2 utility request remains a
deferred stronger-evidence wish, not an open frozen-promise RQ.

## Current Transition

Step 0034 is complete. Start Step 0035 in `BUILD_AND_EVALUATE /
EXPERIMENT_GATE` with exactly **RQ1 — Does Semantic Profiling Improve Resource
Attribution?** The bounded source/artifact screen must first test whether the
already-complete R114/R170 and other existing real trajectories contain an
independent responsibility target unavailable to construction. If they do, the
experiment uses them and the smallest information-equivalent source-native and
established labeled-profiler/trace-query alternatives. If they do not, select a
real official external asset rather than inventing a toy harness. The primary
outcome is correct independently defined responsibility or decision, not mass
conservation, prompt-tag mixedness, another cutoff, or presentation quality.

The thesis, four RQs, positive hypotheses, two-object model, submodule story,
and current paper stay unchanged. Git persistence follows once for this
completed step after final verification; its success or failure does not affect
the scientific transition.
