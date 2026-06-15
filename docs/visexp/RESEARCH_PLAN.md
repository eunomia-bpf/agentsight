# AgentFlame Research Plan

Last updated: 2026-06-15
Stage at update: supplement / experiment-design plus completed full local-session characterization
Source/command: R170 full-history refresh plus R187 launch package generation; latest launch command `python3 docs/visexp/r187_prepare_pilot_materials.py --out docs/visexp/out/user-task-pilot-r142/launch`
Completeness: partial

## Thesis

AgentFlame's current proven contribution is semantic attribution and
aggregation of AI coding-agent system effects: it joins user-level semantic
intent with system-level provenance and flamegraph-style aggregation. The
stronger claim that this improves developer forensics remains a C5 hypothesis
until participant evidence exists.

```text
sessionTag;promptTag;llmcall/tool;process*;effect
```

The paper should not claim novelty as "flamegraphs for agents." Span-duration
flamegraphs already exist for ordinary distributed traces and have been shown
for multi-agent workflows. The claim must be narrower and stronger:

> Existing agent observability shows spans, tools, duration, prompts, costs, or
> logs. It does not directly answer which user-level intent caused which
> process/file/network effects, nor which repeated or heavy effects are
> semantically the same or different across sessions.

## Paper Type

- Type: systems-for-ML observability and measurement tooling.
- Target venue: OSDI/SOSP-style systems venue.
- Artifact status: Rust CLI prototype over real local Codex/Claude session
  histories; AgentSight exact-effect integration has harness and native-export
  smokes but is not yet the primary full-run input.
- Current maturity: stronger than a workshop demo for characterization and
  artifact-internal claims, but not OSDI weak-accept. R184 mechanically reports
  `not_weak_accept` because C5 has no participant responses and C6 has no
  independent human labels; R187 has removed launch friction by packaging the
  frozen R142 materials into P01-P05 participant packets and a blank response
  CSV, but it is not outcome evidence.
- Main reviewer risk: reviewers may see the work as a restyled trace UI unless
  the paper proves semantic attribution plus system provenance answers questions
  that span flamegraphs and flat process summaries cannot answer.

## Closest Baselines And Same-Claim Risk

The related-work risk is real:

- Datadog, SigNoz, New Relic, Honeycomb, Coralogix, Grafana/Pyroscope, and
  Sentry already visualize spans, traces, profiles, and duration-oriented
  flamegraphs.
- Inkeep + SigNoz publicly describes "Flamegraph for Debugging" for multi-agent
  workflows, where each horizontal bar is a span and width is proportional to
  duration. That view exposes sequential/parallel execution, error cascades,
  tool overhead, and sub-agent boundaries.
- LangSmith, Langfuse, Phoenix, and AgentOps expose agent/LLM/tool traces,
  trees, timelines, analytics, prompts, completions, and costs.

Therefore the novelty is not the visual idiom. The defensible novelty is the
specific attribution model and aggregation target:

- Small LLM labels only the semantic control plane: session, prompt, LLM call.
- Deterministic lineage supplies the system plane: tool call, shell, child
  process, file/network effect.
- Folded stacks aggregate repeated task-effect paths across sessions, rather
  than drawing one duration timeline per trace.

Same-claim risk: medium. The individual pieces exist; the combined
`semantic intent -> exact system effect -> aggregated folded stack` model appears
less common and is the paper's best contribution.

## Research Questions

The RQs are now ordered by claim risk. RQ1-RQ3 establish the mechanism; RQ4
and RQ5 decide whether the paper can move from a strong measurement-tooling
paper to an OSDI weak-accept candidate. RQ6 is artifact/community positioning
and cannot substitute for RQ4/RQ5.

### RQ1. Feasibility And Cost

Can a local small LLM tag all session, prompt, and LLM-call contexts for real
AI coding-agent histories with acceptable syntax validity, runtime, and cache
behavior?

Required evidence:

- Full local history run, not a cherry-picked sample.
- Session, prompt, and LLM-call tag counts.
- Invalid-output count and retry/failure behavior.
- Cache hit rate and uncached local llama.cpp calls.
- Model-size comparison for 0.6B, 1B, and 3B models.

