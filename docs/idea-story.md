# Idea Story

Last updated: 2026-07-08
Stage at update: stage 9 paper integration / stage 10 prose polish / stage 11 reproducibility prep
Source/command: current branch `research/semantic-flamegraph-artifacts-v2`; `docs/evaluation.md`; `docs/design.md`; `docs/implementation.md`; `docs/background-related-work.md`; read-only audit of `docs/agentpprof-paper/main.tex`; latest outer commit `f2cdb8e9`; R320/R328/R392/R393/R394/R395/R396/R397/R398/R399/R402/R403/R404/R405/R407/R408/R409/R352/R356/R357/R360-R364 artifacts
Completeness: partial. The scoped profiling claim is paper-ready against the current labeled-trace evidence, and the post-R392 reviewer gate is closed by R393; broader human-utility, full ecosystem-compatibility, and universal boundary-discovery claims remain unsupported.

## Current State And Blocking Gate

Purpose: Give the project a single canonical entry point for the paper story, claim ledger, and next gate.

Draft paragraph: AgentSight's semantic profiling work is now in paper-integration mode. The design has been narrowed to two profiler abstractions, `operation` and `operation stack`. The strongest current claim is not human productivity, full automatic diagnosis, or complete trace-ecosystem compatibility. It is that operation/operation-stack profiling can localize, rank, and explain task-relevant failures, quality problems, and semantic boundaries in real labeled agent traces, while requiring less inspection work than flat summaries and less fragmentation than fixed-session drilldown. Fixed-session drilldown is the current trace-tree-shaped baseline in this benchmark; real OpenTelemetry/OpenInference/Phoenix-style span-tree imports are future baselines.

Evidence/claim dependency: The primary empirical gate is R320 over 6 tasks, 4 oracle-rich datasets, 34,539 operations, 3,699 positives, and 144 view/ranker policies. R333/R334/R337/R339/R344/R355 add work-budget, fragmentation, fixed-recall, sequence-scope, metric-surface, and oracle-depth checks. R354/R358 add executable profile-spec patch and boundary-derived-field actionability evidence. R402/R403/R404 add the maintained Rust operation-stack induction path: adjacent boundary scoring induces variable-depth stacks without a user-provided field chain, scores that induced view against the same hidden-label tasks, and exposes depth as a profile configuration knob rather than an automatic boundary detector. R327/R328 cover replayability and offline cost; R392 covers profile-spec input-source replay for local-session, agent-trace, and standard-trace inputs. The July 8 read-only audit of `docs/agentpprof-paper/main.tex` confirms that the English submodule still uses an older three-RQ structure and is missing the outer E3/E4 split and induction display; this is a recorded paper-organization gap, not a missing mandatory experiment for the current scoped claim. R395 checks that this main claim and the C4 verdict remain aligned across this file, the evaluation ledger, and paper drafts after the latest three-plus-one consolidation repair. R396 checks that the English and Chinese drafts build through temporary output locations, final logs have no unresolved references/citations, and the English ACM figure-description warning is gone. R405 records that the English paper submodule is read-only in the current workflow and remains behind the outer four-block organization. R407 converts R402/R403/R404 into a reader-facing induction table for the Chinese paper. R397 and R398 now treat the outer Chinese paper as the authoritative writable paper body: they keep R-numbered runs and internal checklist-style terms out of the main narrative, require the Chinese RQ1/E1--RQ4/E4 path and E2/E3/E4 role boundaries, and accept the English side only if it is synced or R405 records the read-only sync gap. R399 checks that the committed Chinese PDF contains the same main-display path as the TeX source, while English PDF/source drift is bounded by the R405 read-only gap instead of triggering submodule edits. R408 independently checks that the Chinese PDF contains the reader-facing induction display. R409 checks the worktree path, branch, AGENTS/CLAUDE submodule policy, unstaged-but-not-staged submodule state, R405/R397/R398/R399 gap-aware behavior, and direct-push safety. R338/R352/R356/R357/R359/R360/R361/R362/R364/R396/R397/R398/R399/R405/R408/R409 are scope, rubric, reviewer, structure, claim-scope, build-readiness, submodule-policy, or paper-organization checks, not new empirical profiler evidence.

