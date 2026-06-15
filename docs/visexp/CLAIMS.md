# Claim Ledger: AgentFlame

Last updated: 2026-06-15
Stage at update: claim-gate / supplement
Source/command: `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/model-benchmarks-r123.json`, `docs/visexp/out/user-task-results.json`, `docs/visexp/out/artifact-usability-r160.json`
Completeness: partial

This ledger separates current evidence from OSDI-level claims. The paper should
present AgentFlame as semantic attribution of agent system effects, not as a
generic agent flamegraph.

## Supported By Current Full Run

### C1: AgentFlame generates semantic folded stacks over real local agent histories.

Scope:

- Local AgentSight repository history on this machine.
- Codex and Claude JSONL sessions readable by the current user.
- Agent-native tool/system reconstruction, not live kernel-level exact effects.

Evidence:

- 205 sessions analyzed: `codex=78`, `claude=50`, `claude-subagent=77`.
- 130,632 raw tool events and 90,930 raw LLM events.
- 167,005 system observations collapsed into 24,295 unique semantic system
  stacks.
- Folded totals match summary totals for semantic, nonsemantic, prompt, session,
  and LLM-token projections.
- Dashboard, SVGs, folded stacks, and redacted `agentflame.json` were generated
  under `.agentsight/agentflame/latest`.

Status: supported as a local-history artifact claim.

### C2: Local one-word LLM tagging is syntactically feasible for session, prompt, and LLM-call frames.

Scope:

- 3B Qwen2.5 Instruct Q4_K_M through llama.cpp HTTP.
- Temperature 0, one-word grammar, retry-on-invalid.

Evidence:

- 93,598 tag requests.
- 64,297 cache hits.
- 29,302 llama.cpp HTTP calls.
- 29,301 successful final tags.
- 0 final tag failures.
- 2,463 prompt rows, 303 unique prompt tags, 0 invalid prompt tags.
- 90,930 LLM-call tags, 1,250 unique LLM-call tags, 0 invalid LLM-call tags.

Additional evidence:

- R123 ran 300 real redacted fragments from R122 through the available 3B
  llama.cpp server with 3 identical repeats each: 900/900 valid tags, p95
  request latency 31 ms after load, and 285/300 exact-stable fragments.

Status: supported for 3B syntax/latency; partial for model-size coverage and
adequacy.

### C3: Semantic frames expose task-effect mixtures hidden by nonsemantic and flat summaries.

Scope:

- Same full local-history workload as C1.
- Mechanism-level information gain, not user-outcome proof.

Evidence:

- Nonsemantic folded stacks, with session/prompt frames removed, produce 4,209
  mixed buckets covering 150,670 observations, 90.219% of system weight.
- Flat effect buckets produce 4,051 mixed buckets covering 151,590 observations,
  90.770% of system weight.
- High-volume examples include `git read`, `cargo test`, `python3 process`,
  `docker process`, and `tool write/process` effects that split across
  `refactor`, `review`, `design`, `research`, `analyze`, and `test` regions.
- R131 semantic-axis ablation preserves total weight for every projection and
  shows prompt tags carry most system-effect separation: no-semantic mixes
  90.219% of full semantic bucket weight, session-only leaves 84.180%,
  prompt-only leaves 37.687%, and session+prompt leaves 0.000% by construction.

Status: supported as a partitioning claim.

## Diagnostic Only

### D1: Semantic stacks characterize local Codex/Claude behavior differences.

Evidence:

- Full run includes Codex and Claude/Claude-subagent cohorts.
- Command summary and semantic stacks reveal different tool/effect distributions.

Limitation:

- The histories are observational and unpaired. They are not the same tasks on
  the same repository state. This cannot support a causal "Codex vs Claude"
  benchmark.

Status: diagnostic only.

### D2: Token projections help local accounting.

Evidence:

- `semantic-token`, `session-token`, `prompt-token`, and `llm-token` views are
  generated and total weights match their source totals.

Limitation:

- Codex and Claude token fields are heterogeneous. Some token weights are
  estimates. Token projections should not be used for cross-agent cost claims
  until normalization is audited.

Status: diagnostic only.

## Supported With Scope Limits

### C4: AgentSight exact system effects preserve semantic attribution value.

