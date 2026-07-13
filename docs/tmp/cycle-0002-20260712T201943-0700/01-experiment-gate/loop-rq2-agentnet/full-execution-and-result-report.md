# AgentNet reciprocal-transfer FULL execution and result report

**Started:** 2026-07-13T04:14:43-07:00

**Completed:** 2026-07-13T04:17:17-07:00

**Outer gate:** EXPERIMENT

**Execution status:** `VALID`

**Predeclared construction verdict:** `CONTRADICTED`

**Paper/story/RQ/hypothesis edit authorized:** no

## Tested hypothesis and scope

This FULL run tests the single approved RQ2 hypothesis from plan revision 4:
on complete scorable AgentNet Windows and Darwin populations, a target-label-
blind cross-run semantic AgentProf profile should improve operation-weighted
localization AP over both a raw-action grouped profile and ungrouped transferred
risk, while improving recall@30 and work-to-50 over raw action.

The verdict applies only to this fixed AgentNet construction. It does not answer
all of RQ2, change the positive paper-level hypothesis, narrow the four RQs,
replace the canonical AgentProf thesis, or authorize writing a negative result
into the paper. A valid non-supporting result stays in experiment history and
routes to a materially improved experiment or method.

## Exact approved command

```bash
python3 script/agentnet_cross_platform_eval.py full \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/full \
  --bootstraps 10000 --max-bootstrap-attempts 50000 --seed 4204
```

The coordinator accepted no task-subset argument. It independently validated
the prepared source before running either fold.

## Complete source and coverage

The source is official `xlangai/AgentNet` revision
`d76ee50a63fad81cfdbe576416757d7c2091ed50`.

| Target platform | Tasks | Released trajectories | Operations | Positive | Negative | Unresolved | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Windows | 12,364 | 12,427 | 239,710 | 38,565 | 201,145 | 0 | 100% |
| Darwin | 5,168 | 5,198 | 99,295 | 16,653 | 82,642 | 0 | 100% |
| **Total** | **17,532** | **17,625** | **339,005** | **55,218** | **283,787** | **0** | **100%** |

Projection and platform-label operation IDs have exact one-to-one coverage.
Repeated released rows remain separate trajectories, while the original task
ID remains the resampling cluster.

## Predictor and label boundary

| Transfer fold | Reference operations | Target operations | Iterations / cap | Target-label input |
|---|---:|---:|---:|---|
| Windows → Darwin | 239,710 | 99,295 | 18 / 1,000 | none |
| Darwin → Windows | 99,295 | 239,710 | 12 / 1,000 | none |

Both fixed logistic models converged. Each used only `projection.jsonl` and the
reference platform's label file. Both report seed 4204,
`target_label_input=null`, `legacy_normalize_agentnet_used=false`, and exactly
the four approved source helpers. The two independently trained model scores
were never pooled into a single ranking.

## Real AgentProf reconstruction

Both folds used exactly `agentpprof 0.2.37`.

| Target | View | Groups | Reconstructed operations | Exact |
|---|---|---:|---:|---|
| Darwin | flat | 1 | 99,295 | yes |
| Darwin | fixed session | 5,198 | 99,295 | yes |
| Darwin | source native | 21,536 | 99,295 | yes |
| Darwin | raw action | 2,220 | 99,295 | yes |
| Darwin | semantic | 6,176 | 99,295 | yes |
| Windows | flat | 1 | 239,710 | yes |
| Windows | fixed session | 12,427 | 239,710 | yes |
| Windows | source native | 49,982 | 239,710 | yes |
| Windows | raw action | 3,174 | 239,710 | yes |
| Windows | semantic | 8,332 | 239,710 | yes |

Both scorer reports retain `agentprof_count_conservation=true`. Full-precision
risk mass is conserved across all emitted views within floating-point
summation tolerance.

## FULL bootstrap completion

Each label-blind fold contains one draw-file header followed by exactly 50,000
deterministic task-cluster attempt specifications written before target
scoring. Both scorers examined 10,240 specifications in fixed batches and
retained exactly the first 10,000 valid paired draws. Each compressed
`bootstrap-effects.jsonl.gz` contains exactly 10,000 result rows.

After target scoring, the coordinator recomputed predictions, group
assignments, group summaries, model report, profile report, and draw-file
digests. All six artifacts in each fold, 12 total, remained byte-identical to
their pre-score values.

