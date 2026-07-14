# Real Preflight Report

- Completed: `2026-07-14T10:07:00-07:00`
- Status: **PASS**
- Real input: completed AgentProcessBench full-run summary and independent full
  execution report

The approved read-only path extracted the semantic and raw-action macro AP,
their paired interval, the matched-refinement permutation, execution status,
and original scientific verdict directly from
`docs/visexp/out/agentprocessbench-rq2/full/summary.json`.

Extracted values were semantic AP `0.5876552758661584`, raw-action AP
`0.5561333744490712`, delta `0.03152190141708722`, 95% interval
`[0.015137772679136302, 0.05351434768663876]`, matched-permutation
`p=0.009950248756218905`, exact size preservation `true`, execution status
`VALID`, and original verdict `INCONCLUSIVE`.

All rounded values and the original verdict match
`docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/full-execution-report.md`.
The first extraction used an incorrect interval selector and returned `null`;
inspection found the existing value under `bootstrap.intervals`, and the
corrected read-only command returned the reviewed interval. No input, result,
metric, code, or plan changed.

The real input, metric, baseline, uncertainty, matched control, and report
comparison path all work. Proceed to all three planned workloads.
