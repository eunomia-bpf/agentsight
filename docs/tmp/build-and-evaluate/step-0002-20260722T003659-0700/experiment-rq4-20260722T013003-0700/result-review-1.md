# RQ4 Result Review — Round 1

**Reviewer:** independent result reviewer `/root/rq4_result_review`  
**Reviewed:** `plan.md`, `plan-review-2.md`,
`agentvis/research/plot_rq4.py`, `commands.log`, all four raw CSV files,
`result.md`, and F7 PDF/PNG  
**Verdict:** **BLOCK**

The frozen extraction and concurrency-component construction are reproducible,
and the stated coverage stop is directionally correct.  F7 cannot yet enter the
paper, however, because Panel B pools terminal no-mutation components into a
quantity labelled *pre-mutation*, the access-identity replay is not exact, and
the promised estimator-level coverage counts are absent from the figure.  The
first defect materially changes the displayed composition; the second is a
smaller numerical defect but violates the frozen identity construct.

## Independent checks that passed

- All recorded source/output hashes match `commands.log`.  A fresh execution to
  a new temporary directory completed in 3.76 seconds at 628,012 KiB maximum
  RSS.  All four CSV files, the PNG, and `result.md` were byte-identical to the
  reviewed outputs.  The PDF differs only through the already-disclosed
  Matplotlib metadata behavior.
- The output has 120 concurrency components across 12 worktree lanes and 108
  adjacent component boundaries.  Independently checking each lane gives
  `sum(components_in_lane - 1) = 108`; every adjacent output component is
  strictly non-overlapping.  The implementation's interval scan correctly
  takes the transitive closure and treats equal endpoints as overlap.
- Worktree projection preserves all confirmed RQ1 mutations exactly once:
  component `mutation_rows` sum to 13,152, matching the 13,152 frozen mutation
  rows, including exact per-project totals (6,482 AgentSight; 5,770 ActPlane;
  283 BPF tutorial; 170 eunomia.dev; 196 AgentSkill paper; 251 Writing skills).
- Boundary-row invariants hold: the five exclusive prefix counts sum to
  `prefix_actions`; no-mutation rows have no timing or overlap value; and every
  mutation-observed row has a first-mutation action step.  Artifact/module
  overlap uses unique next-component sets and leaves empty denominators blank.
- The six-state first-mutation classification is source-bounded and visually
  separated from the overlap scatter.  Root files use `repo-root-files`.  The
  figure does not make a reset, resume, memory, or forgetting claim.
- The coverage stop is required.  Only BPF tutorial reaches 20 conditional
  first-mutation boundaries (21), 20 mutation-observed boundaries with a
  resolved prefix, and 20 defined artifact/module overlaps.  Thus no estimator
  reaches the preregistered four-project gate.  F7 may only be described as
  coverage/within-case evidence.

## Blocking defect 1 — Panel B is not a pre-mutation population

`derive_boundaries()` sets

```python
prefix_events = [event for event in current_events
                 if first_index is None or event_index < first_index]
```

so a component with no observed mutation contributes its **entire observed
component** to `rq4-prefix-actions.csv` and Panel B.  `plot()` then pools those
rows with genuine prefixes.  This conflicts with the Round-2 plan-review
condition that a no-mutation component contributes only to the separately
reported no-mutation outcome unless a distinct full-observed-prefix stratum is
predeclared.  No such stratum was preregistered, exported, labelled, or drawn.

The contamination is material rather than cosmetic.  No-mutation components
provide 5,037 of 8,626 displayed Panel-B events for AgentSight; 3,354/5,454 for
ActPlane; 642/910 for BPF tutorial; 2,604/2,849 for eunomia.dev; and 148/221 for
Writing skills.  For example, AgentSight's displayed predecessor-artifact share
is 17.0%, whereas the mutation-observed prefix population is 27.7%; BPF
tutorial's no-resolved-path share moves from 50.8% to 33.2%.  The panel must be
rederived from mutation-observed components, or the plan must undergo a new
review that explicitly defines and separates terminal full-component activity.
Relabelling the current pooled bar as “pre-mutation” is not valid.

## Blocking defect 2 — artifact identity replay is incomplete

The plan requires stable identity from deterministic replay of frozen event
actions.  `project_events()` seeds identities from the artifact table but
updates `live` only from confirmed rows in `rq1-mutations.csv`.  RQ1's actual
lifecycle state changes on every resolved non-scope action, including
status-`observed` rename/delete/create actions.  Consequently an observed
rename can move an identity in RQ1 while RQ4 leaves the old path live and the
new path absent.

I independently replayed all frozen actions using the RQ1 `apply_action`
semantics and first verified an exact 7,154/7,154 match to the frozen artifact
creation tuples `(project, artifact_id, first_event_index, first_path,
birth_state)`.  Comparing that independent replay to `rq4-accesses.csv` found
41 wrong identities among 107,554 resolved access rows (0.038%), all in
AgentSight: 36 are incorrectly blank, and five name the wrong lineage.  The
affected actions include 26 reads, nine writes, four renames, one create, and
one delete.  A concrete propagation is the status-unknown move of
`collector/src/local_sessions.rs` to
`collector/src/sources/agent_native.rs`: subsequent accesses should retain
`agentsight:a00000281`, but RQ4 emits an empty identity.

The current aggregate impact happens to be small: with exact replay, boundary
AgentSight/e58fce112c6e `6 -> 7` has 265 predecessor artifacts rather than 264;
the displayed overlap and six first-mutation state totals do not otherwise
change.  This does not make the implementation valid: the exported access
table is part of the evidence, and a future corpus can turn the same lifecycle
error into a changed overlap/state conclusion.  Replay all non-scope frozen
actions in event/action order and assert every emitted access identity against
that replay, while retaining the existing 13,152 mutation reconciliation.

## Blocking defect 3 — required coverage/count disclosure is missing from F7

The plan requires Panel C to print eligible, undefined, and
concurrency-component counts and applies the 20-boundary/4-project gate
separately to timing, resolved prefix composition, artifact overlap, and module
overlap.  The current figure prints timing `n` values and a generic footer, but
Panel C prints no defined/undefined counts, and Panel B prints neither its
eligible population nor the fact that its current population mixes two outcome
types.  `result.md` contains a useful coverage table but does not satisfy the
figure-level disclosure or name each estimator's gate.

After correcting Panel B, print compact per-estimator counts (or a legible
embedded coverage strip/table) and state that every four-project gate stopped.
The observed project counts are: timing 17/14/21/5/1/6 and artifact/module
defined 16/14/20/5/1/5 in the displayed project order.  The figure remains
readable at its current vector size; this is a data-disclosure repair, not a
request for a larger dashboard.

## Verification gap

`self_check()` tests only one transitive-overlap example.  The preregistered
matrix also names equal timestamps, multiple worktrees, no mutation, empty
predecessor sets, multi-path priority, rename, delete--recreate, and all six
first-mutation states.  No separate tests for these cases exist.  The missing
rename check is directly related to Blocking defect 2.  Add compact deterministic
self-checks (no test framework or new dependency is needed) before rerunning.

## Decision

**BLOCK F7 and paper integration.**  Preserve the valid component construction,
worktree projection, conditional timing estimator, unique-set overlap
denominators, coverage stop, and visual layout.  Repair the identity replay,
exclude or separately define no-mutation component activity for Panel B, add
the frozen self-check cases and estimator-level coverage counts, regenerate all
four CSVs plus F7, and request a fresh independent result review.
