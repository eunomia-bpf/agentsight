# Experiment Plan: RQ3 Built-In Operation-Stack Induction

## Research Question

- RQ exactly as written in the paper: **RQ3: How accurate are the tags?**
- Specific uncertainty tested here: whether the built-in target-blind Rust
  operation-stack inducer can recover independently annotated human action-group
  boundaries after its heuristic score is replaced by one resource-weighted
  normalized information-gain objective.
- Why the answer matters: the paper currently describes the Rust inducer but
  reports RQ3 numbers for a separate supervised Bernoulli predictor. A direct
  full-population test removes that mechanism/evidence mismatch without changing
  RQ3, the thesis, or the paper story.

## Paper-Value Admission

- Planned role: **decisive** for the built-in induction component of RQ3.
- Largest credible paper story this experiment could unlock: AgentProf provides
  a simple, target-blind, resource-aware stack-induction algorithm whose emitted
  hierarchy corresponds to independently annotated operation groups and whose
  additive weights remain exact.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  ordered field projection is simple, the present induction score is an
  unexplained mixture of eight terms, and the current RQ3 experiment explicitly
  does not test the shipped inducer.
- Independent evidence added beyond existing runs and published results: direct
  predictions from both the pre-change and revised Rust binaries on all 287
  eligible OSWorld-Human sessions, scored against the existing official human
  groups only after induction.
- Why the result is not tautological, already settled, or dominated: neither
  Rust algorithm reads human-group fields, and existing 0.739/0.816 results come
  from a supervised model trained on other folds, not either Rust inducer.
- Paper decision if positive: describe and evaluate the revised built-in
  information-gain inducer as the paper's one algorithmic mechanism; retain the
  supervised predictor only as an upper comparator or remove it from the main
  mechanism claim during WRITE.
- Paper decision if contradictory, mixed, or inconclusive: keep the thesis and
  RQ3 fixed, report the tested constructor boundary in project evidence, and do
  not claim that the revised built-in inducer is validated. A failure bounds this
  implementation detail, not semantic profiling or the paper thesis.
- Best alternative experiment and why this one has higher decision value: the
  paused R315 LLM-reader experiment adds a downstream RQ2 reader but leaves the
  shipped-algorithm mismatch untouched. This matched RQ3 test addresses the
  more direct algorithmic novelty and evidence objection raised by the user's
  current instruction.

## Expected And Alternative Outcomes

- Current expected answer: the single-objective inducer should beat the
  strongest simple boundary/partition controls and should match or improve the
  pre-change heuristic because every accepted split now optimizes one
  resource-weighted separation criterion rather than a fixed coefficient mix.
- Strongest competing explanation: human action groups depend on supervision or
  domain semantics that target-blind field entropy cannot recover; simplifying
  the score may improve explanation while reducing boundary fidelity.
- Result that would contradict the expectation: the revised inducer fails to
  beat the strongest simple control on both boundary F1 and B-cubed partition F1,
  or loses both metrics to the pre-change Rust heuristic.

## Published Precedent And Real Assets

