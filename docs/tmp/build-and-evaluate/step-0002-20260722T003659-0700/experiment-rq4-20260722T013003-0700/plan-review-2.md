# RQ4 Plan Review — Round 2

**Reviewer:** independent plan reviewer `/root/rq4_plan_review`  
**Reviewed:** repaired `plan.md` as present on 2026-07-22  
**Verdict:** **PASS**

The repaired plan resolves the Round-1 validity defects.  It now measures
boundaries between conservatively constructed source-session concurrency
components, not independent context resets; it removes survival extrapolation;
it fixes the artifact/module units and undefined denominators; and it specifies
a frozen, reproducible identity replay and output path.  The resulting study is
a bounded source-session continuity facet.  It cannot close canonical RQ4 or
support “resume/reset tax” claims, and the plan now says so explicitly.

## Round-1 blocker disposition

| Round-1 defect | Round-2 disposition |
|---|---|
| Adjacent-by-start pairing admitted nested parallel sessions | Fixed by per-worktree interval construction and transitive overlap components (lines 23--31). Same-timestamp endpoints are conservatively overlapping. |
| Child/top-level roles absent | Bounded honestly at lines 8--15 and 106--109. The experiment stops all top-level resume, reset, memory, and forgetting interpretations rather than guessing roles. |
| Last action treated as independent right-censoring | Fixed at lines 35--38 and 67--70. The plan reports a terminal observed no-mutation fraction and a conditional first-mutation ECDF with no survival extrapolation. |
| Overlap unit and denominator ambiguous | Fixed at lines 39--47: exclusive Tool-event categories, unique artifact/module denominators, and `N/A` for empty relevant sets. |
| Continue-versus-expand dichotomy incomplete | Fixed by the six exclusive source-supported first-mutation states at lines 48--51. |
| Read identity unavailable from the mutation CSV | Fixed by deterministic replay of frozen actions and reconciliation against RQ1 identity/mutation rows at lines 57--63. |
| No executable path | Fixed by the single command, frozen-hash check, ordinary CSV outputs, plot outputs, reconciliation checks, and unit-test matrix at lines 85--101. |
| One global coverage gate | Fixed by per-estimand 20-boundary/4-project gates and mandatory coverage-only output when a gate fails (lines 102--105). |

## Construct and feasibility judgment

The component boundary is deterministic and conservative: a source session's
first/last worktree-attributed Tool actions define its observed interval, and
the transitive interval-overlap closure removes any unique predecessor claim
inside an overlapping group.  Predecessor artifact/module sets are therefore
correctly unions over the whole preceding component.  Worktree-specific
observations remain linked by native session ID, and the plan makes no
action-level independence claim.

This construct may over-collapse long-idle source sessions, but that affects
coverage rather than producing false sequential boundaries.  The residual
result must be named **component continuity**, as Panel C now is, rather than
session resumption.  Long wall-clock gaps may be described, but not interpreted
as forgetting or waste.

The frozen RQ1 files are sufficient for the declared analysis.  They contain
ordered event IDs, timestamps, source-session IDs, event worktree attribution,
path actions, scopes, explicit rename sources, and mutation rows.  Seeding at
the frozen artifact first event and replaying same-worktree lifecycle effects
can map pre-mutation reads to the existing RQ1 identities without rescanning
live sessions or introducing a new IR.  The required reconciliation and
delete--recreate/unknown-rename tests are adequate correctness checks.

The stop rules will engage.  A direct interval-component feasibility count on
the frozen events gives 22, 26, 1, 31, 14, and 11 total component boundaries
for ActPlane, AgentSight, AgentSkill, BPF Tutorial, Academic Writing Skills, and
eunomia.dev.  Thus at most three projects can reach 20 boundaries even before
conditional-mutation or resolved-denominator eligibility.  No F7 panel can
support the preregistered four-project cross-case interpretation on this frozen
corpus.  This does **not** invalidate execution because the repaired plan
predeclares coverage and within-case rows as the terminal output and explicitly
leaves canonical RQ4 open; it does prohibit later weakening of the gate or
promoting the result into a multi-project reset claim.

## F7 validity

- **Panel A** is valid as two distinct descriptive quantities: the observed
  no-mutation component fraction and, only among mutation-observed components,
  the empirical distribution of exact worktree-attributed action steps to the
  first mutation.  They must not be merged into one survival curve.
- **Panel B** must implement the five authoritative categories in lines 39--43.
  The four-item shorthand at lines 71--73 omits “other resolved directory
  scope”; the rendered legend should either show all five categories or state
  a preregistered aggregation without relabeling a resolved scope as
  unresolved.  This is a presentation correction, not a change to the fixed
  estimator in Section 2.
- **Panel C** validly uses unique mutated identities and modules, so repeated
  edits do not inflate the primary overlap measure.  Undefined predecessor or
  next-component sets must remain visibly `N/A`.  The six-state first-mutation
  composition should be a separate subpanel or clearly separated inset rather
  than sharing an axis with the overlap distribution.
- The residual permission at lines 79--81 to show normalized session progress
  is unnecessary.  F7 should retain exact component action steps; any normalized
  animation belongs to the product visualization, not this result figure.
- Because the four-project gates are known to fail, F7's caption and paper text
  must call the output coverage/within-case evidence.  Use vector PDF, preserve
  at least 7-pt printed labels, show boundary/undefined counts, and do not crowd
  six nominal project series into a falsely comparative panel.

For the prefix composition, implementation should state explicitly that
“pre-mutation” excludes the Tool event containing the first mutation and that
components without an observed mutation contribute only to the separately
reported no-mutation outcome unless a distinct full-observed-prefix stratum is
predeclared.  Likewise, in a worktree-specific boundary, only path actions whose
`action.worktree_id` matches that worktree may enter its artifact/module
categories; cross-worktree path actions remain coverage.  These are direct
clarifications of the fixed worktree and pre-mutation definitions and should be
checked in result review.

## Decision

**PASS to real preflight and execution under the repaired stop rules.**  No
additional baseline, wider workload, or semantic inference is required.  A
fresh result reviewer must verify exact component construction, identity replay
reconciliation, conditional populations, worktree filtering, `N/A` handling,
and that F7/paper language remains coverage-only where the gates fail.
