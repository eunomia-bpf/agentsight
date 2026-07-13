# Idea Story

Last updated: 2026-07-10
Stage at update: supplement / evaluation-design recovery
Source/command: current branch `research/semantic-flamegraph-artifacts-v2`; independent paper/protocol review; native Claude/Codex trajectory audit; `docs/evaluation.md` section `2026-07-10 Evidence And Skill Iteration Recovery Plan`
Completeness: blocked. The previous paper-ready verdict is superseded by unresolved result-integrity, claim/evidence, baseline-fairness, source-fidelity, and external-validity issues. Writing skills and paper-polish work are frozen until the recovery claim gate passes.

## Current State And Blocking Gate

Purpose: Give the project a single canonical entry point for the paper story, claim ledger, and next gate.

Draft paragraph: AgentSight's semantic profiling work has two intended profiler abstractions, `operation` and `operation stack`, but its strongest empirical claim is not yet paper-ready. The current labeled-trace results are development evidence until the primary semantic metric uses an independent oracle, hidden labels are physically separated from construction, view/ranker policies are frozen before held-out scoring, and equally informed SQL/tag/fixed-tree baselines are compared. The immediate task is evidence recovery and source-fidelity repair, not prose or figure polish.

Evidence/claim dependency: The detailed recovery protocol, Codex/Claude trajectory audit, four reconstructed RQs, leakage worksheet, baseline policy, skill change specification, and execution phases are in `docs/evaluation.md`. Existing R320/R333/R334/R337/R339/R344/R354/R355/R358 and related artifacts remain candidate evidence, but their paper role and supported wording must be re-gated after protocol reconstruction. Internal R338/R393-style acceptance artifacts are consistency evidence only and cannot close a result-integrity blocker.

Completeness: Blocked at source fidelity and result integrity. The next action is Phase 1 of the recovery plan: repair Codex discovery/identity/token semantics and build one label-stripped held-out localization smoke task with a strongest-baseline comparison. No paper or writing-skill edit is authorized by this state update.

## Downstream Document Index

Purpose: Point reviewers to the authoritative documents rather than leaving the project state in chat history.

Draft paragraph: The current related-work and novelty map is in `docs/background-related-work.md`. The mechanism and abstraction boundary are in `docs/design.md`. Runnable implementation status is in `docs/implementation.md`. The authoritative recovery plan, claim-to-experiment map, run tracker, result summary, and reproducibility checklist are in `docs/evaluation.md`.

Evidence/claim dependency: These files are referenced by R338/R356/R360-R364 source-status checks and by the current paper text.

Completeness: Complete for canonical project-memory navigation. The earlier R393 acceptance is superseded; the next independent review occurs only after evidence freeze.

## Intro P1: Problem And Stakes

Purpose: Establish why ordinary prompt/session/span views are too rigid for agent profiling.

Draft paragraph: AI agent executions are no longer a single prompt, response, or fixed trace tree. A realistic trajectory can contain LLM turns, browser and GUI actions, tool calls, API calls, filesystem and process effects, plans, subagents, user intents, and dataset labels for success, safety, repetition, redundancy, and human grouping. A profiler that binds analysis to one boundary, such as session, prompt, or span, cannot ask the same trajectory to expose task, phase, action, quality, or boundary structure at different depths.

Evidence/claim dependency: R279-R292 show heterogeneous public labeled trajectories entering the same operation layer. R286 shows the same operations fold into dataset, phase, semantic, action, and fixed-session stack depths.

Completeness: Partial. External operation conversion is demonstrated, but local Codex discovery/identity fidelity and general coverage must be repaired before this supports a paper claim.

## Intro P2: Status Quo And Gap

Purpose: Place the work against classic profiling, trace processors, and LLM/agent observability systems.

Draft paragraph: Classic profilers already support folded stacks, labels, and tag-derived pseudo frames, and trace systems already support rich query processing over spans. Modern LLM observability tools expose sessions, traces, observations, evaluations, dashboards, and OpenTelemetry/OpenInference style schemas. The gap is not generic aggregation. The gap is a profiler object model for agent trajectories in which prompt, session, tool call, process, syscall, plan, and subagent are operation forms or fields, and stack shape is a query-time projection over those fields.

Evidence/claim dependency: `docs/background-related-work.md` maps pprof, flamegraphs, Perfetto, OpenTelemetry GenAI, OpenInference, LangSmith, Langfuse, Phoenix, AgentOps, AgentRx, TELBench/DRIFT, Holistic Evaluation, and AgentAtlas. R314 and R352 gate the related-work and evaluation-rubric framing.

Completeness: Partial. The proposed gap is plausible, but novelty depends on the strongest SQL/tag/fixed-tree/trace-query baselines and must be narrowed if they reproduce the same value.

## Intro P3: Key Insight And Thesis

Purpose: State the first-principles abstraction.

