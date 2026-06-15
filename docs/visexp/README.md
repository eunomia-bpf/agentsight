# Semantic Tag Flamegraph Experiment

This directory contains the research artifacts for AgentFlame, a semantic
system-effect profiler for AI coding agents. The current implementation lives in
`agentflame/`: it reads real local Codex and Claude JSONL sessions for this
repository, asks a real llama.cpp-compatible server for one lowercase word per
session, user prompt, and LLM call, then emits folded stacks, SVG flamegraphs,
and a static dashboard.

Start with [RESEARCH_PLAN.md](RESEARCH_PLAN.md) for the thesis and RQs. See
[CLAIMS.md](CLAIMS.md) and [CLAIM_VERDICT.md](CLAIM_VERDICT.md) for the current
evidence gate, and [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) plus
[EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md) for the OSDI-facing evaluation
plan.

The important invariant is aggregation:

```text
project:agentsight;agent:codex;session:design;prompt:flamegraph;tool:shell;cmd:rg;effect:read;path:docs/design;status:ok 7
```

The line above means seven raw tool/effect observations collapsed into one stack.
The SVG is a rendering of the folded stack file, not a per-session trace tree.

## Current Rust Run

Start a local llama.cpp server with a real GGUF model:

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 --port 18080 --reasoning off
```

Generate the current full local-history report:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- run \
  --project-root . \
  --scan-files 10000 \
  --max-sessions 10000 \
  --llama-url http://127.0.0.1:18080 \
  --model local \
  --timeout 60 \
  --out .agentsight/agentflame/latest
```

The Rust path has no heuristic fallback. If the LLM server is unavailable, or
if the model cannot return one valid lowercase word after retry, the run fails.

Bounded artifact-usability smoke:

```bash
python3 docs/visexp/artifact_usability_r160.py \
  --agentflame-dir .agentsight/agentflame/r160-smoke-fixed \
  --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json \
  --out docs/visexp/out/artifact-usability-r160.json
```

R160 uses fixed historical session files rather than dynamic discovery, because
live Codex session files can grow between clean and cached runs. The committed
audit JSON records only sanitized input fingerprints and verifies clean/cached
input equality. The generated `.agentsight/agentflame/*/agentflame.json` reports
are local/private because they can include trace roots and session file
metadata. R160 is a bounded local artifact-path check, not a fresh-clone,
public-release, or community-adoption result.

Legacy Python prototype pipeline:

```bash
python3 docs/visexp/run_pipeline.py --out docs/visexp/out
```

The legacy output is useful for older fixture/user-task scripts, but the current
headline results come from `.agentsight/agentflame/latest`.

## Outputs

- `.agentsight/agentflame/latest/index.html`: current Rust static report page.
- `.agentsight/agentflame/latest/agentflame.json`: current redacted
  machine-readable report.
- `.agentsight/agentflame/latest/tags.json`: current local tag cache with LLM
  provenance and no raw prompt text.
- `.agentsight/agentflame/latest/*.folded.txt`: current folded stacks.
- `.agentsight/agentflame/latest/*.svg`: current dashboard figures.
- `out/full-history-r170.json`: sanitized R170 current full-history refresh
  summary over `.agentsight/agentflame/r170-full-current`, including session
  counts, fresh llama.cpp tag calls, cache hits, folded-total integrity, and
  an explicit C5/C6 non-evidence boundary.
- `out/full-history-r170.md`: human-readable R170 refresh summary.
- `out/model-benchmarks-r180.json`: scrubbed R180 local 0.6B-/1B-/3B-class
  llama.cpp syntax/stability benchmark over the 300 redacted R122 fragments.
  It records 2700/2700 valid one-word outputs, per-model latency/stability, and
  an explicit boundary that this is not human adequacy or controlled
  same-family scaling evidence.
