# Experiment Plan: AgentFlame

Last updated: 2026-06-19
Stage at update: supplement / experiment-design
Source/command: `docs/visexp/RESEARCH_PLAN.md`, R189/R190/R193/R195/R196/R200/R201/R202/R203/R205/R207/R209/R213/R214/R215/R216/R217/R218/R219/R220/R251/R252/R253/R254/R255/R256/R257/R258/R259/R260 generated artifacts, `docs/visexp/LONG_TAIL_COMPACTION.md`, `docs/visexp/out/osdi-gate-review-r204.md`, `python3 docs/visexp/r193_prepare_human_evidence_package.py`, `python3 docs/visexp/r195_human_evidence_pipeline.py`, `python3 docs/visexp/r196_long_tail_governance.py`, `python3 docs/visexp/r200_community_smoke.py`, `python3 docs/visexp/r201_long_tail_sensitivity.py`, `python3 docs/visexp/r202_long_tail_regeneration_smoke.py --regenerate-limit 50 --load-timeout 240 --llama-timeout 60`, `python3 docs/visexp/r203_long_tail_promotion_gate.py`, `python3 docs/visexp/r205_long_tail_compaction_metrics.py`, `python3 docs/visexp/r209_reversible_display_map.py`, `python3 docs/visexp/r213_display_mode_drilldown_smoke.py`, `python3 docs/visexp/r214_long_tail_control_loop.py`, `python3 docs/visexp/r215_frontend_renderer_mode_smoke.py`, `python3 docs/visexp/r216_browser_dom_mode_smoke.py`, `python3 docs/visexp/r217_production_react_display_mode_smoke.py`, `python3 docs/visexp/r218_display_map_update_gate.py`, `python3 docs/visexp/r220_fresh_clone_agentpprof_smoke.py`, `python3 docs/visexp/r253_agentpprof_git_install_smoke.py`, `python3 docs/visexp/r254_agentpprof_pinned_rev_install_smoke.py`, `python3 docs/visexp/r255_paper_scale_r195_bridge.py`, `python3 docs/visexp/r256_agentpprof_crate_package_smoke.py`, `python3 docs/visexp/r257_post_r256_review_gate.py`, `python3 docs/visexp/r258_paper_scale_human_evidence_bundle.py`, `python3 docs/visexp/r259_paper_scale_static_collection_kit.py`, `python3 docs/visexp/r260_paper_r259_consistency.py`, `python3 docs/visexp/r251_behavior_tag_alignment.py`, `python3 docs/visexp/r252_paper_scale_c6_label_package.py`, `python3 docs/visexp/r219_claim_readiness_gap_gate.py`, and `python3 docs/visexp/r207_human_launch_readiness.py`
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
| C2 | Local one-word LLM tagging is syntactically feasible. | 3B llama.cpp full run plus local 0.6B-/1B-/3B-class R180 benchmark. | Invalid rate, cache, latency, failures, tag coverage. | supported for syntax/latency; adequacy separate |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic/flat baselines. | Full local run. | Mixed-bucket count/weight, examples, ablations. | supported as mechanism |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | Live AgentSight traces. | Join coverage, orphan rate, path/domain specificity. | fixed command-mode suite passed |
| C5 | Developers answer forensic questions better with semantic effect flamegraphs. | User/task benchmark. | Time, accuracy, false positives, confidence. | unsupported |
| C6 | One-word tags are stable and adequate enough for navigation. | Multi-model repeated runs and human labels. | Invalid rate, stability, adequacy, noisy-tag rate. | partial |
| C7 | The approach is practical as an open-source developer tool. | Fresh clone, install, and public-fixture runs. | Setup/run commands, expected files, pprof readback, runtime/cache, artifact hygiene. | partial |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Full run with consistent folded outputs. | B1 | Folded totals mismatch or report cannot be regenerated. | Prototype supports only sampled/local histories. |
| C2 | Low invalid/failure rate and practical local runtime. | B1, B5 | Small models fail often or latency is prohibitive. | R180 supports local syntax/latency for available 0.6B-/1B-/3B-class models, not semantic adequacy. |
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
| B4 | C5 | Developer task benchmark | trace tree, event-count proxy, flat summary, nonsemantic stack, semantic stack; R225 prompt wall-clock duration baseline available for next preregistered packet; true tool/LLM span-duration remains future | time, accuracy, confidence, false positives | hidden answer key plus frozen preregistration | Table 3 | must |
| B5 | C2,C6 | Small-model/stability/adequacy | 0.6B, 1B, 3B, repeated runs | latency, invalid rate, exact stability, adequacy | grammar + human labels | Table 4 | must |
| B6 | C3 | Semantic-axis and projection-tradeoff ablation | no semantic, session-only, prompt-only, full session+prompt, raw display, alias-only, profile-guarded candidate, R209 conservative display | information gain, stack growth, mixed/residual weight, review-required support, unreviewed active weight; noisy-tag burden and task accuracy/time deferred | same observations, report/folded cross-checks, baseline queries, R223 projection-tradeoff summary | Fig. 4/Table 5 | done for C3/RQ2 mechanism |
| B7 | C7 | Artifact usability smoke | bounded fixed inputs, public fixture, clean clone, install paths, crate dry-run, documented setup | setup time, runtime/cache, output completeness, pprof readback, package contents, artifact hygiene | artifact checklist | Appendix | partial/done locally |
| B8 | C3; C6 protocol/gate only | Canonical tag consolidation and long-tail governance | raw, alias-only, lexical-only, profile-guarded, review-only suggestions, governance actions, candidate-only regeneration smoke, human-gated promotion protocol, compaction metrics, reversible display-map contract | unique tags, top-20 coverage, long-tail weight, stack reduction, merge-reason distribution, risk-audit rows, regenerate/split/keep action counts, regenerated-candidate grammar validity, promotion-label coverage, review-required support, raw-display-map coverage, hidden-`other` count | raw totals preserved; raw tags not overwritten; audit labels empty until collected; governance/regeneration/promotion/metrics/display-map packets do not count as adequacy | Fig. 5/Table 5 | done as vocabulary-hygiene/governance proxy and audit protocol |

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
  process/effect summary, nonsemantic folded stack, semantic folded stack. R225
  now supplies a timestamp-derived prompt wall-clock duration baseline for the
  next preregistered packet; true tool/LLM span-duration remains future because
  the historical artifact has event timestamps but no tool/LLM start-end spans,
  and prompt wall-clock spans may include idle/user-wait time.
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
  blocked permutation tests plus false-positive guardrails. R249 adds a
  12-participant-packet paper-scale launch package with 168 blank response rows
  and a nondefault assignment file. R255 verifies that R195 can run the R249
  blank response template with that R249 assignment and rejects the old R142
  assignment, but it still records 0 real responses and keeps C5 false.
