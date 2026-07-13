# Post-Result Idea Discussion — Round 1: Problem and Research Direction

**Timestamp:** 2026-07-12T04:48:46-07:00  
**Method:** independent read-only synthesis under `iter-refine-ideas` Round 1  
**Result input:** valid run; expected recursive advantage contradicted

No files, skills, paper text, or Git state were changed by the discussant.

## Largest Faithful Idea

The largest defensible AgentProf idea is not that a recursively organized
semantic profile will beat every flat or execution-derived view. The larger
idea is that an agent trace's recording structure is not automatically the
right structure for analyzing behavior across runs.

Agent systems record events according to execution: trajectories, spans,
turns, tool calls, processes, and local nesting. Profiling asks a different
question: under what recurring unit should an observed measure—time, tokens,
retries, unsafe effects, failures, or changed behavior—be aggregated so that an
analyst can make a decision? Those structures sometimes coincide, but there is
no reason to assume they always do.

> Agent traces are evidence, not a canonical profiling index. Profiling an
> agent requires choosing both the measure and the hierarchy by which that
> measure is aggregated. That hierarchy may be source-native, flat, or
> semantic, and its value must be established for the question rather than
> inherited from the trace format.

This preserves the challenge to execution-tree primacy without replacing it
with an equally unjustified universal semantic tree. The Hodoscope result makes
this position more consequential: apparently reasonable analyses over the same
actions change first-hit effort by more than an order of magnitude.
Representation is not neutral presentation after analysis; it partly
determines what an analysis can reveal.

AgentProf's two abstractions still fit this position. An operation provides a
common evidence record and declared measure. An operation stack makes one
hierarchical profiling choice explicit and replayable. Its scientific role is
to compare recursive aggregation with alternatives and expose when a result
depends on an unexamined hierarchy, not to win every benchmark.

## What the Hodoscope Result Establishes

This is a valid negative condition for RQ2. The official Hodoscope
implementation reproduced its published behavior and found an iQuest
oracle-positive action at rank 2.9 +/- 0.3 in the ten-seed sampled protocol.
The recursive view reached rank 24.9 +/- 15.8. Hodoscope won on all ten paired
seeds; recursive-minus-Hodoscope was +22.0 with a paired-bootstrap interval of
[12.3, 31.8]. On the complete corpus, Hodoscope reached rank 3.0 while the
recursive view averaged 76.3.

> For this sparse action-level cohort anomaly, the official Hodoscope analysis
> bundle surfaces the published effect decisively earlier than the tested fixed
> recursive semantic bundle.

The tested recursion is also not reliably better than its matched alternatives.
Flat and recursive use exactly the same terminal fine clusters, so their
comparison isolates recursive parents under the common excess-mass,
max-over-path, and FPS rule. Recursive point estimates are better than flat in
both phases, but paired intervals cross zero and win rates are only 0.5 and
0.7. The turn-position grouping likewise shows no stable recursive advantage.

Together with AgentRx/TELBench, the paper now has two complementary warnings:

1. Naming or inducing semantic groups does not manufacture a missing
   diagnostic signal.
2. Adding a recursive hierarchy to a semantic partition does not automatically
   concentrate a real signal better than flat or continuous alternatives.

These reject two tempting assumptions that could otherwise make a semantic
profiler scientifically shallow.

## What the Result Does Not Establish

The result does not establish that flat representations generally beat
recursive ones. Hodoscope differs in both representation and scoring: it uses
continuous semantic coordinates, KDE density contrast, and its published FPS
procedure. The complete Hodoscope bundle beats the complete tested hierarchical
bundle, but the current run cannot assign that gap specifically to flatness,
continuous geometry, KDE, normalization, or an interaction.

The matched flat-versus-recursive comparison is the hierarchy isolation, and
it is inconclusive rather than a flat victory. The supported statement is that
recursive parents produced no stable benefit over the matched terminal
partition.

The result does not establish native-tree sufficiency. The native baseline
groups exact released `turn_id` values across trajectories. It tests shared
turn position, not the full `trajectory -> turn -> tool/action` tree, and
cannot answer the larger challenge to execution nesting.

The result also does not establish end-to-end cost. Per-method times cover
construction and ranking after shared t-SNE. Actions and characters inspected
are valid decision-effort measures, not complete capture, preprocessing, model,
query, human-review, or deployment cost.

The Phase B seed-range deviation and placeholder Hodoscope `contrast: 0.0`
metadata must be disclosed or corrected, but neither changes ranking or the
scientific conclusion.

## Falsified Mechanism

The experiment falsifies the expectation that the following fixed construction
is a reliable route to recursive advantage:

- reference-only 8/32/128 nested MiniBatch K-Means;
- target assignment through those discrete centroids;
- excess target mass at every node;
- maximum contrast over an action's path;
- the common FPS action ordering.

