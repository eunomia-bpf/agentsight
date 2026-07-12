# AgentProf Idea Story

Read this file from the first line to the last before any idea-level decision
or paper-level story change. The Initial Narrative is the permanent baseline;
it must remain complete in this current file. The evolution entries record why
each accepted change occurred. The latest entry is not presumed better merely
because it is newer.

## Initial Narrative — Permanent Baseline

**Provenance.** This is the complete scientific narrative from which the
AgentProf project began, reconstructed from the untouched
`docs/agentpprof-paper/main.tex` baseline and the author's original intent. It
preserves the original idea, not every original empirical sentence. Claims
later shown invalid remain identified as original promises rather than current
evidence.

### Problem And Stakes

AI agents perform long, multi-step activities spanning prompts, model calls,
tools, processes, files, and networks. As teams accumulate many trajectories,
the important engineering questions become population-level questions:

- Which recurring kinds of work consume the token, time, or system budget?
- Where do failures and wasted effort concentrate across workflows?
- Which recurring behaviors are associated with unsafe system effects?
- What should a developer optimize, inspect, or constrain across many runs?

Per-run tracing and debugging explain what happened in one execution. They do
not by themselves provide the cross-run aggregation and attribution that
traditional profiling provides for software. The original problem statement
was therefore simple and consequential:

> **Agent observability needs profiling, not only debugging and tracing.**

### Challenged Belief

Traditional profilers attribute additive measures to stable code identities
and runtime call stacks. The original work challenged the belief that an
agent's emitted execution structure is sufficient as the only responsibility
hierarchy for questions about recurring work across heterogeneous runs.
Equivalent behavior may appear under different prompts, tools, sessions, or
runtime boundaries, while one execution tree can mix behavior with different
operational meaning.

The initial paper sometimes stated this too strongly as if agent traces had no
execution hierarchy. The durable challenge was not the absence or uselessness
of native trees. It was that execution occurrence and cross-run profiling
responsibility are different questions.

### Central Insight And Thesis

The fundamental profiling method can transfer from code to agent behavior:
record weighted activities and effects, then attribute the selected measure to
responsible recurring entities at the granularity needed by the question.
Agent trajectories should be treated as profiling samples from a population,
not only as isolated traces.

The original thesis was that a semantic profile can reorganize recorded
activity by reusable task, phase, action, execution, or effect meaning and thus
complement per-run tracing. It was intended to cover cost, regression, safety,
failure, and wasted-work questions rather than one narrow anomaly detector.

### Proposed Model And System

The original model intentionally contained two core abstractions:

1. **Operation:** a uniform, fielded observation of agent activity or effect
   with one or more additive measures.
2. **Operation stack:** an ordered, query-time path derived from operation
   fields and used to fold a selected measure into a hierarchical profile.

Changing selected fields and measures lets the same recorded operations be
viewed by task, phase, action, session, tool, system effect, token count, time,
or another declared dimension. Mappings, taggers, boundary methods, filters,
rankers, importers, pprof serialization, and flamegraph rendering are supporting
mechanisms rather than additional scientific contributions by default.

AgentProf was proposed as an offline profiler that ingests real agent histories
and AgentSight recordings, constructs operation stacks, folds additive
measures, and emits pprof-compatible, folded-stack, JSON, and visual outputs.

### Intended Contributions

The initial narrative promised three contributions:

1. identify the missing cross-run profiling problem in agent observability and
   introduce operations plus query-time operation stacks as a compact model;
2. implement the model in AgentProf with real trace ingestion and standard
   profiler outputs;
3. evaluate whether the profiles faithfully attribute recorded measures and
   help locate real cost, failure, safety, or wasted-work behavior across real
   trajectories and public benchmarks.

### Original Scope And Non-Claims

The ambition was broad across agents, tasks, and additive measures, but the
model was not meant to be a universal causal graph, complete execution ontology,
automatic failure detector, or replacement for per-run debugging. Profiling
and tracing were intended to be complementary. Semantic fields were hypotheses
about useful responsibility, not permission to manufacture signal absent from
the observations.

### Original Research Questions And Evaluation Promise

The first paper organized evaluation around four questions:

1. whether semantic profiling improves resource attribution;
2. whether profiler output corresponds to real annotated problems;
3. whether derived semantic tags agree with held-out annotations;
4. what profiling costs.

It promised real local trajectories, public annotated datasets, hidden-label
problem localization, mapping transfer, and end-to-end profiling cost. The
initial paper reported strong positive numbers. Later audits found that several
positive interpretations were circular, target-guided, incomplete, or broader
than the evidence. Those numbers are historical claims, not current evidence.
The problem, stakes, two-object model, and broad evaluation promise remain the
permanent baseline against which every later story is compared.

## Current Frontier

### Restored Position

Agent traces record where activity occurred in individual runs. Agent profiling
asks which recurring behavior across many runs accounts for a measured cost,
regression, unsafe effect, failure, or wasted effort. AgentProf treats
trajectories as profiling samples and makes the attribution hierarchy explicit
through operations and operation stacks.

