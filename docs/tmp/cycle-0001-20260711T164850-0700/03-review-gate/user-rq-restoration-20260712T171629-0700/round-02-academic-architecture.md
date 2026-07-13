# Round 2 — Academic Architecture And System Direction

**Completed:** 2026-07-12T17:24:52-07:00  
**Parent:** `user-rq-restoration-20260712T171629-0700`  
**Mode:** fresh independent read-only discussion  
**Actions:** no edits, compilation, Git, experiments, or access to Round 1  
**Instruction refresh:** reread the complete user log after the author added
“故事要变得更强更吸引人” during the round

## Interpretation

The strongest faithful paper is about a missing observability capability:

> **Agent observability needs profiling, not only debugging.**

Debugging reconstructs one execution. Profiling attributes accumulated measures
across a population of executions to recurring responsible entities so
developers can decide what to optimize, inspect, or constrain. The non-obvious
claim is that this method transfers to agents even though code identity and
runtime call stacks do not provide all reusable identities and attribution
levels needed by agent engineering questions.

This position derives the original two-object model: an operation records a
weighted activity or effect while retaining its evidence; an operation stack
projects operations at query time into a hierarchy suited to the requested
attribution. Mappings, taggers, filters, ranking, induced boundaries, cohort
comparison, pprof, and flamegraphs are supporting techniques. Flat,
source-native, and semantic views are experimental comparisons rather than
paper contributions.

The reinforced requirement for a stronger, more attractive story supports the
broad profiling program. It does not authorize changing the fixed four RQs or
presenting hoped-for outcomes as results.

## Narrative Comparison

The Initial Narrative has the best academic skeleton: a large quality, safety,
failure, and cost problem across many runs; a challenge to debugging
sufficiency; a two-object profiling model; a system; and four direct evaluation
questions. It is simple, memorable, and consequential. Its weakness is
empirical overstatement—execution structure, semantic-category correctness,
target-guided localization, and incomplete cost accounting—not its architecture.

The immediately previous narrative improves discipline by distinguishing
execution location, semantic similarity, and accounting responsibility; using
native trees as baselines; and recognizing that a hierarchy cannot manufacture
a missing signal. But its three RQs turn controls into the center. Tag accuracy
disappears, cost becomes subordinate, and negative mechanisms dominate the
Abstract and Conclusion. The paper asks when a representation helps rather than
advancing the stronger profiling thesis.

The proposed architecture restores the initial skeleton while keeping the
previous version's controls. It is a positive research program, not yet a
positive result story; top-conference completion still requires valid evidence
for all four RQs.

## Derived Academic Architecture

Motivation begins with the consequence: long-running agents produce populations
of heterogeneous trajectories, and developers need to know which recurring work
consumes resources, where failures and unsafe effects concentrate, and which
behavior to change. Per-run debugging fragments this evidence. Execution traces
preserve context but do not alone attribute accumulated measures to reusable
task, phase, action, or effect categories.

The challenged belief is precise: an emitted execution structure is not
automatically the only responsibility hierarchy for population-level profiling.
Native structures remain useful rather than absent.

Four solution-independent requirements follow:

1. **Evidence-linked resource accounting:** connect recorded intent, tool
   activity, and system effects without losing source identity, double-counting,
   or claiming unverified causality.
2. **Repeatable cross-run identity:** group semantically equivalent work despite
   prompt, session, agent, or runtime variation, with held-out validation.
3. **Hierarchical auditable attribution:** aggregate a declared measure at task,
   phase, action, and effect levels and drill every aggregate back to native
   operations.
4. **Practical profiling cost:** make profile construction and revision
   affordable on real corpora, including actual capture or tagging costs.

Operations satisfy common weighted accounting and evidence retention. Field
mappings or taggers produce candidate identities. Operation stacks supply
query-time hierarchical attribution. Folding produces the profile; native
evidence remains available for drilldown. Existing profiler formats are reused.

Localization also needs a visible problem-relevant measure or comparison.
Before/after excess, retries, errors, unsafe system effects, or wasted actions
can be folded through the same operation stacks. Profile differencing is an
ordinary analysis over two profiles, not a new abstraction.

```text
real trajectories and effects
-> evidence-linked weighted operations
-> fixed field derivation
-> query-time operation stacks
-> weighted profile and source drilldown
-> engineering decision
```

Flat/native/semantic comparisons are controls below this flow, not the paper's
problem or replacement RQs.

## Contributions

1. Identify profiling as the missing population-level layer in agent
   observability and introduce operations plus query-time operation stacks.
2. Implement AgentProf over real agent histories and supported trace inputs,
   with field derivation, configurable stacks, weighted folding, drilldown, and
   standard profiler outputs.
3. Provide eventual complete evidence through exactly four RQs—attribution,
   real-problem localization, tag accuracy, and profiling cost—not through a
   negative hierarchy taxonomy.

## Fixed RQs And Evidence Architecture

### RQ1: Does Semantic Profiling Improve Resource Attribution?

