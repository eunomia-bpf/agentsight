# Implementation

Last updated: 2026-07-07
Stage at update: stage 4 execute / stage 8 audit / stage 11 reproducibility prep
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `agentpprof/src/standard_trace.rs`, `agentpprof/tests/standard_trace_cli.rs`, `agentpprof/tests/profile_spec_cli.rs`, `script/operation_*.py`, `script/agent_trace_datasets.py sample tau-bench-trajectories`, `script/agent_trace_datasets.py sample agent-reward-bench`, `script/agent_trace_datasets.py sample satraj-os-safety`, `script/agent_trace_datasets.py sample osworld-human`, `script/agent_trace_datasets.py sample agentnet`, `script/agent_trace_datasets.py sample scalecua-navigation`, `script/agent_trace_exchange_eval.py`, `script/agent_trace_chrome_exchange_eval.py`, `script/operation_standard_trace_exchange_eval.py`, `script/operation_where_filter_eval.py`, `script/operation_rust_rank_rule_eval.py`, `script/operation_rank_mode_eval.py`, `script/operation_rank_feature_eval.py`, `script/operation_rank_feature_ablation_eval.py`, `script/operation_rank_feature_robustness_eval.py`, `script/operation_profile_spec_composition_eval.py`, `script/operation_profile_patch_eval.py`, `script/operation_boundary_profile_patch_eval.py`, `script/operation_oracle_depth_adequacy_eval.py`, `script/operation_field_derivation_mechanism_eval.py`, `script/paper_core_experiment_consolidation_audit.py`, `script/paper_core_result_tables.py`, `script/paper_core_claim_evidence.py`, `script/paper_core_section_readiness.py`, `script/paper_visualization_portfolio.py`, `script/paper_headline_case_studies.py`, `script/paper_claim_integrity_r356.py`, `script/implementation_consistency_audit.py`, `script/paper_two_abstraction_doc_gate.py`, `script/paper_build_smoke_r396.py`, `script/paper_main_body_run_ledger_r397.py`, `cargo test --manifest-path agentpprof/Cargo.toml --test profile_spec_cli`, `cargo test --manifest-path agentpprof/Cargo.toml`
Additional source/command: `script/operation_field_suitability_eval.py`, `script/operation_rust_task_stack_induction_eval.py`, `script/operation_induced_stack_scoring_eval.py`
Completeness: partial

## Repository Layout Relevant To Semantic Profiling

Purpose: identify the maintained implementation boundary.

