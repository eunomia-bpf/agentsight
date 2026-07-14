# Step 0010 Full-Paper Reread and Cycle Audit

## Review scope

This is an independent Phase 3/4 reread after the blind review and external-source report. I reread the complete current paper, the project evidence frontier, Step 0008/0009 completion records, and the completed RQ2 result reports. I did not browse externally in this phase. The target is AAAI-27 Main Track, and the paper is genuinely cross-domain: a systems mechanism is used to make claims about AI-agent diagnosis.

## Verdict

- **AAAI-27 readiness: 5/10 — Weak Reject, improved from the blind 4/10.**
- **Confidence: 4/5.**
- **Routing: not submission-ready; one RQ2 synthesis from existing audited results should precede any new experiment.**
- **Taste assessment: incomplete-but-promising.** The durable principle is simple and attractive: agent activity can be profiled without runtime call stacks by projecting source-linked additive effects onto stable semantic responsibility fields. The remaining problem is not implementation volume; it is proving that the projected hierarchy carries responsibility and decision value beyond ordinary cross-trace grouping.

The strongest reject argument remains source-grounded. LangSmith Insights and Datadog Patterns already provide hierarchical cross-trace semantic categories with cost, latency, error, and evaluation aggregates; pprof can promote tags to pseudo-frames; Pivot Tracing already selects and groups metrics across causally related components. AgentProf therefore cannot win on semantic hierarchy, aggregation, or pprof compatibility separately. It must establish that the conjunction of source lineage, conserved cross-layer effects, selectable responsibility projections, and better diagnosis changes the scientific capability. The current paper establishes parts of that conjunction, but not yet the whole causal and utility claim.

## What is already strong

- The fixed thesis and four explicit RQs form a coherent, memorable paper structure.
- The artifact is real and the paper cleanly states several scope boundaries.
- RQ1 has unusually concrete real-system evidence: 20 real Codex tasks, 1,629 concurrent-control effects rejected, 100.0% scoped precision, 96.569% recall, and exact conservation of 1,520 selected effects through current AgentProf.
- RQ2 uses complete public workloads, target-hidden final scoring, fixed released risk/localization signals, and independently audited artifacts. AgentProcessBench includes a matched-refinement permutation control, not merely a raw-action comparison.
- RQ3 uses session-held-out prediction and evaluates both boundary F1 and whole-partition B-cubed agreement; Step 0008 adds independent task-partition evidence rather than another boundary variant.
- RQ4 measures the released construction path with an identical-input raw-action control and reports both time and memory.
- The paper meets the seven-content-page plus two-reference-page AAAI format, and the canonical submodule remains untouched.

## Blind-attack disposition

