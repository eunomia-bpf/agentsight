# RQ6/F9 Plan Review — Round 1

**Reviewed:** 2026-07-22  
**Scope:** independent plan review only; no implementation or result review  
**Verdict:** **BLOCK**

## Overall assessment

RQ6 is a useful supporting, hypothesis-generating case analysis, and the plan
correctly forbids causal skill/harness claims, human gold, action-level
p-values, and zero-filling unavailable cells.  A coverage-first F9 is also the
right failure mode.  The current plan is nevertheless not executable as a
valid exposed-versus-unexposed association study.  The frozen RQ1 export does
not contain several fields used to define the proposed exposure; the proposed
exposure kinds do not share one construct; absence of an observed exposure is
not evidence of absence; and the outcome windows, concurrency handling, and
estimands are not frozen.  A forest plot made from this plan could therefore
look quantitative while comparing source visibility, work targets, vendors,
and calendar periods rather than skill/harness-associated process patterns.

## Blocking findings

### 1. The declared exposure is not recoverable from the frozen input

The plan says to reuse only the frozen RQ1 native Tool timeline.  The frozen
`RepositoryEvent` rows retain `tool_name`, `category`, `command_name`, effect,
status, worktree, and resolved file actions, but do **not** retain:

- the full Tool command/input or the argument/name of a `Skill` invocation;
- the session-level model/configuration fields present in `AgentSession`; or
- repository-external skill/config paths discarded by repository projection.

Consequently, the proposed “source-visible name” and native harness/model
setting cannot be reconstructed from the admitted input.  A schema inspection
also shows that some projects have `Skill` Tool rows while others expose only
repository path accesses, so treating all of these as one binary field would
partly measure adapter/source coverage.

**Required repair:** either (a) narrow RQ6 to fields actually frozen in RQ1,
with an explicit coverage-only stop for skill name/model/config, or (b) perform
one minimal, cutoff-preserving re-export through `agent-session` that adds the
exact native fields to `RepositoryEvent`.  Freeze the source-field-to-exposure
mapping and output a source-ID-level exposure ledger.  Do not recover the
fields from prose or an LLM.

### 2. The exposure kinds do not identify one comparable construct

An explicit native Skill invocation, an explicit active harness setting, a
manual read of `AGENTS.md`, a mutation to a repository's `SKILL.md`, and a
model setting are materially different events.  In
`academic-writing-skills`, for example, skill definitions are often the
artifact being developed; reading or editing them does not establish that the
skill governed the session.  Likewise, a Tool read of `AGENTS.md` detects a
visible inspection, while many harnesses load instructions without emitting a
Tool read.  A config mutation is normally an outcome of work, not a baseline
exposure.

Thus “unexposed” currently means only “no qualifying event was observed,” and
can contain sessions that were actually governed by the same instructions.
Pooling the source kinds creates differential exposure misclassification and
reverse causality.

**Required repair:** call the groups `observed-source-event` and
`no-observed-source-event`, never actual exposed/unexposed.  Make explicit
native invocation/configuration the only admissible primary construct if its
recording is complete enough.  Treat instruction-file reads as a separate
event-following analysis and skill/config mutations as work-target outcomes,
not exposure.  Analyze each source kind separately; combine kinds only if a
predeclared construct argument and support audit justify it.  Freeze exact,
case-insensitive path and manifest rules and the allowed status values.  Remove
the undefined “equivalent” and “declared harness configuration” clauses or
enumerate them exhaustively.

### 3. The temporal comparison and eligibility denominator are undefined

For an observed session, the event occurs before the first confirmed mutation,
but the plan then lists session-level outcomes without saying whether
pre-event actions are included.  For a session with no observed event there is
no comparable anchor.  Sessions with no mutation also have no “before first
mutation” boundary and are not assigned an eligibility rule.  This creates
pre-exposure contamination, incomparable follow-up opportunity, and possible
selection on making progress.

Documentation readback is especially horizon-dependent: a file created early
has much more opportunity to be reread than one created near the cutoff.
“Later session” can also be concurrent rather than temporally subsequent.

**Required repair:** define the eligible session population including
zero-mutation sessions, the index event/anchor, the post-index action/time
window, left truncation, terminal right censoring, and the unit-specific
denominator for every outcome.  Either match no-observed sessions to a
source-independent anchor (for example, the same action ordinal under a frozen
within-project/vendor/time rule) or avoid an anchored between-group claim and
report event-following trajectories only.  Treat documentation readback as a
time-to-reuse/competing-risk quantity or use a predeclared common opportunity
window; do not compare raw eventual ratios under unequal horizons.

### 4. Parallel work and repeated sessions invalidate the stated bootstrap

The corpus contains parallel sessions and multiple sessions acting on the same
worktree.  A later read, validation, or mutation can be produced by another
concurrent session.  Session-level bootstrap therefore does not supply valid
uncertainty when sessions share work episodes and artifacts.  Merely comparing
within project also leaves vendor, model, task family, worktree, and calendar
era structurally coupled to whether an exposure source is visible.  The
current phrase “structurally separated by project or time” is not an
operational overlap check.