| Path | Role | Status |
|---|---|---|
| `agentpprof/src/main.rs` | Rust CLI, argument parsing, operation-file entrypoint, output dispatch. | source of truth |
| `agentpprof/src/profile.rs` | Operation loading, mapping, stack construction, pprof/folded/SVG/JSON profile generation. | source of truth |
| `agentpprof/src/standard_trace.rs` | Chrome Trace Event export/import bridge that normalizes trace events into operation records before folding. | exchange bridge |
| `agentpprof/src/tagger.rs` | Regex/LLM prompt tagging for local-session operation fields. | maintained |
| `agentpprof/tests/standard_trace_cli.rs` | CLI round-trip test for standard trace export/import. | regression test |
| `agentpprof/tests/profile_spec_cli.rs` | CLI regression for profile-spec composition over operation JSONL and local-session inputs, mapping/tagging, predicates, operation-level rank rules, and stack-depth override. | regression test |
| `agent-session/` | Shared local Codex/Claude session parser. | maintained |
| `script/agent_trace_datasets.py` | External labeled trajectory samplers and operation JSONL normalization. | research harness |
| `script/agent_trace_exchange_eval.py` | Reproducible agent-session trace export/import/conversion equality check. | research harness |
| `script/agent_trace_chrome_exchange_eval.py` | Reproducible Chrome/Perfetto-style trace exchange equality check. | research harness |
| `script/operation_standard_trace_exchange_eval.py` | R353 operation-file standard-trace exchange check over an existing tracked real labeled operation prefix. | reproducibility harness |
| `script/operation_map_infer.py` | Generates reproducible operation-field mapping rules from labeled operations. | research harness |
| `script/operation_stack_quality.py` | Scores operation stacks against dataset-provided labels. | research harness |
| `script/operation_leaveout_eval.py` | Leave-dataset-out mapping validation over external traces. | research harness |
| `script/operation_stack_depth_eval.py` | R286 recursive depth sweep over the Rust `agentpprof` path. | research harness |
| `script/operation_where_filter_eval.py` | R321 profile-spec predicate probe over tracked R300 operation JSONL. | research harness |
| `script/operation_rust_rank_rule_eval.py` | R322 Rust visible rank-rule probe over tracked R300 operation JSONL. | research harness |
| `script/operation_rank_mode_eval.py` | R323 Rust rank-mode comparison over tracked R300 operation JSONL. | research harness |
| `script/operation_rank_feature_eval.py` | R324 Rust operation-level rank-feature probe; derives a visible-only profiler input from tracked R300 operation JSONL before scoring with hidden labels. | research harness |
| `script/operation_rank_feature_ablation_eval.py` | R325 leave-one-feature actionability probe over R324's scrubbed visible profiler input. | research harness |
| `script/operation_rank_feature_robustness_eval.py` | R326 equal-weight, global-bank, and ablation-repaired rank-feature robustness probe over R324's scrubbed visible profiler input. | research harness |
| `script/operation_profile_spec_composition_eval.py` | R342 profile-spec composition audit over tracked R324 real-trace Rust outputs; checks predicates, operation-level rank rules, rank mode, and recursive stack depth without prompt/session frames. | research harness |
| `script/operation_profile_patch_eval.py` | R354 executable profile-spec patch audit; reruns default and patched Rust profiles over tracked R324 visible operations and scores with hidden labels after profiling. | research harness |
| `script/operation_boundary_profile_patch_eval.py` | R358 boundary-derived profile patch audit; reruns Rust profile specs over R297 held-out OSWorld-Human boundary fields as ordinary operation fields and scores hidden labels after profiling. | research harness |
| `script/operation_oracle_depth_adequacy_eval.py` | R355 oracle-depth adequacy audit; scores visible-ranked profile groups at session, operation/step, positive-run proxy, and task-specific oracle depths over tracked labeled outputs. | research harness |
| `script/operation_field_derivation_mechanism_eval.py` | R366 field-derivation mechanism audit; consolidates deterministic mapping, profile-spec composition, rank-feature ablation, supervised boundary backends, and boundary-derived profile patches from tracked artifacts without rerunning the profiler. | paper hygiene harness |
| `script/operation_field_suitability_eval.py` | R400 field-derivation suitability audit; converts tracked R325/R358/R366 evidence into guarded accept/caution/reject profile-configuration decisions without syncing data or rerunning the profiler. | paper hygiene harness |
| `script/operation_rust_task_stack_induction_eval.py` | R402 Rust boundary-based task-stack induction replay; runs `agentpprof --induce-task-stack` on one tracked R300 real-trace slice and checks task-only, variable-depth stacks without a user stack-field chain or oracle source fields. | research harness |
| `script/operation_induced_stack_scoring_eval.py` | R403 hidden-label scoring for Rust-induced task-only stacks; runs `agentpprof --induce-task-stack` on the existing six R300/R320 real labeled tasks, reconstructs per-operation induced stack groups from Rust split decisions, and scores hidden labels only after profiling. | research harness |
| `script/paper_entry_claim_path_audit.py` | R367 entry claim-path audit; checks that abstract, introduction/problem framing, and main result table present RQ1/E1-RQ4/E4 as three empirical profiling questions plus one systems/reproducibility question, with R-runs as provenance and only operation/operation-stack profiler abstractions. | paper hygiene harness |
| `script/paper_trace_tree_baseline_audit.py` | R368 trace-tree-shaped baseline audit; reads existing R320/R355 hidden-label scoring outputs and makes the flat/fixed-session/dataset-native/raw-action baseline tradeoffs explicit without importing ecosystem traces or rerunning the profiler. | paper hygiene harness |
| `script/paper_core_experiment_consolidation_audit.py` | R359 paper-facing core-experiment consolidation audit; checks that evaluation is organized as RQ1/E1-RQ4/E4, R-runs are provenance, and R358 remains an RQ3/E3 mechanism ablation. | paper hygiene harness |
| `script/paper_core_result_tables.py` | R360 paper core-result table generator; regenerates the RQ1/E1-RQ4/E4 headline table and metric rows from tracked artifacts, now folding R366 field-derivation evidence into RQ1/E1 and RQ3/E3 without rerunning the profiler. | paper hygiene harness |
| `script/paper_core_claim_evidence.py` | R361 core-claim evidence ledger; binds each RQ/E experiment to claim, oracle, baselines, primary metrics, actionability, counterpoints, scoped wording, and R366 field-derivation scope. | paper hygiene harness |
| `script/paper_core_section_readiness.py` | R362 section-readiness audit; checks that Chinese/English RQ1/E1-RQ4/E4 result sections carry claim, oracle, baseline, metric, counterpoint/scope, and two-abstraction guardrails. | paper hygiene harness |
| `script/paper_visualization_portfolio.py` | R363 paper visualization portfolio; turns tracked RQ1/E1-RQ4/E4 evidence artifacts into baseline-tradeoff, metric-heatmap, diagnostic-lens, actionability-knob, and oracle-depth SVG/CSV/HTML views plus a LaTeX table fragment without rerunning the profiler. | paper hygiene harness |
| `script/paper_headline_case_studies.py` | R365 paper headline/case-study selector; compresses RQ2/E2 and RQ3/E3 evidence into five headline rows and six task cards from tracked artifacts without rerunning the profiler. | paper hygiene harness |
| `script/paper_claim_integrity_r356.py` | R356 claim-integrity refresh over R354/R355 plus the R338 R320-R350 gate; checks paper numbers, source provenance, guardrails, and the two-abstraction boundary. | paper hygiene harness |
| `script/profile_artifact_relocation_audit.py` | R343 relocated-checkout audit for historical profile specs that contain absolute artifact paths; verifies R342/R338 path normalization over existing tracked outputs. | reproducibility harness |
| `script/operation_metric_consistency_eval.py` | R344 multi-metric consistency audit over R320 scored policy outputs; checks AP, nDCG, top-k, budget, work, and fragmentation support/counterpoints. | research harness |
| `script/implementation_consistency_audit.py` | R319 implementation/docs consistency audit over Rust CLI, docs, and paper wording. | paper hygiene harness |
| `script/paper_two_abstraction_doc_gate.py` | R394 two-abstraction documentation consistency gate; checks Rust CLI wording, user guides, canonical docs, and papers after the Chinese guide field-derivation cleanup. | paper hygiene harness |
| `script/paper_build_smoke_r396.py` | R396 Chinese/English paper build smoke gate; runs the English Makefile in a temporary paper copy, runs Chinese XeLaTeX passes into a temporary output directory, checks final logs for unresolved references/citations, and verifies the English ACM figure-description warning is absent. | reproducibility harness |
| `script/paper_main_body_run_ledger_r397.py` | R397 main-body run-ledger suppression gate; checks that Chinese/English paper bodies keep R-numbered runs out of the main narrative while preserving RQ1/E1-RQ4/E4 as the only reviewer-facing experiment path. | paper hygiene harness |
| `docs/visexp/` | Historical AgentFlame/visual-experiment notes and older prototypes. | archive/reference; not authoritative |

