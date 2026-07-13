# Evaluation

Last updated: 2026-07-10
Stage at update: supplement / evaluation-design recovery
Reader note: the 2026-07-10 recovery plan is the authoritative current state.
The `Source/command` lines and the later 3+1 block preserve the pre-audit
provenance/evaluation organization; they are historical evidence to reconstruct,
not approval to resume paper integration.
Source/command: `script/agent_trace_datasets.py`, `script/operation_split.py`, `script/operation_leaveout_eval.py`, `script/operation_map_infer.py`, `script/operation_stack_depth_eval.py`, `script/operation_boundary_backend_eval.py`, `script/boundary_family_calibration_eval.py`, `script/operation_query_utility_eval.py`, `script/operation_analyst_task_eval.py`, `script/operation_analyst_ranking_eval.py`, `script/operation_case_study_eval.py`, `script/operation_case_baseline_eval.py`, `script/operation_analyst_outcome_eval.py`, `script/operation_problem_value_synthesis.py`, `script/operation_where_filter_eval.py`, `script/operation_rust_rank_rule_eval.py`, `script/operation_rank_mode_eval.py`, `script/operation_rank_feature_eval.py`, `script/operation_rank_feature_ablation_eval.py`, `script/operation_rank_feature_robustness_eval.py`, `script/operation_profile_spec_composition_eval.py`, `script/operation_metric_consistency_eval.py`, `script/operation_view_frontier_eval.py`, `script/operation_profile_accuracy_eval.py`, `script/operation_profile_uncertainty_eval.py`, `script/operation_profile_negative_control_eval.py`, `script/operation_view_depth_fit_eval.py`, `script/operation_inspection_frontier_eval.py`, `script/operation_fragmentation_tradeoff_eval.py`, `script/operation_actionability_synthesis_eval.py`, `script/operation_actionability_selection_eval.py`, `script/operation_inspection_target_eval.py`, `script/operation_sequence_adequacy_eval.py`, `script/operation_oracle_depth_adequacy_eval.py`, `script/operation_policy_transfer_eval.py`, `script/operation_action_counterfactual_eval.py`, `script/operation_action_transfer_eval.py`, `script/operation_profile_patch_eval.py`, `script/operation_boundary_profile_patch_eval.py`, `script/paper_core_experiment_consolidation_audit.py`, `script/paper_core_result_tables.py`, `script/paper_core_claim_evidence.py`, `script/paper_core_section_readiness.py`, `script/paper_visualization_portfolio.py`, `script/operation_standard_trace_exchange_eval.py`, `script/paper_claim_integrity_audit.py`, `script/paper_claim_integrity_r356.py`, `script/paper_reviewer_acceptance_r357.py`, `script/paper_evaluation_rubric_audit.py`, `script/analyst_study_protocol.py`, `script/analyst_study_readout_eval.py`, `script/paper_real_problem_narrative.py`, `script/paper_reviewer_acceptance_audit.py`, `script/implementation_consistency_audit.py`, `script/agent_trace_to_operations.py`, `script/agent_trace_convert.py`, `script/agent_trace_exchange_eval.py`, `script/agent_trace_chrome_trace.py`, `script/agent_trace_chrome_exchange_eval.py`, `script/paper_claim_synthesis.py`, `script/reviewer_evidence_packet.py`, `script/paper_value_novelty_synthesis.py`, `script/paper_claim_readiness_synthesis.py`, `script/paper_evidence_matrix_synthesis.py`, `script/paper_robustness_audit.py`, `script/paper_submission_audit.py`, `agentpprof --operation-file`, `agentpprof --trace-file`, `agentpprof --profile-spec`, `agentpprof --where`, `agentpprof --rank-rule`, `agentpprof --rank-op-rule`, `agentpprof --rank-mode`, `script/operation_stack_quality.py`, `cargo test --manifest-path agentpprof/Cargo.toml`
Additional source/command: `script/paper_headline_case_studies.py`, `script/operation_field_derivation_mechanism_eval.py`, `script/operation_field_suitability_eval.py`, `script/operation_rust_task_stack_induction_eval.py`, `script/operation_induced_stack_scoring_eval.py`, `script/operation_induced_depth_sensitivity_eval.py`, `script/paper_english_experiment_gap_audit.py`, `script/paper_english_induction_sync_audit.py`, `script/paper_induction_display_r407.py`, `script/paper_chinese_induction_pdf_freshness_r408.py`, `script/paper_reviewer_evidence_path.py`, `script/paper_main_experiment_contract.py`, `script/paper_evaluation_narrative_focus.py`, `script/paper_main_body_concision_audit.py`, `script/paper_task_claim_verdict.py`, `script/paper_core_experiment_weight_gate.py`, `script/paper_core_claim_gate.py`, `script/paper_three_plus_one_gate.py`, `script/paper_main_claim_evidence_gate.py`, `script/paper_experiment_block_consolidation_gate.py`, `script/paper_diagnosis_card_gate.py`, `script/paper_canonical_three_plus_one_gate.py`, `script/paper_canonical_reviewer_acceptance_r383.py`, `script/paper_post_r392_reviewer_acceptance_r393.py`, `script/paper_main_claim_verdict_alignment_r395.py`, `script/paper_build_smoke_r396.py`, `script/paper_main_body_run_ledger_r397.py`, `script/paper_current_three_plus_one_gate_r398.py`, `script/paper_pdf_freshness_r399.py`; read-only audit of `docs/agentpprof-paper/main.tex` after commit `f2cdb8e9`
Completeness: blocked at result-integrity and claim/evidence alignment; the
2026-07-10 recovery plan below freezes paper-writing work until the core
protocols pass.

## 2026-07-10 Evidence And Skill Iteration Recovery Plan

### Decision And Scope Freeze

This project is not currently at paper integration or prose polish. The
concrete paper and artifact audit found unresolved result-integrity,
claim/evidence, baseline, and external-validity blockers, so the project rolls
back to `supplement / evaluation-design recovery`. Internal checker acceptance
does not override a protocol-level blocker discovered from the paper, scripts,
or raw result path.

This recovery has two coupled goals:

1. repair the AgentProf evaluation until the central claims survive a blinded,
   leakage-audited, baseline-fair protocol; and
2. use the research trajectories as dogfooding evidence to improve the
   non-writing research and AgentSight analysis skills, then test whether those
   changes actually reduce repeated agent rework.

The academic writing skills are explicitly frozen during this recovery. Do not
modify `iter-refine-writing`, `iter-refine-writing-idea`, section-revision,
terminology, style, abstract/intro, or prose-tightening skills. Existing writing
outputs remain useful, but no writing workflow may advance the project while
the result-integrity gate is blocked. Writing resumes only after the claim gate
in Phase 4.

### What The Current Trajectory Audit Establishes

Audit source/status: exploratory read-only analysis of native session metadata
and JSONL events under `~/.codex/sessions`, the existing July Claude trace
subset, and `~/.agentsight/monitor/monitor-2026-W25.db`. Explicit Codex exports
were written only to `/tmp` for this audit. These counts guide the recovery
plan; they are not paper results. Phase 1 must turn the selection, identity
join, and metric extraction into a tracked reproducible fixture/report before
any number is promoted into a research claim.

The first mixed-source profile was only a narrow July subset: 72 exported trace
records, comprising 8 Claude primary records, 62 Claude subagent records, and 2
Codex-format rows. Those two Codex rows are one parent and one child reviewer,
not two independent primary sessions. That profile was adequate for discovering
the initial tag taxonomy, but it is not the Codex research corpus and must not be
used for a Claude-versus-Codex comparison.

A raw inventory finds 5,337 JSONL files, of which 5,334 have valid first-line
session metadata and unique metadata IDs. Filtering by the two AgentProf
research branches and then adding
the parent/child lineage that branch-only filtering misses yields 439 relevant
Codex records:

| Stratum | Records | Interpretation |
|---|---:|---|
| Interactive research parents | 3 | Two multi-day orchestrators and the later parent that requested the pprof visualization review. |
| Children of those parents | 329 | All are depth-1 subagents: 225 from the v2 parent, 103 from the earlier parent, and 1 from the later parent. |
| Other interactive VS Code sessions | 4 | Standalone project interactions not attached to those parents. |
| `source=exec` sessions | 103 | Experiment workload/probe executions; keep separate from evidence about how the research agent itself behaves. |
| Total | 439 | Relevant raw records, not all equivalent observational units. |

The two long parents contain 211 filtered user prompts. A broad multilingual
correction heuristic matches 81 (38.4%); the v2 parent alone matches 25 of 49.
This is a directional diagnostic, not a paper metric, until approximately 200
prompts are manually labeled. The repeated themes are nevertheless clear from
the prompt sequence: 32 evidence/claim discussions, 36 paper-narrative or RQ
organization discussions, 39 visualization/stack-quality discussions, 20
workspace/branch/submodule safety discussions, and 14 requests to re-explain
project state. These are overlapping keyword/heuristic categories, not mutually
exclusive manual codes. Concrete repeated corrections include preserving exactly two
profiler abstractions, using real labeled traces, not substituting a human study
for the profiling claim, consolidating many small runs into 3--4 RQs, removing
experiment-diary and terminology-heavy prose, staying in the requested
worktree, and not touching the English paper submodule.

The raw call profile also differs sharply between long parents and bounded
children. The two long parents made 30,963 function calls; 7,511 (24.3%) repeat
an identical tool input within the same parent, and at least 910 command results
contain a non-zero shell exit. The 416 branch-tagged records contain 11,785
calls, with 423 exact repeats (3.6%) and 233 non-zero exits. Their primary rows
repeat 15.5% of calls while child rows repeat 2.4%, consistent with the parent
re-running checks and managing iterations while children perform narrower
tasks. Non-zero exit is not automatically an agent mistake: 79 normalized
failures are `rg` no-match exits and 12 are `diff`, so failure analysis must
separate expected negative probes from unexpected failures.

The 329 child tasks reveal a stronger review-design problem:

| Child-task signal | Count | Share |
|---|---:|---:|
| Read-only wording | 206 | 62.6% |
| Exact verdict requested | 183 | 55.6% |
| Re-review after an earlier finding/fix | 69 | 21.0% |
| Internal `R###` run mentioned | 272 | 82.7% |
| Explicit protocol/falsification wording | 29 | 8.8% |
| Human/analyst evidence discussed | 47 | 14.3% |

Among tasks asking for an ACCEPT/PASS versus negative verdict, 175 end in
ACCEPT/PASS and only 1 ends in a negative verdict. This 99.4% acceptance rate is
not evidence that the artifact was nearly perfect. The prompts are heavily
primed: 51 state that findings were fixed, 62 report that checks already pass,
44 mention a prior verdict, and only one asks the reviewer to rely on the paper
and primary results while excluding internal gate artifacts. Forty-two prompts
use independent/adversarial wording, but 15 of those also disclose a fix/pass
summary. An actually independent reviewer should receive the paper, primary
results, protocol, and code needed to reproduce the claim, not the desired
verdict or the project's own acceptance artifacts.

These associations motivate a working diagnosis for how dozens of reviews and
a final internal acceptance state could coexist with the current leakage,
circular-metric, baseline, and external-validity blockers: review-task priming
and checker-oriented verification may cause reviewers to confirm the project's
prior interpretation rather than reconstruct and falsify the load-bearing
claim. The current audit does not establish that causal effect. The dogfooding
study must include a prompt-ablation arm that gives matched reviewers either
(A) internal pass/fix/verdict context or (B) only the paper, primary results,
protocol, and code, then compare blocker recall and false-positive rate.

The AgentProf ingestion path itself fails the source-fidelity gate. Exporting
416 branch-tagged Codex files produces 416 rows but only 199 unique exported
IDs: 217 v2 rows collapse onto one parent ID, and the later parent/child pair
also collapse. Older Codex logs can be assigned a rollout filename rather than
their metadata UUID. Long-session token accounting is also unusable: child logs
can inherit or repeat parent-level cumulative counters, and AgentProf converts
hundreds of thousands of `token_count` updates into apparent LLM-response
events. Do not publish Codex token cost, LLM-call count, or per-session cost
until identity, parent linkage, and token-event semantics are repaired and
validated against raw files.

The earlier Claude-only trajectory findings remain useful within their scoped
July corpus: correction/clarification prompts account for roughly one quarter
of non-cache token use; raw Claude results expose 103 tool errors, including 60
stale-read/file-modified edits, 22 shell exits, and 15 edit-target misses. They
must not be combined numerically with the broken Codex token counters.

System evidence has two scopes. The July Claude/Codex paper iteration is later
than the available monitor database, so it still lacks overlapping CPU/RSS
capture. The full Codex research history, however, overlaps the monitor window
from June 16--23: the database contains 126 Codex session identifiers and 69
Codex sessions whose cwd/path/command is AgentSight-related. Monitor IDs use a
`local:codex:...` display identity rather than the raw metadata UUID, so a
validated path-and-time join is still required before attributing CPU/RSS to a
research session. A new overlapping capture remains the clean path for the
final cost claim.

### Blocking Gates

| Gate | Current verdict | Evidence required to pass |
|---|---|---|
| G0 source fidelity | fail | Discovery reports expected/observed coverage across repo worktrees; parent/child Codex IDs and lineage survive export; old/new ID schemas normalize consistently; token updates and raw tool errors preserve their semantics; session counts deduplicate correctly. |
| G1 RQ1 construct validity | fail | The principal semantic-quality metric uses an oracle independent of the stack fields; zero mixing by construction is labeled only as an audit upper bound. |
| G2 RQ2 leakage and protocol freeze | fail | Hidden labels are physically unavailable to view/ranker construction; visible fields, tuning budget, split, and freeze commit are recorded before test scoring. |
| G3 baseline fairness and novelty | fail | AgentProf is compared with SQL/DuckDB hierarchical aggregation, a fixed trace tree, tag/attribute grouping, and available trace/profile tools under equal information and tuning budgets. |
| G4 mechanism isolation | partial | Ablations show which benefit comes from the operation model, recursive stack projection, field derivation, or ranking, including cases where the simpler hierarchy wins. |
| G5 external validity | fail | At least three independent projects or trace families and more than one agent implementation are evaluated under the same frozen protocol. |
| G6 human/analyst utility | fail | A blinded analyst study or an explicitly narrowed non-human-utility claim; artifact-authored task rules cannot substitute for analyst evidence. |
| G7 system cost | blocked | New overlapping AgentSight capture reports tagging and profiling CPU/RSS/time/output cost; capture overhead is measured or removed from the claim. |
| G8 claim gate | fail | Every central claim has a supported/partial/unsupported verdict from primary results, followed by an independent falsification review with no must-fix issue. |

No new paper prose, figure polish, or submission positioning is a gate-clearing
action before G0--G4 pass.

### Reconstructed Paper Claims And Research Questions

The recovery should consolidate the current run history into four falsifiable
blocks. Existing R-runs remain provenance and may be reused only after their
protocol role is reconstructed.

| RQ | Claim candidate | Primary experiment | Falsifying result |
|---|---|---|---|
| RQ1 abstraction | A fielded operation representation and query-time recursive projection express useful agent diagnostic views beyond fixed prompt/session/span boundaries. | Same trace corpus through AgentProf and equally informed aggregation/tree baselines; measure oracle-independent semantic fidelity, fragmentation, and query cost. | Fails RQ1-D1/D2 below; then novelty narrows to the agent operation model, lineage, and reusable profile specification. |
| RQ2 localization | With labels hidden from construction, operation-stack profiles reduce inspection work for locating failures or quality problems. | Frozen leave-family-out ranking over physically label-stripped inputs, with labels joined only inside a separate scorer. | Fails RQ2-D1/D2/D3 below; then the localization claim is unsupported or task-specific. |
| RQ3 mechanism and utility | Recursive projection and field derivation provide actionable diagnostic structure, and analysts can use it more effectively than raw/flat/fixed-tree views. | Mechanism ablations plus a blinded analyst task study. | Fails RQ3-D1, or RQ3-D2 if human utility is claimed; then retain only the mechanism or representation/replay claims that pass. |
| RQ4 generalization and cost | The approach generalizes across agents/projects and remains practical for offline analysis. | Multi-project, multi-agent, cold/warm scale and resource study with overlapping capture. | Fails RQ4-D1/D2/D3 below; narrow the population, scale, or cost claim. |

### Preregistered Decision Rules

These rules apply to the hardened main runs, not the three pipeline smoke runs.
Freeze the exact bootstrap unit, random seed, task weighting, reference machine,
and threshold values before unblinding test labels. A threshold may change once
after a label-free pilot only if the rationale and old/new values are recorded;
it cannot change after a test score is seen. Treat the listed D1 rules as the
claim-level primary comparisons; label other metrics secondary and control
their false-discovery rate within each RQ rather than selecting a favorable
slice after scoring.

| ID | Primary decision rule | Pass | Partial/fail action |
|---|---|---|---|
| RQ1-D1 semantic construct validity | Project/family-held-out macro-F1 against an independent semantic oracle; paired hierarchical bootstrap against the best non-oracle fixed/session/SQL/tag baseline. | Point improvement is at least 0.05 and the 95% CI lower bound on the improvement is above 0; fragmentation is no more than 10% worse. | If the CI includes 0 or improvement is below 0.05, remove semantic-quality superiority wording. |
| RQ1-D2 aggregation novelty | Equivalence interval for AgentProf versus an equally informed SQL/tag implementation on output groups, weights, ranking, and analyst query result. | At least one load-bearing diagnostic view or lineage/profile-spec behavior is not equivalent within an absolute 0.02 metric margin under equal information/tuning, and its mechanism is isolated. | If all outputs are equivalent within 0.02, do not claim aggregation novelty; reframe to the agent operation schema, lineage, profile-spec replay, and integration. |
| RQ2-D1 localization quality | Held-out AP/AUPRC versus the strongest deployable baseline, paired by family/task. | Point improvement is at least 0.03 and the hierarchical-bootstrap 95% CI lower bound is above 0. | Otherwise localization superiority is unsupported; report per-family scope or a negative result. |
| RQ2-D2 inspection work | Work-to-first-positive ratio versus the same strongest baseline. | Median ratio is at most 0.80 and the 95% CI upper bound is below 1.0. | Otherwise remove the reduced-inspection-work claim. |
| RQ2-D3 fragmentation non-inferiority | Ratio of ranked groups required to reach 25% positive recall versus the same strongest baseline. | 95% CI upper bound on the groups-to-25%-recall ratio is at most 1.10. | If worse, report the Pareto tradeoff without claiming a joint win. |
| RQ3-D1 mechanism isolation | Remove/replace recursive projection and field derivation one at a time on held-out families. | Each claimed mechanism worsens AP by at least 0.03 or inspection work by at least 15% on at least two of three held-out families, with no median reverse regression larger than those margins. | Drop a mechanism from the contribution or narrow it to the families where it passes. |
| RQ3-D2 analyst utility, optional | Blinded matched analyst tasks; correctness non-inferiority margin 5 percentage points plus completion-time ratio. | 95% CI lower bound on correctness difference is above -0.05 and 95% CI upper bound on median-time ratio is below 0.80. | If the study is underpowered or either rule fails, make no analyst productivity/time claim. |
| RQ4-D1 transfer | Repeat the frozen RQ2 protocol on at least three independent projects and two agent implementations. | Pooled RQ2-D1 direction is positive with 95% CI lower bound above 0, and no project loses more than 0.03 AP to its strongest baseline. | Narrow the population to passing projects/agents; one originating project cannot support generality. |
| RQ4-D2 offline cost | On a frozen reference machine, profile 1M operations cold and warm. | p95 profiler wall time is at most 60 seconds and peak RSS at most 2 GiB; report output size without hiding conversion/tagging cost. | Narrow the supported scale/cost envelope to the largest passing point. |
| RQ4-D3 capture overhead, conditional | Matched workload with and without AgentSight capture. | If a capture-overhead claim is retained, both wall-time and CPU overhead are at most 5% with uncertainty reported. | Otherwise remove capture/zero-runtime-overhead wording and claim only offline post-processing. |

### Mandatory Leakage Worksheet For RQ1 And RQ2

Every task must persist the following fields before a test run. A blank field
blocks the run rather than becoming a post-hoc explanation.

| Field | Required record |
|---|---|
| Hidden oracle | Exact label columns and derivation; dataset-provided, external human label, or proxy. |
| Visible input | Exact operation fields available to conversion, stack induction, ranking, and rule generation. |
| Physical separation | Label-stripped test artifact hash and a scorer-only label artifact hash. |
| Author access | Whether task designers saw test labels or outcomes while writing rules; if yes, the task is development evidence, not held-out evidence. |
| Split unit | Project/family/session/task split and why adjacent records cannot leak. |
| Freeze point | Commit/config hash and timestamp before test labels are joined. |
| Tuning budget | Number of rule/model/config trials allowed per method, including human effort. |
| Baseline parity | Same visible fields, same split, same budget, and same metric implementation. |
| Scorer isolation | Separate command/process that reads predictions plus labels, never the profiler's construction path. |
| Negative control | Shuffled labels, irrelevant fields, or a label-free null view expected not to improve. |
| Failure action | Exact claim narrowing if the primary success criterion fails. |

RQ1 must stop using `session + prompt -> 0% residual mixing` as its principal
semantic result. That number is true by construction when the grouping key
contains the same field used to define mixing. It may remain as an audit upper
bound. The primary comparison needs an independent semantic oracle and must
compare at least: no-semantic grouping, session/prompt grouping, predicted
semantic grouping, and oracle grouping.

RQ2 must not describe a rule as blind merely because the scorer hides labels at
runtime. Rules or rankers written after inspecting test labels, task outcomes,
or positive fractions are development-tuned. The primary result should use a
leave-family-out protocol: freeze the rule generator/ranker on development
families, strip labels from the held-out input, generate rankings, and join
labels only in the scorer. Report a Pareto frontier over localization quality,
inspection work, and fragmentation instead of selecting one favorable metric.

### Baselines And Fairness Policy

The minimum baseline set is:

1. flat operation summary;
2. fixed session/prompt hierarchy;
3. dataset-native hierarchy where available;
4. DuckDB or SQL ordered grouping/recursive aggregation over the same visible
   fields;
5. pprof labels/tags or equivalent tag-derived pseudo-frames;
6. OpenTelemetry/Perfetto-style attribute or fixed-span-tree query when an
   importable real trace is available;
7. raw action/tool stack;
8. oracle view as an unattainable upper bound, never as a deployable baseline.

All methods receive the same label-stripped input and tuning budget. Report
absolute metrics and uncertainty, not only relative improvements. Preserve
negative rows, including cases where native hierarchy has better AP, recall,
or F1 and AgentProf wins only on group count or inspection work. If the SQL/tag
baseline matches AgentProf, reframe novelty around the agent-specific operation
schema, lineage, profile-spec replay, and integration rather than aggregation
itself.

### New Evidence To Collect

#### E1: Free-Form Semantic Oracle

- Sample 600--1,000 prompts from at least three projects and more than one
  agent implementation.
- Use two independent annotators plus adjudication; report agreement and the
  adjudication protocol.
- Freeze a project-held-out split before comparing regex rules, a small local
  LLM, embeddings/classifier, clustering, keyword grouping, and the human upper
  bound.
- Report accuracy/F1 or clustering metrics appropriate to the label space,
  coverage, abstention, cost, and failure categories.
- If no row contains both public free text and an independent semantic oracle,
  keep free-form semantic accuracy out of the paper claim.

#### E2: Blinded Localization Benchmark

- Rebuild the six current tasks through the leakage worksheet.
- Mark any task-specific rule that saw test labels as development evidence.
- Add at least one held-out family per task type or narrow the claim to the
  families with a legitimate split.
- Compare the complete baseline set with equal human/config tuning budgets.
- Run multiple seeds where model/rule induction is stochastic and bootstrap
  uncertainty over tasks or sessions for deterministic policies.
- Primary outputs: AP/AUPRC, recall at fixed inspection budget, work to first
  positive, fragmentation, and the Pareto frontier.

#### E3: Mechanism And Analyst Study

- Isolate operation schema, recursive depth, field derivation, ranker, and
  profile-spec patching one at a time.
- Use known-correct fields when testing recursive projection so generation
  accuracy does not confound the folding mechanism.
- Run an 8--12 developer protocol pilot, then preregister the main sample size
  from a power analysis for RQ3-D2 (at least 80% power at alpha 0.05 and no
  fewer than 20 completed participants).
- Compare raw trace, flat summary, fixed session hierarchy, and AgentProf on
  matched diagnosis tasks; randomize order and blind condition names.
- Measure answer correctness, time, evidence cited, confidence/calibration,
  and action chosen. Record failures and learning effects.
- Without this study, describe RQ3 as machine-scored diagnostic localization,
  not human productivity or practical analyst utility.

#### E4: Generalization, Scale, And Cost

- Use 3--5 independent projects with different agents, task types, and trace
  shapes.
- Sweep roughly 1K to 1M operations where feasible; report cold/warm p50/p95
  runtime, peak RSS, output size, and tagging time.
- Record a new AgentSight monitor/session capture that overlaps the experiment
  interval and verify the target process tree is captured before the long run.
- If the paper retains a zero-runtime-overhead claim, separate offline profiler
  overhead from AgentSight capture overhead and measure both. Otherwise narrow
  the claim to offline post-processing.

### Non-Writing Skill Change Specification

Skill changes begin only after this plan is reviewed. Each change must be small,
traceable to an observed failure, and forward-tested on raw artifacts without
revealing the expected answer.

| Target | Observed failure | Planned change | Forward-test acceptance |
|---|---|---|---|
| `auto-research-orchestrator` | Internal pass documents overrode concrete protocol contradictions; prose work continued after evidence failure. | Make concrete evidence authoritative; any independent must-fix result-integrity issue rolls the stage back; require protocol-from-scripts reconstruction before paper integration; stop adding small runs that do not strengthen a named RQ. | Given the current paper plus primary results but no internal verdict files, the workflow routes to evaluation recovery and names leakage/circularity before prose. |
| `research-experiment-design` | Existing task-specific rules could be called hidden-label evaluation without recording author access, freeze point, or physical label separation. | Add the mandatory leakage worksheet, label-stripped artifact/scorer isolation, equal tuning budget, leave-family-out policy, negative controls, Pareto reporting, and direct mechanism validation. | On a sanitized current task, the skill blocks scoring until all worksheet fields exist and rejects a post-hoc test rule. |
| `agent-interaction-insights` | Generic correction counts identify rework but miss claim churn, review echo chambers, checker theater, and downstream cost. | Add research-specific friction classes, multilingual correction patterns, parent/child attribution, and links from a correction to subsequent token/tool/file cost. | On a human-reviewed prompt sample, class precision/recall and cost attribution meet the preregistered threshold; uncertain prompts are reported as uncertain. |
| `agentsight-system-friction` | Normalized tool status hides most raw `tool_result.is_error` failures and cannot explain stale multi-writer edits. | Parse raw tool-result error fields; classify stale-read, edit-target-miss, command-exit, permission, and multi-writer/file-state failures. | Reconcile normalized counts against a manually labeled raw sample and recover the known stale-edit cases. |
| `agentpprof-flamegraph` and `agent-session` ingestion | Default token view produced an uninformative graph; exact-cwd discovery missed Codex app worktrees and 414/416 branch-tagged records in the first audit; 217 child rows collapsed onto one parent ID; older metadata IDs became rollout filenames; cumulative token updates became apparent LLM responses. | Add repo/worktree-aware discovery with a coverage manifest, preserve raw session ID/parent ID/depth/path, define token-event semantics, add research preset guidance, separate semantic/structural coverage, use discover-once/export-once multi-view rendering, and enforce visual readability checks. | A fixture with old/new Codex parents and children preserves 1:1 identities and lineage; expected/observed discovery count matches; token totals reconcile with raw terminal usage; four views render from one trace export; the chosen graph passes minimum branch/label/readability checks without a user correction. |

No change is planned for the writing skills in this cycle. The current
`iter-refine-writing` workflow is strong within its stated scope: it assumes
claims are stable, runs serial rather than conflicting parallel edits, keeps
numbers read-only, applies subsection-sized changes, checks structure/logic/
terminology/language/citations separately, and compiles after each round. Its
`common-pitfalls` reference already captures the user's recurring objections to
experiment-diary prose, jargon inflation, weak subjects, structure drift, and
unsupported claim tone.

`iter-refine-writing-idea` is useful for expressing a stable idea, but its
"re-attack until a reviewer cannot easily reject" loop is unsafe if upstream
evidence has not passed. In this corpus, reviewers were frequently given the
claimed fix, internal pass artifacts, and desired verdict; a smooth framing can
therefore hide rather than resolve a research blocker. The immediate fix is
invocation control: the orchestrator must not route to either writing workflow
until result integrity and the independent claim gate pass. Do not expand a
writing skill into an experiment auditor; that responsibility belongs to the
orchestrator, experiment-design, reviewer, and trajectory-analysis workflows.
Reconsider a small writing-skill change only after a blinded before/after test
shows a remaining writing-specific failure under frozen claims.

### Dogfooding Experiment: Do Revised Skills Reduce Research Friction?

Treat skill improvement as an experiment rather than editing instructions until
they sound better.

- **Population:** at least 24 matched research tasks from at least three
  projects after a 12-task pilot.
- **Conditions:** A = current non-writing skills; B = revised non-writing
  skills. Freeze model, permissions, context budget, start commit, and task
  artifact. Randomize condition order where carryover can be controlled.
- **Review-context ablation:** independently randomize reviewer prompts between
  P = current primed context (claimed fixes/internal pass/prior verdict) and U =
  unprimed context (paper, primary results, protocol, and code only). Analyze
  A/B skill effects separately from P/U prompt effects and their interaction.
- **Blind oracle/adjudication:** the ground-truth issue checklist is created
  from raw artifacts by adjudicators who never see condition output. U-condition
  review participants receive no internal pass/fail documents; P-condition
  participants receive them by experimental design. Neither participant group
  sees the oracle checklist or the other condition's output.
- **Primary metrics:** must-fix blocker recall, incorrect supported claims,
  correction/clarification rate, validation omissions, and stale-edit errors.
- **Cost metrics:** non-cache tokens, attributed wall time with idle-time caveat,
  tool calls, files touched, and downstream rework after a correction.
- **Safety metrics:** false-positive blocker rate, destructive/unauthorized
  actions, user-scope violations, and missed negative results.
- **Suggested success criteria:** blocker recall at least 90%; at least 30%
  relative reduction in correction/clarification prompts; at least 80%
  reduction in stale-read edit failures; at least 20% reduction in token/time
  cost; no increase in validation omissions or false-positive blockers.
- **Calibration prerequisite:** manually label about 200 multilingual prompts
  before using correction regexes as an outcome. Report precision, recall, and
  uncertainty; do not optimize to an unvalidated proxy.

This dogfooding result can support a motivating case study or a skill-engineering
artifact claim. It must not substitute for the paper's main human-utility or
external-validity evidence.

### Phase 0 Non-Goals And First Three Run Contracts

Non-goals for the recovery batch:

- do not edit either paper, regenerate paper figures, or modify any writing
  skill before G8;
- do not compare Claude versus Codex token/call cost until Codex identity and
  token semantics pass R000;
- do not treat `source=exec` workloads as user correction or research-agent
  behavior;
- do not add more datasets or small checker runs before R001/R002 decide whether
  the core constructs and blinded protocol are viable;
- do not claim analyst productivity without RQ3-D2 or capture/zero-overhead
  without RQ4-D3;
- do not edit the English paper submodule in this workflow.

The first three runs are fixed by purpose; Phase 0 does not pass by agreeing to
an unnamed experiment.

| Run | Role | Input/compared artifacts | Oracle and success criterion | Failure action |
|---|---|---|---|---|
| R000 source-fidelity regression | G0 sanity | Sanitized old/new Codex parent+child fixtures spanning main repo and app worktree; raw JSONL versus export/import. | Raw metadata manifest is the oracle. Expected/discovered/exported counts are identical; every raw ID, parent ID, depth, cwd/repo identity, path, prompt/tool count, and selected token/error event maps 1:1 with no collision. | Stop all trajectory cost/error claims and fix ingestion before R001/R002. |
| R001 independent-oracle construct smoke | RQ1 construct sanity | One development family containing the same rows with public/free text and an independent semantic oracle; no-semantic, fixed session/prompt, SQL/tag, predicted semantic, and oracle views. | Before scoring: at least two oracle classes, minority prevalence between 10% and 90%, labels absent from construction, and all methods emit predictions for the same rows. Human labels require adjudicated agreement of Cohen's kappa or Krippendorff's alpha at least 0.70. This smoke checks engagement, not RQ1-D1 superiority. | If no suitable oracle exists, remove semantic-accuracy wording and prioritize annotation/data acquisition; do not reuse a by-construction metric. |
| R002 blinded localization baseline smoke | RQ2 protocol sanity | One held-out family; label-stripped operation artifact; frozen AgentProf policy; flat, fixed-tree, native hierarchy, SQL/tag, and raw action/tool baselines; scorer-only label artifact. | Hashes prove physical separation; profiler/rankers cannot open labels; freeze commit precedes label join; all baselines see identical visible fields and tuning budget. Rankings must be byte-identical when the scorer label artifact is absent, original, or replaced by 100 independently shuffled label files; scorer-only shuffled-label AP must remain within 0.02 of prevalence on average, with no permutation test significant at alpha 0.05 after within-smoke correction. This smoke checks protocol, not RQ2-D1/D2/D3 effect size. | If any construction path can read labels, rankings change with label artifacts, the negative control fails, or parity cannot be established, discard the score and repair the protocol. |

### Execution Order And Stop Conditions

| Phase | Work | Entry condition | Exit gate | Estimated effort |
|---|---|---|---|---|
| 0 plan freeze | Review this recovery plan; preserve current artifacts; stop paper prose. | Current audit complete. | RQ decision rules, non-goals, and R000--R002 contracts are frozen; canonical-doc review has zero must-fix findings. | 1--2 days |
| 1 source and skill instrumentation | Fix Codex parent/child identity, raw error normalization, trace-once workflow; write minimal non-writing skill changes. | Plan frozen. | G0 passes; forward-test fixtures exist. | 2--4 days |
| 2 core protocol rebuild | Leakage worksheets, label-stripped artifacts, frozen splits, strongest baselines, RQ1 independent oracle. | G0 passes. | G1--G4 pass or claims are explicitly narrowed. | about 1 week |
| 3 missing external evidence | Free-form annotation, multi-project traces, analyst study, overlapping resource capture. | Core protocol produces nontrivial signal. | G5--G7 pass or corresponding claims are removed. | 1--3 weeks |
| 4 claim gate | Rebuild claim ledger only from primary results; independent adversarial review. | All required results frozen. | No unresolved must-fix claim/evidence issue. | 1--2 days |
| 5 paper integration | Update idea story, paper claims, figures, and then rerun writing skills. | G8 passes. | Paper consistency, prose, citation, figure, and reproducibility gates pass. | after evidence freeze |

Stop or pivot when any of the following occurs:

- the label-stripped frozen protocol removes the principal RQ2 gain;
- SQL/tag/fixed-tree baselines reproduce the result with no AgentProf-specific
  advantage and the remaining operation-model claim is too small for the
  target venue;
- no independent semantic oracle can be obtained for RQ1;
- analyst tasks show no correctness/time benefit;
- multi-project transfer fails and the single-project claim is not sufficiently
  novel;
- source identity or result provenance cannot be made reproducible.

In each case, record the negative result and narrow or reframe the claim before
running another experiment. Do not create another checker script to reinterpret
the same evidence.

### First Authorized Implementation Batch After Plan Freeze

The first batch should be deliberately narrow and should not edit paper prose or
writing skills:

1. implement and run R000: the parent/child source-fidelity fixture, coverage
   manifest, old/new ID normalization, token-event semantics, and raw-error
   reconciliation; include discover-once/trace-export-once rendering in the
   same source-fidelity path;
2. review R000 and stop if any expected/discovered/exported count, identity,
   lineage, token, or selected error event fails exact reconciliation;
3. prepare and run R001 only after R000 passes, using one independent semantic
   oracle and the complete smoke baseline set;
4. prepare and run R002 only after R000 passes, using physically separate
   label-stripped input and scorer-only labels plus SQL/fixed-tree baselines;
5. review R001/R002 against their smoke criteria and freeze the hardened main
   configs before expanding the matrix.

No long run starts until the smoke task proves that labels are inaccessible to
construction, scorer isolation works, the mechanism is engaged, and all result
paths/commits/configs are recorded in the run tracker.

## Claim-To-Experiment Map

Historical status: this is the July 8 claim map retained for provenance. Its
status column is superseded by the recovery claim ledger and decision rules
above; none of these rows is current paper wording until G8 passes.

| Claim | Required evidence | Historical status (superseded) | Next experiment |
|---|---|---|---|
| C1: `agentpprof` profiles operations and operation stacks without privileging prompt/session boundaries. | A non-Codex/Claude labeled trajectory enters as operation JSONL and folds with arbitrary `--stack` frames; a local agent-native session can also be exported/imported through an exchange trace and converted to operation JSONL. | Supported. R279/R281/R282/R283/R284/R285/R286/R287/R288/R289/R290/R291 cover 14 core external datasets and 42,590 operations; R292 adds a supplemental ScaleCUA Ubuntu navigation stream sample, bringing the smoke set to 15 datasets / 47,590 operations. R170/R223/R224 add a local Codex/Claude semantic-axis projection over 325 real sessions and 183,714 system-effect observations: no-semantic aggregation mixes 90.402% of full semantic weight, prompt-only reduces it to 36.722%, and full session+prompt is the audit view with zero residual mixing by construction. R293 shows the same R291 AgentNet projection can be reproduced from a JSON profile spec and overridden to a different stack depth without changing operation input. R294 shows a Codex fixture can be exported as `agentsight.agent-session.trace.v1`, imported through `--trace-file`, converted to operation JSONL, and folded identically through `--operation-file`; R303 turns that bridge into a reproducible script with the same 6 samples / 5 stacks and byte-identical folded output. R306 adds a Chrome Trace Event JSON bridge: the same fixture exports to `traceEvents`, imports back to operation JSONL, and preserves the same 6 samples / 5 stacks folded output across direct trace, direct operation, and Chrome-import paths. R353 adds the symmetric operation-file standard-trace export path on a tracked real labeled operation prefix: 512 operations export to 512 Chrome events, import through `--standard-trace-file`, and preserve 512 samples / 11 stacks with byte-identical folded output. R321 adds profile-spec `where_rules` over the tracked R300 real labeled operation JSONL: mapping-derived predicates select 729, 714, and 4,285 operations before folding, matching source counts exactly. R342 verifies the full profile-spec composition path over the tracked R324/R300 real labeled outputs: 12/12 variants compose operation files, query predicates, operation-level rank rules, rule-score ranking, and explicit stack depth while remaining prompt/session-free. R295 mechanically gates the paper wording as supported for heterogeneous public trajectories and local session exchange, while excluding full-benchmark/image-archive claims. R298 maps this into a reviewer-facing heterogeneous-trace-object evidence block. R307 refreshes the claim gate after R300-R306 and keeps C1 supported while explicitly excluding complete OpenTelemetry/Chrome ecosystem compatibility and third-abstraction trace claims. | Stop broad dataset expansion until the paper extracts stronger conclusions from the existing oracle-rich sources; next high-value experiment is importing one real OpenTelemetry GenAI or Perfetto trace from another agent tool. |
| C2: Recursive operation stacks recover useful task/subtask/phase structure from linear agent trajectories. | Compare mapped-stack output against dataset-native boundaries and action/step labels. | Supported with scoped limits. R286 shows the same operation set can be folded from 9 dataset stacks to 57 phase stacks, 226 tool/semantic stacks, 455 action stacks, or 3,757 fixed-session stacks by changing only `--stack`; R290 adds OSWorld-Human desktop actions with phase/action V-measure 0.586 and exact-aligned grouped-action boundary F1 0.627 under a conservative `group_pattern` projection; R291 adds 1,000 AgentNet human desktop tasks / 16,741 operations with phase/action V-measure 0.674 and boundary F1 0.715 while carrying step correctness and redundancy as ordinary stackable operation fields. R295 adds a mechanical claim gate: recursive stacks support task, phase, action, human-group, safety, and quality-label views, but do not prove perfect intent recovery, one universal stack depth, or quality prediction from task outcome alone. R298 turns recursive depth, boundary, and diagnostic evidence into real-problem value blocks. R339 adds a sequence-scope adequacy scorer over the same six labeled tasks: ranked operation-stack groups are scored not just for positive operations, but for positive sessions hit and session scope touched. R355 extends that scorer below session scope over existing labels: 24 accuracy task-depth rows cover session, operation/step, positive-run, and task-specific units, plus one ScaleCUA context-only row; operation-stack query-aware has median 0.4342 budget-30 positive oracle-unit recall and 0.4908 positive-run recall, while explicit counterpoints keep positive-run and AgentRewardBench turn units out of human-intent claims. | Add stronger true subtask oracles such as instruction-step or solution-path labels before claiming broad latent intent-boundary recovery; current R355 scoring covers the available oracle depths but only OSWorld-Human `human_group` is a true subtask segment oracle. |
| C3: Label-derived operation-field mappings improve semantic aggregation. | Deterministic op-map files and learned boundary fields derived from labeled fields compared with no-map, leave-dataset-out, and held-out boundary baselines. | Supported with scoped limits. R282/R285 support deterministic learned-from-labeled-fields rule files, including held-out sessions and leave-dataset-out stress tests; R285 fixes the R284 API/tool negative cases by prioritizing a tool/API phase family before action-verb phase rules, keeps 0 negative stack-reduction regressions, and reports mapped phase/action V-measure above 0.7 on 7/9 held-out datasets, with API-Bank at 0.0 and ToolBench at 0.1342 as action-vocabulary counterpoints. R297 adds a supervised adjacent-boundary backend on held-out OSWorld-Human sessions: it predicts human-group boundaries with F1 0.7735 and writes `learned_group_pattern` fields that the Rust profiler folds into 74 stacks over 1,132 held-out operations. R299 extends the same backend pattern to existing AgentNet and AgentRewardBench labels and shows mixed calibration. R366 consolidates the mechanism evidence: held-out mapping improves compression 14.049->19.091 while intentionally coarsening fine action labels; leave-dataset-out mapping reduces stacks on 6/9 datasets with 0 negative reductions; profile-spec composition stays prompt/session-free on 12/12 variants; boundary backends beat the best simple baseline on 4/5 rows, while AgentRewardBench looping is fully explained by `repeat_signal_change`. R170/R180 support only the free-text tagger execution and grammar path: the local-history run handled 118,021 tag requests with 82,886 cache hits, 35,136 new local-model calls, and 0 failures; the small-model smoke produced 2,700/2,700 syntactically valid tags with p95 latency 18-32 ms. R405 checks the current tracked operation JSONL inputs for free-text/oracle suitability: 6 sources / 67,304 rows include 60,305 rows with oracle fields but no row that also exposes public free-form text fields and oracle semantic labels. R295/R298/R366/R405 gate final wording to deterministic/supervised field derivation; unsupervised/model-free intent discovery and same-input regex/embedding/LLM tagger accuracy remain unsupported. | Add calibrated boundary models, replicate on another tracked tool-dialogue operation JSONL, and compare against an LLM or sequence-model backend only after a same-input free-text semantic oracle exists and suitability gates pass; these are expansion probes, not prerequisites for the current scoped C3 claim. |
| C4: Operation-stack profiling localizes, ranks, and explains task-relevant failures, quality problems, and semantic boundaries on real labeled traces. | Compare flat, fixed-session drilldown, dataset-native hierarchy, raw action stack, operation-stack, query-aware ranking, and oracle upper-bound policies on the same labeled operations with precision@k, recall@budget, F1, AP/AUPRC-style score, nDCG, work-to-first-positive, fragmentation, and actionability metrics. Fixed-session drilldown is the current trace-tree-shaped baseline; real OpenTelemetry/OpenInference/Phoenix-style span-tree imports are future baselines. | Supported as hidden-label profiler benchmark, not human utility. R320 scores 144 policies over 6 tasks / 4 datasets / 34,539 operations and 3,699 positives: query-aware operation-stack top-5 work is 0.0937 versus flat 1.0, top-5 recall beats fixed-session on 5/6 tasks, and median groups fall from 285.0 to 157.5. R333/R334/R337/R339/R355 add inspection-budget, fragmentation, fixed-recall, sequence-scope, and oracle-depth evidence. R354/R358 provide mechanism/actionability evidence: 5/6 executable profile-spec patches improve AP, top-5 lift, and first-positive work, while the OSWorld-Human boundary-field ablation improves AP from 0.2402 to 0.2583 and reduces groups from 108 to 74 with preserved work counterpoints. R338/R352/R356/R357/R359/R360/R361 are scope-control and paper-organization checks, not empirical profiler evidence. | Broaden to additional oracle-rich tool/API/mobile families only if the paper needs wider generality; run human/agent analyst studies only for productivity or time-to-answer claims; import a real span-tree/OTel-style trace before ecosystem-specific compatibility or span-tree superiority claims. |

## Paper-Facing Research Questions And Core Experiments

The R-numbered runs are provenance, not the paper's evaluation structure. The
main paper should present three substantial empirical profiling experiments plus one replayability/scope-control block, and then cite individual R-runs as main comparisons, ablations,
counterpoints, or reproducibility gates. This avoids a chronological
"experiment log" and gives reviewers a clear claim-to-evidence path: RQ1/E1
establishes the operation/operation-stack abstraction across workloads, RQ2/E2
tests hidden-label profiler fidelity and baseline tradeoffs, RQ3/E3 isolates
mechanisms and actionability, and RQ4/E4 checks replayability, offline cost, and
claim scope without being treated as a fourth accuracy result or a fourth empirical profiling experiment.
New runs are allowed only when they strengthen one of these blocks as a primary
comparison, ablation, stress/counterpoint, provenance check, or scope check. A
run that cannot be assigned one of those roles should stay out of the main
paper rather than becoming another small experiment.

| RQ / paper block | Claim tested | Main workload and oracle | Main comparisons and metrics | Evidence placement |
|---|---|---|---|---|
| RQ1 / E1: Generality and recursive operation-stack formation | C1/C2/C3: two abstractions cover heterogeneous agent trajectories, and stack depth is a query over operation fields. | 15 public labeled trace families / 47,590 operations, plus local-session semantic-axis projections, duration/effect view projections, local-session exchange fixtures, and standard-trace exchange fixtures; OSWorld-Human and AgentNet provide the strongest boundary/quality labels. | Coverage, operations, stack counts, compression, semantic-axis mixing, duration/effect view divergence, V-measure, boundary F1, profile-spec replay, stack override, predicate replay, trace import/export equality, and boundary-based induced operation-stack depth. | Main results: R279-R292, R286, R290, R291, R170/R223/R224/R225, R293, R321, R342. Reproducibility/exchange support: R294/R303/R306/R353. Mapping, boundary-field, and operation-stack-induction probes: R281/R282/R285/R297/R299/R366/R402/R403/R404. |
| RQ2 / E2: Hidden-label localization and ranking | C4: profile groups can be scored as ranked localization outputs against real hidden labels. | Six oracle-backed failure/safety/quality/boundary tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human: 34,539 operations / 3,699 positives. | Flat, fixed-session drilldown, dataset-native, raw-action, operation-stack, label-drilldown, induced operation-stack, and oracle policies; AP/AUPRC-style score, precision/recall/F1@k, nDCG, recall@work budget, work-to-first-positive, groups, fragmentation, and oracle-depth scoring. | Main result: R320. Budget/fragmentation/depth/robustness slices: R330/R331/R333/R334/R337/R339/R344/R355. R403/R404 are mechanism-side induced-stack scoring and depth-sensitivity ablations inside E2/E3, not new main experiments. R300-R305/R308-R313 remain setup and case-packet provenance. |
| RQ3 / E3: Mechanism and actionability | C2/C3/C4: improvements come from stack shape, field derivation, ranking policy, and profile-spec patches, and the profiler exposes actionable knobs without becoming an automatic selector. | The same six labeled tasks plus held-out OSWorld-Human boundary-backend operations from R297. | Width vs visible rankers, induced recursive stacks, operation-level feature density, leave-one-feature ablation, equal/global/transfer policies, objective-specific selection, diagnostic lenses, casebook, action counterfactuals, held-out action transfer, before/after profile-spec patches, and field-derivation suitability checks. | Main actionability block: R324/R325/R326/R329/R335/R336/R340/R341/R342/R345/R346/R347/R348/R349/R350/R354. R358 is a mechanism ablation/counterpoint for the R354 OSWorld-Human rejection: boundary-derived fields help AP and reduce groups, but do not improve all inspection-cost metrics. R366 consolidates mapping/ranking/boundary mechanism evidence and preserves simple-field and inspection-cost counterpoints. R400 turns that evidence into guarded profile-configuration decisions rather than a universal selector. R403/R404 show induced stacks and depth caps are configurable folding evidence, not replacements for task-specific specs. |
| RQ4 / E4: Replayability, offline cost, and scope control | C1/C2/C4 scope checks: the profiler path is replayable, low-cost enough for offline artifacts, and the paper does not overclaim human utility, complete trace-ecosystem compatibility, universal selectors, or automatic boundary discovery. | Tracked profile specs, tracked operation inputs, local-session/agent-trace/standard-trace profile-spec input regressions, repeated profile outputs, runtime logs, and source-status rows; no dataset sync, no relabeling, no human/agent analyst task. | Semantic/raw determinism, sample/stack equality, input-source replay coverage, runtime and output size, source provenance, number alignment, scope checks, and abstraction-boundary checks. | Main reproducibility result: R327/R328. Implementation/exchange checks: R319/R353/R392. Claim/rubric/reviewer checks: R338/R352/R356/R357 constrain scope only, not empirical evidence and not part of the hidden-label accuracy comparison. Controlled analyst-study protocol R315/R316 remains optional for future human-utility claims only. |

## Historical Read-Only English Paper Experiment Gap

Status: pre-audit record. All `supported`, `paper-ready`, `accepted`, and
next-action wording in this historical ledger is superseded by the recovery
plan and decision rules above until G8 passes.

The current English submodule is useful as a read-only comparison point, but it is not the writable authority for the evaluation structure in this worktree.
Its Evaluation section still uses an older three-RQ organization: RQ1 covers semantic-axis separation, RQ2 covers hidden-label localization, and RQ3 covers derived-label reliability.
That draft folds profile-configuration actionability into RQ2 and places deterministic replay at the end of RQ3, while the outer Chinese paper and this ledger now separate the reviewer-facing evidence into E1 abstraction/recursive folding, E2 hidden-label localization, E3 mechanism/actionability, and E4 replayability/scope control.
The read-only audit therefore finds a paper-organization gap, not a required new small experiment.

The July 8 ledger judged that the outer evidence filled the main gaps in the English draft for the scoped claim; the recovery audit no longer treats that judgment as final support.
R402/R403/R404 support recursive operation-stack induction without a user-provided field chain, R407/R408 make that induction display visible in the Chinese paper and PDF, R354/R358/R400 support profile-configuration actionability, and R327/R328/R392 support replayability and input-source coverage.
The remaining experiment gaps are expansion gates only: a real OpenTelemetry/OpenInference/Phoenix-style span-tree import is needed before ecosystem-specific compatibility or span-tree-superiority claims, and a same-input free-form text plus hidden semantic-label oracle is needed before claiming regex/embedding/LLM tagger accuracy.
The July 8 conclusion that the next action was paper prose and figure/table
polish is superseded by the 2026-07-10 recovery plan at the top of this file.
The current next action is source-fidelity repair followed by one frozen,
label-stripped localization smoke task and strongest-baseline comparison.

R363 adds a visualization portfolio over these four paper-facing blocks rather than a
fifth experiment. It reads tracked R320/R345/R348/R354/R355/R358/R361/R362
artifacts and emits five views: a baseline tradeoff scatter, metric heatmap,
diagnostic-lens summary, actionability-knob chart, and oracle-depth adequacy
chart. These views are the paper's preferred presentation units for E2/E3
tradeoffs and actionability; flamegraphs remain one possible profiler output,
not the evaluation structure.
R365 then compresses the same E2/E3 evidence into paper headline and case-study
rows. It reads tracked R320/R333/R334/R345/R348/R354/R355/R358/R363 artifacts,
does not fetch data or rerun the profiler, and emits five headline rows plus six
task cards. The headline rows keep the main reviewer-facing story together:
Work@5 0.0937 versus flat 1.0, R@30% 0.3900 versus fixed-session 0.3559,
157.5 versus 285 median groups, 24/24 oracle-depth rows with lower unit work
than flat, 20/24 rows beating fixed-session unit recall, 27/36 objective rows
needing non-default actions, R354's 5/6 accepted profile-spec patches, and
R358's AP 0.2583 versus 0.2402 boundary-field mechanism ablation. R365 is a
paper-integration artifact, not a fifth experiment or a new profiler result.
R400 makes the E3 configuration guard explicit. It reads the tracked R325,
R358, and R366 artifacts without syncing data or rerunning the profiler, then
turns field-derivation evidence into five profile-knob decisions covering
deterministic mapping, stack depth and predicates, operation-level rank
features, supervised boundary-derived fields, and boundary-derived profile
repair. Its boundary-family matrix has one accept, three caution, and one
reject decision, which keeps field derivation scoped as a guarded configuration
loop rather than a universal automatic selector.
R402 closes the current implementation gap behind the "no user stack-field chain"
design requirement. It reruns Rust `agentpprof --induce-operation-stack` on one
tracked AgentRewardBench looping slice from R300, treats visible fields only as
boundary evidence, scores adjacent cuts with semantic-shift, changed-field,
query, and partition-coherence signals, permits the same evidence field to
recur at different recursive cuts, and emits induced `operation:` stacks. The
overview view covers 729 operations and produces 15 stacks with depth histogram
1/1/13 at depths 2/3/4; the session-candidate view covers the same operations
and produces 16 stacks with depth histogram 2/14 at depths 3/4. This is an
RQ1/E1 mechanism and visualization
replay, not a new hidden-label localization result and not a claim that all
intent boundaries are automatically discovered.
R403 scores that induced-stack path as a normal visible profiler view on the
six existing R300/R320 hidden-label tasks. It uses the tracked R300 operation
file and R320 baseline scores without dataset sync, reconstructs per-operation
stack groups from Rust split decisions, and verifies that 4/6 tasks produce
variable-depth stacks while 2/6 AgentNet quality tasks stop at one segment when
visible evidence has no material split. The induced view has median top-5 work
0.653 versus 1.0 for flat summaries and median 12.0 groups versus 285.0 for
fixed-session drilldown, while median AP remains below the hand-configured
operation stack, 0.2762 versus 0.3116. This strengthens the
E2/E3 recursive-folding mechanism claim without promoting automatic boundary
discovery or a fifth paper experiment.
R404 sweeps the same Rust induction path over depth caps 1 through 5 on the
same six hidden-label tasks. The profiler still receives only visible fields
and query hints; hidden labels are used only after profiling to score the
resulting groups. The depth surface is not flat: query-aware median AP peaks at
depth 3 with 0.2865, lowest median top-5 work occurs at depth 5 with 0.4727,
and material-split task AP-best depths span 2, 3, 4, and 5. Those four tasks
choose different depths for AP and top-5 work. This makes induced stack depth an actionable
profile-configuration knob rather than a user-supplied ontology or an automatic
selector.
R369 then turns the four paper-block rows into a reviewer evidence path. It reads
tracked R360/R361/R363/R365/R368 artifacts plus the current Chinese/English
paper text, emits a four-row table that maps each RQ to its main paper
table/figure, source artifact, guardrail, and non-claim, and does not fetch
data, relabel, or rerun the profiler. R369 is a paper-integration guardrail:
its purpose is to make the claim-to-evidence path auditable without reading
the chronological R-run ledger.
R370 then fixes the main-experiment contract. It reads tracked
R360/R361/R363/R364/R365/R368/R369 artifacts plus the current Chinese/English
paper text and requires each of the three empirical profiling experiments plus
the replayability/scope-control block to state a
primary test, workload/oracle, baselines and metrics, primary evidence,
supporting R-run roles, failure interpretation, and non-claim. R370 is the
guardrail for the "3-4 substantial experiments, not scattered small runs"
organization: later runs must strengthen E1-E4 as primary evidence, ablations,
counterpoints, provenance, or scope checks instead of creating new main
experiments by chronology.
R371 then audits the evaluation narrative focus in the paper text itself. It
checks that RQ1 does not absorb E3 ranker/actionability probes, RQ2 leads with
the R320 hidden-label localization benchmark before robustness slices, RQ3
explains rank-feature/mapping mechanisms before executable patch cases, and RQ4
leads with replay/cost evidence before scope-control checks. R371 is another
paper-organization guardrail: it changes no data, reruns no profiler, and adds
no fifth experiment.
R372 then audits main-body concision after the RQ2/E2 compaction. It checks
that the English RQ2 section now presents R330-R334/R355 as one supporting
audit block instead of five chronological run paragraphs, while preserving the
E2 primary numbers, scoped non-claims, Chinese compact wording, and RQ3
mechanism/actionability boundary. R372 changes no data, reruns no profiler, and
adds no empirical result.
R373 then converts the existing R320/R354/R355/R358/R365 task evidence into a
task-level claim-verdict matrix. It reports, for each of the six real labeled
tasks, the fidelity/work evidence against flat summaries, the fixed-session
tradeoff and counterpoint, the executable patch or boundary-field repair, and a
scoped verdict. R373 reads tracked artifacts only; it does not download data,
relabel traces, or rerun the profiler.
R374 then turns subagent reviewer feedback into a stricter paper-facing
three-plus-one role gate. It replaces main-body run-ledger presentation with a
primary-anchor/support-role/non-claim table, keeps R369-R373 in the artifact
ledger rather than main prose, narrows the span-tree wording to fixed-session
drilldown as the evaluated trace-tree-shaped proxy, and narrows fragmentation
claims to median/tradeoff wording. R374 reads tracked artifacts and paper text
only; it does not download data, relabel traces, or rerun the profiler.
R375 then turns the three empirical profiling experiments plus the
replayability/scope-control block into an explicit claim gate. It reads
tracked R361/R364/R370/R373/R374 artifacts plus the current Chinese/English
paper text, emits a four-row table that records each experiment's gate
decision, allowed paper claim, failure/narrowing rule, and must-not-claim
boundary, and does not download data, relabel traces, or rerun the profiler.
The historical R375 verdict labeled the strongest E2 wording supported as a hidden-label profiler benchmark; that verdict is now development evidence pending R002 and RQ2-D1/D2/D3:
operation-stack profiling reduces flat-summary inspection work and improves the
median-fragmentation tradeoff against the fixed-session drilldown proxy, while
metric dominance, human/agent analyst productivity, automatic boundary
discovery, automatic patch selection, and full trace-ecosystem compatibility
remain out of scope.
R376 then hardens the paper organization from earlier homogeneous
experiment-block wording into the intended three-plus-one shape: E1-E3 are the scientific
profiling experiments, while E4 is a replayability/scope-control block. It reads
current Chinese and English paper text, the evaluation ledger, and regenerated
R374/R375 role/claim tables. It does not download data, relabel traces, or
rerun the profiler. Its purpose is to prevent E4 from being used as hidden-label
accuracy evidence and to keep the Chinese user-facing document from framing the
novelty as flamegraph-only.
R377 then materializes the main profiler claim into five auditable evidence
facets: faithful hidden-label localization/ranking, less inspection work than
flat summaries, less fragmentation than the fixed-session drilldown proxy,
actionable optimization insight, and mechanism isolation under the
operation/operation-stack boundary. These facets route back into the same 3+1
paper structure rather than creating five smaller studies: the first three
belong to E2, the next two belong to E3 with E1/E4 supplying abstraction and
artifact guardrails. R377 reads tracked R320/R333/R334/R354/R355/R358/R366/
R375/R376 artifacts and current paper text only. It is not a new experiment; it
is the reviewer-facing proof route for the central claim and
keeps metric dominance, human utility, automatic boundary discovery,
automatic patch selection, and ecosystem-compatibility claims out of scope.
R378 then tightens the main-body presentation budget. It keeps the E2/E3
non-flamegraph figure and core tables in the papers, but demotes the R363 full
portfolio table, R365 headline/case tables, and R373 verdict matrix to artifact
ledger material. This is not new empirical evidence; it is a paper-integration
guardrail that prevents the 3+1 evaluation from looking like a scattered
sequence of small table generators.
R379 then tightens the RQ2/RQ3 prose itself. It checks that RQ2 starts with the
primary comparison, success criterion, baseline scope, and failure
interpretation before support-run details, and that RQ3 starts with the
mechanism/actionability question, hidden-label no-leakage rule, executable
profile-spec loop, and non-claims. Like R378, it is a paper-integration
guardrail; it does not add a dataset, rerun the profiler, or create a new
empirical experiment.
R380 then enforces the higher-level experiment-block shape requested for the
paper: three substantial empirical profiling experiments plus one
replayability/scope-control block, not a series of small run-ledger experiments.
It checks that the English and Chinese papers keep RQ1/E1--RQ4/E4 as the
paper-facing blocks, that R-numbered runs are provenance/support inside those
blocks, and that the implementation/RQ3/RQ4 prose no longer narrates R321-R329
or R327-R328 chronologically. It is a paper-integration guardrail only: no
dataset sync, no relabeling, no profiler rerun, and no new empirical result.
R381 then strengthens the E3 presentation by turning the existing R365/R373
task cards into compact diagnosis/actionability summary rows in the English
and Chinese papers. Each row ties a label-scored localization signal to a
concrete profile action plus a scoped verdict with counterpoints for
one of the six oracle-backed tasks. R381 reads the existing task-card/verdict
artifacts and current paper text only; it does not fetch data, relabel, or rerun
the profiler, and it remains inside the 3+1 evaluation structure.
R382 then aligns the canonical research docs with that same shape. It updates
the idea story and design text from the older "four core experiments" wording to
the current three empirical profiling experiments plus one
replayability/scope-control block wording, and checks the canonical docs, papers,
ledger, R380, and R381 together. R382 is a documentation-consistency gate only;
it does not fetch data, relabel traces, rerun the profiler, or add another
empirical result.
R383 records the independent reviewer closure for the R382 cleanup. Four
read-only reviewers checked canonical-doc experiment organization, claim-safety
boundaries, E4 scope boundaries, and paper/ledger consistency; all
four returned ACCEPT with zero blocking issues. R383 reads R380/R381/R382 and
current docs/papers only, and remains a paper-integration guardrail rather than
new empirical profiler evidence.
R393 records the independent reviewer closure after the R392 E4 input-source
replay update. Four read-only reviewers checked the current canonical docs and
paper drafts; three accepted immediately, and one flagged a Chinese dataset
caption that incorrectly implied the first 14 sources were oracle-rich. The
caption now separates E1's 15 public labeled sources from RQ2/E2's four
oracle-rich hidden-label families, and the blocking reviewer returned ACCEPT.
R393 checks that R392 remains E4 replay/scope evidence, not a new accuracy
experiment, third abstraction, human-utility claim, or ecosystem-compatibility
claim.
R394 closes the follow-up two-abstraction documentation drift after the Chinese
`agentpprof` guide cleanup. It checks the Rust CLI wording, English and Chinese
user guides, canonical docs, and Chinese/English papers for the same contract:
tagging, mapping, LLM tags, clustering, predicates, and profile specs derive
operation fields or configure queries before operation-stack folding; they do
not add a third profiler abstraction or automatic intent-boundary detector. It
is a documentation-consistency guardrail only, not a dataset sync, profiler
rerun, human/agent analyst task, or new empirical result.
R395 closes the latest main-claim/verdict alignment after the R380/R391
three-plus-one consolidation repair. It checks `docs/idea-story.md`, this
evaluation ledger, and the Chinese/English papers for one consistent central
claim: hidden-label localization/ranking, lower flat-summary inspection work,
a fixed-session drilldown proxy fragmentation tradeoff, configuration-level
actionability, and explicit non-claims for human productivity, automatic
boundary discovery, metric dominance, complete trace-ecosystem compatibility,
and universal selectors. It is a paper-integration guardrail only, not a
dataset sync, profiler rerun, new empirical result, or human/agent analyst task.
R396 closes a paper-build smoke gate after the claim-verdict alignment. It
builds the English ACM draft with `make` in a temporary copy, builds the
Chinese draft with two `xelatex` passes into a temporary output directory,
checks both generated PDFs exist, checks final copied logs have no unresolved
references or citations, and verifies the English ACM accessibility warning for
the non-flamegraph portfolio figure is gone after adding a `\Description`.
This is an E4 reproducibility/paper-readiness guardrail only, not a fifth
experiment, dataset sync, profiler rerun, new empirical result, or human/agent
analyst task.
R397 closes a main-body run-ledger suppression gate under the current
English-submodule read-only policy. It checks the Chinese and English paper
bodies for residual `R###` run identifiers, requires the writable Chinese draft
to preserve RQ1/E1--RQ4/E4 as the reviewer-facing evaluation path, accepts the
English side only when it is synced or R405 records the read-only sync gap,
checks that the main papers avoid internal checklist-style terms such as
`Claim test`, `Claim-test`, `Experiment contract`, `实验契约`, and
`artifact ledger`, and keeps R-numbered runs in this ledger as provenance
rather than main-paper structure. This is a paper-integration guardrail only,
not a dataset sync, profiler rerun, new empirical result, fifth experiment, or
human/agent analyst task.
R398 closes a current three-plus-one organization regression gate after the
Chinese display-path update. It requires the writable Chinese paper to carry
exactly RQ1/E1--RQ4/E4, verifies E2 remains the single hidden-label accuracy
block, keeps E3 mechanism/actionability evidence from becoming a fifth
experiment, keeps E4 as replayability/scope-control rather than
accuracy/human/ecosystem evidence, rejects paper-facing venue-readiness
self-undercut wording and internal checklist-style regressions, checks this
ledger plus the idea story still reject scattered new empirical blocks, and
treats English only as synced or as the R405 read-only gap. This is a
paper-organization guardrail only, not a dataset sync, profiler rerun, new
empirical result, fifth experiment, or human/agent analyst task.
R399 closes a tracked-PDF freshness gate after the display-path cleanup. It
uses `pdftotext` on the committed Chinese PDF and verifies that the rendered
artifact contains the same workload-provenance, hidden-label
fidelity/baseline-tradeoff, mechanism/actionability, and replay/cost display
path that the TeX source exposes. It also checks R396/R398/R405 are still
passing and treats English PDF/source drift through the read-only R405 sync
gap instead of editing the submodule. This is an E4 scope-control guardrail
only, not a paper rebuild, dataset sync, profiler rerun, new empirical result,
fifth experiment, or human/agent analyst task.
R409 closes an English-submodule read-only policy gate. It checks the requested
outer worktree path, the research/v2 branch, AGENTS/CLAUDE submodule policy,
the current dirty-but-unstaged submodule state, R405/R397/R398/R399 gap-aware
behavior, canonical-doc policy wording, and direct-push safety. It records that
direct push is unsafe while ahead history contains a submodule gitlink update.
This is a collaboration/reproducibility guardrail only, not a paper edit, paper
build, dataset sync, profiler rerun, new empirical result, fifth experiment, or
human/agent analyst task.
R366 consolidates C3/E3 field-derivation mechanism evidence. It reads tracked
R282/R285/R297/R299/R325/R342/R358 artifacts, does not fetch data or rerun the
profiler, and emits six mechanism rows plus five boundary-family rows. The
headline is scoped: deterministic mappings improve aggregation and reduce
fragmentation; profile specs compose mappings, predicates, rank rules, and
stack depth; rank-feature ablations identify useful and misleading fields; and
supervised boundary backends beat the best simple baseline on 4/5 rows. The
explicit counterpoint is equally important: mapping can coarsen fine action
labels, AgentRewardBench looping is better explained by `repeat_signal_change`,
and R358 improves AP/groups while increasing some inspection-work metrics.
Thus R366 supports first-class field derivation, not automatic intent boundary
discovery and not a new profiler object.
R360/R361/R364 now consume R366 as internal RQ1/E1 and RQ3/E3 evidence: the
paper still has three empirical profiling experiments plus one
replayability/scope-control block, and R366 is not a fifth core experiment.

## Paper-Ready Synthesis

Historical status: this synthesis records the pre-audit interpretation and is
not current paper-ready wording. Rebuild it only after G8.

The current paper should claim mechanism, profiler fidelity with respect to
dataset-provided hidden labels, localization and ranking accuracy, and
actionable tradeoffs on real labeled traces, not user
productivity.
The strongest story is that a two-object model, operations plus operation
stacks, can express profiling views over heterogeneous public agent trajectories
without hard-coding prompt/session/span boundaries. The core novelty is that
the agent-operation record model is coupled to recursive multi-field
operation-stack shapes: changing the stack changes the localization unit,
inspection cost, and fragmentation while leaving the operation layer unchanged.
This is narrower than generic query-time aggregation because pprof already has
sample tags and tag pseudo frames, and Perfetto already has SQL/derived trace
analysis. The best evidence blocks are
R286 recursive-depth sweep, R282/R285 mapping validation, R290 OSWorld-Human
grouped boundaries, R291 AgentNet step-quality labels, and R288/R289
failure/safety diagnostics. R293 adds the reproducibility hook: a tracked
profile spec replays the AgentNet operation-stack query and lets reviewers
change stack depth without reassembling shell commands. R321 extends that
implementation hook with explicit `where_rules`: profile specs now record the
operation source, mapping rules, query predicate, stack projection, and output,
and the Rust profiler selects the expected R300 operation subsets before
folding. R322 adds a Rust JSON rank-rule surface over the same operation-stack
groups: visible stack-text rank rules improve AP over width on 4/6 tasks and
top-5 lift on 3/6 tasks, while preserving SATraj and side-effect as evidence
that binary regex boosts are weaker than the full R320 group-feature rankers.
R323 turns that negative result into a rank-mode mechanism probe: `rule-score`
improves AP over `width-boost` on 4/6 tasks and top-5 lift on 4/6 tasks while
leaving side-effect and OSWorld-Human as ranker-depth counterexamples.
R324 moves group-feature ranking into Rust: `rank_op_rules` match visible
operation `field=value` tokens, aggregate matched operation weight inside each
folded group, and emit auditable per-group feature contributions. The harness
first writes a scrubbed visible-operation JSONL for Rust, removing R300 oracle
fields; the original labels are not passed to Rust and are used only for
offline scoring. On
semantic stacks, AP improves over width on 5/6 tasks, top-5 lift on 4/6, and
first-positive work on 5/6; a coarser stack depth improves AP on 4/6 while
reducing group fragmentation. OSWorld-Human remains a boundary-derived-field
counterexample rather than a ranker win.
R325 turns this into an actionability ablation: the same scrubbed profiler
input and stack projections are replayed with newly generated profile specs
that remove one visible operation feature at a time. It identifies 7
critical feature instances, including `repeat_signal` for AgentRewardBench
looping, `write-action` for side effects, and `status=success` for SATraj
safety; it also finds 3 misleading feature instances, including a SATraj
loop-like rule and OSWorld-Human input-phase rules. Coarse stack depth is
AP-preferred on only 2/6 tasks but reduces groups in all 6, so stack depth is a
cost/accuracy knob rather than a universally better abstraction.
R326 probes whether those rank features are brittle hand-tuned weights. It
replays the same scrubbed profiler input through five visible policies:
width, the R324 task-weighted policy, an equal-weight task policy, a global
equal-weight feature bank, and an R325-guided repaired policy that drops
misleading features. The global equal policy improves AP over width on 4/6
semantic tasks and 5/6 coarse tasks, and improves semantic first-positive work
on 4/6 tasks. The equal-weight task policy stays within 0.02 AP of the
weighted policy on 8/12 task/depth variants. The repaired policy improves AP
on 2/3 misleading-feature cases and first-positive work on 2/3 cases; 1/3
improves both metrics. This is robustness
and post-hoc actionability evidence, not a claim that the deployed profiler has
learned a label-free universal ranker.
R342 then audits the composition boundary that matters for the two-object
abstraction. It reuses the tracked R324 Rust outputs over the R300 real labeled
operation suite and checks that 12/12 profile specs combine operation sources,
query predicates, visible per-operation rank rules, score-first ranking, and
explicit recursive stack depths without introducing prompt/session frames.
Those same composed variants improve AP over width on 9/12 task-depth variants
and first-positive work on 10/12, while coarse depth reduces group counts on
6/6 tasks with median group reduction 0.8267. Best AP still splits by task
between semantic and coarse depth, so this supports configurable recursive
folding and stack-depth actionability rather than a universal stack selector.
R344 then audits the metric surface so the value claim is not AP-only. It
reuses the R320 scored policy table and compares operation-stack query-aware
against flat, fixed-session, dataset-native, raw-action, and width-only
operation-stack baselines across AP/AUPRC-style score, nDCG, P/R/F1@5, 30%
work-budget recall/F1, top-5 work, work-to-first-positive, and group count.
Thirty of fifty baseline-metric comparisons support the scoped claim, sixteen
are explicit counterpoints, and four are mixed or weak. The useful conclusion
is not metric dominance: AP, budget recall/F1, inspection work, and fixed-session
fragmentation support the profiler-localization tradeoff, while nDCG and
coarse top-k recall remain secondary/counterpoint metrics because flat or
dataset-native groups can score well by inspecting very broad groups.
R344 token ledger for auditability: flat AP 6/6, budget30 recall 6/6, work-to-first-positive 6/6, fixed-session top-5 F1 5/6, fixed-session groups 4/6, width AP 6/6, and width budget30 recall 5/6.
R345 then turns the actionability evidence into a diagnostic-lens portfolio rather than another single-metric result. It reads the tracked R335/R341/R344 artifacts and groups the existing scored outputs into six analysis lenses: ranked-stack AP, hot-stack F1, budgeted inspection, first-positive drilldown, recall-fragmentation, and group-fragmentation overview. Across 36 objective rows, operation-stack-family views win 11 objectives, non-operation-stack counterpoints win 25, and all 6/6 tasks need at least three best views across objectives; the result is a lens portfolio for optimization, not a universal selector.
R345 token ledger for auditability: 6 tasks, 4 datasets, 6 diagnostic lenses, 36 objective rows, 6/6 actionable task cards, 5 distinct optimization actions, 9/36 default operation-stack, 11/36 operation-stack family, 25/36 counterpoints, 6/6 tasks need at least three best views, 3 best views, 4 best views, 46 counterpoint rows, 30 support, 16 counterpoints, and 4 mixed/weak.
R346 turns the top-ranked operation-stack groups into a diagnostic casebook. It reads the tracked R335/R345 artifacts and the existing public labeled operation JSONL, selects top-5 operation-stack groups with the visible query-aware ranker, keeps a visible packet separate from the hidden-label answer key, and links each case to a diagnostic lens, optimization action, and counterpoint.
R346 token ledger for auditability: 6 tasks, 4 datasets, 30 case groups, top-5 operation-stack groups, 5/6 top-1 positive tasks, 6/6 top-5 positive tasks, median top-5 recall 0.188, median top-5 precision 0.1991, median top-5 lift 1.6508, median top-5 work 0.0937, median first-positive work 0.0378, 6/6 actionable case cards, 6/6 counterpoints, 6/6 tasks need at least three best views, 3 best views, and 4 best views.
R347 compares those case-level operation-stack outputs against flat, fixed-session, dataset-native, and raw-action views under the same visible top-5 query-aware protocol. It keeps hidden labels out of ranking and uses them only to score already-ranked groups, so the result is a baseline-contrast case audit rather than a new oracle selector.
R347 token ledger for auditability: 6 tasks, 4 datasets, 5 visible views, 30 view-task rows, top-5 groups, 6/6 top-5 positive tasks, 5/6 top-1 positive tasks, median top-5 recall 0.188, median top-5 lift 1.6508, median top-5 work 0.0937, median first-positive work 0.0378, 6/6 wins vs flat top-5 work, 5/6 wins vs fixed-session top-5 recall, 4/6 wins vs fixed-session group count, 6/6 tasks with counterpoints, 6 task cards, 24 baseline-pair rows, 124 top-group rows, fixed-session first-positive counterpoint 4/6, and flat full-work recall counterpoint 6/6.
R348 turns actionability into an objective-level counterfactual audit. It reads tracked R335/R341/R347 artifacts, uses hidden labels only through already-scored visible policy rows, and asks which knob would have to change relative to default operation-stack query-aware for each objective. Across 36 objective rows, 36/36 best rows are visible non-oracle, 27/36 require non-default actions, 25/36 require view changes, 2/36 require operation-stack ranker tuning, and all 6/6 tasks have at least three action classes plus case counterpoints.
R348 token ledger for auditability: 6 tasks, 4 datasets, 36 objective rows, 27/36 non-default action rows, 9/36 default-best rows, 36/36 visible non-oracle best rows, 25/36 view-change rows, 2/36 operation-stack tuning rows, 25/36 non-operation-stack counterpoints, 6/6 tasks with non-default actions, 6/6 tasks with at least three action classes, 6/6 tasks with case counterpoints, median gain over default 0.1447, median non-default gain 0.6188, max gain 288.0, 6 actionability cards, 5 visible views, 6 action classes, 7 flat counterpoint rows, 7 fixed-session drilldown rows, 5 dataset-native rows, 6 raw-action rows, 9 keep-default rows, and 2 operation-stack ranker rows.
R349 turns R340 held-out policy transfer into a stricter action-transfer guardrail. It maps non-target-selected visible policies to action classes and compares them against the R348 target-task action oracle. The result is intentionally mixed: held-out transfer often preserves metric tolerance, but exact action-class transfer is too weak to claim a label-free automatic selector, especially for non-default target actions.
R349 token ledger for auditability: 96 transfer decisions, 60 aligned decisions, 36 excluded decisions, 5 aligned objectives, 6 tasks, 4 datasets, 60/60 selected visible non-oracle, 60/60 best visible non-oracle, 50/60 best-policy matches, 10/60 best-policy mismatches, 7/60 exact action, 7/60 policy exact, 13/60 R340 exact best, 11/60 view exact, 27/60 ranker exact, 35/60 within tolerance, 30/60 beats default, 26/60 default within tolerance, 42 non-default target rows, 2/42 non-default exact action, 24/42 non-default within tolerance, 2/42 selected default action, leave-task 4/30 exact action, leave-dataset 3/30 exact action, leave-task 18/30 within tolerance, leave-dataset 17/30 within tolerance, 36 sequence objective exclusions, 6 R348 untransferred objectives, 13 summary rows, 16 action-confusion rows, and 12 task cards.
R350 turns the casebook, baseline contrast, action counterfactual, and held-out guardrail into bounded evidence packets. It reads tracked-clean R346/R347/R348/R349 artifacts, does not rerank or relabel data, and uses hidden labels only through already-scored upstream artifacts.
R350 token ledger for auditability: 6 tasks, 4 datasets, 36 objective rows, 6 action classes, 6/6 top-5 positive packets, 5/6 top-1 positive packets, 4/6 strict 30% work packets, 4/6 first-positive <=10% work packets, 6/6 baseline counterpoints, 6/6 non-default action packets, 6/6 three-action-class packets, 6/6 beats flat work, 5/6 beats fixed recall, 4/6 fewer groups than fixed, median top-5 work 0.0937, median first-positive work 0.0378, median top-5 recall 0.188, median top-5 lift 1.6508, 27/36 non-default objective rows, 36/36 visible non-oracle best rows, median non-default gain 0.6188, max gain 288.0, 60 aligned transfer decisions, 35/60 within tolerance, 7/60 exact action, 24/42 non-default within tolerance, 6 task packets, 36 objective packets, and 7 budget rows.
R354 makes one actionability link executable instead of purely synthetic. It
reads the tracked R324 visible-operation profiler input and R348 action cards,
writes default semantic-width profile specs plus profile-guided patched specs,
executes the maintained Rust `agentpprof --profile-spec` path for both, and
scores the emitted groups with hidden labels only after profiling. The result
is 5/6 accepted patches, AP improvement on 5/6 tasks, top-5 lift improvement on
5/6, first-positive-work improvement on 5/6, median AP delta 0.0376, and one
intentional rejection: OSWorld-Human needs boundary-derived fields rather than
visible phase/action rank features alone. This is executable actionability
evidence, not a human/agent analyst study or an automatic label-free patch
selector.
R354 token ledger for auditability: 6 tasks, 4 datasets, 12 Rust profile-spec
invocations, 5/6 accepted patches, 1/6 rejected-or-needs-mapping patch, 5/6 AP
improved tasks, 5/6 top-5 lift improved tasks, 5/6 first-positive-work improved
tasks, 2/6 group-reduced tasks, median delta AP 0.0376, median delta top-5 lift
0.5750, median delta first-positive work -0.0859, and source policy
`tracked_clean`.
R355 extends the R339 session-scope audit downward to the oracle depth available
in each existing labeled task. It reuses tracked R300/R320/R339 operation JSONL
and visible policy outputs, then scores session, operation/step, positive-run,
and task-specific units only after ranking. The default operation-stack
query-aware policy has median top-5 oracle-unit work 0.1307, median budget-30
positive oracle-unit recall 0.4342, median budget-30 positive oracle-unit F1
0.4484, and median positive-run recall 0.4908. Against flat, it uses lower
top-5 unit work on 24/24 task-depth rows and lower operation work to 50%
positive units on 24/24. Against fixed-session, it has higher budget-30
positive-unit recall on 20/24 rows, higher budget-30 unit F1 on 18/24, and
fewer groups to 50% positive units on 22/24. Against raw-action, it has fewer
positive units per group on 24/24. The counterpoint is equally important:
`budget30_positive_session_without_unit_hit` does not improve over fixed-session
on any row, so the result supports a depth-aware triage surface, not complete
subtask or intent-boundary recovery.
R355 token ledger for auditability: 6 tasks, 4 datasets, 24 accuracy
task-depth rows, 16 subtask-eligible rows, 5 true subtask-oracle rows, 1
ScaleCUA context-only row, 6 visible policies, median top-5 unit work 0.1307,
median budget-30 unit recall 0.4342, median budget-30 unit F1 0.4484, median
positive-run recall 0.4908, 24/24 lower top-5 unit work than flat, 20/24 higher
budget-30 unit recall than fixed-session, 18/24 higher budget-30 unit F1 than
fixed-session, 22/24 fewer groups to 50% positive units than fixed-session,
24/24 fewer positive units per group than raw-action, and source policy
`tracked_clean`.
R356 refreshes the paper claim-integrity gate for these newer supplements. It
reuses the R338 R320-R350 gate, then hashes the tracked R354 and R355 artifacts,
checks R354/R355 paper tokens across the evaluation ledger and Chinese/English
drafts, and verifies source provenance, must-not-claim guardrails, and the
two-abstraction boundary. R356 is not a new empirical result; it is a
claim-integrity audit ensuring that R354's executable profile-spec patch result
and R355's oracle-depth adequacy result are represented without automatic
patch-selector, human-utility, ecosystem-compatibility, or complete
intent-boundary-discovery claims.
R356 token ledger for auditability: R338 base gate pass, R354 status pass, R355
status pass, R354 5/6 accepted patches, R354 median delta AP 0.0376, R354
median delta top-5 lift 0.5750, R355 24 accuracy task-depth rows, R355 median
budget-30 unit recall 0.4342, R355 20/24 higher unit recall than fixed-session,
R355 22/24 fewer groups to 50% positive units than fixed-session,
source_artifacts_tracked_clean=true, network_access_required=false, and
profiler_abstractions=`operation` plus `operation stack`.
R351 records the current independent reviewer closure after R350/R338. Four read-only subagent reviewers focus on OSDI/SOSP systems framing, NeurIPS/ML hidden-label evaluation, artifact reproducibility, and claim-safety guardrails; all four return ACCEPT with zero blocking issues. The script also rereads R320/R328/R331/R338/R350 and checks hidden-label leakage, R328 clean deterministic-output provenance, no dataset sync/relabeling, R338 integrity, R350 bounded packet numbers, and visible must-not-claim wording. R351 is a paper-readiness gate, not empirical evidence and not a human/agent analyst-study result.
R351 token ledger for auditability: 4 reviewers, 4/4 final ACCEPT, 0 blocking issues, 11/11 acceptance checks, 1 resolved residual risk, R328 76/76 semantic and raw-byte deterministic specs with empty git/code status, R338 350 number checks / 78 source-policy checks / 16 guardrail checks, R350 6 tasks / 4 datasets, 6/6 top-5 positive packets, 4/6 strict 30% work packets, and network_access_required=false.
R352 maps the existing evidence to the evaluation standard expected of a profiling paper. It reads tracked R320-R351 artifacts and current paper text, does not download or sync datasets, does not rerun the profiler, and checks whether the scoped claim has evidence for faithful localization/ranking, actionability, baseline tradeoffs, generality, mechanism isolation, statistical robustness, reproducibility, and must-not-claim boundaries. It passes 26/26 required checks and classifies the current evidence as `level_4_scoped_profile_benchmark`.
R352 token ledger for auditability: 26/26 checks, 10/10 rubric areas passed, 6 tasks, 4 datasets, 36 objective rows, 6/6 top-5 positive packets, 4/6 strict 30% work packets, 35 within-tolerance transfer decisions, 7 exact-action transfer decisions, empirical_sources_tracked_clean=true, network_access_required=false, not_new_empirical_result=true, not_a_human_study_result=true, and profiler_abstractions=`operation` plus `operation stack`.
R357 refreshes reviewer acceptance after R356. Four current read-only reviewers
cover OSDI/SOSP systems framing, NeurIPS/ML hidden-label evaluation,
artifact/provenance, and claim-safety; all four return ACCEPT with zero
blocking issues. The script rereads tracked R351/R352/R354/R355/R356 artifacts
and current paper/docs hashes, checks R356's 69/69 number checks, 18/18 text
checks, 54/54 guardrail checks, R354's executable patch numbers, R355's
oracle-depth numbers, R352's rubric level, R351's prior acceptance gate, and
the operation and operation stack abstraction boundary. R357 is a
submission-readiness gate and not a new empirical result, not a human/agent
analyst study, and not a trace-ecosystem compatibility result.
R357 token ledger for auditability: 4 reviewers, 4/4 current ACCEPT, 0
blocking issues, 3 non-blocking traceability notes, R356 69/69 number checks,
18/18 text checks, 54/54 guardrail checks, R354 5/6 accepted patches, R354
median delta AP 0.0376, R354 median delta top-5 lift 0.5750, R355 24
accuracy task-depth rows, R355 median budget-30 unit recall 0.4342, R355
20/24 higher unit recall than fixed-session, R355 22/24 fewer groups to 50%
positive units than fixed-session, R352
`level_4_scoped_profile_benchmark`, source_gate=pass,
network_access_required=false, and profiler_abstractions=`operation` plus
`operation stack`.
R358 closes the R354 OSWorld-Human rejection loop as a mechanism ablation, not
a new main experiment. It reuses tracked R297 held-out boundary-backend
operations, strips oracle/group labels from the Rust profiler input, keeps
learned boundary fields as visible operation fields, writes
flat/fixed/semantic/learned-boundary profile specs, runs Rust
`agentpprof --profile-spec`, and scores hidden labels only after profiling.
Learned-boundary folding improves AP to 0.2583 versus 0.2402 for semantic
width and 0.2253 for the visible-rank patch, reduces groups to 74 versus 108
semantic groups and 96 fixed-session groups, and improves top-5 recall by
0.1111 versus semantic width. The counterpoint is explicit: top-5 operation
work increases by 0.0813 versus semantic width, first-positive work increases
by 0.1581, and learned-boundary rank rules reduce AP by 0.0224 versus width.
This supports boundary-derived operation fields as an RQ3/E3 actionability knob;
it does not support automatic boundary discovery, a universal patch selector,
or human/agent analyst utility.
R358 token ledger for auditability: 1,132 held-out operations, 243 positives,
6 visible policies, 2 hidden upper bounds, learned-boundary AP 0.2583,
semantic-width AP 0.2402, visible-rank AP 0.2253, learned-boundary groups 74,
semantic groups 108, fixed-session groups 96, top-5 recall delta versus
semantic 0.1111, top-5 work delta versus semantic 0.0813, first-positive-work
delta versus semantic 0.1581, learned-boundary rank AP delta -0.0224, no
dataset sync, no relabeling, no human/agent analyst task, and
profiler_abstractions=`operation` plus `operation stack`.
R359 audits the paper structure after the RQ1/E1-RQ4/E4 consolidation. It reads the
evaluation ledger, Chinese claim setup, Chinese draft, English submodule draft,
and R358 artifacts; it does not rerun the profiler, download data, sync data,
create labels, or form a new empirical result. The gate passes 13/13 checks:
the paper-facing evaluation has RQ1/E1-RQ4/E4 as three empirical profiling
experiments plus one replayability/scope-control block, legacy scattered RQ
framing is absent from the drafts, the Chinese main result table is a four-row
RQ/paper-block table, R-numbered runs are provenance rather than main structure,
R358 is positioned as an RQ3/E3
mechanism/actionability ablation rather than a fifth experiment, the R358
AP/group/counterpoint tokens remain visible, and the two-abstraction and
must-not-claim guardrails remain visible.
R359 token ledger for auditability: 3 empirical profiling experiments plus 1 replayability/scope-control block, 13/13 checks,
R358 learned-boundary AP 0.2583, semantic-width AP 0.2402, learned-boundary
groups 74, top-5 work delta 0.0813, first-positive-work delta 0.1581, no new
empirical result, no human/agent analyst task, no dataset sync, and no fifth
core experiment.
R360 materializes the RQ1/E1--RQ4/E4 main result table from tracked artifacts. It reads
R285/R286/R320/R328/R338/R342/R353/R354/R355/R357/R358/R359/R366 plus the current
paper/docs, writes JSON/CSV/Markdown/HTML and a LaTeX table fragment, and does
not rerun the profiler or touch datasets. The generated table has 4 paper-block
rows and 20 metric rows: RQ1/E1 includes 13,265 recursive-depth-sweep
operations, 8 stack depths from 9 to 3,757 stacks, 6/9 positive
leave-dataset-out stack reductions, 12/12 prompt/session-free profile specs,
R366 field-derivation mechanism rows, and a 512-operation standard-trace round trip; RQ2/E2 preserves the 6-task /
4-dataset / 34,539-operation / 3,699-positive / 144-policy benchmark and the
0.0937 vs 1.0 top-5 inspection-work headline; RQ3/E3 preserves R354 5/6 accepted
patches, median delta AP 0.0376, median top-5 lift 0.5750, R358 AP 0.2583 vs
0.2402, R366 7 critical and 3 misleading field rows, and the top-5-work/first-positive-work counterpoints; E4 preserves only
the R328 replay/cost result: 76/76 semantic and raw-byte deterministic specs
over 152 profiler invocations with median runtime 1.601s and p95 2.767s.
R338/R352/R357/R359 remain scope-control checks, not main-table evidence.
R360 is a table consolidation gate, not a new empirical result.
R360 token ledger for auditability: 4 paper-block rows, 20 metric rows, 8/8 checks,
no profiler rerun, no dataset sync, no relabeling, no human/agent analyst
task, and profiler_abstractions=`operation` plus `operation stack`.
R361 turns the RQ1/E1--RQ4/E4 table into a reviewer-facing claim-evidence ledger. It
reads tracked R320/R352/R354/R355/R357/R358/R359/R360/R366 artifacts plus the
current evaluation ledger and Chinese/English drafts, then emits JSON, CSV,
Markdown, HTML, and a LaTeX fragment. Each paper-block row records its
claim, research question, oracle, baselines, primary metrics, headline result,
actionable insight, counterpoint, scoped wording, and primary sources. The gate
passes 11/11 checks, including hidden-label scale/metric coverage, baseline
tradeoff rather than metric dominance, oracle-depth/fragmentation evidence,
field-derivation mechanism integration, mechanism/actionability counterpoints, reproducibility and scope-control
gates, the two-abstraction boundary, and must-not-claim guardrails. R361 is not a new
empirical result, does not rerun the profiler, and does not sync, create, or
relabel datasets.
R361 token ledger for auditability: 4 paper-block claim rows, 11/11 checks, R320
6 tasks / 4 datasets / 34,539 operations / 3,699 positives, R355 24
oracle-depth rows with 20/24 fixed-session recall wins and 22/24
groups-to-50% wins, R354 5/6 accepted patches, R358 learned-boundary AP
0.2583 vs 0.2402 with top-5-work and first-positive-work counterpoints, R366
6 mechanism rows and 5 boundary-family rows, R360
8/8 scope-control checks, and profiler_abstractions=`operation` plus
`operation stack`.
R362 then audits that the R361 ledger is visible in the actual paper sections.
It parses the Chinese and English RQ1/E1--RQ4/E4 result subsections and checks that
each section states claim, oracle, baseline, metric, and counterpoint/scope
tokens; E2 additionally carries precision@k, recall, F1, nDCG, and
work-to-first-positive; E3 carries actionable and not-automatic guardrails; E4
carries not-live and not-human guardrails. The gate passes 16/16 checks and
8/8 section-token rows. R362 is a paper-section readiness gate, not a new
empirical result, profiler rerun, dataset sync, relabeling step, or human/agent
analyst task.
R362 token ledger for auditability: 16/16 checks, 8 section-token rows,
Chinese and English RQ1/E1-RQ4/E4 subsections present, R361 11/11 reused as source,
must-not-claim scope visible, prompt/session/tool/process/syscall kept as
operation forms or operation fields, and profiler_abstractions=`operation`
plus `operation stack`.
R363 then turns the RQ1/E1-RQ4/E4 evidence into a paper visualization portfolio. It
reads tracked R320/R345/R348/R354/R355/R358/R361/R362 artifacts, writes SVG,
CSV, Markdown, HTML, JSON, and a LaTeX table fragment, and runs no profiler or
dataset sync.
The five generated views are baseline tradeoff, metric heatmap, diagnostic
lenses, actionability knobs, and oracle-depth adequacy. R363 is not a new
empirical result, not a human/agent analyst task, and not a flamegraph-only
claim; it is a reviewer-facing presentation layer over operation and
operation-stack evidence.
R363 token ledger for auditability: 5 paper views, `portfolio-table.tex`, 7/7 checks, baseline
tradeoff preserves lower operation-stack query-aware top-5 work than flat and
at least fixed-session budget recall, diagnostic lenses preserve
non-operation-stack counterpoints, actionability rows include non-default
knobs, oracle-depth rows preserve 24/24 lower flat-work and >=20/24
fixed-session recall/group support, source artifacts tracked clean, no dataset
sync, no profiler rerun, and profiler_abstractions=`operation` plus
`operation stack`.
R294 closes an
engineering reproducibility gap for local agent sessions: they can now leave
native Codex/Claude logs as a portable `agent-session` trace before becoming
operation JSONL, and R303 scripts that exchange/conversion/equality check as a
tracked reproducer. R306 adds a standard Chrome Trace Event JSON bridge for the
same fixture and shows that Chrome-imported operations preserve the same folded
operation-stack output. R353 extends that standard-trace bridge to an existing
real labeled operation-file prefix without creating or syncing data: 512
operations export to 512 Chrome events and import back with byte-identical
512-sample / 11-stack folded output. R295 turns those scattered results into a mechanical claim
gate: it reads tracked R282-R294 JSON artifacts and emits supported/partial
verdicts plus paper-ready wording under
`docs/visexp/out/paper-claim-synthesis-r295/`. R296 then turns the same
evidence into a reviewer navigation packet under
`docs/visexp/out/reviewer-evidence-packet-r296/`: 11 non-flamegraph or
evidence-navigation entries, 4 reviewer questions, derived ratios for mapping,
recursive folding, human-group reduction, diagnostic negative controls, and
explicit expansion gates. R307 refreshes the claim gate after R300-R306, with
R303 explicitly included for scripted agent-session exchange evidence: C1 and
C2 are mechanism-ready under scoped wording, C3 remains partial for
deterministic/supervised field derivation, and C4 is supported only as an
automated inspectability proxy. R308 then turns the R305 visible packets and
hidden answer key into first-evidence analyst-outcome proxies: operation-stack
packets contain positives in all 6 tasks and high-lift groups in 5 tasks, while
still preserving fixed-session as a cheaper first-positive baseline on some
tasks. R309 then converts R298/R300/R302/R305/R308 into problem-value cards:
across 4 datasets and 34,539 task-operations, operation stacks are more
selective than flat packets on all 6 tasks, expose high-lift evidence in 5
tasks, and improve selected recall over fixed-session packets in 5 tasks, while
fixed-session remains lower-work in 4 tasks. R310 reads the tracked R307/R309
artifacts and emits a paper evidence matrix under
`docs/visexp/out/paper-evidence-matrix-r310/`: C1, C2, and C4 are scoped
paper-ready claims, C3 remains partial, and the global must-not-claim list
excludes human accuracy/time improvement, automatic anomaly detection,
universal fixed-session dominance, unsupervised intent discovery, and complete
trace-ecosystem compatibility. R311 reads R302/R305/R308/R309/R310 and adds a
reviewer-stress audit under
`docs/visexp/out/paper-robustness-audit-r311/`: operation stacks pass the flat
selectivity attack (6/6 more selective, 6/6 positive groups, 5/6 high-lift
tasks), but the fixed-session dominance claim is explicitly narrowed because
operation stacks are lower-work than fixed-session on only 2/6 tasks. R313
then converts the R302/R305 candidate views into a Pareto frontier over work,
recall, lift, and inspected groups. Operation stacks are nondominated on all 6
tasks and have the best lift or 30%-work recall on 4 tasks, but flat and
fixed-session views also remain frontier points on all 6 tasks, so the paper
should present a configurable analysis surface rather than one best hierarchy.
R320 is the main profiling-paper accuracy result. It treats profile groups as
ranked localization outputs and scores 144 view/ranker policies with hidden
labels over the same 4 datasets, 6 tasks, 34,539 operations, and 3,699 positive
operations. Query-aware operation-stack top-5 groups inspect median 9.37% of
operations, compared with 100% for flat summaries. Against fixed-session
query-aware drilldown, operation stacks improve top-5 recall on 5/6 tasks and
reduce median group fragmentation from 285.0 to 157.5 groups. Query-aware
ranking improves average precision over width-only operation-stack ranking on
6/6 tasks, but top-5 F1 and work still expose prevalence, side-effect, and
boundary-depth counterexamples. The paper should use R320 to claim profiler
localization/ranking faithful to dataset-provided hidden labels in this
benchmark, plus actionable optimization insight, while
leaving human/agent analyst accuracy and time-to-answer as an optional later
user-utility study.
R330-R335 harden the same C4 claim rather than broadening it. R330 adds a
task-paired bootstrap over the six task families and keeps the strongest
flat/fixed/width comparisons directional while preserving counterpoints. R331
adds a prevalence and group-size negative control and shows AP and budgeted
recall survive label permutation better than top-five precision or
first-positive work. R332 shows no single visible hierarchy or source-task
selector is best for every task/objective. R333 turns R320 into
inspection-efficiency curves and shows operation-stack query-aware has the
strongest median recall at 30% inspected work among the core non-oracle
policies. R334 then separates fragmentation from operation work: compared with
fixed-session query-aware, operation-stack query-aware uses fewer ranked groups
to reach 50% positives on 5/6 tasks and fewer groups at the same 30% work
budget on 5/6 tasks, but it has lower work-to-first-positive on only 2/6
tasks. The supported wording is therefore fixed-session fragmentation
reduction plus inspection-budget recall, not universal work dominance.
R335 then merges R320/R325/R326/R329/R332/R334 into task-level actionability
cards. All 6/6 cards have a concrete optimization action and query-aware AP
gain over width; mapping helps 2/6 and hurts 4/6, critical features appear on
4/6, misleading features on 2/6, coarse depth reduces groups on 6/6 but is
AP-preferred on only 2/6, and fixed-session remains a first-positive work
counterpoint on 4/6. This turns actionability into a mechanism ledger, not a
claim that one policy is universally best.
R336 converts that ledger into a multi-objective selection audit over the 15
visible R320 policies. It shows operation-stack query-aware is Pareto-frontier
on 6/6 tasks, best visible AP on 3/6 tasks, best 30% budget recall on 3/6 tasks,
lower top-5 work than flat on 6/6 tasks, higher top-5 recall than fixed-session
on 5/6 tasks, and lower groups-to-50% positives than fixed-session on 5/6 tasks.
It also keeps the hard counterpoints: every task has more than one best policy
across objectives, flat is the pure group-count minimum, and operation-stack
has lower work-to-first-positive than fixed-session on only 2/6 tasks. This is
actionable policy selection evidence, not an automatic universal selector.
R337 turns the inspection curves into fixed recall-target costs. At a 25%
positive-recall target, operation-stack query-aware reaches 6/6 tasks with
median inspected work 0.2000 and median 16.0 groups; flat reaches the same
target only by inspecting median work 1.0000, and fixed-session query-aware
also reaches 6/6 but needs median 50.0 groups. At a 10% early-recall target,
operation stacks and fixed-session both reach 6/6 tasks with about 10% work,
but operation stacks use median 12.5 groups versus 37.5; at 50% recall,
operation-stack query-aware reaches 5/6 tasks and operation-stack width,
dataset-native, and raw-action policies become best-work counterpoints. This
supports target-specific inspection-cost guidance, not universal dominance.
R339 adds the missing sequence-scope adequacy view over the same real labeled
tasks and policies. It treats a trajectory/session as the unit a profiler user
may need to inspect after a hot group is ranked, and scores whether selected
groups hit sessions that actually contain positive operations. At top-5 groups,
operation-stack query-aware inspects median 0.0937 operation work and covers
median 0.2629 positive-session recall, while flat needs 1.0000 operation work
and fixed-session covers only 0.0160 positive-session recall. At a 30%
operation budget, operation-stack query-aware reaches median 0.3900 positive
operation recall and 0.4669 positive-session recall while touching median
0.3467 sessions. Fixed-session reaches 0.3230 positive-session recall at
0.3227 session work; raw-action reaches higher positive-session recall
(0.5147) but touches far more sessions (0.9103). This supports a
sequence-scope triage tradeoff, not a claim that one stack view dominates all
sequence objectives.
R340 adds a target-held-out policy-transfer audit over the already-scored R320
and R339 artifacts. It selects only visible policies from non-target tasks or
non-target datasets, then scores the selected policy on the held-out target. It
produces 96 transfer decisions across 6 tasks, 8 objectives, and 2 protocols:
31/96 exact best, 62/96 within tolerance of the held-out best visible policy,
and strict wins over width, fixed-session, and flat baselines on 72/96, 69/96,
and 41/96 decisions. The main conclusion is not that one operation-stack policy
wins everywhere, since operation-stack views are selected in only 16/96
decisions. The conclusion is that policy, stack depth, and view choice can be
selected and audited as profiler knobs while preserving target-label separation.
R338 also checks the R340 isolation invariants: selected and best policies are
visible and non-oracle on 96/96 decisions, and leave-task/leave-dataset training
scopes exclude the target task or target dataset on 96/96 decisions.
R341 adds a mechanism/error-attribution audit over the existing R320/R335/R336/R340
artifacts. It classifies 36/36 objective-task recommendations as actionable,
shows that 27/36 best visible policies are not the default operation-stack view,
and assigns 34/96 out-of-tolerance transfer decisions to view/ranker or
baseline-counterpoint explanations. Among those transfer misses, 32/34 change
view relative to the held-out best, 26/34 change ranker, and 29/34 are
high-regret misses, which makes the optimization target explicit rather than
opaque.
R349 connects the R340 held-out transfer protocol to the R348 action oracle.
Across 60 aligned R340/R348 decisions, held-out selection is within target
metric tolerance on 35/60 and beats default operation-stack query-aware on
30/60. Exact action-class transfer is only 7/60, and only 2/42 when the target
best action is non-default, so R349 supports protocol-sensitivity and
actionability tradeoff claims while explicitly rejecting an automatic action
selector claim.
R350 combines the R346 casebook, R347 baseline contrast, R348 action
counterfactuals, and R349 held-out guardrail into a bounded evidence-packet
audit. Top-five operation-stack packets contain positives on 6/6 tasks, top-one
packets contain positives on 5/6, and 4/6 tasks meet the strict 30% operation
work and first-positive <=10% work budgets. Median top-five work/recall/lift is
0.0937/0.188/1.6508. The same packets preserve 6/6 baseline counterpoints,
27/36 non-default objective rows, 36/36 visible non-oracle best rows, and the
R349 35/60 within-tolerance plus 7/60 exact-action guardrail. The two strict
budget exceptions are high-prevalence looping and human-boundary group-start,
so R350 supports bounded actionable evidence packets rather than universal
budget dominance or automatic action selection.
R338 mechanically audits the paper-facing R327/R328 reproducibility numbers and R320-R350 evidence after the
profiling-paper claim shift. It reads tracked-clean source artifacts, hashes the
current Chinese and English drafts, and checks result invariants, source-policy
provenance, must-not-claim guardrails, and the two-abstraction boundary. The
audit passes its result invariants, source-policy checks, and guardrail checks.
It is not new empirical evidence; its value is preventing the paper from drifting
from the supported profiler-localization and actionability claim into
unsupported human-utility, automatic-boundary, ecosystem-compatibility, or
universal-selector wording.
R312 audits the current Chinese draft against R310/R311/R320 and reports
`scoped_claim_ready`: number alignment, two-abstraction boundary,
must-not-claim guardrails, paper-structure checks, and the R320
hidden-label profiler-accuracy gate all align. R297 is the first non-rule boundary-backend probe:
it trains a supervised adjacent-boundary model on OSWorld-Human train sessions,
evaluates held-out human-group boundaries, writes predicted boundary fields
back into operation JSONL, and folds those fields through the existing Rust
`agentpprof --profile-spec` path. R298 turns R295-R297 into a paper-value and
novelty synthesis under `docs/visexp/out/paper-value-novelty-r298/`: 6
real-problem evidence blocks, 4 novelty claims, an explicit maturity label
(`level-3 conference-paper evidence, approaching level 4 for mechanism
claims`), and the remaining level-4 gaps. R299 addresses one of those gaps by
running the adjacent-boundary backend pattern on existing non-OSWorld labels:
AgentNet step correctness/redundancy and AgentRewardBench looping. The result
is deliberately mixed and therefore useful for claim scope: AgentNet quality
boundaries are learnable but low-precision, AgentRewardBench looping is better
handled by the simpler `repeat_signal_change` field, SATraj safety has no
within-session adjacent boundaries in the sample, and ScaleCUA history state is
not a semantic boundary oracle. R300 adds an automated real-problem proxy over
existing labels: 6 failure/safety/quality/boundary tasks and 34,539 operations
compare flat, fixed-session, semantic operation-stack, and label-drilldown
views. Semantic operation stacks beat flat summaries on median positive lift
and inspection fraction, and beat fixed-session views on cross-session
aggregation and group count, while fixed sessions remain stronger on some
instance-local inspection tasks. R301 adds the more conservative label-hidden
variant: visible packets show only width-ranked operation-stack groups and keep
oracle labels in a separate answer key. It supports the claim that operation
stacks reduce fixed-session fragmentation and expose many positives under
default browsing, but it also narrows the story because width ranking alone is
not a detector and sometimes spends more operation budget than fixed-session
drilldown. R302 adds a label-hidden ranking-policy probe over the same tasks.
It shows that operation stacks are useful beyond flamegraph width: query-aware
ranking over visible fields can trade recall, lift, and inspection work without
using oracle labels or adding a new profiler abstraction. It also keeps the
claim narrow because the ranking policies are heuristics, not learned online
detectors. R292
ScaleCUA is a useful supplemental stream sample for GUI history-depth fields,
but not a main boundary oracle because the sampled Ubuntu navigation subset is
mostly click/terminate.

The paper must not claim fully unsupervised boundary discovery, complete
intent recovery, or improved developer task performance. Those remain future
gates.

## Claim Verdict

Historical status: the verdict table below is superseded by the recovery claim
ledger and must be reissued from frozen primary results after RQ1-D1 through
RQ4-D3 are applied as relevant.

| Claim | Verdict | Evidence | Current supported wording | Maximal plausible wording | Expansion experiments |
|---|---|---|---|---|---|
| C1 | supported | R295 `heterogeneous_coverage`, `recursive_depth`, and `reproducibility_and_exchange`; source artifacts include R286, R291/R292 combined quality, R293 profile-spec replay, and R294 trace exchange. R303 adds a scripted trace-exchange reproduction after the R295 claim gate. R342 verifies that 12/12 real-trace profile-spec variants compose operation files, predicates, operation-level ranking, rule-score mode, and explicit stack depth without prompt/session frames. R353 verifies that an existing real labeled operation-file prefix can export through a Chrome Trace Event container and import back with byte-identical folded operation-stack output. | The operation-stack profiler can represent heterogeneous public agent trajectories and local agent sessions as operations, then profile them through user-selected operation stacks without hard-coding prompt/session boundaries. | Full-benchmark and image/video-heavy trajectory profiling across the broader GUI/web/desktop benchmark ecosystem. | Add larger streaming runs for AgentNet Windows/macOS/full Ubuntu, ScaleCUA multi-platform shards, VisualWebArena/UI-Vision, and image-aware redaction policies. |
| C2 | supported with scoped limits | R295 `recursive_depth`, `human_boundaries`, and `quality_and_failure_diagnostics`; strongest oracles are OSWorld-Human grouped actions, AgentNet step-quality labels, AgentRewardBench looping labels, SATraj safety/attack labels, and R355 oracle-depth scoring over session, operation/step, positive-run, and task-specific units. | Recursive operation stacks recover useful task, phase, action, human-group, safety, and quality-label views, expose when a coarse field is not a valid proxy for a finer oracle, and can be scored at the dataset-provided oracle depth. | Robust intent/subtask recovery across desktop, web, mobile, and tool-agent-user traces. | Add non-rule boundary backend, stronger instruction-step or solution-path scorers, leave-family-out validation, and a manual adjudication packet for ambiguous groups before broad latent-boundary claims. |
| C3 | supported with scoped limits | R295 `mapping_generalization`; R282 held-out mapping improves compression and R285 removes negative leave-dataset-out stack-reduction regressions after operation-family precedence; R297 shows a supervised adjacent-boundary backend can derive stackable `learned_group_pattern` fields on held-out OSWorld-Human sessions; R299 replicates the backend pattern on AgentNet quality-state boundaries and AgentRewardBench looping with calibration/error analysis; R366 consolidates the mechanism evidence and counterpoints across deterministic mapping, profile-spec composition, rank-feature ablation, boundary-family suitability, and R358 boundary-derived profile patches. | Label-derived deterministic and supervised field derivations improve semantic aggregation or localization when the target family has suitable visible operation fields and an oracle-backed objective: held-out mapping improves compression 14.049->19.091, leave-dataset-out mapping reduces stacks on 6/9 datasets with 0 negative reductions, and boundary backends beat the best simple baseline on 4/5 tested rows. These are reproducible field derivations folded through operation stacks, not unsupervised boundary discovery. | Rules, learned mappings, or model-backed boundary detectors can infer useful operation-stack fields from unseen trajectories when the target family has a suitable adjacent-boundary oracle, calibrated features, and a simple-baseline check. | Add calibrated boundary models, track tau-bench operation JSONL for tool-dialogue boundary probes, and compare against an LLM or sequence-model backend after suitability checks; keep these as expansion probes for broader automatic-boundary claims. |
| C4 | supported as hidden-label profiler benchmark | Empirical profiler evidence: R300 `query-utility-report.json`, four Rust profile-spec folded outputs, R301 `analyst-task-report.json`, visible task packets, hidden answer key, R302 `ranking-report.json`, R304 `visible-case-packet.json` plus `answer-key.json`, R305 cross-view case-packet baselines, R308 analyst first-evidence outcomes, R309 problem-value cards, R311 reviewer-stress audit, R313 view-frontier report, R320 `profile-accuracy-report.json`, R330 uncertainty report, R331 negative-control report, R332 view-depth report, R333 inspection-frontier report, R334 fragmentation-tradeoff report, R335 actionability-synthesis report, R336 actionability-selection report, R337 inspection-target report, R339 sequence-adequacy report, R340 policy-transfer report, R341 mechanism-attribution report, R342 profile-spec composition report, R344 metric-consistency report, R345 diagnostic-lens portfolio report, R346 diagnostic casebook report, R347 case-level baseline contrast report, R348 action-counterfactual report, R349 action-transfer report, R350 evidence-packet report, R354 profile-patch report, R355 oracle-depth adequacy report, and operation-stack analysis over 34,539 operations. Scope-control and claim-scope gates, not empirical profiler evidence: R338 claim-integrity report, R352 evaluation-rubric report, and R356 claim-integrity refresh. | On six oracle-backed analysis tasks, operation-stack profiling localizes and ranks labeled failure/safety/quality/boundary positives relative to dataset-provided hidden labels, with less inspection work than flat summaries and less fragmentation than fixed-session drilldown. Query-aware operation-stack top-5 groups inspect median 9.37% of operations versus 100% for flat summaries; they improve top-5 recall over fixed-session query-aware drilldown on 5/6 tasks and reduce median groups from 285.0 to 157.5. R333 shows operation-stack query-aware reaches median recall 0.3900 at 30% inspected work, versus 0.0000 for flat, 0.3559 for fixed-session, 0.3377 for dataset-native, and 0.3325 for raw-action. R334 shows it reaches 50% positives with fewer ranked groups than fixed-session on 5/6 tasks and inspects fewer groups at the same 30% work budget on 5/6 tasks. R335 shows all 6/6 task cards have concrete optimization actions, while mapping, feature, depth, transfer, and fixed-session drilldown choices remain task-specific. R336 scores 15 visible policies across 6 diagnostic objectives: operation-stack query-aware is Pareto-frontier on 6/6 tasks, best visible AP on 3/6, best 30% budget recall on 3/6, lower top-5 work than flat on 6/6, higher top-5 recall than fixed-session on 5/6, and lower groups-to-50% positives than fixed-session on 5/6. R337 shows that at a 25% recall target operation-stack query-aware reaches 6/6 tasks with median work 0.2000 versus flat 1.0000 and median 16.0 groups versus fixed-session 50.0. R339 adds sequence-scope evidence: at 30% operation work, operation-stack query-aware covers median 0.4669 positive-session recall versus 0.3230 for fixed-session while touching median 0.3467 sessions; raw-action reaches 0.5147 positive-session recall but touches 0.9103 sessions. R355 adds oracle-depth evidence over the same existing labeled traces: across 24 task-depth rows, operation-stack query-aware uses lower top-5 oracle-unit work than flat on 24/24 rows, has higher budget-30 positive-unit recall than fixed-session on 20/24 and higher unit F1 on 18/24, reaches 50% positive units with fewer groups than fixed-session on 22/24, and has fewer positive units per group than raw-action on 24/24, while depth-gap versus fixed-session remains an explicit counterpoint. R340 adds non-target policy-transfer evidence: across 96 leave-task and leave-dataset decisions, selected visible policies are within tolerance of the held-out best on 62 decisions and strictly beat width, fixed-session, and flat baselines on 72, 69, and 41 decisions. R341 adds mechanism/error attribution: 36/36 objective rows have optimization actions, 27/36 best visible policies are non-default, and 34/96 transfer misses are classified, with 32/34 involving view changes, 26/34 involving ranker changes, and 29/34 high-regret misses. R344 confirms the metric surface is a tradeoff rather than cherry-picked AP: 30/50 baseline-metric comparisons support operation-stack query-aware, 16 are explicit counterpoints, and 4 are mixed/weak; AP, budget recall/F1, inspection work, and fragmentation carry the main claim, while nDCG and coarse top-k recall remain secondary/counterpoint metrics. R345 turns those actionability results into a diagnostic-lens portfolio: 6 diagnostic lenses cover 36 objective rows, operation-stack-family views win 11/36 objectives, non-operation-stack counterpoints win 25/36, and all 6/6 tasks need at least three best views. R346 turns the top-ranked operation-stack groups into label-scored case evidence: 30 case groups, 6/6 top-5 positive tasks, 5/6 top-1 positive tasks, median top-5 lift 1.6508, and 6/6 actionable case cards with counterpoints. R347 contrasts 5 visible case views: operation-stack wins vs flat top-5 work on 6/6, vs fixed-session top-5 recall on 5/6, and vs fixed-session group count on 4/6, while fixed-session first-positive and flat full-work recall remain counterpoints. R348 adds objective-level action counterfactuals: 36/36 best rows are visible non-oracle, 27/36 require non-default actions, 25/36 require view changes, 2/36 require operation-stack tuning, and median gain over default is 0.1447. R349 adds target-held-out action-transfer evidence: across 60 aligned decisions, held-out policy selection is within tolerance on 35/60 and beats default on 30/60, but exact action-class transfer is only 7/60 and only 2/42 on non-default target actions. R350 adds evidence-packet actionability: top-five operation-stack packets contain positives on 6/6 tasks, top-one on 5/6, 4/6 meet the strict 30% work budget, median top-five work/recall/lift is 0.0937/0.188/1.6508, and the packets preserve 27/36 non-default objective rows plus the 35/60 within-tolerance transfer guardrail. R354 materializes the actionability loop as executable before/after profile specs: profile-guided patches improve AP, top-5 lift, and first-positive work on 5/6 tasks over the same visible operation input, while OSWorld-Human rejects the visible rank-feature patch and points to boundary-derived fields. Scope-control checks R338/R352/R356 check number alignment, source provenance, rubric coverage, and guardrails; they are not empirical profiler evidence. Flat, fixed-session, dataset-native, raw-action, and oracle policies remain explicit counterpoints. | Current evidence supports profiler fidelity with respect to dataset-provided hidden labels, label-scored localization/ranking, inspection-budget recall, fixed-session fragmentation reduction, fixed-recall inspection-cost guidance, sequence-scope and oracle-depth triage, metric-surface tradeoff accounting, case-level baseline contrast, objective-level action counterfactuals, executable profile-spec patch actionability, target-held-out actionability/protocol-sensitivity insight, and bounded evidence-packet actionability on real labeled traces. It does not support developer productivity, time-to-answer, automatic anomaly detection, complete intent-boundary discovery, real OpenTelemetry/OpenInference/Phoenix span-tree superiority, automatic universal policy/action selection, or single-view/work dominance. | Expand to more oracle-rich tool/API/mobile GUI families only if broader generality is required; add stronger true subtask or solution-path oracles before broad latent-boundary claims; import a real span-tree trace before ecosystem-specific claims; run a controlled human/agent analyst study only if the paper wants to claim analyst productivity or time-to-answer. |

R342 addendum: the profile-spec composition audit reuses the tracked R324/R300
real labeled outputs and does not add a new dataset or third profiler
abstraction. It verifies 12/12 variants compose operation files, `where_rules`,
`rank_op_rules`, `rank_mode=rule-score`, and explicit stack depth while staying
prompt/session-free. It also shows visible operation-feature ranking improves
AP over width on 9/12 variants and first-positive work on 10/12 variants, while
coarse depth reduces groups on 6/6 tasks with median group reduction 0.8267 and
depth choice changes the preferred objective on 3/6 tasks.

## Dataset Matrix

| Dataset | Oracle fields | Access path | Current repository support | Evaluation use |
|---|---|---|---|---|
| WebLINX chat | demo id, turn, action, action history, utterances | HF Dataset Viewer: `McGill-NLP/WebLINX`, config `chat` | `script/agent_trace_datasets.py sample weblinx-chat` emits raw rows and operation JSONL. | First external smoke; action phase and demo/session folding. |
| WebShop expert | task name, reward, conversation actions | HF Dataset Viewer: `lclan/webshop_expert_trajectories` | `script/agent_trace_datasets.py sample webshop-expert` emits one operation per assistant action. | Long expert web trajectories; current top candidate. |
| API-Bank | gold API request, API domain | HF first-rows: `liminghao1630/API-Bank` | `script/agent_trace_datasets.py sample api-bank` emits one operation per gold API call; rows endpoint currently 500s after first rows. | Compact tool-call baseline. |
| AgentTrek | verified web GUI action tags | HF Dataset Viewer: `xlangai/AgentTrek` | `script/agent_trace_datasets.py sample agenttrek` emits one operation per action tag. | Large web GUI source; current top candidate if synthetic verified data is acceptable. |
| SWE-agent trajectories | issue instance, command trajectory, success target | HF Dataset Viewer: `nebius/SWE-agent-trajectories` | `script/agent_trace_datasets.py sample swe-agent-trajectories` emits one operation per command action. | Closest external software-agent source; current top candidate. |
| Mind2Web | task description, action sequence, website/domain, snapshots/traces | HF repo `osunlp/Mind2Web`; official raw dump | `script/agent_trace_datasets.py sample mind2web` downloads an HF repo JSON shard and emits operation JSONL; R274 sampled 9 tasks / 49 operations. | Cross-domain web operation-stack oracle. |
| AndroidControl | high-level goal, step instructions, screenshots, accessibility trees, JSON actions | Official Google Research TFRecord; HF mirror `smolagents/android-control` | `script/agent_trace_datasets.py sample android-control` emits one operation per UI action and strips screenshot payloads from saved raw rows; R278 sampled 2 episodes / 9 operations. | Step-instruction boundary oracle for recursive depth. |
| GUI-Odyssey | episode id, category, app combo, instruction, annotated step actions | HF Dataset Viewer: `OpenGVLab/GUI-Odyssey`, config `default`, split `all` | `script/agent_trace_datasets.py sample gui-odyssey` emits one operation per annotated GUI step; R279 sampled 500 episodes / 7,868 operations. | Best current large-scale mobile/cross-app trajectory source. |
| Android in the Wild | instruction, screen/action episodes | Official google-research release | Manifested; converter pending. | Large-scale robustness once mobile converter exists. |
| ToolBench | instruction, solution path, toolenv, API calls, reasoning traces | Official OpenBMB release plus HF mirror `tuandunghcmut/toolbench-v1` | `script/agent_trace_datasets.py sample toolbench` emits one operation per assistant tool action; R279 sampled 300 rows / 866 operations. | Tool/planner/API operation-stack oracle. |
| tau-bench trajectories | multi-turn user/assistant/tool messages, task domain, success/failure outcome, gold task actions | HF repo files: `AgentSuite/tau-bench-trajectories`, one JSONL per model | `script/agent_trace_datasets.py sample tau-bench-trajectories --repo-file gpt-4o-mini.jsonl` emits user prompt, assistant response, tool-call, and tool-observation operations; R287 sampled 50 episodes / 1,560 operations. | Best current tool-agent-user dialogue source; useful for dialogue/tool/observation phase stacks and outcome/failure analysis. |
| AgentRewardBench | expert success, side-effect, looping, optimality labels plus BrowserGym cleaned steps | HF Dataset Viewer annotations plus HF repo cleaned JSON: `McGill-NLP/agent-reward-bench` | `script/agent_trace_datasets.py sample agent-reward-bench` reads annotations, downloads matching `cleaned/<benchmark>/<model>/<experiment>/<task_id>.json`, and emits one browser-action operation per step; R288 sampled 38 trajectories / 729 operations across assistantbench, visualwebarena, webarena, and workarena. | Best current expert trajectory-quality oracle; useful for failure, side-effect, repetitive-action, and non-flamegraph diagnostics. |
| SATraj-OS safety | desktop computer-use actions, success, safety, reward, attack type | HF Dataset Viewer: `AI45Research/SATraj-OS`, config `safety` | `script/agent_trace_datasets.py sample satraj-os-safety` extracts assistant `computer_use` tool calls, redacts raw messages/task text from saved rows, and emits one desktop-action operation per step; R289 sampled 250 trajectories / 4,285 operations. | Best current desktop computer-use source in this harness; useful for OS action-family precedence, safety/attack diagnostics, and non-web/non-mobile generalization. |
| OSWorld-Human | human reference single-action and grouped-action desktop trajectories | GitHub JSON files: `WukLab/osworld-human` | `script/agent_trace_datasets.py sample osworld-human` fetches repository JSON files across apps, drops raw instruction/config/evaluator fields by default, and emits one desktop operation per human single action with redacted target fields. Exact `single-action`/`grouped-action` alignment is required before writing `human_group`, `group_pattern`, and `group_position`; R290 sampled all 369 tasks / 6,010 operations and found exact grouped-action oracle fields for 320 tasks / 4,011 operations. | Best current human desktop grouped-boundary oracle; directly tests recursive folding from single actions into task-dependent operation-stack depths while flagging non-exact grouped annotations instead of scoring them as gold. |
| AgentNet | human desktop PyAutoGUI actions, task outcome, alignment/efficiency/difficulty, step correctness, step redundancy | HF repo JSONL stream: `xlangai/AgentNet`, file `agentnet_ubuntu_5k.jsonl` | `script/agent_trace_datasets.py sample agentnet` streams only the requested JSONL prefix/range from Hugging Face, drops raw task text and raw trajectories from saved rows, and emits one `tool=computer` operation per PyAutoGUI step. R291 sampled 1,000 Ubuntu tasks / 16,741 operations without syncing the full source JSONL. | Best current large human desktop step-quality oracle; tests whether task outcome, step correctness, redundancy, and repetition diagnostics remain ordinary operation fields rather than new profiler objects. |
| ScaleCUA Ubuntu navigation | GUI navigation actions, previous-operation context, image path, width/height | HF repo JSONL stream: `OpenGVLab/ScaleCUA-Data`, file `annotations/data_20250428_ubuntu_navigation_20250506.jsonl` | `script/agent_trace_datasets.py sample scalecua-navigation` streams the requested annotation JSONL prefix from Hugging Face, drops raw `conversations`, does not download images or source archives, and emits one `tool=computer` operation per gold GUI action. R292 sampled 5,000 rows / 5,000 operations across 131 sessions. | Supplemental GUI history-depth source; useful for `history_state`/`history_depth` fields, but not a core action-boundary oracle because this subset is mostly click/terminate. |
| TRAIL | human-annotated reasoning/planning/execution errors | HF auto-gated dataset plus official benchmark repo | Manifested; gated access pending. | Best future failure-boundary oracle. |

## Run Tracker

| Run ID | Claim | Purpose | Command/config | Commit | Machine | Seed/reps | Result path | Status |
|---|---|---|---|---|---|---|---|---|
| R272 | C1, C2 | WebLINX external operation-file smoke | See command below | worktree based on `1d0134b` before this commit | local | 25 rows, offset 0 | `docs/visexp/out/external-agent-trace-weblinx-r272/` | done |
| R273 | C1, C2 | Cross-dataset operation-stack smoke across 5 labeled sources | WebLINX 500, WebShop 100, API-Bank 48, AgentTrek 200, SWE-agent 20; `--view operations` | worktree after `9673a30` | local | 3,748 operations | `docs/visexp/out/external-agent-trace-cross-dataset-r273/` | done |
| R274 | C1, C2 | Six-dataset operation mapping smoke | WebLINX 500, WebShop 100, API-Bank 48, AgentTrek 200, SWE-agent 20, Mind2Web 9; `--view operations` + `--op-map` task/phase mapping | worktree after `8125c26` | local | 3,797 operations | `docs/visexp/out/external-agent-trace-mapped-r274/` | done |
| R275 | C1, C2 | AndroidControl step-boundary oracle | TFRecord/parquet converter to operation JSONL | todo | local | at least 100 episodes | `docs/visexp/out/external-agent-trace-androidcontrol-r275/` | todo |
| R276 | C1, C2 | ToolBench tool/API stack oracle | official data converter for instruction/answer/toolenv | todo | local | at least G1/G2/G3 samples | `docs/visexp/out/external-agent-trace-toolbench-r276/` | todo |
| R277 | C2 | Stack abstraction ablation | flat stack vs fixed demo/session stack vs mapped operation stack | worktree after `8125c26` | local | same 3,797 operations as R274 | `docs/visexp/out/operation-stack-ablation-r277/` | done |
| R278 | C1, C2 | Expanded 8-dataset mapped-stack smoke | R274 inputs + ToolBench 40 + AndroidControl 2; `--view operations` + `--op-map` task/phase mapping | worktree after `04169d7` | local | 3,932 operations | `docs/visexp/out/external-agent-trace-expanded-r278/` | done |
| R279 | C1, C2 | Scaled 9-dataset mapped-stack run | R278 inputs + GUI-Odyssey 500, ToolBench 300, Mind2Web train_0 100; `--view operations` + `--op-map` task/phase mapping | worktree after `2a2528d` | local | 13,265 operations | `docs/visexp/out/external-agent-trace-scaled-r279/` | done |
| R280 | C2 | Operation-stack quality scorer | R279 operation files; coverage, V-measure, and sequence boundary F1 via `script/operation_stack_quality.py` | worktree after `2a2528d` | local | same 13,265 operations as R279 | `docs/visexp/out/operation-stack-quality-r280/` | done |
| R281 | C1, C2, C3 | Learned-from-labels operation mapping baseline | R279 operation files; `script/operation_map_infer.py` generates `--op-map-file`, then `agentpprof --operation-file --op-map-file` and `script/operation_stack_quality.py --op-map-file` rerun the same stack | worktree after `74ff667` | local | same 13,265 operations as R279 | `docs/visexp/out/operation-map-infer-r281/` | done |
| R282 | C1, C2, C3 | Held-out generated mapping validation | `script/operation_split.py` splits R279 operations by `dataset,session` with dataset stratification; `script/operation_map_infer.py` trains on 9,275 train operations; `agentpprof` and quality scorer evaluate 3,990 held-out operations with learned `--op-map-file` and no-map baseline | worktree after `027c4f2` | local | 1 deterministic 70/30 group split, seed `r282` | `docs/visexp/out/operation-map-heldout-r282/` | done |
| R283 | C2, C3 | Leave-dataset-out generated mapping, raw-action stack | `script/operation_leaveout_eval.py`; each of 9 datasets held out in turn; train mappings on the other 8; evaluate stack `project,dataset,task,phase,op,tool,action,status` with mapped vs no-map baseline | worktree after `9f2c6c0` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-r283/` | done |
| R284 | C2, C3 | Leave-dataset-out generated mapping, semantic stack | Same as R283 but stack is `project,dataset,task,phase,op,tool,status`, removing raw `action` as a leaf to test semantic aggregation view | worktree after `9f2c6c0` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-semantic-r284/` | done |
| R285 | C2, C3 | Leave-dataset-out semantic stack with API/tool phase precedence | Same as R284 after updating learned rule inference to classify API/tool traces before generic action-verb phase rules, including a generic `op=tool.*domain=` API fallback | worktree after `63f1a06` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-api-r285/` | done |
| R286 | C1, C2 | Recursive stack-depth sweep over the same operations | `script/operation_stack_depth_eval.py`; same 13,265 R279 operations and R286 inferred op-map; compare dataset/task/phase/op/tool/semantic/action/fixed-session stack shapes through Rust `agentpprof --operation-file --stack` | worktree after `0a645c7` | local | 8 stack depths over identical operations | `docs/visexp/out/operation-stack-depth-r286/` | done |
| R287 | C1, C2 | tau-bench tool-agent-user trajectory converter and smoke | `script/agent_trace_datasets.py sample tau-bench-trajectories --limit 50 --repo-file gpt-4o-mini.jsonl`; Rust `agentpprof --operation-file` over tau-bench alone and combined with the R279 9-dataset set | worktree after `5a3abaa` | local | 50 episodes, 1,560 tau-bench operations; 10-dataset combined smoke has 14,825 operations | `docs/visexp/out/external-agent-trace-taubench-r287/` | done |
| R288 | C1, C2 | AgentRewardBench expert trajectory-quality labels and 11-dataset smoke | `script/agent_trace_datasets.py sample agent-reward-bench` at offsets 0, 40, 700, and 800; Rust `agentpprof --operation-file` over AgentRewardBench alone and combined with the R287 10-dataset set; stack fields include `status`, `side_effect`, `looping`, `optimality`, and action-derived `repeat_signal` | worktree after `3dbea0f` | local | 38 trajectories, 729 AgentRewardBench operations; 11-dataset combined smoke has 15,554 operations | `docs/visexp/out/external-agent-trace-agentreward-r288/` | done |
| R289 | C1, C2 | SATraj-OS desktop computer-use safety converter and 12-dataset smoke | `script/agent_trace_datasets.py sample satraj-os-safety` at offsets 0, 500, 3000, 4000, and 5900; Rust `agentpprof --operation-file` over SATraj alone and combined with the R288 11-dataset set; stack fields include `attack_type`, `safety`, `status`, and `repeat_signal` | worktree after `fc71300` | local | 250 trajectories, 4,285 SATraj operations; 12-dataset combined smoke has 19,839 operations | `docs/visexp/out/external-agent-trace-satraj-r289/` | done |
| R290 | C1, C2 | OSWorld-Human grouped-action converter and 13-dataset smoke | `script/agent_trace_datasets.py sample osworld-human --limit 369`; Rust `agentpprof --operation-file` over OSWorld-Human alone and combined with the R289 12-dataset set; stack fields include `human_group`, `group_pattern`, `group_position`, `group_alignment`, and desktop action phases | worktree after `1bde500` | local | 369 human tasks, 6,010 OSWorld-Human operations; exact grouped-action oracle covers 320 tasks, 4,011 operations, and 2,075 session-local grouped actions; 13-dataset combined smoke has 25,849 operations | `docs/visexp/out/external-agent-trace-osworldhuman-r290/` | done |
| R291 | C1, C2 | AgentNet human desktop step-quality converter and 14-dataset smoke | `script/agent_trace_datasets.py sample agentnet --limit 1000 --offset 0`; Rust `agentpprof --operation-file` over AgentNet alone and combined with the R290 13-dataset set; stack fields include `step_correct`, `step_redundant`, `alignment_score`, `efficiency_score`, `task_difficulty`, and `repeat_signal` | worktree after `12f11ca` | local | 1,000 human Ubuntu desktop tasks, 16,741 AgentNet operations; 14-dataset combined smoke has 42,590 operations | `docs/visexp/out/external-agent-trace-agentnet-r291/` | done |
| R292 | C1, C2 | ScaleCUA Ubuntu navigation supplement and 15-dataset smoke | `script/agent_trace_datasets.py sample scalecua-navigation --limit 5000 --offset 0`; Rust `agentpprof --operation-file` over ScaleCUA alone and combined with the R291 14-dataset set; stack fields include `platform`, `environment`, `trajectory_type`, `history_state`, and `history_depth` | worktree after `5b28038` | local | 5,000 ScaleCUA operations across 131 sessions; 15-dataset supplemental smoke has 47,590 operations and 1,611 unique stacks | `docs/visexp/out/external-agent-trace-scalecua-r292/` | done |
| R293 | C1, C2 | Profile-spec reproducibility over AgentNet | `agentpprof --profile-spec docs/visexp/out/profile-spec-r293/agentnet-diagnostic-spec.json`; second run overrides `--stack` and `-o` from CLI | worktree after this commit | local | Same 1,000 AgentNet tasks / 16,741 operations as R291; spec projection has 608 stacks, override projection has 83 stacks | `docs/visexp/out/profile-spec-r293/` | done |
| R294 | C1 | Agent-session trace exchange and operation JSONL bridge | `agentpprof --session-file ... --export-trace`; `agentpprof --trace-file`; `script/agent_trace_to_operations.py`; `agentpprof --operation-file` over the converted operations | worktree after this commit | local | Public Codex fixture: 1 exported trace session, 6 converted operations, trace import and operation import both produce 6 samples / 5 stacks and byte-identical folded output | `docs/visexp/out/agent-trace-exchange-r294/` | done |
| R295 | C1, C2, C3 | Mechanical paper claim synthesis and claim gate | `python3 script/paper_claim_synthesis.py > docs/visexp/out/paper-claim-synthesis-r295/run-result.json` | worktree after R294 | local | Reads tracked R282-R294 JSON/folded artifacts; emits 3 claim verdicts, 6 evidence bundles, unsupported-claim list, and source paths | `docs/visexp/out/paper-claim-synthesis-r295/` | done |
| R296 | C1, C2, C3 | Reviewer evidence packet and non-flamegraph navigation layer | `python3 script/reviewer_evidence_packet.py > docs/visexp/out/reviewer-evidence-packet-r296/run-result.json` | worktree after R295 | local | Reads 39 tracked/clean R282-R295 artifacts; emits 11 non-flamegraph/evidence-navigation entries, 4 reviewer questions, derived metrics, and 3 expansion gates | `docs/visexp/out/reviewer-evidence-packet-r296/` | done |
| R297 | C2, C3 | Supervised adjacent-boundary backend over OSWorld-Human | `python3 script/operation_boundary_backend_eval.py`; `cargo run --manifest-path agentpprof/Cargo.toml -- --profile-spec docs/visexp/out/operation-boundary-backend-r297/learned-boundary-profile-spec.json`; `script/operation_stack_analysis.py` over the learned folded output | worktree after R296 | local | Held-out split over exact-aligned OSWorld-Human: 191 train sessions / 2,655 train pairs and 96 test sessions / 1,036 test pairs; learned boundary F1 0.7735, precision 0.7400, recall 0.8102; Rust fold has 1,132 samples / 74 stacks | `docs/visexp/out/operation-boundary-backend-r297/` | done |
| R298 | C1, C2, C3 | Paper value and novelty synthesis from tracked evidence | `python3 script/paper_value_novelty_synthesis.py` | worktree after R297 | local | Reads tracked/clean R295 claim synthesis, R296 reviewer packet, R297 boundary report, and R288/R289/R291 quality reports; emits 6 real-problem evidence blocks, 4 novelty claims, paper readiness, and must-not-claim gates | `docs/visexp/out/paper-value-novelty-r298/` | done |
| R299 | C2, C3 | Boundary-family calibration over existing labeled operation JSONL | `python3 script/boundary_family_calibration_eval.py`; `cargo run --manifest-path agentpprof/Cargo.toml -- --profile-spec docs/visexp/out/boundary-family-calibration-r299/boundary-family-profile-spec.json`; `script/operation_stack_analysis.py` over the R299 folded output | worktree after R298 | local | Suitability over 7 candidates; 4 trained candidates; OSWorld human-group F1 0.6916, AgentNet step-correct F1 0.3197, AgentNet step-redundant F1 0.3361, AgentRewardBench looping F1 0.7833 but repeat-signal-change baseline F1 1.0; Rust fold has 8,961 samples / 1,548 stacks | `docs/visexp/out/boundary-family-calibration-r299/` | done |
| R300 | C4 | Operation-query utility proxy over existing labeled operations | `python3 script/operation_query_utility_eval.py`; four `agentpprof --profile-spec docs/visexp/out/operation-query-utility-r300/*-profile-spec.json` runs; `script/operation_stack_analysis.py` over `operation_stack.folded` | worktree after R299 | local | 6 tasks / 34,539 operations; Rust profiles: flat 6 stacks, fixed-session 2,012 stacks, operation-stack 944 stacks, label-drilldown 318 stacks; operation-stack vs flat median top-positive lift 5.726x and inspection fraction ratio 0.288; operation-stack vs fixed-session group-count ratio 0.554, top-group session ratio 5.5, inspection ratio 1.302 | `docs/visexp/out/operation-query-utility-r300/` | done |
| R301 | C4 | Width-ranked analyst task proxy with hidden answer key | `python3 script/operation_analyst_task_eval.py` over existing R288-R291/R300 operation JSONL | worktree after R300 | local | 6 tasks / 168 task-view-budget scores; visible packets exclude oracle labels and answer key is separate; at 30% inspected-operation budget, operation-stack median recall is 33.6% over 4.5 groups versus fixed-session 28.4% over 25.5 groups; at top-10 width-ranked groups, operation-stack median recall is 64.1% versus fixed-session 19.5%, but operation-stack inspects a larger operation fraction | `docs/visexp/out/operation-analyst-task-r301/` | done |
| R302 | C4 | Label-hidden analyst ranking policy proxy | `python3 script/operation_analyst_ranking_eval.py` over existing R288-R291/R300 operation JSONL | worktree after R301 | local | 6 tasks / 192 task-view-ranker-budget scores; rankers are width, visible-risk, query-aware, and oracle upper bound; top-10 query-aware operation-stack groups inspect 11.6% of operations with lift 1.587 versus width ranking's 67.1% and lift 1.079; at 30% operation budget, query-aware recall is 39.0% versus width 34.0%, but groups inspected rise from 4.5 to 39.5 | `docs/visexp/out/operation-analyst-ranking-r302/` | done |
| R303 | C1 | Scripted agent-session trace exchange reproducer | `python3 script/agent_trace_exchange_eval.py` exports a public Codex fixture to `agentsight.agent-session.trace.v1`, checks filesystem/tool-command portability, converts it with `script/agent_trace_to_operations.py`, then profiles both paths with the same stack | worktree after R302 | local | 1 exported trace session, 6 converted operations, `trace_filesystem_portable=true`, direct trace import and converted operation import both produce 6 samples / 5 stacks and byte-identical folded output | `docs/visexp/out/agent-trace-exchange-r303/` | done |
| R304 | C4 | Reviewer-facing operation-stack case packet | `python3 script/operation_case_study_eval.py` over the existing R300/R302 task operations | worktree after R303 | local | 6 tasks / 30 top-5 query-aware operation-stack case groups; visible packet excludes oracle fields and answer key is separate; median inspected operation fraction 9.37%, median positive recall 18.8%, and median positive lift 1.6509 | `docs/visexp/out/operation-case-study-r304/` | done |
| R305 | C4 | Cross-view case-packet baseline | `python3 script/operation_case_baseline_eval.py` over the existing R300/R302/R304 task operations | worktree after R304 | local | 6 tasks / 18 task-view case packets; visible packets exclude oracle fields and answer key is separate; flat inspects 100% ops for 100% recall, fixed-session inspects median 1.63% ops for 2.26% recall and lift 1.6615, operation-stack inspects median 9.37% ops for 18.8% recall and lift 1.6509; operation-stack vs fixed-session median recall ratio 3.63 and lift ratio 1.268, with 1.717x work | `docs/visexp/out/operation-case-baseline-r305/` | done |
| R306 | C1 | Chrome/Perfetto trace exchange bridge | `python3 script/agent_trace_chrome_exchange_eval.py` exports a public Codex fixture to `agentsight.agent-session.trace.v1`, converts it to Chrome Trace Event JSON with the Chrome bridge now surfaced through `script/agent_trace_convert.py export-standard --format chrome`, imports that trace back to operation JSONL, and profiles all paths with the same stack | worktree after R305 | local | 1 exported trace session, 6 Chrome complete events, 6 direct operations, 6 Chrome-imported operations; direct trace import, direct operation import, and Chrome-import operation import all produce 6 samples / 5 stacks with byte-identical folded output | `docs/visexp/out/agent-trace-chrome-exchange-r306/` | done |
| R307 | C1, C2, C3, C4 | Paper claim readiness synthesis after R300-R306 | `python3 script/paper_claim_readiness_synthesis.py` reads tracked R295/R298, R303, and R300-R306 artifacts, checks inputs are git-tracked and clean, and writes claim verdicts plus next-gate wording | worktree after R306 | local | 4 claim verdicts; C1 supported, C2 supported with scoped limits, C3 partial, C4 supported only as automated proxy at that time; analysis suite is 6 tasks / 34,539 operations; the then-open controlled analyst-study gate is now optional for human utility, while R320 is the main profiler-accuracy gate | `docs/visexp/out/paper-claim-readiness-r307/` | done |
| R308 | C4 | Label-hidden analyst outcome proxy | `python3 script/operation_analyst_outcome_eval.py` reads tracked R305 visible packets and answer key, checks source artifacts are tracked and clean, verifies visible packet alignment, and scores first-positive / high-lift outcome proxies | worktree after R307 | local | 6 tasks / 18 task-view packets; operation-stack packets contain a positive group in 6/6 tasks and a >=1.5x high-lift group in 5/6 tasks, versus fixed-session 5/6 and 4/6 and flat 6/6 and 0/6; operation-stack median selected work/recall/top-group lift are 9.37% / 18.8% / 1.574; fixed-session remains cheaper on first-positive work | `docs/visexp/out/operation-analyst-outcome-r308/` | done |
| R309 | C4 | Real-problem value synthesis | `python3 script/operation_problem_value_synthesis.py` reads tracked R298/R300/R302/R305/R308 artifacts, checks they are tracked and clean, and writes reviewer-facing problem cards plus claim/counterpoint synthesis | worktree after R308 | local | 6 problem cards across 4 datasets / 34,539 task-operations; operation-stack packets are more selective than flat on 6/6 tasks, contain high-lift evidence in 5/6 tasks, and have higher selected recall than fixed-session on 5/6 tasks; fixed-session uses less selected work in 4/6 tasks | `docs/visexp/out/operation-problem-value-r309/` | done |
| R310 | C1, C2, C3, C4 | Paper evidence matrix | `python3 script/paper_evidence_matrix_synthesis.py` reads tracked R307/R309 artifacts, checks they are tracked and clean, and writes JSON/Markdown/CSV/TeX/HTML claim matrix outputs | worktree after R309 | local | 4 claim rows; C1/C2/C4 scoped paper-ready, C3 partial; carries forward 34,539 operations, 3,699 positives, 5/6 high-lift, 6/6 more selective than flat, 5/6 higher selected recall than fixed-session, and fixed-session lower selected work in 4/6 tasks | `docs/visexp/out/paper-evidence-matrix-r310/` | done |
| R311 | C1, C2, C3, C4 | Paper robustness and reviewer-stress audit | `python3 script/paper_robustness_audit.py` reads tracked R302/R305/R308/R309/R310 artifacts, checks they are tracked and clean, and writes task-level robustness plus pass/narrow/partial/fail reviewer-stress rows | worktree after R310 | local | 6 tasks / 4 datasets / 34,539 operations; operation-stack packets are more selective than flat on 6/6 tasks, expose positive groups in 6/6 and high-lift evidence in 5/6, beat fixed-session selected recall in 5/6, but beat fixed-session selected work in only 2/6; human utility and automatic detection remain unsupported | `docs/visexp/out/paper-robustness-audit-r311/` | done |
| R312 | C1, C2, C3, C4 | Paper submission claim/guardrail audit | `python3 script/paper_submission_audit.py` reads tracked R310/R311 artifacts, the R320 profiler-accuracy report, and the current Chinese draft; checks number alignment, two-abstraction wording, must-not-claim guardrails, paper structure, and current C4 gate wording; and writes JSON/Markdown/CSV/TeX/HTML audit outputs | worktree after R320 plus current paper edits | local | Overall `scoped_claim_ready`; number alignment pass, two-abstraction boundary pass, must-not-claim guardrails pass, paper structure pass; C4 marked `hidden_label_profiler_accuracy_ready`; no dataset sync or profiler rerun | `docs/visexp/out/paper-submission-audit-r312/` | done |
| R313 | C4 | Operation-view Pareto frontier over existing task packets | `python3 script/operation_view_frontier_eval.py` reads tracked R300/R302/R305/R311 artifacts, checks they are tracked and clean, and writes JSON/Markdown/CSV/HTML frontier outputs | worktree after R312 | local | 6 tasks / 4 datasets / 34,539 operations / 3,699 positives; 162 non-oracle view/ranker/budget candidate points; operation-stack is on the Pareto frontier for 6/6 tasks, best lift for 4/6 tasks, and best recall under 30% work for 4/6 tasks; flat and fixed-session also remain frontier counterpoints on 6/6 tasks | `docs/visexp/out/operation-view-frontier-r313/` | done |
| R314 | C1, C2, C4 | Related-work novelty and baseline audit | `python3 script/paper_related_work_audit.py` reads the current related-work ledger, Chinese draft, claim ledger, evaluation ledger, and tracked R313 frontier output, then writes JSON/Markdown/CSV/HTML audit outputs | worktree after R313 | local | Overall `scoped_related_work_ready`; checks closest-work coverage, novelty delta, baseline grounding, guardrails, and R313 alignment; no dataset sync or profiler rerun | `docs/visexp/out/paper-related-work-audit-r314/` | done |
| R315 | C4 | Controlled analyst-study protocol over existing case packets | `python3 script/analyst_study_protocol.py` reads tracked R305/R308/R313 artifacts, checks visible/hidden separation, and writes study protocol, visible packets, hidden scoring key, assignment CSV, Markdown, HTML, and run-result | worktree after R314 | local | 6 tasks, 3 views, 24 participants, 144 trials; all task-view cells have 8 assigned trials; visible-packet leakage check pass; not a human/agent study result | `docs/visexp/out/analyst-study-protocol-r315/` | done |
| R316 | C4 | Analyst-study readout sensitivity over the R315 assignment | `python3 script/analyst_study_readout_eval.py` reads tracked R315 artifacts and scores the fixed visible-order top-k scripted policy against the hidden key | worktree after R315 | local | Top-3 operation-stack positive hit rate 1.0 and high-lift hit rate 0.8333; fixed-session is 0.8333 and 0.6667; flat is 1.0 and 0.0; operation-stack vs fixed-session task-paired median recall delta 0.1333 with median work delta 0.0207; not a human/agent study result | `docs/visexp/out/analyst-study-readout-r316/` | done |
| R317 | C1, C2, C4 | Claim-first real-problem paper narrative | `python3 script/paper_real_problem_narrative.py` reads tracked R309/R313/R316 artifacts, checks they are tracked and clean, and writes JSON/Markdown/CSV/HTML task narratives and readiness rubric | worktree after R316 | local | 6 task narratives across 4 datasets / 34,539 operations / 3,699 positives; operation-stack frontier coverage 6/6, high-lift coverage 5/6, higher selected recall than fixed-session 5/6, lower work than fixed-session 2/6; mechanism claims level-4 scoped, inspectability level-3-plus automated proxy, not new empirical evidence | `docs/visexp/out/paper-real-problem-narrative-r317/` | done |
| R318 | paper-readiness guardrail | Independent reviewer acceptance closure | `python3 script/paper_reviewer_acceptance_audit.py` records four subagent reviewer verdicts, verifies the Linnaeus artifact-log blocker is fixed, and checks current R312/R314/R317 guardrails | worktree after R317 paper polish | local | 4/4 final reviewer ACCEPT; 1 NEEDS_CHANGES round closed; R312 `scoped_claim_ready`, R314 `scoped_related_work_ready`, and R317 synthesis/two-abstraction checks pass; not empirical evidence or an analyst-task result | `docs/visexp/out/paper-reviewer-acceptance-r318/` | done |
| R319 | C1, C2, C4 | Implementation/docs consistency audit | `python3 script/implementation_consistency_audit.py` reads current Rust CLI/profile/standard-trace sources, canonical docs, and the Chinese paper to check profile-spec support, CLI help wording, operation predicates, standard-trace import/export, two-abstraction wording, and remaining-gate wording | worktree after R321 plus CLI help guardrail refresh | local | Overall `implementation_consistent`; 16/16 checks pass only if profile spec is no longer a stale pending task, CLI help/about is operation-stack-first with a regression test rejecting stale local-session/flamegraph-first wording, `--where`/`where_rules` are documented as query predicates, standard trace exchange is documented as operation import/export, and remaining gates are analyst utility, calibrated boundary backend, and real producer trace import; not dataset sync or empirical evidence | `docs/visexp/out/implementation-consistency-r319/` | done |
| R320 | C4 | Profiler accuracy and actionability benchmark | `python3 script/operation_profile_accuracy_eval.py` reads tracked/clean R288-R291/R300 operation JSONL and scores flat, fixed-session, dataset-native, raw-action, operation-stack, label-drilldown, width, visible-risk, query-aware, and oracle-upper policies with hidden labels | worktree after R319 | local | 4 datasets / 6 tasks / 34,539 operations / 3,699 positives / 144 policy scores; operation-stack query-aware top-5 work 0.0937 vs flat 1.0; operation-stack improves top-5 recall over fixed-session in 5/6 tasks and reduces median groups from 285.0 to 157.5; query-aware ranking improves AP over width-only operation-stack ranking in 6/6 tasks; no dataset sync or test-set creation | `docs/visexp/out/operation-profile-accuracy-r320/` | done |
| R321 | C1, C2 | Query-time operation predicate implementation probe | `python3 script/operation_where_filter_eval.py` writes profile specs with `where_rules`, runs Rust `agentpprof --profile-spec`, and checks folded sample counts against the tracked R300 operation JSONL | worktree after R320 plus `--where` implementation | local | 3 probes over existing real labeled operations; mapping-derived predicates select 729/729 AgentRewardBench looping operations, 714/714 non-success looping operations, and 4,285/4,285 SATraj safety operations before recursive stack folding; no dataset sync or test-set creation | `docs/visexp/out/operation-where-filter-r321/` | done |
| R322 | C2, C4 | Rust visible rank-rule implementation probe | `python3 script/operation_rust_rank_rule_eval.py` writes profile specs with `rank_rules`, runs Rust `agentpprof --profile-spec`, and scores the emitted JSON ranked operation-stack groups offline with hidden labels that are not passed to Rust ranking | worktree after R321 plus `--rank-rule` implementation | local | 6 tasks / tracked R300 operation JSONL; visible rank rules read only `action`, `environment`, `phase`, `repeat_signal`, and `status`; Rust ranking improves AP over width on 4/6 tasks, top-5 recall on 2/6 tasks, and top-5 lift on 3/6 tasks; no dataset sync or hidden-label leakage in rank rules | `docs/visexp/out/operation-rust-rank-rule-r322/` | done |
| R323 | C2, C4 | Rust rank-mode mechanism probe | `python3 script/operation_rank_mode_eval.py` writes profile specs with `rank_mode=width-boost` and `rank_mode=rule-score`, runs Rust `agentpprof --profile-spec`, and scores both JSON orderings offline with hidden labels that are not passed to Rust ranking | worktree after R322 plus `--rank-mode` implementation | local | 6 tasks / tracked R300 operation JSONL; `rule-score` improves AP over `width-boost` on 4/6 tasks, AP@20 on 3/6, top-5 lift on 4/6, and first-positive work on 3/6; SATraj first-positive work improves from 0.6376 to 0.0842; side-effect and OSWorld-Human remain counterexamples; no dataset sync or hidden-label leakage | `docs/visexp/out/operation-rank-mode-r323/` | done |
| R324 | C2, C4 | Rust operation rank-feature mechanism probe | `python3 script/operation_rank_feature_eval.py` writes a scrubbed visible-operation JSONL, writes profile specs with `rank_op_rules`, runs Rust `agentpprof --profile-spec`, and scores semantic plus coarse stack rankings offline with hidden labels that are not passed to Rust ranking | worktree after R323 plus `--rank-op-rule` implementation | local | 6 tasks / tracked R300 operation JSONL; Rust profiler input removes oracle fields before ranking; semantic-stack operation-feature ranking improves AP over width on 5/6 tasks, top-5 lift on 4/6, and first-positive work on 5/6; coarse-stack ranking improves AP on 4/6 and first-positive work on 5/6 while reducing groups; no dataset sync or hidden-label leakage in operation rank rules | `docs/visexp/out/operation-rank-feature-r324/` | done |
| R325 | C2, C4 | Rust operation rank-feature leave-one-out actionability probe | `python3 script/operation_rank_feature_ablation_eval.py` reuses the R324 scrubbed visible-operation profiler input, writes width/all/drop-one profile specs, runs Rust `agentpprof --profile-spec`, and scores each emitted ranking offline with hidden labels that are not passed to Rust ranking | worktree after R324 plus `--rank-op-rule` implementation | local | 6 tasks / 2 stack depths / 74 Rust profile-spec runs; all-feature semantic AP improves over width on 5/6 and first-positive work on 5/6; leave-one-out finds 7 critical feature instances and 3 misleading feature instances; coarse depth is AP-preferred on 2/6 tasks while reducing group counts on 6/6; no dataset sync or hidden-label leakage | `docs/visexp/out/operation-rank-feature-ablation-r325/` | done |
| R326 | C2, C4 | Rust operation rank-feature robustness/actionability probe | `python3 script/operation_rank_feature_robustness_eval.py` reuses the R324 scrubbed visible-operation profiler input and R325 findings, writes width/task-weighted/task-equal/global-equal/repaired profile specs, runs Rust `agentpprof --profile-spec`, and scores each emitted ranking offline with hidden labels that are not passed to Rust ranking | worktree after R325 plus `--rank-op-rule` implementation | local | 6 tasks / 2 stack depths / 5 policies / 60 Rust profile-spec runs; global equal visible feature bank improves AP over width on 4/6 semantic and 5/6 coarse tasks; task-equal stays within 0.02 AP of weighted policies on 8/12 variants; R325-guided repairs improve AP on 2/3 misleading-feature cases and first-positive work on 2/3 cases, with 1/3 improving both; no dataset sync or hidden-label leakage | `docs/visexp/out/operation-rank-feature-robustness-r326/` | done |
| R330 | C4 | Task-paired uncertainty audit over R320 policy scores | `python3 script/operation_profile_uncertainty_eval.py` reads tracked R320 `profile-accuracy-report.json` and `policy-scores.csv`; bootstrap unit is task family | worktree after R320 | local | 6 task families / 10,000 bootstrap reps / seed 330; directionally stable deltas include operation-stack query-aware versus flat AP, top-5 work, 30% budget recall, and work-to-first-positive; versus fixed-session top-5 recall, top-5 F1, and groups; versus width-only operation-stack AP and top-5 work; mixed/counterpoint metrics remain explicit | `docs/visexp/out/operation-profile-uncertainty-r330/` | done |
| R331 | C4 | Label-permutation negative-control audit | `python3 script/operation_profile_negative_control_eval.py` reads tracked R320 artifacts and the same source operation JSONL; it fixes visible ranking order and randomly reallocates hidden positives within task-sized groups | worktree after R330 | local | 6 tasks / 5 visible policies / 2,000 permutations / seed 331; operation-stack query-aware AP exceeds the 95% null on 6/6 tasks and budget30 recall on 5/6, while top-5 precision is 3/6 and work-to-first-positive is 0/6; fixed-session and raw-action AP also carry signal | `docs/visexp/out/operation-profile-negative-control-r331/` | done |
| R332 | C4 | View/depth task-fit audit over R320 visible policies | `python3 script/operation_view_depth_fit_eval.py` reads tracked R320 report/CSV and compares visible policies for AP, top-5 F1, 30% budget recall, and work-to-first-positive | worktree after R331 | local | Best visible AP splits across operation-stack 3/6, fixed-session 2/6, and dataset-native 1/6; best top-5 F1 spans raw-action, dataset-native, fixed-session, flat, and operation-stack; leave-task source selection is exact-best on 0/6 AP and 0/6 F1 tasks | `docs/visexp/out/operation-view-depth-fit-r332/` | done |
| R333 | C4 | Inspection-efficiency frontier over R320 scorer outputs | `python3 script/operation_inspection_frontier_eval.py` reruns the R320/R300 local scorer over tracked operation JSONL and emits full top-k/work-budget curves | worktree after R332 | local | 6 tasks / 4 datasets / 144 scored policy rows / 810 visible inspection points / 252 task-policy curve rows; at 30% inspected work, operation-stack query-aware median recall is 0.3900 versus 0.0000, 0.3559, 0.3377, and 0.3325 for flat, fixed-session, dataset-native, and raw-action; no dataset sync or creation | `docs/visexp/out/operation-inspection-frontier-r333/` | done |
| R334 | C4 | Positive-fragmentation and coverage audit over R320/R333 | `python3 script/operation_fragmentation_tradeoff_eval.py` reads tracked R320 policy scores, R333 inspection curves, and source operation JSONL; no dataset sync, creation, or relabeling | worktree after R333 | local | 6 tasks / 4 datasets / 34,539 operations / 3,699 positives; operation-stack query-aware reaches 50% positives with fewer ranked groups than fixed-session query-aware on 5/6 tasks and inspects fewer groups at the same 30% work budget on 5/6 tasks, but has lower work-to-first-positive on only 2/6 tasks | `docs/visexp/out/operation-fragmentation-tradeoff-r334/` | done |
| R335 | C4 | Actionability and mechanism synthesis over R320/R325/R326/R329/R332/R334 | `python3 script/operation_actionability_synthesis_eval.py` reads tracked score, ablation, robustness, transfer, view-depth, and fragmentation artifacts; no dataset sync, creation, or relabeling | worktree after R334 | local | 6 task actionability cards; 6/6 have concrete optimization actions and query-aware AP gain over width; mapping helps 2/6 and hurts 4/6; critical features appear on 4/6 and misleading features on 2/6; coarse depth reduces groups on 6/6 but is AP-preferred on 2/6; fixed-session has lower work-to-first-positive on 4/6 | `docs/visexp/out/operation-actionability-synthesis-r335/` | done |
| R336 | C4 | Multi-objective actionability-selection audit over R320/R333/R334/R335 | `python3 script/operation_actionability_selection_eval.py` reads tracked profile accuracy, inspection-frontier, fragmentation, and actionability artifacts; no dataset sync, creation, or relabeling | worktree after R335 plus committed R336 evaluator | local | 15 visible policies / 6 tasks / 6 diagnostic objectives; operation-stack query-aware is Pareto-frontier on 6/6 tasks, best AP on 3/6, best 30% budget recall on 3/6, lower top-5 work than flat on 6/6, higher top-5 recall than fixed-session on 5/6, lower groups-to-50% positives than fixed-session on 5/6, and lower work-to-first-positive than fixed-session on only 2/6; every task has more than one best policy across objectives | `docs/visexp/out/operation-actionability-selection-r336/` | done |
| R337 | C4 | Fixed recall-target inspection-cost audit over R333/R336 | `python3 script/operation_inspection_target_eval.py` reads tracked inspection-frontier curves and actionability recommendations; no dataset sync, creation, or relabeling | worktree after R336 plus committed R337 evaluator | local | 6 tasks / 4 datasets / 6 visible policies / 3 recall targets; at 25% positive recall, operation-stack query-aware reaches 6/6 tasks with median work 0.2000 and median 16.0 groups, flat reaches 6/6 only at median work 1.0000, and fixed-session reaches 6/6 with median 50.0 groups; at 10% recall, operation-stack and fixed-session both reach 6/6 but operation-stack uses median 12.5 groups versus 37.5; at 50% recall, operation-stack query-aware reaches 5/6 and other visible policies are best-work counterpoints | `docs/visexp/out/operation-inspection-target-r337/` | done |
| R338 | C4 guardrail / scope control | Paper claim-integrity audit over R327/R328 and R320-R350 | `python3 script/paper_claim_integrity_audit.py` reads tracked-clean R327/R328 reproducibility artifacts plus R320/R333/R334/R335/R336/R337/R339/R340/R341/R342/R344/R345/R346/R347/R348/R349/R350 result artifacts and hashes current Chinese/English paper sources; no dataset sync, creation, relabeling, or new ranking | worktree after committed clean R328 deterministic-output artifact plus updated R338 evaluator | local | Overall `pass`; 350/350 number checks, result invariants, source-policy checks, guardrail checks, paper text coverage, two-abstraction boundary, and tracked-clean empirical source checks pass | `docs/visexp/out/paper-claim-integrity-r338/` | done |
| R339 | C2/C4 | Sequence-scope adequacy audit over R300/R320 policies | `python3 script/operation_sequence_adequacy_eval.py` reads tracked R288-R291 operation JSONL plus R320/R337 reports; no dataset sync, creation, relabeling, or hidden-label ranking; hidden labels only for scoring after visible ranking | worktree after committed R339 evaluator | local | 6 tasks / 4 datasets / 144 policies; overall `pass`; hidden labels used only after visible ranking; at top-5 operation-stack query-aware inspects median work 0.0937 and covers median 0.2629 positive-session recall versus fixed-session 0.0160; at 30% work it covers median 0.4669 positive-session recall versus fixed-session 0.3230 while touching median 0.3467 sessions; raw-action reaches 0.5147 but touches 0.9103 sessions | `docs/visexp/out/operation-sequence-adequacy-r339/` | done |
| R340 | C4 | Cross-task/cross-dataset visible policy-transfer audit | `python3 script/operation_policy_transfer_eval.py` reads tracked-clean R320 profile-accuracy artifacts and R339 sequence-adequacy artifacts; selection uses only non-target tasks or non-target datasets, and target hidden labels are used only for offline scoring of already-ranked policies | worktree after R339 plus R340 evaluator | local | 6 tasks / 4 datasets / 15 visible policies / 8 objectives / 2 protocols / 96 held-out decisions; 31/96 exact-best selections and 62/96 within-tolerance selections; selected policies strictly beat width on 72/96 decisions, fixed-session on 69/96, and flat on 41/96; operation-stack is selected on 16/96 decisions, so the claim is objective-specific policy transfer rather than a universal selector | `docs/visexp/out/operation-policy-transfer-r340/` | done |
| R341 | C4 | Mechanism and transfer-error attribution over R320/R335/R336/R340 | `python3 script/operation_mechanism_attribution_eval.py` reads tracked-clean profile accuracy, actionability cards, objective recommendations, and transfer decisions; no dataset sync, creation, relabeling, or new ranking | worktree after committed R340 artifact plus R341 evaluator | local | 6 tasks / 36 objective rows / 96 transfer decisions; 36/36 best policies visible, 36/36 best policies non-oracle, and 36/36 objective rows have optimization actions; 27/36 best visible policies are non-default; 34/96 transfer decisions are outside tolerance and classified into view/ranker/baseline-counterpoint explanations; 32/34 misses change view, 26/34 change ranker, and 29/34 high-regret misses expose tuning errors; stack-depth signals on 6/6, transfer-policy signals on 6/6, critical features on 4/6, misleading features on 2/6, and three or more mechanism labels on 6/6 tasks | `docs/visexp/out/operation-mechanism-attribution-r341/` | done |
| R342 | C1/C2/C4 | Profile-spec composition and recursive stack-depth audit over R324 real-trace Rust outputs | `python3 script/operation_profile_spec_composition_eval.py` reads tracked-clean R324 report/CSV/profile specs/Rust JSON and recomputes task/depth tradeoffs; no dataset sync, creation, relabeling, or new ranking | worktree after committed R342 evaluator | local | 6 tasks / 12 profile-spec variants; 12/12 compose operation files, `where_rules`, `rank_op_rules`, `rank_mode=rule-score`, and explicit stack depth; 12/12 prompt/session-free; AP improves over width on 9/12 variants, top-5 lift improves on 8/12 variants, and first-positive work on 10/12; coarse depth reduces groups on 6/6 tasks with median group reduction 0.8267; best AP depth splits semantic 4 / coarse 2, and depth choice changes objective on 3/6 tasks | `docs/visexp/out/operation-profile-spec-composition-r342/` | done |
| R343 | C1/C2/C4 | Relocated-checkout audit for historical profile-spec artifact paths | `python3 script/profile_artifact_relocation_audit.py` reads tracked R324/R342 artifacts, simulates a different checkout root for historical absolute `operation_files`, and checks that R342/R338 path normalization rebases them via the `docs/visexp/out/...` suffix; no dataset sync, creation, relabeling, or new ranking | worktree after R342/R338 relocation fix | local | Overall `pass`; 12/12 operation-file path checks pass; 12/12 raw operation-file paths are absolute historical paths; R338 recomputes 12 variants / 6 tasks / 12 composition variants from R342 source paths under relocated-path normalization | `docs/visexp/out/profile-artifact-relocation-r343/` | done |
| R344 | C4 | Multi-metric consistency audit over R320 scored profiler rankings | `python3 script/operation_metric_consistency_eval.py` reads tracked R320 policy scores and report; it does not rerank, sync, create, or relabel data | worktree after committed R344 evaluator | local | Overall `pass`; 6 tasks / 50 baseline-metric comparisons / 300 task-metric deltas; 30 support verdicts, 16 counterpoints, and 4 mixed/weak verdicts. Operation-stack query-aware beats flat on AP, budget30 recall/F1, top-5 work, and work-to-first-positive on 6/6 tasks; beats width-only operation-stack on AP on 6/6 and budget30 recall/F1 on 5/6; beats fixed-session on top-5 precision/recall/F1 on 5/6; nDCG and coarse top-k recall are explicit counterpoints | `docs/visexp/out/operation-metric-consistency-r344/` | done |
| R345 | C4 | Diagnostic-lens portfolio over actionability and metric counterpoints | `python3 script/operation_diagnostic_lens_portfolio_eval.py` reads tracked-clean R335/R341/R344 artifacts; it does not rerank, sync, create, or relabel data | worktree after committed R344 artifact plus R345 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 6 diagnostic lenses / 36 objective rows; 6/6 task cards remain actionable; operation-stack-family views win 11/36 objectives, non-operation-stack counterpoints win 25/36, and 6/6 tasks need at least three best views across objectives; 46 counterpoint rows preserve fixed-session, flat, raw-action, dataset-native, and metric-surface counterpoints | `docs/visexp/out/operation-diagnostic-lens-portfolio-r345/` | done |
| R346 | C4 | Diagnostic casebook over top-ranked operation-stack groups | `python3 script/operation_diagnostic_casebook_eval.py` reads tracked-clean R335/R345 artifacts and existing public labeled operation JSONL; it does not fetch, sync, create, relabel, or use hidden labels for ranking | worktree after committed R346 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 30 case groups; top-5 visible operation-stack groups contain positives on 6/6 tasks and top-1 contains positives on 5/6 tasks; median top-5 recall 0.188, precision 0.1991, lift 1.6508, work 0.0937, and first-positive work 0.0378; 6/6 case cards link evidence to actions and counterpoints | `docs/visexp/out/operation-diagnostic-casebook-r346/` | done |
| R347 | C4 | Case-level baseline contrast over visible views | `python3 script/operation_case_baseline_contrast_eval.py` reads tracked R346 casebook artifacts and existing public labeled operation JSONL; it compares flat, fixed-session, dataset-native, raw-action, and operation-stack visible views and uses hidden labels only for scoring already-ranked groups | worktree after committed R347 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 5 visible views / 30 view-task rows; operation-stack top-5 groups contain positives on 6/6 tasks and top-1 contains positives on 5/6; median top-5 lift 1.6508 and work 0.0937; operation-stack wins vs flat top-5 work on 6/6, vs fixed-session top-5 recall on 5/6, and vs fixed-session group count on 4/6, while fixed-session first-positive and flat full-work recall remain counterpoints | `docs/visexp/out/operation-case-baseline-contrast-r347/` | done |
| R348 | C4 | Action-counterfactual audit over objective-level tuning knobs | `python3 script/operation_action_counterfactual_eval.py` reads tracked R335/R341/R347 artifacts; it uses hidden labels only through already-scored visible policy rows and does not form a deployment selector | worktree after committed R348 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 36 objective rows; 36/36 best rows are visible non-oracle, 27/36 require non-default actions, 25/36 require view changes, 2/36 require operation-stack ranker tuning, 25/36 are non-operation-stack counterpoints, and 6/6 tasks have at least three action classes plus case counterpoints; median gain over default is 0.1447 and median non-default gain is 0.6188 | `docs/visexp/out/operation-action-counterfactual-r348/` | done |
| R349 | C4 | Held-out action-transfer guardrail | `python3 script/operation_action_transfer_eval.py` reads tracked R340/R348 artifacts; it maps non-target-selected visible policies to action classes and compares them against the R348 target-task action oracle without creating or relabeling datasets | worktree after committed R349 evaluator | local | Overall `pass`; 96 transfer decisions, 60 aligned decisions, and 36 excluded sequence decisions; selected policies and target best policies are 60/60 visible non-oracle; held-out selection is within tolerance on 35/60 and beats default on 30/60, but exact action-class transfer is only 7/60 and only 2/42 on non-default target actions | `docs/visexp/out/operation-action-transfer-r349/` | done |
| R350 | C4 | Evidence-packet budget audit | `python3 script/operation_evidence_packet_eval.py` reads tracked R346/R347/R348/R349 artifacts and combines top-ranked operation-stack evidence, baseline counterpoints, action counterfactuals, and held-out transfer guardrails; no dataset sync, creation, relabeling, or new ranking | worktree after committed R350 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 36 objective rows; top-5 packets contain positives on 6/6 tasks, top-1 packets on 5/6, strict 30% work budget on 4/6, first-positive <=10% work on 4/6; packets preserve 6/6 baseline counterpoints, 27/36 non-default objective rows, 36/36 visible non-oracle best rows, and R349 35/60 within-tolerance / 7/60 exact-action guardrail | `docs/visexp/out/operation-evidence-packet-r350/` | done |
| R351 | C4 guardrail / scope control | Independent reviewer acceptance after R350/R338 | `python3 script/paper_reviewer_acceptance_r351.py` records four current read-only subagent reviewer verdicts and rereads tracked R320/R328/R331/R338/R350 artifacts; no dataset sync, profiler rerun inside R351, relabeling, or human/agent analyst task | worktree after committed clean R328 deterministic-output artifact | local | Overall `accepted`; 4/4 reviewers ACCEPT, 0 blocking issues, 11/11 acceptance checks pass; R328 clean deterministic-output provenance resolves 1 Galileo residual, and R338 integrity, R350 bounded packet evidence, R320 hidden-label leakage check, R331 negative-control provenance, no dataset sync/relabeling, and must-not-claim wording are all checked | `docs/visexp/out/paper-reviewer-acceptance-r351/` | done |
| R352 | C4 guardrail / scope control | OSDI-style evaluation-rubric audit | `python3 script/paper_evaluation_rubric_audit.py` reads tracked R320-R351 artifacts and current paper text; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after committed R351/R338 state | local | Overall `pass`; 26/26 required checks pass at `level_4_scoped_profile_benchmark`; all 10 rubric areas pass, covering claim-evidence alignment, setup, fidelity, baseline tradeoff, actionability, generality, mechanism isolation, robustness/statistics, reproducibility/overhead, and must-not-claim guardrails | `docs/visexp/out/paper-evaluation-rubric-r352/` | done |
| R353 | C1 | Operation-file standard-trace exchange over existing real labeled rows | `python3 script/operation_standard_trace_exchange_eval.py` reads a deterministic prefix of tracked R324 visible-operation JSONL, exports it through the Rust `--operation-file --export-standard-trace` path, imports it with `--standard-trace-file`, and profiles both paths with the same stack; no dataset sync, creation, relabeling, or accuracy scoring | worktree after R352/R353 implementation | local | Overall `ok`; 512 prefix operations export to 512 Chrome complete events, both direct and imported profiles report 512 samples / 11 unique stacks, and folded outputs are byte-identical; source and operation schema are `agentsight.operation.v1`; this is an exchange/reproducibility smoke, not a new accuracy result | `docs/visexp/out/operation-standard-trace-exchange-r353/` | done |
| R354 | C4 | Executable profile-spec patch actionability audit | `python3 script/operation_profile_patch_eval.py` reads tracked R324 visible-operation profiler input plus R348 action cards, writes default semantic-width profile specs and profile-guided patched specs, runs Rust `agentpprof --profile-spec` for both, and scores emitted groups with hidden labels only after profiling; no dataset sync, creation, relabeling, or human/agent analyst task | worktree after R353 implementation | local | Overall `pass`; 6 tasks / 4 datasets / 12 Rust profile-spec invocations; profile-guided patches are accepted on 5/6 tasks; AP improves on 5/6, top-5 lift on 5/6, first-positive work on 5/6, and groups reduce on 2/6; median delta AP 0.0376, median delta top-5 lift 0.5750, median delta first-positive work -0.0859; OSWorld-Human is the intentional rejected patch that needs boundary-derived fields | `docs/visexp/out/operation-profile-patch-r354/` | done |
| R355 | C2/C4 | Oracle-depth adequacy audit over existing labeled profile rankings | `python3 script/operation_oracle_depth_adequacy_eval.py` reads tracked-clean R300 operation JSONL, R320 profile-accuracy report, R339 sequence-adequacy report, and ScaleCUA context rows; it scores visible-ranked groups at session, operation/step, positive-run, and task-specific oracle depth after ranking, with hidden labels used only for offline scoring | worktree after R354 plus committed R355 evaluator | local | Overall `pass`; 6 tasks / 4 datasets / 24 accuracy task-depth rows / 1 context-only ScaleCUA row; operation-stack query-aware median top-5 oracle-unit work 0.1307, budget-30 positive-unit recall 0.4342, budget-30 positive-unit F1 0.4484, and positive-run recall 0.4908; compared with flat/fixed/raw-action it has 24/24 lower top-5 unit work than flat, 20/24 higher budget-30 unit recall than fixed-session, 18/24 higher budget-30 unit F1 than fixed-session, 22/24 fewer groups to 50% positive units than fixed-session, and 24/24 fewer positive units per group than raw-action; depth-gap versus fixed-session remains a counterpoint | `docs/visexp/out/operation-oracle-depth-adequacy-r355/` | done |
| R356 | C4 guardrail / scope control | Paper claim-integrity refresh over R354/R355 | `python3 script/paper_claim_integrity_r356.py` reuses the R338 R320-R350 gate, hashes tracked-clean R354/R355 artifacts, hashes current docs and Chinese/English paper text, and checks paper tokens, result invariants, source provenance, must-not-claim guardrails, and the operation/operation-stack boundary; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R355 plus committed R356 evaluator | local | Overall `pass`; base R338 gate pass; R354/R355 result invariants pass; paper text coverage pass; guardrails pass; source artifacts tracked clean; checks include R354 5/6 accepted patches, median delta AP 0.0376, median delta top-5 lift 0.5750, R355 24 accuracy task-depth rows, 0.4342 budget-30 unit recall, 20/24 fixed-session recall wins, and 22/24 groups-to-50% wins | `docs/visexp/out/paper-claim-integrity-r356/` | done |
| R357 | C4 guardrail / scope control | Reviewer-acceptance refresh after R356 | `python3 script/paper_reviewer_acceptance_r357.py` records four current read-only reviewer verdicts and rereads tracked R351/R352/R354/R355/R356 artifacts plus current paper/docs hashes; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after committed R356 state plus R357 evaluator | local | Overall `accepted`; 4/4 current reviewers ACCEPT, 0 blocking issues, 3 non-blocking traceability notes, all mechanical acceptance checks pass, source gate passes, and checks cover R356 69/69 number checks, 18/18 text checks, 54/54 guardrails, R354 5/6 accepted patches with 0.0376 AP delta and 0.5750 lift delta, R355 24 oracle-depth rows with 0.4342 budget-30 unit recall, R352 level-4 rubric, R351 prior acceptance, must-not-claim guardrails, and operation/operation-stack boundary | `docs/visexp/out/paper-reviewer-acceptance-r357/` | done |
| R358 | C2/C4 | Boundary-derived profile patch audit for OSWorld-Human | `python3 script/operation_boundary_profile_patch_eval.py` reads tracked R297 held-out OSWorld-Human boundary-backend operations, strips oracle/group labels from the Rust profiler input, keeps learned boundary fields as visible operation fields, writes flat/fixed/semantic/learned-boundary profile specs, runs Rust `agentpprof --profile-spec`, and scores emitted groups with hidden labels only after profiling; no dataset sync, creation, relabeling, or human/agent analyst task | worktree after R357 plus R358 evaluator | local | Overall `pass`; 1,132 held-out operations / 243 positives; learned-boundary AP 0.2583 vs semantic-width 0.2402 and visible-rank 0.2253; learned-boundary groups 74 vs semantic 108 and fixed-session 96; top-5 recall delta vs semantic +0.1111; counterpoints are top-5 work delta +0.0813, first-positive-work delta +0.1581, and learned-boundary rank AP delta -0.0224, so boundary-derived fields help AP/fragmentation but not every inspection-cost metric | `docs/visexp/out/operation-boundary-profile-patch-r358/` | done |
| R359 | RQ1/E1-RQ4/E4 paper-structure guardrail | Core experiment consolidation audit | `python3 script/paper_core_experiment_consolidation_audit.py` reads the evaluation ledger, Chinese claim setup, Chinese paper, English submodule paper, and tracked R358 artifacts; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R358 plus R359 evaluator and RQ/E table update | local | Overall `pass`; 13/13 checks pass; confirms RQ1/E1-RQ4/E4 are the paper-facing evaluation structure, R-numbered runs are provenance, legacy scattered RQ/Paper-question framing is absent, R358 is an RQ3/E3 mechanism/actionability ablation rather than a fifth experiment, R358 AP/group/counterpoint tokens remain visible, and the two-abstraction plus must-not-claim guardrails remain visible | `docs/visexp/out/paper-core-experiments-r359/` | done |
| R360 | RQ1/E1-RQ4/E4 table/provenance guardrail | Paper core-result table generator | `python3 script/paper_core_result_tables.py` reads tracked R285/R286/R320/R328/R338/R342/R353/R354/R355/R357/R358/R359/R366 artifacts plus current paper/docs, generates the RQ/E main-result table, metric CSV, Markdown, HTML, LaTeX fragment, source-status, and checks; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R366 plus R360 table generator refresh | local | Overall `pass`; 8/8 checks pass; 4 paper-block rows and 20 metric rows generated; preserves RQ1/E1 13,265-operation depth sweep, 9-to-3,757 stack range, R366 6 mechanism rows / 5 boundary-family rows / 4/5 boundary-backend suitability wins, RQ2/E2 6-task / 4-dataset / 34,539-operation / 3,699-positive / 144-policy benchmark with 0.0937 vs 1.0 top-5 work and 157.5 vs 285 groups, RQ3/E3 R354 5/6 accepted patches, R358 AP 0.2583 vs 0.2402, R366 7 critical and 3 misleading feature rows, and RQ4/E4 R328 76/76 semantic/raw-byte deterministic replay with 1.601s median and 2.767s p95 runtime. R338/R352/R357/R359/R366 are internal evidence or scope-control checks, not extra paper blocks | `docs/visexp/out/paper-core-result-tables-r360/` | done |
| R361 | RQ1/E1-RQ4/E4 ledger/provenance guardrail | Core-claim evidence ledger | `python3 script/paper_core_claim_evidence.py` reads tracked R320/R352/R354/R355/R357/R358/R359/R360/R366 artifacts plus current evaluation ledger and Chinese/English drafts, then writes a reviewer-facing RQ/E ledger with claim, research question, oracle, baselines, primary metrics, headline result, actionability, counterpoint, scoped wording, source-status, Markdown, HTML, and LaTeX; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after refreshed R360 plus R361 evaluator | local | Overall `pass`; 11/11 checks pass; confirms every RQ/E row has claim/oracle/baseline/metric/scope fields, RQ2/E2 preserves R320 hidden-label scale and the full localization/ranking metric surface, RQ2/E2 is a baseline tradeoff rather than all-metric dominance claim, R355 oracle-depth/fragmentation evidence is represented, RQ3/E3 preserves R354/R358/R366 mechanism counterpoints, RQ4/E4 preserves R328 replay/cost evidence while R352/R357/R359/R360 remain scope-control checks, and the operation/operation-stack boundary plus must-not-claim guardrails remain explicit | `docs/visexp/out/paper-core-claim-evidence-r361/` | done |
| R362 | RQ1/E1-RQ4/E4 section guardrail | Paper section-readiness audit | `python3 script/paper_core_section_readiness.py` reads R361, the Chinese paper, the English submodule paper, and the evaluation ledger; it parses RQ1/E1-RQ4/E4 result subsections and checks claim/oracle/baseline/metric/counterpoint tokens, RQ2/E2 localization metrics, RQ3/E3 actionability guardrails, RQ4/E4 reproducibility guardrails, and the two-abstraction boundary; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after refreshed R361 plus R362 evaluator | local | Overall `pass`; 16/16 checks pass; 8/8 section-token rows pass across Chinese and English RQ/E sections; R361 11/11 remains the source ledger; must-not-claim scope remains visible; prompt/session/tool/process/syscall are kept as operation forms or operation fields, not new profiler objects | `docs/visexp/out/paper-core-section-readiness-r362/` | done |
| R363 | RQ2/E2-RQ3/E3 presentation artifact | Paper visualization portfolio over RQ1/E1-RQ4/E4 evidence | `python3 script/paper_visualization_portfolio.py` reads tracked R320/R345/R348/R354/R355/R358/R361/R362 artifacts and generates paper-facing SVG/CSV/Markdown/HTML/JSON views plus `portfolio-table.tex`; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R362 plus R363 visualization generator | local | Overall `pass`; 7/7 checks pass; 5 paper views and one LaTeX table fragment generated: baseline tradeoff, metric heatmap, diagnostic lenses, actionability knobs, and oracle-depth adequacy; checks preserve baseline-tradeoff evidence, diagnostic counterpoints, non-default actionability knobs, oracle-depth support, tracked-clean sources, and the two-abstraction boundary | `docs/visexp/out/paper-visualization-portfolio-r363/` | done |
| R364 | RQ1/E1-RQ4/E4 sufficiency guardrail | Three-plus-one sufficiency audit | `python3 script/paper_core_experiment_sufficiency_audit.py` reads tracked R338/R352/R356/R357/R360/R361/R363/R366 artifacts plus current paper/docs and verifies that E1-E3 have primary empirical profiling tests and E4 has replayability/cost/scope-control evidence, with oracle or replay target, baselines or scope condition, metrics, quantified success criterion, failure interpretation, figure/table target, and claim-gate decision; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after refreshed R360/R361 plus R364 evaluator | local | Overall `pass`; 15/15 checks pass; confirms exactly RQ1/E1-RQ4/E4 as three empirical profiling experiments plus one replayability/scope-control block, flat/fixed-session drilldown/dataset-native/raw-action/operation-stack baselines for empirical rows, localization metrics, executable profile-spec and supervised boundary-field actionability, R366 field derivation internal to RQ1/E1 and RQ3/E3 rather than a new core experiment, non-flamegraph visualization targets, scoped trace-tree baseline wording, task-query ranker wording, and scope-control treatment for self-audits | `docs/visexp/out/paper-core-experiment-sufficiency-r364/` | done |
| R365 | E2/E3 paper-integration artifact | Headline evidence and case-study selector | `python3 script/paper_headline_case_studies.py` reads tracked R320/R333/R334/R345/R348/R354/R355/R358/R363 artifacts, emits five headline rows and six task cards, and does not sync data, relabel, rerun profiler, or run a human/agent analyst task | worktree after R364 plus R365 generator | local | Overall `pass`; 5 headline rows and 6 task cards; preserves Work@5 0.0937 vs flat 1.0, R@30% 0.3900 vs fixed-session 0.3559, 157.5 vs 285 groups, 24/24 lower unit work than flat, 20/24 fixed-session unit recall wins, 27/36 non-default actions, R354 5/6 accepted patches, and R358 AP 0.2583 vs 0.2402 with work counterpoints | `docs/visexp/out/paper-headline-case-studies-r365/` | done |
| R366 | C3/E3 mechanism guardrail | Operation-field derivation mechanism audit | `python3 script/operation_field_derivation_mechanism_eval.py` reads tracked R282/R285/R297/R299/R325/R342/R358 artifacts plus current paper/docs, emits six mechanism rows and five boundary-family rows, and does not sync data, relabel, rerun the profiler, or run a human/agent analyst task | worktree after R365 plus R366 generator | local | Overall `pass`; 6/6 checks pass; held-out mapping compression 14.049->19.091 with action-label coarsening counterpoint; leave-dataset-out mapping reduces stacks on 6/9 datasets with 0 negative reductions; 12/12 profile-spec variants are prompt/session-free; rank-feature ablation finds 7 critical and 3 misleading feature rows; boundary backends beat best simple baseline on 4/5 rows; R358 learned-boundary fields improve AP 0.2402->0.2583 and groups 108->74 while increasing top-5 and first-positive work | `docs/visexp/out/operation-field-derivation-mechanism-r366/` | done |
| R367 | RQ1/E1-RQ4/E4 entry-narrative guardrail | Paper entry claim-path audit | `python3 script/paper_entry_claim_path_audit.py` reads the Chinese paper, English submodule paper, evaluation ledger, implementation doc, and tracked R360/R361/R364/R366 ledgers; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R366 plus R367 evaluator | local | Overall `pass`; 11/11 checks pass and 6/6 entry-token rows pass; confirms abstract, introduction/problem framing, and main result table all present RQ1/E1-RQ4/E4 as three empirical profiling experiments plus one replayability/scope-control block, keep R-runs as provenance, preserve only operation and operation stack as profiler abstractions, carry RQ2/E2/RQ3/E3/RQ4/E4 headline numbers, keep R366 internal to RQ1/E1 and RQ3/E3, and exclude human-productivity, automatic-boundary, metric-dominance, live-overhead, and complete ecosystem-compatibility claims | `docs/visexp/out/paper-entry-claim-path-r367/` | done |
| R368 | E2 baseline-scope guardrail | Trace-tree-shaped baseline tradeoff audit | `python3 script/paper_trace_tree_baseline_audit.py` reads existing R320 policy scores, R355 oracle-depth comparisons, R361/R364/R367 ledgers, and current Chinese/English paper text; no dataset sync, creation, relabeling, profiler rerun, real OTel/Phoenix/LangSmith/Perfetto import, or human/agent analyst task | worktree after R367 plus R368 evaluator | local | Overall `pass`; 10/10 checks pass; confirms the evaluated trace-tree-shaped baseline is fixed-session drilldown rather than ecosystem compatibility, operation-stack query-aware improves fixed-session top-5 recall/F1 on 5/6 tasks and budget-30 recall on 4/6, reduces median groups from 285.0 to 157.5, improves flat AP/budget-recall/top-5-work on 6/6, improves dataset-native AP on 4/6 and top-5 work on 6/6, preserves raw-action counterpoints, and keeps fixed-session top-5-work / first-positive-work wins on 4/6 as non-dominance evidence. R355 adds 20/24 fixed-session unit-recall wins and 22/24 groups-to-50%-positive-unit wins | `docs/visexp/out/paper-trace-tree-baseline-r368/` | done |
| R369 | RQ1/E1-RQ4/E4 reviewer evidence-path guardrail | Paper reviewer evidence path | `python3 script/paper_reviewer_evidence_path.py` reads tracked R360/R361/R363/R365/R368 artifacts plus current Chinese/English paper text and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R368 plus R369 evaluator | local | Overall `pass`; 9/9 checks pass; emits a four-row reviewer evidence path connecting each RQ to its main paper evidence, source artifact, guardrail, and non-claim; preserves RQ2 hidden-label localization path with R320/R368, RQ3 executable patch and boundary-field path with R354/R358/R365/R366, the two-abstraction boundary, must-not-claim limits, tracked upstream gates, and no-new-data/no-profiler-rerun policy | `docs/visexp/out/paper-reviewer-evidence-path-r369/` | done |
| R370 | RQ1/E1-RQ4/E4 main-experiment contract guardrail | Paper main-experiment contract | `python3 script/paper_main_experiment_contract.py` reads tracked R360/R361/R363/R364/R365/R368/R369 artifacts plus current Chinese/English paper text and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R369 plus R370 evaluator | local | Overall `pass`; 10/10 checks pass; emits four paper-block contracts requiring primary test, workload/oracle, baselines/metrics, primary evidence, supporting R-run roles, failure interpretation, and non-claim; enforces the three-empirical-plus-one-artifact organization and keeps later R-runs as primary evidence, ablations, counterpoints, provenance, or scope checks inside E1-E4 rather than new chronological experiments | `docs/visexp/out/paper-main-experiment-contract-r370/` | done |
| R371 | RQ1/E1-RQ4/E4 evaluation narrative-focus guardrail | Paper evaluation narrative focus audit | `python3 script/paper_evaluation_narrative_focus.py` reads tracked R370, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R370 plus R371 evaluator | local | Overall `pass`; 10/10 checks pass; verifies both papers have RQ1/E1-RQ4/E4 sections, English RQ1 no longer lists E3 ranker/actionability probes as recursive-folding evidence, RQ2 leads with R320 before robustness slices, RQ3 explains rank-feature/mapping mechanisms before executable patch and boundary repair cases, RQ4 leads with R327/R328 replay/cost before scope-control checks, every RQ section carries claim-test/counterpoint/non-claim language, and R371 remains no-new-data/no-profiler-rerun organization check | `docs/visexp/out/paper-evaluation-narrative-focus-r371/` | done |
| R372 | RQ2/E2-RQ3/E3 main-body concision guardrail | Paper main-body concision audit | `python3 script/paper_main_body_concision_audit.py` reads tracked R371, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R371 plus R372 evaluator | local | Overall `pass`; 9/9 checks pass; verifies English RQ2 compresses R330-R334/R355 into one supporting-audit paragraph instead of chronological support-run paragraphs, preserves E2 headline numbers and scoped non-claims, confirms Chinese RQ2 is already compact, and checks RQ3 still centers mechanism/actionability plus automatic-selector and automatic-boundary-discovery non-claims | `docs/visexp/out/paper-main-body-concision-r372/` | done |
| R373 | RQ2/E2-RQ3/E3 task-level claim-verdict synthesis | Paper task-level claim verdict | `python3 script/paper_task_claim_verdict.py` reads tracked R320/R354/R355/R358/R365 artifacts plus current Chinese/English paper text and the evaluation ledger, emits a six-row task verdict table, and writes the English submodule table fragment; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R372 plus R373 generator | local | Overall `pass`; 9/9 checks pass; 6/6 tasks improve AP and top-5 work over flat, 5/6 improve top-5 recall over fixed-session, 4/6 reduce fixed-session group fragmentation, 4/6 preserve fixed-session first-positive-work counterpoints, and 6/6 have actionable configuration evidence through 5/6 accepted R354 patches plus the R358 boundary-field repair; outputs task verdict CSV/JSON/Markdown/HTML and LaTeX table fragments | `docs/visexp/out/paper-task-claim-verdict-r373/` | done |
| R374 | RQ1/E1-RQ4/E4 three-plus-one role gate | Paper three-plus-one role map | `python3 script/paper_core_experiment_weight_gate.py` reads tracked R370/R371/R372/R373 artifacts plus current Chinese/English paper text and the evaluation ledger, emits a four-row primary-anchor/support-role/non-claim table, and writes the English submodule table fragment; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after subagent reviewer feedback plus R374 terminology refresh | local | Overall `pass`; checks that the paper remains organized as three empirical profiling experiments plus one replayability/scope-control block, each block has a substantial primary anchor, support runs are downgraded to support/presentation/scope-check/future-protocol roles, fidelity/actionability/tradeoff evidence is covered, non-claims remain explicit, and both papers expose the compact R374 role map instead of R369-R373 process logs; also records reviewer-driven wording fixes for fixed-session as trace-tree proxy and median/tradeoff fragmentation | `docs/visexp/out/paper-core-experiment-weight-r374/` | done |
| R375 | RQ1/E1-RQ4/E4 claim-decision guardrail | Paper three-plus-one claim gate | `python3 script/paper_core_claim_gate.py` reads tracked R361/R364/R370/R373/R374 artifacts plus current Chinese/English paper text and the evaluation ledger, emits explicit claim decisions, and writes the English submodule table fragment; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R374/R375 terminology refresh | local | Overall `pass`; records E1 as scoped abstraction support, E2 as hidden-label profiler benchmark, E3 as profile-configuration actionability, and E4 only as offline replayability and scope control. The table uses paper-block terminology and keeps metric dominance, human utility, automatic boundary discovery, automatic patch selection, live overhead, and full ecosystem compatibility out of scope | `docs/visexp/out/paper-core-claim-gate-r375/` | done |
| R376 | RQ1/E1-RQ4/E4 three-plus-one organization guardrail | Paper three-plus-one organization gate | `python3 script/paper_three_plus_one_gate.py` reads current Chinese/English paper text, `docs/agentpprof-zh.md`, the evaluation ledger, and regenerated R374/R375 reports/tables; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R374/R375 terminology refresh plus R376 generator | local | Overall `pass`; 13/13 checks pass; verifies English/Chinese papers frame E1-E3 as three empirical profiling experiments and E4 as a replayability/scope-control block, result tables use `RQ / paper block`, generated R374/R375 tables and JSON contracts use `paper_block` / `paper_blocks`, R375 records the current R374 hash, the paper avoids old four-question framing, and the Chinese user doc no longer presents novelty as flamegraph-only | `docs/visexp/out/paper-three-plus-one-r376/` | done |
| R377 | Main profiling-claim evidence gate | Paper main-claim evidence packet | `python3 script/paper_main_claim_evidence_gate.py` reads tracked R320/R333/R334/R354/R355/R358/R366/R375/R376 artifacts plus current Chinese/English paper text and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R376 plus R377 generator | local | Overall `pass`; 12/12 checks pass; emits five claim-facet rows tying the paper's central profiling claim to hidden-label localization/ranking, lower flat inspection work, fixed-session fragmentation tradeoff, actionable profile-configuration insight, and mechanism isolation, while checking that these facets route back into the 3+1 paper structure instead of becoming additional experiments, requiring the English-paper submodule input to be committed and captured by the parent gitlink, and preserving counterpoints for metric dominance, fixed-session drilldown, automatic boundary discovery, automatic patch selection, human utility, and complete ecosystem compatibility | `docs/visexp/out/paper-main-claim-evidence-r377/` | done |
| R378 | RQ2/E2-RQ3/E3 main-body table-budget guardrail | Paper main-body table-budget cleanup | `python3 script/paper_main_body_table_budget_gate.py` reads R377, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R377 plus R378 presentation cleanup | local | Overall `pass`; table-heavy R363/R365/R373 support artifacts are demoted from main-body tables to prose/artifact-ledger material while the core E1-E4 result displays, R320 accuracy table, E2/E3 non-flamegraph figure, E3 actionability table, and E4 reproducibility tables remain; requires the English-paper submodule input to be clean and captured by the parent gitlink | `docs/visexp/out/paper-main-body-table-budget-r378/` | done |
| R379 | RQ2/E2-RQ3/E3 claim-flow guardrail | Paper RQ2/RQ3 claim-flow cleanup | `python3 script/paper_rq2_rq3_claim_flow_gate.py` reads R377/R378, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R378 plus R379 prose cleanup | local | Overall `pass`; verifies RQ2 opens with primary comparison, success criterion, flat/fixed-session baseline scope, and failure interpretation; verifies RQ3 opens with mechanism/actionability, hidden-label no-leakage, executable profile-spec patches, failure interpretation, and automatic-boundary/patch-selector non-claims; requires the English-paper submodule input to be clean and captured by the parent gitlink | `docs/visexp/out/paper-rq2-rq3-claim-flow-r379/` | done |
| R380 | RQ1/E1-RQ4/E4 experiment-block consolidation guardrail | Paper experiment-block consolidation | `python3 script/paper_experiment_block_consolidation_gate.py` reads R377/R378/R379, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R379 plus R380 prose consolidation | local | Overall `pass`; 14/14 checks pass; verifies the main paper remains three substantial empirical profiling experiments plus one replayability/scope-control block, support runs stay as provenance inside E1-E4, stale chronological R321-R329/R327-R328 implementation prose is removed, E3 mechanism/actionability prose is block-structured, R-run references are explicitly labeled as support/provenance, and non-claim boundaries remain visible | `docs/visexp/out/paper-experiment-block-consolidation-r380/` | done |
| R381 | RQ2/E2-RQ3/E3 diagnosis/actionability presentation guardrail | Paper E3 diagnosis rows | `python3 script/paper_diagnosis_card_gate.py` reads R365/R373/R380, current Chinese/English paper text, and the evaluation ledger; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R380 plus E3 diagnosis/actionability table update | local | Overall pass; 10/10 checks verify six task rows preserve localization signals, profile actions, verdicts with counterpoints, non-claims, and 3+1 paper structure while remaining paper integration rather than a new empirical result | `docs/visexp/out/paper-diagnosis-card-r381/` | done |
| R382 | RQ1/E1-RQ4/E4 canonical three-plus-one consistency guardrail | Canonical docs and paper organization wording | `python3 script/paper_canonical_three_plus_one_gate.py` reads R380/R381, current idea story, design, evaluation ledger, and Chinese/English paper text; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R381 plus canonical-doc wording cleanup | local | Overall pass; 8/8 checks verify canonical docs and paper drafts consistently present three empirical profiling experiments plus one replayability/scope-control block, without stale "four core experiments" or replayability-as-empirical-experiment wording | `docs/visexp/out/paper-canonical-three-plus-one-r382/` | done |
| R383 | RQ1/E1-RQ4/E4 canonical reviewer acceptance guardrail | Reviewer acceptance after R382 | `python3 script/paper_canonical_reviewer_acceptance_r383.py` records four read-only subagent ACCEPT verdicts and checks R380/R381/R382 plus current docs/papers; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R382 plus reviewer closure | local | Overall accepted; 4/4 reviewers ACCEPT, zero blocking issues, 11/11 checks pass, R382 still passes, canonical docs/papers retain three-plus-one wording, E4 remains replayability/scope-control not empirical accuracy, and R383 remains paper integration rather than a new empirical result | `docs/visexp/out/paper-canonical-reviewer-acceptance-r383/` | done |
| R393 | RQ1/E1-RQ4/E4 post-R392 reviewer acceptance guardrail | Post-R392 reviewer acceptance | `python3 script/paper_post_r392_reviewer_acceptance_r393.py` records four final read-only reviewer ACCEPT verdicts after the R392 E4 input-source replay update, including one resolved Chinese caption blocker, and checks R392/E4 scope, 3+1 organization, two-abstraction wording, and non-claim boundaries; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R392 and the R393 caption fix | local | Overall accepted; 4/4 final reviewers ACCEPT, 1 resolved blocker, 0 unresolved blockers, 12/12 checks pass, R392 remains E4 input-source replay scope rather than a new accuracy experiment, and the Chinese dataset caption now separates E1's 15 public labeled sources from RQ2's four oracle-rich hidden-label families | `docs/visexp/out/paper-post-r392-reviewer-acceptance-r393/` | done |
| R394 | RQ1/E1-RQ4/E4 two-abstraction documentation consistency guardrail | Two-abstraction documentation consistency | `python3 script/paper_two_abstraction_doc_gate.py` reads the Rust CLI wording, `agentpprof` README, English and Chinese user guides, idea story, design, evaluation ledger, and Chinese/English paper text; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after the Chinese guide field-derivation cleanup plus R394 generator/ledger sync | local | Overall pass; 12/12 checks verify operation and operation stack remain the only profiler abstractions, tagging/mapping/LLM tags/clustering are field derivation before stack folding, trace/session/span remain containers/fields/baselines, automatic-boundary/detector non-claims stay visible, the 3+1 paper structure remains intact, and the English submodule gitlink is clean | `docs/visexp/out/paper-two-abstraction-doc-r394/` | done |
| R395 | RQ1/E1-RQ4/E4 main claim and verdict alignment guardrail | Main claim and verdict alignment | `python3 script/paper_main_claim_verdict_alignment_r395.py` reads the idea story, evaluation ledger, Chinese/English paper text, and current R377/R380/R383/R391/R393/R394 gate outputs; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after the R380/R391 three-plus-one consolidation repair and R394 two-abstraction doc gate | local | Overall pass; 13/13 checks verify the central claim, C4 verdict, E1-E4 role split, fixed-session proxy wording, headline E2 numbers, actionability non-selector wording, E4 non-accuracy scope, two-abstraction boundary, and unsupported-claim exclusions remain aligned across canonical docs and both paper drafts | `docs/visexp/out/paper-main-claim-verdict-alignment-r395/` | done |
| R396 | RQ4/E4 paper build smoke and accessibility guardrail | Chinese/English paper build smoke | `python3 script/paper_build_smoke_r396.py` runs the English `make` build in a temporary submodule copy, runs two Chinese `xelatex` passes into a temporary output directory, checks generated PDFs and copied final logs, and records command logs; no dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R395 plus English figure `\Description`, paper build smoke harness, and Chinese LaTeX ignore cleanup | local | Overall pass; 7/7 checks verify all build commands exit zero, both temporary-build PDFs exist, English and Chinese final logs have no unresolved references/citations, the English ACM figure-description warning is absent, R395 still passes, and build inputs/outputs are tracked or intentionally dirty while generated | `docs/visexp/out/paper-build-smoke-r396/` | done |
| R397 | RQ1/E1-RQ4/E4 main-body anti-run-ledger guardrail | Main-body run-ledger suppression | `python3 script/paper_main_body_run_ledger_r397.py` reads the Chinese and English paper bodies, evaluation ledger, idea story, R395/R396 run results, and R405 English read-only gap audit; no dataset sync, creation, relabeling, profiler rerun, submodule edit, or human/agent analyst task | worktree after the Chinese paper display-path update and R405 read-only English gap audit | local | Overall pass; 13/13 checks verify both main papers have zero `R###` run-id mentions and zero internal checklist-style term hits, the writable Chinese paper preserves RQ1/E1--RQ4/E4, English is synced or covered by R405's read-only gap, E4 remains replayability/scope-control rather than a hidden-label accuracy experiment, R-numbered runs stay as ledger provenance, and R395/R396/R405 still pass | `docs/visexp/out/paper-main-body-run-ledger-r397/` | done |
| R398 | RQ1/E1-RQ4/E4 current three-plus-one organization guardrail | Current three-plus-one organization regression | `python3 script/paper_current_three_plus_one_gate_r398.py` reads the Chinese and English paper bodies, evaluation ledger, idea story, R395/R396/R397 run results, and R405 English read-only gap audit; no dataset sync, creation, relabeling, profiler rerun, submodule edit, or human/agent analyst task | worktree after R397 plus current read-only-English organization gate | local | Overall pass; 14/14 checks verify the writable Chinese paper has exactly four RQ/E subsections, E2 as the single hidden-label accuracy block, E3 as mechanism/actionability rather than a fifth experiment, E4 as replayability/scope-control rather than accuracy/human/ecosystem evidence, no main-body `R###` run IDs, no internal checklist-style terms, no paper-facing venue-readiness self-undercut wording, ledger run IDs as provenance, new-run role assignment inside E1-E4, main-display path visibility, idea-story anti-sprawl wording, and English synced or covered by R405's read-only gap | `docs/visexp/out/paper-current-three-plus-one-r398/` | done |
| R399 | RQ4/E4 tracked paper PDF freshness guardrail | Tracked PDF display-path freshness | `python3 script/paper_pdf_freshness_r399.py` reads tracked Chinese/English TeX sources and PDFs, runs `pdftotext` on committed PDFs, and checks R396/R398/R405 run results; no paper rebuild, dataset sync, creation, relabeling, profiler rerun, submodule edit, or human/agent analyst task | worktree after refreshing the Chinese tracked PDF and recording the English read-only gap through R405 | local | Overall pass; 9/9 checks verify `pdftotext` is available, tracked PDFs exist, PDF extraction succeeds, Chinese source display-path tokens are present, the committed Chinese PDF contains workload provenance, hidden-label fidelity/baseline-tradeoff, mechanism/actionability, and replay/cost display-path text, and English PDF/source drift is covered by R405's read-only gap rather than a submodule edit | `docs/visexp/out/paper-pdf-freshness-r399/` | done |
| R405 | Paper-integration guardrail | English paper experiment-gap audit | `python3 script/paper_english_experiment_gap_audit.py` reads the English submodule draft and outer evidence in read-only mode; no submodule edit, dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R404/R405 generator | local | Overall pass; 7/7 checks map the English draft to outer evidence, identify the 3+1 structure sync gap, preserve tagger/human/ecosystem future-work boundaries, keep operation/operation-stack as the only profiler abstractions, and scan 6 operation JSONL sources / 67,304 rows for free-text/oracle availability. | `docs/visexp/out/paper-english-experiment-gap-audit-r405/` | done |
| R406 | Paper-integration guardrail | English operation-stack induction sync packet | `python3 script/paper_english_induction_sync_audit.py` reads the dirty English submodule draft in read-only mode and existing R402/R403/R404 artifacts; no submodule edit, dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R404 operation-stack induction artifacts | local | Overall pass; 8/8 checks confirm R402/R403/R404 pass, the English submodule still lacks induced operation-stack evidence, the outer Chinese paper and ledger have the evidence, public JSON uses `operation_stack_induction`, and generated English snippets preserve non-claim boundaries | `docs/visexp/out/paper-english-induction-sync-r406/` | done |
| R407 | Paper-integration guardrail | Operation-stack induction paper display | `python3 script/paper_induction_display_r407.py` reads existing R402/R403/R404 artifacts and writes a claim-facing table for the Chinese paper; no dataset sync, creation, relabeling, profiler rerun, English submodule edit, or human/agent analyst task | worktree after R406 plus Chinese paper table input | local | Overall pass; 7/7 checks confirm R402/R403/R404/R406 pass, the table has exactly three claim-facing rows, each row carries a non-claim boundary, and the Chinese paper inputs the generated table fragment | `docs/visexp/out/paper-induction-display-r407/` | done |
| R408 | Paper-integration freshness guardrail | Chinese induction PDF freshness | `python3 script/paper_chinese_induction_pdf_freshness_r408.py` reads the tracked Chinese TeX/PDF and R407 display artifacts, extracts the PDF with `pdftotext`, and checks the reader-facing induction table text; no rebuild, dataset sync, creation, relabeling, profiler rerun, English submodule read, or human/agent analyst task | worktree after refreshing the Chinese tracked PDF and removing R-run wording from the induction table caption | local | Overall pass; 7/7 checks verify `pdftotext` extraction, R407 pass status, Chinese TeX table input, reader-facing table labels, PDF presence of E1/E2/E3 induction evidence and headline numbers, absence of R402/R403/R404/R407/R408 tokens from the PDF text, and no English submodule source dependency | `docs/visexp/out/paper-chinese-induction-pdf-r408/` | done |
| R409 | Paper-integration / collaboration guardrail | English submodule read-only policy | `python3 script/paper_submodule_readonly_policy_r409.py` reads git/submodule status, AGENTS/CLAUDE policy, canonical docs, and R397/R398/R399/R405 outputs; no submodule file read, submodule edit, paper rebuild, dataset sync, creation, relabeling, profiler rerun, or human/agent analyst task | worktree after R399/R408 plus canonical-doc read-only policy sync | local | Overall pass; 12/12 checks verify the requested worktree path, research/v2 branch, AGENTS/CLAUDE no-touch policy, no staged submodule changes, dirty submodule state recorded but not cleaned, R405 gap audit pass, R397/R398/R399 gap-aware behavior, canonical docs record read-only handling, and direct push is explicitly unsafe because ahead history contains a submodule gitlink update | `docs/visexp/out/paper-submodule-readonly-policy-r409/` | done |

R272 command:

```bash
python3 script/agent_trace_datasets.py sample weblinx-chat --limit 25 --offset 0

cargo run --manifest-path agentpprof/Cargo.toml -- \
  --project-root . \
  --project-name external-agent-traces \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-25.jsonl \
  --view files \
  --format folded \
  -o docs/visexp/out/external-agent-trace-weblinx-r272/weblinx.folded \
  --stack 'project,agent,dataset,task,session,phase,op,action,target,status' \
  --stack-rule 'task:authenticate=(target=login|target=email|action=type)' \
  --stack-rule 'task:navigate=(action=click|action=load|action=say)' \
  --stack-rule 'phase:select=(action=click)' \
  --stack-rule 'phase:input=(action=type)' \
  --stack-rule 'phase:open=(action=load)' \
  --stack-rule 'phase:dialogue=(action=say)'
```

## Result Summary

Historical status: these are candidate/development results pending protocol
reconstruction; retain their provenance and negative rows, but do not promote
their old supported wording.

| Run | Result | Interpretation | Limitations |
|---|---|---|---|
| R272 | 25 WebLINX gold action operations produced 18 folded stacks with no prompt frame. Output: `docs/visexp/out/external-agent-trace-weblinx-r272/weblinx.folded`. | Confirms third-party labeled trajectories can enter as operation JSONL and use arbitrary recursive operation stacks. | Small sample; action-type rules only; no boundary adequacy metric yet. |
| R273 | 5 external datasets produced 3,748 operations and 100 folded stacks under `--view operations`; compression ratio 37.48. Outputs: `cross-dataset.folded`, `stack-analysis.json`, `stack-analysis.html`. | Confirms the same operation/operation-stack path works across web navigation, shopping, API calls, GUI replay, and software-engineering commands. | API-Bank is limited to first rows via Dataset Viewer; no Mind2Web/AndroidControl/ToolBench full converters yet. |
| R274 | 6 external datasets produced 3,797 operations and 103 folded stacks under `--view operations`; compression ratio 36.864. Outputs: `mapped.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Confirms `--op-map` derives reusable task/phase operation fields before `--stack` without adding a third abstraction or binding stacks to prompt/session boundaries. | Mind2Web sample is a small shard; mappings are deterministic and hand-written. |
| R277 | On the same 3,797 operations, flat stack produced 103 unique stacks, fixed session/demo stack produced 1,083 unique stacks, and mapped stack produced 103 unique stacks with added task/phase frames. | Directly tests the prompt/session-boundary objection: fixed boundaries fragment aggregation by 10.5x, while mapped operation stacks keep aggregation and add semantic depth. | Boundary adequacy is still structural/compression-based; no gold span scorer yet. |
| R278 | 8 external datasets produced 3,932 operations and 190 folded stacks; compression ratio 20.695. Outputs: `expanded.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Adds mobile UI and tool/API traces without changing the profiler abstraction; ToolBench intentionally increases stack diversity through long-tail API names. | AndroidControl is only a 2-episode smoke because row download includes screenshot payloads; ToolBench uses an HF mirror for lightweight sampling. |
| R279 | 9 external datasets produced 13,265 operations and 455 folded stacks; compression ratio 29.154. Outputs: `scaled.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Scaling GUI-Odyssey, ToolBench, and Mind2Web preserves aggregation and broadens the claim to cross-app mobile, web, software, and API/tool traces. | Still deterministic mapping; GUI-Odyssey dominates operation count and should be balanced in final figures. |
| R280 | On R279 operations, mapped fields have 100% coverage for stack fields; phase/action V-measure is 0.765; phase/action boundary precision is 1.0, recall 0.6862, F1 0.8139; task/dataset V-measure is 0.862. | First reusable quality scorer for operation-stack adequacy beyond flamegraphs. It shows deterministic mappings are conservative: they avoid false positive action-boundary changes but miss some fine-grained action changes. | Action labels are a proxy oracle for phase boundaries; deeper task/subtask adequacy still needs step-instruction or solution-path scoring. |
| R281 | `script/operation_map_infer.py` inferred 10 operation-field mapping rules from the 13,265 labeled operations. The resulting `learned.folded` is byte-identical to R279's hand-mapped `scaled.folded`; quality metrics reproduce R280: phase/action V-measure 0.765 and boundary F1 0.8139. | Confirms rule files can be generated from dataset labels and consumed by the same operation/operation-stack path; mapping rules are no longer tied to ad hoc CLI invocations. | This is a seeded deterministic taxonomy over observed labels, not a full unsupervised boundary detector. Held-out split validation is still required before a stronger C3 claim. |
| R282 | A deterministic group split produced 9,275 train operations and 3,990 held-out test operations across all 9 datasets. Train-only rules produce 209 held-out stacks (compression 19.091), versus 284 no-map stacks (compression 14.049). Held-out task/dataset V-measure improves from 0.8374 no-map to 0.8531 mapped; phase/action boundary F1 is 0.7774 mapped versus 0.9677 no-map because no-map leaves `phase` nearly identical to the fine-grained action label. | Shows generated mappings generalize across held-out sessions and improve semantic aggregation on unseen trajectories. It also clarifies the intended tradeoff: operation stacks deliberately coarsen low-level actions into reusable task/phase frames, so action-boundary F1 is not the only success metric. | Still not leave-dataset-out or unsupervised; action labels remain a proxy for phase boundaries. Need step-instruction and solution-path scoring for deeper recursive adequacy. |
| R283 | Leave-dataset-out with the R279-compatible stack (`...phase,op,tool,action,status`) is mostly neutral: only Mind2Web reduces unique stacks (9 to 3); aggregate summary reports 1/9 positive stack-reduction datasets, 0 negative. | This is an important stack-shape ablation: when raw `action` remains a leaf frame, phase/task mappings can improve interpretability without changing the number of folded stacks. It validates that users can preserve low-level action detail when they want exact action drilldown. | This view underestimates semantic aggregation because action labels still fragment stacks below the mapped phase. |
| R284 | Leave-dataset-out with semantic stack (`project,dataset,task,phase,op,tool,status`) reduces unique stacks on 6/9 datasets: AgentTrek 9→7, AndroidControl 5→3, GUI-Odyssey 6→5, Mind2Web 9→3, SWE-agent 20→16, WebLINX 7→6. ToolBench regresses 173→179, API-Bank regresses 1→3, WebShop is neutral at 119. | Shows the same operation sequence can be folded at a different semantic depth by changing only `--stack`. It also surfaces where the current mapping taxonomy is weak: API and ToolBench need a tool/API-family layer rather than action-verb phase rules. | Still deterministic and taxonomy-seeded; leave-family-out and deeper step/solution-path oracles remain open. |
| R285 | Re-running the R284 semantic stack after API/tool phase precedence removes all negative leave-out regressions. Aggregate summary: 6/9 positive stack-reduction datasets, 0 negative, weighted stack reduction 1162.005 per 1k operations. Mapped phase/action V-measure is above 0.7 on 7/9 held-out datasets, ranging from AndroidControl 0.7157 to Mind2Web and WebShop expert 1.0; API-Bank is 0.0 and ToolBench is 0.1342. API-Bank is neutral at 1→1 and ToolBench is neutral at 173→173; the six positive datasets remain AgentTrek, AndroidControl, GUI-Odyssey, Mind2Web, SWE-agent, and WebLINX. | Confirms that phase mapping must respect operation-family boundaries before action verbs. Tool/API traces are still operations, but their phase should be derived from tool/API structure rather than lexical verbs like `search`, `show`, or `create`. | This is still deterministic taxonomy-seeded mapping. It validates the two-abstraction design path, not unsupervised discovery; deeper task/subtask adequacy and leave-family-out validation remain open. |
| R286 | A recursive stack-depth sweep over the same 13,265 operations produced 9 dataset stacks, 11 task stacks, 57 phase stacks, 57 op stacks, 226 tool stacks, 226 semantic stacks, 455 action stacks, and 3,757 fixed-session stacks. Phase/action V-measure is 0.7638 and phase/action boundary F1 is 0.8095 under the shared R286 mapping. | Directly validates the design requirement that operation stacks are user-selected recursive projections rather than fixed prompt/session boundaries. Adding `session` causes an 8.26x expansion relative to action depth and 417.44x relative to dataset depth, which explains why session should be optional drilldown, not the default abstraction. | This is a stack-shape and boundary-proxy result; it does not yet prove unsupervised boundary discovery or deeper step-instruction/solution-path adequacy. |
| R287 | tau-bench adds 50 multi-turn tool-agent-user episodes and 1,560 operations: 414 user prompt ops, 364 assistant LLM response ops, 391 tool-call ops, and 391 tool-observation ops. The tau-only stack produces 68 unique stacks and compression 22.941; phase/action V-measure is 0.7868 and phase/action boundary F1 is 0.699 with precision 1.0. Combined with R279, the 10-dataset smoke covers 14,825 operations and 509 stacks; tau-bench becomes the third-largest source by operation count. | Confirms the same operation/operation-stack path handles dialogue, tool calls, and tool observations without adding a new abstraction. tau-bench is a stronger future oracle than ToolBench for user-agent-tool phase analysis because it includes outcomes and expected task actions. | Current run samples one model file (`gpt-4o-mini.jsonl`) and 50 episodes; larger multi-model tau-bench runs and outcome-specific analysis remain pending. |
| R288 | AgentRewardBench adds 38 expert-reviewed web-agent trajectories and 729 operations across assistantbench, visualwebarena, webarena, and workarena. The AgentRewardBench-only diagnostic stack produces 147 unique stacks after adding `repeat_signal`; phase/action V-measure is 0.784 and phase/action boundary F1 is 0.9236 with precision 1.0. Action-derived `repeat_signal` improves looping alignment to V-measure 0.3777, versus 0.0105 for single-step `step_error`. The 11-dataset combined smoke covers 15,554 operations and 561 stacks; task/dataset V-measure is 0.8593 and phase/action V-measure is 0.7791. | Confirms expert trajectory-quality labels can be carried as operation fields and folded recursively without a new failure/label abstraction. It also adds a non-flamegraph diagnostic target: success, side-effect, looping, optimality, and action-derived repetition can be projected as stack frames or scored in HTML/JSON reports. | The sample is intentionally lightweight because cleaned BrowserGym JSON files are large. `repeat_signal` is a useful sequence-level proxy for looping but still imperfect, and benchmark alone only weakly predicts side effects; final claims need stronger repeated-action/side-effect mappings. |
| R289 | SATraj-OS adds 250 desktop computer-use safety trajectories and 4,285 operations across account, induced-text, OS, popup, and unknown-file attack categories. The SATraj-only diagnostic stack produces 147 unique stacks and compression 29.150; desktop phases are `navigate` 3,380, `input` 838, `finish` 36, `observe` 28, and `computer-action` 3. Phase/action V-measure is 0.6697 and boundary F1 is 0.6274 with precision 1.0. The 12-dataset combined smoke covers 19,839 operations and 708 stacks; task/dataset V-measure is 0.9041 and phase/action V-measure is 0.7170. | Confirms desktop computer-use actions fit the same operation/operation-stack path and do not require prompt-, GUI-, or safety-specific abstractions. It also catches a real mapping bug: generic web `action=type -> phase=modify` must not override desktop `type/key -> phase=input`, so operation-family rules need precedence before generic action verbs. | The run samples the readable `safety` config only; the SATraj `capability` config was not fully accessible through Dataset Viewer rows. Safety and attack labels are useful diagnostic frames, but they are outcome/context labels, not strong phase-boundary oracles. |
| R290 | OSWorld-Human adds all 369 human reference desktop tasks and 6,010 single-action operations. The converter validates grouped-action labels against the single-action sequence: 320 tasks / 4,011 operations / 2,075 groups are exact-aligned and receive `human_group` oracle fields, while 31 content-mismatch and 18 length-mismatch tasks are kept for action profiling but excluded from grouped-boundary scoring. The action-depth stack produces 482 unique stacks and compression 12.469; the grouped-depth stack produces 106 unique stacks and compression 56.698. OSWorld-only phase/action V-measure is 0.5858, phase/action boundary F1 is 0.6383 with precision 1.0, and exact-aligned `group_pattern` versus `human_group` boundary F1 is 0.6268 with precision 1.0 and recall 0.4564. The 13-dataset combined smoke covers 25,849 operations and 1,035 stacks; task/dataset V-measure is 0.8463 and phase/action V-measure is 0.6791. | Confirms human desktop trajectories with two action granularities fit the same operation/operation-stack path. The result directly exercises the user's design requirement: a single prompt/action sequence can be folded at different depths by selecting frames such as `phase`, `action`, `human_group`, or `group_pattern`; none of these become new profiler abstractions. It also adds non-flamegraph HTML/JSON tree, transition, top-field, quality, skipped-oracle-pair, and grouped-stack reports. | The grouped-action labels are used only as evaluation fields and stack frames, not as training data. `group_pattern` is deliberately conservative, so it avoids false positive grouped-boundary changes but misses many human group transitions. This is still deterministic mapping/tagging, not unsupervised boundary discovery. |
| R291 | AgentNet adds 1,000 human-annotated Ubuntu desktop tasks and 16,741 PyAutoGUI operations. The AgentNet-only stack produces 608 unique stacks and compression 27.535; phases are `navigate` 13,219, `input` 2,414, `finish` 1,001, and `observe` 107. Step labels have full operation coverage: `step_correct` is 13,844 correct / 874 incorrect / 2,023 unknown, and `step_redundant` is 9,334 necessary / 733 redundant / 6,674 unknown. AgentNet-only phase/action V-measure is 0.6735 and phase/action boundary F1 is 0.7149 with precision 1.0. The 14-dataset combined smoke covers 42,590 operations and 1,497 stacks; task/dataset V-measure is 0.7508 and phase/action V-measure is 0.6628. | Confirms a much larger human desktop corpus fits the same two-abstraction path. Task outcome, alignment score, efficiency score, difficulty, step correctness, redundancy, and action-derived repetition are all plain operation fields: they can be folded into a stack, scored in HTML/JSON reports, or omitted without changing profiler semantics. It also validates a streaming access path that samples public HF JSONL without syncing the full source file. | This run samples the first 1,000 Ubuntu rows only, not the full Windows/macOS/Ubuntu corpus. Step correctness and redundancy are quality diagnostics, not task-boundary labels: task `status` weakly predicts per-step correctness, so final boundary claims still need stronger subtask/span oracles. |
| R292 | ScaleCUA adds a supplemental 5,000-row Ubuntu navigation sample with 131 sessions and max observed step 48. The ScaleCUA-only stack produces 6 unique stacks and compression 833.333; phases are `navigate` 4,086 and `finish` 914, and `history_state` is `with-history` for 4,085 operations and `start` for 915 operations. The 15-dataset combined supplemental smoke covers 47,590 operations, 1,611 unique stacks, compression 29.541, and phase/action boundary F1 0.8039 with precision 1.0. | Confirms public HF annotation JSONL can be streamed without saving the full source JSONL or images, and that previous-operation context can be represented as ordinary `history_state`/`history_depth` fields. It is useful for the paper's data-source suitability discussion. | This is not a strong boundary oracle because the sampled subset is mostly click/terminate and therefore has trivial phase/action alignment. It should not displace OSWorld-Human or AgentNet in the main evidence story. |
| R293 | A tracked profile spec over the existing R291 AgentNet operations reproduces the original 608-stack diagnostic folded output byte-for-byte and reports 16,741 samples. A CLI override on the same spec changes only the stack to `project,dataset,task,phase,action,status,step_correct,repeat_signal`, yielding 83 unique stacks over the same 16,741 operations. | Confirms reproducibility and customizability are now first-class in the Rust CLI: reviewers can replay operation files, op-map files, views, stack specs, and outputs from a single config while still overriding the query at the command line. This supports the paper's "like jq flags/config, not fixed prompt/session hierarchy" design point without adding a third abstraction. | This is a reproducibility and interface result, not new dataset evidence or a boundary-detector result. It does not strengthen unsupervised C3 beyond the existing deterministic mapping evidence. |
| R294 | A public Codex fixture exports to `agentsight.agent-session.trace.v1` with 1 session. `script/agent_trace_to_operations.py` converts the trace to 6 operation JSONL rows. Direct `agentpprof --trace-file` import and converted `agentpprof --operation-file` import both produce 6 samples, 5 unique stacks, and byte-identical folded output under `project,agent,op,phase,tool,status`. | Confirms local agent-native sessions can be exchanged, replayed, and bridged into the same operation JSONL path used by public benchmark traces. This answers the implementation concern that native sessions and external operations were separate paths. | This is a fixture-level interoperability smoke, not a large-scale dataset result. It does not evaluate boundary quality or failure diagnosis. |
| R303 | `script/agent_trace_exchange_eval.py` replays the R294 bridge end-to-end from one command: export a public Codex session to `agentsight.agent-session.trace.v1`, check that the trace has trace-local paths and command-name-only tool commands, convert the trace to operation JSONL, run direct trace import and converted operation import, and compare folded files. The scripted run again reports 1 session, 6 operations, 6 samples / 5 stacks on both paths, `trace_filesystem_portable=true`, and `folded_outputs_identical=true`. | Converts the trace-exchange idea into a reproducible artifact instead of a remembered shell sequence. It keeps agent-session as a portable exchange trace and keeps profiling in the operation/operation-stack path. The portability check covers filesystem fields and tool command text, not prompt/LLM preview redaction. | This is still an interoperability/reproducibility check, not new dataset evidence or user-facing value evidence. |
| R306 | `script/agent_trace_chrome_exchange_eval.py` adds a Chrome Trace Event JSON bridge on the same public Codex fixture, and `script/agent_trace_convert.py` exposes the reusable commands: `export-standard --format chrome`, `import-standard --format chrome`, and `to-operations`. The fixture exports 1 `agent-session` trace, writes 6 Chrome complete events, imports them back to 6 operation JSONL rows, and profiles direct trace, direct operation, and Chrome-import operation paths under `project,agent,op,phase,tool,status`. All three folded outputs report 6 samples / 5 stacks and are byte-identical. | Answers the standard-trace interoperability concern without changing the profiler model: Chrome/Perfetto trace JSON is a container for exchange and visualization, while imported data still becomes operation JSONL before operation-stack folding. | This is a fixture-level exchange smoke. It does not imply all OpenTelemetry/Chrome trace producers map perfectly, and it does not evaluate boundary quality or user utility. |
| R295 | `script/paper_claim_synthesis.py` reads tracked R282-R294 JSON/folded artifacts and emits `claim-synthesis.json` plus `claim-synthesis.md`. Verdicts: C1 supported for heterogeneous public trajectories and local session exchange; C2 supported with scoped limits for recursive task/phase/action/human-group/safety/quality views; C3 partial for deterministic label-derived mapping only. It also records unsupported final claims: unsupervised latent intent discovery, human productivity improvement, and complete full-scale conversion of every public dataset. | Converts scattered results into a paper-claim gate with explicit source paths and negative evidence. This is the strongest current bridge from experiment artifacts to OSDI/NeurIPS-style claim wording. | It is a synthesis artifact, not new empirical evidence. The underlying limitations remain: no unsupervised boundary backend, no user study, and no full-scale conversion of every candidate corpus. |
| R296 | `script/reviewer_evidence_packet.py` reads 39 tracked/clean artifacts from R282-R295 and emits `reviewer-evidence.json`, `reviewer-evidence.md`, and `index.html`. The packet records 11 visualization/catalog entries, 4 reviewer questions, and derived metrics: held-out mapping reduces unique stacks by 26.408%, OSWorld grouped stacks reduce action-depth unique stacks by 78.008%, AgentRewardBench repeat-signal/looping V-measure is 0.3777 vs 0.0105 for the step-error baseline (35.971x), and profile-spec override reduces AgentNet stacks by 86.349% without changing operations. | Gives reviewers one auditable path from claim to artifact and indexes evidence beyond flamegraphs: depth sweeps, stack trees, transition/top-field reports, quality reports, grouped-boundary reports, history-depth reports, and claim gates. | It is a navigation and synthesis layer, not new empirical evidence. It improves paper auditability but does not remove the need for a non-rule boundary backend or user-utility study. |
| R297 | `script/operation_boundary_backend_eval.py` trains a Bernoulli adjacent-boundary backend on non-oracle OSWorld-Human operation fields, excluding `human_group`, `group_index`, `group_position`, `group_size`, `group_pattern`, and `group_alignment` from model features. On 96 held-out exact-aligned sessions / 1,036 adjacent pairs, the learned backend reaches precision 0.7400, recall 0.8102, and F1 0.7735. Baselines on the same held-out pairs are phase-change F1 0.2919, action-change F1 0.5142, target-change F1 0.4086, always-boundary F1 0.7090, and conservative `group_pattern` reference F1 0.5810 at precision 1.0. The script writes `learned_group_pattern` and `learned_group_position` fields back into 1,132 held-out operations; Rust `agentpprof --profile-spec` folds them into 74 stacks and `operation_stack_analysis.py` emits a tree/transition report. | Moves C3 beyond hand-written regex mapping into a supervised boundary-backend expansion probe while preserving the two-abstraction contract: the backend only derives operation fields, and the existing Rust operation-stack path performs folding. It also shows the precision/recall tradeoff that a stronger boundary detector must manage. | This is supervised label-derived boundary prediction on one dataset family, not unsupervised intent discovery and not a general boundary detector. It needs leave-family-out validation, calibration, and AgentNet/tau-bench replication before C3 can become a final supported claim. |
| R298 | `script/paper_value_novelty_synthesis.py` reads R295, R296, R297, and diagnostic quality artifacts, then emits `value-novelty-synthesis.json`, Markdown, and HTML. It maps six real reviewer problems to evidence: heterogeneous trace object models, recursive depth choice, field derivation, human/subtask boundaries, failure/safety/quality diagnostics, and artifact auditability. It also records four novelty claims: two-object agent profiling, query-time recursive stacks, unified field derivation, and non-flamegraph diagnostic views. | Converts result interpretation into a mechanical paper-value gate. It supports the paper's central novelty/value wording while preserving limits: mechanism and diagnostic value are supported, but unsupervised intent discovery and developer productivity are not. | It is a synthesis/audit artifact, not a new dataset or user study. It labels the current evaluation as level-3 conference-paper evidence approaching level 4 for mechanism claims, and explicitly keeps boundary-family replication, user-utility study, and boundary calibration as remaining gaps. |
| R299 | `script/boundary_family_calibration_eval.py` evaluates 7 existing candidate boundary oracles without syncing new data. Four candidates pass suitability and positive-split gates: OSWorld-Human `human_group`, AgentNet `step_correct`, AgentNet `step_redundant`, and AgentRewardBench `looping`. Held-out learned F1 scores are 0.6916, 0.3197, 0.3361, and 0.7833 respectively. AgentNet quality-state boundaries beat always-boundary baselines (0.2155 and 0.2645) but have low precision and nontrivial calibration error. AgentRewardBench looping is better explained by `repeat_signal_change`, whose baseline F1 is 1.0. SATraj safety has no within-session adjacent boundaries, ScaleCUA history state is a context marker rather than semantic boundary, and tau-bench lacks tracked operation JSONL in R287. | Turns the R298 level-4 gap into a falsifiable boundary-family calibration result. It shows the backend interface generalizes, but the boundary claim does not become universal: each target family needs suitability checks, calibrated models, and comparison against simple derived-field baselines. | This is still supervised field derivation on sampled tracked operation JSONL. It does not prove unsupervised intent discovery, a single cross-family model, or a usable tool-dialogue boundary detector. |
| R300 | `script/operation_query_utility_eval.py` builds 6 oracle-backed analysis tasks without fetching data: AgentRewardBench looping and side-effect, SATraj unsafe operations, AgentNet incorrect and redundant steps, and OSWorld-Human group starts. The task set contains 34,539 operations. Under Rust `agentpprof --profile-spec`, flat has 6 stacks, fixed-session has 2,012 stacks, semantic operation-stack has 944 stacks, and label-drilldown has 318 stacks. Semantic operation stacks improve median top-positive lift over flat by 5.726x and reduce the median operation fraction needed to cover 50% positives to 0.2879. Compared with fixed-session stacks, semantic stacks use 0.554x as many groups and top groups cover 5.5x more sessions, but fixed-session stacks have lower oracle-sorted inspection fraction on some instance-local tasks. | Adds the first automated real-problem utility proxy. It turns failure/safety/quality/boundary labels into reviewer-auditable analysis tasks and quantifies the tradeoff between flat summaries, fixed-session drilldown, semantic operation stacks, and label-drilldown views. | This is not a human study. The ranking is oracle-sorted clustering quality, so it supports inspectability and aggregation claims, not developer productivity or online anomaly detection. |
| R301 | `script/operation_analyst_task_eval.py` reuses the same 6 labeled tasks and writes visible task packets plus a hidden answer key. Unlike R300, the visible ranking is width-only: groups are sorted by operation count, not by oracle positive rate. At a 30% operation-inspection budget, operation-stack median recall is 0.336 over 4.5 groups, while fixed-session recall is 0.284 over 25.5 groups. At top-10 groups, operation-stack median recall is 0.641 versus fixed-session 0.195, but the operation-stack work fraction is larger. Flat summaries either inspect everything at top-10 groups or fit no group into the 30% budget. | Converts the utility proxy into a task packet that can be replayed by a human or agent analyst without leaking labels. It supports cross-session aggregation and fragmentation reduction under a label-hidden browsing policy. | Width ranking alone is not a detector and does not prove human productivity. Some safety/quality positives remain buried without learned or oracle-aware ranking, so the paper should claim inspectability support rather than end-user time savings. |
| R302 | `script/operation_analyst_ranking_eval.py` keeps R301's hidden-label discipline and compares four ranking policies over fixed-session and operation-stack groups: width, visible-risk, query-aware, and oracle upper bound. The non-oracle rankers read only visible fields such as status, repeat signal, phase, action, and environment, while explicitly excluding `looping`, `side_effect`, `safety`, `step_correct`, `step_redundant`, and group-position fields. Top-10 query-aware operation-stack groups inspect a median 0.116 operation fraction with lift 1.587, compared with width ranking's 0.671 fraction and lift 1.079. At a 30% operation budget, query-aware operation-stack recall is 0.390 versus width 0.340, while inspected groups rise from 4.5 to 39.5. | Adds a non-flamegraph analysis-policy result. It shows that the same operation stacks can be sorted by user/query intent to trade recall, precision, and inspection work without adding a third abstraction or reading oracle labels. | The rankers are hand-written heuristics, not learned detectors or human studies. The oracle upper bound shows remaining headroom, and the paper should frame R302 as configurable analysis policy evidence rather than anomaly-detection evidence. |
| R304 | `script/operation_case_study_eval.py` converts the R300/R302 task suite into reviewer-facing case packets. For each of the 6 tasks, it selects the top-5 query-aware operation-stack groups, writes a visible packet containing only ordinary operation fields, and writes a separate answer key with oracle positives. Across the 30 case groups, median inspected operation fraction is 0.0937, median positive recall is 0.188, and median positive lift is 1.6509. SATraj unsafe cases are especially concentrated, with 0.042 work fraction, 0.262 recall, and 6.238 lift; AgentNet quality cases have low recall but still lift above 1.98 on very small work fractions. | Turns the automated proxy into concrete case-study evidence that reviewers can inspect without seeing labels. It demonstrates non-flamegraph analysis surfaces over operation stacks, while preserving the two-object model and hidden-label discipline. | This is still an automated packet, not a human study or detector. Mixed task results should stay in the paper because they show where case packets are strong and where recall remains weak. |
| R305 | `script/operation_case_baseline_eval.py` applies the same top-5 query-aware case-packet policy to flat, fixed-session, and operation-stack views over the R300 task suite. Flat packets inspect all operations and recover all positives, which is complete but not selective. Fixed-session packets inspect median 0.0163 of operations with median recall 0.0226 and lift 1.6615. Operation-stack packets inspect median 0.0937 of operations with median recall 0.188 and lift 1.6509. Compared with fixed-session packets, operation-stack packets have median recall ratio 3.63 and lift ratio 1.268, but median inspected-work ratio 1.717. | Adds a direct baseline for the reviewer-facing case-packet evidence. It shows operation stacks are a useful middle view: much more selective than flat, less fragmented and higher-recall than fixed-session at the same top-k packet count, but not uniformly cheaper than fixed-session. | This is still a label-hidden automated proxy. It should be used to narrow the claim to inspectability tradeoffs, not to claim analyst productivity or automatic detection. |
| R307 | `script/paper_claim_readiness_synthesis.py` reads R295/R298, R303, and R300-R306 tracked artifacts and emits `paper-readiness-synthesis.json`, Markdown, and HTML. The refresh records 15 datasets / 47,590 operations for C1, R303 agent-session exchange equality, 6 analysis tasks / 34,539 operations for C4, R305 operation-stack case work 0.0937 with recall 0.188 and lift 1.6509, and R306 Chrome-trace exchange equality. Claim verdicts were C1 supported, C2 supported with scoped limits, C3 partial, and C4 supported as automated proxy only before R320. | Provides the historical paper claim gate after R300-R306. R320 supersedes its C4 next gate by adding a hidden-label profiler benchmark; controlled analyst study remains only for human productivity or time-to-answer claims. | This is a synthesis artifact, not new empirical evidence. It depends on the correctness and scope of the underlying R295/R298/R303/R300-R306 artifacts. |
| R308 | `script/operation_analyst_outcome_eval.py` scores first-evidence outcomes from the R305 visible case packets and hidden answer key without syncing data. It reports that operation-stack packets contain a positive group in 6/6 tasks and a >=1.5x high-lift group in 5/6 tasks. Fixed-session packets contain positives in 5/6 tasks and high-lift groups in 4/6 tasks. Flat packets contain positives in 6/6 tasks but no high-lift group because the flat packet is the whole task. Operation-stack median selected work is 0.0937 with recall 0.188 and median top-group lift 1.5739. | Moves the C4 value evidence one step closer to an analyst protocol: the same label-hidden packets can be scored by first positive evidence, first enriched group, and high-lift group coverage. It strengthens the inspectability claim while keeping fixed-session's cheaper first-positive work as a real counterpoint. | This is still an automated replay over hidden labels, not a human or agent analyst study. It does not prove accuracy, time-to-answer, automatic detection, or dominance over fixed-session on every metric. |
| R309 | `script/operation_problem_value_synthesis.py` synthesizes R298/R300/R302/R305/R308 into six problem cards over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human. The report records 34,539 task-operations, 3,699 positive operations, operation-stack high-lift coverage of 5/6 tasks, selected work/recall/top-lift of 0.0937 / 0.188 / 1.5739, and top-10 query-aware ranking work/lift of 0.1163 / 1.5867 versus width ranking's 0.6713 / 1.0795. | Converts the utility evidence into a reviewer-facing disaggregation by real problem: safety is a strong selective win, AgentNet quality gives high lift at low recall, looping is prevalent and lacks high-lift evidence, and side-effect/human-boundary tasks show ranking-depth sensitivity. It strengthens novelty/value framing without changing the two-abstraction profiler model. | This is a synthesis/disaggregation artifact over existing proxy results. It does not prove human accuracy, time-to-answer, automatic detection, or universal dominance over fixed-session drilldown. |
| R310 | `script/paper_evidence_matrix_synthesis.py` reads tracked, clean R307/R309 artifacts without syncing datasets and emits JSON, Markdown, CSV, TeX, and HTML evidence-matrix outputs. The matrix records 4 claims: C1, C2, and C4 are scoped paper-ready claims, while C3 remains partial. It carries forward the R309 problem-value suite of 4 datasets / 6 tasks / 34,539 operations / 3,699 positives, high-lift coverage of 5/6 tasks, operation-stack selectivity over flat on 6/6 tasks, higher selected recall than fixed-session on 5/6 tasks, and fixed-session lower selected work on 4/6 tasks. | Converts the current paper story into a table/audit artifact that the abstract, evaluation, and conclusion can cite directly. It keeps trace exchange, problem cards, and paper synthesis as evidence surfaces around the same two abstractions: operation and operation stack. | This is a synthesis/audit artifact, not a new empirical result. It does not change the C3 boundary-generalization gap or the C4 human-utility gap. |
| R311 | `script/paper_robustness_audit.py` reads tracked, clean R302/R305/R308/R309/R310 artifacts without syncing datasets and emits JSON, Markdown, CSV, TeX, and HTML reviewer-stress outputs. It records that operation-stack packets are more selective than flat on 6/6 tasks, expose positive groups in 6/6, expose high-lift evidence in 5/6, and beat fixed-session selected recall in 5/6, but beat fixed-session selected work in only 2/6. | Converts the strongest current C4 evidence into reviewer-facing pass/narrow/partial/fail stress tests. It directly supports the paper wording that operation stacks provide a useful inspectability tradeoff, while rejecting stronger claims of universal fixed-session dominance, automatic detection, or human productivity. | This is a synthesis/audit artifact over six task-level proxy checks. It is not a statistical generalization claim, not a human study, and not new empirical evidence. |
| R312 | `script/paper_submission_audit.py` reads tracked, clean R310/R311 artifacts, the current R320 profiler-accuracy report, and the current Chinese draft without syncing datasets or rerunning profilers. It emits JSON, Markdown, CSV, TeX, and HTML submission-audit outputs. It reports number alignment, two-abstraction boundary, must-not-claim guardrails, and paper structure as pass, with overall `scoped_claim_ready`, and marks C4 as `hidden_label_profiler_accuracy_ready`. | Converts the current draft into a claim-safety audit aligned with the R320 profiling-paper gate. It proves the paper wording no longer violates the two-abstraction boundary, C4 guardrails, run-id-density structure check, or human-utility/productivity guardrails. | This is a paper audit artifact, not a new empirical result. It uses R320 as the empirical profiler-accuracy gate; controlled analyst study is optional for human-utility wording. |
| R313 | `script/operation_view_frontier_eval.py` reads tracked, clean R300/R302/R305/R311 artifacts without syncing datasets or rerunning profilers. It emits JSON, Markdown, CSV, and HTML frontier outputs over 162 non-oracle view/ranker/budget points. Operation stacks are on the non-oracle Pareto frontier for 6/6 tasks, deliver the best lift on 4/6 tasks, and deliver the best recall under 30% inspected work on 4/6 tasks. Flat and fixed-session views also remain frontier counterpoints on 6/6 tasks. | Converts C4 from pairwise comparisons into a configurable analysis-surface result. It shows why the abstraction should expose view/ranker choices instead of hard-coding flat, fixed-session, or operation-stack as the single hierarchy. | This is a synthesis/audit artifact over existing task packets, not a human study or detector. It strengthens inspectability-tradeoff wording while explicitly rejecting single-view dominance. |
| R314 | `script/paper_related_work_audit.py` reads the current related-work ledger, Chinese draft, claim ledger, evaluation ledger, and tracked R313 frontier output without syncing datasets or rerunning profilers. It emits JSON, Markdown, CSV, and HTML related-work audit outputs. It checks coverage of classic flamegraphs/pprof, OpenTelemetry GenAI, OpenInference, LangSmith, Langfuse, Phoenix, AgentOps, and public labeled trajectory benchmarks. It also checks that fixed-session and trace-tree-shaped baselines are discussed conservatively, that R313 numbers stay aligned, and that trace ecosystem, human utility, single-view dominance, and universal-detector guardrails remain present. | Converts novelty and baseline grounding into a paper-facing audit. It makes the closest same-problem threats explicit: existing systems already trace LLM/tool/agent spans and runs, pprof already has sample tags and tag pseudo frames, and Perfetto already has SQL/derived trace analysis, so the paper's defensible claim must stay on agent-operation records, recursive multi-field operation-stack projection, public labeled trajectory evidence, and hidden-label localization scoring. | This is a related-work and claim-scope audit, not a new empirical result or product comparison. It does not prove OpenTelemetry/Phoenix/LangSmith/Langfuse/AgentOps interoperability, and it should not be used to claim feature parity with trace platforms or real span-tree superiority. |
| R315 | `script/analyst_study_protocol.py` reads tracked, clean R305 visible case packets and hidden answer key plus R305/R308/R313 summaries without syncing datasets or rerunning profilers. It emits a controlled analyst-study package: `study-protocol.json`, `visible-study-packets.json`, `hidden-scoring-key.json`, `assignment.csv`, Markdown, HTML, and `run-result.json`. The generated protocol has 6 tasks, 3 views, 24 participants, 144 trials, balanced task-view cells, and visible-packet leakage status `pass`. | Turns the remaining user-utility gate into an executable protocol over the existing label-hidden packets. It specifies response fields, randomization, hidden scoring, primary/secondary endpoints, and promotion criteria for comparing flat, fixed-session, and operation-stack views. | This is a ready-to-run study protocol, not a completed human or agent analyst study. It does not support developer productivity, time-to-answer, or accuracy-improvement claims until analysts complete the visible packets and the hidden answer key is scored. |
| R316 | `script/analyst_study_readout_eval.py` reads tracked, clean R315 study protocol, visible packets, hidden scoring key, and assignment without syncing datasets or rerunning profilers. It scores a fixed scripted analyst policy that selects the first top-k visible groups in each assigned packet, then uses the hidden key only for scoring. Top-3 operation-stack packets hit a positive group in 100.0% of assigned trials and a high-lift group in 83.3%, versus fixed-session 83.3% and 66.7%; flat hits positives in 100.0% but has 0.0% high-lift and 100.0% work. The task-paired median recall delta for operation-stack over fixed-session is 0.1333, with median work delta 0.0207. | Converts the ready-to-run protocol into a sensitivity readout: the assignment and hidden key can recover the same inspectability tradeoff under an oracle-blind visible-order policy. It strengthens the case that R315 is a meaningful controlled-study instrument before spending human/agent analyst effort. | This is not a human or agent analyst result. It does not support accuracy, time-to-answer, productivity, detector, or single-view-dominance claims; it only supports automated protocol-sensitivity wording. |
| R317 | `script/paper_real_problem_narrative.py` reads tracked, clean R309 problem cards, R313 view-frontier report, and R316 analyst-study readout without syncing datasets or rerunning profilers. It emits JSON, Markdown, CSV, HTML, and run-result outputs that classify six real-problem tasks by paper value, evidence pattern, safe wording, and counterpoint. The summary keeps the same 4 datasets / 6 tasks / 34,539 operations / 3,699 positives, records operation-stack frontier coverage 6/6, high-lift coverage 5/6, higher selected recall than fixed-session 5/6, lower work than fixed-session 2/6, and repeats the R316 top-3 positive/high-lift tradeoff. | Converts scattered task-level results into a claim-first paper narrative: safety is the strongest selective win, AgentNet quality is high-lift but low-recall, looping is prevalent rather than enriched, and side-effect/human-boundary tasks are ranking-depth sensitive. It labels mechanism claims as level-4 scoped systems narrative and C4 as level-3-plus automated proxy. | This is a synthesis artifact, not new empirical evidence, not a human/agent study, and not a detector. It should be used to strengthen paper explanation and reviewer navigation while preserving the human-utility and boundary-generalization gates. |
| R318 | `script/paper_reviewer_acceptance_audit.py` reads the current paper, claim setup, evaluation ledger, R312 submission audit, R314 related-work audit, and R317 real-problem narrative. It records four independent subagent reviewer verdicts: three initial ACCEPT results plus one NEEDS_CHANGES result that became ACCEPT after the artifact-log prose/table fixes. It also checks that the current paper contains a claim-centered result table, that the former artifact-log phrase is removed, that paper-ready wording is now prose guidance, and that R312/R314/R317 still pass. | Closes the requested independent reviewer loop for the current scoped paper update. It shows the reviewer concern was not about claim evidence but about paper presentation, and that the presentation fix was accepted without changing the two-abstraction or must-not-claim boundaries. | This is a review-closure artifact, not empirical evidence and not a human/agent analyst-task result. It does not remove the controlled analyst-study gap. |
| R319 | `script/implementation_consistency_audit.py` reads current Rust sources, docs, and the Chinese paper. It checks the Rust `--profile-spec` implementation, operation-stack-first CLI help/about wording, CLI override contract, operation predicates, standard trace import/export path, standard-trace CLI test, implementation-doc status, two-abstraction wording, guarded third-abstraction language, and remaining-gate wording. | Prevents the paper from drifting back into a mixed old/new implementation story. The audit confirms profile specs, CLI help, `--where` predicates, and standard trace exchange are implemented and documented as wrappers/query components/containers over operations and operation stacks, while the remaining gaps are real research gates. | This is a consistency audit, not a dataset run, not new empirical evidence, and not an analyst study. It does not support stronger trace-platform compatibility, automatic boundary detection, or human-utility claims. |
| R320 | `script/operation_profile_accuracy_eval.py` reads tracked, clean R288-R291/R300 operation JSONL without syncing or creating datasets. It scores 144 view/ranker policies over flat, fixed-session, dataset-native, raw-action, operation-stack, label-drilldown, width, visible-risk, query-aware, and oracle-upper policies. It emits JSON, Markdown, CSV, and HTML under `docs/visexp/out/operation-profile-accuracy-r320/`. | Converts C4 into the profiling-paper main result. Operation-stack query-aware top-5 groups inspect median 9.37% of operations versus 100% for flat summaries. Against fixed-session query-aware drilldown, operation stacks improve top-5 recall on 5/6 tasks and reduce median groups from 285.0 to 157.5. Query-aware ranking improves AP over width-only operation-stack ranking on 6/6 tasks, and task insights identify concrete stack/ranker tuning points. | This is an automated hidden-label profiler benchmark, not a human/agent analyst study. It supports localization/ranking fidelity with respect to dataset-provided hidden labels on the selected real labeled tasks, while preserving single-view, detector, and human-productivity guardrails. |
| R344 | `script/operation_metric_consistency_eval.py` reads tracked-clean R320 `policy-scores.csv` and `profile-accuracy-report.json` and compares the default operation-stack query-aware policy against flat, fixed-session, dataset-native, raw-action, and width-only operation-stack baselines across AP, nDCG, top-5 precision/recall/F1, 30% budget recall/F1, top-5 work, work-to-first-positive, and groups. | Prevents metric cherry-picking. It records 30 support verdicts, 16 counterpoints, and 4 mixed/weak verdicts across 50 baseline-metric comparisons. The supported wording is a localization/work/fragmentation tradeoff, while nDCG and coarse top-k recall remain explicit secondary/counterpoint metrics. | This is a metric audit over existing R320 scored outputs, not a new dataset run, not a new ranking policy, not a human/agent analyst study, and not evidence of universal dominance. |
| R321 | `script/operation_where_filter_eval.py` reads tracked R300 operation JSONL, writes `where_rules` profile specs, runs Rust `agentpprof --profile-spec`, and emits JSON, Markdown, CSV, folded outputs, profile specs, and HTML under `docs/visexp/out/operation-where-filter-r321/`. | Closes an implementation gap between the paper's `(predicate, stack, weight)` view model and the CLI: query predicates now run after mapping/tagging and before stack folding, so one operation source can produce multiple task-specific views without binding to prompt/session boundaries. | This is an implementation/reproducibility probe, not a new accuracy benchmark and not a new dataset. It supports C1/C2 configurability, while C4 accuracy remains grounded in R320. |
| R322 | `script/operation_rust_rank_rule_eval.py` reads tracked R300 operation JSONL, writes `rank_rules` profile specs, runs Rust `agentpprof --profile-spec`, and scores the Rust-emitted JSON ranking offline with hidden labels that are not passed to Rust ranking. It emits JSON, Markdown, CSV, profile specs, Rust JSON outputs, and HTML under `docs/visexp/out/operation-rust-rank-rule-r322/`. | Closes the next implementation gap between R320's analysis-policy story and the Rust profiler surface: JSON output now contains a complete visible-rule ordering over operation-stack groups. The probe shows AP improves over width on 4/6 tasks, top-5 recall on 2/6 tasks, and top-5 lift on 3/6 tasks. It also preserves negative evidence: SATraj safety and AgentRewardBench side-effect need richer group-level rankers than binary stack-text boosts. | This is an implementation and mechanism-isolation probe, not the main C4 benchmark, not a detector, not a human/agent analyst study, and not a new dataset. Rank rules read only visible stack fields (`action`, `environment`, `phase`, `repeat_signal`, `status`) and do not read hidden oracle labels. |
| R323 | `script/operation_rank_mode_eval.py` reads tracked R300 operation JSONL, writes paired `rank_mode=width-boost` and `rank_mode=rule-score` profile specs, runs Rust `agentpprof --profile-spec`, and scores both Rust-emitted JSON rankings offline with hidden labels that are not passed to Rust ranking. It emits JSON, Markdown, CSV, profile specs, Rust JSON outputs, and HTML under `docs/visexp/out/operation-rank-mode-r323/`. | Turns R322's width-dominance counterexample into a mechanism-isolation result. Score-first ranking improves AP over width-boost on 4/6 tasks, top-5 lift on 4/6 tasks, and first-positive work on 3/6 tasks; SATraj unsafe improves first-positive work from 0.6376 to 0.0842. Side-effect and OSWorld-Human remain negative evidence, so the paper should frame rank mode as an actionability knob, not a universal ranker. | This is an implementation and mechanism-isolation probe, not the main C4 benchmark, not a learned detector, not a human/agent analyst study, and not a new dataset. It uses the same visible fields as R322; hidden labels are not passed to Rust and are used only for offline scoring. |
| R324 | `script/operation_rank_feature_eval.py` reads tracked R300 operation JSONL, writes a scrubbed `visible-query-utility-operations.jsonl` without oracle fields for Rust, writes `rank_op_rules` profile specs for semantic and coarse stack depths, runs Rust `agentpprof --profile-spec`, and scores Rust-emitted JSON rankings offline with hidden labels that are not passed to Rust ranking. It emits JSON, Markdown, CSV, profile specs, Rust JSON outputs, the scrubbed profiler input, and HTML under `docs/visexp/out/operation-rank-feature-r324/`. | Closes more of the R320 query-aware implementation gap: Rust now aggregates visible operation-feature density inside folded operation-stack groups. On semantic stacks, AP improves over width on 5/6 tasks, top-5 lift on 4/6, and first-positive work on 5/6; on coarse stacks, AP improves on 4/6 and first-positive work on 5/6 while reducing group counts. SATraj gets the largest AP/work gain, while OSWorld-Human remains a boundary-field counterexample. | This is an implementation and mechanism-isolation probe, not the main C4 benchmark, not a learned detector, not a human/agent analyst study, and not a new dataset. `rank_op_rules` match individual visible `field=value` operation tokens after mapping/filtering; the profiler input has hidden fields removed, and hidden labels are not passed to Rust and are used only for offline scoring. |
| R325 | `script/operation_rank_feature_ablation_eval.py` reuses the R324 scrubbed visible-operation JSONL, writes profile specs for width, all-feature, and leave-one-feature-out policies over semantic and coarse stack depths, runs Rust `agentpprof --profile-spec`, and scores Rust-emitted rankings offline with hidden labels that are not passed to Rust ranking. It emits JSON, Markdown, CSV, profile specs, Rust JSON outputs, feature-finding tables, stack-depth tables, and HTML under `docs/visexp/out/operation-rank-feature-ablation-r325/`. | Turns R324 into actionability evidence. Leave-one-out finds 7 critical feature instances: `repeat_signal` drives AgentRewardBench looping, `write-action` drives side-effect localization, `status=success` unexpectedly drives SATraj safety ranking, and AgentNet redundancy has a first-positive-work-sensitive failure feature. It also finds 3 misleading feature instances: SATraj loop-like and OSWorld-Human input-phase rules can hurt AP or first-positive work. Coarse depth is AP-preferred on only 2/6 tasks while reducing groups on all 6, making stack depth an explicit cost/accuracy knob. | This is an implementation, mechanism-isolation, and actionability probe, not the main C4 benchmark, not a learned detector, not a human/agent analyst study, and not a new dataset. The ablation operates over hand-authored visible policies; hidden labels are not passed to Rust and are used only for offline scoring. |
| R326 | `script/operation_rank_feature_robustness_eval.py` reuses the R324 scrubbed visible-operation JSONL and the R325 ablation report, writes profile specs for width, task-weighted, task-equal, global-equal, and R325-guided repaired policies over semantic and coarse stack depths, runs Rust `agentpprof --profile-spec`, and scores Rust-emitted rankings offline with hidden labels that are not passed to Rust ranking. It emits `rank-feature-robustness-report.json`, `rank-feature-robustness-summary.csv`, `rank-feature-repair-findings.csv`, Markdown, HTML, 60 profile specs, and Rust JSON outputs under `docs/visexp/out/operation-rank-feature-robustness-r326/`. | Tests whether R324/R325 depend on brittle weight choices. A global equal-weight visible feature bank improves AP over width on 4/6 semantic and 5/6 coarse tasks, and improves semantic first-positive work on 4/6 tasks. Equal-weight task policies stay within 0.02 AP of the weighted task policies on 8/12 task/depth variants. R325-guided repaired policies improve AP on 2/3 misleading-feature cases and first-positive work on 2/3 cases; 1/3 improves both metrics. | This is an implementation, robustness, and post-hoc actionability probe, not the main C4 benchmark, not a learned detector, not a label-free deployment ranker, not a human/agent analyst study, and not a new dataset. Global/task-equal policies are visible and label-free at ranking time; the repaired policy uses R325 offline-scored findings and is therefore evidence that ablation can guide policy repair, not a deployment policy. |
| R342 | `script/operation_profile_spec_composition_eval.py` reads tracked-clean R324 report/CSV/profile specs/Rust JSON and writes JSON, Markdown, CSV, HTML, and run-result outputs under `docs/visexp/out/operation-profile-spec-composition-r342/`. It does not sync, create, or relabel datasets; it recomputes composition and stack-depth tradeoffs from existing real labeled outputs. | Verifies the concrete two-object composition story: all 12/12 profile-spec variants compose operation files, `where_rules`, `rank_op_rules`, `rank_mode=rule-score`, and explicit stack depth, and all 12/12 remain prompt/session-free. Visible operation-feature ranking improves AP over width on 9/12 variants and first-positive work on 10/12; coarse depth reduces groups on 6/6 tasks with median group reduction 0.8267, while best AP depth splits semantic 4 / coarse 2. | This is a reproducibility/mechanism audit over existing R324/R300 outputs, not a new main accuracy benchmark, not a human or agent analyst study, not automatic boundary discovery, and not a universal stack-depth selector. |

## Candidate Selection

| Rank | Dataset | Current judgment | Why |
|---|---|---|---|
| 1 | GUI-Odyssey | Keep as primary | Large cross-app mobile episodes, clean step/action labels, easy HF sampling, strong scale signal in R279. |
| 2 | AgentNet | Keep as primary desktop step-quality oracle | Large human desktop trajectories with task outcomes, step correctness, redundancy, and PyAutoGUI actions; R291 adds the largest human desktop operation sample in the harness. |
| 3 | WebShop expert | Keep as primary | Long expert trajectories, many operations per task, rewards, strong compression signal. |
| 4 | tau-bench trajectories | Keep as primary | Best current user-agent-tool dialogue source; has multi-turn messages, tool calls, observations, outcomes, and gold task actions. |
| 5 | AgentRewardBench | Keep as primary failure/quality oracle | Best current expert-labeled outcome, side-effect, looping, and optimality source; R288 shows it folds through the same operation-stack path. |
| 6 | OSWorld-Human | Keep as primary desktop grouped-boundary oracle | Human reference trajectories for all sampled OSWorld tasks, with both single-action and grouped-action annotations; R290 directly tests recursive folding depth on desktop actions. |
| 7 | SATraj-OS safety | Keep as primary desktop/safety oracle | Best current desktop safety/outcome source in the harness; R289 adds success, safety, reward, attack type, and OS action-family precedence evidence. |
| 8 | ToolBench | Keep as primary | Best current long-tail API source; R279 exposes API-domain stack diversity. |
| 9 | WebLINX chat | Keep as primary | Human/expert web demonstrations with clean action/demo/turn fields and multiple held-out splits. |
| 10 | Mind2Web | Keep as secondary primary | Strong cross-domain web oracle with task/domain/action labels; train_0 shard scales to 100 rows / 774 ops. |
| 11 | SWE-agent trajectories | Keep as domain bridge | Closest to coding-agent domain and has command/action trajectories plus success labels, but sampled rows are smaller than GUI/web sources. |
| 12 | AgentTrek | Keep as scale supplement | Large verified GUI/web trajectory source; useful for scale, but synthetic provenance weakens human-oracle claims. |
| 13 | AndroidControl | Keep as boundary oracle after heavier sampling | Step instructions provide a stronger subtask oracle than action type, but screenshot payloads make sampling heavier. |
| 14 | API-Bank | Keep as baseline | Good compact tool-call oracle, but mostly single-step and less useful for recursive boundary depth. |
| 15 | ScaleCUA | Keep as supplement | Public annotation JSONL streams cleanly and has multi-step GUI history context, but the sampled Ubuntu navigation subset is too action-narrow to be a main boundary oracle. |

## Metrics And Oracles

| Metric | Definition | Oracle | Claim |
|---|---|---|---|
| Operation coverage | Fraction of dataset rows converted to operation JSONL without dropping required action fields. | Dataset row count and converter warnings. | C1 |
| Operation mapping coverage | Fraction of operations receiving derived fields such as `task` and `phase` under `--op-map`. | `agentpprof` JSON summary plus stack-analysis top-kind counts. | C1, C2 |
| Stack compression ratio | Total operation weight divided by unique folded stacks. | `agentpprof` JSON summary or folded stack count. | C2 |
| Fixed-boundary expansion factor | Unique stacks under fixed demo/session boundaries divided by unique stacks under mapped operation stacks. | R277 ablation on identical operation JSONL. | C1, C2 |
| Boundary adequacy | Agreement between inferred task/subtask/phase frames and dataset labels such as demo id, action type, step instruction, or solution path. | Dataset-native labels; manual adjudication for ambiguous cases. | C2, C3 |
| Phase/action V-measure | Homogeneity/completeness between mapped phase labels and dataset action labels. | `operation_stack_quality.py --oracle-pair phase:action`. | C2 |
| Sequence boundary F1 | Precision/recall of mapped phase changes against action-label changes within each session. | `operation_stack_quality.py --boundary-pair phase:action`. | C2 |
| Tool-agent role alignment | Homogeneity/completeness between normalized operation kind and message role. | R287 `operation_stack_quality.py --oracle-pair op:role`. | C1, C2 |
| Trajectory-quality label coverage | Fraction of operations with expert `status`, `side_effect`, `looping`, and `optimality` labels. | R288 AgentRewardBench operation JSONL and `operation_stack_quality.py --coverage-field`. | C1, C2 |
| Failure/looping/side-effect diagnostics | Alignment between stack frames, sequence-derived repetition fields, and expert trajectory-quality labels. | R288 `operation_stack_quality.py --oracle-pair repeat_signal:looping --oracle-pair benchmark:side_effect`; `step_error:looping` is retained as a weak negative control. | C2 |
| Desktop safety/attack diagnostics | Coverage and stack distribution for `safety`, `attack_type`, `status`, `reward`, and `repeat_signal` fields. | R289 SATraj-OS operation JSONL and `operation_stack_quality.py --coverage-field safety --coverage-field attack_type`. | C1, C2 |
| Human grouped-action boundary F1 | Precision/recall of derived grouped-action frames against benchmark human `human_group` boundaries within each desktop task, restricted to tasks where `single-action` exactly matches flattened `grouped-action`. | R290 OSWorld-Human `operation_stack_quality.py --boundary-pair group_pattern:human_group` plus the grouped-depth folded stack; report `candidate_pairs` and `skipped_missing_fields` to make excluded non-exact rows visible. | C2 |
| Desktop step-quality diagnostics | Coverage and alignment for `step_correct`, `step_redundant`, task `status`, and action-derived `repeat_signal` fields. | R291 AgentNet operation JSONL and `operation_stack_quality.py --coverage-field step_correct --coverage-field step_redundant --oracle-pair status:step_correct --oracle-pair repeat_signal:step_redundant`. | C1, C2 |
| Operation-family precedence regression | Whether desktop/tool/API/web/mobile phase mappings are applied before generic action-verb mappings. | R285 API/tool leave-out fix, R289 SATraj `satraj-op-map.txt`, and R290 OSWorld-Human `osworld-op-map.txt` combined runs. | C1, C2 |
| Held-out mapping compression delta | Unique stack reduction and compression improvement when train-derived op-map rules are applied to unseen sessions. | R282 mapped vs no-map folded stacks on identical held-out operation JSONL. | C2, C3 |
| Leave-dataset-out stack reduction | Unique stack change when one full dataset is held out from mapping-rule generation. | R283/R284 mapped vs no-map folded stacks, one held-out dataset per fold. | C2, C3 |
| Recursive stack-depth expansion | Unique stack count and compression change as the same operations are folded with progressively deeper `--stack` specs. | R286 depth sweep over identical R279 operations and one R286 op-map. | C1, C2 |
| Abstraction ablation delta | Difference in compression and boundary adequacy between flat, fixed-boundary, and recursive stacks. | Same operation JSONL under different `--stack` configs. | C1, C2 |
| Transition concentration | Top weighted parent-child stack transitions from `operation_stack_analysis.py`. | Folded stack transition table. | C2 |
| Profile-spec reproducibility | Whether a tracked profile spec can replay operation-file, op-map, view, stack, output, and CLI override choices. | R293 `agentnet-diagnostic-spec.json`, result JSON, folded output comparison, and override folded output. | C1, C2 |
| Query-predicate reproducibility | Whether a tracked profile spec can replay operation-file, op-map, where predicate, stack, and output choices while selecting the expected operation subset. | R321 `where-filter-report.json`, `where-filter-summary.csv`, profile specs, folded outputs, and agentpprof result JSON generated from tracked R300 operation JSONL. | C1, C2 |
| Rust visible rank-rule reproducibility | Whether a tracked profile spec can replay operation-file, query predicate, stack, and visible rank policy choices while emitting a JSON ranked operation-stack group order that can be scored offline with hidden labels that are not passed to Rust ranking. | R322 `rust-rank-rule-report.json`, `rust-rank-rule-summary.csv`, profile specs, Rust JSON outputs, and HTML generated from tracked R300 operation JSONL. | C2, C4 |
| Rust rank-mode reproducibility | Whether the same visible rank rules can be replayed under different Rust rank modes to isolate width-dominated versus score-first policies over identical operation-stack groups. | R323 `rank-mode-report.json`, `rank-mode-summary.csv`, paired profile specs, Rust JSON outputs, and HTML generated from tracked R300 operation JSONL. | C2, C4 |
| Rust operation rank-feature reproducibility | Whether visible per-operation rank features can be aggregated inside folded stack groups and replayed from profile specs at semantic and coarse stack depths. | R324 `rank-feature-report.json`, `rank-feature-summary.csv`, paired stack-depth profile specs, scrubbed visible-operation profiler input, Rust JSON outputs, and HTML generated from tracked R300 operation JSONL. | C2, C4 |
| Rust operation rank-feature ablation | Whether each visible rank feature contributes to localization and whether stack-depth choices trade accuracy for fewer groups. | R325 `rank-feature-ablation-report.json`, `rank-feature-ablation-summary.csv`, `rank-feature-findings.csv`, `rank-feature-stack-depth.csv`, profile specs, Rust JSON outputs, and HTML generated from the R324 scrubbed visible-operation profiler input. | C2, C4 |
| Rust operation rank-feature robustness | Whether equal-weight and global visible rank policies preserve localization gains, and whether ablation-guided repairs can remove misleading features. | R326 `rank-feature-robustness-report.json`, `rank-feature-robustness-summary.csv`, `rank-feature-repair-findings.csv`, profile specs, Rust JSON outputs, and HTML generated from the R324 scrubbed visible-operation profiler input plus R325 findings. | C2, C4 |
| Profile-spec composition and stack-depth audit | Whether real-trace profile specs compose operation sources, predicates, visible per-operation rank rules, rank mode, and recursive stack depth without prompt/session boundaries, and whether depth choice trades localization accuracy for group count. | R342 `profile-spec-composition-report.json`, `profile-spec-composition-variants.csv`, `profile-spec-composition-tasks.csv`, Markdown, HTML, and run-result generated from tracked-clean R324 report/CSV/profile specs/Rust JSON. | C1, C2, C4 |
| Relocated-checkout artifact portability | Whether historical profile specs that contain absolute artifact paths remain replayable from a different checkout root without editing the source artifacts. | R343 `relocation-audit-report.json`, `relocation-checks.csv`, Markdown, HTML, and run-result generated from tracked R324/R342 artifacts. | C1, C2, C4 |
| Agent-session trace exchange equivalence | Whether exported native session traces can be imported directly and converted to operation JSONL without changing stack output. | R294 `fixture-trace.json`, `fixture-operations.jsonl`, `trace-import.folded`, `operation-import.folded`, and `cmp` equality; R303 `exchange-report.json` reproduces the same equality through `script/agent_trace_exchange_eval.py` and records `trace_filesystem_portable=true`. | C1 |
| Standard trace exchange equivalence | Whether a standard trace container can carry agent-session or normalized operation-file inputs and import back to operations without changing operation-stack output. | R306 `fixture-chrome-trace.json`, `fixture-chrome-operations.jsonl`, `trace-import.folded`, `direct-operation-import.folded`, `chrome-operation-import.folded`, and `chrome-exchange-report.json`; R353 `operation-prefix-chrome-trace.json`, `direct-operation.folded`, `standard-trace-import.folded`, and `standard-trace-exchange-report.json`. | C1 |
| Profile-spec input-source replay | Whether profile specs can replay local-session, imported agent-trace, and standard-trace input sources without silently ignoring configured paths, while keeping tags, predicates, rank rules, stack override, and standard-trace args inside the operation/operation-stack path. | R392 Rust regressions in `agentpprof/tests/profile_spec_cli.rs` and `agentpprof/tests/standard_trace_cli.rs`; effective `session_files`, `trace_files`, `standard_trace_files`, and `include_standard_trace_args` are reported by CLI status JSON. | C1, C2, E4 |
| Paper claim synthesis gate | Whether paper-ready claim wording is mechanically grounded in tracked artifacts and unsupported claims are explicitly excluded. | R295 `claim-synthesis.json`, `claim-synthesis.md`, and `run-result.json` generated from R282-R294 result JSON/folded artifacts. | C1, C2, C3 |
| Reviewer evidence packet | Whether the paper's main evidence can be audited through a single claim-to-artifact navigation layer that includes non-flamegraph views and negative evidence. | R296 `reviewer-evidence.json`, `reviewer-evidence.md`, and `index.html` generated from tracked/clean R282-R295 artifacts. | C1, C2, C3 |
| Supervised boundary-backend F1 | Held-out adjacent-pair precision/recall/F1 for learned operation-boundary fields against dataset-provided human-group labels. | R297 `boundary-backend-report.json`, learned operation JSONL, Rust folded output, and stack-analysis HTML/JSON. | C2, C3 |
| Paper value and novelty synthesis | Reviewer-facing mapping from real debugging/profiling problems to tracked evidence, novelty claims, must-not-claim limits, and remaining level-4 gaps. | R298 `value-novelty-synthesis.json`, Markdown, and HTML generated from R295-R297 plus R288/R289/R291 diagnostic artifacts. | C1, C2, C3 |
| Paper claim readiness refresh | Whether late utility/trace results change the paper-ready claim wording and next gate. | R307 `paper-readiness-synthesis.json`, Markdown, HTML, and run-result generated from tracked R295/R298, R303, and R300-R306 artifacts. | C1, C2, C3, C4 |
| Boundary-family calibration | Suitability, held-out F1/precision/recall, Brier/ECE calibration, and simple-baseline comparisons for adjacent-boundary backends across existing labeled operation families. | R299 `boundary-family-report.json`, augmented operation JSONL, Rust folded output, and stack-analysis HTML/JSON. | C2, C3 |
| Operation-query utility proxy | Oracle-sorted positive lift, operation fraction to cover 50% positives, group count, compression, and cross-session support for flat, fixed-session, semantic operation-stack, and label-drilldown views. | R300 `query-utility-report.json`, combined operation JSONL, four profile-spec Rust folded outputs, and operation-stack analysis HTML/JSON. | C2, C4 |
| Width-ranked analyst task proxy | Label-hidden top-k and operation-budget recall, lift, inspected work fraction, and inspected groups when groups are ranked by width only. | R301 `analyst-task-report.json`, `visible-task-packets.json`, `answer-key.json`, Markdown, and HTML. | C4 |
| Label-hidden ranking policy proxy | Top-k and operation-budget recall, lift, inspected work fraction, and inspected groups for width, visible-risk, query-aware, and oracle-upper-bound rankers. | R302 `ranking-report.json`, Markdown, and HTML. | C4 |
| Reviewer-facing case packet | Whether operation-stack groups can be shown as label-hidden cases with visible examples and a separate answer key. | R304 `visible-case-packet.json`, `answer-key.json`, `case-study-report.json`, Markdown, and HTML. | C4 |
| Cross-view case-packet baseline | Whether the same label-hidden case-packet policy behaves differently under flat, fixed-session, and operation-stack groupings. | R305 `visible-case-packets.json`, `answer-key.json`, `case-baseline-report.json`, Markdown, and HTML. | C4 |
| Analyst first-evidence proxy | Whether existing label-hidden packets expose positive and high-lift evidence early enough to motivate a controlled analyst study. | R308 `analyst-outcome-report.json`, Markdown, HTML, and run-result generated from tracked R305 visible packets and answer key. | C4 |
| Real-problem value cards | Whether the existing proxy results support problem-specific value conclusions and preserve counterexamples. | R309 `problem-value-report.json`, Markdown, HTML, and run-result generated from tracked R298/R300/R302/R305/R308 artifacts. | C4 |
| Operation-view Pareto frontier | Whether operation-stack, fixed-session, and flat views form a configurable tradeoff surface rather than one universally dominant hierarchy. | R313 `view-frontier-report.json`, Markdown, CSV, HTML, and run-result generated from tracked R300/R302/R305/R311 artifacts. | C4 |
| Label-scored profiler localization/ranking | Precision@k, recall@operation-budget, F1@k, AP/AUPRC-style ranking score, nDCG, work-to-first-positive, group fragmentation, and task-level actionability for profile groups treated as ranked localization outputs and scored against hidden labels after ranking. | R320 `profile-accuracy-report.json`, `policy-scores.csv`, `task-accuracy.csv`, `optimization-insights.csv`, Markdown, HTML, and run-result generated from tracked R288-R291/R300 operation JSONL. | C4 |
| Multi-metric consistency audit | Whether the R320 label-scored claim holds as a tradeoff across AP/AUPRC-style score, nDCG, precision/recall/F1@5, recall/F1 at 30% inspected work, work-to-first-positive, and group fragmentation rather than depending on a single metric. | R344 `metric-consistency-report.json`, `metric-summary.csv`, `task-metric-deltas.csv`, Markdown, HTML, and run-result generated from tracked R320 policy scores and report. | C4 |
| Diagnostic-lens portfolio | Whether the profiler evidence identifies which analysis lens and view should be used for each real labeled task; this is not a universal selector and should not collapse actionability into one flamegraph. | R345 `diagnostic-lens-report.json`, `diagnostic-lens-summary.csv`, `task-lens-cards.csv`, `counterpoint-ledger.csv`, Markdown, HTML, and run-result generated from tracked R335/R341/R344 artifacts. | C4 |
| Diagnostic casebook | Whether top-ranked operation-stack groups can be inspected as concrete label-scored cases and connected to diagnostic lenses, optimization actions, and counterpoints without leaking hidden labels into ranking. | R346 `diagnostic-casebook-report.json`, `visible-diagnostic-casebook.json`, `answer-key.json`, `task-diagnostic-case-cards.csv`, `top-stack-evidence.csv`, Markdown, HTML, and run-result generated from tracked R335/R345 artifacts and existing labeled operation JSONL. | C4 |
| Case-level baseline contrast | Whether the same top-ranked case evidence gives a better inspection-work/fragmentation/recall tradeoff than flat, fixed-session, dataset-native, and raw-action visible views while preserving counterpoints. | R347 `case-baseline-contrast-report.json`, `view-case-metrics.csv`, `task-baseline-contrast-cards.csv`, `baseline-pair-summary.csv`, `top-group-contrast.csv`, Markdown, HTML, and run-result generated from tracked R346 artifacts and existing labeled operation JSONL. | C4 |
| Action-counterfactual audit | Whether profiler actionability cards correspond to objective-level counterfactual policy/view/ranker changes over already-scored visible policies, while preserving non-operation-stack counterpoints. | R348 `action-counterfactual-report.json`, `objective-counterfactuals.csv`, `action-class-summary.csv`, `task-action-counterfactual-cards.csv`, Markdown, HTML, and run-result generated from tracked R335/R341/R347 artifacts. | C4 |
| Held-out action-transfer audit | Whether non-target-selected visible policies imply the same action class on held-out tasks, or at least preserve metric tolerance without target-label selection. | R349 `action-transfer-report.json`, `action-transfer-decisions.csv`, `action-transfer-summary.csv`, `action-transfer-confusion.csv`, `task-action-transfer-cards.csv`, exclusions, Markdown, HTML, and run-result generated from tracked R340/R348 artifacts. | C4 |
| Evidence-packet budget audit | Whether top-ranked operation-stack evidence, baseline counterpoints, action counterfactuals, and held-out transfer guardrails form bounded reviewer-auditable diagnostic packets. | R350 `evidence-packet-report.json`, `task-evidence-packets.csv`, `objective-evidence-packets.csv`, `budget-summary.csv`, Markdown, HTML, and run-result generated from tracked R346/R347/R348/R349 artifacts. | C4 |
| Executable profile-spec patch audit | Whether profiler actionability can be materialized as before/after profile-spec edits over the same visible operation input and scored after Rust profiling. | R354 `profile-patch-report.json`, `profile-patch-summary.csv`, default and patched profile specs, Rust JSON profiles, Markdown, HTML, and run-result generated from tracked R324/R348 artifacts. | C4 |
| Oracle-depth adequacy audit | Whether the same visible-ranked profile groups localize positives at the oracle depth available in each dataset: session, operation/step, positive-run proxy, and task-specific units such as OSWorld-Human `human_group`. | R355 `oracle-depth-adequacy-report.json`, `oracle-depth-matrix.csv`, `policy-depth-adequacy.csv`, `depth-policy-comparisons.csv`, `task-depth-cards.csv`, Markdown, HTML, and run-result generated from tracked R300/R320/R339 artifacts plus ScaleCUA context-only rows. | C2, C4 |
| OSDI evaluation-rubric audit | Whether the existing profiler evidence satisfies a scoped top-conference profiling-paper rubric for faithful localization/ranking, actionability, baseline tradeoff, generality, mechanism isolation, robustness, reproducibility, and claim-scope guardrails. | R352 `evaluation-rubric-report.json`, `evaluation-rubric-checks.csv`, `residual-risks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320-R351 artifacts plus current paper text hashes. | C4 guardrail / scope control |
| Inspection-efficiency frontier | Whether ranked profile groups recover positives under fixed inspected-work budgets, rather than only top-k group budgets. | R333 `inspection-frontier-report.json`, `policy-curve-summary.csv`, `task-policy-curves.csv`, `default-vs-baselines.csv`, Markdown, HTML, and run-result generated from tracked R320/R300 operation JSONL. | C4 |
| Fragmentation tradeoff audit | Whether operation-stack groups reduce fixed-session positive fragmentation separately from operation-work and first-positive metrics. | R334 `fragmentation-tradeoff-report.json`, `default-fragmentation-comparisons.csv`, `budget-fragmentation-comparisons.csv`, `fixed-session-fragmentation-cases.csv`, Markdown, HTML, and run-result generated from tracked R320/R333 artifacts. | C4 |
| Actionability synthesis | Whether profiler outputs identify concrete tuning knobs for ranker, mapping/tagging, stack depth, feature policy, transfer policy, and fixed-session drilldown while preserving counterpoints. | R335 `actionability-synthesis-report.json`, `task-actionability-cards.csv`, `mechanism-evidence.csv`, Markdown, HTML, and run-result generated from tracked R320/R325/R326/R329/R332/R334 artifacts. | C4 |
| Actionability selection audit | Whether the actionability knobs translate into objective-specific visible policy choices without becoming a universal selector. | R336 `actionability-selection-report.json`, `objective-recommendations.csv`, `policy-objective-summary.csv`, `pareto-frontier.csv`, Markdown, HTML, and run-result generated from tracked R320/R333/R334/R335 artifacts. | C4 |
| Inspection-target cost audit | Whether the ranked profiles reduce work and group count at fixed positive-recall targets, rather than only at fixed top-k or work budgets. | R337 `inspection-target-report.json`, `inspection-targets.csv`, `policy-target-summary.csv`, `task-target-best.csv`, `default-target-comparisons.csv`, Markdown, HTML, and run-result generated from tracked R333/R336 artifacts. | C4 |
| Paper claim-integrity audit | Whether paper-facing R327/R328 reproducibility numbers, R320-R350 profiler numbers, source provenance, must-not-claim guardrails, and the operation/operation-stack abstraction boundary stay aligned across the evaluation ledger and Chinese/English drafts. | R338 `claim-integrity-report.json`, `claim-number-checks.csv`, `source-policy-checks.csv`, `paper-text-coverage.csv`, `guardrail-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R327/R328/R320/R333/R334/R335/R336/R337/R339/R340/R341/R342/R344/R345/R346/R347/R348/R349/R350 artifacts plus current paper text hashes. | C4 guardrail / scope control |
| Paper claim-integrity refresh for R354/R355 | Whether the newer executable patch and oracle-depth results are aligned with the evaluation ledger, Chinese/English drafts, source provenance, must-not-claim guardrails, and the operation/operation-stack abstraction boundary. | R356 `claim-integrity-r356-report.json`, `number-checks.csv`, `text-coverage.csv`, `guardrail-checks.csv`, `abstraction-text-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R354/R355 artifacts plus the R338 R320-R350 gate and current paper text hashes. | C4 guardrail / scope control |
| Paper reviewer acceptance after R356 | Whether independent reviewers accept the current R356 paper state under the scoped hidden-label profiler claim, R354/R355 supplements, must-not-claim guardrails, and operation/operation-stack boundary. | R357 `reviewer-acceptance-r357.json`, `reviewer-verdicts.csv`, `acceptance-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current paper/docs plus tracked R351/R352/R354/R355/R356 artifacts. | C4 guardrail / scope control |
| Boundary-derived profile patch audit | Whether boundary-derived operation fields repair the R354 OSWorld-Human rejection when folded through the same Rust profile-spec path, and which inspection-cost counterpoints remain. | R358 `boundary-profile-patch-report.json`, `policy-metrics.csv`, `policy-comparisons.csv`, `top-stacks.csv`, profile specs, Rust JSON profiles, scrubbed visible-operation input, Markdown, HTML, and run-result generated from tracked R297 held-out boundary-backend operations. | C2, C4 |
| Three-plus-one consolidation audit | Whether the paper-facing evaluation is organized as three empirical profiling experiments plus one replayability/scope-control block rather than a chronological list of R-runs, while preserving R358 counterpoints and claim boundaries. | R359 `core-experiment-report.json`, `core-experiment-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from the current evaluation ledger, Chinese claim setup, Chinese draft, English submodule draft, and tracked R358 artifacts. | RQ1/E1-RQ4/E4 paper-structure guardrail |
| Paper core-result table generator | Whether the four paper-block rows and their headline numbers can be regenerated from tracked artifacts rather than copied as prose, with R366 field-derivation evidence integrated into RQ1/E1 and RQ3/E3 rather than a fifth block. | R360 `core-result-tables.json`, `core-result-experiments.csv`, `core-result-metrics.csv`, `core-result-checks.csv`, `paper-table.tex`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R285/R286/R320/R328/R338/R342/R353/R354/R355/R357/R358/R359/R366 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 table/provenance guardrail |
| Core-claim evidence ledger | Whether each RQ/E paper-block row is claim-complete for a profiling paper: claim, research question, oracle, baselines, primary metrics, headline result, actionable insight, counterpoint, scoped wording, and source runs, including field-derivation scope. | R361 `core-claim-evidence.json`, `core-claim-ledger.csv`, `core-claim-checks.csv`, `claim-ledger-table.tex`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320/R352/R354/R355/R357/R358/R359/R360/R366 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 ledger/provenance guardrail |
| Paper section-readiness audit | Whether the Chinese and English RQ1/E1-RQ4/E4 result sections themselves carry the R361 structure: claim, oracle, baseline, metric, counterpoint/scope, localization metrics, actionability guardrails, reproducibility guardrails, and the two-abstraction boundary. | R362 `section-readiness.json`, `section-token-matrix.csv`, `section-readiness-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R361 plus current paper/docs. | RQ1/E1-RQ4/E4 section guardrail |
| Paper visualization portfolio | Whether the RQ1/E1-RQ4/E4 evidence is presented as a small set of paper-ready analysis views rather than a flamegraph-only artifact or a chronological R-run list. | R363 `visualization-portfolio.json`, `portfolio-table.tex`, `baseline-tradeoff.svg`, `metric-heatmap.svg`, `diagnostic-lenses.svg`, `actionability-knobs.svg`, `oracle-depth-adequacy.svg`, corresponding CSVs, `portfolio-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320/R345/R348/R354/R355/R358/R361/R362 artifacts. | RQ2/E2-RQ3/E3 presentation artifact |
| Three-plus-one sufficiency audit | Whether E1-E3 are substantial reviewer-facing empirical profiling experiments and E4 is a replayability/scope-control block, with each block carrying primary evidence, oracle or replay target, baselines or scope condition, metrics, success criterion, failure interpretation, figure/table target, and claim-gate decision, while keeping R366 internal to RQ1/E1 and RQ3/E3. | R364 `core-experiment-sufficiency.json`, `sufficiency-matrix.csv`, `sufficiency-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R338/R352/R356/R357/R360/R361/R363/R366 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 sufficiency guardrail |
| Paper headline/case-study selector | Whether RQ2/E2 and RQ3/E3 evidence has compact paper-ready headline rows and task cards without becoming a new experiment, dataset, profiler run, or profiler abstraction. | R365 `headline-case-studies.json`, `headline-rows.csv`, `task-case-cards.csv`, `headline-checks.csv`, `source-status.csv`, `headline-table.tex`, Markdown, HTML, and run-result generated from tracked R320/R333/R334/R345/R348/R354/R355/R358/R363 artifacts plus current paper/docs. | RQ2/E2-RQ3/E3 paper-integration artifact |
| Operation-field derivation mechanism audit | Whether mapping, tagging/rank-feature, profile-spec, and supervised boundary-field mechanisms improve aggregation or localization through operation fields while preserving simple-baseline and inspection-cost counterpoints. | R366 `field-derivation-mechanism-report.json`, `mechanism-rows.csv`, `boundary-family-summary.csv`, `mechanism-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R282/R285/R297/R299/R325/R342/R358 artifacts plus current paper/docs. | C3/E3 mechanism guardrail |
| Field-derivation suitability audit | Whether operation-field derivation produces guarded profile-configuration decisions instead of a universal selector. | R400 `field-suitability-report.json`, `decision-rules.csv`, `family-decisions.csv`, `field-suitability-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R325/R358/R366 artifacts without dataset sync or profiler rerun. | C3/E3 actionability guardrail |
| Rust operation-stack induction replay | Whether the maintained Rust profiler can induce recursive operation stacks from adjacent boundary evidence without a user-provided stack-field chain. | R402 `summary.json`, `report.md`, `run-result.json`, folded outputs, SVG/PNG flamegraphs, and JSON profiles generated by `script/operation_rust_task_stack_induction_eval.py` over the tracked R300 AgentRewardBench looping slice. | C1/E1 mechanism and visualization guardrail |
| Induced operation-stack hidden-label scoring | Whether Rust-induced operation stacks, treated as a normal profiler view, localize hidden positives and reduce fragmentation on the existing six R300/R320 real labeled tasks. | R403 `induced-stack-scoring-report.json`, `policy-summary.csv`, `comparison-summary.csv`, `view-summary.csv`, `induced-policy-scores.csv`, `index.html`, and `run-result.json` generated by `script/operation_induced_stack_scoring_eval.py` from the tracked R300 operations and R320 baseline scores. | RQ2/E2 and RQ3/E3 mechanism ablation |
| Induced operation-stack depth sensitivity | Whether the induced recursive operation stack exposes a real accuracy/work/fragmentation depth surface on the same hidden-label tasks rather than requiring a fixed field chain. | R404 `depth-sensitivity-report.json`, `depth-policy-scores.csv`, `depth-summary.csv`, `best-depth-by-task.csv`, `depth-comparisons-to-depth4.csv`, Markdown, HTML, and `run-result.json` generated by `script/operation_induced_depth_sensitivity_eval.py` from tracked R300 operations and R320/R403 scoring machinery. | RQ2/E2 and RQ3/E3 mechanism/actionability ablation |
| English paper experiment gap audit | Whether the English submodule draft is behind the outer evidence base, which gaps are supported, future work, or non-claims, and whether current operation JSONL inputs can support same-input free-text tagger accuracy without editing the submodule. | R405 `english-experiment-gap-audit.json`, CSV, Markdown, HTML, `source-status.csv`, and `run-result.json` generated by `script/paper_english_experiment_gap_audit.py` from the English submodule draft plus outer evidence; the scan covers 6 operation JSONL sources / 67,304 rows and finds no row with both public free-form text fields and oracle semantic labels. | Paper-integration and C3 tagger-scope guardrail |
| English operation-stack induction sync packet | Whether R402/R403/R404 operation-stack induction evidence is ready to port into the English paper, while preserving non-claims and keeping the submodule read-only. | R406 `english-induction-sync.json`, `english-induction-sync.csv`, `english-induction-snippets.tex`, Markdown, HTML, `source-status.csv`, and `run-result.json` generated by `script/paper_english_induction_sync_audit.py` from existing R402/R403/R404 artifacts. | Paper-integration guardrail |
| Operation-stack induction paper display | Whether the induction evidence is presented as one claim-facing table rather than prose-only support or a run ledger. | R407 `induction-display.json`, `induction-display.csv`, `induction-claim-table.tex`, Markdown, HTML, `source-status.csv`, and `run-result.json` generated by `script/paper_induction_display_r407.py` from existing R402/R403/R404 artifacts. | RQ1/E1-RQ3/E3 paper-integration guardrail |
| Chinese induction PDF freshness | Whether the tracked Chinese PDF actually contains the updated induction display and keeps the table reader-facing rather than run-ledger-facing. | R408 `chinese-induction-pdf-report.json`, `induction-pdf-tokens.csv`, `induction-pdf-checks.csv`, Markdown, HTML, `source-status.csv`, and `run-result.json` generated by `script/paper_chinese_induction_pdf_freshness_r408.py` from the tracked Chinese paper/PDF plus R407 artifacts. | Paper-integration freshness guardrail |
| English submodule read-only policy gate | Whether the current workflow preserves the user's submodule constraint: only the outer worktree is modified, the English submodule is dirty but not staged, gap-aware gates use R405 instead of editing English, and direct push safety is explicit. | R409 `submodule-readonly-policy-report.json`, `submodule-readonly-policy-checks.csv`, `source-status.csv`, Markdown, HTML, and `run-result.json` generated by `script/paper_submodule_readonly_policy_r409.py` from git status, AGENTS/CLAUDE, canonical docs, and R397/R398/R399/R405 outputs. | Collaboration/reproducibility guardrail |
| Paper entry claim-path audit | Whether the abstract, introduction/problem statement, and main result framing present the paper as RQ1/E1-RQ4/E4 rather than scattered R-runs, while preserving the two-abstraction boundary and must-not-claim limits. | R367 `entry-claim-path-report.json`, `entry-token-matrix.csv`, `entry-claim-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current Chinese/English paper text plus tracked R360/R361/R364/R366 ledgers. | RQ1/E1-RQ4/E4 entry-narrative guardrail |
| Trace-tree-shaped baseline tradeoff audit | Whether fixed-session drilldown is sufficiently supported as the evaluated trace-tree-shaped baseline, and whether flat, dataset-native, and raw-action counterpoints remain visible. | R368 `trace-tree-baseline-report.json`, `baseline-family-summary.csv`, `trace-tree-comparisons.csv`, `task-baseline-cards.csv`, `trace-tree-baseline-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320/R355 artifacts plus current paper/docs. | E2 baseline-scope guardrail |
| Reviewer evidence-path audit | Whether the paper gives a compact reviewer route from each RQ to its main table/figure, source artifact, guardrail, and non-claim without forcing readers through the chronological run ledger. | R369 `evidence-path.json`, `evidence-path.csv`, `evidence-path-table.tex`, `evidence-path-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R360/R361/R363/R365/R368 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 reviewer evidence-path guardrail |
| Main-experiment contract audit | Whether each paper-facing block has a primary test, workload/oracle, baselines and metrics, primary evidence, supporting R-run roles, failure interpretation, and non-claim, with E1-E3 empirical and E4 replayability/scope-control. | R370 `main-experiment-contract.json`, `main-experiment-contract.csv`, `main-experiment-contract-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R360/R361/R363/R364/R365/R368/R369 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 main-experiment organization guardrail |
| Evaluation narrative-focus audit | Whether the Chinese and English RQ sections follow the main-experiment contract in prose: primary result before support runs, RQ1/E1 kept separate from E3 ranker probes, RQ4/E4 replay/cost before scope checks, and claim-test/counterpoint/non-claim language in each section. | R371 `narrative-focus-report.json`, `narrative-focus-checks.csv`, `section-summary.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R370 plus current paper/docs. | RQ1/E1-RQ4/E4 prose-organization guardrail |
| Main-body concision audit | Whether RQ2/RQ3 main-body prose stays organized as core-experiment evidence rather than support-run chronology: RQ2 robustness/depth slices remain one supporting-audit paragraph, and RQ3 still centers mechanism/actionability plus non-claims. | R372 `main-body-concision-report.json`, `main-body-concision-checks.csv`, `section-summary.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R371 plus current paper/docs. | RQ2/E2-RQ3/E3 main-body anti-ledger guardrail |
| Task-level claim verdict synthesis | Whether each real labeled task supports the main profiler claim through fidelity/work evidence, fixed-session tradeoff evidence, and actionable configuration evidence while preserving task-specific counterpoints. | R373 `task-claim-verdict-report.json`, `task-claim-verdict.csv`, `task-claim-verdict-checks.csv`, `task-verdict-table.tex`, `source-status.csv`, Markdown, HTML, run-result, and the English submodule `figures/task-verdict-table.tex` generated from tracked R320/R354/R355/R358/R365 artifacts plus current paper/docs. | RQ2/E2-RQ3/E3 task-level claim verdict |
| Three-plus-one role gate | Whether the main paper presents three empirical profiling experiments plus one replayability/scope-control block with primary anchors, support/presentation roles, and non-claim boundaries, instead of mirroring the R-run ledger. | R374 `core-experiment-weight-report.json`, `experiment-role-map.csv`, `core-experiment-weight-checks.csv`, `experiment-role-table.tex`, `source-status.csv`, Markdown, HTML, run-result, and the English submodule `figures/experiment-role-table.tex` generated from tracked R370/R371/R372/R373 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 role/weight guardrail |
| Three-plus-one claim gate | Whether E1-E3 empirical profiling experiments and the E4 replayability/scope-control block each have an explicit gate decision, allowed paper claim, failure/narrowing rule, and must-not-claim boundary, so the paper can support the profiling claim without drifting into metric dominance, human utility, automatic boundary discovery, automatic patch selection, or ecosystem compatibility. | R375 `core-claim-gate-report.json`, `claim-gate.csv`, `claim-gate-checks.csv`, `claim-gate-table.tex`, `source-status.csv`, Markdown, HTML, run-result, and the English submodule `figures/claim-gate-table.tex` generated from tracked R361/R364/R370/R373/R374 artifacts plus current paper/docs. | RQ1/E1-RQ4/E4 claim-decision guardrail |
| Three-plus-one paper organization gate | Whether current Chinese/English paper text, generated R374/R375 tables, evaluation ledger, and Chinese user doc consistently frame E1-E3 as empirical profiling experiments and E4 as replayability/scope-control, while de-emphasizing flamegraph-only novelty. | R376 `three-plus-one-report.json`, `three-plus-one-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current Chinese/English paper text, `docs/agentpprof-zh.md`, R374/R375 reports/tables, and the evaluation ledger. | RQ1/E1-RQ4/E4 paper-organization guardrail |
| Main profiling-claim evidence gate | Whether the central profiler claim is supported as five auditable claim facets inside the 3+1 paper structure: hidden-label localization/ranking, lower flat inspection work, fixed-session fragmentation tradeoff, actionable optimization insight, and mechanism isolation, with non-claim boundaries preserved. | R377 `main-claim-evidence-report.json`, `main-claim-evidence.csv`, `main-claim-evidence-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320/R333/R334/R354/R355/R358/R366/R375/R376 artifacts plus current paper/docs. | RQ2/E2-RQ3/E3 main-claim evidence guardrail |
| Main-body table-budget gate | Whether the paper keeps support artifacts as provenance instead of main-body table sprawl: R363 full portfolio, R365 headline/case tables, and R373 verdict matrix are demoted while core E1-E4 displays remain. | R378 `main-body-table-budget-report.json`, `main-body-table-budget-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R377 plus current Chinese/English paper text and the evaluation ledger. | RQ2/E2-RQ3/E3 paper-presentation guardrail |
| RQ2/RQ3 claim-flow gate | Whether RQ2/RQ3 prose follows a profiling-paper claim-test order: comparison, success criterion, baseline scope, failure interpretation, mechanism/actionability, executable configuration loop, and non-claims before support-run detail. | R379 `rq2-rq3-claim-flow-report.json`, `rq2-rq3-claim-flow-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R377/R378 plus current Chinese/English paper text and the evaluation ledger. | RQ2/E2-RQ3/E3 prose-claim-flow guardrail |
| Experiment-block consolidation gate | Whether the main paper remains organized as three empirical profiling experiments plus one replayability/scope-control block, while support runs stay as provenance/support roles inside E1-E4 instead of reappearing as chronological mini-experiments. | R380 `experiment-block-consolidation-report.json`, `experiment-block-consolidation-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R377/R378/R379 plus current Chinese/English paper text and the evaluation ledger. | RQ1/E1-RQ4/E4 anti-ledger paper-organization guardrail |
| Diagnosis/actionability presentation gate | Whether the E3 task rows preserve six task-level localization signals, concrete profile actions, verdicts with counterpoints, non-claim wording, and linkage to task-card/verdict artifacts without becoming a new empirical experiment. | R381 `diagnosis-card-report.json`, `diagnosis-card-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R365/R373/R380 plus current Chinese/English paper text and the evaluation ledger. | RQ2/E2-RQ3/E3 actionability presentation guardrail |
| Canonical three-plus-one consistency gate | Whether canonical docs and paper drafts consistently describe E1-E3 as empirical profiling experiments and E4 as a replayability/scope-control block, with stale four-experiment wording removed. | R382 `canonical-three-plus-one-report.json`, `canonical-three-plus-one-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R380/R381 plus current idea story, design, evaluation ledger, and Chinese/English paper text. | RQ1/E1-RQ4/E4 canonical-doc paper-organization guardrail |
| Canonical reviewer acceptance after R382 | Whether independent read-only reviewers accept the canonical-doc three-plus-one cleanup and the scope boundaries around E4, claim safety, and paper/ledger consistency. | R383 `reviewer-acceptance-r383.json`, `reviewer-verdicts.csv`, `acceptance-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R380/R381/R382 plus current docs/papers and recorded reviewer verdicts. | RQ1/E1-RQ4/E4 canonical-doc reviewer-acceptance guardrail |
| Post-R392 reviewer acceptance | Whether independent read-only reviewers accept the current paper/docs after the R392 E4 input-source replay update, with R392 kept inside E4, the 3+1 structure preserved, and the dataset-source wording corrected. | R393 `reviewer-acceptance-r393.json`, `reviewer-verdicts.csv`, `acceptance-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from R383 plus current docs/papers and recorded reviewer verdicts. | RQ1/E1-RQ4/E4 post-R392 reviewer-acceptance guardrail |
| Two-abstraction documentation consistency gate | Whether maintained docs and paper drafts keep operation/operation-stack as the only profiler abstractions after the Chinese guide cleanup, with tagging, mapping, LLM tags, clustering, predicates, and profile specs framed as operation-field derivation or query configuration before folding. | R394 `two-abstraction-doc-report.json`, `two-abstraction-doc-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current Rust CLI wording, user guides, canonical docs, and paper drafts. | RQ1/E1-RQ4/E4 two-abstraction doc guardrail |
| Main claim and verdict alignment gate | Whether the current idea story, evaluation ledger, and paper drafts align the central profiling claim with the C4 claim verdict after the three-plus-one consolidation repair: hidden-label fidelity, lower flat-summary work, fixed-session proxy fragmentation tradeoff, configuration-level actionability, and explicit unsupported-claim boundaries. | R395 `main-claim-verdict-alignment-report.json`, `main-claim-verdict-alignment-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current canonical docs, paper drafts, and R377/R380/R383/R391/R393/R394 gate outputs. | RQ1/E1-RQ4/E4 main-claim/verdict alignment guardrail |
| Paper build smoke and accessibility gate | Whether the Chinese and English paper drafts build locally into PDFs after the claim-verdict alignment, final logs have no unresolved references/citations, and the English ACM non-flamegraph figure carries description metadata. | R396 `paper-build-smoke-report.json`, `paper-build-smoke-checks.csv`, `paper-build-commands.csv`, `source-status.csv`, copied final logs, command stdout logs, Markdown, HTML, and run-result generated from current paper sources and R395 output through temporary build locations. | RQ4/E4 paper-build reproducibility guardrail |
| Main-body run-ledger suppression gate | Whether the main paper bodies keep R-numbered runs and internal checklist-style terms out of the narrative while the writable Chinese paper preserves RQ1/E1--RQ4/E4 as the reviewer-facing experiment path and English drift is handled only by the R405 read-only sync gap. | R397 `main-body-run-ledger-report.json`, `main-body-run-ledger-checks.csv`, `run-id-hits.csv`, `main-paper-internal-style-hits.csv`, `chinese-internal-style-hits.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current paper sources, canonical docs, R395/R396 outputs, and the R405 gap audit. | RQ1/E1-RQ4/E4 paper-organization guardrail |
| Current three-plus-one organization gate | Whether the writable Chinese paper still has exactly RQ1/E1--RQ4/E4 as the main result path, with E2 as the single hidden-label accuracy block, E3 as mechanism/actionability, E4 as replayability/scope-control, no main-body run IDs, no internal checklist-style terms, no paper-facing venue-readiness self-undercut wording, explicit new-run role assignment inside E1-E4, a visible main-display path, no new small-experiment sprawl in the canonical next action, and English treated only as synced or R405-recorded read-only gap. | R398 `current-three-plus-one-report.json`, `current-three-plus-one-checks.csv`, `paper-run-id-hits.csv`, `main-paper-internal-style-hits.csv`, `chinese-internal-style-hits.csv`, `paper-self-undercut-hits.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from current paper sources, canonical docs, R395/R396/R397 outputs, and the R405 gap audit. | RQ1/E1-RQ4/E4 paper-organization regression guardrail |
| Tracked paper PDF freshness gate | Whether the committed Chinese PDF contains the same main-display path as the TeX source, so the rendered outer paper artifact does not lag source edits, while English PDF/source drift remains a read-only R405 sync gap. | R399 `pdf-freshness-report.json`, `pdf-freshness-checks.csv`, `pdf-token-checks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked paper sources/PDFs plus R396/R398/R405 outputs. | RQ4/E4 tracked-PDF replayability/scope-control check |
| Sequence-scope adequacy audit | Whether ranked profile groups localize positives to useful trajectory/session scope, rather than only to positive operations or groups. | R339 `sequence-adequacy-report.json`, `task-sequence-adequacy.csv`, `policy-sequence-summary.csv`, `default-sequence-comparisons.csv`, `task-sequence-cards.csv`, Markdown, HTML, and run-result generated from tracked R288-R291 operation JSONL plus R320/R337 reports. | C2, C4 |
| Cross-family policy-transfer audit | Whether visible policy choices selected from non-target tasks or non-target datasets remain useful on held-out labeled tasks without looking at the target labels during selection. | R340 `policy-transfer-report.json`, `transfer-decisions.csv`, `objective-transfer-summary.csv`, `selected-policy-summary.csv`, `task-transfer-cards.csv`, Markdown, HTML, and run-result generated from tracked R320/R339 artifacts. | C4 |
| Mechanism and transfer-error attribution | Whether objective-specific wins and held-out transfer misses can be explained as concrete view, ranker, mapping/tagging, stack-depth, feature-policy, or baseline-counterpoint knobs. | R341 `mechanism-attribution-report.json`, `objective-mechanism-attribution.csv`, `transfer-error-attribution.csv`, Markdown, HTML, and run-result generated from tracked R320/R335/R336/R340 artifacts. | C4 |
| Related-work novelty audit | Whether the paper explicitly distinguishes two-object operation profiling from classic folded-stack profilers, LLM observability trace trees, OpenTelemetry/OpenInference semantic conventions, and public labeled trajectory benchmarks. | R314 `related-work-audit.json`, Markdown, CSV, HTML, and run-result generated from the current related-work ledger, paper draft, claim ledger, evaluation ledger, and tracked R313 frontier artifact. | C1, C2, C4 |
| Controlled analyst-study protocol | Whether the existing visible packets and hidden answer key are sufficient to run a balanced controlled human/agent analyst study without leaking oracle labels. | R315 `study-protocol.json`, `visible-study-packets.json`, `hidden-scoring-key.json`, `assignment.csv`, Markdown, HTML, and run-result generated from tracked R305/R308/R313 artifacts. | C4 |
| Analyst-study readout sensitivity | Whether the R315 assignment and hidden scoring key can recover the expected flat/fixed/operation-stack tradeoff under a fixed visible-order scripted policy before running real analysts. | R316 `readout-report.json`, `trial-scores.csv`, Markdown, HTML, and run-result generated from tracked R315 artifacts. | C4 |
| Paper real-problem narrative | Whether existing problem cards, frontier points, and protocol readout form a claim-first OSDI-style narrative with explicit counterpoints. | R317 `paper-narrative-report.json`, `task-narrative.csv`, Markdown, HTML, and run-result generated from tracked R309/R313/R316 artifacts. | C1, C2, C4 |
| Paper reviewer acceptance | Whether independent subagent reviewers accept the scoped R317 paper update after fixing artifact-log presentation blockers. | R318 `reviewer-acceptance.json`, `reviewer-verdicts.csv`, Markdown, HTML, and run-result generated from current paper plus R312/R314/R317 artifacts. | paper-readiness guardrail |
| Paper reviewer acceptance after R350 | Whether independent reviewers accept the current R350/R338 paper state under the scoped hidden-label profiler claim, must-not-claim guardrails, and clean deterministic-output provenance. | R351 `reviewer-acceptance.json`, `reviewer-verdicts.csv`, Markdown, HTML, and run-result generated from current paper plus tracked R320/R328/R331/R338/R350 artifacts. | C4 guardrail / scope control |
| Paper evaluation rubric after R351 | Whether the accepted paper state meets a profiling-paper evaluation rubric without adding unsupported human-utility, automatic boundary-discovery, ecosystem-compatibility, or universal-selector claims. | R352 `evaluation-rubric-report.json`, `evaluation-rubric-checks.csv`, `residual-risks.csv`, `source-status.csv`, Markdown, HTML, and run-result generated from tracked R320-R351 artifacts plus current paper text hashes. | C4 guardrail / scope control |
| Implementation/docs consistency | Whether the current Rust CLI/profile/standard-trace implementation, CLI help/about, canonical docs, and Chinese paper agree on profile specs, standard trace exchange, two core abstractions, and real remaining gates. | R319 `implementation-consistency.json`, CSV, Markdown, HTML, and run-result generated from current source and docs. | C1, C2, C4 |
| Paper evidence matrix | Whether final paper claims, evidence numbers, and must-not-claim boundaries are mechanically aligned after R309. | R310 `evidence-matrix.json`, Markdown, CSV, TeX, HTML, and run-result generated from tracked R307/R309 artifacts. | C1, C2, C3, C4 |
| Paper robustness audit | Whether the final claim wording survives reviewer stress tests over existing ranking, case-packet, outcome, value-card, and evidence-matrix artifacts. | R311 `robustness-audit.json`, Markdown, CSV, TeX, HTML, and run-result generated from tracked R302/R305/R308/R309/R310 artifacts. | C1, C2, C3, C4 |
| Paper submission audit | Whether the current Chinese draft preserves R310/R311/R320 numbers, two-abstraction wording, C4 profiler-accuracy wording, and must-not-claim guardrails. | R312 `submission-audit.json`, Markdown, CSV, TeX, HTML, and run-result generated from tracked R310/R311 artifacts, current R320 profiler-accuracy output, and current `main.tex`. | C1, C2, C3, C4 |

## Reproducibility Checklist

| Item | Status |
|---|---|
| Raw external samples are kept under `.agentsight/`, which is gitignored. | done |
| Normalized operation JSONL omits raw task text by default. | done |
| First external smoke output is tracked under `docs/visexp/out/`. | done |
| Cross-dataset non-flamegraph analysis emits tree, top-kind bars, and transition tables. | done |
| Rust unit tests cover operation JSONL input. | done |
| Rust unit tests cover `--op-map` operation field mapping before stacking. | done |
| Mind2Web HF repo JSON shard sampling is implemented. | done |
| ToolBench HF mirror conversation sampling is implemented. | done |
| AndroidControl lightweight sampling is implemented with screenshot redaction for saved raw rows. | done |
| GUI-Odyssey lightweight sampling is implemented. | done |
| tau-bench trajectory JSONL sampling is implemented and tracked under R287. | done |
| AgentRewardBench annotation-plus-cleaned-trajectory sampling is implemented and tracked under R288. | done |
| SATraj-OS safety trajectory sampling is implemented and tracked under R289. | done |
| OSWorld-Human GitHub JSON trajectory sampling is implemented and tracked under R290. | done |
| AgentNet HF repo JSONL stream sampling is implemented and tracked under R291 without syncing the full source JSONL. | done |
| ScaleCUA HF repo annotation JSONL stream sampling is implemented and tracked under R292 without syncing the full source JSONL or images. | done |
| Profile-spec reproducibility for operation-stack experiments is implemented and tracked under R293. | done |
| Portable agent-session trace export/import and trace-to-operation JSONL conversion are implemented and tracked under R294. | done |
| Scripted agent-session trace exchange reproduction is implemented and tracked under R303. | done |
| Mechanical paper-claim synthesis from tracked artifacts is implemented and tracked under R295. | done |
| Reviewer evidence packet with non-flamegraph navigation is implemented and tracked under R296. | done |
| Supervised OSWorld-Human boundary-backend expansion probe is implemented and tracked under R297. | done |
| Paper value and novelty synthesis is implemented and tracked under R298. | done |
| Boundary-family calibration over existing tracked operation JSONL is implemented and tracked under R299. | done |
| Operation-query utility proxy over existing tracked operation JSONL is implemented and tracked under R300. | done |
| Width-ranked analyst task proxy with visible packets and hidden answer key is implemented and tracked under R301. | done |
| Label-hidden analyst ranking policy proxy over existing tracked operation JSONL is implemented and tracked under R302. | done |
| Reviewer-facing operation-stack case packet over existing tracked operation JSONL is implemented and tracked under R304. | done |
| Cross-view case-packet baseline over existing tracked operation JSONL is implemented and tracked under R305. | done |
| Paper claim readiness refresh after R300-R306 is implemented and tracked under R307. | done |
| Analyst first-evidence proxy over R305 visible packets and answer key is implemented and tracked under R308. | done |
| Real-problem value cards over tracked proxy artifacts are implemented and tracked under R309. | done |
| Paper evidence matrix over tracked R307/R309 artifacts is implemented and tracked under R310. | done |
| Paper robustness and reviewer-stress audit over tracked R302/R305/R308/R309/R310 artifacts is implemented and tracked under R311. | done |
| Paper submission claim/guardrail audit over tracked R310/R311 artifacts, current R320 profiler-accuracy output, and current draft is implemented and tracked under R312. | done |
| Operation-view Pareto frontier over tracked R300/R302/R305/R311 artifacts is implemented and tracked under R313. | done |
| Related-work novelty and baseline audit over current docs/paper plus tracked R313 frontier is implemented and tracked under R314. | done |
| Controlled analyst-study protocol over R305 visible packets and hidden answer key is implemented and tracked under R315. | done |
| Analyst-study scripted readout sensitivity over tracked R315 artifacts is implemented and tracked under R316. | done |
| Claim-first real-problem paper narrative over tracked R309/R313/R316 artifacts is implemented and tracked under R317. | done |
| Independent reviewer acceptance closure over the R317 paper update is implemented and tracked under R318. | done |
| Implementation/docs consistency audit over current Rust CLI/profile/standard-trace sources and paper docs is implemented and tracked under R319. | done |
| Label-scored profiler localization/ranking benchmark over tracked real labeled operation JSONL is implemented and tracked under R320. | done |
| Query-time operation predicate profile-spec probe is implemented and tracked under R321. | done |
| Rust visible rank-rule profile-spec probe is implemented and tracked under R322. | done |
| Rust rank-mode profile-spec probe is implemented and tracked under R323. | done |
| Rust operation rank-feature profile-spec probe is implemented and tracked under R324. | done |
| Rust operation rank-feature ablation/actionability probe is implemented and tracked under R325. | done |
| Rust operation rank-feature robustness/actionability probe is implemented and tracked under R326. | done |
| Fragmentation tradeoff audit over tracked R320/R333 artifacts is implemented and tracked under R334. | done |
| Actionability synthesis over tracked R320/R325/R326/R329/R332/R334 artifacts is implemented and tracked under R335. | done |
| Actionability selection audit over tracked R320/R333/R334/R335 artifacts is implemented and tracked under R336. | done |
| Inspection-target cost audit over tracked R333/R336 artifacts is implemented and tracked under R337. | done |
| Paper claim-integrity audit over tracked R327/R328/R320-R350 result artifacts and current Chinese/English paper hashes is implemented and tracked under R338. | done |
| Sequence-scope adequacy audit over tracked R288-R291/R320/R337 artifacts is implemented and tracked under R339. | done |
| Cross-task/cross-dataset visible policy-transfer audit over tracked R320/R339 artifacts is implemented and tracked under R340. | done |
| Mechanism and transfer-error attribution over tracked R320/R335/R336/R340 artifacts is implemented and tracked under R341. | done |
| Profile-spec composition and recursive stack-depth audit over tracked R324/R300 real-trace Rust outputs is implemented and tracked under R342. | done |
| Relocated-checkout artifact portability audit over tracked R324/R342 profile-spec artifacts is implemented and tracked under R343. | done |
| Multi-metric consistency audit over tracked R320 scored profiler rankings is implemented and tracked under R344. | done |
| Diagnostic-lens portfolio over tracked R335/R341/R344 actionability and metric-counterpoint artifacts is implemented and tracked under R345. | done |
| Diagnostic casebook over tracked R335/R345 actionability artifacts and existing labeled operation JSONL is implemented and tracked under R346. | done |
| Case-level baseline contrast over tracked R346 artifacts and existing labeled operation JSONL is implemented and tracked under R347. | done |
| Action-counterfactual audit over tracked R335/R341/R347 artifacts is implemented and tracked under R348. | done |
| Held-out action-transfer audit over tracked R340/R348 artifacts is implemented and tracked under R349. | done |
| Evidence-packet budget audit over tracked R346/R347/R348/R349 artifacts is implemented and tracked under R350. | done |
| Independent reviewer acceptance after R350/R338 is implemented and tracked under R351, including the clean R328 deterministic-output provenance check. | done |
| OSDI-style evaluation-rubric audit over tracked R320-R351 artifacts is implemented and tracked under R352. | done |
| Operation-file standard-trace exchange over a tracked real labeled operation prefix is implemented and tracked under R353. | done |
| Executable profile-spec patch audit over tracked R324 visible operations and R348 action cards is implemented and tracked under R354. | done |
| Oracle-depth adequacy audit over tracked R300/R320/R339 labeled profile outputs is implemented and tracked under R355. | done |
| Paper claim-integrity refresh over R354/R355 and current Chinese/English drafts is implemented and tracked under R356. | done |
| Reviewer-acceptance refresh after R356 is implemented and tracked under R357. | done |
| Boundary-derived OSWorld-Human profile patch audit over tracked R297 held-out operations is implemented and tracked under R358. | done |
| Three-plus-one consolidation audit over the evaluation ledger and Chinese/English drafts is implemented and tracked under R359. | done |
| Paper core-result table generator over tracked RQ1/E1-RQ4/E4 artifacts, including R366 as internal RQ1/E1 and RQ3/E3 evidence, is implemented and tracked under R360. | done |
| Claim evidence ledger over tracked RQ1/E1-RQ4/E4 artifacts, including R366 field-derivation scope, is implemented and tracked under R361. | done |
| Paper section-readiness audit over Chinese/English RQ1/E1-RQ4/E4 result sections is implemented and tracked under R362. | done |
| Paper visualization portfolio over tracked RQ1/E1-RQ4/E4 evidence is implemented and tracked under R363. | done |
| Three-plus-one sufficiency audit over RQ1/E1-RQ4/E4 reviewer-facing blocks, with R366 kept internal to RQ1/E1 and RQ3/E3, is implemented and tracked under R364. | done |
| Paper headline/case-study selector over tracked RQ2/E2 and RQ3/E3 evidence is implemented and tracked under R365. | done |
| Operation-field derivation mechanism audit over tracked mapping/ranking/boundary artifacts is implemented and tracked under R366. | done |
| Field-derivation suitability audit over tracked R325/R358/R366 actionability artifacts is implemented and tracked under R400. | done |
| Rust boundary-based operation-stack induction replay over the tracked R300 AgentRewardBench looping slice is implemented and tracked under R402. | done |
| Induced operation-stack hidden-label scoring over the existing six R300/R320 labeled tasks is implemented and tracked under R403. | done |
| Induced operation-stack depth-sensitivity sweep over the existing six R300/R320 labeled tasks is implemented and tracked under R404. | done |
| Read-only English paper experiment-gap audit is implemented and tracked under R405. | done |
| Read-only English operation-stack induction sync packet over R402/R403/R404 is implemented and tracked under R406. | done |
| Paper-facing induction display table over R402/R403/R404 is implemented and tracked under R407. | done |
| Chinese tracked PDF freshness check for the induction display is implemented and tracked under R408. | done |
| Paper entry claim-path audit over abstract, introduction/problem framing, and RQ1/E1-RQ4/E4 main result framing is implemented and tracked under R367. | done |
| Trace-tree-shaped baseline tradeoff audit over existing R320/R355 hidden-label scoring artifacts is implemented and tracked under R368. | done |
| Reviewer evidence-path audit over RQ1/E1-RQ4/E4 main paper tables/figures, source artifacts, guardrails, and non-claims is implemented and tracked under R369. | done |
| Main-experiment contract audit over RQ1/E1-RQ4/E4 primary tests, support roles, failure interpretations, and non-claims is implemented and tracked under R370. | done |
| Evaluation narrative-focus audit over RQ1/E1-RQ4/E4 prose ordering, support-run placement, and non-claim language is implemented and tracked under R371. | done |
| Main-body concision audit over RQ2/E2 support-run compaction and RQ3/E3 mechanism/actionability focus is implemented and tracked under R372. | done |
| Task-level claim verdict synthesis over six real labeled tasks is implemented and tracked under R373. | done |
| Three-plus-one role gate over RQ1/E1-RQ4/E4 primary anchors, support roles, and non-claims is implemented and tracked under R374. | done |
| Three-plus-one claim gate over RQ1/E1-RQ4/E4 allowed wording, narrowing rules, and must-not-claim boundaries is implemented and tracked under R375. | done |
| Three-plus-one paper organization gate over Chinese/English paper text, generated R374/R375 tables, evaluation ledger, and Chinese user doc is implemented and tracked under R376. | done |
| Main profiling-claim evidence gate over five claim facets mapped back into the 3+1 paper structure is implemented and tracked under R377. | done |
| Main-body table-budget gate demoting R363/R365/R373 support tables while preserving core E1-E4 displays is implemented and tracked under R378. | done |
| RQ2/RQ3 claim-flow gate over primary comparison, success criterion, failure interpretation, mechanism/actionability, executable configuration loop, and non-claims is implemented and tracked under R379. | done |
| Experiment-block consolidation gate over RQ1/E1-RQ4/E4 main-paper organization, anti-run-ledger prose, and support-run provenance roles is implemented and tracked under R380. | done |
| Diagnosis/actionability presentation over six E3 task rows, localization signals, profile actions, verdicts with counterpoints, and non-claim boundaries is implemented and tracked under R381. | done |
| Canonical three-plus-one consistency gate over idea story, design, evaluation ledger, and paper drafts is implemented and tracked under R382. | done |
| Canonical reviewer acceptance closure after R382 is implemented and tracked under R383. | done |
| Main-paper experiment focus gate demoting the R374/R375/R377 run-role material to artifact-ledger provenance while preserving the E1/E2/E3/E4 paper structure is implemented and tracked under R384. | done |
| RQ section contract focus gate replacing R-run-led section openings with claim-facing experiment contracts in the Chinese/English drafts is implemented and tracked under R385. | done |
| E1 main-display gate over the RQ1/E1 claim-test table, recursive folding, mapping/boundary, and human-boundary evidence is implemented and tracked under R386. | done |
| E2 main-display gate over the hidden-label localization benchmark table, baseline rows, headline numbers, and scoped non-claims is implemented and tracked under R387. | done |
| E3 main-display gate over the diagnosis/actionability task rows, actionability numbers, source-artifact role, and non-claim boundaries is implemented and tracked under R388. | done |
| E4 main-display gate over replayability/cost, deterministic-output repair, source-artifact role, and scope-control non-claims is implemented and tracked under R389. | done |
| Novelty-positioning and core-experiment organization gate over the Chinese/English drafts, related-work map, idea story, and evaluation ledger is implemented and tracked under R390. | done |
| Core evaluation readiness gate over RQ1/E1-RQ4/E4 reviewer evidence path, success criteria, failure narrowing rules, and prerequisite display gates is implemented and tracked under R391. | done |
| Profile-spec local-session, agent-trace, and standard-trace input replay regressions are implemented and tracked under R392, confirming that input paths, regex tag rules, standard-trace args, predicates, ranking, and stack-depth override are replayed through one profile-spec path. | done |
| Post-R392 reviewer acceptance closure is implemented and tracked under R393, including the resolved Chinese dataset-caption blocker and 4/4 final reviewer ACCEPT verdicts. | done |
| Two-abstraction documentation consistency gate after the Chinese guide field-derivation cleanup is implemented and tracked under R394. | done |
| Main claim and verdict alignment gate after the R380/R391 three-plus-one consolidation repair is implemented and tracked under R395. | done |
| Paper build smoke and accessibility gate for the Chinese and English drafts is implemented and tracked under R396. | done |
| Main-body run-ledger suppression gate over the writable Chinese draft plus English read-only gap handling, including internal checklist-style term suppression, is implemented and tracked under R397. | done |
| Current three-plus-one organization gate over exact Chinese RQ/E subsection count, E2/E3/E4 role boundaries, anti-run-ledger main body, internal checklist-style term suppression, paper-facing self-undercut wording, explicit new-run role assignment, main-display path visibility, anti-small-experiment next-action wording, and R405 English read-only gap handling is implemented and tracked under R398. | done |
| Tracked paper PDF freshness gate over the committed Chinese PDF, source display-path tokens, PDF text extraction, scoped non-claims, and R405 English read-only gap handling is implemented and tracked under R399. | done |
| English submodule read-only policy gate over the requested worktree, branch, AGENTS/CLAUDE policy, R405 gap handling, unstaged submodule dirty state, and direct-push safety is implemented and tracked under R409. | done |
| Flat/fixed/mapped stack ablation is tracked under R277. | done |
| Operation-stack quality scorer is implemented and tracked under R280. | done |
| Learned-from-labeled-fields op-map generation is implemented and tracked under R281. | done |
| Held-out split validation for generated op-map rules is implemented and tracked under R282. | done |
| Leave-dataset-out validation for generated op-map rules is implemented and tracked under R283/R284. | done |
| Recursive stack-depth sweep over identical operations is implemented and tracked under R286. | done |
| Large full-dataset conversion commands are not yet implemented for AndroidControl, AITW, official ToolBench, AgentRewardBench, SATraj capability, AgentNet Windows/macOS/full Ubuntu, full multi-platform ScaleCUA, UI-Vision, or VisualWebArena; Mind2Web still needs larger shard/raw-dump runs. | pending |
| Stronger true subtask/intent-boundary oracle expansion beyond R355's available labels remains pending; R355 covers session, operation/step, positive-run proxy, and OSWorld-Human `human_group`, but does not prove broad latent boundary discovery. | pending |
| R340 implements leave-task and leave-dataset visible policy-transfer validation over the current six-task R320/R339 suite; broader full-family conversions remain pending. | pending |
