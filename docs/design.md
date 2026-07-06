# Design

Last updated: 2026-07-06
Stage at update: stage 5 analyze / stage 6 claim gate / stage 9 paper integration
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `agent-session`, `script/agent_trace_to_operations.py`, `script/agent_trace_convert.py`, `script/agent_trace_exchange_eval.py`, `script/agent_trace_chrome_trace.py`, `script/agent_trace_chrome_exchange_eval.py`, `script/operation_boundary_backend_eval.py`, `script/boundary_family_calibration_eval.py`, `script/operation_query_utility_eval.py`, `script/operation_analyst_task_eval.py`, `script/operation_analyst_ranking_eval.py`, `script/operation_case_study_eval.py`, `script/operation_case_baseline_eval.py`, `script/operation_analyst_outcome_eval.py`, `script/operation_problem_value_synthesis.py`, `script/operation_where_filter_eval.py`, `script/operation_rust_rank_rule_eval.py`, `script/operation_rank_mode_eval.py`, `script/operation_rank_feature_eval.py`, `script/operation_rank_feature_ablation_eval.py`, `script/operation_rank_feature_robustness_eval.py`, `script/operation_profile_patch_eval.py`, `script/operation_boundary_profile_patch_eval.py`, `script/operation_oracle_depth_adequacy_eval.py`, `script/paper_core_experiment_consolidation_audit.py`, `script/paper_core_result_tables.py`, `script/paper_core_claim_evidence.py`, `script/paper_core_section_readiness.py`, `script/paper_visualization_portfolio.py`, `script/paper_claim_integrity_r356.py`, `script/paper_claim_synthesis.py`, `script/reviewer_evidence_packet.py`, `script/paper_value_novelty_synthesis.py`, `script/paper_claim_readiness_synthesis.py`, `script/paper_evidence_matrix_synthesis.py`, `script/paper_robustness_audit.py`, `docs/evaluation.md`, `agentpprof --profile-spec`
Completeness: partial

## Current State And Blocking Gate

Purpose: keep the current operation-stack profiler design aligned with the active
implementation.

AgentSight's profiler should expose only two core abstractions:
`operation` and `operation stack`. Prompt, tool call, process, file event,
network event, syscall, plan step, and subagent event can be concrete operation
records or derived operation fields. Session, span, task, and trace identifiers
are operation fields, exchange containers, or baseline shapes, not separate
profiler abstractions.

The current blocking gate is not more dataset breadth. R279-R294 show that
external labeled trajectories can be projected through the current Rust
implementation and folded at multiple depths. R320 is now the main empirical
gate for the profiling claim: hidden labels score profile groups after ranking
over 6 tasks, 4 oracle-rich datasets, 34,539 operations, and 3,699 positives.
R333/R334/R337/R339/R344/R355 add inspection-budget, fragmentation,
fixed-recall, sequence-scope, multi-metric, and oracle-depth checks, while
R354/R358 show profile-configuration actionability through executable profile
spec patches and boundary-derived fields. C3 remains partial because current
boundary evidence is deterministic or supervised field derivation, not
unsupervised discovery. Human or agent analyst evidence, broader automatic
boundary detection, and real producer span-tree imports are future expansion
gates, not blockers for the current scoped profiler-localization claim. R296
adds a reviewer evidence packet over
tracked/clean R282-R295 artifacts; it is a navigation layer over operation and
operation-stack outputs, not a new profiler abstraction. R297 adds the first
supervised boundary-backend expansion probe: the backend predicts
OSWorld-Human human-group boundaries on held-out sessions, writes
`learned_group_pattern` fields onto operations, and the existing Rust
operation-stack path folds those fields. R298 adds a paper-value and novelty
synthesis over tracked artifacts; it is an audit layer that maps real reviewer
problems to operation/operation-stack evidence, not a runtime abstraction. R299
adds the first boundary-family calibration pass over existing non-OSWorld
labels. It keeps the same extension point, but adds a design constraint:
boundary backends must pass a suitability/calibration gate for each target
oracle instead of being presented as one universal detector. R300 adds an
automated analysis-utility proxy: it converts existing labeled problems into
ordinary operations with fields such as `analysis_task` and `target_positive`,
then compares flat, fixed-session, semantic operation-stack, and label-drilldown
projections. These analysis tasks are not a third profiler abstraction; they are
evaluation labels over operation-stack queries. R301 makes the same boundary
more concrete for future analyst studies: visible task packets contain only
width-ranked operation-stack groups, while the hidden answer key stores oracle
labels separately. The packet and key are evaluation artifacts, not runtime
objects. R302 adds label-hidden ranking policies over the same grouped
operation-stack outputs. These policies sort groups by width, visible-risk, or
query-aware scores computed from ordinary operation fields; they are analysis
policies over operation-stack groups, not new profiler objects. R322 moves a
bounded version of that idea into Rust JSON output with visible `rank_rules`
over folded stack text; it is still a projection over operation-stack groups,
not a third abstraction or detector. R323 adds a rank-mode knob so the same
visible rules can be interpreted as width-boosted or score-first rankings; the
mode is an analysis policy over operation-stack groups, not a new object. R324
adds operation-level rank features: visible rules match mapped `field=value`
operation tokens and aggregate matched weight inside each folded stack group.
This makes group-feature ranking a policy over operations and operation stacks,
not a new profiler object. R325 and R326 keep the same boundary: ablation,
equal-weight, global-bank, and repaired rank policies change how existing
operation-stack groups are ordered and audited; they do not introduce a learned
ranker object or third profiler abstraction. R304 turns
those ranked groups into reviewer-facing case packets with a separate answer
key. R305 compares the same label-hidden packet construction against flat and
fixed-session views. A case remains a selected operation-stack or baseline
group plus visible examples; the answer key is an evaluation artifact, not a
runtime profiler abstraction.