| Blind attack | Disposition after reread | Evidence status |
|---|---|---|
| **B1. An arbitrary categorical projection is not yet a responsibility stack.** | **Confirmed.** The paper defines folding correctly, but no invariant distinguishes truthful responsibility order from an exploratory field order. Existing product, pprof, and Pivot Tracing precedents sharpen this novelty/mechanism risk. | Missing scientific mechanism/evidence, not a reporting omission. |
| **B2. The central utility is not measured and strong baselines are absent.** | **Partly resolved.** The downstream quality/safety/action outcome remains absent. However, most structural baseline experiments were already run and independently audited; they are omitted from the compact paper rather than absent from the project. | Native, independent-step, session, flat, width-only, ungrouped-risk, permutation, and oracle controls exist unevenly across RQ2 workloads; analyst intervention remains untested. |
| **B3. RQ3 is unanswered and methodologically mismatched.** | **Partly resolved, still major.** Step 0008 adds positive task-partition evidence, and Step 0006 supports held-out group boundaries. Phase, broad action, literal-name accuracy, repeated-run stability, and cross-family generalization remain unproven; the supervised boundary predictor is still not the built-in Rust inducer. | Task and boundary evidence exists; GUI action evidence is negative internally; phase/stability and production-inducer accuracy are absent. |
| **M1. RQ1 mixed weight rewards adding the evaluated tag.** | **Partly resolved.** The session-preserving permutation shows non-random association beyond session, and source-lineage truth is independently tested. The plotted purity-style metric remains structurally advantaged by refinement and is not independent tag correctness. | Supporting control exists but does not fully validate the main construct. |
| **M2. Duration is not automatically additive.** | **Confirmed.** The project record itself notes prompt spans may include idle/user wait time. The paper does not define overlap, concurrency, self time, or inclusive time. | Evidence absent. |
| **M3. Source attribution belongs partly to AgentSight.** | **Partly resolved.** The paper now scopes the R114-compatible AgentSight path and separately states AgentProf's lossless fold. Contribution ownership and asynchronous inheritance semantics remain weaker than the headline conjunction suggests. | Current integration replay exists; current CLI-native capture/linkage does not. |
| **M4. Closest-work/novelty risk.** | **Confirmed.** External verification shows strong same-capability product and systems precedents. | Not a mere writing issue. |
| **M5. Generality may come from dataset-specific mappings.** | **Confirmed.** Fifteen-family schema coverage is useful, but it is not inference generalization. Step 0008 helps two task partitions without establishing broad mapping/tagger generality. | Per-source artifacts exist; held-out cross-family evidence is absent. |
| **M6. RQ2 mixes signals, metrics, and favorable operating points.** | **Confirmed, with a large reporting component.** Full curves and controls exist, but the paper compresses them into AP, Work@80, and Work@50 headlines. TraceElephant's favorable 50%-recall point is descriptive after the predeclared 80%-recall comparison was inconclusive; it must not be presented as if all three experiments passed the same prospective test. | Experiments exist; synthesis and calibrated reporting are missing. |
| **M7. RQ4 excludes expensive/relevant paths.** | **Partly resolved by scope.** The offline construction result is valid for operation inputs, but capture, current field derivation, end-to-end native-history reconstruction, and larger scale are not measured. | Raw-action construction control exists; full end-to-end cost is absent. |
| **M8. Semantic-method reproducibility is insufficient.** | **Partly resolved at artifact level.** Plans and audited outputs contain more details than the seven-page paper. Exact model/prompt/configuration, mappings, feature definitions, and stability evidence are not adequately surfaced in the manuscript or a visible reproducibility package. | Much is run but omitted; repeated-run stability remains absent. |

The largest scientific gap is B1: why an ordered semantic projection is a valid responsibility hierarchy rather than an OLAP hierarchy. The largest writing/reporting gap is M6: the paper hides the already completed baseline matrix and therefore invites a stronger missing-baseline rejection than the evidence warrants.

## Cumulative RQ verdicts

### RQ1 — Resource attribution

**Positive but scoped.** The real-task lineage/control experiment and exact fold conservation establish the tested source-to-profile edge. The semantic-axis study shows declared-category separation beyond session membership, not independent intent truth. RQ1 supports the paper if “resource attribution” continues to distinguish source correctness, conservation, and conditional semantic grouping.

### RQ2 — Correspondence to real problems

**Positive evidence exists, but the current three-number presentation overstates uniformity.** The completed artifacts show:

- **AgentProcessBench:** semantic AP improves by 0.0315 with 95% interval [0.0151, 0.0535], improves all four family point estimates, and beats a matched-refinement null (`p=0.00995`). Work-to-50 remains inconclusive. This is the strongest semantic-specific result.
- **HINTBench:** AgentProf needs 41.57% work at 80% macro recall versus 57.93% native, 100% independent-step, 59.14% session, and 46.29% raw action. It is decisively better than the first three; the paired interval against raw action narrowly crosses zero. The exact reconstruction identity matches AgentProf, as intended for that control.
- **TraceElephant:** the fixed semantic profile has strong early concentration (19.55% work for 50% recall versus 46.64% raw; 52.57% versus 23.79% recall at 20% work), but the predeclared 80%-recall comparison is inconclusive/adverse in point estimate, and the matched-permutation criterion does not support semantic specificity at that threshold.

