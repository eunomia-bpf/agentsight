# Blind Full-Paper Read and Reject-Hypothesis Attack Map

## Node metadata

- **Started:** 2026-07-16T18:19:00-07:00
- **Completed:** 2026-07-16T18:34:00-07:00
- **Parent:** Step 0034 REVIEW gate, milestone review 001
- **Objective:** Form an unprimed, paper-only assessment of the complete AgentProf manuscript and enumerate the strongest reject hypotheses and externally verifiable load-bearing claims before consulting prior reviews, author intent, evaluation work logs, cycle artifacts, or project memory.
- **Target venue:** AAAI-27.
- **Contribution classification:** Genuinely cross-domain. The paper makes a systems claim (a profiler abstraction, source-to-effect attribution path, pprof-compatible implementation, and cost) and AI/ML claims (semantic intent attribution, trajectory grouping, benchmark problem localization, and tag accuracy). Both layers are load-bearing, so this review applies the systems and AI/ML bars together rather than accepting strength in one as compensation for weakness in the other.
- **Review references loaded before the read:** `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md` from the `iter-review-critique` skill.

## Inputs and provenance

The blind pass read `docs/paper/main.tex` from beginning to end, the compiled nine-page `docs/paper/main.pdf`, `docs/paper/references.bib`, the reproducibility checklist, every TeX table and architecture figure under `docs/paper/figures/`, and every raster figure under that directory. The included figures are the three semantic flame graphs, the RQ1 semantic-axis ablation, and the architecture diagram. The directory also contains apparently stale, non-included claim artifacts (`actionability-knobs.png`, `baseline-tradeoff.png`, `fig-rq3-vmeasure.png`, `case-table.tex`, `claim-gate-table.tex`, `evidence-path-table.tex`, `experiment-role-table.tex`, and `task-verdict-table.tex`) and two unrelated Sandlock benchmark JSON files. I treated those as paper-directory consistency evidence, not as support for the compiled manuscript. `AnonymousSubmission2027.tex` is the AAAI author-kit template, not manuscript content.

No prior review, author rebuttal, `docs/evaluation` content, Step 0034 plan/result/report/code, `docs/idea-story.md`, `docs/user-instruction.md`, or canonical memory was read during this phase.

### Reviewer-context disclosure and unavoidable contamination

The assignment itself disclosed the target venue, that the thesis and exactly four RQs are fixed, that Step 0034 has a proposed no-paper-change disposition, and that the paper might be cross-domain. I independently classified it cross-domain from the claims, but cannot claim ignorance of the suggestion. Reading all claim-bearing paper-directory artifacts as explicitly required also exposed stale tables that mention old RQ/E-number formulations and prior experiment identifiers (`R320`, `R365`, and similar). Those artifacts are not used to infer author intent or to soften the blind verdict; their presence is itself a submission-hygiene inconsistency. Bibliography annotations such as `USED_FOR` necessarily exposed the authors' intended citation roles because they are embedded in the required bibliography.

## Method

I reconstructed the manuscript as one causal argument, mapped each fixed RQ to its mechanism and evidence, tested the cross-domain causal chain, and then generated reject hypotheses without external search. This report therefore distinguishes paper-internal evidence from claims that still require primary-source verification. No external source is treated as verified here.

## Paper-only reconstruction

### Problem, stakes, challenged belief, and principle

The problem is population-scale understanding of agent behavior across many trajectories: developers want to know which semantic responsibilities consume resources, concentrate failures, or cause unsafe effects. The stakes are agent quality, safety, and cost. The claimed status quo is that agent observability mainly traces or debugs individual runs, whereas profiling should aggregate recurring responsibility across executions.

The paper's principle in one plain sentence is: **replace execution call stacks with query-time stacks over semantic operation fields, so additive agent costs and effects can be folded across heterogeneous trajectories.**

The challenged belief is that trace/span hierarchies or raw actions are the natural and sufficient structure for agent observability. The paper asserts that semantic responsibility categories—not runtime nesting—should be the profiler frames. Whether the community actually holds the stated debugging-only belief, and whether current products already perform equivalent hierarchical cross-trace aggregation, requires external verification.

