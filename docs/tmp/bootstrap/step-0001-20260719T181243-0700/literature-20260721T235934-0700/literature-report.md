# Literature Report: Longitudinal Progress In Agent-Modified Workspaces

Created: 2026-07-21T23:59:34-07:00
Gate: BOOTSTRAP / EXPERIMENT_GATE
Parent: Node B27
Status: complete for empirical-study design and first local-case plan

## Objective And Declared Coverage

The author withdrew the intervention-improvement claim and requested an
empirical study with at least five study RQs, one tool-measurement RQ, and a
first analysis of five or six local projects. This node asks which parts of
that study are already established and which narrower, falsifiable gap remains.

The search covered six threat branches:

1. empirical studies of coding-Agent trajectories and success/failure;
2. procedural representations, motif mining, fingerprints, and exact queries;
3. long-horizon and cross-session failure diagnosis;
4. persistent file-system workspaces for coding and research Agents;
5. real-world Agent-authored open-source evolution; and
6. LLM-as-judge trajectory understanding versus deterministic measurement.

Completion required at least one verified primary source in every branch, the
closest runnable tool to be inspected, and an explicit novelty consequence for
every proposed RQ. The root reread `docs/user-instruction.md`, the complete
`docs/idea-story.md`, the current paper, and the existing PDF corpus before
searching.

## Candidate Claims Without Project Names

1. **Empirical claim.** In work lasting across independently reset sessions,
   action volume is not the same as accumulation of durable,
   verification-associated artifacts; rework and re-grounding can be measured
   directly from action time and artifact state.
2. **Scope claim.** Persistent artifact identity across sessions exposes
   longitudinal structure not present in one-task/one-run action sequences or
   pull-request metadata.
3. **Measurement claim.** Artifact-linked queries recover a class of
   source-verifiable process facts that Final Diff, aggregate Counts, and the
   standard action-only procedural representation do not encode; bounded LLM
   analysis over Raw records is a separate accuracy/cost comparison.

The trajectory reconstruction itself is by construction and is not an
empirical claim. General trajectory analysis, process mining, action-sequence
motifs, behavior fingerprints, failure diagnosis, and persistent workspaces are
not claimed as new.

## Search And Source Verification

| Time | Query or source | Branch | Verified result |
|---|---|---|---|
| 2026-07-21 | `long-running AI agents empirical study progress rework persistent workspace multi-session trajectories artifacts` | long horizon | HORIZON studies 3,100+ trajectories in four domains with a trajectory-grounded LLM judge validated against human labels; generic long-horizon diagnosis is occupied. |
| 2026-07-21 | `coding agents session boundaries rediscovery rework empirical trajectory study context reset repository` | continuity | AgingBench and *Plans Don't Persist* study memory aging and loss of plan signal, but not longitudinal artifact accumulation in a real workspace. |
| 2026-07-21 | `agent trajectory procedural fingerprint ProcGrep artifact evolution workspace progress empirical study` | procedure/tool | ProcGrep is the strongest runnable procedural baseline and already performs deterministic pattern search, fingerprints, entropy/JSD analyses, and local Claude/Codex ingest. |
| 2026-07-21 | `agent behavior trajectories empirical study software engineering` | empirical coding | ASE's thought-action-result study, the ICSE code-Agent behavior study, *Beyond Resolution Rates*, and TRAJEVAL already cover motifs, validation behavior, fault localization, rework/thrashing, and outcome association in benchmark runs. |
| 2026-07-21 | `persistent workspace agent long horizon ML research` | workspace/research | AiScientist and FS-Researcher explicitly use durable file workspaces across stages or sessions and show outcome benefit. A persistent workspace is not novelty. |
| 2026-07-21 | `coding agents in the wild empirical study pull requests` | real projects | AIDev contains 932,791 Agent-authored PRs; current empirical work studies merge, CI, review, size, security, and concurrency from repository metadata, not native action-time workspace evolution. |
| 2026-07-21 | `long horizon agent trajectory LLM as judge` | judge | HORIZON already uses an LLM judge for trajectory failure attribution and validates it with human agreement. An LLM judge is a baseline, not a novelty axis or truth source here. |
| 2026-07-21 | official ProcGrep repository | runnable baseline | Cloned `hamidahoderinwale/procgrep@2e8277003dacaa774b5ef61ba150ae03a4f06693`; inspected README, `METRICS.md`, `STUDIES.md`, adapters, tests, and examples. |

## Closest Work