## Current Implementation Status

Purpose: state what works now.

The current Rust implementation supports:

- normalized operation JSONL via `--operation-file`;
- arbitrary stack shape via `--stack`;
- inline operation-field mappings via `--op-map`;
- reusable mapping files via `--op-map-file`;
- query-time operation predicates via `--where` and profile-spec
  `where_rules`;
- visible stack-group ranking via `--rank-rule` and profile-spec
  `rank_rules` in JSON output;
- visible per-operation rank-feature aggregation via `--rank-op-rule` and
  profile-spec `rank_op_rules`; these rules match individual mapped
  `field=value` operation tokens and aggregate matched operation weight inside
  each folded stack group;
- rank-policy selection via `--rank-mode width-boost|rule-score` and
  profile-spec `rank_mode`;
- recursive task-stack induction via `--induce-task-stack`, which scores
  adjacent operation boundaries from visible fields, semantic shift,
  changed-field density, and optional query terms, writes a multi-value `task`
  field, and folds that field as the only stack frame for the induced view;
- frame-local stack overrides via `--stack-rule`;
- reusable profile specs via `--profile-spec`, including operation-file,
  local-session, imported agent-trace, and standard-trace input paths;
- portable local agent-session trace import/export via `--trace-file` and
  `--export-trace`;
- Chrome Trace Event import/export via
  `--standard-trace-file` and `--export-standard-trace`, including direct
  standard-trace export from normalized operation JSONL;
- pprof, folded, SVG, and JSON outputs;
- local Codex/Claude session projections and external dataset projections
  through the same stack construction code path.

Profile specs are implemented in the maintained Rust CLI rather than a separate
experiment runner. R293 tracks an AgentNet spec replay that reproduces the
16,741-operation / 608-stack diagnostic view and a CLI override that folds the
same operations into 83 stacks. A profile spec is a reproducibility wrapper over
operation files, mappings, predicates, views, stacks, and outputs; it is not a
third profiler abstraction. R321 verifies that `where_rules` run after
mapping/tagging and before stack folding by selecting 729, 714, and 4,285
operations from the tracked R300 real labeled operation JSONL with exact folded
sample-count matches. R322 extends the same Rust JSON output with visible
`rank_rules` over folded operation-stack text: on the six existing R300 tasks,
the Rust-ranked groups improve AP over width ranking on 4/6 tasks and top-5
lift on 3/6 tasks, while SATraj and side-effect remain useful counterexamples
showing why the full R320 query-aware ranker still needs richer group-level
features. R323 adds `rank_mode=rule-score`, which ranks by visible rule score
before width: it improves AP over `width-boost` on 4/6 tasks, top-5 lift on 4/6
tasks, and first-positive work on 3/6 tasks, but still leaves side-effect and
OSWorld-Human as ranker-depth counterexamples. R324 moves the next query-aware
mechanism into Rust with `rank_op_rules` and feeds Rust a scrubbed
visible-operation JSONL derived from the R300 source: semantic-stack
operation-feature ranking improves AP over width on 5/6 tasks, top-5 lift on
4/6, and first-positive work on 5/6; a coarser stack depth improves AP on 4/6
while reducing groups substantially on the same operation source. R325 replays
the same Rust path under leave-one-feature ablations and records 7 critical
feature instances, 3 misleading feature instances, and a stack-depth tradeoff
where coarse depth is AP-preferred on 2/6 tasks while reducing groups on 6/6.
R326 replays the same scrubbed input under equal-weight, global-bank, and
R325-guided repaired policies: the global equal visible feature bank improves
AP over width on 4/6 semantic and 5/6 coarse tasks, task-equal stays within
0.02 AP of weighted task policies on 8/12 variants, and repairs improve AP on
2/3 misleading-feature cases and first-positive work on 2/3 cases; 1/3
improves both metrics. The repaired policy
uses offline R325 findings and is evidence for actionability, not a deployment
ranker.

