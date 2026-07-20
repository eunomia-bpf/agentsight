# Experiment Plan — Rooted Semantic Stack With Transient-Leaf Contraction

**Proposed:** 2026-07-19T22:51:00-07:00  
**State:** Approved by independent Grok 4.5 review; scoped cache migration and
implementation authorized  
**Paper RQ:** **RQ3 — How accurate are the tags?**

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The four RQs remain attribution, localization, tag accuracy, and
cost. The original paper story, opening, motivation, contributions, and
positive RQ3 hypothesis remain fixed.

No CodeTrace stage or score has been opened for any Qwen semantic-stack output.
This plan is motivated only by source-visible behavior: Qwen creates a fresh
leaf on almost every operation, even though a semantic operation is defined as
a temporally extended goal capable of owning several lower-level actions.

## Why A Semantic Operation Exists

Execution structure answers where code ran and which process or tool invoked
which other component. Profiling also needs to answer what goal repeatedly
consumed resources across prompts, tools, files, processes, and runs. A
semantic operation is therefore a run-local goal frame that:

- persists across one or more lower-level actions;
- nests under a variable-depth active task stack;
- owns the conserved additive weight of its descendant actions;
- has a run-local instance identity distinct from its cross-run semantic label.

The operation is not a renamed command. A frame that covers only one raw action
offers no semantic aggregation beyond that action and has no temporal evidence
of being an extended goal.

## One Tested Hypothesis

> On all 405 source-valid failed CodeTraceBench trajectories, adding a permanent
> task root to the fixed local-Qwen single-frame stack and contracting
> single-operation transient frames produces effective leaf-operation
> partitions whose ordinary per-operation B-cubed F1 exceeds the completed
> multi-resolution recurrence, released recurrence, source phase, and raw
> action baselines.

This is one RQ3 mechanism hypothesis. It cannot change the paper-level
hypothesis, story, or RQs.

## Fixed Root And Contraction

The completed V2.3 inference supplies, for every operation, a causal active path
of generated frame instances. The scorer adds one immutable task-root instance
per trajectory, labelled by the same public task-identity text already visible
to inference. It is the ancestor of every generated path and cannot be popped
or replaced.

For every generated frame instance f, define support:

    support(f) = number of trajectory operations whose active path contains f

Retain the immutable root and exactly those generated frames with support at
least two. For each operation, its effective group is the deepest retained
frame on its rooted active path. Removed-frame weight is not dropped; assigning
the operation to its nearest retained ancestor conserves every additive unit.

Because child support cannot exceed parent support, this is equivalent to
bottom-up contraction of transient single-operation leaves and any transient
single-operation chain above them. It does not set a maximum depth. A frame at
depth 20 remains intact if it owns at least two operations; a depth-1 frame is
contracted if it owns only one.

The support threshold is not tuned. Two is the minimum evidence that a frame
organizes more than one raw action and therefore provides profiling aggregation
beyond a renamed action. There is no sweep, score calibration, model judge,
embedding threshold, or target-label feedback.

## Fixed Inputs And Reuse

Use one complete V2.3 prediction for every one of the 20,866 operations. V2.3
uses the fixed Qwen 2.5 3B model, prompt, public task identity, current stack,
preceding observation, current action, seed, temperature, and compact
single-frame grammar registered by Experiment 003.

Valid V2.2 prefix caches may be migrated because v2.3 is a strict grammar
subset and every retained response already passed the same non-empty parser.
Migration is permitted only if a read-only audit proves every raw response is
canonical, legal under v2.3, in source order, and replays to the retained path
and identities. Migrated files record their origin constraint version. The
invalid response was never cached and cannot be reused. All remaining
operations run normally under v2.3. This reuse affects computation only, not
the candidate partition.

## Standard Evaluation

The candidate is the contracted effective-leaf partition. Compare exactly:

1. rooted, contracted Qwen semantic stack;
2. completed multi-resolution recurrence;
3. released recurrence;
4. source phase;
5. raw action.

The primary metric is ordinary unweighted per-operation B-cubed precision,
recall, and F1 over all official flat human stages. Exact adjacent-boundary
precision, recall, and F1 are secondary standard metrics. Report candidate
minus every baseline, a paired 10,000-resample task-cluster bootstrap against
the named multi-resolution recurrence, each framework separately, raw and
contracted group counts, contraction rate, retained depth distribution,
new-frame rate, validity, and model cost.

The uncontracted near-singleton leaf partition is a diagnostic, not a second
candidate arm or an adoption escape hatch.

## Fixed Interpretation

- **Supported and adopted:** contracted candidate B-cubed F1 exceeds every
  baseline, the task-cluster 95% interval against multi-resolution recurrence
  is wholly positive, all four framework effects are non-negative, and all
  inference, migration, contraction, coverage, and isolation checks pass.
  Adoption also requires remeasuring RQ4 construction cost.
- **Promising but not adopted:** point estimate is highest but interval or
  per-framework conditions fail.
- **Contradicted:** candidate does not exceed the strongest baseline.
- **Invalid/incomplete:** any missing operation, illegal/mutated cache,
  leakage, path inconsistency, weight loss, or scoring failure.

Flat stages validate only the effective leaf partition. No outcome authorizes
claims that ancestor labels, exact hierarchy depth, or semantic names are gold
accurate, nor that stack depth alone caused any gain.

## Execution

1. Independently review this source-only plan and the cache-migration proof.
2. Run a fresh four-framework V2.3 preflight.
3. Audit and migrate only byte-valid V2.2 prefix responses, then finish all
   missing V2.3 operations.
4. Freeze complete source-only predictions and materialize rooted contracted
   assignments before the scorer opens stages.
5. Score the complete population once and independently reconstruct metrics.

No paper or release mechanism changes before the registered result review.