Completeness: Partial. The main paper evidence is organized into three empirical profiling experiments plus one replayability/scope-control block, R393 records 4/4 final reviewer ACCEPT after fixing one dataset-caption blocker, R394 checks the maintained docs against the two-abstraction field-derivation wording, R395 checks the main claim-verdict alignment, R396 checks paper-build readiness, R405 records the English submodule sync gap under the read-only policy, R397 keeps R-numbered run history and internal checklist-style terms out of the main paper bodies, R398 keeps the writable Chinese paper aligned on RQ/E subsection count, E2/E3/E4 role boundaries, new-run role rule, main-display path, internal-style check, and venue-self-undercut check, R399/R408 keep the tracked Chinese PDF fresh, and R409 makes the read-only submodule/push-safety state explicit. The next gate is prose and figure/table polish, not more small experiments; the read-only English audit reinforces that this work belongs in the outer Chinese paper rather than the submodule.

## Downstream Document Index

Purpose: Point reviewers to the authoritative documents rather than leaving the project state in chat history.

Draft paragraph: The current related-work and novelty map is in `docs/background-related-work.md`. The mechanism and abstraction boundary are in `docs/design.md`. Runnable implementation status is in `docs/implementation.md`. The claim-to-experiment map, run tracker, result summary, and reproducibility checklist are in `docs/evaluation.md`. The Chinese paper draft is `docs/visexp/paper/main.tex`, and the English paper submodule is `docs/agentpprof-paper/main.tex`.

Evidence/claim dependency: These files are referenced by R338/R356/R360-R364 source-status checks and by the current paper text.

Completeness: Complete for current repo navigation; post-R392 independent review is accepted by R393.

## Intro P1: Problem And Stakes

Purpose: Establish why ordinary prompt/session/span views are too rigid for agent profiling.

Draft paragraph: AI agent executions are no longer a single prompt, response, or fixed trace tree. A realistic trajectory can contain LLM turns, browser and GUI actions, tool calls, API calls, filesystem and process effects, plans, subagents, user intents, and dataset labels for success, safety, repetition, redundancy, and human grouping. A profiler that binds analysis to one boundary, such as session, prompt, or span, cannot ask the same trajectory to expose task, phase, action, quality, or boundary structure at different depths.

Evidence/claim dependency: R279-R292 show heterogeneous public labeled trajectories entering the same operation layer. R286 shows the same operations fold into dataset, phase, semantic, action, and fixed-session stack depths.

Completeness: Supported for the sampled public trace families and local session fixtures. Not a claim about full conversion of every public agent dataset.

## Intro P2: Status Quo And Gap

Purpose: Place the work against classic profiling, trace processors, and LLM/agent observability systems.

Draft paragraph: Classic profilers already support folded stacks, labels, and tag-derived pseudo frames, and trace systems already support rich query processing over spans. Modern LLM observability tools expose sessions, traces, observations, evaluations, dashboards, and OpenTelemetry/OpenInference style schemas. The gap is not generic aggregation. The gap is a profiler object model for agent trajectories in which prompt, session, tool call, process, syscall, plan, and subagent are operation forms or fields, and stack shape is a query-time projection over those fields.

Evidence/claim dependency: `docs/background-related-work.md` maps pprof, flamegraphs, Perfetto, OpenTelemetry GenAI, OpenInference, LangSmith, Langfuse, Phoenix, AgentOps, AgentRx, TELBench/DRIFT, Holistic Evaluation, and AgentAtlas. R314 and R352 gate the related-work and evaluation-rubric framing.

Completeness: Supported as scoped novelty. The paper must not claim feature parity or complete compatibility with those ecosystems.

## Intro P3: Key Insight And Thesis

