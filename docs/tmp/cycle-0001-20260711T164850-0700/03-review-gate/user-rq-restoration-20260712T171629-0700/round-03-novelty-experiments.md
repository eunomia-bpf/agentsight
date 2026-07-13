# Round 3 — Novelty, Experiments, And Results

**Completed:** 2026-07-12T17:31:51-07:00  
**Parent:** `user-rq-restoration-20260712T171629-0700`  
**Mode:** fresh independent read-only discussion  
**Inputs:** complete user log, idea history, current and untouched papers and
bibliographies, literature frontier, evaluation frontier, admitted RQ2 reports,
and Hodoscope summaries  
**Actions:** no edits, Git, compilation, browsing, experiments, or access to
Rounds 1--2

## Interpretation And Narrative Comparison

The strongest faithful direction remains:

> **Agent observability needs profiling, not only debugging.**

AgentProf tests whether populations of agent trajectories can be treated as
profiling samples whose additive measures are attributed to recurring
responsible behavior. Operations and query-time operation stacks remain the only
core abstractions. The fixed evaluation architecture is:

1. RQ1 attribution: Does semantic profiling improve resource attribution?
2. RQ2 localization: Does profiler output correspond to real problems?
3. RQ3 tag accuracy: How accurate are the tags?
4. RQ4 cost: What is the profiling cost?

Flat, source-native, and semantic views are controls inside experiments; they do
not replace these questions.

The Initial Narrative is strongest in problem importance, the profiling transfer
insight, conceptual economy, and the direct chain from attribution through
localization and tag validity to practical cost. Its weakness was evidence
authorization: circular category truth, target-informed localization,
mismatched tag oracles, incomplete timing, and overstatement about native
hierarchies.

The immediately previous narrative repaired those defects through conservation
versus lineage, genuine baselines, label timing, matched evidence, and honest
mechanism results. It lost the larger paper by replacing the four RQs with
controls and limits, folding cost into analytical value, dropping tag accuracy,
and promoting negative intermediate mechanisms into the headline.

The proposed narrative restores the exact thesis, four RQs, and positive
hypotheses while retaining every experimental control learned from failed
studies. Failed induced leaves and the Hodoscope adapter remain auditable history
and mechanism lessons. They need not occupy the final paper when a materially
different stronger method supplies the final evidence. The final paper must not
present the unchanged failed mechanism as broadly positive while omitting its
contradiction.

## Closest-Work And Novelty Boundary

Mechanism-level novelty is crowded:

- domain-specific profiling already builds hierarchical models from selected
  dimensions;
- pprof represents weighted stacks and tag-derived frames;
- Perfetto supports derived events and query-time aggregation;
- Pivot Tracing supports cross-layer query-time attribution;
- aggregate-trace work combines many traces;
- differential flame graphs establish a before/after regression protocol.

Weighted records, field grouping, query-time hierarchy, pprof output,
flamegraphs, and differential aggregation are not individually novel. An
OpenTelemetry + Perfetto SQL + pprof reconstruction is a credible reviewer
baseline.

Hodoscope is the closest agent-specific threat because it already performs
semantic comparison across agent cohorts. AgentDiagnose limits semantic
trajectory visualization claims; ARIA limits semantic projection plus additive
aggregation; Datadog and Laminar supply product-level semantic grouping; and
AgentRx, TELBench/DRIFT, TrajAD, AgentFixer, SDBL, Who&When, and TRAIL block a
generic first-localization claim.

The current verified handoff contains no full precedent for the complete paper:
profiling recurring agent behavior across runs, attributing multiple additive
measures through explicit query-time responsibility stacks, and validating
attribution, real-problem localization, tag accuracy, and end-to-end cost. This
is not enough for a safe “first” claim; `research-literature-novelty` must search
recent observability products and OpenTelemetry-based agent analytics.

The defensible novelty is the position plus evidence: whether cross-run profiles
of recurring agent responsibility enable real decisions that per-run traces and
ordinary semantic grouping do not.

## Positive Hypotheses And Current Evidence

### RQ1

**Hypothesis:** a semantic profile attributes recorded token, time, and system
effects to recurring task/phase/action responsibility more faithfully and
usefully than flat or per-run/native organization while conserving measure and
preserving independent lineage.

**Current evidence:** implementation, conservation, and declared-category
separation only—not correct attribution.

### RQ2

**Hypothesis:** a differential semantic operation-stack profile localizes a real
distributed agent regression with less inspection than flat and native profiles
and identifies an intervention that removes the regression.

**Current evidence:** two exact mechanisms failed under different conditions;
neither answers this additive-regression/intervention hypothesis.

### RQ3

**Hypothesis:** a frozen tagger or mapping assigns stable semantic tags and
boundaries accurately on unseen agents/families, and errors do not materially
corrupt resource attribution.

**Current evidence:** mapping proxy with an uncertain oracle and an inconsistent
six/seven-of-nine summary—not a complete answer.

### RQ4

**Hypothesis:** complete profiling has practical predictable near-linear cost
that is small relative to execution and repeated trace review.

**Current evidence:** component timings show the implementation runs, not full
end-to-end cost.

## Four Complete Experiments

### RQ1 — Independent Resource Attribution

Run a real published agent on an official benchmark while collecting native
agent spans and independent AgentSight process/tool evidence. Benchmark task IDs
establish task ownership, native tool/span IDs establish execution ownership,
and AgentSight process/file/network events establish low-level effect lineage.
Freeze the task/phase/action mapping on development tasks.

