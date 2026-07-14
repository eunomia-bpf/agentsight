# Experiment Plan: RQ3 Operation-Stack Induction Without An Arbitrary Depth Cap

## Research Question And Tested Hypothesis

- Paper RQ, unchanged: **RQ3: How accurate are the tags?**
- One uncertainty tested here: whether the arbitrary depth-four runtime limit,
  rather than the registered gain-versus-penalty rule, caused the current Rust
  operation-stack inducer to under-segment OSWorld-Human action groups.
- Tested hypothesis: when all other mechanism and scoring choices are held
  fixed, an effectively unbounded run improves both adjacent-boundary F1 and
  operation-weighted B-cubed F1 over the same current algorithm at depth four
  and exceeds the strongest simple control on both metrics.
- The experiment may change the conclusion about this tested mechanism. It may
  not change RQ3, the thesis, the four-RQ structure, the paper story, or the
  operation/operation-stack model.

## Why This Single Experiment Is Admitted

Step 0017 ran the complete 287-session population and found that the revised
single-objective Rust inducer reached the depth-four limit in 106 sessions and
at 488 terminal nodes. A binary tree of depth four can represent at most 16
leaves, while 22 official sessions have more than 16 human groups. The cap is
therefore an observed, materially binding implementation constraint rather than
an arbitrary new feature proposal.

This follow-up is explicitly **post-hoc** because OSWorld-Human diagnostics
selected it. It can determine whether the cap caused the observed
under-segmentation; it cannot by itself provide fresh independent confirmation
of a broad RQ3 claim. No score, field, penalty, cutoff, model, benchmark,
metric, label, or ontology is admitted. Another depth value, penalty sweep, or
same-data heuristic branch is outside this experiment.

The paper decision is direct:

- if the fixed hypothesis succeeds, the cap-free mechanism becomes a candidate
  paper method, but its broad accuracy claim still requires one independent
  annotated workload;
- if it fails or is mixed, the hard cap is not the sufficient explanation and
  the project must not search another depth or tune the local penalty on this
  dataset; and
- under every outcome, the larger profiling thesis and fixed RQ3 remain intact.

## Fixed Mechanism And One Variable

Both methods use the same current release binary and exactly the algorithm
recorded in Step 0017's `algorithm-note.md`:

- identical target-blind eligible visible fields and oracle/noisy-field
  exclusions;
- identical candidate boundaries at adjacent visible-field changes;
- identical equal mean of resource-weighted normalized per-field information
  gain;
- identical strict acceptance rule `G(I,b) > ln(n)/(2n)`;
- identical dominant `field=value` child frames;
- identical query-relevance tie-breaking and deterministic residual ties; and
- identical path reconstruction, accounting, and termination semantics.

The sole independent variable is `--induce-max-depth`:

- **candidate:** `255`, equal to the maximum operation count in the complete
  population and therefore non-binding for any possible recursive path here;
- **main baseline:** `4`, the current default and exact Step 0017 configuration.

`255` is not a tuned candidate depth. For any session with at most 255
operations, recursive nonempty binary splitting can create at most 254 nested
edges on one path, so this value removes the cap for the declared population.
The experiment will not compare or select among intermediate depths.

## Strongest Competing Explanation

The local complexity penalty may be too weak to act as a principled global stop
condition. In particular, a two-operation interval with one differing eligible
field can have normalized gain one, which exceeds `ln(2)/4`. Removing the cap
may therefore recurse toward nearly every visible-field change and approach the
always-boundary control rather than recover meaningful human groups.

The result review must inspect predicted boundary count, leaf count, stop
reasons, and distance from the always-boundary control. More segmentation is
not itself evidence of accuracy. If cap removal merely approaches the
always-boundary control without beating it on both registered metrics, the
tested hypothesis is not supported.

## Real Assets And Comparisons

- Workload: all 287 eligible sessions in the tracked complete OSWorld-Human
  operation conversion, containing 3,978 operations, 3,691 adjacent pairs, and
  2,042 official human groups.
- Ground truth: existing official `human_group` boundaries and partitions,
  retained by the scorer only and removed from every profiler input.
- Main baseline: the same current information-gain binary at depth four.
- Simple controls, reused without recomputation: action change, phase change,
  and always boundary on the same 3,691 pairs and session partitions.
- Extra-information comparator, reused and labeled separately: the existing
  supervised out-of-fold Bernoulli boundary predictor.
- Primary metrics, unchanged: micro adjacent-boundary precision/recall/F1 and
  operation-weighted B-cubed precision/recall/F1.
- Diagnostics, not additional gates: number of predicted boundaries, leaf
  counts, no-split sessions, maximum leaf depth, terminal stop reasons, and
  results by the already defined length/depth-cap strata.
- Repetitions: one deterministic full-population execution per method. No seed,
  bootstrap, threshold, or hyperparameter sweep is scientifically meaningful
  for these deterministic methods.

