# AgentFlame Experiment Audit

Last updated: 2026-06-19
Stage at update: audit / supplement
Source/command: OSDI rubric audit over `docs/visexp/STATE.md`, `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/out/evaluation.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/live-network-r182.json`, `docs/visexp/out/model-benchmarks-r180.json`, `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-label-join-r124.json`, `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json`, `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json`, `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json`, `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json`, `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json`, `docs/visexp/out/long-tail-compaction-r205/long-tail-compaction-r205.json`, `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json`, `docs/visexp/out/stack-examples-r211/stack-examples-r211.json`, `docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json`, `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json`, `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json`, `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json`, `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json`, `docs/visexp/out/production-react-display-r217/production-react-display-r217.json`, `docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json`, `docs/visexp/out/claim-readiness-r219/claim-readiness-r219.json`, `docs/visexp/out/human-evidence-r193/manifest.json`, `docs/visexp/out/human-evidence-preflight-r194.json`, `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json`, `docs/visexp/out/human-evidence-contract-r242/human-evidence-contract-r242.json`, `docs/visexp/out/human-evidence-collection-kit-r243/collection-kit-r243.json`, `docs/visexp/out/human-evidence-collection-kit-export-smoke-r244/collection-kit-export-smoke-r244.json`, `docs/visexp/out/claim-wording-consistency-r245/claim-wording-consistency-r245.json`, `docs/visexp/out/community-smoke-r200.json`, `docs/visexp/out/user-task-results.json`, `docs/visexp/out/user-task-pilot-r142/launch/manifest.json`, `docs/visexp/out/weak-accept-gate-r184.json`, `docs/visexp/out/artifact-usability-r160.json`, `docs/visexp/out/full-history-r170.json`, `docs/visexp/out/lineage-guard-r240/lineage-guard-r240.json`, `docs/visexp/out/osdi-gate-review-r181.md`, `docs/visexp/out/osdi-gate-review-r185.md`, `docs/visexp/out/osdi-plan-review-r186.md`, `docs/visexp/out/osdi-plan-review-r188.md`, `docs/visexp/out/osdi-gate-review-r192.md`, `docs/visexp/out/osdi-gate-review-r204.md`, `docs/visexp/out/osdi-rq-gate-review-r206.md`, `docs/visexp/out/osdi-gate-review-r208.md`, `docs/visexp/out/osdi-gate-review-r239.md`, and `docs/visexp/out/osdi-gate-review-r241.md`
Additional R246 source: `docs/visexp/out/osdi-gate-review-r246.json`, `docs/visexp/out/osdi-gate-review-r246.md`, and `docs/visexp/out/semantic-ablation-r224-r170/r224-rerun-metadata.json`.
Completeness: partial

## Audit Verdict

Current maturity: Level 3 conference-paper mechanism evidence, not Level 4
systems narrative yet.

AgentFlame now has a credible systems mechanism story:

- local LLM semantic control-plane labeling at full-history scale;
- deterministic folded-stack projections and semantic/nonsemantic ablations;
- fixed command-mode, controlled external, and selected target-network exact
  lineage with negative controls;
- executable but empty user-task and tag-adequacy gates;
- bounded artifact-usability smoke with verified cached reruns, including a
  public-safe generated-fixture smoke.

It is not OSDI weak accept yet because two reviewer-facing claims remain
unsupported by outcome data:

1. C5 user utility has no participant responses.
2. C6 tag adequacy has no human labels.

The paper can be written as a strong mechanism/measurement-tooling paper only
if those gaps are made explicit. It cannot claim improved developer outcomes or
semantic correctness yet.

The independent read-only subagent gate reviews recorded in R171, R181, R185,
R188, and R192 agree with this audit: current maturity is Level 3, weak accept
is not yet supported, C5/C6 are correctly blocked, and the smallest next outcome
artifacts are scored R142/R151 participant responses and scored R124 human
adequacy labels. The current benchmark plan also keeps the non-duration
baseline named as `event-count-proxy`, not as a span-duration flamegraph.

R170 refreshes the current full-history AgentFlame path over all discovered
repo sessions without overwriting `.agentsight/agentflame/latest`: 325 sessions,
142,468 raw tool events, 114,837 raw LLM events, 183,714 system observations,
26,829 semantic system stacks, 35,136 fresh llama.cpp tag calls, 82,886 cache
hits, 0 tagger failures, and folded totals matching the report. This strengthens
C1-C3 mechanism reproducibility and C7 artifact confidence, but it is not human
tag adequacy, developer utility, broad exact lineage, or community adoption
evidence.

R171 adds a second read-only subagent gate review after the R124-join and R170
updates. It again classifies the work as Level 3 rather than weak accept and
identifies R124-labels plus R142/R151 participant responses as the smallest
non-fabricated outcome artifacts.

R180 adds a real local multi-model syntax/stability benchmark over the same 300
R122 redacted fragments: 0.6b, TinyLlama 1.1b, and 3b each produced 900/900
grammar-valid one-word tags, with exact stability of 299/300, 279/300,
and 285/300 and p95 latencies of 23/18/32 ms. This clears the previous
0.6B/1B-class syntax/stability gap for the local machine, but it is not a
controlled same-family scaling experiment and the 1.1b run's localization-like
collapse is negative adequacy evidence.

R181 adds a read-only subagent gate review after R180. It agrees that the R180
wording is correctly scoped to syntax/latency/stability and does not overclaim
human adequacy or controlled scaling. It still classifies the work as Level 3,
not weak accept, because C6 human labels and C5 participant responses remain
missing.

