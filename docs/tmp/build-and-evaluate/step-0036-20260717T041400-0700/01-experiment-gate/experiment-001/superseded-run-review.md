# Superseded Full Run Review

- recorded: 2026-07-17T05:14:43-0700
- experiment: Step 0036, RQ2 same-signal diagnostic decomposition
- disposition: superseded before claim use
- paper or evaluation integration: none

## Run Covered

The first complete execution covered the approved 1,756-trajectory,
27,346-operation population and produced all planned AgentProf, raw-action,
atomic, and session results plus 10,000 paired cluster-bootstrap draws.  Its
raw artifacts were present under
`.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full/`.
Before replacement, the three principal files had these SHA-256 digests:

- `summary.json`: `5a5e4237c86c56d4c2dd37dc2dac287da370aa861966b6168326aa7fde977cc9`
- `per-query.jsonl`: `cb0baebea328c5df545b73b2924fffc28f1aa8d644ab73d5641ebdafc5f2598b`
- `bootstrap-deltas.json`: `fa52dc8e5aafd37416e944e7e21ad13217febbcc0c44a338db5b7266e6b95bd6`

The run reported the following MAP / expected Recall@20% pairs:

| Benchmark | AgentProf | Raw action | Atomic | Session |
|---|---:|---:|---:|---:|
| AgentProcessBench | 0.788919 / 0.562766 | 0.773170 / 0.544346 | 0.863171 / 0.651185 | 0.448076 / 0.316667 |
| HINTBench | 0.452852 / 0.574109 | 0.281491 / 0.486033 | 0.410559 / 0.548394 | 0.111239 / 0.218858 |
| TraceElephant | 0.230168 / 0.457529 | 0.121270 / 0.348270 | 0.208713 / 0.332129 | 0.059042 / 0.223719 |

## Independent Review Finding

A fresh result reviewer reconstructed the populations, per-query AP,
fixed-budget tie handling, and bootstrap effects from the raw artifacts.  The
main ranking results recomputed exactly, and the raw-action and atomic
comparators were both genuinely engaged.  The reviewer nevertheless marked
the run invalid for claim use because the retained Wilson implementation can
return floating residues of approximately `1e-17` when the mathematical lower
bound is zero.  The adapter interpreted every value greater than zero as clean
support, which inflated HINTBench's project-defined clean propagation control
and slightly perturbed rankings among zero-evidence operations.

The defect is numerical rather than scientific: zero-hit Wilson values must be
canonicalized to exact zero within machine precision.  The reviewer estimated
that the corrected HINTBench MAP would be approximately 0.452373 for AgentProf
and 0.281237 for raw action, leaving the substantive AgentProf-minus-raw effect
positive.  Recall@20% is unaffected.  AgentProcessBench and TraceElephant are
scientifically unaffected.

The review also found that three of HINTBench's 938 official target steps are
absent from the released operation projection (`test:170` step 7, `test:233`
step 9, and `test:516` step 13).  The approved plan required the corresponding
mapped-target sensitivity, but the first run did not report it.  Finally, the
review required all 24 retained validation field-order candidates to be
re-evaluated after zero canonicalization before reusing the selected test
profile.

## Authorized Correction

The replacement run may make only the following changes:

1. map floating values within `64 * ulp(1.0)` of mathematical zero to exact
   zero before ranking or support classification;
2. re-evaluate the already materialized 24 HINTBench validation candidates and
   confirm that the selected field order remains unchanged;
3. report the planned sensitivity that treats projection-absent official
   targets as unrecovered; and
4. record input roots and Python/scikit-learn versions.

It may not change the localizer, profile, field order, score definition,
benchmark population, model, RQ, tested hypothesis, or paper story.  The first
run supplies no paper claim and is retained here only as an auditable failure
record.

## Corrected Attempt 2: Pooled-AP Bypass

- executed: 2026-07-17T05:15:04-0700
- independent review completed: 2026-07-17T05:31:00-0700
- disposition: superseded before claim use
- `summary.json` SHA-256:
  `ba542f7393328e07645749640e44137dd9d230abea26eaee4871667ee4a3ff94`
- `per-query.jsonl` SHA-256:
  `e4efaa62b4a7ace599309f2876adb17a9efe4333fa185b219f6996fd7f795af1`
- `bootstrap-deltas.json` SHA-256:
  `625aad9e06443464eaa44ea00e8bacf11ccd37601be9e965938f79f2592a4f25`

Attempt 2 correctly canonicalized the scores used by every per-query MAP,
Recall@20%, target sensitivity, clean-support, and bootstrap calculation.  An
independent reviewer reproduced all 1,234 per-query rows and all 120,000 draws,
confirmed that the tolerance was more than 454 million times smaller than a
hypothetical one-hit Wilson score over all 27,346 operations, and reproduced
the unchanged HINT validation selection over all 24 field orders.

The attempt was still invalid for claim use because pooled AP selected
operations from the original loaded benchmark object rather than the corrected
per-query grouping.  That secondary path therefore restored floating residues
for HINTBench.  Reported versus corrected pooled AP was:

| View | Attempt 2 | Correct value |
|---|---:|---:|
| AgentProf | 0.249713778372 | 0.249439433307 |
| Raw action | 0.180483969360 | 0.180366365748 |
| Atomic | 0.266199343048 | 0.266199343048 |
| Session | 0.104413047480 | 0.103928182703 |

The authorized repair changes only that list source: pooled AP must flatten the
already canonicalized operation groups used by every other metric. It does not
change any input, score definition, scientific result, metric, profile, field
order, or paper claim. Attempt 2 supplies no paper number or table.