Information-gain tree induction (Quinlan, 1986,
<https://doi.org/10.1007/BF00116251>) and recursive binary segmentation
(Fryzlewicz, 2014, <https://arxiv.org/abs/1411.0858>) remain the closest
published ingredients. This experiment claims no novelty for either one; it
tests whether the registered agent-operation instantiation has a functioning
intrinsic stop rule once an arbitrary runtime cap is removed.

## Minimal Implementation Reuse

Reuse `script/rq3_rust_inducer_fidelity_eval.py`, its existing OSWorld loader,
scrubber, Rust-decision replay, B-cubed scorer, simple-control loader,
per-session rows, summary format, resume behavior, and invariants. Make only the
smallest runner generalization needed to:

1. pass a declared maximum depth to each method;
2. compare the same current binary under method names `depth_unbounded` and
   `depth_four`; and
3. verify and record each method's actual reported depth configuration.

The old-heuristic comparison must remain the runner's default behavior so the
Step 0017 command and artifacts remain reproducible. No second large evaluation
script, data conversion, scorer, or algorithm implementation is justified.

## Planned Runs

| Run | Role | Workload | Candidate / baseline | Consequence |
|---|---|---|---|---|
| real preflight | dependency and configuration check | real 255-operation session `236833a3-5704-47fc-888c-4f298f09f799`, selected because the depth-four run has a recorded cap stop | current binary at depth 255 / same binary at depth 4 | both real paths, replay, scoring, and a cap-binding case execute; no paper result |
| complete run | scientific result | all 287 eligible sessions | current binary at depth 255 / same binary at depth 4 | tests the fixed hypothesis on the complete declared population |
| reused controls | comparison | the same operations/pairs | action, phase, always-boundary, supervised OOF | determines whether any gain exceeds simple segmentation and shows the supervised ceiling |

## Commands And Raw Outputs

After the minimal runner change, run its focused tests or syntax checks and the
existing Rust tests. Then rebuild the current release binary once:

```bash
python3 -m py_compile script/rq3_rust_inducer_fidelity_eval.py
cargo test --manifest-path agentpprof/Cargo.toml operation_stack_induction
cargo test --manifest-path agentpprof/Cargo.toml --test profile_spec_cli
cargo build --release --manifest-path agentpprof/Cargo.toml
```

Real preflight:

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode preflight \
  --comparison depth-limit \
  --candidate-max-depth 255 \
  --baseline-max-depth 4 \
  --candidate-binary agentpprof/target/release/agentpprof \
  --baseline-binary agentpprof/target/release/agentpprof \
  --preflight-sequence 236833a3-5704-47fc-888c-4f298f09f799 \
  --out-dir .agentsight/experiments/rq3-rust-inducer-depth-v1/preflight
```

Complete run:

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode full \
  --comparison depth-limit \
  --candidate-max-depth 255 \
  --baseline-max-depth 4 \
  --candidate-binary agentpprof/target/release/agentpprof \
  --baseline-binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq3-rust-inducer-depth-v1/full
```

Raw output is
`.agentsight/experiments/rq3-rust-inducer-depth-v1/{preflight,full}/`.
Existing per-session checkpoint/resume behavior may skip only an already
complete row whose method, binary, policy, depth, workload, and command metadata
match; otherwise it must rerun that cell.

## Real-Preflight And Full-Run Validity

The real preflight is valid only if both actual profiler invocations complete
on the declared real session; the reports state maximum depths 255 and 4; all
operations receive exactly one terminal path; every split decision is consumed;
all input and emitted weight is conserved; scorer/oracle fields are absent from
selected evidence; every accepted split strictly clears the fixed penalty; and
the depth-four baseline reproduces the prior session result. The preflight is
dependency evidence only.

The full run is complete only if the same checks hold for both methods on all
287 sessions, all 3,978 operations, and all 3,691 pairs. The depth-four baseline
must reproduce Step 0017's boundary and B-cubed metrics exactly; otherwise the
comparison is invalid until the runner mismatch is repaired and the complete
run is repeated. No two- or three-session smoke sample can substitute for this
run.

## Registered Interpretation

- **Supported:** depth 255 improves both registered F1 metrics over depth four
  and exceeds the strongest simple control on both. The result supports cap-free
  induction on this post-hoc population, but a broad paper claim still requires
  an independent annotated confirmation.
- **Contradicted:** depth 255 improves neither registered F1 metric over depth
  four, or clears neither metric's strongest simple control. The cap is not the
  sufficient explanation for the shipped-mechanism gap.
- **Mixed:** every other valid result that is neither supported nor
  contradicted. Report the exact mechanism boundary without changing RQ3.
- **Invalid/inconclusive:** any leakage, configuration, replay, mass,
  completeness, or baseline-reproduction check fails. Repair only that defect
  and rerun the same complete plan.

After a valid supported result, the next evidence source is one independent
annotated workload, not another OSWorld-Human setting. After a valid mixed or
contradicted result, do not try another depth, score term, threshold, or local
penalty on OSWorld-Human. The root must decide whether a genuinely different
principled global objective is warranted or whether automatic induction remains
an optional implementation path while the paper relies on already admitted
supervised and task-partition evidence. Either decision belongs after result
review and does not authorize changing the RQ or paper story.
