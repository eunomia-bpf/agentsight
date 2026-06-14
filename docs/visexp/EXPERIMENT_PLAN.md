# Experiment Plan: AgentFlame

Last updated: 2026-06-14
Stage at update: experiment-design
Source/command: `docs/visexp/RESEARCH_PLAN.md`, `.agentsight/agentflame/latest/agentflame.json`
Completeness: partial

## Thesis

AgentFlame is better for forensic debugging and audit of AI coding agents in a
local developer repository because it combines semantic intent frames with
deterministic system-effect provenance and folded-stack aggregation.

## Paper Type

- Type: systems-for-ML observability and measurement tooling.
- Target venue: OSDI/SOSP-style systems venue.
- Artifact status: Rust CLI prototype with a full local-history run; exact
  AgentSight live lineage has a scoped smoke, while native export is pending.
- Main reviewer risk: the work will be rejected as "just another agent
  trace/flamegraph UI" unless the evaluation proves semantic attribution answers
  questions that span-duration traces and process summaries cannot.

## Claim Ledger

| ID | Claim | Scope | Metric/evidence needed | Status |
|----|-------|-------|------------------------|--------|
| C1 | AgentFlame generates semantic folded stacks over real local agent histories. | This repository's readable Codex/Claude sessions. | Session/tool/LLM counts, folded totals, generated artifacts. | supported |
| C2 | Local one-word LLM tagging is syntactically feasible. | 3B llama.cpp full run; later 0.6B/1B/3B. | Invalid rate, cache, latency, failures, tag coverage. | supported for 3B syntax |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic/flat baselines. | Full local run. | Mixed-bucket count/weight, examples, ablations. | supported as mechanism |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | Live AgentSight traces. | Join coverage, orphan rate, path/domain specificity. | partial live smoke |
| C5 | Developers answer forensic questions better with semantic effect flamegraphs. | User/task benchmark. | Time, accuracy, false positives, confidence. | unsupported |
| C6 | One-word tags are stable and adequate enough for navigation. | Multi-model repeated runs and human labels. | Invalid rate, stability, adequacy, noisy-tag rate. | partial |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Full run with consistent folded outputs. | B1 | Folded totals mismatch or report cannot be regenerated. | Prototype supports only sampled/local histories. |
| C2 | Low invalid/failure rate and practical local runtime. | B1, B5 | Small models fail often or latency is prohibitive. | 3B works; smaller models remain optional. |
| C3 | Semantic frames split mixed nonsemantic/flat buckets. | B2, B6 | Mixed weight is negligible or examples are not useful. | Semantic frames are a label overlay, not strong information gain. |
| C4 | Live exact effects inherit prompt/session ancestry. | B3 | In-scope orphan rate is high or lineage cannot cross process trees. | Use harness-scoped live evidence only; native export remains future work. |
| C5 | Users solve tasks better with semantic views. | B4 | No time/accuracy/confidence improvement. | Semantic flamegraphs are expert exploratory views. |
| C6 | Tags are stable and adequate. | B5 | High instability, generic/noisy tags, poor adequacy. | Tags are lossy hints only. |

## System-Under-Test Model

- Components: `agentflame` Rust CLI, `normalize-chat-sessions`, llama.cpp HTTP
  tagger, folded stack builder, SVG/dashboard renderer, AgentSight future exact
  lineage input.
- Durable state: generated reports under `.agentsight/agentflame/latest`;
  committed research artifacts under `docs/visexp`.
- Trust/failure boundaries: local raw agent histories are sensitive and are not
  committed; reports should contain hashes, tags, counts, and redacted previews.
- Workloads: local real Codex/Claude histories for AgentSight; future paired
  benchmark tasks run under AgentSight collection.
- Observability: session/prompt/LLM-call tags now; exact
  `tool_call -> shell -> child process -> file/network effect` later.
- Assumptions: a tool/effect inherits semantic intent through session/prompt
  ancestry; the LLM does not classify low-level effects directly.

## Experiment Matrix

| Block | Claim | Experiment | Baselines/variants | Metrics | Oracle | Figure/table | Priority |
|-------|-------|------------|--------------------|---------|--------|--------------|----------|
| B1 | C1,C2 | Full local-history characterization | 3B llama.cpp, cache enabled | sessions, events, tags, invalids, cache, unique stacks | JSON/folded consistency and tag grammar | Table 1 | done/must repeat |
| B2 | C3 | Semantic information-gain audit | semantic, nonsemantic, flat summary | mixed buckets, mixed weight, examples | deterministic stack comparison | Fig. 2 | done |
| B3 | C4 | Live exact-effect lineage | agent-native proxy vs AgentSight exact stream | join coverage, orphan rate, path/domain specificity | lineage checker | Fig. 3/Table 2 | smoke done/native must |
| B4 | C5 | Developer task benchmark | trace tree, span flamegraph, flat summary, nonsemantic stack, semantic stack | time, accuracy, confidence, false positives | hidden answer key | Table 3 | must |
| B5 | C2,C6 | Small-model/stability/adequacy | 0.6B, 1B, 3B, repeated runs | latency, invalid rate, exact stability, adequacy | grammar + human labels | Table 4 | must |
| B6 | C3,C6 | Semantic-axis ablation | no semantic, session-only, prompt-only, prompt+LLM-call | information gain, stack explosion, noisy tags | same queries/tasks | Fig. 4 | must |
| B7 | C6 | Artifact usability smoke | fresh clone/run, documented setup | setup time, errors, output completeness | artifact checklist | Appendix | should |