- Success criterion: semantic view improves exact answer accuracy by >=10
  percentage points or median task time by >=20% on core forensic tasks, with no
  >5 percentage-point increase in false positives, under the preregistered
  participant/task/order blocked permutation analysis.
- Failure interpretation: keep the tool as an expert exploratory profiler.

### B5. Small-Model Cost And Tag Adequacy

- Claim tested: C2, C6.
- Hypothesis: smaller local models can produce grammar-valid one-word tags cheaply, but
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

- Claim tested: C3. Auxiliary C6 visual-noise protocol/gate artifacts and B4
  task accuracy/time remain deferred.
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
  R224 reruns the same checker on R170 current full-history folded artifacts,
  aligning the semantic-axis denominator with R212's 183,714 effect weight:
  no-semantic mixes 90.402%, session-only 84.407%, prompt-only 36.722%, and
  prompt-only residual is 7.485%. R223 repackages this as a
  projection-selection tradeoff rather than a single "best" flamegraph:
  no-semantic is the compact baseline, prompt-only is the best single semantic
  axis, and full session+prompt is the audit view. R223 also combines
  R212/R205/R209 to show display compaction tradeoffs: R209 conservative
  display is alias-only active with 0.0% unreviewed active weight, while
  profile-guarded candidate application would reduce stacks more but activate
  2.532% unreviewed effect weight and must stay behind human gates.

### B8. Canonical Tag Consolidation

- Claim tested: C3 mechanism; C6 noise-control boundary only.
- Hypothesis: open-vocabulary one-word tags can remain raw and auditable while
  a display-time canonical layer provides a candidate reduction in long-tail
  fragmentation.
- Workload: R170 current full-history artifacts, without rescanning or mutating
  raw agent traces.
- Compared systems: raw tag stacks, auto-merged canonical stacks, review-only
  suggestions.
- Metrics: unique tag count, top-20 coverage, long-tail weight, unique folded
  stack count, total-weight preservation, merge-reason distribution, profile
  similarity distribution, number of review rows.
- Oracle: canonical folded totals equal raw folded totals; raw tag mapping CSV
  records every merge; review suggestions are not applied; the merge-risk
  scorer must keep empty audit labels as `human_labels_empty` and only report
  over-merge/under-merge rates after two independent labeler sheets and
  adjudication.
- Current result: R189 maps `raw_tag -> canonical_tag` for session, prompt, and
  LLM-call tags. Prompt-effect tags reduce 263 -> 216, prompt-row tags reduce
  328 -> 279, LLM-event tags reduce 1423 -> 1254, system stacks reduce
  26,829 -> 26,067 with total system weight preserved, and token stacks reduce
  8569 -> 7661 with total token weight preserved. Applied merges are reported
  separately as dictionary aliases and lexical+profile merges; there are no
  profile-only merges in this prototype.
- R190 adds the missing audit protocol and consolidation-rule ablation. Raw,
  alias-only, lexical-only, and current profile-guarded variants produce
  prompt-effect tag counts of 263, 241, 200, and 216 respectively; LLM-event tag
  counts of 1423, 1392, 868, and 1254; system-stack counts of 26,829, 26,612,
  25,985, and 26,067. This shows lexical-only consolidation is much more
  aggressive than the current profile-guarded policy. R190 also writes an
  80-row over-merge proxy set and an 80-row under-merge proxy set for later
  human audit; R190-score currently reports `human_labels_empty`, 160 rows, 0
  final labels, and `canonicalization_quality_supported=false`.
- R196 adds the missing long-tail governance loop over the same R170/R189
  artifacts. It emits 231 existing canonical merges, 114 review-merge rows, 39
  regeneration candidates, 2 contextual-split candidates, 1,241 kept rare
  distinct tags, and 184 kept head tags. Review-required support remains small:
  0.938% for session tags, 3.258% for prompt tags, and 1.376% for LLM-call
  tags. The rule deliberately keeps multi-peak semantic head tags such as
  `refactor` rather than splitting them automatically; only generic/noisy tags
  are eligible for regeneration or contextual split.
