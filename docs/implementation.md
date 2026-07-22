# AgentProf Implementation

## Current Artifact

The implemented artifact is the Rust crate and CLI under `agentpprof/`, version
`0.2.37` in `agentpprof/Cargo.toml`. Its package description is a pprof-style
semantic profiler for local AI coding-agent sessions. It also accepts explicit
operation files and supported trace containers used by repository experiments.

This file records implemented reality. The exact pre-recovery implementation
history is archived at
`docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/archive-pre-recovery/implementation.md`.

## Source Layout

| Path | Role |
|---|---|
| `agentpprof/src/main.rs` | CLI, profile-spec loading, source selection, mapping/filter options, and the sole pprof output route |
| `agentpprof/src/profile.rs` | operation records, operation-stack configuration, mappings, filters, folding, pprof encoding, and stack induction |
| `agentpprof/src/session.rs` | local agent-session ingestion |
| `agentpprof/src/standard_trace.rs` | Chrome/Perfetto Trace Event input normalization through operation records |
| `agentpprof/src/tagger.rs` | optional open-vocabulary and declared-label tagging support |
| `agentpprof/tests/profile_spec_cli.rs` | pprof-only CLI/profile-spec/mapping/filter/induction integration tests |
| `agentpprof/tests/standard_trace_cli.rs` | standard-trace input and alternative-output rejection tests |
| `agentpprof/backend/python/` | archived clustering prototype; not a product backend or output path |
| `agentpprof/examples/` | public fixture and usage material |
| `script/hodoscope_representation_eval.py` | thin official-data adapter for the completed matched Hodoscope/flat/turn/recursive experiment; not a core AgentProf subsystem |
| `script/hintbench_profile_localization_eval.py` | thin official-data adapter, real-AgentProf runner, baseline scorer, and result reporter for the completed HINTBench experiment; not a core AgentProf subsystem |
| `script/r315_llm_reader_eval.py` | thin rank-hidden packet collector and post-collection scorer for the completed fixed-reader RQ2 experiment; not a core AgentProf subsystem |
| `script/rq1_codetracebench_token_attribution_eval.py` | complete CodeTraceBench ordinary and resource-weighted B-cubed attribution evaluator; not a core AgentProf subsystem |
| `script/rq3_codetracebench_stage_fidelity_eval.py` | complete CodeTraceBench coarse and multi-resolution recurrence evaluator over fixed trajectories; not a core AgentProf subsystem |
| `script/rq2_same_signal_diagnostic_decomposition.py` | complete three-workload standard-MAP, fixed-budget, atomic/raw/session decomposition over retained diagnostic signals; not a core AgentProf subsystem |
| `script/rq2_local_first_semantic_ranking.py` | adaptive evaluation-only local-first semantic tie-refinement and matched local-plus-raw comparison; not the release ranking path |
| `script/rq3_recurrence_stack_induction_eval.py` | fixed five-fold Python development adapter and scorer for the completed recurrence-induction experiment |
| `script/rq3_recurrence_stack_rust_equivalence.py` | mechanical full-population verifier for Python/Rust boundary, segment, motif, and mass equivalence |
| `script/rq3_reference_calibrated_existing_traces_eval.py` | completed Step 0030 adapter for one grouped-reference scalar on the retained OSWorld-Human and CodeTraceBench trajectories |
| `script/rq3_reference_calibrated_rust_equivalence.py` | complete release-binary verifier for the optional calibrated path's cutoffs, decisions, segments, and motifs |
| `script/rq3_source_native_task_progress_boundary_eval.py` | Step 0053 source-native reconstruction and fixed adjacent-boundary development evaluator; not a core AgentProf subsystem |
| `script/rq3_stateful_native_turn_task_stack_eval.py` | Step 0054 source-native turn reconstruction, legal variable-depth task-stack inference, and standard score-only evaluation; not a core AgentProf subsystem or release constructor |
| `script/rq3_stateful_visible_path_identity_eval.py` | Step 0055 score-only audit of exact profiler-visible task-label paths versus hidden occurrence identity and recurrence; not a model backend or core AgentProf subsystem |
| `script/rq3_global_task_semantic_segmentation_eval.py` | Steps 0057--0058 whole-trajectory task-semantic adapter, persistent task-occurrence scorer, fixed-model identity check, and failed-output renderer; not a model backend, release constructor, or paper figure source |
| `script/rq3_well_nested_task_stack_eval.py` | Step 0059 literal `stay`/single-leaf `push`/single-leaf `pop` online task-stack evaluator and standard scorer; not a model backend, release constructor, or paper figure source |

