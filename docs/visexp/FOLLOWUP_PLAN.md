# AgentFlame OSDI Follow-Up Plan

Last updated: 2026-06-15
Stage at update: supplement / experiment-design
Source/command: auto-research-orchestrator + osdi-experiment-design gate review over `docs/visexp`
Completeness: partial

## Positioning

The paper should be framed as:

> AgentFlame: Semantic Effect Profiling for AI Coding Agents.

The contribution is not a new trace UI and not "flamegraphs for agents." The
claim is that user-level semantic intent, produced by a local small LLM, can be
deterministically joined with tool/process/effect provenance in fixed
command-mode runs, then aggregated as folded stacks:

```text
sessionTag;promptTag;llmcall/tool;process*;effect
```

This joins three things that existing views usually keep separate:

1. semantic control plane: what the user asked the agent to do;
2. system provenance plane: what commands, processes, files, and network targets
   were actually touched;
3. aggregation plane: which repeated/heavy effects are semantically the same or
   different across sessions.

## Existing Practice Boundary

Span-duration agent flamegraphs already exist and must be treated as a
baseline, not as the paper's novelty. SigNoz's Inkeep case study explicitly
shows a "Flamegraph for Debugging" where each horizontal bar is a span and width
is proportional to duration; it is used for sequential/parallel execution,
error cascades, tool overhead, and sub-agent boundaries. Agent-tracing systems
such as LangSmith, Langfuse, Phoenix/OpenInference, OpenSearch Agent Traces, and
Datadog also expose trace trees, timelines, DAGs, or span flamegraph-style
views over LLM/tool/agent spans.

Concrete existing examples to treat as related work and baselines:

- SigNoz/Inkeep: span-duration flamegraph for multi-agent debugging.
- OpenSearch Agent Traces: agent graph, trace tree, and Gantt-style timeline.
- Datadog Trace View: waterfall and flamegraph visualizations over spans.
- LangSmith/Langfuse/Phoenix/OpenInference: agent/LLM/tool tracing and
  OpenTelemetry/OpenInference-style span conventions.
- Agentrial: trajectory flame graphs across repeated agent trials.

See `docs/visexp/RELATED_WORK_NOTES.md` for URLs and baseline implications.

Therefore AgentFlame must not claim "we invented agent flamegraphs." The
claimable delta is:

1. one-word semantic frames assigned to real Codex/Claude session, prompt, and
   LLM-call contexts by a local model;
2. exact local system-effect lineage from prompt/tool intent through shell and
   child processes to process/file effects in the fixed command-mode suite;
3. folded-stack aggregation across sessions so repeated heavy or divergent
   effects can be grouped by semantic task, not only by span name or duration.

## Current OSDI Gate

Current reviewer posture: promising systems tooling, not OSDI weak accept.

The current evidence supports C1-C3 as mechanism/characterization claims and C4
for a fixed 20-task command-mode suite. It does not yet support broad
cross-repo/full-history exact provenance, user utility, or tag adequacy.

Weak accept requires all four gates below:

| Gate | Claim(s) | Required evidence | Current state | Status |
|------|----------|-------------------|---------------|--------|
| G1 full-history semantic characterization | C1-C3 | all repo-related readable sessions annotated by real llama.cpp model, with redacted output and baseline-mixing analysis | 205 sessions, 29,302 llama.cpp HTTP calls, 0 final tag failures, 90.219%/90.770% mixed baseline weights | pass |
| G2 live exact semantic-effect lineage | C4 | broader live `agentsight record` suite, recall/precision table, join/orphan table, child-depth and path specificity, negative controls | R114 fixed 20-task suite: 20/20 targets completed, 20/20 tasks observed negative controls, 1273/1273 in-scope effects joined, 100.0% precision/recall, 3170 observed negative-control effects with 0 joined, child-depth/path/redaction tables generated | pass for fixed suite |
| G3 small-model and tag adequacy | C2,C6 | 0.6B/1B/3B llama.cpp benchmark, repeated-run stability, human adequacy labels | 3B syntax/full-run evidence plus R123 real redacted stability: 900/900 valid tags, 285/300 exact-stable fragments, p95 31 ms; no local 0.6B/1B weights; human adequacy still missing | partial |
| G4 developer task utility | C5 | head-to-head task benchmark against trace tree, true span-duration flamegraph or explicitly named event-count proxy, flat summary, nonsemantic stack, semantic stack | R142-packet generated 14 tasks, 8 primary utility tasks, 6 limitation/comprehension tasks, 5 conditions, 70 leak-checked blinded packets, P01-P05 counterbalanced assignments, hidden answer key, manifests, and per-task same-event-slice `slice_id` checks. The former span-like event-weight condition is now explicitly named `event-count-proxy`, so the packet no longer claims to be a span-duration baseline. R142-scoring adds response-contract checks, task-level diagnostic deltas, Holm-corrected participant/task/order fixed-effect paper gates, false-positive guardrails, and C5 support/pilot gates. R142-preregistration is now frozen before collection and records source hashes, task roles, response schema, exclusions, conditions, and success thresholds; no participants | missing outcome data |