The profile-spec composition path has direct Rust CLI regressions in
`agentpprof/tests/profile_spec_cli.rs`. The test writes a temporary operation
JSONL source, derives `task`, `intent`, and `phase` fields through an
`op_map_file`, filters with `where_rules`, ranks JSON groups with
`rank_op_rules` and `rank_mode=rule-score`, and then reruns the same spec with a
CLI `--stack` override. The semantic run folds three selected operations into
three operation stacks without any `session` or `prompt` frames; the override
folds the identical selected operations into one coarser stack. This is an
engineering regression for configurable recursive folding, not a new empirical
result.

R392 adds matching local-session, imported agent-trace, and standard-trace
profile-spec regressions over the public Codex fixture and a generic Chrome
trace fixture. The local-session and agent-trace specs carry `session_files` or
`trace_files`, regex `tag_rules`, `where_rules`, `rank_op_rules`,
`rank_mode=rule-score`, and a semantic stack; the CLI override folds the same
selected prompt into a coarser stack. The standard-trace spec carries
`standard_trace_files` and `include_standard_trace_args`, then checks that a
generic trace arg can become an operation field before folding. This closes a
replay gap for E4: input selection and local-session tag derivation are now
part of the same profile-spec path as operation-file mappings and ranking, but
they remain operation-field derivations folded into operation stacks rather
than a third profiler object.

R402 adds a first-class Rust task-stack induction mode. `agentpprof
--induce-task-stack` no longer requires a user-supplied stack-field chain. It
treats visible fields as evidence, filters oracle and label fields, scores
adjacent operation boundaries inside the current contiguous segment with
semantic-shift, changed-field, query, and partition-coherence signals, permits
the same evidence field to recur at different recursive cuts, recursively
splits only when the children have enough weight and distinct dominant
evidence, and stores the induced path as a multi-value `task` field before
normal stack folding. The
replay artifact runs this mode over
`dataset=agent-reward-bench;analysis_task=agentreward_looping` from the tracked
R300 operation file. The overview view produces 729 operations, 15 stacks, and
depth histogram 1/3/11 at depths 2/3/4; the session-candidate view uses the same
operations and produces 15 stacks with depth histogram 7/6/2. `session` is
selected only when explicitly allowed as evidence. This is an implementation
and visualization check for recursive task-only folding, not a hidden-label
accuracy result.

R403 turns that implementation path into a scored profiler view without adding
datasets or labels. `script/operation_induced_stack_scoring_eval.py` reuses the
tracked R300 operation JSONL and R320 policy-score CSV, runs the release
`agentpprof --induce-task-stack` binary for all six hidden-label tasks,
reconstructs operation-to-stack assignments from the Rust split-decision report,
and scores flat/fixed-session/dataset-native/raw-action/operation-stack
baselines with the same R320 machinery. The run passes 9/9 checks: all six tasks
use Rust induction, reconstructed stack weights match Rust JSON, no oracle
source fields are selected, hidden labels are used only after profiling, and all
six tasks produce variable-depth induced stacks. Median induced-task-stack
query-aware work@5 is 0.2819 versus 1.0 for flat summaries, median groups are
15.0 versus 285.0 for fixed-session drilldown, and median AP remains lower than
the hand-configured operation stack, 0.3034 versus 0.3116. This is RQ2/RQ3
mechanism evidence for automatic recursive folding, not a new main experiment
or a claim of universal boundary discovery.

R342 extends that composition check to existing real labeled traces without
fetching or relabeling data. `script/operation_profile_spec_composition_eval.py`
reads the tracked R324 report, summary CSV, profile specs, and Rust JSON outputs
over the R300 task suite, then verifies that all 12/12 task-depth variants
compose operation files, `where_rules`, `rank_op_rules`, `rank_mode=rule-score`,
and explicit stack depth while staying prompt/session-free. The same audit
records the resulting tradeoff: visible operation-feature ranking improves AP
over width on 9/12 variants and first-positive work on 10/12, while coarse
stack depth reduces groups on 6/6 tasks with median reduction 0.8267. This is a
real-trace mechanism/reproducibility audit for operation and operation stack,
not a third abstraction or a human-utility result.