**Required repair:** assign events through worktree-local action time, use the
reviewed concurrency-component rule (or exclude overlapping components), and
block uncertainty at the independent work-episode/concurrency-component level
rather than raw session level.  Predeclare support tables and overlap gates by
project, vendor, worktree/time epoch, and model where source-visible.  If both
groups do not coexist within those strata, report descriptive coverage only.
Do not use bootstrap intervals as a substitute for confound control.

### 5. Outcome definitions are not yet recomputable

Several outputs are names rather than frozen estimands:

- “artifact-type allocation” has no action/call weighting rule for multi-path
  Tool calls and no `unknown` handling;
- “validation-attempt rate per attributed action” does not specify whether the
  denominator is all home-worktree actions, only file-directed actions, or only
  `status == ok`; recognized validation often has no file path;
- “observed rework proportion” and “cross-session rework” do not identify the
  exact reviewed RQ3/RQ4 numerator, denominator, or competing outcomes;
- “documentation artifact” and create/write eligibility are not tied to the
  frozen RQ5 classifier and lineage rules;
- “test-only concentration” alternates between “confined to” and a continuous
  share, with no rule for zero-file sessions or mixed-path calls; and
- the canonical RQ/paper mentions survival, but the plan neither defines it nor
  explicitly removes it for insufficient source coverage.

**Required repair:** give each metric one formula, unit, status policy,
unknown/N/A policy, multi-artifact weighting rule, and horizon.  Reuse only
RQ3/RQ4/RQ5 definitions that have passed their own review.  State explicitly
whether persistence/survival is omitted because RQ1 coverage is only 3/6.
Keep outcome families primary/secondary rather than interpreting a large menu
of exploratory contrasts as one result.

### 6. F9 currently overstates what the design can support

A conventional forest plot labeled as exposed-minus-unexposed “effects” would
visually imply comparable treatments and a meta-analytic estimand, neither of
which exists here.  The four outcomes have different units and eligibility
sets.  The cross-project gate (10 sessions/group) can pass while every metric
cell is suppressed by the separate 20/group gate.  Bootstrap method,
replicate count, seed, interval type, and project summary rule are absent.

**Required repair:** make Panel A the unconditional primary result: source
coverage by project, vendor, source kind, status, and calendar interval.  Draw
Panel B only for separately defined source kinds and call values
`within-stratum descriptive contrasts`, not effects.  Facet metrics with their
own units and raw denominators; do not pool them on one common scale or compute
a global association.  Use one coherent preregistered estimability gate and
freeze the component-block bootstrap algorithm, seed, and repetitions.  If
the gate fails, F9 must contain only coverage and an explicit stop reason.

### 7. The experiment lacks the required execution and decision contract

There is no runnable command, script/version, raw-output layout, input hashes,
completion/reconciliation checks, resource bound, or explicit expected,
contradictory, mixed, and inconclusive interpretation.  The plan also does not
state whether RQ6 is supporting evidence or only a dependency/coverage audit.

**Required repair:** add one real command and ordinary outputs, minimally:

```text
raw/rq6-source-coverage.csv
raw/rq6-observed-events.csv
raw/rq6-session-or-component-outcomes.csv
raw/rq6-contrasts.csv          # only if gates pass
figures/rq6-configuration-association.{pdf,png}
result.md
commands.log
```

Reconcile every RQ1 event/session to included, excluded, unknown, or N/A;
verify each reported exposure row against a native source ID; verify that F9
reads only frozen CSVs; and define completion as either a reviewed coverage
stop or a reviewed admitted contrast run.  State in advance what positive,
contradictory, heterogeneous, and coverage-inconclusive outcomes change in the
paper.  No human or LLM gold is needed for any of these source-verifiable
checks.

## Baseline and paper-value judgment

No external algorithmic baseline is required for this descriptive RQ.  The
relevant comparison is the carefully qualified source-event group versus a
supported no-observed-event group, with source-kind and confound controls.
Adding weak trajectory baselines would not repair the exposure problem.

The experiment is admissible only as **supporting observational evidence** or
as a **coverage stop**.  It cannot support harness effectiveness, waste,
causality, or population prevalence.  A positive result would identify a
source-visible case association worth controlled follow-up; a heterogeneous
result would bound that association to particular projects/source kinds; a
null result with adequate support would show no detectable descriptive
contrast under the frozen metrics; insufficient or separated support would be
an informative coverage-only result and should suppress the forest panel.

## Conditions for Round 2 PASS

Round 2 can pass without widening the corpus if the revised plan:

1. uses only recoverable fields or declares a minimal cutoff-preserving native
   re-export;
2. separates actual native invocation/config fields from instruction reads and
   work-target mutations;
3. defines comparable anchors, horizons, eligibility, concurrency, and every
   metric denominator;
4. operationalizes confound/support checks and coherent coverage stops;
5. downgrades F9 to coverage plus separately faceted descriptive contrasts;
6. freezes command, outputs, checks, uncertainty, and result decisions; and
7. keeps all claims source-verifiable, observational, and free of human gold.

