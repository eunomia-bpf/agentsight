# Idea Discussion Round 2 — Academic Architecture

**Completed:** 2026-07-12T16:48:46-07:00  
**Mode:** fresh read-only `iter-refine-ideas` discussion  
**Files read:** project instructions, verbatim user log, complete idea story,
both complete papers, and current design, implementation, and evaluation docs  
**Mutations:** none

## Derived Architecture

The thesis implies a population-level attribution method: preserve recorded
evidence, declare selected operations, additive measure, and responsibility
hierarchy, conserve the measure, retain native drilldown, and then test whether
the profile improves an independent engineering decision.

- An operation is a fielded, weighted observation, not a causal claim.
- An operation stack is a query-time attribution path that generalizes the
  profiling role of a call stack without replacing native structure.
- The contributions remain the missing profiling problem and compact model,
  the AgentProf implementation, and empirical evidence about fidelity,
  decision value, transfer, and limits.
- The three fixed RQs organize fidelity, real analytical value, and transfer.
  Cost belongs to RQ2 because it is meaningful only relative to value.

## Difference from the Submodule

The submodule's motivation and two-object system story are preserved. Its
claims that operation stacks replace runtime structure, intent labels act like
stable function identities, AgentSight trigger lineage is directly recovered,
and hidden labels close the paper are rejected. Mappings and induction are
field producers, not contributions. Current negative evidence is retained, but
the third contribution must not shrink to “two mechanisms fail.”

## New Directions and Question

Before/after regression profiling is a closer analogue to classical profiling
than generic hidden-failure localization. A profile should be judged by the
intervention it enables. The key unasked question is whether a profile can
support the correct intervention even when its semantic labels do not match a
canonical human taxonomy.

## Next Experiment

On one published agent and official benchmark, compare the same tasks under two
pinned versions/configurations with a recorded additive regression. Fold
identical operations through flat, native, and one unchanged semantic stack.
Measure effort to find the independently documented changed behavior and
whether the resulting intervention recovers cost without degrading official
task success. Run the full matrix and retain failures and null cells.