R354 then closes an actionability execution gap. Instead of only reading
already-scored policy tables, `script/operation_profile_patch_eval.py` writes
before/after profile specs, reruns the maintained Rust `agentpprof
--profile-spec` path on the tracked R324 visible-operation input, and scores
the emitted groups with hidden labels only after profiling. The profile-guided
patches improve AP, top-5 lift, and first-positive work on 5/6 tasks; the
remaining OSWorld-Human row is an intentional rejected patch that points to
boundary-derived fields. This is an executable profile-spec patch audit, not a
human/agent analyst study or automatic patch selector.

R358 follows up the R354 OSWorld-Human rejection without changing the runtime
abstractions. `script/operation_boundary_profile_patch_eval.py` reuses tracked
R297 held-out boundary-backend operations, strips oracle/group labels from the
Rust profiler input, keeps learned boundary fields as visible operation
fields, writes flat/fixed/semantic/learned-boundary profile specs, and scores
hidden labels only after Rust emits groups. Learned-boundary folding improves
AP and reduces groups, while increasing top-5 operation work and
first-positive work. This is a boundary-field mechanism ablation, not
automatic boundary discovery or an automatic patch selector.

R359 makes the paper organization check executable.
`script/paper_core_experiment_consolidation_audit.py` reads the evaluation
ledger, Chinese claim setup, Chinese paper, English paper submodule, and R358
artifacts. It confirms the paper-facing evaluation is RQ1/E1-RQ4/E4, not a chronological
R-run list; R-runs remain provenance, ablations, counterpoints, or audit gates;
and R358 stays an RQ3/E3 mechanism/actionability ablation. This is a paper hygiene
gate, not a profiler rerun or new empirical result.

R360 then makes the paper result table itself executable.
`script/paper_core_result_tables.py` reads tracked RQ1/E1-RQ4/E4 artifacts, including
R285/R286/R320/R328/R338/R342/R353/R354/R355/R357/R358/R359/R366, and writes a
four-row table, twenty metric rows, Markdown/HTML, and a LaTeX fragment. This
is table provenance over existing results, not a runtime component, profiler
rerun, or new empirical result.

R361 turns that table into a claim-evidence ledger.
`script/paper_core_claim_evidence.py` reads tracked R320/R352/R354/R355/R357/
R358/R359/R360/R366 artifacts and records, for each RQ/E block, the claim,
research question, oracle, baselines, primary metrics, headline result,
actionable insight, counterpoint, and scoped wording. The ledger is a reviewer
navigation artifact over operation/operation-stack evidence; it is not a third
profiler abstraction, a new result source, or a human/agent analyst study.

R362 checks that the main result sections themselves follow that ledger.
`script/paper_core_section_readiness.py` parses the Chinese and English papers,
extracts the RQ1/E1-RQ4/E4 subsections, and verifies that each section states the
claim, oracle, baseline, metric, counterpoint/scope, and the relevant
must-not-claim guardrails. This prevents the paper from relying on a
chronological R-run list for the reviewer-facing argument; it is still a paper
hygiene gate, not a profiler run or a new experiment.

R363 adds the paper visualization portfolio for that same RQ1/E1-RQ4/E4 structure.
`script/paper_visualization_portfolio.py` reads tracked R320/R345/R348/R354/
R355/R358/R361/R362 artifacts and emits five paper views plus a LaTeX table
fragment: baseline tradeoff, metric heatmap, diagnostic lenses, actionability
knobs, and oracle-depth adequacy. The portfolio is a report layer over
operation and operation-stack outputs; it does not introduce a flamegraph-only
framing, a new profiler abstraction, a profiler rerun, or a new empirical
result.

R365 adds the headline/case-study selector for the same RQ2/E2 and RQ3/E3 evidence.
`script/paper_headline_case_studies.py` reads tracked R320/R333/R334/R345/
R348/R354/R355/R358/R363 artifacts and emits five headline rows, six task
cards, a LaTeX table fragment, Markdown, HTML, JSON, CSV checks, and source
status. It is a paper-integration layer over existing profiler results, not a
new experiment, dataset sync, profiler rerun, human/agent analyst task, or
third profiler abstraction.

R366 adds the operation-field derivation mechanism audit.
`script/operation_field_derivation_mechanism_eval.py` reads tracked R282/R285/
R297/R299/R325/R342/R358 artifacts and emits six mechanism rows plus five
boundary-family rows. It checks that deterministic mappings, rank/tag fields,
profile specs, and supervised boundary backends remain operation-field
derivation mechanisms folded through operation stacks. It also records the
counterpoints: mapping can coarsen fine action labels, simple sequence-derived
fields can beat a learned backend, and boundary-derived profile patches can
improve AP/groups while increasing some inspection-work metrics. This is a
mechanism guardrail, not a new dataset, profiler rerun, human/agent analyst
task, automatic boundary detector, or third profiler abstraction.
R360/R361/R364 now consume this R366 audit as internal RQ1/E1 and RQ3/E3 evidence, so the
paper-facing structure remains three empirical profiling questions plus one
systems/reproducibility question rather than adding a fifth block.

