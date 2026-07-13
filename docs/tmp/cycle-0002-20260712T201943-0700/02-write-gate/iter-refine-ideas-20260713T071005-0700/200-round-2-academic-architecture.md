# Round 2 Memo — Academic Architecture and System Direction

- Timestamp: `2026-07-13T07:19:32-07:00`
- Parent run: `cycle-0002-20260712T201943-0700 / WRITE / iter-refine-ideas`
- Method: independent, read-only academic-architecture audit; the discussant did not read Round 1 output, edit files, run Git, compile, or delegate.
- Recommendation: **KEEP CANONICAL**

## Files read

The discussant completely read `docs/paper/main.tex`, `docs/paper/references.bib`, the whole `docs/idea-story.md` including the permanent Initial Narrative and E000–E008, `docs/user-instruction.md`, `docs/evaluation.md`, `docs/agentpprof-paper/main.tex`, the WRITE gate entry, both AgentProcessBench FULL reports, and the user-selected attachment.

The attachment is normalized-content identical to the submodule paper; its raw hash differs because it uses CRLF line endings. The active paper retains the same scientific body under the AAAI wrapper.

## Central answer

The strongest architecture is the canonical one, made more explicit but not replaced: **cross-run agent-development decisions require population-level profiling; operations provide the common weighted evidence unit; operation stacks provide the query-time responsibility hierarchy; AgentProf materializes those two abstractions; and the four fixed RQs test attribution, real-problem localization, tag accuracy, and profiling cost.**

## Initial Narrative vs. current paper vs. proposed architecture

### Initial Narrative

The Initial Narrative remains the strongest version because it starts from consequential questions about quality, safety, failures, wasted work, and cost across many trajectories; states the memorable thesis “Agent observability needs profiling, not only debugging”; and explains the solution with only operations and operation stacks.

Its weakness is not ambition. Some sentences overstate the absence of execution structure, treat semantic responsibility as automatically correct, or move too quickly from grouping to validated diagnosis. Those are evidence and wording problems, not reasons to replace the story.

### Current canonical paper

The active canonical paper preserves the Initial Narrative’s scientific spine almost exactly and adds a complete system and evaluation organization. It also retains historical result statements whose evidentiary status must be established through complete experiments.

The current idea history improves the scientific boundary by distinguishing execution occurrence from cross-run profiling responsibility, grouping from correct attribution, semantic fields from automatic diagnostic authority, and one tested construction from an entire RQ. These distinctions should discipline experiments and wording, not become a replacement thesis about hierarchy authority, representation choice, or decision-oriented aggregation.

### Best proposed academic architecture

The best proposal is **canonical-plus-explicit-derivation**, not a new narrative:

1. Long-running agents generate many heterogeneous trajectories.
2. Developers need aggregate answers about recurring cost, failure, safety, and wasted work.
3. Per-run traces preserve execution occurrence; they do not by themselves produce reusable cross-run responsibility categories.
4. Agent profiling needs a common weighted observation across agent and system layers, stable fields for recurring behavior, and an explicit hierarchy for multi-resolution attribution.
5. An **operation** supplies the common weighted observation.
6. An **operation stack** supplies the explicit query-time hierarchy.
7. AgentProf parses real traces, derives fields, projects operations onto stacks, folds additive measures, and emits standard profile outputs.
8. The four fixed RQs test whether this construction works scientifically and practically.

This is already latent in the canonical paper. WRITE should expose it more cleanly, not invent a new center.

## Preservation audit

| Fixed element | Disposition |
|---|---|
| “Agent observability needs profiling, not only debugging.” | Preserved verbatim as the paper-level center |
| RQ1 attribution | Preserved |
| RQ2 real-problem localization | Preserved |
| RQ3 tag accuracy | Preserved |
| RQ4 profiling cost | Preserved |
| Operations and operation stacks | Preserved as the only core abstractions |
| Quality, safety, cost, failure, and wasted-work stakes | Preserved |
| Profiling complements debugging/tracing | Preserved |
| Intermediate negative/inconclusive results in final paper | Rejected |
| New core graph, taxonomy, registry, hierarchy authority, or decision layer | Rejected |
| Replacing thesis with cross-run recurrence wording | Rejected |
| Treating AgentProcessBench as the answer to RQ2 | Rejected |

