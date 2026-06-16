# R190 Merge-Risk Labeling

Give `r190-merge-risk-labeler-1.csv` and `r190-merge-risk-labeler-2.csv` to two independent labelers.
Labelers should fill only `audit_label` and `audit_notes`.

Allowed labels:
- `acceptable`: the raw-to-canonical decision is acceptable for display aggregation.
- `overmerge`: an applied merge hides a meaningfully distinct tag.
- `undermerge`: a retained/review-only tag should be merged into the proposed canonical tag.
- `unclear`: the row does not provide enough context for a confident judgment.

After both sheets are frozen, score:

```bash
python3 docs/visexp/r190_score_merge_audit.py \
  --labeler-1 docs/visexp/out/human-evidence-r193/r190/r190-merge-risk-labeler-1.csv \
  --labeler-2 docs/visexp/out/human-evidence-r193/r190/r190-merge-risk-labeler-2.csv
```