R400 adds the field-derivation suitability audit.
`script/operation_field_suitability_eval.py` reads tracked R325/R358/R366
artifacts and emits five profile-knob decisions plus five boundary-family
decisions. It records when deterministic mapping, stack-depth changes,
operation-level rank features, supervised boundary-derived fields, and
boundary-profile repair should be accepted, used with caution, or rejected. It
does not sync datasets, relabel operations, rerun the profiler, add a third
profiler object, or claim a universal automatic selector. The output is a
profile-configuration guardrail for RQ3/E3 actionability.

R367 checks the paper entry path for that same structure.
`script/paper_entry_claim_path_audit.py` reads the Chinese paper, English
submodule paper, evaluation ledger, implementation doc, and tracked
R360/R361/R364/R366 ledgers. It parses the abstract, introduction/problem
statement, and main-result framing, then checks that they all present RQ1/E1-RQ4/E4 as
the paper-facing experiment structure, keep R-runs as provenance, preserve the
two-abstraction boundary, carry the RQ2/E2, RQ3/E3, and RQ4/E4 headline numbers, and avoid human
productivity, automatic-boundary, metric-dominance, live-overhead, or ecosystem
compatibility claims. It passed 11/11 checks with 6/6 entry-token rows. R367 is
a paper-integration guardrail, not a new dataset, profiler run, empirical
result, or fifth experiment.

R368 makes the RQ2/E2 trace-tree-shaped baseline scope explicit.
`script/paper_trace_tree_baseline_audit.py` reads the existing R320 policy
scores, R355 oracle-depth comparisons, R361/R364/R367 paper ledgers, and the
current Chinese/English paper text. It compares operation-stack query-aware
against flat summary, fixed-session drilldown, dataset-native hierarchy, and
raw-action stacks on the same six labeled tasks and records both support and
counterpoints. The gate passes 10/10 checks: operation-stack improves top-5
recall/F1 over fixed-session on 5/6 tasks, reduces median groups from 285.0 to
157.5, and R355 preserves 20/24 fixed-session unit-recall wins plus 22/24
groups-to-50%-positive-unit wins; fixed-session still wins top-5 work and
first-positive work on 4/6 tasks. R368 is an RQ2/E2 baseline-scope guardrail, not a
real OpenTelemetry/Phoenix/LangSmith/Perfetto import, new dataset, profiler
rerun, human/agent analyst task, or metric-dominance claim.

R355 then closes the main R339 depth-scoring gap without adding another
runtime object. `script/operation_oracle_depth_adequacy_eval.py` reuses tracked
R300 operation JSONL plus R320/R339 scored artifacts and evaluates the same
visible-ranked groups at session, operation/step, positive-run proxy, and
task-specific oracle depths such as OSWorld-Human `human_group`. Hidden labels
are used only for offline scoring after ranking. The result is a paper-facing
adequacy scorer for recursive operation-stack outputs: operation-stack
query-aware has median 0.4342 budget-30 positive oracle-unit recall over 24
task-depth rows and beats fixed-session recall on 20/24, while preserving the
depth-gap counterpoint. Unit-depth rows are scoring oracles, not profiler
abstractions; positive-run proxy units are derived episode units, not human
intent, and R355 does not claim automatic boundary discovery or latent intent
recovery.

R356 refreshes the paper-integrity layer for R354/R355. The script reuses the
R338 R320-R350 gate, then hashes the tracked R354 profile-spec patch artifacts
and R355 oracle-depth adequacy artifacts and checks that docs and papers keep
the only two profiler abstractions: operation and operation stack. This is an
audit over existing results, not a new empirical run, not a human/agent analyst
study, and not an automatic boundary-discovery or patch-selector claim.

R343 closes the relocated-checkout portability gap found during review.
`script/profile_artifact_relocation_audit.py` reads the same tracked R324/R342
artifacts and simulates a different checkout root for profile specs whose
`operation_files` still contain historical absolute paths. The audit verifies
that both the R342 composition path and the R338 paper-claim path rebase those
paths onto the current repository via the `docs/visexp/out/...` artifact suffix,
with 12/12 operation-file path checks passing and R338 still recomputing 12
variants across 6 tasks. This is a reproducibility guard for existing artifacts,
not a new dataset, ranker, boundary detector, or profiler abstraction.