- R201 adds the missing sensitivity check for the R196 policy. Across seven
  threshold and generic-vocabulary variants, baseline review-required support
  is 1.926% of total support and the worst variant is 1.931%, so
  review-required row/support counts are stable in this grid. The
  higher-tail-threshold variant lowers
  baseline-head stability to 65.217%, which is a reported display-policy risk,
  not hidden positive evidence.
- R202 exercises the optional regeneration path for the R196 regenerate/split
  rows. A managed local llama.cpp server attempts 41/41 candidates and returns
  41 grammar-valid one-word outputs with 0 invalid outputs; 32 changed from the raw tag
  and 9 were unchanged. This validates the candidate-generation path, not tag
  adequacy or merge quality. The top-level R202 summary/attempts are
  public-oriented; the nested details are local-audit-only until sanitized or
  excluded.
- R203 adds the promotion gate after regeneration. It consumes only the
  public-oriented R202 attempts CSV and writes a 41-row promotion packet plus two
  blank reviewer sheets. The default result has 0 final labels,
  `long_tail_promotion_review_supported=false`, and `canonical_map_updated=false`,
  so the mechanism is reviewable but no regenerated tag is accepted.
- R205 adds the compaction-metrics view for that contract. It reads only
  generated R189/R190/R196/R201/R202/R203 artifacts and reports raw unique tag
  strings 1,546 -> canonical unique tag strings 1,364, top-20 support coverage
  93.683% -> 95.186%, long-tail support 1.746%, review-required support
  1.926%, R203 final labels 0, and R190 over/under-merge rates `n/a`. These
  are mechanism metrics, not adequacy or merge-quality evidence.
- R209 exports the renderer-facing reversible display-map contract for the same
  rows. It covers 1,811/1,811 R196 raw tags, exposes 1,509 active display
  labels, keeps 41 regenerated labels candidate-only, emits 0 reviewed diff
  rows, records 0 hidden `other` rows, and preserves drilldown support. This is
  a data contract, not a canonical-map update or quality claim.
- R213 verifies the raw/display/pending display-mode data layer over R209
  artifacts. It preserves 482,398 support, keeps pending membership unchanged,
  and checks that drilldown raw-tag membership matches the active display map.
  It is not a frontend renderer test.
- R214 converts the long-tail policy into explicit control gates. It keeps 63
  deterministic aliases active, keeps 168 profile-merge candidates and 41
  regenerated/split candidates pending, exposes 323 review-required rows, and
  fails the prompt-review-budget and high-tail-stability triggers. This is the
  guard against automatic tail cleanup.
- R215 compiles the frontend TypeScript display-mode consumer and runs a Node
  harness that renders R209 display-map/drilldown rows while cross-checking
  R213/R214 summary counts. It preserves raw/display/pending support and
  membership, keeps candidates as overlays, and rejects corrupted drilldown plus
  candidate-as-active fixtures. It is a renderer-model smoke, not a browser DOM,
  visual, or utility test.
- R216 compiles the same display-mode consumer as browser ES modules and runs a
  temporary headless-browser DOM harness. It clicks raw/display/pending controls,
  verifies visible DOM counts, saves a screenshot and DOM dump, and rejects the
  same corrupted-membership and candidate-promotion fixtures. It is a browser
  harness, not the production React view, visual drilldown, or utility test.
- R217 builds the real Next frontend and verifies that production
  `AgentFlameView` renders the default display panel from R209 artifacts: 1,748
  buckets, 482,398 support, 3 mode buttons, and matching raw membership. It is
  a production render smoke only, not a click-path, visual drilldown, or utility
  test.
- R218 checks the reviewed display-map update gate using synthetic review
  fixtures over real R209 pending rows. It accepts 2 preview diff rows, rejects
  4 unsafe rows, preserves 1,811 raw keys and 482,398 support, and keeps the
  canonical map unchanged. It is update-gate mechanics only, not promotion
  quality or adequacy evidence.
- R219 turns the current state into a reviewer-facing claim/RQ readiness gate.
  It reads generated artifacts only, records C5 as unsupported with 0 responses
  and C6 as partial with 0 final labels, keeps `weak_accept_supported=false`,
  and lists R142/R124 as the P0 next evidence rows. It is audit evidence, not an
  outcome result.
- R195 adds the post-collection ingestion/scoring path for the human evidence
  that B4/B5/B8 require. The current default run has an empty inbox and reports
  `awaiting_human_inputs`; it runs no scorers and keeps C5/C6/canonicalization
  support gates false. When real files are supplied, R195 writes scored outputs
  under `docs/visexp/out/human-evidence-r195/scored` so the canonical empty
  gates remain auditable until deliberately promoted. R195 now includes R203 as
  a fourth collection group: completed promotion sheets can support only the
  long-tail promotion-review gate, not C5/C6 or a canonical-map update.
- R207 audits the launch handoff before collection. It confirms the sendable
  units are present and still blank: five R142 participant packets, a 70-row
  response template, two 300-row R124 sheets, two 160-row R190 sheets, two
  41-row R203 sheets, and an explicit R195 return-file naming plan. It supports
  launch readiness only, not C5/C6 outcomes.
- Failure interpretation: if over-merge risk is high, keep canonical tags as an
  optional UI overlay and require R124 human labels before using them in any
  adequacy claim.

## Reviewer-Critical Execution Slice

The experiment plan is intentionally split into mechanism evidence and
weak-accept evidence. The next work should optimize for the latter:

