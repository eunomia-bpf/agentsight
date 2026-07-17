# Experiment Result: Standard RQ2 Localization Metrics

**Status before independent review:** full run complete; result not yet admitted

**Research question:** Does profiler output correspond to real problems?

**Tested hypothesis:** On each of the three already-complete public RQ2
workloads, the fixed AgentProf operation-stack score has higher
trajectory-level MAP than the matched raw-action score.

## What Ran

The experiment reused the completed AgentProcessBench, HINTBench, and
TraceElephant artifacts without invoking a model, profiler, tagger, localizer,
benchmark generator, or new ranking method. One read-only adapter reconstructed
the fixed per-operation scores and called
`sklearn.metrics.average_precision_score` for each target-bearing trajectory.

The real preflight command was:

```text
python script/rq2_standard_localization_metrics.py preflight --out .agentsight/experiments/rq2-standard-map-existing-trajectories-v1/preflight
```

It loaded one real target-bearing trajectory from each benchmark and produced
six finite AgentProf/raw AP values. Its verdict remained
`NOT_EVALUATED_PREFLIGHT`.

The complete command was:

```text
python script/rq2_standard_localization_metrics.py full --out .agentsight/experiments/rq2-standard-map-existing-trajectories-v1/full --bootstraps 10000 --seed 20260716
```

It loaded all 1,756 trajectories and 27,346 operations: 1,000/8,509 from
AgentProcessBench, 536/12,877 from HINTBench, and 220/5,960 from
TraceElephant. Raw point estimates, every per-query AP row, and all 30,000
bootstrap draws are under
`.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/full/`.

## Standard Metric Definition

One target-bearing trajectory is one query; its operations are ranked items;
independently annotated problem operations are relevant items. AP is
scikit-learn 1.4.1.post1's non-interpolated average precision, and MAP is the
unweighted arithmetic mean over target-bearing trajectories. Equal scalar
scores stay tied at the same threshold. No operation ID, timestamp, file order,
or post-result cutoff breaks a tie.

This is the standard per-query AP/MAP construction documented by
[NIST TREC](https://trec.nist.gov/presentations/TREC9/overview/tsld014.htm),
using the published
[scikit-learn AP implementation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
MAP is conditional on a trajectory containing at least one relevant item:
AgentProcessBench contributes 614 of 1,000 trajectories, HINTBench 400 of 536,
and TraceElephant 220 of 220. Pooled operation AP is reported separately over
all operations, retaining the 386 AgentProcessBench and 136 HINTBench
zero-positive trajectories as nonrelevant work.

## Primary Result

| Complete workload | MAP queries | AgentProf MAP | Raw-action MAP | Difference | Paired 95% interval |
|---|---:|---:|---:|---:|---:|
| AgentProcessBench | 614 | 0.7889 | 0.7732 | +0.0157 | [0.0047, 0.0271] |
| HINTBench | 400 | 0.4529 | 0.2815 | +0.1714 | [0.1545, 0.1887] |
| TraceElephant | 220 | 0.2302 | 0.1213 | +0.1089 | [0.0780, 0.1413] |

The registered sign rule is satisfied: the complete-population AgentProf-minus-
raw MAP point estimate is positive on all three workloads. The tested
hypothesis is therefore **supported**, subject to independent result review.
There is no cross-benchmark average or custom composite score.

## Standard Secondary Result And Controls

| Workload | AgentProf pooled AP | Raw pooled AP | Other trajectory-level MAP controls |
|---|---:|---:|---|
| AgentProcessBench | 0.6918 | 0.6688 | atomic 0.8632; session/flat 0.4481 |
| HINTBench | 0.2497 | 0.1805 | atomic 0.4106; session 0.1112; flat-identity 0.4529 |
| TraceElephant | 0.0776 | 0.0528 | atomic 0.2087; source-native 0.0796; session/flat 0.0590 |

The standard pooled sensitivity has the same AgentProf-over-raw direction on
all three workloads. The controls bound the interpretation rather than
changing the primary comparison:

- AgentProcessBench's per-operation judge score remains stronger than its
  grouped profile. AgentProf improves over raw action but does not dominate the
  atomic signal.
- HINTBench and TraceElephant reverse that boundary: the grouped AgentProf MAP
  is higher than the respective atomic localizer score.
- HINTBench `flat-identity` is an implementation identity check over the same
  selected leaves and scores, not an independent flat-profile baseline. Its
  native view uses ordinal ordering and therefore remains only in the already
  reviewed Work result, not the scalar MAP matrix.

The three HINTBench official targets absent from the released displayed-step
projection are counted as unretrieved in a registered sensitivity. AgentProf
MAP changes from 0.452852 to 0.452121 and raw action from 0.281491 to 0.280827;
the conclusion is unchanged.

## Uncertainty

Each benchmark used 10,000 paired bootstrap draws with seed `20260716`.
AgentProcessBench resampled all 200 released task clusters within four families
and carried every target-bearing trajectory from a sampled task together.
HINTBench resampled its 400 target-bearing records within 44 environments.
TraceElephant resampled 220 traces within five cells. The nearest-rank intervals
in the primary table are positive. AgentProcessBench has 21 nonpositive draws;
HINTBench and TraceElephant have none.

## Interpretation Boundary

This result supports a standard ranking statement: for a trajectory known to
contain an independently annotated problem, AgentProf's fixed semantic
operation-stack score ranks the problem operations earlier than raw-action
organization on all three complete public workloads. Pooled AP adds the same
direction while retaining safe/zero-positive work.

The result does not claim that every grouped view dominates every atomic or
session view, that MAP directly measures human debugging time, or that the
existing Work curves should be discarded. Work@80/Work@50 remain secondary
inspection diagnostics. The fixed thesis, RQ2, two abstractions,
contributions, and paper story are unchanged.
