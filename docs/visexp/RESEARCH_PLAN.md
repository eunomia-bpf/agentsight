# AgentFlame Research Plan

Last updated: 2026-06-15
Stage at update: supplement / experiment-design plus completed full local-session characterization
Source/command: R170 full-history refresh, R187 launch package generation, R189 canonical tag consolidation, R190 merge-risk audit, R190-score empty-label gate, R196 long-tail governance, R201 long-tail sensitivity, R202 candidate regeneration smoke, R203 promotion gate, R205 compaction metrics, R209 reversible display-map contract, R211 stack examples, R212 display-compaction ablation, R213 display-mode drilldown data-layer smoke, R214 long-tail control loop, R215 frontend renderer-model smoke, R216 browser DOM harness smoke, R217 production React display smoke, R218 display-map update gate, R219 claim-readiness gap gate, R193 human-evidence collection package, R195 human-evidence ingestion pipeline, R207 human-evidence launch-readiness audit, R200 public-safe community smoke, `docs/visexp/LONG_TAIL_COMPACTION.md`, and R204 read-only gate review; latest analysis commands `python3 docs/visexp/r195_human_evidence_pipeline.py`, `python3 docs/visexp/r207_human_launch_readiness.py`, `python3 docs/visexp/r200_community_smoke.py`, `python3 docs/visexp/r201_long_tail_sensitivity.py`, `python3 docs/visexp/r202_long_tail_regeneration_smoke.py --regenerate-limit 50 --load-timeout 240 --llama-timeout 60`, `python3 docs/visexp/r203_long_tail_promotion_gate.py`, `python3 docs/visexp/r205_long_tail_compaction_metrics.py`, `python3 docs/visexp/r209_reversible_display_map.py`, `python3 docs/visexp/r211_stack_examples.py`, `python3 docs/visexp/r212_display_compaction_ablation.py`, `python3 docs/visexp/r213_display_mode_drilldown_smoke.py`, `python3 docs/visexp/r214_long_tail_control_loop.py`, `python3 docs/visexp/r215_frontend_renderer_mode_smoke.py`, `python3 docs/visexp/r216_browser_dom_mode_smoke.py`, `python3 docs/visexp/r217_production_react_display_mode_smoke.py`, `python3 docs/visexp/r218_display_map_update_gate.py`, `python3 docs/visexp/r219_claim_readiness_gap_gate.py`, and `docs/visexp/out/osdi-gate-review-r204.md`
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

### Reviewer-Facing RQ Gate Summary

The reviewer-facing thesis is: AgentFlame is a semantic attribution system for
agent system effects, not a new agent trace UI. Every RQ therefore tests one
link in the chain:

```text
sessionTag;promptTag;llmcall/tool;process*;effect
```

