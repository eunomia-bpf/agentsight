# Step 0046 — Existing-Trajectory Process/Phase Baseline Availability Audit

**Gate:** REVIEW
**Started and completed:** 2026-07-17 15:32:35 -0700
**Mode:** bounded read-only repository inspection; no experiment execution
**Decision:** close the optional baseline branch

## Question

Step 0044 identified one *optional* experiment: run the existing standard MAP
scorer on an information-matched, published process/phase view if such a view
already exists naturally in all three RQ2 trajectories and could change the
paper-level conclusion. It explicitly rejected inventing a new mapping,
implementing another system, adding a benchmark, or returning to a custom
budget metric.

The fixed RQ remains:

> **RQ2: Does profiler output correspond to real problems?**

This audit does not change the thesis, RQ, claim, algorithm, paper, or result.

## Inspected inputs

- `script/rq2_standard_localization_metrics.py`, the current standard per-query
  AP/MAP scorer.
- Complete AgentProcessBench group assignments under
  `docs/visexp/out/agentprocessbench-rq2/full/`.
- Complete HINTBench test projection under
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/`.
- Complete TraceElephant projection under
  `.agentsight/experiments/traceelephant-rq2-v1/`.
- Step 0036 and Step 0037 plans, result reviews, and outer audit.

## Availability by workload

| Workload | Naturally retained views/fields | Published, information-matched phase/process baseline available? |
|---|---|---|
| AgentProcessBench | `semantic`, `raw_action`, `session`, `flat`, `ungrouped_risk`; the project-derived semantic stack string contains an internal `phase` component | **No.** Isolating that component would create another project ablation, not recover an independently published process representation. |
| HINTBench | Raw visible `action`, `environment`, `phase`, and `status` fields | **Yes, locally.** A phase-only grouping could be evaluated without new model output. |
| TraceElephant | Raw visible `component`, `intent`, `raw_action`, `role`, `status`, `system`, and `trace_id` fields | **No.** There is no phase field or published same-semantics phase map in the retained projection. |

The strongest already-retained common alternative is operation-local evidence,
which is reported in the paper. Session and source-native alternatives were
also computed and are materially weaker. Raw action is the matched common
grouping baseline across all three complete populations.

## Why no experiment is admitted

A three-workload “phase/process” comparison would require one of the following:

1. compare a natural HINTBench phase field with newly invented mappings for the
   other two workloads;
2. strip one component from AgentProcessBench's project-derived semantic stack
   while substituting `role` or `intent` for phase in TraceElephant; or
3. reimplement an external system's representation over incompatible source
   schemas.

None is a published, information-matched common alternative. Each would add a
new design choice and would be harder to interpret than the existing matched
raw-action and operation-local comparisons. A HINTBench-only phase ablation
cannot overturn the existing three-complete-workload conclusion and would make
the evaluation less uniform.

## Decision and handoff

Do not run this optional experiment. The branch fails the Step 0044 admission
condition before execution: a common natural baseline is unavailable, and
constructing one would add complexity without a credible path to changing the
paper-level RQ2 answer. Preserve the completed standard-MAP evidence and return
to whole-paper REVIEW synthesis.

No source file, paper file, experiment artifact, or Git state was modified by
this audit other than this Markdown report.