**Hypothesis:** semantic operation stacks attribute recorded token, time, tool,
or system-effect measures to correct recurring responsibilities more accurately
and less ambiguously than flat, request, or session-only organization.

**Evidence:** real published workloads with independent native
tool/span/process lineage and task responsibility; weighted attribution
precision/recall, unassigned/duplicate mass, mixed responsibility, and
conservation against flat, session, and genuine source-native baselines. Current
conservation is implementation evidence, not attribution correctness.

### RQ2: Does Profiler Output Correspond To Real Problems?

**Hypothesis:** under a label-blind fixed policy, high-priority semantic profile
entries concentrate externally established failures, unsafe effects,
regressions, or wasted work and reduce inspection effort relative to flat,
session, and source-native views.

**Evidence:** a real benchmark with operation-linked problem evidence and a
visible deployable signal; development-only fitting; AP, recall under budget,
work to coverage, and source drilldown. A successful intervention and held-out
rerun are stronger than retrospective localization alone.

### RQ3: How Accurate Are The Tags?

**Hypothesis:** tags derived without target annotations recover stable task,
phase, action categories and boundaries across held-out agents and datasets.

**Evidence:** one fixed mapper or tagger in leave-family-out evaluation against
independent annotations; V-measure, boundary precision/recall/F1, unmatched
coverage, vocabulary-shift failures, lexical/raw-action and learned baselines.
Existing mapping numbers require source/protocol revalidation.

### RQ4: What Is The Profiling Cost?

**Hypothesis:** end-to-end offline profiling is practical at realistic corpus
sizes, and cached derivation makes repeated queries substantially cheaper than
initial construction.

**Evidence:** release builds and recorded hardware over real corpus scales;
separate cold parsing, tag derivation, cache reuse, folding, serialization, peak
memory, storage, and capture overhead when used. Offline does not mean zero cost.

These remain hypotheses, not findings.

## System Direction

- RQ1 needs a thin adapter preserving genuine tool/span/process identities
  through normalization, not a provenance subsystem.
- RQ2 should improve signal and cross-run identity rather than add recursive
  levels. Use a differential or effect-weighted profile over a real regression,
  unsafe effect, retry pattern, or redundant-work signal. The same terminal
  operations and fields feed flat, native, and one fixed semantic stack.
- RQ3 should select one strongest reproducible field-derivation method and
  evaluate it completely. Other taggers/mappings remain optional backends.
- RQ4 needs stage timing, CPU, peak memory, storage, cache behavior, and input
  size. No new cost subsystem is required.

The Rust inducer, ranking rules, differential comparison, profile formats, and
visualizations remain optional supporting mechanisms.

## Unexpected Directions

### Intervention Validation

After a profile identifies a recurring high-cost or problematic group, change
that behavior—tool policy, retry rule, prompt phase, or permission—and rerun the
official workload. A predicted reduction with controlled quality would be
unusually strong RQ2 evidence.

### System Effects As The Flagship Measure

AgentSight's independently observable file, network, and process effects can
connect high-level semantics to concrete behavior. Profiling unsafe network
access, destructive file activity, or repeated subprocess work may give cleaner
RQ1 ground truth and a more compelling RQ2 problem than generic failure labels.

### Longitudinal Release Profiling

Apply the same tags and stack unchanged to two real agent releases or
configurations on the same official benchmark and attribute token, time, retry,
or effect regressions to recurring work.

## Important Unasked Question

> **What population does an AgentProf profile claim to represent?**

The Evaluation setup should define the cohort, hold task mix fixed in
before/after comparisons, report per-family strata, and test composition
sensitivity where needed. This is not a fifth RQ.

## Target Locations

- Restore the exact four RQs and record the narrative comparison in
  `docs/idea-story.md`.
- Rebuild the paper Abstract and Introduction around the profiling problem and
  four-RQ positive program; restore four Evaluation subsections; remove
  representation choice and negative mechanisms from the paper-level center.
- Use Background/Design for evidence-linked accounting, reusable identity,
  auditable attribution, and practical cost.
- Distinguish implemented ingestion/folding/output from missing lineage,
  held-out tagging, deployable localization signal, and cost measurement.
- Restore the four-row `docs/evaluation.md` frontier while keeping failures in
  timestamped history.
- Keep tracing, clustering, localization, and profiling comparisons at the
  missing-capability level in Related Work and Discussion.

## Remaining Evidence And Next Action

The four required packages are independent attribution ground truth, one
successful label-blind localization/intervention experiment, held-out tag
accuracy, and end-to-end cost scaling. The next empirical move should be RQ2 on
a real additive regression or independently recorded unsafe/wasted effect. If
no released public corpus passes source preflight, run two pinned real agent
versions/configurations on an official benchmark with AgentSight; do not use a
toy trace.

This direction is stronger and more attractive than both the unsupported
Initial Narrative and the limitation-centered current paper. It preserves the
original ambition while turning hard-won controls into experimental discipline
rather than the thesis.
