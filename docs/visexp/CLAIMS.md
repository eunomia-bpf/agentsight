# Claim Ledger: AgentFlame

Last updated: 2026-06-18
Stage at update: claim-gate / supplement
Source/command: `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/live-network-r182.json`, `docs/visexp/out/model-benchmarks-r180.json`, `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json`, `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json`, `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json`, `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json`, `docs/visexp/out/long-tail-compaction-r205/long-tail-compaction-r205.json`, `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json`, `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json`, `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json`, `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json`, `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json`, `docs/visexp/out/production-react-display-r217/production-react-display-r217.json`, `docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json`, `docs/visexp/out/claim-readiness-r219/claim-readiness-r219.json`, `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/user-task-results.json`, `docs/visexp/out/artifact-usability-r160.json`, `docs/visexp/out/community-smoke-r200.json`, `docs/visexp/LONG_TAIL_COMPACTION.md`, `docs/visexp/out/osdi-gate-review-r204.md`
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

- 3B Qwen2.5 Instruct Q4_K_M through llama.cpp HTTP for the full local-history
  path.
- Local 0.6B-, 1B-, and 3B-class GGUFs for the R180 redacted-fragment
  syntax/stability benchmark.
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
- R180 ran the same 300 R122 fragments over local 0.6b, TinyLlama 1.1b, and 3b
  GGUFs with `--reasoning off`: 2700/2700 valid tags, per-model exact stability
  299/300, 279/300, and 285/300, and p95 latency 23/18/32 ms.

Status: supported for local syntax/latency over available 0.6B-/1B-/3B-class
models; partial for semantic adequacy.

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
- R189 adds an auditable canonical tag layer over the R170 full-history
  artifacts. It preserves total folded weights while reducing prompt-effect
  tags 263 -> 216 and system stacks 26,829 -> 26,067, showing that part of the
  observed long tail is a candidate display-noise reduction opportunity. It
  does not prove those raw tags are semantically redundant without human audit.
- R190 compares raw, alias-only, lexical-only, and profile-guarded variants and
  shows the profile-guarded policy is less aggressive than lexical-only
  consolidation: prompt-effect tags are 263/241/200/216 and LLM-event tags are
  1423/1392/868/1254 across those four variants. R190-score keeps the current
  unlabeled audit packet at `human_labels_empty`, so this remains mechanism and
  audit evidence rather than merge-quality evidence.
- R196 adds a long-tail governance packet over the same R170/R189 artifacts:
  231 existing canonical merges, 114 review-merge rows, 39 regeneration
  candidates, 2 contextual-split candidates, 1,241 kept rare distinct tags, and
  184 kept head tags. Review-required support is 0.938% for session tags,
  3.258% for prompt tags, and 1.376% for LLM-call tags. It is a conservative
  governance mechanism, not adequacy evidence.
- R201 stress-tests that governance policy over seven threshold and
  generic-vocabulary variants. Baseline review-required support is 1.926% of
  total support and the worst variant is 1.931%; high-tail threshold head
  stability drops to 65.217%, which is reported as display-policy risk.
- R202 exercises optional llama.cpp regeneration over the R196 regenerate/split
  candidates: 41/41 attempted rows produce grammar-valid one-word candidate tags, with
  0 invalid outputs. This proves the candidate-generation path runs locally, not
  that the regenerated tags are semantically better. Only the top-level R202
  summary and attempts CSV are public-oriented; the nested detail directory is
  local-audit-only until sanitized or excluded.
- R203 turns those candidates into a promotion-review protocol: 41 promotion
  rows, two blank reviewer sheets, 0 final labels, no canonical-map update, and
  all adequacy/quality/user/adoption gates false.
- R205 reports compaction metrics for this display layer: raw unique tag strings
  1,546 -> canonical unique tag strings 1,364, top-20 support coverage
  93.683% -> 95.186%, long-tail support 1.746%, review-required support
  1.926%, 0 R203 final labels, and `n/a` R190 over/under-merge rates.
- R209 exports the reversible display-map data layer: 1,811/1,811 raw rows have
  active display rows, 1,509 active display labels are exposed, 41 regenerated
  labels remain candidate-only, reviewed display-map diff rows are 0, and no
  rows are hidden under `other`.
- R213 verifies the raw/display/pending display-mode data layer over R209
  artifacts: all modes preserve 482,398 support, pending membership is unchanged,
  and drilldown membership matches the active display map. It is not a frontend
  renderer test.
- R214 adds the long-tail control loop: deterministic aliases may be active, but
  profile merges, regenerated labels, and split candidates remain pending until
  reviewed. The current control gates fail prompt review budget and high-tail
  head stability, so automatic long-tail cleanup is explicitly rejected. R214
  also emits a seven-row governance rollup preview and a versioned regeneration
  policy; both are candidate/control surfaces, not canonical-map updates.
