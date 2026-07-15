# Step 0028 — Calibrate Existing Recurrence On Existing Trajectories

**Started:** 2026-07-15T07:20:00-07:00
**Completed:** 2026-07-15T08:17:36-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gates:** EXPERIMENT → WRITE → REVIEW
**Parent:** Step 0027 REVIEW return edge
**Status:** Completed; experiment INVALID, hypothesis not tested, no research
progress, no paper impact

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The original AgentProf story and exactly four RQs—attribution,
localization/correspondence, tag accuracy, and cost—remain fixed. The selected
question is verbatim:

> **RQ3: How accurate are the tags?**

This step is supporting group-boundary calibration evidence only. It cannot
answer phase, action, literal-name, or whole-RQ accuracy and cannot change the
hypothesis, contribution, story, or reader-facing thesis. The authoritative
`docs/agentpprof-paper` submodule, current skills, KVM material, and branch are
out of scope.

## EXPERIMENT Gate

**Entered:** 2026-07-15T07:20:00-07:00
**Parent:** Step 0027 REVIEW return edge
**Status:** Completed; child experiment closed INVALID
**Gate-entry alignment:** `docs/user-instruction.md` and
`docs/questions-for-author.md` were read before selection. There were no open
author questions and no permission to wait. The gate retained the exact thesis,
four RQs, original story, existing-trajectory preference, no-skill-change
instruction, branch prohibition, and read-only submodule boundary. Step 0027's
whole-paper review and corrected evidence counts supplied the entry frontier.

### Node E001 — Paper-Value Admission And Proposal

**Started:** 2026-07-15T07:20:00-07:00
**Completed:** 2026-07-15T07:32:17-07:00
**Parent:** EXPERIMENT gate entry
**Status:** Completed; plan APPROVED after two review rounds

**Question.** Can independent reference group boundaries improve the existing
action-transition recurrence algorithm on the same already-run trajectories,
without adding a benchmark, score family, semantic field, context window, or
new constructor?

**Prior evidence.** Step 0024 is the current release: OSWorld-Human B-cubed F1
0.786170 and CodeTraceBench 0.649173. Step 0025's sequence-local suppression is
mixed, and Step 0026 proves that action-pair/window/margin/support/sign/length
rules cannot be selected without acting as target-informed population
selectors. Step 0027's independently audited whole-paper review selects a
different information contract rather than another target-outcome rule:
preserve NPMI and post-cutoff construction, and fit one scalar cutoff using
reference annotations only.

**Exact reused assets.** OSWorld reuses 287 sessions under five existing folds.
CodeTraceBench reuses the exact Step 0024 2,229-session target-disjoint score
reference, filters exactly 483 solved normalized references with 18,152
operations and 2,886 stages for calibration, excludes 112 unavailable
non-target manifest rows, and withholds all labels for the same 405 failed
development targets until after predictions.

**One candidate.** The fitter maximizes operation-weighted B-cubed F1 on
reference group partitions across every distinct scalar decision partition;
an exact tie selects the numerically smallest cutoff. Unseen transitions remain
boundaries. This is the only objective, tie rule, and cutoff. The Step 0024
NPMI table, visible fields, target scoring, segments, motifs, stacks, and
folding do not change.

**Admission.** The proposal is admitted as supporting RQ3 group-boundary
evidence. Positive and contradictory results lead to different paper decisions,
all required real assets already exist, and reuse has higher immediate value
than collecting another benchmark under the user's current instruction. The
complete plan is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).
Independent plan review is required before implementation.

### Node E002 — Implementation And Independent Review

**Started:** exact timestamp unavailable; after E001 approval
**Completed:** 2026-07-15T07:53:55-07:00
**Parent:** E001 approved experiment plan
**Status:** Completed; implementation review APPROVED for REAL PREFLIGHT only

The optional grouped-reference calibration input, one-scalar B-cubed fitter,
focused Rust tests, and independent Python equivalence adapters were
implemented without changing the Step 0024 NPMI score or post-cutoff
construction. Static validation passed: 44 Rust unit tests, 9 profile CLI
tests, 3 standard-trace CLI tests, formatting, Clippy with warnings denied, and
Python parsing.

A fresh reviewer explicitly using `research-experiment-design` returned
**APPROVE** with zero must-fix findings in
[`experiment-001/implementation-review.md`](experiment-001/implementation-review.md).
No candidate metric was run during implementation review.