## System-Under-Test Model

Purpose: define the evaluated artifact.

The evaluated artifact is the Rust `agentpprof` CLI. It reads either local
Codex/Claude session histories or already-normalized operation JSONL and emits
pprof, folded-stack, SVG, or JSON projections.

The data model is:

```text
agent-native transcript
  -> agent-session trace exchange format
  -> operation fields + weight
  -> optional operation-field mappings
  -> optional operation predicate
  -> user-selected operation stack frames
  -> weighted profile projection
  -> optional JSON rank projection over operation-stack groups
```

`--view` chooses which operations are sampled and how they are weighted.
`--op-map` and `--op-map-file` derive or overwrite operation fields before
stacking. `--where` selects a subset of operations after mapping and before
stacking. `--stack` chooses the recursive stack shape. `--stack-rule` is a
frame-local override for one projection. `--rank-rule` orders JSON profile
groups after folding by visible stack text; `--rank-op-rule` matches visible
mapped operation `field=value` tokens before folding and aggregates matched
operation weight inside each group; `--rank-mode` chooses whether width or
visible rule score is primary. None of these changes the sampled operations or
the stack abstraction.

## Core Abstraction: Operation

Purpose: define the only sample-level object.

An operation is a weighted observation with string fields. Examples include:

- a user prompt operation with `op=prompt`;
- an LLM call operation with `op=llm`;
- a tool/API operation with `op=tool`;
- a file, process, network, or system observation represented as operation
  fields;
- an external dataset action row normalized into operation JSONL.

An operation can be coarse or fine. A single prompt can be one operation, or a
sequence of prompts can be mapped into a higher-level intent/task field before
folding. The profiler should not privilege prompt/session boundaries.

## Core Abstraction: Operation Stack

Purpose: define recursive folding.

An operation stack is an ordered list of frames selected from operation fields.
The same operation sequence can be folded at multiple depths:

```text
project,dataset
project,dataset,task
project,dataset,task,phase
project,dataset,task,phase,op,tool
project,dataset,task,phase,op,tool,action,status
```

R286 validates this directly on the same 13,265 external operations: the unique
stack count changes from 9 at dataset depth to 57 at phase depth, 226 at
tool/semantic depth, 455 at action depth, and 3,757 when fixed session is added.
This is expected behavior: users choose the stack depth that matches the
question instead of accepting a fixed prompt/session hierarchy.