R182 adds a scoped network-capture smoke. The first loopback run exposed that
`agentsight record` was not passing process `--trace-net`; after enabling that
flag and rebuilding, two real loopback-task Codex runs completed with 35/35
low-level `codex` process network rows joined, 0 network orphans, 100.0%
precision/recall, and 0/604 observed negative-control effects joined. The
target-specific oracle found 0/0 loopback or expected child-process network
rows, so R182 is implementation evidence for record-mode network tracing, not
proof of loopback workload capture. It does not affect the C5/C6 outcome
blockers.

R191, R229, R232, and R234 strengthen C4 within explicitly controlled scopes:
R191 joins 4/4 target `python3` HTTP network rows with 0/310 negative-control
joins; R229 joins 394/394 controlled multi-workspace in-scope effects with
0/306 negative-control joins; R232 joins 353/353 external-repo in-scope effects
and 4/4 target network rows with 0/480 negative-control joins; and R234 joins
269/269 in-scope effects plus 8/8 target network rows across one Claude
command-mode task and two Codex HTTP probes with 0/331 negative-control joins.
These runs support scoped exact lineage, not arbitrary prompt compliance,
arbitrary repositories, raw sockets, or broad Claude-launched target-network
coverage.

R235--R238 deliberately probe that broader boundary. R235 shows only
single-process Codex TCP target rows are captured; Codex multiprocess TCP and
Claude HTTP/TCP probes execute but export 0 target rows. R236 localizes this to
target-row observation and lineage orphaning. R237 adds runtime witnesses and
shows all probes execute, but witness-port linkage and direct multiprocess
lineage remain partial. R238 fixes the record-command process-tracer readiness
race: a compact committed supplement summarizes 5/5 direct-only readiness
repetitions, and the official full run records 4/4 runtime witnesses, 4/4
witness ports observed, direct HTTP/direct multiprocess controls joined, 13/16
target network rows joined, and 0/186 negative-control joins. The direct-only
repetitions have no negative controls, so they do not independently support
precision.
Codex/Claude-launched rows still have 3 target-network orphan or missing-action
cases, so the audit keeps broad target-network coverage partial.

R240 responds to the R239 code/artifact review by turning two implementation
risks into executable regressions. The synthetic lineage guard proves the
`command_root_pid_self_time_window` fallback joins only root-self events and
does not accidentally join a sibling process just because it shares
`root_pid`. The BPF runtime test adds a target-child loopback case under
`-p --trace-net` and checks that bind/listen/connect are visible while an
unrelated port remains excluded; Rust unit tests cover readiness-wait behavior.
This reduces regression risk for C4 mechanics, but it is not new broad
agent-launched capture evidence and does not affect the C5/C6 blockers.

R241 adds an independent read-only gate review after R240. It agrees that R240
is correctly scoped as regression evidence and does not change the weak-accept
gate. The review found three hygiene fixes rather than new science: R240
provenance should be regenerated from a clean commit, the machine-readable R240
artifact should record the external BPF/Rust regression commands, and C7 should
include the already-generated R220 `agentpprof` clean-clone pprof readback
evidence. The author response applies those fixes and keeps the verdict at
Level 3/not weak accept because C5/C6 are still missing real human evidence.

R184 adds a mechanical weak-accept human-evidence gate over the existing R124
and R142 artifacts. It reports `not_weak_accept`: C5 is only
`ready_for_participant_collection`, C6 is only
`ready_for_independent_label_collection`, and subagent review, LLM-filled labels,
mock responses, placeholder rows, and syntax-only tag validity are disallowed as
C5/C6 evidence. R185 independently reviews that gate and again classifies the
work as Level 3 rather than weak accept.

R186 reviews the revised research plan and RQs against the OSDI plan-template
rubric. It keeps the maturity at Level 3, makes the executable order R142 pilot
first, R124 labels parallel/second, R151 only after R142 passes, and defers C4
network hardening plus R160/R200 artifact polish until C5/C6 are no longer
empty.

R189/R190/R190-score add a canonical tag consolidation protocol. R189 preserves
raw tags and folded totals while reducing display-time tag fragmentation; R190
compares raw, alias-only, lexical-only, and profile-guarded consolidation and
exports 160 merge-risk rows. R190-score currently reports `human_labels_empty`,
0 final labels, and `canonicalization_quality_supported=false`, so no
over-merge or under-merge rate can be claimed yet.

R196 extends this into a long-tail governance packet. It classifies all raw
session/prompt/LLM-call tags into existing canonical merges, review merges,
regeneration candidates, contextual-split candidates, kept rare distinct tags,
and kept head tags. It preserves raw tags and keeps semantic adequacy plus
canonicalization quality gates false.

R201 adds the missing sensitivity check for that governance packet. Across
seven policy variants, review-required support stays within 1.926% to 1.931%
of total support, while the higher-tail-threshold variant lowers
baseline-head stability to 65.217%. This is useful mechanism evidence and a
reported sensitivity risk, but not adequacy or merge-quality evidence.

R202 exercises the optional regeneration path on the R196 rows that were
already routed to regenerate or contextual split. It uses a managed local
llama.cpp server, attempts 41/41 candidate rows, gets 41 grammar-valid one-word outputs
and 0 invalid outputs, and keeps `canonical_map_updated=false`. This proves the
candidate path runs; it does not prove the regenerated labels are better. The
top-level R202 summary and attempts CSV are public-oriented, but the nested
`r196-with-regeneration/` detail directory is local-audit-only because it can
contain path/profile buckets.

R203 consumes only the public-oriented R202 attempts CSV and creates the
promotion-review protocol for regenerated candidates. It writes a 41-row packet
plus two blank reviewer sheets, reports 0 final labels, keeps
`long_tail_promotion_review_supported=false`, and keeps
`canonical_map_updated=false`. This instantiates the empty review-gate scaffold
after regeneration but does not prove promotion quality.