## Weak-Accept Execution Protocol

The next work should not add another visualization polish pass unless it
directly unblocks C5 or C6. OSDI weak accept requires outcome evidence, so the
execution order is:

1. **R124-labels for C6.** Use
   `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv` to collect two
   independent human labels for every row, join the frozen sheets with
   `docs/visexp/r124_join_blinded_labels.py`, adjudicate disagreements into
   `docs/visexp/out/tag-adequacy-adjudication-template-r124.csv`, and rerun
   `score_tag_adequacy.py` on the joined packet. Subagents or LLMs may review
   the rubric and spot-check leakage, but their labels do not count as human
   adequacy evidence.
2. **R142-pilot for C5.** The current packet has been rescoped to use an
   explicitly named `event-count-proxy` baseline rather than a misleading
   span-duration condition. The C5 analysis preregistration is now frozen in
   `docs/visexp/out/user-task-preregistration-r142.json`; run the P01-P05
   counterbalanced packet with real developers or scoped expert
   participants. The pilot can validate procedure and task wording, but it must
   stay labeled as pilot evidence unless the paper-scale C5 gate passes.
3. **R151 paper run for C5.** Only after the pilot response contract passes and
   the C5 analysis model is preregistered, collect 12-20 participant response
   rows or explicitly narrow to a scoped expert study. The scorer's
   Holm-corrected participant/task/order fixed-effect gate decides whether any
   user-utility claim is allowed.
4. **C4/RQ6 replication and artifact polish.** Run cross-repo or clean-install
   work only after C5/C6 are no longer empty. These runs strengthen scope and
   artifact positioning but cannot substitute for adequacy or utility evidence.

Hard evidence boundaries:

- If R124 remains `human_labels_empty`, C6 can only claim syntax/stability.
- If R142/R151 remains `participant_results_empty`, C5 must remain
  unsupported.
- If the R142 pilot fails the response contract, revise packets/scoring before
  recruiting for R151.
- If R151 does not meet the accuracy/time/false-positive gate, the paper should
  narrow to "mechanism plus expert case studies" rather than claim developer
  utility.

### R124 Label Collection Contract

The label packet already contains 300 rows: 100 session fragments, 100 prompt
fragments, and 100 LLM-call fragments. The labeler-facing sheet must be blinded:
it contains only `row_id`, fragment level, redacted preview/context, candidate
tag, rubric text, and label fields. Labelers must not see raw trace files,
model identity, model size, stability metadata, modal counts, generation
timestamps, benchmark latency, or downstream result columns. Those hidden
columns can be joined back only after labels are frozen. Each row requires:

- `labeler_1`: `adequate`, `generic_noisy`, or `misleading`;
- `labeler_2`: an independent label from a second labeler;
- `adjudicated_label`: required only when the two labelers disagree;
- `notes`: optional short reason, without adding raw prompt text.

R124 can support a narrowed C6 claim only if:

- candidate tags cover 300/300 rows;
- both labelers label 300/300 rows;
- every disagreement is adjudicated;
- `adequate_share_pct >= 80.0`;
- `generic_noisy_share_pct <= 20.0`;
- `misleading_share_pct <= 5.0`;
- Cohen's kappa is `>= 0.6`, or the paper explicitly narrows the adequacy
  wording and reports the disagreement pattern.

