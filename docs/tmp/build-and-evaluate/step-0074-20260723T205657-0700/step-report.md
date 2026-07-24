# Step 0074 Report — Fixed Recursive RQ3 Backend

**Timestamp:** 2026-07-23T21:43:00-07:00
**Gate:** EXPERIMENT
**Status:** complete; valid negative result; route to RQ4

## Node 0074-E1 — resume the fixed complete run

The step resumed `recursive-operation-segmentation-v4` without changing its
model, prompt, grammar, source projection, split/stop policy, seed, context
limit, or decision rule. It retained 256 valid complete session caches, removed
only three empty interrupted writes, and completed the remaining 149 sessions.
Official stages, recurrence assignments, prior candidate outputs, and scores
were not inputs to inference.

One execution-only correction removed preflight-only tokenizer work from full
mode. The inference contract SHA-256 remained
`73dd70e987d6f573bfaab2c13e4c91f8294cdc4a5ccd176e2d2c970ad27ae853`.
Four wall-time regions were also observed without entering the RQ3 decision.

## Node 0074-E2 — complete source-only population

All 405 sessions, 17,148 source-native turns, and 20,866 operations were
materialized before scoring. The fixed local Qwen3.6-27B backend made 1,990
calls and produced 1,068 leaves/marks. Only 73 sessions contained an internal
split; 332 remained one segment. Observed semantic depth was one through five
over the complete population.

Both required pprof files load in stock `go tool pprof` and conserve exact
operation mass:

- complete population: 20,866;
- fixed long-horizon collection: 5,750.

The long-horizon collection has no path with five semantic frames and therefore
fails the plan's positive semantic-usefulness condition. No paper figure or
case claim is admitted from this candidate.

## Node 0074-E3 — score once after prediction completion

The official verified stages were opened only after all predictions and
profiles existed. Ordinary unweighted operation-level B-cubed and exact
adjacent-boundary F1 give:

| Method | B³ F1 | Boundary F1 |
|---|---:|---:|
| Recursive v4 | .386034 | .090455 |
| Multi-resolution recurrence | .662740 | .265571 |
| Causal Qwen 3B | .649878 | .256606 |
| Native source tree | .396530 | .259373 |
| Source-native turn | .361145 | .246396 |

Recursive v4 emits 863 predicted occurrences for 2,948 official stages.
Its B-cubed precision/recall is `.242532/.945422`; boundary recall is
`.057019`. It replaces fragmentation with severe undersegmentation.

Candidate minus recurrence has a task-clustered 10,000-resample 95% interval
of `[-.306589,-.245664]`; candidate minus causal Qwen is
`[-.293000,-.233085]`. The candidate loses both standard metrics in all four
frameworks. The registered tested hypothesis is contradicted.

## Node 0074-E4 — independent reconstruction

An independent reviewer using the research-experiment-design skill rebuilt the
prediction-to-mark and prediction-to-score linkage, all aggregate and
per-framework metrics, both 10,000-draw bootstraps, cache/model identity,
pprof hashes, and pprof mass. The reconstruction matches to floating-point
precision and gives:

- run: **VALID**;
- hypothesis: **CONTRADICTED**;
- research value: supporting negative mechanism evidence;
- paper impact: mechanism boundary only.

The reviewer also records two cost boundaries:

1. 6.80M logical model tokens are a valid complete-cache total;
2. the 1,762.63-second resumed wall time includes 256 cache hits and is not a
   fresh 405-session annotation latency.

## Node 0074-E5 — scientific disposition

The recursive v4 backend is closed and not adopted. No prompt retry, cutoff,
contraction, new benchmark, story rewrite, RQ change, or paper edit follows.
A2 remains the current paper backend, while Step 0073 retains its
fixed-instruction follow-on boundary.

The next outer node is a separate RQ4 experiment. It will reuse complete
backend executions and report source adaptation, automatic annotation, and
pprof materialization separately. Backend quality and cost must remain paired:
v4 cost cannot become the positive product cost, and A2 quality cannot inherit
v4 timing.

## Evidence

- [full run and root result](experiment-001/full-run-and-result.md)
- [independent result review](experiment-001/independent-result-review.md)
- [resume and real-execution report](experiment-001/resume-and-preflight-report.md)
- [closest-work and baseline update](01-experiment-gate/closest-work-and-baseline-update.md)