R289 extends the same model to SATraj-OS desktop computer-use traces. The stack
does not add a GUI, safety, prompt, or OS-specific object: `safety`,
`attack_type`, `status`, `action`, and `repeat_signal` are ordinary operation
fields that can be selected or omitted from the operation stack.

R290 extends the same model to OSWorld-Human human desktop trajectories. The
same single-action sequence can be viewed at action depth
(`...phase,op,tool,action,status`) or grouped-action depth
(`...phase,group_pattern,group_position,status`) by changing only `--stack`.
The benchmark's `human_group` labels are carried as operation fields for
evaluation and optional drilldown only when flattened `grouped-action` labels
exactly match the `single-action` sequence. Non-exact rows are marked through
`group_alignment` and remain usable for action profiling, but not for
grouped-boundary scoring. These labels are not a new profiler abstraction.

R291 extends the same model to AgentNet human desktop trajectories. The sampled
1,000 Ubuntu tasks produce 16,741 PyAutoGUI operations and can be folded with
frames such as `environment`, `phase`, `action`, `status`, `step_correct`,
`step_redundant`, and `repeat_signal`. Task outcome, alignment score,
efficiency score, difficulty, step correctness, and redundancy are operation
fields: they may be projected, scored, or omitted without introducing a
quality-label, desktop, or prompt/session abstraction.

R292 extends the same model to a supplemental ScaleCUA Ubuntu navigation stream
sample. The sampled 5,000 rows produce 5,000 computer-use operations across 131
sessions with `platform`, `environment`, `trajectory_type`, `history_state`,
and `history_depth` fields. This run is useful for proving previous-operation
context is still just operation data, but it is not a main boundary oracle
because the sampled subset is mostly click/terminate.

R293 packages the AgentNet operation-stack query as a reusable profile spec.
The spec references the existing R291 operation JSONL and op-map file, produces
the same 16,741-operation / 608-stack diagnostic projection, and a CLI stack
override on the same spec folds the identical operations into 83 coarser
stacks. This validates reproducible configuration without adding a profile-spec
object to the paper model: the evaluated objects remain operations and
operation stacks.

R294 adds a filesystem-normalized trace exchange step for local agent sessions. The
`agent-session` crate owns the `agentsight.agent-session.trace.v1` schema and
now exposes parse/serialize helpers on `AgentTrace`; `agentpprof --export-trace`
writes that parsed IR, `agentpprof --trace-file` imports it, and
`script/agent_trace_convert.py to-operations` converts it to operation JSONL.
On the public Codex fixture, trace import and operation-file import both produce
6 samples / 5 stacks with byte-identical folded output under the same stack
spec. R303 adds `script/agent_trace_exchange_eval.py` as a one-command
reproducer for export, import, conversion, portability checks, and folded-output
equality. Exported traces use trace-local session paths, `cwd=repo`, path-grouped
files, and command names rather than full raw shell text; prompt and LLM previews
remain parsed transcript summaries outside this portability check. This is
an interoperability layer before operations, not a profiler abstraction. R306
adds a Chrome Trace Event JSON bridge, with `script/agent_trace_convert.py`
as the user-facing import/export entrypoint and
`script/agent_trace_chrome_trace.py` as the lower-level implementation:
the same fixture exports to a Perfetto/Chrome-readable `traceEvents` file,
imports back to operation JSONL, and produces the same 6 samples / 5 stacks and
byte-identical folded output as direct trace and direct operation imports.
R353 adds the symmetric operation-file export path in the maintained Rust CLI:
a deterministic 512-row prefix of the tracked R324 real labeled
visible-operation corpus exports to 512 Chrome events, imports through
`--standard-trace-file`, and preserves 512 samples / 11 stacks with
byte-identical folded output. Chrome trace is a standard exchange container;
after import the profiler still sees only operations and operation stacks.

R297 adds a supervised adjacent-boundary backend over OSWorld-Human. The model
is deliberately outside the core profiler abstraction: it reads adjacent
operation fields, excludes oracle/group labels from features, predicts held-out
human-group boundaries, and writes derived fields such as
`learned_group_pattern`, `learned_group_position`, and `learned_boundary_prev`
back onto operations. `agentpprof` then folds the augmented operation file with
the ordinary stack
`project,dataset,task,phase,learned_group_pattern,learned_group_position,action,status`.
This validates the intended extension point for boundary detection: backends
derive operation fields, while recursive folding remains an operation-stack
query.