### Artifact, mechanism, and causal chain

AgentProf parses local Codex/Claude histories or operation JSONL into uniform weighted records, derives categorical fields with rules, mappings, clustering, or a local LLM, selects an ordered field list or induces boundaries from recurrent action transitions, folds identical projected field sequences, and exports pprof, folded stacks, SVG, or JSON.

The intended cross-domain causal chain is:

> heterogeneous agent trajectory and system-effect data -> missing stable responsibility identifiers and semantic nesting -> field derivation plus operation-stack projection -> conserved aggregation into semantic groups -> earlier inspection of groups containing problems and more interpretable resource responsibility -> better developer decisions about quality, safety, and cost.

The paper directly supports the representation, folding, and some benchmark-grouping edges. It does not directly test the final developer-decision or intervention edge. RQ2's fixed-model reader is an indirect proxy and is explicitly disclaimed as human utility.

### Claimed contributions and scope

1. A semantic operation stack model comprising uniform operations and query-time field projections.
2. AgentProf, a roughly 9.8K-line offline Rust profiler with pluggable intent attribution and stack construction, and pprof-compatible output.
3. An evaluation spanning source lineage, semantic resource views, public problem-localization benchmarks, task/action/group tag fidelity, and offline construction cost.

The paper scopes itself to offline post-execution profiling; its RQ1 source experiment uses a fixed 20-task Codex suite and declared manifest categories; literal phase tags and unknown label sets are outside RQ3 evidence; CodeTraceBench calibration is post hoc; and capture/live-agent overhead is excluded.

## Fixed RQ map and initial answers

The thesis and these exactly four questions are evaluated as written; none is replaced, narrowed, or redefined here.

| Fixed RQ | Paper-level claim/goal | Mechanism and evidence presented | Blind answer |
|---|---|---|---|
| **RQ1: Does semantic profiling improve resource attribution?** | Source-linked effects can be conserved and attributed at useful semantic resolutions beyond tag-free/session aggregation. | A 20-task AgentSight join recovers 1,520/1,574 in-scope effects with zero false positives and rejects 1,629 controls; folding conserves all recovered weights. On 325 local trajectories, prompt-tag projection lowers mixed-tag weight from 90.4% to 36.7% and increases unique stacks; field and weight choices produce different folds. | **Partially answered.** Source fidelity and conservation are credible for the declared suite, but the central "improve attribution" construct is not independently validated. Mixedness is defined by the same declared prompt categories that create the groups, and source joining is upstream AgentSight functionality. There is no external-observability or independently judged responsibility baseline. |
| **RQ2: Does profiler output correspond to real problems?** | Target-blind semantic groups rank independently annotated problem operations earlier than matched raw-action grouping. | Complete AgentProcessBench, HINTBench, and TraceElephant workloads; MAP improvements over raw action; inspection-work curves; a fixed Qwen reader selects groups in six tasks. Atomic scores beat AgentProf on AgentProcessBench; work intervals cross zero; the reader raises work on 4/6 tasks. | **Positive but incomplete for the thesis.** It supports correspondence and group prioritization relative to one matched raw-action control, not diagnosis utility, analyst productivity, intervention quality, or superiority to existing hierarchical trace analytics. The ranking signal is inherited from released benchmark scores, so attribution of gains to the operation-stack abstraction remains uncertain. |
| **RQ3: How accurate are the tags?** | Pre-specified target-blind methods recover accurate, stable task, phase, action, and group fields on unseen families. | OSWorld-Human group boundaries; post-hoc CodeTraceBench calibration; K-Means partitions on 9 Mind2Web and 100 ScienceWorld sessions; Qwen classification over AgentBoard task families and software-agent action labels. | **Unanswered as a single RQ.** The evidence covers heterogeneous components with different backends and constructs; literal phase labels are explicitly untested, unknown label sets are excluded, one core mechanism was selected after inspecting OSWorld, and CodeTraceBench selection is post hoc. Some subclaims are answered, but the stated composite hypothesis is not. |
| **RQ4: What is the profiling cost?** | The offline parse-construct-fold-serialize path is practical and predictable over the tested range. | Three-run medians on four public workloads and their union, reaching 27,765 operations in 1.17 seconds and 464.5 MiB, with 18.2% time and 1.3% memory added over raw action. | **Answered only for the measured binary, machine, and small range.** The reported cost is low enough for the tested offline use, but "predictable" is weakly supported by five naturally covarying sizes and a descriptive linear fit; no live/capture cost is promised here. |