Local trace exchange is also implemented through the maintained Rust path.
R294/R303 show `agentsight.agent-session.trace.v1` export/import and operation
JSONL conversion preserve the same 6-sample / 5-stack folded output on the
public Codex fixture. R306 adds a Chrome Trace Event JSON `traceEvents` bridge
that is Perfetto-readable in the fixture path: `agentpprof` exports the same
fixture with `--export-standard-trace`, imports it with
`--standard-trace-file`, and folds the imported events as ordinary operations.
The CLI test in `agentpprof/tests/standard_trace_cli.rs` covers this
standard-trace round trip, and R353 extends the Rust path to external
operation-file inputs: a 512-row deterministic prefix of the tracked R324 real
labeled visible-operation corpus exports to 512 Chrome events, imports through
`--standard-trace-file`, and preserves 512 samples / 11 stacks with
byte-identical folded output. This is still an exchange/reproducibility smoke;
real OpenTelemetry, OpenInference, or Perfetto producer traces remain an open
compatibility gate.

The external sampler currently covers 15 labeled trajectory sources, including
R287's tau-bench converter, R288's AgentRewardBench converter, and R289's
SATraj-OS converter, R290's OSWorld-Human converter, and R291's AgentNet
converter, plus R292's ScaleCUA navigation converter. The tau-bench converter
treats user messages, assistant responses, tool calls, and tool observations as
operation shapes, so tool-agent-user dialogue still uses the same
operation/operation-stack path. The AgentRewardBench converter reads the HF
annotations table, downloads only
matching `cleaned/` trajectory JSON files, and turns BrowserGym steps into
browser-action operations with expert `status`, `side_effect`, `looping`, and
`optimality` fields plus action-derived `repeat_state` and `repeat_signal`
fields for sequence-level repetition diagnostics.

The SATraj-OS converter reads the Dataset Viewer `safety` config, extracts
assistant `computer_use` XML tool-call parameters, and emits desktop
computer-action operations. Saved raw rows drop `messages` and `task`, and
operation JSONL records bucketed coordinate targets or generic text/key targets
instead of raw prompt, screenshot, or typed text content. SATraj `success`,
`safety`, `reward`, and `attack_type` labels are stored as operation fields, so
they can be folded as stack frames or scored by the same HTML/JSON analysis
scripts without adding a safety-specific profiler object.

The OSWorld-Human converter reads GitHub repository JSON files across desktop
applications, drops raw `instruction`, `config`, and `evaluator` fields by
default, and emits one operation per human single action. Each operation carries
desktop fields such as `app`, `environment`, `action`, `phase`, and `tool`, plus
`group_alignment`. The benchmark's grouped-action metadata is emitted as
ordinary fields only when flattened `grouped-action` labels exactly match the
`single-action` sequence: `human_group`, `group_index`, `group_size`,
`group_position`, and derived `group_pattern`. Content- or length-mismatched
rows remain in the operation file for action-level profiling but omit the gold
group fields so grouped-boundary metrics cannot score them accidentally. Tracked
operation JSONL omits raw instruction/action text unless the sampler is run with
`--include-text`.

The AgentNet converter reads public HF repository JSONL through
`hf-repo-jsonl-stream`, which opens the source file and stops after the
requested offset/range instead of saving the full 282MB/1.4GB source files.
Saved rows drop `instruction`, `natural_language_task`, `actual_task`,
`reason`, and raw `traj` fields by default. The converter emits one
`tool=computer` operation per PyAutoGUI step with normalized desktop fields,
bucketed coordinates or generic text/key targets, task `status`, alignment and
efficiency scores, `task_difficulty`, `step_correct`, `step_redundant`, and
action-derived repetition fields. R291 samples 1,000 Ubuntu tasks / 16,741
operations and uses those labels only as operation fields and evaluation
oracles.

The ScaleCUA converter reads public HF repository annotation JSONL through the
same streaming path and stops after the requested offset/range instead of
saving the source annotation file or downloading images. Saved rows drop the
raw `conversations` field by default, and operation JSONL records only derived
fields such as `platform`, `environment`, `trajectory_type`, `history_state`,
`history_depth`, `screen_size`, normalized action, bucketed target, and status.
R292 samples 5,000 Ubuntu navigation rows / 5,000 operations across 131
sessions. This is intentionally treated as a supplemental GUI history-depth
source because the sampled subset is mostly click/terminate.

`operation_map_infer.py` now includes desktop task-family rules, input/system/fail
phase families, and an effective-support filter that drops generated rules fully
shadowed by higher-priority rules. `operation_stack_quality.py` skips adjacent
boundary pairs where either side lacks the requested predicted or oracle field,
and reports `candidate_pairs` plus `skipped_missing_fields`, so combined reports
do not penalize datasets that legitimately do not carry OSWorld-specific
grouped-action labels while still exposing how many pairs were excluded.

The Python scripts are experiment harnesses. They download or normalize
third-party traces, generate mapping files, call the Rust CLI, and score
outputs. They are not an alternate operation-stack profiler implementation.

