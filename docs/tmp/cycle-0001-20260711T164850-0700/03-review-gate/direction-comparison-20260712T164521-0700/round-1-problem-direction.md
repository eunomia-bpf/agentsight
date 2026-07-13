# Idea Discussion Round 1 — Problem and Direction

**Completed:** 2026-07-12T16:45:21-07:00  
**Mode:** fresh read-only `iter-refine-ideas` discussion  
**Files read:** project instructions, verbatim user log, complete idea story,
complete untouched submodule paper, and complete active paper  
**Mutations:** none

## Interpretation

The largest faithful direction is the exact author-fixed thesis:

> **Agent observability needs profiling, not only debugging.**

Agent trajectories are not only executions to inspect individually; across
runs, releases, configurations, and workloads, they are samples from a
behavioral population. Profiling attributes measured aggregate consequences —
cost, regression, unsafe effects, failure, and waste — to recurring responsible
behavior. Hierarchy comparison is subordinate to this problem.

Operations and operation stacks remain the only two core abstractions. Tags,
mappings, clustering, induction, rankers, differential comparison, and output
formats are replaceable mechanisms.

## Submodule Comparison

The untouched submodule states the important missing-profiling problem more
forcefully, but it often says agents lack useful execution hierarchy, treats
semantic categories as the responsible entities, and presents operation stacks
as replacing runtime stacks. It also turns category separation, tuned hidden-
label ranking, and incomplete cost measurements into broad positive evidence.

The active direction preserves the thesis and model while recognizing native
structure as evidence and a strong baseline. Flat, source-native, and semantic
views are hypotheses over the same observations. Conservation, declared
category separation, correct lineage, diagnostic correspondence, transfer,
decision value, and cost are distinct evidence levels.

## Unexpected Directions and Unasked Questions

- Profile a real regression between agent releases or configurations.
- Evaluate whether the profile enables an intervention that removes measured
  cost or failure without reducing task success.
- Test stability under behavior-preserving execution changes.
- Ask what makes AgentProf more than path-key `GROUP BY` plus pprof output; the
  answer must be an end-to-end population-level decision, not another name.

## Next Evidence

Run one complete RQ2 experiment in which a fixed semantic operation stack
attributes a directly recorded additive regression across heterogeneous real
agent runs relative to flat and genuine source-native projections. Use a real
agent, official benchmark, pinned releases/configurations, identical evidence,
an external quality constraint, and an intervention or held-out attribution
check.

