# Independent Result Review

## Node record

- Completed: 2026-07-14T02:44:32-07:00
- Reviewer: independent subagent explicitly applying
  `research-experiment-design`
- Inputs: approved plan, three plan reviews, preflight, runner, all 30 raw run
  directories, `runs.csv`, `result.json`, and committed R160 result
- Verdict: **PASS**
- Run status: `VALID / COMPLETE`
- Tested hypothesis: **SUPPORTED**
- Scientific value: decisive for the scoped RQ4 cost question
- Must-fix: zero

## Independent completeness checks

- 30/30 planned run cells exist with no missing or extra combination.
- Every workload/profile cell has exactly three repetitions.
- Every run has exit status 0, profiler status `ok`, and empty stderr.
- Every sample total and profile weight sum equals its operation-row count.
- Every reported unique-stack count equals the parsed profile group count.
- Output byte counts equal file sizes.
- The three deterministic profile hashes within every cell are identical.
- Source rows are 729, 4,285, 6,010, and 16,741; the exact union is 27,765.
- Every source row contains all required fields and unit value.

## Independently recomputed medians

| Workload | Semantic median wall / median RSS | Raw-action median wall / median RSS |
|---|---|---|
| AgentRewardBench | 40 ms / 19,496 KiB | 30 ms / 19,304 KiB |
| Satraj | 170 ms / 75,248 KiB | 140 ms / 74,240 KiB |
| OSWorld-Human | 250 ms / 110,904 KiB | 210 ms / 109,704 KiB |
| AgentNet | 710 ms / 285,064 KiB | 580 ms / 281,656 KiB |
| Exact union | 1,170 ms / 475,612 KiB | 990 ms / 469,564 KiB |

The union semantic repetitions are 1,150, 1,190, and 1,170 ms. The largest
observed union RSS is 475,640 KiB (464.49 MiB). Both predeclared practical
bounds pass: 1.17 s is below 10 s and every repetition is below 1 GiB.

On identical union inputs, semantic construction adds 180 ms (18.18%) and
6,048 KiB largest peak RSS (1.29%) over the raw-action cost control.

## Independently recomputed descriptive fits

- semantic: slope 0.042176132 ms/operation, intercept -0.408127 ms,
  R-squared 0.999737740, strictly monotonic;
- raw-action: slope 0.035599544 ms/operation, intercept -5.368541 ms,
  R-squared 0.999511993, strictly monotonic.

These are descriptive results over 729--27,765 operations and five existing
heterogeneous workloads, not universal complexity claims.

## R160 boundary recomputation

R160 records one predecessor AgentFlame fixed-input pair: clean 1.64 s with 60
LLM calls; identical-input cached 0.11 s with 76/76 cache hits and zero LLM
calls. The exact ratio is 14.9091x, and its sanitized manifest confirms input
equality. It supports the shared cache mechanism's elimination of repeated
field-derivation calls. It is not current `agentpprof 0.2.37` cache timing or a
repeated performance estimate.

## Scientific answer

Across the four complete existing public workload files and their exact
27,765-operation union, current `agentpprof 0.2.37` semantic construction has a
predictable near-linear measured scale curve. The largest complete input takes
1.17 s median and 464.49 MiB maximum RSS. Together with the strictly bounded
R160 predecessor evidence, the current evidence supports practical profile
construction and a cache mechanism that avoids repeated LLM derivation calls.

This is additional RQ evidence, not a thesis challenge. Proceed to WRITE while
preserving the current-binary versus predecessor-cache boundary. No additional
experiment or control is required for this transition.
