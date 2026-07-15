# Step 0021 — Confirm Unchanged Recurrence On Reused Code-Agent Trajectories

**Started:** 2026-07-15T02:34:51-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gate:** REVIEW
**Status:** Complete
**Owner:** root orchestrator
**Completed:** 2026-07-15T03:11:46-07:00

## Fixed Scientific Contract

This step preserves the exact thesis **“Agent observability needs profiling,
not only debugging.”**, the original AgentProf story, exactly four paper-level
RQs, and the existing recurrence algorithm. It does not edit the read-only
`docs/agentpprof-paper` submodule, invoke an idea revision, or tune the already
observed OSWorld-Human population.

The selected paper question remains verbatim:

> **RQ3 — How accurate are the tags?**

The fixed positive paper hypothesis remains that a pre-specified target-blind
tagger or mapping recovers accurate, stable task, phase, action, and boundary
identities on unseen agent and task families. This step tests only whether the
released label-free recurrence constructor recovers independently annotated
stage partitions on a second real trajectory family. It cannot rename, split,
merge, or weaken RQ3.

## EXPERIMENT Gate

### Node E001 — Resume And Recovery Audit

**Context.** Recovery started at 2026-07-15T02:34:51-07:00 after completed
Step 0020. The active branch is
`research/semantic-flamegraph-artifacts-v2` at
`2672447390a713ca4c9f1d45417aa341d3f7cbe0`; it is 78 commits ahead of the
remote because prior normal pushes did not advance. The worktree was clean.
The authoritative paper submodule was clean and untouched at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

**Question and entry.** Step 0020 completed the user's requested algorithm
improvement on already-run OSWorld-Human trajectories. It raised boundary F1
from 0.4720 to 0.6799 and B-cubed F1 from 0.6720 to 0.7862, then ported the
mechanism to the existing Rust induction interface. Its independent outer
audit passed, but correctly classified the same-corpus result as post-hoc
mechanism development. The open empirical question is therefore whether an
unchanged port works on an independent annotated family without collecting a
new benchmark.

**Inputs and method.** At entry the root read the current user instructions,
questions-for-author file, complete idea story, evaluation frontier, Step 0020
report and outer audit, current RQ3 paper section, the experiment-design skill,
its plan template, and the hierarchical-state-machine resume and report
requirements. There are no open author questions. The current instruction is
already logged in `docs/user-instruction.md`: reuse trajectories that have
already run instead of creating a new experiment source.

**Scientific impact and decision.** Step 0020 remains complete and is not
reopened. This step enters a new EXPERIMENT gate only for independent
confirmation. No paper, idea-story, implementation, or algorithm file has been
changed at recovery.

### Node E002 — Existing-Asset Screen And Paper-Value Admission

**Question.** Which already-downloaded real trajectory family can test the
unchanged recurrence constructor against independent group or stage
annotations without making the input and target the same field?

**Inputs and method.** The root inspected the existing RQ3 task/action assets,
the complete CodeTraceBench RQ2 artifacts and official manifests, existing
AgentProcessBench traces, and normalized AgentNet, AgentReward, and SATraj
operations. Candidate labels were checked against the recurrence input rather
than accepted because they had a convenient field name.

**Results and raw evidence.** AndroidControl and GUI-Odyssey action cells are
inadmissible for recurrence action-identity confirmation: their source-native
action type is the same information normalized into the algorithm's `action`
input, so a literal action score would be circular. AgentProcessBench's local
`phase` is a project-derived ordinal rule and its human labels measure step
quality, not phase identity. AgentNet, AgentReward, and SATraj likewise provide
problem labels or project-derived phase mappings rather than an independent
operation partition.

CodeTraceBench is admissible. Its already-downloaded official verified
manifest contains complete source-authored stage intervals for 1,000
trajectories, and the existing source audit has already produced exact
source-aligned operations. The current full artifacts contain 2,634 reference
sessions / 108,569 operations and 405 source-valid failed target sessions /
20,866 operations across four code-agent frameworks. Every one of the 1,000
official stage annotations covers its declared one-based step interval exactly.
For the target set, official stages remain scorer-only. The recurrence input is
the existing visible `action_kind` sequence, a pre-existing project-derived
deterministic nine-way mapping. CodeTracer's released two-way `phase`
classifier output, `raw_action_key`, and the official `stages` column are
excluded from construction. The Rust adapter contains only unit weight and
`{session, action}`.

