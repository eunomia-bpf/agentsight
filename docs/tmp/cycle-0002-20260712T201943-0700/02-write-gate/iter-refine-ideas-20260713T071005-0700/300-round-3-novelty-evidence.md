# Round 3 — Novelty and Evidence Memo

- Timestamp: `2026-07-13T07:28:53-07:00`
- Mode: independent, read-only literature/novelty review
- Governing skill: `research-literature-novelty`
- Disposition: **KEEP CANONICAL**

## Central answer

Keep the canonical thesis—**“Agent observability needs profiling, not only debugging.”**—but make it credible and exciting by proving that AgentProf turns heterogeneous traces and system effects from many real executions into an actionable, multi-resource profile of recurring work, outperforming native trace trees, ordinary metadata dashboards, and per-run diagnosis on the four fixed RQs without claiming that existing products cannot aggregate at all.

## Material read

The discussant read the complete entry snapshot: active paper and bibliography, full idea history and Initial Narrative, user instructions, evaluation memory, submodule paper, user-selected attachment, WRITE gate entry, and both complete AgentProcessBench FULL reports.

External search covered the same problem, mechanism, outcome, benchmark, product, tracing-standard, cost-attribution, and fault-localization branches. Novelty judgments use primary papers, official repositories, or official product documentation.

## Initial Narrative, current canonical paper, and proposed direction

### Initial Narrative

The Initial Narrative has the strongest problem:

- agents accumulate long, heterogeneous executions;
- developers need fleet-level answers about cost, failure, safety, and wasted work;
- per-run debugging does not itself provide the population-level responsibility attribution supplied by software profiling;
- operations and query-time operation stacks transfer profiling to agents.

It is simple, memorable, and larger than later hierarchy-centered rewrites.

### Current canonical paper

The current paper correctly restores the original thesis, two-object model, system direction, and four RQs. Its main weakness is not the scientific objective. It is that several empirical and closest-work sentences are no longer authorized:

- “existing agent tools … [are] unable to aggregate by semantic category” is too broad;
- “input distributions rather than resource attribution” no longer cleanly separates AgentProf from current products;
- RQ2 conflates grouping with the independent score that ranks groups;
- several strong numerical conclusions remain historical targets rather than currently authorized results.

### Proposed direction

Do not replace the canonical story. Strengthen it around the same principle:

> AgentProf profiles an agent fleet by attributing independently measured tokens, time, system effects, failures, unsafe effects, and wasted work to recurring task–phase–action responsibility across executions.

The paper should win on three demonstrated properties, not on denying that competitors aggregate data:

1. **cross-layer attribution:** connect high-level recurring work to downstream tools, processes, files, and network effects;
2. **query-time hierarchical responsibility:** reorganize the same measured operations at multiple task, phase, action, session, and effect granularities;
3. **decision value:** the resulting profile materially reduces the work or cost needed to find and fix recurring problems.

This is a stronger realization of the canonical story, not a new thesis or model.

## Preservation audit

The proposal preserves:

- exact thesis: **“Agent observability needs profiling, not only debugging.”**
- exactly four RQs: resource attribution, real-problem localization, tag accuracy, profiling cost;
- operations and operation stacks as the only core abstractions;
- broad quality, safety, cost, failure, and wasted-work scope;
- tracing/debugging as complementary rather than obsolete;
- one experiment testing one hypothesis within an RQ;
- positive hypotheses despite intermediate inconclusive results.

It does not replace profiling with hierarchy comparison, reduce RQ2 to one anomaly detector, promote a ranker/tagger/scorer to a new core contribution, insert AgentProcessBench’s inconclusive verdict into the final paper, add a fifth RQ, or adopt any coined abstraction.

## Closest-work map