Needed:

- Live AgentSight snapshots from real sessions.
- Exact `tool_call -> shell -> child process -> file/network effect` ancestry.
- Join coverage and in-scope orphan-rate metrics.
- Comparison against agent-native proxy stacks.

Current evidence:

- `docs/visexp/effect_lineage_smoke.py` validates the checker over an
  AgentSight-shaped fixture.
- R110 runs the checker on three real AgentSight SQLite DB exports after
  `docs/visexp/live_lineage_harness.py` adds a minimal agent-run envelope around
  detected Codex/Claude root processes. The low-level process/file/network
  effects are not synthesized.
- R110 covers and joins 182/318 raw effects, for 57.233% raw coverage. Within
  the covered scope it validates 182/182 effects with 0 orphans and 100.0%
  in-scope join rate. It also records 136 out-of-scope raw effects outside
  detected agent roots.
- R111 moves the same minimal agent-run envelope into native `collector report
  export`: exported snapshots now contain 3 sessions and 3 tool calls across the
  same three DBs, and the checker joins 182/318 raw effects. The orphan count
  remains 136, so this is native-export smoke evidence, not full C4 proof.
- R112 runs explicit `collector report materialize-observed` backfill on copies
  of the same DBs, writes 3 SQLite `sessions` rows and 3 `tool_calls` rows, then
  exports with `--no-observed-projection`. The persisted-only snapshots still
  join 182/318 raw effects and leave 136 orphans.
- R113 implements capture-time `record -- <command>` session/tool rows with
  `view_source=record_capture_time_agent_envelope` and verifies the row shape in
  a temp SQLite DB.
- R113-live runs five real read-only `codex exec` tasks under `agentsight
  record`. It creates 5/5 capture-time sessions/tools and joins 508/508 raw
  effects; 258 effects join through process-family ancestry and 250 through
  `root_pid_time_window`.
- Full R114 runs 20 real Codex command-mode tasks under `agentsight record`,
  including read-only, edit, test/debug, dependency, failure/retry, and
  disposable-workspace write tasks. It observes negative controls in all 20
  tasks, joins 1273/1273 in-scope effects, reports 100.0% precision and
  100.0% recall, attributes 0/3170 observed negative-control effects, and
  passes child-depth/path/redaction analysis.
- The full Rust AgentFlame history characterization still uses agent-native
  session histories rather than full live exact-effect history.

Status: supported for the fixed command-mode Codex suite; partial broadly.
Complete full-history exact lineage, cross-repo coverage, more agent types, and
user utility remain unproven.

## Not Yet Supported

### C5: Semantic effect flamegraphs improve developer task outcomes.

Needed:

- Head-to-head task benchmark against trace tree, event-count proxy, flat
  summary, nonsemantic folded stack, and semantic folded stack. A true
  span-duration flamegraph remains a separate future baseline if reconstructed
  from timestamps.
- Metrics: answer accuracy, task time, false positives, confidence, and
  repeated-effect recall.

Current partial setup:

- R142-packet generated 14 blinded forensic tasks from R114/R123/R131/full-run
  artifacts: 8 primary utility tasks, 6 limitation/comprehension tasks, five
  conditions (`trace-tree`, `event-count-proxy`, `flat-summary`,
  `nonsemantic-stack`, `semantic-stack`), 70 participant packets, hidden answer key, P01-P05
  counterbalanced assignment template, recursive leak check, and same-event
  `slice_id` fairness across conditions.
- R142-scoring validates response contract, rejects duplicate/partial/bad
  measurement CSVs, keeps task-level deltas as diagnostics, and gates
  paper-scale C5 with Holm-corrected participant/task/order fixed-effect blocked
  permutation tests.
- Current scored output is `participant_results_empty`,
  `c5_supported=false`, and `pilot_ready=false`.

Status: unsupported as a user-outcome claim.

### C6: One-word tags are semantically adequate across models and reruns.

Needed:

- 0.6B/1B/3B model comparison over the same fragments.
- Repeated-run stability.
- Human adequacy labels.
- Generic/noisy-tag rate.

Current partial evidence:

- Full 3B run has 0 malformed tags.
- Some noisy tags exist, such as `agentsightsm`, `testcodex`, and
  `bashoutput`.
