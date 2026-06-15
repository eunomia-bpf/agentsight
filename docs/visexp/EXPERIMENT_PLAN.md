# Experiment Plan: AgentFlame

Last updated: 2026-06-15
Stage at update: supplement / experiment-design
Source/command: `docs/visexp/RESEARCH_PLAN.md`, `.agentsight/agentflame/latest/agentflame.json`
Completeness: partial

## Thesis

AgentFlame's current proven contribution is semantic attribution and
aggregation of AI coding-agent system effects. Its user-debugging benefit is a
hypothesis that requires C5 participant evidence.

## Paper Type

- Type: systems-for-ML observability and measurement tooling.
- Target venue: OSDI/SOSP-style systems venue.
- Artifact status: Rust CLI prototype with a full local-history run; exact
  AgentSight live lineage has harness, native-export, DB-persisted backfill,
  capture-time record-command, and fresh Codex live-record smokes, while
  high-coverage live provenance is pending.
- Main reviewer risk: the work will be rejected as "just another agent
  trace/flamegraph UI" unless the evaluation proves semantic attribution answers
  questions that span-duration traces and process summaries cannot.

## Claim Ledger

| ID | Claim | Scope | Metric/evidence needed | Status |
|----|-------|-------|------------------------|--------|
| C1 | AgentFlame generates semantic folded stacks over real local agent histories. | This repository's readable Codex/Claude sessions. | Session/tool/LLM counts, folded totals, generated artifacts. | supported |
| C2 | Local one-word LLM tagging is syntactically feasible. | 3B llama.cpp full run; later 0.6B/1B/3B. | Invalid rate, cache, latency, failures, tag coverage. | supported for 3B syntax |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic/flat baselines. | Full local run. | Mixed-bucket count/weight, examples, ablations. | supported as mechanism |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | Live AgentSight traces. | Join coverage, orphan rate, path/domain specificity. | fixed command-mode suite passed |
| C5 | Developers answer forensic questions better with semantic effect flamegraphs. | User/task benchmark. | Time, accuracy, false positives, confidence. | unsupported |
| C6 | One-word tags are stable and adequate enough for navigation. | Multi-model repeated runs and human labels. | Invalid rate, stability, adequacy, noisy-tag rate. | partial |
| C7 | The approach is practical as an open-source developer tool. | Fresh clone or clean-worktree run. | Setup/run commands, expected files, runtime/cache, artifact hygiene. | partial |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Full run with consistent folded outputs. | B1 | Folded totals mismatch or report cannot be regenerated. | Prototype supports only sampled/local histories. |
| C2 | Low invalid/failure rate and practical local runtime. | B1, B5 | Small models fail often or latency is prohibitive. | 3B works; smaller models remain optional. |
| C3 | Semantic frames split mixed nonsemantic/flat buckets. | B2, B6 | Mixed weight is negligible or examples are not useful. | Semantic frames are a label overlay, not strong information gain. |
| C4 | Live exact effects inherit prompt/session ancestry. | B3 | Raw orphan rate is mistaken for recall or lineage cannot cross process trees. | R114 passes on a fixed 20-task command-mode Codex suite; broader and full-history exact coverage remain open. |
| C5 | Users solve tasks better with semantic views. | B4 | No time/accuracy/confidence improvement. | Semantic flamegraphs are expert exploratory views. |
| C6 | Tags are stable and adequate. | B5 | High instability, generic/noisy tags, poor adequacy. | Tags are lossy hints only. |
| C7 | Community developers can reproduce the core views without internal harness knowledge. | B7 | Fresh-clone smoke cannot produce expected files or leaks raw traces/artifacts outside the output dir. | Prototype remains a research artifact, not a packaged community tool. |

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
- Observability: session/prompt/LLM-call tags now; capture-time record-command
  session/tool rows exist and have been exercised on the 20-task R114 fixed
  Codex suite; exact per-effect
  `tool_call -> shell -> child process -> file/network effect` is supported for
  that command-mode suite, while broader full-history/cross-repo capture remains
  future work.
- Assumptions: a tool/effect inherits semantic intent through session/prompt
  ancestry; the LLM does not classify low-level effects directly.

## Experiment Matrix