Purpose: State the first-principles abstraction.

Draft paragraph: The key insight is to separate the observed event from the profiling stack. AgentSight represents each relevant unit as an `operation`, a fielded weighted observation. An `operation stack` is an ordered recursive projection over operation fields chosen by the user, profile spec, mapping, tagger, query, or boundary-scoring induction. Explicit stack specs are reproducible views, not the only algorithm: the maintained Rust induction path scores adjacent cuts inside each contiguous operation segment and recursively stops when visible evidence no longer supports a material split. Mapping, tagging, and boundary backends derive fields before folding; they are first-class configuration mechanisms, but they do not create a third profiler abstraction. This lets the same prompt or action sequence fold at different depths depending on the diagnostic task.

Evidence/claim dependency: R281/R282/R285 validate generated mapping rules; R293/R321/R342 validate profile specs, predicates, rank rules, and explicit stack depth; R297/R358 validate boundary-derived fields as ordinary operation fields; R402/R403/R404 validate recursive operation-stack induction, hidden-label scoring of the induced view, and induced-depth sensitivity without oracle source fields; R394 checks that the Rust CLI, user guides, canonical docs, and paper drafts describe tagging/mapping/LLM tags/clustering as field derivation before stack folding rather than a third abstraction.

Completeness: Supported for deterministic and supervised field derivation. Fully unsupervised intent-boundary discovery is not supported.

## Intro P4: Artifact Or Method

Purpose: Identify what was built.

Draft paragraph: The evaluated artifact is the Rust `agentpprof` offline profiler and its dataset/conversion/evaluation harness. It reads operation JSONL, local agent-session traces, and standard trace containers after normalization; applies mapping, tagging, filtering, rank rules, and profile specs; folds recursive operation stacks; and emits folded stacks, JSON profiles, pprof-compatible profiles, SVG/HTML views, and analysis outputs. Local session and standard trace exchange are containers around the operation path, not separate profiler objects.

Evidence/claim dependency: R294/R303/R306/R353 validate trace and standard-trace exchange. R319 validates implementation/docs consistency. R327/R328 validate deterministic replay over 76 profile specs and 152 profiler invocations. R392 validates that profile specs can replay local-session, agent-trace, and standard-trace input sources with effective metadata rather than silently ignoring configured paths.

Completeness: Supported for the offline artifact path. Live eBPF overhead and full producer-ecosystem import are not part of the current claim.

## Intro P5: Claims And Evaluation Promise

Purpose: Tie the thesis to three empirical profiling experiments plus one replayability/scope-control block.

Draft paragraph: The evaluation is organized around three core empirical profiling experiments plus one replayability/scope-control block. E1 tests whether one operation layer can cover heterogeneous labeled agent trajectories and be recursively folded into multiple stack depths by explicit specs or induced boundary scoring. E2 is the main hidden-label localization/ranking benchmark over real labeled traces. E3 isolates mechanism and actionability through ranker, mapping, induced depth, transfer, case, boundary-field, and profile-spec patch evidence. E4 checks replayability, offline cost, and claim scope, while claim-integrity and reviewer checks constrain scope rather than adding empirical profiler evidence.

Evidence/claim dependency: E1 uses R279-R292/R286/R290/R291/R293/R321/R342 plus exchange checks and R402 recursive induction. E2 uses R320 plus R330/R331/R333/R334/R337/R339/R344/R355 and the R403 induced-stack ablation. E3 uses R324-R326/R335/R336/R340/R341/R345-R350/R354/R358 plus R404 induced-depth sensitivity. E4 uses R327/R328/R392 plus source-status and scope checks.

Completeness: Supported as a scoped profiling-paper evaluation. The paper should keep R-runs as provenance rather than the main narrative.

## Intro P6: Contributions, Scope, And Non-Goals

Purpose: Close the introduction with calibrated contributions and explicit non-claims.