| Priority | Run | Claim | Why It Matters To OSDI Reviewers | Decision Gate |
|----------|-----|-------|----------------------------------|---------------|
| must | R142-pilot | C5/RQ4 | Tests whether real developers can use the semantic effect view without the authors interpreting it for them. | Response contract valid; task-level deltas interpretable; no leakage or duplicate/partial responses. |
| must | R124-labels | C6/RQ5 | Separates "local models emit valid one-word tags" from "humans find the tags adequate navigation labels." | Complete two-labeler sheets, adjudication, agreement threshold, adequate/generic/misleading rates. |
| must if claiming compaction quality | R190-labels and R203-labels | C6/B8 | Determines whether canonical merges and regenerated long-tail candidates are acceptable display overlays. | Complete paired labels; over-merge/under-merge/promotion rates pass thresholds; no automatic map update. |
| should | R191 target-specific network lineage | C4/RQ3 | Strengthens the most systems-specific novelty beyond fixed command-mode process/file effects. | Target-specific network rows observed and joined; 0 negative-control joins; scoped recall/precision reported. |
| should | External fresh-clone artifact smoke | C7/RQ6 | Moves the artifact from local research prototype toward community tool. | R220 covers a clean local clone with public fixture and pprof readback; external machine/container, real-report sanitization, and feedback remain open. |

Additional visual polish, new dashboards, or more subagent reviews do not move
the paper unless they protect one of these gates from overclaim.

## Run Order

