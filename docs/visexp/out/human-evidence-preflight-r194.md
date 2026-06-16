# R194 Human Evidence Preflight

Status: `ready_for_human_collection_no_outcomes`

## Gate

- Files OK: `True`
- R124 sheets blank: `True`
- R190 sheets blank: `True`
- R203 sheets blank: `True`
- R142 response template blank: `True`
- Existing scorers empty: `True`
- Support gates false: `True`

## Current Evidence Counts

- R124 final labels: 0
- R190 final labels: 0
- R203 final labels: 0
- R142 real responses: 0

## Next Commands

After real R124 labels are collected:

```bash
python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 <r124-labeler-1.csv> --labeler-2 <r124-labeler-2.csv> --adjudication <r124-adjudication.csv>
python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv
```

After real R142 pilot responses are collected:

```bash
python3 docs/visexp/score_user_task_results.py --responses <completed-pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142
```

After real R190 merge labels are collected:

```bash
python3 docs/visexp/r190_score_merge_audit.py --labeler-1 <r190-labeler-1.csv> --labeler-2 <r190-labeler-2.csv> --adjudication <r190-adjudication.csv>
```

After real R203 promotion labels are collected:

```bash
python3 docs/visexp/r203_long_tail_promotion_gate.py --labeler-1 <r203-labeler-1.csv> --labeler-2 <r203-labeler-2.csv> --adjudication <r203-adjudication.csv>
```

Claim impact: R194 is a preflight gate only. It does not support C5, C6, canonicalization quality, or long-tail promotion decisions.