> **Agent observability needs cross-run profiling of recurring behavior and
> measured effects, not only tracing individual executions. No emitted or
> semantic hierarchy has automatic authority; the hierarchy used to attribute a
> measure must be exposed and tested against the analyst's decision.**

This restores the original consequential problem. Hierarchy and representation
choice are load-bearing parts of the model and evaluation, not the paper-level
thesis by themselves.

### Scientific Model

The two original abstractions remain the complete core model:

1. an **operation** is a weighted, fielded observation;
2. an **operation stack** is a query-time path used to aggregate a selected
   measure.

Flat summaries, genuine source-native paths, and semantic stacks are competing
projections over the same evidence. Mappings, tags, rankers, importers,
differential comparison, pprof output, and visualizations remain supporting
mechanisms.

### Admitted Evidence And Boundaries

- The Rust artifact implements operation ingestion, mapping, predicates,
  configurable stacks, weighted folding, multiple views, and pprof/folded/
  JSON/SVG output.
- Existing local and public trajectories establish representation reach,
  reprojection, and measure conservation. They do not establish independently
  correct semantic lineage or causal responsibility.
- AgentRx/TELBench invalidates the tested positive semantic-leaf localization
  claim: AP gains over prevalence are small and statistically unresolved, and
  simple controls are stronger in important cases.
- Hodoscope establishes a sparse-anomaly boundary: its published continuous
  density-gap/FPS bundle finds the first oracle action at `2.9 +/- 0.3`, while
  the tested recursive bundle reaches `24.9 +/- 15.8`; adding recursive parents
  has no stable matched advantage.
- A hierarchy attributes a recorded signal; it cannot manufacture a missing
  failure signal. Semantic membership and recursive parents are not automatic
  proof of decision value.

These negative results change the expected answer for their tested hypotheses.
They do not directly challenge the paper-level profiling thesis or authorize
shrinking cost, regression, safety, or failure out of the RQ.

### Current Research Questions

The paper keeps three explicit RQs:

- **RQ1 — fidelity and comparability:** can heterogeneous traces be represented
  and reprojected into flat, source-native, and semantic profiles while
  preserving the declared measure and independently verifiable source context?
- **RQ2 — analytical value:** for real cross-run cost, regression, safety, or
  failure analyses, when does a semantic or differential operation-stack
  profile improve the decision over flat and source-native views under matched
  information and inspection effort?
- **RQ3 — generality and limits:** which workload, query, and projection
  properties predict whether the advantage transfers across agents and task
  families, and when are native structure or simpler grouping sufficient?

These RQs preserve the original scope while repairing its organization. An
experiment tests one hypothesis inside one RQ; it does not rewrite the RQ.

### Competing Explanations

1. Recurring semantic responsibility is the useful cross-run index for some
   measured changes.
2. Any apparent gain comes from extra visible fields or a stronger ranker.
3. Arbitrary or simple grouping supplies the same benefit.
4. Native execution hierarchy is sufficient for the relevant decisions.
5. Different signal shapes and decisions favor different projections.

The current bold hypothesis is that additive changes distributed over recurring
roles across many source trees are the condition most likely to benefit from a
fixed semantic operation stack. Sparse isolated anomalies may favor continuous
flat search, and subtree-local effects may favor native structure. This is a
prediction to test, not an achieved law or new named taxonomy.

### Next Decisive Evidence

First complete the following WRITE gate so the paper expresses the accepted
story. Then reopen `research-literature-novelty` because the restored central
position must be checked against closest work before the next empirical plan.
After that, run one complete RQ2 experiment on a real published agent and
benchmark, using a directly recorded additive regression, genuine native
hierarchy, identical terminal operations and visible information, and only
flat, native, and one semantic stack fixed before target inspection. The result
must connect to an independently meaningful decision and retain all negative,
failed, and nonterminated cells.

If no released dataset contains the required evidence, run two pinned real
agent revisions or configurations on an official benchmark with AgentSight
instrumentation. Do not substitute a toy trace or retune the failed Hodoscope
construction.

## Narrative Evolution — Accepted Changes Only

### E000 — Initial profiling narrative

**Before/after:** project inception; the complete baseline above was the
starting narrative.  
**Reason:** cross-run agent development raised cost, failure, safety, and wasted
work questions that per-run debugging did not aggregate.  
**Root disposition:** accepted as the project objective and two-object system
direction.  
**Comparison:** no prior narrative; it defines the permanent baseline.  
**Revisit:** never remove the baseline; only evidence and current conclusions
may evolve.

### E001 — Evidence-fidelity correction

