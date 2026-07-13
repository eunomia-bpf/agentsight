# Round 1 Research Memo — Recovering the Largest Faithful AgentProf Direction

- Timestamp: `2026-07-13T07:14:05-07:00`
- Parent run: `cycle-0002-20260712T201943-0700 / WRITE`
- Round: `iter-refine-ideas`, Round 1 — Problem and Research Direction
- Mode: independent, read-only discussion
- Recommendation: **KEEP CANONICAL**

## Entry snapshot and material read

The discussant read the complete active paper and bibliography, the complete idea history from the Initial Narrative through E008, all user instructions, evaluation memory, the read-only submodule paper, the WRITE gate entry, both complete AgentProcessBench FULL reports, and the user-selected attachment.

The attachment and submodule paper are identical after stripping CRLF differences. The active paper has the same scientific body under the AAAI wrapper.

## Central answer

**The largest faithful problem is that modern agent observability records individual executions but lacks a profiling layer that aggregates recurring behavioral responsibility, resource use, failures, unsafe effects, and wasted work across a population of trajectories; the canonical original AgentProf story already expresses this problem more simply, broadly, and memorably than the hierarchy-centered alternatives developed later.**

The exact thesis should remain:

> **Agent observability needs profiling, not only debugging.**

## Interpretation of the idea

The important leap is not merely that agent traces can be regrouped using semantic fields, nor that an execution hierarchy is sometimes the wrong hierarchy. Those observations support the idea but are not the idea.

The larger scientific position is that the operational unit of analysis changes when agents become long-running and widely deployed. An individual trace answers “what happened in this execution?” A profile answers population-level questions such as:

- Where does an agent fleet spend its tokens and time?
- Which recurring workflows account for failures or wasted work?
- Which categories of behavior are associated with unsafe system effects?
- What should developers optimize, inspect, or constrain first?

Traditional software observability already distinguishes tracing from profiling. Code profiling works because repeated executions expose stable code identities and call stacks. Agent activity is instead spread across prompts, model calls, tools, processes, files, networks, sessions, and changing natural-language expressions. A trace can preserve occurrence order without supplying the recurring responsibility categories needed for cross-run attribution.

AgentProf’s two abstractions are a compact answer:

1. an **operation** records an activity or effect together with additive measures;
2. an **operation stack** folds those observations into a query-time attribution hierarchy.

The system is valuable if this turns many heterogeneous trajectories into profiles that guide real cost, quality, safety, and optimization decisions. Taggers, mappings, boundary detection, rankers, pprof serialization, and flame graphs are mechanisms that support this position; none should replace it.

## Initial, current, and proposed narratives

### A. Complete Initial Narrative

The Initial Narrative is the strongest version at the level of scientific importance. It establishes:

- long-running, multi-run agents as the changed setting;
- quality, safety, cost, failure, and wasted work as consequences;
- profiling versus debugging as the challenged observability assumption;
- trajectories as samples from a behavioral population;
- operations and operation stacks as the only two core abstractions;
- four questions spanning attribution, localization, tag accuracy, and cost.

Its greatest strength is that it explains why a new profiling layer matters independently of whether any particular grouping algorithm wins. Its problem survives changes in models, agent frameworks, benchmarks, and tagging mechanisms.

It also correctly distinguishes the durable idea from an overly literal claim that agents have no execution structure. Agents can have span trees, tool trees, or process trees. The issue is that those structures describe where activity occurred in a run; they are not automatically the cross-run responsibility hierarchy required for profiling.

### B. Immediately previous/current canonical story

The restored submodule paper is the best current paper-level expression of the Initial Narrative. Its strongest passages are the concrete population-level questions, the analogy with conventional profiling, and the simple transition from missing stable identities and attribution hierarchies to operations and operation stacks.

It is substantially better than the later representation-choice story because it makes the scientific consequence—not a control experiment—the headline. The exact conclusion sentence is especially strong and should not be replaced by a longer description of cross-run recurrence:

> **Agent observability needs profiling, not only debugging.**

The canonical paper does contain statements that future writing and evidence review must handle carefully without replacing the story:

- “agent trajectories have no runtime hierarchy” is too literal if read as denying span or execution trees; the intended point is that execution nesting does not automatically provide the needed semantic profiling hierarchy;
- “existing tools support debugging and tracing but not profiling” is a broad novelty claim that needs current, source-grounded comparison;
- cross-layer attribution must not silently imply causal attribution unless the collected lineage supports it;
- several positive result sentences remain intended claim targets rather than presently authorized evidence.

These are evidence and expression problems. They are not reasons to substitute a smaller scientific direction.

### C. Best proposed direction

The strongest proposed direction is a sharpening of the canonical story, not a replacement:

> Individual agent traces are samples. AgentProf turns a population of those samples into profiles of recurring behavior and measured effects, so developers can decide what to optimize, inspect, or constrain.