## Problem → model → system → evaluation dependency

| Problem pressure | Required capability | Existing abstraction or mechanism | Scientific test |
|---|---|---|---|
| Activities and effects span prompts, LLM calls, tools, processes, files, and networks | Represent heterogeneous evidence and additive measures uniformly | **Operation** | RQ1 and RQ4 |
| Equivalent recurring work appears under different sessions and surface strings | Derive stable reusable fields without evaluation targets | Supporting tagger or mapping over operation fields | RQ3 |
| Execution trees do not directly answer every cross-run responsibility question | Select an explicit multi-resolution attribution hierarchy | **Operation stack** | RQ1 and RQ2 |
| Developers must find concentrated failures, unsafe effects, or waste | Rank profile groups target-blind and inspect real annotations afterward | Supporting ranking policy over profile output | RQ2 |
| Profiling must be repeatedly usable over large histories | Parse, cache fields, fold stacks, emit standard outputs efficiently | AgentProf implementation | RQ4 |

The chain is principled only if operations preserve the measured quantity and enough source association to connect effects to their producing activities. A uniform schema alone does not prove correct cross-layer attribution. Taggers produce fields, not a third scientific abstraction. Stack construction chooses a projection; it does not manufacture evidence. Ranking supports RQ2 but is not a new contribution. pprof/flamegraphs show compatibility and usability rather than novelty.

## Do operations and operation stacks suffice?

**Yes**, provided their roles remain precise.

An operation is a fielded observation associated with additive measures and traceable to the activity/effect it represents. An operation stack is an ordered projection of operation fields, selected at query time and folded for hierarchical multi-resolution attribution.

Everything else fits beneath them: intent attribution and mapping add fields; automatic induction proposes fields or boundaries; filters choose operations; weights choose the additive measure; rankers prioritize folded groups; pprof/flamegraphs render results. A new named model for lineage, hierarchy selection, confidence, navigation, or decision making would weaken the paper.

The model supports attribution and prioritization, not automatic causal proof. Saying a profile locates recurring annotated problems is coherent. Saying the stack proves why a problem occurred would require causal evidence beyond the two abstractions.

## What currently obscures the chain

1. “Agent trajectories have no hierarchy” is too literal. Many emit spans, tool nesting, plans, or execution trees. Execution occurrence is not automatically the cross-run responsibility hierarchy needed for profiling.
2. Requirement labels R1/R2/R3 collide with evaluation RQ1–RQ4.
3. “A flat GROUP BY cannot produce these views” is not essential. Databases can group by multiple fields; the contribution is an explicit responsibility projection, additive measures, hierarchical drill-down, and profiler-compatible results.
4. Operations do not automatically establish cross-layer responsibility. Tag inheritance and source association must be implemented and evaluated, not promoted to a third abstraction.
5. Automatic stack induction must remain an optional stack-construction mechanism, not the story.
6. The evaluation must distinguish model evidence from ranker evidence. One inconclusive released score does not invalidate the model; a strong ranker alone does not validate it.

## Evaluation architecture under fixed RQs

### RQ1 — Attribution

Establish that the same recorded population can be correctly attributed across recurring task, phase, action, and system-effect categories while conserving independently recorded token, time, process, file, network, or other measures. Compare flat, per-session, source-native, raw-action, and fixed semantic stacks under matched visible information. Do not define correctness using the same tag under evaluation.

### RQ2 — Real-problem localization

Establish that target-blind profiles concentrate independently annotated failures, unsafe effects, redundancy, or wasted work and reduce inspection versus strong fair alternatives. The AgentProcessBench constructions offer promising AP evidence but the conjunctive result remains inconclusive. It guides a fresh source or mechanism; it neither enters the final story nor narrows RQ2.

### RQ3 — Tag accuracy

Validate the dependency used by RQ1/RQ2: derived fields agree with independent identities on unseen agents/families. Strong designs leave agents, families, or domains out and test downstream sensitivity, not only label agreement.

### RQ4 — Cost

Measure full construction and repeated-query cost: parsing, field derivation, stack construction, folding, memory, and output size. The attractive systems claim is that one construction enables many inexpensive profiling views over the same recorded operations, not simply that offline work has zero runtime overhead.

