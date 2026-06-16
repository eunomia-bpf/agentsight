# R124 Tag Adequacy Labeling

Give `r124-tag-adequacy-labeler-1.csv` and `r124-tag-adequacy-labeler-2.csv` to two independent labelers.
Labelers should fill only `label` and `notes`.

Allowed labels:
- `adequate`: the tag preserves the main intent well enough for navigation.
- `generic_noisy`: the tag is grammatical but too broad or visually noisy.
- `misleading`: the tag points to the wrong task, object, or action.

After both sheets are frozen, join and score:

```bash
python3 docs/visexp/r124_join_blinded_labels.py \
  --labeler-1 docs/visexp/out/human-evidence-r193/r124/r124-tag-adequacy-labeler-1.csv \
  --labeler-2 docs/visexp/out/human-evidence-r193/r124/r124-tag-adequacy-labeler-2.csv
python3 docs/visexp/score_tag_adequacy.py \
  --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv
```