Current evidence:

- Completed full local run on `.agentsight/agentflame/latest`.
- 205 readable repo-related sessions analyzed: `codex=78`, `claude=50`,
  `claude-subagent=77`.
- One unreadable root-owned Claude JSONL was skipped and recorded in
  `warnings`.
- 2,463 prompt rows, 303 unique prompt tags, 0 invalid prompt tags.
- 90,930 LLM events, 1,250 unique LLM-call tags, 0 invalid LLM-call tags.
- 93,598 tag requests, 64,297 cache hits, 29,302 llama.cpp HTTP calls, 29,301
  successful final tags, no final tag failures. The one-call difference is
  consistent with a retry that recovered before final failure.
- R170 reran the current full-history path against the local 3B llama.cpp
  server without overwriting `latest`: 325 sessions, 118,021 tag requests,
  82,886 cache hits, 35,136 fresh llama.cpp calls, 64,477 final cache entries,
  0 tagger failures, and folded totals matching the generated report. This is
  mechanism/artifact refresh evidence, not human adequacy evidence.
- R121 started a real local llama.cpp server, repeated three fixed synthetic
  fragments three times each, and produced 9/9 valid 3B tags with 7-41 ms
  request latency after a 1002 ms load. Exact fixed-input stability was mixed:
  2/3 fragments were exact-stable and one coding fragment drifted from
  `refactor` to `test`.
- R122 sampled 300 real redacted fragments from 294 parsed local sessions:
  100 session summaries, 100 prompt fragments, and 100 LLM-call fragments.
- R123 ran the R122 fragment file through the local 3B llama.cpp server with
  3 identical repeats per fragment: 900/900 valid tags, 1002 ms load, p95
  request latency 31 ms, and 285/300 exact-stable fragments.
- R180 ran the same 300 R122 fragments through local 0.6b, TinyLlama 1.1b, and
  3b GGUFs with `--reasoning off`: 2700/2700 valid tags; exact stability
  299/300, 279/300, and 285/300; p95 latency 23/18/32 ms.

Remaining gap:

- R180 is a local operational smoke over different model families and
  quantization paths, not a controlled same-family scaling result. Paper-level
  C6 still needs human adequacy labels over the R122 packet; the TinyLlama 1.1b
  localization-like collapse shows why syntax/stability is not enough.

### RQ2. Semantic Partitioning Beyond Traditional Tools

Do session and prompt semantic frames separate system-effect buckets that
duration trace trees, span flamegraphs, or flat process/file summaries would
merge, while LLM-call tags remain scoped to token/accounting views?

Required evidence:

- Semantic folded stacks and nonsemantic/flat baselines from the same input.
- Mixed-bucket metrics: count, whole-bucket mixed weight, non-dominant residual
  mixed weight, percent of observation weight, examples.
- Disaggregation examples that answer real developer questions such as "which
  semantic task caused repeated cargo test runs?"

Current evidence:

- 130,632 raw tool events and 90,930 raw LLM events.
- 167,005 system-effect observations collapsed into 24,295 unique semantic
  system stacks; compression ratio 6.874x; max stack reuse 6,004.
- Removing session/prompt frames yields 4,209 mixed nonsemantic buckets covering
  150,670 observations, 90.219% of system weight.
- Flat effect grouping yields 4,051 mixed buckets covering 151,590 observations,
  90.770% of system weight.
- Example mixed baselines include `git read`, `cargo test`, `python3 process`,
  `docker process`, and high-volume `tool write/process` stacks that split into
  different `refactor`, `review`, `design`, `research`, and `analyze` regions.
- R131 ran a semantic-axis ablation over the same folded observations without
  rescanning raw traces. All system and token projection totals were preserved,
  `agentflame.json` totals matched the folded inputs, and projected counters
  exactly matched the already generated nonsemantic/session/prompt folded files.
  For system effects, no-semantic projection mixed 90.219% of full semantic
  bucket weight with 44.639% non-dominant residual weight; session-only left
  84.180% bucket / 34.138% residual; prompt-only left 37.687% bucket / 7.526%
  residual. Full session+prompt semantics leaves 0.000% by construction. This
  isolates the contribution: prompt tags carry most of the system-effect
  separation, while session tags provide the remaining provenance context.