| RQ | What It Must Prove | Current Evidence | Falsifying Result | Next Executable Gate |
|----|--------------------|------------------|-------------------|----------------------|
| RQ1 feasibility/cost | A local small LLM can cheaply assign one-word semantic frames to real session, prompt, and LLM-call contexts. | R170 full-history refresh; R180 0.6B/1B/3B-class syntax/stability with 2700/2700 valid tags and p95 18-32 ms. | Tagger failures, invalid tags, unacceptable latency, cache instability, or only toy/synthetic traces. | Keep as mechanism-supported; rerun only after tagger or parser changes. |
| RQ2 semantic partitioning | Semantic frames split system-effect buckets that trace trees, span-duration views, and flat process summaries merge. | R131 total-preserving ablation: no-semantic mixes 90.219% of full semantic bucket weight; prompt-only reduces residual mixing to 7.526%; R189-R205 quantify display compaction without changing raw tags; R209 exports the reversible display map and raw drilldown contract; R211 packages label distributions plus concrete process/prompt split examples; R212/R213/R214 cover conservative display policy, data-layer drilldown, and long-tail control gates; R215/R216/R217 exercise renderer-model, browser DOM, and production default rendering; R218 checks the reviewed-diff gate with synthetic review fixtures. | Nonsemantic/flat baselines answer the same repeated-effect questions, or semantic tags create visual noise without reducing mixed buckets. | Add C5 task outcomes; keep R205/R209/R211/R212/R213/R214/R215/R216/R217/R218 as mechanism, compaction, and figure-input evidence only. |
| RQ3 exact lineage | System effects inherit semantic ancestry through deterministic `tool_call -> shell -> process* -> effect`, not LLM guesses. | R114 fixed 20-task command-mode suite joins 1273/1273 in-scope effects with 100.0% precision/recall and 0/3170 negative-control joins; R182 is only low-level record-mode network smoke. | Negative controls inherit agent ancestry, in-scope effects become orphaned, or network/file claims depend on missing target-specific rows. | R191 target-specific network lineage hardening before broad network claims. |
| RQ4 developer utility | Developers answer forensic questions faster or more accurately with semantic effect stacks than with named baselines. | R142/R187/R193/R195/R207 make the packet, launch materials, response contract, scorer, and return-file plan executable; no responses exist. | No accuracy/time gain, higher false positives, invalid response contract, or only pilot-scale evidence. | Collect real R142 pilot responses; then R151 paper-scale or explicitly scoped expert study. |
| RQ5 tag adequacy | One-word tags are adequate navigation labels, not merely syntactically valid. | R180 supports syntax/stability; R251 supports behavior association beyond a session-preserving shuffle null; R124/R190/R203 label protocols are launch-ready but empty. | Adequacy below threshold, high generic/misleading rate, low agreement, or LLM/subagent labels substituted for humans. | Collect R124 adequacy labels and R190/R203 review labels; score through R195. |
| RQ6 artifact/community | A community developer can run the tool and reproduce the core views without internal harness knowledge. | R160 fixed-session smoke and R200 public-safe generated-fixture smoke pass. | Fresh clone fails, raw traces leak, setup depends on private state, or external developers cannot reproduce outputs. | External fresh-clone run plus public setup/write-set audit. |

This table is intentionally stricter than the current paper draft. RQ1-RQ3 can
support a mechanism paper today. RQ4 and RQ5 are the weak-accept gates. RQ6
improves artifact credibility but cannot compensate for missing C5/C6 outcome
evidence.

R219 now encodes the same gate mechanically. It reads only generated artifacts,
emits claim/RQ readiness CSVs, and keeps `weak_accept_supported=false` because
C5 has 0 participant responses and C6 has 0 final human adequacy labels. Its
next-experiment table makes the first two rows P0: `R142-pilot-return` and
`R124-labels-return`. This is useful as an audit and planning artifact, but it
does not replace R184/R195 or any human evidence.

### Reversible Long-Tail Compaction Boundary

The open one-word vocabulary is part of the research design, not an accident:
it lets repository-specific intent surface instead of forcing every prompt into
a fixed ontology. The cost is long-tail fragmentation. AgentFlame should handle
that fragmentation with a reversible display overlay, not by rewriting history.

The reviewer-facing contract is:

```text
raw_tag -> governance_action -> optional regenerated_tag ->
promotion_review -> reviewed display-map diff -> canonical_tag
```

Raw tags remain immutable and drill-down-visible. The default folded view may
use versioned canonical labels to improve aggregation, but every aggregate must
be able to expose its raw tags, support mass, top processes/effects/path
buckets, and map version. Rare but specific tags stay visible; generic or noisy
tags are routed to review, regeneration, or split candidates; regenerated tags
remain candidates until paired/adjudicated review accepts them.

R214 now turns this into an explicit control loop. The default display remains
active-alias-only with pending overlays: 63 deterministic alias rows are active,
168 profile-merge candidates and 41 regenerated/split candidates remain pending,
and 323 rows require review. The control loop now also emits a seven-bucket
rollup preview that partitions all 1,811 raw-tag rows and 482,398 support by
governance state, plus a versioned regeneration policy keyed by
`dimension;raw_tag;profile_hash;generator_version`. The rollup preview is a
maintenance and pending-review surface, not default flamegraph membership. The
control loop deliberately fails `prompt_review_budget` and
`head_stability_under_high_tail_threshold`, so the current evidence argues
against automatically merging the prompt tail or raising tail thresholds merely
to make the flamegraph smaller.

R215 checks that the frontend TypeScript display-mode consumer obeys the same
boundary at the renderer-model layer. It compiles the module and runs a Node
harness that preserves raw/display/pending support, keeps pending membership
unchanged, and rejects corrupted drilldown membership plus candidate-as-active
promotion. It is still not a browser DOM or usability result.

