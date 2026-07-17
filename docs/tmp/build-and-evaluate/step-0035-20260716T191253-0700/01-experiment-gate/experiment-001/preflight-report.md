# Real Preflight Report

**Executed:** 2026-07-16

**State:** `EXPERIMENT_GATE / REAL PREFLIGHT`

**Status:** **PASS**; admitted to the complete full run.

## Scope

The preflight ran the approved read-only adapter and scorer on one complete
released trajectory from each source form. It did not change or rerun the
Step 0024 recurrence constructor:

| Source form | Sessions | Operations |
|---|---:|---:|
| mini native | 1 | 47 |
| mini SWE raw | 1 | 38 |
| OpenHands native | 1 | 95 |
| OpenHands SWE raw | 1 | 33 |
| SWE-agent | 1 | 32 |
| Terminus2 | 1 | 22 |
| **Total** | **6** | **267** |

The command was:

```bash
python3 script/rq1_codetracebench_token_attribution_eval.py \
  --mode preflight \
  --output .agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight
```

## Source And Measurement Validity

- All 267 `(session, step_id)` operations joined to Step 0024 assignments,
  manifest stages, source-native `raw_action_key`, and positive provider usage.
- The adapter recovered 259 operation-producing response groups.
- Seven real Terminus2 responses produced 15 official operations. Their
  41,656 total tokens were counted once per response and allocated across only
  the matched official operations.
- No shared response crossed an official stage. Seven crossed raw-action-key
  groups and one crossed a recurrence group, so the allocation sensitivity was
  actually exercised rather than vacuously skipped.
- Provider totals and equal-allocation totals agree exactly: 7,341,862 prompt,
  123,894 completion, and 7,465,756 total tokens.
- The selected SWE-agent trajectory exercised two empty final-trajectory
  elements anchored between accepted tool-response IDs, including a text-only
  planning response and a retry response. Both received released usage without
  inventing an operation.

## Metric Path

The standard ordinary B-cubed path and the published object-weighted B-cubed
path both completed for recurrence, contiguous raw-action-key change,
action-kind and phase ablations, session-block, and singleton controls. The
preflight recurrence-minus-raw-action-key F1 deltas were:

| Analysis | Delta |
|---|---:|
| ordinary operation-level B-cubed | +0.099550 |
| total-token weighted, equal allocation | +0.083081 |
| total-token weighted, all-to-first | +0.081969 |
| total-token weighted, all-to-last | +0.081926 |

These six trajectories are an execution-path check only. The scorer records
`preflight_only`, does not authorize the RQ1 statement, does not run a
bootstrap, and does not change the expected full-population answer.

## Outputs

- `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight/operation-usage.jsonl`
- `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight/per-session.jsonl`
- `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight/framework-metrics.json`
- `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight/summary.json`
- `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight/report.md`

## Independent Audit

The independent reviewer reconstructed all 267 joins and every reported
ordinary/weighted B-cubed value from raw output, matching within approximately
`1e-15`. It also read-only checked the full 28-session SWE-agent and 93-session
Terminus2 populations, including 69 empty/retry operations, 1,426 multi-command
responses, and the two known non-executed response commands. It found no
scientific or execution defect and returned `PASS`; the complete 405-session
run is admitted without changing the plan.