| Work | What it already establishes | Data and method | Direct threat | Remaining difference |
|---|---|---|---|---|
| Bouzenia and Pradel, *Understanding Software Engineering Agents* (ASE 2025) | Trajectory properties, action 4-grams, repeated actions, fix-without-test, semantic coherence | 120 program-repair trajectories, 2,822 LLM interactions; quantitative sequence mining plus manual coding | General empirical trajectory/motif study | One task attempt is the unit; no stable artifact identity or evolution across independent sessions. |
| Majgaonkar et al., *Understanding Code Agent Behaviour* (ICSE 2026) | Success/failure strategy, length, variance, localization | Three Agents on SWE-bench | Comparative code-Agent behavior is occupied | Benchmark attempts rather than days-long workspace lineages. |
| Mehtiyev and Assunção, *Beyond Resolution Rates* (2026) | Read-first and validation behavior; task difficulty and model identity confound naive length findings; model/framework behavioral effects | 9,374 trajectories, 19 Agents, 500 matched tasks | Any claim that validation, context gathering, or framework behavior is newly discovered | Provides the required confound precedent; does not measure artifact survival or session restart over persistent work. |
| Kim et al., TRAJEVAL / *Coherence Collapse* (2026) | Correct code can be reached then overwritten; search/read/edit precision; thrashing and validation interventions | 16,758 trajectories aligned to reference patches | Rework/coherence-collapse is occupied | Reference-patch task trajectories, not ongoing multi-artifact projects or cross-session continuity. |
| Oderinwale, *Agent Trajectories as Programs* / ProcGrep (2026) | Canonical action atoms, learned procedures, fingerprints, JSD/entropy, exact episodic search, early patterns, local Claude/Codex adapters; deterministic search beats LLMs | 2,639+ benchmark traces plus released MIT-licensed tool | Strongest threat to representation, measurement, fingerprint, query, and LLM-comparison claims | Its standard spine is action-only and each trajectory is one task/session; README explicitly says patterns lack temporal windows and variable binding. Artifact identity, lifecycle, hierarchy, and cross-session lineage remain outside the standard representation. |
| Wang et al., HORIZON (2026) | Cross-domain long-horizon degradation and scalable LLM-judge diagnosis | 3,100+ trajectories, four domains, human validation | Generic long-horizon failure analysis and LLM judge are occupied | No persistent workspace evolution study; this project forbids semantic human/LLM gold. |
| Zhu et al., AgingBench (2026) | Reliability changes across 8--200 sessions; compression, interference, revision, and maintenance aging | ~400 runs, paired probes and dependency graphs | Cross-session degradation and session-local insufficiency are occupied | Studies agent memory state, not how work artifacts accumulate, survive, or are verified. |
| Mehta and Datta, *Plans Don't Persist* (2026) | Plan signal can decay after one action and context management is load bearing | Replay pairing and model-state probes | Session reset/context loss is not automatically a new phenomenon | Does not quantify workspace re-grounding and rework in natural long-running projects. |
| Chen et al., AiScientist (2026) | Structured orchestration plus durable File-as-Bus state improves long-horizon ML research | PaperBench and MLE-Bench Lite with ablations | Durable artifact state and workspace maps are occupied mechanisms | System construction/outcome evaluation, not an observational study of artifact progress and rework. |
| Zhu et al., FS-Researcher (2026) | File-system workspace supports evidence accumulation and report writing across sessions | DeepResearch Bench and DeepConsult | File system as external memory is occupied | Fixed two-stage system; no general action-time workspace evolution analysis. |
| AIDev and Agentic-PR studies (2026) | Large-scale real GitHub Agent contributions, merge/CI/review and change-size characteristics | 932,791 PRs; curated 33,596-PR subset | “First open-source Agent evolution study” is not defensible at PR/commit level | Public data lacks the native reads, failed tests, transient files, and cross-session action lineage needed here. |
| Object-centric process mining / PM4AA / PMAx | Event-object lifecycles, process discovery, features, conformance, software repository process mining, Agent consumption of deterministic process artifacts | Standards and released process-mining software | Event-object modeling and generic process mining are not novel | These are analysis precedents; the paper contribution must be empirical findings about Agent work, not a renamed event model. |

## Same-Claim Risk And Root Disposition

| Candidate claim | Risk | Disposition |
|---|---:|---|
| “We are the first to analyze Agent trajectories beyond outcome.” | Very high | Reject. ASE/ICSE studies and ProcGrep already do this. |
| “We discover edit loops, testing gaps, or behavior fingerprints.” | Very high | Reject as novelty. Reuse their metrics or compare findings. |
| “A file system or persistent workspace helps long-horizon Agents.” | Very high | Reject. AiScientist and FS-Researcher directly establish it. |
| “Deterministic structure beats an LLM on trace queries.” | Very high | Reject as broad claim. ProcGrep already reports this. |
| “Git/PR metadata misses native work.” | Low novelty and low importance | Keep only as a supporting observability contrast. |
| “Days-long work should be measured as durable and verification-associated artifact accumulation across reset sessions.” | Medium | Retain as the central empirical question; closest work studies task attempts, memory aging, or system outcomes rather than this longitudinal unit. |
| “Artifact identity and lifecycle add process-fact coverage beyond action-only procedures.” | Medium | Retain as the narrow tool RQ; compare fairly with ProcGrep, including action-only questions where it should tie or win. |
| “Skill/harness use causes progress or waste.” | High without control | Do not make causal claims from local cases. Report within-case temporal associations and use them only to motivate a later controlled experiment. |

