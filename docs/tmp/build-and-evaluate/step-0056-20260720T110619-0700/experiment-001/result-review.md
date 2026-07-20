# Step 0056 Independent Result Review — Causal Exact Task-Identity Invariant

## Verdict

**APPROVE — must-fix: 0.**

- reviewer: separate Claude Sonnet agent process;
- required skill explicitly read and applied: `research-experiment-design`;
- mode: read-only repository audit;
- reviewer performed no planning, implementation, experiment execution, model
  inference, file modification, or Git mutation for Step 0056.

## Independent Method

The reviewer did not rerun the repository scorer. Its read-only sandbox did not
permit Python, `awk`, or `bc`, so it independently implemented the joins,
metrics, and resampling logic in `jq` directly over raw JSONL/JSON. It checked
the evaluator code only after reconstructing the relevant quantities.

## Coverage And Join Reconstruction

- 20,866 prediction rows and 405 sessions independently counted;
- every operation key is present in both fixed Step 0054 and Step 0055 score
  rows;
- zero gold-label drift between those fixed inputs; and
- complete population, framework, stage-occurrence, adjacent-pair, and task-
  cluster counts agree with the registered report.

## Causal-Reuse Audit

The reviewer traversed all 405 raw session caches. Exact-request reuse occurs
only up to and including the first invariant-applied turn; every later turn is
newly inferred. All 2,876 reused responses match the Step 0054 `raw_response`
and `request_sha256` byte-for-byte.

The raw transitions independently reproduce:

- proposals: 6,604 push, 6,130 replace, 4,411 stay, three pop;
- applied: 3,020 push, 2,983 replace, 11,142 stay, three pop;
- 6,731 invariant applications; and
- 397 affected sessions.

No second intervention or look-ahead was found. Gold labels and the official
manifest remain absent from inference.

## Independent Metric Reconstruction

The reviewer reimplemented ordinary B-cubed, adjacent-boundary, and exact-span
scores for the causal candidate, Step 0055 visible-path baseline, and recurrence
incumbent. Every value matches `full/score/summary.json` to approximately ten
significant digits.

Because its sandbox could not run Python, the reviewer additionally tested
bootstrap stability with an independent Park-Miller RNG, seed 987654321, and
2,000 task-cluster resamples instead of copying the registered Python sequence:

| Comparison | Independent 95% interval | Registered 95% interval |
|---|---:|---:|
| causal minus recurrence | [-0.0278, +0.0027] | [-0.0278, +0.0025] |
| causal minus Step 0055 | [+0.0662, +0.1005] | [+0.0663, +0.1008] |

The adoption conclusions are therefore stable to an independent resampling
implementation and seed. The reviewer also read `run_score()` and confirmed
that the registered values necessarily yield `adopted=False`,
`contradicted=False`, and `close-online-qwen3b-branch-inconclusive`.

Terminus2's positive framework slice and the behavior diagnostics—maximum
depth 28, median per-session maximum 5, p90 14, and 184 sessions without a
depth decrease—also reproduce exactly.

## Claim And Research-Contract Audit

The result correctly states that the identity invariant has a positive causal
mechanism effect but does not clear the registered constructor-adoption rule.
Closing this fixed online Qwen2.5-3B branch is therefore correct. It does not
close RQ3, weaken its positive hypothesis, narrow the task-semantic hierarchy,
or change the thesis **“Agent observability needs profiling, not only
debugging.”**

## Non-Blocking Observations

1. Skim readers benefit from explicitly labeling the Step0056 preflight score
   as preflight rather than the registered result.
2. A Python-capable audit could bit-exactly reproduce the stored
   `random.Random(20260720)` bootstrap sequence, but the independent metric
   reconstruction and differently seeded resampling already confirm every
   scientific decision; this is not a must-fix.