R205 summarizes the compaction metrics implied by R189/R190/R196/R201/R202/R203.
It reads only generated artifacts and does not update the canonical map. It
reports raw unique tag strings 1,546 -> canonical unique tag strings 1,364,
top-20 support coverage 93.683% -> 95.186%, long-tail support 1.746%, and
review-required support 1.926%. It also preserves the human-gate boundary:
R203 final labels remain 0, R190 over/under-merge rates are `n/a`, and
adequacy, merge-quality, utility, adoption, and map-update gates remain false.

R209 materializes the reversible display-map contract that R205 only measures.
It reads generated R196/R203/R205 artifacts, writes active display-map,
drilldown, and reviewed-diff CSVs, covers all 1,811 R196 raw-tag rows, exposes
1,509 active display labels, applies only 63 deterministic alias rows as active
display merges, keeps 168 lexical/profile merges pending, keeps 41 regenerated
labels candidate-only, records 0 reviewed diff rows and 0 hidden `other` rows,
preserves drilldown support, and stores complete raw-tag membership for every
display bucket. It makes C3's display aggregation auditable without changing
any C6 quality gate.

R212 adds the missing display-compaction ablation over generated R170 folded
stacks. It compares raw, alias-only, profile-guarded-candidate-applied, and R209
conservative display policies while preserving 183,714 total system-effect
weight. Raw has 26,829 stacks; alias-only and R209 conservative display both
have 26,612 stacks; profile-guarded-candidate-applied has 26,067 stacks but
would activate unreviewed profile merges over 2.532% of total effect weight.
This supports the conservative display-policy mechanism and exposes the cost of
activating pending merges; it still does not support merge quality or C5/C6
outcomes.

R213 adds the display-mode drilldown data-layer smoke missing from the R209/R212
contract. It reads only generated R209 artifacts and verifies raw/display/pending
mode summaries: raw has 1,811 buckets, display has 1,748 buckets, pending keeps
the same 1,748 buckets while overlaying 209 candidates and 323 review-required
rows, all modes preserve 482,398 support, and drilldown membership matches the
active display map. This supports only display data-layer auditability; it does
not exercise the frontend renderer and does not support merge quality, tag
adequacy, or developer utility.

R214 adds the adaptive long-tail control loop that the compaction design needs.
It reads generated R196/R201/R202/R205/R209/R213 artifacts only, keeps the
default view active-alias-only with pending overlays, and reports 63 active
alias rows, 168 pending profile-merge candidates, 41 pending regenerated/split
candidates, 323 review-required rows, and 0 active candidate merges. It also
emits a non-default seven-bucket rollup preview that preserves all 1,811 rows
and 482,398 support, plus a regeneration policy with 0 promotable rows without
human labels. It deliberately fails `prompt_review_budget` and
`head_stability_under_high_tail_threshold`, which is evidence against automatic
threshold raising or prompt-level candidate promotion without human review.

R215 adds a frontend renderer-model smoke for the same display contract. It
compiles the TypeScript display-mode module and runs a Node harness that renders
R209 display-map/drilldown rows while cross-checking R213/R214 summary counts.
The harness preserves 482,398 support, keeps display and pending membership
aligned at 1,748 buckets, overlays 209
candidate rows and 323 review-required rows only in pending mode, and rejects
both corrupted drilldown membership and candidate-as-active promotion. This
closes a TypeScript consumer gap, but it is explicitly not a browser DOM test,
not a visual drilldown test, and not C5/C6 outcome evidence.

R216 adds the browser DOM harness smoke missing from R215 while keeping the
claim boundary narrow. It compiles the same display-mode module as browser ES
modules, serves a temporary localhost page, runs headless Chrome, clicks
raw/display/pending controls, verifies visible DOM counts, and writes a DOM dump
plus screenshot. The browser run preserves 482,398 support, shows pending mode
with 1,748 buckets, 209 candidate overlays, 323 review-required rows, 63 active
merges, and 0 hidden `other` rows, and rejects the same corrupted-membership and
candidate-promotion negative fixtures. It is still a harness, not the production
React `AgentFlameView`, not a visual drilldown test, and not C5/C6 outcome
evidence.

R217 adds the production React default-rendering smoke missing from R216. It
builds the real Next static frontend, serves a minimal AgentFlame API fixture
with R209 artifacts, opens `/agentflame` in headless Chrome, and verifies that
production `AgentFlameView` renders the default display panel with 1,748
buckets, 482,398 support, 3 mode buttons, and matching display/drilldown
membership. It is not a production click-path test, not a visual drilldown test,
and not C5/C6 outcome evidence.

R218 adds the reviewed display-map update gate for the long-tail
merge/regeneration lifecycle. It reads generated R209 artifacts only and uses
synthetic review fixtures over real pending rows. The preview accepts 2 final
consensus/adjudicated diffs, rejects 4 unsafe rows, preserves 1,811 raw keys and
482,398 support, and creates no hidden `other` bucket. Because the labels are
synthetic, it is update-gate mechanics only, not promotion quality, adequacy, or
canonical-map-update evidence.

R219 adds a mechanical claim/RQ readiness gap gate over generated artifacts. It
records C1 as supported, C2 as syntax/latency supported, C3 as mechanism
supported, C4 as fixed-suite supported, C5 as unsupported, C6 as partial
syntax/stability only, and C7 as partial. Its overall status is
`osdi_weak_accept_not_supported`, with C5 responses 0 and C6 final adequacy
labels 0. This is an audit and next-run selection artifact, not outcome
evidence.

R211 packages the RQ2 case-study and figure inputs from generated R170/R189
artifacts. It reports six tag-distribution dimensions, 16 process-split rows,
14 baseline-collapse examples, and 12 top semantic-stack examples. The strongest
baseline-failure rows show that `rg` spans 176 prompt tags, `sed` spans 180,
`git` spans 147, and `cargo` spans 68; the concrete
`process:git;effect:read;status:ok` bucket has 116 prompt tags and 75.023%
non-top-prompt weight. R211 reads no raw traces, calls no LLM, and keeps C5/C6
and exact-lineage-breadth gates false.