Protocol command after both independent sheets are frozen:

```bash
python3 docs/visexp/r124_join_blinded_labels.py \
  --labeler-1 path/to/labeler1.csv \
  --labeler-2 path/to/labeler2.csv \
  --adjudication path/to/adjudication.csv
python3 docs/visexp/score_tag_adequacy.py \
  --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv \
  --out-json docs/visexp/out/tag-adequacy-results-r124.json \
  --out-csv docs/visexp/out/tag-adequacy-results-r124.csv \
  --out-md docs/visexp/out/tag-adequacy-results-r124.md
```

The default R124 join manifest is intentionally protocol-only:
`ready_for_independent_label_collection`, 300 source rows, 0 labeler rows, no
joined label output, and an empty adjudication template.

### R142/R151 Participant Contract

Do not collect R142 pilot or R151 paper responses until the analysis contract is
frozen and the baseline name remains honest:

- The `span-duration` condition must be a real trace/timeline view: spans
  ordered by timestamp, widths derived from measured duration, and no semantic
  inheritance into file/network effects. If trace timestamps are unavailable,
  the condition must be renamed `event-count-proxy`, and C5/RQ4/paper text must
  stop calling it a span-duration flamegraph baseline.
- Existing R142 packet excerpts with `width_basis=event_weight_same_slice` and
  "duration unavailable" notes are useful as an event-count proxy only; they are
  not a fair span-duration baseline.
- The current R142 packet satisfies this naming boundary by exposing the
  event-weight view as `event-count-proxy`. A future true duration baseline
  requires regenerated packet artifacts and updated scoring thresholds.
- The C5 analysis must be preregistered before pilot collection if possible, and
  before R151 at the latest. Freeze the response unit, primary task subset,
  condition comparisons, exclusion rules, participant/task/order blocking
  factors, condition rotation for 12-20 participants, and Holm correction
  family.

The C5 scorer requires real response rows with these fields:
`participant_id`, `order_index`, `packet_id`, `task_id`, `condition`,
`response_json`, `task_time_seconds`, `confidence`, and `notes`.

The pilot should use the existing P01-P05 assignment template exactly once per
participant. The paper run should use 12-20 participants or a clearly scoped
expert-study limitation. The scorer should reject duplicate, partial, or
nonnumeric response files before any claim analysis.

Paper-scale C5 support requires:

- at least 12 participants;
- at least 8 primary semantic-vs-baseline task pairs per baseline;
- at least a 10 percentage-point participant/task/order fixed-effect accuracy
  gain or 20% median task-time reduction for `semantic-stack`;
- Holm-corrected blocked-permutation `p <= 0.05` over the preregistered
  participant/task/order design;
- no more than a 5 percentage-point false-positive increase.

### Subagent Review Gate

Before running R151 or upgrading any paper claim, run a read-only OSDI review
subagent over `FOLLOWUP_PLAN.md`, `CLAIM_VERDICT.md`, the relevant result JSON,
and the paper evaluation section. The review must answer:

- Does every supported claim have a result path and oracle?
- Are C5/C6 still correctly blocked if labels/responses are empty?
- Are baselines named and fair?
- Are pilot-scale results labeled as pilot, not paper-scale evidence?
- Are any privacy boundaries violated by committed artifacts?

## Revised Research Questions

### RQ1: Can local LLM tagging cover real agent histories?

Can AgentFlame use a real local llama.cpp server to assign one-word tags to all
session, prompt, and LLM-call contexts in this repository's readable Codex and
Claude traces without fallback labels or malformed outputs?

Primary oracle: `agentflame.json` and `tags.json` report valid tags, complete
counts, cache behavior, model provenance, and explicit skipped/unreadable
inputs.

Falsifier: final tag failures, invalid tags after retry, missing LLM-call tags,
or silent skipping of readable sessions.

### RQ2: Do semantic frames expose information that nonsemantic tools merge?

Do session and prompt frames separate repeated system effects that would be
merged by ordinary span traces, flat process/file/network summaries, or folded
stacks without semantic frames? LLM-call tags are evaluated separately for
token/accounting views, not as system-effect attribution frames.

