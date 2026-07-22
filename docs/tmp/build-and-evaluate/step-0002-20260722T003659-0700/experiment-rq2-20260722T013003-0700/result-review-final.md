# RQ2 Final Result Review

**Reviewed:** 2026-07-22  
**Verdict:** **BLOCK**

The command completed reproducibly, and most bookkeeping checks pass, but the
primary worktree-local mutation projection drops 4,099 confirmed mutation rows.
This materially changes an AgentSight worktree's complete-cycle distribution,
so the current CSVs, result text, and F5 are not admissible paper evidence.

## Checks that pass

- All seven frozen input SHA-256 values and all five output SHA-256 values match
  `commands.log` exactly. The six gzip payloads are read directly, not replaced
  by mutable uncompressed JSON.
- Every frozen event array is ordered by `(ts_ms, event.id)`, has unique event
  IDs within its project, and ends at or before cutoff `1784708569241`.
- The current trajectory CSV contains 175,850 rows in 11 event-worktree lanes.
  Within that projection, action ranks are consecutive, source event IDs,
  timestamps, sessions, effects, mutation counts, and cumulative counts all
  reconcile.
- Native recognized-attempt counts independently recompute as
  AgentSight `2065/331/110`, ActPlane `1493/201/77`, and eunomia.dev
  `6/0/87` for `ok/fail/observed`; the other three projects have no recognized
  attempt. The preregistered coverage stop is therefore correctly `3/6`.
- The 3,575 cycle rows exactly recompute from the current trajectory: 3,559
  complete intervals, five left-censored prefixes, five right-censored
  suffixes, and six no-success-observed lanes. Boundaries are worktree-local,
  ending successes are included in action length, durations are non-negative,
  and native sessions are not serialized into an invented order.
- ActPlane has 44 co-observed mutation rows on 43 successful validation events.
  They are reported as ending co-observed effects and excluded from the
  preceding complete-cycle accumulation as preregistered.
- The reported complete-cycle summaries exactly match the current cycle CSV:
  ActPlane/`3dae...` `n=1491`, zero `89.1%`, median `0`, p90 `1`, max `1144`;
  AgentSight/`b5bc...` `311`, `92.9%`, `0`, `0`, `800`;
  AgentSight/`e58f...` `1752`, `86.9%`, `0`, `1`, `95`; and
  eunomia.dev/`30e8...` `5`, `60.0%`, `0`, `32`, `32`.
- `verify_inputs()` checks the pinned gzip and mutation-CSV hashes before
  extraction. After writing the three RQ2 CSVs, the script releases extraction
  objects and `plot_from_csv()` reopens the written CSVs to render PDF and PNG.
  No fixture value enters F5.

## Blocking defect: mutation worktree is discarded

`derive_trajectory()` joins mutation rows by
`(project, event.worktree_id, event_id)`. A Tool event's execution worktree and
an affected file's `FileAction.worktree_id` can differ, especially when a
command in one checkout explicitly edits another checkout. The frozen RQ1
mutation table intentionally preserves the latter identity.

All 13,152 mutation rows resolve to a frozen source event by
`(project, event_id)`, but only 9,053 have the same event and file-action
worktree. The current RQ2 projection silently omits the remaining **4,099**:

- 4,094 AgentSight rows from `e58fce112c6e` into `b5bc34dabe6a`;
- 4 AgentSight rows from `e58fce112c6e` into `f2407a7d66d5`;
- 1 eunomia.dev row from `30e8a01e495d` into `da5c4a85644b`.

These are not weak path guesses: the frozen mutation rows classify 3,093
writes, 985 creates, 19 deletes, and 2 renames, and their source Tool events
are successful adapter-recognized writes. Consequently, Panel A reports only
2,384 of AgentSight's 6,482 frozen mutation rows and 169 of eunomia.dev's 170.

This omission changes the substantive within-case pattern. Projecting each
mutation onto its file-action worktree while retaining successful validation
on its command worktree changes AgentSight/`b5bc...` from 1,066 to 5,160
cumulative mutation rows. Its complete-cycle zero fraction changes from 92.9%
to 25.1%, median from 0 to 2, and p90 from 0 to 26. One concrete pair of
success boundaries (`...:20426` to `...:24741`) contains 553 target-worktree
mutation rows, whereas the current CSV counts 13. This is not a presentation
detail; it invalidates the current cycle distribution and plotted trajectory.

The repaired projection must explicitly permit one Tool event to appear in
more than one worktree lane: validation belongs to the command/event worktree,
while confirmed file mutations belong to each `FileAction.worktree_id`.
Lane-local ranks, cycles, censoring, summaries, hashes, and F5 then need a full
rerun from the same frozen sources. The figure should also add per-lane attempt
counts, which the approved plan requires but the current Panel A labels omit.

## Result-review judgments

```text
run status: invalid
tested hypothesis: inconclusive
research value: supporting if repaired; current result is not admissible evidence
paper impact: no RQ2 evidence should enter the paper from this run
next paper decision: repair cross-worktree event projection and rerun the frozen RQ2 analysis once
```