Remaining gap:

- Current metrics prove partitioning, not user benefit. They should support a
  mechanism claim, not the full usability claim.
- R131 also shows a boundary condition: token-accounting projections need the
  session axis. Prompt+LLM-call projection still mixed 95.765% of full
  session/prompt/LLM-call token weight, so LLM-call tags should be claimed as
  token-navigation labels, not as substitutes for session/prompt system-effect
  attribution.

### RQ3. Exact Semantic-Effect Lineage

Can AgentSight's exact provenance chain preserve ancestry from user intent to
tool calls, child processes, and file/network effects with low in-scope orphan
rate?

Required evidence:

- Live AgentSight capture, not only Codex/Claude session history.
- `tool_call -> shell -> process* -> effect` join coverage.
- In-scope orphan rate, path/domain specificity, and redaction checks.
- Comparison of agent-native proxy stacks versus exact-effect stacks.

Current evidence:

- The model and fixture checker exist in `docs/visexp/effect_lineage_smoke.py`.
- Current full run is still agent-native session-history input. It extracts
  commands, status, path groups, and effect classes, but it is not a kernel-level
  exact file/network stream.
- R110 live smoke on three real AgentSight DB exports covers and joins 182/318
  raw effects, for 57.233% raw coverage. Within the covered scope it validates
  182/182 effects with 0 orphans after adding a harness-synthesized agent-run
  envelope and llama.cpp root tags.
- R111 moves the minimal envelope into native `collector report export`; the
  exported snapshots contain 3 sessions/tools and the checker joins the same
  182/318 raw effects, leaving 136 orphans.
- R112 persists the minimal envelope into SQLite `sessions` and `tool_calls`
  tables on DB copies, exports with `--no-observed-projection`, and verifies the
  same 182/318 raw join from persisted-only snapshots.
- R113 implements capture-time `record -- <command>` session/tool rows with
  `view_source=record_capture_time_agent_envelope` and verifies the row shape in
  a temp SQLite DB.
- R113-live runs five real read-only `codex exec` tasks under `agentsight
  record`; all five create capture-time session/tool rows and join 508/508 raw
  effects with 0 orphans.
- R114-smoke runs the new precision suite for one task with wrapper negative
  controls. After `--agent-comm codex` retargeting and scoped oracle accounting,
  it joins 45/45 in-scope effects, reports 0 false positives and 0 false
  negatives, and attributes 0/306 observed negative-control effects. Raw join is
  only 11.392% because wrapper/sibling/out-of-scope effects remain orphaned.
- Full R114 runs 20 real Codex tasks, including read-only, edit, test/debug,
  dependency, failure/retry, and disposable-workspace write tasks. After
  missing-root child fallback and disposable-workspace `--skip-git-repo-check`,
  20/20 targets complete, 20/20 tasks observe negative controls, 1273/1273
  in-scope effects join, precision and recall are both 100.0%, 3170
  negative-control effects are observed with 0 joined, and child-depth/path/
  redaction analysis passes.
- R182 exposes and fixes a record-mode network-capture gap by enabling process
  `--trace-net` for `agentsight record`. Two loopback-network Codex tasks then
  complete with 35/35 low-level `codex` process network audit rows joined, 0
  network orphans, 100.0% precision/recall, and 0/604 observed negative-control
  effects joined. The target-specific oracle sees 0/0 loopback or expected
  child-process network rows, so this is record-mode `--trace-net`
  implementation evidence, not target-specific network workload coverage or
  full HTTP payload/URL reconstruction.

Remaining gap:

- The strongest exact-lineage evidence now covers a fixed 20-task command-mode
  suite with negative controls plus a partial record-mode network tracing
  smoke. C4 still should not be stated as a broad cross-repo/full-history or
  target-specific network workload claim until the artifact covers more
  repositories, more agent types, broader network workloads, and user-task
  outcomes.