R216 then checks the same contract in a real headless browser. It compiles the
display-mode module as browser ES modules, serves a temporary DOM harness, clicks
raw/display/pending controls, verifies visible counts, and writes a screenshot
and DOM dump. This closes the browser DOM harness gap, but it still does not
exercise the production React `AgentFlameView`, visual drilldown, developer
utility, merge quality, or tag adequacy.

R217 checks the default production React path: the real Next frontend renders
`AgentFlameView` from R209 artifacts in headless Chrome with 1,748 display
buckets and 482,398 support. It is a rendering smoke only; it does not click the
production controls or exercise visual drilldown.

R218 checks the versioned display-map update gate. Synthetic review fixtures
over real R209 pending rows produce 2 accepted preview diffs and 4 rejected
unsafe rows while preserving 1,811 raw keys and 482,398 support. This is a gate
mechanism for future reviewed updates, not evidence that any candidate label is
correct.

This boundary matters for the OSDI argument. It lets the paper claim measurable
aggregation behavior, such as R205's raw/canonical unique-tag reduction and
top-K coverage change, without claiming semantic adequacy or merge quality.
Those stronger claims remain gated on R124 adequacy labels, R190 merge-risk
labels, and R203 promotion labels.

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
- R189 canonicalization is useful tag-noise control, but it is not semantic
  adequacy evidence. High-support canonical merges should still be audited by
  humans or a frozen label protocol before being treated as correct intent
  labels.
- R190 produces that audit protocol, not the labels: a 160-row merge-risk packet
  with 80 over-merge proxy rows and 80 under-merge proxy rows. It also shows
  lexical-only consolidation is much more aggressive than the current
  profile-guarded policy, especially for LLM-event tags (868 vs 1254 unique
  tags). R190-score now adds the two-labeler/adjudication scorer and currently
  reports `human_labels_empty`, 0 final labels, and
  `canonicalization_quality_supported=false`. Human labels are still required
  to estimate over-merge and under-merge rates.
- R196 adds a long-tail governance packet, not a new correctness claim. It
  classifies raw tags into existing canonical merges, review merges,
  regeneration candidates, contextual-split candidates, kept rare distinct
  tags, and kept head tags. It keeps semantic heads even when their system
  profiles are multi-peak, and routes only generic/noisy tags to regeneration
  or split review by default.
- R201 stress-tests that R196 policy over seven threshold and generic-vocabulary
  variants. Review-required support stays nearly flat, from the baseline 1.926%
  to the worst observed 1.931%, but the higher-tail-threshold variant drops
  baseline-head stability to 65.217%. This strengthens the governance argument
  while exposing a real display-policy sensitivity risk.
- R202 exercises the optional regeneration branch rather than just describing
  it: 41/41 R196 regenerate/split candidates produce grammar-valid one-word outputs
  through a local llama.cpp server, with 0 invalid outputs. This is an
  executability smoke for candidate generation; no generated tag is accepted
  without human review. The top-level R202 summary/attempts are
  public-oriented; nested `r196-with-regeneration/` details are local-audit-only
  until sanitized or excluded.
- R203 adds that human-review boundary as an executable promotion gate: it
  consumes only the public-oriented R202 attempts CSV, writes a 41-row promotion
  packet and two blank reviewer sheets, and records 0 final labels with
  `long_tail_promotion_review_supported=false` and `canonical_map_updated=false`.
- The mechanism-level design is now centralized in
  `docs/visexp/LONG_TAIL_COMPACTION.md`: raw tags remain immutable, canonical
  maps are versioned display overlays, long-tail rows take fixed governance
  actions, regeneration receives only a bounded profile packet, and promotion
  requires paired/adjudicated review plus a later display-map diff. The
  paper-level metrics should include raw/canonical unique tags, top-K coverage,
  long-tail support mass, review-required support mass, head stability,
  regeneration validity/change rate, promotion acceptance rate, and R190
  over-merge/under-merge rates after labels exist.
- R205 computes those metrics over existing generated artifacts: raw unique tag
  strings 1,546 -> canonical unique tag strings 1,364, top-20 support coverage
  93.683% -> 95.186%, long-tail support 1.746%, review-required support 1.926%,
  R202 regeneration 41/41 grammar-valid candidates, R203 0 final labels, and
  R190 over/under-merge rates still `n/a`. It supports compaction measurement
  only, not semantic adequacy, merge quality, or developer utility.