| Block | Claim | Experiment | Baselines/variants | Metrics | Oracle | Figure/table | Priority |
|-------|-------|------------|--------------------|---------|--------|--------------|----------|
| B1 | C1,C2 | Full local-history characterization | 3B llama.cpp, cache enabled | sessions, events, tags, invalids, cache, unique stacks | JSON/folded consistency and tag grammar | Table 1 | done/must repeat |
| B2 | C3 | Semantic information-gain audit | semantic, nonsemantic, flat summary | mixed buckets, mixed weight, examples | deterministic stack comparison | Fig. 2 | done |
| B3 | C4 | Live exact-effect lineage | agent-native proxy vs AgentSight exact stream plus negative controls | recall, precision, orphan rate, path/domain specificity | lineage checker with false-positive controls | Fig. 3/Table 2 | fixed-suite done |
| B4 | C5 | Developer task benchmark | trace tree, event-count proxy, flat summary, nonsemantic stack, semantic stack; true span-duration remains future if reconstructed from timestamps | time, accuracy, confidence, false positives | hidden answer key plus frozen preregistration | Table 3 | must |
| B5 | C2,C6 | Small-model/stability/adequacy | 0.6B, 1B, 3B, repeated runs | latency, invalid rate, exact stability, adequacy | grammar + human labels | Table 4 | must |
| B6 | C3 | Semantic-axis ablation | no semantic, session-only, prompt-only, prompt+LLM-call | information gain and stack growth; noisy-tag burden and task accuracy/time deferred | same observations, report/folded cross-checks, baseline queries | Fig. 4 | done for C3 mechanism |
| B7 | C7 | Artifact usability smoke | fresh clone/run, documented setup | setup time, runtime/cache, output completeness, artifact hygiene | artifact checklist | Appendix | should |

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
- Workload: 20 controlled coding-agent tasks run under AgentSight collection,
  including read-only, edit, test/debug, dependency, failure/retry, and
  disposable-repo write tasks.
- Compared systems: agent-native proxy extraction vs exact AgentSight stream,
  with concurrent negative-control processes that must not inherit agent
  ancestry.
- Metrics: recall, precision, true positives, false positives, false negatives,
  orphan rate, child-process depth, path/domain specificity, redaction failures.
- Current result: R110 covers and joins 182/318 raw effects across three real DB
  exports, for 57.233% raw coverage, after adding a harness-synthesized
  agent-run envelope. R111 moves that minimal envelope into native
  `collector report export`; the exported snapshots contain 3 sessions/tools and
  the checker joins the same 182/318 raw effects, leaving 136 orphans. R112
  persists those envelope rows into SQLite `sessions` and `tool_calls` tables on
  DB copies and verifies persisted-only export with the same 182/318 raw join.
  R113-live joins 508/508 raw effects across five real read-only Codex tasks.
  R114-smoke adds wrapper negative controls and shows why raw join rate is the
  wrong headline metric: after retargeting the envelope to the real `codex`
  child, it joins 45/45 in-scope effects with 100.0% precision/recall and
  attributes 0/306 observed negative-control effects, while raw join remains
  11.392% because wrapper/sibling/out-of-scope effects stay orphaned. Full R114
  then runs 20 fixed Codex tasks and passes the command-mode gate: 20/20 targets
  completed, 20/20 tasks observed negative controls, 1273/1273 in-scope effects
  joined, 100.0% precision/recall, 0/3170 negative-control effects joined, and
  redaction scan passed.
- Setup/config: run selected Codex/Claude tasks with AgentSight collector;
  export sanitized snapshot; join tags by session/tool/prompt IDs.
- Run budget: smoke 3-5 tasks; paper 20 tasks.
- Oracle: lineage checker rejects any in-scope effect without tool/prompt
  ancestry unless explicitly out of scope, and rejects any attribution of
  concurrent background or sibling-repository negative-control effects.
- Success criterion: >=95% in-scope recall, >=98% precision, 0 negative-control
  over-attributions, 0 redaction failures, and concrete examples where exact
  lineage adds path/process specificity beyond agent-native logs.
- Failure interpretation: if broader replication fails, paper claims exact
  provenance only for command-mode capture-time suites, not arbitrary histories.

### B4. Developer Task Benchmark

- Claim tested: C5.
- Hypothesis: semantic effect flamegraphs improve answer accuracy or task time
  for repeated/heavy/divergent system-effect questions.