- R215 compiles the frontend TypeScript display-mode consumer and runs a Node
  harness that renders R209 display-map/drilldown rows while cross-checking
  R213/R214 summary counts. It preserves support and membership across
  raw/display/pending modes, keeps candidates as pending overlays, and rejects
  corrupted drilldown plus candidate-as-active fixtures. This is not a browser
  DOM or usability result.
- R216 compiles the same display-mode consumer as browser ES modules and runs a
  temporary headless-browser DOM harness. It clicks raw/display/pending controls,
  verifies visible DOM counts, saves a screenshot and DOM dump, and rejects the
  same corrupted membership and candidate promotion fixtures. This is not the
  production React view, visual drilldown, or usability result.
- R217 builds the real Next static frontend and verifies that production
  `AgentFlameView` renders the default display panel from R209 artifacts:
  `display` mode, 1,748 buckets, 482,398 support, 3 mode buttons, and matching
  raw membership. This is still not a click-path, visual drilldown, or usability
  result.
- R218 uses synthetic review fixtures over real R209 pending rows to check the
  reviewed display-map update gate. It accepts 2 final consensus/adjudicated
  preview diff rows, rejects 4 unsafe rows, preserves 1,811 raw keys and
  482,398 support, creates 0 hidden `other` buckets, and keeps the canonical
  map unchanged. This is update-gate mechanics only, not promotion-quality
  evidence.
- R219 reads generated evidence artifacts and emits a claim/RQ readiness matrix.
  It records C5 as unsupported, C6 as partial syntax/stability only, C7 as
  partial, and `weak_accept_supported=false`; its P0 next rows are real R142
  participant returns and R124 human labels. It is an audit artifact, not a new
  claim-supporting result.
- R224 reruns the semantic-axis ablation on the R170 current full-history
  folded artifacts, aligning the system-axis denominator with R212's 183,714
  effect weight. R223 consolidates the RQ2 projection tradeoff across
  R224/R205/R209/R212: no-semantic is most compact but mixes 90.402% of
  system-effect weight, session-only still mixes 84.407%, prompt-only reduces
  mixed/residual mixed weight to 36.722%/7.485% and is the best single
  system-effect task axis, and full session+prompt is the audit projection.
  R223 also confirms R209's
  conservative display policy is alias-only-equivalent with 0.0% unreviewed
  active weight, while the hypothetical profile-guarded variant would activate
  2.532% unreviewed effect weight and therefore remains gated. This supports a
  pluggable projection framework claim, not user utility, tag adequacy, or
  merge/promotion quality.
- `docs/visexp/LONG_TAIL_COMPACTION.md` defines this as a versioned display
  overlay, not a raw-label rewrite: raw tags are immutable, regenerated tags
  are candidates only, and a reviewed display-map diff is required before any
  canonical-map update.
- R204 independently reviews the R203/R193/R194/R195/R202 integration and finds
  no must-fix overclaim, but keeps the project at Level 3/not weak accept
  because C5 participant responses and C6 human labels are still missing.

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
- R182 enables record-mode process `--trace-net` and reruns two loopback-task
  Codex commands. It joins 35/35 low-level `codex` process network rows with
  0 network orphans and 0/604 negative-control joins, but target-specific
  loopback or expected child-process network rows remain 0/0.
- The full Rust AgentFlame history characterization still uses agent-native
  session histories rather than full live exact-effect history.

Status: supported for the fixed command-mode Codex suite; partial broadly and
partial for network workloads. Complete full-history exact lineage, cross-repo
coverage, more agent types, target-specific child-process network capture,
full HTTP payload/URL reconstruction, and user utility remain unproven.

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
- R195 provides a post-collection ingestion path for real R142 responses, but
  the current default run is `awaiting_human_inputs`, has no input CSV, runs no
  scorer, and keeps `c5_supported=false`.

Status: unsupported as a user-outcome claim.

### C6: One-word tags are semantically adequate across models and reruns.

Needed:

- Human adequacy labels.
- Generic/noisy-tag rate.
- Controlled same-family model-size comparison only if the paper wants a model
  scaling claim rather than a local deployment smoke.

Current partial evidence:

- Full 3B run has 0 malformed tags.
- Some noisy tags exist, such as `agentsightsm`, `testcodex`, and
  `bashoutput`.
- R122 creates a redacted 300-fragment label packet.
- R123 provides 300/300 candidate tags from the 3B real-fragment benchmark.
- R180 provides local multi-model syntax/stability over the same fragments:
  2700/2700 valid tags and aggregate 863/900 exact-stable fragments.
- The R180 TinyLlama 1.1b run is a negative adequacy signal because most tags
  collapse to localization/localized variants.
- R124-scoring scores that packet without fabricating labels. The current
  output is `human_labels_empty` with 0 final labels, so adequacy remains
  unproven.
