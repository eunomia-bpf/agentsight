# Full-Run Report — RQ3 Fixed-Instruction Follow-On

**Timestamp:** 2026-07-23T20:42:00-07:00
**Status:** complete
**Decision:** INCONCLUSIVE under the approved B-cubed hypothesis

## Population and execution

The approved scorer filtered the existing current-A2 rows to the complete
manifest-defined follow-on population:

- 364 sessions;
- 15,116 operations;
- 14,752 adjacent pairs;
- 238 task clusters;
- all four CodeTrace frameworks;
- zero overlap with the initial 41 long-horizon sessions.

The full 10,000-resample run completed in 0.89 seconds with 84.1 MiB maximum
RSS. This timing is scorer cost, not automatic annotation cost and not an RQ4
paper result.

## Standard metrics

| Method | B³ P | B³ R | B³ F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Current automatic Agent A2 | 0.910237 | 0.535911 | 0.674628 | **0.402802** |
| Multi-resolution recurrence | 0.758227 | 0.627664 | **0.686795** | 0.289023 |
| Native source tree | 0.977391 | 0.269893 | 0.422985 | 0.285869 |
| Source-native turn | 0.993477 | 0.196407 | 0.327974 | 0.251788 |

The approved primary comparison is A2 minus recurrence B-cubed F1:

- point difference: `-0.012167`;
- 10,000-resample mean difference: `-0.012091`;
- task-cluster 95% interval: `[-0.027266, +0.003221]`;
- positive-draw fraction: `0.0577`.

The interval crosses zero, so the positive hypothesis is inconclusive. It is
not contradicted under the approved rule because the upper endpoint is
positive.

## Framework heterogeneity

| Framework | A2 B³ F1 | Recurrence B³ F1 | Delta | A2 boundary F1 | Recurrence boundary F1 |
|---|---:|---:|---:|---:|---:|
| OpenHands | .669585 | .684925 | -.015340 | .391439 | .279375 |
| SWE-agent | .659321 | .726080 | -.066758 | .348968 | .323864 |
| Terminus2 | .701945 | .660118 | +.041827 | .433253 | .312121 |
| mini-SWE-agent | .662271 | .691523 | -.029252 | .431933 | .276013 |

A2 has substantially higher exact-boundary F1 in every framework, including
the three where recurrence has higher B-cubed. The two metrics expose a real
precision/fragmentation tradeoff rather than an implementation failure:

- A2 has higher B-cubed precision (`.910` versus `.758`) but lower recall
  (`.536` versus `.628`);
- A2 produces 5,198 predicted occurrences for 2,382 official stages;
- 1,623 A2 occurrences (31.2%) contain one operation;
- recurrence produces 4,131 occurrences and is also oversegmented, but less so.

## Scientific interpretation

The union result `.704` versus `.663` does not generalize uniformly to the
follow-on subset. The initial 41-session product collection is selected by
long trajectory length and is heavily Terminus2-weighted (28 Terminus2, 11
OpenHands, 2 SWE-agent, no mini-SWE-agent), whereas the follow-on population is
dominated by OpenHands and includes all 71 mini-SWE-agent sessions. This
distribution difference is fixed by the earlier manifest; it was not selected
after this result.

The current A2 backend is better at placing exact transitions but fragments
semantic stages too aggressively on the shorter and broader follow-on
population. That is an actionable algorithm diagnosis. It does not authorize
changing RQ3 or the thesis, and it does not justify selecting another subset,
cutoff, or score.

## Next scientific decision

Do not tune A2 boundaries on these stage labels. The highest-value next RQ3
test is the already implemented, source-only recursive Qwen3.6-27B backend:
complete its existing interrupted run under its fixed binary segmentation
policy, score the full population once, and report its automatic-annotation
cost separately under RQ4. This directly tests whether a reproducible recursive
backend reduces the observed fragmentation without inventing a gold-driven
contraction rule.
