# RQ5 Plan Review — Round 1

**Reviewer:** independent plan reviewer  
**Date:** 2026-07-22  
**Verdict:** **BLOCK**

The frozen six-project data are readable and large enough to execute a
descriptive RQ5 analysis, and the plan correctly keeps Git time and Nebula's
force-layout coordinates out of the statistics. However, several primary
measurements are not yet uniquely defined. Different reasonable
implementations would produce different allocation, transition, revisit, and
hotspot results, so execution must not begin from this version.

## What already passes

- The main estimand is appropriately bounded to observable file-directed
  activity rather than an Agent's internal cognitive state.
- The main unit of one weight per non-scope file action is reasonable, and the
  plan preserves read versus mutation instead of combining them into a hand
  weighted score.
- The first-match artifact taxonomy, stable directory color, explicit
  `other/unknown`, `repo-root-files`, and exclusion of force-layout positions
  are sound design choices.
- This is a descriptive multi-case study, so no external baseline is needed.
  Cases must remain cases rather than being treated as independent draws from
  an Agent population.
- All six frozen gzip files pass integrity checks. They contain 463--40,377
  resolved file-directed Tool calls and 463--57,652 non-scope file actions per
  project, so the present minimum-size gate is feasible.

## Blocking defects

### 1. `artifact-path-v1` is called frozen but is not fully executable

The precedence order is clear, but phrases such as "a known manifest/build
basename such as" leave the accepted basename set open. Matching semantics for
README/CHANGELOG/LICENSE are also unspecified: exact basename, basename with an
extension, or prefix. A future implementer could add familiar files after
seeing the corpus and change the artifact mix while still claiming to follow
the plan.

Freeze an exhaustive case-insensitive basename list or exact regular
expressions. State that path components are computed after repository-relative
normalization, with no `.` or `..`. Also state how a rename is classified: the
destination path should receive the allocation weight, while a cross-module
rename should be retained as a separate source-to-destination fact. Generic
`.json` and other intentionally unmatched paths may remain `other/unknown`.

### 2. Tool-call sensitivity and spatial transitions are undefined under fan-out

Multi-file calls are common, not an edge case: the frozen AgentSight trace has
7,658 calls with more than one non-scope file action and ActPlane has 2,708.
The plan does not say whether a Tool call touching three source files and one
test contributes four votes, one vote to every class, fractional votes, or one
dominant class. It also asks for one of `same artifact`, `same module`, or
`cross-module` between consecutive Tool calls without defining how two sets of
paths map to one mutually exclusive category. Ordering file actions within a
call would be invalid because the exported order is not a native execution
order.

Freeze both units before execution. One valid contract would be:

1. the primary action-weighted analysis gives each non-scope file action unit
   weight;
2. in the Tool-call sensitivity, each call has total weight one within each
   reported operation stratum and divides that weight across its distinct
   resolved artifact lineages/classes;
3. a Tool-call transition operates on sets: `same artifact` if lineage sets
   intersect, otherwise `same module` if `(worktree_id, module)` sets
   intersect, otherwise `cross-module`;
4. singleton-only transitions are reported as a sensitivity to show whether
   high-fan-out calls determine the result.

Other deterministic choices are acceptable, but they must preserve total
weight and be stated. `same artifact` must use the RQ1 lifecycle identity,
including rename inheritance and delete/recreate separation, rather than path
equality. The module key must include the worktree identity so two `src`
directories in different worktrees are not declared the same module. Use the
repository event ID as the call identity; `source_call_id` is optional evidence
metadata.

### 3. Revisit distance and censoring are not defined

"Revisit distance to a previously active module in action steps, wall time,
and sessions" does not identify the previous event, the qualifying intervening
activity, or the denominator. It is also unclear whether "action steps" means
all Tool actions, resolved Tool calls, or individual file actions. A global
ordinal session distance is not well-defined when sessions overlap and their
events interleave. Reporting only observed returns would systematically omit
the very long-inactive modules that motivate the question.