- R189 reduces tag fragmentation in a deterministic canonical display layer:
  prompt-row tags 328 -> 279, LLM-event tags 1423 -> 1254, and token stacks
  8569 -> 7661, while retaining raw tags in `canonical-tag-map-r189.csv`.
  This is a noise-control mechanism, not adequacy evidence.
- R190 writes an explicit merge-risk audit packet with 80 over-merge proxy rows
  and 80 under-merge proxy rows. The packet has blank audit labels, so it is
  ready for human review. R190-score reports `human_labels_empty`, 160 rows, 0
  final labels, and `canonicalization_quality_supported=false`, so it provides
  no correctness rate yet.
- R196 distinguishes long-tail outcomes instead of hiding them in an `other`
  bucket: kept rare distinct tags, regeneration candidates, contextual-split
  candidates, R189 existing merges, and R189 review-merge rows. This improves
  display-vocabulary auditability but still requires R124/R190 human labels
  before any semantic-quality claim, plus R203 promotion labels before any
  regenerated tag can enter the display map.
- R201 adds deterministic sensitivity evidence for that display policy. It
  keeps raw tags preserved and keeps adequacy/merge-quality gates false; it only
  reports review-required row/support counts, action movement, and head
  stability under policy variants.
- R202 adds candidate-only regeneration smoke evidence for the same display
  policy: 41/41 R196 regenerate/split rows produce grammar-valid one-word candidates,
  but the canonical map is not updated and adequacy/merge-quality gates stay
  false. Its detailed R196 rerun is local-audit-only because it can include
  path/profile buckets.
- R203 adds the corresponding promotion gate: regenerated labels can only become
  display-map candidates after paired/adjudicated human labels, and the default
  run has `human_labels_empty` with `long_tail_promotion_review_supported=false`.
- R209 confirms the active display map still exposes raw drilldown and keeps all
  regenerated labels inactive until a reviewed display-map diff exists.
- R213/R214/R215/R216/R217/R218 confirm the display-mode data layer,
  long-tail control gates, frontend renderer-model consumer, browser DOM
  harness, production default rendering, and reviewed-diff gate mechanics, but
  they still keep visual drilldown, adequacy, merge quality, promotion quality,
  utility, and map-update claims unsupported.
- R195 can join/score completed R124, R190, and R203 labeler sheets into an
  R195-specific scored directory after they are returned. The current default
  run has no label inputs, runs no scorer, and keeps
  `c6_adequacy_supported=false`,
  `canonicalization_quality_supported=false`,
  `long_tail_promotion_review_supported=false`, and
  `canonical_map_updated=false`.

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
- R200 adds a public-safe generated-fixture smoke. It creates a temporary
  synthetic Codex JSONL fixture instead of reading real `.codex` or `.claude`
  traces, starts a managed llama.cpp server, runs the Rust CLI once, then reruns
  the same explicit `--session-file`. The clean run made 5 llama.cpp tag calls;
  the cached rerun made 0 model calls with 5/5 cache hits; expected
  dashboard/folded/SVG/tag-cache artifacts existed; folded totals matched; no
  prompt previews leaked; the generated fixture was removed; and no new
  raw-trace-like git paths became dirty. The committed summary is
  `docs/visexp/out/community-smoke-r200.json`.

Status: partial. A bounded local artifact path and a public-safe generated
fixture smoke are verified. Fresh-clone setup on another machine,
public-release sanitization of real local reports, full write-set containment,
and community-developer feedback are not yet proven.

## Paper Wording Rule

Allowed current wording:

- "AgentFlame can generate semantic folded stacks over real local Codex/Claude
  histories."
- "In our local full-history run, removing semantic frames causes more than 90%
  of system observation weight to fall into mixed semantic buckets."
- "Local one-word tagging is syntactically feasible with the available
  0.6B-/1B-/3B-class llama.cpp models on the R122 redacted fragment sample."
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
- "R182 validates the record-mode `--trace-net` implementation path: 35/35
  low-level `codex` process network rows joined and 0/604 negative-control
  effects were attributed, while target-specific loopback child-process network
  capture remains unproven."
- "R142 provides a ready but empty developer-task benchmark packet and scorer;
  no C5 user-outcome evidence exists until real participant responses pass the
  paper-scale gate."
- "R160 verifies an auditable bounded local artifact path with fixed historical
  sessions, a sanitized input manifest, expected output files, redacted
  previews, and a fully cached rerun."
- "R200 verifies a public-safe generated-fixture AgentFlame run with managed
  llama.cpp tagging, expected artifacts, redacted committed summary, and a fully
  cached fixed-input rerun."

Disallowed current wording:

- "AgentFlame proves developers debug faster."
- "AgentFlame is already a validated community developer tool."
- "AgentFlame has validated native full-run exact file/network provenance."
- "AgentSight captures complete session/tool ancestry for arbitrary histories."
- "One-word tags are semantically correct."
- "AgentFlame is the first flamegraph for agents."
- "AgentFlame is already a verified community-ready tool."