| Work | Verified overlap | Precise difference and implication | Same-claim risk |
|---|---|---|---|
| [Datadog Agent Observability](https://docs.datadoghq.com/llm_observability/) and [Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Traces requests, aggregates cost, clusters production traffic into a parent–child topic hierarchy, and can identify topics with failed evaluations. | Directly invalidates a categorical claim that existing tools cannot perform semantic aggregation or cross-trace failure analysis. Public docs do not establish AgentProf’s uniform cross-layer operation model, arbitrary query-time responsibility paths, system-effect propagation, pprof output, or benchmarked inspection benefit. AgentProf must demonstrate those differences. | **High** for “first semantic aggregation”; medium for full AgentProf claim. |
| [LangSmith dashboards](https://docs.langchain.com/langsmith/dashboards) and [cost tracking](https://docs.langchain.com/langsmith/cost-tracking) | Aggregates tokens/cost and groups charts by tags or metadata. Official docs note metadata is not automatically propagated between parent and child runs. | Strong baseline for ordinary tagged aggregation. Defensible distinction is automatic/reconstructed propagation across heterogeneous agent/system operations plus multi-level profile paths—not “aggregation versus no aggregation.” | **High** for basic cost grouping; medium for cross-layer hierarchical attribution. |
| [AgentOps](https://arxiv.org/abs/2411.05285) | Defines observability artifacts and lifecycle-wide monitoring, logging, and analytics. | Same broad problem; taxonomy rather than evaluated population-level resource profiler. | Medium. |
| [AgentSight](https://arxiv.org/abs/2508.02736) | Correlates intercepted semantic intent with kernel-level system effects and reports under 3% capture overhead. | Strong real cross-layer input and lineage precedent. AgentProf must show what cross-run profiling adds beyond recording/diagnosis. Complement and required upstream baseline, not an adversary to dismiss. | Medium; very high if cross-layer capture is claimed as new. |
| [AgentProcessBench](https://arxiv.org/abs/2603.14465) and [official repository](https://github.com/RUCBM/AgentProcessBench) | 1,000 real tool-using trajectories and 8,509 human-labeled steps across four task families. | Evaluates step-level process judges, not population-level profiling. Strong annotation source, but two adaptive score constructions exhausted the observed target. It should not supply the next fresh RQ2 claim. | Low for model; high as RQ2 protocol reference. |
| [AgentRx](https://arxiv.org/abs/2602.02475) | Localizes critical failure steps in 115 failed trajectories using constraints and an LLM judge. | Per-failed-trajectory diagnosis rather than cross-run category concentration. Strong localizer usable after a profile selects high-value groups. | Medium for localization, low for population profiling. |
| [TELBench/DRIFT](https://arxiv.org/abs/2606.02060) | 2,790 collected trajectories and a 1,000-instance harmful-span localization benchmark for deep-research agents. | Strong per-trajectory semantic-span diagnosis; it does not identify recurring fleet categories accounting for aggregate cost or harm. | Medium. |
| [AgentLocate](https://arxiv.org/abs/2607.07989) | Attributes a failed multi-agent execution to a responsible agent and earliest decisive step, with several baselines. | Unit is an individual failed execution; AgentProf’s unit is a recurring category. Shows per-run localization is crowded and should not be AgentProf’s novelty claim. | Medium. |
| [TrajAD](https://arxiv.org/abs/2602.06443) | Detects/localizes procedural anomalies using fine-grained process supervision. | Specialized anomaly verification, not general cross-run resource profiling. Its benchmark may be a fresh RQ2 source if the official artifact is complete. | Low–medium. |
| [AgentFixer](https://arxiv.org/abs/2603.29848) | Detects recurring failures, performs root-cause analysis, and improves a real agent on AppWorld/WebArena. | Raises the bar from descriptive localization to repair. AgentProf should show at least one profile-guided intervention. | Medium–high for actionable recurring diagnosis. |
| [ClawTrace](https://arxiv.org/abs/2604.23853) | Records per-step cost/redundancy, produces per-session TraceCards, and reports cost-reducing skill changes on SpreadsheetBench/SkillsBench. | Closest cost-aware actionability precedent. AgentProf can distinguish cross-run hierarchical profiles over arbitrary measured effects but should compare to per-session TraceCards and show fleet-level profile-guided improvement. | **High** for cost-aware diagnosis; medium for general profiling. |
| [A–R Behavioral Space](https://arxiv.org/abs/2604.12116) | Constructs aggregate execution/refusal profiles across regimes and autonomy configurations. | Shows “agent profiling” already includes aggregate behavior characterization. It uses fixed task-specific dimensions; AgentProf proposes a general fielded, weighted, query-time hierarchy. | Medium. |
| [OpenTelemetry GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | Standardizes agent, model, and tool telemetry. | Input/interoperability standard; span kinds do not by themselves establish cross-run semantic responsibility or decision value. | Low for model; high if event standardization is claimed new. |

## Most important unasked question

> **What independent additive signal makes an AgentProf group “hot” or problem-rich without using the target labels that later evaluate it?**

An operation stack groups and attributes measurements; grouping alone cannot predict failures. RQ2 is scientifically sound only when it separates:

1. the target-blind stack;
2. an independently available measurement such as token cost, retry work, tool errors, policy alerts, process-verifier scores, or redundancy signals;
3. hidden human/environment labels used only for evaluation.

Without this separation, RQ2 risks evaluating a scorer or label-derived ranking rather than the profiling model.

## Non-obvious larger directions

### 1. Differential profiling across agent versions

Use the same operation-stack model to compare two real agent versions, models, prompts, or skills and identify recurring task–phase–action paths that account for a cost or reliability regression. This connects AgentProf to the most important use of conventional profilers: explaining why one version regressed. It adds no abstraction and fits RQ1, RQ2, and RQ4.

A complete experiment could run official SWE-agent, OpenHands, or another reproducible agent across the same SWE-bench/OSWorld workload before and after one configuration change, then test whether the profile identifies categories responsible for the measured regression.

### 2. Profile first, diagnose second

Use AgentProf to select recurring groups accounting for most cost, error, or unsafe-effect mass; invoke AgentRx-, DRIFT-, or AgentLocate-style expensive per-trajectory diagnosis only inside those groups.

- AgentProf answers **where across the fleet to spend attention**.
- Per-run localizers answer **what failed inside a selected execution**.

The decisive metric is the fraction of annotated problems localized under a fixed human/LLM-judge budget, not AP alone. This can make profiling-versus-debugging experimentally undeniable.

## Strictly larger attractive story

> **Profile the agent fleet, not just individual runs. AgentProf turns prompts, model calls, tools, processes, files, and networks into multi-resource profiles of recurring work, revealing which task–phase–action paths account for fleet-wide cost, regressions, failures, and unsafe effects—and directing developers to the few behaviors whose repair changes real outcomes.**

This is larger than the current implementation but faithful to the thesis and two-object model. It is an evidence target, not an immediately authorized paper claim.

## Prioritized complete evidence program

### Priority 1 — RQ2: fresh, actionable localization

**Hypothesis:** A fixed semantic operation stack using an independently released cost/redundancy signal concentrates recurring waste across real executions better than flat, raw-action, native-trace, and per-session views, reducing work for a successful profile-guided intervention.

**Chosen source:** ClawTrace’s released artifact and complete SpreadsheetBench/SkillsBench protocol, after a bounded screen confirms referenced TraceCards and official evaluation path are downloadable. Its paper supplies real per-step cost, redundancy, held-out transfer, and a published intervention protocol.

**Complete experiment:**

- use every released trajectory/task in the selected official split;
- preserve released per-step cost/redundancy measurements;
- derive task/phase/action stacks without redundancy labels;
- compare flat, raw tool/action, native trace/session hierarchy, ClawTrace per-session TraceCard prioritization, AgentProf semantic stack, and label-visible oracle only as an upper bound;
- report task-cluster AP, work to recover 50%/80% of redundant cost, and inspected steps under a fixed budget;
- apply one profile-selected repair/prune action through the official benchmark and measure cost saved at fixed task success on the complete held-out split.

If complete ClawTrace data are unavailable, continue without human waiting to the first runnable fresh source among TrajAD/TrajBench or AgentLocate. Do not return to a third AgentProcessBench score.

### Priority 2 — RQ1: real cross-layer resource attribution

**Hypothesis:** A fixed semantic operation stack attributes independently recorded system resources to recurring task categories more faithfully and with less fragmentation than native per-execution trees or ordinary tag dashboards.

**Sources/systems:** official AgentSight capture, OpenTelemetry GenAI spans as native hierarchy, complete real workloads from OSWorld, SWE-bench/SWE-agent, or another official benchmark, and at least two agent implementations or materially different versions.

**Baselines:** flat summary; raw tool/process grouping; native OTel span tree; per-session grouping; explicit tag/metadata aggregation representing LangSmith/Datadog; semantic operation stack; source task/phase metadata as evaluation oracle, never target-blind tagger input.

**Metrics:** conservation of tokens/duration/processes/file/network events; attribution error against independently recorded task/phase and process-lineage identities; groups needed to cover 80% of true category resource mass; fragmentation/contamination; paired results across tasks, agents, and resources.

The current mixed-weight result is insufficient because its category reference is prompt-derived. A new test needs identities recorded independently of AgentProf.

### Priority 3 — RQ3: target-blind tag transfer

**Hypothesis:** A fixed tagger trained without the target family assigns useful task, phase, action, and boundary identities on unseen real agent families.

**External data:** complete official WebLINX, Mind2Web, AgentNet, OSWorld-Human, API-Bank, ToolBench, tau-bench, SWE-agent, and compatible released families. Use native annotations and admit only label levels with honest cross-family correspondence.

**Protocol:** leave one complete agent/dataset family out; fix tagger, prompt/rules, label inventory, and cache before target evaluation; no target-label-driven field/rule changes; evaluate task/action/boundary labels separately; report macro held-out results and downstream RQ1/RQ2 sensitivity when predicted tags replace native tags.

**Metrics:** macro F1 for named labels; V-measure where clustering is genuinely the task; boundary precision/recall/F1; repeated-decoding stability; downstream attribution/localization change.

The original “7 of 9 above 0.7” is not presently authorized as a complete transfer conclusion.

### Priority 4 — RQ4: full end-to-end cost and scale

**Hypothesis:** Complete AgentProf construction scales practically on real corpora, and cached repeated queries are substantially cheaper than cold construction and repeated raw-trace analysis.

**Workloads:** full real AgentSight history and complete public corpora at natural scales, including WebLINX, AgentProcessBench, AgentNet, Mind2Web, and the largest admitted source. No smoke subset is a final experiment.

**Protocol/tools:** official `hyperfine`, `/usr/bin/time -v`, profiler-native counters; cold parse/tag/fold; warm cached profile query; repeated predicates, field paths, and weights; every complete workload and repetition.

**Metrics:** wall time; operations/second; peak RSS; cache and profile-output size; cold tag cost; warm 1/10/100-query cost; comparison to OTel/native-tree aggregation and, where runnable, a standard analytical-query baseline.

“Zero runtime overhead” must report capture and offline analysis separately because acquiring telemetry can cost resources.

## What current evidence authorizes

### RQ1

Authorizes exact mass conservation for tested R170 projections, declared prompt-tag separation, association between prompt tags and behavior beyond session membership under the recorded permutation, and different token/time view rankings.

Does not authorize correct semantic intent, causal prompt-to-effect attribution, semantic tags being necessary, or the broad conclusion that over 90% of previously unattributable effect cost was correctly attributed.

### RQ2

Both AgentProcessBench constructions internally authorize positive equal-family macro AP effects, semantic-specific matched shuffles, and favorable all-family work point estimates in the second construction. They do not authorize the conjunctive localization claim because task-cluster work intervals include zero, or another same-target scoring variant.

### RQ3

No current complete result authorizes the general “7 of 9 held-out datasets” sentence without rechecking exact mappings, training boundary, native labels, and downstream consequence.

### RQ4

Historical timing/cache numbers may be implementation observations but do not authorize a complete profiling-cost conclusion across real scale, cold/warm modes, memory, output size, and capture cost.

## Terminology and drift risks

1. **“Existing tools only trace/debug.”** Factually stale. Datadog/LangSmith aggregate. Preserve the thesis by comparing what their aggregation represents and which decisions it supports.
2. **“Semantic profiling.”** Define as attribution of measured additive effects to recurring semantic responsibility, not topic clustering.
3. **“Intent attribution.”** Can sound causal. Tag assignment and downstream causal propagation are separate claims.
4. **“Operation stack.”** A query-time responsibility path, not a recovered runtime call stack.
5. **“Top-ranked profiler groups.”** Always name the independent weight/risk signal; grouping is not a failure predictor.
6. **“Hidden labels.”** Labels are not hidden if fields, thresholds, rankings, or mappings were tuned after viewing them.
7. **“Ground truth.”** Distinguish native metadata, human quality labels, outcomes, and oracle fields.
8. **“Zero overhead.”** Offline work begins after telemetry; capture/export may cost resources.
9. **Stacked terminology.** Do not name score variants, controls, workflow phases, or evidence levels. Operations and operation stacks are sufficient.

## Final disposition

**KEEP CANONICAL.**

Accept into root synthesis:

- current products already perform semantic/cost aggregation;
- independent measurement/ranking must be explicit;
- fleet-level, multi-resource, profile-to-intervention is the larger evidence target;
- use the prioritized fresh-source program.

Reject:

- any replacement thesis;
- hierarchy-centered story;
- third AgentProcessBench score;
- new core abstractions or coined terminology;
- insertion of inconclusive internal results;
- rewriting RQs to match the successful experiment.

The original AgentProf story remains more ambitious and valuable than later alternatives. Its path to a top venue is stronger competition and complete external evidence, not a smaller idea.