This makes three aspects already latent in the canonical paper more explicit:

1. **Population:** the work is about accumulated trajectories, not a different rendering of one trace.
2. **Measured responsibility:** profiling attributes declared additive measures to recurring behavioral entities; semantic grouping alone is not the result.
3. **Decision:** the profile should guide optimization, inspection, or constraints, rather than merely produce an attractive visualization.

This sharpening should use ordinary prose. It does not require a new named concept, new layer, new taxonomy, or another core abstraction.

## Preservation audit

### Thesis

Preserved verbatim:

> **Agent observability needs profiling, not only debugging.**

Neither “cross-run semantic aggregation,” “responsibility hierarchy selection,” nor “decision-oriented observability” should replace this sentence as the thesis.

### Four fixed RQs

All four remain unchanged in number and meaning:

1. **Attribution:** Does Semantic Profiling Improve Resource Attribution?
2. **Real-problem localization:** Does Profiler Output Correspond to Real Problems?
3. **Tag accuracy:** How Accurate Are the Tags?
4. **Profiling cost:** What Is the Profiling Cost?

No proposed experiment, result, or writing refinement should merge, delete, reinterpret, or answer these questions wholesale.

### Positive hypotheses

The fixed hypotheses are preserved:

- semantic operation stacks should improve attribution of independently recorded resources;
- target-blind profiles should concentrate independently annotated real problems and reduce inspection;
- target-blind tags should transfer accurately and stably;
- complete profiling should scale practically, with cheaper repeated cached queries.

The recent AgentProcessBench studies test one construction inside RQ2. Their positive AP effects and unresolved work intervals neither answer RQ2 nor authorize changing its hypothesis.

### Model and contribution structure

Operations and operation stacks remain the only core abstractions. The paper remains a problem/model/system/evaluation contribution, not a benchmark-only, hierarchy-selection, semantic-clustering, or anomaly-detection paper.

## Non-obvious upward directions

### 1. Differential profiling across agent versions

The canonical paper mostly presents a static profile, but the larger operational value may lie in comparing profiles across releases, prompts, models, tools, or policies. A developer often needs to know not only where current cost or failures concentrate, but what changed after an agent update. The same operation-stack model could compare two populations and show which recurring behaviors gained token cost, latency, unsafe effects, or failure mass. This is directly analogous to differential CPU or heap profiles and remains faithful to the profiling thesis.

Evidence needed:

- complete real trajectories from at least two versions or configurations of the same agent;
- matched tasks or a defensible workload distribution;
- conservation and lineage checks for the measured resource;
- comparison against per-run trace inspection and flat aggregate dashboards;
- independently observed regressions or interventions whose location is not selected from the profile;
- practical cost of repeated differential queries.

This is strictly larger than the current static story, but it should remain an upward experimental direction until the system and evidence support it. It should not become a new paper claim merely because it sounds attractive.

### 2. Profiling an agent fleet rather than one framework

The model is potentially framework-independent because operations normalize prompts, tools, model calls, and system effects before profiling. The larger story could therefore concern an organization’s heterogeneous agent workload: multiple models, frameworks, tools, projects, and task families profiled through a common method.

This would make AgentProf analogous to a general workload profiler rather than a Codex/Claude visualization tool. It would also strengthen the claim that execution-local structures are insufficient: heterogeneous runtimes expose different trace schemas, while operators still need comparable cost, safety, and failure categories.

Evidence needed:

- multiple real agent implementations, not only multiple datasets mapped into one schema;
- independently captured measures from those systems;
- a fixed cross-agent tagger or mapping evaluated on held-out families;
- comparison with each source’s native hierarchy and observability product;
- evidence that one operation representation preserves meaningful source lineage without erasing important differences;
- complete overhead and scaling measurements.

This direction broadens deployment scope without changing the four RQs.

### 3. One profiling method across cost, quality, and safety

A less obvious strength of the original story is that tokens, duration, file effects, unsafe operations, failures, and redundant work can all be treated as additive measures over the same recorded operations. If supported, this means AgentProf is not merely a token profiler or failure grouper: it is one profiling method for several operational objectives.

Evidence needed:

- independent measures for each objective rather than tags manufactured from the outcome;
- consistent mass conservation and source lineage;
- target-blind group construction;
- demonstrations that different measures produce materially different actionable rankings;
- real public tasks for safety, failure, redundancy, and cost;
- no claim that AgentProf automatically detects an outcome it merely aggregates.

This is already latent in the canonical paper and should be strengthened through experiments rather than additional terminology.

## Most important unasked question

**Do semantic profiles remain stable and useful enough across agent changes that acting on a high-cost or high-problem group produces a measurable improvement in a later population of trajectories?**

The current four RQs establish the necessary chain—attribution, localization, tag validity, and cost—but the project has not yet directly shown the operational consequence implied by the thesis.

This need not become a fifth RQ. A real before/after or held-out intervention can strengthen RQ1 or RQ2:

