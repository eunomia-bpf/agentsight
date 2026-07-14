# Step 0007 Independent Targeted-Repair Verification

- **Timestamp:** 2026-07-14T08:28:43-07:00
- **Role:** fresh independent REVIEW-gate verifier
- **Scope:** read-only verification of the Step 0007 targeted repair after report `991-root-routing-and-repair-20260714T081802-0700.md`
- **Verdict:** **PASS**
- **Scientific or user-contract blockers:** **none**
- **Required repair before closing Step 0007:** **none**

## Independence and review method

I used the complete `auto-research-orchestrator` and `iter-review-critique` instructions, including the hierarchical state-machine, research-taste, systems, AI/ML, and cross-domain review references. The paper is a cross-domain systems/AI paper, so both systems and AI/ML standards apply.

The task packet disclosed the prior review's focus, but I did not adopt its verdict. I first read the complete current paper and canonical project memory, then inspected the complete Step 0007 experiment/write/review record, independently recomputed the RQ1 counts from raw artifacts, checked implementation truth, checked the targeted diff against `a95cbab7`, rebuilt/inspected the PDF evidence, and checked current primary-source product precedent.

Reviewed canonical inputs include:

- complete `docs/paper/main.tex`, `references.bib`, and the nine-page rendered PDF;
- complete `docs/user-instruction.md`, `docs/idea-story.md`, `docs/evaluation.md`, `docs/background-related-work.md`, `docs/design.md`, and `docs/implementation.md`;
- every Markdown report under the Step 0007 EXPERIMENT, WRITE, and REVIEW gates, including all five experiment-plan review rounds and all eleven earlier writing-round records;
- the RQ1 R114 live recording, scoped operation JSONL, profile JSON, and all twenty raw task CSVs;
- the relevant AgentProf CLI, Rust profile inducer, optional Python clustering backend, and existing operation leave-dataset-out experiment skeleton;
- official LangSmith Insights and Datadog Patterns documentation for the closest current product precedent.

No paper, code, shared skill, canonical memory, or Git state was changed by this review. This report is the only created file.

## Contract-by-contract verdict