R299 extends that extension point across existing labeled families and makes
calibration part of the contract. The same backend pattern writes
`learned_segment_pattern`, `learned_segment_position`, and
`learned_boundary_prev` fields for OSWorld-Human, AgentNet, and
AgentRewardBench held-out operations, then `agentpprof --profile-spec` folds
the augmented JSONL as ordinary operation stacks. The result is intentionally
not a universal-boundary claim: AgentNet step-quality boundaries are difficult
and low-precision, AgentRewardBench looping is better handled by a simple
`repeat_signal_change` baseline, and SATraj safety is a per-trajectory field
rather than an adjacent boundary in the current sample.

R300 evaluates whether those operation-stack choices help on real labeled
analysis tasks. It uses existing AgentRewardBench, SATraj-OS, AgentNet, and
OSWorld-Human operations to define 6 oracle-backed tasks, then writes a combined
operation file and four reproducible profile specs. The compared views are just
different stacks over the same operations: `analysis_task,dataset` for flat,
`analysis_task,dataset,session` for fixed-session, semantic fields for
operation-stack, and `target_positive` for label-drilldown. The result supports
inspectability and cross-session aggregation, not human productivity.

R301 evaluates the same tasks under a stricter browsing contract. The script
writes `visible-task-packets.json` without oracle-positive fields and
`answer-key.json` with hidden labels, then scores width-ranked top-k and
operation-budget inspection. This keeps the design honest: if a result depends
on `target_positive`, it belongs to the answer key or label-drilldown baseline,
not to the default operation-stack view.

R302 evaluates non-flamegraph ranking policies over those same operation-stack
groups. Width ranking follows flamegraph area, visible-risk ranking uses
operation fields such as `status`, `repeat_signal`, `phase`, `action`, and
`environment`, and query-aware ranking changes the weights for the analyst's
task. The script explicitly excludes oracle fields such as `looping`, `safety`,
`step_correct`, and `target_positive` from non-oracle rankers. The design point
is that ranking is another projection over operations and operation stacks,
just like mapping or stack selection.

R354 turns one piece of that ranking/actionability design into an executable
profile-spec patch loop. It starts from the same visible operation file, writes
default semantic-width specs and patched specs that change only stack depth and
visible operation-level rank rules, runs Rust `agentpprof --profile-spec`, and
scores with hidden labels only after profiling. Five of six patches improve AP,
top-5 lift, and first-positive work; the OSWorld-Human patch is rejected and
points to boundary-derived fields. A rejected patch is still a design signal:
boundary backends should derive operation fields, while the profiler continues
to fold operation stacks. The patch plan, profile spec, and report are
reproducibility wrappers, not new profiler abstractions. R354 is not an
automatic patch selector; it shows that a profiler-guided edit can be replayed
and scored on the same visible operation input.

R358 tests the design implication of the R354 OSWorld-Human rejection. The
boundary backend still does not become a profiler object: it writes
`learned_group_pattern`, `learned_group_position`, and related fields onto
held-out operations, and the profiler folds those fields through ordinary
profile specs. The learned-boundary stack improves held-out AP and reduces
groups, but worsens top-5 operation work and first-positive work. This keeps
the design claim scoped to boundary-derived operation fields as an actionable
knob, not complete intent-boundary recovery.

R355 evaluates the same operation-stack outputs at finer oracle depths without
changing the model. It reads existing labeled operations and already-defined
visible policies, then scores selected groups as session units, operation/step
units, contiguous positive-run proxy units, and task-specific units such as
OSWorld-Human `human_group`. These unit depths are scoring coordinates over
operations, not profiler objects. The design implication is conservative:
recursive folding exposes a measurable depth-aware triage surface, but
positive-run proxies and session-level labels do not become human intent
boundaries. R355 does not support automatic boundary discovery; the depth-gap
counterpoint versus fixed-session remains explicit.

