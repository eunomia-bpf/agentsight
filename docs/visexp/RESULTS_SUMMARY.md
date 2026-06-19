# Results Summary: AgentFlame Semantic Effect Profiling

Last updated: 2026-06-19
Stage at update: analyze
Source/command: R170 full-history run plus `python3 docs/visexp/r189_tag_consolidation.py`, `python3 docs/visexp/r190_tag_consolidation_audit.py`, `python3 docs/visexp/r190_score_merge_audit.py`, `python3 docs/visexp/r196_long_tail_governance.py`, `python3 docs/visexp/r201_long_tail_sensitivity.py`, `python3 docs/visexp/r202_long_tail_regeneration_smoke.py --regenerate-limit 50 --load-timeout 240 --llama-timeout 60`, `python3 docs/visexp/r203_long_tail_promotion_gate.py`, `python3 docs/visexp/r205_long_tail_compaction_metrics.py`, `python3 docs/visexp/r209_reversible_display_map.py`, `python3 docs/visexp/r211_stack_examples.py`, `python3 docs/visexp/r212_display_compaction_ablation.py`, `python3 docs/visexp/r213_display_mode_drilldown_smoke.py`, `python3 docs/visexp/r214_long_tail_control_loop.py`, `python3 docs/visexp/r215_frontend_renderer_mode_smoke.py`, `python3 docs/visexp/r216_browser_dom_mode_smoke.py`, `python3 docs/visexp/r217_production_react_display_mode_smoke.py`, `python3 docs/visexp/r218_display_map_update_gate.py`, `python3 docs/visexp/r220_fresh_clone_agentpprof_smoke.py`, `python3 docs/visexp/r219_claim_readiness_gap_gate.py`, `python3 docs/visexp/r193_prepare_human_evidence_package.py`, `python3 docs/visexp/r194_human_evidence_preflight.py`, `python3 docs/visexp/r195_human_evidence_pipeline.py`, `python3 docs/visexp/r207_human_launch_readiness.py`, `python3 docs/visexp/r242_human_evidence_contract_smoke.py`, `python3 docs/visexp/r200_community_smoke.py`, `python3 docs/visexp/r131_semantic_ablation.py --input .agentsight/agentflame/r170-full-current --local-out .agentsight/agentflame/ablations-r224-r170/summary.json --out-dir docs/visexp/out/semantic-ablation-r224-r170`, `python3 docs/visexp/r223_projection_tradeoff.py`, `python3 docs/visexp/r225_prompt_span_duration_baseline.py`, `python3 docs/visexp/r237_agent_execution_witness_network_capture.py --run-id R238`, `python3 docs/visexp/r240_lineage_guard_regression.py`, `docs/visexp/LONG_TAIL_COMPACTION.md`, `docs/visexp/out/osdi-gate-review-r204.md`, `docs/visexp/out/osdi-rq-gate-review-r206.md`, `docs/visexp/out/osdi-gate-review-r208.md`, `docs/visexp/out/osdi-gate-review-r228.md`, `docs/visexp/out/osdi-gate-review-r239.md`, and `docs/visexp/out/osdi-gate-review-r241.md`
Additional R245/R246 source: `python3 docs/visexp/r245_claim_wording_consistency.py`, `python3 docs/visexp/r246_post_review_hygiene.py`, `docs/visexp/out/osdi-gate-review-r246.json`, and `docs/visexp/out/semantic-ablation-r224-r170/r224-rerun-metadata.json`.
Additional R247 source: `python3 docs/visexp/r247_human_evidence_distribution_bundle.py`, `docs/visexp/out/human-evidence-distribution-r247/human-evidence-distribution-r247.json`, and `docs/visexp/out/human-evidence-distribution-r247/agentflame-human-evidence-r247.tar.gz`.
Additional R248 source: `python3 docs/visexp/r248_agentpprof_install_smoke.py`, `docs/visexp/out/agentpprof-install-r248/agentpprof-install-r248.json`, and `agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl`.
Completeness: partial

## Headline Result

The current strongest evidence is a full local-session characterization over
real AgentSight-related Codex and Claude histories on this machine. AgentFlame
used a real local llama.cpp 3B model to assign one-word tags to session, prompt,
and LLM-call contexts, then folded tool/system behavior into semantic stacks.

The current R170 refresh analyzed 325 readable sessions, 142,468 raw tool
events, and 114,837 LLM events. It produced 183,714 system-effect observations
and collapsed them into 26,829 unique semantic system stacks, for a 6.848x
compression ratio. Removing session/prompt semantics causes heavy mixing:
nonsemantic stacks mix multiple semantic regions for 90.402% of observation
weight, and flat effect buckets mix 90.918%.

This supports the mechanism claim that semantic frames separate system-effect
regions that ordinary process summaries or nonsemantic folded stacks merge.
R224 further isolates which semantic axes matter on the same R170 denominator:
no-semantic stacks mix 90.402% of full semantic weight, session-only leaves
84.407%, prompt-only leaves 36.722%, and full session+prompt semantics leaves
0.000% by construction. Its non-dominant residual mixed weight drops from
44.716% with no semantic axis to 7.485% with prompt-only. R114 adds fixed-suite
live exact lineage over 20 real Codex tasks with negative controls. R191, R229,
R232, and R234 extend that evidence through target-process HTTP network rows,
controlled multi-workspace replication, controlled external-repository
replication, and a controlled expansion with one Claude command-mode task plus
two Codex HTTP-family target-network probes. R235--R238 then
test harder raw/multiprocess/Claude-launched network boundaries: R238 fixes the
record-command readiness race and makes direct HTTP/direct multiprocess
controls stable, but the official full run still has Codex/Claude-launched
target-network orphan or missing-action cases. R240 then turns two R239
implementation risks into regression checks: the command-root fallback joins
only the root process itself, and a BPF runtime target-child loopback test
captures bind/listen/connect while excluding an unrelated port. The project
therefore supports scoped exact-lineage mechanisms, not broad full-history,
arbitrary network, or Claude-launched coverage, and it still does not prove
user utility.

R189 adds a display-time canonical tag consolidation run over the R170
full-history artifacts. It preserves all folded weights while reducing
prompt-effect tags 263 -> 216, prompt-row tags 328 -> 279, LLM-event tags
1423 -> 1254, system stacks 26,829 -> 26,067, and token stacks 8569 -> 7661.
This is useful evidence for an auditable vocabulary-hygiene layer and a
candidate display-noise reduction proxy. It is not human tag adequacy evidence
and does not prove the merged tags are semantically redundant.

R190 adds the missing consolidation-rule ablation and audit packet. Raw,
alias-only, lexical-only, and profile-guarded variants produce prompt-effect
tag counts of 263, 241, 200, and 216 respectively; LLM-event tag counts of
1423, 1392, 868, and 1254; system-stack counts of 26,829, 26,612, 25,985, and
26,067. The result clarifies that lexical-only consolidation is much more
aggressive than the current profile-guarded policy. R190 exports 80
over-merge proxy rows and 80 under-merge proxy rows with blank audit labels; it
is an audit protocol, not correctness evidence.

R190-score adds the scoring bridge for that audit packet. The current run over
the blank 160-row packet reports `human_labels_empty`, 0 final labels, paired
coverage 0.0%, and `canonicalization_quality_supported=false`; over-merge and
under-merge rates remain `n/a` until two independent labeler sheets and any
adjudication are supplied.

R196 adds a long-tail governance pass over the R170/R189 artifacts. It preserves
raw tags and classifies display actions instead of collapsing the tail into
`other`: 231 existing canonical merges, 114 review-merge rows, 39 regeneration
candidates, 2 contextual-split candidates, 1,241 kept rare distinct tags, and
184 kept head tags. Review-required support is 0.938% for session tags, 3.258%
for prompt tags, and 1.376% for LLM-call tags. This is a mechanism/review
packet, not semantic adequacy or merge-quality evidence.

R201 stress-tests the long-tail governance thresholds and generic/noisy
vocabulary. Review-required support stays nearly flat at 1.926%-1.931% across
seven variants, while the higher-tail-threshold variant drops baseline-head
stability to 65.217%. R202 then exercises the optional regeneration path with
the local llama.cpp server: all 41 regenerate/split rows return grammar-valid
one-word candidate tags, with 32 changed from the raw tag and 9 unchanged. R203
converts those candidates into a 41-row promotion-review protocol with two
blank reviewer sheets, 0 final labels,
`long_tail_promotion_review_supported=false`, and
`canonical_map_updated=false`. These are semantic compaction and governance
artifacts; they do not prove tag adequacy or merge quality.

`docs/visexp/LONG_TAIL_COMPACTION.md` now defines the intended compaction
contract: immutable raw tags, versioned canonical maps, fixed governance
actions, bounded local-LLM regeneration packets, paired promotion review, and
metrics for raw/canonical unique tags, tail mass, review-required support,
head stability, regeneration validity, and promotion acceptance. This makes
the long-tail mechanism explicit, but it does not change any human-evidence
gate.

R205 computes that metric packet over the current generated artifacts. Overall,
raw unique tag strings are 1,546 and canonical unique tag strings are 1,364
(11.772% reduction). Top-20 support coverage increases from 93.683% to 95.186%
after the current canonical overlay. Long-tail support is 1.746% and
review-required support is 1.926%. The same packet records 41/41 grammar-valid
R202 regenerated candidates, 0 R203 final promotion labels, 0.0% R203 paired
label coverage, and `n/a` R190 over/under-merge rates. Its input-consistency
check matches all 1,811 R196 rows to R189 with 0 canonical mismatches and
231/231 auto-canonicalize rows coming from R189 merge rows. This is a measurable
compaction artifact, not a quality, adequacy, or utility claim.

