# R270 C6 Real Label Scoring Pipeline

Status: `awaiting_private_c6_labels`

## Private Inputs

- Required existing: `0` / `6`.
- All required exist: `False`.
- All inputs private or absent: `True`.
- Safe to score: `False`.
- Public export policy: `existence_and_aggregate_status_only`.

## Commands

```bash
python3 docs/visexp/r264_human_return_intake_preflight.py --out-dir private/completed-paper-scale-r264/r264-c6-intake --c5-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r124-labeler-1 private/completed-paper-scale-r264/c6/L01/r124-labeler-1.csv --r124-labeler-2 private/completed-paper-scale-r264/c6/L02/r124-labeler-2.csv --r190-labeler-1 private/completed-paper-scale-r264/c6/L01/r190-labeler-1.csv --r190-labeler-2 private/completed-paper-scale-r264/c6/L02/r190-labeler-2.csv --r203-labeler-1 private/completed-paper-scale-r264/c6/L01/r203-labeler-1.csv --r203-labeler-2 private/completed-paper-scale-r264/c6/L02/r203-labeler-2.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --r195-scored-dir private/completed-paper-scale-r264/r195-scored
python3 docs/visexp/r195_human_evidence_pipeline.py --r142-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --r124-labeler-1 private/completed-paper-scale-r264/c6/L01/r124-labeler-1.csv --r124-labeler-2 private/completed-paper-scale-r264/c6/L02/r124-labeler-2.csv --r124-adjudication private/completed-paper-scale-r264/c6/adjudication/r124-adjudication.csv --r190-labeler-1 private/completed-paper-scale-r264/c6/L01/r190-labeler-1.csv --r190-labeler-2 private/completed-paper-scale-r264/c6/L02/r190-labeler-2.csv --r190-adjudication private/completed-paper-scale-r264/c6/adjudication/r190-adjudication.csv --r203-labeler-1 private/completed-paper-scale-r264/c6/L01/r203-labeler-1.csv --r203-labeler-2 private/completed-paper-scale-r264/c6/L02/r203-labeler-2.csv --r203-adjudication private/completed-paper-scale-r264/c6/adjudication/r203-adjudication.csv --scored-dir private/completed-paper-scale-r264/r195-scored --out-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-md private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.md
python3 docs/visexp/r266_real_human_evidence_public_summary_gate.py --r195-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-dir docs/visexp/out/c6-real-label-pipeline-r270/public-summary-r266
```

## Step Summaries

- `r264_preflight`: exists=`False`, status=`None`.
- `r195_score`: exists=`False`, status=`None`.
- `r266_public_summary`: exists=`False`, status=`None`.

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Canonicalization quality supported: `False`.
- Long-tail promotion review supported: `False`.
- Weak accept supported: `False`.
- Public claim update allowed: `False`.

## Boundary

R270 orchestrates private C6 human-label returns through R264, R195, and R266. It can support public C6 aggregate claims only after real private labeler CSVs exist and any R195 adjudication requirement is resolved. It never creates labels and cannot support weak accept without C5.

## Next Action

Collect completed private R124/R190/R203 paired labeler CSVs, then rerun this script. If it reports c6_needs_adjudication, fill the private adjudication CSVs generated from the R195 templates and rerun before publishing aggregate C6 numbers.