R356 audits these newer R354/R355 claims against the same two-object design
boundary. It reads the R354/R355 artifacts and the current papers, then checks
that profile-spec patches, oracle-depth unit rows, case packets, and audit
reports remain wrappers around operation fields and operation stack queries.
It is a claim-integrity layer, not another profiler abstraction.

R359 audits the paper-facing experiment structure against that same boundary.
It checks that the evaluation is organized as three empirical profiling
experiments plus one artifact/reproducibility block, while R-numbered runs
remain provenance, ablations, counterpoints, or audit gates. It also checks
that R358 is an E3 mechanism/actionability ablation, not a fifth experiment or
an automatic boundary detector. This keeps the design claim centered on
operation and operation stack rather than on a collection of one-off artifacts.

R360 audits the paper table that summarizes those four paper-facing blocks. It reads
tracked artifacts and emits the RQ1/E1-RQ4/E4 headline table plus metric rows. The
table is a provenance view over existing operation/operation-stack evidence,
not another profiler abstraction, visualization primitive, or result source.

R361 audits the claim-evidence layer for those same four paper-facing blocks. It reads
tracked R320/R352/R354/R355/R357/R358/R359/R360 artifacts and emits a ledger
that binds each RQ/E block to its claim, research question, oracle, baselines,
primary metrics, headline result, actionable insight, counterpoint, and scoped
paper wording. The ledger is a reviewer-facing report over operation and
operation-stack evidence. Prompt, session, tool, process, syscall, safety, and
human-boundary concepts remain operation fields, labels, or baselines rather
than profiler objects.

R362 audits that this ledger is visible in the paper body, not only in generated
tables. It extracts the Chinese and English RQ1/E1-RQ4/E4 result sections and checks for
claim/oracle/baseline/metric/counterpoint structure, localization metrics,
actionability language, and must-not-claim guardrails. This is a narrative
readiness gate over existing operation/operation-stack evidence. It does not
introduce a section, claim, or table as a profiler abstraction.

R363 packages the same RQ1/E1-RQ4/E4 evidence into multiple paper visualizations:
baseline tradeoff, metric heatmap, diagnostic lenses, actionability knobs, and
oracle-depth adequacy. The design point is that visualization choice is another
report projection over operations and operation stacks. Flamegraphs, heatmaps,
case packets, drilldown tables, and actionability cards are presentation views;
they do not add a third profiler abstraction or change the scoped claim.

R304 evaluates the presentation boundary for those ranked groups. It writes
`visible-case-packet.json` with stack frames, visible feature rates, hashed
session examples, and example operations. It writes oracle positives only to
`answer-key.json`. The design invariant is that a case packet is not a third
object type; it is a report over operation-stack groups with hidden scoring
separated for evaluation.

R305 keeps the same invariant while adding baselines. It writes cross-view
visible packets for `flat`, `fixed_session`, and `operation_stack`, then scores
them only through a hidden answer key. The result is intentionally mixed:
operation stacks reduce median inspected work versus flat packets and improve
median lift versus fixed-session packets, but they do not dominate fixed-session
inspection work on every task.

R307 then reads R295/R298, R303, and R300-R306 artifacts to refresh the paper
claim gate. Its verdicts keep the abstraction boundary explicit: C1/C2 mechanism
claims are ready under scoped wording, C3 remains partial for field derivation,
and C4 is only an automated inspectability proxy until a controlled analyst
study runs over existing visible packets and hidden answer keys. R307 is a
review synthesis artifact, not a runtime profiler abstraction.

R308 reuses the R305 visible packets and hidden answer key as an analyst-outcome
proxy. It scores first-positive evidence, first enriched evidence, and high-lift
groups across flat, fixed-session, and operation-stack packets. This is another
evaluation report over operations and operation stacks: the profiler still has
only the operation record and the operation-stack query, while packets, answer
keys, and outcome reports remain review surfaces.

R309 synthesizes the existing R298/R300/R302/R305/R308 artifacts into
reviewer-facing real-problem value cards. Each card keeps the same abstraction
boundary: failure, safety, step-quality, and human-boundary tasks are ordinary
operation fields and operation-stack reports, while the synthesis only explains
where operation stacks help, where fixed-session drilldown remains cheaper, and
which claims remain unsupported.

