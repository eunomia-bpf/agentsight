# Step 0029 — Multi-Step Recurrence On Existing Trajectories

**Started:** 2026-07-15T08:30:07-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gates:** EXPERIMENT → WRITE → REVIEW
**Parent:** Step 0028 REVIEW return edge
**Completed:** 2026-07-15T15:59:51-07:00
**Status:** Completed; EXPERIMENT VALID / COMPLETE / CONTRADICTED, Step 0024
restored, WRITE no paper change, REVIEW closed with no automatic algorithm retry

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The original AgentProf story, operations and operation stacks as
the only core abstractions, and exactly four RQs remain fixed. This step is
assigned the paper question verbatim:

> **RQ3: How accurate are the tags?**

The tested hypothesis concerns one target-blind operation-group constructor
inside RQ3. It cannot change, narrow, split, or answer all of RQ3. It cannot
change the thesis, contribution, story, or the attribution/localization/tag/
cost organization. The authoritative `docs/agentpprof-paper` submodule,
current skills, KVM material, current branch, and paper story are out of scope.

## EXPERIMENT Gate

**Entered:** 2026-07-15T08:30:07-07:00
**Parent:** Step 0028 REVIEW return edge
**Status:** Completed; independent follow-up APPROVE, zero must-fix

At gate entry the root reread the complete `docs/user-instruction.md` and
`docs/questions-for-author.md`. The latter had no open questions. The former
required the exact original story and four RQs, no submodule or current-skill
edits, complete real experiments, reuse of prior trajectories, minimal
complexity, and direct improvement of the existing algorithm rather than a new
dataset. The selected loop therefore reused the two complete populations,
tested one constructor inside verbatim RQ3, prohibited story/RQ changes and a
second candidate, and continued without waiting for author judgment.

### Node E001 — Paper-Value Admission And Source Screen

**Started:** 2026-07-15T08:30:07-07:00
**Completed:** 2026-07-15T08:33:56-07:00
**Parent:** EXPERIMENT gate entry
**Status:** Completed; one experiment admitted

The user directly prefers improving the current algorithm over already-run
trajectories rather than adding a dataset or new story. Step 0026 closes only
flat action-pair, small-window, margin, support, sign, and cutoff retuning; it
explicitly does not show that every future sequence model is impossible. Step
0028's reference-supervised scalar-cutoff protocol is invalid and permanently
closed, so this step cannot repair or rename it.

Three directions were compared by paper decision value:

1. another scalar/window adjustment is rejected because it repeats the closed
   Steps 0025--0028 branches;
2. a new RQ2 decision or repair study has high eventual value but would not
   answer the user's current request to improve the existing constructor;
3. a published grammar-induction principle can use longer recurring action
   motifs while retaining the exact existing inputs, populations, and metrics.

Direction 3 is admitted. Re-Pair establishes the relevant published principle:
recursively replace repeated adjacent symbols with grammar rules, so higher-
order recurring structure appears without a fixed context window. Step 0029
registers one explicit multi-session, reference-to-target adaptation: distinct-
session support chooses a pair, session boundaries stay hard, and the learned
ordered rules apply unchanged to held-out target sessions. These deviations are
stated as method choices rather than attributed to standard Re-Pair. The
algorithm remains supporting infrastructure for operation-stack construction,
not a new paper abstraction or invented name.

The source-only screen used the established repository loaders and no scoring
labels. OSWorld-Human retains 287 sessions, 3,978 operations, and 3,691 pairs;
its visible action vocabulary contains recurring cross-session sequences
through at least length six. The exact CodeTrace target-disjoint reference
retains 2,229 sessions and 87,703 operations; the target remains 405 sessions
and 20,866 operations. The reference corpus contains 6,416 distinct length-six
action sequences present in at least two sessions. These input statistics show
that a multi-step recurrence mechanism has real source support; they are not a
candidate metric or scientific result.

### Node E002 — Experiment Plan And Independent Review

**Started:** 2026-07-15T08:38:00-07:00
**Parent:** E001 admitted direction
**Completed:** 2026-07-15T08:46:08-07:00
**Status:** Completed; final APPROVE with zero must-fix