## Primary base results

Lower work-to-50 is better. All other displayed metrics are higher-is-better.

| Target | Method | AP | Recall@30 | Work-to-50 |
|---|---|---:|---:|---:|
| Windows | raw action | 0.280606 | 0.492026 | 0.346798 |
| Windows | semantic | 0.269660 | 0.484196 | **0.313867** |
| Windows | ungrouped risk | 0.276432 | 0.494594 | 0.305248 |
| Darwin | raw action | 0.269817 | 0.474269 | 0.338567 |
| Darwin | semantic | 0.264431 | 0.476611 | **0.319956** |
| Darwin | ungrouped risk | 0.273393 | 0.485078 | 0.311798 |

The semantic profile consistently reduces work required to reach 50% of
positive operations relative to raw-action grouping: 3.293 percentage points
on Windows and 1.861 points on Darwin. However, it does not satisfy the fixed
AP comparisons.

## Paired 95% task-cluster bootstrap intervals

| Target | Effect (positive favors semantic) | Point effect | 95% interval |
|---|---|---:|---:|
| Windows | semantic − raw AP | -0.010947 | [-0.013612, -0.008404] |
| Windows | semantic − raw recall@30 | -0.007831 | [-0.010696, 0.000949] |
| Windows | raw − semantic work-to-50 | 0.032931 | [0.026254, 0.038707] |
| Windows | semantic − ungrouped AP | -0.006773 | [-0.008753, -0.004886] |
| Darwin | semantic − raw AP | -0.005386 | [-0.007675, -0.002635] |
| Darwin | semantic − raw recall@30 | 0.002342 | [-0.008014, 0.011383] |
| Darwin | raw − semantic work-to-50 | 0.018611 | [0.008931, 0.028578] |
| Darwin | semantic − ungrouped AP | -0.008962 | [-0.010687, -0.006901] |

The equal-weight, within-fold secondary effects are -0.008166 AP versus raw,
-0.002745 recall@30 versus raw, +0.025771 raw-minus-semantic work-to-50,
and -0.007867 AP versus ungrouped risk. They do not enter the verdict.

## Why the verdict is `CONTRADICTED`

The plan predeclared `SUPPORTED` only if every required interval favors semantic
in both folds independently. More importantly, it predeclared `CONTRADICTED`
when either platform has an interval excluding zero in the adverse direction
for semantic AP against raw action or ungrouped risk.

Both platforms have adverse, zero-excluding AP intervals for both primary AP
comparisons. Therefore condition (b) for `CONTRADICTED` is satisfied. This is
not condition (a): semantic work-to-50 is significantly better than raw action
in both folds. The coordinator's verdict exactly matches the predeclared rule.

## Machine-output identities

The ignored complete outputs occupy approximately 561 MiB. Key SHA-256 values
at result recording are:

| Artifact | SHA-256 |
|---|---|
| top-level `execution-status.json` | `094b587fa25db1a5dbce2f5bf7e18797ff35dc882da49a5e3c8efff952909926` |
| top-level `metrics.json` | `4496a45b75174414b1e7a2e384b4c1c4ce46ddfb29a02d62fa8e239d1f12edfd` |
| top-level `report.md` | `d5ce92e634146085de9b5d2a7d25d44594a9aeb2c82867de33b8c2c0e9627e37` |
| Windows score metrics | `e615b8d056963d3df3ab47009b51d4288872df1d14a156626cefc25c9d44ac06` |
| Darwin score metrics | `4c8e9f5707752cc6b2de7e4a29277e6353a841809b825eefaa34977bf0f2205a` |

The dedicated implementation suite was rerun after FULL and passes 11/11.

## Required independent result review

An independent `research-experiment-design` reviewer must now verify execution,
recompute the verdict, and diagnose which aspect of the current construction
caused AP degradation despite the consistent work-to-50 improvement. The
review must distinguish an experiment-design defect, a method/construction
defect, and a genuinely incompatible dataset/estimand.

The reviewer may recommend a materially improved next experiment or algorithm,
but may not tune on held-out Windows/Darwin labels, rewrite the paper, narrow
RQ2, weaken the positive hypothesis, or change the canonical story. Any new
construction must return to a fresh RQ-grounded plan and serial review before
execution.
