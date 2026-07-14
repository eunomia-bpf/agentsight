# External Search and Primary-Source Verification

## Context and question

- **Phase/node:** WRITING, step 0016, REVIEW gate, milestone review 001,
  `EXTERNAL SEARCH -> SOURCE VERIFY`.
- **Started:** 2026-07-14T11:39:00-0700.
- **Completed:** 2026-07-14T11:43:57-0700.
- **Parent:** [blind full-paper read](100-blind-full-paper-read.md).
- **Question:** Do primary sources sustain the blind review's two load-bearing
  reject hypotheses: (H1) AgentProf's core capability is already available as
  labeled/grouped trace analytics, and (H2) RQ2 stops at concentration rather
  than a consequential diagnosis or improvement decision?
- **Scope:** AAAI-27 rules and review criteria; official pprof and Perfetto
  capabilities; official LangSmith Insights and Datadog Patterns capabilities;
  the closest current trajectory-analysis/diagnosis papers; and primary sources
  for the RQ2 benchmark setting. This is a targeted review search, not a new
  comprehensive literature survey.

Before this node, the root reread all of `docs/user-instruction.md` and the
complete `docs/idea-story.md`. The search therefore keeps the exact thesis,
two-object model, and four fixed RQs intact. It treats overlap as a demand for
more discriminating evidence, not authorization to narrow or replace the
story. It also applies the newest instruction: reuse existing experiments and
avoid unnecessary experimental complexity.

## Search method and coverage

Searches were issued on 2026-07-14 against official documentation, official
proceedings, arXiv primary records, and primary paper pages. Representative
queries included:

- `site:aaai.org/conference/aaai/aaai-27 main technical track page limit`
- `site:github.com/google/pprof tagroot tagleaf labels profile documentation`
- `site:perfetto.dev trace processor metrics pivot derived events`
- `site:docs.langchain.com/langsmith/insights hierarchical categories metrics`
- `site:docs.datadoghq.com/llm_observability patterns hierarchy metrics`
- `AI agent cross trajectory patterns profiling diagnosis 2026`
- `AgentProcessBench`, `HINTBench`, and `TraceElephant` primary-paper searches
- targeted searches for TraceGraph, Agent Mentor, AgentGraph, Signals,
  AgentRx, HarnessFix, and TrajAudit.

Search snippets and secondary summaries were used only for discovery. The
judgments below rely on opened official pages, official proceedings, or primary
paper records. ArXiv-only work is explicitly treated as current preprint
evidence rather than accepted venue evidence.

## Venue verification