- Workload: 12-20 tasks generated from B1/B3 traces with hidden answer keys.
- Compared systems: raw trace tree, explicitly named `event-count-proxy`, flat
  process/effect summary, nonsemantic folded stack, semantic folded stack. A
  true span-duration flamegraph remains a future stronger baseline if
  reconstructed from timestamps.
- Metrics: answer accuracy, task time, false positives, confidence, subjective
  workload.
- Setup/config: within-subject counterbalanced design; each task shown once per
  participant; condition order randomized with a Latin-square or equivalent
  counterbalance.
- Run budget: pilot 5 developers for complete condition coverage; paper 12-20 developers or a smaller
  expert-study with careful limitations.
- Oracle: preregistered answer key from exact event/provenance data.
- Current result: R142-packet generated the current pilot packet from
  R114/R123/R131/full-run inputs: 14 tasks, split into 8 primary utility tasks
  and 6 limitation/comprehension tasks; five conditions (`trace-tree`,
  `event-count-proxy`, `flat-summary`, `nonsemantic-stack`, `semantic-stack`); 70
  blinded packets with recursive forbidden-key leakage checks; a P01-P05
  counterbalanced assignment template; a hidden answer key; script/output
  manifests; and an empty scorer output marked `participant_results_empty`. For baseline fairness, each task's five condition
  excerpts share exactly one `slice_id`, so all views are derived from the same
  evidence slice. R142-scoring now validates response assignment consistency,
  keeps paired task-level semantic-vs-baseline deltas as diagnostics, and gates
  paper-scale C5 with Holm-corrected participant/task/order fixed-effect
  blocked permutation tests plus false-positive guardrails.
- Success criterion: semantic view improves exact answer accuracy by >=10
  percentage points or median task time by >=20% on core forensic tasks, with no
  >5 percentage-point increase in false positives, under the preregistered
  participant/task/order blocked permutation analysis.
- Failure interpretation: keep the tool as an expert exploratory profiler.

### B5. Small-Model Cost And Tag Adequacy

- Claim tested: C2, C6.
- Hypothesis: smaller local models can produce valid one-word tags cheaply, but
  adequacy may vary.
- Workload: 300 session/prompt/LLM-call fragments sampled from B1: 100 session
  summaries, 100 prompt texts, and 100 LLM-call previews, with hashes and no
  committed raw text.
- Compared systems: 0.6B, 1B, 3B local models; optional larger reference model;
  deterministic no-LLM baseline only as a lower bound.
- Metrics: latency p50/p95, invalid rate, retry rate, exact stability, generic
  tag rate, human adequacy.
- Oracle: grammar checker plus human adequacy labels with adequate,
  generic/noisy, and misleading classes.
- Success criterion: at least one local model reaches 0 final invalid tags, p95
  per-fragment latency under 500 ms after model load, >=80% identical-fragment
  stability, >=80% adequate labels, <=20% generic/noisy labels, and kappa >=0.6
  or a weaker claim.

### B6. Semantic-Axis Ablation

- Claim tested: C3. Auxiliary C6 visual-noise evidence and B4 task
  accuracy/time remain deferred.
- Hypothesis: prompt-level tags carry most system-effect partitioning, while
  LLM-call tags mostly help token/accounting views.
- Workload: same full run and B4 tasks.
- Compared systems: no semantic, session-only, prompt-only, prompt+LLM-call,
  session+prompt+LLM-call.
- Metrics: mixed bucket weight, non-dominant residual mixed weight, unique stack
  growth, max stack reuse. Task accuracy/time and noisy-tag burden are deferred
  to B4/R124.
- Oracle: same folded observations, total-weight equality checker,
  `agentflame.json` total cross-check, and exact counter match against the
  already generated nonsemantic/session/prompt folded files.
- Success criterion: semantic axes improve information gain more than they
  increase visual noise.
- Current result: R131 reads the existing full folded artifacts without
  rescanning raw traces and preserves total weight for all projections. It also
  records that `agentflame.json` totals match the folded inputs and that
  generated nonsemantic/session/prompt folded files exactly match the script's
  projections. For system effects, no-semantic stacks mix 90.219% of full
  semantic bucket weight with 44.639% non-dominant residual weight; session-only
  leaves 84.180% bucket / 34.138% residual; prompt-only leaves 37.687% bucket /
  7.526% residual. Full session+prompt semantics leaves 0.000% by construction.
  Prompt tags therefore carry most of the system-effect separation. For token
  accounting, prompt+LLM-call still mixes 95.765% of full
  session/prompt/LLM-call bucket weight but only 0.027% residual weight, so
  LLM-call tags should be presented as token-navigation frames rather than
  system-effect attribution frames.

