# Milestone Review 001 — Full-Paper Reread Assessment

**Completed:** 2026-07-15T07:12:00-07:00  
**Paper:** complete `docs/paper/main.tex` after source verification  
**No paper edit occurred in this review**

## What Survives The Closest-Work Attack

The exact thesis remains strong and should not change:

> **Agent observability needs profiling, not only debugging.**

Cross-trace clustering and dashboards are no longer novel by themselves.
However, the paper's actual principle survives: one set of source-linked
operations can carry additive token, time, file, process, network, and other
effects; ordered semantic fields define selectable responsibility stacks; and
folding conserves each selected weight in pprof-compatible output. LangSmith
Insights, Datadog Patterns, and NeMo's profiler make this distinction more
precise, not smaller.

The four RQs also remain the right architecture and are not renamed, merged, or
narrowed:

1. resource attribution;
2. problem correspondence/localization;
3. tag accuracy;
4. profiling cost.

## Updated RQ Assessment

### RQ1 — resource attribution

The source-lineage and conservation evidence is coherent and is the paper's
strongest systems result. The question is answered for the declared offline
scope. A future end-to-end experiment may connect it to a decision, but another
lineage microbenchmark is not the best use of the current budget.

### RQ2 — problem correspondence

The cumulative result is positive but bounded: profiler groups improve a
fixed reader's selected-positive recall on five of six tasks and precision on
four of six, while work rises on four of six. This supports prioritization, not
universal inspection reduction. Insights Generator, CodeTracer, and
AgentTelemetry show that downstream repair or intervention is the eventual
decisive standard. The current user request is algorithm improvement on
existing traces, so RQ2 is not selected for the immediate experiment.

### RQ3 — tag accuracy

This remains the most visible paper blocker. The paper promises target-blind
task, phase, action, and group identities but directly supports task partitions
and group boundaries only. The current label-free recurrence constructor is
post-hoc, slightly below external phase-change on pooled CodeTraceBench
B-cubed, and uses only action-pair recurrence despite both corpora already
containing richer source-visible fields and independent reference annotations.

Step 0026 correctly closed further *action-only, unsupervised, local cutoff*
tuning. It did not prove that the existing trajectories cannot improve the
constructor. The verified inputs expose a different, principled route: treat
the current recurrence score as the mechanism and learn only its boundary
calibration from independent labeled reference trajectories. This changes the
information contract, not the paper RQ or story. At inference, the 405
CodeTraceBench target stages and each OSWorld held-out fold remain hidden.

### RQ4 — cost

The measured offline construction path is sufficiently answered. Another
cost variant is lower value than closing RQ3 or RQ2.

## Rechecked Reject Hypotheses

| Attack | Status after external verification | Required response |
|---|---|---|
| RQ3 is incomplete | **Still blocking** | Add supporting target-label-withheld boundary-calibration evidence on existing trajectories; phase/action/literal-name accuracy remains open and the RQ is not narrowed. |
| RQ2 lacks decisive consequence | **Still major** | Later run a fixed decision/repair protocol; do not add another score or benchmark-only cell now. |
| Constructor is post-hoc and weaker than one simple external view | **Still major and immediately actionable** | Use the same trajectories and current recurrence score, with independent reference-label calibration and the label-free release as baseline. |
| Closest work already does cross-trace grouping | **Verified** | Keep novelty on source linkage, additive conservation, selectable stacks, and pprof compatibility. Add Insights Generator in a later WRITE pass. |
| Paper format incomplete | **Verified** | Complete the AAAI reproducibility checklist before submission. |

## Exact Experiment Routing

Route the next step to `research-experiment-design`, RQ3, with no new source.
Its planned role is **supporting** group-boundary evidence, not a complete or
decisive answer to all of RQ3. The candidate is not another algorithm family
and not another benchmark:

```text
existing operation sequences
-> unchanged action-transition NPMI recurrence score
-> boundary cutoff learned only from independently annotated reference sessions
-> unchanged segments, motifs, operation stacks, folding, and metrics
```

- OSWorld-Human keeps the existing five session-held-out folds; each fold's
  calibration uses only the other four folds' human boundaries.
- CodeTraceBench uses the 483 verified, already-normalized non-target
  trajectories as the labeled reference and the same 405 failed trajectories
  as a target-label-withheld reused development population. The reference
  population is solved while the target population is failed, so the result
  explicitly tests that distribution shift rather than assuming matched
  populations or claiming untouched confirmation.
- The current Step 0024 label-free constructor is the main baseline. The
  existing supervised OSWorld predictor and external CodeTraceBench
  phase-change view are comparators, not new runs.
- Primary metric remains operation-weighted B-cubed F1 on each complete target
  population; boundary F1 is diagnostic.
- No target labels, new benchmark, reader, score family, parameter sweep, or
  paper-story change is allowed.

This is a direct improvement mode of the existing algorithm on already-run
traces.
It is a supervised calibration mode, so a positive result cannot be mislabeled
as label-free evidence. A positive result supports an annotation-availability
tradeoff for scalar group-boundary calibration while preserving the simple
operation-stack story; phase, action, literal-name, and whole-RQ accuracy remain
open.
