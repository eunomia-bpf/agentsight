# Plan Review: RQ2 Representation Choice On Hodoscope SWE-bench

## Round 1 — Scientific Question, Baselines, And Fairness

**Reviewer role:** fresh independent scientific reviewer  
**Verdict:** REVISE  
**Files edited by reviewer:** none

### Blocking findings

1. Matched-view ranking did not specify exact node scoring, size
   normalization, internal/terminal competition, coordinate space, or complete
   action permutation. Different choices could manufacture a recursive win.
2. The “initial” semantic stack left ontology and clustering decisions open
   despite public knowledge of the target behavior. Banning literal oracle
   keywords did not prevent a target-informed category.
3. It was unclear whether the semantic mapping used all reference actions while
   official Hodoscope used a 50% per-seed subsample.
4. First-hit rank alone did not establish the full RQ2 end-to-end cost condition.
5. The statistical decision rule was not executable.
6. Corpus counts conflated 4,006 iQuest target actions with the five-cohort
   total of 11,855 actions (7,849 reference plus 4,006 target).

### Optional findings

- Keep the metric set small; large-k hit concentration adds little.
- Remove the optional confirmed-future-patch annotation or predefine it fully.
- Treat the all-250 phase as a sensitivity extension, not a second RQ.

### Main-agent response

**Accepted all six blocking findings.** The plan is revised before preflight:

- The semantic representation is now a fully mechanical nested clustering of
  author-released embeddings, with fixed 8/32/128 fanout, reference-only fit,
  and no manually named workflow or action categories.
- Every paired seed fits all matched representations on the same reference
  subsample and scores the same target subsample using the same official t-SNE
  coordinates.
- Every representation maps each target action to a nonnegative excess-mass
  contrast. The matched action permutation uses the same density-weighted
  farthest-point procedure as Hodoscope; only the contrast induced by the
  representation changes.
- The node contrast, action contrast, tie rule, coordinate space, and complete
  permutation are defined algebraically in the plan.
- The experiment is explicitly partial RQ2 inspection-effort evidence. It
  reports preprocessing, construction, query, wall time, RSS, storage, actions,
  and characters separately and makes no full end-to-end value claim.
- The paired decision rule is a prespecified bootstrap interval plus win rate
  over identical seeds/subsamples; no vague “unambiguous” criterion remains.
- Counts are corrected to 11,855 complete-corpus actions, of which 4,006 are
  target actions and 132 are published oracle-positive target actions.
- The optional independently confirmed-exploit metric is removed.

The reviewer also confirmed that Hodoscope is the right precedent and that the
official artifacts are sufficient. Round 2 receives only the revised plan and
this discussion history, with no desired verdict.

## Round 2 — Executability, Commands, And Artifact Path

**Reviewer role:** fresh independent execution reviewer  
**Verdict:** REVISE  
**Files edited by reviewer:** none

### Blocking findings

1. Released Hodoscope records do not expose the proposed
   `source_action_type`; the native parser and globally comparable identity were
   undefined.
2. Official Hodoscope ranks at most 500 actions per group and assigns a sentinel
   afterward, conflicting with the plan's complete-permutation requirement.
3. The released schema has no standalone stable action ID, so the tie-break was
   not executable.
4. Nested clustering left full-path identity, small-parent behavior, empty
   children, embedding normalization, and native fallback open.
5. Phase B mixed “one deterministic complete run” with ten stochastic seeds.
6. The comparative extension had no exact entry point, arguments, or output
   schema.

### Main-agent response

**Accepted all blocking findings.** The revised plan:

- uses only the released `turn_id` as the source-order/native frame, with
  trajectory and source retained only for drillback;
- defines a composite action key from analysis source, trajectory ID, turn ID,
  and within-source ordinal;
- preserves the official 500-action Hodoscope prefix and appends sentinel-tail
  actions by composite key only for the complete-extension permutation;
- specifies full cluster-path IDs, `min(4,n)` child behavior, no empty nodes,
  finite-vector checks, and explicit L2 normalization;
- makes Phase B ten complete-corpus runs with no subsampling, varying only the
  prespecified clustering/projection/FPS seed;
- names one comparative runner and fixes its CLI modes and raw-output schema;
- expands real preflight to all four views and defines the no-hit metric row.

Round 3 receives the twice-revised plan and complete review discussion. It must
decide whether any result-invalidating defect remains rather than request
optional infrastructure.

## Round 3 — Final Convergence Audit

**Reviewer role:** fresh independent full-plan auditor  
**Verdict:** PASS  
**Files edited by reviewer:** none

The reviewer found no remaining scientific or executability defect that would
invalidate the result:

- the experiment answers RQ2 while explicitly limiting its claim to partial
  inspection-effort evidence;
- paired information and review budgets are matched;
- flat and recursive views share terminal clusters, isolating hierarchy;
- hierarchy construction, node scoring, FPS, complete permutations, ties,
  oracle isolation, counts, and no-hit handling are mechanical;
- Hodoscope's official prefix is preserved and its extension-only tail is
  labeled;
- ten paired repetitions, bootstrap rule, interpretations, cost boundary,
  preflight, full completion, raw paths, and schemas are executable.

Two non-blocking execution reminders remain: print the fully expanded
`--mode all` command before the run, and keep A1 official-reproduction output
separate from the paired Hodoscope permutations. Existing plan text already
requires both. No further plan revision or review round is needed.

## Review Outcome

**Plan status: approved for REAL PREFLIGHT.** Three fresh serial reviewers were
used. Rounds 1 and 2 found and resolved result-invalidating defects; Round 3
passed the revised plan. Optional polish does not block execution.