## Run Order

| Run ID | Stage | Purpose | Config | Seed/reps | Decision gate | Cost | Risk |
|--------|-------|---------|--------|-----------|---------------|------|------|
| R100 | sanity | full local-history run | 3B llama.cpp, `tag_llm_calls=true` | one full run plus cached rerun | report exists and parses | completed | done |
| R110 | decision | exact lineage harness smoke | 3 live tasks under AgentSight | 3 tasks | raw coverage, in-scope join coverage, orphan report | low | done |
| R111 | decision | exact lineage native export smoke | same 3 DB exports | 3 tasks | native sessions/tools plus raw join/orphan report | low | done/partial |
| R112 | decision | exact lineage DB-persisted backfill smoke | same 3 DB copies | 3 tasks | persisted sessions/tools plus raw join/orphan report | low | done/partial |
| R114 | decision | broader live exact-lineage suite | 20 `agentsight record` tasks, disposable repos for writes | fixed task manifest | C4 scope can widen only if join/orphan/path/domain/redaction gates pass | medium | live task variance |
| R121 | decision | real local model benchmark | `agentflame bench` over available 0.6B/1B/3B-class GGUF models | 3 fixed fragments x 3 identical repeats | C2 can cite only models that actually ran; C6 remains partial unless stability and adequacy pass | medium | missing model sizes and small smoke sample |
| R122 | decision | redacted tag adequacy packet | 100 session + 100 prompt + 100 LLM-call fragments | deterministic sample | label packet and redaction gate | low | trace privacy |
| R123 | decision | real-fragment stability benchmark | R122 fragment file through 3B llama.cpp server | 300 fragments x 3 identical repeats | C2/C6 can cite 3B stability only if grammar/latency/stability pass | low | missing model sizes |
| R124-scoring | decision | tag adequacy scorer and empty-result gate | R122 label packet with no human labels yet | deterministic scorer over 300 rows | output must have 300/300 candidate tags, stay `human_labels_empty`, and keep C6 partial until labels exist | low | evidence boundary |
| R124-blinding | decision | blinded human labeler sheet | R122 label packet with candidate tags | deterministic export | labelers see row id, level, redacted preview, candidate tag, rubric, label, notes; model/source/stability columns hidden | low | done; labels still missing |
| R124 | decision | human tag adequacy labels | blinded R124 labeler sheet | >=2 labelers if possible | tag adequacy wording | medium | subjective labels |
| R131 | decision | semantic-axis ablation | no/session/prompt/full variants plus token LLM-call projections | deterministic | passed for C3 mechanism: totals and external folded cross-checks preserved; system prompt-only reduces mixed full semantic bucket weight from 90.219% to 37.687% and residual from 44.639% to 7.526%; token prompt+LLM-call remains 95.765% bucket mixed but only 0.027% residual | low | done for C3; C6/B4 deferred |
| R141-packet | decision | superseded user-task packet draft | old `user_task_benchmark.py` packet before same-slice enforcement | deterministic 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | superseded by R142 because same-event-slice fairness was unresolved | low | superseded |
| R142-packet | decision | same-event-slice user-task packet and empty scorer check | `user_task_benchmark.py` over current artifacts; scorer over response template | deterministic 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | packet ready only if leakage, assignment, same-slice, explicit event-count baseline naming, and scorer checks pass | low | done/packet |
| R142-scoring | decision | response-contract and paper-scale user-task scorer gate | `score_user_task_results.py` over response template | deterministic empty-template check | C5 must stay unsupported until real responses; real runs use contract checks, diagnostic paired deltas, participant/task/order fixed-effect blocked permutation tests, and Holm correction | low | done/empty |
| R142-preregistration | decision | freeze C5 analysis before collection | `python3 docs/visexp/r142_preregistration.py` | deterministic over bundle, assignments, answer key, response template, and scorer constants | prereg artifact is `frozen_before_collection`, validates conditions/schema/thresholds, and source hashes match | low | done/protocol |
| R142 | main | user task pilot | 5 developers, five conditions | counterbalanced P01-P05 template | protocol and answer keys work on real responses under the frozen preregistration | medium | recruiting |
| R151 | main | user task paper run | 12-20 developers or scoped expert study | counterbalanced | C5 verdict | high | strongest missing evidence |
| R160 | polish | bounded fixed-session open-source usability smoke | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command against the same output dir; then `python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke-fixed --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json --out docs/visexp/out/artifact-usability-r160.json ...` | one clean run plus cached rerun over fixed inputs | expected files, runtime/cache summary, sanitized input manifest, clean/cached input equality, fully cached rerun, no raw trace commit, generated report path containment | low | done/bounded; full fresh-clone/community usefulness and pre/post write-set audit still open |