The existing reference file contains the 405 targets because the prior RQ2
experiment was transductive. This experiment removes those target IDs before
learning recurrence statistics, leaving 2,229 reference sessions, 87,703
operations, and the same nine visible action kinds. No recurrence formula,
cutoff, cluster rule, input feature, metric, or benchmark variant is selected
from CodeTraceBench stage results.

**Scientific impact and decision.** The experiment is admitted as
**decisive** RQ3 evidence. A positive result would turn the release recurrence
row from same-corpus mechanism development into cross-family evidence on
independently annotated code-agent stages. A contradictory result would bound
this unchanged constructor on code-agent stage structure while leaving the
fixed RQ and thesis intact. This has higher paper value than another OSWorld
tuning round, another action-normalization cell, or a newly collected
benchmark because it directly tests the current release path on complete
existing real data.

The approved proposal is not yet executable: independent plan review must
first verify stage provenance, target/reference disjointness, metric
non-circularity, baseline roles, and the exact no-tuning contract. The plan is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).

### Node E003 — Independent Plan Review

The fresh read-only reviewer used `research-experiment-design` and initially
returned `REVISE` for two bounded defects: the plan conflated the provenance of
project-derived `action_kind` and CodeTracer-derived `phase`, and it incorrectly
classified coverage failure as a scientific mixed result. The root corrected
only those statements and disclosed that the external phase baseline receives
richer raw-action information than recurrence. The single follow-up returned
`APPROVE` with zero remaining blockers. The complete discussion is
[`experiment-001/plan-review.md`](experiment-001/plan-review.md).

### Node E004 — Real Preflight And Independent Implementation Audit

**Question.** Does the approved path execute on one real target without label
leakage, reference overlap, coverage loss, boundary-index error, partition-
metric error, or a hidden algorithm change?

**Inputs and method.** The root implemented one adapter/scorer at
`script/rq3_codetracebench_stage_fidelity_eval.py`. It writes only unit
`value` and `{session, action}` into the release Rust interface, excludes all
405 target IDs from the recurrence reference, waits for Rust predictions
before loading official stages, and emits complete pair and operation rows.
The approved preflight used the lexicographically first complete 47-operation
target and the full disjoint 2,229-session / 87,703-operation reference.

**Results and review.** The path ran to terminal status and conserved all 47
operations. Independent audit recomputed the Rust inputs, zero target/reference
overlap, all 46 boundary positions, all 47 assignments, exact coverage by ten
one-based official stage intervals, all five boundary and B-cubed metrics, and
the static 405-session full input. It found no computational defect. Its one
must-fix was reporting-only: the first preflight report incorrectly interpreted
one diagnostic session as `contradicted`. The root changed preflight to
`tested_hypothesis: not tested`, an execution-only interpretation, a preflight
heading, diagnostic-metric wording, and `full_population_scored: false`; it did
not change the algorithm, scorer, plan, or numbers. The regenerated preflight
passed bounded follow-up review with zero remaining must-fix findings.

**Scientific impact and decision.** REAL PREFLIGHT passes and establishes only
executability. It does not answer RQ3 or authorize any paper change. Raw
artifacts are under
`.agentsight/experiments/rq3-recurrence-codetracebench-v1/preflight/`.

### Node E005 — Complete Existing-Trajectory Run

**Question.** Does the unchanged recurrence constructor exceed every approved
alternative on both official-stage boundary F1 and operation-weighted B-cubed
partition F1 over the complete existing target population?

**Inputs and method.** At 2026-07-15T02:51:00-07:00 the root ran the approved
full command once, without changing the recurrence formula, cutoff, input,
population, baselines, or scorer after preflight. The run used all 405 existing
failed trajectories, 20,866 operations, 20,461 adjacent pairs, 2,948 complete
official stage intervals, and four frameworks.

