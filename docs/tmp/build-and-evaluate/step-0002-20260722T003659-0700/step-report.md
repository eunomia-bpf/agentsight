# BUILD_AND_EVALUATE Step 0002 — RQ1

**Started:** 2026-07-22T00:36:59-07:00  
**Parent:** BOOTSTRAP step 0001, Node B32  
**Active question:** RQ1 only — how much long-running Agent activity becomes
artifact change that persists, is later reused, and is followed by successful
validation?

## EXPERIMENT_GATE

### Node E1 — RQ1 plan drafted for independent review

**Context.** 2026-07-22T00:36:59-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: in review.

**Question.** Turn the frozen RQ1 contract into one real, source-linked,
six-project run that can produce paper Figures F3 and F4 without interpreting
RQ2--RQ7 or inventing data.

**Inputs and method.** The root reread the current user instructions, empirical
contract, design and implementation frontiers, paper RQ1, existing
`agent-session` types, and `agentvis::RepositoryTrace`. It wrote
`experiment-rq1-20260722T003659-0700/plan.md`. The plan adds only the missing
source-native command effect and an RQ1 research exporter; it does not add a
frontend, server, database, semantic labeler, fixed event window, or another
general event IR.

**Next gate.** A fresh reviewer must attack construct validity, source
qualification, censoring, lineage, final-state interpretation, plot semantics,
and executable stop conditions before code or a real run is admitted.

### Node E2 — Plan review round 1

**Context.** 2026-07-22T00:45:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E1; status: BLOCK.

**Independent result.** The read-only reviewer accepted the minimal architecture
but blocked implementation on five issues recorded verbatim in
`experiment-rq1-20260722T003659-0700/plan-review-1.md`: path existence cannot
stand for write durability; worktree identity is required; validation coverage
is adapter-derived; delete/supersede are competing outcomes; and longitudinal
case qualification needs explicit session/mutation/coverage gates.

**Root decision.** Accept every blocker. The qualifying product scan also found
that AgentSight, ActPlane, bpf-developer-tutorial, and eunomia.dev have multiple
worktrees, so this is not a hypothetical threat. The plan must be revised and
receive a follow-up PASS before implementation.

### Node E3 — Plan review round 2

**Context.** 2026-07-22T00:55:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E2; status: BLOCK with one remaining repair.

**Independent result.** The reviewer accepted the five Round-1 repairs but
found that rename to an unoccupied destination was still entering the
introduced-artifact denominator. `plan-review-2.md` records the exact defect.

**Root decision.** Accept and repair. Artifact introduction now requires an
identity born from confirmed-success create; rename inherits source birth
state, and unknown rename lineage is excluded. The plan and canonical docs are
aligned and return for a final follow-up review before implementation.

### Node E4 — Experiment plan admitted

**Context.** 2026-07-22T00:57:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E3; status: PASS.

**Independent result and decision.** The final read-only follow-up review in
`plan-review-3.md` found no remaining scientific or executable blocker. The RQ1
plan is admitted. Implementation must remain inside its thin-projection and
plain-row scope, then pass unit tests and the AgentSight real preflight before
the fixed six-project run.

### Node E5 — Thin implementation and real AgentSight preflight

**Context.** 2026-07-22T01:00:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E4; status: complete.

**Implementation.** `RepositoryEvent` now retains the adapter-derived command
effect and optional hashed Tool-worktree ID. `FileAction` retains destination
and previous worktree IDs, and Tool-level workdir precedes session cwd. The
trace reports candidate/parsed/included sessions by vendor. The research-only
`research-rq1` entrypoint derives source-linked artifact/mutation/summary rows;
`agentvis/research/plot_rq1.py` renders only frozen CSVs. No frontend, database,
semantic labeler, or second general event IR was added.

**Verification.** All 11 `agent-session` tests and 35 `agentvis` tests pass;
collector type-checks; the Python plotter compiles and its Aalen--Johansen
synthetic self-check passes. Tests cover Tool workdir, worktree separation,
delete--recreate, left-censored rename versus confirmed create, and validation
before supersession. Existing parser tests cover vendor status outcomes.