Primary oracle: mixed-bucket analysis from the same underlying observations.

Falsifier: mixed weight is low, top examples are not actionable, or ablations
show the semantic axes add only visual noise.

### RQ3: Can live AgentSight traces preserve exact semantic-effect lineage?

Can each in-scope process/file effect row observed in live agent runs inherit
the right `sessionTag/promptTag/tool` ancestry through
`tool_call -> shell -> process* -> effect` rather than through post-hoc text
guessing?

Primary oracle: lineage checker over exported AgentSight snapshots, with
joined/orphan counts, false-positive counts, join method, child depth,
path/domain specificity, negative controls, and redaction status.

Falsifier: high orphan rate, broad root-pid over-attribution, non-agent
background work incorrectly attributed to an agent tool, missing child-process
depth, or path/domain effects that cannot be traced to the agent-run tool
envelope.

### RQ4: Do semantic effect flamegraphs improve developer forensics?

Do developers answer questions such as "which task caused repeated tests?",
"which prompt introduced repo-outside reads?", or "which semantic region caused
network calls?" more accurately or faster with semantic effect flamegraphs than
with trace trees, span-duration flamegraphs, flat summaries, or nonsemantic
folded stacks?

Primary oracle: preregistered answer-key task benchmark with accuracy, time,
confidence, and false-positive metrics.

Falsifier: no accuracy/time/confidence improvement, or semantic views introduce
more false positives than baselines.

### RQ5: Are one-word tags stable and adequate as navigation frames?

Are 0.6B/1B/3B local models fast and stable enough to produce useful one-word
labels for session/prompt/LLM-call navigation?

Primary oracle: repeated model benchmark plus human adequacy labels.

Falsifier: high invalid/generic/noisy rate, unstable labels for identical
fragments, or latency/cost too high for local developer use.

## Must-Run Experiment Blocks

### B3x: Broader Live Exact-Lineage Suite

- Claim tested: C4.
- Workload: 20 live agent tasks under `agentsight record`, not only read-only
  documentation queries. Include read-only analysis, code edit, test/debug,
  dependency inspection, and failure/retry tasks. Use disposable repo copies for
  write tasks.
- Baselines/variants: agent-native proxy stacks, exact AgentSight effect stacks,
  session-scoped root-pid propagation enabled, and negative controls where
  unrelated processes run concurrently but must not inherit the agent root.
- Negative controls: background shell commands in the same repository,
  background commands in a sibling repository, and same-time-window sibling
  processes that share the collector but not the agent process family.
- Metrics: raw effects, true positives, false positives, false negatives,
  precision, recall, orphan effects, join method, child depth distribution, top
  paths/domains, repo-inside/outside split, redaction failures.
- Oracle: each in-scope effect must join to exactly one agent-run tool envelope
  by process-family or session-scoped root-pid lineage; negative-control effects
  must remain unattributed. Effects outside the task time window, outside the
  process family/root hint, or generated by declared background controls are
  out of scope for recall and in scope for false-positive checks.
- Success criterion for paper: at least 20 tasks, >=95% in-scope recall, >=98%
  precision, 0 negative-control over-attributions, 0 redaction failures, and at
  least three concrete cases where exact lineage reveals path/process
  detail that agent-native history alone lacks.
- Current evidence: R114 retargets the record envelope to the real `codex`
  child process with `--agent-comm codex`, handles missing related-root process
  nodes by anchoring on captured children, and joins 1273/1273 in-scope effects
  across 20 real tasks. It leaves wrapper/sibling/out-of-scope effects orphaned
  and attributes 0/3170 observed negative-control effects; all 20 tasks observe
  negative-control effects.
- Failure interpretation: if broader replication fails, C4 remains scoped to
  command-mode capture-time suites and cannot be claimed for arbitrary histories.
- Result path: `.agentsight/agentflame/exact-lineage-r114/summary.json` plus
  committed redacted summary under `docs/visexp/out/live-record-r114.*`.

### B5x: Small-Model Cost, Stability, And Adequacy

- Claim tested: C2, C6.
- Workload: 300 fragments sampled from the full run: 100 session summaries, 100
  prompt texts, 100 LLM-call previews. Store only hashes, redacted previews, and
  labels in committed artifacts.