R310 reads the tracked R307 claim gate and R309 problem-value synthesis to emit
a paper evidence matrix. It is an audit surface over existing artifacts: C1,
C2, and C4 become scoped paper-ready rows, C3 remains partial, and the
must-not-claim list stays explicit. It does not add a profile object, exchange
object, task object, or visualization object to the runtime model.

R311 reads the tracked R302/R305/R308/R309/R310 artifacts and emits a
reviewer-stress audit. It keeps the same two abstractions, then asks whether
the current evidence survives common reviewer attacks: operation stacks are more
selective than flat packets on 6/6 tasks, contain positive groups on 6/6 tasks,
and contain high-lift evidence on 5/6 tasks, but only beat fixed-session on
selected work in 2/6 tasks. This makes the design claim stricter: operation
stacks provide a configurable inspectability tradeoff, not universal dominance
over fixed-session drilldown.

## Mapping And Tagging

Purpose: align mapping/tagging with the two-abstraction model.

Mapping and tagging are first-class ways to derive operation fields. They do not
create a third profiler object. The current regex backend is deliberately close
to shell-style filtering: rules match the searchable `key=value` text of an
operation and write labels such as `task=web` or `phase=navigate`.

The intended contract is:

- mappings run before stack construction;
- later mappings can match fields derived by earlier mappings;
- first match wins per destination field;
- `--where FIELD=REGEX` and `FIELD!=REGEX` predicates run after mappings and
  before stack construction, so they select a query subset without creating a
  new object type;
- operation-family mappings must run before generic action-verb mappings;
- stack specs remain independent of the mapping backend;
- learned mappings can be generated from labeled traces and reused through the
  same `--op-map-file` path.
- learned boundary backends can write derived fields such as
  `learned_group_pattern` before stack construction, but they do not create a
  boundary object in the profiler.
- `--profile-spec` may bundle `--view`, `--stack`, `--op-map-file`,
  `--operation-file`, `where_rules`, output, and project metadata for
  reproducibility, but command-line rules still override spec defaults and no new profiler
  abstraction is introduced.

R285, R289, R290, R291, R292, and R293 are the current regression tests for mapping
precedence. Tool/API operations should derive `phase=api` from tool/API
structure before generic verbs such as `search` or `create`; desktop
computer-use operations should derive `phase=input` for `key`/`type` before
generic web rules map `type` to `modify`; desktop clicks such as AgentNet
`tripleClick` should normalize into the existing navigate family; OSWorld-Human
grouped-action patterns should be derivable from validated action sequences and
group metadata without binding stacks to prompt/session boundaries; ScaleCUA
history state and depth should remain selectable fields rather than a new
trajectory-history object; profile specs should make those choices repeatable
without freezing the stack shape; learned boundary fields such as R297's
`learned_group_pattern` should be stackable fields, not a separate boundary
abstraction. R321 adds the implementation-level query-predicate regression:
profile specs use mapping-derived `task_family` fields plus `where_rules` to
select AgentRewardBench looping and SATraj safety subsets from the same R300
operation JSONL, and folded counts match the expected 729/729, 714/714, and
4,285/4,285 samples. This is ordering over operation fields and query
configuration, not a separate abstraction. R322 adds visible rank-rule
profile specs that sort the JSON operation-stack groups emitted by Rust; the
emitted order is scored offline with hidden labels that are not passed to Rust
ranking. AP improves over width on 4/6 tasks, but the SATraj and side-effect
counterexamples show that binary stack-text boosts are not a substitute for
richer query-aware group features.
R323 follows that counterexample by adding `rule-score` ranking: SATraj's
first-positive work drops from 0.6376 to 0.0842 relative to `width-boost`, but
side-effect and OSWorld-Human remain counterexamples, so rank mode is a useful
policy knob rather than a universal detector.
R324 closes more of the R320 implementation gap by aggregating visible
operation-level rank features inside stack groups. The harness derives a
scrubbed visible-operation JSONL from the tracked R300 source before invoking
Rust, so oracle fields are available only to the offline scorer. On that
profiler input, semantic-stack `rank_op_rules` improve AP over width on 5/6
tasks, top-5 lift on 4/6, and first-positive work on 5/6. The coarse-stack
variant reduces group counts while still improving AP on 4/6 tasks and
first-positive work on 5/6, reinforcing that stack depth and rank policy are
task-dependent knobs. OSWorld-Human remains a counterexample because it needs
boundary-derived fields.
R325 isolates those knobs with leave-one-feature-out Rust profile specs. It
finds 7 critical feature instances and 3 misleading feature instances, and it
shows coarse stack depth is AP-preferred on only 2/6 tasks while reducing group
counts on all 6. The design implication is to expose feature rules, rank modes,
and stack depth as configurable policies over operation stacks rather than
shipping one fixed hierarchy or one universal ranker.
R326 tests the robustness of that implication. Equal-weight task policies stay
within 0.02 AP of weighted policies on 8/12 task/depth variants, and a global
equal-weight visible feature bank beats width on 4/6 semantic and 5/6 coarse
tasks. R325-guided repairs improve AP on 2/3 misleading-feature cases and
first-positive work on 2/3 cases; 1/3 improves both metrics. The resulting
design rule is to expose default global
feature banks plus task-specific overrides, while treating repair from
offline-scored ablations as a paper/actionability workflow rather than a
deployment-time label-free ranker.