Draft paragraph: The key insight is to separate the observed event from the profiling stack. AgentSight represents each relevant unit as an `operation`, a fielded weighted observation. An `operation stack` is an ordered recursive projection over operation fields chosen by the user, profile spec, mapping, tagger, query, or boundary-scoring induction. Explicit stack specs are reproducible views, not the only algorithm: the maintained Rust induction path scores adjacent cuts inside each contiguous operation segment and recursively stops when visible evidence no longer supports a material split. Mapping, tagging, and boundary backends derive fields before folding; they are first-class configuration mechanisms, but they do not create a third profiler abstraction. This lets the same prompt or action sequence fold at different depths depending on the diagnostic task.

Evidence/claim dependency: R281/R282/R285 validate generated mapping rules; R293/R321/R342 validate profile specs, predicates, rank rules, and explicit stack depth; R297/R358 validate boundary-derived fields as ordinary operation fields; R402/R403/R404 validate recursive operation-stack induction, hidden-label scoring of the induced view, and induced-depth sensitivity without oracle source fields; R394 checks that the Rust CLI, user guides, canonical docs, and paper drafts describe tagging/mapping/LLM tags/clustering as field derivation before stack folding rather than a third abstraction.

Completeness: Partial. The mechanisms exist, but their independent contribution and semantic correctness remain behind G1--G4; fully unsupervised intent-boundary discovery is unsupported.

## Intro P4: Artifact Or Method

Purpose: Identify what was built.

Draft paragraph: The evaluated artifact is the Rust `agentpprof` offline profiler and its dataset/conversion/evaluation harness. It reads operation JSONL, local agent-session traces, and standard trace containers after normalization; applies mapping, tagging, filtering, rank rules, and profile specs; folds recursive operation stacks; and emits folded stacks, JSON profiles, pprof-compatible profiles, SVG/HTML views, and analysis outputs. Local session and standard trace exchange are containers around the operation path, not separate profiler objects.

Evidence/claim dependency: R294/R303/R306/R353 validate trace and standard-trace exchange. R319 validates implementation/docs consistency. R327/R328 validate deterministic replay over 76 profile specs and 152 profiler invocations. R392 validates that profile specs can replay local-session, agent-trace, and standard-trace input sources with effective metadata rather than silently ignoring configured paths.

Completeness: Partial. The offline artifact path exists, but Codex source identity, token semantics, worktree discovery, and final cost evidence fail or remain blocked.

## Intro P5: Claims And Evaluation Promise

Purpose: Tie the thesis to the four recovery RQs and their falsifiable decision rules.

Draft paragraph: The recovery evaluation is planned around four falsifiable blocks: RQ1 tests abstraction and semantic construct validity against equally informed baselines; RQ2 rebuilds localization under physically hidden labels and a frozen held-out protocol; RQ3 isolates mechanisms and, only if claimed, analyst utility; RQ4 tests multi-project generalization and offline/capture cost. The earlier three-plus-one organization is historical evidence provenance, not a passed claim gate.

Evidence/claim dependency: Existing R-runs are candidate inputs to reconstruct, not final support. Each new primary block must use the success/non-inferiority threshold, leakage worksheet, baseline parity, oracle, and failure action in `docs/evaluation.md`.

Completeness: Planned and blocked at G0--G4. No current RQ has passed the recovery claim gate.

## Intro P6: Contributions, Scope, And Non-Goals

Purpose: Close the introduction with calibrated contributions and explicit non-claims.

Draft paragraph: The contribution candidates are a two-abstraction semantic profiler model for agent trajectories, a configurable Rust implementation with mappings, tagging, query predicates, rank rules, profile specs, and trace import/export bridges, and a blinded labeled-trace evaluation of localization and inspection tradeoffs. The third candidate remains a hypothesis until the recovery experiments pass. The paper does not claim improved human analyst productivity, automatic discovery of all intent boundaries, metric dominance on every task, full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility, or a universal policy selector.

Evidence/claim dependency: The implementation candidate is inspectable now. The positive evaluation candidate depends on G1--G7 and the independent claim gate; internal scope/checker artifacts do not supply that evidence.

Completeness: Partial for model/implementation; blocked for the positive empirical contribution.

## Claim Ledger

| ID | Claim | Scope | Metric/evidence needed | Status |
|---|---|---|---|---|
| C1 | Agent trajectories can be represented as operations and recursively folded operation stacks without privileging prompt/session/span boundaries. | Public labeled trace samples, local agent sessions, and standard trace exchange fixtures. | Dataset coverage, operation counts, stack-depth sweep, profile-spec replay, exchange equality, source-fidelity regression. | partial; local source fidelity blocked |
| C2 | Recursive operation stacks expose useful task, phase, action, quality, safety, and available boundary structure. | Dataset-provided labels and available oracle depths, especially OSWorld-Human and AgentNet. | Independent oracle, V-measure, boundary F1, oracle-depth recall/F1, fragmentation, strongest baselines. | partial; construct validity blocked |
| C3 | Mapping, tagging, and boundary-derived fields improve semantic aggregation as first-class field derivation before stack folding. | Deterministic mappings, held-out splits, leave-dataset-out stress, supervised boundary-field probes. | Compression, stack reduction, held-out boundary F1, patch acceptance, failure/counterpoint analysis. | partial |
| C4 | Operation-stack profiling localizes, ranks, and explains task-relevant failures, quality problems, and semantic boundaries on real labeled traces. | Six hidden-label tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human. | Frozen label-stripped split, scorer isolation, equal tuning, strongest baselines, AP/recall/work/fragmentation Pareto result. | blocked; current tasks are development evidence |
| C5 | The artifact is replayable and cheap enough for offline artifact evaluation. | Tracked operation inputs, local-session/agent-trace/standard-trace input-source specs, and profile specs. | Correct identity/token semantics, deterministic hashes, input-source replay coverage, median/p95 runtime, CPU/RSS/output size. | partial; source fidelity and cost blocked |