## Experiment Blocks

### B1. Full Local-History Characterization

- Claim tested: C1, C2.
- Hypothesis: a local small LLM can tag all real repo-related sessions and
  AgentFlame can produce consistent semantic folded stacks.
- Workload: readable local Codex/Claude sessions for this repository.
- Compared systems: none; this is feasibility and artifact integrity.
- Metrics: session count, source count, raw tool/LLM events, tag requests, cache
  hits, llama calls, invalid tags, failures, unique stacks, compression.
- Current result: 205 sessions, 130,632 raw tool events, 90,930 LLM events,
  93,598 tag requests, 0 final tag failures, 24,295 unique semantic system
  stacks.
- Oracle: report parses; folded totals match; tag regex violations are zero;
  warnings are explicit.
- Failure interpretation: reduce claim to sampled histories or fix scanner.
- Reproducibility artifacts: `.agentsight/agentflame/latest/agentflame.json`,
  `.agentsight/agentflame/latest/*.folded.txt`, `tags.json`.

### B2. Semantic Information-Gain Audit

- Claim tested: C3.
- Hypothesis: removing semantic frames merges behavior from multiple task
  regions.
- Workload: same as B1.
- Compared systems: semantic stack, nonsemantic stack, flat process/effect
  summary.
- Metrics: mixed-bucket count, mixed observation weight, top examples.
- Current result: nonsemantic mixed weight 90.219%; flat mixed weight 90.770%.
- Oracle: mixed buckets must list multiple `session/prompt` variants under the
  same nonsemantic or flat key.
- Failure interpretation: claim only availability of tags, not information gain.

### B3. Live AgentSight Exact-Effect Lineage

- Claim tested: C4.
- Hypothesis: AgentSight can join each in-scope system effect to semantic
  ancestry without high orphan rate.
- Workload: 5-10 controlled coding-agent tasks run under AgentSight collection.
- Compared systems: agent-native proxy extraction vs exact AgentSight stream.
- Metrics: in-scope join coverage, orphan rate, child-process depth, path/domain
  specificity, redaction failures.
- Current result: R110 validates 182/182 in-scope effects across three real DB
  exports after adding a harness-synthesized agent-run envelope with llama.cpp
  root tags. Current DB export without that envelope has no session/tool rows.
- Setup/config: run selected Codex/Claude tasks with AgentSight collector;
  export sanitized snapshot; join tags by session/tool/prompt IDs.
- Run budget: smoke 3 tasks; paper 10-20 tasks.
- Oracle: lineage checker rejects any in-scope effect without tool/prompt
  ancestry unless explicitly out of scope.
- Success criterion: high join coverage in native export and concrete examples
  where exact lineage adds path/network/process specificity beyond agent-native
  logs.
- Failure interpretation: paper becomes a local-history profiler, not an exact
  system-effect provenance system.

### B4. Developer Task Benchmark

- Claim tested: C5.
- Hypothesis: semantic effect flamegraphs improve answer accuracy or task time
  for repeated/heavy/divergent system-effect questions.
- Workload: 12-20 tasks generated from B1/B3 traces with hidden answer keys.
- Compared systems: raw trace tree, span-duration flamegraph, flat
  process/effect summary, nonsemantic folded stack, semantic folded stack.
- Metrics: answer accuracy, task time, false positives, confidence, subjective
  workload.
- Setup/config: within-subject counterbalanced design; each task shown once per
  participant; condition order randomized.
- Run budget: pilot 4 developers; paper 12-20 developers or a smaller
  expert-study with careful limitations.
- Oracle: preregistered answer key from exact event/provenance data.
- Success criterion: semantic view improves accuracy or time on core forensic
  tasks without increasing false positives.
- Failure interpretation: keep the tool as an expert exploratory profiler.

### B5. Small-Model Cost And Tag Adequacy

- Claim tested: C2, C6.
- Hypothesis: smaller local models can produce valid one-word tags cheaply, but
  adequacy may vary.
- Workload: 200 session/prompt/LLM-call fragments sampled from B1, with hashes
  and no committed raw text.