## Initial paper-only verdict

**Weak reject, with an incomplete-but-promising core.** The operation-stack principle is simple and memorable, and the artifact integrates an unusually broad collection of agent traces. However, the evaluation currently rewards the representation before establishing the paper's main causal consequence. RQ1's main separation metric is close to definitional, RQ2 compares against a narrow raw-action control while disavowing human utility, RQ3 is explicitly incomplete, and the closest-work argument is compressed into two paragraphs despite current products that already derive cross-trace categories and aggregate cost/error metrics. At AAAI, broad AI significance and construct-valid agent evaluation are not yet established by systems integration volume.

This is not yet simple-but-deep: it is **incomplete-but-promising**, with a risk of becoming complicated-but-shallow because the many datasets, taggers, mappings, calibration variants, and metrics do not yet isolate the one new prediction implied by semantic operation stacks.

## Reject-hypothesis attack map

### H1 — The novelty is a relabeling of known labeled aggregation (potential blocker: novelty/scientific framing)

The operation stack mathematically projects rows onto an ordered field tuple and sums weights. The paper itself notes that pprof can promote labels to pseudo-frames, that Perfetto supports derived events, and that LangSmith Insights and Datadog Patterns derive hierarchical categories across traces and aggregate cost/error/latency. A skeptical reviewer can interpret AgentProf as `GROUP BY`/data-cube aggregation plus flame-graph rendering, with semantic labeling delegated to known rules, K-Means, or an LLM. The paper must establish what new falsifiable prediction or semantic invariant the abstraction adds beyond existing span attributes, process mining, trace clustering, and pprof labels. External closest-work search is decisive.

### H2 — RQ1's "improved attribution" evidence is construct-circular (blocker: evidence/evaluation)

The decisive local result groups observations by prompt tags and then measures how much weight remains mixed across those same prompt-tag categories. Unless the ground-truth responsibility labels are independently obtained, adding the label used by the metric must reduce mixing. The permutation test shows nonrandom association in this corpus, not correctness of responsibility. The 20-task source-lineage experiment validates an AgentSight scoping join and AgentProf's conservation, but does not compare semantic responsibility against a serious alternative. The missing promised evidence is an independent attribution oracle or downstream decision measure under equal source data, not merely another cutoff or metric variant.

### H3 — RQ2 cannot attribute problem-localization gains to the claimed mechanism (major: evidence/evaluation)

The method ranks operations or groups using released judge/localization signals and changes the grouping field relative to raw action. There is no end-to-end comparison with existing hierarchical observability products, trace trees, conventional clustering/process-mining pipelines, or a tuned semantic aggregation baseline with equal labels and signals. Atomic scores are strongest on one workload. Work improvements are uncertain, and the LLM reader is tiny (six tasks, 66 responses), single-model, and explicitly not evidence of human utility. The paper therefore establishes a grouping effect, not that semantic profiling improves real diagnosis or observability.

### H4 — RQ3 promises one broad accuracy claim but reports a collage of non-equivalent tasks (blocker: global logic/evidence)

Task clustering, closed-set task-family classification, closed-set action classification, phase labeling, and boundary induction are different constructs. They use different data, labels, backends, and levels of supervision. Literal phase labels are absent; recurrence was chosen after earlier OSWorld inspection; the 405-trajectory CodeTraceBench modification is post-hoc selection, not an untouched test. Yet the abstract highlights the calibrated number. A complete empirical submission must either answer every load-bearing part of this fixed RQ with honest independent evidence or mark the missing decisive evidence without presenting the RQ as answered.

### H5 — The cross-domain causal chain stops before operational value (major: scientific framing/evidence)

