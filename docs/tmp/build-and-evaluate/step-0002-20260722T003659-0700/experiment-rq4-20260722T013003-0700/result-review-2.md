# RQ4 Result Review — Round 2

**Reviewer:** independent result reviewer `/root/rq4_result_review`  
**Reviewed:** repaired `plan.md`, `agentvis/research/plot_rq4.py`,
`commands.log`, all regenerated raw CSV files, `result.md`, F7 PDF/PNG, and
Round-1 blocker disposition  
**Verdict:** **PASS**

All Round-1 validity blockers are resolved.  The regenerated outputs use an
exact RQ1-compatible lifecycle replay, restrict Panel B to components with an
observed mutation, expose estimator coverage on F7, preserve the preregistered
coverage stop, and reproduce byte-for-byte for the CSV/PNG anchors.  F7 is
admissible as **coverage/within-case component-continuity evidence only**.  It
still cannot support a session-reset, resume, memory, comprehension, or
forgetting claim, and it cannot by itself close canonical RQ4.

## Round-1 blocker disposition

| Round-1 blocker | Round-2 disposition |
|---|---|
| Terminal no-mutation components were pooled into “pre-mutation” composition | Fixed. `pre_mutation_events(..., None)` returns an empty population; all no-mutation boundary rows now have `prefix_actions=0`. Panel B contains 6,290 events only from mutation-observed components and is titled “Mutation-observed prefix composition.” |
| Identity replay omitted status-`observed` lifecycle effects | Fixed. Every resolved non-scope action is replayed in event/action order. Same-worktree rename preserves lineage regardless of status, delete closes it, and later access/create creates the next RQ1 identity. |
| Estimator coverage was absent from F7 | Fixed. The embedded coverage strip prints components, boundaries, mutation-observed timing, prefix-action volume, and defined artifact/module overlap counts, followed by the explicit statement that every four-project gate stopped. |
| Frozen synthetic verification matrix was missing | Substantially fixed. The in-command checks now cover transitive overlap, equal endpoints, separate worktree lanes, no-mutation prefix exclusion, multi-path priority, observed rename, delete--recreate, and all six first-mutation states. |

## Independent source and identity verification

I independently replayed the six frozen event streams without using the RQ4
access CSV as an oracle.  The replay reproduced the full set of 7,154 RQ1
artifact creation tuples exactly, including project, artifact ID, first event,
first path, and birth state.  Comparing all keyed
`(project,event_id,action_ordinal)` rows gave 0 identity differences across
107,554 exported accesses, and no non-scope access has a blank identity.  Every
one of the 13,152 confirmed mutation rows resolves to its frozen RQ1 artifact
ID.

The concrete Round-1 error is repaired: AgentSight boundary `6 -> 7` now has
265 predecessor artifacts rather than 264.  No other overlap value or
first-mutation-state total was changed by that correction, consistent with the
small scope of the original identity defect.

## Population, denominator, and boundary verification

- Component construction remains unchanged and valid: 120 transitive
  concurrency components across 12 worktree lanes produce exactly 108 adjacent
  non-overlapping boundaries.  Worktree-projected component mutation totals
  still reconcile exactly to the 13,152 frozen mutation rows.
- `rq4-prefix-actions.csv` now has 6,290 rows, exactly equal to the sum of
  boundary `prefix_actions`.  No no-mutation boundary contributes a prefix.
  Two mutation-observed boundaries have zero prefix because their first
  worktree-attributed action is already the first mutation; treating these as
  empty rather than fabricating an action is correct.
- The five prefix categories remain exhaustive and exclusive for every emitted
  event.  The repaired composition matches the mutation-observed values found
  in Round 1 (for example, AgentSight predecessor-artifact 27.7% and BPF
  tutorial no-resolved-path 33.2%).
- Artifact/module overlap remains a unique-set, per-boundary measure.  Empty
  predecessor or next-mutation denominators are still blank rather than zero.
  The defined counts are 16/14/20/5/1/5 for both artifact and module overlap in
  displayed project order.  Undefined counts are recoverable from the printed
  boundary totals and are 13/8/11/6/0/9.
- First-mutation action steps and delays remain conditional on an observed
  mutation.  The six first-mutation states are exclusive per identity at the
  first mutation event and remain separated from the overlap scatter.

## Coverage stop and F7 audit

The preregistered four-project gate fails for every estimator.  In displayed
project order, timing boundary counts are 17/14/21/5/1/6; resolved-prefix
boundary counts are 15/14/20/5/1/6; and artifact/module-defined counts are
16/14/20/5/1/5.  Only BPF tutorial reaches 20 for any conditional estimator.
The figure's coverage-only footer is therefore correct and no threshold was
weakened.

F7 is visually coherent at the reviewed 1263.78-by-588.76-point vector size:
the no-mutation bar and conditional ECDF remain distinct; Panel B's repaired
population is named explicitly; overlap and first-state views use separate
axes; all five prefix and six first-state classes appear in the legends; and
the source-role limitation is legible below the panels.  The plot contains no
arbitrary action window, normalized-session estimator, Git boundary, or causal
interpretation.

## Reproducibility

A fresh independent run to a new temporary directory completed in 3.92 seconds
at 627,488 KiB maximum RSS.  All four CSV files, the PNG, and `result.md` were
byte-identical to the reviewed artifacts and match `commands.log`.  As already
disclosed, PDF metadata is not the byte-reproducibility anchor; the PDF remains
single-page vector output and visually matches the PNG.

## Non-blocking presentation note

The coverage strip defines `P` as the number of prefix **actions**, while the
formal gate is expressed in eligible resolved-prefix **boundaries**.  This is
not a validity blocker: the label is explicit, the total boundary count `B`
already proves that fewer than four projects can reach the gate, and the footer
correctly stops the interpretation.  For a paper-sized revision, replacing or
augmenting `P` with resolved-prefix boundary count `R`
(`15/14/20/5/1/6`) would make the preregistered gate directly auditable without
derivation.  Likewise, an explicit one-line empty-predecessor overlap assertion
would complete the synthetic matrix, although the real-data blank denominators
were independently verified here.

## Decision

**PASS.**  F7 and its supporting rows may enter the paper only with the
coverage/within-case qualification already present in the figure and
`result.md`.  Preserve the current source-role and four-project stop language;
do not promote the result to an independent reset/resumption estimate or a
cross-project RQ4 conclusion.