- R209 materializes the reversible display-map layer that R205 only measures:
  1,811/1,811 raw tags have active display rows, 1,509 active display labels
  exist, 63 deterministic alias rows are active display merges, 168
  lexical/profile merges remain pending merge candidates, 41 regenerated labels
  remain candidate-only, 0 reviewed display-map diff rows exist, 0 rows are
  hidden under `other`, drilldown support is preserved, and each display bucket
  stores complete raw-tag membership. This is the UI/data contract for
  compaction, not a quality claim or a canonical-map update.
- R212 adds a display-compaction ablation over the R170 semantic-system folded
  stacks. It conserves 183,714 total system-effect weight across all variants:
  raw has 26,829 stacks, alias-only and R209 conservative display both have
  26,612 stacks, and the hypothetical profile-guarded-candidate-applied view has
  26,067 stacks. That hypothetical view would activate unreviewed profile merges
  over 2.532% of total system-effect weight. R212 therefore supports the
  conservative display-policy choice, not merge correctness or developer
  utility.
- R211 materializes the RQ2 examples and figure inputs: `rg` spans 176 prompt
  tags, `sed` spans 180, `git` spans 147, and `cargo` spans 68; the concrete
  collapsed key `process:git;effect:read;status:ok` has 116 prompt tags and
  only 24.977% top-prompt share, while `process:cargo;effect:test;status:ok`
  has 48 prompt tags and 68.05% non-top-prompt weight. This is evidence that
  process summaries hide semantic mixtures, not evidence that users benefit or
  that labels are semantically adequate.
- R193 packages the blank R124, R190, and R203 labeler sheets and points to the
  frozen R142 launch package. This removes a distribution/logistics gap for
  adequacy, merge-risk, promotion-review, and user-task collection, but it
  still records 0 labels and 0 participant responses.
- R195 adds the post-collection ingestion/scoring entry point. The default run
  has no returned CSV files in its inbox, reports `awaiting_human_inputs`, runs
  no scorers, and keeps C5/C6/canonicalization gates false. When real files are
  supplied, it scores complete R142/R124/R190/R203 groups into R195-specific
  output directories without overwriting canonical empty gates. R203 can only
  support a long-tail promotion-review gate; it does not update the canonical
  map or substitute for C5/C6 evidence.
- R207 audits the launch handoff: five R142 participant packets, a blank 70-row
  response template, two 300-row R124 sheets, two 160-row R190 sheets, two
  41-row R203 sheets, and exact R195 return-file names are present and valid.
  This supports only collection readiness; it still records no participant
  responses and no human labels.

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
- R189 adds a canonical display layer over the R170 full-history artifacts
  without mutating raw tags or raw traces. It preserves folded totals while
  reducing prompt-effect tags 263 -> 216, prompt-row tags 328 -> 279,
  LLM-event tags 1423 -> 1254, system stacks 26,829 -> 26,067, and token stacks
  8569 -> 7661. This quantifies a candidate display-noise reduction proxy, not
  proof that the merged tags are semantically redundant.
- R190 compares raw, alias-only, lexical-only, and current profile-guarded
  consolidation. Prompt-effect tag counts are 263/241/200/216; LLM-event tag
  counts are 1423/1392/868/1254; system-stack counts are
  26,829/26,612/25,985/26,067. The result positions profile-guarding as a
  conservative risk-control choice, not as a correctness proof. R190-score
  confirms that the current audit state remains `human_labels_empty`; no
  over-merge or under-merge rate is reportable yet.
- R196 makes the remaining long-tail policy explicit: 231 existing canonical
  merges, 114 review-merge rows, 39 regeneration candidates, 2 contextual-split
  candidates, 1,241 kept rare distinct tags, and 184 kept head tags.
  Review-required support is 0.938% for session tags, 3.258% for prompt tags,
  and 1.376% for LLM-call tags.
- R201 reports policy sensitivity on the same R170/R189 inputs: seven variants,
  baseline review-required support 1.926%, worst review-required support
  1.931%, lower/higher tail thresholds moving long-tail support from 0.921% to
  3.030%, and high-tail threshold head stability 65.217%. It keeps adequacy,
  canonicalization-quality, and developer-utility gates false.
