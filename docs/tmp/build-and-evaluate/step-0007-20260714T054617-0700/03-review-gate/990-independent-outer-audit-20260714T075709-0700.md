# Step 0007 Independent Outer Audit

- Timestamp: `2026-07-14T07:57:09-07:00`
- Phase: `BUILD_AND_EVALUATE`
- Gate: `REVIEW_GATE` / independent outer audit
- Paper: `docs/paper/main.tex` and its compiled PDF
- Venue posture: AAAI 2027, with both systems and AI/ML evidentiary bars because the paper combines an observability/profiling system with learned or derived semantic fields
- Verdict: **RETURN TO TARGETED WRITE_GATE REPAIR, THEN RUN ONE COMPLETE REUSED-ASSET RQ3 EXPERIMENT**

## 1. Executive judgment

Step 0007's experiment is real, complete, and scientifically useful. I independently recomputed the central counts from the recorded aggregate, operation JSONL, and folded profile: all 20 real Codex tasks completed; all 20 concurrent negative controls were observed; the scoped join produced 1,520 true positives, 0 false positives, and 54 false negatives, for 100% precision and 96.569% recall; none of 1,629 negative-control effects joined; the current AgentProf profile preserved all 1,520 selected operation samples and their category mass. This supports the tested RQ1 hypothesis for the stated fixed suite and source-scope definition. It is not a smoke result and should not be discarded or followed by another slightly different RQ1 benchmark.

The outer cycle nevertheless cannot pass as written. The WRITE gate ran the full 11-round `iter-refine-writing` workflow during `BUILD_AND_EVALUATE`, including an abstract/introduction rebuild and substantial structural rewriting. That violates the phase policy and the user's frozen-story instruction. More importantly, the resulting paper contains two direct implementation contradictions: it implies direct reading of AgentSight recordings although the current CLI requires conversion to supported operation input, and it describes the Rust automatic stack inducer as TF-IDF/cosine based although the current Rust implementation is token-set/Jaccard based. The broad current-tool gap also overlooks current LangSmith Insights and Datadog Patterns capabilities already material to the novelty claim.

These problems require a **small, factual WRITE repair**, not a new story, new RQs, or a wholesale paper rewrite. The exact thesis—“Agent observability needs profiling, not only debugging.”—and the four fixed RQs remain intact and must stay intact. After that repair, the highest-value next experiment is the still-open RQ3 task/phase/action component. It should reuse the existing converted public traces, existing AgentProf operation path, and existing leave-one-dataset-out machinery, while ensuring that scorer-only reference labels are not copied into predictor inputs. One complete held-out experiment is enough; do not add a new benchmark, model family, metric family, or cutoff sweep.

## 2. Independence and inputs

I applied the `auto-research-orchestrator` outer-audit requirements and the whole-paper, external-search, and cross-domain standards of `iter-review-critique`.

I read:

- the complete current paper source and PDF, figures, and bibliography;
- every Step 0007 EXPERIMENT-gate report, including all five plan/review rounds, approved plan, real preflight, full-run report, independent result review, and gate exit;
- every Step 0007 WRITE-gate report and all eleven writing-round reports;
- `docs/user-instruction.md`, the complete `docs/idea-story.md`, `docs/evaluation.md`, `docs/background-related-work.md`, `docs/design.md`, and `docs/implementation.md`;
- the raw Step 0007 aggregate, selected-operation JSONL, current AgentProf result/profile, the replay adapter, and the relevant historical scoring path;
- the current implementation code needed to check the ingestion and automatic-inducer statements;
- the existing RQ3-related reusable scripts and outputs, especially R251, R252, R283–R285, R297, R299, R355, R366, and R400/R404 families where relevant.

Blind-read disclosure: complete independence from prior context was impossible because the task and earlier trajectory context exposed that Step 0007 was an RQ1 result and that story drift was a concern. I nevertheless formed the initial paper-level objection map from the paper itself before using the gate reports to attribute causes, and I independently recomputed the experiment's central quantities instead of trusting the gate booleans.

## 3. EXPERIMENT_GATE audit

### 3.1 What was tested

The approved hypothesis was appropriately narrower than the whole RQ: on the fixed 20-task real Codex suite, the historical R114-compatible AgentSight source-scope path should select the effects belonging to the responsible process/tool lineage, reject concurrent negative-control effects, and feed current AgentProf without losing selected weight.

This is the correct unit of interpretation. One experiment supports or rejects its tested hypothesis; it does not by itself redefine the paper-level RQ, thesis, or story.

