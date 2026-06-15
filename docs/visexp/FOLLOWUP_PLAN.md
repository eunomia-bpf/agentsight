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
| G3 small-model and tag adequacy | C2,C6 | 0.6B/1B/3B llama.cpp benchmark, repeated-run stability, human adequacy labels | 3B syntax/full-run evidence plus R121 3B bench smoke; no local 0.6B/1B weights; stability/adequacy still missing | missing |
| G4 developer task utility | C5 | head-to-head task benchmark against trace tree, span flamegraph, flat summary, nonsemantic stack, semantic stack | packets/scorer exist, no participants | missing |

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

Do session/prompt/LLM-call frames separate repeated system effects that would be
merged by ordinary span traces, flat process/file/network summaries, or folded
stacks without semantic frames?

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
- Current design gap: the current `agentflame bench` prompt embeds the run index,
  so it cannot measure identical-input stability until the benchmark uses a
  fixed fragment set and repeats each exact fragment.
- Result path: `.agentsight/agentflame/model-benchmarks.json` and
  `docs/visexp/out/tag-adequacy-labels.csv`.

### B6x: Semantic Axis Ablation

- Claim tested: C3; auxiliary evidence for C6 visual-noise burden only.
- Workload: the same 205-session full run and the B4 task-question set.
- Variants: no semantic frames, session-only, prompt-only, prompt+LLM-call,
  full session+prompt+LLM-call.
- Metrics: mixed weight, unique stack growth, max stack reuse, number of
  visually noisy tags, and B4 task accuracy/time if run before the user study.
- Oracle: each variant must be generated from the same raw observations and
  checked for identical total weight.
- Success criterion for paper: prompt/session frames materially reduce baseline
  mixing while keeping stack growth manageable; LLM-call frames help token views
  or are scoped out from system-effect claims.
- Result path: `.agentsight/agentflame/ablations-r131/summary.json`.

### B4x: Developer Forensic Task Benchmark

- Claim tested: C5.
- Workload: 12-20 questions generated from B1/B3x evidence. Examples:
  - Which semantic task caused the most repeated `cargo test` executions?
  - Which prompt region produced repo-outside file reads?
  - Which task caused network calls, and to which domains?
  - Which repeated failures are concentrated in one semantic region?
- Conditions: raw trace tree, span-duration flamegraph, flat process/effect
  summary, nonsemantic folded stack, semantic effect flamegraph.
- Design: within-subject, Latin-square/counterbalanced order, one condition per
  question per participant, blinded scoring, participants with recent coding
  agent experience or a scoped expert-study limitation.
- Metrics: exact answer accuracy, task time, false positives, confidence, NASA
  TLX-lite or simple workload rating.
- Oracle: hidden answer key computed mechanically from B3x exact lineage and
  manually checked.
- Statistical plan: paired permutation test or mixed-effects model with
  participant and question as random effects; Holm correction across primary
  comparisons.
- Success criterion for paper: semantic view improves exact answer accuracy by
  >=10 percentage points or median task time by >=20% on core questions, with no
  >5 percentage-point increase in false positives. If only experts benefit or
  thresholds fail, wording must narrow to case-study/expert forensic workflow.
- Result path: `docs/visexp/out/user-task-results.json`.

## Tracker Rows To Add Next

| Run ID | Claim | Block | Purpose | Command/config | Seed/reps | Oracle | Decision gate | Result path | Status |
|--------|-------|-------|---------|----------------|-----------|--------|---------------|-------------|--------|
| R114 | C4 | B3x | Broader live exact-lineage task suite over 20 real agent tasks. | `python3 docs/visexp/r114_live_record_suite.py --out docs/visexp/out --timeout 240`; then `python3 docs/visexp/r114_lineage_analysis.py --result docs/visexp/out/live-record-r114.json --out docs/visexp/out` | 20 tasks, fixed task manifest | lineage checker + precision/recall + redaction/path analyzer | passed: 20/20 tasks observed negative controls, 100.0% precision, 100.0% recall, 0/3170 negative-control joins, 0 redaction failures | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | done |
| R121 | C2,C6 | B5x | Real llama.cpp model benchmark. | `agentflame bench --runs 3 --model ...` using available GGUF models | 3 repeats/model | grammar/stability/latency checker | no claims for missing size classes; adequacy labels required | `.agentsight/agentflame/model-benchmarks.json` | planned |
| R122 | C6 | B5x | Human adequacy labeling over sampled fragments. | create redacted label packet and collect labels | 300 fragments, >=2 labelers if possible | adequacy/generic/misleading rubric plus agreement | >=80% adequate, <=20% generic/noisy, kappa >=0.6 or limited claim | `docs/visexp/out/tag-adequacy-labels.csv` | planned |
| R131 | C3 | B6x | Semantic-axis ablation. | regenerate stacks for no/session/prompt/full variants | deterministic | total-weight equality + mixed-weight delta | semantic axes must improve information gain without unbounded stack growth | `.agentsight/agentflame/ablations-r131/summary.json` | planned |
| R141 | C5 | B4x | User-task pilot. | 4 developer participants, counterbalanced conditions | 4 participants | answer key and timing data | task protocol works before paper run | `docs/visexp/out/user-task-results-pilot.json` | planned |
| R151 | C5 | B4x | User-task paper run. | 12-20 participants or scoped expert study | counterbalanced | accuracy/time/false-positive/confidence scorer | required for any user-utility claim | `docs/visexp/out/user-task-results.json` | planned |

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

Move to G3/G4 next. R114/B3x now gives the paper concrete exact-lineage
evidence that span-duration traces do not provide, but OSDI weak accept still
needs evidence that the semantic labels are adequate and that developers
actually answer forensic questions better with the visualization.

1. fix B5x identical-fragment stability so the benchmark repeats the same
   redacted fragments for each model;
2. prepare R122 human adequacy labels for one-word session/prompt/LLM-call tags;
3. run R131 semantic-axis ablations over the same observations;
4. run the B4 developer task pilot using the R114 answer keys and compare
   trace tree, span flamegraph, flat summary, nonsemantic stack, and semantic
   effect stack conditions.