- R202 reports optional regeneration-path executability on the same policy
  layer: 41/41 regenerate/split candidates attempted, 41 grammar-valid one-word
  candidate tags, 0 invalid outputs, 32 changed from raw tag, 9 unchanged, and
  no canonical-map update. It keeps adequacy, canonicalization-quality,
  developer-utility, and community-adoption gates false; only top-level R202
  outputs are public-oriented by default.
- R203 reports the paired-review promotion protocol for those candidates:
  41 packet rows, 0 final labels, no canonical-map update, and no adequacy or
  merge-quality support.

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
- R200 verifies a public-safe generated-fixture artifact path in
  `docs/visexp/out/community-smoke-r200.json`: the script uses a temporary
  synthetic Codex fixture, reads no real `.codex` or `.claude` traces, removes
  the fixture after the run, makes 5 clean llama.cpp tag calls, then reruns with
  0 model calls and 5/5 cache hits. The committed summary records 0
  non-redacted prompt previews and no raw-trace dirty paths.
- R170 records a current full-history refresh in
  `docs/visexp/out/full-history-r170.json`: 325 sessions, 142,468 raw tool
  events, 114,837 raw LLM events, 183,714 system observations, 35,136 fresh
  llama.cpp tag calls, and folded-total integrity. The private generated report
  stays under `.agentsight/agentflame/r170-full-current`.
- Raw local traces are not committed. The full run records skipped unreadable
  files instead of requiring elevated privileges.

Remaining gap:

- There is still no external-machine fresh-clone or clean-install smoke that a
  community developer could rerun end-to-end with public setup docs. R160 and
  R200 are local artifact-hygiene checks, not community adoption results. They
  also do not prove public-release readiness of real local `.agentsight`
  reports or full pre/post write-set containment. This is not a core
  scientific result, but it is important for turning the research prototype
  into a credible open-source project.

## Claim Ledger Snapshot