- `out/model-benchmarks-r180.md`: human-readable R180 benchmark summary.
- `out/live-network-r182.json`: scrubbed R182 network exact-lineage supplement
  over two real `codex exec` loopback-task runs under `agentsight record`.
  It records 35/35 joined low-level `codex` process network rows, 0 network
  orphans, and 0/604 joined negative-control effects after record-mode process
  `--trace-net` is enabled. It also records 0/0 target-specific loopback or
  expected child-process network rows, so loopback workload capture remains
  partial.
- `out/live-network-r182.md`: human-readable R182 network supplement summary.
- `out/osdi-gate-review-r183.md`: read-only subagent OSDI gate review that
  downgraded the initial R182 overclaim and keeps the network result scoped as
  a partial record-mode `--trace-net` smoke.
- `out/weak-accept-gate-r184.json`: mechanical C5/C6 weak-accept human
  evidence gate. It currently reports `not_weak_accept`, with C5 ready for
  participant collection and C6 ready for independent label collection.
- `out/weak-accept-gate-r184.md`: human-readable R184 gate summary and exact
  commands to run after real human inputs exist.
- `out/osdi-gate-review-r185.md`: read-only subagent OSDI gate review after
  R184; it identifies the real R142 developer pilot as the highest-value next
  artifact.
- `out/index.html`: legacy Python report page.
- `out/visual-summary.html`: compact visual progress gallery.
- `out/system-flamegraph.svg`: system/tool footprint flamegraph.
- `out/token-flamegraph.svg`: token footprint flamegraph.
- `out/session-system.svg`: system footprint projected by session tag.
- `out/prompt-system.svg`: system footprint projected by prompt tag.
- `out/session-token.svg`: token footprint projected by session tag.
- `out/prompt-token.svg`: token footprint projected by prompt tag.
- `out/llm-token.svg`: token footprint projected by LLM-call tag.
- `out/claim-gates.svg`: current claim-readiness chart.
- `out/semantic-mixing.svg`: semantic aggregation and baseline-mixing chart.
- `out/effect-lineage.svg`: legacy C4 exact-effect lineage readiness chart.
- `out/semantic-system.folded.txt`: collapsed system stacks.
- `out/nonsemantic-system.folded.txt`: baseline folded stacks with session and
  prompt tags removed.
- `out/semantic-token.folded.txt`: collapsed token stacks.
- `out/tag-dimensions.json`: machine-readable summaries for each dimension
  projection.
- `out/tag-dimensions.csv`: compact table for dimension projections.
- `out/pipeline-report.json`: one-command pipeline step report.
- `out/pipeline-summary.md`: human-readable one-command pipeline summary.
- `out/aggregation.json`: proof that raw events were collapsed into fewer
  unique stacks, with repeated stack examples.
- `out/input-manifest.json`: exact argv, selected session hashes, script hash,
  llama.cpp commit when available, and model checksum.
- `out/agent-diff.csv`: Codex-vs-Claude comparison after removing the agent
  frame from each normalized system stack, split by top/subagent cohort and
  normalized per 1000 observations.
- `out/command-summary.csv`: flat process/tool baseline.
- `out/evaluation.json`: artifact-level evaluation of aggregation strength,
  semantic-vs-nonsemantic mixing, tag quality proxies, and claim gates.
- `out/semantic-mixing.csv`: examples where nonsemantic or flat baselines merge
  multiple session/prompt tags that semantic stacks separate.
- `out/claim-gates.csv`: machine-readable claim verdicts for current artifacts.
- `out/evaluation-summary.md`: human-readable artifact audit.
- `out/effect-lineage-smoke.json`: fixture-backed C4 checker summary for
  joining process/file/network events to session/tool/prompt ancestry.
- `out/effect-lineage.csv`: per-event exact-effect lineage rows, including
  orphan reasons for failed joins.
- `out/effect-lineage.folded.txt`: exact-effect folded stack output from the
  lineage checker.
