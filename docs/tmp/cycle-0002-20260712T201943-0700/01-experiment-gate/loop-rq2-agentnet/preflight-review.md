# Independent review: AgentNet REAL PREFLIGHT

**Reviewed:** 2026-07-13T03:55:07-07:00  
**Reviewer method:** `research-experiment-design`  
**Review mode:** independent and read-only  
**Disposition:** `PASS — AUTHORIZE FULL`  
**Must-fix:** none

The reviewer did not use the direction or magnitude of any preflight metric to
judge the hypothesis. It independently re-read the approved plan, source and
preflight reports, implementation, model/profile reports, score outputs, draw
files, and current label-blind artifacts.

## Independent findings

### Fixed source subset

The projection subset is exactly the lexically first 256 original task IDs per
platform with no missing or extra cluster.

- Held-out Windows: 256 tasks, 256 trajectories, 3,608 operations.
- Held-out Darwin: 256 tasks, 261 trajectories, 4,844 operations.
- Five selected Darwin task IDs have two released trajectories each.
- Each draw header contains exactly 256 unique original task IDs, so both
  trajectories of a repeated task share one bootstrap multiplicity.

### Predictor and model

Both model reports list only the visible projection and the appropriate
reference-platform label file as inputs. `target_label_input` is null,
`legacy_normalize_agentnet_used` is false, and the helper list is exactly:

- `agentnet_code_action`;
- `agentnet_action_target`;
- `agentnet_action_phase`; and
- `repeat_features_for_signatures`.

Both fixed logistic models converged in 5 iterations under the 1,000-iteration
cap.

### AgentProf and risk reconstruction

The installed binary and both reports identify exactly `agentpprof 0.2.37`.
Every flat, fixed-session, source-native, raw-action, and semantic view reports
`exact=true` and reconstructs every target operation. Recomputed group and
total full-precision risk differs from saved prediction totals only at roughly
`2e-12`, within the declared floating-point tolerance.

### Bootstrap and label boundary

Each fold's label-blind stage wrote one header and all 1,000 deterministic draw
specifications before scoring. Both scorers examined a fixed 512-spec batch and
retained attempts 0 through 199 as the first 200 valid draws. The retained
attempt IDs are unique and sorted.

The reviewer recomputed SHA-256 for predictions, assignments, group summaries,
draw specifications, model reports, and profile reports in both folds. All 12
values match the saved pre-score digests.

### Status separation

Top-level and execution outputs are `VALID` and
`NOT_EVALUATED_PREFLIGHT`; `tested_hypothesis_only` is false. The detailed
report intentionally does not interpret the preflight effect values.

### Regression suite

The reviewer reran the dedicated suite and observed 10/10 tests pass, including
alternate, wrong-platform, and withheld target-label invariance.

## Decision

REAL PREFLIGHT satisfies every approved execution obligation. FULL is
authorized with no code, plan, RQ, hypothesis, paper, or story change. It must
use the complete 17,625 trajectories / 339,005 operations, exactly 10,000 valid
task-cluster draws per fold, a 50,000 attempt cap, and seed 4204.

**Read-back correction (2026-07-13):** the operation total in the original
review text was an arithmetic typo. The reviewed per-platform counts and
machine source remained `239,710 + 99,295 = 339,005`; no execution input or
authorization condition changed.

**Files modified by reviewer:** none.