## Implemented Pipeline

The maintained Rust path implements:

```text
local Codex/Claude sessions, operation JSONL, or supported trace input
  -> operation records with string fields and weights
  -> inline/file-backed field mappings
  -> field predicates
  -> declared or induced operation stack
  -> weighted folding
  -> weighted semantic stack and evidence labels
  -> one standard .pb or .pb.gz pprof
```

The Rust inducer now constructs operation identities from cross-session action
recurrence. It counts adjacent action transitions in a reference population,
computes normalized pointwise mutual information (NPMI) with left and right
marginals from that same transition sample space, and separates low- from
high-association transitions with deterministic occurrence-weighted
one-dimensional two-means. It fits that calibration globally and over
action-changing occurrences. Same-action decisions use the global midpoint;
action-changing decisions use `min(global, cross-action)`. This parameter-free
constraint can remove a global-rule boundary but cannot add one. An unseen
transition or a score strictly below its applied midpoint starts a new segment;
otherwise the current segment continues. When every reference and target
operation has a nonempty `action_detail`, the inducer fits the identical model
to `(action, action_detail)` transitions. Detailed continuity may remove a
coarse boundary but cannot add one; missing, unseen, or weak detail falls back
exactly to the coarse decision. Each resulting frame is the
run-length-compressed action sequence of its segment, so the same recurring
motif receives the same cross-session identity.

An optional supervised path keeps the same NPMI model but fits one scalar
cutoff from disjoint grouped historical operations. The CLI accepts those rows
through `--induce-calibration-operation-file` only when a separate
`--induce-reference-operation-file` supplies the score-reference corpus. The
fitter enumerates the finite score intervals and maximizes per-operation
B-cubed F1 over the reference `group` assignments, giving every operation one
vote regardless of profile resource value and choosing the smallest cutoff on
an exact tie. It never accepts target groups or a user-selected numeric
cutoff. Omitting calibration preserves the label-free constructor and its
serialized report.

Automatic induction requires exactly one nonempty `session` and one nonempty
`action` value per operation. It uses input order within each session and gives
each adjacent transition one count; operation weights remain additive profile
measures and do not alter motif learning. `--induce-reference-operation-file`
may supply a separate label-free reference corpus. Missing fields, a population
with no transitions, a degenerate score distribution, or failed two-means
separation is an explicit error rather than a fallback. The old information-
gain objective and its depth, query, and session options are not runtime
alternatives; supplying those legacy knobs with recurrence induction is
rejected. TF-IDF/K-Means belongs only to the optional Python rule-authoring
backend. The built-in time view weights a timestamped operation by elapsed time
to the next recorded event rather than by an independently recorded operation
duration.

Implemented CLI capabilities include:

- `--profile-spec` for repeatable source, view, mapping, filter, stack,
  tagging, and output choices;
- repeated `--task-choice TAG=DESCRIPTION` with the LLM tagger for assigning a
  separate canonical task field while preserving the raw open-vocabulary tag;
- `--op-map` and `--op-map-file` for derived operation fields;
- `--where` for operation predicates after mapping and before folding;
- `--stack` and `--stack-rule` for declared stack construction;
- `--induce-operation-stack` for cross-session recurrence-based operation
  identity, with optional label-free reference operations from
  `--induce-reference-operation-file` and optional disjoint grouped calibration
  operations from `--induce-calibration-operation-file`;
- Chrome/Perfetto Trace Event import through operations;
- exactly one standard pprof artifact per successful invocation.

The exact CLI remains authoritative; use `cargo run --manifest-path
agentpprof/Cargo.toml -- --help` before copying a command into a paper or
experiment plan.

Step 0031 adds the declared-label path without replacing the existing tagger.
Each session retains its raw `session_tag` and receives a separate `task_tag`
only when at least two `--task-choice` values are supplied. The canonical task
field flows through session JSON, standard trace, operation construction, and
stack projection. `--no-cache` now disables cache loading, in-memory hits, and
writes. A step-level outer audit found that the experimental optional branch
stored both fields but had reused the task request for the raw tag. The release
path now preserves the original raw request (`session`, title/CWD/prompt,
source/model hints) and issues the goal-only declared task request separately;
the latter is byte-equivalent to the request scored in the complete AgentBoard
experiment. Sixty-two Rust and CLI tests, including a request-contract test,
plus Clippy pass after the repair.

## What Is Not Implemented

The current artifact does not implement the reviewer-generated mechanism stack
from the pre-recovery paper, universal unsupervised intent/failure discovery, or
automated repair and analyst recommendation. Detailed discarded mechanism names
and specifications remain only in the timestamped recovery archive.

