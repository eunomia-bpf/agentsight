# AgentFlame OSDI Follow-Up Plan

Last updated: 2026-06-19
Stage at update: supplement / experiment-design
Source/command: auto-research-orchestrator + osdi-experiment-design gate review over `docs/visexp`, plus R196 long-tail governance review packet, R201 sensitivity artifact, R202 candidate regeneration smoke, R203 promotion gate, R205 compaction metrics, R209 reversible display-map contract, R213 display-mode drilldown data-layer smoke, R214 long-tail control loop, R215 frontend renderer-model smoke, R216 browser DOM harness smoke, R217 production React display smoke, R218 display-map update gate, R219 claim-readiness gap gate, R195 human-evidence ingestion pipeline, R207 human-evidence launch-readiness audit, R200 public-safe community smoke, `docs/visexp/LONG_TAIL_COMPACTION.md`, R204 read-only gate review, R206 RQ/experiment-plan gate review, and R208 OSDI gate review after paper-plan alignment
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
for fixed command-mode, controlled external-repository, and selected
target-network workloads. It does not yet support broad full-history exact
provenance, arbitrary network workloads, Claude-launched target-network
coverage, user utility, or tag adequacy.
R219 now encodes that boundary as a claim/RQ readiness matrix: C5 is
unsupported with 0 participant responses, C6 is partial with 0 final labels,
and `weak_accept_supported=false`. Its next-experiment table makes
`R142-pilot-return` and `R124-labels-return` the two P0 rows.

Weak accept requires all four gates below:

| Gate | Claim(s) | Required evidence | Current state | Status |
|------|----------|-------------------|---------------|--------|
| G1 full-history semantic characterization | C1-C3 | all repo-related readable sessions annotated by real llama.cpp model, with redacted output and baseline-mixing analysis | R170: 325 sessions, 35,136 llama.cpp HTTP calls, 0 final tag failures, 90.402%/90.918% nonsemantic/flat mixed baseline weights | pass |
| G2 live exact semantic-effect lineage | C4 | broader live `agentsight record` suite, recall/precision table, join/orphan table, child-depth and path specificity, target-network probes, negative controls | R114 fixed 20-task suite: 20/20 targets completed, 1273/1273 in-scope effects joined, 100.0% precision/recall, 3170 observed negative-control effects with 0 joined; R191 joins 4/4 fixed target `python3` HTTP network rows with 0/310 negative joins; R229 joins 394/394 controlled multi-workspace in-scope effects with 0/306 negative joins; R232 joins 353/353 external-repo in-scope effects and 4/4 external HTTP target rows with 0/480 negative joins; R234 joins 269/269 controlled Claude/Codex in-scope effects and 8/8 target network rows with 0/331 negative joins; R238 fixes process-tracer readiness and has a compact 5/5 direct-only readiness supplement, while the official full run joins 13/16 target network rows with 0/186 negative joins; Codex/Claude-launched rows remain partial | pass for fixed and controlled scoped workloads; broad full-history, arbitrary raw sockets, and Claude-launched target-network coverage still partial |
| G3 small-model and tag adequacy | C2,C6 | 0.6B/1B/3B llama.cpp benchmark, repeated-run stability, human adequacy labels | R180 covers local 0.6B-/1B-/3B-class syntax/stability over the 300 R122 redacted fragments: 2700/2700 valid tags; per-model exact stability is 299/300, 279/300, and 285/300 with p95 23/18/32 ms. R189/R190 add a total-preserving canonical display layer plus a 160-row merge-risk audit packet and scorer; R196 adds a long-tail governance packet with regenerate/split/keep actions; R201 adds threshold/generic-vocabulary sensitivity with review-required support 1.926%-1.931% and high-tail head stability 65.217%; R202 exercises candidate-only regeneration with 41/41 grammar-valid one-word outputs and 0 invalid outputs; R203 adds a 41-row promotion packet and blank paired-review gate with 0 final labels; R205 reports raw/canonical unique tags 1,546 -> 1,364, top-20 support coverage 93.683% -> 95.186%, and review-required support 1.926%; R213 verifies display-mode drilldown membership over R209; R214 exposes active/pending/review control gates, a non-default seven-bucket rollup preview, and a versioned regeneration policy while failing prompt review budget plus high-tail head stability; R215 verifies the frontend renderer-model consumer preserves membership and rejects corrupted/candidate-as-active fixtures; R216 verifies the same mode contract in a headless-browser DOM harness; R217 verifies production default rendering; R218 verifies reviewed-diff update-gate mechanics with synthetic review fixtures. These long-tail artifacts are C6 protocol/gate artifacts, not adequacy evidence. R190-score and R203 are still `human_labels_empty`. This is not controlled same-family scaling, and TinyLlama 1.1B collapses semantically toward localization-like tags; human adequacy still missing | partial |
| G4 developer task utility | C5 | head-to-head task benchmark against trace tree, true span-duration flamegraph or explicitly named event-count proxy, flat summary, nonsemantic stack, semantic stack | R142-packet generated 14 tasks, 8 primary utility tasks, 6 limitation/comprehension tasks, 5 conditions, 70 leak-checked blinded packets, P01-P05 counterbalanced assignments, hidden answer key, manifests, and per-task same-event-slice `slice_id` checks. The former span-like event-weight condition is now explicitly named `event-count-proxy`, so the packet no longer claims to be a span-duration baseline. R142-scoring adds response-contract checks, task-level diagnostic deltas, Holm-corrected participant/task/order fixed-effect paper gates, false-positive guardrails, and C5 support/pilot gates. R142-preregistration is now frozen before collection and records source hashes, task roles, response schema, exclusions, conditions, and success thresholds; no participants | missing outcome data |

## Weak-Accept Execution Protocol