| ID | Claim | Current Status | Evidence Needed For OSDI |
|----|-------|----------------|--------------------------|
| C1 | AgentFlame can generate semantic folded stacks and dashboards over real local agent histories. | supported | verifier for full run and reproducibility script |
| C2 | Local one-word LLM tagging is feasible for session/prompt/LLM-call contexts. | supported for local 0.6B-/1B-/3B-class syntax/latency; partial for adequacy | human adequacy labels; controlled same-family scaling only if claimed |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic and flat summaries. | supported as mechanism | stronger examples and task benchmark |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | supported for fixed command-mode suite; partial broadly and partial for target-specific network workloads | cross-repo/full-history exact integration, target-specific network workloads, broader agent coverage, and user-task outcomes |
| C5 | Developers answer debugging/audit questions better with semantic effect flamegraphs. | unsupported; R142 packet/scorer/preregistration and R187 launch package exist | user/task benchmark responses with valid response contract passing the Holm-corrected paper-scale C5 gate |
| C6 | One-word tags are stable and adequate enough for navigation. | partial; R180 syntax/stability exists, R251 behavior association exists, R124 scorer/join protocol exists, labels are empty | human adequacy labels with thresholds |
| C7 | The approach is practical as an open-source developer tool. | partial; R160 bounded fixed-input smoke and R200 public-safe generated-fixture smoke pass | external-machine fresh clone, public docs, real-report sanitization, full write-set audit, and external developer feedback |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Full-history run over real local sessions, folded outputs, verifier coverage, no raw-trace commit | B1, B7 | Tagger/report cannot complete without manual trace editing, raw trace leaks into committed artifacts, or folded totals do not match reports | "AgentFlame generated semantic folded-stack artifacts for this repository's local histories." |
| C2 | Local llama.cpp annotation validity, latency, stability, cache behavior, and explicit adequacy boundary | B1, B5 | Small models frequently emit invalid tags, unstable tags break navigation, or human adequacy labels reject tags | "Local models can produce syntactically valid one-word navigation tags on this workload; adequacy is bounded by R124." |
| C3 | Same observations projected into semantic and nonsemantic baselines with total-weight equality and mixed-bucket reduction | B2, B6 | Removing semantic frames does not increase mixing, or prompt/session axes fail to isolate any real system-effect buckets | "Semantic frames partition system-effect buckets that traditional summaries merge in this repository." |
| C4 | Live AgentSight lineage with negative controls, process ancestry, file/network effects, and scoped precision/recall | B3 | In-scope recall below threshold, negative controls join, target-specific network rows remain absent for a network claim, or redaction/path checks fail | "Exact lineage is supported for the fixed command-mode suite; broad and target-specific network claims remain partial." |
| C5 | Preregistered developer task benchmark against named baselines with accuracy/time/false-positive/confidence outcomes | B4 | Semantic view does not improve accuracy or time, increases false positives, fails response contract, or only pilot-scale evidence exists | "The task benchmark is a protocol or pilot result only; no paper-scale user-utility claim." |
| C6 | Two independent human label sheets plus adjudication and scorer thresholds over R122/R124 fragments | B5 | Adequacy below threshold, high generic/misleading rate, low agreement without adjudication, or only LLM/subagent labels exist | "Tags are lossy navigation hints with measured syntax/stability and behavior association; adequacy remains unsupported." |
| C7 | Clean one-command public workflow, fixed-input cache behavior, write-set/report containment, and external usability evidence | B7 | Fresh clone fails, run requires internal state, raw traces leak, runtime/cost is unacceptable, or external users cannot reproduce outputs | "The artifact path has bounded local and public-safe fixture evidence, but is not externally validated as community-ready." |

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
| R192 | gate | Independent OSDI review after R190-score | read-only review over current plan/tracker/results/verdict/audit/followup/paper and R190 artifacts | one subagent review | confirms whether R190-score changes weak-accept status and whether docs overclaim | done | confirmed Level 3 only |
| R196 | supplement | Long-tail tag governance | `docs/visexp/out/long-tail-governance-r196` generated from R170/R189 artifacts | deterministic; optional regeneration disabled | raw tags preserved; review packet distinguishes keep/merge/regenerate/split outcomes; support gates remain false | done | governance only, cannot count as C6 adequacy |
| R201 | supplement | Long-tail governance sensitivity | `docs/visexp/out/long-tail-sensitivity-r201` generated from R170/R189 artifacts | deterministic 7-variant grid; no raw-trace mutation; no LLM regeneration | report action-count movement, review-required support share, and stability of high-support semantic heads; support gates remain false | done | strengthens R196 defensibility; C6 remains partial |
| R202 | supplement | Long-tail candidate regeneration smoke | `docs/visexp/out/long-tail-regeneration-r202` generated from R170/R189 artifacts and local llama.cpp | one managed llama.cpp run; no raw-trace mutation; no canonical-map update | 41/41 candidate rows grammar-valid, invalid count 0, support gates remain false; nested details local-audit-only | done | executability only, cannot count as C6 adequacy |
| R203 | supplement | Long-tail promotion gate | `docs/visexp/out/long-tail-promotion-r203` generated from R202 public-oriented attempts | deterministic; no raw-trace reads; no canonical-map update; 0 human labels | 41-row promotion packet, two blank reviewer sheets, promotion gate false | done | protocol only, cannot count as C6 adequacy |
| R205 | supplement | Long-tail compaction metrics | `docs/visexp/out/long-tail-compaction-r205` generated from R189/R190/R196/R201/R202/R203 artifacts | deterministic; no raw-trace reads; no canonical-map update | raw/canonical unique tags, top-K coverage, tail mass, review burden, regeneration and promotion gates reported | done | metrics only, cannot count as C6 adequacy or merge quality |
| R209 | supplement | Reversible display-map and raw drilldown contract | `docs/visexp/out/reversible-display-map-r209` generated from R196/R203/R205 artifacts | deterministic; no raw-trace reads; no canonical-map update | every R196 raw tag has one active display row, only deterministic aliases are active merges, lexical/profile merges and regenerated tags stay candidate-only, no hidden `other`, drilldown support and complete raw-tag membership preserved | done | data contract only, cannot count as C6 adequacy or merge quality |
| R211 | supplement | Stack examples and label distribution figures | `docs/visexp/out/stack-examples-r211` generated from R170/R189 artifacts | deterministic; no raw-trace reads; no LLM calls | top tag shares, process split rows, baseline-collapse examples, and top semantic stacks for RQ2 figures | done | figure/example evidence only, cannot count as C5 utility or C6 adequacy |
| R212 | supplement | Display-compaction ablation | `docs/visexp/out/display-compaction-ablation-r212` generated from R170/R196/R209 artifacts | deterministic; no raw-trace reads; no LLM calls | raw, alias-only, profile-guarded-candidate-applied, and R209 conservative display variants preserve total effect weight; R209 equals alias-only; profile candidates remain unreviewed | done | display-policy evidence only, cannot count as C5 utility or C6 adequacy |
| R213 | supplement | Raw/display/pending display-mode data-layer drilldown smoke | `docs/visexp/out/display-mode-drilldown-r213` generated from R209 artifacts | deterministic; no raw-trace reads; no LLM calls; no frontend renderer execution | all modes preserve support, display/pending buckets match, pending overlays candidate/review rows without changing membership, and drilldown membership matches the active display map | done | data-layer smoke only, cannot count as C5 utility, C6 adequacy, or frontend renderer evidence |
| R214 | supplement | Adaptive long-tail control loop | `docs/visexp/out/long-tail-control-r214` generated from R196/R201/R205/R209/R213 artifacts | deterministic; no raw-trace reads; no LLM calls; no canonical-map update | active deterministic aliases stay separate from pending profile/regenerated/split candidates; prompt-review and head-stability triggers expose unsafe automatic compaction | done | control-loop evidence only, cannot count as C6 adequacy or merge quality |
| R215 | supplement | Frontend raw/display/pending renderer-model smoke | `docs/visexp/out/frontend-renderer-mode-r215` generated from R209 display-map/drilldown rows, R213/R214 summary cross-checks, and `frontend/src/utils/agentflameDisplayModes.ts` | deterministic; no raw-trace reads; no LLM calls; TypeScript module compiled and run under Node, not browser DOM | frontend consumer preserves support and membership, overlays pending candidates without changing active display rows, and rejects corrupted drilldown plus candidate promotion fixtures | done | renderer-model smoke only, cannot count as C5 utility, C6 adequacy, merge quality, or browser renderer evidence |
| R216 | supplement | Browser raw/display/pending DOM harness smoke | `docs/visexp/out/browser-dom-mode-r216` generated from R209/R213/R214/R215 artifacts and `frontend/src/utils/agentflameDisplayModes.ts` | deterministic; no raw-trace reads; no LLM calls; TypeScript module compiled as browser ES modules, not the production React view | headless browser renders and clicks raw/display/pending controls, visible pending counts match the display contract, and corrupted drilldown plus candidate promotion fixtures are rejected | done | browser-DOM harness only, cannot count as C5 utility, C6 adequacy, merge quality, production UI, or visual drilldown evidence |
| R217 | supplement | Production React default display smoke | `docs/visexp/out/production-react-display-r217` generated from the real Next frontend plus a fixture AgentFlame API serving R209 artifacts | deterministic; no raw-trace reads; no LLM calls; builds frontend and runs headless Chrome over `/agentflame` | production `AgentFlameView` renders default display mode with 1,748 buckets, 482,398 support, and matching drilldown membership | done | production-render smoke only, cannot count as click-path, visual drilldown, C5 utility, C6 adequacy, or merge-quality evidence |
| R218 | supplement | Reviewed display-map update gate | `docs/visexp/out/display-map-update-gate-r218` generated from R209 artifacts and synthetic review fixtures over real pending rows | deterministic; no raw-trace reads; no LLM calls; synthetic review only; no canonical-map update | final consensus/adjudicated fixtures can produce preview diffs, unsafe rows are rejected, raw keys/support are preserved, and hidden `other` is rejected | done | update-gate smoke only, cannot count as promotion quality, C6 adequacy, C5 utility, or map-update evidence |
| R219 | gate | Claim/RQ readiness gap gate | `docs/visexp/out/claim-readiness-r219` generated from current evidence artifacts | deterministic; no raw-trace reads; no LLM calls; no labels or responses synthesized | claim/RQ matrix must keep C5 unsupported, C6 partial, weak accept unsupported, and R142/R124 as P0 next rows | done | audit-only, cannot upgrade any claim |
| R251 | supplement | Behavior-association check for prompt tags | `docs/visexp/out/behavior-tag-alignment-r251` generated from R170 folded stacks | deterministic; 1,000 session-preserving prompt-shuffle permutations; no raw-trace reads; no LLM calls; no labels or responses synthesized | prompt tags retain behavior information beyond session membership and emit a low-coherence review queue | done | behavior-association only, cannot count as human C6 adequacy |
| R204 | gate | Read-only OSDI gate review after R203/R193/R194/R195/R202 integration | `docs/visexp/out/osdi-gate-review-r204.md` | one independent review | no must-fix overclaim found; still Level 3/not weak accept because C5/C6 outcome data are missing | done | review only, cannot upgrade C5/C6 |
| R193 | collection | Human-evidence collection handoff | `docs/visexp/out/human-evidence-r193` generated from frozen R187/R124/R190/R203 artifacts | deterministic; 0 labels/responses | blank R124/R190/R203 sheets and R142 pointers exist, support gates remain false | done | logistics only, cannot count as C5/C6 |
| R194 | collection | Human-evidence preflight | `docs/visexp/out/human-evidence-preflight-r194.json` generated from R193 plus existing scorers | deterministic; 0 labels/responses | status is `ready_for_human_collection_no_outcomes`, hashes match, sheets/templates blank, scorers empty | done | preflight only, cannot count as C5/C6 |
| R195 | collection | Human-evidence ingestion/scoring | `docs/visexp/out/human-evidence-pipeline-r195.json` generated by `python3 docs/visexp/r195_human_evidence_pipeline.py` | deterministic default; 0 inputs/operations | status is `awaiting_human_inputs`, no scorers run, R195-specific scored outputs only, support gates remain false | done | pipeline only, cannot count as C5/C6 |
| R207 | collection | Human-evidence launch-readiness audit | `docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json` generated by `python3 docs/visexp/r207_human_launch_readiness.py` | deterministic; 0 labels/responses; no raw-trace reads | launch package is sendable and return files map to R195 inbox names while support gates remain false | done | launch readiness only, cannot count as C5/C6 |
| R151 | execute | Paper-scale developer utility run | 12-20 developers or deliberately narrowed expert population | preregistered participant/task/order blocking | Holm-corrected C5 gate passes and false positives stay within threshold | high | likely reviewer-critical |
| R191 | supplement | Target-specific network lineage hardening | expanded loopback/HTTP child-process workloads under `agentsight record --trace-net` | fixed manifest plus negative controls | target-specific network rows observed and joined, 0 joined negatives | medium | may require collector changes |
| R200 | artifact | Public-safe generated-fixture community smoke | temporary synthetic Codex fixture plus managed llama.cpp run via `python3 docs/visexp/r200_community_smoke.py` | clean + cached rerun | expected artifacts, no real trace reads, prompt redaction, fixed-input cache behavior, no raw-trace dirty paths | done | artifact-hygiene only; external adoption still unproven |

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
R184 reports `not_weak_accept`; R219 reports
`osdi_weak_accept_not_supported`; R185 says the plan is still Level 3 until
real C5/C6 human evidence exists.

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
4. After real R142/R124/R190/R203 CSV files are returned, run
   `python3 docs/visexp/r195_human_evidence_pipeline.py` with the files in its
   inbox or passed explicitly. R195 is the preferred post-collection scoring
   entry point, but the current default run remains `awaiting_human_inputs` and
   cannot upgrade any claim.
5. If the pilot passes, run R151 with 12-20 developers or a deliberately
   narrowed expert-study population. C5 can be claimed only if the
   Holm-corrected participant/task/order fixed-effect gate passes and false
   positives do not increase beyond the preregistered threshold.
6. Run target-specific network lineage hardening only for claims that extend C4
   beyond the fixed command-mode suite; do not let C4 hardening substitute for
   C5/C6.
7. Turn the bounded R160/R200 artifact smokes into an external-machine
   fresh-clone/clean-install community workflow after the core claims stop
   moving.
8. Rewrite the paper around "semantic attribution of agent system effects," not
   around "agent flamegraph UI," and keep C5/C6 limitations explicit unless the
   new results pass their gates.

No-go rule: if R124 remains `human_labels_empty` or R142/R151 remains
`participant_results_empty`, the paper should stay at "mechanism plus
measurement artifact." It should not claim tag adequacy, developer utility, or
community-tool readiness. R200 lowers artifact-hygiene risk but does not change
that gate.
