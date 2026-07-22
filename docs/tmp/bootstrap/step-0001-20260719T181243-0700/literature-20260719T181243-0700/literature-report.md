# Claim-Oriented Literature Grounding Report

Started: 2026-07-19T18:12:43-07:00
Completed: 2026-07-19T18:19:16-07:00
Parent: BOOTSTRAP Step 0001, EXPERIMENT_GATE
Node: B2 — Closest-work, baseline, and experiment-grounding audit

## Objective And Coverage Boundary

The node tested whether the intended claim—automatic process-level oversight of long-horizon Agents using cross-session workspace-centered action trajectories—was already established. It searched direct automatic diagnosis, repository coding traces, harness attribution, online intervention, cross-session aggregation, long-lived agents, persistent multi-artifact workspaces, process metrics, and observability taxonomies. The search prioritized primary papers, official repositories, and official datasets. It did not attempt an exhaustive survey of human-facing software visualization because the active scientific scope excludes human-interface claims.

## Entry Claims

1. A queryable workspace-centered trajectory may improve automatic diagnosis over final artifacts, summaries, raw logs, and counts.
2. Cross-session continuity and artifact lifecycle may contain incremental information.
3. The same representation may expose skill or harness behavior that causes waste.
4. A supervisor Agent may identify when to intervene.

## Search Method And Exact Sources

Searches were run on 2026-07-19 using combinations of `automated failure diagnosis agent execution trajectories`, `repository-level coding trajectory failure diagnosis`, `harness trace diagnosis repair`, `online auditing earliest decisive error`, `cross-session agent diagnosis`, `persistent multi-artifact workspace benchmark`, `trajectory behavioral drivers`, `agent observability fault detection`, and named-work follow-ups. Full PDFs were downloaded and text-searched for all retained papers except AgentTelemetry, whose primary OpenReview PDF was readable through the web tool but rejected direct local download with HTTP 403.

Primary sources and artifacts include:

- AgentRx paper and `https://github.com/microsoft/AgentRx`;
- TrajAudit `https://arxiv.org/abs/2605.26563` and `https://huggingface.co/datasets/dengdan1999/RootSE`;
- AgentForesight `https://arxiv.org/abs/2605.08715`, `https://github.com/ZBox1005/AgentForesight`, and `https://huggingface.co/datasets/ZBox008003/AFTraj`;
- AgentDiagnose `https://aclanthology.org/2025.emnlp-demos.15/`;
- OR-Space `https://github.com/0xzhouchenyu/OR-Space` and `https://huggingface.co/datasets/Chenyu-Zhou/OR-Space`;
- Cross-Session Threats and `https://huggingface.co/datasets/intrinsec-ai/cstm-bench`;
- AgingBench `https://github.com/VITA-Group/AgingBench`;
- AgentTelemetry OpenReview `owdmAYFk6k` and AIware 2026 acceptance page;
- official AAAI-27 Main Technical Track/AI Alignment, AAAI-26 Demo, and IAAI-27 calls.

## Verified Findings

### Direct same-claim pressure

AgentRx already turns trajectories into a normalized representation, generates static and dynamic invariants, checks them, and asks an LLM judge to localize and classify failures. TrajAudit already gives an investigator Agent filtered repository traces, a test-failure prior, and on-demand retrieval, then measures localization and token cost. AgentForesight already trains an online auditor to alarm at the earliest decisive error and decide whether execution should continue. HarnessFix already builds harness-aware provenance and maps failures back to harness artifacts for repair. REFLECT already treats intervention outcome as evidence for or against a causal attribution.

Therefore the initial broad wording “automatic diagnosis from Agent trajectories” is not defensible as novelty. Neither “harness diagnosis” nor “early intervention” can be claimed without direct comparison.

### Remaining distinction

The closest systems still usually treat one task execution or a known failed run as the unit and emphasize textual Thought–Action–Result traces, orchestration provenance, or memory state. The project’s strongest remaining distinction is a cross-session trajectory of *realized workspace transformation*: ordered actions are bound to persistent artifacts whose creation, revisitation, modification, validation, movement, and deletion outlive a session. The target pathologies also include progress stalls and successful-but-wasteful work, not only critical failure steps.

