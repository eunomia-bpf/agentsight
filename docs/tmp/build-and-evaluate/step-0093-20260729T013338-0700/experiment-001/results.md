# Results: Cross-Framework Same-Task Retrieval

## Outcome

**The frozen paper-admission gate fails.** Complete canonical paths contain
cross-framework task-discriminative information, but the experiment cannot
separate that result from root-label/prompt retention, and the non-root path
does not reliably beat the strongest source-native baseline.

This is a retrospective descriptive result, not an independent estimate of tag
accuracy or operation equivalence.

## Population

- 405 CodeTrace sessions.
- 251 benchmark task IDs.
- Four frameworks: OpenHands, SWE-agent, Terminus2, and mini-SWE-agent.
- 94 tasks and 240 query sessions have a same-task session from another
  framework.
- Candidate libraries contain 192--377 different-framework sessions per query.
- All 405 session IDs contain their task ID; no ID orders an exact-score tie.

## Primary results

| Representation | Task-macro MAP | Query-micro MAP | Pair AUROC |
|---|---:|---:|---:|
| Pre-canonical full path | 0.2452 | 0.2486 | 0.6089 |
| Canonical full path | 0.1949 | 0.2001 | 0.6859 |
| Canonical root-only | 0.1390 | 0.1434 | 0.7101 |
| Canonical root-stripped | 0.1351 | 0.1265 | 0.6330 |
| Root-stripped + generic-work removal | 0.1226 | 0.1166 | 0.5180 |
| Canonical leaf | 0.1139 | 0.1060 | 0.6625 |
| Source action-kind | 0.0927 | 0.0923 | 0.7191 |
| Source raw-action-key | 0.0540 | 0.0593 | 0.5194 |
| Phase control | 0.0358 | 0.0356 | 0.5338 |
| Operation-count control | 0.0228 | 0.0245 | 0.5161 |
| Random control | 0.0180 | 0.0184 | 0.4831 |

MAP and ranking metrics marginalize over permutations within exact-score tie
groups. Pair AUROC assigns tied positive/negative pairs weight 0.5.

## Frozen admission comparisons

Paired deltas use 10,000 percentile-bootstrap replicates over all 94 eligible
task clusters.

| Paired task-macro MAP delta | Point | 95% task-bootstrap interval | Gate |
|---|---:|---:|---|
| canonical full − action-kind | +0.1021 | [+0.0472, +0.1577] | pass |
| canonical full − raw-action-key | +0.1409 | [+0.0825, +0.2009] | pass |
| canonical full − root-only | +0.0559 | [−0.0009, +0.1118] | **fail** |
| root-stripped − action-kind | +0.0424 | [−0.0137, +0.1001] | **fail** |
| root-stripped − raw-action-key | +0.0811 | [+0.0299, +0.1361] | pass |
| root-stripped generic-removed − action-kind | +0.0298 | [−0.0213, +0.0818] | **fail** |
| root-stripped generic-removed − raw-action-key | +0.0686 | [+0.0236, +0.1168] | pass |
| canonical full − pre-canonical full | −0.0504 | [−0.1233, +0.0239] | no canonicalization credit |

The full path also beats the phase and operation-count controls. Binary-presence
and TF-IDF sensitivities preserve full-path advantages over both source-native
baselines, but those sensitivities do not repair the failed root controls.

## Interpretation

The superficial positive result is large: canonical full-path MAP is about 2.1
times action-kind MAP. The strict controls change the conclusion:

1. full path does not reliably beat root-only after task-cluster resampling;
2. after removing the root, the path does not reliably beat action-kind;
3. removing generic `* work` frames weakens the non-root comparison further;
4. pre-canonical task-specific paths have higher MAP than the canonical output,
   so canonicalization cannot receive credit.

The supported observation is therefore only that prompt-conditioned complete
paths retain task information. That observation does not meet the frozen
paper-admission standard and should not be used as positive RQ3 evidence.

## Decision status

- Automatic gate before independent review: **fail**.
- Paper admission: **pending independent recomputation**, but the frozen gate
  cannot become positive unless the reviewer identifies a validity defect that
  requires a documented rerun.
- If the computations are valid, route the next experiment to an external
  programmatic subgoal/operation oracle rather than another CodeTrace
  task-retrieval reanalysis.
