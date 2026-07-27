# AAAI-27 Review: *AgentProf: Semantic Profiling for AI Agents*

## Review scope and snapshot

This review covers the AAAI-27 Main Technical Track submission represented by `docs/agentpprof-paper/main.tex` and its compiled `main.pdf`. The paper is a cross-domain AI/systems paper: its claimed contribution combines an agent-trajectory segmentation method with a profiling system and empirical agent evaluation.

The target changed several times during the review. All findings below are anchored to the final stable snapshot:

- `main.tex`: SHA-256 `4b2f7efcdfa525282e85ea716cc639ce803bab159e128116f00b2e7c6dc6be74`
- `main.pdf`: SHA-256 `7053c4b969322ba5f6618bdfa4484867d3725b32e34226527b1a46e711e85c4d`
- `references.bib`: SHA-256 `f738ff1bb4946374542139543be86d22c33bf5f5e0eb47c4a552db13618d2e3f`

Official criteria used: the [AAAI-27 Author Kit](https://aaai.org/authorkit27/), [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/), and [AAAI-27 Main Technical Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/).

## Summary

The paper proposes a simple and potentially useful principle: represent agent work as nested, named semantic intervals, fold equal interval paths across trajectories, and attach additive measures so standard pprof tooling can attribute cost and behavior across runs. `AgentProf` implements this idea as an offline Rust profiler. The evaluation covers a real Git-deployment case, 440 AgentRewardBench trajectories, 42 author-workstation sessions, three fault-localization benchmarks, CodeTraceBench, OSWorld-Human, and two closed-label tasks.

The current manuscript is not submission-ready. The introduction, Figure 1, contribution list, and conclusion retain a complete older result set that is absent from the rewritten four-RQ evaluation. The status-quo claim that agent tools trace but do not profile is false as written: NVIDIA has a workflow profiler, LangSmith aggregates token/cost/tool metrics and groups them by tags or metadata, and Datadog aggregates cost and token use across traces and applications. Most importantly, the strongest information-matched baseline ties `AgentProf`, which makes retained source evidence—not the semantic hierarchy—the leading explanation for the localization gains. RQ1 does not quantitatively measure improved attribution, RQ3 evaluates partition/boundary agreement rather than the promised stability of tags, and RQ4 omits the information required to reproduce or interpret the reported cost.

## Part A — AAAI-27 submission compliance

| Requirement | Pass/fail | Exact evidence |
|---|---:|---|
| AAAI-27 template and submission mode | **PASS** | `main.tex:1–2` uses `article` on letter paper and `\usepackage[submission]{aaai2027}`; `main.tex:19–21` records template version 2027.1. The PDF is US Letter, two-column, PDF 1.5, and has no page numbers. |
| Anonymity | **PASS** | `main.tex:33–34` says `Anonymous Submission` with empty affiliations. Submission mode suppresses authors; the PDF displays “Anonymous submission,” and `pdfinfo` contains no author/title identity metadata. The self-reference to “authors’ own 42 development sessions” (`main.tex:596–601`) does not itself identify the authors. |
| Page budget | **PASS** | `main.pdf` has 7 pages total. Non-reference content ends on page 6 and references occupy the remainder of pages 6–7. This is within 7 content pages and 9 total pages (`main.tex:731–768`). |
| Required PDF properties/fonts | **PASS** | All PDF fonts are embedded Type 1 fonts; no Type 3 fonts were found. The PDF is unencrypted, US Letter, and version 1.5. |
| Forbidden packages/commands | **FAIL** | `main.tex:15–16` loads `pgfplots`, explicitly forbidden by the AAAI-27 Author Kit. `main.tex:454` also compiles an external TikZ source with `\resizebox{\linewidth}{!}{\input{figures/fig-architecture.tex}}`; the kit directs authors to pre-generate pgfplots figures and requires a single main `.tex` source rather than source fragments. The `\setlength{\tabcolsep}` uses at `main.tex:633,687` are the kit’s permitted exception and are not failures. |
| Figure/table placement | **FAIL** | Figures 1–2 and Tables 1–2 are near their discussion, but Figure 3 is first cited on PDF page 4 (`main.tex:571–574`) and floats to PDF page 6, after Related Work and Conclusion, immediately before References (`main.tex:604–618`). AAAI asks for a figure on the page or subsequent page where first discussed. |
| Caption convention and figure-label size | **FAIL** | All captions are correctly below their figures/tables (`main.tex:194–202,455–462,609–617,643–645,698–700`), and table text uses the allowed 9-point `\small`. However, Figure 3’s 1980-pixel-wide panels are scaled from 13.75 inches at 144 dpi to 4.9 inches (`main.tex:606–608`), reducing even their large raster headings below 9 pt; internal labels are much smaller. Figure 1 likewise contains illegible tiny raster labels. The kit requires figure text of at least 9 pt. |
| Citation style | **PASS** | `main.tex:8` loads `natbib` without options; `aaai2027.sty` selects `aaai2027.bst`. The PDF renders author–year citations, and the build has no undefined citation warnings. |
| Reproducibility checklist | **FAIL** | AAAI-27 requires a separately uploaded completed checklist. No checklist is colocated with the reviewed submodule. A checklist exists at `docs/paper/ReproducibilityChecklist.tex`, but if it is intended for this submission it explicitly reports no preprocessing/code appendix (`lines 184–188`), no per-result run counts (`205–206`), and only partial seed, hardware, metric, test, and hyperparameter disclosure (`196–215`). The paper itself names no annotation model/version, prompt, decoding settings, hardware, software environment, random seeds, or per-result run counts (`main.tex:469–518,571–727`). |

## Part B — scientific review

### Strengths

1. The central representation is simple and reusable. The view triple \((\varphi,\sigma,w)\) at `main.tex:444–449` cleanly separates filtering, hierarchy, and measure.
2. The rewritten segmentation section now states useful structural invariants: intervals are nested, cover every turn, and have a session root (`main.tex:469–500`).
3. Emitting ordinary pprof profiles is a pragmatic interoperability choice (`main.tex:526–541`).
4. The evaluation includes independent target-bearing benchmarks and reports paired cluster-resampling intervals (`main.tex:624–668`).
5. The paper honestly reports that an information-matched raw-action representation ties the semantic representation (`main.tex:648–658`), which is scientifically valuable negative evidence.

### Internal-consistency and mismatch list

The review specification says that the abstract retains older numbers, but the current abstract contains no numbers: `main.tex:92–94` makes only the qualitative claim that profiling “effectively attributes cost and locates problems.” The stale numerical results occur in Figure 1, the introduction, contribution list, and conclusion.

| Location | Claim in the manuscript | Conflict with the rewritten paper |
|---|---|---|
| `main.tex:194–199` | Figure 1 shows “325 real agent trajectories.” | The current evaluation defines real inputs as 41 coding sessions, 440 AgentRewardBench trajectories, and 42 development sessions (`551–553`), then reports only 3 Git executions, the 440-session population, and the 42 development sessions in RQ1 (`571–601`). No current RQ uses a 325-trajectory population. |
| `main.tex:237–240` | 325 Codex/Claude trajectories, 183,714 system observations, and over 90% of system-effect cost separated. | None of 325, 183,714, or “over 90%” appears in Evaluation. RQ1 instead reports 489 operations/4,558,192 tokens, 7,229 operations/51,904,621 tokens, and 10,423 source nodes/1,380,863,014 token components (`571–601`). |
| `main.tex:242–245` | Four public datasets, 34,539 operations, 9.4% inspection work, and 45% fewer groups. | The new setup distinguishes four annotated data sources from three localization benchmarks over 27,346 operations (`555–564`). RQ2 reports MAP and evidence-opened fractions, not 34,539 operations, 9.4%, or 45% (`624–668`). |
| `main.tex:247` | Tags agree with ground truth on 7 of 9 held-out datasets. | RQ3 reports CodeTraceBench, OSWorld-Human, and two closed-label tasks, but no nine held-out datasets or 7/9 test (`675–709`). |
| `main.tex:265–269` | Evaluation on 325 real trajectories and four public datasets. | This repeats the old evaluation rather than the populations at `551–564`. |
| `main.tex:759–761` | Conclusion repeats over 90%, 9.4%, 7/9, and 4/6 tasks. | None is produced by any current RQ. “4/6 tasks” has no antecedent anywhere in the current Evaluation. |
| `main.tex:230–235` vs. `469–518` | Introduction promises regex, local-LLM, or clustering “intent attribution” plus field-list/boundary stack construction. | The rewritten method instead makes recursive segmentation the core algorithm and describes an agent, language model, or statistical rule only as an unspecified backend. Regex/clustering are neither defined nor evaluated. |
| `main.tex:405–416` vs. `487–500` | An operation is every activity represented as a uniform weighted record. | The segmentation section also declares a terminal named interval to be “one operation.” The manuscript does not distinguish event records from semantic intervals, although the implementation later says each source node contributes an operation path (`526–541`). |
| `main.tex:455–459` vs. `720–727` | Figure 2 calls intent attribution, stack construction, and folding “query-time algorithms.” | RQ4 says annotation is the dominant one-time backend cost and only later measure switches are replayed cheaply. Intent attribution/segmentation is therefore not query-time in the same sense as projection/folding. |
| `main.tex:568` vs. `576–594` | RQ1 asks whether semantic profiling improves resource attribution. | The case study reports a focusable subtree and the population study compares count-versus-token rankings. Neither measures attribution correctness or improvement against a per-session baseline. |
| `main.tex:672` vs. `675–709` | RQ3 asks how accurate the “tags” are. | B³ and adjacent-boundary F1 evaluate partitions/boundaries, not whether names are stable, repeatable, low-cardinality, or semantically correct across sessions—the properties promised at `230–233,368–372`. |

### Number traceability

- **Legacy numbers fail traceability:** 325, 183,714, >90%, 34,539, 9.4%, 45%, 7/9, and 4/6 occur outside Evaluation and have no current evidence (`main.tex:194,237–247,265–269,759–761`).
- **Unused population:** 41 long-horizon coding-agent sessions are introduced at `main.tex:551` but never receive a reported result.
- **RQ1 prose-only values:** 21.47%, 46.15%, 105 calls, six kinds, 39.42%, 0.886, 0.935, 10/77, 1,737, and 1.735% have no table or machine-readable derivation in the paper. Figure 3 does not display the percentages it is used to support.
- **RQ2 rounding mismatch:** Table 1 displays HINTBench `.517 - .411 = .106`, whereas `main.tex:648–649` reports `.107`. This may be valid from unrounded values, but the document does not say so.
- **RQ2 ambiguous interval:** AP `.634` against prevalence `.398` is followed by “interval [.181, .293]” (`main.tex:663–668`). Neither endpoint can be an interval for AP or prevalence; it appears to be an unlabeled interval for the `.236` AP lift.
- **RQ2 otherwise arithmetically consistent:** AgentProcessBench `.894-.863=.031` and TraceElephant `.326-.209=.117` agree with the prose; the HINTBench discrepancy is one unit in the last shown decimal.
- **RQ3 tables are internally consistent:** Table 2’s B³ F1 values agree with its precision/recall after rounding, and the reported `+.101` and `+.214` deltas match `.764-.663` and `.480-.266`.
- **RQ4 arithmetic is consistent but not traceable:** `1.16 s / 27,765 = 0.0418 ms/operation`, but the 27,765-operation union is not identified and differs from the 27,346 localization operations at `main.tex:562–564`. The raw-action runtime behind “19.6% more,” the samples behind \(R^2=.9997\), and the hardware are absent.

### Do the four RQs support their stated answers?

| RQ | Assessment |
|---|---|
| **RQ1: resource attribution** | **Not supported.** One Git case shows that a chosen semantic grouping is readable, while the 440-session result studies rank agreement between two weights and the 42-session result reports output cardinalities. There is no attribution oracle, operator study, quantitative per-session comparison, or reproduction of the introduction’s >90% claim. |
| **RQ2: correspondence to real problems** | **Partially supported.** `AgentProf`-only produces nontrivial MAP, and Direct+AgentProf improves over Direct-only on all three workloads. However, `AgentProf`-only is below Direct-only on AgentProcessBench (`.791` versus `.863`). Direct+Raw+Evidence is statistically tied on every workload, the paper says the anomaly signal lies in evidence shared by both, and full-trace MAP `.502` exceeds `.326`. Thus output correlates with real targets, but the semantic hierarchy is not shown to cause the gain. |
| **RQ3: tag accuracy** | **Partially supported for segmentation, not tags.** CodeTraceBench B³ F1 `.764` is meaningful, but exact boundary F1 is only `.480`. OSWorld and closed-label results lack tables, intervals, model details, and run counts. No experiment measures cross-session naming stability, repeatability, semantic correctness, or cardinality. |
| **RQ4: profiling cost** | **Partially supported.** The paper reports construction time, peak RSS, annotation tokens, wall time, and caching. It omits model/API version, token price/dollar cost, hardware, repetitions/distributions, baseline runtime, and scale provenance, so neither reproducibility nor general cost is established. |

### Figure–text alignment

1. **Figure 1 is a legacy artifact.** Its caption’s 325 trajectories (`main.tex:194`) are absent from the current evaluation. The raster panels show raw frames such as project, agent, session, prompt, call, model, and kind, not the recursive named semantic intervals introduced at `main.tex:469–518`. It therefore illustrates field aggregation, not the rewritten core algorithm.
2. **Figure 1’s “same operations” assertion is not auditable.** The three panels display different depths and totals, but the paper gives no input identifier or conservation total tying them together.
3. **Figure 3 aligns with the current Git case only at a coarse level.** Its 489-operation/4.56M-token subtitles agree with `main.tex:571–574`, and it depicts `diagnose authentication`. It does not expose the claimed 21.47%, 46.15%, or 39.42% values.
4. **Figure 3 cannot visually establish “all three executions.”** Session identities are intentionally hidden from visible frames (`main.tex:536–541`); the rendered top-level branches show agent names rather than three session IDs.
5. **The middle Figure 3 raster is visibly left-cropped at source**, and all three panels become illegible after `.70\linewidth` scaling.

### References, labels, and bibliography

- **Undefined citations:** none reported by LaTeX/BibTeX.
- **Duplicate labels:** none. The 13 labels in `main.tex` are unique.
- **Broken section references:** all section labels are defined with an empty printed number because the AAAI style uses unnumbered sections. Consequently, every `\S\ref{...}` at `main.tex:152,168,173,258,263,269,349,387,389,391,402` renders as “§” or “§–§” in the PDF. These are dangling references even though LaTeX emits no undefined-label warning.
- **Web-reference quality:** cited web entries such as Claude Code (`references.bib:55–60`), Datadog (`190–195`), Laminar (`202–207`), pprof (`228–233`), Perfetto (`241–246`), OpenTelemetry (`254–259`), OpenInference (`267–272`), LangSmith (`280–285`), Langfuse (`293–298`), Phoenix (`306–311`), and OSWorld-Human (`416–421`) omit access dates, contrary to the AAAI reference example.
- **Incomplete proceedings data:** AgentProcessBench uses only “Proceedings of KDD” with no edition/pages (`references.bib:674–681`); AgentFixer uses an arXiv DOI in an `@inproceedings` entry while its own comment says the proceedings DOI is unresolved (`175–182`).
- **Corrupted `.bib` provenance comments:** comments for CodeTracer describe B³ (`references.bib:713–728`); comments for Bouma describe NVIDIA’s profiler (`730–745`); comments for MacQueen describe Graphectory (`747–763`); comments for Bagga–Baldwin describe Wilson intervals (`765–778`); comments for Ruokolainen describe V-measure (`780–797`); comments for McCallum–Nigam describe Act·onomy (`799–813`); and comments for Lewis et al. describe ScienceWorld (`815–829`). These comments do not alter the compiled bibliography, but they make the repository’s claimed citation-verification provenance unreliable.

### Top five reviewer attack points

1. **Blocker — the paper reports two incompatible experiments.**  
   Quoted claim: “On 325 real Codex and Claude trajectories ... semantic profiling separates over 90%” (`main.tex:237–240`).  
   The rewritten Evaluation contains neither population nor result, while the conclusion repeats three other orphan results. A reviewer cannot determine which paper is being submitted. **Route: WRITE_GATE.** Replace every result-bearing sentence in the abstract/introduction/conclusion/Figure 1/contribution list with the four-RQ evidence, or restore the exact experiments and provenance; do not merely soften the claims.

2. **Blocker — the novelty/status-quo premise is false as written.**  
   Quoted claim: “existing agent tools support debugging and tracing but not profiling” (`main.tex:151–152`).  
   NVIDIA’s official [NeMo Agent Toolkit profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.2/workflows/profiler.html) records token/time/tool usage, performs offline analysis, and analyzes nested bottlenecks across workflow runs. [LangSmith dashboards](https://docs.langchain.com/langsmith/dashboards) aggregate cost, token, latency, error, and tool metrics and group them by tags or metadata. [Datadog cost monitoring](https://docs.datadoghq.com/llm_observability/monitoring/cost/) aggregates cost across traces/applications. The defensible novelty may be *automatic recursive semantic hierarchy plus cross-layer propagation and pprof export*, but that requires direct comparison. **Route: EXPERIMENT_GATE + WRITE_GATE.** Add these closest baselines and rewrite the gap around the mechanism actually absent from them.

3. **Major — the evaluation’s strongest control removes the claimed causal gain.**  
   Quoted sentence: “an information-matched raw-action refinement ties” (`main.tex:650–653`).  
   All three Direct+Raw+Evidence values are within `.002` of Direct+AgentProf, and the paper itself attributes the signal to shared source evidence. RQ1 also lacks an attribution oracle. The strongest alternative explanation is therefore that evidence retention/direct diagnostics—not semantic stacking—drives localization. **Route: EXPERIMENT_GATE.** Hold evidence, reader, score, and compute fixed; vary only the hierarchy and measure operator outcomes such as localization quality at equal evidence budget, time-to-diagnosis, and correct repair choice across unseen projects.

4. **Major — the “algorithm” is a contract with an unspecified decision-maker.**  
   Quoted sentence: “selecting no transition terminates the branch and declares \(I\) one operation” (`main.tex:492–496`).  
   Nothing specifies how transition points or names are selected, yet “Direct Agent annotation” supplies the best RQ3 result. No model/version, prompt, decoding settings, retry policy, seeds, or reproducibility package is identified. The contiguity assumption also excludes interleaved or resumed responsibilities without evaluation. **Route: EXPERIMENT_GATE.** Specify an executable backend, release/freeze its prompt/configuration, report repeated-run stability and cost, and test interleaving/resumption adversaries.

5. **Major — the submission artifact itself is noncompliant and unreadable in key places.**  
   Quoted compiled text: “stacks (§–§)” (PDF page 2, sourced from `main.tex:258`).  
   `pgfplots` is forbidden, every section reference is blank, Figure 3 floats two pages after first mention, and raster labels violate the 9-point minimum. These defects prevent reliable navigation and visual verification. **Route: WRITE_GATE.** Pre-render the architecture without forbidden source packages, repair section numbering/references, replace Figure 1 with the current experiment, and render Figure 3 with legible vector text near RQ1.

## Overall verdict

**Score: reject**

The work is **incomplete but promising**, not complicated-but-shallow. Its durable principle is: *derive a reusable semantic hierarchy from agent trajectories and replay multiple additive measures over that hierarchy*. The current evidence does not yet establish that this hierarchy improves attribution or localization over an information-matched raw representation, and the paper’s status-quo claim ignores existing agent profilers and aggregate dashboards.

The strongest alternative explanation is explicitly visible in RQ2: retained evidence and benchmark-native diagnostics produce the gains, while the semantic skeleton mainly compresses what a reader opens. The largest presently defensible claim is therefore that a semantic skeleton may preserve localization quality while reducing evidence-reading volume. The decisive experiment is a blinded, multi-project operator study or automated equal-budget localization test against raw evidence, LangSmith/Datadog-style tagged aggregation, and NVIDIA’s workflow profiler, with identical telemetry and information access.

The terms “intent attribution,” “recursive operation segmentation,” and “stack construction” currently drift across different mechanisms and should be separated precisely or merged. Acceptance would require both an EXPERIMENT_GATE (causal, information-matched, reproducible evidence) and a WRITE_GATE (one consistent result story and AAAI-compliant artifact).