| Review question | Verdict | Independent evidence |
|---|---|---|
| 1. Is the authoritative thesis and four-RQ story preserved? | PASS | The abstract, introduction, and conclusion retain the thesis **“Agent observability needs profiling, not only debugging.”** The evaluation retains exactly four RQs: attribution, problem correspondence, tag accuracy, and cost. `docs/idea-story.md` retains the complete initial narrative and records no Step 0007 story replacement. |
| 2. Is the repair targeted rather than a new paper rewrite? | PASS | Relative to `a95cbab7`, all section and subsection headings are unchanged, and `figures/fig-architecture.tex` is byte-identical (`645de0a7d65c90baa3f9e05e2c8a952ab093d4c73aeb76e57e9d5bcce223e05e`). The `main.tex` diff is 139 insertions/88 deletions, but its substantive categories are bounded: add the Step 0007 RQ1 result, add missing closest-product precedent/citations, correct source ingestion and inducer descriptions, define the RQ2 control, repair section references, and keep the conclusion within page seven. It does not replace headings, architecture, thesis, or RQs. |
| 3. Does the paper now match the implementation? | PASS | It correctly says AgentSight recordings pass through a source-specific adapter and are not read directly by the current CLI. It correctly distinguishes the optional Python TF-IDF/K-Means exploration backend from the current Rust inducer, whose similarity term is Jaccard distance over visible-token sets plus field-change, balance/coverage, and query-overlap terms. |
| 4. Is closest deployed precedent acknowledged without surrendering the contribution? | PASS | The introduction and related work now acknowledge LangSmith's hierarchical cross-trace categories/aggregate metrics and Datadog's production-interaction topic hierarchy, then state the narrower technical distinction: source-linked additive cross-layer effects as selectable pprof-compatible operation-stack projections. The scientific contrast is accurate and preserves the broad contribution. |
| 5. Is the new RQ1 result exact, complete, and scoped? | PASS | Independent recomputation over all twenty full-run task CSVs yields 1,520 selected events, 1,520 true positives, 0 false positives, 54 false negatives, 100% precision, and 96.569% recall. All twenty target commands completed and all controls were observed. The emitted operation multiset exactly matches the expected selected-event multiset; all weights are one; category counts are read 723, edit 380, test 257, dependency 121, failure 39; 152 profile stacks sum to weight 1,520. The paper correctly scopes this result to the historical R114-compatible AgentSight 0.2.37 source path and current AgentProf 0.2.37 conversion/folding path, not AgentSight 0.2.43 or arbitrary live inputs. |
| 6. Is RQ2 calibrated to what was actually tested? | PASS | The paper defines the target-blind scorer, raw-action control, ranking signals, and evaluated AP/recall points. Its positive answer is limited to problem concentration and early surfacing at those evaluated points; it does not claim benchmark-native end-to-end analyst productivity. |
| 7. Are structure and cross-references intact? | PASS | Heading strings are identical to `a95cbab7`. There are no stale `\\S\\ref`/`\\ref{sec:...}` forms, undefined references, or undefined citations in the final build. |
| 8. Is the AAAI layout boundary intact? | PASS | The PDF has nine pages; page seven ends with the complete conclusion, page eight begins References, and page nine continues References. Visual inspection of all pages found no clipping or overlap; the log has no overfull boxes. |
| 9. Is the next RQ3 route simple and reuse-first? | PASS | Canonical memory routes exactly one experiment: reuse the nine public corpora already selected by R285, existing conversion/labels/splits, `script/operation_leaveout_eval.py` as an execution skeleton, and the current AgentProf operation/profile path. It explicitly forbids adding a benchmark, annotation effort, model, metric, or cutoff; it requires running every eligible existing corpus/axis cell and treating absent independent axes as unavailable. |

## Independent RQ1 recomputation

The following values were recomputed directly from raw task CSVs and persisted full-run artifacts rather than copied from the reports:

| Quantity | Recomputed value |
|---|---:|
| Tasks | 20 |
| Target commands completed | 20/20 |
| Controls observed | 20/20 |
| Selected events | 1,520 |
| True positives | 1,520 |
| False positives | 0 |
| False negatives | 54 |
| Precision | 100% |
| Recall | 96.569% |
| Negative-control events joined | 0/1,629 |
| Operation rows / total operation weight | 1,520 / 1,520 |
| Profile stacks / total profile weight | 152 / 1,520 |

Per-task selected counts equal per-task true-positive counts. Raw task event IDs are unique, the expected and emitted operation multisets are equal, all emitted operation weights are one, and the category totals agree exactly between operations and the folded profile.

## Complete Step 0007 outer audit

### EXPERIMENT gate

PASS. The gate asked one fixed RQ1 hypothesis, iterated the Markdown plan through five scientific reviews, performed a real preflight, ran the complete twenty-task matrix, and independently reviewed the full result. It reused the existing R114 workload and current AgentProf path rather than designing a new benchmark. The result answers only the tested ingestion/preservation hypothesis and does not claim to settle all of RQ1.

### WRITE gate

The earlier eleven-round full-paper writing pass was phase-inappropriate and its old PASS cannot authorize the current paper. That issue is already neutralized rather than hidden: `003-targeted-route-repair-20260714T081802-0700.md` supersedes the old write disposition, restores the authoritative `a95cbab7` organization and architecture, and applies only the necessary evidence/truth/citation corrections. The current diff therefore satisfies the targeted repair route even though the superseded intermediate trajectory did not.

### REVIEW gate

PASS after the targeted repair. The prior outer audit's scientific blockers are resolved:

