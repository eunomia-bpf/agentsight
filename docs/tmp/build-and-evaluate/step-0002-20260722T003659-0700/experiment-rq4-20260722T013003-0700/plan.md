# RQ4 Experiment Plan — Cross-Session Continuity

**Created:** 2026-07-22T01:30:03-07:00  
**State:** preregistration draft; no RQ4 statistic has been computed

## 1. Question and boundary

RQ4 asks what observable work occurs when one source-session concurrency
episode is followed by another in a persistent workspace: how long until the
first mutation, what prior artifacts/modules are revisited first, and how much
mutation continues earlier work. Frozen sources do not portably identify
top-level versus child-agent roles, so this experiment cannot estimate an
independent session-reset tax or make resume, memory, comprehension, or
forgetting claims. It supplies the source-session continuity facet only and
cannot alone close canonical RQ4.

## 2. Frozen source and boundary eligibility

Reuse the authoritative RQ1 event and mutation rows at cutoff
`1784708569241`. Analyze native session identity, never prompt boundaries or
Git commits. For each worktree, order sessions by first timed Tool action.

For each `(project, worktree_id)`, construct each source-session interval from
its first/last worktree-attributed Tool action. Same-timestamp endpoints count
as overlap. Collapse the transitive closure of overlapping intervals into a
**concurrency component**. An eligible boundary connects two adjacent,
non-overlapping components; predecessor artifacts/modules are the union over
the entire preceding component. A source session touching multiple worktrees
produces worktree-specific observations linked by the same session ID; no
action-level resampling or independence claim is made. Long inactive gaps
remain observable wall time; no maximum gap is imposed.

For every eligible next component:

1. record worktree-attributed action steps and wall time to its first confirmed
   mutation; separately report the observed no-mutation component fraction.
   Conditional first-mutation ECDFs include only components with an observed
   mutation and make no survival extrapolation;
2. classify every pre-mutation Tool event exclusively by highest priority:
   exact predecessor artifact identity; predecessor module but not artifact;
   other resolved non-scope artifact; other resolved directory scope; or no
   resolved repository path. Multi-path events take their highest-priority
   class;
3. among unique mutated identities and unique mutated modules in the next
   component, report overlap with the predecessor component's unique accessed
   identity/module sets. A next component without mutation or a predecessor
   with an empty relevant set is N/A, not zero; and
4. classify the first mutation identity exclusively as: mutated in the
   predecessor component; accessed but not mutated there; observed only in
   earlier history; confirmed-success create in the next component;
   first-observed existing/left-censored; or unknown lineage.

Unresolved paths stay in action coverage but not artifact-overlap denominators.
Module is the first action-time relative path component; root-level files use
`repo-root-files`, never `/` or `(root)`.

Pre-mutation reads receive stable identity through a deterministic replay of
the frozen event actions. Replay every resolved non-scope action in exact
event/action order using RQ1's lifecycle semantics: an action can introduce a
left-censored identity; same-worktree rename preserves lineage regardless of
status; delete closes the live identity; and a later create at that path starts
a new identity. Scope rows may observe but never create an identity. Reconcile
the replay's artifact creation tuple against every RQ1 artifact row's
`first_event_index/first_path`, and reconcile every confirmed mutation to its
RQ1 artifact ID. Export every resolved access with source `event_id`, replayed
artifact ID/module, operation and scope; a path-string join alone is prohibited.

## 3. Figure F7

- **Panel A — time to first mutation:** observed no-mutation component fraction
  plus conditional ECDFs of exact worktree-attributed action steps to first
  mutation. No-mutation components are terminal descriptive outcomes, not
  right-censored samples.
- **Panel B — re-grounding composition:** per-project distributions of
  pre-mutation actions partitioned into prior-artifact revisit, prior-module
  access, other resolved artifact access, and unresolved/no-path action.
- **Panel C — component continuity:** per-boundary distributions of unique
  mutated-artifact and mutated-module overlap, plus the six-state first-mutation
  classification. Eligible, undefined and concurrency-component counts are
  printed.

No arbitrary 24-step window or “30-second summary” enters the metrics. If the
figure uses normalized session progress for presentation, exact action-step
distances remain the primary axis and table.

## 4. Verification and stop rules

- Implement one command:

  ```bash
  python3 agentvis/research/plot_rq4.py \
    --rq1-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw \
    --output docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq4-20260722T013003-0700
  ```

  It directly verifies the frozen RQ1 gzip/CSV hashes, writes
  `raw/rq4-accesses.csv`, `rq4-components.csv`, `rq4-boundaries.csv`, and
  `rq4-prefix-actions.csv`, then rereads those rows to render
  `figures/rq4-component-continuity.pdf/.png`.
- Reconcile native sessions, unique worktree-attributed actions, mutation rows,
  artifact IDs and replayed lifecycles with RQ1. Unit-test transitive overlap
  (`A=[0,100], B=[10,20], C=[30,40]`), same timestamps, multiple worktrees,
  no mutation, empty predecessor sets, multi-path priority, rename,
  delete--recreate and every first-mutation state.
- Apply the 20-boundary/4-project gate separately to conditional timing,
  resolved prefix composition, artifact overlap, and module overlap. Undefined
  denominators never qualify. If a panel fails, draw source coverage and
  within-case rows only; do not weaken the gate.
- Because top-level/parent roles are unavailable, stop resume/reset
  interpretation regardless of numerical coverage. Do not describe a long
  prefix as waste or forgetting, or infer continuity from path-string
  similarity across identity breaks.

Independent plan and result reviews are required before F7 enters the paper.
