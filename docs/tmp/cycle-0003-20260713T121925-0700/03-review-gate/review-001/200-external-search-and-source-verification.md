# Review 001 / Node 200 — External Search and Primary-Source Verification

**Started:** 2026-07-13 16:18:12 PDT
**Completed:** 2026-07-13 16:22:03 PDT
**Parent:** [`100-blind-full-paper-read-and-attack-map.md`](100-blind-full-paper-read-and-attack-map.md)
**Node status:** complete
**Paper edit authority:** none

## Objective

Attack the blind-read claims with current primary sources from systems tracing,
agent observability, semantic trajectory analysis, failure attribution, and
official AAAI guidance. Verify official artifact availability before treating
a benchmark as an executable next experiment.

## Method and source boundary

Search covered both the systems and AI communities and asked:

1. Is cross-component metric attribution or query-time grouping already known?
2. Do production observability products already perform cross-run semantic
   clustering and failure prioritization?
3. Which current papers already demonstrate semantic trajectory summaries or
   reduced inspection?
4. Which official benchmark provides a fresh population, complete visible
   fields, responsible-component and decisive-step labels, strong baselines,
   and downloadable data?
5. What are the current AAAI-27 deadline, page, anonymity, and reproducibility
   requirements?

Search snippets and secondary summaries were used only for discovery. The
review opened official conference pages, primary papers/PDFs, official
documentation, official repositories, and official dataset endpoints before
using a fact.

## Verified primary sources