| Run ID | Stage | Purpose | Config | Seed/reps | Decision gate | Cost | Risk |
|--------|-------|---------|--------|-----------|---------------|------|------|
| R100 | sanity | full local-history run | 3B llama.cpp, `tag_llm_calls=true` | one full run plus cached rerun | report exists and parses | completed | done |
| R110 | decision | exact lineage harness smoke | 3 live tasks under AgentSight | 3 tasks | raw coverage, in-scope join coverage, orphan report | low | done |
| R111 | decision | exact lineage native export smoke | same 3 DB exports | 3 tasks | native sessions/tools plus raw join/orphan report | low | done/partial |
| R112 | decision | exact lineage DB-persisted backfill smoke | same 3 DB copies | 3 tasks | persisted sessions/tools plus raw join/orphan report | low | done/partial |
| R114 | decision | broader live exact-lineage suite | 20 `agentsight record` tasks, disposable repos for writes | fixed task manifest | C4 scope can widen only if join/orphan/path/domain/redaction gates pass | medium | live task variance |
| R182 | decision | network exact-lineage smoke | 2 `agentsight record` loopback-task runs after record-mode process `--trace-net` fix | fixed task manifest plus negative controls and target-specific oracle | C4 network-workload scope can widen only if loopback or expected child-process rows are observed and joined; low-level agent-process rows alone are implementation evidence | low | partial/network flag smoke |
| R121 | decision | real local model benchmark | `agentflame bench` over available GGUF models | 3 fixed fragments x 3 identical repeats | Historical 3B smoke; superseded by R180 for local model-size coverage | medium | small synthetic sample |
| R122 | decision | redacted tag adequacy packet | 100 session + 100 prompt + 100 LLM-call fragments | deterministic sample | label packet and redaction gate | low | trace privacy |
| R123 | decision | real-fragment stability benchmark | R122 fragment file through 3B llama.cpp server | 300 fragments x 3 identical repeats | C2/C6 can cite 3B stability only if grammar/latency/stability pass | low | superseded for model-size coverage by R180 |
| R180 | decision | local multi-model syntax/stability smoke | R122 fragment file through local 0.6b, TinyLlama 1.1b, and 3b GGUFs with `--reasoning off` | 3 models x 300 fragments x 3 identical repeats | C2 can cite local 0.6B/1B/3B-class syntax/latency only; C6 remains partial because 1.1b semantic collapse and no human labels | low | done; not controlled same-family scaling |
| R124-scoring | decision | tag adequacy scorer and empty-result gate | R122 label packet with no human labels yet | deterministic scorer over 300 rows | output must have 300/300 candidate tags, stay `human_labels_empty`, and keep C6 partial until labels exist | low | evidence boundary |
| R124-blinding | decision | blinded human labeler sheet | R122 label packet with candidate tags | deterministic export | labelers see row id, level, redacted preview, candidate tag, rubric, label, notes; model/source/stability columns hidden | low | done; labels still missing |
| R124 | decision | human tag adequacy labels | blinded R124 labeler sheet | >=2 labelers if possible | tag adequacy wording | medium | subjective labels |
| R131 | decision | semantic-axis ablation | no/session/prompt/full variants plus token LLM-call projections | deterministic | passed for C3 mechanism: totals and external folded cross-checks preserved; system prompt-only reduces mixed full semantic bucket weight from 90.219% to 37.687% and residual from 44.639% to 7.526%; token prompt+LLM-call remains 95.765% bucket mixed but only 0.027% residual | low | done for C3; C6/B4 deferred |
| R189 | decision | canonical tag consolidation | R170 full-history `agentflame.json`, `semantic-system.folded.txt`, and `semantic-token.folded.txt` | deterministic; no raw-trace mutation | total weights preserved; raw tags retained in mapping; merge reasons and review suggestions reported; canonical tags are a candidate long-tail reduction proxy, not adequacy evidence | low | done/vocabulary-hygiene proxy |
| R190 | decision | canonical tag consolidation audit and ablation | R170 full-history artifacts plus R189 consolidation logic | deterministic; no raw-trace mutation; 0 human labels | raw/alias-only/lexical-only/profile-guarded variants compared; over-merge and under-merge proxy packets exported; no correctness claim until labels collected | low | done/audit-packet-ready |
| R190-score | decision | canonical merge-risk scorer | 160-row R190 audit packet | deterministic; no label inference | empty packet must stay `human_labels_empty`; with labels, gate requires complete paired labels, adjudication, kappa >=0.6, unclear <=10%, over-merge <=10%, under-merge <=20% | low | done/empty |
| R196 | supplement | long-tail tag governance packet | R170 full-history artifacts plus R189 mapping | deterministic; optional llama.cpp regeneration disabled by default; no raw-trace mutation | raw tags preserved; high-support semantic heads are not split solely for multi-peak profiles; generic/noisy tags are routed to regenerate/split review; C6 remains unsupported without R124/R190 labels | low | done/governance-packet |
| R201 | supplement | long-tail governance sensitivity | R170/R189 generated artifacts plus R196 policy logic | deterministic 7-variant grid; no raw-trace mutation; no LLM regeneration | review-required row/support counts, long-tail support, action movement, and head stability reported for lower/higher tail thresholds, aggressive/conservative split thresholds, and narrow/expanded generic vocabularies; gates remain false for adequacy, merge quality, and community adoption | low | done/sensitivity |
| R202 | supplement | long-tail candidate regeneration smoke | R170/R189 generated artifacts plus R196 regenerate/split rows | managed local llama.cpp server; one bounded pass; no raw-trace mutation; no canonical-map update | all attempted regeneration outputs must satisfy one-word grammar; raw tags preserved; top-level outputs are public-oriented while nested details are local-audit-only; gates remain false for adequacy, merge quality, developer utility, and community adoption | low | done/regeneration-smoke |
| R203 | supplement | long-tail promotion gate | public-oriented R202 attempts CSV | deterministic; no raw-trace reads; no canonical-map update; 0 human labels | generated candidates require paired/adjudicated human labels before promotion decisions; empty labels keep promotion, adequacy, and map-update gates false | low | done/empty-promotion-gate |
| R205 | supplement | long-tail compaction metrics | R189/R190/R196/R201/R202/R203 generated artifacts | deterministic; no raw-trace reads; no canonical-map update | raw/canonical unique tags, top-K coverage, long-tail mass, review-required support, regeneration validity, promotion-label coverage, and merge-risk rates reported with all support gates scoped | low | done/metrics-only |
| R209 | supplement | reversible display-map and raw drilldown contract | R196/R203/R205 generated artifacts | deterministic; no raw-trace reads; no canonical-map update | every raw tag has one active display row, no hidden `other`, candidate regenerated tags are inactive, drilldown support is preserved, reviewed diff is empty without labels | low | done/display-map-contract |
| R213 | supplement | display-mode drilldown data-layer smoke | R209 display-map and drilldown artifacts | deterministic; no raw-trace reads; no LLM calls; no frontend renderer execution | raw/display/pending data modes preserve support, pending membership is unchanged, drilldown membership matches active display membership, and quality gates remain false | low | done/data-layer-smoke |
| R214 | supplement | adaptive long-tail control loop | R196/R201/R205/R209/R213 generated artifacts | deterministic; no raw-trace reads; no LLM calls; no canonical-map update | active deterministic aliases separated from pending merge/regeneration/split candidates; review-budget, head-stability, hidden-other, and drilldown gates reported | low | done/control-loop |
| R215 | supplement | frontend display-mode renderer-model smoke | R209 display-map/drilldown rows plus R213/R214 summary cross-checks and `frontend/src/utils/agentflameDisplayModes.ts` | deterministic; no raw-trace reads; no LLM calls; TypeScript module compiled and executed under Node, no browser DOM | raw/display/pending support preserved, pending overlays do not change active membership, corrupted drilldown and candidate promotion fixtures rejected | low | done/renderer-model-smoke |
| R216 | supplement | browser display-mode DOM harness smoke | R209 display-map/drilldown rows plus R213/R214/R215 summary cross-checks and `frontend/src/utils/agentflameDisplayModes.ts` | deterministic; no raw-trace reads; no LLM calls; TypeScript module compiled as browser ES modules and executed in a headless-browser DOM harness, no production React view | raw/display/pending controls render and click, visible pending counts match R209/R213/R214, corrupted drilldown and candidate promotion fixtures rejected | low | done/browser-dom-harness-smoke |
| R217 | supplement | production React default display smoke | real Next static frontend plus fixture AgentFlame API serving R209 artifacts | deterministic; no raw-trace reads; no LLM calls; production React render only, no production click path | `AgentFlameView` renders default display panel with 1,748 buckets, 482,398 support, and matching display/drilldown membership | low | done/production-render-smoke |
| R218 | supplement | reviewed display-map update gate | R209 display-map rows plus synthetic review fixtures over real pending rows | deterministic; no raw-trace reads; no LLM calls; synthetic review only; no canonical-map update | final consensus/adjudicated rows produce preview diffs; unsafe rows are rejected; raw keys/support are preserved | low | done/update-gate-smoke |
| R219 | gate | claim/RQ readiness gap gate | generated evidence artifacts | deterministic; no raw-trace reads; no LLM calls; no labels/responses synthesized | C5/C6 remain blockers, weak accept stays unsupported, synthetic/subagent evidence is disallowed, and R142/R124 are P0 next rows | low | done/readiness-audit |
| R251 | supplement | behavior-association check for prompt tags | R170 semantic folded stacks | deterministic; 1,000 session-preserving prompt-shuffle permutations; no raw-trace reads; no LLM calls; no labels/responses synthesized | prompt tags should retain behavior information beyond session membership while C6 human adequacy stays unsupported | low | done/behavior-association; not human adequacy |
| R252 | collection | paper-scale C6 label package and blank R195 check | R193 R124/R190/R203 blank label sheets | deterministic packaging; isolated R195 blank-input check; no raw-trace reads; no LLM calls; no labels/responses synthesized | two labeler packets cover R124 adequacy, R190 merge-risk, and R203 promotion labels; 501 rows per labeler, 1002 required independent label decisions; blank inputs keep all gates false | low | done/paper-scale-label-ready; no human labels |
| R204 | gate | independent OSDI gate review after long-tail promotion integration | R203/R193/R194/R195/R202 artifacts plus current claim-boundary docs | one read-only subagent review | no must-fix overclaim; C5/C6 remain blocked until real participant responses and human labels exist; R202/R203 named as protocol/gate artifacts | low | done/review |
| R193 | collection | human-evidence collection package | frozen R187/R124/R190/R203 artifacts | deterministic; 0 labels/responses | package blank R124/R190/R203 sheets and R142 pointers while keeping support gates false | low | done/collection-ready |
| R194 | collection | human-evidence preflight gate | R193 manifest plus existing R187/R124/R190/R203/R142 scorer outputs | deterministic; 0 labels/responses | hashes match, blank sheets/templates remain blank, scorers empty, support gates false | low | done/preflight-ready |
| R195 | collection | human-evidence ingestion/scoring pipeline | `docs/visexp/out/human-evidence-r195/inbox` or explicit returned CSV paths | deterministic default; scorer operations only for complete input groups | default empty inbox must produce `awaiting_human_inputs`, no scorer operations, and false C5/C6/canonicalization/promotion gates; completed R142/R124/R190/R203 inputs score into R195-specific paths without overwriting canonical empty outputs | low | done/pipeline-awaiting |
| R207 | collection | human-evidence launch-readiness and return-file mapping | R187/R193/R195 generated artifacts | deterministic; 0 labels/responses; no raw-trace reads | launch-ready only if packets/sheets/templates/READMEs are valid, blank, and mapped to R195 inbox names while support gates remain false | low | done/launch-ready |
| R255 | collection | paper-scale R195 C5 scoring bridge | R249 blank response template plus R249 assignment, with old R142 assignment as negative case | deterministic; no raw-trace reads; no LLM calls; no participant responses synthesized | R195 must accept the R249 assignment case as `scored_human_inputs_no_supported_gate`, reject the old-assignment case as `scoring_failed`, and keep C5/weak-accept false | low | done/paper-scale bridge; no outcome evidence |
| R141-packet | decision | superseded user-task packet draft | old `user_task_benchmark.py` packet before same-slice enforcement | deterministic 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | superseded by R142 because same-event-slice fairness was unresolved | low | superseded |
| R142-packet | decision | same-event-slice user-task packet and empty scorer check | `user_task_benchmark.py` over current artifacts; scorer over response template | deterministic 14 tasks x 5 conditions; P01-P05 assignments; 0 responses | packet ready only if leakage, assignment, same-slice, explicit event-count baseline naming, and scorer checks pass | low | done/packet |
| R142-scoring | decision | response-contract and paper-scale user-task scorer gate | `score_user_task_results.py` over response template | deterministic empty-template check | C5 must stay unsupported until real responses; real runs use contract checks, diagnostic paired deltas, participant/task/order fixed-effect blocked permutation tests, and Holm correction | low | done/empty |
| R142-preregistration | decision | freeze C5 analysis before collection | `python3 docs/visexp/r142_preregistration.py` | deterministic over bundle, assignments, answer key, response template, and scorer constants | prereg artifact is `frozen_before_collection`, validates conditions/schema/thresholds, and source hashes match | low | done/protocol |
| R225 | decision | prompt wall-clock duration baseline from R170 timestamps | `python3 docs/visexp/r225_prompt_span_duration_baseline.py` | deterministic over generated R170 `agentflame.json` and `semantic-system.folded.txt`; no raw trace reads; no LLM calls | reconstruct prompt wall-clock spans, generate duration folded/SVG artifacts, compare duration ranking against system-effect ranking, and keep C5/C6 support false | low | done/prompt-span baseline; may include idle/wait time; update R142 packet only after prereg revision |
| R142 | main | user task pilot | 5 developers, five conditions | counterbalanced P01-P05 template | protocol and answer keys work on real responses under the frozen preregistration | medium | recruiting |
| R151 | main | user task paper run | 12-20 developers or scoped expert study | counterbalanced | C5 verdict | high | strongest missing evidence |
| R160 | polish | bounded fixed-session open-source usability smoke | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command against the same output dir; then `python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke-fixed --clean-agentflame-json .agentsight/agentflame/r160-smoke-fixed/agentflame.clean.json --out docs/visexp/out/artifact-usability-r160.json ...` | one clean run plus cached rerun over fixed inputs | expected files, runtime/cache summary, sanitized input manifest, clean/cached input equality, fully cached rerun, no raw trace commit, generated report path containment | low | done/bounded; broad community usefulness and pre/post write-set audit still open |
| R200 | polish | public-safe generated-fixture community smoke | `python3 docs/visexp/r200_community_smoke.py --command-timeout 360 --load-timeout 240` | one temporary synthetic Codex fixture; one clean run plus cached rerun | no real `.codex`/`.claude` trace reads; expected artifacts; clean run has real llama.cpp calls; cached rerun has all cache hits and 0 model calls; committed summary redacts local paths and prompt previews | low | done/artifact-hygiene; external-machine adoption and feedback still open |
| R220 | polish | fresh-clone `agentpprof` community smoke | `python3 docs/visexp/r220_fresh_clone_agentpprof_smoke.py` | one temporary clean clone at current HEAD; one public synthetic Codex fixture; regex tagger; no LLM calls | clean clone before fixture, `agentpprof` tasks/tools/tokens/files/network outputs, fixture-level expected tools/files/network/token stacks, Go pprof readback, output containment, no real agent-history reads, privacy scan | low | done/local clean-clone smoke; external-machine adoption, llama.cpp setup, real-history public sanitization, and feedback still open |
| R253 | polish | GitHub-branch `agentpprof` install smoke | `python3 docs/visexp/r253_agentpprof_git_install_smoke.py` | `cargo install --git https://github.com/eunomia-bpf/agentsight --branch research/semantic-flamegraph-artifacts --locked --force agentpprof`; committed public fixture; regex tagger; no LLM calls | installed help, tasks/tools/tokens/files/network outputs, expected tools/files/network/token stacks, Go pprof readback, output containment, no real agent-history reads, privacy scan | low | done/git-install-smoke; crates.io, external-machine adoption, llama.cpp setup, real-history public sanitization, and feedback still open |
| R254 | polish | pinned-revision `agentpprof` install smoke | `python3 docs/visexp/r254_agentpprof_pinned_rev_install_smoke.py` | `cargo install --git https://github.com/eunomia-bpf/agentsight --rev c43daf2b2565531dfd95de8654adabb30ac878d4 --locked --force agentpprof`; committed public fixture; regex tagger; no live model calls | installed help, install rev matches driver commit, tasks/tools/tokens/files/network outputs, expected tools/files/network/token stacks, Go pprof readback, output containment, no real agent-history reads, privacy scan | low | done/pinned-rev-smoke; crates.io, external-machine adoption, llama.cpp setup, real-history public sanitization, and feedback still open |
| R256 | polish | `agentpprof` crate-package dry-run | `python3 docs/visexp/r256_agentpprof_crate_package_smoke.py` | `cargo package --list` and `cargo package` over clean provenance commit `a388c89ce718849ebfa5b8610709cbb50cf66b48`; no private-history discovery; no LLM calls | intended 8-file crate set, archive/list equality, forbidden-path absence, registry `agent-session v0.3.3` verification, summary privacy scan | low | done/crate-package-smoke; crates.io publish/readback, external-machine adoption, llama.cpp setup, real-history public sanitization, and feedback still open |
| R257 | gate | post-R256 review gate | `python3 docs/visexp/r257_post_r256_review_gate.py` | deterministic read over R256 artifacts and current evidence docs; no raw traces, no LLM calls, no labels/responses | 7/7 checks pass; R256 stays scoped to crate-package dry-run; C5/C6/publish/weak-accept gates remain false | low | done/review-hygiene; no outcome evidence |
| R258 | collection | unified paper-scale C5/C6 launch bundle | `python3 docs/visexp/r258_paper_scale_human_evidence_bundle.py` | deterministic package over R249/R252/R255/R257 artifacts; no raw traces, no LLM calls, no labels/responses | 43-member tarball, 12 C5 participant packets, 168 C5 response rows, 2 C6 labeler packets, 1,002 C6 decisions, source/tar leak scans pass, claim gates false | low | done/paper-scale bundle-ready; next step is real returns |
| R259 | collection | paper-scale static collection forms and export smoke | `python3 docs/visexp/r259_paper_scale_static_collection_kit.py` | deterministic HTML generation and synthetic export smoke over R249/R252/R258 artifacts; headless Chrome DOM checks; no labels/responses | 12 participant forms, 6 labeler forms, C5 merge page, 168-row C5 synthetic merge, 1,002 C6 blank-label rows, browser/leak checks pass | low | done/static-kit-smoke; next step is real returns |
| R260 | gate | post-R259 paper/evidence consistency audit | `python3 docs/visexp/r260_paper_r259_consistency.py` | deterministic read over R258/R259/R245 artifacts and current paper/docs; no raw traces, no LLM calls, no labels/responses | 25/25 checks pass, R259 counts preserved, paper/docs keep collection-logistics boundary and false gates | low | done/wording-audit; next step is real returns |