## Largest Plausible Claim

Purpose: Keep the ambitious target visible without promoting it before evidence exists.

Draft paragraph: The largest plausible claim hypothesis is that operation/operation-stack profiling gives a better inspection-work and fragmentation tradeoff than equally informed flat, fixed-tree, SQL/tag, and trace-query baselines for localizing task-relevant issues across multiple real labeled agent-trace families, while exposing actionable configuration knobs at practical offline cost. This is a target to falsify, not current paper wording.

Evidence/claim dependency: Existing R320/R333/R334/R337/R339/R344/R354/R355/R358 are development evidence. Promotion requires the frozen RQ2 protocol, strongest baselines, multi-project transfer, mechanism isolation, and RQ4 cost gate.

Completeness: Unsupported as final wording; retained as the maximal recovery hypothesis.

## Reviewer Attack Surface

| Attack | Current answer | Remaining risk |
|---|---|---|
| This is just flamegraphs with labels. | The novelty is agent operation records plus recursive multi-field operation-stack projections plus hidden-label localization scoring; flamegraphs are only one output. | Need keep related work precise around pprof tag frames and Perfetto SQL. |
| The evaluation is a long run log. | The paper is organized as RQ1/E1-RQ4/E4; R-runs are provenance, ablations, counterpoints, or gates. | `docs/evaluation.md` remains long and should stay a ledger, not the paper narrative. |
| Query-aware ranking leaks labels or is tuned post hoc. | Current runtime scrubbing is insufficient to prove blindness because author label access, physical label separation, freeze point, split, and equal tuning budget were not recorded for every rule. | Rebuild RQ2 with the mandatory leakage worksheet and a label-stripped held-out artifact/scorer split. |
| Fixed sessions sometimes cost less. | The claim is Pareto tradeoff, not metric dominance; fixed-session counterpoints remain explicit. | Do not write "always better" or "replaces drilldown." |
| Boundary detection is overclaimed. | Mappings and supervised boundary fields are field derivations; automatic discovery of all intent boundaries is not claimed. | Need stronger true subtask/solution-path oracles for broader boundary claims. |
| Human productivity is unmeasured. | Correct. Current claim is profiler fidelity/localization/actionability against hidden labels, not analyst productivity. | Run human/agent analyst study only if claiming productivity or time-to-answer. |

## Open Questions And Blockers

| Item | Status | Next action |
|---|---|---|
| Independent reviewer pass after the latest three-plus-one consolidation. | superseded | R393 records internal acceptance, but the trajectory audit shows verdict priming and checker-oriented review. Repeat only after evidence freeze with paper/primary results and no desired verdict or internal pass artifacts. |
| Source fidelity for Codex trajectories. | blocking | Repair repo/worktree discovery, raw metadata IDs, parent linkage, token-event semantics, and error normalization; require an expected/observed coverage manifest. |
| Blind hidden-label localization protocol and strongest baselines. | blocking | Build one label-stripped held-out smoke task, freeze the policy, isolate the scorer, and compare SQL/tag/fixed-tree baselines before expanding. |
| Independent semantic oracle for RQ1. | blocking | Replace the by-construction mixing result with an external/human/dataset oracle or remove semantic-accuracy wording. |
| Full real span-tree baseline import. | required for broad baseline/ecosystem claims | Import a real OpenTelemetry/OpenInference/Phoenix-style trace or narrow the comparison claim. |
| Broader oracle-rich tool/API/mobile families. | required for broad generality | Add only after the core frozen protocol produces a nontrivial result. |
| Human or agent analyst study. | required only for human-utility wording | Run a blinded study or keep productivity/time-to-answer out of scope. |
| Claim-complete Chinese and English prose polish. | blocked | Resume only after the independent claim gate passes; do not edit the English submodule unless explicitly authorized. |

## Next Action

Purpose: Define the next concrete step.

Draft paragraph: Freeze paper prose and writing skills. First repair Codex source fidelity and produce one reproducible label-stripped held-out localization smoke task with scorer isolation and an equally informed SQL/fixed-tree baseline. Review that evidence before expanding the matrix. The detailed five-step first batch and stop conditions are in `docs/evaluation.md`.

Evidence/claim dependency: Phase 1 must reconcile expected versus discovered sessions, preserve parent/child identity, define token-event semantics, and normalize raw failures. Phase 2 may start only after G0 passes and must record the RQ2 leakage worksheet, freeze commit/config, label-stripped input hash, scorer-only label hash, tuning budget, and failure action.

Completeness: Blocked. No paper, figure-polish, or writing-skill action clears the current gate.