- Compared systems: 0.6B, 1B, 3B local models; optional larger reference model;
  deterministic no-LLM baseline only as a lower bound.
- Metrics: latency p50/p95, invalid rate, retry rate, exact stability, generic
  tag rate, human adequacy.
- Oracle: grammar checker plus human adequacy labels.
- Success criterion: at least one small model is practical; paper wording
  honestly scopes noisy tags as navigation frames.

### B6. Semantic-Axis Ablation

- Claim tested: C3, C6.
- Hypothesis: prompt-level tags carry most system-effect partitioning, while
  LLM-call tags mostly help token/accounting views.
- Workload: same full run and B4 tasks.
- Compared systems: no semantic, session-only, prompt-only, prompt+LLM-call,
  session+prompt+LLM-call.
- Metrics: mixed weight, unique stack growth, task accuracy/time, noisy-tag
  burden.
- Oracle: same mixed-bucket checker and B4 answer key.
- Success criterion: semantic axes improve information gain more than they
  increase visual noise.

## Run Order

| Run ID | Stage | Purpose | Config | Seed/reps | Decision gate | Cost | Risk |
|--------|-------|---------|--------|-----------|---------------|------|------|
| R100 | sanity | full local-history run | 3B llama.cpp, `tag_llm_calls=true` | one full run plus cached rerun | report exists and parses | completed | done |
| R110 | decision | exact lineage smoke | 3 live tasks under AgentSight | 3 tasks | join coverage and orphan report | low | high value |
| R120 | decision | small-model comparison | 0.6B/1B/3B | 3 repeats per fragment | invalid/stability/latency table | medium | prompt drift |
| R130 | decision | semantic ablation | session-only/prompt-only/full | one deterministic rerun | mixed-weight delta | low | noisy labels |
| R140 | main | user task pilot | 4 developers | counterbalanced | task protocol works | medium | recruiting |
| R150 | main | user task paper run | 12-20 developers | counterbalanced | C5 verdict | high | strongest missing evidence |

## Tracker Handoff

- Update path: `docs/visexp/EXPERIMENT_TRACKER.md`.
- Result path convention:
  - `.agentsight/agentflame/latest` for local generated reports.
  - `.agentsight/agentflame/exact-lineage-*` for live AgentSight runs.
  - `.agentsight/agentflame/model-benchmarks.json` for model cost.
  - `docs/visexp/out/user-task-results.*` for benchmark scoring.
- Required tracker columns: Run ID, Claim, Block, Purpose, Command/config,
  Commit, Machine, Seed/reps, Oracle, Decision gate, Result path, Status.

## Baseline Fairness

- Named baselines:
  - span-duration trace/flamegraph: OpenTelemetry-style span tree/flamegraph,
    represented faithfully even if implemented locally.
  - raw trace tree: session/tool/LLM chronological tree.
  - flat process/effect summary: command/effect/path/domain counts.
  - nonsemantic folded stack: same folding mechanism, semantic frames removed.
- Tuning policy: all baselines use the same underlying event set and redaction
  rules.
- What each baseline proves:
  - span/trace baseline proves whether ordinary agent observability suffices.
  - flat summary proves whether traditional process tools suffice.
  - nonsemantic stack isolates semantic labels from flamegraph aggregation.

## Reproducibility

- Hardware/software versions: record GPU, llama.cpp build, GGUF checksum, Rust
  commit, and AgentSight commit in tracker rows.
- Seeds/repetitions: deterministic temperature-0 tagging for main run; repeated
  runs for B5 stability.
- Data/traces: raw local histories remain local and uncommitted; outputs contain
  hashes/redacted previews.
- Scripts/configs: Rust CLI commands and `docs/visexp` evaluators.
- Result file paths: listed in `docs/visexp/RESULTS_SUMMARY.md`.

## Residual Uncertainty

- Current full run is single-repo and observational.
- Current exact lineage evidence is a live in-scope smoke with
  harness-synthesized session/tool envelopes; native collector export is not yet
  proved.
- Current user utility evidence is absent.
- Current tag adequacy is unproven even though syntax validity is strong.
- These limitations are acceptable for internal planning but not for OSDI final
  claims.

## Claim Gate After Results

| Claim | Evidence file(s) | Verdict | Supported wording |
|-------|------------------|---------|-------------------|
| C1 | `.agentsight/agentflame/latest/agentflame.json` | supported | local-history semantic folded stacks |
| C2 | `.agentsight/agentflame/latest/tags.json` | partial | 3B syntactic feasibility |
| C3 | `.agentsight/agentflame/latest/agentflame.json` | supported | semantic partitioning in local workload |
| C4 | `docs/visexp/out/live-lineage-r110.json` | partial | live in-scope smoke; native export pending |
| C5 | user results pending | unsupported | no user outcome claim |
| C6 | model benchmark and labels pending | partial | syntactic tags, adequacy unproven |
