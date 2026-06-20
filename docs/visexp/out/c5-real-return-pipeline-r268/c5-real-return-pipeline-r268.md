# R268 C5 Real Return Scoring Pipeline

Status: `awaiting_private_c5_returns`

## Private Input

- Exists: `False`.
- Path kind: `private`.
- Safe to score: `False`.
- Public export policy: `existence_and_aggregate_status_only`.

## Commands

```bash
python3 docs/visexp/r264_human_return_intake_preflight.py --out-dir private/completed-paper-scale-r264/r264-intake --c5-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --r195-scored-dir private/completed-paper-scale-r264/r195-scored
python3 docs/visexp/r195_human_evidence_pipeline.py --r142-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --scored-dir private/completed-paper-scale-r264/r195-scored --out-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-md private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.md
python3 docs/visexp/r266_real_human_evidence_public_summary_gate.py --r195-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-dir docs/visexp/out/c5-real-return-pipeline-r268/public-summary-r266
```

## Step Summaries

- `r264_preflight`: exists=`False`, status=`None`.
- `r195_score`: exists=`False`, status=`None`.
- `r266_public_summary`: exists=`False`, status=`None`.

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Weak accept supported: `False`.
- Public claim update allowed: `False`.

## Boundary

R268 orchestrates private C5 user-task returns through R264, R195, and R266. It can support a public C5 summary only when real private C5 responses exist and R195 scores them. It never supports C6 or weak accept by itself.

## Next Action

Collect the 168-row paper-scale C5 response CSV under the private return path, then rerun this script. C6 label evidence must still be collected and scored separately for weak-accept support.
