# RQ3 Plan Review — Round 1

**Verdict: BLOCK**

The planned analysis is feasible as a deterministic reanalysis of the frozen
RQ1 CSVs, and its no-threshold concentration view is useful. However, the
current definitions would give a scientifically misleading name to the main
prefix statistic and leave enough degrees of freedom to over-interpret F6.
Those are construct-validity defects, not optional figure polish.

## Blocking findings

### 1. “Expansion” is not observable for left-censored artifacts

The first confirmed mutation observed for an existing artifact does not expand
the workspace. It may itself be the continuation of extensive work before the
observation window. The proposed two-way classification therefore cannot call
every identity's first mutation an **expansion mutation** while also admitting
left-censored identities.

Repair the primary terminology and statistic as one of the following:

- use **first-observed mutation** versus **repeat-observed mutation** for all
  identities; or
- use a three-way decomposition: confirmed-create introduction,
  first-observed mutation of a pre-existing/uncertain identity, and
  repeat-observed mutation.

“Rework” may remain an operational shorthand only if every claim restates that
it means repeat-observed mutation and does not imply waste, failure, or intent.
The evolution panel must not describe the complement as workspace expansion.

### 2. The CCDF denominator is materially ambiguous

“Confirmed mutations per observed artifact identity” implies that read-only
identities with zero mutations are included, whereas a conventional mutation
load CCDF often conditions on artifacts with at least one mutation. The choice
substantially changes the result: the frozen corpus has 7,154 observed artifact
identities but only 2,219 identities with any confirmed mutation. Per project,
zero-mutation identities range from 4 to 2,630.

Preregister the denominator. Prefer showing the unconditional distribution
with the mass at zero stated explicitly and a clearly labeled conditional
CCDF among mutated identities as sensitivity. The eligibility gate must use
the same declared denominator; “10 observed artifacts” is not sufficient if
only a handful are mutated.

The birth-state sensitivity also needs exhaustive handling. The frozen rows
contain `confirmed_create`, `left_censored_existing`,
`unknown_create_status`, and `unknown_rename_source`, not only the two groups
currently named. Unknown groups must be shown, explicitly excluded with counts,
or retained in the all-identity primary curve; they cannot disappear silently.

### 3. A Tool event can emit multiple mutations of one identity

The frozen mutation CSV contains compound Tool events in which one artifact
identity has two confirmed mutation rows at the same `event_index` (for
example, create→rename or a multi-path rename). Under the current “every later
confirmed mutation” rule, the second effect is classified as rework with zero
action/time distance even though no later Agent action occurred.

Define the repeated-work unit as a mutation **episode** keyed at least by
`(project, worktree_id, artifact_id, event_id)` (or justify another exact
source-action key). Preserve the operations within a compound episode as a
multi-label composition rather than treating them as sequential Agent rework.
Then compute inter-episode distance and cross-session repetition. Reconcile
both raw mutation-row totals and collapsed episode totals to RQ1.

### 4. F6 currently permits two unsupported inference labels

A visual CCDF alone does not establish the statistical distribution class
“heavy-tailed.” F6 may defensibly say **right-skewed**, **long upper tail**, or
report exact top-k/cumulative shares. Reserve “heavy-tailed” for a separately
preregistered tail-model analysis with its fitting range and uncertainty.

Likewise, “stabilizes across multiple trailing fractions” is not a
preregistered convergence criterion: the fractions, statistic, equivalence
bound, and project aggregation are all unspecified. Either define all of them
before computation or, more cleanly for this descriptive RQ3 experiment,
prohibit a convergence claim and describe only how the cumulative observed
repeat-mutation fraction changes. Robustness to removing the largest project
does not repair an undefined convergence criterion.

## Required clarifications before PASS

- State the evolution x-axis exactly. Use the frozen native Tool-action
  `event_index` (with wall time as a secondary view or annotation), not merely
  mutation ordinal; otherwise inactive/exploratory action gaps disappear.
- State whether delete/rename composition is over all mutation episodes or only
  repeat-observed episodes, and keep compound-episode operations multi-label.
- Define cross-session repetition only as “different native session IDs” and
  prohibit interpreting it as forgetting or a reset; parallel sessions can
  interleave.
- Name the frozen RQ1 event JSON/session source used for sampled source-link
  verification. The artifact and mutation CSVs are sufficient for the primary
  statistics, but CSV identifiers alone cannot verify the underlying Tool
  effect.
- Make the completion rule require all three panels, exact per-project
  denominators/exclusions, and explicit coverage-only treatment for ineligible
  projects.

## Feasibility and scope judgment

After these repairs, the experiment is executable without a new trace
extraction. The frozen artifact CSV supplies identity, birth/lineage state,
worktree, and aggregate mutation counts; the mutation CSV supplies native
event order, timestamps, session, operation, and source IDs. F6 can then
support a useful but deliberately descriptive finding about mutation-load
concentration and repeat-observed mutation over action time. It cannot by
itself diagnose thrashing, convergence, defect repair, or wasted work, and it
does not answer RQ3's separate validation-followed rework or module-switching
facets.
