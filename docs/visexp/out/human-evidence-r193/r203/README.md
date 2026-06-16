# R203 Long-Tail Promotion Labeling

Give `r203-long-tail-promotion-labeler-1.csv` and `r203-long-tail-promotion-labeler-2.csv` to two independent labelers.
Labelers should fill only `promotion_label` and `promotion_notes`.

Allowed labels:
- `promote`: the regenerated tag is better than the raw tag for display aggregation.
- `keep_raw`: the raw tag should remain the display label.
- `reject`: the regenerated tag is misleading or worse.
- `split`: the row needs a contextual split instead of one replacement label.
- `unclear`: the provided process/effect/context profile is insufficient.

After both sheets are frozen, score:

```bash
python3 docs/visexp/r203_long_tail_promotion_gate.py \
  --labeler-1 docs/visexp/out/human-evidence-r193/r203/r203-long-tail-promotion-labeler-1.csv \
  --labeler-2 docs/visexp/out/human-evidence-r193/r203/r203-long-tail-promotion-labeler-2.csv
```

Accepted promotion labels still do not update the canonical map. A later reviewed display-map diff is required.