The next work should not add another visualization polish pass unless it
directly unblocks C5 or C6. OSDI weak accept requires outcome evidence, so the
execution order is:

1. **R186 plan review.** This pass completed one read-only OSDI review over the
   revised `RESEARCH_PLAN`, paper RQs, R184 gate, and current tracker/verdict/
   audit artifacts. If the plan or RQ wording changes again, rerun this gate
   before recruiting participants or labelers.
2. **R142-pilot for C5.** The current packet has been rescoped to use an
   explicitly named `event-count-proxy` baseline rather than a misleading
   span-duration condition. The C5 analysis preregistration is now frozen in
   `docs/visexp/out/user-task-preregistration-r142.json`; run the P01-P05
   counterbalanced packet with real developers or scoped expert
   participants. The pilot can validate procedure and task wording, but it must
   stay labeled as pilot evidence unless the paper-scale C5 gate passes.
3. **R124-labels for C6.** Use
   `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv` to collect two
   independent human labels for every row, join the frozen sheets with
   `docs/visexp/r124_join_blinded_labels.py`, adjudicate disagreements into
   `docs/visexp/out/tag-adequacy-adjudication-template-r124.csv`, and rerun
   `score_tag_adequacy.py` on the joined packet. Subagents or LLMs may review
   the rubric and spot-check leakage, but their labels do not count as human
   adequacy evidence.
4. **R190 merge-risk labels for canonical display.** If the paper claims that
   long-tail semantic tags can be safely consolidated, label
   `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-packet-r190.csv`
   for `acceptable`, `overmerge`, `undermerge`, or `unclear`, then score the
   two labeler sheets and any adjudication with
   `python3 docs/visexp/r190_score_merge_audit.py --labeler-1 <sheet1> --labeler-2 <sheet2> --adjudication <adjudication.csv>`.
   This is separate from R124: R190 evaluates the raw-to-canonical display
   layer, while R124 evaluates whether the raw candidate tags are adequate for
   the underlying prompt fragments.
5. **R196 long-tail governance review.** If the paper discusses regeneration
   or contextual splitting, use
   `docs/visexp/out/long-tail-governance-r196/long-tail-review-packet-r196.csv`
   as the review packet. R196 keeps 1,241 rare distinct tags rather than
   collapsing them into `other`, routes 39 generic/noisy tags to regeneration,
   and flags 2 generic/noisy high-support prompt tags for contextual split.
   The packet has 323 review-required rows and 0 accepted review labels. It is
   a governance packet only; optional LLM regeneration may propose candidate
   tags, but it cannot satisfy C5 developer-utility evidence, C6 human adequacy
   evidence, or R190 merge-quality evidence.
   `docs/visexp/LONG_TAIL_COMPACTION.md` is the governing contract for this
   step: report raw/canonical unique tags, top-K coverage, tail mass,
   review-required support, head stability, regeneration validity/change rate,
   and promotion acceptance or rejection once human labels exist.
   R205 now reports the no-label version of these metrics: raw unique tag
   strings 1,546 -> canonical unique tag strings 1,364, top-20 support coverage
   93.683% -> 95.186%, and review-required support 1.926%. Treat this as
   compaction observability, not tag-quality evidence.
   R201 already checks policy sensitivity over seven variants: review-required
   support remains 1.926%-1.931%, but higher tail thresholds reduce baseline
   head stability to 65.217%. Treat that as a reviewer-facing design-risk
   disclosure, not as a quality claim.
   R202 now exercises the optional regeneration path: 41/41 regenerate/split
   rows produce grammar-valid one-word candidate tags and 0 invalid outputs, but none
   are promoted without review. Treat this as executability evidence, not as a
   quality claim.
6. **R193 collection package.** Use
   `docs/visexp/out/human-evidence-r193` as the logistics handoff for R124 and
   R190 labelers, and use its R142 pointer to the R187 launch package. R193
   contains only blank sheets and pointers; it removes collection friction but
   does not count as labels or responses.
7. **R194 preflight.** Run
   `python3 docs/visexp/r194_human_evidence_preflight.py` before distribution
   or after any human data is returned. The current status is
   `ready_for_human_collection_no_outcomes`; once real data exists, this gate
   should stop being empty and the corresponding scorer must be rerun.
8. **R195 ingestion/scoring.** After real completed files return, place or pass
   them as `r142-pilot-responses.csv`, `r124-labeler-1.csv`,
   `r124-labeler-2.csv`, `r190-labeler-1.csv`, `r190-labeler-2.csv`,
   `r203-labeler-1.csv`, and `r203-labeler-2.csv`, then run
   `python3 docs/visexp/r195_human_evidence_pipeline.py`. The current
   default run is `awaiting_human_inputs`: no scorers ran, no scored evidence
   was produced, and C5/C6/canonicalization gates remain false. R195 is only an
   ingestion bridge; it cannot synthesize labels or participant responses.
   R207 now audits the launch handoff directly: five R142 participant packets,
   the blank 70-row response template, two 300-row R124 sheets, two 160-row R190
   sheets, two 41-row R203 sheets, and the R195 return-file naming plan are all
   present and launch-ready. R207 is still no-outcome evidence; it only removes
   collection ambiguity.
9. **R151 paper run for C5.** Only after the pilot response contract passes and
   the C5 analysis model is preregistered, collect 12-20 participant response
   rows or explicitly narrow to a scoped expert study. The scorer's
   Holm-corrected participant/task/order fixed-effect gate decides whether any
   user-utility claim is allowed.
10. **C4/RQ6 replication and artifact polish.** R200 now covers a public-safe
   generated-fixture clean/cached smoke with managed llama.cpp and no raw-trace
   reads. External-machine fresh-clone testing, public setup docs, real report
   sanitization, full write-set audit, and external developer feedback remain
   future C7 work. These runs strengthen scope and artifact positioning but
   cannot substitute for adequacy or utility evidence.