Give flat, genuine native `trajectory -> turn/span -> tool`, and one fixed
semantic stack identical operations and measures. Measure lineage precision and
recall, unassigned/duplicate effects, weighted attribution error for tokens/time/
process/file/network measures, fragmentation of recurring responsibility,
category ranking agreement, and mass conservation. A positive result requires
lower independent attribution error or fragmentation, not merely purer groups.

### RQ2 — Real Regression And Intervention

Use a released real agent, official benchmark, and published or independently
verifiable configuration/version change that produces a distributed additive
regression. Differential flame graphs are the published protocol precedent. The
exact pair must be selected by literature/source search rather than guessed.

Run the same tasks under pinned reference and target conditions, same model,
budgets, and seeds where supported. Record tokens, time, retries, tool calls,
processes, and file/network effects. Use development tasks only to establish the
regression and freeze one semantic stack; confirm on untouched tasks.

Compare identical terminal evidence through flat differential operations,
genuine native hierarchy, and one unchanged semantic operation stack with the
same signed paired score and inspection accounting. The primary outcome is raw
operations or characters inspected before the independently known responsible
behavior. Supporting outcomes are excess mass explained at fixed effort and,
most importantly, a held-out intervention that removes substantial excess
without unacceptable task-success loss. Complete all tasks, seeds, timeouts, and
nonterminations.

Hodoscope remains the strongest cohort-anomaly baseline but need not be forced
into an additive-regression protocol it was not designed for. If no released
pair is accessible, run two pinned official configurations of a real agent on an
official benchmark; do not inject a toy trace.

### RQ3 — Held-Out Tag Accuracy And Consequence

Choose one plain fixed tag vocabulary used by the profiler and verify ontology
compatibility with published annotations before admitting datasets. Develop and
freeze the tagger/mapping on several families; leave out both a dataset and,
where possible, an agent/model family. Join target labels only after
materializing tags and boundaries. Report macro-F1, V-measure, boundary P/R/F1,
abstention, coverage, per-category performance, and relevant baselines.

Replace predicted tags with oracle tags and quantify changes in RQ1 totals and
rankings, measuring whether errors matter operationally. If no public ontology
matches, use independent blinded expert annotation with a published protocol
rather than coercing low-level actions into semantic truth.

### RQ4 — End-To-End Cost

Measure parsing, field derivation, uncached/cached tagging, stack construction,
folding, serialization, storage, and capture separately when AgentSight is in the
evaluated path. Use complete naturally occurring real corpora at several sizes,
recorded hardware/software, release builds, cold/warm caches, wall/CPU time,
peak RSS, accelerator/model tokens, storage, and output size. Report cost as a
function of operations, text, cache misses, stack depth, and output cardinality.
Give Perfetto/pprof equivalent preprocessed fields when using them as cost
baselines.

## When Evidence Would Genuinely Endanger A Hypothesis

One failed dataset or constructor limits a mechanism. The semantic-localization
hypothesis becomes genuinely endangered only after at least two independent
real additive-regression experiments use a published agent/benchmark, genuine
native hierarchy, identical information and effort, pre-target fixed mapping,
independent causal ground truth, complete execution, and confidence intervals
excluding a meaningful semantic benefit. Another leaf or clustering variation
after two such failures would no longer be justified.

Even then, the thesis need not shrink. An ambitious mechanism replacement would
derive responsibility from interventions and measured effects rather than
semantic similarity alone. Repeated RQ3 failure would motivate query-specific,
source-declared, or intervention-derived identities. Prohibitive RQ4 cost would
motivate incremental maintenance. None changes the exact thesis.

## Unexpected Directions

### Profiling As An Optimization Interface

The strongest evidence is a profile-selected tool policy, retry rule, model
route, or workflow intervention that reduces measured cost or unsafe effects
without lowering success. This creates causal engineering evidence without a
new abstraction.

### Agent-Profile Regression Testing In CI

Frozen operation stacks compare model, prompt, tool, or agent revisions over the
same tasks and identify recurring regressions that individual trajectories
fragment.

### Machine-Consumable Profiling

For increasingly capable agents, the profile can feed a controller selecting an
intervention, budget allocation, or safety target. Resource reduction and causal
repair remain measurable even when a human cannot inspect the full trace.

## Important Unasked Question

> **What concrete intervention follows from the top AgentProf frame, and what
> shows that a different frame would lead to a worse intervention?**

This makes the four RQs complementary: attribution says where measure belongs,
localization says what to change, tag accuracy says whether the frame means what
it claims, and cost says whether the method is practical.

## Target Locations And Next Evidence

- `docs/idea-story.md`: retain the Initial Narrative, append a restoration entry,
  restore the exact four RQs and positive hypotheses, and supersede rather than
  delete the three-RQ frontier.
- `docs/evaluation.md`: restore four current rows, retain negative reports in
  historical branches, and make real additive-regression RQ2 the active branch.
- `docs/paper/main.tex`: next WRITE restores four RQs in Abstract, Introduction,
  Contributions, Evaluation, Discussion, and Conclusion; it does not invent
  results or add named machinery.
- `docs/background-related-work.md`: retain current threats and add the verified
  real revision/config pair and published protocol selected for RQ2.

The immediate empirical gap is an accessible published agent revision or
official ablation with a known reproducible additive regression and preserved
native hierarchy. Route that precise question to `research-literature-novelty`.
SWE-agent/SWE-bench is the strongest candidate family in current materials, but
the exact pair must be verified. If it fails, search another published coding or
tool agent rather than using a toy or retuning Hodoscope.

Researchers will believe the direction when a semantic profile changes a real
intervention under matched evidence, not when it merely produces a different
hierarchy.
