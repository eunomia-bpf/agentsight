# Second independent convergence review — AgentNet REAL PREFLIGHT

**Reviewed:** 2026-07-13T04:13:28-07:00

**Reviewer method:** `research-experiment-design`

**Review mode:** independent and read-only

**Verdict:** `PASS—AUTHORIZE FULL`

**Must-fix:** zero

The reviewer explicitly reread the complete current experiment-design skill.
It did not use the direction or magnitude of any REAL PREFLIGHT effect to judge
the hypothesis, and it modified no file or branch.

## Correction-scope review

Commit `8e4ebf57` is report-only. It:

- adds `population-arithmetic-correction.md`;
- corrects the population total in `source-preparation-report.md`;
- corrects the requested or authorized FULL scope in `preflight-report.md`,
  `preflight-review.md`, and `preflight-rerun-after-key-repair.md`; and
- changes no script, test, source artifact, preflight artifact, model, profile,
  metric, draw, RQ, hypothesis, paper, or story.

The correction is explicit rather than silent. The old values occur only in
text clearly describing the historical arithmetic error.

## Complete-population read-back

The reviewer independently obtained:

| Quantity | Windows | Darwin | Total |
|---|---:|---:|---:|
| Released trajectories | 12,427 | 5,198 | **17,625** |
| Operations | 239,710 | 99,295 | **339,005** |
| Positive labels | 38,565 | 16,653 | **55,218** |
| Negative labels | 201,145 | 82,642 | **283,787** |
| Unresolved | 0 | 0 | **0** |

Mechanical line counts were 17,625 for the official trajectory JSONL, 339,005
for the prepared projection, 239,710 for Windows labels, and 99,295 for Darwin
labels. `prepare-status.json` independently reports the same task, repeated-
task, trajectory, operation, positive, negative, unresolved, and platform
counts.

A repository search confirmed that 333,005 and 277,787 now occur only when
explicitly describing the corrected historical error. Every current population
table, transition request, and authorization scope uses 339,005 operations and
283,787 negatives.

## Execution checks retained and reread

Because `8e4ebf57` changes only Markdown, the repaired code and ignored machine
outputs are unchanged. The reviewer nevertheless reread the current outputs
and reran the dedicated suite.

### Reciprocal populations and target-label boundary

- Held-out Windows: 256 tasks, 256 trajectories, 3,608 operations.
- Held-out Darwin: 256 tasks, 261 trajectories, 4,844 operations.
- Both model reports use only projection plus the appropriate reference label
  file.
- Both report `target_label_input=null`, exactly the four approved source
  helpers, and `legacy_normalize_agentnet_used=false`.
- Both fixed models converge at 5 of 1,000 maximum iterations.

### Real AgentProf reconstruction

- Installed and reported version is exactly `agentpprof 0.2.37`.
- Flat, fixed-session, source-native, raw-action, and semantic views all remain
  `exact=true`.
- All 3,608 and 4,844 target operations are reconstructed.
- Both scorer outputs retain `agentprof_count_conservation=true`.
- Independent key/count comparison has zero differences and maximum total-risk
  drift of approximately `2.96e-12`.

### Draw-before-label and invariance

- Each fold has one header plus all 1,000 pre-saved deterministic draw
  specifications.
- Each header contains 256 unique original task IDs and seed 4204.
- Each scorer retains attempts 0 through 199 as the first 200 valid draws.
- All 12 label-blind artifacts match their saved pre-score digests.
- Current top-level label-boundary checks remain true for both platforms.

### Regression and mode separation

- The dedicated suite independently passes 11/11 tests.
- Current preflight status is `VALID / NOT_EVALUATED_PREFLIGHT`.
- `tested_hypothesis_only=false` and `cross_model_pooled_ranking=false`.
- FULL rejects task subsets and separately requires exactly 10,000 valid draws
  per fold, a 50,000-attempt cap, and seed 4204.
- The 200/1,000 REAL PREFLIGHT subset has not replaced the FULL contract.

## Authorization

FULL is authorized for exactly:

- **17,625 released trajectories**;
- **339,005 operations**;
- **10,000 valid task-cluster draws per reciprocal fold**;
- **50,000 maximum attempts per fold**; and
- **seed 4204**.

This authorization applies only to executing and reviewing the approved
AgentNet experiment. It does not authorize modifying the paper, story, RQ,
hypothesis, or canonical research framing.
