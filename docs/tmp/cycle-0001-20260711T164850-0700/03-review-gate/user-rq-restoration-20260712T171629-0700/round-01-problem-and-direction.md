# Round 1 — Problem And Research Direction

**Completed:** 2026-07-12T17:19:34-07:00  
**Parent:** `user-rq-restoration-20260712T171629-0700`  
**Role:** fresh independent read-only research discussant  
**Entry snapshot:** the files named by `000-recovery-entry-20260712T171629-0700.md`  
**Actions:** no edits, compilation, Git operations, experiments, or access to other idea-round reports

## Central Interpretation

The largest faithful idea is not that semantic trees sometimes beat execution
trees or that AgentProf is a better grouping method for failure localization.
It is the exact author-fixed position:

> **Agent observability needs profiling, not only debugging.**

As agents become populations of long-running heterogeneous executions,
developers need an aggregate empirical surface for managing behavior: where
resources accumulate, where real problems recur, whether the semantic identities
used for aggregation are accurate, and whether obtaining those answers is
affordable. Traces preserve occurrences in individual executions. Profiles
reorganize measured activity around recurring behavioral responsibility across
executions.

AgentProf's ambitious claim is that the profiling method transfers from code to
agent behavior. An agent corpus becomes profiling samples; observed activities
and effects become weighted operations; query-time operation stacks attribute
additive measures to recurring tasks, phases, actions, sessions, tools, or
effects. The same evidence can then answer cost, quality, failure, safety,
regression, and wasted-work questions at the granularity of the decision.

The non-obvious insight is not that hierarchical aggregation exists. It is that
an execution hierarchy and a profiling responsibility hierarchy answer different
questions. The former records where an event occurred; the latter attributes a
measure to recurring work across a population. Native execution paths, flat
summaries, and semantic operation stacks remain competing projections over the
same evidence. The bold hypothesis is that semantic responsibility is
load-bearing for many cross-run engineering decisions, not that any semantic
grouping is universally correct or can manufacture a missing signal.

## Narrative Comparison

### Initial Narrative

The Initial Narrative did best at importance, simplicity, and completeness. It
began from population-level engineering questions, distinguished profiling from
debugging, introduced only operations and operation stacks, and mapped the system
directly onto four understandable questions:

1. Does semantic profiling improve resource attribution?
2. Does profiler output correspond to real problems?
3. How accurate are the tags?
4. What is the profiling cost?

This architecture makes AgentProf a general observability method rather than a
benchmark-specific localizer and preserves the intended cost, failure, safety,
regression, and wasted-work consequences.

Its weakness was evidentiary, not conceptual. It treated declared categories as
attribution truth, used target-informed or annotation-adjacent constructions,
conflated concentration with diagnosis, and presented incomplete cost evidence
as end-to-end affordability. It also overstated the absence of native execution
structure.

### Immediately Previous Narrative

The three-RQ narrative correctly separated conservation from lineage,
accounting from causation, semantic membership from diagnostic signal, matched
projection comparison from end-to-end method comparison, and restored
source-native hierarchy as a serious baseline.

It paid too high a price for that discipline. Fidelity/comparability,
analytical value, and generality/limits turned safeguards and boundary analysis
into the paper's center. Attribution became conservation and lineage checking;
localization became a broad question about which projection wins; tag accuracy
disappeared; cost became a condition inside analytical value. The paper reads as
a negative representation-comparison study even though its thesis sentence
survived.

### Proposed Narrative

Combine the original academic architecture with the previous version's
experimental discipline:

- restore the exact thesis and four original RQs as the paper's spine;
- retain operations and operation stacks as the only core abstractions;
- restore the positive hypothesis that recurring semantic responsibility can
  make cross-run agent cost and real problems attributable and localizable;
- keep independent lineage, held-out construction, native baselines, matched
  information, and end-to-end accounting as experiment requirements rather than
  new contributions or replacement RQs;
- keep failed AgentRx/TELBench and Hodoscope constructions in research history,
  where they inform the next mechanism and protocol, rather than making them the
  final paper's headline;
- never restore old positive numbers until new complete experiments authorize
  them.

This is more ambitious and legible than the immediately previous narrative and
more scientifically disciplined than the initial paper.

## Fixed RQs And Positive Hypotheses

### RQ1 — Does Semantic Profiling Improve Resource Attribution?

Semantic operation stacks should improve attribution of real additive measures
across heterogeneous runs because they reunite recurring responsibility that
session and execution paths fragment. Improvement must mean assigning
independently recorded tokens, time, retries, tool actions, process/file/network
effects, or other additive measures to the task, phase, or action responsible
for an engineering decision, while preserving verified source lineage and mass.

The 325-trajectory corpus establishes recurrence, reprojection,
declared-category separation, and conservation. These are premises, not the
complete answer.

### RQ2 — Does Profiler Output Correspond To Real Problems?

Profiles should concentrate externally verified failures, regressions, unsafe
effects, or wasted effort into recurring behavioral regions and reduce raw
evidence inspection relative to flat, session, and genuine source-native views.
A directly recorded change or independent visible signal can be folded and
ranked; the profiler exposes where the signal accumulates rather than acting as a
universal anomaly detector.

