# Round 1 — Problem And Research Direction

**Timestamp:** 2026-07-12T13:41:41-07:00  
**Parent:** REVIEW gate / `idea-story-restoration-20260712T134029-0700`  
**Status:** complete, read-only discussion

## Entry And Method

The central question was: **What is the largest, most interesting, and most
faithful version of the author's idea?** The discussant read the complete
`docs/user-instruction.md`, `docs/idea-story.md`, current paper, untouched
submodule paper, and the evaluation, related-work, design, and implementation
frontiers from entry snapshot `20260712T134029-0700`. It made no edits, ran no
Git commands, and received no other round's verdict.

## Interpretation

The strongest faithful position is not that a recursive semantic hierarchy
always beats an execution hierarchy, and not merely that hierarchy is a
representation choice. It is that **agent traces are samples rather than
profiles**. Agent observability needs population-level profiling that attributes
real measured cost, regressions, unsafe effects, and failures to behavior that
recurs across runs. An execution tree records where events occurred; it is not
automatically the responsibility structure for every cross-run decision.

AgentProf makes this position concrete with two load-bearing abstractions: a
weighted, fielded operation and a query-time operation stack. The stack is an
enabling mechanism, not the paper's whole contribution. Flat, source-native,
and semantic views remain competing ways to attribute the same evidence.

## Initial, Previous, And Proposed Narratives

The original submodule narrative did best at stating a consequential problem:
developers must find which recurring work consumes budget, concentrates
failures, or produces unsafe effects across many runs, while existing tracing
primarily explains one run. It made the profiling-versus-debugging distinction
memorable and kept the model simple. It also overclaimed: prompt-defined
separation was treated as correct attribution, hidden labels entered ranking,
and the paper stated diagnostic wins not supported by a fair protocol.

The immediately previous narrative repaired those scientific defects. It
preserved native trees as real baselines, separated accounting from diagnosis
and causality, admitted the AgentRx/TELBench and Hodoscope negative results, and
kept only operation and operation stack as core abstractions. But it allowed a
supporting representation comparison to replace the larger profiling problem.
The system consequently read as apparatus for comparing hierarchies rather
than as a profiler for recurring agent behavior and effects.

The proposed narrative combines the original ambition with the current
evidence discipline: modern agent engineering decisions concern recurring
behavior across populations of runs; AgentProf treats trajectories as
profiling samples and folds the same recorded measures under explicit flat,
native, or semantic contexts; no hierarchy has automatic authority, so its
decision value must be tested. This is a better research direction, but it is
not yet an achieved positive empirical conclusion.

## Unexpected Directions And Missing Question

Two valuable branches were identified. First, evaluate profile-guided
intervention rather than only inspection: does a profile lead to a change that
actually recovers cost, quality, or safety? Second, treat disagreement among
plausible profiles as observability uncertainty: a conclusion visible under
only one projection is representation-sensitive. A longer-term branch is to
keep the model useful beyond human-readable intent labels by remaining
measure-first rather than ontology-first.

The important unasked question is whether acting on the selected profile leads
to a better real intervention than acting on flat or source-native views,
without moving the problem elsewhere.

## Constraints, Evidence, And Next Action

The proposal preserves the current three RQs, the broad cost/regression/safety/
failure scope, all admitted negative evidence, the two-object model, target
label isolation, and the requirement for real complete experiments. It rejects
restoring the unsupported 90% attribution, 9.4% localization, and 7/9 tag claims
as proof of decision value.

The next decisive evidence should be one complete RQ2 experiment on a real
agent workload with a genuine before/after comparison, a directly recorded
additive signal, a real source hierarchy, identical operations and visible
information across flat/native/semantic views, and a benchmark-native or
independently verifiable decision. The semantic mapping must be fixed outside
the target result.