R206 rechecks the revised RQ and experiment-plan wording after the R205
compaction update. The review finds no material wording blocker: novelty is
framed as semantic attribution of system effects, and baselines/falsifiers are
clear enough for execution. It still reports Level 3/not weak accept because
the blockers are evidence blockers: R142/R151 participant responses and R124
human labels.

R208 rechecks the plan and paper after adding the reversible long-tail
compaction boundary and aligning R205/R207 in the paper. It again reports Level
3/not weak accept. The revisions improve scoping/readiness, but they do not
replace C5 participant responses, C6 adequacy labels, R190/R203 compaction
quality labels, broader C4 lineage evidence, or external C7 artifact evidence.

Hard evidence boundaries:

- If R124 remains `human_labels_empty`, C6 can only claim syntax/stability.
- If R190-score remains `human_labels_empty`, canonicalization can only be
  claimed as an auditable display-layer mechanism, not as a proven long-tail
  quality fix.
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
with trace trees, the explicitly named `event-count-proxy`, flat summaries, or
nonsemantic folded stacks? A true span-duration flamegraph is optional only if
it is regenerated from timestamps and preregistered as a separate baseline.

Primary oracle: preregistered answer-key task benchmark with accuracy, time,
confidence, and false-positive metrics.

Falsifier: no accuracy/time/confidence improvement, or semantic views introduce
more false positives than baselines.

### RQ5: Are one-word tags stable and adequate as navigation frames?

Are local small models fast and stable enough to produce one-word labels for
session/prompt/LLM-call navigation, and are those labels semantically adequate
for humans?

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
  negative-control effects. R182 then enables record-mode process `--trace-net`
  and joins 35/35 low-level `codex` process network rows across two
  loopback-task runs, with 0 network orphans and 0/604 negative-control joins.
  The target-specific oracle still reports 0/0 loopback or expected
  child-process network rows, so network workload capture and HTTP payload/URL
  reconstruction remain open.
- Failure interpretation: if broader replication fails, C4 remains scoped to
  command-mode capture-time suites and cannot be claimed for arbitrary histories.
- Result path: `.agentsight/agentflame/exact-lineage-r114/summary.json` plus
  committed redacted summary under `docs/visexp/out/live-record-r114.*`.

### B5x: Small-Model Cost, Stability, And Adequacy

- Claim tested: C2, C6.
- Workload: 300 fragments sampled from the full run: 100 session summaries, 100
  prompt texts, 100 LLM-call previews. Store only hashes, redacted previews, and
  labels in committed artifacts.
- Models: at minimum the available local 0.6B-, 1B-, and 3B-class GGUFs. R180
  covers 0.6b, TinyLlama 1.1b, and 3b, but it is a local operational smoke over
  different model families/quantization paths, not a controlled same-family
  scaling curve.
- Command skeleton:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench \
  --llama-server /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  --server-arg=--reasoning --server-arg=off --server-arg=--ctx-size --server-arg=2048 \
  --runs 3 \
  --fragment-file .agentsight/agentflame/r122-real-fragments.txt \
  --out .agentsight/agentflame/model-benchmarks-r180.json \
  --model 0.6b=/path/to/model-0.6b.gguf \
  --model 1.1b=/path/to/model-1.1b.gguf \
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
  load, and 285/300 exact-stable fragments (95.000%). R180 reran the same
  fragments over local 0.6b, TinyLlama 1.1b, and 3b GGUFs with 3 repeats each:
  2700/2700 valid tags, exact stability 299/300, 279/300, and 285/300, and p95
  latency 23/18/32 ms. The 1.1b run collapses toward localization-like tags,
  which is an adequacy warning despite syntactic success.
- Privacy guard: `agentflame bench` now omits fragment previews by default; R121
  used `--include-fragment-previews` only because the three smoke fragments are
  synthetic.
- Remaining gap: paper-level C6 still needs human adequacy labels over the R122
  packet. A controlled same-family 0.6B/1B/3B scaling curve is optional and
  should be claimed only if run separately.
- Result path: `.agentsight/agentflame/model-benchmarks-r180.json`,
  `docs/visexp/out/model-benchmarks-r180.json`, and
  `docs/visexp/out/tag-adequacy-label-packet-r122.csv`.

### B6x: Semantic Axis Ablation

- Claim tested: C3. C6 visual-noise burden and B4 task accuracy/time remain
  deferred.
- Workload: the R170 current full-history run (325 readable sessions, 183,714
  system observations) for semantic-axis mechanics; B4 task-question accuracy
  and time remain a separate human/user benchmark.
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
- Current evidence: R224 reran the R131 checker over the R170 current
  full-history folded artifacts and preserved all system/token totals. It
  records that `agentflame.json` totals match folded inputs and that generated
  nonsemantic/session/prompt folded files exactly match the projections. System
  no-semantic projection mixed 90.402% of full semantic bucket weight with
  44.716% residual; session-only left 84.407% bucket / 33.434% residual;
  prompt-only left 36.722% bucket / 7.485% residual. Full session+prompt left
  0.000% by construction. Token prompt+LLM-call still mixed 92.978% of full
  semantic token bucket weight but only 0.041% residual, so the paper should
  scope LLM-call tags to token navigation rather than
  system-effect attribution.