**Before:** semantic separation, hidden-annotation ranking, mapping agreement,
and offline timing were presented as broad proof that AgentProf improved
attribution and diagnosis.  
**After:** conservation, declared-category separation, independent lineage,
diagnostic correspondence, causality, and end-to-end decision value became
distinct evidence levels; unsupported positive claims were withdrawn.  
**Reason/evidence:** source audits found prompt-derived or hidden-label
circularity, target-time tuning, weak native baselines, and incomplete cost and
lineage evidence.  
**Root disposition:** accept the evidence correction; reject shrinking the
underlying profiling problem.  
**Initial/previous/chosen comparison:** the initial story remained more
important and simpler, while the chosen version became scientifically honest;
the correction improved claim authorization without replacing the thesis.  
**Detail:** [trajectory audit and recovery plan](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/trajectory-audit-and-recovery-plan.md).  
**Revisit:** restore a positive result only through a clean real experiment.

### E002 — Revert reviewer-driven mechanism expansion

**Before:** repeated reviewer attacks had promoted stable identity, semantic
scope trees, navigators, bundle emulation, cost contracts, and large comparator
programs over the original operation/operation-stack center.  
**After:** the accepted story returned to operations and operation stacks as the
only core abstractions; the added mechanisms were demoted to optional techniques
unless later implementation and evidence justified one independently.  
**Reason/evidence:** each objection was treated as a mechanism obligation rather
than classified as a fatal defect, evidence need, optional control, alternative,
or future work.  
**Root disposition:** reject the expanded mechanism-centered narrative and
accept the reversion; retain only independently implemented or experimentally
necessary pieces as supporting techniques.  
**Initial/previous/chosen comparison:** the initial narrative had the clearer
two-object center; the immediately previous expanded version was more defensive
but less simple, less implemented, and less faithful; the chosen reversion was
therefore stronger than the previous version and restored the initial strength
without restoring unsupported empirical claims.  
**Detail:** [trajectory audit and recovery plan](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/trajectory-audit-and-recovery-plan.md).  
**Revisit:** only if a decisive experiment requires one mechanism and the
artifact plus evidence justify it independently.

### E003 — Representation-choice narrative after valid negative results

**Before:** the restored center was cross-run semantic profiling as a complement
to tracing.  
**After:** the paper increasingly centered on flat, native, and recursive
hierarchies as competing profiling indices and on the absence of automatic
hierarchy authority.  
**Reason/evidence:** AgentRx/TELBench and Hodoscope contradicted expected
semantic-leaf and recursive advantages; the project correctly preserved native
baselines and separated signal from grouping.  
**Root disposition at the time:** accept hierarchy choice and signal shape as
important scientific boundaries.  
**Initial/previous/chosen comparison:** this version improved fairness,
closest-work honesty, and negative-result interpretation, but lost the initial
problem's scale by making a supporting comparison the headline. It is retained
as the immediately previous narrative, not the current thesis.  
**Detail:** [post-result full-paper review](tmp/cycle-0001-20260711T164850-0700/03-review-gate/post-result-full-paper-review-20260712T054200-0700.md).  
**Revisit:** representation sensitivity may become central only after repeated
complete matched experiments directly challenge the profiling thesis or show
no useful regime.

### E004 — Restore profiling as the paper-level thesis

**Before:** representation/hierarchy choice occupied the center; the original
profiling problem was present but subordinate.  
**After:** agent observability again needs profiling across recurring behavior
and measured effects, while hierarchy choice remains a falsifiable property of
that profiling model. All valid negative evidence and novelty limits remain.  
**Reason/evidence:** the user's explicit correction and three independent
read-only idea discussions found that local method/workload negatives were not
direct thesis challenges and that the submodule's problem framing had greater
scientific potential.  
**Root disposition:** accept the combined restoration; reject restoring
unsupported old results; defer paper changes to WRITE.  
**Initial/previous/chosen comparison:** the initial story supplies importance,
simplicity, and ambition; the previous story supplies scientific discipline;
the chosen story combines both and is therefore stronger and more faithful than
either alone.  
**Idea audit:** [root disposition](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-story-restoration-20260712T134029-0700/500-idea-audit-20260712T140000-0700.md).  
**Revisit:** only a direct thesis challenge—not one local negative result,
reviewer objection, or unavailable dataset—can reopen the paper-level center.

## Invariants For Every Future Story Decision

- Read this entire file, including the Initial Narrative and every evolution
  entry, before deciding.
- Compare the initial, immediately previous, and proposed narratives explicitly;
  recency is not evidence.
- Preserve the largest faithful problem and use bold hypotheses with careful
  validation. Negative results change tested answers or search branches before
  they change the paper-level objective.
- Keep operations and operation stacks as the only core abstractions unless
  implementation and decisive evidence justify a genuine new abstraction.
- Prefer one simple, non-obvious principle over stacked terminology.
- Use real papers, benchmarks, systems, datasets, and complete experiments.
- Record every accepted problem, thesis, contribution, system-direction, scope,
  or RQ change here with before/after meaning, reason, evidence, root
  disposition, comparison, report link, and revisit condition.
- `iter-refine-ideas` proposes; the root records a disposition; the WRITE gate
  alone changes the paper.