### Node E003 — Real Preflight And Closure

**Started:** exact timestamp unavailable; after E002 approval
**Closed:** 2026-07-15T07:56:12-07:00
**Parent:** E002 implementation-review return edge
**Status:** INVALID; hypothesis not tested; experiment permanently closed

The approved OSWorld preflight was attempted twice. Both attempts stopped in
the new adapter before NPMI construction, cutoff fitting, product invocation,
prediction persistence, target-label scoring, or candidate metric computation.
The adapter failed to exactly reproduce the established source eligibility
order: apply `group_alignment=exact`, then exclude groups with fewer than two
operations. The exact attempt record and authoritative 287-session / 3,978-
operation / 3,691-pair population reconciliation are in
[`experiment-001/preflight-failures.md`](experiment-001/preflight-failures.md).

The experiment is closed under the skill's two-attempt preflight limit. It has
**no scientific result** and cannot change any paper claim, RQ answer,
hypothesis, thesis, or story. CodeTrace preflight and all full runs were not
started.

### Node E004 — Independent Result Review And Minimum Disposition

**Started:** exact timestamp unavailable; after E003 closure
**Completed:** 2026-07-15T08:04:37-07:00
**Parent:** E003 invalid experiment result
**Status:** PASS; zero must-fix; narrow removal completed and re-audited

A fresh reviewer explicitly using `research-experiment-design` returned
**PASS** with zero must-fix findings in
[`experiment-001/result-review.md`](experiment-001/result-review.md). It
independently verified that both attempts stopped inside `load_visible()` and
that the raw OSWorld root contains only an empty `preflight/` directory while
the CodeTrace and equivalence roots do not exist.