R209 makes that compaction layer directly consumable by renderers and reviewers.
It reads only generated R196/R203/R205 artifacts and emits an active display
map, a complete raw-tag drilldown index, and a reviewed display-map diff file. The
current run covers 1,811/1,811 raw tag rows, exposes 1,509 active display
labels, applies only 63 deterministic alias rows as active display merges, keeps
168 R189 lexical/profile merges as pending merge candidates, keeps 41
regenerated labels as candidate-only rows, emits 0 reviewed diff rows, records
0 hidden `other` rows, preserves drilldown support, and stores complete raw-tag
membership for every display bucket. It does not activate unreviewed profile
merges, regenerated labels, or any canonical-map update.

R212 then ablates that session/prompt display policy over the generated R170
semantic-system folded stacks. It preserves the 183,714 total system-effect weight in all four
variants. Raw stacks are 26,829; alias-only and R209 conservative display both
produce 26,612 stacks with 48 session tags and 241 prompt tags; the hypothetical
profile-guarded-candidate-applied view produces 26,067 stacks with 45 session
tags and 216 prompt tags, but it would activate unreviewed profile merges over
2.532% of system-effect weight. For selected collapsed behaviors, R209 reduces
distinct prompt tags without changing top-prompt mass: `git/read/ok` moves from
146 raw prompt tags to 133 under R209, while the hypothetical profile-guarded
view would move to 116; `cargo/test/ok` moves from 62 to 57 under R209 and 52
under profile-guarded. R212 is a display-policy ablation only; it does not
cover LLM/token display compaction, and false-merge and missed-merge rates
remain `n/a` until R190/R203 human labels exist.

R213 turns the R209 contract into a display-mode data-layer smoke for
raw/display/pending views. It reads generated R209 artifacts only and verifies
that all three modes preserve 482,398 total support. Raw mode exposes 1,811
buckets; display and pending modes expose 1,748 buckets; pending overlays 209
candidate rows and 323 review-required rows with 9,293 support, without changing
display membership. The strengthened oracle also checks that drilldown raw-tag
membership exactly matches the active display map. This supports the data-layer
drilldown contract only; it is not frontend-renderer, merge-quality, adequacy,
or user-utility evidence.

R214 makes the long-tail mechanism operational as a control loop rather than an
implicit cleanup rule. It reads only generated R196/R201/R202/R205/R209/R213
artifacts and emits dimension priorities, action gates, trigger gates, a
review-priority queue, a non-default rollup preview, and a regeneration version
policy. The current policy keeps 63 deterministic alias rows active, keeps 168
profile-merge candidates and 41 regenerated/split candidates pending, preserves
1,241 rare-distinct rows as raw labels, and exposes 323 review-required rows.
The rollup preview exactly partitions 1,811 raw-tag rows and 482,398 support
into seven governance buckets, but it is not default membership. Overall
long-tail support is 1.746% and review-required support is 1.926%, but
prompt-level review support is 3.258% and high-tail threshold head stability is
only 65.217%, so R214 deliberately fails those two control triggers. This is
the answer to the long-tail question: merge or regenerate candidates can be
proposed, but they cannot change default display membership without reviewed
display-map diffs.

R215 adds a frontend renderer-model smoke for that contract. It compiles
`frontend/src/utils/agentflameDisplayModes.ts` under TypeScript and runs a Node
harness that renders from R209 display-map/drilldown rows and cross-checks
R213/R214 summary counts. The frontend consumer sees the same raw/display/pending
shape as R213: 1,811 raw buckets, 1,748 display buckets, 1,748 pending buckets,
482,398 support preserved, 209 candidate
overlays, 323 review-required rows, 63 active merges, and 0 hidden `other`
rows. Two negative fixtures are rejected: corrupted raw drilldown membership
and treating a candidate display tag as active membership. This supports only a
frontend TypeScript renderer-model boundary, not a browser DOM, visual click
path, merge-quality, adequacy, or user-utility claim.

R216 moves that same display-mode contract into a real headless browser without
claiming the production React view. The script compiles
`frontend/src/utils/agentflameDisplayModes.ts` as ES browser modules, serves a
temporary localhost DOM harness, clicks raw/display/pending controls, and writes
both a DOM dump and screenshot. The browser-visible state preserves 482,398
support, shows 1,748 pending buckets, 209 candidate overlays, 323
review-required rows, and 63 active merges, while the same corrupted-drilldown
and candidate-as-active fixtures are rejected. This closes the browser DOM
harness gap, but production `AgentFlameView`, visual drilldown, merge quality,
C5 utility, and C6 adequacy remain untested.

R217 closes the production-rendering smoke for the default display view. It
builds the real Next static frontend, serves a minimal AgentFlame API fixture
with R209 display-map/drilldown artifacts, opens `/agentflame` in headless
Chrome, and checks the production `AgentFlameView` DOM. The visible default
mode is `display` with 1,748 buckets, 482,398 support, 3 mode buttons, 0
candidate/review overlays in the default view, and display-map membership
matching the raw drilldown. This is still not a click-path, visual drilldown,
merge-quality, adequacy, or user-utility result.

R218 turns the long-tail merge/regeneration answer into a checked update gate.
It reads generated R209 artifacts only and uses synthetic review fixtures over
real pending candidate rows. The gate accepts 2 final consensus/adjudicated
promotion rows into a preview display-map diff, rejects 4 unsafe rows
(`unclear`, weak single-label, hidden `other`, and missing-source cases),
preserves 1,811 raw keys and 482,398 support in the preview, and keeps
`canonical_map_updated=false`. This supports the reviewed-diff mechanism only;
because the review labels are synthetic, it is not promotion-quality or human
adequacy evidence.

R211 packages the R170/R189 outputs into reviewer-facing stack examples and
figure inputs. It reports that `rg` spans 176 prompt tags, `sed` spans 180,
`git` spans 147, and `cargo` spans 68. The `process:git;effect:read;status:ok`
bucket has 116 prompt tags and top-prompt share 24.977%, while
`process:cargo;effect:test;status:ok` has 48 prompt tags and non-top-prompt
weight 68.05%. This is RQ2 case-study evidence, not user-utility or tag-quality
evidence.

R193 packages the remaining human-evidence collection materials without adding
outcome data: two blank R124 labeler sheets, two blank R190 labeler sheets, two
blank R203 promotion labeler sheets, and a pointer to the already frozen R142
launch package. Its manifest records 0 R124 final labels, 0 R190 final labels,
0 R203 final labels, 0 R142 real responses, and all support gates false.

R194 preflights that package and the existing scorer outputs. It reports
`ready_for_human_collection_no_outcomes`: hashes match, R124/R190/R203 sheets
are blank, the R142 response template is blank, existing scorers are empty, and
all support gates remain false.

R195 adds the post-collection ingestion/scoring pipeline. The default run has
no returned CSV files in its inbox, so it reports `awaiting_human_inputs`, runs
no scorers, writes no R195 scored results, and keeps `c5_supported=false`,
`c6_adequacy_supported=false`, and
`canonicalization_quality_supported=false`,
`long_tail_promotion_review_supported=false`, and
`canonical_map_updated=false`. When real R142 responses or R124/R190/R203 label
sheets are supplied, R195 writes scored outputs under its own R195-specific
directory rather than overwriting the canonical empty gates.

R242 adds a synthetic contract smoke for that ingestion path. It generates
synthetic completed R142/R124/R190/R203 return files, verifies that R195 can
score all four groups into R195-specific output directories, and checks three
negative cases: one missing R124 labeler sheet is `partial_human_inputs`, a
duplicate/incomplete R142 response file becomes `scoring_failed`, and an empty
inbox remains `awaiting_human_inputs`. The canonical empty R124/R142/R190/R203
gates are preserved. Because every returned row is synthetic, R242 is contract
coverage only and does not count as C5/C6 outcome evidence.

R243 turns the launch materials into a static local collection kit. It generates
five participant HTML forms, six paired labeler HTML forms, a coordinator page
that merges participant exports into `r142-pilot-responses.csv`, a README, and a
manifest over the R187/R193/R207/R195 sources. The manifest records R142 70
response rows, R124 300 rows per labeler, R190 160 rows per labeler, R203 41
rows per labeler, no forbidden answer/scoring token hits outside the manifest,
and all C5/C6/canonicalization/promotion/map-update gates false. R243 reduces
return-format and merge friction only; it still contains 0 real responses and 0
human labels.

R244 smoke-tests that static kit. Headless Chrome loads the index, coordinator,
P01 participant, and R124/R190/R203 labeler pages. The export simulation writes
five synthetic participant CSVs and merges them into a 70-row
`r142-pilot-responses.csv` with P01-P05 each contributing 14 rows; the six
synthetic labeler CSVs preserve source fields and row counts while keeping
label cells blank. The outputs remain under the R244 directory, not the R195
inbox, so R244 is export-contract evidence only.