### RQ4. Developer Utility

Do developers answer forensic questions faster or more accurately with semantic
effect flamegraphs than with trace trees, the explicitly named
`event-count-proxy`, flat process/file/network summaries, and nonsemantic folded
stacks? A true span-duration flamegraph is an optional additional baseline only
if regenerated from timestamps and preregistered separately.

Required evidence:

- Task benchmark with preregistered answer key.
- Baselines: raw trace/tree, explicitly named `event-count-proxy`, flat
  process/file/network summary, nonsemantic folded stack, semantic folded stack.
  A true span-duration flamegraph can be added only if regenerated from
  timestamps and preregistered as a separate baseline.
- Metrics: accuracy, time, confidence, false positives, repeated-effect recall.

Current evidence:

- R142-packet generated a current pilot packet from R114/R123/R131/full-run
  artifacts: 14 questions, 8 primary utility tasks, 6
  limitation/comprehension tasks, five conditions (`trace-tree`,
  `event-count-proxy`, `flat-summary`, `nonsemantic-stack`, `semantic-stack`),
  70 leak-checked blinded participant packets, a P01-P05
  counterbalanced assignment template, a hidden answer key, manifests, a scorer
  output marked `participant_results_empty`, response contract checks, a
  paper-scale C5 support gate, and per-task same-event-slice `slice_id` checks
  across all five conditions.
- The former span-like R142 condition now uses the explicit
  `event-count-proxy` name because folded artifacts do not expose real span
  durations. It must not be cited as a span-duration flamegraph baseline.
- R187 packages the frozen R142 assignment into
  `docs/visexp/out/user-task-pilot-r142/launch`: P01-P05 participant JSON/MD
  files, a blank 70-row response CSV, and a manifest that checks five
  participants, 14 assignments each, no answer key in the launch directory, no
  forbidden oracle/scoring keys in participant payloads, zero real responses,
  and `c5_supported=false`.
- No real participant responses are available.

Remaining gap:

- Without participant responses, the paper can claim improved information
  organization but not improved user outcomes.

### RQ5. Robustness Of One-Word Tags

Are one-word semantic tags stable and adequate enough for navigation across
models, sessions, and prompt distributions?

Required evidence:

- Local 0.6B-/1B-/3B-class model comparison for syntax, latency, and
  temperature-0 repeated-run stability.
- Optional robustness at a small nonzero temperature or a controlled
  same-family scaling curve, if the paper wants those claims.
- Human adequacy labels over session/prompt/LLM-call fragments.
- Generic-tag and malformed-tag rates.

Current evidence:

- The full 3B run has 0 malformed prompt and LLM-call tags.
- R180 covers local 0.6B-/1B-/3B-class syntax/stability on the R122 redacted
  fragment sample: 2700/2700 valid outputs, per-model exact stability
  299/300, 279/300, and 285/300, and p95 latency 23/18/32 ms. It is not a
  controlled same-family scaling curve.
- R124-scoring now reads the R122 human-label packet and emits an auditable
  empty result when no labels exist: 300 packet rows, 300 candidate tags, 0
  final labels, `human_labels_empty`, and `adequacy_supported=false`. This
  prepares the gate but does not support adequacy.
- R124-join now validates the blinded labeler sheet against the source packet,
  records the no-label default state, and emits an empty adjudication template.
  It prepares the two-labeler/adjudication bridge but does not support
  adequacy until real human sheets are joined and scored.
- Some tags are clearly useful (`refactor`, `review`, `test`, `analyze`,
  `design`, `research`), but some are noisy or over-specific
  (`agentsightsm`, `testcodex`, `designcodex`, `bashoutput`).
- TinyLlama 1.1b in R180 is syntactically valid but collapses most outputs to
  localization-like labels, showing why grammar/stability is not adequacy.

Remaining gap:

- The one-word grammar is solved; semantic adequacy is not solved.

### RQ6. Open-Source Developer Usefulness

Can a community developer run AgentFlame on a local agent-history workspace and
obtain the three paper views without learning the internal experiment harness?

Required evidence:

- Fresh-clone or clean-worktree smoke using documented commands.
- One command that either starts or connects to a llama.cpp-compatible server
  and writes `.agentsight/agentflame/latest`.
- Generated artifacts for the three core views: attribution model evidence,
  semantic flamegraph, and baseline-failure comparison.
- Runtime/resource/cost summary for local use, including cache behavior.
- Artifact hygiene: no committed raw traces, generated report path containment,
  raw-trace git hygiene, and explicit warnings for unreadable/skipped traces.

Current evidence:

- The Rust CLI can generate `.agentsight/agentflame/latest/agentflame.json`,
  folded stacks, SVGs, and dashboard artifacts over the local AgentSight
  history.
- R160 verifies a bounded fixed-session local artifact path:
  `.agentsight/agentflame/r160-smoke-fixed` contains the dashboard, folded
  stacks, SVGs, and tag cache for 8 historical Codex sessions; the clean run
  took 1.64 s with 60 uncached llama.cpp calls, and the cached rerun took
  0.11 s with 76/76 cache hits and 0 LLM calls.
- `docs/visexp/verify_artifacts.py` checks committed evaluation artifacts, C5
  response-contract fields, R124 tag-adequacy boundaries, and folded totals.
- `docs/visexp/artifact_usability_r160.py` checks expected artifact files,
  folded-total equality, redacted previews, generated report path containment,
  dirty raw-trace-like paths, a sanitized fixed-input manifest, clean/cached
  input equality, and the cached-rerun gate.
- R160 records that `.agentsight/agentflame/*/agentflame.json` is a local,
  private report because it includes trace roots and session file metadata. The
  public audit artifact is `docs/visexp/out/artifact-usability-r160.json`.
- R170 records a current full-history refresh in
  `docs/visexp/out/full-history-r170.json`: 325 sessions, 142,468 raw tool
  events, 114,837 raw LLM events, 183,714 system observations, 35,136 fresh
  llama.cpp tag calls, and folded-total integrity. The private generated report
  stays under `.agentsight/agentflame/r170-full-current`.
- Raw local traces are not committed. The full run records skipped unreadable
  files instead of requiring elevated privileges.

Remaining gap:

- There is still no fresh-clone or clean-install smoke that a community
  developer could rerun end-to-end with public setup docs. R160 is a bounded
  local artifact check, not a community adoption result. It also does not prove
  public-release readiness of the local `.agentsight` reports or full pre/post
  write-set containment. This is not a core scientific result, but it is
  important for turning the research prototype into a credible open-source
  project.

## Claim Ledger Snapshot