## Experimental Precedents And Implications

| Study question | Precedent to reuse | What to reuse | Required correction for this study |
|---|---|---|---|
| Activity and progress | TRAJEVAL; git-of-theseus-style survival analysis | Intermediate-to-final survival, outcome-independent process measurement | Separate durability and verification; do not invent an opaque weighted progress score. |
| Validation dynamics | ASE trajectory study; *Beyond Resolution Rates* | Test-after-edit sequences, validation investment, task/model confound warning | Use source-native command status and event distance; call it association, not successful validation coverage of a particular change. |
| Rework | TRAJEVAL coherence collapse; ProcGrep patterns | Edit streaks, repeated patterns, sensitivity thresholds | Preserve artifact identity and report distributions rather than one arbitrary “thrash” cutoff. |
| Cross-session continuity | AgingBench; *Plans Don't Persist* | Longitudinal ordering and paired/session-boundary analysis | Measure the observable pre-mutation re-grounding prefix and prior-artifact overlap; do not infer memory contents. |
| Process heterogeneity | ProcGrep; *Beyond Resolution Rates* | canonical atoms, entropy/JSD, within-group noise, matched confound reasoning | Apply ProcGrep officially for action-only procedural variation and add artifact-linked measurements separately. |
| Tool measurement | ProcGrep episodic search; HORIZON LLM judge | exact queries, bounded judge input, fact-level accuracy/cost | Use source-verifiable factual questions, no human semantic labels; stratify action-only versus artifact/cross-session questions. |

## Mandatory Comparison Roles

1. **Final Diff / final workspace:** represents outcome-only inspection. It is a
   lower-information control, not a credible general trace analyzer.
2. **Aggregate Counts:** represents conventional telemetry and activity volume.
   It is a lower-information control.
3. **ProcGrep `2e827700...`:** strongest runnable action-procedure baseline.
   Use its official Claude/Codex adapters and standard action spine when
   possible. If local input coverage fails, report the exact adapter boundary;
   do not substitute a weaker homemade n-gram baseline.
4. **Bounded Raw-log LLM analysis:** represents the requested single-model
   reading approach. Give it the same source membership and a fixed context/
   retrieval budget. It is not ground truth.
5. **Artifact-linked trajectory queries:** proposed measurement for stable
   artifact identity, lifecycle, hierarchy, time, and session lineage.

The main tool interpretation is complementary coverage, not blanket
superiority. Action-only questions test parity with ProcGrep. Artifact-linked
and cross-session questions test the claimed additional information. Raw-log
LLM accuracy, citations, tokens, and latency measure the cost of reconstructing
the same facts dynamically.

## Local Multi-Case Asset Shortlist

The first case study should use repositories with a real Git history and enough
repository-direct native sessions to retain surrounding no-file actions:

| Repository | Direct Claude sessions found | Work type | Initial role |
|---|---:|---|---|
| AgentSight | 153 plus discoverable Codex/Gemini sessions | systems software and research | large coding case |
| ActPlane | 74 plus discoverable other-Agent sessions | systems software and research | large coding case |
| bpf-developer-tutorial | 35 | tutorial, code, documentation | documentation-heavy contrast |
| eunomia.dev | 31 | site, blogs, documentation, code | content/software contrast |
| agentskill-observability-paper | 8 | paper, experiments, code | auto-research case |
| academic-writing-skills | 16 | skills, prompts, tests, documentation | skill/harness-development case |

AgentCap and AgentFS remain useful sensitivity examples but are not primary
cases: only one and zero repository-direct Claude session files were found,
respectively. Global path matching recovers file effects but intentionally omits
surrounding no-file actions, making validation and session-restart measures
incomplete.

## Novelty Verdict And Next Experiment Handoff

- **Overall same-claim risk:** high for generic trajectory analysis, behavior
  motifs, fingerprints, failure diagnosis, persistent workspaces, and
  deterministic search; medium for longitudinal artifact progress across
  independently reset sessions.
- **Surviving central position:** activity volume is not a process measure of
  durable progress. Study how observable artifact changes survive, become
  associated with successful validation, undergo repeated modification, and
  carry across session boundaries in real multi-day Agent work.
- **Tool position:** do not claim a new general trajectory language. Test the
  incremental factual coverage of stable artifact identity and cross-session
  lifecycle over ProcGrep's strongest official action-only representation.
- **First evidence role:** a six-repository multi-case study is supporting and
  hypothesis-generating. It can answer descriptive RQs for this corpus but
  cannot establish causal skill/harness effects or population-wide rates.
- **Paper-strength risk:** five or six author-controlled local projects alone
  are too selected for a broad AAAI empirical claim. A later public or
  prospectively collected corpus is required for external validity, but it must
  be chosen after the local study reveals which metrics have reliable source
  coverage, not before.
- **Immediate next action:** freeze the RQs and operational definitions in a
  Chinese empirical-study design; qualify the six repositories; then run one
  integrated extraction and descriptive analysis over every qualifying native
  session without cherry-picking episodes.