**Preflight and repair.** The final AgentSight preflight used cutoff
`1784707912312`, admitted 1,362 sessions, attributed 1,138 sessions and
96,604/126,410 Tool actions to three worktrees, and emitted 4,254 artifacts and
6,472 confirmed mutations in 23.83 seconds. Every mutation source ID resolved,
CSV summaries recomputed exactly, and both figures rendered. Earlier preflight
iterations exposed and repaired two validity defects before admission: a test
could otherwise associate across worktrees, and remote-matched actions without
a resolvable worktree could otherwise inflate the primary activity axis. The
former is now forbidden; the latter remains explicit source coverage.

### Node E6 — Frozen six-project RQ1 run and F3/F4

**Context.** 2026-07-22T01:15:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E5; status: complete, pending independent result review.

**Execution.** The authoritative command in
`experiment-rq1-20260722T003659-0700/commands.log` applied the same cutoff to
all six fixed projects. A first attempt stopped without interpretation when
ActPlane's Git metadata named a missing worktree. The repair represents final
state as known/unknown instead of converting query failure to absence; the
entire run then restarted. A later otherwise-successful run was also discarded
without interpretation because it reused the preflight cutoff while querying
final state minutes later. The authoritative run froze a fresh cutoff of
`1784708569241` immediately before extraction, took 39.69 seconds, peaked at
762,708 KiB RSS, and emitted 7,154 artifacts and 13,152 confirmed mutations.

**Reconciliation and coverage.** All six projects satisfy the longitudinal
gate. Only AgentSight, ActPlane, and eunomia.dev have an eligible confirmed
create, and only those same three expose an adapter-recognized successful
validation in a retained worktree. The preregistered four-case threshold
therefore stops cross-case persistence and validation interpretation; those
panels are coverage-only. Reuse is measurable in all six cases. Its observed
proportions range from 89.80% to 97.26%; worktree-attributed action volume and
reuse proportion have descriptive Spearman rho 0.0857. This is a descriptive
six-case contrast, not a population or causal result.

**Figures and evidence.** F3 shows persistence coverage and competing-risk
reuse/validation curves with risk tables. F4 shows exact project
numerator/denominator labels, stops correlation in the two three-case panels,
and reports rho only for six-case reuse. Both PDF and PNG forms were visually
inspected. The full event JSONs remain locally available and are committed as
gzip-compressed source rows; uncompressed 113 MiB copies are ignored. CSVs,
coverage JSON, hashes, commands, figures, and `result.md` are under
`experiment-rq1-20260722T003659-0700/full-six-projects/`.

**Next gate.** A fresh reviewer must recompute selected rows, inspect the
competing-risk implementation and figures, verify the stopping decisions, and
return PASS/BLOCK before any RQ1 statement enters the paper.

### Node E7 — Independent RQ1 result review and paper figures

**Context.** 2026-07-22T01:38:00-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
parent E6; status: complete.

**Independent review.** A fresh reviewer independently reconciled all 206,249
Tool events, 7,154 artifacts and 13,152 mutation rows; verified frozen hashes,
cutoff, worktree attribution, create/rename/delete identity, unknown final
state, validation-before-supersession and Aalen--Johansen derivation; and
regenerated F3/F4 to byte-identical PNGs. The review returns PASS in
`experiment-rq1-20260722T003659-0700/result-review-final.md`.

**Scientific disposition.** All six cases pass the longitudinal gate. Reuse is
measurable in 6/6, with descriptive action-volume Spearman rho 0.085714.
Persistence and recognized validation remain coverage-only at 3/6, so the
preregistered cross-case stop is retained in text and figures. No population,
causal, content-durability or validation-coverage claim is made.

**Paper integration.** Reviewed vector F3/F4 copies are under
`docs/paper/figures/`, cited with construct-qualified captions, and compile in
the six-page AAAI draft without overfull boxes or undefined references. The
paper now reports exact corpus coverage and RQ1 results; RQ2--RQ7 remain open.

### Node E8 — RQ2 recognized-validation dynamics and F5

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after three plan reviews and two result reviews.

**Execution and repair.** The approved analysis projects recognized validation
onto its command worktree and each confirmed mutation onto its affected
FileAction worktree. The first result was rejected because 4,099 cross-worktree
mutations were omitted; the repaired run reconciles all 13,152 mutation rows.
F5 follows every worktree lane in Agent action order and summarizes complete
inter-success mutation intervals.