**Raw result.** Every validity and conservation check passed. Recurrence reaches
boundary precision 0.161640, recall 0.792371, and F1 0.268506, narrowly above
action-change F1 0.267524. Its B-cubed F1 is 0.475008, below the richer external
phase-change baseline at 0.654445. Under the approved two-metric rule the raw
result is `mixed`. Recurrence differs from action-change on only 70 of 20,461
pairs, all `install -> other`; it is identical to action-change on the other
20,391 pairs and introduces no extra split for same-action pairs. This exposes
a specific calibration failure: occurrence-weighted two-means is dominated by
high-NPMI self-transitions and therefore treats almost every action change as a
boundary.

**Current decision.** The complete run is terminal, but independent raw-result
review is required before transition. Complete commands and raw paths are recorded in
[`experiment-001/full-run.md`](experiment-001/full-run.md).

### Node E006 — Independent Full-Result Review And EXPERIMENT Handoff

**Question.** Do the raw rows support the declared mixed verdict and the
mechanism diagnosis strongly enough to select the next action without changing
the paper-level scientific contract?

**Inputs and method.** A fresh read-only reviewer used the
`research-experiment-design` result-review standard and independently rebuilt
the population, reference exclusion, NPMI/cutoff, Rust boundary and motif
decisions, official stage coverage, pooled metrics, B-cubed assignments, and
framework comparison from the raw artifacts. It received no desired numerical
verdict.

**Results.** Review returns PASS with no must-fix or optional validity issue.
It exactly reproduces boundary F1 0.2685055633 and B-cubed F1 0.4750077514,
confirms the approved `MIXED` result, and verifies that 20,391/20,461 decisions
(99.6579%) equal action-change. OpenHands, SWE-agent, and mini-SWE-agent are
identical to action-change on every pair; Terminus2 contains all 70 differences.
The complete review is
[`experiment-001/result-review.md`](experiment-001/result-review.md).

**Scientific impact and decision.** The unchanged recurrence is not accepted
as positive cross-family confirmation. The result is accepted as decisive
mechanism-selection evidence: the current occurrence-weighted cutoff is
dominated by self-transitions and does not learn useful cross-action continuity
on this family. RQ3, its positive hypothesis, the thesis, four-RQ structure,
and original story remain fixed. The paper is not asked to headline this mixed
development result.

**Tree/search update and handoff.** EXPERIMENT closes. It rejects a new
benchmark, score sweep, cutoff sweep, richer feature bundle, and claim rewrite.
It motivates one minimal sibling mechanism for the next outer cycle: preserve
the same NPMI recurrence and zero-parameter two-means, treat identical actions
as continuous by identity, and calibrate the recurrence cutoff only across
actual action changes. That candidate must reuse the complete existing
OSWorld-Human and CodeTraceBench trajectories, run once without a sweep, and be
reported as post-hoc mechanism development on both observed populations.
WRITE receives only the reviewed evidence and canonical-memory update; no
paper claim or prose change is supported by this experiment.

## Ranked Open Objections

1. The release recurrence still lacks positive untouched cross-family
   confirmation; the complete CodeTraceBench run instead exposes action-change
   degeneration.
2. Even a positive future stage-partition result would not validate literal stage names
   or every action/task component of the broader fixed RQ3 hypothesis.
3. The AAAI reproducibility checklist remains a separate submission task and
   does not affect this experiment's scientific validity.

## WRITE Gate

### Node W001 — Evidence Disposition And Targeted Paper Verification

**Question and entry.** Does the reviewed mixed CodeTraceBench result require a
reader-facing paper edit, and can canonical evidence be synchronized without
allowing a mechanism failure to rewrite the fixed thesis, RQs, or positive
hypothesis? WRITE entered from E006 with no accepted idea-level change and no
permission to run `iter-refine-ideas` in BUILD_AND_EVALUATE.

**Inputs and method.** The root reread `docs/user-instruction.md`, confirmed
`docs/questions-for-author.md` has no blocking question, read the current
canonical RQ3 frontier and complete current `docs/paper/main.tex`, and compared
the paper's abstract, introduction, four explicit RQs, RQ3 method/result,
limitations, and conclusion with the reviewed raw result. The target was a
paper decision, not prose activity. No writing subskill was asked to make a
scientific decision.