- `out/effect-lineage-summary.md`: human-readable C4 smoke summary.
- `out/live-lineage-r110.json`: R110 live in-scope C4 smoke summary over three
  real AgentSight DB exports with harness-synthesized agent-run envelopes.
- `out/live-lineage-r110.md`: human-readable R110 boundary and result table.
- `out/native-lineage-r111.json`: R111 native export C4 smoke summary over the
  same DB exports after `collector report export` emits session/tool envelope
  rows.
- `out/native-lineage-r111.md`: human-readable R111 boundary and result table.
- `out/native-lineage-r112.json`: R112 DB-persisted backfill C4 smoke summary
  over copies of the same DB exports, verified with persisted-only export.
- `out/native-lineage-r112.md`: human-readable R112 boundary and result table.
- `out/capture-time-r113.json`: R113 capture-time `record -- <command>`
  session/tool row implementation smoke.
- `out/capture-time-r113.md`: human-readable R113 boundary and result table.
- `out/live-record-r113.json`: R113-live summary over five real read-only Codex
  tasks wrapped with `agentsight record`.
- `out/live-record-r113.md`: human-readable R113-live boundary and result table.
- `out/tag-stability-smoke.json`: local-only repeated-run tag stability smoke
  summary over hashed session/prompt/LLM fragments.
- `out/tag-stability-smoke.csv`: sanitized per-fragment tag outputs.
- `out/tag-stability-summary.md`: human-readable C6 smoke summary.
- `out/tag-adequacy-label-packet-r122.csv`: redacted C6 packet for collecting
  human adequacy labels. The packet includes the candidate one-word tag being
  judged; ordinary prompt wording such as exact-output instructions may remain
  in redacted previews, while home paths, secrets, emails, URL paths, and long
  ids are removed.
- `out/tag-adequacy-results-r124.json`: C6 adequacy scorer output. The current
  committed result is `human_labels_empty` with 300/300 candidate tags, not
  adequacy evidence.
- `out/tag-adequacy-results-r124.csv`: per-fragment normalized label state.
- `out/tag-adequacy-results-r124.md`: human-readable C6 adequacy scoring
  boundary.
- `out/tag-adequacy-label-join-r124.json`: C6 protocol manifest for joining
  two frozen blinded human-label sheets back into a scoring packet. The current
  committed manifest has no labeler inputs and does not support adequacy.
- `out/tag-adequacy-adjudication-template-r124.csv`: empty adjudication
  template. It is populated only for real rows where two completed labeler
  sheets disagree.
- `out/tag-adequacy-label-join-r124.md`: human-readable R124 join protocol.
- `out/user-task-benchmark.json`: C5 user-task benchmark bundle with sanitized
  tasks and source-view references.
- `out/user-task-answer-key.csv`: machine-readable answer key for the C5 tasks.
- `out/user-task-benchmark.md`: human-readable C5 task bundle summary.
- `out/user-task-participant-packets.json`: participant-facing C5 condition
  packets with no oracle fields.
- `out/user-task-participant-packets.md`: human-readable participant packet
  summary.
- `out/user-task-response-template.csv`: response CSV schema for collecting C5
  participant answers.
- `out/user-task-preregistration-r142.json`: frozen C5 analysis contract for
  the R142/R151 user-task benchmark. It records task counts, primary tasks,
  conditions, exclusion rules, response schema, scorer thresholds, and source
  hashes before participant collection.
- `out/user-task-preregistration-r142.md`: human-readable C5 preregistration
  summary.
- `out/user-task-results.json`: scored C5 participant results after running
  `score_user_task_results.py` on a real response CSV. It includes response
  contract status, diagnostic task-level deltas, and the paper-scale C5 claim
  gate; the current committed result is `participant_results_empty`, not
  user-utility evidence.
- `out/user-task-results.csv`: per-response scored C5 rows.
- `out/user-task-results.md`: human-readable C5 scoring summary.
- `out/artifact-usability-r160.json`: bounded R160 artifact-usability smoke,
  including expected-file checks, redaction, folded-total equality, clean/cached
  runtime, sanitized fixed-input manifest, input-equality check, local-report
  privacy boundary, and cached-rerun tagger stats.
