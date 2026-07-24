# Review fix report

Timestamp: 2026-07-23T23:55:00-07:00

## Trigger

The independent Claude Opus whole-paper review returned `WEAK ACCEPT` with one
must-fix: the abstract and introduction still described an older RQ2
comparison whose vocabulary and numbers were not traceable to the current
matched Table 1. It also requested tighter scope language and primary-source
verification of the closest 2026 neighbors.

The user then asked whether the trajectory baseline lets an Agent read and
evaluate the trajectory without using AgentProf.

## Baseline audit

The complete Step 0072 baseline is a per-workload fixed direct diagnostic, not
one common Agent rerun:

- AgentProcessBench contributes released per-operation process-judge risk
  units.
- HINTBench contributes released/reproduced localizer decisions.
- TraceElephant contributes a localizer that reads the complete trace and
  reference answer before predicting the responsible agent and decisive step.

There is also a completed fixed Qwen3.6-27B reader study over six tasks and 66
rank-hidden packet presentations, but that study compares operation-stack and
fixed-session views. It is not a complete raw-trajectory reader baseline over
the three RQ2 populations and is not represented as one.

The Step 0072 comparison remains fair:

1. `Direct+AgentProf` may refine exact direct-score ties only.
2. It cannot reverse any strict ordering made by the fixed direct diagnostic.
3. `Direct+Raw+Evidence` retains the same source evidence and aggregation, so
   it is the information-matched test of the semantic prefix.
4. Candidate-minus-matched-raw intervals include zero on all three workloads.

The supported conclusion is therefore that the complete profile complements
fixed direct diagnostics. The experiment does not establish that the semantic
prefix alone improves target ranking.

## Paper fixes

- Replaced every abstract/introduction RQ2 headline with the exact matched
  result: MAP gains of 0.031, 0.107, and 0.117 over direct-only, with a
  statistical tie against information-matched raw action plus source evidence.
- Removed the unsupported abstract sentence about canonical renaming.
- Added the adaptive protocol-development scope next to the headline result.
- Renamed the prose baseline from a generic trajectory reader to the exact
  benchmark-native process judge or trajectory localizer.
- Harmonized the 405-trajectory CodeTrace population as released trajectories
  reconstructable from source.
- Made the contribution and conclusion describe RQ2 as supplementing direct
  diagnostics rather than beating raw action.
- Surfaced RQ1 as a repeated-task resource case rather than a population-wide
  discovery-rate claim.

## Closest-work verification

Primary sources were reopened:

- TraceProbe, arXiv:2607.06184, describes a canonical nine-action
  representation, deterministic effect labels, single-run anti-pattern
  diagnostics, and reference-scoped cross-run divergence analysis.
- Graphectory, arXiv:2512.02393 / OOPSLA 2026 DOI 10.1145/3798271, constructs a
  cyclic per-trajectory action/navigation graph, derives phase-flow and pattern
  analyses, and supports online intervention.
- Act·onomy, arXiv:2605.13625, provides a fixed three-level behavior taxonomy
  (10 actions, 46 sub-actions, 120 leaves) and an automated trace-analysis
  pipeline that emits behavior profiles.
- CHIEF, arXiv:2602.23701, constructs task/subtask causal graphs from OTAR
  structure and uses virtual-oracle backtracking plus counterfactual screening
  for failure attribution.

The paper's earlier phrase “TraceProbe supplies resource-aware process
profiles” was too loose. Related Work now states the mechanisms directly and
bounds AgentProf's delta against all four neighbors to shared variable-depth
responsibility annotations that cover native call evidence, fold across runs,
and replay the same boundaries under multiple additive resource measures in
standard pprof.

## Validation

`make` completes successfully. The result remains a 12-page AAAI-format PDF.
The first page was rasterized and visually checked after the abstract rewrite;
there is no overflow or clipping. Remaining LaTeX messages are underfull-box
warnings, not build failures.
