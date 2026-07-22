# RQ4 Plan Review — Round 1

**Reviewer:** independent plan reviewer `/root/rq4_plan_review`  
**Reviewed:** `plan.md` as present on 2026-07-22  
**Verdict:** **BLOCK**

The question is worthwhile and the plan correctly keeps Agent action time
separate from Git time, avoids claims about hidden memory, retains long gaps,
and freezes the RQ1 evidence.  Execution is nevertheless blocked because the
current boundary constructor can label concurrent work as a longitudinal
resume, the frozen rows do not yet establish that boundary endpoints are
independent/top-level sessions, and the proposed censoring and overlap
denominators do not identify the quantities named in F7.

## Blocking findings

### 1. Adjacent-by-start pairing does not remove parallel work

Lines 18--24 sort sessions by first action and test only whether the immediately
previous session ends before the next begins.  This is insufficient for nested
or chained intervals.  For example, with `A=[0,100]`, `B=[10,20]`, and
`C=[30,40]`, the rule admits `B -> C` even though `A` is active throughout.
Consequently, an admitted boundary need not be a return to a quiescent
workspace and does not support a session-reset interpretation.

Define intervals independently per worktree using only that worktree's
attributed action stream, then build connected components of overlapping
intervals (same-timestamp endpoints count as overlap).  The plan must choose
one of two estimands before execution:

1. boundaries between concurrency components, where predecessor artifacts and
   modules are the union over the preceding component; or
2. conservative session-to-session boundaries for which both adjacent
   components are singletons.

The first is an *episode* estimand and must not be called the preceding
session.  The second preserves the declared session estimand but will have
lower coverage.  A session that touches multiple worktrees produces correlated
worktree-specific observations; the boundary key and any resampling unit must
state how these are deduplicated or clustered.

### 2. “Native session” is not yet “independent resumed session”

The frozen event `session_id` is a vendor plus source-file stem.  It retains a
source-session identity, but not a portable parent/child or top-level role.
Overlap alone cannot repair this: a child Agent that runs after its parent has
gone idle can appear sequential.  This conflicts with the study contract that
parallel/spawned workers are concurrency rather than longitudinal restarts.

The endpoint eligibility rule therefore needs a source-derived role/parent
field, frozen before analysis, or a conservative `known_top_level` gate with
unknown roles reported and excluded.  Recognizable names such as
`claude:agent-*` may be a useful coverage check but are not a cross-vendor
parent oracle.  If source metadata cannot distinguish independent/top-level
endpoints, the stop rule must forbid “session reset tax” and “resume” claims;
the result may only describe transitions between observed source-session
files.

### 3. Session end is not a justified right-censoring mechanism

Lines 28--30 and Panel A treat a no-mutation session's last action as
right-censoring.  A completed session ending without mutation is a terminal
competing outcome, not independent loss to follow-up; a source file that may
continue after the frozen cutoff is instead cutoff-censored.  Pooling these in
a Kaplan--Meier curve estimates a hypothetical eventual mutation under an
unsupported non-informative-censoring assumption.

Before execution, choose one of these valid presentations:

- report the observed no-mutation fraction and the empirical first-mutation
  action-step distribution conditional on observing a mutation, separately;
- if completed-session status is source-identifiable, use a competing-risk
  curve with `first mutation` and `session ended without mutation`, retaining
  only cutoff-truncated sessions as censored; or
- present a purely descriptive boundary table with no survival extrapolation.

“Kaplan--Meier/ECDF-style” is not a fixed estimator and must be replaced by one
exact method.  Wall time and action steps may both be reported, but one must be
preregistered as primary.

### 4. Artifact/module overlap lacks an unambiguous unit and denominator

Panels B and C currently mix Tool actions, file-action rows, unique artifacts,
and modules.  One Tool action can refer to multiple paths in different
categories; a directory scope is not an artifact; repeated writes can
arbitrarily inflate a mutation-event denominator; and a predecessor with no
resolved artifacts makes a zero overlap uninterpretable rather than evidence
of discontinuity.

Freeze all of the following:

- **Panel B unit:** either Tool events or path-access rows.  If Tool events are
  used, define an exclusive priority such as exact predecessor artifact,
  predecessor module but not artifact, other resolved artifact, then no
  resolved path.  State that a multi-path event takes its highest-priority
  class.  If path-access rows are used, show no-path Tool events separately
  rather than mixing unlike units in one composition.
- **Artifact eligibility:** non-scope file actions only, mapped by deterministic
  replay to the same stable RQ1 identity.  Directory scopes may support module
  access but never artifact overlap.
- **Module:** the first action-time path component within a worktree, with a
  preregistered value for root-level files.  Rename changes the observed module
  but preserves identity only when RQ1's explicit same-worktree rename lineage
  does.