1. build a profile on one complete population;
2. select an optimization or correction using only that profile;
3. apply the change to the agent or workflow;
4. run a held-out population;
5. measure whether the targeted cost, failure, or unsafe-effect mass falls without unacceptable displacement elsewhere.

Such evidence would connect “profiling output corresponds to real problems” to why profiling matters. It would be more persuasive than inventing another grouping metric.

## Strictly larger and more attractive version

> As agents become persistent operational systems, their traces become samples from an evolving behavioral workload. AgentProf brings profiling to that workload: it attributes cost, failures, unsafe effects, and wasted work to recurring behavior across agents and executions, allowing developers to find regressions and decide what to optimize, inspect, or constrain.

This version is larger because it covers populations rather than isolated traces, changing agent versions rather than one static dataset, heterogeneous agents rather than one runtime, several operational measures rather than tokens alone, and regression and intervention decisions rather than visualization alone.

It preserves the exact thesis and four RQs. It would require multi-project/fleet evidence and at least one held-out differential or intervention study. Until that evidence exists, the canonical story should remain the paper’s authority and this version should guide experiment selection rather than appear as an unsupported contribution.

## Evidence program implied by the canonical story

The strongest evidence path remains the four fixed RQs:

- **RQ1:** independently recorded resources, preserved lineage and mass, and matched flat/native/semantic comparisons on real traces;
- **RQ2:** fresh public agent executions with independent problem labels, target-blind profiles, strong native and per-session baselines, complete localization and inspection results;
- **RQ3:** a fixed tagger or mapping transferred to unseen agent and task families, including downstream attribution sensitivity;
- **RQ4:** full construction time, memory, output size, scaling, cache behavior, and repeated-query cost on complete workloads.

The two AgentProcessBench constructions contribute positive semantic-specific AP evidence but do not complete the inspection-work condition. They should guide selection of a fresh external source or different evidence mechanism after whole-paper review. They should not cause a third target-tuned score, a smaller RQ2, or negative-result prose in the paper.

## Drift and terminology risks

The main danger is again allowing a supporting observation to replace the larger problem.

Avoid:

- making “execution hierarchy has no authority” the thesis;
- turning AgentProf into a generic semantic clustering system;
- presenting automatic stack induction as the central contribution;
- equating a visually coherent group with correct attribution;
- treating a fixed public-dataset label as a universal definition of failure;
- claiming causal responsibility when the evidence only establishes association or inherited lineage;
- making one recent RQ2 construction answer all of RQ2;
- replacing positive hypotheses with conservative claims about representation sensitivity.

Avoid adding terms such as responsibility graph, semantic scope tree, profile contract, decision hierarchy, evidence packet, or attribution lineage layer. The paper already has the only two technical objects it needs: operation and operation stack. Even phrases such as “behavioral workload” and “differential profiling” should be ordinary descriptions unless repeated implementation and evidence make a dedicated term indispensable.

The paper should distinguish a trace’s execution structure, a profile’s recurring attribution structure, and the independent measure being aggregated. That distinction can be expressed in one paragraph and does not need a taxonomy.

## Candidate expression targets

These are presentation targets for the later writing loop, not authorized idea changes:

- **Abstract:** emphasize accumulated trajectories as the population being profiled and retain the quality/safety/cost stakes.
- **Introduction paragraphs 2–5:** make the transition from per-run explanation to cross-run operational decisions explicit; keep the concrete questions.
- **Background:** clarify that native execution trees may exist but do not automatically provide recurring semantic responsibility across runs.
- **Design opening:** keep the derivation from projection, stable tags, and hierarchical attribution to the two-object model.
- **Evaluation opening:** state that the four RQs test the complete thesis chain and that an experiment tests only its assigned hypothesis.
- **Conclusion:** retain the exact thesis sentence and avoid replacing it with evidence-control language.

No idea-level modification should be applied before the root disposition, and no unsupported empirical sentence should be altered merely on the basis of this discussion.

## Final recommendation: KEEP CANONICAL

The canonical original AgentProf story is already the largest, clearest, and most faithful version presently justified. Later hierarchy- and representation-centered alternatives improved experimental discipline but made a supporting issue the headline and reduced the paper’s scientific consequence.

The best course is therefore:

- keep the exact thesis and four RQs;
- keep operations and operation stacks as the only core abstractions;
- preserve the canonical problem/model/system/contribution chain;
- treat population-level profiling, operational decisions, differential comparison, and heterogeneous fleets as ways to strengthen the original story through evidence;
- let experiments repair unsupported positive claims rather than letting inconclusive experiments rewrite the story;
- reject any proposal that makes a local grouping result, reviewer objection, or evidence-control mechanism the new thesis.

This round proposes no accepted scientific story change. Its only recommended refinement is to express the canonical idea more explicitly as profiling a population of agent trajectories for decisions about cost, quality, safety, and wasted work.
