# RQ2 Result Review — Round 2

**Reviewed:** 2026-07-22  
**Verdict:** **PASS**

The repaired run closes the blocking cross-worktree projection defect. The
current CSVs, result summary, and F5 are valid supporting evidence for
adapter-recognized validation dynamics in the three covered projects. The
predeclared `3/6` stop remains binding, so this result does not support a
six-project cross-case claim and does not close canonical RQ2.

## Independent recomputation

- All seven input hashes and all five recorded output hashes match
  `commands.log`. An independent execution of the current script reproduced
  the three CSV hashes and PNG hash exactly.
- The trajectory has 179,928 rows. For every frozen Tool event, I independently
  formed the union of its home worktree and all explicit
  `FileAction.worktree_id` values. The resulting `(project, event_id,
  worktree_id)` key set, lane-local action ranks, event indices, timestamps,
  session/vendor fields, home marker, effects, statuses, mutation counts,
  artifact IDs, co-observed counts, and cumulative counts match every written
  trajectory row exactly.
- All **13,152** frozen mutation rows appear exactly once in the worktree named
  by the mutation/FileAction row. No mutation key is missing or duplicated.
  Project totals now reconcile to AgentSight 6,482; ActPlane 5,770; BPF
  tutorial 283; eunomia.dev 170; AgentSkill paper 196; and Writing skills 251.
- Validation is home-only: no non-home projection carries `effect=test` or a
  validation status, and every home projection retains its native event
  effect. Recognized outcomes independently remain AgentSight
  `2065/331/110`, ActPlane `1493/201/77`, eunomia.dev `6/0/87`, and zero in the
  other three projects. Thus `3/6 recognized-success coverage; cross-case
  interpretation stopped` is correct.
- The 3,576 interval rows recompute exactly: 3,559 complete cycles, five
  left-censored prefixes, five right-censored suffixes, and seven
  no-success-observed worktree lanes. All boundaries are lane-local, the ending
  success is included in action length, durations are non-negative, session
  counts use distinct native IDs, and no other worktree's validation closes an
  interval.
- The 44 mutation rows on 43 successful ActPlane validation events remain
  separately reported as ending co-observed effects and are excluded from the
  preceding interval's mutation accumulation.
- Complete-cycle statistics independently recompute as:
  - ActPlane/`3dae...`: `n=1491`, zero `89.1%`, median `0`, p90 `1`, max `1144`;
  - AgentSight/`b5bc...`: `n=311`, zero `25.1%`, median **2**, p90 **26**,
    max **800**;
  - AgentSight/`e58f...`: `n=1752`, zero `86.9%`, median `0`, p90 `1`, max `95`;
  - eunomia.dev/`30e8...`: `n=5`, zero `60.0%`, median `0`, p90 `32`, max `32`.
  The previously diagnostic `...:20426` to `...:24741` interval now contains
  the correct 553 target-worktree mutation rows.

## Figure audit

F5 is consistent with the repaired CSVs. Panel A contains all 12 worktree
lanes, reports the corrected AgentSight `b5bc...` total of 5,160 mutation rows,
and now exposes per-lane `ok/fail/observed` attempt counts (`v=`). Non-home
mutation projections do not acquire validation markers. Panel B plots the four
eligible lane distributions and exact cycle counts, while Panel C retains all
six projects and visibly states the `3/6` stop. Titles, legends, and footer use
“recognized validation” and correctly disclaim mutation coverage.

Two non-blocking provenance/label precisions remain:

1. Panel C's AgentSight denominator is the 96,670 home-worktree-attributed Tool
   events; 312 additional events have only an explicit FileAction target
   worktree. The current rate is internally consistent with RQ1's primary
   action denominator, but “home-worktree-attributed actions” would be a more
   exact axis label.
2. Matplotlib's PDF metadata makes a fresh PDF byte hash differ across runs,
   although the recorded PDF matches `commands.log` and the independently
   regenerated PNG and all numerical CSVs are byte-identical. This does not
   affect the plotted content or measurements.

## Result-review judgments

```text
run status: valid
tested hypothesis: supported within the three adapter-covered projects; cross-case answer remains inconclusive
research value: supporting
paper impact: additional RQ2 evidence with an explicit source-coverage boundary
next paper decision: admit F5 and the within-case cadence result, retain the 3/6 stop, and do not claim validation coverage or causal quality effects
```