The introduction motivates developer questions about quality, safety, and cost, but no experiment shows a developer finding a fault faster, choosing a correct mitigation, reducing unsafe effects, or lowering cost using the profile. This is not merely a request for a larger user study: some externally anchored decision or intervention experiment is needed because "observability needs profiling" is the thesis. The fixed-model reader is a proxy over pre-ranked groups and does not operate the system or choose a remediation.

### H6 — The evaluation is broad in datasets but narrow in controlled baselines and protocol validity (major: evidence/evaluation)

Fifteen mapped families mainly demonstrate parsability, not generality of semantic responsibility. RQ1's tag categories are declared; RQ2 uses one matched raw-action comparison; RQ3's simple boundary controls omit stronger sequence segmentation, change-point detection, process-mining, embedding, or modern supervised baselines; stochastic LLM evaluations provide deterministic repeats but not model/prompt robustness or human calibration. Multiple dataset-specific signals and chosen field orders increase researcher degrees of freedom. The reproducibility checklist itself answers `partial` or `no` for parameter-search reporting, code availability, seeds, infrastructure, metrics, run counts, and source appendices.

### H7 — The belief challenge may be a strawman (major pending external verification: framing/novelty)

The manuscript says existing tools support single-run debugging, then immediately acknowledges cross-trace hierarchical categories and aggregate cost/evaluation metrics. The narrower delta—source-linked additive system effects plus selectable pprof projections—may be useful, but it does not by itself prove that agent observability lacked profiling. Official tool documentation and agent-observability literature must be opened before the claim can stand.

### H8 — The system mechanism is underspecified at trust and failure boundaries (major: technical mechanism)

The paper says ingestion propagates semantic fields from tool invocations to resulting effects, but does not formalize causality under concurrency, asynchronous tools, subprocesses, shared resources, missing events, or ambiguous lineage. The suite reports 54 false negatives but provides no failure taxonomy. Operation field conflicts, empty values, hierarchy ordering, double-counting across timed operations, and conservation under filtering are not specified as invariants. The source-specific adapter caveat also weakens the architecture figure's direct local-history story.

### H9 — RQ4's "predictable" claim overstates a descriptive microbenchmark (minor-to-major: evidence/claim calibration)

Five points are four datasets plus their union, not controlled scale levels, and time is reported at two-decimal resolution with only three runs. A high linear-fit value is unsurprising when union size dominates. Peak RSS reaches 464.5 MiB for only 27,765 operations, but no memory scaling or larger stress range is shown. The paper may safely claim the measured offline time; practical predictability across production histories is not yet demonstrated.

### H10 — Paper-directory and narrative hygiene are not submission-ready (major writing/global consistency, not scientific evidence)

The compiled manuscript's Related Work is only two short paragraphs and cannot carry the closest-work burden. The paper directory contains stale figures and tables with incompatible old RQ formulations (for example, RQ1/E1 "generality and recursive folding" and RQ4/E4 "artifact replayability") plus unrelated Sandlock raw data. `fig-rq3-vmeasure.png` displays substantially different per-dataset results and a threshold not explained in the current text. These do not alter the compiled claims, but they create artifact-review ambiguity and indicate claim drift. The checklist admits missing datasets/code appendices and incomplete reproducibility reporting.

## Load-bearing claims and facts requiring external verification

1. Existing agent-observability products do not already provide the effective equivalent of selectable semantic hierarchical aggregation over cross-trace metrics and system effects.
2. Pprof labels/tagroot/tagleaf and Perfetto SQL/derived events cannot already express the core operation-stack abstraction with ordinary preprocessing.
3. The closest academic work in agent observability, agent profiling, trajectory diagnosis, execution provenance, and behavior discovery does not make the same profiling claim.
4. Process mining, hierarchical sequence segmentation, trace clustering, and semantic aggregation do not already use the same mechanism or stronger accepted protocols.
5. AgentProcessBench, HINTBench, and TraceElephant labels/signals are used in a way consistent with their official tasks and splits; the paper's MAP/work construction is accepted for this use.
6. OSWorld-Human action groups are an appropriate ground truth for semantic stack boundaries, and its 287 "development sessions" are not being presented as independent confirmation after mechanism selection.
7. CodeTraceBench's verified split and source-valid-failure filtering support the stated population, and the post-hoc calibration does not cross a benchmark-use boundary.
8. Current strong baselines for sequence/group-boundary induction substantially exceed the three simple controls used here or reveal alternative explanations.
9. B-cubed, V-measure, MAP, Wilson ranking, and the reported bootstrap units match the constructs and sampling units claimed.
10. Real operational evidence shows developers need aggregate semantic responsibility views rather than only trace-level diagnosis, and identifies decisions such views improve.
11. AAAI-27 rules permit the current page/checklist/artifact form and require reproducibility disclosures consistent with the manuscript.