## Tracker Handoff

- Update path: `docs/visexp/EXPERIMENT_TRACKER.md`.
- Result path convention:
  - `.agentsight/agentflame/latest` for local generated reports.
  - `.agentsight/agentflame/exact-lineage-*` for live AgentSight runs.
  - `.agentsight/agentflame/model-benchmarks*.json` and
    `docs/visexp/out/model-benchmarks-r12*.json` for model cost/stability.
  - `.agentsight/agentflame/ablations-*` for semantic-axis ablations.
  - `docs/visexp/out/tag-consolidation-r189` for canonical tag consolidation
    summaries, mappings, and folded outputs.
  - `docs/visexp/out/tag-adequacy-results-r124.*` for C6 human-label scoring.
  - `docs/visexp/out/user-task-results.*` for benchmark scoring.
- Required tracker columns: Run ID, Claim, Block, Purpose, Command/config,
  Commit, Machine, Seed/reps, Oracle, Decision gate, Result path, Status.

## Baseline Fairness

- Named baselines:
  - event-count proxy: same event slice rendered with event/count weights and no
    semantic inheritance; this is not a duration baseline.
  - prompt-span duration flamegraph: R225 reconstructs prompt-level wall-clock
    intervals from timestamps; this may include idle/user-wait time and can be
    used only after revising the preregistered packet.
  - true span-duration trace/flamegraph: OpenTelemetry-style span tree/flamegraph
    with tool/LLM start-end spans; historical R170 artifacts do not provide this.
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
  capture-time record passes on 20 fixed Codex tasks. R182 adds record-mode
  process `--trace-net` and observes joined low-level `codex` process network
  rows, but target-specific loopback/expected child-process network rows remain
  0/0 and HTTP payload/URL reconstruction is absent. The remaining uncertainty
  is full-history, cross-repo, more agent types, target-specific network
  workloads, and broader workload coverage, not command-mode capture-time row
  creation.