These must not appear as achieved system contributions. Existing mapping,
ranking, and stack-induction options may serve as experimental policies, but
their presence does not establish diagnostic value.

## Build And Test

From the repository root:

```bash
cargo build --manifest-path agentpprof/Cargo.toml --locked
cargo test --manifest-path agentpprof/Cargo.toml --locked
cargo run --manifest-path agentpprof/Cargo.toml -- --help
```

Public-fixture smoke and package/install scripts exist under `docs/visexp/`.
They are useful artifact checks, not substitutes for the paper's full real
experiment.

## Input And Output Boundaries

- Private raw local histories remain outside committed public artifacts.
- Experiments should use explicit, source-documented inputs and record the
  command, versions, mapping/profile specification, and raw output path.
- Public benchmark outcome labels remain outside target-time construction and
  ranking unless a baseline explicitly uses them as an oracle upper bound.
- Trace containers are normalized into operations before profiling.
- AgentPProf accepts trace containers as inputs but never emits them as a
  second artifact.
- The only successful product output is one `.pb` or `.pb.gz` pprof. Existing
  pprof-compatible tools provide visualization and interaction.
- Automatic operation-stack induction requires exactly one nonempty `session`
  and `action` value per operation and returns an explicit error when its
  recurrence model cannot be learned.
- Supervised recurrence calibration additionally requires exactly one nonempty
  `group` value per calibration operation, a separate score-reference corpus,
  and calibration session IDs disjoint from the target.
- AgentSight evidence must first be converted into one of the supported inputs;
  the current CLI has no direct AgentSight-recording reader and does not claim
  verified trigger lineage.
- The pprof must preserve the selected weighted paths and reversible source
  evidence for the effective configuration.

## Known Scientific Gaps

The implementation is ahead of the admitted scientific evidence in breadth of
configuration. In particular:

1. recurrence induction clears the registered simple controls on the same
   post-hoc OSWorld-Human development population, and declared task-family and
   action-label accuracy are measured for one named backend on AgentBoard and
   the ASE trajectory artifact. The action measurement runs through a standalone
   llama.cpp experiment adapter, not the current AgentProf CLI. The CLI exposes
   phase as a configurable mapping/operation field and recurrence-derived
   groups; phase/group structure is evaluated through partitions and boundaries,
   while the measured task/action backends are not integrated CLI taggers;
2. many mapping and rank rules were developed on datasets later used for
   analysis, so unchanged transfer needs a genuinely untouched family;
3. profile-group ranking can improve because of visible fields or rank policy
   rather than semantic hierarchy;
4. current trace exchange is not complete OpenTelemetry/OpenInference/Phoenix
   compatibility;
5. offline replay cost does not establish end-to-end diagnostic efficiency;
6. correct semantic or causal lineage needs an independent source-native oracle.
7. the tested fixed 8/32/128 recursive adapter has no stable first-hit advantage
   on Hodoscope iQuest, and the official density-gap/FPS bundle is substantially
   stronger on its published task.
8. imported zero values are currently normalized to one; existing admitted
   experiments use positive integer weights, but zero-valued measures require
   an artifact correction before use.
9. the final same-signal RQ2 consolidation improves standard MAP over matched
   raw-action organization on all three complete workloads, but direct local
   evidence remains stronger on AgentProcessBench. The adaptive local-first
   semantic refinement improves over local-only and semantic-only ranking on
   all three observed populations and over matched local-plus-raw refinement on
   HINTBench and TraceElephant; AgentProcessBench does not distinguish the two
   refinements. It is evaluation-only post-hoc mechanism evidence, not the Rust
   release ranking path or an untouched universal replacement.
10. the fixed-reader result is limited to one local model and each view's
    query-aware top-five packet; it adds group-prioritization evidence but does
    not establish lower work, reader-only causality, human utility, or raw-action
    superiority.
11. the completed source-native stateful development backend produces legal
    variable-depth paths and improves over the prior operation-level stack, but
    it creates a fresh frame on 74.55% of native turns and reaches ordinary
    B-cubed F1 0.4909 versus 0.6627 for the current recurrence constructor when
    scored by hidden active-frame instance. Repeated labels frequently receive
    new hidden identities. Step 0055 evaluates profiler-visible label-path
    identity separately. This backend is not integrated into the Rust CLI and
    does not establish automatic recovery of the task-semantic hierarchy.