## Global internal consistency findings

- The title, abstract, introduction, and conclusion agree on the fixed thesis.
- The four RQs are explicit and evaluation sections follow their order.
- RQ3 is internally inconsistent with its own fixed hypothesis: literal phase accuracy is promised by the hypothesis but explicitly absent from evidence.
- The abstract says "Across real and public trajectories, semantic profiles separate resource use by responsible category," but the highlighted boundary evidence measures human-partition agreement rather than resource separation.
- RQ1 alternates between source fidelity, category separation, number of stack depths, and multiple weights. These demonstrate different properties and do not jointly instantiate one independent attribution-accuracy construct.
- The architecture figure suggests local histories directly become uniform operations while the implementation says AgentSight recordings require an external source-specific adapter and are not read by the CLI.
- Figure 1 has no quantitative comparator and visually contains truncated labels; it demonstrates renderability more than semantic insight.
- Figure 3 omits a visible bar for the combined session+prompt mixed/residual values even though the caption emphasizes four configurations; the line remains visible. This hinders exact interpretation.
- RQ4 reports 27,765 operations over four public workloads, while RQ2 reports 27,346 over three and the public annotated set reports 47,590. These can all be true, but the relationships are not explained and invite population confusion.
- The checklist's `partial`/`no` answers contradict a submission-ready impression: run counts are said not to be stated even though some experiments state them, and infrastructure/metric details remain incomplete.

## Largest gaps

- **Largest scientific/evidence gap:** independent, end-to-end evidence that the semantic operation-stack abstraction improves responsibility attribution or a real developer decision under equal input data and against strong semantic/hierarchical alternatives. This is missing promised evidence for RQ1 and the thesis, not merely a wish for more breadth.
- **Largest writing-only gap:** Related Work and novelty positioning are far too compressed to distinguish the abstraction from pprof labels, Perfetto queries, existing cross-trace behavior hierarchies, process mining, trajectory segmentation, and agent-diagnosis systems. This is reparable in WRITE_GATE only after external novelty verification.

## Alternatives and provisional decision

The paper should not respond by shrinking "semantic profiling" into a narrower visualization utility or by replacing any fixed RQ. The ambitious repair is to isolate the principle causally: hold the source data, ranking signal, and label budget constant; compare operation stacks against the strongest existing hierarchical semantic baseline; and measure independent attribution correctness or a consequential diagnostic/configuration decision. A fresh family must then test the finalized RQ3 constructor and all promised tag types without post-hoc selection.

The provisional route is **EXPERIMENT_GATE**, conditional on external search confirming that the principle is novel enough to defend. If closest work already implements the same abstraction, the next outer action must first be a focused `research-literature-novelty` cycle rather than polishing.

## Tree/search updates and project-memory updates

The attack tree now has three load-bearing branches: novelty/equivalence (H1/H7), construct and causal validity (H2-H6), and mechanism/artifact readiness (H8-H10). External search must attack both the AI-agent observability/evaluation community and the systems profiling/process-mining community. No canonical project-memory update was made; this report is evidence for the parent orchestrator only.

## Completion assessment, uncertainty, and next node

The blind phase is complete: all current manuscript claims, included figures/tables, bibliography, checklist, and claim-bearing directory artifacts were reviewed without consulting prior review/cycle intent. Confidence is high in the internal-evidence findings and moderate in the novelty hypotheses until primary sources are opened. The next node is mandatory external search and source verification, recorded in `02-external-search-source-verification.md`.