| ID | Claim | Current Status | Evidence Needed For OSDI |
|----|-------|----------------|--------------------------|
| C1 | AgentFlame can generate semantic folded stacks and dashboards over real local agent histories. | supported | verifier for full run and reproducibility script |
| C2 | Local one-word LLM tagging is feasible for session/prompt/LLM-call contexts. | supported for local 0.6B-/1B-/3B-class syntax/latency; partial for adequacy | human adequacy labels; controlled same-family scaling only if claimed |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic and flat summaries. | supported as mechanism | stronger examples and task benchmark |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | supported for fixed command-mode suite; partial broadly and partial for target-specific network workloads | cross-repo/full-history exact integration, target-specific network workloads, broader agent coverage, and user-task outcomes |
| C5 | Developers answer debugging/audit questions better with semantic effect flamegraphs. | unsupported; R142 packet/scorer/preregistration and R187 launch package exist | user/task benchmark responses with valid response contract passing the Holm-corrected paper-scale C5 gate |
| C6 | One-word tags are stable and adequate enough for navigation. | partial; R180 syntax/stability exists, R124 scorer/join protocol exists, labels are empty | human adequacy labels with thresholds |
| C7 | The approach is practical as an open-source developer tool. | partial | one-command install/run, runtime/cost, docs, artifact hygiene |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Full-history run over real local sessions, folded outputs, verifier coverage, no raw-trace commit | B1, B7 | Tagger/report cannot complete without manual trace editing, raw trace leaks into committed artifacts, or folded totals do not match reports | "AgentFlame generated semantic folded-stack artifacts for this repository's local histories." |
| C2 | Local llama.cpp annotation validity, latency, stability, cache behavior, and explicit adequacy boundary | B1, B5 | Small models frequently emit invalid tags, unstable tags break navigation, or human adequacy labels reject tags | "Local models can produce syntactically valid one-word navigation tags on this workload; adequacy is bounded by R124." |
| C3 | Same observations projected into semantic and nonsemantic baselines with total-weight equality and mixed-bucket reduction | B2, B6 | Removing semantic frames does not increase mixing, or prompt/session axes fail to isolate any real system-effect buckets | "Semantic frames partition system-effect buckets that traditional summaries merge in this repository." |
| C4 | Live AgentSight lineage with negative controls, process ancestry, file/network effects, and scoped precision/recall | B3 | In-scope recall below threshold, negative controls join, target-specific network rows remain absent for a network claim, or redaction/path checks fail | "Exact lineage is supported for the fixed command-mode suite; broad and target-specific network claims remain partial." |
| C5 | Preregistered developer task benchmark against named baselines with accuracy/time/false-positive/confidence outcomes | B4 | Semantic view does not improve accuracy or time, increases false positives, fails response contract, or only pilot-scale evidence exists | "The task benchmark is a protocol or pilot result only; no paper-scale user-utility claim." |
| C6 | Two independent human label sheets plus adjudication and scorer thresholds over R122/R124 fragments | B5 | Adequacy below threshold, high generic/misleading rate, low agreement without adjudication, or only LLM/subagent labels exist | "Tags are lossy navigation hints with measured syntax/stability; adequacy remains unsupported." |
| C7 | Clean one-command public workflow, fixed-input cache behavior, write-set/report containment, and external usability evidence | B7 | Fresh clone fails, run requires internal state, raw traces leak, runtime/cost is unacceptable, or external users cannot reproduce outputs | "The artifact path is bounded-local only, not community-ready." |

## System-Under-Test Model

- Components: `agentflame` Rust CLI, `normalize-chat-sessions` parser,
  llama.cpp-compatible local tagger, tag cache, folded-stack generator, SVG/HTML
  report generator, AgentSight record/export lineage artifacts, and verification
  scripts under `docs/visexp`.
- Durable state: local agent histories under user-controlled trace roots,
  generated private reports under `.agentsight/agentflame/*`, committed redacted
  summaries under `docs/visexp/out`, R124/R142 human-input templates, and
  experiment trackers/plans.
- Trust boundaries: LLM labels are untrusted navigation hints; file/process/
  network effects must come from parser or AgentSight provenance; human C5/C6
  evidence must come from completed participant/labeler CSVs, not from LLM,
  subagent, author mock data, or placeholder rows.
- Failure boundaries: unreadable traces must be recorded as skipped, not read
  with elevated privileges; out-of-scope sibling/wrapper effects must remain
  orphaned; active-session drift must be isolated with fixed `--session-file`
  manifests for cache/usability measurements.
- Workloads: current local Codex/Claude histories for full-run mechanism
  evidence; R114/R182 live Codex command-mode suites for exact-lineage evidence;
  R122/R124 redacted fragments for tag adequacy; R142/R151 blinded task packets
  for developer utility.
- Observability: folded stack totals, tag contract counters, cache/latency
  counters, lineage precision/recall, negative-control joins, task response
  accuracy/time/false positives/confidence, and artifact hygiene checks.
- Assumptions: committed outputs must be redacted; local `.agentsight` reports
  remain private unless a separate public sanitization path is verified; current
  C5/C6 claims stay unsupported until R184's human-evidence gate clears.

## Experiment Matrix