- **Panel C primary denominator:** preferably unique mutated artifact identities
  and unique mutated modules per next session; an event-weighted mutation share
  can be secondary.  A next session without mutation, or a predecessor with an
  empty reference set, is `N/A`, not zero.

Unresolved-path actions can remain in action coverage, as planned, but cannot
enter resolved-access or overlap denominators.

### 5. “Continues or expands” is not a complete first-mutation classification

Lines 35--36 collapse several distinct states.  An identity absent from the
immediate predecessor may have appeared in an earlier session; a left-censored
existing file first seen now is not a newly created artifact; and an unknown
rename source cannot establish either continuity or expansion.

Use at least these source-supported categories: mutated in the immediate
predecessor; observed only in earlier history; first-observed existing/left
censored; confirmed create in the next session; and unknown lineage.  Only an
adapter-recognized successful create on an unoccupied RQ1 identity may be
described as expansion by artifact creation.

### 6. The frozen source is sufficient only after identity replay is specified

The frozen event JSON contains source IDs, event time, source-session IDs,
worktree IDs, effects, status, and path actions.  The mutation CSV supplies
stable identity only for mutation rows.  It does not map pre-mutation reads to
artifact identities.  Exact read/revisit overlap is feasible without rescanning
live sessions only if RQ4 deterministically replays the frozen event actions
through the same RQ1 create/rename/delete identity semantics (or consumes a
frozen per-access identity export).  A path-string join is invalid across
rename/delete/recreate and would violate line 65.

The plan must name this replay, its input hashes, its output rows, and a
reconciliation check against the frozen RQ1 artifact and mutation IDs.  This is
a thin analysis projection, not a reason to add another event IR.

### 7. The plan is not yet executable or reviewable as a fixed experiment

No runnable command, analysis script, raw-output path, expected project matrix,
completion rule, cost bound, or figure-generation path is specified.  Add one
command over the six frozen event files, exact output CSV/JSON paths, row-count
reconciliations, the Python script that reads those outputs to draw F7, and the
terminal condition.  These are ordinary reproducibility details; no new
control schema is needed.

## F7 and stop-rule audit

F7 can validly support one descriptive claim: the observable prefix and
artifact/module continuity at conservatively identified session or episode
boundaries vary across projects.  It cannot support hidden-memory, forgetting,
causal reset-cost, or process-quality claims.

The final figure should use the exact estimator selected above, show eligible
and excluded boundary counts in the caption or a compact coverage strip, use
`N/A` rather than zero for undefined overlap, and draw per-boundary
distributions or uncertainty rather than only project means.  Do not normalize
session progress in F7: that would discard the action-step quantity Panel A is
supposed to measure.  Six project curves plus risk tables and two distribution
panels may be too dense at one-column width; F7 should be a vector two-column
figure, or be split if its printed labels fall below 7 pt.  The plot script must
read result rows rather than contain hand-entered values.

The current `20 boundaries/project` and `4 projects` rules must be applied
separately to each estimand: boundary timing; Panel B resolved composition;
artifact-overlap; and module-overlap.  A project can qualify for timing while
having no predecessor artifact set or no next-session mutation.  Add these
hard stops:

- fewer than four projects meeting a panel's exact eligibility rule => no
  cross-case interpretation for that panel;
- inability to establish independent/top-level boundary endpoints => stop the
  resume/reset interpretation entirely;
- fewer than 20 eligible boundaries in a project => coverage only, as already
  planned; and
- failure to reconcile identity replay and frozen RQ1 rows => no artifact
  overlap result.

As a feasibility diagnostic only, the frozen event files expose why the final
boundary rule matters.  The current adjacent-start rule yields 242, 1103, 27,
37, 14, and 25 nominal non-overlapping adjacent pairs for ActPlane, AgentSight,
AgentSkill, BPF Tutorial, Academic Writing Skills, and eunomia.dev.  Collapsing
all intersecting observed session intervals into concurrency components leaves
only 22, 26, 1, 31, 14, and 11 component boundaries, respectively.  Requiring
singleton components and excluding only recognizable `claude:agent-*`
endpoints leaves 3, 3, 0, 15, 11, and 5.  These are not RQ4 findings and the
name-based filter is not an accepted role oracle; they show that the current
four-project threshold may fail once the construct is repaired.  The stop rule
must be honored rather than weakening the boundary definition.

## Decision

**BLOCK execution.**  Repair the boundary unit and endpoint-role eligibility,
replace ambiguous censoring with a fixed estimand, define exclusive overlap
units/denominators and first-mutation states, specify frozen identity replay and
the runnable artifact path, and make panel-specific stop rules explicit.  No
additional baseline or wider workload is required for this descriptive RQ.