R245 audits the paper and evidence docs after R244. It reads generated gate
artifacts and current text only, does not read raw traces, and does not call an
LLM. The audit passes 9/9 hard evidence checks, 13/13 required wording checks,
and finds 0 forbidden strong-claim hits. It also records a useful bookkeeping
boundary: R219 remains an older readiness board, so R238/R240/R242-R244 must be
read as post-R219 addenda or through R245.

R246 records the post-R245 OSDI review and author hygiene response. It keeps
the project at Level 3/not weak accept because C5 still has 0 real participant
responses and C6 still has 0 real human labels. It also fixes two provenance
bookkeeping issues: R170 is now explicitly marked as `repo_dirty=true`
dirty-provenance mechanism evidence, and R224 now has
`r224-rerun-metadata.json` with `checker_id=R131` to clarify that the R224
paper result reruns the R131 semantic-axis checker over the R170 denominator.
R246 adds no outcome evidence.

R247 packages the R243 static collection kit into a sendable offline bundle.
The generated `agentflame-human-evidence-r247.tar.gz` has 17 members, 182,992
bytes, and a SHA-256 hash recorded in the summary. It includes participant
forms, labeler forms, the R142 coordinator merge form, a package README, a
manifest, and a seven-row return checklist for the exact R195 filenames. It
verifies local HTML links, excludes R244 synthetic exports, and scans the
tarball for answer-key, scorer, raw-trace, and synthetic-export tokens. This is
distribution readiness only; it still records `outcome_evidence_added=false`.

R219 summarizes the current evidence as a mechanical claim/RQ readiness gate.
It reads generated artifacts only, writes claim/RQ/next-experiment CSVs, and
reports `osdi_weak_accept_not_supported`: C1 is supported, C2 is supported for
syntax/latency, C3 is supported as mechanism, C4 is supported for the fixed
command-mode suite, C5 is unsupported, C6 is partial syntax/stability only, and
C7 is partial. It records 0 C5 participant responses and 0 C6 final adequacy
labels, making `R142-pilot-return` and `R124-labels-return` the P0 next rows.
The current rerun also includes R223/R225 in C3 evidence: projection tradeoffs
and prompt-span duration baselines strengthen the mechanism story but do not
change the weak-accept gate.

R224 reruns the semantic-axis ablation over the R170 current full-history
folded artifacts, so the system-axis rows share the same 183,714 effect
denominator as R212 display-policy rows. R246 adds
`docs/visexp/out/semantic-ablation-r224-r170/r224-rerun-metadata.json`, which
records `checker_id=R131` and prevents the R224 rerun identity from being
confused with a new checker or outcome result. R223 then turns RQ2 into an explicit
projection-selection experiment over R170-derived generated evidence. It reads
R224/R205/R209/R212/R219 artifacts only, does not read raw traces, and does
not call an LLM. The tradeoff table shows that no-semantic stacks are most
compact (11,967 stacks, 15.352x compression) but mix 90.402% of system-effect
weight and have up to 171 full semantic variants per bucket. Session-only
still mixes 84.407% of weight. Prompt-only is the best single semantic axis
for system effects: 24,703 stacks, 7.437x compression, 36.722% mixed weight,
and 7.485% residual mixed weight. Full session+prompt is the audit view:
26,829 stacks and 0.000% mixed weight by construction. R223 also summarizes
display-policy tradeoffs: R209's
conservative display policy matches alias-only, reducing stacks 26,829 ->
26,612 with 0.0% unreviewed active weight, while the hypothetical
profile-guarded policy would reduce stacks to 26,067 but activate unreviewed
profile/lexical merges over 2.532% of effect weight. The vocabulary overlay
reduces raw unique tag strings 1,546 -> 1,364 and improves top-20 support
coverage 93.683% -> 95.186%, while preserving raw drilldown and keeping
review-required support at 1.926%. That coverage is display-support
concentration, not tag correctness. This supports the framework claim that
semantic profiling is a pluggable projection over R170-derived evidence; it
does not support C5 utility, C6 adequacy, merge quality, or promotion quality.

R225 adds the missing duration-side baseline artifact without overclaiming it
as a true workflow trace. It reconstructs 2,858 prompt wall-clock spans from
R170 timestamps, with 2,854 nonzero spans over 324/325 sessions and 859.019
total prompt-duration hours. Its covered prompt-index effect denominator is
183,714/183,714 observations, and the expanded effect-by-prompt totals match
the folded file. Duration and effect-count prompt-tag rankings are
related but different: top-10 overlap is 7/10, top-20 overlap is 12/20, and
Spearman rank correlation is 0.623. Duration-only top-10 tags include
`network`, `compare`, and `source`, while effect-only top-10 tags include
`benchmark`, `debug`, and `explain`. R225 supports only a prompt-span duration
baseline and the claim that duration and system-effect projections answer
different questions; it may include idle/user-wait time and does not provide
active runtime, tool/LLM start-end spans, or C5/C6 outcome evidence.

R226 records the read-only OSDI subagent review after R225. The review keeps the
paper at not weak accept because C5/C6 are still missing, accepts R225 only as a
prompt wall-clock baseline, and flags denominator alignment as the main
methodological issue. The current R225 revision addresses that issue by
reconstructing covered prompt-index system effects from the same R170
`agentflame.json` and checking them against the folded file.

R220 adds a local clean-clone smoke for the new `agentpprof` user entrypoint.
It clones the repository into a temporary checkout, creates a public synthetic
Codex fixture under `.codex/sessions/...`, runs the real Rust CLI with the
deterministic regex tagger, and reads the generated pprof protobuf with
`go tool pprof -top`. It produces nonzero tasks/tools/tokens/files/network
projections with samples 6/4/190/3/1, writes folded/SVG/JSON/profile artifacts,
passes fixture-level expected-stack checks for tools/files/network/token
components, passes output-containment and privacy scans, and records no real
agent-history reads and no LLM calls. This strengthens C7 local artifact usability for
`agentpprof`, but it is not external adoption, llama.cpp setup evidence,
real-history public sanitization, C5 user utility, or C6 tag adequacy.

R248 adds an installed-CLI smoke for `agentpprof`. It commits a small public
Codex fixture under `agentpprof/examples/codex/sessions/...`, installs the local
package with `cargo install --path agentpprof --locked --force`, runs the
installed binary with explicit `--session-file`, `--tagger regex`, and
`--no-cache`, and verifies pprof/folded/JSON/SVG outputs plus `go tool pprof`
readback. It passes all required gates and records no private-history discovery,
no LLM calls, `c5_supported=false`, `c6_supported=false`, and
`weak_accept_supported=false`. This upgrades C7 local install-smoke evidence,
not community adoption or human-outcome evidence.

R249 fixes a C5 logistics gap that R247 left open: the sendable bundle is only a
five-participant pilot, while the scorer gates paper-scale C5 on at least 12
participants. R249 derives a separate paper-scale package from the frozen R142
task packets with 12 participant packets, 168 assignment/response rows, and a
nondefault assignment file for `score_user_task_results.py`. Every task-condition
has 2-3 replicates, the participant payload leak scan passes, and scoring the
blank template with the R249 assignment file returns `participant_results_empty`
with `c5_supported=false`. This is launch readiness only, not outcome evidence.

R228 records the read-only OSDI subagent review after R220. The review accepts
R220 only as narrow C7 local clean-clone/pprof-readback evidence, keeps the
project at not weak accept because C5/C6 remain missing, and flags two R220
polish points. The current R220 revision addresses them by adding
fixture-level expected-stack checks and by making parent worktree dirtiness a
non-gating provenance note.

R241 records the read-only OSDI subagent review after R240. It keeps the
project at Level 3/not weak accept: R240 is correctly scoped as regression
evidence and does not affect C5/C6. The author response regenerates R240
provenance, adds external regression-test status to the R240 manifest,
strengthens the target-child `NET_BIND` port assertion, adds R220 to the C7
claim row, and fixes the paper table's C4 wording.

## Completed Runs

