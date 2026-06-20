# R264 Human Return Intake Preflight

Status: `awaiting_private_returns`

## What This Checks

- R258 return checklist shape and row counts.
- C5 paper-scale response row coverage against the R249 assignment file.
- R124/R190/R203 paired labeler row counts and nonblank label coverage.
- Known synthetic-return markers from R259/R244 before R195 scoring.
- Ignore rules for private returned CSVs and R195 inbox/scored outputs.

## C5

- Status: `missing`.
- Ready for R195: `False`.
- Rows: `0` / `168`.
- Placeholder rows: `0`.
- Errors: `0`.

## C6 Groups

| group | status | ready | present files |
|---|---|---:|---|
| `r124` | `missing` | `False` | `` |
| `r190` | `missing` | `False` | `` |
| `r203` | `missing` | `False` | `` |

## Safety

- Input marker safety: `True`.
- R259 synthetic-marker regression: `True`.
- Privacy guard: `True`.

## R195 Command Template

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py --r142-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --r124-labeler-1 private/completed-paper-scale-r264/c6/L01/r124-labeler-1.csv --r124-labeler-2 private/completed-paper-scale-r264/c6/L02/r124-labeler-2.csv --r190-labeler-1 private/completed-paper-scale-r264/c6/L01/r190-labeler-1.csv --r190-labeler-2 private/completed-paper-scale-r264/c6/L02/r190-labeler-2.csv --r203-labeler-1 private/completed-paper-scale-r264/c6/L01/r203-labeler-1.csv --r203-labeler-2 private/completed-paper-scale-r264/c6/L02/r203-labeler-2.csv --scored-dir private/completed-paper-scale-r264/r195-scored --out-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-md private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.md
```

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Weak accept supported: `False`.

## Boundary

R264 validates whether returned human-study CSVs are complete and safe to pass to R195. It does not score responses, infer labels, adjudicate disagreements, or upgrade C5/C6.