- Current user utility outcome evidence is absent. R142-packet makes the B4
  packet/scorer executable for a pilot, but no participant responses have been
  collected. R193 points to the R142 launch materials and R195 can ingest
  returned pilot responses. R249/R255 extend that path to paper-scale C5 by
  verifying the R249 assignment can be supplied to R195 and the old R142
  assignment is rejected, but the current R195/R255 runs have no real inputs and
  do not add responses.
- Current tag adequacy is unproven even though syntax validity is strong.
  R124-scoring can score labels and reports the current packet as
  `human_labels_empty` with 300/300 candidate tags, so it is a reproducibility
  artifact rather than adequacy evidence. R193 packages two blank R124 labeler
  sheets and R195 can join/score completed copies, but the current R195 run has
  no labeler inputs and does not add labels.
- Current tag canonicalization is deterministic and useful as a candidate
  display-time long-tail reduction proxy, but R189/R190-score do not prove
  semantic correctness, do not prove that merged raw tags are redundant, and do
  not replace R124 labels until the R190 audit packet has real human labels.
- Current regenerated long-tail candidates are not accepted display labels.
  R193 now packages two blank R203 promotion sheets and R195 can score returned
  copies, but the current R195 run has no promotion labels,
  `long_tail_promotion_review_supported=false`, and
  `canonical_map_updated=false`.