- Models: at minimum 3B and every locally available 1B/0.6B-class GGUF; R121
  found only one real 3B model locally, while 0.6B/1B were absent, so any paper
  claim about those size classes requires downloading or adding real weights.
- Command skeleton:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench \
  --llama-server /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  --runs 3 \
  --out .agentsight/agentflame/model-benchmarks.json \
  --model 3b=/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

- Metrics: load time, per-tag latency p50/p95, invalid rate, retry rate,
  exact-stability rate across identical repeats, generic/noisy tag rate, human
  adequacy.
- Adequacy rubric: two labelers score each tag as adequate, generic/noisy, or
  misleading. Adequate means the one-word label preserves the main user/task
  intent well enough to navigate a flamegraph bucket; generic/noisy means it is
  grammatical but too broad, such as `task` or `work`; misleading means it points
  to the wrong action or object.
- Oracle: grammar checker plus blinded human labels over the same fragments;
  report inter-label agreement and adjudicate disagreements before claim
  wording.
- Success criterion for paper: one local model has 0 final invalid tags, p95
  per-fragment latency under 500 ms after model load, >=80% exact stability over
  identical repeats, >=80% adequate labels, <=20% generic/noisy labels, and
  inter-label agreement of Cohen's kappa >=0.6 or an explicitly weaker
  limitation statement.
- Current evidence: R121 fixed the identical-fragment benchmark path. R122 then
  sampled 300 real redacted fragments from 294 parsed local sessions: 100
  session summaries, 100 prompt fragments, and 100 LLM-call fragments. R123 ran
  those fragments through the available 3B llama.cpp server with 3 identical
  repeats each and produced 900/900 valid tags, p95 request latency 31 ms after
  load, and 285/300 exact-stable fragments (95.000%).
- Privacy guard: `agentflame bench` now omits fragment previews by default; R121
  used `--include-fragment-previews` only because the three smoke fragments are
  synthetic.
- Remaining gap: paper-level C6 still needs human adequacy labels over the R122
  packet and any added 0.6B/1B real model weights if the paper wants to claim
  smaller size classes.
- Result path: `.agentsight/agentflame/model-benchmarks.json`,
  `docs/visexp/out/model-benchmarks-r123.json`, and
  `docs/visexp/out/tag-adequacy-label-packet-r122.csv`.

### B6x: Semantic Axis Ablation

- Claim tested: C3. C6 visual-noise burden and B4 task accuracy/time remain
  deferred.
- Workload: the same 205-session full run and the B4 task-question set.
- Variants: no semantic frames, session-only, prompt-only, prompt+LLM-call,
  full session+prompt+LLM-call.
- Metrics: mixed bucket weight, non-dominant residual mixed weight, unique stack
  growth, max stack reuse. Visually noisy tags and B4 task accuracy/time are
  deferred to R124/B4.
- Oracle: each variant must be generated from the same folded observations and
  checked for identical total weight, matching `agentflame.json` totals, and
  exact counter equality against already generated folded projections where
  available.
- Success criterion for paper: prompt/session frames materially reduce baseline
  mixing while keeping stack growth manageable; LLM-call frames help token views
  or are scoped out from system-effect claims.
- Current evidence: R131 ran over the existing full folded artifacts and
  preserved all system/token totals. It records that `agentflame.json` totals
  match folded inputs and that generated nonsemantic/session/prompt folded files
  exactly match the projections. System no-semantic projection mixed 90.219% of
  full semantic bucket weight with 44.639% residual; session-only left 84.180%
  bucket / 34.138% residual; prompt-only left 37.687% bucket / 7.526% residual.
  Full session+prompt left 0.000% by construction. Token prompt+LLM-call still
  mixed 95.765% of full semantic token bucket weight but only 0.027% residual,
  so the paper should scope LLM-call tags to token navigation rather than
  system-effect attribution.
- Result path: `.agentsight/agentflame/ablations-r131/summary.json`,
  `docs/visexp/out/semantic-ablation-r131.json`.

### B4x: Developer Forensic Task Benchmark