Therefore a cumulative synthesis is **scientifically meaningful, not merely post-hoc**, if it preserves each workload's predeclared primary outcome, reports full baseline families, and labels secondary curve regions as descriptive. It would be **post-hoc** to meta-average incompatible metrics or claim that all three predeclared experiments succeeded by selecting AP for one workload, Work@80 for another, and the favorable Work@50 region after TraceElephant's primary threshold failed. The defensible cumulative answer is that semantic profiles can add target-blind early problem concentration beyond same-information structural views, with strongest semantic-specific evidence on AgentProcessBench and workload-dependent high-recall behavior.

### RQ3 — Tag accuracy

**Positive partial answer, not a complete fixed-RQ answer.** Task partitions are supported on Mind2Web and ScienceWorld, and session-held-out human group boundaries are supported on OSWorld-Human. Phase, robust action identity, literal tag naming, stability, and unseen-family scope remain open. The fixed RQ and ambitious hypothesis should remain; the paper should not imply that these untested components have already been established.

### RQ4 — Profiling cost

**Positive for offline construction over the tested range.** The 1.17 s result and identical-input cost control answer the narrow construction question. They do not establish full capture-plus-derivation cost or production-scale memory behavior.

## Top three must-fix risks

1. **Responsibility semantics and novelty:** define what makes a field order a valid responsibility projection and why source-linked conserved views provide a capability beyond existing semantic hierarchy/grouping systems.
2. **RQ2 evidence integrity:** expose the already-run same-information baselines and preserve prospective-versus-descriptive distinctions; the current compact table makes a strong evidence base look both weaker and more selectively reported than it is.
3. **RQ3 completeness:** retain the fixed ambitious RQ, but do not equate task partitions plus supervised boundaries with accurate, stable task/phase/action/boundary tags across unseen families.

## Cycle-change audit

The cycle preserved the user-authorized thesis, the four fixed RQs, the ambitious original story, the canonical submodule, and the seven-page main-paper constraint. Step 0008 was appropriately simple: it reused four public sources, existing backends, V-measure, and current AgentProf without adding a model, dataset, metric, or sweep. It completed every planned cell and kept the GUI-Odyssey action failure in internal evidence. Step 0009 synchronized only the positive task evidence and repaired page legality without changing the thesis, abstract, introduction, model, or design.

The main recurring risk is not story shrinkage in these two steps; it is **evidence-selection drift**. Several experiment-level hypotheses were correctly recorded as inconclusive, while later paper-level prose selected favorable AP or early-curve regions without showing the full prospective baseline context. Preserving an ambitious story does not require pretending heterogeneous evidence is uniform. The stronger route is to show the complete existing control surface and state the larger positive principle it actually supports.

The process also respected the constraints against waiting for humans, editing the canonical submodule, or launching complex new benchmarks. Existing real and citable assets remain the correct first choice.

## Exactly one minimal next action

**Create one cumulative RQ2 baseline synthesis from the already completed AgentProcessBench, HINTBench, and TraceElephant artifacts, then use that single synthesis to replace the current RQ2 headline table/prose.**

This is an ANALYSIS/WRITE action for one hypothesis—whether semantic profiles add early problem concentration beyond same-information structural views—not a new benchmark experiment. It must add no model, dataset, metric, threshold, or retuning. For each workload, show the predeclared primary outcome and uncertainty first; then show the already-run native, independent-step, session, flat/reconstruction, width-only, raw-action, ungrouped-risk, matched-permutation, and oracle references where available. Mark secondary curve points as descriptive and do not compute a cross-metric meta-average.

This is the smallest action most likely to change the verdict because it directly answers the strongest fixable blind-review objection with existing independently audited evidence. No new human study, benchmark, model, dataset, or metric should begin before this synthesis is judged.
