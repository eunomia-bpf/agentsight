# RQ5 Plan Review — Round 2

**Reviewer:** independent plan reviewer  
**Date:** 2026-07-22  
**Verdict:** **BLOCK**

Round 2 closes most of the first review. `artifact-path-v1` is now exhaustive;
rename allocation is explicit; RQ4 supplies lifecycle identity; return events
use resolved-call distance rather than an ordinal session index; the top-8 and
60-column display contract is nearly fixed; the construct is narrowed away
from time/internal attention; and the command, outputs, reconciliation, and
per-dimension gates are executable. Four remaining ambiguities can still
change a primary number or misclassify a spatial transition, so they require
one final repair before execution.

## Round-1 disposition

| Round-1 issue | Round-2 judgment |
|---|---|
| Exhaustive path classifier | **PASS.** The exact basename list/regex, case folding, precedence, normalization, unknown class, and rename destination rule are frozen. |
| Action versus Tool-call fan-out | **PARTIAL.** Set-valued calls and fractional weighting are present, but the fractional denominator and operation strata remain ambiguous. |
| Set-valued transitions | **PARTIAL.** Lineage and `(worktree_id,module)` sets are correct, but different-worktree adjacency is folded into `cross-module`. |
| Return distance and censoring | **PARTIAL.** The return event and two distance axes are fixed, but the terminal risk interval is not. |
| Heatmap compaction | **PARTIAL.** Top 8, lexical ties, remainder, and 60-bin assignment are fixed; color normalization is not. |
| Source/claim boundary | **PARTIAL.** Failed/scope/time limitations are correct, but inclusion of `observed` versus `ok` action status is unspecified. |
| Runnable outputs and gates | **PASS.** The command, frozen inputs, raw tables, figure outputs, reconciliation, and dimension-specific stop rules are adequate. |

## Remaining blocking repairs

### 1. Freeze action status and the exact fractional formula

“Successfully resolved” can mean either “path resolution succeeded” or
`event.status == ok`. The frozen data contain 11,311 non-scope file actions
whose event status is `observed`, in addition to 83,801 with status `ok`; this
choice is therefore material. State explicitly whether both `ok` and
`observed` enter as resolved activity. If both enter, say that `resolved`
describes path resolution and does not upgrade `observed` to confirmed effect.

Likewise, “divide evenly across distinct resolved artifact
lineages/classes” admits two different results. Freeze the formula as, for
example, `1 / number_of_distinct_lineage_ids_in_the_call_and_stratum` for each
lineage, then sum lineage weights by class. Define the two Panel-A strata
exactly as `read` and `mutation = {write, create, rename, delete}`; a call
containing both receives one unit in each separate panel, not two units in a
combined denominator. Reconcile the fractional weights to the number of calls
eligible for each stratum.

### 2. Do not encode a worktree switch as a module switch

The current precedence makes two adjacent calls from different worktrees
`cross-module`, even though the module comparison is undefined across separate
workspace identities. Either form adjacency independently within each
`(project, worktree_id)` sequence, or add a fourth mutually exclusive
`cross-worktree` outcome before `cross-module`. For set-valued calls, state the
set rule explicitly. Panel C and its qualification denominator must follow the
same choice. This is required to support a module-migration statement rather
than a mixture of module and worktree switching.

Because timestamp ordering can interleave concurrent native sessions, describe
these transitions as movement of the **merged observed workspace activity**,
not a single Agent's serial cognitive path. RQ4 identity replay supplies
artifact lineage; it does not establish top-level Agent identity.

### 3. Define when a terminal module-return interval is at risk

As written, “a terminal right-censored gap for every active module not returned
to” can assign a censored gap to every module's final occurrence, including a
module present in the final call. That is inconsistent with the return event,
which requires at least one intervening call without the module.

Open a return-risk interval only at the first subsequent resolved call that
does not contain module `m`, retain the last call containing `m` as the distance
origin, close it at the next call containing `m`, and right-censor only intervals
still open at observation end. A module present in the final call has no open
terminal interval. Export observed/censored status and both exact call-step and
wall-time distances. This removes survivor bias without inventing a forgetting
claim.

### 4. Freeze heatmap color normalization

“Row-normalized only for color” must specify the denominator. Choose one exact
rule, such as `cell_count / sum(row_cell_counts)` or
`cell_count / max(row_cell_counts)` with an all-zero rule, and state whether
the `remainder` row uses the same transformation. The top-8 selection should
also say that a multi-file call counts at most once for each module key; this
is implied by the set representation but should be executable from the plan.
These choices do not affect CSV statistics, but they materially affect F8's
visible hotspot pattern.

## Claim boundary after repair

With these repairs, the plan can validly support a descriptive result about
artifact allocation, module transitions, and return gaps in successfully
resolved non-scope activity across six observed repositories. It must retain
the current prohibitions on duration, effort, internal attention, importance,
productivity, causality, forgetting, and population inference. No additional
baseline, workload, or analysis family is required.

## Required disposition

Apply only the four definition repairs above and return the same plan for the
third and final plan-review round. If any primary unit remains ambiguous after
that round, close the RQ5 experiment rather than interpreting an implementation
choice post hoc.