12. the completed score-only audit establishes exact ordered visible label path
    as the evaluated profile identity and raises ordinary B-cubed F1 from
    0.4909 to 0.5671 relative to hidden frame IDs, but the fixed online
    constructor remains below recurrence at 0.6627. Adjacent repeated-frame
    contraction is a diagnostic only; the Rust pprof path preserves every
    frame.
13. the final causal exact-leaf evaluator applies 6,731 identity-preserving
    stays and improves exact-visible-path B-cubed F1 from 0.5671 to 0.6499, but
    does not clear recurrence at 0.6627; its paired adoption interval crosses
    zero. The unrestricted path-editor branch is closed and remains outside the
    Rust CLI. A later user-directed experiment separately tests a literal
    well-nested online controller rather than reopening its arbitrary edits.
14. the completed whole-trajectory global adapter covers all 405 preselected
    reconstructable failed trajectories but emits exactly one interval for
    every trajectory with both tested checkpoints. Qwen2.5-3B produces variable
    zero-to-39-frame summary paths; the fixed Qwen3.6-27B sufficiency test
    produces depth-zero-or-one paths. Both reach ordinary B-cubed F1 0.2958 and
    boundary F1 zero because neither emits a task-progress boundary. The 27B
    evaluator now scores maximal contiguous equal task/subtask paths as the
    persistent task occurrence and records the full
    phase/action/object/result suffix, but that distinction cannot help when
    every session has one segment. This adapter is not integrated into the Rust
    CLI. The next distinct constructor should maintain a live task stack and
    classify each next semantic operation as keep, push, or pop rather than
    repeat a global prompt or model variant. Step 0059 performs that distinct
    live-stack test.
15. the Step 0059 live controller permits only `stay`, one-leaf `push`, and
    one-leaf `pop` and retains exact active-leaf identity. Under a common
    maximal-contiguous-occurrence scorer, it raises B-cubed F1 modestly from
    0.6543 to 0.6574 relative to Step 0056 but remains below
    recurrence at 0.6627, with a candidate-minus-recurrence paired interval
    crossing zero. The fixed 3B policy applies 5,343 pushes and only 128 pops,
    leaves 334 of 405 sessions without any depth decrease, and reaches depth
    122. The well-nested data structure is not rejected, but this transition
    policy is not integrated into the Rust CLI and does not establish automatic
    recovery of task completion, ancestor semantics, or the lower semantic
    suffix.
16. Step 0060's evaluation-only result-grounded controller separates OPEN from
    CLOSE and stores an observable completion condition per child. Its
    authoritative r7 run projects only `{label, done_when}` to CLOSE and has
    zero internal instance or sequence-ID leakage. Nevertheless, the fixed
    Qwen2.5-3B policy returns `complete` for 4,893/4,907 real ToolSandbox CLOSE
    calls and 13,590/13,604 real CodeTrace CLOSE calls, reaches maximum depth
    three, and oversegments CodeTrace to 8,861 groups. It is not integrated
    into the Rust CLI. The earlier r6 candidate artifacts are invalid because
    raw child instances exposed model/persona/session identity; only the r6
    Step 0059 baseline caches are valid and were replay-validated for r7 reuse.

## Implementation Policy After The Recurrence Port

The Step 0017--0018 information-gain results remain frozen experiment artifacts
and historical baselines; that mechanism is no longer the Rust runtime path.
Step 0024 retains the Step 0020 coarse recurrence objective and adds only the
monotone cross-action calibration above. Step 0049 adds the detailed
visible-action continuity arm. On the already-observed 287-session OSWorld
population, absent non-redundant detail causes exact coarse fallback at 0.6799
boundary / 0.7862 B-cubed F1. On all 405 existing CodeTraceBench targets,
multi-resolution recurrence reaches 0.2656 boundary F1 and 0.6627 B-cubed F1,
versus 0.2871 / 0.6492 for coarse recurrence. Its +0.0136 B-cubed gain over
coarse has a task-cluster 95% interval of [+0.0087,+0.0180] and is positive in
all four frameworks. Both populations had already informed mechanism
diagnosis, so these numbers authorize the release implementation but remain
post-hoc rather than fresh RQ3 confirmation.

The release Rust port exactly matches the fixed Python evaluator on all 3,691
adjacent decisions, 3,978 motif assignments, and 2,656 segments across the five
existing folds, while conserving all 3,978 profile units. Raw global,
cross-action, and applied cutoffs agree within `1e-12`; scorer-only fields remain
outside induction. Complete adoption records are under
[`step-0024-20260715T042557-0700`](tmp/build-and-evaluate/step-0024-20260715T042557-0700/).
