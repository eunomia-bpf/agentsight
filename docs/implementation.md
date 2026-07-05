# Implementation

Last updated: 2026-07-04
Stage at update: stage 4 execute / stage 8 audit / stage 11 reproducibility prep
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `agentpprof/src/standard_trace.rs`, `agentpprof/tests/standard_trace_cli.rs`, `script/operation_*.py`, `script/agent_trace_datasets.py sample tau-bench-trajectories`, `script/agent_trace_datasets.py sample agent-reward-bench`, `script/agent_trace_datasets.py sample satraj-os-safety`, `script/agent_trace_datasets.py sample osworld-human`, `script/agent_trace_datasets.py sample agentnet`, `script/agent_trace_datasets.py sample scalecua-navigation`, `script/agent_trace_exchange_eval.py`, `script/agent_trace_chrome_exchange_eval.py`, `script/operation_where_filter_eval.py`, `script/operation_rust_rank_rule_eval.py`, `script/operation_rank_mode_eval.py`, `script/operation_rank_feature_eval.py`, `script/operation_rank_feature_ablation_eval.py`, `script/operation_rank_feature_robustness_eval.py`, `script/implementation_consistency_audit.py`, `cargo test --manifest-path agentpprof/Cargo.toml`
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
| `agent-session/` | Shared local Codex/Claude session parser. | maintained |
| `script/agent_trace_datasets.py` | External labeled trajectory samplers and operation JSONL normalization. | research harness |
| `script/agent_trace_exchange_eval.py` | Reproducible agent-session trace export/import/conversion equality check. | research harness |
| `script/agent_trace_chrome_exchange_eval.py` | Reproducible Chrome/Perfetto-style trace exchange equality check. | research harness |
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
| `script/implementation_consistency_audit.py` | R319 implementation/docs consistency audit over Rust CLI, docs, and paper wording. | paper hygiene harness |
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
- frame-local stack overrides via `--stack-rule`;
- reusable profile specs via `--profile-spec`;
- portable local agent-session trace import/export via `--trace-file` and
  `--export-trace`;
- Chrome Trace Event import/export via
  `--standard-trace-file` and `--export-standard-trace`;
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

Local trace exchange is also implemented through the maintained Rust path.
R294/R303 show `agentsight.agent-session.trace.v1` export/import and operation
JSONL conversion preserve the same 6-sample / 5-stack folded output on the
public Codex fixture. R306 adds a Chrome Trace Event JSON `traceEvents` bridge
that is Perfetto-readable in the fixture path: `agentpprof` exports the same
fixture with `--export-standard-trace`, imports it with
`--standard-trace-file`, and folds the imported events as ordinary operations.
The CLI test in `agentpprof/tests/standard_trace_cli.rs` covers this
standard-trace round trip. Real OpenTelemetry, OpenInference, or Perfetto
producer traces remain an open compatibility gate.

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
outputs. They are not an alternate semantic-profiler implementation.

## Build And Test Commands

Purpose: make the current runnable path explicit.

```bash
cargo test --manifest-path agentpprof/Cargo.toml
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
  script/agent_trace_exchange_eval.py script/agent_trace_chrome_exchange_eval.py \
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
| Execute the controlled human/agent analyst study from R315/R316/R317. | The current C4 evidence is an automated proxy; productivity, accuracy, time-to-answer, and user utility remain unsupported. | pending |
| Import one real OpenTelemetry GenAI, OpenInference, or Perfetto trace from another agent tool. | R306 proves a standard trace container round trip on a fixture, not compatibility with real producer traces. | pending |
| Add converters for the best next trajectory sources: UI-Vision, OSWorld-Verified/OSWorld 2.0 trajectories, and VisualWebArena trajectories. | Future expansion beyond the current 15 sources should be driven by stronger oracles, not dataset count alone. | pending |
| Scale tau-bench beyond the R287 `gpt-4o-mini` 50-episode sample. | Multi-model tau-bench trajectories can support outcome/failure and model-comparison analysis. | pending |
| Scale AgentRewardBench beyond the R288 38-trajectory lightweight sample. | Expert side-effect and looping labels are sparse; larger balanced sampling is needed for paper-grade failure diagnostics and better sequence-derived repetition rules. | pending |
| Scale SATraj-OS beyond the R289 safety sample and revisit the capability config. | Desktop computer-use is now represented, but capability rows were not fully readable through Dataset Viewer and need a heavier access path. | pending |
| Add stronger non-flamegraph comparison reports for any new datasets or stack-depth questions. | The current scoped paper already has tree, transition, quality, boundary, case-packet, frontier, reviewer-stress, and claim-audit reports, but future expansion should keep adding non-flamegraph views rather than only folded stacks. | current scoped set covered by R273-R318; future expansion pending |