**Result and paper decision.** The paper already labels recurrence as
OSWorld-Human development evidence, reports the supervised held-out comparator
and task-partition evidence separately, and states that phase/action components
need matched annotations and pre-specified mappings. It makes no CodeTraceBench
generalization claim. Adding a mixed post-hoc constructor diagnostic would not
strengthen the reader-facing case and would confuse development history with
the strongest supported answer. Therefore no paper section is changed in this
gate. The exact thesis remains present in abstract, introduction, and
conclusion; the four explicit RQs remain attribution, localization, tag
accuracy, and cost.

**Canonical update and verification.** `docs/evaluation.md` now records the
complete Step 0021 population, metrics, independent verdict, degeneration
diagnosis, rejected alternatives, and the one-candidate existing-trajectory
next step. `docs/idea-story.md`, `docs/design.md`, and
`docs/implementation.md` remain unchanged because this step accepted no story,
design, or implementation change. `docs/paper/` has no diff. The authoritative
`docs/agentpprof-paper` submodule remains clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

**Transition.** WRITE passes as an explicit no-paper-change disposition and
hands the complete EXPERIMENT/WRITE record to REVIEW. REVIEW must verify that
the mixed result is neither hidden behind a new generalization claim nor used
to shrink the ambitious fixed RQ, and that the selected minimal calibration
repair is simpler and more informative than a new benchmark or score sweep.

## REVIEW Gate

### Node R001 — Independent Outer Audit And Meta-Review

**Question and entry.** Did EXPERIMENT and WRITE solve the intended question
with complete external evidence, preserve the ambitious fixed contract, and
select the simplest high-value next action without turning a mixed mechanism
result into a new benchmark, sweep, claim retreat, or story rewrite?

**Inputs and method.** One fresh reviewer with no Step 0021 planning,
implementation, execution, result-review, or writing role applied the
`auto-research-orchestrator` outer-audit and meta-review requirements. It read
the complete step and child reports, canonical RQ3 frontier, paper contract,
current user instructions, and direct preflight/full artifacts. Prior verdicts,
expected answers, and the proposed repair were disclosed but treated only as
claims to verify.

**Result.** The audit returns PASS with zero must-fix findings. It independently
reproduces the complete population and primary metrics, verifies preflight is
execution-only, confirms zero reference/target overlap and minimal Rust input,
and recomputes the 99.6579% action-change equality. It additionally verifies
that 38,171/38,478 high-cluster reference occurrences (99.202%) are
self-transitions and that `install -> other` is the only high-cluster
cross-action transition. The complete audit is
[`outer-audit-20260715T031146-0700.md`](outer-audit-20260715T031146-0700.md).

**Direction.** PASS. The thesis and exact four RQs remain ambitious and
unchanged. A real complete official benchmark exposes a simple mechanism-level
failure; no toy, proxy, jargon layer, or post-hoc claim replacement is used.

**Method and evidence.** PASS. The next action is the one minimal candidate
directly predicted by the failure: keep same-action identity continuous and
calibrate the same zero-parameter recurrence only among actual action changes.
It must rerun the already-complete OSWorld-Human and CodeTraceBench populations
once, with no feature, cutoff, score, or benchmark sweep, and call both results
post-hoc development evidence.

**Writing and contract.** PASS. The paper correctly remains unchanged and does
not claim CodeTraceBench generalization. `docs/evaluation.md` holds the full
mixed result. Thesis, RQs, hypothesis, story, paper, idea story, design,
implementation, and authoritative submodule do not drift.

**Maintenance.** No AGENTS rule, repo-local skill, or shared-skill change is
warranted. The lesson is research-specific and already lives in the evaluation
frontier; design and implementation stay unchanged until the repair is tested
and accepted.

### REVIEW Completion And Next-Step Handoff

Step 0021 closes with EXPERIMENT, WRITE, and REVIEW complete. It adds no
reader-facing claim, but it converts a vague cross-family risk into a precise,
independently verified cutoff-calibration defect. The next outer cycle remains
BUILD_AND_EVALUATE/RQ3 and may execute exactly one mechanism candidate over
existing trajectories. Step completion requires the root's final static checks,
one coherent commit, and a normal best-effort push; Git outcome is publication
bookkeeping and does not alter the scientific PASS.
