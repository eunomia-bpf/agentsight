# Experiment Plan: RQ2 Cumulative Baseline Synthesis

## Research Question

- RQ exactly as written in the paper: **RQ2: Does profiler output correspond
  to real problems?**
- Specific uncertainty tested here: whether the complete existing RQ2 evidence
  shows that target-blind semantic operation stacks concentrate independently
  annotated problems beyond structural grouping alone, once all already-run
  baselines and prospective outcomes are considered together.
- Why the answer matters: the current seven-page paper shows only one compact
  raw-action comparison per workload, which makes completed evidence appear
  absent and can conceal where the evidence is semantic-specific versus merely
  an early-curve effect.

## Paper-Value Admission

- Planned role: **decisive reanalysis**.
- Largest credible paper story this experiment could unlock: semantic profiling
  exposes recurring responsibility groups enriched for real problems across
  heterogeneous public agent workloads, while retaining a clear distinction
  from per-step signals and per-session drilldown.
- Strongest reviewer reject argument addressed: RQ2 uses a weak raw-action
  baseline and favorable operating points, so the reported utility may be an
  artifact of grouping granularity or selective presentation.
- Independent evidence added beyond existing runs: no new observations; the
  scientific addition is one provenance-preserving integrated proof from three
  independently audited complete experiments that the paper currently reports
  separately and incompletely.
- Why the result is not tautological, already settled, or dominated: the three
  experiments used different public targets and prospective metrics, and their
  complete control surfaces have not yet been jointly reviewed against one
  paper-level hypothesis.
- Paper decision if positive: WRITE a compact full-baseline RQ2 synthesis while
  retaining the fixed thesis, RQ, and ambitious correspondence claim.
- Paper decision if contradictory, mixed, or inconclusive: do not invent a
  stronger aggregate; return the exact unresolved mechanism to REVIEW so it can
  select a genuinely different experiment.
- Best alternative experiment: a profile-derived intervention on existing
  trajectories. It has higher implementation cost and is premature until the
  completed evidence is correctly synthesized.

## Expected And Alternative Outcomes

- Current expected answer: AgentProcessBench supplies semantic-specific AP
  evidence; HINTBench supplies a positive 80%-recall comparison against native,
  independent-step, and session organization; TraceElephant supplies positive
  descriptive early concentration. The high-recall and raw-action comparisons
  are not expected to be uniformly positive.
- Strongest competing explanation: gains arise only from the released step
  signal, finer partitions, or a favorable curve point rather than semantic
  grouping.
- Result that would contradict the expectation: the audited controls show no
  semantic-specific positive result, or every positive point is dominated by a
  same-information structural view under its existing metric.

## Published Precedent And Real Assets

- Closest published protocols: AgentProcessBench's human-labeled process
  quality, HINTBench's released localization targets, and TraceElephant's
  responsible-agent/decisive-step targets.
- Official data: complete existing snapshots already used by the three audited
  experiments.
- What is reused: their full-run JSON summaries, bootstrap/permutation results,
  original plans, full result reviews, and existing AgentProf outputs.
- Necessary deviations or custom glue: none. Standard `jq`, `rg`, and direct
  report comparison will extract existing fields into one Markdown report.

## Comparison

- Proposed method: the already-run AgentProf semantic profile in each workload.
- Main baseline: raw-action grouping, representing a compact recurring view
  without semantic responsibility fields.
- Structural references where already present: native order, independent step,
  session, flat/reconstruction identity, and width-only grouping.
- Diagnostic controls where already present: ungrouped risk, matched semantic
  permutation, and oracle. These are not main baselines and cannot establish a
  proposed-method win by losing.
- Information fairness: use only each completed experiment's original inputs,
  signals, mappings, splits, and outputs. No reranking or retuning.

## Workloads And Metrics

- AgentProcessBench: existing macro AP and Work@50, four-family results,
  bootstrap interval, matched-refinement permutation, and group counts.
- HINTBench: existing Work@80, paired trajectory bootstrap intervals, and group
  counts.
- TraceElephant: existing prospective Work@80 result and permutation outcome
  first; existing Work@50 and Recall@20 descriptive curve points second; group
  counts.
- Per-workload verdict rule: reproduce the original full experiment verdict
  unchanged. A prospective primary component is positive only when its original
  uncertainty or matched-null test excludes the null; an inconclusive or
  contradictory primary result stays so. Secondary curve regions may explain
  behavior but cannot change a workload verdict.