## Build And Test Commands

Purpose: make the current runnable path explicit.

```bash
cargo test --manifest-path agentpprof/Cargo.toml
cargo test --manifest-path agentpprof/Cargo.toml --test profile_spec_cli
cargo fmt --manifest-path agentpprof/Cargo.toml -- --check
python3 -m py_compile script/agent_trace_datasets.py script/operation_split.py \
  script/operation_map_infer.py \
  script/operation_stack_quality.py script/operation_leaveout_eval.py \
  script/operation_stack_depth_eval.py script/agent_trace_convert.py \
  script/operation_where_filter_eval.py \
  script/operation_rust_rank_rule_eval.py script/operation_rank_mode_eval.py \
  script/operation_rank_feature_eval.py \
  script/operation_rank_feature_ablation_eval.py \
  script/operation_rank_feature_robustness_eval.py \
  script/operation_profile_spec_composition_eval.py \
  script/operation_profile_patch_eval.py \
  script/operation_boundary_profile_patch_eval.py \
  script/paper_core_experiment_consolidation_audit.py \
  script/paper_core_result_tables.py \
  script/paper_entry_claim_path_audit.py \
  script/paper_trace_tree_baseline_audit.py \
  script/agent_trace_exchange_eval.py script/agent_trace_chrome_exchange_eval.py \
  script/operation_standard_trace_exchange_eval.py \
  script/implementation_consistency_audit.py
```

R286 depth sweep can be reproduced with:

```bash
python3 script/operation_map_infer.py \
  --operation-file <operation.jsonl> \
  --out docs/visexp/out/operation-stack-depth-r286/inferred-op-map.txt \
  --json-out docs/visexp/out/operation-stack-depth-r286/inferred-op-map.json

python3 script/operation_stack_depth_eval.py \
  --operation-file <operation.jsonl> \
  --op-map-file docs/visexp/out/operation-stack-depth-r286/inferred-op-map.txt \
  --out-dir docs/visexp/out/operation-stack-depth-r286
```

In the tracked R286 run, `<operation.jsonl>` is repeated for the nine operation
files listed in
`docs/visexp/out/external-agent-trace-scaled-r279/agentpprof-result.json`.

## Integration Constraints

Purpose: prevent drift back to old abstractions.

- Do not add prompt/session-specific code paths for external trajectory
  profiling; normalize them into operation fields.
- Do not add separate profiler concepts for tool calls, processes, syscalls, or
  plans; represent them as operation fields and stack frames.
- Keep mapping/tagging rule files reproducible and inspectable.
- Keep large raw samples under `.agentsight/`; tracked experiment outputs should
  be summaries, folded stacks, HTML reports, and JSON analyses.
- Keep README Quick Start stable unless the user-facing first-run flow changes.

## Open Engineering Tasks

Purpose: name work still needed before a paper-ready artifact.

| Task | Why it matters | Status |
|---|---|---|
| Add deeper boundary scorers for step instructions, solution paths, and failure labels. | Action-label F1 is too shallow for final recursive-boundary claims. | pending |
| Add a non-rule or model-backed boundary backend for OSWorld-Human and AgentNet. | The paper can currently claim configurable deterministic mapping, not automatic boundary discovery. | pending |
| Execute the controlled human/agent analyst study from R315/R316/R317. | The current C4 evidence is an automated hidden-label profiler benchmark; analyst productivity, analyst accuracy, time-to-answer, and user utility remain unsupported. | pending |
| Import one real OpenTelemetry GenAI, OpenInference, or Perfetto trace from another agent tool. | R306/R353 prove standard-trace container round trips for session and operation-file inputs, not compatibility with real producer traces. | pending |
| Add converters for the best next trajectory sources: UI-Vision, OSWorld-Verified/OSWorld 2.0 trajectories, and VisualWebArena trajectories. | Future expansion beyond the current 15 sources should be driven by stronger oracles, not dataset count alone. | pending |
| Scale tau-bench beyond the R287 `gpt-4o-mini` 50-episode sample. | Multi-model tau-bench trajectories can support outcome/failure and model-comparison analysis. | pending |
| Scale AgentRewardBench beyond the R288 38-trajectory lightweight sample. | Expert side-effect and looping labels are sparse; larger balanced sampling is needed for paper-grade failure diagnostics and better sequence-derived repetition rules. | pending |
| Scale SATraj-OS beyond the R289 safety sample and revisit the capability config. | Desktop computer-use is now represented, but capability rows were not fully readable through Dataset Viewer and need a heavier access path. | pending |
| Add stronger non-flamegraph comparison reports for any new datasets or stack-depth questions. | The current scoped paper already has tree, transition, quality, boundary, case-packet, frontier, reviewer-stress, and claim-audit reports, but future expansion should keep adding non-flamegraph views rather than only folded stacks. | current scoped set covered by R273-R318; future expansion pending |