R204 adds an independent read-only subagent gate review after the R203/R193/
R194/R195/R202 integration. It finds no must-fix overclaim for those artifacts
and agrees they are scoped as logistics, protocol, regeneration-smoke, and
promotion-gate artifacts. It still classifies the project as Level 3/not weak
accept because C5 has no real participant responses and C6 has no human labels.
It recommends naming R202/R203 as C6 protocol/gate artifacts rather than C6
adequacy evidence.

R206 reviews the revised RQ summary and experiment-plan execution slice. It
finds no material plan-wording blocker: novelty is framed as semantic
attribution of system effects, baselines/falsifiers/oracles are clear enough
for execution, and event-count proxy is not mislabeled as span duration. It
still classifies the project as Level 3/not weak accept because C5 participant
responses and C6 human labels remain missing.

R192 independently reviews the post-R190-score state and keeps the verdict at
Level 3/not weak accept. It finds no major R190-score overclaim, but confirms
that R190-score strengthens only the audit gate and cannot substitute for R124
human adequacy labels or R142/R151 user data.

R193 packages the human-evidence collection materials without changing any
claim verdict: two blank R124 labeler sheets, two blank R190 labeler sheets,
two blank R203 promotion sheets, and a pointer to the frozen R142/R187 launch
package. Its manifest records 0 R124 final labels, 0 R190 final labels, 0 R203
final labels, 0 R142 real responses, and false C5/C6/canonicalization/
promotion gates.

R194 preflights the R193 package against the frozen source artifacts and scorer
outputs. It reports `ready_for_human_collection_no_outcomes`: hashes match,
R124/R190/R203 sheets and the R142 response template are blank, existing
scorers are empty, and all support gates remain false.

R195 adds a conservative ingestion/scoring pipeline for returned human-evidence
files. Its current default run has an empty inbox, reports
`awaiting_human_inputs`, runs no scorer operations, and keeps
`c5_supported=false`, `c6_adequacy_supported=false`, and
`canonicalization_quality_supported=false`,
`long_tail_promotion_review_supported=false`, and
`canonical_map_updated=false`. This improves post-collection reproducibility
but remains logistics/protocol evidence until real participant responses and
human labels exist.

R242 adds a synthetic contract smoke around R195. It creates synthetic complete
R142/R124/R190/R203 return files and verifies that all four scorer operations
run into R195-specific output paths while all support gates remain false. It
also checks partial input, invalid duplicate R142 responses, and no-input
cases. The canonical empty gates are preserved. This is valuable ingestion
coverage, but it is explicitly not participant, labeler, or outcome evidence.

R243 packages the same human-evidence path as static local forms. It generates
5 participant forms, 6 paired labeler forms, a coordinator merge page for the
R195 `r142-pilot-responses.csv` file, a README, and a manifest with source
hashes. It preserves R142/R124/R190/R203 row counts, reports no forbidden
answer/scoring token hits outside the manifest, and keeps all human-evidence
support gates false. It is a collection-format hardening artifact only.

R244 checks that the R243 package is executable as a static browser artifact.
Headless Chrome loads representative index/coordinator/participant/labeler
pages, the synthetic participant exports merge to the 70-row R195 response
shape, and the labeler exports keep source fields and row counts with zero label
cells filled. The synthetic CSVs stay under the R244 output directory, so this
does not alter the R195 empty-input gate.

R245 checks that the paper and evidence docs still respect those claim
boundaries after R244. It reads only generated gate artifacts and current text,
performs no raw-trace reads and no LLM calls, and passes 9/9 hard evidence
checks plus 13/13 required wording checks with 0 forbidden strong-claim hits.
It also records that R219 is now an older readiness board: R238/R240/R242-R244
must be read as post-R219 addenda or through R245. This is audit hygiene only;
it creates no participant responses, human labels, or broader C4 support.

R246 records the post-R245 OSDI review and author hygiene response. The review
keeps the project at Level 3/not weak accept: C5 still has 0 real participant
responses and C6 still has 0 real human labels. The author response fixes
bookkeeping only: R170 is now explicitly treated as `repo_dirty=true`
dirty-provenance mechanism evidence, and R224 has companion metadata clarifying
that it is the paper-level rerun of the R131 semantic-axis checker over the
R170 denominator. It creates no outcome evidence.

R207 audits the launch handoff after R195. It confirms the sendable units are
present and still blank: five R142 participant packets, a 70-row response
template, two 300-row R124 sheets, two 160-row R190 sheets, and two 41-row R203
sheets. It also records the exact R195 inbox names for returned files. This
supports launch readiness only; it does not change C5, C6, canonicalization, or
promotion gates.

R208 reviews the plan and paper after the reversible long-tail compaction
boundary and R205/R207 paper alignment. It records the same Level 3/not weak
accept decision: R205/R207 improve readiness and scoping, but C5 requires real
participant responses, C6 requires R124 human labels, compaction quality
requires R190/R203 labels if claimed, C4 breadth requires target-specific
network/cross-repo evidence, and C7 requires external fresh-clone/community
artifact evidence.

## Claim-Evidence Alignment

