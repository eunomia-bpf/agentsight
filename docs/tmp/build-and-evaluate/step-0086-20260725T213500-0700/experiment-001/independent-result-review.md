# Independent result review

Review mode: fresh, read-only result audit after Phases 1--4  
Verdict: **valid and complete**

## Evidence independently confirmed

- The workspace contains 10,423 nodes: 42 session, 1,252 prompt, 5,620
  LLM, and 3,509 tool nodes.
- The annotation contains 1,737 boundaries. All 1,294 mandatory session and
  prompt scopes are covered, with no invalid references, crossing ranges,
  uncovered nodes, or derived-path mismatches.
- All 42 batch records are unique, complete, and `status=ok`; their
  annotations merge exactly to the final annotation.
- Stock `go tool pprof` loads both profiles:
  - operation profile: 3,509 samples and exact mass 3,509;
  - token profile: 5,620 samples and exact mass 1,380,863,014.
- Usage recomputes to 15,231,328 input, 13,112,320 cached input, 311,097
  output, and 107,830 reasoning-output tokens.
- The fixed instruction is present verbatim, followed only by the operational
  batch-scope appendix. The protocol used one pass, immediate per-batch
  validation, and no aggregate-aware revision.
- The recorded product suite passed 90 tests with zero failures.
- Aggregate tables, depth distributions, agent split, longest-session facts,
  and reconstructed critical-path cost match independent recomputation.

## Validity boundaries

- This run does not measure tag accuracy. Only 18 of 353 optional names recur
  across records, and 72 warnings with 70 issue intervals remain.
- The population represents one project and is heavily Claude-weighted:
  99.286% of tokens and 93.445% of tool operations. The 42 frozen records
  contain 31 distinct native `source_session` strings, so record-normalized
  cost and reuse are not estimates over 42 independent runs.
- Step 0077 is contextual rather than a fair baseline: workload lengths differ
  and its cache split is unavailable.
- Conservation validates the adapter-to-pprof path, not independent
  raw-session parser correctness.
- Tool ancestry uses nearest same-prompt LLM timestamps. `result_preview`
  retains status rather than complete tool output. These choices can limit
  drill-down fidelity without affecting mass.
- Low name reuse was observed under the independent per-record protocol; this
  run does not prove that batching caused it.

## Required judgments

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional RQ evidence, primarily profiling-cost and
  real-history feasibility, with a one-project/Claude-heavy workload boundary
next paper decision: retain as supporting RQ4 cost and feasibility evidence;
  make no thesis or story change; do not use it as tag-accuracy, causal, or
  superiority evidence; next prioritize controlled correctness and
  problem-correspondence evaluation
```
