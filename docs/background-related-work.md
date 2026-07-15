# Background And Related Work

Last updated: 2026-07-15T02:10:00-07:00
Source/command: primary papers, official proceedings/project documentation,
official npm metadata, and the detailed reports linked below
Completeness: first BOOTSTRAP coverage pass complete; RECAP artifact availability
and external user-study recruitment remain unresolved

Detailed reports:

- [search and source verification](tmp/bootstrap/step-0001-20260715T015636-0700/literature-20260715T021000-0700/search-and-verification.md)
- [coverage and contradiction review](tmp/bootstrap/step-0001-20260715T015636-0700/literature-20260715T021000-0700/coverage-review.md)
- [baseline and experiment handoff](tmp/bootstrap/step-0001-20260715T015636-0700/literature-20260715T021000-0700/baseline-handoff.md)

## Search Log

| Date | Query/source | Purpose | Result |
|---|---|---|---|
| 2026-07-15 | SeeSoft, Evolution Matrix, CodeCity, EvoStreets, Software Cartography, History Flow, code_swarm, Ownership Map, Evolution Storylines | Verify the seven historical families | Primary metadata and author/official PDFs verified; several user-supplied dates were corrected or made precise. |
| 2026-07-15 | coding-agent trajectory analysis, replay, observability, survival, long-horizon | Find same-problem and same-claim work | RECAP is the closest process-replay system; recent trajectory and survival papers create high empirical-overlap risk. |
| 2026-07-15 | Git visual analytics, evaluation of software visualization | Find commit-only baselines and accepted protocols | Githru and the Merino et al. review imply real systems, task accuracy/time, case studies, usability, and engagement evidence. |
| 2026-07-15 | official ECharts, D3, Cytoscape.js, uPlot, Perfetto, Gource, Hercules docs and npm metadata | Bound custom implementation | Existing libraries cover charts, stable/preset graphs, large time series, trace timelines, animation, and Git burndown/coupling. |

## PDF Corpus

No PDFs are committed. Eight open-access, high-risk or method-relevant papers
are retained locally under ignored `docs/reference/` for full-text claim and
protocol checks. Durable claims below link public primary pages, and each active
BibTeX entry records its verification source and local-PDF availability.

## Claim-Oriented Novelty Map

