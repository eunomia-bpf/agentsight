# RQ5 Plan Review — Round 3 (Final)

**Reviewer:** independent plan reviewer  
**Date:** 2026-07-22  
**Verdict:** **PASS**

The repaired plan closes all four Round-2 blockers without broadening the
experiment or weakening its claim boundary.

## Final verification

1. **Status and fractional fan-out — closed.** The primary source universe now
   explicitly includes path-resolved non-scope actions from both `ok` and
   `observed` events, keeps those status strata visible, and repeats allocation
   on `ok` alone. “Resolved” is correctly limited to path resolution. The two
   operation strata are frozen as `read` and
   `mutation = {write, create, rename, delete}`. Tool-call weighting now
   deduplicates lineage IDs, assigns each lineage exactly `1 / n` within a
   present call/stratum, aggregates those weights by artifact class, and
   reconciles the total to eligible calls. Mixed read/mutation calls are
   unambiguous.

2. **Worktree and set-valued transition semantics — closed.** Adjacency is
   independently constructed within each `(project, worktree_id)` lane, so a
   worktree switch cannot be mislabeled as module migration. Multi-worktree
   events enter each affected lane without creating cross-worktree adjacency.
   Within a lane, the `same artifact` → `same module` → `cross-module`
   precedence operates on lineage/module sets, and singleton-only sensitivity
   is retained. The plan explicitly limits interpretation to merged observed
   workspace activity rather than a single Agent's cognitive path.

3. **Return risk and terminal censoring — closed.** A module return interval
   opens only after the first subsequent call in the lane that omits the
   module, uses the last containing call as its distance origin, closes on the
   next containing call, and is right-censored only if still open at the
   observation end. A module present in the final call has no terminal
   interval. Observed/censored status, call-step distance, wall time, and
   same/different native session ID are all exported; no ordinal-session or
   forgetting inference remains.

4. **Heatmap compaction and color — closed.** Top-eight selection is based on
   distinct containing calls per `(worktree_id,module)`, ties are lexical, all
   other modules enter `remainder`, and calls use the frozen 60-bin formula.
   Color is exactly `cell_count / row_max`, including `remainder`, with a
   defined all-zero result. Exact counts remain outside this display-only
   normalization.

## Executability and evidence boundary

The frozen RQ1 cutoff and reviewed RQ4 identity dependency are explicit. The
single command names its inputs and outputs; reconciliation covers status,
actions, calls, fractional denominators, scope/failure coverage, and project/
vendor strata; allocation, transition, and revisit have separate qualification
gates. The figure is regenerated from exported rows. These checks are
sufficient for a real preflight and full six-case run.

The admitted result remains supporting and descriptive: it may characterize
artifact allocation, module transitions, and return gaps in path-resolved
non-scope activity for the six observed repositories. It cannot establish
duration, effort, internal attention, artifact importance, productivity,
causality, forgetting, or population-level Agent behavior. No scientific or
executability defect remains in the preregistered plan.