- Claim tested: C5.
- Workload: 12-20 questions generated from B1/B3x evidence. Examples:
  - Which semantic task caused the most repeated `cargo test` executions?
  - Which prompt region produced repo-outside file reads?
  - Which task caused network calls, and to which domains?
  - Which repeated failures are concentrated in one semantic region?
- Conditions: raw trace tree, `event-count-proxy`, flat process/effect summary,
  nonsemantic folded stack, semantic effect flamegraph. If a future
  span-duration baseline is reconstructed from timestamps, it must replace or
  supplement `event-count-proxy` with a separate preregistered condition.
- Design: within-subject, Latin-square/counterbalanced order, one condition per
  question per participant, blinded scoring, participants with recent coding
  agent experience or a scoped expert-study limitation.
- Metrics: exact answer accuracy, task time, false positives, confidence, NASA
  TLX-lite or simple workload rating.
- Oracle: hidden answer key computed mechanically from B3x exact lineage and
  manually checked.
- Statistical plan: preregister a response-level analysis before collection.
  Primary tests use participant/task/order fixed effects and a blocked
  permutation family matching the assignment design; Holm correction applies
  across semantic-stack-versus-baseline primary comparisons.
- Success criterion for paper: semantic view improves exact answer accuracy by
  >=10 percentage points or median task time by >=20% on core questions, with no
  >5 percentage-point increase in false positives. If only experts benefit or
  thresholds fail, wording must narrow to case-study/expert forensic workflow.
- Current evidence: R142-packet makes the pilot packet executable but does not
  score utility. It generates 14 tasks from R114/R123/R131/full-run artifacts,
  split into 8 primary utility tasks and 6 limitation/comprehension tasks; five
  conditions (`trace-tree`, `event-count-proxy`, `flat-summary`,
  `nonsemantic-stack`, `semantic-stack`); 70 blinded packets with recursive
  forbidden-key leakage checks; a P01-P05 counterbalanced assignment template;
  a hidden answer key; script/output manifests; and a scorer output marked
  `participant_results_empty`. For baseline
  fairness, every task's five condition excerpts now share exactly one
  `slice_id`, so trace/event-proxy/flat/nonsemantic/semantic packets are derived
  from the same underlying evidence slice. The event-weight view is explicitly
  named `event-count-proxy`, so it is not presented as a fair span-duration
  baseline. R142-scoring now validates
  response assignment consistency, keeps task-level semantic-vs-baseline deltas
  as diagnostics, and gates paper-scale C5 with Holm-corrected
  participant/task/order fixed-effect blocked permutation tests. C5 remains
  unsupported until the preregistration is frozen and participant responses are
  collected and scored.
- Result path: `docs/visexp/out/user-task-results.json`.

## Tracker Rows To Add Next