Freeze a module-return episode on the resolved Tool-call sequence. For
example, a return to module `m` occurs when a call contains `m`, the immediately
preceding resolved call did not, and `m` appeared earlier; distance is measured
from the most recent earlier call containing `m`. Report event and wall-clock
distance, same-session versus cross-session status, and terminal right-censored
gaps for modules not observed again. Remove ordinal "session distance" unless
a non-overlapping session order can be established. Do not translate an
unobserved return into internal "forgetting."

### 4. Hotspot migration and heatmap compaction are under-specified

The plan does not fix how many "top modules" remain, how ties are resolved, how
many equal-count columns are drawn, or whether columns contain file actions or
Tool calls. More importantly, cumulative prefix rank can show accumulation and
leader changes but cannot show a hotspot cooling: old counts never decay.
Consequently the current measurement cannot support the stated formation,
migration, and cooling interpretation.

Predeclare a deterministic display rule (for example, select a fixed number of
modules by full-trace action count, break ties lexically, aggregate every other
module into `remainder`, and bin resolved Tool calls into a fixed number of
nearly equal-count columns). Label this explicitly as display compaction and
retain exact counts outside the plot. Separately define the exact migration
facts: cumulative leader-change sequence for accumulation, and return/terminal
gap distributions for cooling or inactivity. If a local-window hotspot metric
is desired, freeze its window or a multiscale sensitivity before looking at
the result. Do not call cumulative rank a cooling measure. The plan must also
either define the registered transition entropy in the RQ contract or state
that it is intentionally omitted and will not be claimed.

### 5. The frozen source supports only successful resolved file activity, not all source-visible attention or time spent

The RQ1 projection deliberately clears `actions` for failed Tool calls and
marks directory arguments as `scope`. Across the six gzip files, 6,849 calls
have scope actions but no non-scope file action, and 5,933 failed calls have no
exported action. Thus attempted accesses in failed calls and the files actually
examined by directory-scoped search cannot be recovered from these rows. Tool
timestamps also do not establish duration, so access proportions cannot answer
how much wall-clock "time" was spent on a class.

Either re-extract attempted paths from the native source under a separately
frozen rule, or narrow the primary estimand to **successfully resolved,
non-scope file-directed activity in the RQ1 projection**. The latter remains a
useful RQ5 study, but it requires a coverage table containing all
worktree-attributed Tool calls, resolved file-directed calls/actions,
scope-only calls, failed calls with unavailable paths, and vendor/project
strata. Claims must say "share of resolved actions," not total attention,
effort, or time. The current `>=100` gate alone does not address this construct
coverage difference.

### 6. The execution and stopping contract is incomplete

The plan gives neither a runnable analysis command nor raw/result paths,
completion reconciliation, or per-dimension qualification. Add one command,
the exact frozen input directory and cutoff, raw table paths, F8 output paths,
and a completion rule that reconciles action-weighted and Tool-call-weighted
denominators back to the source rows. The existing four-project/100-action gate
should be applied separately to allocation, transition, and revisit dimensions:
undefined dimensions (for example, fewer than two active modules or no eligible
inter-call transition) stay as coverage-only rather than silently entering a
cross-case summary.

## Claim and paper-decision boundary

This experiment can support a **supporting descriptive finding** that the
distribution and movement of successfully resolved file activity differ among
artifact classes and modules in six observed projects. It cannot establish
internal attention, time allocation, artifact importance, productivity,
parallel strategy, forgetting, or a population-level difference among Agents.
The plan should say that a homogeneous result is still informative—it bounds
the value of RQ5 as an additional empirical dimension—while a heterogeneous
result motivates the artifact/module view but does not explain its cause.

## Required disposition

Revise the same plan to resolve the six items above, then return it for round-2
review. These are definition and executability repairs, not requests for more
projects, more baselines, or a broader claim.