Draft paragraph: The contributions are a two-abstraction semantic profiler model for agent trajectories, a configurable Rust implementation with mappings, tagging, query predicates, rank rules, profile specs, and trace import/export bridges, and a labeled-trace evaluation showing faithful localization/ranking and actionable optimization insights. The paper does not claim improved human analyst productivity, automatic discovery of all intent boundaries, metric dominance on every task, full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility, or a universal policy selector.

Evidence/claim dependency: The non-claims are enforced by R338/R352/R356/R357/R360/R361/R362/R364 and by the paper text. The positive claim is grounded in R320/R333/R334/R337/R339/R344/R354/R355/R358.

Completeness: Supported for current paper wording. Broader claims require additional experiments.

## Claim Ledger

| ID | Claim | Scope | Metric/evidence needed | Status |
|---|---|---|---|---|
| C1 | Agent trajectories can be represented as operations and recursively folded operation stacks without privileging prompt/session/span boundaries. | Public labeled trace samples, local agent sessions, and standard trace exchange fixtures. | Dataset coverage, operation counts, stack-depth sweep, profile-spec replay, exchange equality. | supported |
| C2 | Recursive operation stacks expose useful task, phase, action, quality, safety, and available boundary structure. | Dataset-provided labels and available oracle depths, especially OSWorld-Human and AgentNet. | V-measure, boundary F1, oracle-depth recall/F1, fragmentation, counterpoint rows. | supported with scoped limits |
| C3 | Mapping, tagging, and boundary-derived fields improve semantic aggregation as first-class field derivation before stack folding. | Deterministic mappings, held-out splits, leave-dataset-out stress, supervised boundary-field probes. | Compression, stack reduction, held-out boundary F1, patch acceptance, failure/counterpoint analysis. | partial |
| C4 | Operation-stack profiling localizes, ranks, and explains task-relevant failures, quality problems, and semantic boundaries on real labeled traces. | Six hidden-label tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human. | Precision@k, recall@budget, F1, AP/AUPRC-style score, nDCG, work-to-first-positive, fragmentation, actionability. | supported as hidden-label profiler benchmark |
| C5 | The artifact is replayable and cheap enough for offline artifact evaluation. | Tracked operation inputs, local-session/agent-trace/standard-trace input-source specs, and profile specs. | Deterministic semantic/raw hashes, sample/stack equality, input-source replay coverage, median/p95 runtime, source-status rows. | supported for offline path |

## Largest Plausible Claim

Purpose: Keep the ambitious target visible without promoting it before evidence exists.

Draft paragraph: The largest plausible current claim is that operation/operation-stack profiling gives a better inspection-work and fragmentation tradeoff than flat summaries and fixed-session drilldown for localizing task-relevant issues in real labeled agent traces, while also exposing actionable configuration knobs. A larger future claim would add true span-tree imports from production observability systems and broader tool/API/mobile oracle-rich families, then show the same tradeoff across more domains.

Evidence/claim dependency: Current large claim uses R320/R333/R334/R337/R339/R344/R354/R355/R358. Future claim needs real span-tree/OTel-style imported traces and stronger oracle-rich expansion datasets.

Completeness: Current claim is supported; larger claim is a future expansion hypothesis.

## Reviewer Attack Surface

| Attack | Current answer | Remaining risk |
|---|---|---|
| This is just flamegraphs with labels. | The novelty is agent operation records plus recursive multi-field operation-stack projections plus hidden-label localization scoring; flamegraphs are only one output. | Need keep related work precise around pprof tag frames and Perfetto SQL. |
| The evaluation is a long run log. | The paper is organized as RQ1/E1-RQ4/E4; R-runs are provenance, ablations, counterpoints, or gates. | `docs/evaluation.md` remains long and should stay a ledger, not the paper narrative. |
| Query-aware ranking leaks labels. | Rust visible inputs scrub oracle fields; hidden labels are used only for offline scoring; oracle policies are upper bounds. | Keep source-status and visible/hidden separation checks in every new run. |
| Fixed sessions sometimes cost less. | The claim is Pareto tradeoff, not metric dominance; fixed-session counterpoints remain explicit. | Do not write "always better" or "replaces drilldown." |
| Boundary detection is overclaimed. | Mappings and supervised boundary fields are field derivations; automatic discovery of all intent boundaries is not claimed. | Need stronger true subtask/solution-path oracles for broader boundary claims. |
| Human productivity is unmeasured. | Correct. Current claim is profiler fidelity/localization/actionability against hidden labels, not analyst productivity. | Run human/agent analyst study only if claiming productivity or time-to-answer. |

