# R252 Paper-Scale C6 Label Package

Status: `paper_scale_label_collection_ready_no_labels`

This package collects the C6 human-label tasks into one handoff:

- R124 tag adequacy: 300 redacted session/prompt/LLM fragments per labeler.
- R190 merge-risk audit: 160 canonicalization-risk rows per labeler.
- R203 regenerated long-tail promotion review: 41 candidate rows per labeler.

Two independent labelers should fill the files under `labeler-packets/L01` and
`labeler-packets/L02`. The coordinator should copy completed files into the
R195 inbox names listed under `blank-r195-inbox-template`, keeping completed
returns private until review/adjudication is finished.

Required R195 return filenames:

```text
r124-labeler-1.csv
r124-labeler-2.csv
r190-labeler-1.csv
r190-labeler-2.csv
r203-labeler-1.csv
r203-labeler-2.csv
```

Do not run the default R195 command unless you intentionally copied completed
files into the default R195 inbox. The package-specific scoring command is:

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py \
  --r124-labeler-1 <completed-r124-labeler-1.csv> \
  --r124-labeler-2 <completed-r124-labeler-2.csv> \
  --r190-labeler-1 <completed-r190-labeler-1.csv> \
  --r190-labeler-2 <completed-r190-labeler-2.csv> \
  --r203-labeler-1 <completed-r203-labeler-1.csv> \
  --r203-labeler-2 <completed-r203-labeler-2.csv> \
  --r142-responses <missing-or-private-r142-responses.csv> \
  --scored-dir <private-scored-output-dir>
```

Optional adjudication files are `r124-adjudication.csv`,
`r190-adjudication.csv`, and `r203-adjudication.csv`.

Claim boundary: R252 fixes C6 label-collection logistics and verifies that blank R195 inputs do not upgrade any support gate. It adds no human labels and cannot support tag adequacy, merge quality, promotion quality, or weak accept.