### 3.2 Plan and execution quality

The plan covered the scientific essentials: fixed real tasks, concurrent negative controls, explicit lineage/tool scope, a real preflight, a full run, and result review. Five plan iterations were more than necessary, but they converged on a simple executable design rather than introducing new infrastructure.

The one-task preflight was valid and unfavorable—84.694% recall—yet the pipeline did not tune on it or stop. It proceeded to the complete 20-task run, as it should. All intended real tasks and controls reached a terminal outcome. This satisfies the user's requirement to run complete experiments rather than treating two or three smoke cases as evidence.

### 3.3 Independent recomputation

From the recorded artifacts I recomputed:

| Quantity | Independently checked value |
|---|---:|
| Completed real tasks | 20 / 20 |
| Observed negative controls | 20 / 20 |
| True positives | 1,520 |
| False positives | 0 |
| False negatives | 54 |
| Precision | 100% |
| Recall | 96.569% |
| Negative-control effects | 1,629 |
| Negative-control effects joined | 0 |
| AgentProf operation rows | 1,520 |
| AgentProf total/sample weight | 1,520 |
| Unique folded stacks | 152 |

The profile category mass also reconciles exactly to 1,520: dependency 121, edit 380, failure 39, read 723, and test 257. The replay adapter consumes persisted process and tool identifiers from the source suite; it does not silently replace the suite's scorer with a new semantic classifier.

### 3.4 Scientific interpretation

The tested hypothesis is supported. Together with prior RQ1 evidence for multi-granularity and multi-weight separation, Step 0007 permits a positive cumulative RQ1 answer under a precise boundary:

- the result covers the fixed 20-task suite;
- “responsible” means membership in the predeclared scoped process/tool lineage, not arbitrary causal responsibility;
- the capture path is the historical R114-compatible AgentSight 0.2.37 path;
- task categories come from the fixed manifest, not automatic task inference;
- current AgentProf is tested for conversion/folding and weight preservation after selection, not for directly discovering the source lineage.

No further RQ1 benchmark, score, cutoff, or slightly altered replay is justified now. The experiment is useful precisely because it closes the tested source-fidelity question without pretending to answer every possible form of attribution.

### 3.5 Experiment complexity and waste

The experiment itself stayed acceptably simple and reused an existing real suite. The avoidable cost was procedural: five plan rounds restated overlapping details. Future plans can retain scientific review while removing repeated restatement. This is not a reason to add another gate or contract. The existing Markdown plan/review/result artifacts are sufficient.

## 4. WRITE_GATE and frozen-contract audit

### 4.1 Phase-policy violation

The orchestrator's `BUILD_AND_EVALUATE` policy permits targeted evidence integration, not a full paper-wide writing refinement or abstract/introduction/story rebuild. Step 0007 nevertheless invoked all eleven `iter-refine-writing` rounds. The progress checker likewise reports two post-bootstrap full-writing runs as forbidden for this phase.

Round 4 is explicit: it is titled “Abstract and Introduction Rebuild,” reorders the introduction into a prescribed problem/root-cause/existing-gap sequence, and derives an eight-sentence abstract from that reordered introduction. Round 1 also rebuilt the abstract. This is not a local RQ1 result update. It created unnecessary opportunity for narrative drift after the user had designated the restored submodule story as authoritative.

### 4.2 What remained stable

The following high-level contract survived and must not be changed during repair:

- exact thesis: **Agent observability needs profiling, not only debugging.**
- RQ1: attribution;
- RQ2: real-problem correspondence/localization;
- RQ3: tag accuracy;
- RQ4: profiling cost;
- two core abstractions: operations and operation stacks;
- the positive, broad profiling motivation rather than a retreat to a run-local debugging or “tree replacement” story.

### 4.3 Unauthorized narrative and structural drift

The current paper differs broadly from the canonical `docs/agentpprof-paper/main.tex`: the design structure was split and reorganized, headings changed, a new scope section was added, the implementation expanded, and the abstract/introduction were repeatedly reconstructed. Vocabulary associated with an earlier rejected drift also became more prominent: “responsibility,” “recurring,” and “query-time profile hierarchies” now carry more of the framing than in the canonical version.

Those terms are not individually forbidden. The defect is that a general writing workflow treated the current body as the source of truth and optimized a new story around them, instead of treating the canonical story plus `docs/idea-story.md` as the immutable narrative source. The repair should compare only the changed structural/narrative portions against the canonical paper and restore canonical wording/organization where the writing rounds—not new evidence—caused the change. It must not discard valid Step 0007 evidence or wholesale revert unrelated improvements.