- Cumulative paper-level rule: call the evidence **supporting** only if at least
  two independent workloads contain a positive prospective primary component,
  at least one positive is semantic-specific under a matched/null control, and
  no workload has an originally supported primary contradiction. Call it
  **mixed** if a supported primary contradiction coexists with a positive; call
  it **inconclusive** if fewer than two workloads or no semantic-specific
  control supports the hypothesis. Report this synthesis separately from the
  unchanged original workload verdicts.
- Correctness: every extracted number must match both the raw summary and the
  corresponding independent full-result review.
- Repetitions/uncertainty: reuse the completed bootstrap and permutation runs;
  do not create new resamples.

## Planned Runs

| Run group | Role | Workload | Method/control | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| APB extraction | proposed, baseline, controls | AgentProcessBench full 1,000 trajectories | semantic, raw action, flat, session, ungrouped risk, matched permutation | existing full run | tests semantic-specific concentration |
| HINT extraction | proposed, baseline, controls | HINTBench full 536-test-trajectory snapshot | AgentProf, raw action, native, independent step, session, flat identity, width only | existing 10,000 bootstrap | tests high-recall inspection work |
| Trace extraction | proposed, baseline, controls | TraceElephant all 220 failures | AgentProf, raw, source native, independent step, session, flat, width only, oracle, matched permutation | existing full run and resampling | separates prospective high-recall and descriptive early-region evidence |

## Execution

- Authoritative inputs:
  - AgentProcessBench raw summary:
    `docs/visexp/out/agentprocessbench-rq2/full/summary.json`; review:
    `docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/full-execution-report.md`.
  - HINTBench raw summary:
    `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/summary.json`;
    review:
    `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/full-result-review.md`.
  - TraceElephant raw summary:
    `.agentsight/experiments/traceelephant-rq2-v1/metrics/summary-full.json`;
    review:
    `docs/tmp/build-and-evaluate/step-0004-20260713T172452-0700/01-experiment-gate/loop-001-rq2-traceelephant/008-independent-result-review-20260714T011915-0700.md`.
- Direct read-only workflow from repository root:

  ```bash
  jq '{execution_status, scientific_verdict, effects:.results.effects, macro:.results.macro, bootstrap:.bootstrap, shuffle:.shuffle}' docs/visexp/out/agentprocessbench-rq2/full/summary.json
  jq '{execution_status, scientific_verdict, decision, methods:(.point_results.primary | with_entries(.value |= {groups, selected, reached_80_macro_recall})), intervals:.bootstrap.intervals}' docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/summary.json
  jq '{execution_status, scientific_verdict, verdict_details, methods:(.point_results | with_entries(.value |= {groups, work_at_macro_recall, recall_at_work})), bootstrap, permutation}' .agentsight/experiments/traceelephant-rq2-v1/metrics/summary-full.json
  rg -n 'verdict|primary|inconclusive|supported|interval|permutation|Work@|average precision' docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/full-execution-report.md docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/full-result-review.md docs/tmp/build-and-evaluate/step-0004-20260713T172452-0700/01-experiment-gate/loop-001-rq2-traceelephant/008-independent-result-review-20260714T011915-0700.md
  ```
- Real preflight: extract AgentProcessBench semantic/raw AP and its matched
  permutation result, then verify exact agreement with the independent review.
- Full completion rule: every planned workload, baseline/control role,
  prospective result, uncertainty result, and descriptive result is represented
  in one Markdown synthesis with zero unexplained mismatch.
- Synthesis output:
  `docs/tmp/build-and-evaluate/step-0011-20260714T095842-0700/01-experiment-gate/loop-001-rq2-cumulative-baseline-synthesis/full-result-report.md`.
- No copied or transformed raw-result file is created.
- Recovery: rerun the read-only extraction for any mismatch; never change the
  underlying result.

## Interpretation

- Positive/supporting: the cumulative rule above passes; this does not relabel
  any original inconclusive workload experiment as successful.
- Contradictory: same-information controls explain or dominate every claimed
  semantic benefit.
- Mixed/inconclusive: preserve the per-workload verdicts and return the exact
  unresolved alternative to REVIEW; do not average incompatible metrics.
- Target paper output: one compact RQ2 table or figure plus prose that exposes
  the strongest existing baselines and distinguishes prospective from
  descriptive evidence.

## Reproducibility Notes

- Software/data versions and commands remain those recorded by the completed
  experiments.
- No code, config, seed, input, model, mapping, score, or threshold changes.
- This step is a full reuse analysis, not a new data-collection run.
