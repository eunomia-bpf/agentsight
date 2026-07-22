# RQ3 Experiment Plan — Rework Structure over Artifact Evolution

**Created:** 2026-07-22T01:30:03-07:00  
**State:** preregistration draft; no RQ3 statistic has been computed

## 1. Question and boundary

RQ3 asks how repeated mutation is distributed across artifacts and how the mix
of first-observed versus repeat-observed mutation changes over an Agent action sequence.
It does not label any fixed mutation count as “thrashing,” infer defect repair
or intent, or equate repeated work with waste. Rework here is an observable
operation shorthand for repeat-observed mutation episodes; it never implies
waste, failure, or intent. This experiment answers the mutation-concentration
facet of RQ3 only; validation-followed revision and module switching require
their own source-qualified analyses.

## 2. Frozen source and deterministic units

Reuse only the authoritative RQ1 artifact/mutation CSVs and their source event
JSONs under
`experiment-rq1-20260722T003659-0700/full-six-projects/raw/`, frozen at cutoff
`1784708569241`. Preserve `(project, worktree_id, artifact_id)` identity,
delete--recreate splits, and explicit rename lineage exactly as exported.

- **Mutation episode:** all confirmed mutation rows sharing
  `(project, worktree_id, artifact_id, event_id)`. Compound operations remain
  multi-labels inside one episode and never create zero-distance repetition.
- **First-observed mutation:** the first mutation episode of an observed
  identity. It is an observation-window boundary, not workspace expansion.
- **Repeat-observed mutation:** every later episode of that same identity,
  including later-session repetition.
- **Mutation load:** episode count per observed artifact identity.
- **Inter-episode distance:** native Tool-action `event_index`, wall time, and
  session-ID difference between consecutive episodes of the same identity.
- **Cross-session repetition:** a repeat episode whose preceding episode has a
  different native session ID. Parallel sessions may interleave, so this is not
  interpreted as forgetting or reset cost.

Left-censored existing artifacts remain eligible for observed rework because
the definition concerns repetition inside the observation window; they are
reported separately from observation-born artifacts. Status-unknown or failed
effects do not become confirmed mutations.

The primary denominator is all 7,154 observed artifact identities, including
the point mass at zero mutation episodes. A labeled sensitivity CCDF conditions
on the 2,219 identities with at least one episode. Birth-state strata retain
all frozen categories: `confirmed_create`, `left_censored_existing`,
`unknown_create_status`, and `unknown_rename_source`; none silently disappears.

## 3. Figure F6

Generate PDF and PNG from frozen RQ3 CSVs:

1. **Mutation-load distribution:** project-level mass at zero across all
   observed identities plus a complementary cumulative distribution of episode
   count conditional on at least one episode. Exact all/mutated identity,
   episode and raw-row denominators are printed; birth-state strata are a
   labeled sensitivity where denominators permit.
2. **Concentration curve:** cumulative share of mutations accounted for by the
   most-mutated artifact identities, one curve per project. This exposes whether
   work concentrates without choosing a hotspot threshold.
3. **Evolution curve:** as episodes arrive at their frozen native Tool-action
   `event_index`, plot the cumulative fraction classified as repeat-observed;
   annotate cross-session share and rename/delete multi-label composition among
   repeat episodes. Wall time is a secondary annotation. This is an exact
   action-prefix statistic, not mutation ordinal, a rolling window, or a
   smoothed trend.

The figure may support descriptions such as right-skew, a long observed upper
tail, concentration, or a changing first/repeat-observed mix. It cannot claim a
heavy-tailed distribution class, convergence, thrashing, defect repair, or
waste.

## 4. Verification and stop rules

- Reconcile both raw mutation-row totals and collapsed episode totals exactly
  with RQ1, and resolve sampled episode `event_id`s to the frozen event JSON.
- Check identity lineage, delete--recreate, and cross-session classification on
  unit fixtures and sampled source-linked rows.
- Every project needs at least 20 mutation episodes and 10 mutated artifact
  identities for a conditional project curve; otherwise it remains
  coverage-only while retaining its all-artifact zero mass.
- Cross-case statements require at least four eligible projects and must remain
  descriptive case comparisons.
- No thresholded “hotspot,” pooled action-level confidence interval,
  unregistered smoothing, heavy-tail fit, or convergence inference is allowed.
- Completion requires all three panels, exact per-project denominators and
  exclusions, and explicit coverage-only treatment for ineligible projects.

A fresh plan review is required before implementation, followed by an
independent result and figure review before paper inclusion.