| Run | Command/config | Result path | Status |
|-----|----------------|-------------|--------|
| R100 | Rust AgentFlame full local repo-related scan, 3B llama.cpp server, `tag_llm_calls=true` | `.agentsight/agentflame/latest/agentflame.json` | done |
| R101 | Rust unit/clippy verification after Unicode and unreadable-session fixes | `cargo test --manifest-path agentflame/Cargo.toml`; `cargo clippy --manifest-path agentflame/Cargo.toml -- -D warnings` | done |
| R110 | Live exact-lineage smoke over real AgentSight DB exports with harness-synthesized agent-run envelopes and llama.cpp root tags | `docs/visexp/out/live-lineage-r110.json` | partial |
| R111 | Native export exact-lineage smoke over the same real AgentSight DB exports after moving the envelope into `collector report export` | `docs/visexp/out/native-lineage-r111.json` | partial |
| R112 | DB-persisted backfill smoke over copies of the same real DB exports, then persisted-only export with observed projection disabled | `docs/visexp/out/native-lineage-r112.json` | partial |
| R113 | Capture-time `record -- <command>` session/tool envelope implementation smoke | `docs/visexp/out/capture-time-r113.json` | partial |
| R113-live | Five real read-only `codex exec` tasks wrapped with `agentsight record`, then exported and checked for lineage | `docs/visexp/out/live-record-r113.json` | partial |
| R114 | Twenty fixed Codex tasks under `agentsight record` with negative controls and scoped precision/recall analysis | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | done |
| R182 | Loopback-task Codex runs under `agentsight record` after enabling process `--trace-net`, with R114-style negative-control accounting and target-specific network oracle | `docs/visexp/out/live-network-r182.json`, `docs/visexp/out/live-network-r182.md` | partial/network flag smoke |
| R240 | Command-root lineage guard plus target-child process network regression tests after R239 review | `docs/visexp/out/lineage-guard-r240/lineage-guard-r240.json`, `docs/visexp/out/lineage-guard-r240/lineage-guard-r240.md` | done/regression; no C5/C6 outcome evidence |
| R122 | Redacted human adequacy label packet over 100 session, 100 prompt, and 100 LLM-call fragments | `docs/visexp/out/tag-adequacy-label-packet-r122.json` | packet only |
| R123 | 3B llama.cpp real-fragment stability benchmark over the R122 packet | `docs/visexp/out/model-benchmarks-r123.json` | done |
| R180 | Local 0.6B-/1B-/3B-class llama.cpp benchmark over the same R122 redacted fragments | `docs/visexp/out/model-benchmarks-r180.json`, `docs/visexp/out/model-benchmarks-r180.md` | done/syntax-stability; not adequacy |
| R124-scoring | Human tag-adequacy scorer over the current blank R122 packet | `docs/visexp/out/tag-adequacy-results-r124.json` | done/empty |
| R124-blinding | Blinded labeler-facing sheet that hides model/source/stability columns from R122 packet rows | `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.json` | done/protocol |
| R124-join | Join/adjudication protocol for two frozen blinded human-label sheets | `docs/visexp/out/tag-adequacy-label-join-r124.json` | done/protocol |
| R131 | Semantic-axis ablation over the same folded observations | `docs/visexp/out/semantic-ablation-r131.json` | done |
| R141-packet | Superseded deterministic C5 task benchmark draft over R114/R123/R131/full-run artifacts | historical `docs/visexp/out/user-task-benchmark.json` at commit `80fc9fc` | superseded by R142 |
| R142-packet/scoring | Same-event-slice C5 task benchmark packet, response-contract checker, and empty paper-scale scorer gate over R114/R123/R131/full-run artifacts | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-results.json` | packet/scorer only; no participants |
| R142-preregistration | Frozen C5 analysis contract before participant collection | `docs/visexp/out/user-task-preregistration-r142.json` | done/protocol; no participants |
| R184 | Mechanical weak-accept human-evidence gate over R124/R142 artifacts | `docs/visexp/out/weak-accept-gate-r184.json`, `docs/visexp/out/weak-accept-gate-r184.md` | `not_weak_accept`; C5/C6 human evidence missing |
| R185 | Read-only subagent OSDI gate review after R184 | `docs/visexp/out/osdi-gate-review-r185.md` | Level 3; next artifact is real R142 developer pilot |
| R186 | Read-only OSDI plan/RQ review and cleanup before human collection | `docs/visexp/out/osdi-plan-review-r186.md` | Level 3; R142 pilot next, R124 labels parallel/second |
| R187 | R142 pilot launch package with P01-P05 participant packets and a blank response CSV | `docs/visexp/out/user-task-pilot-r142/launch/manifest.json` | done/launch; no participants |
| R188 | Read-only OSDI plan review after R187 | `docs/visexp/out/osdi-plan-review-r188.md` | Level 3; still not weak accept; R142/R124 real evidence next |
| R160 | Bounded fixed-session artifact-usability smoke over 8 historical Codex sessions, with clean and cached AgentFlame runs | `docs/visexp/out/artifact-usability-r160.json` | done/bounded; C7 remains partial |
| R200 | Public-safe generated-fixture AgentFlame community smoke with managed llama.cpp clean/cached run | `docs/visexp/out/community-smoke-r200.json`, `docs/visexp/out/community-smoke-r200.md` | done/artifact-hygiene; no adoption claim |
| R220 | Fresh-clone `agentpprof` community smoke with public fixture and Go pprof readback | `docs/visexp/out/fresh-clone-agentpprof-r220/fresh-clone-agentpprof-r220.json`, `docs/visexp/out/fresh-clone-agentpprof-r220/pprof-top-r220.txt`, `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/tasks.pb.gz` | done/local clean-clone smoke; C7 remains partial |
| R170 | Current full-history AgentFlame refresh over all discovered repo sessions with real llama.cpp annotation calls | `docs/visexp/out/full-history-r170.json` | done/mechanism; not C5/C6 |
| R189 | Canonical tag consolidation over R170 folded stacks and tag profiles | `docs/visexp/out/tag-consolidation-r189/tag-consolidation-r189.json` | done/noise-control mechanism; not adequacy |
| R190 | Canonical tag consolidation ablation and merge-risk audit packet | `docs/visexp/out/tag-consolidation-audit-r190/tag-consolidation-audit-r190.json` | done/audit-packet-ready; no labels |
| R190-score | Merge-risk audit scorer and empty-label gate | `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json` | done/empty; no quality claim |
| R196 | Long-tail tag governance packet over R170/R189 artifacts | `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json` | done/governance mechanism; no adequacy claim |
| R201 | Long-tail governance sensitivity over R196 policy variants | `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json` | done/sensitivity; no adequacy claim |
| R202 | Long-tail candidate regeneration smoke over R196 regenerate/split rows | `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json` | done/candidate-only regeneration smoke; no adequacy claim |
| R203 | Human-gated promotion protocol for R202 regenerated long-tail candidates | `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json` | done/empty-promotion-gate; no adequacy or map-update claim |
| R205 | Long-tail compaction metrics over R189/R190/R196/R201/R202/R203 artifacts | `docs/visexp/out/long-tail-compaction-r205/long-tail-compaction-r205.json` | done/metrics-only; no adequacy or quality claim |
| R209 | Reversible display-map and raw drilldown contract over R196/R203/R205 artifacts | `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json` | done/display-map contract; no adequacy, quality, or map-update claim |
| R211 | Reviewer-facing label distribution, stack examples, and baseline-collapse figure inputs over R170/R189 artifacts | `docs/visexp/out/stack-examples-r211/stack-examples-r211.json` | done/RQ2 examples only; no C5/C6 outcome claim |
| R212 | Display-compaction ablation over R170 folded stacks and R196/R209 maps | `docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json` | done/display-policy ablation; no merge-quality or utility claim |
| R213 | Display-mode raw/display/pending drilldown data-layer smoke over R209 artifacts | `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json` | done/data-layer smoke; no frontend-renderer, merge-quality, or utility claim |
| R214 | Adaptive long-tail control loop over R196/R201/R202/R205/R209/R213 artifacts | `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json` | done/control-loop plus rollup/regeneration-version gates; no semantic-quality or map-update claim |
| R215 | Frontend TypeScript renderer-model smoke for raw/display/pending display modes | `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json` | done/renderer-model smoke; no DOM, quality, adequacy, or utility claim |
| R216 | Headless-browser DOM harness smoke for raw/display/pending display modes | `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json` | done/browser-DOM harness smoke; no production React view, visual drilldown, adequacy, quality, or utility claim |
| R217 | Production React `AgentFlameView` default display-mode smoke over R209 artifacts | `docs/visexp/out/production-react-display-r217/production-react-display-r217.json` | done/production-render smoke; no click path, visual drilldown, adequacy, quality, or utility claim |
| R218 | Reviewed display-map update gate over real R209 candidate rows with synthetic review fixtures | `docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json` | done/update-gate smoke; synthetic review only, no promotion-quality or map-update claim |
| R219 | Claim/RQ readiness gap gate over generated evidence artifacts | `docs/visexp/out/claim-readiness-r219/claim-readiness-r219.json` | done/readiness audit; `weak_accept_supported=false`, P0 next rows are R142/R124 |
| R224 | R170 semantic-axis ablation rerun with R131 checker | `docs/visexp/out/semantic-ablation-r224-r170/semantic-ablation-r131.json`, `docs/visexp/out/semantic-ablation-r224-r170/semantic-ablation-r131.md` | done/R170 denominator alignment for RQ2 |
| R223 | Projection tradeoff summary over R224/R205/R209/R212/R219 generated artifacts | `docs/visexp/out/projection-tradeoff-r223/projection-tradeoff-r223.json`, `docs/visexp/out/projection-tradeoff-r223/projection-tradeoff-r223.md` | done/RQ2 tradeoff artifact; no C5/C6 outcome claim |
| R225 | Prompt wall-clock duration baseline from R170 timestamps | `docs/visexp/out/prompt-span-duration-r225/prompt-span-duration-r225.json`, `docs/visexp/out/prompt-span-duration-r225/prompt-span-duration-r225.md`, `docs/visexp/out/prompt-span-duration-r225/prompt-span-duration.svg` | done/prompt-span duration baseline; covered effects 183,714/183,714; may include idle/wait time; no active runtime, true tool/LLM spans, or C5/C6 outcome claim |
| R226 | Read-only OSDI review after R225 integration | `docs/visexp/out/osdi-gate-review-r226.md` | not weak accept; R225 useful but C5/C6 remain blockers |
| R228 | Read-only OSDI review after R220 integration | `docs/visexp/out/osdi-gate-review-r228.md` | not weak accept; R220 useful for C7 local clean-clone scope but C5/C6 remain blockers |
| R241 | Read-only OSDI review after R240 regression guards | `docs/visexp/out/osdi-gate-review-r241.md` | not weak accept; R240 scoped correctly, C5/C6 remain blockers |
| R204 | Read-only OSDI gate review after long-tail promotion and human-evidence integration | `docs/visexp/out/osdi-gate-review-r204.md` | Level 3/not weak accept; no must-fix overclaim found |
| R206 | Read-only OSDI RQ/experiment-plan gate review after R205 and RQ summary revision | `docs/visexp/out/osdi-rq-gate-review-r206.md` | no material plan-wording blocker; Level 3/not weak accept because C5/C6 evidence missing |
| R208 | Read-only OSDI gate review after R205/R207 paper-plan alignment | `docs/visexp/out/osdi-gate-review-r208.md` | Level 3/not weak accept; latest revisions improve scoping/readiness but not outcome evidence |
| R192 | Read-only subagent OSDI gate review after R190-score | `docs/visexp/out/osdi-gate-review-r192.md` | Level 3; R190-score strengthens gate only |
| R193 | Human-evidence collection package for R142/R124/R190/R203 | `docs/visexp/out/human-evidence-r193/manifest.json` | done/collection-ready; no outcome evidence |
| R194 | Human-evidence collection preflight gate | `docs/visexp/out/human-evidence-preflight-r194.json` | done/preflight-ready; no outcome evidence |
| R195 | Human-evidence ingestion/scoring pipeline | `docs/visexp/out/human-evidence-pipeline-r195.json` | awaiting inputs; no outcome evidence |
| R207 | Human-evidence launch-readiness audit and R195 return-file mapping | `docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json` | launch-ready/no outcomes; five packets, blank sheets/templates, clear return names |
| R242 | Synthetic R195 human-evidence contract smoke | `docs/visexp/out/human-evidence-contract-r242/human-evidence-contract-r242.json` | done/contract-smoke; synthetic only, no C5/C6 outcome evidence |
| R243 | Static human-evidence collection kit | `docs/visexp/out/human-evidence-collection-kit-r243/collection-kit-r243.json` | done/collection-kit; static forms and R142 merge page, no outcome evidence |
| R244 | Static collection-kit form/export smoke | `docs/visexp/out/human-evidence-collection-kit-export-smoke-r244/collection-kit-export-smoke-r244.json` | done/export-smoke; Chrome load checks and synthetic CSV exports, no outcome evidence |
| R245 | Post-R244 claim-wording consistency audit | `docs/visexp/out/claim-wording-consistency-r245/claim-wording-consistency-r245.json` | done/wording-audit; hard checks 9/9, wording checks 13/13, forbidden strong-claim hits 0 |
| R246 | Post-R245 OSDI review hygiene and R170/R224 provenance bookkeeping | `docs/visexp/out/osdi-gate-review-r246.json`, `docs/visexp/out/osdi-gate-review-r246.md`, `docs/visexp/out/semantic-ablation-r224-r170/r224-rerun-metadata.json` | done/review-hygiene; not weak accept; no outcome evidence |
| R247 | Sendable offline human-evidence collection bundle | `docs/visexp/out/human-evidence-distribution-r247/human-evidence-distribution-r247.json`, `docs/visexp/out/human-evidence-distribution-r247/agentflame-human-evidence-r247.tar.gz` | done/distribution-ready; 17-member tarball, return checklist, no outcome evidence |
| R248 | Installed `agentpprof` public-fixture smoke | `docs/visexp/out/agentpprof-install-r248/agentpprof-install-r248.json`, `docs/visexp/out/agentpprof-install-r248/profiles/tasks.pb.gz`, `agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl` | done/install-smoke; installed CLI pprof readback, no private history, no C5/C6 outcome evidence |
| R248-review | Post-R247/R248 OSDI paper/artifact review | `docs/visexp/out/osdi-gate-review-r248.json`, `docs/visexp/out/osdi-gate-review-r248.md` | Level 3/not weak accept; paper hygiene and C7 install-smoke fixes applied, C5/C6 still missing |
| R249 | Paper-scale C5 participant launch package | `docs/visexp/out/user-task-paper-r249/manifest.json`, `docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv`, `docs/visexp/out/user-task-paper-r249/scored/user-task-results.json` | done/paper-scale launch-ready; 12 participants, 168 blank response rows, scorer accepts template as empty, no outcome evidence |
| R171 | Read-only subagent OSDI gate review after R170/R124-join planning | `docs/visexp/out/osdi-gate-review-r171.md` | done/review |
| R181 | Read-only subagent OSDI gate review after R180 local multi-model benchmark | `docs/visexp/out/osdi-gate-review-r181.md` | done/review; still not weak accept |
| R060 | legacy Python prototype pipeline over sampled sessions | `docs/visexp/out/pipeline-report.json` | legacy, superseded for headline scale |
| R020a | fixture exact-effect lineage checker | `docs/visexp/out/effect-lineage-smoke.json` | partial, fixture only |

## Artifact Usability Smoke

R160 verifies that the Rust CLI can regenerate a bounded local artifact package
without the legacy Python harness. It uses 8 fixed historical Codex session
files with LLM-call tags enabled. The clean run wrote
`.agentsight/agentflame/r160-smoke-fixed`, produced the dashboard, folded stack
files, SVGs, and tag cache, made 60 uncached llama.cpp calls over 76 tag
requests, and took 1.64 s. The cached rerun used the same inputs and output
directory, served 76/76 tag requests from `tags.json`, made 0 model calls, and
took 0.11 s.

The verifier result is `docs/visexp/out/artifact-usability-r160.json`. It
checks expected artifact keys, folded-total equality, redacted prompt previews,
generated report path containment, dirty raw-trace-like paths, a sanitized
fixed-input manifest, and clean/cached input equality. The manifest hash is
`11ae4fb2c96a2d1478aa1525`, and it contains no raw prompts, absolute session
paths, or session filenames. This supports only an auditable bounded
artifact-path claim.

R200 adds a public-safe generated-fixture smoke that does not read real
`.codex` or `.claude` traces. It starts a managed llama.cpp server, runs the
Rust AgentFlame CLI against one temporary explicit Codex fixture, then reruns
the same command to check fixed-input caching. The clean run made 5 llama.cpp
tag calls, the cached rerun made 0 tag calls with 5/5 cache hits, the run
produced the expected dashboard/folded/SVG/tag-cache artifacts, folded totals
matched, prompt previews stayed redacted, no raw-trace-like git paths became
dirty, and the committed summary redacts local paths. This strengthens C7
artifact hygiene only: it is not a fresh-clone install on another machine, not
public-release sanitization of real `.agentsight` reports, not full write-set
containment, and not external developer feedback.

R220 moves the public-fixture path to the productized `agentpprof` entrypoint
and a clean local clone. It uses no llama.cpp server, so it validates the
deterministic regex baseline and pprof export path rather than LLM tag quality.
The smoke writes `tasks.pb.gz`, `tools.folded`, `tokens.json`, `files.folded`,
`network.folded`, and `tools.svg`, then verifies `go tool pprof -top` reports
6 total task samples and the expected fixture stacks are present for read/test,
network, file, and token components. The clean clone was empty before fixture creation; the
only clone-local dirty path after the run was the synthetic `.codex/` fixture;
all committed outputs stayed under `docs/visexp/out/fresh-clone-agentpprof-r220`.
This closes the local clean-clone/readback gap, but external-machine install,
real report sanitization, llama.cpp setup, and developer feedback remain open.

## Current Full-Run Metrics

| Metric | Value |
|--------|-------|
| Generated at | 2026-06-15T10:30:26Z |
| Readable sessions analyzed | 325 |
| Source cohorts | `codex=198`, `claude=50`, `claude-subagent=77` |
| Skipped sessions | 1 unreadable root-owned Claude JSONL, recorded in `warnings` |
| Raw tool events | 142,468 |
| Raw LLM events | 114,837 |
| Prompt rows | 2,859 |
| Unique prompt tags | 328 |
| Invalid prompt tags | 0 |
| LLM-call tags | 114,837 |
| Unique LLM-call tags | 1,423 |
| Invalid LLM-call tags | 0 |
| System observations | 183,714 |
| Unique semantic system stacks | 26,829 |
| Semantic system compression | 6.848x |
| Max system stack reuse | 6,004 |
| Nonsemantic mixed buckets | 4,685 |
| Nonsemantic mixed weight | 166,081 / 183,714 = 90.402% |
| Flat mixed buckets | 4,529 |
| Flat mixed weight | 167,030 / 183,714 = 90.918% |

## Tagger Result

| Metric | Value |
|--------|-------|
| LLM backend | llama.cpp HTTP server |
| Model | `qwen2.5-3b-instruct-q4_k_m.gguf` |
| Tag requests | 118,021 |
| Cache hits | 82,886 |
| llama.cpp HTTP calls | 35,136 |
| Successful final tags | 35,135 |
| Final failures | 0 |
| Tag cache entries after run | 64,477 |

The one-call difference between HTTP calls and final successes is consistent
with a retry after one invalid intermediate output; no final tag failed. This is
important for RQ1: syntax validity is strong in the completed run, while
semantic adequacy still needs human labels.

R122/R123 add a real-fragment stability check over the same local trace corpus:
R122 sampled 300 redacted fragments from 294 parsed sessions (100 session, 100
prompt, 100 LLM-call), and R123 ran the local 3B llama.cpp server over those
fragments with three identical repeats each. R123 produced 900/900 valid tags,
285/300 exact-stable fragments (95.000%), p95 request latency 31 ms after a
1002 ms model load, and no committed fragment previews in the benchmark summary.
This supports 3B syntax/latency/stability, but not human adequacy.

R180 reruns the same 300 redacted R122 fragments over three locally available
GGUFs with `--reasoning off`: 0.6b produced 900/900 valid tags, 299/300
exact-stable fragments, and p95 23 ms latency after a 2529 ms load; TinyLlama
1.1b produced 900/900 valid tags, 279/300 exact-stable fragments, and p95 18 ms
after a 1002 ms load; the 3b model reproduced 900/900 valid tags, 285/300
exact-stable fragments, and p95 32 ms after a 1003 ms load. This removes the
previous "no 0.6B/1B local result" gap for syntax/stability, but it is not a
controlled same-family scaling experiment. It also exposes an adequacy warning:
the 1.1b run collapses most outputs to localization/localized variants despite
passing the one-word grammar.

R124-scoring adds the missing scorer path for human adequacy labels without
inventing labels. On the current blank R122 packet it reports
`human_labels_empty`, 300 packet rows, 300 candidate tags, 0 final labels, no
adequacy percentage, and `adequacy_supported=false`. This keeps C6 partial while
making the next human-label run mechanically auditable.

## Canonical Tag Consolidation

R189 reads only the generated R170 `agentflame.json`,
`semantic-system.folded.txt`, and `semantic-token.folded.txt`; it does not
rescan or mutate raw agent traces. It preserves raw one-word tags and writes an
auditable `raw_tag -> canonical_tag` mapping.

| Dimension | Raw unique | Canonical unique | Top-20 coverage before | Top-20 coverage after |
|-----------|-----------:|-----------------:|-----------------------:|----------------------:|
| Session effect | 53 | 45 | 99.465% | 99.714% |
| Prompt effect | 263 | 216 | 90.445% | 92.720% |
| Prompt rows | 328 | 279 | 79.573% | 83.666% |
| LLM events | 1,423 | 1,254 | 94.546% | 95.337% |
| LLM tokens | 1,423 | 1,254 | 99.999% | 100.000% |

The canonical folded outputs preserve totals: system stacks reduce
26,829 -> 26,067 with the same 183,714 system-effect weight; token stacks reduce
8569 -> 7661 with the same token weight. Example high-confidence merges include
`testcodex -> test`, `docsupdate -> docs`, `rootpidrefs -> trace`, and
`jsonokno -> verify`. Rows below the auto-merge threshold stay as review
suggestions.

R189 reports merge mechanisms separately. Applied merges are 8 dictionary
aliases and 3 lexical+profile merges for session tags, 24 aliases and 25
lexical+profile merges for prompt tags, and 31 aliases plus 140
lexical+profile merges for LLM-call tags. There are no profile-only merges in
this prototype, so the result should be read as alias/lexical consolidation
guarded by behavior profiles, not as proof of a learned semantic taxonomy.

R190 compares consolidation rules directly:

| Variant | Prompt-effect tags | LLM-event tags | System stacks | Token stacks |
|---------|-------------------:|---------------:|--------------:|-------------:|
| raw | 263 | 1,423 | 26,829 | 8,569 |
| alias-only | 241 | 1,392 | 26,612 | 8,190 |
| lexical-only | 200 | 868 | 25,985 | 7,169 |
| profile-guarded current | 216 | 1,254 | 26,067 | 7,661 |

The `merge-risk-audit-packet-r190.csv` file contains blank `audit_label` and
`audit_notes` columns. R190-score reads the same packet and currently reports
`human_labels_empty`: 160 rows, 0 final labels, paired coverage 0.0%,
`canonicalization_quality_supported=false`, and no over-merge/under-merge rate.
The required next step is human review of these rows to estimate merge quality.

R196 extends this into an explicit long-tail governance packet. It classifies
all 1,811 observed raw tags across session, prompt, and LLM-call dimensions:
231 are existing R189 canonical merges, 114 are R189 review-merge rows, 39 are
profile-only regeneration candidates, 2 are contextual-split candidates, 1,241
are kept rare distinct tags, and 184 are kept head tags. The key design choice
is conservative: multi-peak semantic head tags such as `refactor`, `review`,
or `design` are not split automatically merely because they touch many
process/path buckets. Regeneration and contextual split are reserved for
generic/noisy tags such as `update`, `codex`, or `ignored`. The review packet is
ready with 323 review-required rows and 0 accepted review labels, but it is not
a human adequacy result.

R201 adds a policy-sensitivity check for that governance layer. It reruns the
R196 decision logic over seven threshold and generic-vocabulary variants.
Baseline review-required support is 1.926% of total support; the worst variant
is expanded generic vocabulary at 1.931%. Lower and higher tail thresholds move
long-tail support from 0.921% to 3.030%. The higher-tail-threshold variant
lowers baseline-head stability to 65.217%, which is a reported policy risk. The
result strengthens the claim that review-required row/support counts are stable
within this grid, but it does not measure reviewer time and does not prove
adequacy or merge quality.

R202 exercises the optional llama.cpp regeneration path for the R196 rows that
were already routed to regeneration or contextual split. It attempts all 41
candidate rows with the local qwen2.5-3B GGUF server: 41/41 outputs are
grammar-valid one-word tags, 0 are invalid, 32 differ from the raw tag, 9 are
unchanged, and 25 unique regenerated tags are proposed. The output is
candidate-only mechanism evidence: raw tags remain preserved, the canonical map
is not updated, and C5, C6, canonicalization quality, and community adoption
gates remain false. Only the top-level R202 summary and attempts CSV are
public-oriented; the nested `r196-with-regeneration/` details remain
local-audit-only until sanitized or excluded.

R203 adds the missing promotion gate for those R202 candidates. It consumes only
the public-oriented R202 attempts CSV, writes a 41-row promotion packet plus two
blank reviewer sheets and an adjudication template, and reports
`human_labels_empty`: 0 final labels, `long_tail_promotion_review_supported=false`,
`canonical_map_updated=false`, and `semantic_adequacy_supported=false`. This
turns long-tail regeneration into a reviewable protocol rather than an automatic
display-map mutation.

R209 then exports the reversible display-map contract that a UI can consume
without hiding the tail. `active-display-map-r209.csv` has one row for every
R196 raw tag; `display-drilldown-r209.csv` groups those rows under the active
display labels with support, review burden, top processes/effects/paths, and
complete raw-tag lists; `reviewed-display-map-diff-r209.csv` is empty because R203 has
0 final promotion labels. The committed artifact reports complete raw coverage,
0 hidden `other` rows, 63 active alias rows, 168 pending merge candidates, 41
candidate regenerated labels, and no map update.

R212 checks the session/prompt display-policy consequences directly on the R170
folded system stacks. It confirms R209's conservative display is exactly alias-only in the
current artifact: both variants have 26,612 stacks and affect 1.188% of
system-effect weight. Applying all profile-guarded candidates would reduce to
26,067 stacks and affect 3.72% of weight, but 2.532% of total effect weight would
come from unreviewed profile merges. This is useful reviewer evidence for why
R209 keeps those merges pending; it is not a claim that the pending merges are
correct, and it does not cover LLM/token display compaction.

R213 checks the display-mode data-layer consequence of that contract. The raw
mode has 1,811 buckets, display has 1,748 buckets, and pending has the same
1,748 display buckets while overlaying 209 candidate rows and 323
review-required rows. All modes preserve 482,398 support, pending membership is
unchanged, drilldown membership matches the active display map, and hidden
`other` buckets remain 0. This makes the display contract auditable, but it
still does not exercise the frontend renderer and cannot support quality or
utility claims.

R214 turns the long-tail display contract into a control loop. The committed
artifact keeps the default view active-alias-only with pending overlays: 63
active alias rows, 209 pending candidate rows, 323 review-required rows, and 0
candidate merges active by default. It also exposes a seven-bucket governance
rollup preview that preserves all 1,811 rows and 482,398 support while remaining
non-default, and it records that the 41 regenerated candidates have 0 promotable
rows without human labels. Its trigger gates intentionally fail
`prompt_review_budget` and `head_stability_under_high_tail_threshold`, which
means the current evidence argues against automatically raising tail thresholds
or promoting prompt-level candidates without human review.

R215 takes the next step into the frontend code path without claiming browser
coverage. The TypeScript display-mode module compiles under `tsc` and a Node
harness renders raw/display/pending buckets from R209 display-map/drilldown rows
while cross-checking expected R213/R214 summary counts. It preserves the same
482,398 support across modes, exposes 1,811
raw buckets and 1,748 display/pending buckets, overlays 209 candidates and 323
review-required rows only in pending mode, and rejects both corrupted drilldown
membership and candidate-as-active promotion. This closes the renderer-model
consumer gap left by R213, but a DOM renderer, visual drilldown path, and user
task utility remain untested.

R216 adds the browser DOM harness that R215 deliberately avoided. The script
compiles the same display-mode module as a browser ES module, serves a temporary
localhost page, and runs it under headless Chrome. The DOM harness
programmatically clicks raw, display, and pending controls; the final pending
view exposes 1,748 buckets, 482,398 support, 209 candidate overlays, and 323
review-required rows. The DOM checks verify these counts, re-run the membership
oracle, and reject corrupted raw membership plus unreviewed candidate promotion;
the screenshot is saved for manual inspection. R216 is still a harness, not the
production React `AgentFlameView`, and it is not a C5/C6 outcome.

R211 turns the same R170/R189 measurements into compact tables and SVG figure
inputs for the baseline-failure story. The top label shares are deliberately
shown as distributions, not as adequacy evidence: `review` is 25.231% of
sessions, while `refactor` is 39.824% of prompt system-effect weight and
83.575% of estimated LLM-token tag weight. The process split table shows why a
flat process summary is insufficient: `rg`, `sed`, `git`, `find`, `python3`,
and `cargo` each carry dozens to hundreds of distinct prompt tags. The
baseline-collapse examples keep concrete stacks such as
`process:git;effect:read;status:ok` and `process:cargo;effect:test;status:ok`
with their semantic prompt splits for paper figures.

The following top-tag tables are the original 205-session headline run, not the
R189 canonical R170 counts.

Top prompt tags:

| Tag | Count |
|-----|------:|
| `refactor` | 883 |
| `review` | 408 |
| `docs` | 113 |
| `test` | 112 |
| `analyze` | 108 |
| `design` | 103 |
| `research` | 66 |
| `trace` | 38 |
| `debug` | 20 |
| `validate` | 17 |

Top LLM-call tags:

| Tag | Count |
|-----|------:|
| `refactor` | 40,099 |
| `test` | 8,379 |
| `design` | 7,722 |
| `tokenize` | 7,037 |
| `analyze` | 5,848 |
| `report` | 3,998 |
| `review` | 3,922 |
| `docs` | 3,030 |
| `debug` | 1,609 |
| `build` | 1,262 |

## System-Effect Results

Top flat command/effect rows show why a semantic join is needed:

| Agent | Cohort | Tool | Command | Effect | Status | Count |
|-------|--------|------|---------|--------|--------|------:|
| codex | top | shell | sed | read | ok | 25,755 |
| codex | top | shell | rg | read | ok | 15,336 |
| codex | top | tool | write | process | ok | 12,824 |
| codex | top | shell | git | read | ok | 8,549 |
| codex | top | shell | nl | read | ok | 6,354 |
| codex | top | shell | cargo | test | ok | 2,903 |
| codex | top | shell | python3 | process | ok | 2,880 |
| codex | top | shell | docker | process | ok | 1,561 |

Flat rows reveal heavy behavior, but not why it happened. AgentFlame's semantic
stacks split those rows by session and prompt labels, for example separating
`cargo test` into `review`, `refactor`, `research`, `design`, and `test`
regions.

## Live Exact-Lineage Smoke

R110 moves C4 beyond fixture-only evidence, but only as a scoped smoke. Current
SQLite exports contain process/file/network effects but do not materialize
session/tool ancestry, so `docs/visexp/live_lineage_harness.py` adds a minimal
agent-run envelope around detected Codex/Claude root processes and tags those
roots with the local llama.cpp 3B model. It does not synthesize low-level
effects.

Across three real AgentSight DB exports, the checker covered and joined 182 of
318 raw effects. This is 57.233% raw coverage and 100.0% join within the covered
scope, not 100.0% coverage of all raw effects:

| Run | Roots | Synthetic sessions/tools | Raw effects | In-scope effects | Raw coverage | Joined | Orphans | In-scope join |
|-----|------:|------------------------:|------------:|-----------------:|-------------:|-------:|--------:|--------------:|
| codex-local | 2 | 2 / 2 | 90 | 48 | 53.333% | 48 | 0 | 100.0% |
| codex-attach | 2 | 2 / 2 | 168 | 86 | 51.190% | 86 | 0 | 100.0% |
| debug-ssl-auto | 4 | 4 / 4 | 60 | 48 | 80.000% | 48 | 0 | 100.0% |
| aggregate | 8 | 8 / 8 | 318 | 182 | 57.233% | 182 | 0 | 100.0% |

The aggregate join methods are `related_event_id=8` for root effects and
`pid_family_time_window=174` for descendant process-family effects.

This supports the lineage checker and process-family attribution path for
in-scope live effects. It does not yet prove native AgentSight export because
136 raw effects were outside detected agent roots and session/tool envelopes are
harness-generated.

R111 removes the Python harness from the export path. `collector report export`
now emits export-derived session/tool envelope rows from observed local prompts
and root process events. Running the same checker on the full exported snapshots
gives the same aggregate raw join, but with native exported sessions/tools:

| Run | Sessions | Tool calls | Raw effects | Joined | Orphans | Raw join |
|-----|---------:|-----------:|------------:|-------:|--------:|---------:|
| codex-local | 1 | 1 | 90 | 48 | 42 | 53.333% |
| codex-attach | 1 | 1 | 168 | 86 | 82 | 51.190% |
| debug-ssl-auto | 1 | 1 | 60 | 48 | 12 | 80.000% |
| aggregate | 3 | 3 | 318 | 182 | 136 | 57.233% |

R111 is still partial. It proves that native export can carry the minimal
session/tool ancestry needed by the checker, but it also exposes the remaining
coverage problem: 136 raw effects are still orphaned.

R112 adds a DB persistence smoke. It copies the same three real SQLite DBs,
runs `collector report materialize-observed`, verifies that SQLite contains 3
`sessions` rows and 3 `tool_calls` rows with
`view_source=sqlite_observed_agent_envelope`, and then exports with
`--no-observed-projection` so the snapshot must read persisted DB rows:

| Run | DB session rows | DB tool rows | Raw effects | Joined | Orphans | Raw join |
|-----|----------------:|-------------:|------------:|-------:|--------:|---------:|
| codex-local | 1 | 1 | 90 | 48 | 42 | 53.333% |
| codex-attach | 1 | 1 | 168 | 86 | 82 | 51.190% |
| debug-ssl-auto | 1 | 1 | 60 | 48 | 12 | 80.000% |
| aggregate | 3 | 3 | 318 | 182 | 136 | 57.233% |

R112 improves the artifact boundary from export-derived rows to DB-persisted
backfill rows. It does not improve the C4 verdict because raw join remains
182/318, and the session/tool rows are still produced by explicit backfill
rather than capture-time instrumentation.

R113 adds capture-time instrumentation for the command-recording path. When
`agentsight record -- <command>` starts a target child, the collector now writes
a SQLite `sessions` row and matching `tool_calls` row with
`view_source=record_capture_time_agent_envelope`, `tool_name=agent-run`, and
`related_pid=<target child pid>` before the child is continued. On target exit,
the same row ids are updated with end time, duration, status, and exit code.
The unit smoke verifies 1 session and 1 tool row in a temp SQLite DB. This fixes
the narrow "no capture-time row" objection for command-mode `record`; R113-live
below adds the fresh eBPF rerun.

R113-live adds the missing fresh live rerun. The harness runs five real
read-only `codex exec` tasks in this repository under `agentsight record`, then
exports each SQLite DB and runs the exact-lineage checker:

| Metric | Value |
|--------|------:|
| Codex tasks | 5 |
| Capture-time record sessions/tools | 5 / 5 |
| Process nodes | 243 |
| Raw effects | 508 |
| Joined effects | 508 |
| Orphan effects | 0 |
| Raw join | 100.0% |

All tasks succeeded and all five DBs contained
`record_capture_time_agent_envelope` session/tool rows. The important systems
change is session-scoped root-pid propagation in the capture path: 258 effects
joined through the observed process family, and 250 effects joined through
`root_pid_time_window`, covering short-lived helper processes whose intermediate
fork nodes do not appear as process nodes.

R114 scales this command-mode path to a fixed 20-task Codex suite with negative
controls. The suite includes read-only, edit, test/debug, dependency,
failure/retry, and disposable-workspace write tasks. The analysis scopes recall
to the retargeted agent process family and uses per-task negative-control
bursts to catch over-attribution:

| Metric | Value |
|--------|------:|
| Target tasks completed | 20 / 20 |
| Tasks with observed negative controls | 20 / 20 |
| In-scope effect events | 1,273 |
| Joined in-scope effect events | 1,273 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 100.0% |
| Recall | 100.0% |
| Observed negative-control effects | 3,170 |
| Negative-control effects joined | 0 |
| Raw join | 22.055% |

The raw join stays low by design because wrapper, sibling, and out-of-scope
effects remain orphaned rather than being attributed to the agent. This is the
right evidence for the paper's exact-lineage claim only within the fixed
command-mode suite; it is not yet broad full-history provenance.

## Dimension Projection Results

| View | Unique stacks | Total weight | Compression | Max reuse |
|------|--------------:|-------------:|------------:|----------:|
| `semantic-system` | 26,829 | 183,714 | 6.848x | 6,004 |
| `nonsemantic-system` | 11,967 | 183,714 | 15.352x | not primary |
| `prompt-system` | 24,703 | 183,714 | 7.437x | 6,310 |
| `session-system` | 15,027 | 183,714 | 12.226x | 10,130 |
| `semantic-token` | 8,569 | 31,805,830,937,143 | 3,711,731,933.381x | not primary |
| `llm-token` | 2,568 | 31,805,830,937,143 | 12,385,448,184.246x | 25,366,043,637,938 |

Token views are useful for source-local accounting but should not be used for
cross-agent cost claims until token normalization is audited.

R131 turns these projections into a mechanism ablation by grouping each
projection against the full semantic key. It checks total-weight equality,
matches `agentflame.json` report totals against folded inputs, and verifies
that generated folded files exactly match the script projections. Mixed bucket
weight counts the whole projected bucket if it contains more than one full
semantic key; residual mixed weight counts only the non-dominant variants
inside such buckets.

| Family | Variant | Total | Unique stacks | Mixed bucket weight | Residual mixed weight |
|--------|---------|------:|--------------:|--------------------:|----------------------:|
| system | no semantic | 183,714 | 11,967 | 90.402% | 44.716% |
| system | session only | 183,714 | 15,027 | 84.407% | 33.434% |
| system | prompt only | 183,714 | 24,703 | 36.722% | 7.485% |
| system | session + prompt | 183,714 | 26,829 | 0.000% | 0.000% |
| token | no semantic | 31,805,830,937,143 | 33 | 100.000% | 41.196% |
| token | prompt + LLM-call | 31,805,830,937,143 | 7,382 | 92.978% | 0.041% |
| token | session + prompt + LLM-call | 31,805,830,937,143 | 8,569 | 0.000% | 0.000% |

The system-effect result supports the paper's mechanism claim: prompt tags
carry most of the system-effect partitioning, while session tags add remaining
provenance context. The full 0.000% rows are construction checks, not
independent evidence of user value. The token result is narrower: LLM-call tags
help token navigation, but they do not replace the session axis for full token
provenance.

## Negative And Mixed Evidence

- C4 exact AgentSight lineage is supported for the fixed command-mode suite but
  partial broadly. R114 joins 1,273/1,273 scoped in-scope effects and rejects
  3,170 observed negative-control effects. R182 then exposed and fixed a
  missing record-mode network capture flag. R238 later fixes the record-command
  process-tracer readiness race by waiting for the `CLOCK_SYNC/start` barrier.
  A compact committed supplement summarizes 5/5 direct-only readiness
  repetitions, and the official full run records 4/4 runtime witnesses, 4/4
  witness ports observed, direct HTTP/direct multiprocess controls joined,
  13/16 target network effects joined, and 0/186 negative joins. C4
  network-workload coverage still remains partial because the
  Codex/Claude-launched rows have 3 target-network orphan or missing-action
  cases. The direct-only repetitions have no negative controls, so precision
  evidence comes from the official full run. R240 adds a synthetic lineage
  guard and runtime regression tests for command-root fallback and target-child
  network capture, but it is still checker/runtime regression evidence rather
  than broad workload support. R182 is implementation evidence for record-mode
  `--trace-net`; R238 is boundary/localization evidence, not proof of HTTP payload/URL
  reconstruction, arbitrary raw sockets, or broad Claude-launched coverage.
- C5 user utility remains unsupported. Task packets and scoring scripts exist,
  and R142-packet now provides 14 tasks, 8 primary utility tasks, 6
  limitation/comprehension tasks, 5 conditions, 70 leak-checked blinded packets,
  a P01-P05 assignment template, a hidden answer key, manifests, and an empty
  scorer output. The former span-like event-weight view is now explicitly named
  `event-count-proxy`, not span-duration. All five condition excerpts for each
  task share one `slice_id`, so the packet clears the same-event-slice fairness
  check. The scorer now validates assignment/packet consistency, rejects
  duplicate or partial real response CSVs, keeps paired task-level
  semantic-vs-baseline deltas as diagnostics, and gates paper-scale C5 on
  participant/task/order fixed-effect blocked permutation tests with Holm
  correction. R142-preregistration freezes the current bundle, assignment,
  answer key, response schema, primary tasks, exclusion rules, source hashes,
  event-count proxy boundary, and scorer thresholds before participant
  collection. R187 packages the frozen assignment into P01-P05 launch files and
  a blank 70-row response CSV, with a manifest check for no answer key, no
  forbidden oracle/scoring fields, zero real responses, and
  `c5_supported=false`. R249 additionally derives a paper-scale launch package
  from the same frozen task packets: 12 participants, 168 blank response rows,
  a nondefault assignment file, and 2-3 replicates for every task-condition;
  scoring the blank template still returns `participant_results_empty` and
  `c5_supported=false`. R188 independently reviews the post-R187 state and
  again records Level 3/not weak accept: R187 is launch material only, and the
  next real evidence rows are R142-pilot plus R124-labels.
  The current output is `participant_results_empty`, `c5_supported=false`, and
  `pilot_ready=false`; no real participant responses have been collected.
- C6 semantic adequacy is partial. The grammar is strong, but labels such as
  `agentsightsm`, `testcodex`, and `bashoutput` show that one-word tags need
  human adequacy measurement and possibly prompt repair. R124-scoring exists
  and currently records `human_labels_empty`; R124-blinding now gives labelers a
  sheet without model/source/stability fields; R124-join now validates the
  blinded sheet against the source packet and prepares an empty adjudication
  template. R190-score similarly records `human_labels_empty` for canonical
  merge-risk labels. R196/R201/R202/R203 add governance, sensitivity,
  candidate-only regeneration-smoke, and an empty promotion-gate protocol for
  the display layer, but these
  remain protocol/mechanism artifacts, not adequacy
  evidence.
- R131 is a mechanism ablation, not a usability result. It supports C3 and
  figure design, but not the C5 developer-utility claim.
- R170 refreshes the current full-history path without overwriting `latest`:
  325 sessions, 142,468 raw tool events, 114,837 raw LLM events, 183,714 system
  observations, 26,829 semantic system stacks, 82,886 tag-cache hits, 35,136
  fresh llama.cpp tag calls, 0 tagger failures, and folded totals matching the
  generated report. This strengthens mechanism reproducibility, not user
  utility or human tag adequacy.
- R171 independently re-reviewed the gate and still finds Level 3 evidence:
  R124-labels and R142/R151 participant responses remain the smallest path to
  weak accept.
- One root-owned Claude session could not be read. The run records this as a
  warning rather than claiming perfect trace coverage.

## Result Files Used

- `.agentsight/agentflame/latest/agentflame.json`
- `.agentsight/agentflame/latest/tags.json`
- `.agentsight/agentflame/latest/semantic-system.folded.txt`
- `.agentsight/agentflame/latest/nonsemantic-system.folded.txt`
- `.agentsight/agentflame/latest/session-system.folded.txt`
- `.agentsight/agentflame/latest/prompt-system.folded.txt`
- `.agentsight/agentflame/latest/llm-token.folded.txt`
- `docs/visexp/out/effect-lineage-smoke.json` for fixture checker status
- `docs/visexp/out/live-lineage-r110.json` for live in-scope C4 smoke status
- `docs/visexp/out/native-lineage-r111.json` for native export C4 smoke status
- `docs/visexp/out/native-lineage-r112.json` for DB-persisted backfill C4 smoke status
- `docs/visexp/out/capture-time-r113.json` for capture-time record-command implementation status
- `docs/visexp/out/live-record-r113.json` for fresh live Codex record lineage status
- `docs/visexp/out/live-record-r114.json` and `docs/visexp/out/live-record-r114-analysis.json` for fixed-suite live exact lineage
- `docs/visexp/out/live-network-r182.json` and `.md` for fixed-suite network
  exact-lineage smoke after enabling record-mode process `--trace-net`; current
  target-specific loopback/child-process network coverage remains partial
- `docs/visexp/out/agent-execution-witness-network-capture-r238/agent-execution-witness-network-capture-r238.json`
  and `.md` for the R238 readiness-barrier/network-witness boundary result:
  direct controls pass, Codex/Claude-launched rows remain partial
- `docs/visexp/out/lineage-guard-r240/lineage-guard-r240.json`, `.md`, `.csv`,
  and `lineage-guard-r240-snapshot.json` for command-root fallback and
  target-child network regression checks
- `docs/visexp/out/tag-adequacy-label-packet-r122.json` for the redacted adequacy-label packet
- `docs/visexp/out/tag-adequacy-results-r124.json` for the empty human-label scorer gate
- `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.json` and `.csv` for the blinded labeler-facing R124 sheet
- `docs/visexp/out/tag-adequacy-label-join-r124.json`, `.md`, and `docs/visexp/out/tag-adequacy-adjudication-template-r124.csv` for the R124 human-label join protocol
- `docs/visexp/out/model-benchmarks-r180.json` and `.md` for local multi-model
  real-fragment syntax/stability; `model-benchmarks-r123.json` remains the
  original 3B-only stability run
- `docs/visexp/out/semantic-ablation-r131.json` for semantic-axis ablation
- `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-participant-packets.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-manifest.json`, `docs/visexp/out/user-task-preregistration-r142.json`, and `docs/visexp/out/user-task-results.json` for the R142-packet C5 benchmark bundle
- `docs/visexp/out/user-task-pilot-r142/launch/manifest.json`, `participants/P01.md` through `participants/P05.md`, and `responses/user-task-response-template-r142-pilot.csv` for the R187 launch-only R142 pilot package
- `docs/visexp/out/full-history-r170.json` and `.md` for the current full-history refresh summary
- `docs/visexp/out/weak-accept-gate-r184.json` and `.md` for the current
  mechanical C5/C6 weak-accept human-evidence gate
- `docs/visexp/out/osdi-gate-review-r185.md` and
  `docs/visexp/out/osdi-plan-review-r186.md` plus
  `docs/visexp/out/osdi-plan-review-r188.md` for the latest read-only OSDI gate
  and plan reviews; earlier R171/R181 reviews remain historical checkpoints