| Run ID | Claim | Block | Purpose | Command/config | Seed/reps | Oracle | Decision gate | Result path | Status |
|--------|-------|-------|---------|----------------|-----------|--------|---------------|-------------|--------|
| R114 | C4 | B3x | Broader live exact-lineage task suite over 20 real agent tasks. | `python3 docs/visexp/r114_live_record_suite.py --out docs/visexp/out --timeout 240`; then `python3 docs/visexp/r114_lineage_analysis.py --result docs/visexp/out/live-record-r114.json --out docs/visexp/out` | 20 tasks, fixed task manifest | lineage checker + precision/recall + redaction/path analyzer | passed: 20/20 tasks observed negative controls, 100.0% precision, 100.0% recall, 0/3170 negative-control joins, 0 redaction failures | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | done |
| R121 | C2,C6 | B5x | Real llama.cpp model benchmark. | `agentflame bench --runs 3 --model ...` using available GGUF models | 3 fixed fragments x 3 identical repeats | grammar/stability/latency checker | done for 3B smoke: 9/9 valid tags, 2/3 exact-stable fragments; no claims for missing size classes; adequacy labels required | `.agentsight/agentflame/model-benchmarks.json`, `docs/visexp/out/model-benchmarks-r121.json` | done |
| R122 | C6 | B5x | Redacted label packet. | create redacted label packet | 300 fragments | redaction scan + stratified counts | packet ready; labels still required | `docs/visexp/out/tag-adequacy-label-packet-r122.csv` | done/packet |
| R123 | C2,C6 | B5x | Real redacted fragment stability. | `agentflame bench --fragment-file .agentsight/agentflame/r122-real-fragments.txt --runs 3 --model ...` | 300 fragments x 3 repeats | grammar/stability/latency checker | done for 3B: 900/900 valid, 285/300 exact-stable, p95 31 ms; adequacy labels required | `.agentsight/agentflame/model-benchmarks-r123.json`, `docs/visexp/out/model-benchmarks-r123.json` | done |
| R124-scoring | C6 | B5x | Adequacy scorer and empty-result gate. | `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r122.csv ...`; then `python3 docs/visexp/evaluate_artifacts.py --out docs/visexp/out` | deterministic over 300 packet rows | candidate-tag coverage, empty/partial/scored status, adequacy/kappa thresholds | done as protocol only: current output is `human_labels_empty`, 300 candidate tags, 0 final labels, `adequacy_supported=false`; C6 remains partial | `docs/visexp/out/tag-adequacy-results-r124.json` | done/empty |
| R124-join | C6 | B5x | Blinded label join and adjudication protocol. | `python3 docs/visexp/r124_join_blinded_labels.py` | deterministic over 300 packet rows | source/blinded row match, hidden-field contract, no committed human labels, empty adjudication template | protocol passed: ready for independent label collection; does not support C6 until real labels are joined and scored | `docs/visexp/out/tag-adequacy-label-join-r124.json`, `docs/visexp/out/tag-adequacy-adjudication-template-r124.csv` | done/protocol |
| R124 | C6 | B5x | Human adequacy labeling over sampled fragments. | collect two independent completed copies of `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`; join them with `python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 ... --labeler-2 ... --adjudication ...`; score with `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv --out-json docs/visexp/out/tag-adequacy-results-r124.json --out-csv docs/visexp/out/tag-adequacy-results-r124.csv --out-md docs/visexp/out/tag-adequacy-results-r124.md` | 300 fragments, >=2 labelers | adequacy/generic/misleading rubric plus agreement/adjudication | scored gate has >=80% adequate, <=20% generic/noisy, <=5% misleading, kappa >=0.6 or limited claim | `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-results-r124.csv`, `docs/visexp/out/tag-adequacy-results-r124.md` | planned |
| R131 | C3 | B6x | Semantic-axis ablation. | `python3 docs/visexp/r131_semantic_ablation.py --input .agentsight/agentflame/latest --local-out .agentsight/agentflame/ablations-r131/summary.json --out-dir docs/visexp/out` | deterministic | total-weight equality + report/folded cross-checks + mixed/residual delta | passed for C3 mechanism: all totals preserved; generated folded files match projections; system prompt-only reduced mixed full semantic bucket weight from 90.219% to 37.687% and residual from 44.639% to 7.526%; C6/B4 deferred | `.agentsight/agentflame/ablations-r131/summary.json`, `docs/visexp/out/semantic-ablation-r131.json` | done for C3; C6/B4 deferred |
| R141-packet | C5 | B4x | Superseded deterministic user-task packet draft. | `python3 docs/visexp/user_task_benchmark.py ...` before same-slice enforcement | 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | leak check + assignment coverage + scorer status | superseded by R142 same-slice packet | `docs/visexp/out/user-task-benchmark.json` historical commit | superseded |
| R142-packet | C5 | B4x | Same-event-slice user-task packet and empty scorer check. | `python3 docs/visexp/user_task_benchmark.py --out docs/visexp/out --agentflame-dir .agentsight/agentflame/latest`; scorer over `user-task-response-template.csv` | 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | hidden answer key + leak-checked blinded packets + assignment coverage + per-task common `slice_id` + explicit `event-count-proxy` baseline naming + scorer status | packet ready for preregistered pilot collection; no C5 claim without participants | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-results.json` | done/packet |
| R142-scoring | C5 | B4x | Response-contract and paper-scale C5 scorer gate. | `python3 docs/visexp/score_user_task_results.py --responses docs/visexp/out/user-task-response-template.csv --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out` | deterministic empty-template check; real responses later | assignment/packet contract checks, diagnostic task-level deltas, Holm-corrected participant/task/order fixed-effect tests, false-positive guardrail, pilot/paper support gates | current output is `participant_results_empty`, `c5_supported=false`, `pilot_ready=false`; no C5 claim without participants | `docs/visexp/out/user-task-results.json` | done/empty |
| R142-preregistration | C5 | B4x | Frozen analysis contract before participant collection. | `python3 docs/visexp/r142_preregistration.py` | deterministic over current bundle, assignments, answer key, response template, and scorer constants | source-hash lock, condition/schema/threshold validation, event-count proxy boundary, exclusion rules | prereg gate passed as `frozen_before_collection`; still no outcome evidence | `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-preregistration-r142.md` | done/protocol |
| R142 | C5 | B4x | User-task pilot. | collect 5 developer participants using counterbalanced P01-P05 conditions; score with `python3 docs/visexp/score_user_task_results.py --responses <pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142` | 5 participants for complete condition coverage | answer key, timing data, false positives, confidence, response-contract checker | task protocol works before paper run; pilot is not paper-scale C5 support | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` | planned |
| R151 | C5 | B4x | User-task paper run. | 12-20 participants or scoped expert study | counterbalanced | accuracy/time/false-positive/confidence scorer | required for any user-utility claim | `docs/visexp/out/user-task-results.json` | planned |
| R160 | C7 | B7 | Bounded fixed-session open-source usability smoke. | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command against the same output dir; then `python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke-fixed --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json --out docs/visexp/out/artifact-usability-r160.json ...` | one clean run plus cached rerun over fixed inputs | expected files + runtime/cache summary + sanitized input manifest + clean/cached input equality + 76/76 cached rerun + no raw-trace git dirt + generated report path containment | bounded local artifact path is auditable without the internal harness; fresh-clone/community usefulness, public report sanitization, and full write-set containment remain open | `docs/visexp/out/artifact-usability-r160.json` | done/bounded |
| R170 | C1,C2,C3,C7 | B1/B5/B7 | Current full-history refresh. | seed R170 tag cache from `latest`, run AgentFlame over current repo sessions against local 3B llama.cpp server, summarize with `python3 docs/visexp/r170_full_history_refresh.py` | all discovered repo sessions under scan cap | AgentFlame ok + 0 tagger failures + folded totals match report + redacted committed summary | done as mechanism/artifact evidence: 325 sessions, 35,136 fresh llama.cpp tag calls, 0 failures; does not support C5/C6 | `docs/visexp/out/full-history-r170.json` | done/mechanism |
| R171 | C5,C6 | gate | Read-only subagent OSDI gate review. | inspect current plan/tracker/results/verdict/audit/followup/paper/gate outputs | one independent review | strict OSDI rubric | review says Level 3, not weak accept; R124-labels and R142/R151 remain the must-fix outcome artifacts | `docs/visexp/out/osdi-gate-review-r171.md` | done/review |