RQ3 logically validates a dependency in RQ1/RQ2 even though it remains the third presented RQ. The overview should state that relationship without reordering or renaming RQs.

## Surprising upward directions

### 1. Profiles as richer agent evaluation than scalar leaderboards

Agent benchmarks reduce trajectories to success, reward, or judge score. AgentProf could profile where success cost, failures, unsafe actions, and wasted steps concentrate by task, phase, action, model, or tool. This connects to top-AI concerns without changing the thesis or adding an RQ. Evidence requires multiple real benchmark families, fixed target-blind stacks, and examples where agents with similar headline scores have different failure/cost profiles.

### 2. Longitudinal differential profiling

Compare model, prompt, tool-policy, or agent releases and reveal which recurring categories account for a cost/failure regression even when aggregate success barely changes. This uses the same operations/stacks and needs paired real workloads, fixed construction, independent measures, and evidence that the profile identifies responsible categories.

### 3. Safety effects as a profiled budget

Treat independently annotated unsafe tool operations as an additive measure attributed across recurring tasks, phases, tools, or policies, not merely isolated anomalies. This makes the original safety promise concrete under RQ2 and requires real safety traces, target-blind grouping, and fair inspection baselines.

## Most important unasked question

> **What concrete developer decision becomes possible or substantially cheaper because of the semantic profile, compared with having the same raw traces, native hierarchy, and visible fields?**

This is not a fifth RQ. It is the decision-level interpretation connecting RQ1 and RQ2. A fixed profile can demonstrate that it identifies the recurring category a developer should optimize, inspect, or constrain under a bounded inspection budget.

## Strictly larger attractive version

> **AgentProf is a general profiling substrate for agent development: it turns heterogeneous trajectories into reusable profiles of where quality failures, unsafe effects, wasted work, and resource consumption concentrate across tasks, phases, actions, agents, and system effects.**

This is the larger implication of, not a replacement for, “Agent observability needs profiling, not only debugging.” It preserves the two abstractions and four RQs.

Earning this scope would require multiple agents/frameworks, multiple independently measured quantities, fresh public failure/safety annotations, target-blind tags/ranking, comparisons with flat/session/native/raw-action views, held-out tag validation, full construction/repeated-query cost, and ideally one longitudinal/cross-agent decision example hidden by aggregate metrics.

## Drift and jargon risks

Reject:

- replacing the thesis with recurring behavior, hierarchy authority, or execution-tree wording;
- making semantic-vs-native hierarchy the main problem;
- named graphs, contracts, navigators, scopes, registries, confidence layers, or decision pipelines;
- promoting taggers, induction, ranking, pprof, or flamegraphs to independent core contributions;
- interpreting one failed/inconclusive construction as a failed RQ;
- shrinking quality/safety/cost ambition for reviewer comfort;
- claiming semantic tags are causal truth;
- claiming SQL/trace systems cannot aggregate, rather than explaining their default structure does not answer profiling questions;
- adding a fifth decision-utility RQ;
- inserting internal negative development results into the final positive story.

A simple safeguard is that every section must trace back to the thesis, an operation, an operation stack, or one of the four fixed RQs.

## Presentation targets, not scientific changes

- Abstract/Introduction: expose population-level decisions and the two-object chain directly.
- Background: distinguish execution structure from cross-run profiling responsibility without weakening the gap.
- Requirements: retain three needs but avoid labels colliding with RQ numbering.
- Design: centralize operations/stacks; demote taggers, induction, rankers, and formats.
- Evaluation overview: state how RQ3 validates the semantic assumption in RQ1/RQ2 and RQ4 establishes repeated usability.
- Related Work: compare tracing, clustering, localization, and profiling by their answered questions without categorical “cannot aggregate” claims.
- Conclusion: preserve the exact thesis and broad quality/safety/cost implication.

No idea-story entry is needed unless the root accepts a genuine narrative change.

## Final recommendation

**KEEP CANONICAL.** Accept only the clearer dependency chain, evidence separation, and larger experimental directions as guidance. Reject any proposal that replaces the thesis, changes four RQs, adds a third core abstraction, foregrounds inconclusive experiments, or turns controls into the contribution.