- Result path: `.agentsight/agentflame/ablations-r224-r170/summary.json`,
  `docs/visexp/out/semantic-ablation-r224-r170/semantic-ablation-r131.json`,
  and `docs/visexp/out/semantic-ablation-r224-r170/semantic-ablation-r131.md`.
  The original R131 paths remain historical evidence for the older 205-session
  run, not the current paper denominator.

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
| R182 | C4 | B3x | Network exact-lineage smoke after record-mode process `--trace-net` fix. | `cargo test -p agentsight cmd_trace::tests::`; `cargo build -p agentsight`; `python3 docs/visexp/r182_network_record_suite.py --out docs/visexp/out --work-dir /tmp/agentsight-r182-network --task-limit 2 --timeout 240` | 2 loopback-task runs, fixed manifest | network lineage + target-specific oracle + precision/recall + negative-control checker | partial: 2/2 targets completed, 35/35 low-level `codex` network rows joined, 0 network orphans, 100.0% precision/recall, 0/604 negative-control joins; target-specific loopback/child-process rows are 0/0 | `docs/visexp/out/live-network-r182.json`, `docs/visexp/out/live-network-r182.md` | partial/network-flag-smoke |
| R121 | C2,C6 | B5x | Real llama.cpp model benchmark. | `agentflame bench --runs 3 --model ...` using available GGUF models | 3 fixed fragments x 3 identical repeats | grammar/stability/latency checker | done for 3B smoke: 9/9 valid tags, 2/3 exact-stable fragments; no claims for missing size classes; adequacy labels required | `.agentsight/agentflame/model-benchmarks.json`, `docs/visexp/out/model-benchmarks-r121.json` | done |
| R122 | C6 | B5x | Redacted label packet. | create redacted label packet | 300 fragments | redaction scan + stratified counts | packet ready; labels still required | `docs/visexp/out/tag-adequacy-label-packet-r122.csv` | done/packet |
| R123 | C2,C6 | B5x | Real redacted fragment stability. | `agentflame bench --fragment-file .agentsight/agentflame/r122-real-fragments.txt --runs 3 --model ...` | 300 fragments x 3 repeats | grammar/stability/latency checker | done for 3B: 900/900 valid, 285/300 exact-stable, p95 31 ms; adequacy labels required | `.agentsight/agentflame/model-benchmarks-r123.json`, `docs/visexp/out/model-benchmarks-r123.json` | done |
| R180 | C2,C6 | B5x | Local multi-model syntax/stability smoke. | `agentflame bench --fragment-file .agentsight/agentflame/r122-real-fragments.txt --runs 3 --server-arg=--reasoning --server-arg=off --model 0.6b=... --model 1.1b=... --model 3b=...` | 3 models x 300 fragments x 3 repeats | grammar/stability/latency checker plus explicit non-adequacy boundary | done: 2700/2700 valid, exact stability 299/300, 279/300, 285/300, p95 23/18/32 ms; 1.1b semantic collapse means adequacy still unproven | `.agentsight/agentflame/model-benchmarks-r180.json`, `docs/visexp/out/model-benchmarks-r180.json` | done/syntax-stability |
| R124-scoring | C6 | B5x | Adequacy scorer and empty-result gate. | `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r122.csv ...`; then `python3 docs/visexp/evaluate_artifacts.py --out docs/visexp/out` | deterministic over 300 packet rows | candidate-tag coverage, empty/partial/scored status, adequacy/kappa thresholds | done as protocol only: current output is `human_labels_empty`, 300 candidate tags, 0 final labels, `adequacy_supported=false`; C6 remains partial | `docs/visexp/out/tag-adequacy-results-r124.json` | done/empty |
| R124-join | C6 | B5x | Blinded label join and adjudication protocol. | `python3 docs/visexp/r124_join_blinded_labels.py` | deterministic over 300 packet rows | source/blinded row match, hidden-field contract, no committed human labels, empty adjudication template | protocol passed: ready for independent label collection; does not support C6 until real labels are joined and scored | `docs/visexp/out/tag-adequacy-label-join-r124.json`, `docs/visexp/out/tag-adequacy-adjudication-template-r124.csv` | done/protocol |
| R124 | C6 | B5x | Human adequacy labeling over sampled fragments. | collect two independent completed copies of `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`; join them with `python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 ... --labeler-2 ... --adjudication ...`; score with `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv --out-json docs/visexp/out/tag-adequacy-results-r124.json --out-csv docs/visexp/out/tag-adequacy-results-r124.csv --out-md docs/visexp/out/tag-adequacy-results-r124.md` | 300 fragments, >=2 labelers | adequacy/generic/misleading rubric plus agreement/adjudication | scored gate has >=80% adequate, <=20% generic/noisy, <=5% misleading, kappa >=0.6 or limited claim | `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-results-r124.csv`, `docs/visexp/out/tag-adequacy-results-r124.md` | planned |
| R131 | C3 | B6x | Semantic-axis ablation. | `python3 docs/visexp/r131_semantic_ablation.py --input .agentsight/agentflame/latest --local-out .agentsight/agentflame/ablations-r131/summary.json --out-dir docs/visexp/out` | deterministic | total-weight equality + report/folded cross-checks + mixed/residual delta | passed for C3 mechanism: all totals preserved; generated folded files match projections; system prompt-only reduced mixed full semantic bucket weight from 90.219% to 37.687% and residual from 44.639% to 7.526%; C6/B4 deferred | `.agentsight/agentflame/ablations-r131/summary.json`, `docs/visexp/out/semantic-ablation-r131.json` | done for C3; C6/B4 deferred |
| R141-packet | C5 | B4x | Superseded deterministic user-task packet draft. | `python3 docs/visexp/user_task_benchmark.py ...` before same-slice enforcement | 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | leak check + assignment coverage + scorer status | superseded by R142 same-slice packet | `docs/visexp/out/user-task-benchmark.json` historical commit | superseded |
| R142-packet | C5 | B4x | Same-event-slice user-task packet and empty scorer check. | `python3 docs/visexp/user_task_benchmark.py --out docs/visexp/out --agentflame-dir .agentsight/agentflame/latest`; scorer over `user-task-response-template.csv` | 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | hidden answer key + leak-checked blinded packets + assignment coverage + per-task common `slice_id` + explicit `event-count-proxy` baseline naming + scorer status | packet ready for preregistered pilot collection; no C5 claim without participants | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-results.json` | done/packet |
| R142-scoring | C5 | B4x | Response-contract and paper-scale C5 scorer gate. | `python3 docs/visexp/score_user_task_results.py --responses docs/visexp/out/user-task-response-template.csv --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out` | deterministic empty-template check; real responses later | assignment/packet contract checks, diagnostic task-level deltas, Holm-corrected participant/task/order fixed-effect tests, false-positive guardrail, pilot/paper support gates | current output is `participant_results_empty`, `c5_supported=false`, `pilot_ready=false`; no C5 claim without participants | `docs/visexp/out/user-task-results.json` | done/empty |
| R142-preregistration | C5 | B4x | Frozen analysis contract before participant collection. | `python3 docs/visexp/r142_preregistration.py` | deterministic over current bundle, assignments, answer key, response template, and scorer constants | source-hash lock, condition/schema/threshold validation, event-count proxy boundary, exclusion rules | prereg gate passed as `frozen_before_collection`; still no outcome evidence | `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-preregistration-r142.md` | done/protocol |
| R184 | C5,C6 | gate | Mechanical weak-accept human-evidence gate over existing R124/R142 artifacts. | `python3 docs/visexp/r184_weak_accept_gate.py --out-dir docs/visexp/out` | deterministic over current R124/R142 outputs | C5 and C6 both must pass existing human-data scorers; subagent/LLM/mock/placeholder evidence is disallowed | current output is `not_weak_accept`; C5 is ready for participant collection and C6 is ready for independent label collection | `docs/visexp/out/weak-accept-gate-r184.json`, `docs/visexp/out/weak-accept-gate-r184.md` | done/gate |
| R186 | C1-C7 | gate | Read-only OSDI review and cleanup of revised RQ/experiment plan before collecting new outcome data. | inspect `docs/visexp/RESEARCH_PLAN.md`, `docs/visexp/paper/main.tex`, R184/R185, tracker/verdict/audit/followup artifacts | one independent review | OSDI plan-template and evaluation-rubric gate: every claim has falsifying result, oracle, baseline, run order, and outcome-data boundary | review says Level 3/not weak accept; cleanup makes R142 pilot the next executable human study while R151 remains blocked until R142 passes | `docs/visexp/out/osdi-plan-review-r186.md` | done/review |
| R187 | C5 | B4x | User-task pilot launch package. | `python3 docs/visexp/r187_prepare_pilot_materials.py --out docs/visexp/out/user-task-pilot-r142/launch` | deterministic packaging over frozen R142 packets | P01-P05 participant files, blank 70-row response CSV, no answer key, no forbidden oracle/scoring keys, `c5_supported=false` | launch material is ready to send; it records 0 real responses and cannot support C5 | `docs/visexp/out/user-task-pilot-r142/launch/manifest.json` | done/launch |
| R188 | C1-C7 | gate | Read-only OSDI plan review after R187. | inspect R187 launch manifest plus current plan/tracker/verdict/audit/followup/paper | one independent review | strict OSDI rubric, R187 launch/outcome boundary, no C5/C6 non-human substitutes | review says Level 3/not weak accept; next real evidence rows remain R142-pilot and R124-labels | `docs/visexp/out/osdi-plan-review-r188.md` | done/review |
| R142 | C5 | B4x | User-task pilot. | send R187 P01-P05 packets, collect 5 developer participants using counterbalanced conditions, and score with `python3 docs/visexp/score_user_task_results.py --responses <pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142` | 5 participants for complete condition coverage | answer key, timing data, false positives, confidence, response-contract checker | task protocol works before paper run; pilot is not paper-scale C5 support | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` | planned/collection |
| R151 | C5 | B4x | User-task paper run. | 12-20 participants or scoped expert study | counterbalanced | accuracy/time/false-positive/confidence scorer | required for any user-utility claim | `docs/visexp/out/user-task-results.json` | planned |
| R160 | C7 | B7 | Bounded fixed-session open-source usability smoke. | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command against the same output dir; then `python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke-fixed --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json --out docs/visexp/out/artifact-usability-r160.json ...` | one clean run plus cached rerun over fixed inputs | expected files + runtime/cache summary + sanitized input manifest + clean/cached input equality + 76/76 cached rerun + no raw-trace git dirt + generated report path containment | bounded local artifact path is auditable without the internal harness; fresh-clone/community usefulness, public report sanitization, and full write-set containment remain open | `docs/visexp/out/artifact-usability-r160.json` | done/bounded |
| R200 | C7 | B7 | Public-safe generated-fixture community smoke. | `python3 docs/visexp/r200_community_smoke.py --command-timeout 360 --load-timeout 240` | one temporary synthetic Codex fixture; clean + cached rerun | no real `.codex`/`.claude` trace reads; expected artifacts; clean run has 5 llama.cpp calls; cached rerun has 0 model calls and 5/5 cache hits; no prompt-preview leakage; no raw-trace dirty paths | public-safe artifact path works on generated inputs, but external adoption, real-report public sanitization, and full write-set audit remain open | `docs/visexp/out/community-smoke-r200.json`, `docs/visexp/out/community-smoke-r200.md` | done/artifact-hygiene |
| R170 | C1,C2,C3,C7 | B1/B5/B7 | Current full-history refresh. | seed R170 tag cache from `latest`, run AgentFlame over current repo sessions against local 3B llama.cpp server, summarize with `python3 docs/visexp/r170_full_history_refresh.py` | all discovered repo sessions under scan cap | AgentFlame ok + 0 tagger failures + folded totals match report + redacted committed summary | done as mechanism/artifact evidence: 325 sessions, 35,136 fresh llama.cpp tag calls, 0 failures; does not support C5/C6 | `docs/visexp/out/full-history-r170.json` | done/mechanism |
| R189 | C3,C6 | B8 | Total-preserving canonical tag consolidation for long-tail display noise. | `python3 docs/visexp/r189_tag_consolidation.py` | deterministic over R170/R189 generated artifacts | raw totals preserved, raw-to-canonical map exported, merge reasons separated into dictionary alias, lexical+profile, profile-only, and review-only suggestions | done as display-layer mechanism: prompt-effect tags 263->216, LLM-event tags 1423->1254, system stacks 26,829->26,067, token stacks 8,569->7,661; does not prove adequacy | `docs/visexp/out/tag-consolidation-r189/tag-consolidation-r189.json` | done/mechanism |
| R190 | C3,C6 | B8 | Merge-risk audit packet and consolidation ablation. | `python3 docs/visexp/r190_tag_consolidation_audit.py` | deterministic over R170/R189 generated artifacts | raw/alias-only/lexical-only/profile-guarded comparison plus over-merge/under-merge audit packet | packet ready: lexical-only is more aggressive than profile-guarded current policy, especially LLM-event tags 868 vs 1254; 160 audit rows exported with 0 human labels, so no over/under-merge rate is claimed | `docs/visexp/out/tag-consolidation-audit-r190/tag-consolidation-audit-r190.json` | done/audit-packet |
| R190-score | C3,C6 | B8 | Merge-risk audit scorer and empty-evidence gate. | `python3 docs/visexp/r190_score_merge_audit.py` | deterministic over the 160-row R190 packet | two-labeler/adjudication scorer, kappa, unclear rate, over-merge rate, under-merge rate, empty-label boundary | current output is `human_labels_empty`: 160 rows, 0 final labels, `canonicalization_quality_supported=false`; protocol ready but no quality claim | `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json` | done/empty |
| R196 | C3,C6 | B8 | Long-tail tag governance packet. | `python3 docs/visexp/r196_long_tail_governance.py` | deterministic over R170/R189 generated artifacts; optional regeneration disabled | raw tags preserved; semantic heads kept; generic/noisy tags routed to regenerate/split; review support measured | packet ready: 231 existing merges, 114 review merges, 39 regeneration candidates, 2 contextual-split candidates, 1,241 kept rare distinct tags, and 184 kept heads; no adequacy or merge-quality claim | `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json` | done/governance |
| R201 | C3,C6 | B8 | Long-tail governance sensitivity. | `python3 docs/visexp/r201_long_tail_sensitivity.py` | deterministic 7-variant grid over R170/R189 generated artifacts; no raw-trace mutation; no LLM regeneration | threshold/generic-vocabulary variants report review-required row/support counts, long-tail support, action movement, and head stability while support gates remain false | sensitivity complete: baseline review-required support 1.926%, worst 1.931%, long-tail support 0.921%-3.030% under lower/higher thresholds, high-tail head stability 65.217%; no adequacy or merge-quality claim | `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json` | done/sensitivity |
| R202 | C3; C6 protocol/gate only | B8 | Long-tail candidate regeneration smoke. | `python3 docs/visexp/r202_long_tail_regeneration_smoke.py --regenerate-limit 50 --load-timeout 240 --llama-timeout 60` | managed local llama.cpp server over R196 regenerate/split rows; no raw-trace mutation; no canonical-map update | attempted rows, grammar-valid/invalid regenerated tags, changed/unchanged candidates, gates remain false | smoke passed: 41/41 attempted rows, 41 grammar-valid one-word outputs, 0 invalid, 32 changed, 9 unchanged, 25 unique regenerated tags; top-level outputs are public-oriented, but nested `r196-with-regeneration/` details are local-audit-only; no adequacy or merge-quality claim | `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json` | done/regeneration-smoke |
| R203 | C3; C6 protocol/gate only | B8 | Human-gated promotion protocol for regenerated long-tail candidates. | `python3 docs/visexp/r203_long_tail_promotion_gate.py` | deterministic over public-oriented R202 attempts; no raw-trace reads; no canonical-map update; 0 human labels | promotion packet, blank reviewer sheets, paired/adjudicated-label gate, and empty-label boundary | packet ready: 41 rows, 41 grammar-valid regenerated candidates, 32 changed-from-raw candidates, 0 final labels, `long_tail_promotion_review_supported=false`, `canonical_map_updated=false`; no adequacy or merge-quality claim | `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json` | done/empty-promotion-gate |
| R205 | C3; C6 protocol/gate only | B8 | Long-tail compaction metrics. | `python3 docs/visexp/r205_long_tail_compaction_metrics.py` | deterministic over generated R189/R190/R196/R201/R202/R203 artifacts; no raw-trace reads; no canonical-map update | raw/canonical unique tags, top-K coverage, long-tail support, review-required support, regeneration validity, promotion-label coverage, and merge-risk rates must be reported without changing support gates | metrics ready: raw unique tag strings 1,546 -> canonical unique tag strings 1,364; top-20 support coverage 93.683% -> 95.186%; review-required support 1.926%; R203 labels 0; R190 rates `n/a`; no adequacy or quality claim | `docs/visexp/out/long-tail-compaction-r205/long-tail-compaction-r205.json` | done/metrics-only |
| R209 | C3; C6 protocol/gate only | B8 | Reversible display-map and raw drilldown contract. | `python3 docs/visexp/r209_reversible_display_map.py` | deterministic over generated R196/R203/R205 artifacts; no raw-trace reads; no canonical-map update | every R196 raw tag has one active display row, no hidden `other` bucket, regenerated labels remain candidates, drilldown support is preserved, and reviewed diff stays empty without R203 labels | display-map contract ready: 1,811/1,811 raw rows covered, 1,509 active display labels, 41 candidate regenerated labels, 0 reviewed diff rows, 0 hidden `other` rows; no adequacy or quality claim | `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json` | done/display-map-contract |
| R213 | C3; C6 protocol/gate only | B8 | Display-mode drilldown data-layer smoke. | `python3 docs/visexp/r213_display_mode_drilldown_smoke.py` | deterministic over R209 artifacts; no raw-trace reads; no LLM calls; no frontend renderer execution | raw/display/pending data modes preserve support, pending membership is unchanged, and drilldown membership matches active display membership | data-layer smoke ready: all modes preserve 482,398 support, raw has 1,811 buckets, display/pending 1,748 buckets, 323 review rows visible; no adequacy, quality, utility, or frontend claim | `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json` | done/data-layer-smoke |
| R214 | C3; C6 protocol/gate only | B8 | Adaptive long-tail control loop. | `python3 docs/visexp/r214_long_tail_control_loop.py` | deterministic over R196/R201/R202/R205/R209/R213 artifacts; no raw-trace reads; no LLM calls; no canonical-map update | deterministic aliases stay active; profile/regenerated/split candidates stay pending; rollup preview preserves all rows/support but remains non-default; prompt review budget and head-stability gates expose unsafe automatic compaction | control loop ready: 63 active alias rows, 209 pending candidates, 323 review-required rows, 0 active candidate merges; 7 rollup buckets preserve 1,811 rows and 482,398 support; 41 regenerated candidates have 0 promotable rows without labels; prompt-review and high-tail-stability triggers fail | `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json` | done/control-loop |
| R215 | C3; C6 protocol/gate only | B8 | Frontend display-mode renderer-model smoke. | `python3 docs/visexp/r215_frontend_renderer_mode_smoke.py` | deterministic over R209 display-map/drilldown rows plus R213/R214 summary cross-checks and TypeScript display-mode utility; no raw-trace reads; no LLM calls; no browser DOM | frontend consumer preserves raw/display/pending support and active membership; pending candidates remain overlays; corrupted drilldown and candidate-as-active fixtures are rejected | renderer-model smoke ready: raw/display/pending buckets 1,811/1,748/1,748, support 482,398, 209 candidate overlays, 323 review rows, 0 hidden `other`; no DOM, adequacy, quality, or utility claim | `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json` | done/renderer-model-smoke |
| R216 | C3; C6 protocol/gate only | B8 | Browser DOM display-mode harness smoke. | `python3 docs/visexp/r216_browser_dom_mode_smoke.py` | deterministic over R209/R213/R214/R215 generated artifacts and TypeScript display-mode utility; no raw-trace reads; no LLM calls; no production React view | headless browser renders raw/display/pending controls, clicks all modes, preserves support/membership, and rejects corrupted drilldown plus candidate-as-active fixtures | browser-DOM harness ready: pending view shows 1,748 buckets, 482,398 support, 209 candidate overlays, 323 review rows, 63 active merges, 0 hidden `other`; no production UI, adequacy, quality, or utility claim | `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json` | done/browser-dom-harness-smoke |
| R217 | C3; C6 protocol/gate only | B8 | Production React default display smoke. | `python3 docs/visexp/r217_production_react_display_mode_smoke.py` | deterministic over R209/R216 generated artifacts and real Next static frontend; no raw-trace reads; no LLM calls; no production click path | production `AgentFlameView` renders default display mode with 1,748 buckets, 482,398 support, 3 buttons, and matching raw membership | production-render smoke ready; no click path, visual drilldown, adequacy, quality, utility, or map-update claim | `docs/visexp/out/production-react-display-r217/production-react-display-r217.json` | done/production-render-smoke |
| R218 | C3; C6 protocol/gate only | B8 | Reviewed display-map update gate. | `python3 docs/visexp/r218_display_map_update_gate.py` | deterministic over R209 generated artifacts; synthetic review fixtures only; no raw-trace reads; no LLM calls; no canonical-map update | final consensus/adjudicated rows can create preview diffs, unsafe rows are rejected, support/raw keys are preserved, hidden `other` is rejected | update-gate smoke ready; no promotion quality, adequacy, utility, or map-update claim | `docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json` | done/update-gate-smoke |
| R219 | C1-C7 audit | gate | Claim/RQ readiness gap gate. | `python3 docs/visexp/r219_claim_readiness_gap_gate.py` | deterministic over generated evidence artifacts; no raw-trace reads; no LLM calls; no labels/responses synthesized | C5 and C6 remain blockers, weak accept stays unsupported, synthetic/subagent evidence is disallowed, and R142/R124 are P0 next rows | readiness gate reports `osdi_weak_accept_not_supported` with C5 responses 0 and C6 final labels 0 | `docs/visexp/out/claim-readiness-r219/claim-readiness-r219.json` | done/readiness-audit |
| R204 | C5,C6 | gate | Read-only OSDI gate review after R203/R193/R194/R195/R202 integration. | inspect current long-tail promotion and human-evidence pipeline artifacts plus claim-boundary docs | one independent review | strict OSDI rubric: empty promotion packets, LLM labels, and subagent review cannot substitute for human labels/responses | review says Level 3/not weak accept; no must-fix R203/R193/R194/R195/R202 overclaim; call R202/R203 C6 protocol/gate artifacts, not adequacy evidence | `docs/visexp/out/osdi-gate-review-r204.md` | done/review |
| R206 | C1-C7 | gate | Read-only OSDI RQ/experiment-plan gate review after R205 and reviewer-facing RQ summary. | inspect revised RQ summary, execution-slice table, current gate docs, and paper | one independent review | strict OSDI rubric: novelty must be semantic attribution, baselines/falsifiers/oracles must be executable, and empty human gates must remain unsupported | review says no material plan-wording blocker; current maturity remains Level 3/not weak accept because C5 responses and C6 human labels are missing | `docs/visexp/out/osdi-rq-gate-review-r206.md` | done/review |
| R208 | C1-C7 | gate | Read-only OSDI gate review after R205/R207 paper-plan alignment. | inspect revised plan, paper, long-tail compaction contract, R205 metrics, R207 launch readiness, and current gate docs | one independent review | strict OSDI rubric: readiness/scoping artifacts must not substitute for C5/C6 outcome evidence or compaction-quality labels | review says revisions materially improve scoping/readiness, but current maturity remains Level 3/not weak accept; next rows are real R142 responses, R124 labels, and optionally R190/R203 labels | `docs/visexp/out/osdi-gate-review-r208.md` | done/review |
| R192 | C5,C6 | gate | Read-only OSDI gate review after R190-score. | inspect R190-score plus current plan/tracker/results/verdict/audit/followup/paper | one independent review | strict OSDI rubric: R190-score cannot count as human labels or participant evidence | review says Level 3/not weak accept; no major R190-score overclaim; next real evidence remains R142/R151 and R124 | `docs/visexp/out/osdi-gate-review-r192.md` | done/review |
| R193 | C5,C6 | collection | Human-evidence collection package. | `python3 docs/visexp/r193_prepare_human_evidence_package.py` | deterministic over frozen R187/R124/R190/R203 artifacts | blank-sheet field checks, zero human evidence counts, no answer-key copying, support gates false | package ready: R124 has two blank 300-row sheets, R190 has two blank 160-row sheets, R203 has two blank 41-row promotion sheets, R142 pointer references R187 launch; no labels or responses | `docs/visexp/out/human-evidence-r193/manifest.json` | done/collection-ready |
| R194 | C5,C6 | collection | Human-evidence collection preflight. | `python3 docs/visexp/r194_human_evidence_preflight.py` | deterministic over R193/R187/R124/R190/R203/R142 artifacts | file hashes, blank sheets, blank response template, empty scorers, false support gates | preflight passed as `ready_for_human_collection_no_outcomes`; R124/R190/R203 sheets and R142 template are blank; no labels or responses | `docs/visexp/out/human-evidence-preflight-r194.json` | done/preflight |
| R195 | C5,C6 | collection | Human-evidence ingestion/scoring pipeline. | `python3 docs/visexp/r195_human_evidence_pipeline.py` | deterministic default over empty R195 inbox; real CSVs scored only when present | missing inputs must produce `awaiting_human_inputs`, no scorer operations, R195-specific scored outputs only, and false support gates | default run is `awaiting_human_inputs`; required inputs missing, no operations ran, and C5/C6/canonicalization/promotion gates remain false | `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/human-evidence-pipeline-r195.md` | done/pipeline-awaiting |
| R207 | C5,C6 | collection | Human-evidence launch-readiness and return-file mapping. | `python3 docs/visexp/r207_human_launch_readiness.py` | deterministic over R187/R193/R195 generated artifacts; no raw-trace reads; no labels/responses filled | participant packets, label sheets, response template, READMEs, R195 inbox names, and false support gates | launch-ready/no outcomes: five R142 packets, blank 70-row response template, two 300-row R124 sheets, two 160-row R190 sheets, two 41-row R203 sheets, and clear R195 return names | `docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json` | done/launch-ready |
| R171 | C5,C6 | gate | Read-only subagent OSDI gate review. | inspect current plan/tracker/results/verdict/audit/followup/paper/gate outputs | one independent review | strict OSDI rubric | review says Level 3, not weak accept; R124-labels and R142/R151 remain the must-fix outcome artifacts | `docs/visexp/out/osdi-gate-review-r171.md` | done/review |
| R181 | C2,C5,C6 | gate | Read-only subagent OSDI gate review after R180. | inspect R180 model benchmark, claim gates, paper wording, and current audit | one independent review | strict OSDI rubric | review says R180 is correctly scoped as syntax/stability only; still Level 3, not weak accept, with C6 labels and C5 responses missing | `docs/visexp/out/osdi-gate-review-r181.md` | done/review |
| R185 | C5,C6 | gate | Read-only subagent OSDI gate review after R184. | inspect current research state, R184 gate, plan/tracker/results/verdict/audit/followup/paper | one independent review | strict OSDI rubric with no human-label or participant substitution | review says no claim reaches weak accept; the single highest-value next artifact is a real R142 five-participant developer pilot | `docs/visexp/out/osdi-gate-review-r185.md` | done/review |

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
- "0.6B/1B are semantically adequate";
- "semantic tags are correct."

## Immediate Next Action

Move to G3/G4 next. After R187, R142 pilot collection can start from the
per-participant launch package under
`docs/visexp/out/user-task-pilot-r142/launch`; do not collect R151 paper-run
responses until R142 passes its response-contract and pilot checks.
R114/B3x now gives the paper concrete exact-lineage evidence that
span-duration traces do not provide, but OSDI weak accept still needs evidence
that the semantic labels are adequate and that developers actually answer
forensic questions better with the visualization.

1. send the R187 P01-P05 R142 pilot packets and collect real completed response
   rows in a copy of the blank launch CSV;
2. collect/adjudicate human adequacy labels using the blinded R124 labeler
   sheet, then rerun `score_tag_adequacy.py`;
3. if claiming canonicalized long-tail tags, label the R190 merge-risk audit
   packet, run `r190_score_merge_audit.py`, and report over-merge/under-merge
   rates separately from R124 adequacy;
4. copy returned R142/R124/R190/R203 CSV files into
   `docs/visexp/out/human-evidence-r195/inbox` or pass them to
   `r195_human_evidence_pipeline.py` explicitly, then score through the R195
   pipeline;
5. after a successful pilot, run R151 or narrow the paper to a scoped expert
   study before making any user-utility claim.
