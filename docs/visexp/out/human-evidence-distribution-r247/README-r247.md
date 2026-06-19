# AgentFlame Human Evidence Bundle R247

This offline bundle contains static HTML forms for the R142 participant pilot
and R124/R190/R203 human label collection. It contains no answer key, scorer
script, raw agent trace, or synthetic smoke export.

Open `index.html` in a browser. Participant forms export per-participant CSVs.
Use `coordinator/r142-merge.html` to merge P01-P05 exports into the R195-ready
`r142-pilot-responses.csv` file.

Returned files:

| File | Source form | Rows | Required gate |
|------|-------------|------|---------------|
| `r142-pilot-responses.csv` | `coordinator/r142-merge.html` | 70 | yes |
| `r124-labeler-1.csv` | `labelers/r124-labeler-1.html` | 300 | yes |
| `r124-labeler-2.csv` | `labelers/r124-labeler-2.html` | 300 | yes |
| `r190-labeler-1.csv` | `labelers/r190-labeler-1.html` | 160 | if claiming merge quality |
| `r190-labeler-2.csv` | `labelers/r190-labeler-2.html` | 160 | if claiming merge quality |
| `r203-labeler-1.csv` | `labelers/r203-labeler-1.html` | 41 | if claiming regenerated-tag promotion |
| `r203-labeler-2.csv` | `labelers/r203-labeler-2.html` | 41 | if claiming regenerated-tag promotion |

After real returns exist, place them in `docs/visexp/out/human-evidence-r195/inbox`
using the exact filenames above, then run:

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py
```

Do not treat this bundle, blank forms, synthetic exports, subagent review, or
LLM-filled labels as C5/C6 evidence. Only scored real returns can change those
claim gates.