The complete one-experiment contract is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md). No
candidate implementation, preflight, target score, paper edit, or canonical
frontier edit is authorized before independent plan approval.

The independent round-1 review in
[`experiment-001/plan-review.md`](experiment-001/plan-review.md) returned
**REVISE** with three must-fix findings while affirming paper-value admission,
the mechanism's distinction from Steps 0025--0028, Step 0024 as the correct
same-information baseline, and the complete two-population matrix. The plan now
accurately specifies the multi-session Re-Pair deviations and total ordering,
registers exact product/evaluator commands plus the minimum truthful grammar
report, and distinguishes execution-time label isolation from post-hoc family
selection after earlier target outcomes. No candidate code or metric was run.

The same independent reviewer then performed the single permitted follow-up
and appended a final **APPROVE** with zero must-fix findings. Implementation may
now begin for exactly the one registered grammar candidate. Candidate metrics,
REAL PREFLIGHT, and FULL execution remain prohibited until a fresh read-only
implementation review passes.

### Node E003 — Product And Evaluator Implementation

**Started:** 2026-07-15T08:46:08-07:00
**Parent:** E002 final APPROVE
**Completed:** 2026-07-15T14:42:00-07:00
**Status:** Completed; focused follow-up APPROVE, zero must-fix

Implementation is limited to the approved Rust induction/report/help path,
focused tests, and three thin evaluators that reuse the established population
loaders and scorers. No target candidate metric may run in this node.

The implementation now keeps the existing `--induce-operation-stack` product
interface while replacing only its constructor internals and truthful report:
ordered cross-session grammar rules replace NPMI/cutoff decisions, each target
rule is applied once in creation order, and the report records ordered rules,
segments, assignment coverage, and mass. Focused Rust and CLI fixtures cover
nested rules, total pair ordering, hidden-label invariance, motif-label
collisions, no-rule inputs, and external-reference transfer. All 53 Rust/CLI
tests pass, as does `cargo clippy --all-targets -- -D warnings`.

The three approved evaluator paths now exist. They import the established
OSWorld population/fold/scorer functions and CodeTrace visible/stage loaders,
implement the registered grammar independently in Python, and require exact
ordered-rule and segment equality with the Rust product before scoring. Python
compilation, all three `--help` paths, a label-free nested-grammar fixture, and
`git diff --check` pass. No OSWorld or CodeTrace candidate metric, REAL
PREFLIGHT, or FULL run has executed. A fresh independent implementation review
is now required before any real-data command.

The fresh review in
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md)
returned **REVISE** with three localized evaluator must-fix findings while
approving the one registered grammar algorithm and product surface. It found
that OSWorld labels were loaded before prediction, one established fold source
and planned comparator rows were copied or missing, retained baseline identity
was under-checked, and the equivalence verifier covered only part of the
registered report. It did not request or authorize an algorithm change, new
trajectory, new parameter, second candidate, cap, RQ change, or story change.

The focused repair now uses Step 0024's identity-checked, persisted label-free
OSWorld operation artifact for candidate construction; imports the established
fold authority; persists Python segments and per-operation assignments before
either scorer loads an oracle; and only then loads the established OSWorld or
CodeTrace scorer data and asserts exact visible-population alignment. It adds
the already planned OSWorld one-session-block and per-fold diagnostics,
CodeTrace per-framework Step 0024 rows, exact retained-control checks, and
schema/mode/policy/population/raw-artifact checks for historical baselines. The
shared verifier now checks objective/order/source/field exclusions, exact
reference and target session counts, rule/depth/group/motif totals, contiguous
per-session coverage, every assignment, and additive mass.

After this repair, all 53 Rust/CLI tests and Clippy still pass; all evaluators
compile and expose their CLI; `git diff --check` passes; and a synthetic nested
case passes exact Rust/Python comparison over the expanded report contract. No
real candidate metric, REAL PREFLIGHT, or FULL run has executed. The repaired
implementation must return to the same reviewer for a focused follow-up before
REAL PREFLIGHT.

### Node E004 — REAL PREFLIGHT

