# Literature Report: Empirical RQs And External-Validity Boundary

Created: 2026-07-22T18:20:00-07:00
Gate: BOOTSTRAP reconstruction
Status: complete for RQ restructuring and RQ5 plan admission

## Objective

Reassess the empirical RQs after the author identified two risks: an obvious
RQ1 and a selected six-project corpus. The search asked which questions are
already occupied, which public sources expose real action/artifact data, and
what the local natural longitudinal cases can legitimately establish.

## Search branches and verified primary sources

| Branch | Primary source or artifact | Verified fact | Consequence |
|---|---|---|---|
| Natural persistent research use | Alzahrani, *Persistent AI Agents in Academic Research* (arXiv:2605.26870) | One investigator reports 96 active days, 75,671 de-duplicated records, 5,760 all-Agent session files, 57 skills, heterogeneous research work, and artifact-level measurement recommendations. | A persistent self-observed case study and “artifact as denominator” are occupied. Our six cases broaden within-author work types but still do not provide population prevalence. |
| Heterogeneous workspaces | *Workspace-Bench 1.0* (arXiv:2605.03596; official OpenDataBox repository) | 388 tasks over five worker profiles, 74 file types, 20,476 files, lineage/dependency structure, four harnesses and seven models. | Heterogeneous workspace structure is not novel; this is a future controlled external workload, not a natural longitudinal corpus. |
| Large public coding traces | NVIDIA Open-SWE-Traces (arXiv:2606.16038; Dataset Viewer checked 2026-07-22) | 207,489 rows, OpenHands/SWE-agent configurations, two model splits, exact tool-call arguments, repository/language, patches, and resolved labels; 18.34 GB Parquet. | Strong external replication source for within-attempt validation/rework/focus relations, but every row is one task attempt rather than persistent cross-session evolution. |
| Public scientific-process traces | IdeaTrail (arXiv:2607.10144; Dataset Viewer checked 2026-07-22) | 1,170 reverse-synthesized ideation/proposal trajectories, 60--270 messages, seven tools, explicit artifact updates. | Adds a non-coding process contrast, but synthetic reverse-to-forward generation cannot establish natural behavior rates. |
| Repository exploration | SWE-Explore (arXiv:2606.07297) | 848 issues and line-level read regions derived from at least two successful trajectories; links context selection to downstream repair. | File-level attention/exploration quality is occupied; our focus question must concern longitudinal hotspot turnover and artifact lifecycle, not generic localization. |
| Procedural behavior | ProcGrep (arXiv:2606.16988; official commit `2e827700...`) | Action atoms, procedures, fingerprints, exact queries, JSD/noise-floor comparisons, and local Claude/Codex/Gemini adapters. | Generic motifs/fingerprints are occupied. Skill episodes must add explicit mechanism boundaries and artifact-class/lineage facts, and use ProcGrep-style within-group noise reasoning rather than claim a new sequence language. |
| Long-horizon research system | FS-Researcher (arXiv:2602.01566) | A file-system knowledge base coordinates context building and report writing across sessions. | Durable file workspaces are a premise, not a contribution. |

## Public-data feasibility checks

The Hugging Face Dataset Viewer was queried read-only. For
`nvidia/Open-SWE-Traces`, `/is-valid` reports preview/viewer/search/filter
support; `/size` reports 207,489 rows and 18,338,420,390 Parquet bytes; the four
config/split cells contain 44,785--57,268 rows. `/first-rows` exposes
`instance_id`, `repo`, `language`, `trajectory_id`, nested messages/tool calls,
tools, `resolved`, reference/model patches, and source metadata. This is enough
for a deterministic stratified sample without downloading the full corpus.

IdeaTrail's official dataset exposes 1,170 rows with message lengths 60--270
and explicit artifact-edit tools. It is suitable only as a domain/schema
triangulation because the trajectories are synthetically reconstructed.

## Claim and RQ audit

| Current question | Non-obvious? | Source support | Disposition |
|---|---:|---|---|
| Activity is not progress | No; already established broadly | Local actions plus partial survival/validation | Remove as a standalone claim. Preserve its measurements inside artifact consolidation. |
| Validation rhythm | Partly; generic test gaps are occupied | Recognized validation in only 3/6 local cases | Retain only as event-ordered response and coverage-stratified within-case evidence; externally replicate where statuses exist. |
| Repeated mutation | Descriptive but incomplete alone | Strong six-case path/effect coverage | Merge with survival, dormancy, and revival into consolidation rather than calling repeats rework or waste. |
| Session continuity | Interesting but old component gate weak | Native overlaps and roles are incomplete in the current projection | Sharpen with explicit source roles and matched pseudo-boundaries; otherwise report N/A. |
| Workspace migration | Useful, but generic action transitions are occupied | Strong path-resolved coverage | Retain the longitudinal hotspot lifecycle and heterogeneous-artifact allocation, not generic transition counts as novelty. |
| Skill source coverage | Old conclusion false | Native source has names, arguments and attribution | Replace with exact invocation/access episodes and footprint stability. No causal effect claim. |
| Tool capability comparison | Separate systems question; currently stalled | Prospective 72-session freeze, no Raw run | Demote from this empirical paper. Do not spend the empirical contract on a readiness/cost arm. |
| External validity | Missing | Public coding and synthetic scientific traces available | Add explicit replication-boundary RQ; never pool these with local cross-session cases as one population. |

## Novelty boundary after reconstruction

The defensible story is not that trajectories, persistent workspaces,
validation gaps, or process fingerprints are new. The narrower empirical gap is
how natural, multi-session Agent work reorganizes persistent heterogeneous
artifact lineages over days: consolidation and revival, validation-aligned
change, hotspot turnover, re-grounding at real session boundaries, and the
observable footprints of explicitly invoked process mechanisms.

The six local projects provide analytic generalization across six work types,
not statistical generalization to all Agents. Public single-attempt corpora are
used to test the direction and coverage of within-session relations; failure to
replicate narrows the claim, while replication does not validate the
cross-session findings.

## Sources

- https://arxiv.org/abs/2605.26870
- https://arxiv.org/abs/2605.03596
- https://github.com/OpenDataBox/Workspace-Bench
- https://arxiv.org/abs/2606.16038
- https://huggingface.co/datasets/nvidia/Open-SWE-Traces
- https://arxiv.org/abs/2607.10144
- https://huggingface.co/datasets/AliceKJ/IdeaTrail
- https://arxiv.org/abs/2606.07297
- https://arxiv.org/abs/2606.16988
- https://github.com/hamidahoderinwale/procgrep
- https://arxiv.org/abs/2602.01566