- `out/osdi-gate-review-r181.md`: latest read-only OSDI gate review, confirming
  that R180 is syntax/stability evidence only and that C5/C6 remain the weak
  accept blockers.
- `out/prompt-tags.csv`: sanitized prompt hashes, previews, and one-word tags.
- `out/sessions.json`: per-session counts and tag summaries.

## What It Can And Cannot Show

It can show where sessions spend their work semantically, which prompt tags drive
repeated shell/edit/network/tool patterns, how much semantic tags add beyond a
non-semantic folded baseline, and where Codex and Claude differ on normalized
behavior diagnostics.

It cannot yet prove native full-run precise file/network side effects from real
sessions. `effect_lineage_smoke.py` proves the checker and folded-stack grammar
over an AgentSight-shaped fixture. R110 shows the same checker covering and
joining 182/318 raw effects from three real AgentSight DB exports after
`live_lineage_harness.py` adds a minimal agent-run envelope. R111 moves that
envelope into native `collector report export`: exported snapshots contain
session/tool rows and join the same 182/318 raw effects. R112 persists that
envelope into SQLite `sessions` and `tool_calls` rows on DB copies and verifies
persisted-only export. R113 implements capture-time `record -- <command>`
session/tool rows with `related_pid`. R113-live wraps five real read-only Codex
tasks with `agentsight record`, creates 5/5 capture-time sessions/tools, and
joins 508/508 raw effects by combining process-family and session-scoped
root-pid ancestry.
Broader task coverage, full-history exact integration, and user/task evidence
are still required before claiming complete developer utility.

## Test

```bash
python3 docs/visexp/run_pipeline.py --out docs/visexp/out
python3 -m unittest docs/visexp/test_semantic_tag_flamegraph.py
python3 docs/visexp/effect_lineage_smoke.py --fixture --out docs/visexp/out
python3 docs/visexp/verify_artifacts.py --out docs/visexp/out
python3 docs/visexp/tag_stability_smoke.py --out docs/visexp/out
python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r122.csv
python3 docs/visexp/r124_join_blinded_labels.py
python3 docs/visexp/r170_full_history_refresh.py
python3 docs/visexp/user_task_benchmark.py --out docs/visexp/out
python3 docs/visexp/r142_preregistration.py
python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke-fixed --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json --out docs/visexp/out/artifact-usability-r160.json
python3 docs/visexp/evaluate_artifacts.py --out docs/visexp/out
python3 docs/visexp/visual_summary.py --out docs/visexp/out
```

For a real AgentSight DB export converted to snapshot JSON, enrich it with:

```bash
python3 docs/visexp/live_lineage_harness.py \
  --snapshot path/to/export.json \
  --out /tmp/enriched.json \
  --scope-covered-effects
```

After collecting real C5 response rows:

```bash
python3 docs/visexp/score_user_task_results.py \
  --responses path/to/responses.csv \
  --assignments docs/visexp/out/user-task-assignments.csv \
  --out docs/visexp/out
```

The C5 scorer compares `semantic-stack` against `trace-tree`,
`event-count-proxy`, `flat-summary`, and `nonsemantic-stack`. It first validates
assignment/packet consistency and rejects duplicate, partial, or nonnumeric
real-response CSVs. Task-level paired deltas remain diagnostic; paper-scale
support requires the Holm-corrected participant/task/order fixed-effect gate in
`claim_analysis.claim_gate` to pass. Pilot-scale output should not be cited as
a user-utility result.

After collecting real C6 human label sheets:

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

The C6 join script refuses single-labeler input, checks that labeler sheets keep
the blinded column contract, writes disagreement rows into the adjudication
template, and only produces a joined scoring packet when both frozen sheets are
provided. LLM or subagent labels are not valid C6 evidence.