- These limitations are acceptable for internal planning but not for OSDI final
  claims.

## Claim Gate After Results

| Claim | Evidence file(s) | Verdict | Supported wording |
|-------|------------------|---------|-------------------|
| C1 | `.agentsight/agentflame/latest/agentflame.json` | supported | local-history semantic folded stacks |
| C2 | `.agentsight/agentflame/latest/tags.json`, `docs/visexp/out/model-benchmarks-r180.json` | supported for syntax/latency; partial for adequacy | local 0.6B-/1B-/3B-class syntactic feasibility on the redacted R122 sample |
| C3 | `.agentsight/agentflame/latest/agentflame.json` | supported | semantic partitioning in local workload |
| C4 | `docs/visexp/out/native-lineage-r112.json`, `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/live-network-r182.json` | supported for fixed command-mode suite; partial broadly and partial for target-specific network workloads | exact lineage over the fixed 20-task command-mode suite; R182 validates record-mode `--trace-net` for low-level agent-process rows but not loopback child-process capture |
| C5 | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-results.json`, `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/human-evidence-paper-bridge-r255/paper-scale-r195-bridge-r255.json` | unsupported | same-slice packet, frozen preregistration, paper-scale R195 bridge, and ingestion pipeline exist; no user outcome claim |
| C6 | `docs/visexp/out/model-benchmarks-r180.json`, `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json`, `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json`, `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json`, `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json`, `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json`, `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json`, `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json`, `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json`, `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json`, `docs/visexp/out/production-react-display-r217/production-react-display-r217.json`, `docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json`, `docs/visexp/out/behavior-tag-alignment-r251/behavior-tag-alignment-r251.json`, `docs/visexp/out/human-evidence-pipeline-r195.json` | partial | multi-model syntactic/stability evidence plus behavior-association evidence and C6 protocol/gate artifacts for display-layer governance, sensitivity, candidate regeneration, promotion review, reversible display export, data-layer drilldown, long-tail control, frontend/browser/production rendering, and reviewed-diff gate mechanics; adequacy scorer and ingestion pipeline ready but labels empty |
| C7 | `docs/visexp/out/artifact-usability-r160.json`, `docs/visexp/out/community-smoke-r200.json`, `docs/visexp/out/fresh-clone-agentpprof-r220/fresh-clone-agentpprof-r220.json`, `docs/visexp/out/agentpprof-install-r248/agentpprof-install-r248.json`, `docs/visexp/out/agentpprof-git-install-r253/agentpprof-git-install-r253.json`, `docs/visexp/out/agentpprof-pinned-rev-install-r254/agentpprof-pinned-rev-install-r254.json`, `docs/visexp/out/agentpprof-crate-package-r256/agentpprof-crate-package-r256.json` | partial | bounded fixed-session artifact smoke, public-safe generated-fixture clean/cached smoke, local clean-clone `agentpprof` pprof readback, local install smoke, GitHub-branch install smoke, pinned-revision GitHub install smoke, and local crate-package dry-run passed; no broad community-tool claim until crates.io publish/readback or external-machine setup, real report sanitization, llama.cpp path, full write-set audit, and external-developer feedback exist |