**Scientific disposition.** Only 3/6 projects expose recognized successful
validation, so the four-project cross-case gate stops. Within covered lanes,
60.0--89.1% of complete intervals contain no confirmed mutation and rare
intervals contain up to 1,144 mutations. This is cadence/adapter evidence, not
proof of redundant validation or coverage. Independent Round-2 result review
returns PASS.

### Node E9 — RQ3 repeated-mutation structure and F6

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after independent plan and result repair/review.

**Execution and repair.** RQ3 collapses same-action multi-path mutations into
13,150 artifact mutation episodes from 13,152 source rows. A first result review
rejected within-action ordering and an inexact top-10% statistic. F6 now updates
episodes atomically per Tool action and evaluates concentration at the exact
fractional 10% identity boundary.

**Scientific disposition.** Repeat-observed episodes comprise 71.8--91.8% of
observed mutation episodes; the exact top-10% identity share ranges from
41.9--86.7%. Independent Round-2 review returns PASS for this descriptive
mutation-concentration facet only, not convergence, thrashing, defect repair,
or waste.

### Node E10 — RQ4 source-session component continuity and F7

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after two plan and two result reviews.

**Execution and repair.** Because native sources do not provide portable
parent/child roles and sessions overlap, the approved estimator compares
adjacent non-overlapping transitive concurrency components in each worktree
lane. The first result was rejected for lifecycle and prefix-population defects;
the repaired replay matches all 7,154 RQ1 artifact births and 13,152 mutation
identities exactly.

**Scientific disposition.** F7 covers 120 components and 108 boundaries but
fewer than four projects meet every 20-boundary estimator gate. Independent
Round-2 review returns PASS for source-coverage/within-case evidence only; no
reset, resume, memory, comprehension, or forgetting claim is admitted.

### Node E11 — RQ5 workspace activity allocation/migration and F8a/F8b

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after three plan reviews and independent result review.

**Execution.** The approved analysis retains 95,111 path-resolved primary
units, separates `ok` and `observed` status, fractionally weights multi-path
Tool calls, and computes within-worktree same-artifact/same-module/cross-module
transitions plus return gaps. F8 is split into paper-width allocation and
migration figures. Eight CSVs and both PNGs reproduce byte-identically.

**Scientific disposition.** Status sensitivity is material, so no stratum is
silently treated as truth. Five cases meet the return-gap gate; AgentSkill's
three returns remain N/A. Independent review returns PASS only for
path-resolved workspace activity, not duration, internal attention, importance,
productivity, entropy, cooling, or forgetting.

### Node E12 — RQ6 source-signal coverage stop and F9

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after two plan and two result reviews.

**Execution and repair.** The approved audit counts exact `Skill` Tool calls
and exact-basename instruction reads/mutations, yielding 1,762 rows across 1,525
native Tool events. The first result review accepted all data but rejected F9
because absent project/vendor strata looked like observed zeros. The repaired
figure uses an admitted-session availability mask, gray N/A cells, and a
labeled log1p unique-event color scale; a fresh review returns PASS.

**Scientific disposition.** Skill names/arguments, model/config fields,
repository-external instructions, and proof of non-exposure are unavailable.
F9 therefore documents `ASSOCIATION ANALYSIS STOPPED`; it supports no
skill/harness association, benefit, harm, or causal claim.

### Node E13 — RQ7 matched-comparison readiness and F10

**Context.** 2026-07-22T01:30:03-07:00; BUILD_AND_EVALUATE EXPERIMENT_GATE;
status: complete after two plan and two result reviews.

**Execution and repair.** The approved dependency-only audit reads the frozen
RQ1 manifests and checks six source contracts per project before any question,
baseline, or model call. Round 1 blocked the output because the command log was
empty and matrix text was undersized. The repaired run records the full command
and hashes, uses paper-readable labels, and reproduces every CSV and PNG
byte-for-byte. Independent Round-2 review returns PASS.

**Scientific disposition.** F10 finds 12 present, zero partial, and 24 N/A
project--contract cells. Counts satisfies descriptive prerequisites and the
artifact trajectory is coverage-only; Final State, pinned ProcGrep, and bounded
Raw-log LLM remain N/A because native admitted prefixes and cutoff worktree
state were not frozen. The matched comparison therefore stops before the
$30\times4$ template gates. This closes the readiness question only and
provides no accuracy, advantage, evidence, latency, token, cost, or trajectory-
superiority result.
