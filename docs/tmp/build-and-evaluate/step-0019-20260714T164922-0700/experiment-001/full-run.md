# Full Run: RQ2 Fixed-Reader Problem Prioritization

**Completed:** 2026-07-14T17:19:13-07:00
**Selected RQ:** RQ2: Does profiler output correspond to real problems?
**Run status before independent result review:** complete and mechanically valid

## Executed Matrix

The approved command ran the fixed local `qwen3.6-27b` reader over every
planned presentation:

```bash
python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 --model qwen3.6-27b \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/full \
  --order-scheme cyclic-5 \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 3
```

Collection completed 66 of 66 presentations in 517.65 seconds: all five
cyclic rotations for each of six operation-stack and six fixed-session
packets, plus one presentation for each of six flat packets. All 66 responses
succeeded on the first API attempt; no response was dropped, imputed, or
manually repaired. The score phase then ran the approved separate command:

```bash
python3 script/r315_llm_reader_eval.py score \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --hidden-key docs/visexp/out/analyst-study-protocol-r315/hidden-scoring-key.json \
  --ranker-scores docs/visexp/out/analyst-study-readout-r316/trial-scores.csv \
  --responses .agentsight/experiments/r315-llm-reader-rq2-v2/full/responses.jsonl \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/full
```

The hidden key was loaded only by this post-collection score phase. No model
call occurs in `score`.

## Mechanical Checks

- `responses.jsonl` contains 66 unique successful presentation records: 30
  operation-stack, 30 fixed-session, and 6 flat.
- Every response contains exactly the planned number of distinct valid aliases
  and non-empty visible evidence.
- Every non-flat original group occupies aliases `G01` through `G05` exactly
  once across its five cyclic rotations; there are zero position-balance
  failures.
- No original group ID occurs in a serialized model request. Parsing the user
  payloads finds none of the forbidden keys `packet_id`, `view`, `ranker`,
  `response_prompt`, `rank`, `group_id`, or a hidden-key field.
- The reader did react to order in some packets: six of twelve non-flat
  packets produced more than one selected group set across rotations. The
  approved within-packet rotation average is therefore necessary rather than
  cosmetic.
- The emitted files contain 66 presentation-score rows, 18 task/view rows, six
  paired task rows, and 18 deduplicated existing-ranker control rows.

## Registered Primary Result

After averaging the five rotations within each non-flat task/view, the
operation-stack view is compared with fixed-session on six paired task units.

| Metric | Mean paired delta | Median paired delta | Better / tied / worse tasks | Registered pass |
|---|---:|---:|---:|---|
| Selected-positive operation recall | +0.147029 | +0.080571 | 5 / 0 / 1 | yes |
| Selected-positive operation precision | +0.052880 | +0.035501 | 4 / 0 / 2 | yes |

An independent shell recomputation over the six emitted paired rows reproduces
both medians and win counts. Because both registered primary metrics have a
positive median and improve on at least four of six tasks, the predeclared
experiment verdict is **SUPPORTED**.

The task-level recall deltas are `-0.004805`, `+0.008186`, `+0.361111`,
`+0.064356`, `+0.356545`, and `+0.096785`. Precision deltas are `+0.009599`,
`+0.061404`, `-0.105263`, `+0.159329`, `-0.177203`, and `+0.369412` for the
same task order. These heterogeneous rows remain the scientific units; no
population-level p-value or cross-task generalization claim is made.

## Deviations And Scope

There was no execution, prompt, model, metric, task, packet, rotation, budget,
or outcome-rule deviation from the approved plan. The result covers one
deterministic quantized Qwen3.6-27B reader, six public-data tasks, existing
top-five R315 packets, and an exactly-three-group decision. It is not a human
study and does not establish remediation, human productivity, superiority to
raw action, cross-model generality, or universal view dominance.

The fresh result reviewer must still independently recompute the raw evidence
and judge baseline fairness, leakage, mechanism engagement, uncertainty,
research value, and paper impact before the orchestrator may update the paper.

## Raw Evidence

- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/collection-summary.json`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/responses.jsonl`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/presentation-scores.csv`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/task-view-scores.csv`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/paired-task-comparison.csv`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/ranker-control.csv`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/summary.json`
- `.agentsight/experiments/r315-llm-reader-rq2-v2/full/result-report.md`