| Claim | Closest prior work | Same-claim risk | Novelty delta | Baselines implied | Expansion opportunity |
|---|---|---:|---|---|---|
| Joining fine-grained coding activity with code evolution recovers context unavailable from chat or Git alone. | [RECAP](https://arxiv.org/abs/2605.01104) | High | Cross-vendor native histories; repository-level multi-session evolution; explicit recorded-event/candidate-actual-Git/endpoint mismatch. | RECAP position, native event table, Git-only view. | Treat mismatch and durable survival as first-class evidence, not only replay alignment. |
| Coordinated evolution views improve long-horizon process review. | [Githru](https://arxiv.org/abs/2009.03115), RECAP, [AgentSeer](https://ojs.aaai.org/index.php/AAAI/article/view/42392) | Medium-high | Seven coordinated software-evolution projections over event-plus-Git data, shared stable layout and time cursor, decision-specific tasks. | Githru/Git-only, RECAP-style linear replay, event table. | Establish which review questions require a joined representation rather than claiming visual novelty alone. |
| Event granularity exposes stable coding-agent behavior patterns. | [Understanding Code Agent Behaviour](https://arxiv.org/abs/2511.00197), [Agent trajectories as programs](https://arxiv.org/abs/2606.16988) | High | Multi-session repository growth, durable outcomes, and local system evidence rather than benchmark issue trajectories alone. | Published action taxonomies and trajectory statistics. | Link process patterns to commit/survival outcomes and review decisions. |
| Agent-associated code has measurable survival and ownership dynamics. | [Will It Survive?](https://arxiv.org/abs/2601.16809), [Code Lifespan Survival Analysis](https://arxiv.org/abs/2606.04993) | High | Visualization and event-to-outcome provenance rather than a new survival-analysis claim. | Published survival protocols and replication packages. | Use survival as one coordinated projection and validity check; do not claim first agent-code survival study. |
| The system remains interactive across weeks or months. | [Perfetto](https://perfetto.dev/docs/visualization/perfetto-ui), Githru | Medium | Repository/event semantic aggregation with stable spatial views, not general trace rendering. | Perfetto trace export and raw browser benchmark. | Publish a reusable longitudinal dataset/format if privacy permits. |

## Closest Work

| Work | Claim | Method/artifact | Evaluation | Relation | Gap relative to this project |
|---|---|---|---|---|---|
| [RECAP (2026)](https://arxiv.org/abs/2605.01104) | Chat or Git alone cannot reconstruct AI-assisted programming context. | VS Code extension records Copilot chat plus shadow-Git edits; web timeline replay and analyses. | 41 students, two-week project, 2,034 prompts and 8,239 edits. | Same problem and core join mechanism. | Copilot/VS Code-specific; focuses developer-AI interactions and replay, not cross-agent repository evolution, actual Git outcomes, blame, or current survival. |
| [Githru (TVCG 2021)](https://doi.org/10.1109/TVCG.2020.3030414) | Git metadata needs scalable visual analytics. | Commit-graph reconstruction/clustering, summaries, file hierarchy, comparisons. | Domain expert cases and controlled study with 12 developers. | Same evaluation tasks and Git setting; commit-only mechanism. | No agent events or process/outcome mismatch. |
| [AgentSeer (AAAI 2026 demo)](https://doi.org/10.1609/aaai.v40i48.42392) | Raw spans are insufficient for agent observability. | Temporal action and component graphs plus action-level red teaming. | Six-agent demonstration. | Same action observability, different domain goal. | No coding-repository evolution or longitudinal Git join. |
| [Understanding Code Agent Behaviour (ICSE 2026 manuscript)](https://arxiv.org/abs/2511.00197) | Success rates hide meaningful trajectory structure. | Normalized OpenHands/SWE-agent/Prometheus trajectories and manual/statistical analyses. | SWE-bench trajectories; success/failure and localization analyses. | Same event-pattern problem. | Benchmark tasks rather than days-to-months product evolution; no visualization artifact or durable history. |
| [Will It Survive? (EASE 2026 manuscript)](https://arxiv.org/abs/2601.16809) | Agent-authored code longevity differs from human code. | File/line survival over 201 repositories and 200k+ units. | Kaplan--Meier, Cox models, modification taxonomy, released package. | Same survival question. | No process events; authorship starts from agent PR labels. This project must not claim novelty for survival analysis itself. |
| [Hercules](https://github.com/src-d/hercules) | Full Git history supports fast burndown, ownership, coupling, and churn analysis. | Go analysis DAG plus plotting tools. | Open-source system and documented large-repository runs. | Same Git-derived metrics and several view families. | No native agent events; inactive release line increases reproduction risk. |

## Historical Foundations

- [SeeSoft](https://dblp.org/rec/journals/tse/EickSS92) maps each source line
  to a thin colored row and reports interaction over up to 50,000 lines.
- [The Evolution Matrix](https://www.inf.usi.ch/lanza/PUBS/P/Lanz2001c.pdf)
  represents versions and classes/files as a matrix and classifies recurring
  evolution shapes.
- [CodeCity](https://doi.org/10.1145/1370175.1370188),
  [EvoStreets](https://doi.org/10.1145/1879211.1879239), and
  [Software Cartography](https://doi.org/10.1002/smr.414) establish the city
  metaphor, incrementally stable layouts, and semantically meaningful stable
  maps respectively.
- [History Flow](https://research.ibm.com/publications/studying-cooperation-and-conflict-between-authors-with-history-flow-visualizations)
  makes contribution survival visible; [code_swarm](https://doi.org/10.1109/TVCG.2009.123)
  studies organic animated histories; [Software Evolution Storylines](https://doi.org/10.1145/1879211.1879219)
  uses storyline/metro-map conventions to show developer interaction.
- [Ownership Map](https://rmod-files.lille.inria.fr/Team/Texts/Papers/Girb05cOwnershipMap.pdf)
  connects repository changes to developer knowledge and responsibility.

## Mandatory Baselines

| Baseline | Official artifact/version | Runnable status | Visible information | Tuning surface | Protocol | Risk | Consequence |
|---|---|---|---|---|---|---|---|
| Git-only | local Git plus official `git log`, `diff`, `blame` | Runnable | Commits, files, lines, authors, current survival | time range, rename threshold, first-parent/all | Same repository/time range; no agent fields | Merge/squash and rename ambiguity | If it answers process tasks equally well, the event-level claim fails. |
| Native event table | `agent-session` normalized JSON | Runnable after exporter | prompts, tools, paths, status, tokens, timestamps | filtering/aggregation only | Same events without coordinated views or Git join | Raw logs can leak private text | If it matches the gallery, visualization utility is unsupported. |
| Perfetto timeline | current official browser UI; legacy Trace Event JSON accepted | Runnable export; external UI | timestamped tracks and event detail | track mapping | Same event set converted without gallery-specific views | Not repo spatial/survival aware | Establishes whether custom timeline work is necessary. |
| Gource | [0.56](https://gource.io/) | Not locally installed; custom-log export is feasible | animated file tree and actors | time scale, filters, colors | Feed equivalent Git and agent-touch logs | Poster-oriented and no analysis tasks | If animation alone answers tasks, richer playback may be unnecessary. |
| Hercules | [v10.7.2](https://github.com/src-d/hercules) | Not installed; Docker/source possible | Git burndown, ownership, couples, churn | sampling/granularity/identity map | Cross-check Git-derived aggregates on one repository | Last release 2020; optional TensorFlow plotting deps | Metric disagreement blocks interpretation until resolved. |
| RECAP position | [arXiv:2605.01104](https://arxiv.org/abs/2605.01104) | Paper verified; public code link not found in full text | merged chat/edit replay and analysis | system-specific | Compare supported questions and information model, not fabricated runtime numbers | Artifact availability unresolved | Claims must remain differentiated even without a runnable comparison. |

## Experimental Precedents And External Assets

| RQ | Accepted paper/protocol | Asset | Reusable design | Required deviation/glue |
|---|---|---|---|---|
| RQ1 | RECAP's parallel streams; Githru's Git-history abstraction | Local native sessions; Git plumbing; RECAP paper | Explicitly compare information available from each source and the join | Add observed/committed/surviving mismatch audit and rename handling. |
| RQ2 | ICSE trajectory study and published action taxonomies | SWE-bench experiment trajectories where licensing permits | Predefine action classes; compare success/failure and agents | Extend from single issue attempts to multi-session repository evolution and durable outcomes. |
| RQ3 | [Merino et al.](https://doi.org/10.1016/j.jss.2018.06.027) evaluation guidance; Githru controlled tasks | Real OSS repositories and recorded task answers | Accuracy/time plus case study, usability, recollection/engagement | Use process-review tasks and include event-table and Git-only baselines. |
| RQ4 | Perfetto large-trace UI and Githru graph abstraction | Synthetic scale-up from real event distributions plus full local history | Report throughput, size, latency, memory and semantic zoom | Add stable spatial layouts and linked selection benchmarks. |
| Survival projection | Will It Survive replication package; [CLSA Zenodo package](https://doi.org/10.5281/zenodo.20714794) | Agent-labelled PR histories and line-survival protocol | Rename/refactoring-aware lineage checks and censored survival | Treat as validation/projection, not central novelty or causal agent attribution. |

## Absorbable Ideas

| Source | Idea to absorb | Claim expansion | Experiment implication | Risk |
|---|---|---|---|---|
| RECAP | Shadow history preserves discarded work. | Model observed-but-not-committed changes explicitly. | Quantify each mismatch category. | Native session logs may lack exact edit snapshots. |
| Githru | Adjustable history abstraction and task-derived requirements. | Tie semantic zoom to review tasks. | Ablate stable aggregation and measure task effects. | Reimplementing its commit graph would bloat scope. |
| Software Cartography | Stable coordinates enable comparison and spatial memory. | One layout across time and views. | Compare stable versus recomputed layout. | Semantic layouts can surprise users; hierarchy-first layout is safer initially. |
| Hercules | Incremental burndown and explicit sampling/granularity. | Reuse verified Git metrics instead of inventing survival math. | Cross-check aggregates and report sampling settings. | Old artifact and heavy optional dependencies. |
| Trajectory studies | Action sequences and repeated edits distinguish agent behavior. | Connect behavior to durable repository outcomes. | Define patterns before final data inspection. | Post-hoc pattern naming would invalidate inference. |

## Adjacent Communities

| Community | Why relevant | Keywords | Useful sources |
|---|---|---|---|
| VIS/TVCG/visual analytics | Coordinated views, dynamic graphs, evaluation | semantic zoom, insight evaluation, stable mental map | Githru, visual-analytics evaluation surveys |
| VISSOFT/ICSE/MSR | Software history, program comprehension, empirical protocols | evolution, repository mining, ownership, survival | Seven historical families, trajectory studies, survival papers |
| Systems observability | Large event streams and trace interaction | timeline, trace query, cross-layer correlation | Perfetto and Trace Event format |
| HCI/CS education | Naturalistic AI-assisted programming and replay studies | process replay, longitudinal classroom deployment | RECAP and History Flow |

## Venue Evaluation Patterns

The strongest cross-domain pattern is a mixed evaluation: real-system case
studies for open-ended discovery, controlled tasks for time/accuracy, qualitative
strategy evidence, and computational scalability. The 2018 systematic review
found that many software-visualization papers lacked strong evaluation and
explicitly recommends real open-source systems and controlled experiments when
variables can be controlled. A poster/demo-only gallery would not support the
paper's target claim.

## Must-Read List

1. RECAP (highest same-mechanism risk).
2. Githru (closest visual-analytics and evaluation precedent).
3. Merino et al. evaluation review (protocol obligation).
4. Understanding Code Agent Behaviour and Agent Trajectories as Programs
   (behavior-pattern overlap).
5. Will It Survive? and CLSA (survival overlap and AST-aware line matching).
6. SeeSoft, Evolution Matrix, Software Cartography, History Flow, code_swarm,
   Ownership Map, and Evolution Storylines (design foundations).

## Novelty Verdict

- **Overall same-claim risk:** high if framed as replay or agent-code survival;
  medium if the contribution is the explicit cross-vendor event-to-durable-
  outcome representation plus demonstrated review utility.
- **Ambitious target claim:** coordinated event-plus-Git evidence enables
  process-review judgments that commit-only and event-only interfaces cannot
  reliably support over long horizons.
- **Claims requiring stronger evidence:** join fidelity, pattern predefinition,
  human review utility, and interaction scale.
- **Larger opportunity:** make disagreement between observed actions, committed
  changes, and surviving code an empirical object rather than hiding it.
- **Mandatory baselines:** Git-only, event table, Perfetto, Gource where
  applicable, Hercules metric cross-check, and a position-level RECAP comparison.
- **Next action:** preserve the current strong thesis, implement the minimum
  joined representation needed for an RQ1 real preflight, and do not claim
  authorship or causality from timestamps alone.