- current ingestion and inducer descriptions match code;
- closest product precedent is acknowledged;
- the RQ2 control and evaluated-point boundary are explicit;
- section references and page boundary are repaired;
- canonical memory consistently routes to the remaining fixed RQ3 rather than another RQ1/RQ2 benchmark swap.

This is not a demand for zero scientific objections. It means the Step 0007 experiment and its paper integration are honest enough to close, while remaining RQ3/RQ4 work continues through later experiment gates.

## Research-taste assessment

The repair keeps the paper's attractive, simple principle: agent observability should aggregate resource and outcome effects over semantically meaningful operations, rather than reduce profiling to execution location or debugging one run. It does not shrink that thesis to the R114 experiment. The experiment is used as careful evidence for one boundary of the larger idea.

The paper also avoids resolving uncertainty by multiplying concepts or protocols. The RQ1 result is a complete reuse of a real existing workload; the next route reuses existing public corpora and machinery. This is consistent with the project instruction to be bold in hypothesis, careful in evidence, and simple in experimental design.

## Non-blocking observations

These do not prevent Step 0007 from closing and do not authorize another broad repair.

1. **Datadog wording is documentation-version brittle.** Official Datadog documentation clearly supports automated hierarchical topic clustering over production interactions. A recently indexed official version also enumerated token/cost/error/latency/evaluation summaries, while the currently rendered Preview page emphasizes hierarchy, volume/share, and coherence. The core precedent and paper distinction remain correct. At the next otherwise-authorized citation-only pass, the safest wording would avoid enumerating Datadog-specific metric columns unless backed by a stable official page. This is a citation-maintenance note, not a scientific blocker.

2. **RQ3 must begin with recovery-only preflight, not new design.** The R285 summary and nine-corpus manifest remain present, and existing dataset conversion and leave-out scripts define the route, but the referenced generated operation JSONL paths are not currently present in the worktree. REAL PREFLIGHT should regenerate or recover exactly those already-defined nine inputs with the existing converter and then enumerate which task/phase/action axes have genuinely independent scorer labels after removing the scored field and direct aliases. Missing axes must remain “unavailable.” This does not justify a new benchmark, annotation project, predictor, metric, or experiment family.

## Authorized next route

Close Step 0007 and enter the next outer **EXPERIMENT_GATE** for the fixed RQ3 only.

The experiment should remain deliberately small in design:

1. recover the exact nine already-selected R285 corpus inputs through existing conversion paths;
2. adapt the existing leave-dataset-out execution skeleton only enough to exclude the scored reference field and its direct aliases from predictor input;
3. run every eligible existing corpus/axis cell to completion;
4. report one primary tag-accuracy summary plus coverage, with per-axis diagnostics;
5. if no axis is independently scoreable, return that precise finding to REVIEW rather than inventing data or changing the RQ.

No new skill is warranted by this repair. The existing orchestration, experiment-design, and full-paper-review roles are sufficient when their present routing boundaries are followed.

## Verification record

- `docs/paper/main.tex`: `259dc933c2abde36c9470732180d5d36c72fec3e61f3b680ea53db90f6fb7f46`
- `docs/paper/references.bib`: `00e80582793f0791d9768266c32731b014e92b536d953e596e9691e77af657eb`
- `docs/paper/main.pdf`: `e63a06d259f8b94453c964776215bd2725c557d5a8d5faf9d7b0457411bc797b`
- `docs/paper/figures/fig-architecture.tex`: `645de0a7d65c90baa3f9e05e2c8a952ab093d4c73aeb76e57e9d5bcce223e05e`, identical to `a95cbab7`
- `git diff --check`: clean
- Git operations by this reviewer: none

## Final disposition

**PASS. Step 0007 may close.** The current targeted repair preserves the authoritative thesis, exact four-RQ architecture, section structure, and system architecture; accurately integrates the completed RQ1 result; resolves the implementation and precedent contradictions; keeps RQ2 within tested evidence; and routes next to a reuse-first, non-expansive RQ3 experiment.
