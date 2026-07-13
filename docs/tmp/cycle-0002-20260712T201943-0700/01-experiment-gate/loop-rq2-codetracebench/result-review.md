# Independent Result Review: CodeTraceBench RQ2 Differential Profiling

**Reviewed:** 2026-07-13T00:36:30-07:00
**Reviewer:** independent subagent
**Skill applied:** `research-experiment-design`
**Inputs:** revision-6 plan, complete runner, 3,316-row coverage ledger,
pre-label predictions and control selection, 200 control results, 2,000 outcome
nulls, and 10,000 task-cluster bootstrap replicates

## Verdict

```text
run status: VALID
tested hypothesis: MIXED
research value: supporting
paper impact: mechanism/workload boundary
next paper decision: preserve the fixed RQ, positive hypothesis, thesis, and story;
                     do not edit the paper; route to one stronger independent experiment
```

Execution PASS and scientific support are separate. The complete run is valid,
but the predeclared global superiority hypothesis is not supported on this
construction and benchmark.

This verdict applies only to the tested CodeTraceBench construction:

```text
phase -> action_kind semantic grouping
+ source-valid failed-versus-successful operation excess
+ task-held-out CodeTraceBench references
```

It does not answer RQ2, reject the positive paper hypothesis, challenge the
thesis, change any of the four RQs, or authorize a story or paper edit.

## Evidence Synthesis

### Point estimates favor semantic profiling on two primary summaries

| Method | AP | Recall @ 30% work | Work @ 50% recall |
|---|---:|---:|---:|
| semantic | 0.052290 | 0.307323 | 0.434343 |
| raw-action | 0.042936 | 0.310924 | 0.500144 |
| phase | 0.048382 | 0.310924 | 0.517588 |

Semantic profiling has the highest deterministic AP and reaches 50% recall
with less work. Its recall at the fixed 30% budget is slightly lower than both
matched baselines. These point estimates are useful mechanism evidence, not the
predeclared success criterion.

### The primary paired criterion fails

| Paired AP difference | Bootstrap mean | 95% interval |
|---|---:|---:|
| semantic - raw-action | 0.009443 | [-0.008322, 0.036855] |
| semantic - phase | -0.001548 | [-0.031736, 0.021013] |

Both intervals cross zero. Across task-cluster bootstrap draws, phase mean AP
is 0.053426 and semantic mean AP is 0.051878. The pooled deterministic ranking
therefore does not establish stable cross-task superiority.

### Semantic organization is better than arbitrary coarsening

The 200 retained label-blind frequency-matched partitions have median AP
0.042294 and a 2.5--97.5% range of [0.036177, 0.048459]. Semantic AP exceeds
the best retained partition by 0.001309. This supports a real role for semantic
grouping rather than group count or mass distribution alone.

The margin is small and cannot establish that the outcome-conditioned
differential signal identifies real problems.

### Outcome null identifies the main limitation

The semantic outcome-null mean AP is 0.052879, slightly above the observed
0.052290, with one-sided empirical p=0.531234. Permuting source trajectory
outcomes within the exact matching cells therefore produces localization
scores indistinguishable from the observed failed-versus-successful contrast.

The most defensible diagnosis is that source `solved` outcome is not a stable
step-localization signal under this constructor. Retuning action regexes or
profiling only favorable frameworks cannot repair that identification problem.

### Framework effects are not directionally stable

- Terminus2: semantic AP 0.075917, above raw 0.029395 and phase 0.060169.
- mini-SWE-agent: semantic AP 0.101729, above raw 0.086119 and phase 0.097428.
- OpenHands: semantic AP 0.043697, below raw 0.052215.
- SWE-agent: semantic AP 0.023227, below phase 0.062766.

This is supporting heterogeneity evidence, not authority to select only the two
favorable frameworks after seeing labels.

### Zero-positive and compatibility metrics do not reverse the verdict

Of 405 targets, 206 contain no incorrect step. Semantic pooled false-positive
burden is slightly below raw-action (0.144058 vs 0.151049), but semantic macro
burden is higher (0.159913 vs 0.139679). Raw-action also has higher macro
P/R/F1 than semantic on the 199 positive targets. Phase has very low burden
because its two coarse groups expose little at a complete-block 30% budget, but
its positive-target recall and F1 are poor.

Unuseful and union point estimates are secondary by design and cannot change
the primary verdict.

## Prohibited Follow-Ups

Do not:

- tune `action_kind` regexes on CodeTraceBench verified labels;
- select only Terminus2 and mini-SWE-agent as the reported population;
- change the 405-target estimand or declared metrics after seeing results;
- place this negative/mixed result in the paper story;
- narrow RQ2, replace the positive hypothesis, or rewrite the thesis; or
- interpret execution PASS as hypothesis support.

The complete result remains an internal mechanism boundary and searchable
experiment history.

## Single Next Experiment

Run one **ToolSafe TS-Bench operational-effect transfer experiment** under the
same fixed RQ2.

### Tested hypothesis instance

> A cross-run profile learned from real safety and utility outcomes on other
> tasks and benchmark families, organized by structured tool/resource effects,
> concentrates hidden unsafe or controversial tool invocations more strongly
> and with less inspection work than equally informed raw-tool and
> source-native baselines.

This is larger, not narrower: it moves from coding-step correctness to real
operational safety across AgentHarm-, ASB-, and AgentDojo-derived families while
retaining the paper's claim that semantic profiling corresponds to real
problems.

### Required real assets and protocol

- official ToolSafe/TS-Bench repository and released family-specific
  trajectories;
- official TS-Bench strict-mode protocol, where controversial is evaluated as
  unsafe, plus published macro accuracy/F1/recall;
- official source benchmark safety, attack-success, refusal/completion, and
  utility outcomes where available;
- target labels used only in terminal scoring; and
- leave-task, leave-domain, and leave-family transfer so a target and its
  semantic near-duplicate cannot build its own profile.

### Proposed and matched organizations

- proposed: `service/resource -> operation/effect -> success/error`, frozen
  from official structured tool schemas and observable execution results;
- baseline 1: raw tool identity under the same references and signal;
- baseline 2: source-native chronological/tool organization under the same
  references and signal;
- published direct-diagnosis reference: official TS-Guard strict-mode results,
  cited under its own model/token protocol rather than presented as an equally
  informed profile baseline.

The primary profile metrics remain hidden-label AP, recall at 30% inspection,
and work to 50% recall. Official strict-mode macro F1/recall are compatibility
metrics. Task/domain-clustered paired bootstrap must give positive AP intervals
against both matched baselines, and all three evaluation families must avoid a
direction reversal.

## Why This Route

The current failure is not a wording problem or a small semantic classifier
mistake. The source run outcome does not statistically identify target
incorrect steps. ToolSafe supplies an untouched public family with explicit
operational safety effects and published protocol, enabling a stronger real
signal and independent cross-domain evidence without reusing CodeTraceBench
labels or weakening the claim.

Before implementation, `research-literature-novelty` must re-audit the current
official repository, dataset units, train/eval boundary, source outcomes,
published baselines, and exact strict-mode metric equations. Then
`research-experiment-design` must propose and serially review one Markdown plan.
No paper edit is authorized before that experiment completes result review.
