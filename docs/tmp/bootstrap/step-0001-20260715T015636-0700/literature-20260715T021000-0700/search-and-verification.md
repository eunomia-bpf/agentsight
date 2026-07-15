# Literature Search And Source Verification

Timestamp: 2026-07-15T02:10:00-07:00
Gate: BOOTSTRAP EXPERIMENT_GATE
Parent: step 0001 node B2
Status: complete for the declared first-pass boundary

## Objective and claims

The search tested three name-free candidate claims:

1. Joining native coding-agent events, Git changes, and current survival exposes
   process/outcome relationships unavailable from either source alone.
2. Stable coordinated views over that join improve realistic long-horizon
   review tasks compared with Git-only and event-table interfaces.
3. Event-resolved histories reveal recurring agent-development patterns that
   remain meaningful when connected to durable outcomes.

The declared coverage boundary included the seven historical visualization
families named by the user, Git visual analytics and mining tools, coding-agent
trajectory/replay/survival work through July 2026, browser visualization and
trace tools, and accepted software-visualization evaluation protocols. It did
not attempt an exhaustive bibliometric census.

## Queries and revisions

Searches were run on 2026-07-15 with primary-source follow-up. Query families:

- `SeeSoft line oriented software statistics 1992 DOI`, `Evolution Matrix
  Lanza 2001`, `CodeCity`, `EvoStreets`, `Software Cartography`, `History Flow`,
  `code_swarm`, `Ownership Map`, `Evolution Storylines`;
- `coding agent trajectory visualization`, `AI-assisted programming replay`,
  `long horizon coding agent trajectory analysis`, `agent generated code
  survival`;
- `Git visual analytics software development history`, `software
  visualization evaluation task time accuracy`;
- official ECharts/D3/Cytoscape/uPlot/Perfetto/Gource/Hercules documentation.

The agent branch was revised after RECAP appeared: queries shifted from generic
"agent observability" to same-mechanism combinations of chat/edit/Git/replay
and to survival/trajectory work. The survival branch was revised again after
finding 2026 agent-code and line-lifespan papers.

## Verification method

- Publication metadata was checked against author-hosted PDFs, DOI/proceedings
  pages, DBLP, IBM Research, IEEE/ACM-linked pages, or arXiv primary records.
- Five high-risk papers were downloaded temporarily from arXiv and converted to
  text to inspect data/artifact statements and limitations beyond abstracts.
- Tool capabilities came from official project documentation; current package
  versions and licenses were checked through npm metadata.
- Search snippets and community posts were excluded from novelty decisions.

## Verified primary evidence

| Source | Verified fact relevant to the decision |
|---|---|
| [SeeSoft](https://doi.org/10.1109/32.177365) | Maps each source line to a thin row, colors line-oriented statistics, and reports interactive use at up to 50k lines. |
| [Evolution Matrix](https://doi.org/10.1145/602461.602467) | Organizes versions and classes in a matrix and categorizes evolution shapes. |
| [CodeCity](https://doi.org/10.1145/1370175.1370188) | Uses packages as districts and classes as buildings with locality/orientation goals. |
| [EvoStreets](https://doi.org/10.1145/1879211.1879239) | Makes development history visible through smooth, stable incrementally evolving layouts. |
| [Software Cartography](https://doi.org/10.1002/smr.414) | Uses LSI and MDS so position reflects vocabulary; motivates cross-version stable comparison. |
| [History Flow](https://research.ibm.com/publications/studying-cooperation-and-conflict-between-authors-with-history-flow-visualizations) | Reveals collaboration patterns through contribution survival and corroborates them statistically. |
| [code_swarm](https://doi.org/10.1109/TVCG.2009.123) | Explicitly studies an organic visualization, its design, public response, and casual/developer audiences. |
| [Ownership Map](https://rmod-files.lille.inria.fr/Team/Texts/Papers/Girb05cOwnershipMap.pdf) | Maps version-control authorship to code ownership and developer knowledge questions. |
| [Evolution Storylines](https://doi.org/10.1145/1879211.1879219) | Uses storyline/metro-map inspiration to show developer interactions with more detail than animation. |
| [Githru](https://doi.org/10.1109/TVCG.2020.3030414) | Uses scalable Git graph abstraction and was evaluated with domain cases and a 12-developer controlled study. |
| [RECAP](https://arxiv.org/abs/2605.01104) | Captures Copilot chat plus shadow-Git edits in VS Code, merges them for timeline replay, and deployed for two weeks with 41 students. |
| [AgentSeer](https://doi.org/10.1609/aaai.v40i48.42392) | Visualizes temporal action and component graphs for multi-agent observability and red teaming. |
| [Understanding Code Agent Behaviour](https://arxiv.org/abs/2511.00197) | Analyzes normalized trajectories from three code agents and shows behavior/failure differences beyond success rates. |
| [Agent trajectories as programs](https://arxiv.org/abs/2606.16988) | Claims agent-identifiable procedural signatures and releases an auditing library. |
| [Will It Survive?](https://arxiv.org/abs/2601.16809) | Performs agent-vs-human survival analysis over 201 repositories and releases a package. |
| [CLSA](https://arxiv.org/abs/2606.04993) | Defines line birth/death with migration handling and publishes a Zenodo replication package. |
| [Merino et al.](https://doi.org/10.1016/j.jss.2018.06.027) | Reviews 181 software-visualization evaluations and requires stronger real-system and controlled evidence. |

## Tool capability and license verification

Local npm metadata on 2026-07-15 reported ECharts 6.1.0 (Apache-2.0), D3 7.9.0
(ISC), Cytoscape.js 3.34.0 (MIT), uPlot 1.6.32 (MIT), PixiJS 8.19.0
(MIT), and Playwright 1.61.1 (Apache-2.0). Official documentation verifies:

- ECharts events and `datazoom`, datasets, visual mapping, and broad chart
  families;
- D3 hierarchy, treemap, force, chord, stack, brush, drag, and zoom;
- Cytoscape.js preset/stable positions, rich layouts, gestures, selection,
  graph algorithms, animation, and image export;
- uPlot's compact high-frequency time-series rendering;
- Perfetto's browser-local Trace Event support and large-trace navigation;
- Gource 0.56 custom/Git history animation;
- Hercules Git burndown, ownership, couples, churn, and sampling controls.

## Result and decision

The search falsified any novelty claim based only on replay, joining chat to
edits, trajectory-pattern analysis, or agent-code survival. It supports a more
specific and still ambitious target: a cross-vendor, repository-level join
between observed process and durable outcomes, evaluated through questions
that require both. The user-requested seven families are historically grounded
but become contributions only through this evidence model and evaluation.

## State updates and next action

`docs/background-related-work.md` was replaced with the current novelty map.
The hypothesis frontier retains H1 but raises its same-claim risk; H2 becomes a
stronger competing explanation. Next: use the baseline handoff to select an RQ1
preflight after the artifact skeleton exists, and require a metric cross-check
before interpreting Git-derived views.