| Block | RQ | Experiment | Baselines/Variants | Metrics | Oracle | Priority |
|-------|----|------------|--------------------|---------|--------|----------|
| B1 | RQ1 | Full local-session characterization | 3B local llama.cpp, cache on/off where feasible | sessions, tags, invalids, runtime, cache hit rate | tag grammar checker and complete report | done, must repeat after changes |
| B2 | RQ2 | Semantic partitioning audit | semantic, nonsemantic, flat process/effect summary | mixed buckets, mixed weight, entropy, examples | deterministic stack comparison | done |
| B3 | RQ3 | Live exact AgentSight lineage | agent-native proxy vs exact effect stream plus negative controls | recall, precision, orphan rate, path/domain specificity | lineage checker with false-positive controls | fixed command-mode suite passed; record-mode network tracing smoke is partial because target-specific network rows are absent |
| B4 | RQ4 | Developer task benchmark | trace tree, event-count proxy, flat summary, nonsemantic stack, semantic stack; optional true span-duration baseline if reconstructed from timestamps | time, accuracy, false positives, confidence | hidden answer key plus frozen preregistration | packet scaffold, baseline naming, preregistration, and R187 launch package done; participant responses missing |
| B5 | RQ5 | Small-model and tag-stability benchmark | local 0.6B-/1B-/3B-class models, optional larger reference | latency, invalid rate, identical-input stability, adequacy | repeated run + human labels | syntax/stability done by R180; adequacy labels missing |
| B6 | RQ2 | Ablations | no semantic, session-only, prompt-only, prompt+LLM-call, full | information gain, stack explosion; noisy-tag burden and B4 task accuracy/time deferred | same observations, total-weight equality, report/folded cross-checks | done for C3 mechanism; C6/B4 deferred |
| B7 | RQ6 | Open-source usability smoke | fresh clone, install, run, view dashboard | setup time, commands, failure modes | artifact checklist | should |

## Baseline Fairness

- Span-duration flamegraph baseline should be represented by an OpenTelemetry
  trace flamegraph or faithful local reconstruction: bars/spans ordered by
  timing, width by duration, no semantic inheritance into file/network effects.
- The existing R142 packet uses `event-count-proxy`, not `span-duration`,
  because its width basis is event weight or task-level proxy counts rather than
  reconstructed span duration.
- Trace tree baseline should show the same session/tool/LLM-call sequence but no
  cross-session folded aggregation.
- Flat summary baseline should show process/effect/path/domain counts without
  session or prompt tags.
- Nonsemantic folded baseline should preserve stack aggregation but remove
  session/prompt frames. This isolates the contribution of semantic frames from
  flamegraph folding itself.

## Run Order And Tracker Handoff

| Run ID | Stage | Purpose | Config | Seed/reps | Decision gate | Cost | Risk |
|--------|-------|---------|--------|-----------|---------------|------|------|
| R186 | plan-review | Independent OSDI review of revised RQ/experiment plan | read-only review over `RESEARCH_PLAN`, `FOLLOWUP_PLAN`, `STATE`, R184/R185, and paper RQs | one subagent review | review says plan is executable and names remaining blockers; otherwise revise plan before new claims | done | confirmed Level 3 only |
| R187 | launch | Package frozen R142 pilot materials for collection | `docs/visexp/out/user-task-pilot-r142/launch` generated from frozen bundle/assignments/templates | deterministic over 70 assignments | five P01-P05 packets, blank response CSV, no answer key, no forbidden keys, `c5_supported=false` | done | launch-only, cannot count as C5 |
| R142-pilot | execute | Five-participant developer pilot using frozen packets | completed copy of `docs/visexp/out/user-task-pilot-r142/launch/responses/user-task-response-template-r142-pilot.csv`, scored into `docs/visexp/out/user-task-pilot-r142` | P01-P05 counterbalanced assignments | response contract valid, no leakage, interpretable task-level deltas; still not paper-scale C5 unless gate says so | human time | cannot be synthesized by LLM/subagent |
| R124-labels | execute | Independent human tag adequacy labels | two completed blinded sheets plus adjudication, joined/scored by R124 scripts | 300 rows x 2 labelers | `adequacy_supported=true`, agreement/adjudication recorded; otherwise C6 wording narrows | human time | label noise may falsify adequacy |
| R151 | execute | Paper-scale developer utility run | 12-20 developers or deliberately narrowed expert population | preregistered participant/task/order blocking | Holm-corrected C5 gate passes and false positives stay within threshold | high | likely reviewer-critical |
| R190 | supplement | Target-specific network lineage hardening | expanded loopback/HTTP child-process workloads under `agentsight record --trace-net` | fixed manifest plus negative controls | target-specific network rows observed and joined, 0 joined negatives | medium | may require collector changes |
| R200 | artifact | Fresh-clone/community smoke | documented install/run path on fixed public-safe inputs | clean + cached rerun | one-command output, no raw trace leak, bounded write set | medium | lower priority than C5/C6 |