The mechanism failed the prespecified rule against every required baseline. It
must not be retuned on the same labeled condition and presented as confirmation.
More generally, recurring semantic membership alone does not make a hierarchy
analytically useful. A hierarchy helps only if the measured effect is
meaningfully aggregated by its parents and that aggregation improves the
decision. A mechanism and expected answer failed in one condition—not the RQ,
the operation model, or the challenge to canonical execution nesting.

## Larger Insight

Agent observability currently conflates three structures:

- where an event occurred during execution;
- which recorded behavior is similar across runs;
- how evidence should be aggregated for a particular decision.

Execution trees naturally serve the first. Hodoscope's continuous semantic
comparison is strong for the second in this benchmark. A recursive profile is
intended for the third by accumulating an additive measure under reusable
groups. None is guaranteed to substitute for another.

The Hodoscope task rewards early discovery of one sparse action. It favors
preserving local distinctions and precise point ranking. Recursive aggregation
can help only if an anomaly is distributed across related descendants strongly
enough that a parent exposes signal that leaves fragment. That condition was
not established here.

> The useful profiling hierarchy is determined by the shape of the measured
> change, not merely by the semantics of recorded actions.

A sparse action anomaly, phase-wide token regression, repeated retries, and a
system effect distributed across tools need not share the same best index. This
keeps the paper ambitious: it asks for a general account of representation
choice, not a single favorable win.

If credible views produce materially different conclusions, the instability
itself shows dependence on an unverified representation assumption. AgentProf
can make that assumption visible. The contribution is not that a semantic tree
is the new correct tree, but that no tree is universally privileged and profile
choice must be explicit and tested.

## Live Explanations

### The effect may be at the wrong scale for recursion

The oracle is sparse and action-local. Recursive aggregation may better match
additive effects distributed across a recurring task or phase: excess tokens,
retries, repeated tests, or a version regression spanning many actions. This is
a prediction within the existing cost, regression, safety, and failure scope,
not permission to narrow RQ2. A future test should use a real recorded change
whose mass naturally spans multiple operations and compare full source-native,
flat, and semantic views over the same measure.

### Hodoscope's scorer may matter more than flatness

Continuous density comparison may preserve a localized cohort difference that
the fixed clusters and excess-mass rule blur; normalization or FPS interaction
may instead be decisive. A future comparison could hold the action-level
cohort signal fixed and ask whether recursive aggregation helps review. It must
not be an immediate retune to win the observed oracle.

### Hierarchy may help explanation after discovery

First-hit rank rewards discovery. A recursive profile might instead explain
how related operations, trajectories, costs, or effects participate once a
difference is known. This does not erase the failed metric; it identifies a
separate question about discovery versus responsibility attribution.

### Representation sensitivity may be first-class evidence

The large divergence among Hodoscope, flat clusters, turn positions, and
recursive clusters shows that conclusions depend strongly on representation.
A paper can report findings stable across views and findings that reverse. This
challenges the belief that hierarchy is mainly a visualization choice and
requires no new abstraction.

## Important Unasked Question

> What observable property of a real analysis signal determines whether flat,
> source-native, continuous semantic, or recursive semantic profiling is most
> useful?

Candidate properties already implicit in RQ3 include:

- isolated versus distributed effect;
- recurrence across trajectories with different execution paths;
- additive measure versus sparse Boolean label;
- alignment between source boundaries and affected behavior;
- target coherence of semantic groups learned from earlier runs;
- one-scale versus multi-scale evidence.

A strong research program would span these properties with real benchmark
conditions and test whether they predict the winning representation.

## Consequences for the Paper

- RQ2 is no longer simply unanswered. One condition is answered negatively:
  the tested hierarchy does not improve sparse iQuest action discovery, while
  the official Hodoscope bundle is decisively stronger.
- RQ2 remains broad because cost, regression, safety, and failure signals have
  different shapes. The result constrains the answer; it does not redefine the
  question.
- RQ3 becomes more central because it asks when each representation is
  sufficient. Hodoscope supplies one real point, not a smaller paper.
- RQ1 remains about faithful evidence and comparable projection; this result
  neither proves nor refutes independent lineage.

The abstract, introduction, evaluation, and conclusion must replace future
tense with the completed result. They must not say flat beats recursive,
continuous geometry is causal, native trees are sufficient, or AgentProf is
cheaper. They may say that Hodoscope's official bundle decisively beats the
tested recursive bundle, while flat-versus-recursive and
recursive-versus-turn-position differences are unstable.

The strongest contribution architecture is:

1. agent profiling is a representation choice because execution structure and
   cross-run analytical responsibility differ;
2. AgentProf makes weighted evidence and question-selected hierarchical
   projection explicit in a working profiler;
3. real results show both the reach and danger of that choice: different
   projections preserve the same evidence yet produce materially different
   groupings and decisions, while two tempting semantic shortcuts fail.

This preserves the required ambition, keeps the two-abstraction model simple,
uses real public evidence, and records uncertainty without waiting for human
intervention.