The strongest answer closes the loop: a profile identifies recurring
responsibility, an engineer changes the associated prompt/tool/policy/config,
and the problem falls on a held-out rerun.

### RQ3 — How Accurate Are The Tags?

Semantic tags learned or authored without target labels should provide stable,
useful identities across paraphrases, sessions, agents, projects, and held-out
families. Independent annotations or repeated human judgments measure accuracy;
stability under wording and version changes tests whether tags support
longitudinal profiling. Mapping transfer, vocabulary shift, boundary agreement,
and tag consistency are evidence inside this fixed RQ rather than a reason to
replace it.

### RQ4 — What Is The Profiling Cost?

AgentProf should be cheap enough for repeated use over realistic trajectory
corpora and substantially cheaper than reviewing every trajectory separately.
The answer includes parsing, field derivation, uncached tagging, caching, stack
construction, folding, output, storage, and any capture or lineage cost required
by the evaluated workflow. Offline operation alone does not establish zero cost.

## Challenged Belief And Competing Explanations

The paper challenges the implicit assumption that retaining and inspecting
individual executions is an adequate basis for managing agent populations.
Execution trees remain indispensable for drilldown and lineage but are not
sufficient as the only aggregation index for population-level questions.

Live competing explanations should drive experiments without replacing the
thesis:

- ordinary multi-column grouping supplies all benefit;
- semantic tags expose extra information or reproduce the oracle;
- session or native execution structure is already sufficient;
- a ranker or visible signal rather than the hierarchy causes localization;
- semantic identity drifts across models and projects;
- profile construction costs more than the inspection it saves.

## Unexpected Directions

### Agent Release And Regression Profiling

Run two real versions, models, prompts, policies, or tool configurations on the
same official tasks, record additive differences in tokens, time, retries, tool
calls, or policy effects, and fold the changes by recurring task/phase/action.
This is faithful to traditional profiling: a developer has a concrete
before/after regression and needs to find where aggregate excess work entered.
Differential comparison is a query over the two existing abstractions, not a
third abstraction.

### Profile-To-Intervention Closure

Use the profile to select one real prompt, tool, policy, or workflow change,
rerun an untouched benchmark, and measure whether the attributed cost or problem
falls without harming the official outcome. This distinguishes decision-relevant
responsibility from decorative clustering.

### Cross-Layer Safety And Resource Budgeting

Combine independently recorded AgentSight process/file/network effects with
agent task/tool context in a real sandboxed benchmark, asking which recurring
semantic phases account for policy-sensitive effects or excess system use.

## Important Unasked Question

> **Does acting on an AgentProf result improve the agent on subsequent runs?**

This should not become a fifth RQ. It is the strongest form of RQ2 evidence. If
changes to an identified phase do not change the problem, the profile may be
correlated but not actionably responsible.

## Target Locations

- `docs/idea-story.md`: restore the four RQs and positive hypotheses in Current
  Frontier and append one evolution entry explaining the correction.
- `docs/paper/main.tex`: restore the population-level thesis, two abstractions,
  four evaluation questions, and ultimately authorized positive results in the
  Abstract and Introduction; remove failed intermediate constructions as the
  headline.
- Background and Design: retain native evidence, accounting-versus-causation,
  drilldown, and mappings/taggers as mechanisms.
- Evaluation: RQ1 independent attribution; RQ2 localization plus intervention;
  RQ3 held-out tag accuracy and stability; RQ4 complete cost.
- `docs/evaluation.md`: restore a four-row current frontier while retaining every
  failed or inconclusive experiment in timestamped history.
- Related Work and Conclusion: present the missing population-level profiling
  layer, not hierarchy selection or anomaly localization, as the center.

## Constraint Resolution

The failed experiments remain auditable in detailed history but should not be
the final positive paper's result story once superseded by clean complete
evidence for the final mechanism. The paper must not claim universality over a
condition where the unchanged final method is known to fail. Until new positive
experiments complete, explicit unresolved result placeholders are preferable to
restoring unaudited numbers.

A fixed hypothesis is genuinely impossible only after clean, prespecified,
complete tests show that permitted observations contain no usable signal or the
final mechanism repeatedly fails against fair baselines across representative
real conditions. One induced leaf, one recursive construction, or one confounded
bundle comparison does not meet that bar.

## Remaining Evidence And Next Action

Required evidence remains:

1. independently recorded lineage and additive effects for RQ1;
2. a complete real experiment in which an unchanged semantic profile improves
   localization or guides a successful intervention for RQ2;
3. target-blind tag accuracy and stability across agents, projects,
   vocabularies, and paraphrases for RQ3;
4. reproducible end-to-end scaling, including uncached tagging and the RQ1/RQ2
   evidence path, for RQ4.

After the root disposition, reopen literature and artifact search for the best
released before/after agent workload, then route the accepted story to WRITE and
one complete real RQ2 experiment.
