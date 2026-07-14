# Real Preflight: RQ3 Inducer Depth

## Status: PASS AFTER ONE EXECUTION-GLUE REPAIR

This preflight is dependency and configuration evidence only. It is not a
paper result and does not alter the registered full-run interpretation.

## First Attempt — Invalid Before Artifact Write

The first invocation reached both real profiler executions but the generalized
evaluator then raised `NameError: name 'METHODS' is not defined` while composing
pair rows. One stale constant reference remained after method names became
comparison-specific. The failure occurred before the evaluator wrote summary,
session, or pair artifacts. It was an evaluation-glue defect, not an algorithm,
workload, scorer, or profiler failure.

The only repair replaced that stale reference with the already declared local
`methods` tuple. The RQ, binary, sequence, depths, fields, objective, penalty,
labels, metrics, and command did not change. Python compilation then passed and
the identical preflight command was rerun.

## Corrected Real Execution

- Sequence: `236833a3-5704-47fc-888c-4f298f09f799`
- Real operations: 255
- Adjacent pairs: 254
- Official human groups retained by scorer: 181
- Candidate: current release binary, depth 255
- Baseline: the same current release binary, depth 4
- Policy for both: `recursive-information-gain-operation-stack-induction`
- Raw output:
  `.agentsight/experiments/rq3-rust-inducer-depth-v1/preflight/`

Both invocations consumed the real scrubbed operation file through the actual
Rust CLI. The evaluator verified the reported configurations, complete terminal
assignment, complete decision replay, exact 255-unit mass conservation,
reconstructed-versus-Rust stack equality, oracle-field exclusion, strict
gain-over-penalty acceptance, same-binary comparison, and exact reproduction of
the Step 0017 depth-four session row. Depth 255 was non-binding.

## Preflight Observation, Not Result

The depth-four run records six splits, maximum leaf depth four, four
`max_depth` terminal stops, and three `no_material_split` stops. The depth-255
run records the same six splits and terminal paths, but all seven terminal
stops are `no_material_split`. Consequently both methods have the same boundary
F1 (`0.0215053763`) and B-cubed F1 (`0.0575938042`) on this one session.

This observation corrects a possible diagnostic overinterpretation: a terminal
node that reaches depth four is not necessarily a node that the intrinsic
objective would split. Removing the cap can simply reclassify its stop reason.
The observation neither supports nor contradicts the registered population
hypothesis. The complete 287-session run remains required.

## Transition

REAL PREFLIGHT passes. Proceed to the unchanged complete run over all 287
eligible sessions. Any valid result must use the mutually exclusive registered
Supported/Contradicted/Mixed rules in `experiment-plan.md`.