| Source | Verified finding | AgentProf implication |
|---|---|---|
| [AAAI-27 Main Track](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) | Abstract deadline July 21, 2026; paper deadline July 28, 2026; seven pages of main content, nine pages total with pages after seven reserved for references; reproducibility checklist required. | AAAI remains a plausible target, but scientific evidence must converge before the deadline. |
| [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems-2/) | Supports selecting, filtering, and grouping a metric by causally preceding events across components and machines. | Cross-layer grouping alone is not new; agent-specific semantic responsibility and outcome value must carry the contribution. |
| [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Production interactions can be hierarchically clustered into semantic topics and scoped to failed or low-quality interactions. | Cross-run semantic clustering and failure-topic prioritization cannot be claimed as absent. Additive responsibility profiling remains a plausible distinction. |
| [Arize Phoenix](https://arize.com/docs/phoenix) | Supports traces, evaluations, datasets, experiments, and comparison of application versions. | “Only single-run debugging” is too broad; the paper needs a precise profiling distinction. |
| [Hodoscope](https://arxiv.org/abs/2604.11072) | Compares behavior distributions across groups and reports reduced review effort while surfacing benchmark exploits. | Cross-run behavior discovery and inspection reduction are occupied claims; AgentProf needs direct matched evidence. |
| [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) | Uses semantic action embeddings and trajectory-transition views and reports downstream WebArena improvement after trajectory filtering. | Semantic summaries already show downstream value. AgentProf must establish measured attribution and profile-guided population inspection. |
| [AgentRx](https://arxiv.org/abs/2602.02475), [official artifact](https://github.com/microsoft/AgentRx) | 115 manually annotated failures across tau-bench, Flash, and Magentic-One; constraint-based diagnosis predicts critical step and category. | Strong evidence that environment response and constraints matter beyond an action label. It is a closest diagnosis baseline, not a profiling population by itself. |
| [HINTBench](https://arxiv.org/abs/2604.13954) | 629 advertised synthetic trajectories and fine-grained intrinsic-risk steps; the current released snapshot used by Cycle 0003 contains 616 records. | Useful mechanism pressure, but not a fresh real-execution population after Cycle 0003. |
| [Who&When](https://arxiv.org/abs/2505.00212), [official artifact](https://github.com/mingyin1/Agents_Failure_Attribution) | ICML 2025 Spotlight; official repository exposes 126 algorithm-generated and 58 hand-crafted annotated failures, with responsible agent and decisive step. The logs are primarily output-side. | Strong precedent and partial-observability reference. Missing input/tool/environment context makes it a poor match for the richer mechanism required after HINTBench. |
| [StepFinder](https://arxiv.org/abs/2606.03467), [official artifact](https://github.com/taiyu-zhu/StepFinder) | Builds temporal-semantic sequences and evaluates learned step attribution on Who&When. | A reviewer-expected learned baseline when the source is Who&When, but its training and source schema do not automatically transfer to another benchmark. |
| [TraceElephant, ACL 2026](https://aclanthology.org/2026.acl-long.912/), [official artifact](https://github.com/TraceElephant/TraceElephant), [official data](https://huggingface.co/datasets/TraceElephant/TraceElephant) | 380 real executions, 220 annotated failures, Captain-Agent/Magentic-One/SWE-Agent, GAIA/AssistantBench/SWE-Bench, complete inputs/outputs/inter-agent messages/tool logs/configuration/architecture, responsible component and decisive step, executable environments, and official attribution methods. | Best current fresh RQ2 source because it exposes the exact context that semantic profiling must exploit instead of retuning action labels. |

## TraceElephant source verification

The official paper and repository establish:

- **population:** 220 failures retained from 380 real agent executions;
- **systems:** Captain-Agent, Magentic-One, and SWE-Agent;
- **task families:** GAIA, AssistantBench, and SWE-Bench;
- **five system-task strata:** Captain/GAIA (73 failures),
  Captain/AssistantBench (12), Magentic/GAIA (74),
  Magentic/AssistantBench (17), and SWE-Agent/SWE-Bench (44);
- **targets:** responsible component and the earliest step at which failure
  becomes inevitable;
- **visible context:** agent inputs and outputs, inter-agent messages, tool
  invocations/raw logs, system configuration, and architecture metadata;
- **official methods:** All-at-Once, Binary Search, Step-by-Step, Static
  Agentic, and Dynamic Agentic;
- **official metrics:** responsible-agent and decisive-step accuracy;
- **artifact:** a public CC-BY-4.0 repository and a public dataset archive;
- **data availability:** the official archive is approximately 596.6 MB and
  directly downloadable;
- **released evaluator:** reads `mistake_agent` and `mistake_step` only during
  scoring and counts exact agent/step predictions;
- **released baseline caveat:** the public one-click inference path visibly
  exposes the three prompting methods; Static/Dynamic Agentic runnability must
  be verified rather than weakly reimplemented.

The paper reports that full context materially improves attribution over an
output-only condition. This is not evidence that AgentProf will win; it is
evidence that the richer fields are load-bearing and that an output-only source
cannot test the mechanism the next experiment needs.

## Who&When versus TraceElephant

| Dimension | Who&When | TraceElephant | Selection impact |
|---|---|---|---|
| Archival status | ICML 2025 Spotlight | ACL 2026 Long Paper | Both credible; TraceElephant is fresher |
| Annotated failures | 184 | 220 from 380 executions | TraceElephant larger |
| Agent systems | Captain-Agent, Magentic-One | Captain-Agent, Magentic-One, SWE-Agent | TraceElephant broader |
| Task sources | GAIA, AssistantBench | GAIA, AssistantBench, SWE-Bench | TraceElephant broader |
| Observable fields | Primarily output-side logs | Full input/output/tool/environment/configuration context | TraceElephant matches the proposed mechanism |
| Official attribution methods | Three prompting strategies | Three prompting plus static/dynamic agentic methods | TraceElephant has stronger source-native comparisons |
| Standard train/dev/test split | None | None | Both require a test-only or externally developed policy |
| Data/compute cost | Lower | 596.6 MB; static inference practical, dynamic replay costly | Who&When cheaper, TraceElephant higher paper value |
| Cross-run profiling risk | Can collapse to output-log debugging | Supports recurring role/subgoal/action/response/status profiles | TraceElephant better |

Who&When remains an important closest-work and partial-observability reference.
It is not selected merely because it is easier. Its absence of exact
input/environment fields conflicts with the mechanism suggested by the
HINTBench boundary and would encourage another action-dominated experiment.

## AAAI format and deadline verification

The official call requires no more than seven pages of main content and nine
pages total. The current `docs/paper/main.pdf` is eight pages. The conclusion
ends and references begin on page seven; page eight contains references only.
The present build therefore satisfies the page-count rule. The wrapper is the
official AAAI-27 style, uses anonymous author metadata, and produces US-letter
pages.

The remaining venue-mechanics work is later submission preparation:

- complete the official reproducibility checklist;
- verify supplemental-code/data packaging and anonymity;
- run final citation and format checks after evidence-driven writing;
- preserve the July 21 abstract and July 28 paper deadlines in planning.

These mechanics are not the current scientific blocker.

## Search conclusions

1. The thesis survives external attack, but related work must stop claiming
   that all alternatives are single-run-only.
2. Semantic clustering, cross-run summaries, flexible trace grouping, and
   failure prioritization already exist.
3. The larger defensible novelty target is cross-layer additive semantic
   responsibility that produces a better population-level analyst decision.
4. A fresh, complete, target-blind RQ2 experiment has the highest immediate
   decision value.
5. TraceElephant is the strongest current source candidate; Who&When is a
   partial-observability precedent and possible development/context source, not
   the selected test population.

## Paper and claim impact

External search does not authorize a paper edit. It strengthens the evidence
obligation while preserving the thesis and RQs. Related-work wording and
novelty boundaries belong to a later targeted WRITE after a decisive result.

## Alternatives and decision

- **Who&When:** initially attractive because it is small, citable, and has
  released learned baselines; rejected as the sole next source because it
  cannot expose the full semantic context needed to beat raw action.
- **AgentRx:** diverse and real, but only 115 failures and more naturally a
  per-trajectory constraint-diagnosis benchmark.
- **HINTBench:** closed for tuning after the valid Cycle 0003 test.
- **RQ3 intent dataset:** necessary later, but does not establish a real
  profiling decision.
- **RQ4 cost:** necessary later, but cannot resolve the target-informed RQ2
  objection.

The provisional source decision is TraceElephant, subject to full-paper reread
and independent route convergence.

## Tree/search updates

The search tree adds TraceElephant as a fresh test-only RQ2 candidate and keeps
Who&When/StepFinder as closest-work and partial-observability branches. The
search strategy moves away from action-only safety datasets toward full agent
inputs, tool responses, outcome status, and multiple real agent architectures.

## Project-memory updates

None in this node. The root will update current-frontier pointers only after
the final routing report passes independent review.

## Completion assessment and next node

The bounded external search is complete. The next node rereads the complete
paper against these sources, verifies implementation facts and venue format,
and ranks the remaining findings before an experiment route is finalized.