## Open Questions And Blockers

| Item | Status | Next action |
|---|---|---|
| Independent reviewer pass after the latest three-plus-one consolidation. | done | R393 records 4/4 final reviewer ACCEPT after fixing the Chinese dataset-caption blocker. |
| Full real span-tree baseline import. | out of current claim | Import a real OpenTelemetry/OpenInference/Phoenix-style trace only before making ecosystem-specific or real span-tree superiority claims. |
| Broader oracle-rich tool/API/mobile families. | optional expansion | Add only if the paper needs wider generality beyond the current four oracle-rich sources. |
| Human or agent analyst study. | optional future work | Use R315/R316 protocol only for human-utility or time-to-answer claims. |
| Claim-complete Chinese and English prose polish. | in progress | R395 keeps the claim-verdict alignment checked, R396 keeps paper-build readiness checked, R405 records the English submodule read-only sync gap, R397/R398 keep the writable Chinese paper on the exact three-plus-one organization, new-run role rule, main-display path, internal-style guard, and self-undercut guard, R399/R408 keep the tracked Chinese PDF fresh, and R409 records that direct push remains unsafe while ahead history contains a submodule gitlink update. The July 8 read-only English audit finds that the submodule still has the older RQ1/RQ2/RQ3 experiment organization, so continue tightening outer/Chinese prose and keep provenance in the ledger; do not edit the English submodule unless explicitly allowed. |

## Next Action

Purpose: Define the next concrete step.

Draft paragraph: The next step is prose polish and figure/table presentation for the accepted three-plus-one paper structure. Do not add another empirical block unless it strengthens e1, e2, e3, or e4 directly; instead, keep R-numbered provenance and internal process vocabulary out of the main paper bodies, keep limitations framed as scoped-claim boundaries rather than venue-readiness self-disclaimers, preserve the R395/R396/R397/R398/R399/R405/R408/R409 paper-integration gates, and keep English-submodule changes out of this workflow unless explicitly allowed. The only future expansion candidates that would materially expand the claim are a real OpenTelemetry/OpenInference/Phoenix-style span-tree import for ecosystem-specific claims or a same-input free-form text plus hidden semantic-label oracle for tagger-accuracy claims.

Evidence/claim dependency: R393 inspected the current branch, `docs/evaluation.md`, this file, and both paper drafts after the R392 E4 input-source replay update. It records four final ACCEPT verdicts, one resolved caption blocker, and no unresolved issues. R395 then checks that the central profiling claim, C4 verdict, fixed-session proxy wording, E4 non-accuracy scope, and must-not-claim boundaries still agree after the R380/R391 consolidation repair. R396 then checks that both paper drafts build in temporary output locations and that final logs/accessibility warnings are clean. R405 records the English submodule as read-only and behind the outer four-block organization. R397/R398 then check the writable Chinese main body, main-display path, E2/E3/E4 role boundaries, anti-run-ledger wording, and small-experiment guard while accepting English only as synced or R405-recorded gap. R399 checks the tracked Chinese PDF against the source display path and treats English PDF drift through the same R405 read-only gap. R408 checks the Chinese induction display in the tracked PDF. R409 records that the current worktree/branch is correct, the submodule is dirty but unstaged, and direct push is unsafe because ahead history contains a submodule gitlink update.

Completeness: Review gate complete; prose polish remains.