## Tracker Handoff

- Update path: `docs/visexp/EXPERIMENT_TRACKER.md`.
- Result path convention:
  - `.agentsight/agentflame/latest` for local generated reports.
  - `.agentsight/agentflame/exact-lineage-*` for live AgentSight runs.
  - `.agentsight/agentflame/model-benchmarks*.json` and
    `docs/visexp/out/model-benchmarks-r12*.json` for model cost/stability.
  - `.agentsight/agentflame/ablations-*` for semantic-axis ablations.
  - `docs/visexp/out/tag-adequacy-results-r124.*` for C6 human-label scoring.
  - `docs/visexp/out/user-task-results.*` for benchmark scoring.
- Required tracker columns: Run ID, Claim, Block, Purpose, Command/config,
  Commit, Machine, Seed/reps, Oracle, Decision gate, Result path, Status.

## Baseline Fairness

- Named baselines:
  - event-count proxy: same event slice rendered with event/count weights and no
    semantic inheritance; this is not a duration baseline.
  - true span-duration trace/flamegraph: OpenTelemetry-style span tree/flamegraph,
    represented faithfully if timestamps are reconstructed in a later packet.
  - raw trace tree: session/tool/LLM chronological tree.
  - flat process/effect summary: command/effect/path/domain counts.
  - nonsemantic folded stack: same folding mechanism, semantic frames removed.
- Tuning policy: all baselines use the same underlying event set and redaction
  rules.
- What each baseline proves:
  - event-count/trace baseline proves whether nonsemantic agent observability
    and count-weighted flame views suffice.
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
- Current exact lineage evidence is split: the R111/R112 DB snapshot/backfill
  smoke still joins only 182/318 raw effects (57.233%), while R114 command-mode
  capture-time record passes on 20 fixed Codex tasks. The remaining uncertainty
  is full-history, cross-repo, and broader workload coverage, not command-mode
  capture-time row creation.
- Current user utility outcome evidence is absent. R142-packet makes the B4
  packet/scorer executable for a pilot, but no participant responses have been
  collected.
- Current tag adequacy is unproven even though syntax validity is strong.
  R124-scoring can score labels and reports the current packet as
  `human_labels_empty` with 300/300 candidate tags, so it is a reproducibility
  artifact rather than adequacy evidence.
- These limitations are acceptable for internal planning but not for OSDI final
  claims.

## Claim Gate After Results

| Claim | Evidence file(s) | Verdict | Supported wording |
|-------|------------------|---------|-------------------|
| C1 | `.agentsight/agentflame/latest/agentflame.json` | supported | local-history semantic folded stacks |
| C2 | `.agentsight/agentflame/latest/tags.json` | partial | 3B syntactic feasibility |
| C3 | `.agentsight/agentflame/latest/agentflame.json` | supported | semantic partitioning in local workload |
| C4 | `docs/visexp/out/native-lineage-r112.json`, `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | supported for fixed command-mode suite; partial broadly | exact lineage over the fixed 20-task command-mode suite; full-history and cross-repo provenance pending |
| C5 | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-results.json` | unsupported | same-slice packet and frozen preregistration exist; no user outcome claim |
| C6 | `docs/visexp/out/model-benchmarks-r123.json`, `docs/visexp/out/tag-adequacy-results-r124.json` | partial | 3B syntactic/stability evidence; adequacy scorer ready but labels empty |
| C7 | `docs/visexp/out/artifact-usability-r160.json` | partial | bounded fixed-session artifact smoke passed; no broad community-tool claim until fresh-clone setup and external-developer feedback exist |