The [AAAI-27 Main Technical Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
confirms:

- seven pages of main content and nine pages total, with pages after page seven
  reserved for references;
- a required reproducibility checklist;
- abstract deadline 2026-07-21, paper deadline 2026-07-28, and supplementary
  material/code deadline 2026-07-31;
- evaluation on significance and novelty, empirical/theoretical soundness,
  AAAI relevance, and clarity; and
- an explicit preference for substantive new territory, new problems, or
  methods of interest beyond a narrow AI sub-area over incremental gains.

The current PDF matches the 7+2 page boundary and official anonymous AAAI-27
style. Format is not the present blocker. The cross-domain paper is in scope,
but its source-linked profiling contribution must produce a substantive AI
consequence rather than only a systems export format.

## H1: what existing profiling and trace systems already provide

### pprof

The official [pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md)
states that samples may carry string or numeric tags as additional dimensions,
that reports break sample values down by tags, and that `tagroot`/`tagleaf`
promote selected tag values into pseudo stack frames. Pprof also merges
compatible profiles and compares/subtracts profiles.

**Effect on H1.** Merely representing semantic attributes as profile frames,
folding weights, and rendering them with pprof is not new. AgentProf can still
be distinct in how it reconstructs agent activities, derives reusable semantic
fields, and connects intent to downstream system effects, but the paper cannot
treat label promotion or pprof compatibility as the scientific novelty.

### Perfetto

Official Perfetto documentation shows that
[PerfettoSQL](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started)
can extract event arguments, create reusable derived metrics, run the same
queries over trace corpora, and identify bottlenecks. Its
[trace-metric guide](https://perfetto.dev/docs/analysis/metrics) demonstrates
ordinary SQL aggregation by a chosen dimension and sum of duration, and
[debug tracks](https://perfetto.dev/docs/analysis/debug-tracks) can pivot query
results by any selected column into separate visual tracks.

**Effect on H1.** Arbitrary field selection, grouping, summation, and alternate
visual projections are established trace-analysis capabilities. The
distinguishing question is not whether AgentProf can express a hierarchical
grouping; it is whether source-linked semantic responsibility across
heterogeneous agent runs enables a decision that these generic facilities do
not provide automatically.

### Current agent-observability products

Official [LangSmith Insights](https://docs.langchain.com/langsmith/insights)
documentation says it automatically groups traces into categories and
subcategories, reports category frequencies, aggregates latency, cost, error,
feedback, and extracted attributes, and permits predefined categories and
scheduled reuse. Official [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)
documentation similarly constructs a parent/child topic hierarchy across
production interactions, reports interaction share and coherence, supports
drill-down, and recommends scoping patterns to failed evaluations to prioritize
failure categories rather than debug traces one by one. Its currently indexed
documentation also exposes cost, token, error, latency, and evaluation
dimensions for pattern analysis.

**Effect on H1.** The paper correctly cites both products, but the source check
shows that “cross-run semantic hierarchy plus aggregate metrics” is already a
real deployed capability, not a strawman gap. H1 is therefore **partly
confirmed**. The remaining credible novelty axis is the combination of:

1. source-linked intent, tool, process, file, and network effects;
2. conserved additive resource measures over those linked effects;
3. reusable selectable responsibility projections over the same evidence; and
4. a demonstrated decision that needs this cross-layer combination.

The first three are represented in the paper, but the fourth is not yet
decisively demonstrated.

## H2: what current trajectory work demonstrates beyond concentration

### Directly competing trajectory triage and improvement

- [Signals](https://arxiv.org/abs/2604.00356), an April 2026 arXiv preprint,
  computes cheap structured attributes for agent-trajectory triage and uses a
  controlled annotation study on tau-bench. It reports an 82% informative-trace
  rate versus 74% heuristic filtering and 54% random, plus 1.52x efficiency per
  informative trajectory. This is a closer protocol precedent for inspection
  value than AgentProf's score-derived group concentration.
- [TraceGraph](https://arxiv.org/abs/2605.31308), a May 2026 arXiv preprint,
  pools multi-model trajectories into shared decision landscapes, exposes
  recurring access/trap/repair behavior, and then uses the landscape for a
  recovery pipeline. On fired SWE-bench states it raises official resolved
  rate from 41.0% to 44.8% on common-fired instances. It makes the same
  “profiles reveal cross-run behavior hidden by aggregate scores” move and
  closes the loop with a task outcome.
- [Agent Mentor](https://arxiv.org/abs/2604.10513), an April 2026 arXiv
  preprint, analyzes recurring semantic features in execution logs, turns them
  into corrective instructions, and reports repeated-run performance
  improvements across three agent configurations.
- [HarnessFix](https://arxiv.org/abs/2606.06324), a June 2026 arXiv preprint,
  normalizes trajectories into a provenance-bearing intermediate
  representation, consolidates recurring diagnoses, maps them to harness
  repairs, and reports held-out improvements across SWE-bench Verified,
  Terminal-Bench 2.0 Verified, GAIA, and AppWorld.
- [AgentGraph](https://ojs.aaai.org/index.php/AAAI/article/view/42393), an
  AAAI-26 demonstration paper, links graph elements to exact trace spans and
  combines trace-grounded analysis with perturbation-based robustness testing.

These works do not subsume AgentProf's source-linked additive resource model.
They do establish that a 2027 reviewer can reasonably demand a downstream
triage, diagnosis, mitigation, or optimization consequence from a trajectory
analysis system.

### RQ2 benchmark meaning

- [HINTBench](https://arxiv.org/abs/2604.13954) defines separate trajectory
  risk detection, risk-step localization, and failure-type identification
  tasks, and reports that localization remains difficult. A released
  localization prediction is therefore already a diagnostic signal; folding
  it into AgentProf groups measures organization of that signal, not discovery
  of risk from raw observations.
- [TraceElephant](https://arxiv.org/abs/2604.22708) is explicitly a failure
  attribution benchmark with full execution traces and decisive-step targets.
  The paper's released localization outputs again provide most of the
  diagnostic inference before AgentProf grouping.
- [AgentRx](https://arxiv.org/abs/2602.02475) directly localizes critical
  failure steps from trajectories using constraints and an LLM judge, showing
  the capability level represented by a diagnosis baseline.

**Effect on H2.** H2 is **confirmed for the current strongest interpretation**:
AgentProf's present RQ2 evidence shows that a selected hierarchy can organize
existing risk/localization evidence and sometimes reduce early inspection, but
it does not yet show that the profile itself improves a real diagnosis,
remediation, or resource decision. This does not invalidate the fixed RQ2 or
thesis. It identifies the single evidence edge still missing.

## Source-informed attack-map revision

| Blind hypothesis | Source-informed status | Consequence |
|---|---|---|
| H1: renamed group-by | **Major, not fatal.** Generic field grouping, pprof tags, trace pivots, and semantic category trees are established. | Stop selling projection/export alone. Test the unique source-linked cross-layer responsibility consequence. |
| H2: external signal drives RQ2 | **Blocker for AAAI acceptance.** Primary benchmark sources confirm the signal is already a risk/localization output. | Reuse real trajectories to test a downstream decision under a matched information/budget comparison. |
| H3: shipped tagger/inducer mismatch | **Major but secondary.** It remains true internally, but another broad tagger benchmark would fragment the evidence program. | Do not immediately open a large new tagger matrix; prefer evidence that tests whether the complete profile is useful. |
| H4: source-to-profile chain split | **Major, partly addressed by RQ1.** The 20-task lineage suite plus exact folding covers the chain in a bounded scope. | Preserve as RQ1 evidence; no new lineage variant unless the downstream experiment needs it. |
| H5: missing AI outcome | **Blocker and same root cause as H2.** Closest work now reports triage efficiency or task improvement. | One decisive outcome experiment can address both H2 and H5. |
| H6/H7: exhaustive systems scale/generalization | **Not the next experiment.** Valid limitations, but low paper-decision value relative to H2/H5. | Keep scoped; do not add complexity, protocols, or many datasets now. |

## Experiment implication under the reuse/simple constraint

The source search rejects three tempting but low-value directions:

1. another pprof/SQL rendering comparison, because equivalence of expression is
   already externally established and would not prove decision value;
2. another benchmark/cutoff sweep over AP or Work@recall, because it repeats
   the present proxy construct; and
3. a large human study or full product integration, because it would be slow,
   expensive, and unnecessarily complex for the next step.

The next node should first inventory existing completed AgentProf artifacts for
a **reusable downstream-decision experiment**. The preferred shape is one RQ2
experiment on existing public trajectories, existing profile outputs, and an
existing real outcome oracle, where the profile selects one bounded action
(for example, which recurring behavior to inspect, replay, patch, or test
first) and the result measures an accepted real outcome such as informative
cases found, official task success, independently annotated fault coverage, or
avoided resource/system effects. It must compare against the strongest
equally-informed raw/session/native choice under the same budget.

Only if no existing artifact can supply such an outcome should a new run be
admitted. A new dataset, model, hierarchy, ranker, cutoff, or scoring framework
is not justified by this search.

## Decision, uncertainty, and next node

- **Scientific decision:** the paper is not yet AAAI-ready. Its central thesis
  remains important, but current products eliminate the broad “no semantic
  aggregation exists” gap, while current papers set a stronger actionability
  bar. The highest-value repair is evidence for the original fixed RQ2, not a
  smaller thesis or a new story.
- **User-intent audit:** thesis, four RQs, original story, positive program,
  submodule authority, and no-skill-edit constraint remain unchanged. The
  recommendation explicitly prefers reuse and one simple complete experiment.
- **Uncertainty:** product APIs may not permit a runnable matched export; the
  recent closest papers are mostly arXiv preprints; and an existing AgentProf
  artifact may already contain an adequate decision outcome. These do not
  block progress.
- **Next node:** source-informed full-paper reread, followed by an audit of the
  existing experiment inventory. The reread must decide whether a reusable
  outcome experiment is actually necessary and name exactly one candidate if
  so.