This distinction is not automatically novel. OR-Space already makes a persistent multi-artifact workspace the task setting; AgingBench studies 8–200-session lifespans with temporal dependency graphs; Cross-Session Threats demonstrates that aggregate session evidence can be necessary. The scientific claim must therefore be incremental and empirical: realized artifact evolution supplies diagnostic information beyond equivalent raw-log access, counts, outcomes, and session summaries.

### Evaluation consequences

The largest confound is information budget. A structured query condition may win merely because raw logs are truncated or difficult to retrieve. The comparison must use the same diagnosis model, prompt, context budget, and tool-call budget, while giving the raw-log baseline usable search/retrieval tools. Simple counts, duration, task difficulty, model, and harness identity must be controlled because Beyond Resolution Rates shows that apparent trajectory effects can reverse after difficulty control.

Independent labels cannot be derived from Agent Nebula’s own features. Labels should include state/failure class, earliest or supporting interval, affected artifacts, and intervention need. Selected controlled cases should use replay or injected harness defects so that correcting the cited cause can validate attribution. Naturalistic cases require expert adjudication from full evidence, blinded to condition outputs.

### External assets

RootSE is the closest coding-failure corpus; its current public dataset states 102 instances and eight agent/model combinations. AFTraj-2K supplies 2,276 safe/unsafe prefix-labeled trajectories for online auditing. AgentRx provides code, sample trajectories, and a ten-category failure taxonomy. OR-Space supplies a non-coding persistent multi-artifact environment. CSTM-Bench supplies cross-session and benign-hard cases but is security-specific. AgingBench supplies controlled multi-session reliability mechanisms. These assets can reduce benchmark construction cost, but none directly provides labels for workspace process pathologies such as repeated rediscovery, validation debt, abandoned artifacts, or documentation/test churn.

## Novelty And Root Disposition

The generic diagnosis claim is rejected. The leading claim is sharpened to:

> Under matched information and model budgets, does a supervisor Agent gain incremental diagnostic and evidence-localization accuracy from a queryable, cross-session account of realized workspace evolution, especially for progress stalls and successful-but-pathological long-horizon work?

This is a root-level scientific change but not a reduction to an easier problem. It removes already-claimed territory and makes the remaining claim more falsifiable. The first experiment must be a small matched-budget diagnostic study rather than more visualization or a large diagnostic implementation.

## Alternatives Kept Live

- Raw logs with competent retrieval may match the workspace trajectory; then the contribution is compression/cost rather than accuracy.
- Counts and final outcomes may explain all apparent process signal; then the workspace representation is not scientifically necessary.
- Native sessions may omit decisive file effects; then AgentSight system evidence becomes necessary.
- Coding and auto-research may not share a useful pathology taxonomy; then the paper must report domain-specific diagnoses rather than force one label set.

## Canonical State Updates

- Added the complete search map, corpus, closest-work table, mandatory baselines, assets, and novelty verdict to `docs/background-related-work.md`.
- Downloaded and verified retained PDFs under `docs/reference/`.
- The next root update must append the sharpened claim to `docs/idea-story.md` without rewriting the immutable Initial Narrative.
- `docs/evaluation.md` must make the matched-budget raw-log retrieval baseline and success-with-pathology slice explicit.

## Remaining Uncertainty

1. AgentTelemetry’s anonymous repository and full local PDF remain inaccessible by direct download.
2. Complete official TrajAudit code was not located; RootSE itself is public.
3. The availability and schema compatibility of naturalistic multi-day auto-research traces has not been audited.
4. Process-mining literature has not yet been searched deeply; object-centric process mining may provide a stronger formal model and additional same-claim pressure.

## Next Node

B3 should formalize the sharpened scientific contract and design the smallest valid pilot: independently label a stratified set of cross-session coding and auto-research trajectories, then compare final-only, session-summary, matched raw-log retrieval, counts, and workspace-trajectory query conditions using one fixed supervisor model and budget.