### 4.4 Direct artifact-truth contradictions

These are blockers because they describe mechanisms the artifact does not currently implement.

1. **Direct AgentSight ingestion.** The paper says AgentProf reads “source-linked AgentSight recordings.” `docs/implementation.md` states that the current CLI has no direct AgentSight-recording reader and that AgentSight evidence must first be converted to supported operation input. Step 0007 itself used a thin replay adapter. The paper may describe an AgentSight-linked path, but it must explicitly identify the conversion/adapter boundary and must not imply native direct ingestion.

2. **Automatic inducer algorithm.** The paper says automatic stack construction scores adjacent operations using TF-IDF cosine shifts, structured-field changes, and group consistency. The current Rust inducer uses visible token-set/Jaccard distance, field changes, balance, and query-term overlap. TF-IDF/K-Means belongs to the optional Python clustering/rule-authoring backend. These two backends must be described separately.

### 4.5 Formatting and local consistency defects

The current PDF builds without undefined citations or conventional undefined-reference warnings. However, AAAI's unnumbered section headings make several `\S\ref{...}` expressions render as a bare “§” or “§–§”. These references are visibly broken even though LaTeX does not warn. Replace them locally with section-title references or another AAAI-compatible form.

The repository memory also contains stale next-step language in `docs/design.md` and `docs/implementation.md` that still points to TraceElephant/RQ2 although cumulative RQ2 review has already finished and Step 0007 has moved on. Update those statements only as project-memory housekeeping; do not let them reopen RQ2.

## 5. Whole-paper scientific review

### 5.1 Strongest contribution

The paper's scientifically interesting core is not generic clustering. It is the combination of:

- source-linked, fine-grained system effects and agent operations;
- additive weights that remain conserved when folded;
- user-selectable, pprof-compatible operation-stack projections over cross-run evidence;
- the ability to ask resource, failure, and behavior questions at different semantic granularities without replacing the execution trace.

This remains a potentially strong systems/AI-observability contribution. It challenges the assumption that run-local trace structure is sufficient for recurring-behavior analysis while retaining traceable, weighted system evidence.

### 5.2 Current-tool and novelty attack

The existing-tools paragraph is too broad. It says current standard interfaces do not derive recurring semantic categories from histories or query-time hierarchies. Current official product documentation provides material counterexamples:

- [LangSmith Insights](https://docs.langchain.com/langsmith/insights) automatically analyzes traces, detects common agent behaviors and failure modes, creates hierarchical categories/subcategories, and aggregates metrics such as error rate, latency, and cost; categories can be reused in later reports.
- [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) automatically clusters production interactions using summaries, embeddings, dimensionality reduction, and density clustering, then builds a topic hierarchy. Its [Patterns API](https://docs.datadoghq.com/api/latest/llm-observability/list-patterns-topics-with-clustered-points/) exposes hierarchy depth and clustered-point/topic metrics including status, duration, token counts, estimated cost, and evaluations.
- [pprof](https://github.com/google/pprof/blob/main/doc/README.md) already supports tags as extra dimensions and `tagroot`/`tagleaf` pseudo-frames.
- [OpenTelemetry GenAI metrics](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-metrics.md) define standard token-usage and duration metrics with attributes.

These sources do **not** eliminate AgentProf's novelty. They invalidate a generic claim that production tools lack cross-run categorization, metric aggregation, or hierarchical topic views. The paper should distinguish AgentProf on source-linked cross-layer effect attribution, additive conservation, and selectable pprof-compatible operation-stack projections. `docs/background-related-work.md` already recognizes Datadog Patterns, so the paper's omission is also an internal information-flow failure.

### 5.3 RQ2 protocol attack

The three public workloads are valuable and should remain. However, the paper's AP and Work@50/80 measures are custom group-concentration/inspection constructs rather than the benchmarks' published primary protocols:

- [AgentProcessBench](https://arxiv.org/abs/2603.14465) and its [official repository](https://github.com/RUCBM/AgentProcessBench) emphasize step-level micro accuracy and first-error accuracy over 1,000 trajectories/8,509 labels.
- [HINTBench](https://arxiv.org/abs/2604.13954) evaluates risk detection, risky-step localization, and failure type over 629 trajectories.
- [TraceElephant](https://aclanthology.org/2026.acl-long.912/) evaluates responsible-agent/decisive-step attribution over 220 real failed traces.

The cumulative experiments support the literal RQ2 question—whether target-blind profile groups correspond to independently labeled real problems and surface them early relative to a raw-action view—over the tested settings. They do not yet establish general analyst-productivity improvement or dominance over current product pattern-analysis systems. The TraceElephant 50%-recall point is also more favorable than the predeclared 80%-recall point, so wording such as “the workloads' reported operating points” must not imply those are the benchmarks' published primary operating points.

This is a claim-calibration issue, not a request for another RQ2 benchmark or cutoff. Preserve the positive RQ2 conclusion but state exactly what the complete experiments establish.

## 6. Per-RQ cumulative synthesis

### RQ1 — attribution: **answered positively within stated scope**

Step 0007 supplies the missing exact-lineage and weight-preservation evidence on 20 real Codex tasks with concurrent controls. Earlier evidence supplies multiple aggregation granularities and multiple weights. The answer must remain tied to scoped source/tool lineage and must not be inflated into arbitrary causal responsibility or current native AgentSight ingestion.

### RQ2 — real-problem correspondence: **answered positively for the tested correspondence/early-concentration construct**

The three complete public workloads show that target-blind operation-stack groups can enrich independent problem labels and expose them earlier than the raw-action comparator at the reported AgentProf operating points. The answer does not establish universal failure localization, human analyst time, or superiority to all current product baselines. Do not reopen RQ2 merely by changing dataset, score, or cutoff.

### RQ3 — tag accuracy: **not yet fully answered**

The OSWorld-Human result supports held-out group-boundary fidelity. It does not answer the fixed task/phase/action tag-accuracy components across agent families. R251 is an association proxy and explicitly does not establish human semantic adequacy. R283–R285 demonstrate leave-dataset-out mapping/stack behavior, but their task/dataset and phase/action comparisons use fields that participate in the derivation and therefore cannot by themselves serve as independent tag-accuracy evidence.

### RQ4 — cost: **answered for tested post-session profile construction**

The current-binary measurements support practical, predictable post-session profile-construction cost over the tested 27,765 operations. Cache evidence is narrower and comes from a predecessor path on one fixed input. The answer does not include all capture, labeling, or model-inference costs, but the current paper mostly defines RQ4 as after-session construction and can retain that positive conclusion.

## 7. Research taste and direction audit

The paper is strongest when it advances one simple but non-obvious idea: agent observability needs a profiling view over recurring, weighted behavior, not only run-local debugging traces. It becomes weaker when writing rounds replace that idea with accumulated terminology—responsibility categories, semantic hierarchies, recurring groups, query-time projections—without making the underlying distinction sharper.

The next work should therefore enlarge evidence for the existing thesis, not invent a smaller thesis or another abstraction. RQ3 is the right next target because it tests whether the semantic axes that make the profiles useful are actually accurate. A positive RQ3 answer would directly strengthen the core story. Another RQ1 replay or RQ2 benchmark would mostly add breadth without changing the paper-level answer.

The positive story should be preserved. Negative or inconclusive historical experiments need not dominate the submitted narrative, but they must continue to constrain what the paper says. The proper response to imperfect evidence is first to improve the experiment for the unchanged hypothesis—not silently rewrite the hypothesis or substitute a smaller RQ.

## 8. Next decisive experiment: simple, complete, and reuse-first

After the targeted paper repair, route to `EXPERIMENT_GATE` for exactly one RQ3 experiment.

### Fixed RQ and tested hypothesis

- **RQ:** RQ3, “How accurate are the tags?”
- **Tested hypothesis:** using existing AgentProf derivation/mapping machinery and existing public agent-trace operations, task, phase, and action tags learned or configured without the held-out corpus recover independently supplied reference labels on that corpus with useful accuracy and coverage.

The experiment must not change RQ3. Its conclusion may calibrate the supported claim, but a disappointing first result should trigger at most the allowed plan/mechanism refinement, not a new RQ or smaller story.

### Reused assets

- reuse the nine already converted public trace corpora listed by R285;
- reuse `script/operation_leaveout_eval.py` as the execution skeleton;
- reuse the current AgentProf operation-file/profile path;
- reuse existing corpus splits and official/native annotations where they are genuinely independent reference labels;
- reuse existing mapping/tagging code rather than introducing a new model.

The existing R283–R285 summary metric must **not** simply be relabeled as RQ3 accuracy: task/dataset and phase/action fields can leak the reference into derivation. For each axis, remove the scored reference field and any direct alias from predictor input; use the withheld reference only in the scorer. If an axis lacks an independent reference in the existing corpora, report it as unavailable rather than manufacturing labels or adding another benchmark.

### Minimal protocol

1. Use leave-one-corpus-out evaluation over every eligible existing corpus.
2. Predict each eligible task, phase, and action axis from the remaining visible operation context; keep reference labels scorer-only.
3. Report one primary accuracy summary across the eligible axes/corpora plus label coverage. A per-axis table is diagnostic, not three new experiments.
4. Run every eligible held-out corpus to completion with the current AgentProf path and verify folded weight conservation.
5. Interpret only the fixed RQ3 hypothesis. Do not add model comparisons, new corpora, score sweeps, or cutoff sweeps unless the approved plan shows they are indispensable to answer RQ3.

### Completion condition

The experiment is complete when all eligible existing corpora and all independently scoreable task/phase/action axes have terminal results, reference fields have been excluded from predictor inputs, current AgentProf has consumed and folded the predicted fields without weight loss, and the result review can state a scoped paper-level answer for the open RQ3 components. Missing independent labels are an explicit scope boundary, not a reason to wait for a human or design a new annotation pipeline.

## 9. Capability-learning assessment

This cycle exposes one stable repository-specific failure: paper-writing review passed claims about ingestion and backend algorithms without checking `docs/implementation.md` and the current CLI/code. A concise future repository instruction could require that any paper statement about AgentProf input support or automatic stack induction be checked against those sources before WRITE passes. The concrete current facts are: no native direct AgentSight-recording reader, and the Rust inducer is Jaccard-based while TF-IDF/K-Means is optional Python clustering/rule authoring.

This does not justify a new skill. Existing consistency and whole-paper review skills already cover artifact truth; the failure was in routing and application. The full-writing phase violation is likewise an orchestrator-usage error, not evidence that another gate or contract is needed. No shared skill change should be made from this audit.

## 10. Ranked objections and routing

### Blockers before the next outer cycle can pass

1. **Artifact contradiction:** direct AgentSight ingestion is implied but not implemented. Route: targeted WRITE repair.
2. **Artifact contradiction:** the Rust automatic inducer is described as TF-IDF/cosine rather than Jaccard/token-set based. Route: targeted WRITE repair.
3. **Frozen-story/phase violation:** a full paper-wide writing loop rebuilt the abstract/introduction during `BUILD_AND_EVALUATE`. Route: targeted comparison with the canonical paper and restoration of only unauthorized narrative/structural drift.

### Major objections

4. **Outdated current-tool gap:** LangSmith Insights and Datadog Patterns already offer automated cross-run hierarchical categorization and metric aggregation. Route: local related-work/current-tools correction that distinguishes source-linked cross-layer profiling.
5. **RQ3 remains partial:** task/phase/action tag accuracy is not independently established. Route: one complete reused-asset RQ3 experiment after repair.
6. **RQ2 construct/baseline boundary:** custom inspection metrics and raw-action comparison do not establish general analyst productivity or dominance. Route: calibrate prose; do not start another RQ2 benchmark/score/cutoff run.

### Minor and maintenance items

7. Replace bare `\S\ref` output under AAAI formatting.
8. Remove stale “next TraceElephant/RQ2” statements from project memory.
9. During later housekeeping, archive stale unreferenced figure/table outputs and move old narrative/evaluation history out of canonical files while preserving the complete initial narrative. This is not on the critical path.

## 11. Exact route decision

**Current route: `REVIEW_GATE → targeted WRITE_GATE repair`.**

The repair is complete when:

- the exact thesis and all four RQs remain unchanged;
- canonical abstract/introduction/system framing is restored wherever the full-writing rounds—not new evidence—caused drift;
- Step 0007's valid RQ1 evidence remains integrated;
- AgentSight conversion/adapter semantics and the Jaccard versus TF-IDF backend distinction match the artifact and `docs/implementation.md`;
- the current-tools paragraph explicitly distinguishes AgentProf from LangSmith Insights and Datadog Patterns without shrinking the contribution;
- RQ2 wording reflects the tested construct and does not imply published benchmark operating points;
- visible bare-section-reference defects are fixed;
- no full `iter-refine-writing`, new story, new RQ, or new abstraction is introduced.

**Then route: `WRITE_GATE → EXPERIMENT_GATE` for the single complete reused-asset RQ3 experiment specified above.**

Git state, hashes, manifests, attestation, or commit/push outcomes are not scientific passage conditions. No human decision is required: record any residual uncertainty, choose the best scoped interpretation, and continue.