**Started:** 2026-07-15T14:42:00-07:00
**Completed:** 2026-07-15T14:44:00-07:00
**Parent:** E003 final implementation APPROVE
**Status:** Completed; PASS on first attempt for both paths

The detailed dependency-only record is
[`experiment-001/preflight-report.md`](experiment-001/preflight-report.md).
OSWorld fold 0 completed with 45 sessions and 521 operations. CodeTrace
completed the full 2,229-session/87,703-operation reference construction and
the lexicographically first 47-operation target. In both paths Python
predictions were persisted before scorer loading, the Rust product completed,
exact equivalence and mass checks passed, and the emitted verdict remained
`preflight-only; no scientific verdict`. Neither path required the permitted
second attempt. No preflight diagnostic changed the plan or algorithm.

### Node E005 — FULL Execution And Local Interpretation

**Started:** 2026-07-15T14:44:00-07:00
**Completed:** 2026-07-15T14:46:00-07:00
**Parent:** E004 PASS
**Status:** Completed; VALID / COMPLETE / CONTRADICTED

The complete result is
[`experiment-001/experiment-result.md`](experiment-001/experiment-result.md).
All five OSWorld folds and all 405 CodeTrace targets completed on the existing
trajectories. Standalone OSWorld equivalence covered all 287 sessions, 621
rules, 1,492 segments, and 3,978 assignments. CodeTrace covered the complete
2,229-session/87,703-operation reference, 405 targets, 20,866 assignments, and
20,461 decisions. All registered controls, per-fold diagnostics,
per-framework Step 0024 rows, coverage, and mass checks are present.

The grammar candidate's operation-weighted B-cubed F1 is 0.717803 versus Step
0024's 0.786170 on OSWorld, and 0.633931 versus 0.649173 on CodeTrace. The
candidate is therefore lower on both complete populations. Under the fixed
pre-execution rule the tested hypothesis is **CONTRADICTED**. This conclusion
does not change RQ3, the story, thesis, or other claims.

### Node E006 — Independent Result Review And Registered Restoration

**Started:** 2026-07-15T15:26:00-07:00
**Completed:** 2026-07-15T15:54:00-07:00
**Parent:** E005 complete raw result
**Status:** APPROVE; VALID / COMPLETE / CONTRADICTED; Step 0024 restored

A fresh independent reviewer explicitly used `research-experiment-design` and
reconstructed both complete populations from raw artifacts. It recomputed all
candidate, Step 0024, supervised, and four control metrics; replayed all 621
OSWorld and 2,453 CodeTrace grammar rules, total tie order, termination, and
target application; verified prediction-before-oracle timing; and confirmed
byte-identical standalone OSWorld equivalence. The review reports zero
must-fix findings and approves the registered disposition in
[`experiment-001/result-review.md`](experiment-001/result-review.md).

Only the Step 0029 candidate changes in `agentpprof/src/main.rs`,
`agentpprof/src/profile.rs`, and `agentpprof/tests/profile_spec_cli.rs` were
reversed. The three Step 0029 grammar evaluator scripts were removed. Raw
outputs and every Markdown plan, review, preflight, and result record remain.
The restored Step 0024 product passes 42 Rust unit tests, 8 profile CLI tests,
3 trace CLI tests, and `cargo clippy --all-targets -- -D warnings`. There is no
remaining tracked product/test diff.

## WRITE Gate

### Node W001 — No-Paper-Change Disposition

**Started:** exact second unavailable; after E006 completed at 2026-07-15T15:54:00-07:00
**Completed:** before the outer audit started at 2026-07-15T15:56:44-07:00
**Parent:** E006 APPROVE and registered Step 0024 restoration
**Status:** Completed; no reader-facing change

BUILD_AND_EVALUATE permits a targeted implementation or evaluation update, but
the registered candidate was contradicted and removed. The complete internal
record was added to `docs/evaluation.md`; no paper section, figure, result,
abstract, introduction, motivation, contribution, thesis, or RQ was changed.
The Step 0024 constructor and its existing positive paper evidence remain
current.