- R122 creates a redacted 300-fragment label packet.
- R123 provides 300/300 candidate tags from the 3B real-fragment benchmark.
- R124-scoring scores that packet without fabricating labels. The current
  output is `human_labels_empty` with 0 final labels, so adequacy remains
  unproven.

Status: partial. Syntax is strong; adequacy is unproven.

### C7: AgentFlame is practical as an open-source developer tool.

Needed:

- Fresh-clone or clean-worktree run using documented commands.
- llama.cpp server/model setup or connection instructions.
- Expected output files and dashboard path.
- Runtime/cache summary.
- Artifact hygiene check: no raw traces committed, raw-trace git status remains
  clean, generated report path stays under `.agentsight/agentflame`, and skipped
  or unreadable traces are explicit.

Current partial evidence:

- The Rust CLI can generate `.agentsight/agentflame/latest/agentflame.json`,
  folded stack files, SVGs, and an HTML dashboard over this local workspace.
- R160 passed a bounded fixed-session smoke using 8 historical Codex sessions
  and LLM-call tags. The clean run wrote
  `.agentsight/agentflame/r160-smoke-fixed`, made 60 uncached llama.cpp calls
  over 76 tag requests, and took 1.64 s. The cached rerun reused `tags.json`,
  served 76/76 tag requests from cache, made 0 LLM calls, and took 0.11 s.
- `docs/visexp/artifact_usability_r160.py` verified expected artifacts, folded
  totals, redacted previews, generated report path containment, 0 dirty
  raw-trace-like paths, a sanitized fixed-input manifest
  (`11ae4fb2c96a2d1478aa1525`), clean/cached input equality, and the
  cached-rerun gate. The audit result is
  `docs/visexp/out/artifact-usability-r160.json`.
- The local `.agentsight/agentflame/*/agentflame.json` reports are private
  workstation artifacts because they include local trace roots and session file
  metadata. The committed/public artifact is the redacted R160 audit JSON, not
  those local reports.
- A broader 36-session discovery run was informative but not used as the final
  cache gate: its clean run took 173.05 s for 9,600 uncached llama.cpp calls,
  and its rerun made 34 new model calls because the live Codex session changed
  between discovery runs. Fixed `--session-file` inputs are therefore required
  for a meaningful cached-rerun artifact test.

Status: partial. A bounded local artifact path is verified; fresh-clone setup,
stable default sampling, and community-developer reproducibility are not yet
proven.

## Paper Wording Rule

Allowed current wording:

- "AgentFlame can generate semantic folded stacks over real local Codex/Claude
  histories."
- "In our local full-history run, removing semantic frames causes more than 90%
  of system observation weight to fall into mixed semantic buckets."
- "Local one-word tagging is syntactically feasible with a 3B llama.cpp model."
- "On three real AgentSight DB exports, the C4 checker covers and joins 182/318
  raw effects; within that covered scope it joins 182/182 effects after a
  harness-synthesized agent-run envelope is added."
- "Native `collector report export` now emits export-derived session/tool
  envelopes for the same three DBs, joining 182/318 raw effects."
- "Explicit `collector report materialize-observed` backfill can persist those
  envelopes into SQLite `sessions` and `tool_calls` rows on DB copies; persisted-only
  export still joins 182/318 raw effects."
- "R114 validates exact semantic-effect lineage for a fixed 20-task Codex
  command-mode suite: 1273/1273 in-scope effects joined, 100.0% precision and
  recall, and 0/3170 negative-control effects attributed."
- "R142 provides a ready but empty developer-task benchmark packet and scorer;
  no C5 user-outcome evidence exists until real participant responses pass the
  paper-scale gate."
- "R160 verifies an auditable bounded local artifact path with fixed historical
  sessions, a sanitized input manifest, expected output files, redacted
  previews, and a fully cached rerun."

Disallowed current wording:

- "AgentFlame proves developers debug faster."
- "AgentFlame is already a validated community developer tool."
- "AgentFlame has validated native full-run exact file/network provenance."
- "AgentSight captures complete session/tool ancestry for arbitrary histories."
- "One-word tags are semantically correct."
- "AgentFlame is the first flamegraph for agents."
- "AgentFlame is already a verified community-ready tool."
