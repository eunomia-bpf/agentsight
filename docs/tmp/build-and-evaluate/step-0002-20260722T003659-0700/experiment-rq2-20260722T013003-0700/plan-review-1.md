# RQ2 Plan Review — Round 1

**Reviewed:** 2026-07-22  
**Verdict:** **BLOCK**

The frozen RQ1 data are sufficient for a useful within-case study of
adapter-recognized validation dynamics, but the current plan can create false
cycles by mixing worktrees and can misleadingly call all mutations between two
successful commands a validation "backlog." These are construct-validity
defects, not optional presentation polish.

## What is already sound

- The plan reuses the frozen RQ1 projection rather than rescanning mutable
  native sessions, preserves native outcomes as `ok`/`fail`/`observed`, and
  explicitly avoids claims about test coverage, correctness, or causality.
- Action distance and wall-clock distance are both retained; commit time is
  correctly absent from the analysis axis.
- Prefix/suffix censoring, exact count annotations, source-event reconciliation,
  fixture checks, and explicit N/A rows are appropriate.
- No external baseline is required for this descriptive empirical RQ. The
  relevant alternative explanation is measurement coverage: an adapter may not
  recognize a real validation command.

## Frozen-data feasibility audit

I independently counted worktree-resolved `effect=test,status=ok` events in the
authoritative RQ1 event JSONs:

| Project | Recognized successes | Worktrees with a success | Complete within-worktree intervals |
|---|---:|---:|---:|
| AgentSight | 2,065 | 2 | 2,063 |
| ActPlane | 1,493 | 2 | 1,491 |
| eunomia.dev | 6 | 1 | 5 |
| bpf-developer-tutorial | 0 | 0 | 0 |
| agentskill-observability-paper | 0 | 0 | 0 |
| academic-writing-skills | 0 | 0 | 0 |

Thus only **3/6 projects qualify**, and the plan's `<4` cross-case stop is
already known to fire. RQ2 remains feasible as a supporting coverage result and
three within-case descriptions, but it cannot be presented as a six-project
cross-case validation-dynamics result. This disposition must be stated before
implementation, not discovered after plotting.

The frozen data also contain 43 successful ActPlane validation events that
carry at least one mutation-like file action in the same Tool event (plus two
`observed` attempts with such effects). Therefore intra-event boundary
semantics are not hypothetical and must be fixed before measuring cycles.

## Required repairs

1. **Partition cycles by worktree.** Define every sequence and cycle within
   `(project, worktree_id)`, then aggregate only explicitly for descriptive
   project summaries. A success in worktree A must never terminate or reset a
   mutation sequence in worktree B. Panel A must either provide worktree lanes
   or otherwise preserve this identity; one mixed project line is invalid.

2. **Replace the unsupported backlog construct.** A recognized successful
   command is not evidence that it covers all preceding mutations, as the plan
   itself correctly acknowledges. Rename the primary measure to
   **inter-success mutation accumulation** (or the literal "confirmed mutations
   since the previous recognized successful validation") and never say that a
   success clears or validates those mutations. `maximum backlog` is redundant
   with the terminal accumulation because the defined count is monotone; drop
   it unless a separately justified outstanding-artifact state is defined.

3. **Freeze same-event semantics.** A Tool event may be both
   `effect=test` and carry mutation rows. The source projection provides no
   within-event temporal order. Mutations sharing the boundary success's
   `event_id` must be reported separately as co-observed validation-command
   effects and excluded from a "before the success" count, or another
   conservative non-ordering rule must be preregistered. They cannot silently
   be assigned before or after the success. Add a fixture for this case.

4. **Use the frozen canonical event order and define the action axis exactly.**
   Preserve the JSON event-array order (already frozen by `(ts_ms, event.id)`),
   verify IDs are unique, and derive a zero/one-based
   `worktree_attributed_action_rank` within each worktree. "Source ID" is
   ambiguous (`event.id` versus `source_call_id`), and RQ1 `event_index`
   includes unattributed actions. State whether cycle action length includes
   the ending validation event. Count confirmed mutation **rows**, not merely
   events, because one Tool event can affect several artifacts.

5. **Make censoring worktree-local.** The observed prefix begins at the first
   worktree-attributed Tool action and the suffix ends at that worktree's last
   attributed action at or before the frozen cutoff—not at another worktree's
   event or at an artificial silent interval to wall-clock cutoff. Define
   `sessions crossed` as either distinct native session IDs or boundary
   transitions; the current phrase is not reproducible. Preserve simultaneous
   or interleaved native sessions without inventing a serial session order.

6. **Pin the source manifest and executable path.** Name the exact RQ1 raw
   directory, cutoff `1784708569241`, the six compressed event-file hashes and
   mutation-CSV hash already recorded in RQ1 `commands.log`, plus the planned
   RQ2 CSV, script, command, and output paths. Reconciliation should include
   per-project totals and exact `event_id` joins. This prevents later local
   files with the same names from silently replacing the freeze.

7. **Freeze artifact/module classification before running it.** Specify the
   ordered path rules for code, test, config, paper/docs, data/results, and
   unknown, as well as the module key (for example, first retained path
   component). Retain unknown and report classifier coverage. Otherwise the
   proposed mix analysis remains post-hoc and non-reproducible.

8. **Make F5 honest about the predetermined coverage stop.** Panel B should be
   labelled "inter-success mutation accumulation," show distributions by
   project/worktree with cycle counts, and not pool cycles as independent
   project samples. Panel A may normalize x only for display, but must expose
   actual attributed-action and elapsed-time ranges and must not overlay a
   validation from one worktree on mutations from another. Panel C should mark
   `3/6 recognized-success coverage; cross-case interpretation stopped` and
   retain all six rows. The caption must state that failed/`observed` markers
   are recognized attempts, not established test failures or absence of
   validation.

9. **Update the scientific decision rule.** Explicitly classify this run as a
   supporting within-case/coverage experiment given the known 3/6 gate. State
   the expected pattern, the competing possibility (recognized attempts simply
   track activity or are too adapter-sparse), and how concentrated, mixed, or
   null within-case results affect RQ2. Do not promote the thousands of cycles
   inside two projects into population-level replication.

## Minimum verification matrix after repair

The unit fixtures should cover: two interleaved worktrees; multiple native
sessions in one worktree; equal timestamps; multiple mutation rows in one Tool
event; a validation event with a co-observed mutation; zero/one/two successes;
failed and `observed` attempts; left prefix and right suffix; and no
worktree-resolved identity. The real preflight should run one qualifying
project end to end from the pinned frozen files and verify selected cycles by
source `event_id` before the full six-row coverage output is generated.

After these repairs, the plan should be executable without rescanning sources
or adding a new event abstraction.