| Claim | Evidence status | Result files | Audit decision |
|-------|-----------------|--------------|----------------|
| C1 semantic folded stacks over real histories | supported for this local repository | `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/evaluation.json` | pass |
| C2 local one-word tagging feasibility | supported for available local 0.6B-/1B-/3B-class syntax/latency; partial for semantic adequacy | `docs/visexp/out/model-benchmarks-r180.json`, `.agentsight/agentflame/latest/agentflame.json` | warn |
| C3 semantic partitioning beyond baselines | supported for partitioning; reversible display-map mechanics supported; merge/regeneration quality unsupported | `docs/visexp/out/semantic-ablation-r131.json`, `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json`, `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json`, `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json`, `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json`, `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json`, `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json`, `docs/visexp/out/stack-examples-r211/stack-examples-r211.json`, `docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json`, `docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json`, `docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json`, `docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json`, `docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json` | pass with quality/UI caveat |
| C4 exact semantic-effect lineage | supported for fixed and controlled scoped workloads; partial broadly and partial for Codex/Claude-launched target-network workloads | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/live-network-r182.json`, `docs/visexp/out/live-network-r191.json`, `docs/visexp/out/exact-lineage-replication-r229.json`, `docs/visexp/out/external-crossrepo-lineage-r232/external-crossrepo-lineage-r232.json`, `docs/visexp/out/broader-agent-network-lineage-r234/broader-agent-network-lineage-r234.json`, `docs/visexp/out/raw-claude-network-lineage-r235/raw-claude-network-lineage-r235.json`, `docs/visexp/out/multiprocess-claude-network-capture-r236/multiprocess-claude-network-capture-r236.json`, `docs/visexp/out/agent-execution-witness-network-capture-r237/agent-execution-witness-network-capture-r237.json`, `docs/visexp/out/agent-execution-witness-network-capture-r238/agent-execution-witness-network-capture-r238.json` | warn |
| C5 developer utility | unsupported | `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-results.json`, `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/human-evidence-collection-kit-r243/collection-kit-r243.json`, `docs/visexp/out/human-evidence-collection-kit-export-smoke-r244/collection-kit-export-smoke-r244.json` | fail for outcome claim |
| C6 tag adequacy | partial; syntax/stability only, with protocol/gate artifacts for canonicalization and long-tail review | `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-label-packet-r122.csv`, `docs/visexp/out/tag-adequacy-label-join-r124.json`, `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json`, `docs/visexp/out/long-tail-governance-r196/long-tail-governance-r196.json`, `docs/visexp/out/long-tail-sensitivity-r201/long-tail-sensitivity-r201.json`, `docs/visexp/out/long-tail-regeneration-r202/long-tail-regeneration-r202.json`, `docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json`, `docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json`, `docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json`, `docs/visexp/out/human-evidence-pipeline-r195.json`, `docs/visexp/out/human-evidence-collection-kit-r243/collection-kit-r243.json`, `docs/visexp/out/human-evidence-collection-kit-export-smoke-r244/collection-kit-export-smoke-r244.json` | fail for adequacy claim |
| C7 open-source usefulness | partial | `docs/visexp/out/artifact-usability-r160.json`: bounded fixed-session smoke passed, with expected artifacts, redacted previews, folded-total checks, generated report path containment, sanitized input manifest `11ae4fb2c96a2d1478aa1525`, clean/cached input equality, and a 76/76 cached rerun; `docs/visexp/out/community-smoke-r200.json`: public-safe generated fixture, 5 clean llama.cpp calls, 0 cached model calls, 5/5 cache hits, no real `.codex`/`.claude` reads, no prompt-preview leakage, and no raw-trace dirty paths | warn |

## Result Integrity Checks

| Check | Evidence | Status |
|-------|----------|--------|
| Full-run scale is not sampled-pipeline scale | `evaluation-summary.md` separates sampled audit scope from full Rust run; headline values come from `.agentsight/agentflame/latest/agentflame.json` | pass |
| Full-run raw traces are not committed | committed artifacts contain redacted previews, hashes, tags, counts, folded stacks, and summaries | pass |
| R170 full-current refresh keeps local reports private | committed R170 artifact is a sanitized summary; the 100MB local `agentflame.json` remains under `.agentsight/agentflame/r170-full-current` and is not committed | pass |
| R170 dirty provenance is explicit | R170 records `repo_dirty=true`; R246 treats it as dirty-provenance mechanism evidence rather than a clean release artifact run | pass |
| C3 ablation preserves totals | R224 reruns the R131 checker on R170 and records preserved system/token totals plus folded-file projection matches | pass |
| R224 rerun identity is clarified | `docs/visexp/out/semantic-ablation-r224-r170/r224-rerun-metadata.json` records paper-level `run_id=R224` and `checker_id=R131` for the R170-denominator rerun | pass |
| C4 precision is not raw join rate | R114 reports scoped in-scope precision/recall plus observed negative controls; raw out-of-scope effects remain orphaned | pass |
| C4 network supplement is scoped | R182 records 35/35 joined low-level `codex` process network rows after enabling record-mode `--trace-net`; R191/R232/R234 add scoped HTTP target-network successes; R235--R238 show raw/multiprocess/Claude-launched boundaries remain partial, with R238 fixing direct readiness but leaving 3 Codex/Claude-launched target-network orphan or missing-action cases. The paper must not claim arbitrary network workload coverage, HTTP payload/URL reconstruction, broad full-history coverage, or broad Claude-launched coverage | pass |
| C5 empty participant template cannot support utility | `user-task-results.json` is `participant_results_empty`, `c5_supported=false`, `pilot_ready=false` | pass |
| C5 R187 launch package is not outcome evidence | R187 contains P01-P05 blinded participant packets and a blank 70-row response CSV, with no answer key and no forbidden oracle/scoring keys, but records `real_response_count=0`, `pilot_ready=false`, and `c5_supported=false` | pass |
| C5 future real response CSV contract is enforced | scorer validates assignments, packets, duplicate rows, partial files, timing, and confidence | pass |
| C6 empty human-label packet cannot support adequacy | R124 is `human_labels_empty`, `adequacy_supported=false` | pass |
| C6 label join path does not fabricate labels | R124-join status is `ready_for_independent_label_collection`, records 0 labeler rows, exposes no joined-label output, and writes an empty adjudication template by default | pass |
| R190 canonical merge audit cannot support quality without labels | R190-score is `human_labels_empty`, has 160 rows, 0 final labels, paired coverage 0.0%, `canonicalization_quality_supported=false`, and no over-merge/under-merge rate | pass |
| R196 long-tail governance cannot support adequacy without review | R196 preserves raw tags and emits action counts plus a review packet, but keeps `semantic_adequacy_supported=false` and `canonicalization_quality_supported=false` | pass |
| R201 long-tail sensitivity cannot support adequacy | R201 reads only generated R170/R189 artifacts, reports seven policy variants plus review-required row/support stability, but keeps `semantic_adequacy_supported=false`, `canonicalization_quality_supported=false`, `developer_utility_supported=false`, and `community_adoption_supported=false` | pass |
| R202 candidate regeneration cannot support adequacy | R202 reads only generated R170/R189 artifacts, uses llama.cpp to produce 41/41 grammar-valid candidate tags for regenerate/split rows, but keeps `canonical_map_updated=false`, `semantic_adequacy_supported=false`, `canonicalization_quality_supported=false`, `developer_utility_supported=false`, and `community_adoption_supported=false` | pass |
| R203 empty promotion gate cannot support adequacy | R203 reads only the public-oriented R202 attempts CSV, writes a promotion packet and blank labeler sheets, but has 0 final labels, `long_tail_promotion_review_supported=false`, `canonical_map_updated=false`, and `semantic_adequacy_supported=false` | pass |
| R205 compaction metrics cannot support adequacy | R205 reads generated R189/R190/R196/R201/R202/R203 artifacts and reports raw/canonical coverage, tail mass, review burden, regeneration validity, and empty human gates, but keeps semantic adequacy, merge quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R209 reversible display map cannot support adequacy | R209 covers every R196 raw tag in an active display map, exports drilldown and reviewed-diff CSVs, keeps lexical/profile merges and regenerated tags candidate-only, records 0 reviewed diff rows and 0 hidden `other` rows, but keeps semantic adequacy, merge quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R211 stack examples cannot support utility or adequacy | R211 reads generated R170/R189 artifacts only, exports label distributions and baseline-collapse examples for RQ2 figures, records `raw_trace_read=false` and `llm_called=false`, but keeps developer utility, semantic adequacy, and exact-lineage breadth unsupported | pass |
| R212 display-compaction ablation cannot support quality | R212 reads generated R170/R196/R209 artifacts only, compares raw/alias/profile/R209 display policies with total effect-weight conservation, verifies R209 is alias-only active, and keeps false-merge/missed-merge, semantic adequacy, developer utility, and community adoption unsupported | pass |
| R213 display-mode drilldown smoke cannot support quality | R213 reads generated R209 artifacts only, verifies raw/display/pending mode support preservation, raw drilldown availability, active-map membership matching, pending membership stability, and 323 queued review rows, but keeps semantic adequacy, merge quality, frontend rendering, developer utility, community adoption, and canonical-map update unsupported | pass |
| R214 long-tail control loop cannot support quality | R214 reads generated R196/R201/R202/R205/R209/R213 artifacts only, exposes active/pending/review gates, a non-default rollup preview, regeneration-version policy, and failed control triggers, but keeps semantic adequacy, merge quality, frontend rendering, developer utility, community adoption, and canonical-map update unsupported | pass |
| R215 frontend renderer-model smoke cannot support DOM or utility | R215 reads generated R209/R213/R214 artifacts only, compiles and runs the TypeScript display-mode module under Node, verifies membership preservation and negative fixtures, but keeps browser DOM, visual drilldown, semantic adequacy, merge quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R216 browser DOM harness cannot support utility or adequacy | R216 reads generated R209/R213/R214/R215 artifacts only, compiles the display-mode module for browser execution, clicks raw/display/pending controls in a temporary DOM harness, saves a screenshot and DOM dump, but keeps production React view, visual drilldown, semantic adequacy, merge quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R217 production React render smoke cannot support utility or adequacy | R217 reads generated R209/R216 artifacts only, builds the real Next static frontend, verifies production `AgentFlameView` default display rendering, and saves a screenshot/DOM dump, but keeps click path, visual drilldown, semantic adequacy, merge quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R218 display-map update gate cannot support promotion quality | R218 reads generated R209 artifacts only and uses synthetic review fixtures over real pending rows to preview accepted/rejected display-map diffs, but keeps semantic adequacy, canonicalization quality, promotion quality, developer utility, community adoption, and canonical-map update unsupported | pass |
| R219 claim-readiness gate cannot upgrade claims | R219 reads generated artifacts only, reports `weak_accept_supported=false`, keeps C5 unsupported with 0 responses and C6 partial with 0 final labels, disallows synthetic/subagent evidence, and emits R142/R124 as P0 next rows | pass |
| R193 collection package is not outcome evidence | R193 has blank R124/R190/R203 labeler sheets, points to R142 launch materials, records 0 labels/responses, and keeps `c5_supported=false`, `c6_adequacy_supported=false`, `canonicalization_quality_supported=false`, `long_tail_promotion_review_supported=false`, and `canonical_map_updated=false` | pass |
| R194 preflight is not outcome evidence | R194 status is `ready_for_human_collection_no_outcomes`; it checks file hashes, blank R124/R190/R203 sheets, blank response template, empty scorers, and false support gates | pass |
| R195 ingestion pipeline is not outcome evidence | R195 status is `awaiting_human_inputs`; no required input files exist, no scorer operations ran, and C5/C6/canonicalization/promotion gates remain false | pass |
| R207 launch readiness is not outcome evidence | R207 status is `launch_ready_no_outcomes`; it checks five R142 participant packets, blank label sheets/templates, READMEs, and R195 return-file names, while keeping C5/C6/canonicalization/promotion gates false | pass |
| R242 synthetic contract smoke is not outcome evidence | R242 uses synthetic returned files to exercise R195 scoring, verifies partial/no-input/invalid-return cases, and preserves the canonical empty gates; it explicitly does not count as participant responses or human labels | pass |
| R243 static collection kit is not outcome evidence | R243 generates static participant/labeler/coordinator forms, validates row counts and R195 filenames, and records no forbidden answer/scoring token hits outside the manifest; it contains 0 real responses, 0 human labels, and false support gates | pass |
| R244 collection-kit export smoke is not outcome evidence | R244 uses headless Chrome and synthetic CSV exports to check static form/export shape; participant smoke rows and blank labeler exports stay under the R244 directory and are not placed in the R195 inbox | pass |
| R245 wording audit cannot upgrade claims | R245 passes hard evidence and wording checks while keeping `weak_accept_supported=false`, `c5_supported=false`, and `c6_adequacy_supported=false`; it only records post-R219 addendum bookkeeping | pass |
| R246 post-review hygiene cannot upgrade claims | R246 records OSDI review and provenance/metadata fixes while keeping `weak_accept_supported=false`, `c5_supported=false`, `c6_adequacy_supported=false`, and `outcome_evidence_added=false` | pass |
| R208 gate review is not outcome evidence | R208 records that reversible compaction and launch handoff revisions improve scoping/readiness, but it keeps Level 3/not weak accept because C5/C6/R190/R203 human evidence is still missing | pass |
| R241 gate review is not outcome evidence | R241 records an independent read-only review after R240 and keeps the project at Level 3/not weak accept; its author-response fixes are provenance/wording/test-manifest hygiene, not C5/C6 outcome evidence | pass |
| C5/C6 weak-accept gate cannot be cleared by non-human substitutes | R184 status is `not_weak_accept`; both C5 and C6 must pass their existing human-data scorers, while subagent review, LLM labels, mock responses, placeholder rows, and syntax-only validity are disallowed | pass |
| Post-R203 subagent review remains protocol evidence only | R204 reports Level 3/not weak accept, finds no must-fix R203/R193/R194/R195/R202 overclaim, and keeps the next real evidence rows as R142/R151 participant responses plus R124 human labels | pass |
| RQ/plan subagent review remains plan evidence only | R206 reports no material plan-wording blocker and accepts the semantic-attribution framing, but still reports Level 3/not weak accept because C5 participant responses and C6 human labels are missing | pass |
| Post-R187 subagent review remains protocol evidence only | R188 reports Level 3/not weak accept and names R142-pilot plus R124-labels as next real evidence; it does not upgrade C5/C6 | pass |
| C6/R180 model smoke is not adequacy evidence | R180 has 2700/2700 syntactically valid tags across local 0.6b/1.1b/3b models, but the interpretation explicitly says it does not measure human adequacy and is not controlled same-family scaling | pass |
| C7 bounded artifact smoke is not a community result | R160 uses 8 fixed historical sessions and records `claim_boundary`; it does not replace fresh-clone install testing or external developer feedback | pass |
| R200 public-safe smoke is not community adoption | R200 uses a generated fixture, records `reads_real_agent_traces=false`, makes 5 clean llama.cpp calls, makes 0 cached model calls with 5/5 cache hits, exposes 0 prompt previews in the committed summary, records no raw-trace dirty paths, and keeps `community_adoption_supported=false` | pass |
| C7 local report privacy boundary | R160 records that `.agentsight/agentflame/*/agentflame.json` is local/private and not public-release-ready because it contains trace roots/session metadata; the committed artifact is the redacted audit JSON | pass |
| C7/R170 mechanism refresh is not overclaimed | R170 records 35,136 fresh llama.cpp calls and folded integrity, but its claim boundary excludes C5/C6 outcome evidence, broad exact lineage, and community adoption | pass |
| C7 write-set scope is not overclaimed | R160 records raw-trace git hygiene and report path containment, but explicitly does not claim full pre/post write-set containment | pass |
| 0.6B/1B small-model syntax claims | R180 covers local available 0.6B-class and 1B-class GGUFs for grammar/latency/stability only | pass if scoped to syntax/stability; fail if claimed as adequacy or controlled scaling |

## Reviewer-Risk Ranking

### Must Fix: C5 User Utility

Reviewer concern: semantic flamegraphs may look plausible but not help users
answer real forensic questions.

Concrete fix: run R142 pilot under the frozen C5 preregistration using the
committed participant packets and score the resulting CSV with
`score_user_task_results.py`.

Decision gate: current paper cannot claim utility unless
`claim_analysis.claim_gate.c5_supported=true` for a paper-scale run, or a
narrower expert-pilot claim is explicitly labeled as pilot evidence.

### Must Fix: C6 Human Adequacy

Reviewer concern: one-word tags may be syntactically valid but noisy,
over-specific, or misleading.

Concrete fix: collect human labels with independent blank copies of
`docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`, join frozen labels
with `docs/visexp/r124_join_blinded_labels.py`, adjudicate disagreements using
`docs/visexp/out/tag-adequacy-adjudication-template-r124.csv`, then rerun
`score_tag_adequacy.py` on
`docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv`.

Decision gate: adequacy claim requires >=80% adequate labels, <=20%
generic/noisy labels, and agreement/adjudication evidence. If labels fail,
paper wording must call tags lossy navigation hints.

### Should Fix: RQ6 Artifact Usability

Reviewer concern: the project may be a one-off local analysis rather than a
community developer tool.

Current status: R160 passes as a bounded fixed-session local smoke, and R200
passes as a public-safe generated-fixture smoke. R160 connects to a
llama.cpp-compatible server, writes `.agentsight/agentflame/r160-smoke-fixed`,
verifies expected outputs with `artifact_usability_r160.py`, records
clean/cached runtime behavior, records a sanitized fixed-input manifest, checks
clean/cached input equality, and proves that a fixed-input rerun is fully
cached. R200 uses a temporary synthetic Codex fixture, does not read real
`.codex` or `.claude` traces, removes the generated fixture, and verifies
fixed-input cache behavior with 5 clean llama.cpp calls and 5/5 cached hits.

Remaining concrete fix: run an external-machine fresh-clone or clean-install
smoke with public setup instructions, choose a stable default sampling mode,
public-sanitize real local reports, run a real pre/post write-set audit, and
collect feedback from external developers. The failed 36-session cached attempt
is informative: dynamic discovery can see new live Codex session fragments
between runs, so cache experiments must pin `--session-file` inputs.

Decision gate: needed for artifact strength and open-source positioning, but
not a substitute for C5/C6 evidence.

## Claim Wording Boundary

Allowed:

- AgentFlame emits semantic folded-stack artifacts over real local Codex/Claude
  histories for this repository.
- Local llama.cpp models in the available 0.6B-, 1B-, and 3B-class
  configurations can produce grammar-valid one-word tags on the 300
  redacted R122 fragment sample, with R180 showing 2700/2700 valid tags and
  per-model exact stability of 299/300, 279/300, and 285/300.
- Semantic frames partition system-effect buckets that nonsemantic folded
  stacks and flat summaries merge in this local workload.
- R114 validates exact semantic-effect lineage for a fixed 20-task Codex
  command-mode suite with 100.0% precision/recall and 0/3170
  negative-control effects attributed.
- R160 verifies an auditable bounded local artifact path with fixed historical
  sessions, a sanitized input manifest, expected output files, redacted
  previews, and a fully cached rerun.
- R200 verifies a public-safe generated-fixture artifact path with no real
  `.codex`/`.claude` trace reads, 5 clean llama.cpp calls, 5/5 cached hits, no
  prompt-preview leakage, and no raw-trace dirty paths.

Disallowed:

- AgentFlame proves developers debug faster or more accurately.
- One-word tags are semantically correct.
- R180 proves smaller models are semantically adequate, or compares a
  controlled same-family model scaling curve.
- AgentSight/AgentFlame has complete exact provenance for arbitrary
  full-history traces.
- AgentFlame is already validated as a community developer tool.
- AgentFlame is novel because it is a flamegraph for agents.

## Next Tracker Rows

| Run ID | Claim | Purpose | Command/config | Seed/reps | Oracle | Decision gate | Result path | Status |
|--------|-------|---------|----------------|-----------|--------|---------------|-------------|--------|
| R124-labels | C6 | Human adequacy labeling for one-word tags. | collect labels over independent copies of `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`; join frozen labels with `python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 ... --labeler-2 ... --adjudication ...`; rerun `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv --out-json docs/visexp/out/tag-adequacy-results-r124.json --out-csv docs/visexp/out/tag-adequacy-results-r124.csv --out-md docs/visexp/out/tag-adequacy-results-r124.md` | 300 fragments, >=2 labelers preferred | adequate/generic-noisy/misleading rubric plus agreement/adjudication | >=80% adequate, <=20% generic/noisy, <=5% misleading, kappa >=0.6 or narrowed wording | `docs/visexp/out/tag-adequacy-results-r124.json` | planned |
| R187-launch | C5 | Launch package for the pilot developer forensic task benchmark. | `python3 docs/visexp/r187_prepare_pilot_materials.py --out docs/visexp/out/user-task-pilot-r142/launch` | deterministic over frozen R142 packet | P01-P05 files, blank 70-row response CSV, leak scan, no answer key, no response evidence | launch only; cannot support C5 until real responses are scored | `docs/visexp/out/user-task-pilot-r142/launch/manifest.json` | done/launch |
| R142-pilot | C5 | Pilot developer forensic task benchmark. | using the R187 P01-P05 launch packets and frozen preregistration in `docs/visexp/out/user-task-preregistration-r142.json`, fill a pilot copy of `docs/visexp/out/user-task-pilot-r142/launch/responses/user-task-response-template-r142-pilot.csv` with real participant responses; rerun `python3 docs/visexp/score_user_task_results.py --responses <pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142` | 5 participants for complete condition coverage | hidden answer key, timing, false positives, confidence, response-contract checker, prereg source-hash lock | pilot only; protocol must work before paper-scale C5 claim | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` | planned |
| R160 | C7 | Bounded fixed-session open-source usability smoke. | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command; verify with `artifact_usability_r160.py` and clean-run report. | 8 fixed historical Codex sessions; one clean run plus cached rerun | expected files, runtime/cache summary, fully cached rerun, sanitized input manifest, clean/cached input equality, no raw-trace git dirt, generated report path containment | bounded local artifact path is audited; fresh-clone/community claim still open | `docs/visexp/out/artifact-usability-r160.json` | done/bounded |
| R200 | C7 | Public-safe generated-fixture community smoke. | `python3 docs/visexp/r200_community_smoke.py --command-timeout 360 --load-timeout 240` | one temporary synthetic Codex fixture; one clean run plus cached rerun | no real `.codex`/`.claude` reads, expected artifacts, prompt redaction, clean/cached cache behavior, no raw-trace dirty paths | public-safe artifact hygiene is audited; external fresh-clone, adoption, real-report sanitization, and full write-set audit remain open | `docs/visexp/out/community-smoke-r200.json` | done/artifact-hygiene |