At WRITE entry the root reread `docs/user-instruction.md` and
`docs/questions-for-author.md`; no author answer or instruction authorized a
story, RQ, claim, or paper rewrite. Full-paper and repository verification found
no diff under `docs/paper/`, no change to the exact thesis or four RQ headings,
no Step 0029 grammar term/result in the reader-facing paper, no submodule pointer
or content change, and no product/test diff after restoration. The internal
`docs/evaluation.md` update is the only canonical scientific record needed.
WRITE exits to REVIEW without invoking a writing or idea skill.

## REVIEW Gate

### Node R001 — Independent Outer Audit And Meta-Review

**Started:** 2026-07-15T15:56:44-07:00
**Completed:** 2026-07-15T15:59:51-07:00
**Parent:** W001 no-paper-change disposition
**Status:** Completed after minimum report repair; scientific PASS

The fresh independent audit in
[`outer-audit-report.md`](outer-audit-report.md) explicitly used
`auto-research-orchestrator`, reconstructed the experiment and restoration,
reran the restored 42 unit, 8 profile CLI, and 3 trace CLI tests plus Clippy,
and verified the paper, submodule, story, and RQ boundaries. Its scientific
verdict is PASS: Step 0029 is valid, complete, and contradicted; Step 0024 is
restored exactly; the paper and scientific contract are unchanged; and no
automatic algorithm retry is authorized.

**Direction.** Accept. The exact thesis, original story, and attribution,
localization, tag-accuracy, and cost RQs remain intact. The contradicted grammar
constructor is an internal mechanism boundary, not a thesis or whole-RQ3
challenge.

**Efficiency.** Accept. The fixed two-population result rule was appropriately
strict; the low-value risk was upstream admission of a high-risk constructor
whose source screen established recurrence but not semantic correspondence.
The plan/implementation reviews found real validity defects, but more than three
thousand lines of child reports and three transient evaluators were expensive
for one short deterministic run. Future work reuses existing loaders/scorers
and keeps only checks that can change validity or a paper decision.

**Maintenance.** Accept and defer non-blocking housekeeping. The long canonical
frontier files can be compacted later only by preserving the Initial Narrative
and linking complete step history. The absent `scripts/check_progress.py` is a
non-gating capability mismatch and is not invented in this step. No
`AGENTS.md`, repo-local skill, design, implementation, paper, or idea-story
change is justified. The skill-level diagnosis is recorded as `observe` or
`propose` only; one parent trajectory does not authorize a global skill edit.

### Ranked Open Paper-Level Objections

1. RQ3 remains partial: current positive evidence covers task partitions and
   operation boundaries, not direct phase/action and literal-name accuracy on
   unseen agents and task families.
2. RQ2's strongest remaining gap is a downstream developer decision or repair
   consequence beyond bounded fixed-reader prioritization.
3. Step 0024 remains post-hoc implementation-selection evidence on reused
   populations; Step 0029 neither upgrades nor weakens that scope.

### Root Response And Route

The root accepts the experimental verdict, exact restoration, no-paper-change
disposition, efficiency diagnosis, and the prohibition on rescuing Step 0029.
It rejects any interpretation that a reviewer may make another constructor the
next task merely by proposing one.

Step 0029 closes. Because the fixed paper still has open evidence gaps, the next
outer selection returns to paper-value admission and compares the actual
paper-level alternatives: direct target-blind phase/action/literal-tag accuracy
under RQ3 versus a genuine downstream decision consequence under RQ2. It must
choose by expected change to the current paper answer, reuse real existing
assets where they answer that question, and run one smallest fair complete
experiment. It must not repair, rename, or retry Step 0029; add another grammar,
cutoff, window, or target-informed anti-overmerge rule; narrow the positive
hypothesis; change the story; or wait for human judgment.

## Publication State

The coherent Step 0029 Markdown record and `docs/evaluation.md` frontier update
were committed on the existing
`research/semantic-flamegraph-artifacts-v2` branch. The normal push attempt did
not update the remote; the branch remains ahead of
`origin/research/semantic-flamegraph-artifacts-v2`. This publication backlog is
decoupled from the scientific verdict and does not reopen or block the step. No
force push, branch creation, or branch switch is authorized.