## Paper Revision Rule

Until G3-G4 pass and broader C4 replication exists, the paper may say:

- supported: AgentFlame can annotate this repo's real agent histories with a
  real local llama.cpp model and expose semantic/nonsemantic mixing;
- supported for fixed suite: command-mode live AgentSight provenance joins all
  scoped in-scope effects in a 20-task suite and rejects per-task negative
  controls;
- unsupported: developer utility and semantic adequacy.

It may not say:

- "comprehensive" live exact provenance;
- "improves developer productivity";
- "0.6B is enough";
- "semantic tags are correct."

## Immediate Next Action

Move to G3/G4 next, but do not collect responses with the current protocol.
R114/B3x now gives the paper concrete exact-lineage evidence that
span-duration traces do not provide, but OSDI weak accept still needs evidence
that the semantic labels are adequate and that developers actually answer
forensic questions better with the visualization.

1. collect/adjudicate human adequacy labels using the blinded R124 labeler
   sheet, then rerun `score_tag_adequacy.py`;
2. run the R142 developer task pilot using the frozen preregistration and the
   corrected trace tree, event-count proxy, flat summary, nonsemantic stack, and
   semantic stack assignment template;
3. after a successful pilot, run R151 or narrow the paper to a scoped expert
   study before making any user-utility claim.