## Assumptions And Invariants

Purpose: name the design constraints that tests should protect.

- All profile outputs must be derivable from operations and operation stacks.
- Local-session projections and external operation JSONL must share the same
  stack construction path.
- Agent-session trace import/export and operation-file standard-trace export
  must be loss-bounded exchange paths that return to operation JSONL semantics
  before profiling; standard trace containers such as Chrome Trace Event JSON
  must import into operations rather than bypassing the operation abstraction.
- Adding `session`, `prompt`, `tool`, `process`, or `path` to a stack is a user
  projection choice, not a hard boundary in the profiler.
- Mapping rules must be visible and reproducible, either inline or in tracked
  files.
- Raw external samples stay outside git under `.agentsight/`; tracked artifacts
  contain folded stacks, summaries, and redacted analysis outputs.

## Design Risks And Validation Hooks

Purpose: keep open risks tied to experiments.

| Risk | Validation hook | Current evidence |
|---|---|---|
| Prompt/session boundaries leak back into the abstraction. | Run fixed-boundary ablations against recursive stacks. | R277 and R286 show fixed session greatly fragments stacks. |
| Hand-written mappings overfit one dataset family. | Held-out and leave-dataset-out mapping evaluation plus operation-family precedence checks. | R282-R285 cover held-out sessions and 9 leave-out datasets; R289/R290/R291 add desktop computer-use precedence checks; R292 adds a supplemental GUI history-depth field check. |
| Action labels are too shallow as boundary oracles. | Add step-instruction, solution-path, outcome, side-effect, looping, repetition, safety/attack, grouped-action, step-quality, and failure-label scorers. | R287 adds tau-bench outcomes and expected task actions; R288 adds AgentRewardBench expert success, side-effect, looping, optimality, and action-derived `repeat_signal` fields; R289 adds SATraj safety and attack labels; R290 adds OSWorld-Human grouped-action boundary labels; R291 adds AgentNet step correctness and redundancy labels. AndroidControl and TRAIL remain deeper oracle candidates. |
| Boundary detection remains only deterministic mapping. | Evaluate learned boundary backends that derive operation fields before stack construction and compare against held-out human or dataset boundaries; require suitability and calibration checks per oracle family. | R297 trains a supervised adjacent-boundary backend on OSWorld-Human, excludes oracle/group fields from features, reaches held-out human-group F1 0.7735, and folds predicted `learned_group_pattern` fields through Rust `agentpprof`. R299 applies the same pattern to OSWorld-Human, AgentNet step-quality labels, and AgentRewardBench looping; it finds mixed results and keeps SATraj/ScaleCUA/tau-bench out of the trained set when they lack suitable adjacent boundary oracles. This is still supervised and family-specific, not unsupervised discovery. |
| Human-facing value remains unmeasured. | First score profiler outputs directly against dataset-provided hidden labels; run a controlled human/agent analyst study only for productivity, time-to-answer, or analyst-accuracy claims. | R320 is the current C4 gate: over 6 tasks, 4 oracle-rich datasets, 34,539 operations, 3,699 positives, and 144 policies, operation-stack query-aware top-5 groups inspect median 0.0937 work versus flat's 1.0, improve top-5 recall over fixed-session on 5/6 tasks, and reduce median groups from 285.0 to 157.5. R333/R334/R337 add work-budget, fragmentation, and fixed-recall checks; R339/R355 score session, operation/step, positive-run, and task-specific oracle depths; R344 shows the metric surface is a tradeoff rather than dominance. R354/R358 show profile-configuration actionability through executable profile-spec and boundary-field patches. This supports profiler fidelity/localization/actionability, not human productivity. |
| Profile experiments remain ad hoc shell commands. | Bundle reproducible operation-file, op-map, view predicate, stack, rank policy, and output choices in profile specs while preserving CLI overrides. | R293 adds an AgentNet profile spec that reproduces the R291 608-stack diagnostic profile and folds the same operations into an 83-stack override view. R321 adds `where_rules` profile specs over the R300 real labeled operation JSONL and confirms mapping-derived predicates select 729, 714, and 4,285 operations before stack folding. R322 adds `rank_rules` profile specs and Rust JSON ranked groups over the same task suite. R323 adds `rank_mode` profile specs for width-boost versus rule-score ranking. R324 adds `rank_op_rules` profile specs for operation-level feature-density ranking over a scrubbed visible-operation profiler input. R325 adds leave-one-feature profile specs to isolate critical and misleading rank features. R326 adds equal-weight, global-bank, and ablation-repaired profile specs to test rank-policy robustness. |
| Local agent sessions and external operation files are hard to exchange or replay outside native logs. | Export parsed sessions as `agentsight.agent-session.trace.v1`, import them through `--trace-file`, convert them to operation JSONL, and bridge session or operation-file inputs through a standard trace container when needed. | R294 public Codex fixture smoke shows direct trace import and converted operation-file import produce identical folded stacks; R303 scripts the same bridge as a tracked reproducer and verifies filesystem/tool-command portability for the exported trace. R306 exports the same fixture to Chrome Trace Event JSON, imports it back to operation JSONL, and preserves the same 6 samples / 5 stacks folded output. R353 exports a tracked real labeled operation prefix to Chrome Trace Event JSON and imports it back with byte-identical 512-sample / 11-stack folded output. |
| Paper claims drift away from tracked artifact evidence. | Mechanically synthesize claim verdicts, reviewer value, novelty, evidence matrices, reviewer-stress audits, and remaining gaps from tracked result JSON/folded artifacts while keeping unsupported claims explicit. | R295 reads R282-R294 artifacts and emits supported/partial verdicts plus unsupported final claims under `docs/visexp/out/paper-claim-synthesis-r295/`; R296 indexes those verdicts with reviewer questions, derived ratios, and source paths; R298 maps 6 real-problem evidence blocks and 4 novelty claims to tracked artifacts while marking unsupervised intent discovery and developer productivity as unsupported; R307 refreshes the post-utility claim gate; R310 turns R307/R309 into JSON/Markdown/CSV/TeX/HTML paper evidence matrix outputs; R311 turns R302/R305/R308/R309/R310 into a reviewer-stress matrix with explicit pass/narrow/partial/fail-for-stronger-claim verdicts. |
| Visualizations collapse back to flamegraphs only. | Generate tree, transition, top-field, quality, grouped-stack, history-depth, depth-sweep, case-packet, cross-view case-baseline, analyst-outcome, problem-value, reviewer-stress, and reviewer-navigation HTML/JSON reports. | R273-R296 include non-flamegraph analyses, reproducible profile specs, trace-exchange smoke tests, and an 11-entry evidence packet under `docs/visexp/out/reviewer-evidence-packet-r296/`; R304 adds a visible case-packet plus answer-key report over operation-stack groups, R305 adds flat/fixed/operation cross-view case-packet baselines, R308 adds a first-evidence analyst-outcome report, R309 adds real-problem value cards, and R311 adds task-level robustness and reviewer-stress HTML/JSON/CSV/TeX views. |