Tracker handoff:

- Update path: `docs/visexp/EXPERIMENT_TRACKER.md`.
- Result path convention: committed redacted summaries under `docs/visexp/out`;
  private full reports remain under `.agentsight/agentflame/*`.
- Required tracker columns: Run ID, Claim, Block, Purpose, Command/config,
  Commit, Machine, Seed/reps, Oracle, Decision gate, Result path, Status.
- R186 plan review is recorded in `docs/visexp/out/osdi-plan-review-r186.md`.
- R187 launch package is recorded in
  `docs/visexp/out/user-task-pilot-r142/launch/manifest.json`.
- Next rows to execute: R142-pilot collection first, then R124-labels in
  parallel or immediately after.

## Figure Plan

1. Attribution Model: `sessionTag/promptTag/llmcall` generated by small LLM;
   `tool -> process* -> effect` inherited deterministically.
2. Semantic Flamegraph: same `cargo`, `git`, `rg`, or `docker` effects split by
   `refactor`, `review`, `design`, `research`, and `analyze`.
3. Baseline Failure: span-duration trace shows order/duration; flat process
   summary shows heavy commands; neither answers which semantic task caused the
   repeated side effects.
4. Evaluation Table: full-run scale, tag validity, mixing, live lineage join
   coverage, user-task results.

## Next Gate

Current OSDI review posture: weak reject / promising measurement-tooling idea.
R184 reports `not_weak_accept`; R185 says the plan is still Level 3 until real
C5/C6 human evidence exists.

The canonical follow-up artifact is `docs/visexp/FOLLOWUP_PLAN.md`. It freezes
the weak-accept gate as four requirements: G1 full-history semantic
characterization, G2 broader live exact lineage, G3 small-model/tag adequacy,
and G4 developer task utility.

The fastest route to weak accept is now a gate-ordered plan:

1. R186 read-only OSDI plan review and R187 launch packaging are complete for
   this revision. If the plan or RQ wording changes again, rerun the same
   subagent gate before strengthening claims.
2. Run a real R142 five-participant developer pilot using the R187 P01-P05
   packets, the frozen preregistration, corrected answer keys, blinded
   condition packets, and a completed copy of the blank launch response CSV.
   The pilot validates packet wording and the response contract; it must stay
   labeled as pilot evidence unless the scorer's paper-scale gate passes.
3. Collect and adjudicate human adequacy labels using the blinded R124 labeler
   sheet, join frozen sheets with `docs/visexp/r124_join_blinded_labels.py`,
   and score `docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv`. The
   packet must receive two independent human labels per row plus adjudication
   for disagreements; LLM or subagent labels can only review the protocol and
   cannot count as C6 evidence.
4. If the pilot passes, run R151 with 12-20 developers or a deliberately
   narrowed expert-study population. C5 can be claimed only if the
   Holm-corrected participant/task/order fixed-effect gate passes and false
   positives do not increase beyond the preregistered threshold.
5. Run target-specific network lineage hardening only for claims that extend C4
   beyond the fixed command-mode suite; do not let C4 hardening substitute for
   C5/C6.
6. Turn the bounded R160 artifact smoke into a fresh-clone/clean-install
   community workflow after the core claims stop moving.
7. Rewrite the paper around "semantic attribution of agent system effects," not
   around "agent flamegraph UI," and keep C5/C6 limitations explicit unless the
   new results pass their gates.

No-go rule: if R124 remains `human_labels_empty` or R142/R151 remains
`participant_results_empty`, the paper should stay at "mechanism plus
measurement artifact." It should not claim tag adequacy, developer utility, or
community-tool readiness.