- Closest published protocol: recursive information-gain tree induction
  (Quinlan, 1986, <https://doi.org/10.1007/BF00116251>) and recursive binary
  segmentation (<https://arxiv.org/abs/1411.0858>); the experiment does not
  claim either ingredient as new.
- Official system/model/data/benchmark/tool and version: the tracked complete
  OSWorld-Human operation conversion at
  `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl`,
  the current Rust `agentpprof`, and the existing Step 0006 scoring definitions.
- What is reused: all 287 eligible sessions, 3,978 unit-weight operations, 3,691
  adjacent pairs, 2,042 official human groups, action/phase/always-boundary
  controls, B-cubed implementation, and mass-conservation checks.
- Necessary deviations or custom glue: one thin runner composes the existing
  OSWorld loader and B-cubed functions with Rust split-decision reconstruction.
  It adds no dataset, annotation, model, feature, or metric.

## Comparison

- Proposed method: the revised target-blind Rust operation-stack inducer using
  the equal mean of per-field resource-weighted normalized information gain,
  a size-dependent complexity penalty, and dominant contributing field/value
  labels.
- Fixed algorithm before any scored run:
  - for every nonempty adjacent cut, score every eligible field with positive
    parent entropy by normalized resource-weighted information gain and average
    those gains equally;
  - eligible fields use the existing target-blind constant, near-numeric,
    high-cardinality, metadata, noisy-field, session-by-default, and oracle-field
    exclusions; these are field admission rules, not score terms;
  - accept the best cut strictly when
    `mean_gain > ln(node_operation_count) / (2 * node_operation_count)`;
  - remove the old `min_score`, `min_node_weight`, `min_second_child`,
    `max_majority_fraction`, label-quality, balance, coverage, semantic-shift,
    small-child, cardinality, and candidate-subsampling gates/terms; only
    nonempty children and the fixed maximum depth remain;
  - choose as primary the largest positive-gain field whose two child dominant
    weighted values differ, and append `field=value` as one new frame to each
    child even if the text occurred at an ancestor; if distinct raw labels
    normalize to the same folded frame, append a deterministic value-derived
    suffix so emitted child paths remain distinct;
  - define one field's query relevance as the fraction of supplied lowercase
    query terms that occur as substrings of its lowercase field name or any
    parent-interval value; break exact primary-field gain ties by higher query
    relevance then lexical field name, and exact cut mean-gain ties by the
    selected primary field's relevance then earlier cut. Query terms never
    enter the numeric score.
- All constants and eligibility rules above are fixed without reading
  OSWorld-Human labels. The experiment will not change them after preflight or
  full scoring.
- Main baseline: the exact pre-change Rust heuristic binary built from the
  current checkout before editing. It represents the strongest alternative
  mechanism: the existing multi-term score under identical fields, depth,
  candidate cuts, data, and metrics.
- Why the main baseline needs a matched run instead of citation alone: no
  published or existing artifact reports session-local boundary F1 or B-cubed
  for that binary on this complete eligible population.
- Controls, labeled separately: existing action-change, phase-change, and
  always-boundary predictions on the same 3,691 pairs; the existing supervised
  out-of-fold Bernoulli result is an extra-information upper comparator, not a
  target-blind baseline.
- Conclusion if the main baseline matches or wins: simplification remains an
  engineering improvement only and cannot support an accuracy advantage; if it
  loses both metrics, the revised implementation is not promoted as the paper's
  validated constructor.
- Information, tuning, and compute fairness: both Rust binaries receive exactly
  the same scorer-scrubbed operations in the same session order, with session
  excluded as split evidence, the same maximum depth, and no access to
  `human_group`, `group_*`, `learned_*`, or other oracle fields. No threshold,
  field, or penalty is selected from OSWorld-Human labels.
- Split or leakage rule: `group_alignment=exact` selects the already declared
  eligible population before scrubbing. The scorer retains `human_group`
  separately; binary inputs remove every Step 0006 leakage field/prefix.

## Workloads And Metrics

- Real workloads or tasks: all 287 eligible OSWorld-Human task-instance
  sessions, not a prefix or sample.
- Primary metrics: micro adjacent-boundary precision/recall/F1 and
  operation-weighted B-cubed partition precision/recall/F1.
- Correctness check or ground truth: official `human_group` changes and
  session-local official partitions, read only by the scorer.
- Repetitions, seeds, and uncertainty: deterministic complete-population run;
  no repeated decoding, seed sweep, bootstrap, or p-value.
- Cost estimate: two Rust builds and 574 small session-local profile calls,
  expected to finish locally within tens of minutes.
- Descriptive diagnostics: no-split sessions and results by existing session
  length/depth-cap strata. These explain behavior and are not extra gates.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | dependency | one real eligible session | old and revised Rust binaries | 1 | proves both real paths, scrubbing, reconstruction, and scoring execute; no paper result |
| full candidate | proposed | all 287 sessions | revised information-gain inducer | 1 | primary tested mechanism |
| full baseline | main baseline | all 287 sessions | pre-change heuristic inducer | 1 | decides whether simplification preserves or improves fidelity |
| reused controls | controls | same 3,691 pairs | action change, phase change, always boundary | existing exact rows | anchors simple alternatives |
| reused supervised | upper comparator | same 287 sessions | Step 0006 out-of-fold Bernoulli predictor | existing exact rows | shows extra-supervision ceiling; not a fair target-blind baseline |

## Execution

- Preserve the pre-change baseline binary before editing:

  ```bash
  cargo build --release --manifest-path agentpprof/Cargo.toml
  cp agentpprof/target/release/agentpprof \
    .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic
  ```

- After implementation, run the focused and full Rust tests and rebuild the
  candidate explicitly:

  ```bash
  cargo test --manifest-path agentpprof/Cargo.toml operation_stack_induction
  cargo test --manifest-path agentpprof/Cargo.toml --test profile_spec_cli
  cargo test --manifest-path agentpprof/Cargo.toml
  cargo build --release --manifest-path agentpprof/Cargo.toml
  ```

- Authoritative preflight:

  ```bash
  python3 script/rq3_rust_inducer_fidelity_eval.py \
    --mode preflight \
    --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
    --candidate-binary agentpprof/target/release/agentpprof \
    --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight
  ```

- Authoritative full run:

  ```bash
  python3 script/rq3_rust_inducer_fidelity_eval.py \
    --mode full \
    --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
    --candidate-binary agentpprof/target/release/agentpprof \
    --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/full
  ```

- Real preflight case: the first sorted eligible session with at least two
  operations; both binaries run on its actual scrubbed operations and the
  scorer verifies complete path reconstruction and mass.
- Full completion rule: both binaries return one terminal prediction for every
  eligible session; 287 sessions, 3,978 operations, and 3,691 pairs score once;
  all binary reports exclude oracle evidence fields; reconstructed stack mass
  equals input mass for every session; every accepted decision is consumed and
  creates two distinct child paths. The runner records each binary's explicit
  maximum depth and confirms both use depth four; other old structural gates
  are part of the old baseline mechanism and are intentionally absent from the
  revised candidate fixed above.
- Replay and scoring semantics are method-specific: the frozen old binary is
  replayed with its legacy ancestor-label de-duplication, while the revised
  candidate appends every reported child frame. Both replayers must consume
  every reported split decision and match the corresponding Rust profile stack
  weights. An adjacent boundary prediction is true exactly when the two final
  reconstructed leaf paths differ; predicted partitions are the maximal
  contiguous runs separated by those boundaries.
- Raw-result path:
  `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/{preflight,full}/`.
- Checkpoint or recovery approach: one JSONL row per completed session and
  method; rerunning resumes only missing cells with the identical binary and
  command, then recomputes the complete summary.

## Interpretation

- Positive result: both boundary F1 and B-cubed F1 exceed the strongest simple
  control and the pre-change heuristic; the revised inducer's target-blind
  boundary/partition fidelity is supported on OSWorld-Human. Because all 3,978
  operations have unit weight, this run validates mass conservation but does
  not isolate an empirical accuracy benefit from resource weighting.
- Negative or contradictory result: neither metric clears the strongest simple
  control, or both lose to the old heuristic; the revised constructor is not
  supported and the paper thesis is unchanged.
- Mixed or inconclusive result: exactly one metric wins, the candidate clears
  simple controls but not the old heuristic on both, or any correctness/leakage/
  completion check fails. Report the precise mechanism boundary.
- Target paper figure or table: replace the RQ3 mechanism row with one compact
  table comparing revised Rust, old Rust, simple controls, and the supervised
  upper comparator only if result review validates the complete run.

## Reproducibility Notes

- Software and data versions: current branch
  `research/semantic-flamegraph-artifacts-v2`; the baseline binary is built
  before the algorithm edit and the candidate after it, without switching
  branches or modifying the canonical submodule.
- Config and seed notes: deterministic output, maximum depth 4, session not an
  evidence field, no query terms for this query-independent RQ3 test, and no
  random component.
- Known deviations: the source is the tracked OSWorld-Human conversion used by
  Step 0006 rather than rerunning upstream conversion; this intentionally holds
  the population and scorer constant.