The reviewer required the narrow minimum disposition: preserve this complete
Markdown history and the separate Step 0027 arithmetic correction, but remove
only the unvalidated Step 0028 calibration implementation before commit. That
disposition is complete. The Step 0028 hunks were removed from
`agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, and
`agentpprof/tests/profile_spec_cli.rs`; the three new reference-calibration
evaluator files were removed. Those three tracked files now have zero diff
against the entry `HEAD`, and the restored original suite passes 42 unit, 8
profile CLI, and 3 standard-trace CLI tests. No unrelated file, paper source,
skill, canonical research document, branch, or submodule was changed.

**Final EXPERIMENT-gate state:** child closed invalid, hypothesis not tested,
audit history preserved, candidate code removed, and no reader-facing paper
action authorized.

## WRITE Gate

**Entered:** 2026-07-15T08:14:29-07:00
**Parent:** E004 PASS and completed candidate-code disposition
**Status:** Completed with an explicit no-paper-change disposition

### Node W001 — Gate-Entry Alignment And Write Decision

**Started:** 2026-07-15T08:14:29-07:00
**Completed:** 2026-07-15T08:14:29-07:00
**Parent:** WRITE gate entry
**Status:** Completed; targeted writing prohibited

`docs/user-instruction.md` and `docs/questions-for-author.md` were read again at
WRITE entry. No author question is open. The experiment produced no valid
observation, no fitted cutoff, and no target metric. Its independent result
review explicitly prohibits adding a result, limitation, negative narrative,
claim adjustment, RQ answer, hypothesis change, thesis change, contribution
change, or story change. Consequently no writing or idea-refinement skill was
invoked and no `docs/paper/` source was edited. This is the phase-correct WRITE
action, not a skipped outer gate.

### Node W002 — Paper-State Verification

**Started:** 2026-07-15T08:14:29-07:00
**Completed:** 2026-07-15T08:14:29-07:00
**Parent:** W001 no-change decision
**Status:** PASS

The complete paper remains byte-unmodified in the worktree. Its exact thesis
remains **“Agent observability needs profiling, not only debugging.”** Its four
RQ headings remain attribution, problem correspondence/localization, tag
accuracy, and profiling cost. `docs/idea-story.md`, terminology, contribution
surface, and the read-only `docs/agentpprof-paper` pointer are unchanged. The
WRITE gate therefore returns no reader-facing delta to REVIEW.

## REVIEW Gate

**Premature audit began:** 2026-07-15T08:05:27-07:00, before the WRITE record
was complete
**Formally re-entered:** 2026-07-15T08:14:29-07:00 after W002
**Parent:** WRITE no-change disposition and independent experiment result review
**Status:** Completed; follow-up outer audit PASS with zero must-fix

### Node R001 — Independent Outer Audit And Meta-Review

**Started:** 2026-07-15T08:05:27-07:00
**Completed:** 2026-07-15T08:13:14-07:00
**Parent:** E004 result-review return edge with an incomplete outer gate record
**Status:** REVISE on provenance only; scientific closure PASS

The independent audit is
[`outer-audit-20260715T080527-0700.md`](outer-audit-20260715T080527-0700.md).
It reconstructed both failed attempts and the empty raw-root state, confirmed
that no candidate metric exists, verified the narrow candidate-code removal,
and passed fixed-contract integrity. Its three must-fix findings concern only
the missing WRITE/REVIEW records, per-node provenance, and stale
`docs/evaluation.md` frontier. It explicitly forbids re-entering Step 0028's
EXPERIMENT loop.

**Meta-review — direction.** The selected direction was aligned with the user:
one principled scalar change on real already-run trajectories, without a new
benchmark or story drift. Because preflight was invalid, it produced no
evidence and cannot be called an algorithm improvement. Step 0024 remains the
current constructor on its prior evidence.

**Meta-review — efficiency.** The plan reused the right assets, but the new
adapter duplicated eligibility behavior already implemented by the established
Step 0024 loader. That duplication consumed both preflight attempts before
candidate construction. The lesson is to reuse source-native population
loaders in a future different experiment when possible; it does not authorize
repairing or retagging this closed protocol.

**Meta-review — maintenance.** No product, paper, skill, AGENTS, KVM, branch, or
submodule maintenance is justified. One adapter failure is insufficient
evidence for a skill change. The orchestrator reference names a diagnostic
`scripts/check_progress.py` that is absent here; that capability mismatch is
recorded but is non-blocking and out of Step 0028 scope.

### Node R002 — Root Response And Frontier Repair

**Started:** 2026-07-15T08:14:29-07:00
**Completed:** 2026-07-15T08:14:29-07:00
**Parent:** R001 REVISE
**Status:** Completed; all three must-fix findings addressed

The root agent accepts the audit without experimental action. This report now
contains the missing gate and node provenance. `docs/evaluation.md` now records
Step 0027's supervised-information-contract reopening, Step 0028's two invalid
preflights and empty raw state, the candidate removal, Step 0024's unchanged
authority, and the permanent no-third-attempt boundary.

**Ranked open scientific objections after Step 0028:**

1. RQ3 still lacks direct phase, action, and literal tag-name accuracy evidence
   on unseen agents/task families; Step 0028 adds nothing to that frontier.
2. RQ2 still lacks a clean end-to-end developer decision or repair consequence
   beyond the bounded fixed-reader prioritization result.
3. Whole-paper novelty and positioning must distinguish AgentProf from current
   cross-trace grouping/profiler systems without replacing the original story.

**Exact route.** After a follow-up outer-audit PASS, close Step 0028 with no
research progress and no paper change. Route Step 0029 to
`EXPERIMENT_GATE → research-experiment-design PAPER-VALUE ADMISSION` for a
different experiment selected by paper-level decision value, preferring reuse
of valid existing evidence and real assets. It must not repair, retag, rename,
or rerun the Step 0028 reference-calibration protocol as a third attempt.

### Node R003 — Follow-Up Outer Audit And Transition

**Started:** exact timestamp unavailable; after R002 completion
**Completed:** 2026-07-15T08:17:36-07:00
**Parent:** R002 provenance/frontier repair
**Status:** PASS; zero must-fix; Step 0028 complete

The same independent outer auditor verified all three repairs, including the
honest premature-audit chronology, and appended its final PASS to
[`outer-audit-20260715T080527-0700.md`](outer-audit-20260715T080527-0700.md).
Step 0028 closes with no scientific observation and no reader-facing delta.
The exact next route is Step 0029's admission of a different experiment under
the fixed thesis and four RQs; Step 0028 cannot be repaired, retagged, renamed,
or rerun.

## Publication State

Step 0027 was committed as `7a7849ca`. A normal push again failed with remote
HTTP 500 and disconnect; the remote publication backlog remains decoupled from
scientific state. No force push, branch change, or publication gate is allowed.
